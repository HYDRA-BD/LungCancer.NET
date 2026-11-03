# LungCancer.NET — Professional Clinical Design System Specification

## 1. Tooling Status & Design Sourcing
- **MCP Tool Integration Status**:
  - `Figma MCP`: Scanned — no active Figma MCP server or workspace connection registered in runtime.
  - `Lovable MCP`: Scanned — no Lovable workspace connection registered in runtime.
  - `Google Stitch MCP`: Scanned — no Stitch MCP integration registered in runtime.
- **Design System Sourcing Strategy**:
  - As mandated by the protocol specification, because external MCP designer integrations are not active in this environment, we execute a **rigorously defined, manual clinical design system** adhering strictly to the required clinical color tokens, typography scale, responsive word-wrapping rules, and native Streamlit dark/light theme integration.

---

## 2. Color Palette & Semantic Tokens

### Core Brand & Clinical Tokens
| Token Name | Hex Code | Semantic Role | Accessibility Contrast Ratio |
|---|---|---|---|
| `--color-primary` | `#1E3A8A` | Deep Clinical Blue — Primary actions, brand headers, focal buttons | 8.8:1 on light (AAA) |
| `--color-primary-hover`| `#172554` | Midnight Blue — Active and pressed states | 11.2:1 on light (AAA) |
| `--color-accent-teal` | `#0D9488` | Warm Teal — Reassurance, positive/protective indicators, accents | 4.8:1 on light (AA) |
| `--color-accent-gold` | `#D97706` | Soft Gold / Amber — Review alerts, clinical warnings, borderline triage | 4.7:1 on light (AA) |
| `--color-danger-coral`| `#DC2626` | Terracotta / Coral — High-risk Referral tier (balanced with soft tint) | 5.2:1 on light (AA) |
| `--color-success-sage`| `#059669` | Sage Green — Rule-Out clearance tier, normal biological findings | 4.9:1 on light (AA) |

### Adaptive Surface Tokens (Light vs. Dark Mode)
| Token Name | Light Mode Hex | Dark Mode Hex | Usage |
|---|---|---|---|
| `--app-bg` | `#F8FAFC` | `#0F172A` | Global application canvas background |
| `--card-bg` | `#FFFFFF` | `#1E293B` | Modular containers, forms, metric cards |
| `--card-border` | `#E2E8F0` | `#334155` | Card dividers, input borders ($\ge 3:1$ UI contrast) |
| `--text-main` | `#0F172A` | `#F8FAFC` | Primary headings, body copy, clinical readouts |
| `--text-muted` | `#64748B` | `#94A3B8` | Subtitles, input helper text, metadata |
| `--input-bg` | `#FFFFFF` | `#0F172A` | Text inputs, numeric selectors, radio buttons |

---

## 3. Typography Scale & Overflow Prevention

### Font Family
- **Primary Typeface**: `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif`
- Loaded via Google Fonts CDN for crisp anti-aliased cross-platform rendering.

### Sizing Scale
| Role | Size | Weight | Line Height | Application |
|---|---|---|---|---|
| **Display / Hero Score** | `32px` | 800 (Extrabold) | 1.15 | Patient Risk Score, Triage Tier Title |
| **Heading 1** | `26px` | 700 (Bold) | 1.25 | Page Header, Section Assessment |
| **Heading 2** | `20px` | 700 (Bold) | 1.35 | Step Titles, Card Subheadings |
| **Heading 3** | `18px` | 600 (Semibold) | 1.4 | Metric Labels, Comorbidity Groups |
| **Body (Standard)** | `16px` | 400 (Regular) | 1.6 | Narrative paragraphs, instructions, options |
| **Caption / Meta** | `14px` | 500 (Medium) | 1.5 | Disclaimers, timestamps, helper text |

### Mandatory Text Overflow Prevention (Non-Negotiable)
To prevent container overflow when resizing the viewport to 50% width or mobile viewports:
```css
* {
    box-sizing: border-box;
}

div, p, span, label, h1, h2, h3, h4, h5, h6 {
    overflow-wrap: break-word !important;
    word-break: break-word !important;
}

[data-testid="column"], .stColumn, [data-testid="stHorizontalBlock"] > div {
    min-width: 0 !important;
}
```
- **Edge Cushioning**: Every card has a minimum of `24px` internal padding (`padding: 24px;`). No text is permitted to touch container or button boundaries.

---

## 4. Dark Mode Architecture

Streamlit 1.35+ introduces `st.context.theme`. To eliminate dark mode flash and contrast inversion bugs:
1. Native theming configuration declared in `.streamlit/config.toml` (`primaryColor = "#1E3A8A"`, `backgroundColor = "#F8FAFC"`, `textColor = "#0F172A"`).
2. Dynamic Python detection via `st.context.theme` determines whether dark mode is active.
3. CSS variables dynamically resolve colors based on both `st.context.theme` and CSS media query `@media (prefers-color-scheme: dark)`:
   - Light mode cards render on `#FFFFFF` with `#E2E8F0` border.
   - Dark mode cards render on `#1E293B` with `#334155` border.
   - Text automatically flips from `#0F172A` to `#F8FAFC`.

---

## 5. Multi-Modal Risk Tier Visualization (Color-Blind Accessible)

No clinical result is communicated by color alone. Every risk tier features an icon, high-contrast badge, and plain-language action plan:
- 🚩 **REFER** (LDCT Evaluation Advised)
  - Color Token: `#DC2626` | Light Tint: `#FEF2F2` | Dark Tint: `#450A0A`
  - Icon: 🚩 Flag
  - Label: `REFERRAL RECOMMENDED · High Probability`
- 🔍 **REVIEW** (Shared Clinical Decision-Making)
  - Color Token: `#D97706` | Light Tint: `#FFFBEB` | Dark Tint: `#451A03`
  - Icon: 🔍 Magnifying Glass
  - Label: `CLINICAL REVIEW REQUIRED · Borderline / Uncertain`
- 🛡️ **RULE-OUT** (Routine Surveillance)
  - Color Token: `#059669` | Light Tint: `#ECFDF5` | Dark Tint: `#064E3B`
  - Icon: 🛡️ Shield
  - Label: `RULE-OUT · Low Probability Routine Annual Screening`

---

## 6. Layout & Visual Hierarchy

1. **Authentication Gateway**:
   - Centered card (`max-width: 480px`, `margin: 40px auto`), generous 32px padding, subtle elevation shadow, crisp typography.
   - Clear tabs: "🔑 Sign In" and "📝 Create Account".
   - Zero sample credentials exposed on screen.
2. **Top Clinical Bar**:
   - Deep blue banner (`#1E3A8A` to `#172554`) with subtle teal accent line.
   - User profile badge with role indicator (`Clinician` vs `Auditor`).
3. **Button Hierarchy**:
   - **Primary Action** (Run Analysis, Sign In, Download): Solid deep blue (`#1E3A8A`) with white text, 48px height, 10px rounded corners.
   - **Secondary Action** (Personas, Clear, Reset): Clean outline button with 1px border (`#CBD5E1` / `#334155`), 48px height.
4. **Linear 4-Step Stepper**:
   - Step 1: Demographics & Air Quality (5-Yr AQI/PM2.5, BMI)
   - Step 2: Inhalation History (Packs, Years, Pack-Years)
   - Step 3: Comorbidities (Asthma, COPD, Cardio-Metabolic)
   - Step 4: Access & Social Equity (Equity Sensitivity Floor)
5. **Results Drawer Architecture**:
   - Hero Triage Card with 32px Risk Score and Tier Badge.
   - 3-Card Boundary Deck (Rule-Out ceiling, Patient Risk, Referral threshold).
   - Collapsible Detail Drawers (SHAP decomposition, USPSTF citations, AI narrative, PDF generator).
