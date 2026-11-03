# LungCancer.NET — UI/UX Redesign & Architectural Changelog

## Release: Accessible Clinical Interface (AI Builders Congress 2026)

### 1. Typography & Readability Architecture
- **Base Body Font Scaled to $\ge 18\text{ px}$**: Redesigned all form fields, labels, helper captions, and clinical narratives to accommodate older adults (ages 45–80) and senior clinical practitioners.
- **High-Impact Display Scale**: Clinical triage readouts (unified risk score percentage and tier heading) elevated to $32\text{--}38\text{ px}$ bold for immediate scanning.
- **Standardized Line Heights**: Line height adjusted to $1.6$ across all narrative blocks to eliminate cognitive crowding.

### 2. Color Palette & Emotional Tone
- **Warm & Empathetic Theme**: Replaced sterile hospital grays with deep marine (`#0B2545`), comforting slate backgrounds (`#F8FAFC`), and healing cyan accents (`#0284C7`).
- **Multi-Modal Color-Blind Safe Triage**: Eliminates reliance on color alone. Each risk tier combines a color token with a distinct icon and explicit text label:
  - 🚩 **REFER**: Terracotta accent (`#DC2626`) + Flag icon + LDCT evaluation recommendation.
  - 🔍 **REVIEW**: Warm amber accent (`#D97706`) + Magnifier icon + Shared decision protocol.
  - 🛡️ **RULE-OUT**: Sage green accent (`#059669`) + Shield icon + Routine surveillance clearance.

### 3. Progressive Intake Stepper & Cognitive Load Reduction
- **Linear 4-Step Intake Flow**: Replaced the dense single-page intake layout with a calm 4-step progressive stepper:
  1. *Step 1: Patient Demographics & Location* (ID, Age, Sex, 5-Year AQI/PM2.5, BMI)
  2. *Step 2: Cumulative Tobacco Exposure* (Packs/Day, Duration, Pack-Years with 20 pk-yr alert)
  3. *Step 3: Medical History & Comorbidities* (Asthma, COPD, Cardiovascular, Diabetes)
  4. *Step 4: Healthcare Access & Equity Safeguards* (Access barriers with 1.5x cost multiplier)
- **Interactive Target Sizing**: All buttons, stepper tabs, and input controls expanded to $\ge 48 \times 48\text{ px}$ with $\ge 12\text{ px}$ clearance between adjacent buttons.

### 4. Results Screen & Collapsible Drawers
- **Hero Triage Banner**: High-visibility header card displaying the triage status, risk score, 95% CI, and plain-language action recommendation.
- **Calibrated Triage Gauge**: 3-metric boundary cards displaying Rule-Out ceiling ($t_{out}$), Patient Risk Score, and Referral floor ($t_{in}$).
- **Collapsible Detail Drawers**:
  - `🔬 Explainable AI (SHAP Waterfall)`: Expanded by default with Rose/Sage risk attribution bars and raw metric values.
  - `📖 Matched USPSTF Clinical Guidelines`: Collapsed drawer with styled blockquote citations.
  - `🤖 Pulmonologist AI Narrative Summary`: Highlighted callout card with on-device narrative.
  - `📄 Official Hospital-Grade PDF Clinical Report`: Vector report generation button and in-memory download.

### 5. Authentication & Role-Based Access Control
- **Zero Hardcoded Credentials**: Removed all hardcoded test accounts from source code and UI.
- **PBKDF2-HMAC-SHA256**: Implemented modern KDF with 250,000 iterations and 32-byte cryptographically secure random salt in `artifacts/users.db` (SQLite).
- **Constant-Time Verification**: Uses `hmac.compare_digest` to prevent timing side-channel attacks.
- **Brute-Force Rate Limiting**: 5 consecutive failed login attempts locks the user out for 60 seconds.
- **Account Provisioning CLI**: Added `create_user.py` for direct provisioning of `Clinician` and `Auditor` roles.
- **Role Permissions**:
  - `Clinician`: Full access to intake form, persona fast-loaders, risk calculations, and PDF generation.
  - `Auditor`: Read-only inspection mode. Intake form and analysis execution buttons are locked. Full access to inspect outputs, SHAP attributions, guidelines, and reports.

### 6. Preservation of Clinical & AI Logic
- Preserved `predictor.get_prediction()` calibrated ensemble and SHAP values.
- Preserved `rag.search_guidelines()` offline ChromaDB semantic search.
- Preserved local Ollama LLM call and deterministic clinical pulmonology fallback.
- Preserved in-memory vector PDF generator (`report_generator.py`) and SHA-256 integrity seal.
- Preserved Model Context Protocol server (`mcp_server.py`) with all 3 read-only tools.
