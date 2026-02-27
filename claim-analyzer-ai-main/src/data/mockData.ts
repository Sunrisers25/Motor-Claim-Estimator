export interface ClaimRecord {
  id: string;
  customer: string;
  policyNo: string;
  vehicle: string;
  carType: "Hatchback" | "Sedan" | "SUV" | "Luxury";
  totalCost: number;
  decision: "Auto Approved" | "Supervisor Review" | "Manual Inspection";
  date: string;
  partsCount: number;
}

export interface Detection {
  part: string;
  severity: "Minor" | "Moderate" | "Severe";
  score: number;
  confidence: number;
  areaCoverage: number;
}

export interface FraudResult {
  filename: string;
  md5: string;
  isDuplicate: boolean;
  duplicateOf?: string;
  blurScore: number;
  isSharp: boolean;
  exifDate?: string;
  riskLevel: "Low" | "Medium" | "High";
}

export const BASE_PRICES: Record<string, number> = {
  Bumper: 6000,
  Headlight: 3500,
  Door: 8000,
  Windshield: 7000,
  Hood: 9000,
  Scratch: 1500,
  Dent: 2500,
};

export const LABOR_COST = 2000;
export const INFLATION_FACTOR = 1.05;

export const CAR_MULTIPLIERS: Record<string, number> = {
  Hatchback: 1.0,
  Sedan: 1.1,
  SUV: 1.3,
  Luxury: 1.8,
};

export const DEMO_DETECTIONS: Detection[] = [
  { part: "Bumper", severity: "Severe", score: 8, confidence: 85, areaCoverage: 43 },
  { part: "Headlight", severity: "Moderate", score: 6, confidence: 78, areaCoverage: 22 },
  { part: "Scratch", severity: "Minor", score: 3, confidence: 71, areaCoverage: 8 },
];

export const DEMO_FRAUD_RESULTS: FraudResult[] = [
  {
    filename: "car_front_damage.jpg",
    md5: "a3f2b1c4d5e6f7890123456789abcdef",
    isDuplicate: false,
    blurScore: 142.3,
    isSharp: true,
    exifDate: "2025-01-15 14:32",
    riskLevel: "Low",
  },
  {
    filename: "car_side_angle.jpg",
    md5: "b4c3d2e1f0a9876543210fedcba98765",
    isDuplicate: false,
    blurScore: 98.7,
    isSharp: true,
    exifDate: "2025-01-15 14:33",
    riskLevel: "Low",
  },
];

export const MOCK_CLAIMS: ClaimRecord[] = [
  { id: "CLM-20250101-A1B2C3", customer: "Rajesh Kumar", policyNo: "POL-2024-001", vehicle: "Maruti Swift", carType: "Hatchback", totalCost: 18500, decision: "Auto Approved", date: "2025-01-01", partsCount: 2 },
  { id: "CLM-20250105-D4E5F6", customer: "Priya Sharma", policyNo: "POL-2024-002", vehicle: "Honda City", carType: "Sedan", totalCost: 42300, decision: "Supervisor Review", date: "2025-01-05", partsCount: 3 },
  { id: "CLM-20250108-G7H8I9", customer: "Amit Patel", policyNo: "POL-2024-003", vehicle: "Hyundai Creta", carType: "SUV", totalCost: 67800, decision: "Manual Inspection", date: "2025-01-08", partsCount: 4 },
  { id: "CLM-20250112-J0K1L2", customer: "Sneha Reddy", policyNo: "POL-2024-004", vehicle: "Tata Nexon", carType: "SUV", totalCost: 23100, decision: "Auto Approved", date: "2025-01-12", partsCount: 2 },
  { id: "CLM-20250115-M3N4O5", customer: "Vikram Singh", policyNo: "POL-2024-005", vehicle: "BMW 3 Series", carType: "Luxury", totalCost: 95400, decision: "Manual Inspection", date: "2025-01-15", partsCount: 5 },
  { id: "CLM-20250118-P6Q7R8", customer: "Ananya Gupta", policyNo: "POL-2024-006", vehicle: "Maruti Baleno", carType: "Hatchback", totalCost: 12800, decision: "Auto Approved", date: "2025-01-18", partsCount: 1 },
  { id: "CLM-20250120-S9T0U1", customer: "Rohit Joshi", policyNo: "POL-2024-007", vehicle: "Honda Amaze", carType: "Sedan", totalCost: 35600, decision: "Supervisor Review", date: "2025-01-20", partsCount: 3 },
  { id: "CLM-20250123-V2W3X4", customer: "Meera Nair", policyNo: "POL-2024-008", vehicle: "Kia Seltos", carType: "SUV", totalCost: 28900, decision: "Supervisor Review", date: "2025-01-23", partsCount: 2 },
  { id: "CLM-20250125-Y5Z6A7", customer: "Suresh Iyer", policyNo: "POL-2024-009", vehicle: "Tata Altroz", carType: "Hatchback", totalCost: 15200, decision: "Auto Approved", date: "2025-01-25", partsCount: 2 },
  { id: "CLM-20250128-B8C9D0", customer: "Kavita Desai", policyNo: "POL-2024-010", vehicle: "Hyundai Verna", carType: "Sedan", totalCost: 51200, decision: "Supervisor Review", date: "2025-01-28", partsCount: 4 },
  { id: "CLM-20250201-E1F2G3", customer: "Arun Mehta", policyNo: "POL-2024-011", vehicle: "Mercedes C-Class", carType: "Luxury", totalCost: 112000, decision: "Manual Inspection", date: "2025-02-01", partsCount: 5 },
  { id: "CLM-20250203-H4I5J6", customer: "Deepika Rao", policyNo: "POL-2024-012", vehicle: "Maruti Dzire", carType: "Sedan", totalCost: 19800, decision: "Auto Approved", date: "2025-02-03", partsCount: 2 },
  { id: "CLM-20250206-K7L8M9", customer: "Nikhil Verma", policyNo: "POL-2024-013", vehicle: "Mahindra XUV700", carType: "SUV", totalCost: 44500, decision: "Supervisor Review", date: "2025-02-06", partsCount: 3 },
  { id: "CLM-20250208-N0O1P2", customer: "Pooja Kapoor", policyNo: "POL-2024-014", vehicle: "Toyota Fortuner", carType: "SUV", totalCost: 72100, decision: "Manual Inspection", date: "2025-02-08", partsCount: 4 },
  { id: "CLM-20250211-Q3R4S5", customer: "Manish Tiwari", policyNo: "POL-2024-015", vehicle: "Hyundai i20", carType: "Hatchback", totalCost: 9500, decision: "Auto Approved", date: "2025-02-11", partsCount: 1 },
  { id: "CLM-20250214-T6U7V8", customer: "Ritu Saxena", policyNo: "POL-2024-016", vehicle: "Honda City", carType: "Sedan", totalCost: 38700, decision: "Supervisor Review", date: "2025-02-14", partsCount: 3 },
  { id: "CLM-20250216-W9X0Y1", customer: "Sanjay Mishra", policyNo: "POL-2024-017", vehicle: "Tata Harrier", carType: "SUV", totalCost: 55300, decision: "Supervisor Review", date: "2025-02-16", partsCount: 3 },
  { id: "CLM-20250218-Z2A3B4", customer: "Lakshmi Pillai", policyNo: "POL-2024-018", vehicle: "Audi A4", carType: "Luxury", totalCost: 89600, decision: "Manual Inspection", date: "2025-02-18", partsCount: 4 },
  { id: "CLM-20250220-C5D6E7", customer: "Gaurav Chopra", policyNo: "POL-2024-019", vehicle: "Maruti Wagon R", carType: "Hatchback", totalCost: 11200, decision: "Auto Approved", date: "2025-02-20", partsCount: 1 },
  { id: "CLM-20250222-F8G9H0", customer: "Swati Jain", policyNo: "POL-2024-020", vehicle: "Skoda Slavia", carType: "Sedan", totalCost: 31400, decision: "Supervisor Review", date: "2025-02-22", partsCount: 2 },
  { id: "CLM-20250224-I1J2K3", customer: "Prakash Bhat", policyNo: "POL-2024-021", vehicle: "Kia Sonet", carType: "SUV", totalCost: 21500, decision: "Auto Approved", date: "2025-02-24", partsCount: 2 },
  { id: "CLM-20250225-L4M5N6", customer: "Nandini Menon", policyNo: "POL-2024-022", vehicle: "Tata Tiago", carType: "Hatchback", totalCost: 14300, decision: "Auto Approved", date: "2025-02-25", partsCount: 2 },
  { id: "CLM-20250226-O7P8Q9", customer: "Ashok Rangan", policyNo: "POL-2024-023", vehicle: "MG Hector", carType: "SUV", totalCost: 47800, decision: "Supervisor Review", date: "2025-02-26", partsCount: 3 },
  { id: "CLM-20250227-R0S1T2", customer: "Divya Krishnan", policyNo: "POL-2024-024", vehicle: "Volkswagen Virtus", carType: "Sedan", totalCost: 40950, decision: "Supervisor Review", date: "2025-02-27", partsCount: 3 },
];

export const getDecisionColor = (decision: string) => {
  switch (decision) {
    case "Auto Approved": return "text-success";
    case "Supervisor Review": return "text-warning";
    case "Manual Inspection": return "text-destructive";
    default: return "text-muted-foreground";
  }
};

export const getDecisionBg = (decision: string) => {
  switch (decision) {
    case "Auto Approved": return "bg-success/10 border-success/30";
    case "Supervisor Review": return "bg-warning/10 border-warning/30";
    case "Manual Inspection": return "bg-destructive/10 border-destructive/30";
    default: return "bg-muted";
  }
};
