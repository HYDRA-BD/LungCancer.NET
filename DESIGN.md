# LungCancer.NET — Clinical Design System & Screen Specifications

## 1. Live Figma Architecture & Deliverables
- **Figma File**: [**LungCancer.NET — Clinical Design System**](https://www.figma.com/design/TuoSnymWvrUvvh29IHqHfx)
- **Design System Frame**: [`00-design-system` (Node 3:3)](https://www.figma.com/design/TuoSnymWvrUvvh29IHqHfx?node-id=3-3&autoplay-code-preview=3-3)
- **Full Screen Specifications**: [`01-login` through `05-pdf` (Node 11:3)](https://www.figma.com/design/TuoSnymWvrUvvh29IHqHfx?node-id=11-3&autoplay-code-preview=11-3)

---

## 2. Locked Design System Tokens (From 00-design-system)

### Colour System
- **Primary Clinical Blue**: `#1E3A8A` | **Primary Hover**: `#1E40AF`
- **Warm Teal (Hope)**: `#0D9488` | **Accent Soft**: `#14B8A6`
- **Success / RULE-OUT**: `#15803D`
- **Warning / REVIEW**: `#B45309`
- **Alert / REFER**: `#B91C1C` *(clinical terracotta, never neon)*
- **Light Surfaces**: Canvas `#FAFAF7`, Cards `#FFFFFF`, Text `#0F172A`, Secondary `#475569`, Border `#E2E8F0`
- **Dark Surfaces**: Canvas `#0F172A`, Cards `#1E293B`, Text `#F1F5F9`, Secondary `#94A3B8`, Border `#334155`

### Typography Hierarchy (Inter & JetBrains Mono)
- **Display / H1**: `32px` / 700 / `-0.02em` (Inter)
- **H2**: `24px` / 600 (Inter)
- **H3**: `20px` / 600 (Inter)
- **Body**: `18px` / 400 / `1.6` line-height (Inter) — *never smaller than 15px*
- **Small / Caption**: `15px` / 400 (Inter)
- **Clinical Value**: `40px` / 700 (JetBrains Mono Bold) — *never smaller than 24px*
- **Micro-Label**: `13px` / 500 / `UPPERCASE` / `0.08em` letterspacing

### Spacing & Elevation
- **Base Grid**: `8px` (`4px`, `8px`, `12px`, `16px`, `24px`, `32px`, `48px`, `64px`)
- **Card Padding**: `24px` | **Section Gap**: `32px` | **Form Gap**: `16px`
- **Border Radii**: Cards `12px`, Buttons `8px`, Inputs `8px`, Tier Badges `999px`
- **Elevations**:
  - Elevation 1 (Card default): `0 1px 3px rgba(15,23,42,0.06), 0 1px 2px rgba(15,23,42,0.04)`
  - Elevation 2 (Card elevated): `0 4px 12px rgba(15,23,42,0.08)`

---

## 3. Screen Specifications (Side-by-Side Light & Dark)

### `01-login` — Clinician & Auditor Authentication Gateway
- **Layout**: Centered card (~420px wide) with 24px padding.
- **Header**: Wordmark `🫁 LungCancer.NET` (H1: 32px / 700 / -0.02em) with subtitle `Clinical AI Pre-Screening & Triage Portal`.
- **Form Controls**:
  - Username or Clinical Email field (48px height, 8px radius, micro-label: 13px uppercase).
  - Password field (48px height, 8px radius).
  - Primary "Sign in to Clinical Portal" button (full width, 48px height, `#1E3A8A`).
  - Text link: "Create an account" (Teal `#0D9488` / `#14B8A6`).
- **Security & Privacy**: Zero sample credentials or demo usernames exposed on screen. Subtle security watermark footer.

### `02-signup` — Clinical Account Registration
- **Layout**: Centered card (~420px wide) with 24px padding.
- **Fields**:
  - Full Clinical Name (`Dr. Sarah Lin, MD`)
  - Clinical Email or Username (`slin_md@hospital.org`)
  - Role Assignment (`Clinician` vs `Auditor`)
  - Password (min 8 characters) with text-only hint: *"Must contain at least 8 characters with a mix of letters and numbers."*
  - Confirm Password
- **Actions**: Primary "Create account" button (48px height) and "Back to sign in" link.

### `03-intake` — Clinical Data Entry Stepper
- **Stepper Header**: 4-step linear flow with numbered bubble nodes:
  `1. Demographics` → `2. Inhalation` → `3. Comorbidities` → `4. Access & Equity`
- **Progress Track**: 6px progress bar with `#0D9488` teal fill.
- **Step 1 Card**: Patient Age (18–100), Biological Sex, and Location with 5-year historical AQI/PM2.5 auto-display.
- **Step 2 Card**: Average packs per day, total years smoked, and a prominent visual pack-years readout (`48.0 PK-YRS` in JetBrains Mono 40px bold) with USPSTF benchmark warning.
- **Step 3 Card**: Comorbidities presented as large interactive checkbox tiles (`COPD`, `Asthma`, `Coronary Heart Disease`, `Diabetes`).
- **Step 4 Card**: Healthcare Access & Equity Safeguards toggle tile.
- **Action Bar**: Persistent "Continue" button (`#1E3A8A`, 48px height).

### `04-results` — Clinical Triage & Explainable AI Dashboard
- **Hero Triage Card**:
  - REFER tier card in terracotta (`#B91C1C` border, light tint `#FEF2F2`, dark tint `#450A0A`).
  - Tier pill: `🚩 TIER: REFER` (999px radius).
  - Risk score: `24.87%` in JetBrains Mono 40px bold.
  - 95% Confidence Interval: `95% CI: [21.40% – 28.34%]`.
  - Action plan: `Action Plan: Immediate Low-Dose CT (LDCT) thoracic imaging order indicated.`
- **3 Structured Sections**:
  1. *Why This Result*: Real-time SHAP factor attribution horizontal bars (+0.12 smoking, +0.08 age, +0.06 COPD).
  2. *Clinical Evidence*: Matched USPSTF guideline citation with blue accent quote bar.
  3. *AI Summary*: On-device pulmonology narrative summary card.
- **Fixed Bottom Action Bar**: "Download Official PDF Report" (Primary 48px) and "New Patient Pre-Screening" (Secondary outline).

### `05-pdf` — Hospital-Grade Vector Clinical PDF Preview
- **Document Layout**: Single-page clinical documentation mockup (~800px width).
- **Navy Header**: Deep navy bar (`#0B2545`) with logo, institution name, Report ID, and date.
- **Demographics Table**: Clean tabular summary of de-identified patient record, age, sex, 5-yr AQI, BMI, and comorbidities.
- **Tier Banner**: Colored risk band with LDCT clinical order instructions.
- **Signature Block**: Physician orders checklist, attending pulmonologist signature line, license details, and SHA-256 cryptographic seal.
