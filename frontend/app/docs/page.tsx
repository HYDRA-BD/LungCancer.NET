"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  Activity,
  ArrowRight,
  ExternalLink,
  CheckCircle2,
  XCircle,
  ShieldCheck,
  Cpu,
  Database,
  Brain,
  Server,
  FileText,
  Layers,
  Scale,
  AlertTriangle,
  RefreshCw,
  Sun,
  Moon,
  Workflow,
  Stethoscope,
  Terminal,
  Clock,
  Sparkles,
  Lock,
  ChevronRight,
  Menu,
  X,
  Code2,
  FileCheck,
  UserCheck,
  Compass,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_API_URL || "https://lungcancer-net.onrender.com";

interface HealthData {
  status: string;
  aqi_states_cached: number | string;
  timestamp: string;
}

interface ApiEndpoint {
  method: string;
  path: string;
  summary: string;
  tags: string[];
}

export default function DocsPage() {
  // Theme state
  const [isDark, setIsDark] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeSection, setActiveSection] = useState("hero");

  // Live data states
  const [health, setHealth] = useState<HealthData | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);
  const [healthError, setHealthError] = useState(false);
  const [lastCheckedTime, setLastCheckedTime] = useState<number | null>(null);
  const [secondsAgo, setSecondsAgo] = useState<number>(0);

  const [statesCount, setStatesCount] = useState<number | string>("—");
  const [statesLoading, setStatesLoading] = useState(true);

  const [endpoints, setEndpoints] = useState<ApiEndpoint[]>([]);
  const [endpointsLoading, setEndpointsLoading] = useState(true);
  const [selectedTag, setSelectedTag] = useState<string>("ALL");

  // Initialize theme
  useEffect(() => {
    const isDarkMode =
      localStorage.getItem("theme") === "dark" ||
      document.documentElement.classList.contains("dark");
    setIsDark(isDarkMode);
    if (isDarkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, []);

  const toggleDarkMode = () => {
    const nextDark = !isDark;
    setIsDark(nextDark);
    if (nextDark) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  };

  // Fetch Health
  const fetchHealth = async () => {
    try {
      setHealthLoading(true);
      const res = await fetch(`${BACKEND_URL}/health`);
      if (!res.ok) throw new Error("Health check failed");
      const data = await res.json();
      setHealth({
        status: data.status || "—",
        aqi_states_cached: data.aqi_states_cached ?? "—",
        timestamp: data.timestamp || new Date().toISOString(),
      });
      setHealthError(false);
      setLastCheckedTime(Date.now());
      setSecondsAgo(0);
    } catch {
      setHealthError(true);
      setHealth({
        status: "unreachable",
        aqi_states_cached: "—",
        timestamp: "—",
      });
      setLastCheckedTime(Date.now());
      setSecondsAgo(0);
    } finally {
      setHealthLoading(false);
    }
  };

  // Fetch States count
  const fetchStates = async () => {
    try {
      setStatesLoading(true);
      const res = await fetch(`${BACKEND_URL}/api/states`);
      if (!res.ok) throw new Error("States fetch failed");
      const data = await res.json();
      if (Array.isArray(data)) {
        setStatesCount(data.length);
      } else if (data && typeof data.count === "number") {
        setStatesCount(data.count);
      } else {
        setStatesCount(50);
      }
    } catch {
      setStatesCount("—");
    } finally {
      setStatesLoading(false);
    }
  };

  // Fetch OpenAPI schema
  const fetchOpenApi = async () => {
    try {
      setEndpointsLoading(true);
      const res = await fetch(`${BACKEND_URL}/openapi.json`);
      if (!res.ok) throw new Error("OpenAPI fetch failed");
      const data = await res.json();
      const extracted: ApiEndpoint[] = [];
      if (data.paths) {
        Object.keys(data.paths).forEach((pathKey) => {
          const pathObj = data.paths[pathKey];
          Object.keys(pathObj).forEach((methodKey) => {
            const op = pathObj[methodKey];
            if (typeof op === "object" && op !== null) {
              extracted.push({
                method: methodKey.toUpperCase(),
                path: pathKey,
                summary:
                  op.summary ||
                  op.description ||
                  `${methodKey.toUpperCase()} ${pathKey}`,
                tags: Array.isArray(op.tags) && op.tags.length > 0 ? op.tags : ["General"],
              });
            }
          });
        });
      }
      setEndpoints(extracted);
    } catch {
      // Fallback endpoints list if network offline
      setEndpoints([
        { method: "GET", path: "/health", summary: "Health status & AQI cache count", tags: ["System"] },
        { method: "POST", path: "/auth/signup", summary: "Provision new clinician or auditor account", tags: ["Authentication"] },
        { method: "POST", path: "/auth/login", summary: "Issue JWT bearer access token", tags: ["Authentication"] },
        { method: "GET", path: "/auth/me", summary: "Get current authenticated profile", tags: ["Authentication"] },
        { method: "GET", path: "/api/states", summary: "List all 50 US states with cached historical AQI", tags: ["Clinical Data"] },
        { method: "GET", path: "/api/aqi/{state}", summary: "Get 5-year PM2.5/AQI normative value for state", tags: ["Clinical Data"] },
        { method: "POST", path: "/api/predict", summary: "Execute 9-predictor stacked ensemble & SHAP", tags: ["Inference"] },
        { method: "POST", path: "/api/guidelines", summary: "ChromaDB RAG search over USPSTF recommendations", tags: ["Guideline RAG"] },
        { method: "POST", path: "/api/analyze", summary: "End-to-end clinical synthesis & tier triage", tags: ["Inference"] },
        { method: "POST", path: "/api/report", summary: "Synthesize hospital-grade PDF with SHA-256 seal", tags: ["Report Generator"] },
      ]);
    } finally {
      setEndpointsLoading(false);
    }
  };

  // Mount effects
  useEffect(() => {
    fetchHealth();
    fetchStates();
    fetchOpenApi();

    // 30s auto-refresh for health
    const healthInterval = setInterval(() => {
      fetchHealth();
    }, 30000);

    // 1s counter for seconds ago
    const secondsInterval = setInterval(() => {
      setSecondsAgo((prev) => prev + 1);
    }, 1000);

    return () => {
      clearInterval(healthInterval);
      clearInterval(secondsInterval);
    };
  }, []);

  // ScrollSpy for TOC
  useEffect(() => {
    const handleScroll = () => {
      const sections = [
        "hero",
        "problem",
        "solution",
        "how-it-works",
        "architecture",
        "live-status",
        "api-endpoints",
        "tech-stack",
        "team",
        "metrics",
        "responsible-ai",
      ];
      const scrollPos = window.scrollY + 200;
      for (const section of sections) {
        const el = document.getElementById(section);
        if (el) {
          const top = el.offsetTop;
          const height = el.offsetHeight;
          if (scrollPos >= top && scrollPos < top + height) {
            setActiveSection(section);
            break;
          }
        }
      }
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Filtered endpoints
  const allTags = useMemo(() => {
    const tags = new Set<string>();
    endpoints.forEach((ep) => ep.tags.forEach((t) => tags.add(t)));
    return Array.from(tags);
  }, [endpoints]);

  const filteredEndpoints = useMemo(() => {
    if (selectedTag === "ALL") return endpoints;
    return endpoints.filter((ep) => ep.tags.includes(selectedTag));
  }, [endpoints, selectedTag]);

  const navItems = [
    { id: "hero", label: "Overview" },
    { id: "problem", label: "The Problem" },
    { id: "solution", label: "The Solution" },
    { id: "how-it-works", label: "How It Works" },
    { id: "architecture", label: "System Architecture" },
    { id: "live-status", label: "Live System Status" },
    { id: "api-endpoints", label: "API Reference" },
    { id: "tech-stack", label: "Tech Stack" },
    { id: "team", label: "Team & Authors" },
    { id: "metrics", label: "Validation & Metrics" },
    { id: "responsible-ai", label: "Responsible AI" },
  ];

  return (
    <div className="min-h-screen bg-background text-foreground antialiased selection:bg-primary/20">
      {/* Background Ambience */}
      <div
        aria-hidden="true"
        className="fixed inset-0 -z-10 pointer-events-none opacity-[0.05] dark:opacity-[0.10]"
        style={{
          backgroundImage: "url(/logo.png)",
          backgroundSize: "contain",
          backgroundPosition: "center",
          backgroundRepeat: "no-repeat",
          filter: "blur(70px)",
        }}
      />

      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-50 w-full bg-card/90 backdrop-blur-md border-b border-border transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
          {/* Logo & Subtitle */}
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="flex items-center gap-2.5 font-bold text-lg sm:text-xl text-foreground hover:opacity-90 transition-opacity"
            >
              <span className="text-2xl" role="img" aria-label="lungs">
                🫁
              </span>
              <span className="tracking-tight font-sans">LungCancer.NET</span>
            </Link>
            <span className="hidden md:inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20">
              Whitepaper & Pitch Deck
            </span>
          </div>

          {/* Right Header CTAs & Theme Toggle */}
          <div className="flex items-center gap-2 sm:gap-3">
            <button
              type="button"
              onClick={toggleDarkMode}
              title={isDark ? "Switch to Light Mode" : "Switch to Dark Mode"}
              className="p-2 rounded-lg border border-border text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            >
              {isDark ? (
                <Sun className="w-4 h-4 text-amber-400" />
              ) : (
                <Moon className="w-4 h-4 text-slate-600" />
              )}
            </button>

            <a
              href="https://lungcancer-net.onrender.com/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="hidden sm:inline-flex"
            >
              <Button variant="outline" size="sm" className="gap-1.5 text-xs font-medium">
                <span>API Docs</span>
                <ExternalLink className="w-3.5 h-3.5 opacity-70" />
              </Button>
            </a>

            <Link href="/login">
              <Button size="sm" className="bg-primary hover:bg-primary-hover text-primary-foreground gap-1.5 text-xs font-semibold shadow-sm">
                <span>Launch App</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Button>
            </Link>

            {/* Mobile TOC Toggle */}
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 lg:hidden rounded-lg border border-border text-muted-foreground hover:text-foreground"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Dropdown Menu for TOC */}
        {mobileMenuOpen && (
          <div className="lg:hidden border-b border-border bg-card px-4 py-3 space-y-1 shadow-lg max-h-[70vh] overflow-y-auto">
            <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground px-2 py-1">
              Table of Contents
            </div>
            {navItems.map((item) => (
              <a
                key={item.id}
                href={`#${item.id}`}
                onClick={() => setMobileMenuOpen(false)}
                className={`block px-3 py-2 rounded-md text-sm transition-colors ${
                  activeSection === item.id
                    ? "bg-primary/10 text-primary font-semibold"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                }`}
              >
                {item.label}
              </a>
            ))}
          </div>
        )}
      </header>

      {/* Main Container with Sidebar + Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 lg:py-12 flex gap-10 items-start">
        {/* Desktop Sticky Table of Contents */}
        <aside className="hidden lg:block w-64 shrink-0 sticky top-24 space-y-6">
          <div className="p-4 rounded-xl border border-border bg-card/60 backdrop-blur shadow-sm space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-muted-foreground px-2">
              <Compass className="w-3.5 h-3.5 text-primary" />
              <span>Table of Contents</span>
            </div>
            <nav className="space-y-1">
              {navItems.map((item, idx) => (
                <a
                  key={item.id}
                  href={`#${item.id}`}
                  className={`group flex items-center justify-between px-3 py-1.5 rounded-lg text-sm transition-all ${
                    activeSection === item.id
                      ? "bg-primary text-primary-foreground font-medium shadow-sm"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted/80"
                  }`}
                >
                  <span className="truncate">
                    <span className="text-xs opacity-60 mr-2 font-mono">
                      {String(idx + 1).padStart(2, "0")}
                    </span>
                    {item.label}
                  </span>
                  <ChevronRight
                    className={`w-3.5 h-3.5 transition-transform ${
                      activeSection === item.id
                        ? "opacity-100 translate-x-0.5"
                        : "opacity-0 group-hover:opacity-60"
                    }`}
                  />
                </a>
              ))}
            </nav>
          </div>

          {/* Quick System Badge in Sidebar */}
          <div className="p-4 rounded-xl border border-border bg-card/40 space-y-2.5 text-xs text-muted-foreground">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-foreground">Backend Status</span>
              <span className="inline-flex items-center gap-1 font-mono text-[11px] text-emerald-600 dark:text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                {health?.status === "ok" ? "LIVE" : "CHECKING"}
              </span>
            </div>
            <p className="leading-relaxed">
              Serving production clinical risk inference on FastAPI & Next.js.
            </p>
            <div className="pt-2 border-t border-border flex items-center justify-between text-[11px]">
              <a
                href="https://github.com/HYDRA-BD/LungCancer.NET"
                target="_blank"
                rel="noreferrer"
                className="hover:text-primary transition-colors inline-flex items-center gap-1"
              >
                GitHub <ExternalLink className="w-3 h-3" />
              </a>
              <a
                href="https://lungcancer-net.onrender.com/health"
                target="_blank"
                rel="noreferrer"
                className="hover:text-primary transition-colors font-mono"
              >
                /health
              </a>
            </div>
          </div>
        </aside>

        {/* Main Document Content */}
        <main className="flex-1 min-w-0 max-w-4xl space-y-20 pb-20">
          {/* ═══════════════════════════════════════════════════════════
              1. HERO / ONE-LINER
              ═══════════════════════════════════════════════════════════ */}
          <section id="hero" className="scroll-mt-24 space-y-8 pt-4">
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20">
                <Sparkles className="w-3.5 h-3.5" />
                <span>AI Clinical Decision Support · AI Builders Congress 2026</span>
              </div>
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-foreground font-sans">
                LungCancer.NET
              </h1>
              <p className="text-lg sm:text-xl text-muted-foreground leading-relaxed max-w-3xl">
                Composite AI clinical pre-screening for lung cancer risk — designed for rural and
                underserved populations where imaging is scarce.
              </p>
            </div>

            {/* Three KPI Cards (pulled from live data + static) */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* KPI 1: Live States */}
              <div className="p-5 rounded-xl border border-border bg-card shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all space-y-1">
                <div className="flex items-center justify-between text-muted-foreground text-xs font-medium uppercase tracking-wider">
                  <span>Coverage</span>
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
                </div>
                <div className="text-3xl font-bold font-mono text-primary flex items-baseline gap-1">
                  {statesLoading ? (
                    <span className="animate-pulse">...</span>
                  ) : (
                    <span>{statesCount}</span>
                  )}
                  <span className="text-sm font-sans font-normal text-muted-foreground">States</span>
                </div>
                <div className="text-xs text-muted-foreground flex items-center gap-1.5 pt-1">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                  <span>50 US states covered (GET /api/states)</span>
                </div>
              </div>

              {/* KPI 2: 9-Predictor Ensemble */}
              <div className="p-5 rounded-xl border border-border bg-card shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all space-y-1">
                <div className="flex items-center justify-between text-muted-foreground text-xs font-medium uppercase tracking-wider">
                  <span>ML Architecture</span>
                  <Cpu className="w-4 h-4 text-primary" />
                </div>
                <div className="text-3xl font-bold font-mono text-foreground flex items-baseline gap-1">
                  9<span className="text-sm font-sans font-normal text-muted-foreground">Predictors</span>
                </div>
                <div className="text-xs text-muted-foreground flex items-center gap-1.5 pt-1">
                  <Layers className="w-3.5 h-3.5 text-accent shrink-0" />
                  <span>XGBoost + CatBoost + LightGBM</span>
                </div>
              </div>

              {/* KPI 3: Deployed */}
              <div className="p-5 rounded-xl border border-border bg-card shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all space-y-1">
                <div className="flex items-center justify-between text-muted-foreground text-xs font-medium uppercase tracking-wider">
                  <span>System Release</span>
                  <span className="relative flex h-2.5 w-2.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500" />
                  </span>
                </div>
                <div className="text-3xl font-bold font-mono text-foreground flex items-baseline gap-1">
                  v1.0
                  <span className="text-sm font-sans font-normal text-emerald-600 dark:text-emerald-400 ml-1">
                    · Deployed
                  </span>
                </div>
                <div className="text-xs text-muted-foreground flex items-center gap-1.5 pt-1">
                  <Server className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                  <span>FastAPI on Render + Vercel Client</span>
                </div>
              </div>
            </div>

            {/* CTAs */}
            <div className="flex flex-wrap items-center gap-4 pt-2">
              <Link href="/login">
                <Button size="lg" className="bg-primary hover:bg-primary-hover text-primary-foreground font-semibold shadow-md gap-2">
                  <span>Launch App</span>
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
              <a
                href="https://lungcancer-net.onrender.com/docs"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Button size="lg" variant="outline" className="font-semibold gap-2 border-border">
                  <span>View API Docs</span>
                  <ExternalLink className="w-4 h-4 text-muted-foreground" />
                </Button>
              </a>
            </div>
          </section>

          <hr className="border-border" />

          {/* ═══════════════════════════════════════════════════════════
              2. THE PROBLEM
              ═══════════════════════════════════════════════════════════ */}
          <section id="problem" className="scroll-mt-24 space-y-6">
            <div className="flex items-center gap-2.5 text-xs font-bold uppercase tracking-wider text-rose-600 dark:text-rose-400">
              <AlertTriangle className="w-4 h-4" />
              <span>The Clinical & Geographic Challenge</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground font-sans">
              The Screening Bottleneck in Underserved Communities
            </h2>
            <div className="p-6 sm:p-8 rounded-xl border border-rose-500/20 bg-rose-500/5 dark:bg-rose-950/10 space-y-4">
              <p className="text-base sm:text-lg leading-relaxed text-foreground">
                <strong>Lung cancer is the leading cause of cancer death worldwide</strong>, accounting for
                over 1.8 million fatalities every year. While early detection via Low-Dose Computed Tomography
                (LDCT) dramatically reduces mortality, <strong>rural populations severely lack access to LDCT imaging facilities</strong>.
              </p>
              <p className="text-base leading-relaxed text-muted-foreground">
                In hundreds of rural counties across America, the nearest accredited CT scanner is hours away,
                and mobile radiology vans are prohibitively expensive. <strong>Current screening guidelines depend
                entirely on expensive, scarce imaging equipment</strong>, leaving primary care clinicians in
                underserved regions without an accessible, low-cost pre-screening mechanism to identify who
                urgently needs scarce referral slots.
              </p>
            </div>
          </section>

          <hr className="border-border" />

          {/* ═══════════════════════════════════════════════════════════
              3. THE SOLUTION
              ═══════════════════════════════════════════════════════════ */}
          <section id="solution" className="scroll-mt-24 space-y-6">
            <div className="flex items-center gap-2.5 text-xs font-bold uppercase tracking-wider text-primary">
              <ShieldCheck className="w-4 h-4" />
              <span>Algorithmic Architecture</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground font-sans">
              A Tripartite Composite Pre-Screening Engine
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              LungCancer.NET flips the diagnostic funnel by triaging patient risk before scheduling costly imaging.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {/* Card 1 */}
              <div className="p-6 rounded-xl border border-border bg-card shadow-sm hover:shadow-md hover:-translate-y-1 transition-all space-y-3">
                <div className="w-10 h-10 rounded-lg bg-primary/10 text-primary flex items-center justify-center font-bold">
                  <FileText className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-foreground">Survey-First Triage</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Uses CDC BRFSS population health survey data and 5-year EPA historical AQI/PM2.5 baselines.
                  Zero imaging required — purely non-invasive biometrics, inhalation history, and comorbidities.
                </p>
              </div>

              {/* Card 2 */}
              <div className="p-6 rounded-xl border border-border bg-card shadow-sm hover:shadow-md hover:-translate-y-1 transition-all space-y-3">
                <div className="w-10 h-10 rounded-lg bg-accent/10 text-accent flex items-center justify-center font-bold">
                  <Layers className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-foreground">9-Predictor Ensemble</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  XGBoost + CatBoost + LightGBM stacked across 3 asymmetric class weightings &#123;1, 5, 10&#125;.
                  Out-of-Fold (OOF) stacked meta-learner outputs calibrated probabilities with SHAP waterfall explanations.
                </p>
              </div>

              {/* Card 3 */}
              <div className="p-6 rounded-xl border border-border bg-card shadow-sm hover:shadow-md hover:-translate-y-1 transition-all space-y-3">
                <div className="w-10 h-10 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold">
                  <Scale className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-foreground">Equity-Aware Policy</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Enforces a strict sensitivity floor (&ge; 85%) across all vulnerable demographic strata.
                  A patient is classified into <strong>RULE-OUT only when every single demographic subgroup passes</strong>.
                </p>
              </div>
            </div>
          </section>

          <hr className="border-border" />

          {/* ═══════════════════════════════════════════════════════════
              4. HOW IT WORKS
              ═══════════════════════════════════════════════════════════ */}
          <section id="how-it-works" className="scroll-mt-24 space-y-6">
            <div className="flex items-center gap-2.5 text-xs font-bold uppercase tracking-wider text-accent">
              <Workflow className="w-4 h-4" />
              <span>Step-by-Step Clinical Workflow</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground font-sans">
              How the System Operates
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              From clinician intake to cryptographically signed diagnostic documentation in 5 vertical steps:
            </p>

            <div className="space-y-4">
              {[
                {
                  step: 1,
                  title: "Patient Intake",
                  desc: "4-step intake form capturing demographics (age, sex, location), inhalation history (pack-years), chronic comorbidities (COPD, asthma, heart conditions), and healthcare access barriers (cost barrier, checkup recency).",
                  icon: Stethoscope,
                },
                {
                  step: 2,
                  title: "Ensemble Prediction & Triage",
                  desc: "9 base gradient-boosted trees infer risk scores, mapped through an OOF-stacked meta-learner into clinical triage tiers: REFER (immediate LDCT order), REVIEW (shared clinician consultation), or RULE-OUT (annual routine surveillance).",
                  icon: Cpu,
                },
                {
                  step: 3,
                  title: "Guideline Retrieval",
                  desc: "Local semantic vector search (ChromaDB + sentence-transformers) queries the official USPSTF 2021 Lung Cancer Screening recommendations for matching clinical eligibility criteria.",
                  icon: Database,
                },
                {
                  step: 4,
                  title: "Clinical Narrative Generation",
                  desc: "An offline, local LLM (Ollama qwen2.5:3b) synthesizes an objective, clinician-facing assessment and rationale with zero cloud API keys or external data transmission.",
                  icon: Brain,
                },
                {
                  step: 5,
                  title: "Hospital-Grade PDF Report",
                  desc: "Dynamic synthesis of an archival-quality PDF featuring triage tier badges, SHAP factor attribution breakdown, USPSTF citations, and a tamper-evident SHA-256 integrity hash seal.",
                  icon: FileCheck,
                },
              ].map((item) => (
                <div
                  key={item.step}
                  className="flex gap-4 p-5 rounded-xl border border-border bg-card shadow-sm hover:shadow-md transition-all items-start"
                >
                  <div className="w-10 h-10 rounded-full bg-primary/10 text-primary flex items-center justify-center font-mono font-bold text-base shrink-0">
                    {item.step}
                  </div>
                  <div className="space-y-1">
                    <h3 className="text-base sm:text-lg font-bold text-foreground flex items-center gap-2">
                      <span>{item.title}</span>
                      <item.icon className="w-4 h-4 text-muted-foreground" />
                    </h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <hr className="border-border" />

          {/* ═══════════════════════════════════════════════════════════
              5. ARCHITECTURE DIAGRAM
              ═══════════════════════════════════════════════════════════ */}
          <section id="architecture" className="scroll-mt-24 space-y-6">
            <div className="flex items-center gap-2.5 text-xs font-bold uppercase tracking-wider text-primary">
              <Layers className="w-4 h-4" />
              <span>Full System Architecture</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground font-sans">
              Decoupled Ingress, Composite Inference & Agent Protocol
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              Standardized HTTP REST endpoints for web clinicians alongside Model Context Protocol (MCP) tool bindings for AI agents.
            </p>

            {/* Architecture Visual Diagram Container */}
            <div className="p-6 sm:p-8 rounded-2xl border border-border bg-card shadow-sm space-y-6 overflow-hidden">
              <div className="flex items-center justify-between border-b border-border pb-4">
                <span className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
                  Architecture Flow Diagram
                </span>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-accent/10 text-accent font-semibold">
                  Zero Patient Data on Disk
                </span>
              </div>

              {/* Interactive SVG Diagram */}
              <div className="w-full overflow-x-auto">
                <svg
                  viewBox="0 0 860 460"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                  className="w-full h-auto min-w-[700px] text-foreground"
                >
                  <defs>
                    <marker
                      id="arrow"
                      viewBox="0 0 10 10"
                      refX="6"
                      refY="5"
                      markerWidth="6"
                      markerHeight="6"
                      orient="auto-start-reverse"
                    >
                      <path d="M 0 1 L 10 5 L 0 9 z" fill="currentColor" opacity="0.6" />
                    </marker>
                    <linearGradient id="boxGrad" x1="0" y1="0" x2="1" y2="1">
                      <stop offset="0%" stopColor="currentColor" stopOpacity="0.04" />
                      <stop offset="100%" stopColor="currentColor" stopOpacity="0.08" />
                    </linearGradient>
                  </defs>

                  {/* Top: Browser & Agent Ingress */}
                  {/* Browser Box */}
                  <g>
                    <rect
                      x="40"
                      y="40"
                      width="190"
                      height="80"
                      rx="10"
                      className="stroke-border fill-card"
                      strokeWidth="2"
                    />
                    <text x="135" y="75" textAnchor="middle" className="fill-foreground font-bold text-sm">
                      Browser / Next.js
                    </text>
                    <text x="135" y="95" textAnchor="middle" className="fill-muted-foreground text-xs font-mono">
                      Clinician Portal :3000
                    </text>
                  </g>

                  {/* AI Agents Box */}
                  <g>
                    <rect
                      x="40"
                      y="180"
                      width="190"
                      height="80"
                      rx="10"
                      className="stroke-border fill-card"
                      strokeWidth="2"
                    />
                    <text x="135" y="215" textAnchor="middle" className="fill-foreground font-bold text-sm">
                      AI Agents
                    </text>
                    <text x="135" y="235" textAnchor="middle" className="fill-muted-foreground text-xs font-mono">
                      Claude, Cursor, IDE
                    </text>
                  </g>

                  {/* Connector 1: Browser -> FastAPI */}
                  <path
                    d="M 230 80 L 330 80"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeDasharray="4 4"
                    markerEnd="url(#arrow)"
                    className="text-primary"
                  />
                  <text x="280" y="70" textAnchor="middle" className="fill-primary text-[11px] font-mono">
                    HTTPS / JSON
                  </text>

                  {/* Connector 2: Agents -> MCP Server */}
                  <path
                    d="M 230 220 L 330 220"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeDasharray="4 4"
                    markerEnd="url(#arrow)"
                    className="text-accent"
                  />
                  <text x="280" y="210" textAnchor="middle" className="fill-accent text-[11px] font-mono">
                    JSON-RPC / stdio
                  </text>

                  {/* Middle: FastAPI & MCP Server */}
                  {/* FastAPI Box */}
                  <g>
                    <rect
                      x="330"
                      y="40"
                      width="200"
                      height="90"
                      rx="10"
                      className="stroke-primary fill-primary/5"
                      strokeWidth="2"
                    />
                    <text x="430" y="75" textAnchor="middle" className="fill-primary font-bold text-sm">
                      FastAPI Backend
                    </text>
                    <text x="430" y="95" textAnchor="middle" className="fill-foreground text-xs">
                      Hosted on Render
                    </text>
                    <text x="430" y="112" textAnchor="middle" className="fill-muted-foreground text-[10px] font-mono">
                      Auth · Validation · Dispatch
                    </text>
                  </g>

                  {/* MCP Server Box */}
                  <g>
                    <rect
                      x="330"
                      y="180"
                      width="200"
                      height="80"
                      rx="10"
                      className="stroke-accent fill-accent/5"
                      strokeWidth="2"
                    />
                    <text x="430" y="215" textAnchor="middle" className="fill-accent font-bold text-sm">
                      MCP Server :8001
                    </text>
                    <text x="430" y="235" textAnchor="middle" className="fill-muted-foreground text-xs font-mono">
                      Model Context Protocol
                    </text>
                  </g>

                  {/* Connector from MCP to same inference logic */}
                  <path
                    d="M 430 180 L 430 130"
                    stroke="currentColor"
                    strokeWidth="2"
                    markerEnd="url(#arrow)"
                    className="text-muted-foreground"
                  />
                  <text x="450" y="155" textAnchor="start" className="fill-muted-foreground text-[10px]">
                    Shared Logic
                  </text>

                  {/* Fan-out Connectors from FastAPI to 3 ML/AI Blocks */}
                  {/* To 9-predictor */}
                  <path
                    d="M 530 65 L 610 50"
                    stroke="currentColor"
                    strokeWidth="2"
                    markerEnd="url(#arrow)"
                    className="text-foreground"
                  />
                  {/* To ChromaDB */}
                  <path
                    d="M 530 85 L 610 135"
                    stroke="currentColor"
                    strokeWidth="2"
                    markerEnd="url(#arrow)"
                    className="text-foreground"
                  />
                  {/* To Ollama */}
                  <path
                    d="M 530 105 L 610 220"
                    stroke="currentColor"
                    strokeWidth="2"
                    markerEnd="url(#arrow)"
                    className="text-foreground"
                  />

                  {/* Right: The 3 Core AI Engines */}
                  {/* 1. 9-predictor ensemble */}
                  <g>
                    <rect
                      x="610"
                      y="20"
                      width="210"
                      height="65"
                      rx="8"
                      className="stroke-border fill-card"
                      strokeWidth="2"
                    />
                    <text x="715" y="45" textAnchor="middle" className="fill-foreground font-bold text-xs">
                      9-Predictor Ensemble
                    </text>
                    <text x="715" y="65" textAnchor="middle" className="fill-muted-foreground text-[11px] font-mono">
                      XGB + CatB + LGBM + SHAP
                    </text>
                  </g>

                  {/* 2. ChromaDB RAG */}
                  <g>
                    <rect
                      x="610"
                      y="105"
                      width="210"
                      height="65"
                      rx="8"
                      className="stroke-border fill-card"
                      strokeWidth="2"
                    />
                    <text x="715" y="130" textAnchor="middle" className="fill-foreground font-bold text-xs">
                      ChromaDB RAG
                    </text>
                    <text x="715" y="150" textAnchor="middle" className="fill-muted-foreground text-[11px] font-mono">
                      USPSTF Screening Vectors
                    </text>
                  </g>

                  {/* 3. Ollama LLM */}
                  <g>
                    <rect
                      x="610"
                      y="190"
                      width="210"
                      height="65"
                      rx="8"
                      className="stroke-border fill-card"
                      strokeWidth="2"
                    />
                    <text x="715" y="215" textAnchor="middle" className="fill-foreground font-bold text-xs">
                      Ollama Local LLM
                    </text>
                    <text x="715" y="235" textAnchor="middle" className="fill-muted-foreground text-[11px] font-mono">
                      qwen2.5:3b (Offline inference)
                    </text>
                  </g>

                  {/* Downward Output: PDF Report */}
                  <path
                    d="M 430 130 L 430 330"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeDasharray="4 4"
                    markerEnd="url(#arrow)"
                    className="text-emerald-500"
                  />
                  <text x="440" y="300" textAnchor="start" className="fill-emerald-600 dark:text-emerald-400 text-xs font-mono">
                    Direct Stream
                  </text>

                  {/* PDF Report Box */}
                  <g>
                    <rect
                      x="330"
                      y="330"
                      width="200"
                      height="80"
                      rx="10"
                      className="stroke-emerald-500 fill-emerald-500/10"
                      strokeWidth="2"
                    />
                    <text x="430" y="365" textAnchor="middle" className="fill-emerald-600 dark:fill-emerald-400 font-bold text-sm">
                      Hospital PDF Report
                    </text>
                    <text x="430" y="385" textAnchor="middle" className="fill-foreground text-xs font-mono">
                      SHA-256 Sealed · In-Memory
                    </text>
                  </g>
                </svg>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs text-muted-foreground pt-2">
                <div className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                  <span>
                    <strong>Clinicians:</strong> Access web portal through responsive Next.js frontend with live SHAP waterfall plots.
                  </span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-accent shrink-0 mt-0.5" />
                  <span>
                    <strong>Autonomous Agents:</strong> Claude and Cursor interact via read-only Model Context Protocol (MCP) tool bindings.
                  </span>
                </div>
              </div>
            </div>
          </section>

          <hr className="border-border" />

          {/* ═══════════════════════════════════════════════════════════
              6. LIVE SYSTEM STATUS
              ═══════════════════════════════════════════════════════════ */}
          <section id="live-status" className="scroll-mt-24 space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5 text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                <Activity className="w-4 h-4" />
                <span>Real-Time Backend Observability</span>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={fetchHealth}
                disabled={healthLoading}
                className="gap-1.5 text-xs h-8"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${healthLoading ? "animate-spin" : ""}`} />
                <span>Refresh Now</span>
              </Button>
            </div>

            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground font-sans">
              Live Health Status
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              Auto-refreshed every 30 seconds directly from{" "}
              <a
                href={`${BACKEND_URL}/health`}
                target="_blank"
                rel="noreferrer"
                className="font-mono text-primary underline underline-offset-4"
              >
                GET /health
              </a>
              .
            </p>

            {/* Health Dashboard Card */}
            <div className="p-6 rounded-2xl border border-border bg-card shadow-sm space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Field 1: Status */}
                <div className="space-y-1">
                  <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Service Health
                  </div>
                  <div className="flex items-center gap-2 pt-1">
                    {health?.status === "ok" ? (
                      <CheckCircle2 className="w-6 h-6 text-emerald-500 shrink-0" />
                    ) : (
                      <XCircle className="w-6 h-6 text-rose-500 shrink-0" />
                    )}
                    <span className="text-2xl font-bold font-mono uppercase">
                      {health?.status || "—"}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {health?.status === "ok"
                      ? "FastAPI server accepting requests"
                      : "Server unreachable or responding with error"}
                  </p>
                </div>

                {/* Field 2: AQI States Cached */}
                <div className="space-y-1">
                  <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Cached State AQI Data
                  </div>
                  <div className="text-2xl font-bold font-mono text-foreground pt-1">
                    {health?.aqi_states_cached ?? "—"}
                    <span className="text-sm font-sans font-normal text-muted-foreground ml-1.5">
                      / 50 US States
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    5-year EPA historical PM2.5/AQI in-memory cache
                  </p>
                </div>

                {/* Field 3: Timestamp */}
                <div className="space-y-1">
                  <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Backend Live Timestamp
                  </div>
                  <div className="text-sm font-mono text-foreground pt-2 truncate" title={health?.timestamp}>
                    {health?.timestamp || "—"}
                  </div>
                  <p className="text-xs text-muted-foreground flex items-center gap-1 pt-0.5">
                    <Clock className="w-3.5 h-3.5" />
                    <span>
                      Last checked:{" "}
                      {lastCheckedTime !== null
                        ? `${secondsAgo} second${secondsAgo === 1 ? "" : "s"} ago`
                        : "connecting..."}
                    </span>
                  </p>
                </div>
              </div>

              {/* Status Details Bar */}
              <div className="pt-4 border-t border-border flex flex-wrap items-center justify-between text-xs text-muted-foreground gap-3">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  <span>30-second automated polling active</span>
                </div>
                <div className="font-mono text-[11px]">
                  Target: {BACKEND_URL}/health
                </div>
              </div>
            </div>
          </section>

          <hr className="border-border" />

          {/* ═══════════════════════════════════════════════════════════
              7. API ENDPOINTS
              ═══════════════════════════════════════════════════════════ */}
          <section id="api-endpoints" className="scroll-mt-24 space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5 text-xs font-bold uppercase tracking-wider text-primary">
                <Terminal className="w-4 h-4" />
                <span>Interactive Swagger Contract</span>
              </div>
              <a
                href={`${BACKEND_URL}/docs`}
                target="_blank"
                rel="noreferrer"
                className="text-xs text-primary hover:underline inline-flex items-center gap-1 font-medium"
              >
                <span>Open Swagger UI</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>

            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground font-sans">
              API Endpoints
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              Auto-fetched dynamically on mount from{" "}
              <a
                href={`${BACKEND_URL}/openapi.json`}
                target="_blank"
                rel="noreferrer"
                className="font-mono text-primary underline underline-offset-4"
              >
                /openapi.json
              </a>
              . Click any endpoint row to jump directly to its interactive OpenAPI Swagger documentation.
            </p>

            {/* Tag Filter Pills */}
            {allTags.length > 0 && (
              <div className="flex flex-wrap gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => setSelectedTag("ALL")}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                    selectedTag === "ALL"
                      ? "bg-primary text-primary-foreground font-semibold"
                      : "bg-secondary text-secondary-foreground hover:bg-muted"
                  }`}
                >
                  All ({endpoints.length})
                </button>
                {allTags.map((tag) => (
                  <button
                    key={tag}
                    type="button"
                    onClick={() => setSelectedTag(tag)}
                    className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                      selectedTag === tag
                        ? "bg-primary text-primary-foreground font-semibold"
                        : "bg-secondary text-secondary-foreground hover:bg-muted"
                    }`}
                  >
                    {tag}
                  </button>
                ))}
              </div>
            )}

            {/* Endpoints Table Container */}
            <div className="rounded-xl border border-border bg-card shadow-sm overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-secondary/50 border-b border-border text-xs uppercase tracking-wider font-semibold text-muted-foreground">
                    <tr>
                      <th className="py-3 px-4 w-28">Method</th>
                      <th className="py-3 px-4 w-56 sm:w-64">Path</th>
                      <th className="py-3 px-4">Summary</th>
                      <th className="py-3 px-4 w-24 text-right">Swagger</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border font-sans">
                    {endpointsLoading ? (
                      <tr>
                        <td colSpan={4} className="py-8 text-center text-muted-foreground">
                          <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-primary" />
                          <span>Fetching schema from OpenAPI...</span>
                        </td>
                      </tr>
                    ) : filteredEndpoints.length === 0 ? (
                      <tr>
                        <td colSpan={4} className="py-6 text-center text-muted-foreground">
                          No endpoints found for this tag.
                        </td>
                      </tr>
                    ) : (
                      filteredEndpoints.map((ep, idx) => {
                        const isGet = ep.method === "GET";
                        const isPost = ep.method === "POST";
                        const isDelete = ep.method === "DELETE";

                        return (
                          <tr
                            key={`${ep.method}-${ep.path}-${idx}`}
                            onClick={() => {
                              window.open(
                                `${BACKEND_URL}/docs`,
                                "_blank",
                                "noopener,noreferrer"
                              );
                            }}
                            className="hover:bg-muted/60 cursor-pointer transition-colors group"
                            title="Click to view endpoint in Swagger UI"
                          >
                            <td className="py-3 px-4">
                              <span
                                className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-bold border ${
                                  isGet
                                    ? "bg-sky-500/10 text-sky-600 dark:text-sky-400 border-sky-500/20"
                                    : isPost
                                    ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20"
                                    : isDelete
                                    ? "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20"
                                    : "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20"
                                }`}
                              >
                                {ep.method}
                              </span>
                            </td>
                            <td className="py-3 px-4 font-mono text-xs font-semibold text-foreground">
                              {ep.path}
                            </td>
                            <td className="py-3 px-4 text-xs text-muted-foreground group-hover:text-foreground transition-colors">
                              {ep.summary}
                            </td>
                            <td className="py-3 px-4 text-right">
                              <ExternalLink className="w-3.5 h-3.5 text-muted-foreground opacity-40 group-hover:opacity-100 group-hover:text-primary transition-all inline-block" />
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </section>

          <hr className="border-border" />

          {/* ═══════════════════════════════════════════════════════════
              8. TECH STACK
              ═══════════════════════════════════════════════════════════ */}
          <section id="tech-stack" className="scroll-mt-24 space-y-6">
            <div className="flex items-center gap-2.5 text-xs font-bold uppercase tracking-wider text-accent">
              <Code2 className="w-4 h-4" />
              <span>Modern Clinical Architecture</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground font-sans">
              Technology Stack
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              Every component chosen for production reliability, cryptographic verification, and reproducible inference:
            </p>

            <div className="flex flex-wrap gap-2.5 pt-1">
              {[
                "FastAPI",
                "Next.js",
                "XGBoost",
                "CatBoost",
                "LightGBM",
                "scikit-learn",
                "ChromaDB",
                "sentence-transformers",
                "Ollama",
                "MCP",
                "Render",
                "Vercel",
                "ReportLab",
                "PostgreSQL (optional)",
                "JWT",
                "PBKDF2",
              ].map((tech) => (
                <div
                  key={tech}
                  className="px-3.5 py-2 rounded-lg border border-border bg-card hover:bg-secondary hover:border-primary/30 transition-all font-mono text-xs sm:text-sm font-medium text-foreground shadow-sm flex items-center gap-2"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-primary" />
                  <span>{tech}</span>
                </div>
              ))}
            </div>
          </section>

          <hr className="border-border" />

          {/* ═══════════════════════════════════════════════════════════
              9. TEAM
              ═══════════════════════════════════════════════════════════ */}
          <section id="team" className="scroll-mt-24 space-y-6">
            <div className="flex items-center gap-2.5 text-xs font-bold uppercase tracking-wider text-primary">
              <UserCheck className="w-4 h-4" />
              <span>Engineering & Clinical Architecture</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground font-sans">
              Meet the Team
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              Bridging machine learning rigor with frontline healthcare accessibility.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {/* Member 1: S.M. Jarif Haider Amio */}
              <div className="p-6 rounded-xl border border-border bg-card shadow-sm hover:shadow-md transition-all flex items-start gap-4">
                <div className="w-14 h-14 rounded-full bg-primary/10 border-2 border-primary/20 text-primary flex items-center justify-center font-bold text-lg shrink-0">
                  JA
                </div>
                <div className="space-y-1">
                  <h3 className="text-lg font-bold text-foreground">S.M. Jarif Haider Amio</h3>
                  <div className="text-xs font-medium text-primary">
                    Lead Engineer & Clinical AI Architect
                  </div>
                  <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed pt-1">
                    Architected the 9-predictor stacked ensemble ladder, equity sensitivity floor algorithm, and full-stack clinical deployment.
                  </p>
                </div>
              </div>

              {/* Member 2: Clinical Research & Epidemiology */}
              <div className="p-6 rounded-xl border border-border bg-card shadow-sm hover:shadow-md transition-all flex items-start gap-4">
                <div className="w-14 h-14 rounded-full bg-accent/10 border-2 border-accent/20 text-accent flex items-center justify-center font-bold text-lg shrink-0">
                  CR
                </div>
                <div className="space-y-1">
                  <h3 className="text-lg font-bold text-foreground">Clinical Advisory Group</h3>
                  <div className="text-xs font-medium text-accent">
                    Epidemiological Research & Validation
                  </div>
                  <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed pt-1">
                    Guided the CDC BRFSS epidemiological feature selection, USPSTF guideline vector synthesis, and health equity guardrails.
                  </p>
                </div>
              </div>

              {/* Member 3: Systems & Compliance */}
              <div className="p-6 rounded-xl border border-border bg-card shadow-sm hover:shadow-md transition-all flex items-start gap-4 md:col-span-2">
                <div className="w-14 h-14 rounded-full bg-emerald-500/10 border-2 border-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold text-lg shrink-0">
                  SE
                </div>
                <div className="space-y-1">
                  <h3 className="text-lg font-bold text-foreground">Biomedical Systems & Security</h3>
                  <div className="text-xs font-medium text-emerald-600 dark:text-emerald-400">
                    Infrastructure & Cryptographic Verification
                  </div>
                  <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed pt-1">
                    Engineered the zero-disk ephemeral data handling pipeline, PBKDF2-HMAC-SHA256 authentication, and tamper-evident SHA-256 PDF synthesis.
                  </p>
                </div>
              </div>
            </div>
          </section>

          <hr className="border-border" />

          {/* ═══════════════════════════════════════════════════════════
              10. METRICS & VALIDATION
              ═══════════════════════════════════════════════════════════ */}
          <section id="metrics" className="scroll-mt-24 space-y-6">
            <div className="flex items-center gap-2.5 text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
              <Scale className="w-4 h-4" />
              <span>Cohort Generalization</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground font-sans">
              Metrics & External Validation
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              Empirical evaluation on large-scale epidemiological survey data with frozen triage cutoffs:
            </p>

            <div className="rounded-xl border border-border bg-card shadow-sm overflow-hidden">
              <table className="w-full text-left text-sm">
                <thead className="bg-secondary/50 border-b border-border text-xs uppercase tracking-wider font-semibold text-muted-foreground">
                  <tr>
                    <th className="py-3 px-4">Evaluation Dimension</th>
                    <th className="py-3 px-4">Empirical Result</th>
                    <th className="py-3 px-4">Source / Methodology</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  <tr>
                    <td className="py-3 px-4 font-semibold text-foreground">
                      External Validation Cohort
                    </td>
                    <td className="py-3 px-4 font-mono text-primary font-medium">
                      LLCP2023 (held out)
                    </td>
                    <td className="py-3 px-4 text-xs text-muted-foreground">
                      320,482 individuals evaluated with frozen meta-learner thresholds
                    </td>
                  </tr>
                  <tr>
                    <td className="py-3 px-4 font-semibold text-foreground">
                      Discrimination (AUROC)
                    </td>
                    <td className="py-3 px-4 font-mono text-foreground font-medium">
                      0.951 <span className="text-xs text-muted-foreground">[95% CI: 0.940 – 0.964]</span>
                    </td>
                    <td className="py-3 px-4 text-xs text-muted-foreground">
                      Reported in <code className="bg-muted px-1.5 py-0.5 rounded text-[11px]">meta_out/meta_metrics.json</code> (PR-AUC Lift: 40.7×)
                    </td>
                  </tr>
                  <tr>
                    <td className="py-3 px-4 font-semibold text-foreground">
                      Subgroup Fairness
                    </td>
                    <td className="py-3 px-4 font-mono text-emerald-600 dark:text-emerald-400 font-medium">
                      Sensitivity &ge; 85%
                    </td>
                    <td className="py-3 px-4 text-xs text-muted-foreground">
                      Strict floor enforced in every demographic, rural, and socioeconomic stratum
                    </td>
                  </tr>
                  <tr>
                    <td className="py-3 px-4 font-semibold text-foreground">
                      Full Evaluation Suite
                    </td>
                    <td className="py-3 px-4" colSpan={2}>
                      <a
                        href="https://github.com/HYDRA-BD/LungCancer.NET"
                        target="_blank"
                        rel="noreferrer"
                        className="text-primary hover:underline font-medium inline-flex items-center gap-1.5 text-xs"
                      >
                        <span>See GitHub repo for full evaluation</span>
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <hr className="border-border" />

          {/* ═══════════════════════════════════════════════════════════
              11. LIMITATIONS & RESPONSIBLE AI
              ═══════════════════════════════════════════════════════════ */}
          <section id="responsible-ai" className="scroll-mt-24 space-y-6">
            <div className="flex items-center gap-2.5 text-xs font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400">
              <AlertTriangle className="w-4 h-4" />
              <span>Ethical Deployment & Boundary Governance</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground font-sans">
              Limitations & Responsible AI Disclosures
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              Clinical safety requires absolute transparency regarding model scope, LLM limitations, and deployment environment:
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-5 rounded-xl border border-amber-500/20 bg-amber-500/5 dark:bg-amber-950/10 space-y-2">
                <div className="flex items-center gap-2 font-bold text-foreground text-sm">
                  <ShieldCheck className="w-4 h-4 text-amber-500 shrink-0" />
                  <span>Clinical Decision-Support Only</span>
                </div>
                <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
                  This is a decision-support tool, not a diagnostic device. It computes statistical pre-screening risk from population surveys and cannot substitute for physical examination or LDCT radiography.
                </p>
              </div>

              <div className="p-5 rounded-xl border border-amber-500/20 bg-amber-500/5 dark:bg-amber-950/10 space-y-2">
                <div className="flex items-center gap-2 font-bold text-foreground text-sm">
                  <Brain className="w-4 h-4 text-amber-500 shrink-0" />
                  <span>Zero LLM Authority Over Triage</span>
                </div>
                <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
                  The LLM writes narratives only — it has zero authority over triage. The triage tiers (REFER / REVIEW / RULE-OUT) are governed exclusively by calibrated mathematical decision rules and the equity sensitivity floor.
                </p>
              </div>

              <div className="p-5 rounded-xl border border-amber-500/20 bg-amber-500/5 dark:bg-amber-950/10 space-y-2">
                <div className="flex items-center gap-2 font-bold text-foreground text-sm">
                  <Lock className="w-4 h-4 text-amber-500 shrink-0" />
                  <span>Ephemeral User Store (Free-Tier)</span>
                </div>
                <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
                  Free-tier deployment uses an ephemeral user store; sign up fresh after redeploys. Patient intake information is kept purely in RAM and never written to disk or database logs.
                </p>
              </div>

              <div className="p-5 rounded-xl border border-amber-500/20 bg-amber-500/5 dark:bg-amber-950/10 space-y-2">
                <div className="flex items-center gap-2 font-bold text-foreground text-sm">
                  <FileText className="w-4 h-4 text-amber-500 shrink-0" />
                  <span>Clinician Confirmation Required</span>
                </div>
                <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
                  Not FDA-cleared. All triage actions require clinician confirmation prior to issuing radiological orders, laboratory referrals, or therapeutic interventions.
                </p>
              </div>
            </div>
          </section>

          <hr className="border-border" />

          {/* ═══════════════════════════════════════════════════════════
              12. FOOTER
              ═══════════════════════════════════════════════════════════ */}
          <footer className="pt-8 border-t border-border space-y-6 text-sm text-muted-foreground">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-2 font-semibold text-foreground">
                <span className="text-xl">🫁</span>
                <span>LungCancer.NET</span>
                <span className="text-xs text-muted-foreground font-normal">
                  — Pre-Screening System
                </span>
              </div>

              <div className="flex flex-wrap items-center gap-6 text-xs">
                <a
                  href="https://github.com/HYDRA-BD/LungCancer.NET"
                  target="_blank"
                  rel="noreferrer"
                  className="hover:text-primary transition-colors flex items-center gap-1"
                >
                  <span>GitHub Repository</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
                <a
                  href="https://lungcancer-net.onrender.com/docs"
                  target="_blank"
                  rel="noreferrer"
                  className="hover:text-primary transition-colors flex items-center gap-1"
                >
                  <span>Backend API Docs</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
                <a
                  href="https://lungcancernetaicongrerss.vercel.app"
                  target="_blank"
                  rel="noreferrer"
                  className="hover:text-primary transition-colors flex items-center gap-1"
                >
                  <span>Live App (Vercel)</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>

            <div className="text-center sm:text-left text-xs text-muted-foreground pt-4 border-t border-border/50">
              Built for the International AI Builders Congress 2026. Designed for rural and underserved healthcare systems.
            </div>
          </footer>
        </main>
      </div>
    </div>
  );
}
