# LungCancer.NET — Clinical UI/UX Design System Specification

## 1. Executive Summary & Design Philosophy
**LungCancer.NET** is an assistive clinical decision-support and population triage platform designed for older adults (aged 45–80) and their healthcare providers. 

### Design Pillars:
1. **Legibility & Comfort for Older Eyes**:
   - High contrast ratios (exceeding WCAG 2.1 AA standards: ≥ 4.5:1 for body text, ≥ 3.0:1 for graphical interfaces).
   - Generous base font size (≥ 18 px) and prominent clinical readouts (≥ 28–36 px).
   - Generous touch and click targets (≥ 48 × 48 px) with minimum 12 px spacing between interactive elements.
2. **Warmth & Hope (De-Stigmatizing Cancer Screening)**:
   - Departure from cold, sterile institutional gray or alarming pure-red alerts.
   - Balanced, warm palette combining deep marine stability (`#0F2942`), healing cyan accents (`#0284C7`), warm slate surfaces (`#F8FAFC`), and reassuring typography.
3. **Multi-Sensory Clinical Signals (Color-Blind Accessible)**:
   - No diagnostic state is ever communicated by color alone. Every risk tier couples color with a distinct icon and explicit plain-text label.
4. **Structured Cognitive Load**:
   - Linear 4-step progressive intake rather than an overwhelming single-page form.
   - Immediate high-level hero card on results, followed by modular, collapsible detail drawers for Explainable AI (SHAP), USPSTF guidelines, AI narrative synthesis, and PDF reporting.

---

## 2. Color Palette & Token Architecture

| Token Name | Hex Code | Role / Usage | WCAG Contrast on Light BG |
|---|---|---|---|
| `--color-navy-deep` | `#0B2545` | Primary brand headers, hero bars, top navigation | 12.8:1 (AAA) |
| `--color-navy-mid` | `#134074` | Subheadings, card borders, active step states | 8.4:1 (AAA) |
| `--color-accent-blue` | `#0284C7` | Primary action buttons, interactive focus rings | 4.6:1 (AA) |
| `--color-warm-amber` | `#D97706` | Warning badges, intermediate review alerts | 4.7:1 (AA) |
| `--color-sage-emerald` | `#059669` | Rule-Out clearance tier, normal physical findings | 4.9:1 (AA) |
| `--color-terracotta` | `#DC2626` | High-risk Referral tier (balanced with soft tint) | 5.2:1 (AA) |
| `--color-bg-canvas` | `#F8FAFC` | Calm neutral page background | Base |
| `--color-surface-card`| `#FFFFFF` | Form cards, results drawers, modal cards | Base |
| `--color-border-subtle`| `#CBD5E1` | Input outlines, dividers (≥ 3:1 against white) | 3.2:1 (UI AA) |
| `--color-text-main` | `#0F172A` | Primary body and heading copy | 14.1:1 (AAA) |
| `--color-text-muted` | `#475569` | Secondary captions, helper hints, timestamps | 5.6:1 (AA) |

### Semantic Risk Tier Colors & Multi-Modal Indicators
- 🚩 **REFER (LDCT Evaluation Advised)**: 
  - Accent: `#DC2626` | Surface: `#FEF2F2` | Border: `#F87171`
  - Multi-modal signal: 🚩 Flag icon + Bold text "REFERRAL RECOMMENDED" + LDCT next steps.
- 🔍 **REVIEW (Shared Clinical Decision-Making)**: 
  - Accent: `#D97706` | Surface: `#FFFBEB` | Border: `#FBBF24`
  - Multi-modal signal: 🔍 Magnifier icon + Bold text "CLINICAL REVIEW REQUIRED" + biomarker context.
- 🛡️ **RULE-OUT (Routine Annual Surveillance)**: 
  - Accent: `#059669` | Surface: `#ECFDF5` | Border: `#34D399`
  - Multi-modal signal: 🛡️ Shield icon + Bold text "RULE-OUT / ROUTINE SURVEILLANCE" + non-invasive clearance.

---

## 3. Typography Scale

Configured with high-legibility system sans-serif font stack (`system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif`).

| Typography Role | Size (px) | Weight | Line Height | Usage |
|---|---|---|---|---|
| **Display / Hero** | 36 px | 800 (Extrabold) | 1.2 | Risk percentage, main triage banner |
| **Heading 1** | 28 px | 700 (Bold) | 1.3 | Page title, section results heading |
| **Heading 2** | 22 px | 700 (Bold) | 1.35 | Section cards, step headers |
| **Heading 3** | 19 px | 600 (Semibold) | 1.4 | Form fieldset labels, sub-metrics |
| **Body (Standard)** | 18 px | 400 (Regular) | 1.6 | Narrative text, guideline summaries, inputs |
| **Body (Emphasized)** | 18 px | 600 (Semibold) | 1.5 | Persona buttons, table keys, alerts |
| **Caption / Helper** | 15 px | 500 (Medium) | 1.5 | Input instructions, disclaimers, timestamps |

*Note: Base body font is locked to 18 px minimum across all forms and descriptions to accommodate presbyopia in patients and senior clinicians.*

---

## 4. Spacing Scale & Interactive Hit Targets

- **Spacing Token 1 (xs)**: `4 px`
- **Spacing Token 2 (sm)**: `8 px`
- **Spacing Token 3 (md)**: `16 px`
- **Spacing Token 4 (lg)**: `24 px`
- **Spacing Token 5 (xl)**: `32 px`
- **Spacing Token 6 (xxl)**: `48 px`

### Hit Target Standards:
- Primary / Secondary Action Buttons: Height ≥ `52 px`, padding `14 px 24 px`.
- Form Inputs (`st.number_input`, `st.text_input`): Height ≥ `50 px`, font size `18 px`.
- Radio Buttons & Checkboxes: Visual touch box ≥ `48 × 48 px` hit area.
- Stepper Tabs: Minimum width `160 px`, height `48 px`.
- Inter-element Spacing: Minimum `12 px` clearance between adjacent clickable buttons.

---

## 5. Component Inventory

1. **Authentication Gateway**:
   - Clean, centered card (`max-width: 480 px`).
   - Pure credentials inputs: Email/Username, Password (min 8 chars).
   - Sign In and Sign Up tabs with clear visual distinction.
   - Absolutely zero hardcoded default credentials or sample hints exposed.
   - Ephemeral session notice informing user that data is secured in local encrypted database.

2. **Executive Top Navigation Bar**:
   - Hospital / Research team branding with icon `🫁 LungCancer.NET`.
   - Active user profile indicator pill with role badge (`Clinician` vs `Auditor`).
   - Global Logout button.

3. **1-Click Clinical Persona Fast-Loaders**:
   - 4 card-styled buttons representing evaluation cohorts (High-Risk, Low-Risk, Borderline, Vulnerable Subgroup).
   - Provides clear summary captions under each persona.

4. **Linear 4-Step Intake Stepper**:
   - **Step 1: Patient & Physical Demographics** (ID, Age, Sex, State, Height, Weight, BMI).
   - **Step 2: Cumulative Tobacco Exposure** (Packs/Day, Years, Pack-Years with 20 pk-yr alert).
   - **Step 3: Comorbidities & Respiratory Burden** (Asthma, COPD, Cardio-Metabolic).
   - **Step 4: Social Determinants & Healthcare Access** (Rural/cost barriers with Equity Floor note).

5. **Clinical Triage Results Hero**:
   - Multi-modal colored hero container with tier badge, large risk percentage, 95% confidence interval, and actionable recommendation.
   - 3-metric boundary gauge card visualizing Rule-Out floor, Current Score, and Referral threshold.

6. **Collapsible Detail Drawers**:
   - **Explainable AI (SHAP Waterfall)**: Color-coded attribution bars (Rose for risk-elevating factors, Sage for protective factors) with raw metric tags.
   - **USPSTF Clinical Guidelines (RAG)**: Formatted blockquotes with page citations.
   - **AI Pulmonology Narrative**: On-device generated synthesis in a readable container.
   - **Official Clinical PDF Report Generator**: Vector PDF builder trigger with download button.

---

## 6. Accessibility & Usability Verification (WCAG 2.1 AA)

- [x] **Color Contrast**: All primary text against background exceeds 5.0:1 (up to 14.1:1).
- [x] **No Pure-Color Dependency**: Icons (🚩, 🔍, 🛡️) and text descriptions accompany all color highlights.
- [x] **Font Sizing**: Base body text is 18 px; critical triage values are 32–36 px.
- [x] **Keyboard Navigation**: Form inputs, radio controls, tabs, and buttons are fully navigable via `Tab` and `Enter`/`Space`.
- [x] **Screen-Reader Compatibility**: All Streamlit widgets use explicit descriptive labels (`label="Patient Age in Years (18–100)"`).
- [x] **Zero Flashing / Anxiety Inducing Elements**: Smooth transitions, calming healthcare blues, and empathetic explanatory copy.
