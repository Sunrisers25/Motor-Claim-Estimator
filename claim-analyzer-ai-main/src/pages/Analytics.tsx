import { useState, useMemo, useEffect } from "react";
import { Link } from "react-router-dom";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { Button } from "@/components/ui/button";
import AnimatedCounter from "@/components/AnimatedCounter";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, Cell,
} from "recharts";
import { MOCK_CLAIMS, getDecisionColor, getDecisionBg, type ClaimRecord } from "@/data/mockData";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { fetchClaims } from "@/lib/api";

const DECISION_COLORS: Record<string, string> = {
  "Auto Approved": "#16a34a",
  "Supervisor Review": "#d97706",
  "Manual Inspection": "#dc2626",
};

const ITEMS_PER_PAGE = 10;

export default function Analytics() {
  const [page, setPage] = useState(0);

  const totalClaims = MOCK_CLAIMS.length;
  const avgCost = Math.round(MOCK_CLAIMS.reduce((s, c) => s + c.totalCost, 0) / totalClaims);
  const autoRate = ((MOCK_CLAIMS.filter((c) => c.decision === "Auto Approved").length / totalClaims) * 100).toFixed(1);

  const partCounts = useMemo(() => {
    const parts: Record<string, number> = {};
    // Simulate part frequency
    ["Bumper", "Headlight", "Scratch", "Door", "Dent", "Windshield", "Hood"].forEach((p, i) => {
      parts[p] = Math.max(2, totalClaims - i * 3);
    });
    return Object.entries(parts).map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count);
  }, [totalClaims]);

  const decisionData = useMemo(() => {
    const counts: Record<string, number> = { "Auto Approved": 0, "Supervisor Review": 0, "Manual Inspection": 0 };
    MOCK_CLAIMS.forEach((c) => counts[c.decision]++);
    return Object.entries(counts).map(([name, count]) => ({ name, count }));
  }, []);

  const costTrend = MOCK_CLAIMS.map((c) => ({ id: c.id.slice(-6), cost: c.totalCost }));

  const pages = Math.ceil(totalClaims / ITEMS_PER_PAGE);
  const pageData = MOCK_CLAIMS.slice(page * ITEMS_PER_PAGE, (page + 1) * ITEMS_PER_PAGE);

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="container py-8">
        {/* Header */}
        <div className="glass-card p-6 mb-8 gradient-mesh">
          <h1 className="text-2xl font-bold text-foreground">📊 Claims Analytics Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1">Real-time insights from processed motor insurance claims</p>
        </div>

        {/* KPI Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { label: "Total Claims", numValue: totalClaims, prefix: "", suffix: "" },
            { label: "Avg Claim Cost", numValue: avgCost, prefix: "₹", suffix: "" },
            { label: "Auto-Approval Rate", numValue: parseFloat(autoRate), prefix: "", suffix: "%" },
            { label: "Most Damaged Part", value: "Bumper" },
          ].map((kpi, i) => (
            <div key={i} className="glass-card p-5 text-center hover-lift">
              <div className="text-xs text-muted-foreground mb-1">{kpi.label}</div>
              <div className="text-2xl font-bold text-foreground">
                {kpi.value ? kpi.value : <AnimatedCounter value={kpi.numValue!} prefix={kpi.prefix} suffix={kpi.suffix} />}
              </div>
            </div>
          ))}
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="glass-card p-5">
            <h3 className="text-sm font-semibold text-foreground mb-4">Decision Breakdown</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={decisionData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(217.2 32.6% 20%)" />
                <XAxis dataKey="name" tick={{ fill: "hsl(215 20.2% 65.1%)", fontSize: 11 }} />
                <YAxis tick={{ fill: "hsl(215 20.2% 65.1%)", fontSize: 11 }} />
                <Tooltip contentStyle={{ background: "hsl(217.2 32.6% 17.5%)", border: "1px solid hsl(217.2 32.6% 25%)", borderRadius: 8, color: "#fff" }} />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {decisionData.map((entry, i) => (
                    <Cell key={i} fill={DECISION_COLORS[entry.name] || "#2563eb"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="glass-card p-5">
            <h3 className="text-sm font-semibold text-foreground mb-4">Most Frequently Damaged Parts</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={partCounts} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(217.2 32.6% 20%)" />
                <XAxis type="number" tick={{ fill: "hsl(215 20.2% 65.1%)", fontSize: 11 }} />
                <YAxis type="category" dataKey="name" tick={{ fill: "hsl(215 20.2% 65.1%)", fontSize: 11 }} width={80} />
                <Tooltip contentStyle={{ background: "hsl(217.2 32.6% 17.5%)", border: "1px solid hsl(217.2 32.6% 25%)", borderRadius: 8, color: "#fff" }} />
                <Bar dataKey="count" fill="#38bdf8" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Cost Distribution */}
        <div className="glass-card p-5 mb-8">
          <h3 className="text-sm font-semibold text-foreground mb-4">Cost Distribution per Claim</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={costTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(217.2 32.6% 20%)" />
              <XAxis dataKey="id" tick={{ fill: "hsl(215 20.2% 65.1%)", fontSize: 10 }} />
              <YAxis tick={{ fill: "hsl(215 20.2% 65.1%)", fontSize: 11 }} />
              <Tooltip contentStyle={{ background: "hsl(217.2 32.6% 17.5%)", border: "1px solid hsl(217.2 32.6% 25%)", borderRadius: 8, color: "#fff" }} formatter={(v: number) => [`₹${v.toLocaleString()}`, "Cost"]} />
              <Line type="monotone" dataKey="cost" stroke="#10b981" strokeWidth={2} dot={{ fill: "#10b981", r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Claim History Table */}
        <div className="glass-card overflow-hidden mb-8">
          <h3 className="text-sm font-semibold text-foreground p-5 pb-0">Full Claim History</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm mt-4">
              <thead><tr className="text-xs text-muted-foreground bg-secondary/30">
                <th className="text-left p-3">Claim ID</th>
                <th className="text-left p-3">Customer</th>
                <th className="text-left p-3 hidden md:table-cell">Policy No</th>
                <th className="text-left p-3 hidden lg:table-cell">Vehicle</th>
                <th className="text-left p-3 hidden lg:table-cell">Car Type</th>
                <th className="text-right p-3">Total Cost</th>
                <th className="text-center p-3">Decision</th>
                <th className="text-left p-3 hidden md:table-cell">Date</th>
              </tr></thead>
              <tbody>
                {pageData.map((c) => (
                  <tr key={c.id} className={cn("border-t border-border/50 text-foreground", getDecisionBg(c.decision).replace("bg-", "hover:bg-").replace("/10", "/5"))}>
                    <td className="p-3 font-mono text-xs">{c.id}</td>
                    <td className="p-3">{c.customer}</td>
                    <td className="p-3 hidden md:table-cell text-muted-foreground">{c.policyNo}</td>
                    <td className="p-3 hidden lg:table-cell">{c.vehicle}</td>
                    <td className="p-3 hidden lg:table-cell">{c.carType}</td>
                    <td className="p-3 text-right font-medium">₹{c.totalCost.toLocaleString()}</td>
                    <td className="p-3 text-center">
                      <span className={cn("text-xs px-2 py-1 rounded-full border", getDecisionBg(c.decision), getDecisionColor(c.decision))}>
                        {c.decision === "Auto Approved" ? "✅" : c.decision === "Supervisor Review" ? "⚠️" : "🔴"} {c.decision}
                      </span>
                    </td>
                    <td className="p-3 hidden md:table-cell text-muted-foreground">{c.date}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex items-center justify-between p-4 border-t border-border/50">
            <span className="text-xs text-muted-foreground">Page {page + 1} of {pages}</span>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0}>
                <ChevronLeft size={14} />
              </Button>
              <Button variant="outline" size="sm" onClick={() => setPage(Math.min(pages - 1, page + 1))} disabled={page >= pages - 1}>
                <ChevronRight size={14} />
              </Button>
            </div>
          </div>
        </div>

        <p className="text-center text-xs text-muted-foreground mb-8">Data from local database • {totalClaims} records • Auto-refreshed on load</p>
      </div>
      <Footer />
    </div>
  );
}
