import React from "react";
import { AlertTriangle, AlertCircle, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";

export type TierType = "REFER" | "REVIEW" | "RULE-OUT";

interface TierBadgeProps {
  tier: TierType;
  className?: string;
  size?: "default" | "lg";
}

export function TierBadge({ tier, className, size = "default" }: TierBadgeProps) {
  const configs = {
    REFER: {
      label: "TIER: REFER",
      icon: AlertTriangle,
      classes:
        "bg-red-500/10 text-red-700 border-red-500/20 dark:bg-red-500/20 dark:text-red-400 dark:border-red-500/30",
    },
    REVIEW: {
      label: "TIER: REVIEW",
      icon: AlertCircle,
      classes:
        "bg-amber-500/10 text-amber-700 border-amber-500/20 dark:bg-amber-500/20 dark:text-amber-400 dark:border-amber-500/30",
    },
    "RULE-OUT": {
      label: "TIER: RULE-OUT",
      icon: CheckCircle2,
      classes:
        "bg-emerald-500/10 text-emerald-700 border-emerald-500/20 dark:bg-emerald-500/20 dark:text-emerald-400 dark:border-emerald-500/30",
    },
  };

  const current = configs[tier] || configs.REVIEW;
  const Icon = current.icon;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 font-mono font-bold tracking-wider rounded-full border shadow-sm dark:shadow-none select-none",
        size === "lg" ? "px-5 py-2 text-lg" : "px-3.5 py-1 text-sm",
        current.classes,
        className
      )}
    >
      <Icon className={size === "lg" ? "w-5 h-5" : "w-4 h-4"} />
      <span>{current.label}</span>
    </span>
  );
}
