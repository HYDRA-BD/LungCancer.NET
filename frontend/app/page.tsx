import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowRight, Lock, Stethoscope, FileText, CheckCircle2 } from "lucide-react";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-4 sm:px-6 lg:px-8 py-10 bg-background text-foreground">
      <div className="max-w-xl w-full p-6 sm:p-8 bg-card rounded-card border border-border shadow-elevation-2 dark:shadow-none space-y-8 text-center">
        {/* Logo & Headline */}
        <div className="space-y-3">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 text-primary mb-2">
            <span className="text-4xl" role="img" aria-label="lungs">
              🫁
            </span>
          </div>
          <h1 className="text-h1 font-bold tracking-tight text-foreground font-sans break-words">
            LungCancer.NET
          </h1>
          <p className="text-body text-muted-foreground leading-relaxed break-words">
            Composite AI clinical pre-screening system using BRFSS population survey data. Targets low-cost screening for rural and underserved communities.
          </p>
        </div>

        {/* Feature Badges */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-left">
          <div className="p-4 bg-secondary rounded-input border border-border flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 text-accent shrink-0" />
            <span className="text-caption font-semibold text-foreground break-words">
              9-Predictor Ensemble Ladder
            </span>
          </div>
          <div className="p-4 bg-secondary rounded-input border border-border flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 text-accent shrink-0" />
            <span className="text-caption font-semibold text-foreground break-words">
              Equity-Aware Sensitivity Floor
            </span>
          </div>
        </div>

        {/* Direct Navigation Links */}
        <div className="space-y-4 pt-2">
          <Link href="/login" className="block w-full">
            <Button className="w-full h-12 px-6 text-body font-semibold bg-primary hover:bg-primary-hover text-primary-foreground rounded-button shadow-sm flex items-center justify-center gap-2 focus:ring-2 focus:ring-ring focus:ring-offset-2">
              <Lock className="w-5 h-5" />
              <span>Clinician & Auditor Portal</span>
              <ArrowRight className="w-4 h-4 ml-auto" />
            </Button>
          </Link>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Link href="/intake">
              <Button
                variant="outline"
                className="w-full h-12 px-6 text-body font-semibold rounded-button flex items-center justify-center gap-2 focus:ring-2 focus:ring-ring focus:ring-offset-2"
              >
                <Stethoscope className="w-4 h-4 text-accent" />
                <span>Patient Intake</span>
              </Button>
            </Link>

            <Link href="/results">
              <Button
                variant="outline"
                className="w-full h-12 px-6 text-body font-semibold rounded-button flex items-center justify-center gap-2 focus:ring-2 focus:ring-ring focus:ring-offset-2"
              >
                <FileText className="w-4 h-4 text-primary" />
                <span>Results Triage</span>
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}
