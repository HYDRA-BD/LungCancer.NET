"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { getCurrentUser, logout, User } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  LogOut,
  User as UserIcon,
  Moon,
  Sun,
  Stethoscope,
  Eye,
} from "lucide-react";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    // Check initial dark mode from DOM / localStorage
    const isDarkMode =
      localStorage.getItem("theme") === "dark" ||
      document.documentElement.classList.contains("dark");
    setIsDark(isDarkMode);
    if (isDarkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }

    // Auth Guard: redirect to login if token or user is missing
    const token = localStorage.getItem("token");
    const currentUser = getCurrentUser();

    if (!token || !currentUser) {
      router.replace("/login");
    } else {
      setUser(currentUser);
    }
  }, [router, pathname]);

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

  return (
    <div
      className="min-h-screen flex flex-col bg-background text-foreground relative"
      suppressHydrationWarning
    >
      {/* FIX 4: Fixed Blurred Logo Background */}
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
      {/* Top Clinical Header */}
      <header className="sticky top-0 z-40 bg-card/95 backdrop-blur border-b border-border shadow-elevation-1">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
          {/* Logo & Navigation */}
          <Link
            href="/intake"
            className="flex items-center gap-2.5 font-bold text-h3 text-foreground hover:opacity-90 transition-opacity"
          >
            <span className="text-2xl" role="img" aria-label="lungs">
              🫁
            </span>
            <span className="tracking-tight">LungCancer.NET</span>
          </Link>

          {/* Right Header: User Info, Dark Mode Toggle, Logout */}
          <div className="flex items-center gap-3">
            {/* Dark Mode Toggle */}
            <button
              type="button"
              onClick={toggleDarkMode}
              title={isDark ? "Switch to Light Mode" : "Switch to Dark Mode"}
              className="p-2 rounded-button border border-border text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            >
              {isDark ? (
                <Sun className="w-4 h-4 text-amber-400" />
              ) : (
                <Moon className="w-4 h-4" />
              )}
            </button>

            {/* User & Role Display */}
            {user ? (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-button bg-secondary border border-border">
                <div className="w-7 h-7 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-caption">
                  {user.name ? user.name.charAt(0).toUpperCase() : <UserIcon className="w-3.5 h-3.5" />}
                </div>
                <div className="text-left hidden sm:block">
                  <div className="text-caption font-semibold text-foreground leading-tight">
                    {user.name}
                  </div>
                  <div className="flex items-center gap-1 text-micro text-muted-foreground capitalize">
                    {user.role === "clinician" ? (
                      <Stethoscope className="w-3 h-3 text-accent" />
                    ) : (
                      <Eye className="w-3 h-3 text-muted-foreground" />
                    )}
                    <span>{user.role}</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-button bg-secondary border border-border opacity-70">
                <UserIcon className="w-4 h-4 text-muted-foreground" />
                <span className="text-caption text-muted-foreground hidden sm:inline">
                  Clinical Session
                </span>
              </div>
            )}

            {/* Logout Button */}
            <Button
              variant="outline"
              size="sm"
              onClick={logout}
              className="h-9 px-3 rounded-button text-caption font-semibold flex items-center gap-1.5 text-destructive border-destructive/20 hover:bg-destructive/10"
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden sm:inline">Logout</span>
            </Button>
          </div>
        </div>
      </header>

      {/* Main App Content Wrapper with Consistent Horizontal & Vertical Breathing Room */}
      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
}
