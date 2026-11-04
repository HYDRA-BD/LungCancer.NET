"use client";

import React, { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { getStates, analyze, StateAQI, PatientInputData } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  User,
  Cigarette,
  Activity,
  HeartHandshake,
  ArrowRight,
  ArrowLeft,
  Sparkles,
  Info,
  Check,
  Loader2,
  Scale,
} from "lucide-react";

// ── Types ────────────────────────────────────────────────────────────────────

interface IntakeFormData {
    age: number;
  sex: number; // 1 = Male, 2 = Female
  state: string;
  unit: "metric" | "imperial";
  weightKg: number;
  weightLbs: number;
  heightCm: number;
  heightFt: number;
  heightIn: number;
  packsPerDay: number;
  yearsSmoked: number;
  packYears: number;
  asthma: boolean;
  copd: boolean;
  respBurden: boolean;
  heartAttack: boolean;
  chd: boolean;
  stroke: boolean;
  diabetes: boolean;
  chronicBurden: boolean;
  lowAccess: boolean;
}

export default function IntakePage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState<number>(0); // 0 to 3 (Steps 1 to 4)
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [statesList, setStatesList] = useState<StateAQI[]>([]);
  const [isLoadingStates, setIsLoadingStates] = useState(true);

  // Clear old state on navigation back to /intake
  useEffect(() => {
    if (typeof window !== "undefined") {
      sessionStorage.removeItem("analysis");
      sessionStorage.removeItem("patient");
      sessionStorage.removeItem("patient_id");
      sessionStorage.removeItem("pdf_blob");
      sessionStorage.removeItem("pdf_url");
      sessionStorage.removeItem("pdf_filename");
    }
  }, []);

  // Single Form State Object across step navigation
  const [formData, setFormData] = useState<IntakeFormData>({
    age: 66,
    sex: 1, // Male
    state: "Ohio",
    unit: "imperial",
    weightKg: 89.1,
    weightLbs: 192,
    heightCm: 180,
    heightFt: 5,
    heightIn: 10,
    packsPerDay: 1.0,
    yearsSmoked: 32,
    packYears: 32,
    copd: true,
    asthma: false,
    respBurden: true,
    chd: true,
    heartAttack: false,
    stroke: false,
    diabetes: true,
    chronicBurden: true,
    lowAccess: false,
  });

  // Load States on mount
  useEffect(() => {
    async function loadStatesData() {
      try {
        const data = await getStates();
        setStatesList(data);
        if (data.length > 0 && !data.some((s) => s.name === formData.state)) {
          setFormData((prev) => ({ ...prev, state: data[0].name }));
        }
      } catch {
        // Handled by API request toast
      } finally {
        setIsLoadingStates(false);
      }
    }
    loadStatesData();
  }, [formData.state]);

  // Automatic BMI Calculation
  const { bmi, bmiCategory, bmiColorClass, heightWeightStr } = useMemo(() => {
    let calculatedBmi = 26.4;
    let hwStr = "";

    if (formData.unit === "metric") {
      const heightM = Math.max(formData.heightCm / 100, 0.5);
      calculatedBmi = formData.weightKg / (heightM * heightM);
      hwStr = `${formData.heightCm} cm · ${formData.weightKg} kg`;
    } else {
      const totalInches = Math.max(formData.heightFt * 12 + formData.heightIn, 20);
      calculatedBmi = (703 * formData.weightLbs) / (totalInches * totalInches);
      hwStr = `${formData.heightFt}'${formData.heightIn}" · ${formData.weightLbs} lbs`;
    }

    const roundedBmi = parseFloat(calculatedBmi.toFixed(1));

    let cat = "Normal";
    let colorClass =
      "bg-emerald-500/10 text-emerald-700 border-emerald-500/20 dark:bg-emerald-500/20 dark:text-emerald-400 dark:border-emerald-500/30";

    if (roundedBmi < 18.5) {
      cat = "Underweight";
      colorClass =
        "bg-red-500/10 text-red-700 border-red-500/20 dark:bg-red-500/20 dark:text-red-400 dark:border-red-500/30";
    } else if (roundedBmi >= 18.5 && roundedBmi <= 24.9) {
      cat = "Normal";
      colorClass =
        "bg-emerald-500/10 text-emerald-700 border-emerald-500/20 dark:bg-emerald-500/20 dark:text-emerald-400 dark:border-emerald-500/30";
    } else if (roundedBmi >= 25.0 && roundedBmi <= 29.9) {
      cat = "Overweight";
      colorClass =
        "bg-amber-500/10 text-amber-700 border-amber-500/20 dark:bg-amber-500/20 dark:text-amber-400 dark:border-amber-500/30";
    } else {
      cat = "Obese";
      colorClass =
        "bg-red-500/10 text-red-700 border-red-500/20 dark:bg-red-500/20 dark:text-red-400 dark:border-red-500/30";
    }

    return {
      bmi: roundedBmi,
      bmiCategory: cat,
      bmiColorClass: colorClass,
      heightWeightStr: hwStr,
    };
  }, [
    formData.unit,
    formData.weightKg,
    formData.weightLbs,
    formData.heightCm,
    formData.heightFt,
    formData.heightIn,
  ]);

  // Quick Persona Loaders
  const loadPersona = (type: "high" | "moderate" | "low") => {
    if (type === "high") {
      setFormData((prev) => ({
        ...prev,
        age: 66,
        sex: 1,
        state: "Ohio",
        unit: "imperial",
        weightLbs: 192,
        heightFt: 5,
        heightIn: 10,
        weightKg: 89.1,
        heightCm: 180,
        packsPerDay: 1.0,
        yearsSmoked: 32,
        packYears: 32,
        copd: true,
        asthma: false,
        respBurden: true,
        chd: true,
        heartAttack: false,
        diabetes: true,
        stroke: false,
        chronicBurden: true,
        lowAccess: false,
      }));
    } else if (type === "moderate") {
      setFormData((prev) => ({
        ...prev,
        age: 45,
        sex: 2,
        state: "Vermont",
        unit: "metric",
        weightKg: 73.5,
        heightCm: 175,
        weightLbs: 149,
        heightFt: 5,
        heightIn: 6,
        packsPerDay: 0.5,
        yearsSmoked: 10,
        packYears: 5,
        copd: false,
        asthma: false,
        respBurden: false,
        chd: false,
        heartAttack: false,
        diabetes: false,
        stroke: false,
        chronicBurden: false,
        lowAccess: false,
      }));
    } else {
      setFormData((prev) => ({
        ...prev,
        age: 25,
        sex: 2,
        state: "Maine",
        unit: "metric",
        weightKg: 63.6,
        heightCm: 170,
        weightLbs: 128,
        heightFt: 5,
        heightIn: 4,
        packsPerDay: 0,
        yearsSmoked: 0,
        packYears: 0,
        copd: false,
        asthma: false,
        respBurden: false,
        chd: false,
        heartAttack: false,
        diabetes: false,
        stroke: false,
        chronicBurden: false,
        lowAccess: false,
      }));
    }
  };

  // Validation
  const canAdvance = useMemo(() => {
    if (currentStep === 0) {
      if (formData.age < 18 || formData.age > 120) return false;
      if (!formData.state) return false;
      if (formData.unit === "metric") {
        if (formData.weightKg < 30 || formData.weightKg > 250) return false;
        if (formData.heightCm < 100 || formData.heightCm > 250) return false;
      } else {
        if (formData.weightLbs < 65 || formData.weightLbs > 550) return false;
        if (formData.heightFt < 3 || formData.heightFt > 8) return false;
      }
      return true;
    }
    if (currentStep === 1) {
      if (formData.packsPerDay < 0 || formData.yearsSmoked < 0) return false;
      return true;
    }
    return true;
  }, [currentStep, formData]);

  const handleNext = () => {
    if (currentStep < 3) {
      setCurrentStep((prev) => prev + 1);
    } else {
      handleSubmit();
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    const freshPatientId = `P-${Date.now().toString().slice(-5)}`;
    const patientPayload: PatientInputData = {
      patient_id: freshPatientId,
      age: formData.age,
      bmi,
      pack_years: formData.packYears,
      resp_burden: formData.respBurden,
      chronic_burden: formData.chronicBurden,
      low_access: formData.lowAccess,
      sex: formData.sex,
      state: formData.state,
      packs_per_day: formData.packsPerDay,
      years_smoked: formData.yearsSmoked,
      asthma: formData.asthma,
      copd: formData.copd,
      heart_attack: formData.heartAttack,
      chd: formData.chd,
      stroke: formData.stroke,
      diabetes: formData.diabetes,
      height_weight: heightWeightStr,
    };

    try {
      const response = await analyze(patientPayload);
      if (typeof window !== "undefined") {
        sessionStorage.removeItem("analysis");
        sessionStorage.removeItem("patient");
        sessionStorage.removeItem("pdf_blob");
        sessionStorage.removeItem("pdf_url");
        sessionStorage.removeItem("pdf_filename");
        sessionStorage.removeItem("patient_id");

        sessionStorage.setItem("analysis", JSON.stringify(response));
        sessionStorage.setItem("patient", JSON.stringify(response.patient));
        const genPid =
          (response.patient as { patient_id?: string })?.patient_id ||
          freshPatientId;
        sessionStorage.setItem("patient_id", genPid);
      }
      router.push("/results");
    } catch {
      // toast shown automatically by API helper
    } finally {
      setIsSubmitting(false);
    }
  };

  const stepMeta = [
    { num: 1, title: "Demographics", icon: User },
    { num: 2, title: "Inhalation", icon: Cigarette },
    { num: 3, title: "Comorbidities", icon: Activity },
    { num: 4, title: "Access & Equity", icon: HeartHandshake },
  ];

  const currentStateData = statesList.find((s) => s.name === formData.state);

  return (
    <div className="w-full max-w-3xl mx-auto space-y-8">
      {/* Top Header & Quick Personas */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 pb-6 border-b border-border">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-2 text-micro font-semibold uppercase tracking-wider text-accent">
            <Sparkles className="w-4 h-4" />
            Clinical Intake & Assessment
          </div>
          <h1 className="text-h2 font-bold text-foreground break-words">
            Patient Pre-Screening
          </h1>
        </div>

        <div className="flex flex-col items-start sm:items-end gap-1.5">
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-caption text-muted-foreground">
              Quick Persona:
            </span>
            <button
              type="button"
              aria-label="Load High Risk Persona"
              onClick={() => loadPersona("high")}
              className="px-3.5 py-2 rounded-button text-caption font-semibold bg-red-500/10 text-red-700 border border-red-500/20 dark:bg-red-500/20 dark:text-red-400 dark:border-red-500/30 hover:opacity-90 transition-all focus:outline-none focus:ring-2 focus:ring-ring"
            >
              High Risk (Refer)
            </button>
            <button
              type="button"
              aria-label="Load Moderate Risk Persona"
              onClick={() => loadPersona("moderate")}
              className="px-3.5 py-2 rounded-button text-caption font-semibold bg-amber-500/10 text-amber-700 border border-amber-500/20 dark:bg-amber-500/20 dark:text-amber-400 dark:border-amber-500/30 hover:opacity-90 transition-all focus:outline-none focus:ring-2 focus:ring-ring"
            >
              Moderate (Review)
            </button>
            <button
              type="button"
              aria-label="Load Low Risk Persona"
              onClick={() => loadPersona("low")}
              className="px-3.5 py-2 rounded-button text-caption font-semibold bg-emerald-500/10 text-emerald-700 border border-emerald-500/20 dark:bg-emerald-500/20 dark:text-emerald-400 dark:border-emerald-500/30 hover:opacity-90 transition-all focus:outline-none focus:ring-2 focus:ring-ring"
            >
              Low Risk (Rule-Out)
            </button>
          </div>
          <p className="text-caption text-muted-foreground">
            Each persona is tuned to demonstrate a different triage tier.
          </p>
        </div>
      </div>

      {/* Horizontal Stepper with Proper Vertical Padding */}
      <div className="py-6 space-y-4">
        <div className="grid grid-cols-4 gap-3">
          {stepMeta.map((s, idx) => {
            const isCompleted = idx < currentStep;
            const isCurrent = idx === currentStep;

            return (
              <button
                key={s.num}
                type="button"
                aria-label={`Jump to step ${s.num}: ${s.title}`}
                onClick={() => {
                  if (idx <= currentStep || canAdvance) {
                    setCurrentStep(idx);
                  }
                }}
                className={`flex flex-col sm:flex-row items-center gap-3 p-3 sm:p-4 rounded-button border text-left transition-all ${
                  isCurrent
                    ? "bg-card border-primary ring-2 ring-primary/20 shadow-sm dark:shadow-none"
                    : isCompleted
                    ? "bg-secondary/60 border-border text-foreground hover:bg-secondary"
                    : "bg-background border-border text-muted-foreground opacity-60 cursor-not-allowed"
                }`}
              >
                {/* Stepper Circles */}
                <div
                  className={`w-9 h-9 sm:w-10 sm:h-10 rounded-full flex items-center justify-center font-bold text-caption shrink-0 transition-colors ${
                    isCompleted
                      ? "bg-primary text-primary-foreground"
                      : isCurrent
                      ? "border-2 border-primary text-primary bg-background"
                      : "border border-border text-muted-foreground bg-muted/40"
                  }`}
                >
                  {isCompleted ? <Check className="w-4 h-4 sm:w-5 sm:h-5" /> : s.num}
                </div>
                <span className="text-caption font-semibold hidden sm:inline truncate">
                  {s.title}
                </span>
              </button>
            );
          })}
        </div>

        {/* Continuous Progress Track */}
        <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${((currentStep + 1) / 4) * 100}%` }}
          />
        </div>
      </div>

      {/* ONE Card containing ONLY the active step with min 24px padding */}
      <div className="bg-card rounded-card border border-border shadow-elevation-1 dark:shadow-none p-6 sm:p-8 space-y-8">
        {currentStep === 0 && (
          <Step1Demographics
            formData={formData}
            setFormData={setFormData}
            statesList={statesList}
            isLoadingStates={isLoadingStates}
            currentStateData={currentStateData}
            bmi={bmi}
            bmiCategory={bmiCategory}
            bmiColorClass={bmiColorClass}
          />
        )}

        {currentStep === 1 && (
          <Step2Smoking formData={formData} setFormData={setFormData} />
        )}

        {currentStep === 2 && (
          <Step3Comorbidities formData={formData} setFormData={setFormData} />
        )}

        {currentStep === 3 && (
          <Step4Access formData={formData} setFormData={setFormData} />
        )}

        {/* Bottom Navigation Buttons: 24px+ margin and internal padding */}
        <div className="mt-8 pt-6 border-t border-border flex items-center justify-between gap-4">
          <Button
            type="button"
            variant="outline"
            disabled={currentStep === 0 || isSubmitting}
            onClick={handleBack}
            className="h-12 px-6 rounded-button text-body font-semibold flex items-center gap-2 focus:ring-2 focus:ring-ring focus:ring-offset-2"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back</span>
          </Button>

          <Button
            type="button"
            disabled={!canAdvance || isSubmitting}
            onClick={handleNext}
            className="h-12 px-8 rounded-button text-body font-semibold bg-primary hover:bg-primary-hover text-primary-foreground shadow-sm flex items-center gap-2 ml-auto focus:ring-2 focus:ring-ring focus:ring-offset-2"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Running Analysis...</span>
              </>
            ) : currentStep === 3 ? (
              <>
                <span>Run Analysis</span>
                <ArrowRight className="w-4 h-4" />
              </>
            ) : (
              <>
                <span>Continue</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

// ── STEP 1 COMPONENT: DEMOGRAPHICS & ANTHROPOMETRICS ─────────────────────────

function Step1Demographics({
  formData,
  setFormData,
  statesList,
  isLoadingStates,
  currentStateData,
  bmi,
  bmiCategory,
  bmiColorClass,
}: {
  formData: IntakeFormData;
  setFormData: React.Dispatch<React.SetStateAction<IntakeFormData>>;
  statesList: StateAQI[];
  isLoadingStates: boolean;
  currentStateData?: StateAQI;
  bmi: number;
  bmiCategory: string;
  bmiColorClass: string;
}) {
  return (
    <div className="animate-in fade-in duration-300 space-y-8">
      <div className="space-y-2">
        <h2 className="text-h3 font-semibold text-foreground break-words">
          Step 1: Patient Demographics, Physical Attributes & Location
        </h2>
        <p className="text-body text-muted-foreground leading-relaxed break-words">
          Baseline characteristics used to determine age risk and compute BMI.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 sm:gap-8">
        {/* Patient Age */}
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <label
              htmlFor="patient-age"
              className="text-micro font-medium uppercase tracking-wider text-muted-foreground"
            >
              Patient Age (Years)
            </label>
            <span className="text-body font-bold font-mono text-primary">
              {formData.age} YRS
            </span>
          </div>
          <input
            id="patient-age"
            type="range"
            min={18}
            max={100}
            value={formData.age}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, age: Number(e.target.value) }))
            }
            className="w-full accent-primary h-2 bg-muted rounded-lg cursor-pointer focus:outline-none focus:ring-2 focus:ring-ring"
          />
          <div className="flex justify-between text-caption text-muted-foreground font-mono">
            <span>18</span>
            <span>50 (USPSTF minimum)</span>
            <span>100</span>
          </div>
        </div>

        {/* Biological Sex */}
        <div className="space-y-2">
          <label className="text-micro font-medium uppercase tracking-wider text-muted-foreground block">
            Biological Sex
          </label>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              aria-label="Select Biological Sex Male"
              onClick={() => setFormData((prev) => ({ ...prev, sex: 1 }))}
              className={`h-12 px-4 rounded-input border font-semibold text-body transition-all focus:outline-none focus:ring-2 focus:ring-ring ${
                formData.sex === 1
                  ? "bg-primary/10 border-primary text-primary"
                  : "border-border bg-background hover:bg-muted text-foreground"
              }`}
            >
              Male
            </button>
            <button
              type="button"
              aria-label="Select Biological Sex Female"
              onClick={() => setFormData((prev) => ({ ...prev, sex: 2 }))}
              className={`h-12 px-4 rounded-input border font-semibold text-body transition-all focus:outline-none focus:ring-2 focus:ring-ring ${
                formData.sex === 2
                  ? "bg-primary/10 border-primary text-primary"
                  : "border-border bg-background hover:bg-muted text-foreground"
              }`}
            >
              Female
            </button>
          </div>
        </div>
      </div>

      {/* Body Measurements Card with 24px+ Padding */}
      <div className="p-6 sm:p-8 bg-secondary/50 rounded-card border border-border space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-border/60">
          <div className="flex items-center gap-2.5">
            <Scale className="w-5 h-5 text-accent" />
            <span className="text-body font-semibold text-foreground">
              Body Metrics
            </span>
          </div>

          {/* Unit Toggle */}
          <div className="inline-flex p-1.5 bg-background rounded-button border border-border gap-1.5">
            <button
              type="button"
              aria-label="Switch to Metric units (kg, cm)"
              onClick={() => setFormData((prev) => ({ ...prev, unit: "metric" }))}
              className={`px-3 py-1.5 text-caption font-semibold rounded-[6px] transition-all focus:outline-none focus:ring-2 focus:ring-ring ${
                formData.unit === "metric"
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Metric (kg, cm)
            </button>
            <button
              type="button"
              aria-label="Switch to Imperial units (lbs, ft/in)"
              onClick={() => setFormData((prev) => ({ ...prev, unit: "imperial" }))}
              className={`px-3 py-1.5 text-caption font-semibold rounded-[6px] transition-all focus:outline-none focus:ring-2 focus:ring-ring ${
                formData.unit === "imperial"
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Imperial (lbs, ft/in)
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {/* Weight Field */}
          <div className="space-y-2">
            <label
              htmlFor="weight-input"
              className="text-micro font-medium uppercase tracking-wider text-muted-foreground block"
            >
              {formData.unit === "metric" ? "Weight (kg)" : "Weight (lbs)"}
            </label>
            {formData.unit === "metric" ? (
              <input
                id="weight-input"
                type="number"
                min={30}
                max={250}
                step={0.5}
                value={formData.weightKg}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    weightKg: parseFloat(e.target.value) || 0,
                  }))
                }
                className="w-full h-12 px-4 bg-background border border-border rounded-input text-body text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              />
            ) : (
              <input
                id="weight-input"
                type="number"
                min={65}
                max={550}
                step={0.5}
                value={formData.weightLbs}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    weightLbs: parseFloat(e.target.value) || 0,
                  }))
                }
                className="w-full h-12 px-4 bg-background border border-border rounded-input text-body text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              />
            )}
          </div>

          {/* Height Field */}
          <div className="space-y-2">
            <label
              htmlFor={formData.unit === "metric" ? "height-cm" : "height-ft"}
              className="text-micro font-medium uppercase tracking-wider text-muted-foreground block"
            >
              {formData.unit === "metric" ? "Height (cm)" : "Height (Feet & Inches)"}
            </label>
            {formData.unit === "metric" ? (
              <input
                id="height-cm"
                type="number"
                min={100}
                max={250}
                step={1}
                value={formData.heightCm}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    heightCm: parseInt(e.target.value, 10) || 0,
                  }))
                }
                className="w-full h-12 px-4 bg-background border border-border rounded-input text-body text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              />
            ) : (
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <input
                    id="height-ft"
                    aria-label="Height Feet"
                    type="number"
                    min={3}
                    max={8}
                    step={1}
                    value={formData.heightFt}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        heightFt: parseInt(e.target.value, 10) || 0,
                      }))
                    }
                    placeholder="Feet"
                    className="w-full h-12 px-4 bg-background border border-border rounded-input text-body text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                  />
                  <span className="text-micro text-muted-foreground block">
                    Feet (3–8)
                  </span>
                </div>
                <div className="space-y-1">
                  <input
                    id="height-in"
                    aria-label="Height Inches"
                    type="number"
                    min={0}
                    max={11}
                    step={1}
                    value={formData.heightIn}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        heightIn: parseInt(e.target.value, 10) || 0,
                      }))
                    }
                    placeholder="Inches"
                    className="w-full h-12 px-4 bg-background border border-border rounded-input text-body text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                  />
                  <span className="text-micro text-muted-foreground block">
                    Inches (0–11)
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Read-Only Calculated BMI Readout */}
        <div className="pt-4 border-t border-border flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="text-lg font-medium text-foreground">
            Calculated BMI:{" "}
            <span className="font-mono font-bold text-primary">
              {bmi} kg/m²
            </span>
          </div>

          <span
            className={`inline-flex items-center px-4 py-1.5 rounded-full text-caption font-semibold border ${bmiColorClass}`}
          >
            {bmiCategory} ({bmi} kg/m²)
          </span>
        </div>
      </div>

      {/* State Residency Dropdown */}
      <div className="space-y-3 pt-6 border-t border-border">
        <label
          htmlFor="state-select"
          className="text-micro font-medium uppercase tracking-wider text-muted-foreground block"
        >
          Residency State (5-Year Historical AQI Match)
        </label>
        {isLoadingStates ? (
          <div className="h-12 flex items-center px-4 border border-border rounded-input text-caption text-muted-foreground bg-muted">
            <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Loading state ambient indices...
          </div>
        ) : (
          <select
            id="state-select"
            value={formData.state}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, state: e.target.value }))
            }
            className="w-full h-12 px-4 bg-background border border-border rounded-input text-body text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          >
            {statesList.map((st) => (
              <option key={st.name} value={st.name}>
                {st.name}
                {st.aqi_5yr !== null ? ` — AQI ${st.aqi_5yr.toFixed(1)}` : ""}
              </option>
            ))}
          </select>
        )}

        {currentStateData && (
          <div className="flex items-center gap-3 p-4 sm:p-5 bg-secondary rounded-input text-caption text-muted-foreground border border-border">
            <Info className="w-5 h-5 text-accent shrink-0" />
            <span className="leading-relaxed">
              Regional exposure:{" "}
              <strong className="text-foreground">
                {currentStateData.name} — AQI{" "}
                {currentStateData.aqi_5yr?.toFixed(1) ?? "N/A"}
              </strong>{" "}
              (PM2.5: {currentStateData.pm25_5yr?.toFixed(1) ?? "N/A"} µg/m³)
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

// ── STEP 2 COMPONENT: INHALATION / SMOKING ───────────────────────────────────

function Step2Smoking({
  formData,
  setFormData,
}: {
  formData: IntakeFormData;
  setFormData: React.Dispatch<React.SetStateAction<IntakeFormData>>;
}) {
  const handlePacksChange = (packs: number) => {
    setFormData((prev) => ({
      ...prev,
      packsPerDay: packs,
      packYears: parseFloat((packs * prev.yearsSmoked).toFixed(1)),
    }));
  };

  const handleYearsChange = (years: number) => {
    setFormData((prev) => ({
      ...prev,
      yearsSmoked: years,
      packYears: parseFloat((prev.packsPerDay * years).toFixed(1)),
    }));
  };

  return (
    <div className="animate-in fade-in duration-300 space-y-8">
      <div className="space-y-2">
        <h2 className="text-h3 font-semibold text-foreground break-words">
          Step 2: Inhalation History & Tobacco Exposure
        </h2>
        <p className="text-body text-muted-foreground leading-relaxed break-words">
          Quantify cumulative tobacco history to evaluate against the USPSTF 20 pack-year benchmark.
        </p>
      </div>

      {/* Visual Pack-Years Readout with 24px+ Padding */}
      <div className="p-6 sm:p-8 bg-secondary/80 rounded-card border border-border flex flex-col sm:flex-row items-center justify-between gap-6">
        <div className="space-y-1 text-center sm:text-left">
          <span className="text-micro font-medium uppercase tracking-wider text-muted-foreground block">
            Cumulative Exposure Index
          </span>
          <div className="text-clinical-val font-mono font-bold text-primary tracking-tight">
            {formData.packYears.toFixed(1)}{" "}
            <span className="text-h3 font-sans text-muted-foreground">
              PK-YRS
            </span>
          </div>
        </div>
        <div className="text-center sm:text-right max-w-xs space-y-2">
          <div className="inline-block px-4 py-1.5 rounded-full text-caption font-semibold bg-accent/15 text-accent border border-accent/20">
            USPSTF Benchmark: ≥ 20.0
          </div>
          <p className="text-caption text-muted-foreground leading-relaxed">
            {formData.packYears >= 20
              ? "Exceeds traditional USPSTF screening threshold."
              : "Below 20 pk-yrs benchmark; ML ensemble evaluates multi-factor risk."}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 sm:gap-8">
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <label
              htmlFor="packs-per-day-range"
              className="text-micro font-medium uppercase tracking-wider text-muted-foreground"
            >
              Average Packs Per Day
            </label>
            <span className="text-body font-bold font-mono text-primary">
              {formData.packsPerDay} packs/day
            </span>
          </div>
          <input
            id="packs-per-day-range"
            type="range"
            min={0.1}
            max={4.0}
            step={0.1}
            value={formData.packsPerDay}
            onChange={(e) => handlePacksChange(parseFloat(e.target.value))}
            className="w-full accent-primary h-2 bg-muted rounded-lg cursor-pointer focus:outline-none focus:ring-2 focus:ring-ring"
          />
          <div className="flex justify-between text-caption text-muted-foreground font-mono">
            <span>0.1</span>
            <span>2.0</span>
            <span>4.0</span>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <label
              htmlFor="years-smoked-range"
              className="text-micro font-medium uppercase tracking-wider text-muted-foreground"
            >
              Total Duration Smoked
            </label>
            <span className="text-body font-bold font-mono text-primary">
              {formData.yearsSmoked} years
            </span>
          </div>
          <input
            id="years-smoked-range"
            type="range"
            min={1}
            max={60}
            value={formData.yearsSmoked}
            onChange={(e) => handleYearsChange(parseInt(e.target.value, 10))}
            className="w-full accent-primary h-2 bg-muted rounded-lg cursor-pointer focus:outline-none focus:ring-2 focus:ring-ring"
          />
          <div className="flex justify-between text-caption text-muted-foreground font-mono">
            <span>1 yr</span>
            <span>30 yrs</span>
            <span>60 yrs</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── STEP 3 COMPONENT: COMORBIDITIES ──────────────────────────────────────────

function Step3Comorbidities({
  formData,
  setFormData,
}: {
  formData: IntakeFormData;
  setFormData: React.Dispatch<React.SetStateAction<IntakeFormData>>;
}) {
  const toggleCopd = () => {
    setFormData((prev) => {
      const next = !prev.copd;
      return { ...prev, copd: next, respBurden: next || prev.asthma };
    });
  };

  const toggleAsthma = () => {
    setFormData((prev) => {
      const next = !prev.asthma;
      return { ...prev, asthma: next, respBurden: prev.copd || next };
    });
  };

  const toggleChd = () => {
    setFormData((prev) => {
      const next = !prev.chd;
      return {
        ...prev,
        chd: next,
        chronicBurden: next || prev.heartAttack || prev.stroke || prev.diabetes,
      };
    });
  };

  const toggleHeartAttack = () => {
    setFormData((prev) => {
      const next = !prev.heartAttack;
      return {
        ...prev,
        heartAttack: next,
        chronicBurden: prev.chd || next || prev.stroke || prev.diabetes,
      };
    });
  };

  const toggleStroke = () => {
    setFormData((prev) => {
      const next = !prev.stroke;
      return {
        ...prev,
        stroke: next,
        chronicBurden: prev.chd || prev.heartAttack || next || prev.diabetes,
      };
    });
  };

  const toggleDiabetes = () => {
    setFormData((prev) => {
      const next = !prev.diabetes;
      return {
        ...prev,
        diabetes: next,
        chronicBurden: prev.chd || prev.heartAttack || prev.stroke || next,
      };
    });
  };

  return (
    <div className="animate-in fade-in duration-300 space-y-8">
      <div className="space-y-2">
        <h2 className="text-h3 font-semibold text-foreground break-words">
          Step 3: Diagnosed Respiratory & Chronic Disease Conditions
        </h2>
        <p className="text-body text-muted-foreground leading-relaxed break-words">
          Select active conditions documented in the patient chart.
        </p>
      </div>

      {/* Respiratory Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between pb-1">
          <span className="text-caption font-bold uppercase tracking-wider text-muted-foreground">
            Respiratory Burden
          </span>
          <span
            className={`text-caption font-semibold px-3 py-1 rounded-full ${
              formData.respBurden
                ? "bg-accent/15 text-accent"
                : "bg-muted text-muted-foreground"
            }`}
          >
            {formData.respBurden ? "Burden Active" : "No Burden"}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
          <button
            type="button"
            aria-label="Toggle COPD condition"
            onClick={toggleCopd}
            className={`p-6 rounded-card border text-left transition-all flex items-start gap-4 focus:outline-none focus:ring-2 focus:ring-ring ${
              formData.copd
                ? "bg-primary/10 border-primary ring-1 ring-primary/20 text-foreground"
                : "bg-background border-border hover:bg-muted text-muted-foreground"
            }`}
          >
            <div
              className={`w-6 h-6 rounded flex items-center justify-center shrink-0 border mt-0.5 ${
                formData.copd
                  ? "bg-primary border-primary text-primary-foreground"
                  : "border-border bg-card"
              }`}
            >
              {formData.copd && <Check className="w-4 h-4" />}
            </div>
            <div className="space-y-1">
              <div className="text-body font-semibold text-foreground">
                COPD / Emphysema
              </div>
              <div className="text-caption text-muted-foreground leading-relaxed">
                Chronic bronchitis or chronic airflow limitation
              </div>
            </div>
          </button>

          <button
            type="button"
            aria-label="Toggle Asthma condition"
            onClick={toggleAsthma}
            className={`p-6 rounded-card border text-left transition-all flex items-start gap-4 focus:outline-none focus:ring-2 focus:ring-ring ${
              formData.asthma
                ? "bg-primary/10 border-primary ring-1 ring-primary/20 text-foreground"
                : "bg-background border-border hover:bg-muted text-muted-foreground"
            }`}
          >
            <div
              className={`w-6 h-6 rounded flex items-center justify-center shrink-0 border mt-0.5 ${
                formData.asthma
                  ? "bg-primary border-primary text-primary-foreground"
                  : "border-border bg-card"
              }`}
            >
              {formData.asthma && <Check className="w-4 h-4" />}
            </div>
            <div className="space-y-1">
              <div className="text-body font-semibold text-foreground">
                Bronchial Asthma
              </div>
              <div className="text-caption text-muted-foreground leading-relaxed">
                Active inhaler prescription reliance
              </div>
            </div>
          </button>
        </div>
      </div>

      {/* Chronic Disease Section */}
      <div className="space-y-4 pt-8 border-t border-border">
        <div className="flex items-center justify-between pb-1">
          <span className="text-caption font-bold uppercase tracking-wider text-muted-foreground">
            Chronic Systemic Disease Burden
          </span>
          <span
            className={`text-caption font-semibold px-3 py-1 rounded-full ${
              formData.chronicBurden
                ? "bg-accent/15 text-accent"
                : "bg-muted text-muted-foreground"
            }`}
          >
            {formData.chronicBurden ? "Burden Active" : "No Burden"}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
          <button
            type="button"
            aria-label="Toggle Coronary Heart Disease"
            onClick={toggleChd}
            className={`p-6 rounded-card border text-left transition-all flex items-start gap-4 focus:outline-none focus:ring-2 focus:ring-ring ${
              formData.chd
                ? "bg-primary/10 border-primary ring-1 ring-primary/20 text-foreground"
                : "bg-background border-border hover:bg-muted text-muted-foreground"
            }`}
          >
            <div
              className={`w-6 h-6 rounded flex items-center justify-center shrink-0 border mt-0.5 ${
                formData.chd
                  ? "bg-primary border-primary text-primary-foreground"
                  : "border-border bg-card"
              }`}
            >
              {formData.chd && <Check className="w-4 h-4" />}
            </div>
            <div className="space-y-1">
              <div className="text-body font-semibold text-foreground">
                Coronary Heart Disease (CHD)
              </div>
              <div className="text-caption text-muted-foreground leading-relaxed">
                Angina pectoris or coronary arterial disease
              </div>
            </div>
          </button>

          <button
            type="button"
            aria-label="Toggle Myocardial Infarction"
            onClick={toggleHeartAttack}
            className={`p-6 rounded-card border text-left transition-all flex items-start gap-4 focus:outline-none focus:ring-2 focus:ring-ring ${
              formData.heartAttack
                ? "bg-primary/10 border-primary ring-1 ring-primary/20 text-foreground"
                : "bg-background border-border hover:bg-muted text-muted-foreground"
            }`}
          >
            <div
              className={`w-6 h-6 rounded flex items-center justify-center shrink-0 border mt-0.5 ${
                formData.heartAttack
                  ? "bg-primary border-primary text-primary-foreground"
                  : "border-border bg-card"
              }`}
            >
              {formData.heartAttack && <Check className="w-4 h-4" />}
            </div>
            <div className="space-y-1">
              <div className="text-body font-semibold text-foreground">
                Myocardial Infarction
              </div>
              <div className="text-caption text-muted-foreground leading-relaxed">
                Prior heart attack documented in history
              </div>
            </div>
          </button>

          <button
            type="button"
            aria-label="Toggle Diabetes Mellitus"
            onClick={toggleDiabetes}
            className={`p-6 rounded-card border text-left transition-all flex items-start gap-4 focus:outline-none focus:ring-2 focus:ring-ring ${
              formData.diabetes
                ? "bg-primary/10 border-primary ring-1 ring-primary/20 text-foreground"
                : "bg-background border-border hover:bg-muted text-muted-foreground"
            }`}
          >
            <div
              className={`w-6 h-6 rounded flex items-center justify-center shrink-0 border mt-0.5 ${
                formData.diabetes
                  ? "bg-primary border-primary text-primary-foreground"
                  : "border-border bg-card"
              }`}
            >
              {formData.diabetes && <Check className="w-4 h-4" />}
            </div>
            <div className="space-y-1">
              <div className="text-body font-semibold text-foreground">
                Diabetes Mellitus
              </div>
              <div className="text-caption text-muted-foreground leading-relaxed">
                Type 1 or Type 2 on glycemic management
              </div>
            </div>
          </button>

          <button
            type="button"
            aria-label="Toggle Cerebrovascular Stroke"
            onClick={toggleStroke}
            className={`p-6 rounded-card border text-left transition-all flex items-start gap-4 focus:outline-none focus:ring-2 focus:ring-ring ${
              formData.stroke
                ? "bg-primary/10 border-primary ring-1 ring-primary/20 text-foreground"
                : "bg-background border-border hover:bg-muted text-muted-foreground"
            }`}
          >
            <div
              className={`w-6 h-6 rounded flex items-center justify-center shrink-0 border mt-0.5 ${
                formData.stroke
                  ? "bg-primary border-primary text-primary-foreground"
                  : "border-border bg-card"
              }`}
            >
              {formData.stroke && <Check className="w-4 h-4" />}
            </div>
            <div className="space-y-1">
              <div className="text-body font-semibold text-foreground">
                Cerebrovascular Event (Stroke)
              </div>
              <div className="text-caption text-muted-foreground leading-relaxed">
                History of transient ischemic attack or stroke
              </div>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}

// ── STEP 4 COMPONENT: ACCESS & EQUITY ────────────────────────────────────────

function Step4Access({
  formData,
  setFormData,
}: {
  formData: IntakeFormData;
  setFormData: React.Dispatch<React.SetStateAction<IntakeFormData>>;
}) {
  return (
    <div className="animate-in fade-in duration-300 space-y-8">
      <div className="space-y-2">
        <h2 className="text-h3 font-semibold text-foreground break-words">
          Step 4: Healthcare Access & Cost Barriers
        </h2>
        <p className="text-body text-muted-foreground leading-relaxed break-words">
          The ensemble meta-learner incorporates an access-aware penalty matrix to safeguard patients facing systemic barriers.
        </p>
      </div>

      <div className="space-y-4">
        <button
          type="button"
          aria-label="Toggle Low Healthcare Access Flag"
          onClick={() =>
            setFormData((prev) => ({ ...prev, lowAccess: !prev.lowAccess }))
          }
          className={`w-full p-6 sm:p-8 rounded-card border text-left transition-all flex items-start gap-5 focus:outline-none focus:ring-2 focus:ring-ring ${
            formData.lowAccess
              ? "bg-accent/10 border-accent ring-1 ring-accent/20 text-foreground"
              : "bg-background border-border hover:bg-muted text-muted-foreground"
          }`}
        >
          <div
            className={`w-6 h-6 rounded flex items-center justify-center shrink-0 border mt-1 ${
              formData.lowAccess
                ? "bg-accent border-accent text-accent-foreground"
                : "border-border bg-card"
            }`}
          >
            {formData.lowAccess && <Check className="w-4 h-4" />}
          </div>
          <div className="space-y-2">
            <div className="text-body font-semibold text-foreground break-words">
              Low Healthcare Access Flag (Cost Barrier / Rural / No Routine Checkup)
            </div>
            <p className="text-caption text-muted-foreground leading-relaxed break-words">
              Patient reports cost-related care delays, resides in a designated rural or Medically Underserved Area (MUA), or lacks a routine checkup within the past 12 months.
            </p>
            <div className="inline-block mt-2 px-3 py-1 bg-accent/15 text-accent rounded text-micro font-semibold uppercase">
              Weights missed-case penalty 1.4× in Meta-Learner
            </div>
          </div>
        </button>
      </div>
    </div>
  );
}
