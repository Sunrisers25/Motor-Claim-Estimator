/**
 * src/lib/api.ts
 * ---------------
 * API service layer — connects the React frontend to the Python FastAPI backend.
 *
 * Usage:
 *   import { analyzeImages, fetchClaims, fetchStats } from "@/lib/api";
 *
 * Set USE_MOCK = true  → use mock data (no backend needed, for demo)
 * Set USE_MOCK = false → call the real FastAPI backend at API_BASE_URL
 */

import {
    DEMO_DETECTIONS,
    DEMO_FRAUD_RESULTS,
    MOCK_CLAIMS,
    BASE_PRICES,
    LABOR_COST,
    INFLATION_FACTOR,
    CAR_MULTIPLIERS,
    type Detection,
    type FraudResult,
} from "@/data/mockData";

// ── Config ────────────────────────────────────────────────────────────────────
export const API_BASE_URL = "http://localhost:8000";

// Toggle: true = use mock data (offline demo), false = call real Python backend
export const USE_MOCK = false;

// ── Types ─────────────────────────────────────────────────────────────────────

export interface AnalyzePayload {
    images: File[];
    customerName: string;
    policyNumber: string;
    vehicleReg: string;
    vehicleMake: string;
    carType: string;
    detectionMode: "simulation" | "huggingface" | "local";
    confidenceThreshold: number;
}

export interface FraudSummary {
    overallRisk: "Low" | "Medium" | "High";
    flaggedCount: number;
    results: FraudResult[];
}

export interface CostBreakdownItem {
    part: string;
    severity: string;
    score: number;
    baseCost: number;
    repairCost: number;
    labor: number;
    total: number;
    recommendation: "Repair" | "Replace";
    justification: string;
}

export interface AnalyzeResult {
    claimId: string;
    fraudSummary: FraudSummary;
    detections: Detection[];
    annotatedImages: string[]; // base64 data URIs
    costBreakdown: CostBreakdownItem[];
    totals: {
        repairSubtotal: number;
        totalLabor: number;
        grandTotal: number;
        carType: string;
        multiplier: number;
    };
    decision: {
        status: string;
        description: string;
        color: string;
        lowConfidenceFlag: boolean;
    };
    nlpExplanation: string;
}

export interface Claim {
    id: string;
    customer: string;
    policyNo: string;
    vehicle: string;
    carType: string;
    totalCost: number;
    decision: string;
    date: string;
}

export interface ClaimStats {
    totalClaims: number;
    avgCost: number;
    autoApprovalRate: number;
    mostDamagedPart: string;
    decisionBreakdown: { name: string; count: number }[];
    partFrequency: { name: string; count: number }[];
    costTrend: { id: string; cost: number }[];
}

// ── Mock helpers ──────────────────────────────────────────────────────────────

function buildMockResult(payload: AnalyzePayload): AnalyzeResult {
    const mult = CAR_MULTIPLIERS[payload.carType] || 1.0;

    const costBreakdown: CostBreakdownItem[] = DEMO_DETECTIONS.map((d) => {
        const base = BASE_PRICES[d.part] || 2000;
        const sevMult =
            d.severity === "Severe" ? 1.0 : d.severity === "Moderate" ? 0.7 : 0.4;
        const repairCost = Math.round(base * sevMult * mult * INFLATION_FACTOR);
        const labor = Math.round(LABOR_COST * mult * INFLATION_FACTOR);
        return {
            part: d.part,
            severity: d.severity,
            score: d.score,
            baseCost: base,
            repairCost,
            labor,
            total: repairCost + labor,
            recommendation: d.areaCoverage >= 30 ? "Replace" : "Repair",
            justification:
                d.areaCoverage >= 30
                    ? `${d.part} damage covers ${d.areaCoverage}% of surface — replacement required.`
                    : `${d.part} damage covers ${d.areaCoverage}% of surface — repair is sufficient.`,
        };
    });

    const grandTotal = costBreakdown.reduce((s, c) => s + c.total, 0);
    const avgConf = Math.round(
        DEMO_DETECTIONS.reduce((s, d) => s + d.confidence, 0) /
        DEMO_DETECTIONS.length
    );

    const decisionStatus =
        avgConf < 60
            ? "Manual Inspection Required"
            : grandTotal <= 25000
                ? "Auto Approved"
                : grandTotal <= 60000
                    ? "Supervisor Review"
                    : "Manual Inspection Required";

    return {
        claimId: `CLM-${new Date()
            .toISOString()
            .slice(0, 10)
            .replace(/-/g, "")}-DEMO01`,
        fraudSummary: {
            overallRisk: "Low",
            flaggedCount: 0,
            results: DEMO_FRAUD_RESULTS,
        },
        detections: DEMO_DETECTIONS,
        annotatedImages: [],
        costBreakdown,
        totals: {
            repairSubtotal: costBreakdown.reduce((s, c) => s + c.repairCost, 0),
            totalLabor: costBreakdown.reduce((s, c) => s + c.labor, 0),
            grandTotal,
            carType: payload.carType,
            multiplier: mult,
        },
        decision: {
            status: decisionStatus,
            description: `Total claim value: ₹${grandTotal.toLocaleString()}`,
            color:
                decisionStatus === "Auto Approved"
                    ? "green"
                    : decisionStatus === "Supervisor Review"
                        ? "orange"
                        : "red",
            lowConfidenceFlag: avgConf < 60,
        },
        nlpExplanation: `📋 DAMAGE ASSESSMENT\n────────────────────────────────────────\n${DEMO_DETECTIONS.map(
            (d) =>
                `• ${d.part}: ${d.severity} damage detected covering ${d.areaCoverage}% of inspected surface.`
        ).join("\n")}\n\n💰 COST REASONING\n────────────────────────────────────────\n${costBreakdown
            .map(
                (c) =>
                    `• ${c.part} (${c.severity}): Base ₹${c.baseCost.toLocaleString()} × multipliers = ₹${c.repairCost.toLocaleString()} + ₹${c.labor.toLocaleString()} labor`
            )
            .join("\n")}\n\n⚖️ DECISION\n────────────────────────────────────────\nDecision: ${decisionStatus}\nGrand Total: ₹${grandTotal.toLocaleString()}`,
    };
}

function buildMockStats(): ClaimStats {
    const totalClaims = MOCK_CLAIMS.length;
    const avgCost = Math.round(
        MOCK_CLAIMS.reduce((s, c) => s + c.totalCost, 0) / totalClaims
    );
    const autoCount = MOCK_CLAIMS.filter(
        (c) => c.decision === "Auto Approved"
    ).length;
    const autoApprovalRate = parseFloat(
        ((autoCount / totalClaims) * 100).toFixed(1)
    );

    const decisionCounts: Record<string, number> = {
        "Auto Approved": 0,
        "Supervisor Review": 0,
        "Manual Inspection": 0,
    };
    MOCK_CLAIMS.forEach((c) => {
        const key = c.decision in decisionCounts ? c.decision : "Manual Inspection";
        decisionCounts[key]++;
    });

    const parts = [
        "Bumper", "Headlight", "Scratch", "Door", "Dent", "Windshield", "Hood",
    ];
    const partFrequency = parts.map((name, i) => ({
        name,
        count: Math.max(2, totalClaims - i * 3),
    }));

    return {
        totalClaims,
        avgCost,
        autoApprovalRate,
        mostDamagedPart: "Bumper",
        decisionBreakdown: Object.entries(decisionCounts).map(([name, count]) => ({
            name,
            count,
        })),
        partFrequency,
        costTrend: MOCK_CLAIMS.map((c) => ({ id: c.id.slice(-6), cost: c.totalCost })),
    };
}

// ── Real API calls ────────────────────────────────────────────────────────────

async function callAnalyze(payload: AnalyzePayload): Promise<AnalyzeResult> {
    const form = new FormData();
    payload.images.forEach((f) => form.append("images", f));
    form.append("customer_name", payload.customerName);
    form.append("policy_number", payload.policyNumber);
    form.append("vehicle_reg", payload.vehicleReg);
    form.append("vehicle_make", payload.vehicleMake);
    form.append("car_type", payload.carType);
    form.append("detection_mode", payload.detectionMode);
    form.append("confidence_threshold", String(payload.confidenceThreshold / 100));

    const res = await fetch(`${API_BASE_URL}/api/analyze`, {
        method: "POST",
        body: form,
    });

    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
}

async function callFetchClaims(): Promise<Claim[]> {
    const res = await fetch(`${API_BASE_URL}/api/claims`);
    if (!res.ok) throw new Error("Failed to fetch claims");
    const raw = await res.json();
    // Normalise from Python snake_case to camelCase
    return (raw as any[]).map((c) => ({
        id: c.claim_id,
        customer: c.customer_name || "N/A",
        policyNo: c.policy_number || "N/A",
        vehicle: c.vehicle_make || "N/A",
        carType: c.car_type || "Sedan",
        totalCost: c.total_cost,
        decision: c.decision,
        date: c.created_at?.slice(0, 10) || "",
    }));
}

async function callFetchStats(): Promise<ClaimStats> {
    const res = await fetch(`${API_BASE_URL}/api/stats`);
    if (!res.ok) throw new Error("Failed to fetch stats");
    return res.json();
}

// ── Public API (used by components) ──────────────────────────────────────────

/**
 * Run the full AI analysis pipeline.
 * Automatically uses mock or real backend based on USE_MOCK flag.
 */
export async function analyzeImages(
    payload: AnalyzePayload
): Promise<AnalyzeResult> {
    if (USE_MOCK) {
        // Simulate network delay
        await new Promise((r) => setTimeout(r, 1200));
        return buildMockResult(payload);
    }
    return callAnalyze(payload);
}

/**
 * Fetch all saved claims for the analytics dashboard.
 */
export async function fetchClaims(): Promise<Claim[]> {
    if (USE_MOCK) {
        await new Promise((r) => setTimeout(r, 400));
        return MOCK_CLAIMS;
    }
    return callFetchClaims();
}

/**
 * Fetch aggregate analytics stats.
 */
export async function fetchStats(): Promise<ClaimStats> {
    if (USE_MOCK) {
        await new Promise((r) => setTimeout(r, 400));
        return buildMockStats();
    }
    return callFetchStats();
}

/**
 * Download PDF report from backend.
 * Returns a blob URL for download.
 */
export async function downloadPDF(
    analyzeResult: AnalyzeResult,
    metadata: {
        customerName: string;
        policyNumber: string;
        vehicleReg: string;
        vehicleMake: string;
        carType: string;
    }
): Promise<void> {
    if (USE_MOCK) {
        // In mock mode, show an alert since we can't generate real PDFs
        alert("PDF download requires the Python backend.\nSet USE_MOCK = false in src/lib/api.ts and run: uvicorn api:app --port 8000");
        return;
    }

    const form = new FormData();
    form.append("payload", JSON.stringify(analyzeResult));
    form.append("customer_name", metadata.customerName);
    form.append("policy_number", metadata.policyNumber);
    form.append("vehicle_reg", metadata.vehicleReg);
    form.append("vehicle_make", metadata.vehicleMake);
    form.append("car_type", metadata.carType);

    const res = await fetch(`${API_BASE_URL}/api/pdf`, {
        method: "POST",
        body: form,
    });

    if (!res.ok) throw new Error("PDF generation failed");

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `claim_${analyzeResult.claimId}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
}
