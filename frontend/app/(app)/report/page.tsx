"use client";

import React, { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { generateReport, PatientInputData } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import {
  FileCheck,
  ArrowLeft,
  Download,
  Loader2,
  AlertCircle,
} from "lucide-react";

export default function ReportPage() {
  const router = useRouter();
  const [status, setStatus] = useState<"loading" | "started" | "error">(
    "loading"
  );
  const [filename, setFilename] = useState("");
  const [, setPatientId] = useState("");
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const blobUrlRef = useRef<string | null>(null);

  useEffect(() => {
    return () => {
      if (blobUrlRef.current) {
        URL.revokeObjectURL(blobUrlRef.current);
      }
    };
  }, []);

  useEffect(() => {
    const rawPatient = sessionStorage.getItem("patient");
    if (!rawPatient) {
      router.replace("/intake");
      return;
    }

    async function processReport() {
      try {
        const patient: PatientInputData = JSON.parse(rawPatient!);
        const pid = patient.patient_id || "PATIENT";
        setPatientId(pid);

        console.log("Generating report for:", pid);
        const pdfBlob = await generateReport(patient);
        const generatedFilename = `LungCancer_${pid}_${Date.now()}.pdf`;
        setFilename(generatedFilename);

        if (blobUrlRef.current) {
          URL.revokeObjectURL(blobUrlRef.current);
        }
        const url = window.URL.createObjectURL(pdfBlob);
        blobUrlRef.current = url;
        setBlobUrl(url);

        // Trigger auto-download
        const a = document.createElement("a");
        a.href = url;
        a.download = generatedFilename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        toast.success(`Downloaded report for ${pid}`);
        setStatus("started");
      } catch {
        setStatus("error");
      }
    }

    processReport();
  }, [router]);

  return (
    <div className="min-h-[75vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full bg-card rounded-card border border-border shadow-elevation-2 dark:shadow-none p-6 sm:p-8 space-y-6 text-center">
        {status === "loading" && (
          <div className="space-y-4 py-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 text-primary mb-2">
              <Loader2 className="w-8 h-8 animate-spin" />
            </div>
            <h1 className="text-h2 font-bold text-foreground break-words">
              Generating Clinical PDF
            </h1>
            <p className="text-body text-muted-foreground leading-relaxed break-words">
              Rendering vector charts, SHAP factor explanations, and cryptographically sealing patient documentation...
            </p>
          </div>
        )}

        {status === "started" && (
          <div className="space-y-6 animate-fadeIn">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500/10 text-emerald-700 border border-emerald-500/20 dark:bg-emerald-500/20 dark:text-emerald-400 dark:border-emerald-500/30 mb-2">
              <FileCheck className="w-8 h-8" />
            </div>
            <div className="space-y-2">
              <h1 className="text-h2 font-bold text-foreground break-words">
                Download Started
              </h1>
              <p className="text-body text-muted-foreground pt-1 leading-relaxed break-words">
                Your hospital-grade clinical report has been compiled and saved to your device.
              </p>
            </div>

            {filename && (
              <div className="p-4 bg-secondary rounded-input border border-border font-mono text-caption text-foreground break-all">
                {filename}
              </div>
            )}

            <div className="space-y-3 pt-4">
              {blobUrl && (
                <a
                  href={blobUrl}
                  download={filename}
                  className="block w-full"
                >
                  <Button
                    variant="outline"
                    className="w-full h-12 px-6 text-body font-semibold rounded-button flex items-center justify-center gap-2 focus:ring-2 focus:ring-ring focus:ring-offset-2"
                  >
                    <Download className="w-4 h-4" />
                    <span>Download Again</span>
                  </Button>
                </a>
              )}

              <Link href="/results" className="block w-full">
                <Button className="w-full h-12 px-8 text-body font-semibold bg-primary hover:bg-primary-hover text-primary-foreground rounded-button shadow-sm flex items-center justify-center gap-2 focus:ring-2 focus:ring-ring focus:ring-offset-2">
                  <ArrowLeft className="w-4 h-4" />
                  <span>Back to Results</span>
                </Button>
              </Link>
            </div>
          </div>
        )}

        {status === "error" && (
          <div className="space-y-6">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-destructive/10 text-destructive mb-2">
              <AlertCircle className="w-8 h-8" />
            </div>
            <div className="space-y-2">
              <h1 className="text-h2 font-bold text-foreground break-words">
                Report Generation Failed
              </h1>
              <p className="text-body text-muted-foreground pt-1 leading-relaxed break-words">
                Could not generate the clinical report. Ensure you are signed in with a Clinician account and the backend is running.
              </p>
            </div>

            <Link href="/results" className="block w-full pt-4">
              <Button className="w-full h-12 px-6 text-body font-semibold rounded-button">
                Back to Results
              </Button>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
