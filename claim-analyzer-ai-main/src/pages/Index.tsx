import { Suspense } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import HeroScene from "@/components/HeroScene";
import {
  motion,
  useScroll,
  useTransform,
} from "framer-motion";
import {
  ArrowRight, Upload, Shield, Search, DollarSign, Scale, FileText,
  Clock, IndianRupee, AlertTriangle, Sparkles, BarChart3, Car, Wrench, Eye, Bot
} from "lucide-react";
import AnimatedCounter from "@/components/AnimatedCounter";

// Animation variants
const easeOut = [0.22, 1, 0.36, 1] as const;

const fadeUp = {
  hidden: { opacity: 0, y: 40 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.6, ease: easeOut as unknown as [number, number, number, number] },
  }),
};

const scaleIn = {
  hidden: { opacity: 0, scale: 0.85 },
  visible: (i: number) => ({
    opacity: 1,
    scale: 1,
    transition: { delay: i * 0.08, duration: 0.5, ease: easeOut as unknown as [number, number, number, number] },
  }),
};

const slideInLeft = {
  hidden: { opacity: 0, x: -60 },
  visible: (i: number) => ({
    opacity: 1,
    x: 0,
    transition: { delay: i * 0.1, duration: 0.6, ease: easeOut as unknown as [number, number, number, number] },
  }),
};

const slideInRight = {
  hidden: { opacity: 0, x: 60 },
  visible: (i: number) => ({
    opacity: 1,
    x: 0,
    transition: { delay: i * 0.1, duration: 0.6, ease: easeOut as unknown as [number, number, number, number] },
  }),
};

const statCards = [
  { label: "30 sec processing", delay: 0 },
  { label: "85–95% accuracy", delay: 1 },
  { label: "₹45K Cr fraud prevented", delay: 2 },
];

const problemStats = [
  { icon: Clock, value: "3–15 Days", desc: "Average manual claim time", numValue: 15, prefix: "3–", suffix: " Days" },
  { icon: IndianRupee, value: "₹8,000", desc: "Cost per manual inspection", numValue: 8000, prefix: "₹", suffix: "" },
  { icon: AlertTriangle, value: "₹45,000 Cr", desc: "Annual fraud losses in India", numValue: 45000, prefix: "₹", suffix: " Cr" },
];

const steps = [
  { icon: Upload, label: "Upload Photos", desc: "Drag & drop vehicle images", num: 1 },
  { icon: Shield, label: "Fraud Check", desc: "Hash, blur, EXIF analysis", num: 2 },
  { icon: Search, label: "AI Detection", desc: "YOLOv8 — 7 damage types", num: 3 },
  { icon: DollarSign, label: "Cost Engine", desc: "Severity × type × inflation", num: 4 },
  { icon: Scale, label: "Claim Decision", desc: "Auto / supervisor / manual", num: 5 },
  { icon: FileText, label: "PDF Report", desc: "Saved to analytics", num: 6 },
];

const features = [
  { icon: Search, title: "AI Damage Detection", desc: "Detects bumper, headlight, door, windshield, hood, scratch, dent with bounding boxes" },
  { icon: Shield, title: "Fraud Detection", desc: "MD5 duplicate check, blur scoring, EXIF metadata analysis" },
  { icon: Wrench, title: "Repair vs Replace", desc: "Area-based logic: <30% repair, ≥30% replace" },
  { icon: Car, title: "Car Type Pricing", desc: "Hatchback/Sedan/SUV/Luxury multipliers + inflation factor" },
  { icon: Bot, title: "AI Explanation", desc: "Natural language damage and cost reasoning per part" },
  { icon: BarChart3, title: "Analytics Dashboard", desc: "Claim history, approval rates, cost trends in real-time" },
];

export default function Index() {
  const { scrollYProgress } = useScroll();
  const heroOpacity = useTransform(scrollYProgress, [0, 0.15], [1, 0]);
  const heroScale = useTransform(scrollYProgress, [0, 0.15], [1, 0.95]);

  return (
    <div className="min-h-screen bg-background overflow-x-hidden">
      <Navbar />

      {/* Hero */}
      <motion.section
        className="relative overflow-hidden min-h-[90vh] flex items-center"
        style={{ opacity: heroOpacity, scale: heroScale }}
      >
        <div className="absolute inset-0 gradient-mesh" />
        <Suspense fallback={null}>
          <HeroScene />
        </Suspense>
        <div className="container relative z-10 py-20 md:py-32 text-center">
          <motion.h1
            className="text-4xl md:text-6xl lg:text-7xl font-extrabold text-foreground mb-6"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          >
            Settle Motor Claims in{" "}
            <motion.span
              className="gradient-text"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.4, duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
            >
              30 Seconds
            </motion.span>
          </motion.h1>
          <motion.p
            className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-10"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.6 }}
          >
            AI-powered damage detection, fraud prevention, and instant cost estimation — no manual assessors, no waiting.
          </motion.p>
          <motion.div
            className="flex flex-col sm:flex-row gap-4 justify-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.6 }}
          >
            <Button variant="hero" size="xl" asChild>
              <Link to="/claim">Start a Claim <ArrowRight className="ml-1" /></Link>
            </Button>
            <Button variant="hero-outline" size="xl" asChild>
              <Link to="/analytics">View Analytics</Link>
            </Button>
          </motion.div>

          {/* Floating stat cards */}
          <div className="flex flex-wrap justify-center gap-6">
            {statCards.map((s, i) => (
              <motion.div
                key={i}
                className="glass-card px-6 py-3 text-sm font-medium text-foreground"
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.7 + i * 0.15, duration: 0.5 }}
                whileHover={{ scale: 1.05, boxShadow: "0 0 30px hsl(217.2 91.2% 59.8% / 0.2)" }}
              >
                <Sparkles className="inline mr-2 text-primary" size={16} />
                {s.label}
              </motion.div>
            ))}
          </div>
        </div>

        {/* Scroll indicator */}
        <motion.div
          className="absolute bottom-8 left-1/2 -translate-x-1/2 z-10"
          animate={{ y: [0, 10, 0] }}
          transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
        >
          <div className="w-6 h-10 rounded-full border-2 border-muted-foreground/40 flex items-start justify-center p-1.5">
            <motion.div
              className="w-1.5 h-1.5 rounded-full bg-primary"
              animate={{ y: [0, 16, 0] }}
              transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
            />
          </div>
        </motion.div>
      </motion.section>

      {/* Problem Stats */}
      <section className="container py-20">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {problemStats.map((s, i) => (
            <motion.div
              key={i}
              className="glass-card p-8 text-center hover-lift cursor-default"
              custom={i}
              variants={fadeUp}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              whileHover={{ y: -8, boxShadow: "0 20px 40px -15px hsl(217.2 91.2% 59.8% / 0.15)" }}
            >
              <motion.div
                initial={{ scale: 0 }}
                whileInView={{ scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 + 0.2, type: "spring", stiffness: 200 }}
              >
                <s.icon className="mx-auto mb-4 text-destructive" size={36} />
              </motion.div>
              <div className="text-3xl font-bold text-foreground mb-1">
                <AnimatedCounter value={s.numValue} prefix={s.prefix} suffix={s.suffix} />
              </div>
              <div className="text-sm text-muted-foreground">{s.desc}</div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* How It Works */}
      <section className="container py-20">
        <motion.h2
          className="text-3xl md:text-4xl font-bold text-foreground text-center mb-4"
          variants={fadeUp}
          custom={0}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.5 }}
        >
          How It Works
        </motion.h2>
        <motion.p
          className="text-muted-foreground text-center mb-14 max-w-xl mx-auto"
          variants={fadeUp}
          custom={1}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.5 }}
        >
          From upload to decision in 6 streamlined steps
        </motion.p>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {steps.map((s) => (
            <motion.div
              key={s.num}
              className="glass-card p-5 text-center group cursor-default relative overflow-hidden"
              custom={s.num}
              variants={scaleIn}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.3 }}
              whileHover={{ scale: 1.08, boxShadow: "0 15px 35px -10px hsl(217.2 91.2% 59.8% / 0.2)" }}
            >
              <motion.div
                className="absolute inset-0 bg-gradient-to-br from-primary/10 to-accent/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
              />
              <div className="relative z-10">
                <motion.div
                  className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center mx-auto mb-3 group-hover:bg-primary/30 transition-colors"
                  whileHover={{ rotate: 360 }}
                  transition={{ duration: 0.6 }}
                >
                  <s.icon className="text-primary" size={22} />
                </motion.div>
                <div className="text-xs text-muted-foreground mb-1">Step {s.num}</div>
                <div className="text-sm font-semibold text-foreground mb-1">{s.label}</div>
                <div className="text-xs text-muted-foreground hidden lg:block">{s.desc}</div>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="container py-20">
        <motion.h2
          className="text-3xl md:text-4xl font-bold text-foreground text-center mb-4"
          variants={fadeUp}
          custom={0}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.5 }}
        >
          Features
        </motion.h2>
        <motion.p
          className="text-muted-foreground text-center mb-14 max-w-xl mx-auto"
          variants={fadeUp}
          custom={1}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.5 }}
        >
          Comprehensive AI-powered claim processing from upload to decision.
        </motion.p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f, i) => (
            <motion.div
              key={i}
              className="glass-card p-6 group cursor-default relative overflow-hidden"
              custom={i}
              variants={i % 2 === 0 ? slideInLeft : slideInRight}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.2 }}
              whileHover={{ y: -6, boxShadow: "0 20px 40px -15px hsl(217.2 91.2% 59.8% / 0.15)" }}
            >
              <motion.div
                className="absolute -top-10 -right-10 w-32 h-32 rounded-full bg-primary/5 group-hover:bg-primary/10 transition-all duration-700 group-hover:scale-150"
              />
              <div className="relative z-10">
                <motion.div
                  whileHover={{ rotate: 15, scale: 1.2 }}
                  transition={{ type: "spring", stiffness: 300 }}
                >
                  <f.icon className="text-primary mb-4" size={30} />
                </motion.div>
                <h3 className="text-lg font-semibold text-foreground mb-2">{f.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{f.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Decision Thresholds */}
      <section className="container py-20">
        <motion.h2
          className="text-3xl md:text-4xl font-bold text-foreground text-center mb-10"
          variants={fadeUp}
          custom={0}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.5 }}
        >
          Decision Thresholds
        </motion.h2>
        <motion.div
          className="glass-card p-8 max-w-3xl mx-auto"
          variants={scaleIn}
          custom={0}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.3 }}
        >
          <motion.div
            className="cost-scale-bar mb-4"
            initial={{ scaleX: 0, transformOrigin: "left" }}
            whileInView={{ scaleX: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
          />
          <div className="flex justify-between text-xs text-muted-foreground mb-6">
            <span>₹0</span>
            <span className="text-success font-medium">✅ Auto Approved</span>
            <span>₹25K</span>
            <span className="text-warning font-medium">⚠️ Supervisor</span>
            <span>₹60K</span>
            <span className="text-destructive font-medium">🔴 Manual</span>
            <span>₹∞</span>
          </div>
          <motion.div
            className="glass-card p-3 text-center text-sm"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.8 }}
          >
            <Eye className="inline mr-2 text-warning" size={16} />
            <span className="text-muted-foreground">AI Confidence &lt; 60% → Always Manual</span>
            <span className="text-muted-foreground ml-1">(Responsible AI)</span>
          </motion.div>
        </motion.div>
      </section>

      {/* CTA Section */}
      <section className="container py-20">
        <motion.div
          className="glass-card p-12 text-center relative overflow-hidden"
          variants={scaleIn}
          custom={0}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.3 }}
        >
          <motion.div className="absolute inset-0 gradient-mesh opacity-50" />
          <div className="relative z-10">
            <motion.h2
              className="text-3xl md:text-4xl font-bold text-foreground mb-4"
              variants={fadeUp}
              custom={0}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
            >
              Ready to Transform Claims Processing?
            </motion.h2>
            <motion.p
              className="text-muted-foreground mb-8 max-w-lg mx-auto"
              variants={fadeUp}
              custom={1}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
            >
              Start processing motor insurance claims with AI-powered precision today.
            </motion.p>
            <motion.div
              variants={fadeUp}
              custom={2}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
            >
              <Button variant="hero" size="xl" asChild>
                <Link to="/claim">
                  Get Started Now <ArrowRight className="ml-2" />
                </Link>
              </Button>
            </motion.div>
          </div>
        </motion.div>
      </section>

      <Footer />
    </div>
  );
}
