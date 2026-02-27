import { useState, useMemo } from "react";
import { Link } from "react-router-dom";
import Navbar from "@/components/Navbar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  Settings, Upload, Shield, Search, DollarSign, Scale, FileText,
  Bot, ChevronDown, ChevronUp, X, Image, Download, CheckCircle, AlertTriangle, XCircle
} from "lucide-react";
import {
  BASE_PRICES, LABOR_COST, INFLATION_FACTOR, CAR_MULTIPLIERS,
  DEMO_DETECTIONS, DEMO_FRAUD_RESULTS,
  type Detection, type FraudResult,
} from "@/data/mockData";
import { cn } from "@/lib/utils";
import { analyzeImages, downloadPDF, type AnalyzeResult } from "@/lib/api";

export default function ClaimEstimator() {
  // Sidebar state
  const [detectionMode, setDetectionMode] = useState<"simulation" | "huggingface" | "local">("simulation");
  const [confidence, setConfidence] = useState(40);
  const [carType, setCarType] = useState<string>("SUV");
  const [showPrices, setShowPrices] = useState(false);

  // Claim form state
  const [customerName, setCustomerName] = useState("");
  const [policyNumber, setPolicyNumber] = useState("");
  const [vehicleReg, setVehicleReg] = useState("");
  const [vehicleMake, setVehicleMake] = useState("");

  // Processing state
  const [images, setImages] = useState<{ name: string; url: string; file?: File }[]>([]);
  const [processing, setProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState(1); // 1=form, 2=upload, 3+=results
  const [fraudResults, setFraudResults] = useState<FraudResult[]>([]);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [downloaded, setDownloaded] = useState(false);
  const [apiResult, setApiResult] = useState<AnalyzeResult | null>(null);
  const [annotatedImages, setAnnotatedImages] = useState<string[]>([]);
  const [apiError, setApiError] = useState<string | null>(null);
  const [nlpExplanation, setNlpExplanation] = useState<string | null>(null);
  const [apiDecision, setApiDecision] = useState<AnalyzeResult["decision"] | null>(null);

  const multiplier = CAR_MULTIPLIERS[carType] || 1.0;
  const adjustedPrices = useMemo(() => {
    const p: Record<string, number> = {};
    Object.entries(BASE_PRICES).forEach(([k, v]) => {
      p[k] = Math.round(v * multiplier * INFLATION_FACTOR);
    });
    return p;
  }, [multiplier]);

  const handleFileUpload = (files: FileList | null) => {
    if (!files) return;
    const newImages = Array.from(files)
      .filter((f) => f.type.startsWith("image/"))
      .map((f) => ({ name: f.name, url: URL.createObjectURL(f), file: f }));
    setImages((prev) => [...prev, ...newImages]);
  };

  const loadDemo = () => {
    setImages([
      { name: "car_front_damage.jpg", url: "/placeholder.svg" },
      { name: "car_side_angle.jpg", url: "/placeholder.svg" },
    ]);
    setCustomerName("Divya Krishnan");
    setPolicyNumber("POL-2024-024");
    setVehicleReg("KA-01-AB-1234");
    setVehicleMake("Volkswagen Virtus");
    setCarType("Sedan");
  };

  const runAnalysis = async () => {
    if (images.length === 0) return;
    setProcessing(true);
    setApiError(null);
    try {
      const files = images.map((img) => img.file).filter(Boolean) as File[];
      const result = await analyzeImages({
        images: files,
        customerName: customerName,
        policyNumber: policyNumber,
        vehicleReg: vehicleReg,
        vehicleMake: vehicleMake,
        carType: carType,
        detectionMode: detectionMode,
        confidenceThreshold: confidence,
      });

      setApiResult(result);
      // Populate component state from API result
      setFraudResults(result.fraudSummary.results);
      setCurrentStep(3);
      setDetections(result.detections);
      setAnnotatedImages(result.annotatedImages);
      setNlpExplanation(result.nlpExplanation);
      setApiDecision(result.decision);
      setCurrentStep(8);
    } catch (err: any) {
      setApiError(err?.message || "Analysis failed. Make sure the Python backend is running.");
    } finally {
      setProcessing(false);
    }
  };

  // Cost calculations
  const costBreakdown = useMemo(() => {
    if (detections.length === 0) return [];
    return detections.map((d) => {
      const base = BASE_PRICES[d.part] || 2000;
      const sevMultiplier = d.severity === "Severe" ? 1.0 : d.severity === "Moderate" ? 0.7 : 0.4;
      const repairCost = Math.round(base * sevMultiplier * multiplier * INFLATION_FACTOR);
      const labor = Math.round(LABOR_COST * multiplier * INFLATION_FACTOR);
      const total = repairCost + labor;
      const recommendation = d.areaCoverage >= 30 ? "Replace" : "Repair";
      return { ...d, baseCost: base, repairCost, labor, total, recommendation };
    });
  }, [detections, multiplier]);

  const grandTotal = costBreakdown.reduce((s, c) => s + c.total, 0);
  const repairSubtotal = costBreakdown.reduce((s, c) => s + c.repairCost, 0);
  const laborTotal = costBreakdown.reduce((s, c) => s + c.labor, 0);
  const avgConfidence = detections.length > 0 ? Math.round(detections.reduce((s, d) => s + d.confidence, 0) / detections.length) : 0;

  const decision = useMemo(() => {
    // Use API decision status if available, else compute locally
    if (apiDecision) return apiDecision.status;
    if (detections.length === 0) return "";
    if (avgConfidence < 60) return "Manual Inspection";
    if (grandTotal <= 25000) return "Auto Approved";
    if (grandTotal <= 60000) return "Supervisor Review";
    return "Manual Inspection";
  }, [grandTotal, avgConfidence, detections, apiDecision]);

  const claimId = apiResult?.claimId ?? `CLM-20250227-A3F2B1`;

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="flex">
        {/* Sidebar */}
        <aside className="hidden lg:block w-[280px] min-h-[calc(100vh-4rem)] border-r border-border bg-card/50 p-5 overflow-y-auto scrollbar-thin">
          <h2 className="text-lg font-bold text-foreground flex items-center gap-2 mb-6">
            <Settings size={20} /> Settings
          </h2>

          {/* Detection Mode */}
          <div className="mb-6">
            <Label className="text-xs text-muted-foreground uppercase tracking-wider">Detection Mode</Label>
            <div className="mt-2 space-y-2">
              {[
                { value: "simulation", label: "🧠 Smart Simulation", sub: "Offline" },
                { value: "huggingface", label: "🤖 HuggingFace AI", sub: "Model" },
                { value: "local", label: "📂 Local YOLOv8", sub: "Model" },
              ].map((m) => (
                <button
                  key={m.value}
                  onClick={() => setDetectionMode(m.value as typeof detectionMode)}
                  className={cn(
                    "w-full text-left px-3 py-2 rounded-lg text-sm transition-all",
                    detectionMode === m.value
                      ? "bg-primary/15 border border-primary/40 text-foreground"
                      : "bg-secondary/50 border border-transparent text-muted-foreground hover:bg-secondary"
                  )}
                >
                  {m.label} <span className="text-xs text-muted-foreground">({m.sub})</span>
                </button>
              ))}
            </div>
            <div className={cn(
              "mt-2 text-xs px-2 py-1 rounded-md inline-block",
              detectionMode === "simulation" ? "bg-warning/20 text-warning" : "bg-success/20 text-success"
            )}>
              {detectionMode === "simulation" ? "⚡ Simulation Mode" : "✅ AI Model Active"}
            </div>
          </div>

          {/* Confidence */}
          <div className="mb-6">
            <Label className="text-xs text-muted-foreground uppercase tracking-wider">Min Confidence</Label>
            <Slider
              value={[confidence]}
              onValueChange={(v) => setConfidence(v[0])}
              min={10} max={95} step={5}
              disabled={detectionMode === "simulation"}
              className="mt-3"
            />
            <div className="text-right text-xs text-primary font-medium mt-1">{confidence}%</div>
          </div>

          {/* Vehicle Class */}
          <div className="mb-6">
            <Label className="text-xs text-muted-foreground uppercase tracking-wider">Vehicle Class</Label>
            <Select value={carType} onValueChange={setCarType}>
              <SelectTrigger className="mt-2"><SelectValue /></SelectTrigger>
              <SelectContent>
                {Object.entries(CAR_MULTIPLIERS).map(([k, v]) => (
                  <SelectItem key={k} value={k}>{k} ({v}×)</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <div className="mt-1 text-xs text-primary">Multiplier: {multiplier}×</div>
          </div>

          {/* Base Prices */}
          <div className="mb-6">
            <button
              onClick={() => setShowPrices(!showPrices)}
              className="flex items-center gap-2 text-xs text-muted-foreground uppercase tracking-wider w-full"
            >
              📊 Parts Base Prices {showPrices ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>
            {showPrices && (
              <div className="mt-2 glass-card p-3">
                <table className="w-full text-xs">
                  <thead><tr><th className="text-left text-muted-foreground">Part</th><th className="text-right text-muted-foreground">Adjusted</th></tr></thead>
                  <tbody>
                    {Object.entries(adjustedPrices).map(([k, v]) => (
                      <tr key={k} className="border-t border-border/50">
                        <td className="py-1 text-foreground">{k}</td>
                        <td className="py-1 text-right text-foreground">₹{v.toLocaleString()}</td>
                      </tr>
                    ))}
                    <tr className="border-t border-border/50">
                      <td className="py-1 text-foreground">Labor/part</td>
                      <td className="py-1 text-right text-foreground">₹{Math.round(LABOR_COST * multiplier * INFLATION_FACTOR).toLocaleString()}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Decision Thresholds */}
          <div>
            <Label className="text-xs text-muted-foreground uppercase tracking-wider">⚖️ Decision Thresholds</Label>
            <div className="mt-2 glass-card p-3 text-xs space-y-1">
              <div className="flex justify-between"><span className="text-success">✅ Auto</span><span className="text-muted-foreground">≤ ₹25,000</span></div>
              <div className="flex justify-between"><span className="text-warning">⚠️ Supervisor</span><span className="text-muted-foreground">₹25K–₹60K</span></div>
              <div className="flex justify-between"><span className="text-destructive">🔴 Manual</span><span className="text-muted-foreground">&gt; ₹60,000</span></div>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-6 md:p-8 overflow-y-auto scrollbar-thin max-w-4xl">
          {/* Step 1: Claim Info */}
          <section className="mb-8 animate-fade-in">
            <h2 className="text-xl font-bold text-foreground mb-4 flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-primary/20 flex items-center justify-center text-xs text-primary font-bold">1</div>
              Claim Information
            </h2>
            <div className="glass-card p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div><Label className="text-muted-foreground text-sm">Customer Name</Label><Input className="mt-1" value={customerName} onChange={(e) => setCustomerName(e.target.value)} placeholder="Enter name" /></div>
              <div><Label className="text-muted-foreground text-sm">Policy Number</Label><Input className="mt-1" value={policyNumber} onChange={(e) => setPolicyNumber(e.target.value)} placeholder="POL-XXXX-XXX" /></div>
              <div><Label className="text-muted-foreground text-sm">Vehicle Reg. No.</Label><Input className="mt-1" value={vehicleReg} onChange={(e) => setVehicleReg(e.target.value)} placeholder="XX-00-XX-0000" /></div>
              <div><Label className="text-muted-foreground text-sm">Vehicle Make/Model</Label><Input className="mt-1" value={vehicleMake} onChange={(e) => setVehicleMake(e.target.value)} placeholder="e.g. Honda City" /></div>
            </div>
          </section>

          {/* Step 2: Upload Images */}
          <section className="mb-8 animate-fade-in" style={{ animationDelay: "0.1s" }}>
            <h2 className="text-xl font-bold text-foreground mb-4 flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-primary/20 flex items-center justify-center text-xs text-primary font-bold">2</div>
              Upload Images
            </h2>
            <div className="glass-card p-6">
              <label
                className="border-2 border-dashed border-border rounded-xl p-10 text-center hover:border-primary/40 transition-colors block cursor-pointer"
                onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); }}
                onDrop={(e) => { e.preventDefault(); e.stopPropagation(); handleFileUpload(e.dataTransfer.files); }}
              >
                <Upload className="mx-auto text-muted-foreground mb-3" size={40} />
                <p className="text-foreground font-medium">Drop car damage photos here or click to browse</p>
                <p className="text-xs text-muted-foreground mt-1">JPG, PNG, WEBP supported • Multiple angles recommended</p>
                <input type="file" accept="image/*" multiple className="hidden" onChange={(e) => handleFileUpload(e.target.files)} />
              </label>
              <Button variant="outline" className="mt-4" onClick={loadDemo}>
                <Image size={16} className="mr-2" /> 🖼️ Load Demo Image
              </Button>

              {images.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-3">
                  {images.map((img, i) => (
                    <div key={i} className="glass-card p-3 flex items-center gap-3">
                      <img src={img.url} alt={img.name} className="w-12 h-12 rounded-md object-cover" />
                      <span className="text-sm text-foreground">{img.name}</span>
                      <button onClick={() => setImages(images.filter((_, j) => j !== i))} className="text-muted-foreground hover:text-destructive">
                        <X size={16} />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {images.length > 0 && currentStep < 3 && (
                <Button className="mt-4" onClick={runAnalysis} disabled={processing}>
                  {processing ? "Analyzing..." : "🔍 Run Analysis"}
                </Button>
              )}
            </div>
          </section>

          {/* Step 3: Fraud Analysis */}
          {currentStep >= 3 && (
            <section className="mb-8 animate-fade-in">
              <h2 className="text-xl font-bold text-foreground mb-4 flex items-center gap-2">
                <div className="w-7 h-7 rounded-full bg-primary/20 flex items-center justify-center text-xs text-primary font-bold">3</div>
                🛡️ Fraud Analysis
              </h2>
              <div className={cn("glass-card p-4 mb-4 border", "bg-success/10 border-success/30")}>
                <span className="text-success font-medium">✅ Fraud Risk: Low — 0/{images.length} images flagged</span>

              </div>
              <div className="space-y-3">
                {fraudResults.map((f, i) => (
                  <div key={i} className="glass-card p-4">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-10 h-10 rounded-md bg-primary/10 flex items-center justify-center"><Image size={18} className="text-primary" /></div>
                      <span className="text-sm font-medium text-foreground">{f.filename}</span>
                      <span className="ml-auto text-xs px-2 py-0.5 rounded-full bg-success/20 text-success">{f.riskLevel}</span>
                    </div>
                    <div className="space-y-1 text-sm">
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <span>MD5 Hash:</span>
                        <span className="text-success">✅ Unique</span>
                      </div>
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <span>Blur Score:</span>
                        <span className={f.isSharp ? "text-success" : "text-warning"}>{f.blurScore} — {f.isSharp ? "✅ Sharp" : "⚠️ Blurry"}</span>
                      </div>
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <span>EXIF Data:</span>
                        <span className="text-foreground">📅 Captured: {f.exifDate || "N/A"}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Step 4: Damage Detection */}
          {currentStep >= 4 && detections.length > 0 && (
            <section className="mb-8 animate-fade-in">
              <h2 className="text-xl font-bold text-foreground mb-4 flex items-center gap-2">
                <div className="w-7 h-7 rounded-full bg-primary/20 flex items-center justify-center text-xs text-primary font-bold">4</div>
                🔍 Damage Detection
              </h2>
              {images.filter((_, i) => !fraudResults[i]?.isDuplicate).map((img, idx) => (
                <div key={idx} className="glass-card p-4 mb-4">
                  <Tabs defaultValue="detections">
                    <TabsList className="mb-4">
                      <TabsTrigger value="detections">Detections</TabsTrigger>
                      <TabsTrigger value="heatmap">Heatmap</TabsTrigger>
                      <TabsTrigger value="original">Original</TabsTrigger>
                    </TabsList>
                    <TabsContent value="detections">
                      <div className="relative bg-secondary/30 rounded-lg h-48 mb-4 flex items-center justify-center overflow-hidden">
                        <img src={img.url} alt={img.name} className="absolute inset-0 w-full h-full object-cover opacity-40" />
                        <div className="absolute top-4 left-6 w-32 h-20 border-2 border-destructive/70 rounded" />
                        <div className="absolute top-6 right-10 w-16 h-16 border-2 border-warning/70 rounded" />
                        <div className="absolute bottom-8 left-20 w-24 h-6 border-2 border-success/70 rounded" />
                        <span className="text-muted-foreground text-sm z-10">{img.name} — annotated</span>
                      </div>
                      <span className="text-xs bg-primary/20 text-primary px-2 py-1 rounded-full">{detections.length} zones detected</span>
                      <table className="w-full text-sm mt-4">
                        <thead><tr className="text-muted-foreground text-xs">
                          <th className="text-left pb-2">Part</th><th>Severity</th><th>Score</th><th>Confidence</th><th>Area</th>
                        </tr></thead>
                        <tbody>
                          {detections.map((d, i) => (
                            <tr key={i} className="border-t border-border/50 text-foreground">
                              <td className="py-2">{d.part}</td>
                              <td className="text-center"><span className={cn("text-xs px-2 py-0.5 rounded-full",
                                d.severity === "Severe" ? "bg-destructive/20 text-destructive" :
                                  d.severity === "Moderate" ? "bg-warning/20 text-warning" : "bg-success/20 text-success"
                              )}>{d.severity}</span></td>
                              <td className="text-center">{d.score}/10</td>
                              <td className="text-center">{d.confidence}%</td>
                              <td className="text-center">{d.areaCoverage}%</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </TabsContent>
                    <TabsContent value="heatmap">
                      <div className="relative bg-secondary/30 rounded-lg h-48 flex items-center justify-center">
                        <img src={img.url} alt={img.name} className="absolute inset-0 w-full h-full object-cover opacity-30" />
                        <div className="absolute top-4 left-6 w-32 h-20 bg-destructive/30 rounded" />
                        <div className="absolute top-6 right-10 w-16 h-16 bg-warning/30 rounded" />
                        <div className="absolute bottom-8 left-20 w-24 h-6 bg-success/30 rounded" />
                        <span className="text-muted-foreground text-sm z-10">{img.name} — heatmap</span>
                      </div>
                      <div className="flex gap-4 mt-3 text-xs text-muted-foreground">
                        <span>🟢 Minor</span><span>🟡 Moderate</span><span>🔴 Severe</span>
                      </div>
                    </TabsContent>
                    <TabsContent value="original">
                      <div className="bg-secondary/30 rounded-lg h-48 flex items-center justify-center overflow-hidden relative">
                        <img src={img.url} alt={img.name} className="absolute inset-0 w-full h-full object-cover" />
                        <span className="text-muted-foreground text-sm z-10 bg-background/60 px-2 py-1 rounded">{img.name} — original</span>
                      </div>
                    </TabsContent>
                  </Tabs>
                </div>
              ))}
              {images.length >= 2 && (
                <div className="glass-card p-4 border border-primary/20 bg-primary/5 text-sm text-muted-foreground">
                  🔗 <strong className="text-foreground">Multi-Image Aggregation:</strong> 6 raw detections across {images.length} images → merged into {detections.length} unique damaged parts. Duplicate detections averaged; highest confidence kept.
                </div>
              )}
            </section>
          )}

          {/* Step 5: Cost Estimation */}
          {currentStep >= 5 && costBreakdown.length > 0 && (
            <section className="mb-8 animate-fade-in">
              <h2 className="text-xl font-bold text-foreground mb-4 flex items-center gap-2">
                <div className="w-7 h-7 rounded-full bg-primary/20 flex items-center justify-center text-xs text-primary font-bold">5</div>
                💰 Cost Estimation
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
                {[
                  { label: "Parts Damaged", value: costBreakdown.length },
                  { label: "Repair Cost", value: `₹${repairSubtotal.toLocaleString()}` },
                  { label: "Labor Cost", value: `₹${laborTotal.toLocaleString()}` },
                  { label: "Grand Total", value: `₹${grandTotal.toLocaleString()}` },
                ].map((kpi, i) => (
                  <div key={i} className="glass-card p-4 text-center">
                    <div className="text-xs text-muted-foreground mb-1">{kpi.label}</div>
                    <div className="text-lg font-bold text-foreground">{kpi.value}</div>
                  </div>
                ))}
              </div>
              <div className="glass-card overflow-hidden">
                <table className="w-full text-sm">
                  <thead><tr className="text-xs text-muted-foreground bg-secondary/30">
                    <th className="text-left p-3">Part</th><th>Severity</th><th className="hidden md:table-cell">Base</th><th>Repair + Labor</th><th>Total</th><th>Rec.</th>
                  </tr></thead>
                  <tbody>
                    {costBreakdown.map((c, i) => (
                      <tr key={i} className="border-t border-border/50 text-foreground">
                        <td className="p-3">{c.part}</td>
                        <td className="text-center"><span className={cn("text-xs px-2 py-0.5 rounded-full",
                          c.severity === "Severe" ? "bg-destructive/20 text-destructive" :
                            c.severity === "Moderate" ? "bg-warning/20 text-warning" : "bg-success/20 text-success"
                        )}>{c.severity}</span></td>
                        <td className="text-center hidden md:table-cell">₹{c.baseCost.toLocaleString()}</td>
                        <td className="text-center">₹{c.repairCost.toLocaleString()} + ₹{c.labor.toLocaleString()}</td>
                        <td className="text-center font-medium">₹{c.total.toLocaleString()}</td>
                        <td className="text-center">
                          <span className={cn("text-xs px-2 py-0.5 rounded-full",
                            c.recommendation === "Replace" ? "bg-destructive/20 text-destructive" : "bg-success/20 text-success"
                          )}>
                            {c.recommendation === "Replace" ? "🔄 Replace" : "🔧 Repair"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {/* Step 6: Claim Decision */}
          {currentStep >= 6 && decision && (
            <section className="mb-8 animate-fade-in">
              <h2 className="text-xl font-bold text-foreground mb-4 flex items-center gap-2">
                <div className="w-7 h-7 rounded-full bg-primary/20 flex items-center justify-center text-xs text-primary font-bold">6</div>
                ⚖️ Claim Decision
              </h2>
              <div className={cn("glass-card p-6 text-center border-2",
                decision === "Auto Approved" ? "border-success/40 bg-success/10" :
                  decision === "Supervisor Review" ? "border-warning/40 bg-warning/10" :
                    "border-destructive/40 bg-destructive/10"
              )}>
                <div className="text-2xl font-bold mb-2">
                  {decision === "Auto Approved" && <span className="text-success">Auto Approved ✅</span>}
                  {decision === "Supervisor Review" && <span className="text-warning">Supervisor Review ⚠️</span>}
                  {decision === "Manual Inspection" && <span className="text-destructive">Manual Inspection Required 🔴</span>}
                </div>
                {avgConfidence < 60 && (
                  <div className="mt-3 glass-card p-3 bg-warning/10 border border-warning/30 text-sm text-warning">
                    ⚠️ Responsible AI Override: Average detection confidence was {avgConfidence}%, below the 60% threshold. Escalated to manual review.
                  </div>
                )}
                <p className="text-sm text-muted-foreground mt-2">
                  Total claim value: ₹{grandTotal.toLocaleString()} | Avg confidence: {avgConfidence}%
                </p>
              </div>
            </section>
          )}

          {/* API Error banner */}
          {apiError && (
            <div className="glass-card p-4 mb-4 border border-destructive/40 bg-destructive/10 text-destructive text-sm">
              ⚠️ {apiError}
            </div>
          )}

          {/* Step 7: AI Explanation */}
          {currentStep >= 7 && costBreakdown.length > 0 && (
            <section className="mb-8 animate-fade-in">
              <h2 className="text-xl font-bold text-foreground mb-4 flex items-center gap-2">
                <div className="w-7 h-7 rounded-full bg-primary/20 flex items-center justify-center text-xs text-primary font-bold">7</div>
                🤖 AI Explanation
              </h2>
              <div className="glass-card p-6 font-mono text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed bg-background/60">
                {`📋 DAMAGE ASSESSMENT
────────────────────────────────────────
• Bumper: The bumper has sustained severe structural damage covering approximately 43% of the inspected surface. Deep deformation and cracking observed.
• Headlight: The headlight shows moderate deformation with 22% area coverage. Lens cracking and housing misalignment detected.
• Scratch: The panel shows minor surface abrasions covering 8% of the area. Paint damage only, no structural compromise.

💰 COST REASONING
────────────────────────────────────────
• Bumper (Severe): Base ₹6,000 × 100% × ${multiplier} × 1.05 = ₹${costBreakdown[0]?.repairCost.toLocaleString()} + ₹${costBreakdown[0]?.labor.toLocaleString()} labor
• Headlight (Moderate): Base ₹3,500 × 70% × ${multiplier} × 1.05 = ₹${costBreakdown[1]?.repairCost.toLocaleString()} + ₹${costBreakdown[1]?.labor.toLocaleString()} labor
• Scratch (Minor): Base ₹1,500 × 40% × ${multiplier} × 1.05 = ₹${costBreakdown[2]?.repairCost.toLocaleString()} + ₹${costBreakdown[2]?.labor.toLocaleString()} labor

⚖️ CLAIM DECISION JUSTIFICATION
────────────────────────────────────────
Decision: ${decision}
The claim value of ₹${grandTotal.toLocaleString()} ${decision === "Supervisor Review" ? "falls between ₹25,000 and ₹60,000, requiring supervisor approval." : decision === "Auto Approved" ? "is below ₹25,000, qualifying for automatic approval." : "exceeds ₹60,000, requiring manual inspection."}

📝 SUMMARY
────────────────────────────────────────
The AI inspection identified damage to ${costBreakdown.length} vehicle components with a combined repair estimate of ₹${grandTotal.toLocaleString()}. Vehicle class: ${carType} (${multiplier}× multiplier).`}
              </div>
            </section>
          )}

          {/* Step 8: Download Report */}
          {currentStep >= 8 && (
            <section className="mb-8 animate-fade-in">
              <h2 className="text-xl font-bold text-foreground mb-4 flex items-center gap-2">
                <div className="w-7 h-7 rounded-full bg-primary/20 flex items-center justify-center text-xs text-primary font-bold">8</div>
                📄 Download Report
              </h2>
              <div className="glass-card p-6 text-center">
                {customerName && policyNumber && (
                  <div className="text-sm text-success mb-4 flex items-center justify-center gap-2">
                    <CheckCircle size={16} /> Claim metadata included in PDF
                  </div>
                )}
                <Button
                  variant="success" size="lg"
                  onClick={async () => {
                    if (apiResult) {
                      await downloadPDF(apiResult, { customerName, policyNumber, vehicleReg, vehicleMake, carType });
                    }
                    setDownloaded(true);
                  }}
                >
                  <Download size={18} className="mr-2" /> Download PDF Report
                </Button>
                {downloaded && (
                  <div className="mt-4 text-sm text-success">
                    ✅ Claim {claimId} saved to history.{" "}
                    <Link to="/analytics" className="text-primary hover:underline">View in Analytics Dashboard →</Link>
                  </div>
                )}
              </div>
            </section>
          )}
        </main>
      </div>
    </div>
  );
}
