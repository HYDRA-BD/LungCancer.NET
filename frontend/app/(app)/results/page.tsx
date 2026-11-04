"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AnalyzeResponse, getCurrentUser, User } from "@/lib/api";
import { fmt } from "@/lib/format";
import { TierBadge } from "@/components/ui/tier-badge";
import { Button } from "@/components/ui/button";
import {
  FileText,
  RotateCcw,
  Sparkles,
  ShieldCheck,
  BookOpen,
  Info,
  TrendingUp,
} from "lucide-react";

export default function ResultsPage() {
  const router = useRouter();
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const raw = sessionStorage.getItem("analysis");
    if (!raw) {
      router.replace("/intake");
      return;
    }

    try {
      const parsed: AnalyzeResponse = JSON.parse(raw);
      setAnalysis(parsed);
      setCurrentUser(getCurrentUser());
    } catch {
      router.replace("/intake");
    } finally {
      setIsLoading(false);
    }
  }, [router]);

  if (isLoading || !analysis) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-3 border-primary border-t-transparent rounded-full animate-spin" />
          <span className="text-body text-muted-foreground font-medium">
            Loading clinical analysis...
          </span>
        </div>
      </div>
    );
  }

  const { prediction, guidelines, summary, aqi, patient } = analysis;

  // ── Null-safe score formatting via fmt() ────────────────────────────────────
  // Backend returns a 0-1 probability; display as percentage.
  const rawScore = prediction.risk_score;
  const scorePercent = fmt(
    typeof rawScore === "number" && Number.isFinite(rawScore) && rawScore <= 1
      ? rawScore * 100
      : rawScore,
    2
  );

  const ciLowerNum =
    prediction.ci_lower !== undefined && prediction.ci_lower !== null
      ? prediction.ci_lower <= 1
        ? prediction.ci_lower * 100
        : prediction.ci_lower
      : null;
  const ciLower = ciLowerNum !== null ? fmt(ciLowerNum, 2) : null;

  const ciUpperNum =
    prediction.ci_upper !== undefined && prediction.ci_upper !== null
      ? prediction.ci_upper <= 1
        ? prediction.ci_upper * 100
        : prediction.ci_upper
      : null;
  const ciUpper = ciUpperNum !== null ? fmt(ciUpperNum, 2) : null;

  const tierStyles = {
    REFER: {
      bg: "bg-red-500/10 border-red-500/20 dark:bg-red-500/20 dark:border-red-500/30",
      text: "text-red-700 dark:text-red-400",
    },
    REVIEW: {
      bg: "bg-amber-500/10 border-amber-500/20 dark:bg-amber-500/20 dark:border-amber-500/30",
      text: "text-amber-700 dark:text-amber-400",
    },
    "RULE-OUT": {
      bg: "bg-emerald-500/10 border-emerald-500/20 dark:bg-emerald-500/20 dark:border-emerald-500/30",
      text: "text-emerald-700 dark:text-emerald-400",
    },
  };

  const currentStyle = tierStyles[prediction.tier] || tierStyles.REVIEW;
  const isClinician = currentUser?.role === "clinician";

  // ── Derived arrays with ?? [] guards ─────────────────────────────────────
  const shapItems = prediction.shap_items ?? [];
  const contributingFactors = prediction.contributing_factors ?? [];
  const matchedGuidelines = guidelines ?? [];

  // Pre-compute max abs SHAP value for bar scaling
  const maxAbsImpact = Math.max(
    ...shapItems.map((i) => Math.abs(i.impact ?? i.contribution ?? 0)),
    0.01
  );

  return (
    <div className="w-full max-w-4xl mx-auto space-y-8 pb-40">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 pb-6 border-b border-border">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-2 text-micro font-semibold uppercase tracking-wider text-accent">
            <Sparkles className="w-4 h-4" />
            Explainable Clinical Triage
          </div>
          <h1 className="text-h2 font-bold text-foreground break-words">
            Risk Stratification Assessment
          </h1>
        </div>

        <div className="text-caption font-mono text-muted-foreground">
          Subject:{" "}
          <strong className="text-foreground">
            {(patient as { patient_id?: string })?.patient_id || "PT-CURRENT"}
          </strong>
        </div>
      </div>

      {/* HERO TRIAGE BANNER */}
      <div
        className={`rounded-card border-2 p-6 sm:p-8 space-y-8 shadow-elevation-2 transition-all ${currentStyle.bg}`}
      >
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-2 border-b border-border/40">
          <TierBadge tier={prediction.tier} size="lg" />
          {aqi && aqi.aqi_5yr !== null && aqi.aqi_5yr !== undefined && (
            <div className="text-caption font-mono text-muted-foreground">
              Regional AQI:{" "}
              <strong className="text-foreground">
                {fmt(aqi.aqi_5yr, 1)}
              </strong>{" "}
              (PM2.5: {fmt(aqi.pm25_5yr, 1)} µg/m³)
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8 items-center">
          <div className="space-y-2">
            <span className="text-micro font-medium uppercase tracking-wider text-muted-foreground block">
              Calculated Ensemble Risk Probability
            </span>
            <div
              className={`text-4xl md:text-clinical-val font-mono font-bold tracking-tight ${currentStyle.text}`}
            >
              {scorePercent}%
            </div>
            {ciLower && ciUpper && (
              <div className="text-caption font-mono text-muted-foreground pt-1">
                95% CI: [{ciLower}% – {ciUpper}%]
              </div>
            )}
          </div>

          <div className="p-6 bg-card/90 rounded-card border border-border/60 shadow-sm space-y-2">
            <div className="flex items-center gap-2 text-caption font-bold text-foreground uppercase tracking-wider">
              <Info className="w-4 h-4 text-accent" />
              Clinical Recommendation
            </div>
            <p className="text-body font-semibold text-foreground leading-relaxed break-words">
              {prediction.recommendation}
            </p>
          </div>
        </div>
      </div>

      {/* SECTION 1: SHAP Factor Attribution */}
      {shapItems.length > 0 && (
        <div className="bg-card rounded-card border border-border shadow-elevation-1 dark:shadow-none p-6 sm:p-8 space-y-6">
          <div className="flex items-center justify-between gap-4 pb-2 border-b border-border/40">
            <div className="flex items-center gap-2.5">
              <TrendingUp className="w-5 h-5 text-primary" />
              <h2 className="text-h3 font-semibold text-foreground break-words">
                1. Why This Result: SHAP Factor Attribution
              </h2>
            </div>
            <span className="text-caption text-muted-foreground font-mono">
              Meta-Learner Contributions
            </span>
          </div>

          <p className="text-body text-muted-foreground leading-relaxed break-words">
            Out-of-fold cross-validated SHAP explainers measure each feature&apos;s positive or negative pull toward LDCT referral:
          </p>

          <div className="space-y-4 pt-2">
            {shapItems.map((item, idx) => {
              // Backend returns `impact`; fall back to `contribution` for
              // any older cached sessions still in sessionStorage.
              const contrib = item.impact ?? item.contribution ?? 0;
              const isPositive = contrib >= 0;
              const absVal = Math.abs(contrib);
              const barWidth = Math.min(
                Math.round((absVal / maxAbsImpact) * 100),
                100
              );

              return (
                <div key={idx} className="space-y-2">
                  <div className="flex justify-between text-caption font-semibold gap-3">
                    <span className="text-foreground break-words">
                      {item.label ?? item.feature}
                    </span>
                    <span
                      className={`font-mono font-bold shrink-0 ${
                        isPositive ? "text-destructive" : "text-accent"
                      }`}
                    >
                      {isPositive ? `+${fmt(contrib, 3)}` : fmt(contrib, 3)}
                    </span>
                  </div>
                  <div className="w-full h-3 bg-muted rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        isPositive ? "bg-destructive" : "bg-accent"
                      }`}
                      style={{ width: `${barWidth}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* SECTION 1b: Contributing Factors (tuple format from backend) */}
      {contributingFactors.length > 0 && (
        <div className="bg-card rounded-card border border-border shadow-elevation-1 dark:shadow-none p-6 sm:p-8 space-y-4">
          <div className="flex items-center gap-2.5 pb-2 border-b border-border/40">
            <Info className="w-5 h-5 text-primary" />
            <h2 className="text-h3 font-semibold text-foreground break-words">
              Contributing Risk Factors
            </h2>
          </div>
          <div className="space-y-2">
            {contributingFactors.map(([kind, text], i) => {
              const kindLower = (kind ?? "").toLowerCase();
              const accent =
                kindLower === "alert" || kindLower === "high"
                  ? "border-destructive text-destructive"
                  : kindLower === "warning" || kindLower === "medium"
                  ? "border-amber-500 text-amber-700 dark:text-amber-400"
                  : "border-accent text-accent";
              return (
                <div
                  key={i}
                  className={`pl-4 border-l-2 text-body ${accent}`}
                >
                  {text}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* SECTION 2: Matched Guidelines */}
      {matchedGuidelines.length > 0 && (
        <div className="bg-card rounded-card border border-border shadow-elevation-1 dark:shadow-none p-6 sm:p-8 space-y-6">
          <div className="flex items-center gap-2.5 pb-2 border-b border-border/40">
            <BookOpen className="w-5 h-5 text-primary" />
            <h2 className="text-h3 font-semibold text-foreground break-words">
              2. Matched USPSTF Clinical Evidence
            </h2>
          </div>

          <div className="space-y-4">
            {matchedGuidelines.map((g, idx) => (
              <div
                key={idx}
                className="p-6 bg-secondary/70 border-l-4 border-primary rounded-r-card space-y-3"
              >
                <div className="flex items-center justify-between text-caption font-bold text-primary uppercase tracking-wider gap-3">
                  <span>Guideline Excerpt #{idx + 1}</span>
                  {g.page !== undefined && (
                    <span className="text-muted-foreground font-mono shrink-0">
                      Page {g.page}
                    </span>
                  )}
                </div>
                <p className="text-body text-foreground italic leading-relaxed break-words">
                  &quot;{g.text}&quot;
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SECTION 3: Clinical Summary */}
      {summary && (
        <div className="bg-card rounded-card border border-border shadow-elevation-1 dark:shadow-none p-6 sm:p-8 space-y-6">
          <div className="flex items-center gap-2.5 pb-2 border-b border-border/40">
            <ShieldCheck className="w-5 h-5 text-accent" />
            <h2 className="text-h3 font-semibold text-foreground break-words">
              3. AI Pulmonology Clinical Summary
            </h2>
          </div>
          <div className="p-6 rounded-input border border-border bg-background text-body text-foreground leading-relaxed break-words">
            {summary}
          </div>
        </div>
      )}

      {/* FIXED BOTTOM ACTION BAR */}
      <div className="fixed bottom-0 left-0 right-0 bg-card/95 backdrop-blur-md border-t border-border p-4 sm:p-6 shadow-elevation-2 z-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="text-caption text-muted-foreground hidden sm:block">
            {isClinician
              ? "Clinician verified · PDF report generation enabled"
              : "Auditor mode · Read-only review"}
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <Link href="/intake" className="flex-1 sm:flex-initial">
              <Button
                variant="outline"
                className="w-full h-12 px-6 rounded-button text-body font-semibold flex items-center justify-center gap-2 focus:ring-2 focus:ring-ring focus:ring-offset-2"
              >
                <RotateCcw className="w-4 h-4" />
                <span>New Pre-Screening</span>
              </Button>
            </Link>

            {/* Generate PDF: visible ONLY for clinicians */}
            {isClinician && (
              <Link href="/report" className="flex-1 sm:flex-initial">
                <Button className="w-full h-12 px-8 rounded-button text-body font-semibold bg-primary hover:bg-primary-hover text-primary-foreground shadow-sm flex items-center justify-center gap-2 focus:ring-2 focus:ring-ring focus:ring-offset-2">
                  <FileText className="w-5 h-5" />
                  <span>Generate PDF</span>
                </Button>
              </Link>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
