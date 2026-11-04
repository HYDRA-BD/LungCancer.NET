/**
 * lib/format.ts — Null-safe number formatters for clinical values.
 * Use these instead of calling .toFixed() directly so that undefined /
 * NaN / non-finite values never crash the page.
 */

/** Format a numeric value to `digits` decimal places, or "—" if not finite. */
export function fmt(v: unknown, digits = 3): string {
  const n = typeof v === "number" ? v : Number(v);
  return Number.isFinite(n) ? n.toFixed(digits) : "—";
}

/** Format a 0-1 probability as a percentage string, or "—" if not finite. */
export function pct(v: unknown, digits = 2): string {
  const n = typeof v === "number" ? v : Number(v);
  return Number.isFinite(n) ? (n * 100).toFixed(digits) + "%" : "—";
}
