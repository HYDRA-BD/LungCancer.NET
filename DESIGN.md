# LungCancer.NET — Locked Clinical Design System Specification

## 1. Design File & Figma Integration
- **Figma File Name**: `LungCancer.NET -- Clinical Design System`
- **Figma File Key**: `TuoSnymWvrUvvh29IHqHfx`
- **Live Figma URL**: [https://www.figma.com/design/TuoSnymWvrUvvh29IHqHfx](https://www.figma.com/design/TuoSnymWvrUvvh29IHqHfx)
- **Active Frame Deliverable**: `00-design-system` (Node ID: `3:3`)

---

## 2. Brand Feel & Emotional Tone
- **Clinical but Warm**: Designed to evoke a trusted family physician's consultation room rather than an alarm-inducing emergency triage display.
- **Older Adult Legibility (Ages 45–80)**: Every label, button, and value is legible without pinch-to-zoom.
- **Hopeful Triage Framing**: Even high-probability `REFER` findings are framed empathetically ("we detected this early and have an immediate diagnostic path"), mitigating screening anxiety.

---

## 3. Colour System (Locked Hex Codes)

| Token Name | Hex Code | Role & Meaning |
|---|---|---|
| **Primary (deep clinical blue)** | `#1E3A8A` | Foundation of trust, primary buttons, major headers |
| **Primary hover** | `#1E40AF` | Focused and pressed interaction states |
| **Accent (warm teal, hope)** | `#0D9488` | Care, clinical guidance, hope, positive progress |
| **Accent soft** | `#14B8A6` | Subtle accents, secondary highlights |
| **Success / RULE-OUT** | `#15803D` | Routine annual surveillance clearance |
| **Warning / REVIEW** | `#B45309` | Shared clinical decision-making & monitoring |
| **Alert / REFER** | `#B91C1C` | Diagnostic LDCT referral (controlled, non-neon) |
| **Background (light)** | `#FAFAF7` | Warm, calming light canvas |
| **Surface (light, cards)** | `#FFFFFF` | Form cards, hero containers |
| **Text primary (light)** | `#0F172A` | High-contrast body copy & headings |
| **Text secondary (light)** | `#475569` | Helper copy, timestamps |
| **Border (light)** | `#E2E8F0` | Card borders, dividers |
| **Background (dark)** | `#0F172A` | Deep slate canvas (never pure black) |
| **Surface (dark, cards)** | `#1E293B` | Elevated card surfaces |
| **Text primary (dark)** | `#F1F5F9` | Crisp dark-mode body copy |
| **Text secondary (dark)** | `#94A3B8` | Muted dark-mode secondary copy |
| **Border (dark)** | `#334155` | Subtle dark-mode card outlines |

---

## 4. Typography Scale & Hierarchy

| Role | Font Family | Size | Weight | Line-Height / Spacing |
|---|---|---|---|---|
| **Display / H1** | Inter | `32px` | 700 (Bold) | `-0.02em` letterspacing |
| **H2** | Inter | `24px` | 600 (Semibold) | `1.3` line-height |
| **H3** | Inter | `20px` | 600 (Semibold) | `1.35` line-height |
| **Body** | Inter | `18px` | 400 (Regular) | `1.6` line-height |
| **Small / Caption** | Inter | `15px` | 400 (Regular) | `1.5` line-height |
| **Clinical Value** | JetBrains Mono | `40px` | 700 (Bold) | `1.1` line-height |
| **Micro-Label** | Inter | `13px` | 500 (Medium) | `UPPERCASE` / `0.08em` letterspacing |

*Hard Rules:*
- Body text is **never** smaller than 15px.
- Clinical readouts are **never** smaller than 24px (standardized to 40px for hero values).
- All text containers strictly enforce `overflow-wrap: break-word` and `min-width: 0`.

---

## 5. Spacing System (8px Base Grid) & Radii

- **Grid Increments**: `4px`, `8px`, `12px`, `16px`, `24px`, `32px`, `48px`, `64px`
- **Card Internal Padding**: `24px`
- **Section Gap**: `32px`
- **Form Field Vertical Gap**: `16px`
- **Button Padding**: `14px × 24px` (minimum `48px` touch target)
- **Border Radii**:
  - Cards: `12px`
  - Buttons: `8px`
  - Inputs: `8px`
  - Tier Badges: `999px` (full pill)

---

## 6. Shadows & Elevation

- **Elevation 1 (Card default)**: `0 1px 3px rgba(15,23,42,0.06), 0 1px 2px rgba(15,23,42,0.04)`
- **Elevation 2 (Card elevated)**: `0 4px 12px rgba(15,23,42,0.08)`
- Zero glowing or saturated colored shadows.

---

## 7. Deliverable #1: Frame `00-design-system` Structure

The `00-design-system` frame has been constructed side-by-side in Light and Dark variants:
1. **Colour Swatches**: All 16 semantic and background tokens labeled with hex codes and roles.
2. **Typography Samples**: Full scale from 13px micro-label up to 40px JetBrains Mono clinical values.
3. **Button Variants**: Primary, Secondary, Ghost, and Disabled with $\ge 48\text{px}$ touch targets.
4. **Input Field States**: Default, Focused (active ring), Error (red border), and Disabled.
5. **Card Variants**: Default (elevation 1), Elevated (elevation 2), and Accent Header card.
6. **Tier Badges**:
   - 🚩 `REFERRAL RECOMMENDED · High Probability` (Terracotta `#B91C1C` + Flag icon)
   - 🔍 `CLINICAL REVIEW REQUIRED · Shared Decision-Making` (Warm Amber `#B45309` + Magnifier icon)
   - 🛡️ `RULE-OUT · Low Probability Routine Annual Screening` (Sage Green `#15803D` + Shield icon)
7. **Spacing Ruler**: Visual representation of the 8px baseline grid (`4px` through `64px`).
