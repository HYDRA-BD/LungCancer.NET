"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { signup } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Shield,
  UserPlus,
  Stethoscope,
  Eye,
  ArrowLeft,
  Sun,
  Moon,
} from "lucide-react";

export default function SignupPage() {
  const router = useRouter();
  const [role, setRole] = useState<"clinician" | "auditor">("clinician");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    if (localStorage.getItem("token")) {
      router.replace("/intake");
    }
    const darkMode =
      localStorage.getItem("theme") === "dark" ||
      document.documentElement.classList.contains("dark");
    setIsDark(darkMode);
  }, [router]);

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setValidationError("Passwords do not match.");
      return;
    }
    if (password.length < 8) {
      setValidationError("Password must contain at least 8 characters.");
      return;
    }
    setValidationError(null);
    setIsLoading(true);

    try {
      await signup(name, email, password, role);
      router.push("/intake");
    } catch {
      // toast is automatically triggered by request helper
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      className="flex min-h-screen flex-col items-center justify-center px-4 sm:px-6 lg:px-8 py-10 bg-background text-foreground relative"
      suppressHydrationWarning
    >
      {/* Fixed Blurred Background Logo */}
      <div
        aria-hidden="true"
        className="fixed inset-0 -z-10 pointer-events-none opacity-[0.08] dark:opacity-[0.14] dark:brightness-200"
        style={{
          backgroundImage: "url(/logo.png)",
          backgroundSize: "contain",
          backgroundPosition: "center",
          backgroundRepeat: "no-repeat",
          filter: "blur(60px)",
        }}
      />
      {/* Dark Mode Switcher */}
      <button
        type="button"
        onClick={toggleDarkMode}
        aria-label="Toggle theme"
        className="absolute top-6 right-6 p-2.5 rounded-button border border-border bg-card text-muted-foreground hover:text-foreground shadow-sm transition-colors focus:ring-2 focus:ring-ring focus:ring-offset-2"
      >
        {isDark ? <Sun className="w-5 h-5 text-amber-400" /> : <Moon className="w-5 h-5" />}
      </button>

      <div className="w-full max-w-[480px] bg-card rounded-card border border-border shadow-elevation-1 dark:shadow-none p-6 sm:p-8 space-y-6">
        {/* Header Wordmark & Subtitle */}
        <div className="space-y-3 text-center">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-primary/10 text-primary mb-1">
            <span className="text-3xl" role="img" aria-label="lungs">
              🫁
            </span>
          </div>
          <h1 className="text-h1 font-bold text-foreground tracking-tight break-words">
            LungCancer.NET
          </h1>
          <p className="text-body text-muted-foreground leading-relaxed break-words">
            Create Clinical Staff Account
          </p>
        </div>

        {/* Role Selection */}
        <div className="space-y-2">
          <span className="text-micro font-medium text-muted-foreground uppercase tracking-wider block">
            Select Staff Role
          </span>
          <div className="grid grid-cols-2 gap-3 p-1.5 bg-secondary rounded-button border border-border">
            <button
              type="button"
              aria-label="Select Clinician Role"
              onClick={() => setRole("clinician")}
              className={`flex items-center justify-center gap-2 py-2.5 px-3 rounded-[6px] text-caption font-semibold transition-all focus:ring-2 focus:ring-ring ${
                role === "clinician"
                  ? "bg-card text-primary shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Stethoscope className="w-4 h-4" />
              Clinician (Full)
            </button>
            <button
              type="button"
              aria-label="Select Auditor Role"
              onClick={() => setRole("auditor")}
              className={`flex items-center justify-center gap-2 py-2.5 px-3 rounded-[6px] text-caption font-semibold transition-all focus:ring-2 focus:ring-ring ${
                role === "auditor"
                  ? "bg-card text-primary shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Eye className="w-4 h-4" />
              Auditor (Read-Only)
            </button>
          </div>
        </div>

        {validationError && (
          <div className="p-4 bg-destructive/10 border border-destructive/20 text-destructive text-body rounded-button">
            {validationError}
          </div>
        )}

        {/* Signup Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <label
              htmlFor="name"
              className="text-micro font-medium text-muted-foreground uppercase tracking-wider block"
            >
              Full Clinical Name
            </label>
            <input
              id="name"
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Dr. Sarah Lin, MD"
              className="w-full h-12 px-4 bg-background border border-border rounded-input text-body text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 transition-all"
            />
          </div>

          <div className="space-y-2">
            <label
              htmlFor="email"
              className="text-micro font-medium text-muted-foreground uppercase tracking-wider block"
            >
              Clinical Email Address
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="slin_md@hospital.org"
              className="w-full h-12 px-4 bg-background border border-border rounded-input text-body text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 transition-all"
            />
          </div>

          <div className="space-y-2">
            <label
              htmlFor="password"
              className="text-micro font-medium text-muted-foreground uppercase tracking-wider block"
            >
              Password (Min 8 characters)
            </label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full h-12 px-4 bg-background border border-border rounded-input text-body text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 transition-all"
            />
            <p className="text-caption text-muted-foreground pt-1 leading-relaxed">
              Must contain at least 8 characters with a mix of letters and numbers.
            </p>
          </div>

          <div className="space-y-2">
            <label
              htmlFor="confirmPassword"
              className="text-micro font-medium text-muted-foreground uppercase tracking-wider block"
            >
              Confirm Password
            </label>
            <input
              id="confirmPassword"
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full h-12 px-4 bg-background border border-border rounded-input text-body text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 transition-all"
            />
          </div>

          <div className="pt-2">
            <Button
              type="submit"
              disabled={isLoading}
              className="w-full h-12 px-6 text-body font-semibold bg-primary hover:bg-primary-hover text-primary-foreground rounded-button transition-all shadow-sm flex items-center justify-center gap-2 focus:ring-2 focus:ring-ring focus:ring-offset-2"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
              ) : (
                <UserPlus className="w-5 h-5" />
              )}
              <span>{isLoading ? "Creating Account..." : "Create Clinical Account"}</span>
            </Button>
          </div>
        </form>

        {/* Footer Nav */}
        <div className="text-center pt-4 border-t border-border space-y-3">
          <p className="text-body text-muted-foreground break-words leading-relaxed">
            Already registered?{" "}
            <Link
              href="/login"
              className="font-semibold text-accent hover:text-accent-soft underline underline-offset-4 inline-flex items-center gap-1.5"
            >
              <ArrowLeft className="w-4 h-4 inline" /> Back to sign in
            </Link>
          </p>

          <div className="flex items-center justify-center gap-2 text-micro text-muted-foreground pt-1">
            <Shield className="w-4 h-4 text-accent shrink-0" />
            <span className="break-words">Zero PII Stored to Disk · Role-Based Medical Governance</span>
          </div>
        </div>
      </div>
    </div>
  );
}
