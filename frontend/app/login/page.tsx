"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { login } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Shield, Lock, Sun, Moon } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    // Check if already authenticated
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
    setIsLoading(true);
    try {
      await login(email, password);
      router.push("/intake");
    } catch {
      // toast is automatically handled by request helper in api.ts
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
            Clinical AI Pre-Screening & Triage Portal
          </p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
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
              placeholder="e.g. slin_md@hospital.org"
              className="w-full h-12 px-4 bg-background border border-border rounded-input text-body text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 transition-all"
            />
          </div>

          <div className="space-y-2">
            <label
              htmlFor="password"
              className="text-micro font-medium text-muted-foreground uppercase tracking-wider block"
            >
              Password
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
                <Lock className="w-5 h-5" />
              )}
              <span>{isLoading ? "Authenticating..." : "Sign in to Clinical Portal"}</span>
            </Button>
          </div>
        </form>

        {/* Footer Nav */}
        <div className="text-center pt-4 border-t border-border space-y-3">
          <p className="text-body text-muted-foreground break-words leading-relaxed">
            Need staff credentials?{" "}
            <Link
              href="/signup"
              className="font-semibold text-accent hover:text-accent-soft underline underline-offset-4"
            >
              Create an account
            </Link>
          </p>

          <div className="flex items-center justify-center gap-2 text-micro text-muted-foreground pt-1">
            <Shield className="w-4 h-4 text-accent shrink-0" />
            <span className="break-words">HIPAA & De-identification Compliant · Ephemeral Session Only</span>
          </div>
        </div>
      </div>
    </div>
  );
}
