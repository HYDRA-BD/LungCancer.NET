"""
app.py — LungCancer.NET Clinical Pre-Screening & Risk Stratification Portal.

Key Features & Architectural Standards:
  • Professional Clinical Design System (Deep Clinical Blue #1E3A8A, Warm Teal #0D9488, Soft Gold #D97706)
  • Robust Typography with Google Font 'Inter' (Body >= 16px, Critical Clinical Values >= 32px)
  • Mandatory Word-Wrap & Flex Rules (overflow-wrap: break-word, word-break: break-word, min-width: 0)
  • Native Dark/Light Mode Theme Detection via st.context.theme with zero white-flash contrast bugs
  • Centered Professional Authentication Gateway with PBKDF2-HMAC-SHA256 (Zero hardcoded credentials)
  • Role-Based Access Control ('Clinician' full access vs 'Auditor' read-only mode)
  • Ephemeral Patient Data with HIPAA Privacy Shield (One-way SHA-256 masking)
  • Linear 4-Step Intake Stepper for lower cognitive burden
  • Calibrated Multi-Predictor Ensemble Scoring with Equity-Aware Sensitivity Floor
  • Explainable AI (SHAP Waterfall Decomposition)
  • Local Semantic Guideline RAG (USPSTF) & On-Device Clinical Pulmonology Narrative
  • Hospital-Grade Vector PDF Report Generation with SHA-256 Seal
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import requests
import streamlit as st

# Core modular components
from auth import authenticate_user, register_user, get_user_count
from predictor import get_prediction

try:
    from report_generator import generate_clinical_report
    PDF_GENERATOR_OK = True
except Exception as _e:
    PDF_GENERATOR_OK = False
    _PDF_IMPORT_ERR = str(_e)

try:
    from aqi_cache import _load_cache, get_state_aqi
    AQI_MODULE_OK = True
except Exception as _e:
    AQI_MODULE_OK = False
    _AQI_IMPORT_ERR = str(_e)

try:
    from rag import search_guidelines
    RAG_OK = True
except Exception as _e:
    RAG_OK = False
    _RAG_IMPORT_ERR = str(_e)


# ================================================================
# STREAMLIT PAGE CONFIGURATION
# ================================================================
st.set_page_config(
    page_title="LungCancer.NET | Clinical AI Pre-Screening Portal",
    page_icon="🫁",
    layout="wide",
    initial_sidebar_state="expanded",
)

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")
ASSETS_DIR = Path(__file__).parent / "assets"
LOGO_PATH = str(ASSETS_DIR / "logo.png")
WATERMARK_PATH = str(ASSETS_DIR / "watermark.png")

REPORT_CONFIG = {
    "team_name":   "LungCancer.NET Team",
    "institution": "LungCancer.NET Clinical AI Research Lab",
    "department":  "Preventive Pulmonology & Population Screening",
    "address":     "AI Builders Congress 2026 Showcase",
    "contact":     "research@lungcancer.net",
}

US_STATES = {
    "Alabama": (32.806671, -86.791130), "Alaska": (61.370716, -152.404419),
    "Arizona": (33.729759, -111.431221), "Arkansas": (34.969704, -92.373123),
    "California": (36.116203, -119.681564), "Colorado": (39.059811, -105.311104),
    "Connecticut": (41.597782, -72.755371), "Delaware": (39.318523, -75.507141),
    "Florida": (27.766279, -81.686783), "Georgia": (33.040619, -83.643074),
    "Hawaii": (21.094318, -157.498337), "Idaho": (44.240459, -114.478828),
    "Illinois": (40.349457, -88.986137), "Indiana": (39.849426, -86.258278),
    "Iowa": (42.011539, -93.210526), "Kansas": (38.526600, -96.726486),
    "Kentucky": (37.668140, -84.670067), "Louisiana": (31.169546, -91.867805),
    "Maine": (44.693947, -69.381927), "Maryland": (39.063946, -76.802101),
    "Massachusetts": (42.230171, -71.530106), "Michigan": (43.326618, -84.536095),
    "Minnesota": (45.694454, -93.900192), "Mississippi": (32.741646, -89.678696),
    "Missouri": (38.456085, -92.288368), "Montana": (46.921925, -110.454353),
    "Nebraska": (41.125370, -98.268082), "Nevada": (38.313515, -117.055374),
    "New Hampshire": (43.452492, -71.563896), "New Jersey": (40.298904, -74.521011),
    "New Mexico": (34.840515, -106.248482), "New York": (42.165726, -74.948051),
    "North Carolina": (35.630066, -79.806419), "North Dakota": (47.528912, -99.784012),
    "Ohio": (40.388783, -82.764915), "Oklahoma": (35.565342, -96.928917),
    "Oregon": (44.572021, -122.070938), "Pennsylvania": (40.590752, -77.209755),
    "Rhode Island": (41.680893, -71.511780), "South Carolina": (33.856892, -80.945007),
    "South Dakota": (44.299782, -99.438828), "Tennessee": (35.747845, -86.692345),
    "Texas": (31.054487, -97.563461), "Utah": (40.150032, -111.862434),
    "Vermont": (44.045876, -72.710686), "Virginia": (37.769337, -78.169968),
    "Washington": (47.400902, -121.490494), "West Virginia": (38.491226, -80.954453),
    "Wisconsin": (44.268543, -89.616508), "Wyoming": (42.755966, -107.302490),
}


# ================================================================
# DYNAMIC THEME DETECTION (STREAMLIT >= 1.35 st.context.theme)
# ================================================================
def detect_dark_mode() -> bool:
    """Detects whether dark mode is currently active via st.context.theme."""
    try:
        theme = getattr(st.context, "theme", {})
        if isinstance(theme, dict):
            val = theme.get("base") or theme.get("type")
        else:
            val = getattr(theme, "base", None) or getattr(theme, "type", None)
        if val and str(val).lower() == "dark":
            return True
    except Exception:
        pass
    return False

IS_DARK = detect_dark_mode()
print(f"[LungCancer.NET] Context theme base detected: {'DARK' if IS_DARK else 'LIGHT'}")


# ================================================================
# SESSION STATE INITIALIZATION
# ================================================================
st.session_state.setdefault("authenticated", False)
st.session_state.setdefault("auth_user", "")
st.session_state.setdefault("auth_role", "")
st.session_state.setdefault("auth_name", "")
st.session_state.setdefault("deidentify", True)  # HIPAA-safe by default
st.session_state.setdefault("zero_retention", True)
st.session_state.setdefault("audit_log", [])
st.session_state.setdefault("analysis", None)
st.session_state.setdefault("pdf_bytes", None)
st.session_state.setdefault("pdf_name", None)

if "aqi_cache" not in st.session_state:
    st.session_state.aqi_cache = (
        _load_cache() if AQI_MODULE_OK
        else {"states": {}, "errors": {}, "created": None}
    )


# ================================================================
# CLINICAL DESIGN SYSTEM CSS (WITH OVERFLOW & THEME HANDLING)
# ================================================================
theme_css_overrides = """
:root {
    --card-bg: #1E293B !important;
    --card-border: #334155 !important;
    --text-main: #F8FAFC !important;
    --text-muted: #94A3B8 !important;
    --app-bg: #0F172A !important;
    --input-bg: #0F172A !important;
    --hero-refer-bg: #450A0A !important;
    --hero-review-bg: #451A03 !important;
    --hero-ruleout-bg: #064E3B !important;
}
""" if IS_DARK else """
:root {
    --card-bg: #FFFFFF !important;
    --card-border: #E2E8F0 !important;
    --text-main: #0F172A !important;
    --text-muted: #64748B !important;
    --app-bg: #F8FAFC !important;
    --input-bg: #FFFFFF !important;
    --hero-refer-bg: #FEF2F2 !important;
    --hero-review-bg: #FFFBEB !important;
    --hero-ruleout-bg: #ECFDF5 !important;
}
"""

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    {theme_css_overrides}

    /* ----------------------------------------------------
       GLOBAL BOX-SIZING & OVERFLOW PREVENTION (NON-NEGOTIABLE)
       ---------------------------------------------------- */
    * {{
        box-sizing: border-box !important;
    }}

    html, body, [class*="css"], .stMarkdown, p, div, label, span {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        font-size: 16px;
        line-height: 1.6;
        color: var(--text-main);
        overflow-wrap: break-word !important;
        word-break: break-word !important;
    }}

    /* Prevent container overflow on flex / columns when window is 50% width */
    [data-testid="column"], .stColumn, [data-testid="stHorizontalBlock"] > div {{
        min-width: 0 !important;
        flex: 1 1 0px !important;
    }}

    h1, .stHeading h1 {{
        font-size: 28px !important;
        font-weight: 800 !important;
        color: var(--text-main) !important;
        letter-spacing: -0.5px;
        margin-bottom: 8px !important;
        overflow-wrap: break-word !important;
    }}

    h2, .stHeading h2 {{
        font-size: 22px !important;
        font-weight: 700 !important;
        color: var(--text-main) !important;
        margin-top: 16px !important;
        margin-bottom: 8px !important;
        overflow-wrap: break-word !important;
    }}

    h3, .stHeading h3 {{
        font-size: 18px !important;
        font-weight: 700 !important;
        color: var(--text-main) !important;
        overflow-wrap: break-word !important;
    }}

    /* ----------------------------------------------------
       BUTTON HIERARCHY & TOUCH TARGETS (>= 48px)
       ---------------------------------------------------- */
    button, .stButton > button {{
        min-height: 48px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        padding: 12px 20px !important;
        margin: 6px 0 !important;
        transition: all 0.18s ease-in-out !important;
        overflow-wrap: break-word !important;
        word-break: break-word !important;
    }}

    /* Primary solid button */
    .stButton > button[kind="primary"] {{
        background-color: #1E3A8A !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: 0 2px 6px rgba(30, 58, 138, 0.25) !important;
    }}
    .stButton > button[kind="primary"]:hover {{
        background-color: #172554 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(30, 58, 138, 0.35) !important;
    }}

    /* Secondary outline button */
    .stButton > button[kind="secondary"] {{
        background-color: transparent !important;
        color: var(--text-main) !important;
        border: 1px solid var(--card-border) !important;
    }}
    .stButton > button[kind="secondary"]:hover {{
        background-color: rgba(30, 58, 138, 0.08) !important;
        border-color: #1E3A8A !important;
    }}

    /* Inputs: text, number, select */
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div {{
        min-height: 48px !important;
        border-radius: 8px !important;
        border-color: var(--card-border) !important;
        background-color: var(--input-bg) !important;
        font-size: 16px !important;
    }}

    div[data-baseweb="input"] input {{
        font-size: 16px !important;
        color: var(--text-main) !important;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px !important;
        border-bottom: 2px solid var(--card-border) !important;
    }}

    .stTabs [data-baseweb="tab"] {{
        min-height: 48px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        padding: 10px 18px !important;
        border-radius: 8px 8px 0 0 !important;
        color: var(--text-muted) !important;
    }}
    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        color: #1E3A8A !important;
        border-bottom: 2px solid #1E3A8A !important;
    }}

    /* ----------------------------------------------------
       CLINICAL CARDS & SURFACES (24px PADDING)
       ---------------------------------------------------- */
    .login-container {{
        background-color: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 12px;
        padding: 32px 28px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
        margin: 20px auto 40px auto;
        max-width: 480px;
    }}

    .clinical-header-bar {{
        background: linear-gradient(135deg, #1E3A8A 0%, #172554 60%, #0D9488 100%);
        color: #FFFFFF !important;
        padding: 24px 28px;
        border-radius: 12px;
        margin-bottom: 24px;
        box-shadow: 0 4px 14px rgba(30, 58, 138, 0.18);
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 16px;
    }}
    .clinical-header-bar h1 {{
        color: #FFFFFF !important;
        margin: 0 !important;
        padding: 0 !important;
        font-size: 24px !important;
    }}
    .clinical-header-bar p {{
        color: #E2E8F0 !important;
        margin: 4px 0 0 0 !important;
        font-size: 15px !important;
    }}

    .user-pill-tag {{
        background: rgba(255, 255, 255, 0.16);
        border: 1px solid rgba(255, 255, 255, 0.35);
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: 600;
        color: #FFFFFF !important;
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }}

    .badge-clinician-tag {{
        background-color: #059669;
        color: #FFFFFF;
        padding: 3px 8px;
        border-radius: 14px;
        font-size: 12px;
        font-weight: 700;
    }}
    .badge-auditor-tag {{
        background-color: #D97706;
        color: #FFFFFF;
        padding: 3px 8px;
        border-radius: 14px;
        font-size: 12px;
        font-weight: 700;
    }}

    .auditor-banner-box {{
        background-color: var(--card-bg);
        border: 2px solid #D97706;
        border-left: 8px solid #D97706;
        color: var(--text-main);
        padding: 20px 24px;
        border-radius: 8px;
        margin-bottom: 24px;
        font-size: 16px;
    }}

    /* Triage Hero Card */
    .triage-hero-box {{
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        border: 2px solid transparent;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
    }}
    .hero-refer {{
        background-color: var(--hero-refer-bg);
        border-color: #DC2626;
        border-left: 10px solid #DC2626;
    }}
    .hero-review {{
        background-color: var(--hero-review-bg);
        border-color: #D97706;
        border-left: 10px solid #D97706;
    }}
    .hero-ruleout {{
        background-color: var(--hero-ruleout-bg);
        border-color: #059669;
        border-left: 10px solid #059669;
    }}

    .tier-badge-pill {{
        display: inline-block;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: 800;
        letter-spacing: 0.5px;
        color: #FFFFFF;
    }}

    .triage-score-display {{
        font-size: 32px !important;
        font-weight: 800 !important;
        line-height: 1.15 !important;
    }}

    .clinical-metric-card {{
        background-color: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 10px;
        padding: 20px 24px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
    }}
    .clinical-metric-card .value {{
        font-size: 26px;
        font-weight: 800;
        margin: 6px 0;
    }}
    .clinical-metric-card .label {{
        font-size: 15px;
        font-weight: 600;
        color: var(--text-muted);
    }}

    /* SHAP Attribution Rows */
    .shap-item-row {{
        background-color: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 8px;
        padding: 12px 18px;
        margin-bottom: 8px;
    }}
    .shap-badge-elevate {{
        background: #FEE2E2;
        color: #B91C1C;
        font-size: 13px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 12px;
    }}
    .shap-badge-protect {{
        background: #DCFCE7;
        color: #15803D;
        font-size: 13px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 12px;
    }}
    .shap-badge-neutral {{
        background: #F1F5F9;
        color: #475569;
        font-size: 13px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 12px;
    }}

    /* Guideline Quote Box */
    .guideline-quote-card {{
        background-color: var(--card-bg);
        border-left: 6px solid #1E3A8A;
        border-top: 1px solid var(--card-border);
        border-right: 1px solid var(--card-border);
        border-bottom: 1px solid var(--card-border);
        padding: 20px 24px;
        border-radius: 0 8px 8px 0;
        margin: 12px 0;
        font-size: 16px;
        line-height: 1.6;
    }}

    .ai-summary-box {{
        background-color: var(--card-bg);
        border: 1.5px solid #0D9488;
        border-radius: 10px;
        padding: 20px 24px;
        font-size: 16px;
        line-height: 1.65;
    }}
</style>
""", unsafe_allow_html=True)


# ================================================================
# SECURITY & SANITIZATION HELPERS
# ================================================================
def sanitize_patient_id(text: str) -> str:
    """Strictly validates and sanitizes Patient ID (alphanumeric, dashes, underscores)."""
    if not text:
        return f"P-{int(time.time()) % 100000:05d}"
    clean = re.sub(r"[^A-Za-z0-9_\-]", "", str(text).strip())
    if not clean:
        clean = f"P-{int(time.time()) % 100000:05d}"
    return clean[:24]


def get_display_patient_id(pid: str) -> str:
    """Returns de-identified pseudonym if HIPAA Privacy Shield is active."""
    if st.session_state.deidentify:
        pseudo = hashlib.sha256(pid.encode("utf-8")).hexdigest()[:6].upper()
        return f"ANON-{pseudo}"
    return pid


def log_audit_event(action: str, details_summary: str = "") -> None:
    """
    Appends an event to the in-memory audit trail.
    Zero patient PII stored: patient references are one-way hashed.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    raw = f"{timestamp}|{st.session_state.auth_user}|{st.session_state.auth_role}|{action}|{details_summary}"
    event_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    st.session_state.audit_log.append({
        "timestamp": timestamp,
        "user": st.session_state.auth_user,
        "role": st.session_state.auth_role,
        "action": action,
        "details": details_summary,
        "hash": event_hash,
    })


def purge_ephemeral_patient_data() -> None:
    """Zero-Retention: completely flushes patient biometrics and analysis from RAM."""
    st.session_state.analysis = None
    st.session_state.pdf_bytes = None
    st.session_state.pdf_name = None
    for k in ["patient_id", "w_kg", "h_cm", "w_lbs", "h_ft", "h_in", "packs", "years", "asthma", "copd", "heart_attack", "chd", "stroke", "diabetes", "low_access"]:
        if k in st.session_state:
            del st.session_state[k]


# ================================================================
# CLINICAL AI & RAG HELPERS
# ================================================================
@st.cache_data(ttl=30)
def check_ollama():
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=1.5)
        if r.status_code != 200:
            return False, []
        return True, [m["name"] for m in r.json().get("models", [])]
    except Exception:
        return False, []


def generate_clinical_summary(input_data: dict, tier: str, rec: str, state_name: str) -> str:
    """Generates an on-device clinical narrative summary without external PII leakage."""
    age = int(input_data.get("AGE", 50))
    pkyrs = float(input_data.get("PACK_YEARS", 0.0))
    resp = "Present" if input_data.get("RESP_BURDEN") else "Absent"
    chronic = "Present" if input_data.get("CHRONIC_BURDEN") else "Absent"
    aqi_val = input_data.get("AQI_5YR", "unknown")

    fallback_text = (
        f"Clinical Evaluation: Patient presents with an estimated cumulative tobacco exposure of "
        f"{pkyrs:.1f} pack-years and documented respiratory burden status ({resp}). In conjunction with 5-year "
        f"ambient particulate exposure (AQI {aqi_val}) in {state_name}, the composite ensemble stratifies this case "
        f"into the '{tier}' category. Protocol recommendation: {rec}"
    )

    ollama_ok, _ = check_ollama()
    if not ollama_ok:
        return fallback_text

    prompt = f"""You are an expert clinical pulmonologist reviewing a population lung cancer screening record.
Write a clear, reassuring, and professional 2-sentence clinical assessment for the patient's medical chart.

Clinical Metrics:
- Age: {age} years
- Smoking Exposure: {pkyrs:.1f} pack-years
- Respiratory Burden (COPD/Asthma): {resp}
- Chronic Disease Comorbidities: {chronic}
- Region: {state_name} (5-Year Historical AQI: {aqi_val})
- Algorithmic Triage Result: {tier}

Provide an objective clinical synthesis highlighting leading risk determinants with no bullet points."""

    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 180},
            },
            timeout=6,
        )
        if r.status_code == 200:
            resp_txt = r.json().get("response", "").strip()
            if resp_txt:
                return resp_txt
    except Exception:
        pass

    return fallback_text


def retrieve_guidelines(input_data: dict, tier: str):
    if not RAG_OK:
        return []
    try:
        safe_age = int(input_data.get("AGE", 50))
        safe_pkyrs = float(input_data.get("PACK_YEARS", 0.0))
        q = f"lung cancer screening criteria age {safe_age} pack years {safe_pkyrs:.1f} triage tier {tier}"
        return search_guidelines(q, k=2)
    except Exception:
        return []


def get_aqi_badge(aqi: float | None) -> tuple[str, str]:
    if aqi is None:
        return "Unknown", "#64748B"
    if aqi <= 50:
        return f"Good ({aqi:.1f})", "#059669"
    if aqi <= 100:
        return f"Moderate ({aqi:.1f})", "#D97706"
    if aqi <= 150:
        return f"Sensitive Groups ({aqi:.1f})", "#EA580C"
    if aqi <= 200:
        return f"Unhealthy ({aqi:.1f})", "#DC2626"
    return f"Hazardous ({aqi:.1f})", "#7F1D1D"


# ================================================================
# CLINICAL PERSONA PRESETS (FOR RAPID EVALUATION)
# ================================================================
PERSONAS = {
    "🔴 High-Risk Smoker": {
        "pid": "P-98421", "age": 66, "sex": "Male", "state": "Ohio",
        "unit": "Imperial (lbs, ft/in)", "w_lbs": 195.0, "h_ft": 5, "h_in": 10,
        "packs": 1.5, "years": 32.0, "asthma": False, "copd": True,
        "heart_attack": False, "chd": True, "stroke": False, "diabetes": True,
        "low_access": False,
    },
    "🟢 Low-Risk Young": {
        "pid": "P-10492", "age": 29, "sex": "Female", "state": "Maine",
        "unit": "Metric (kg, cm)", "w_kg": 62.0, "h_cm": 168.0,
        "packs": 0.0, "years": 0.0, "asthma": False, "copd": False,
        "heart_attack": False, "chd": False, "stroke": False, "diabetes": False,
        "low_access": False,
    },
    "🟡 Borderline Review": {
        "pid": "P-44819", "age": 53, "sex": "Female", "state": "California",
        "unit": "Imperial (lbs, ft/in)", "w_lbs": 160.0, "h_ft": 5, "h_in": 5,
        "packs": 1.0, "years": 14.0, "asthma": True, "copd": False,
        "heart_attack": False, "chd": False, "stroke": False, "diabetes": False,
        "low_access": False,
    },
    "🛡️ Subgroup Equity": {
        "pid": "P-73012", "age": 58, "sex": "Male", "state": "West Virginia",
        "unit": "Imperial (lbs, ft/in)", "w_lbs": 210.0, "h_ft": 5, "h_in": 9,
        "packs": 1.0, "years": 22.0, "asthma": False, "copd": False,
        "heart_attack": True, "chd": False, "stroke": False, "diabetes": True,
        "low_access": True,
    },
}


def load_persona(p_name: str):
    p = PERSONAS[p_name]
    st.session_state["patient_id"] = p["pid"]
    st.session_state["age"] = p["age"]
    st.session_state["sex"] = p["sex"]
    st.session_state["sel_state"] = p["state"]
    st.session_state["unit"] = p["unit"]
    if "Metric" in p["unit"]:
        st.session_state["w_kg"] = p["w_kg"]
        st.session_state["h_cm"] = p["h_cm"]
    else:
        st.session_state["w_lbs"] = p["w_lbs"]
        st.session_state["h_ft"] = p["h_ft"]
        st.session_state["h_in"] = p["h_in"]
    st.session_state["packs"] = p["packs"]
    st.session_state["years"] = p["years"]
    st.session_state["asthma"] = p["asthma"]
    st.session_state["copd"] = p["copd"]
    st.session_state["heart_attack"] = p["heart_attack"]
    st.session_state["chd"] = p["chd"]
    st.session_state["stroke"] = p["stroke"]
    st.session_state["diabetes"] = p["diabetes"]
    st.session_state["low_access"] = p["low_access"]
    st.session_state.analysis = None
    st.session_state.pdf_bytes = None
    log_audit_event("LOAD_PERSONA", f"Loaded preset: {p_name}")


# ================================================================
# CENTERED AUTHENTICATION GATEWAY
# (PROFESSIONAL CLINICAL PORTAL CARD)
# ================================================================
if not st.session_state.authenticated:
    _, auth_center_col, _ = st.columns([1, 1.8, 1])

    with auth_center_col:
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="login-container">
            <div style="text-align: center; margin-bottom: 20px;">
                <h1 style="margin: 0; font-size: 26px; color: #1E3A8A;">🫁 LungCancer.NET</h1>
                <p style="margin: 6px 0 0 0; color: #64748B; font-size: 14px; font-weight: 500;">
                    Clinical Pre-Screening & Risk Stratification Portal
                </p>
                <div style="height: 1px; background-color: var(--card-border); margin: 16px 0;"></div>
            </div>
        """, unsafe_allow_html=True)

        auth_tab_login, auth_tab_signup = st.tabs(["🔑 Sign In", "📝 Create Account"])

        with auth_tab_login:
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            login_user = st.text_input(
                "Username or Clinical Email",
                key="login_user_field",
                placeholder="Enter registered username or email",
            ).strip()
            login_pass = st.text_input(
                "Password",
                type="password",
                key="login_pass_field",
                placeholder="Enter your password",
            )

            st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
            if st.button("Sign In to Clinical Portal", type="primary", use_container_width=True, key="login_submit_btn"):
                success, role, name, msg = authenticate_user(login_user, login_pass)
                if success:
                    st.session_state.authenticated = True
                    st.session_state.auth_user = login_user
                    st.session_state.auth_role = role
                    st.session_state.auth_name = name
                    log_audit_event("AUTH_LOGIN", f"User '{login_user}' authenticated as {role}")
                    st.success(f"Welcome, {name}!")
                    time.sleep(0.3)
                    st.rerun()
                else:
                    st.error(msg)

            if get_user_count() == 0:
                st.info("ℹ️ No registered accounts in local database. Click **Create Account** above or run `python create_user.py` to set up your credentials.")

        with auth_tab_signup:
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            reg_name = st.text_input("Full Clinical Name", placeholder="e.g. Dr. Jane Smith, MD", key="reg_name_input")
            reg_user = st.text_input("Username or Email", placeholder="e.g. jsmith_md", key="reg_user_input")
            reg_role = st.selectbox(
                "Account Role",
                ["Clinician", "Auditor"],
                index=0,
                key="reg_role_select",
                help="Clinicians have full intake and assessment privileges. Auditors have read-only inspection access.",
            )
            reg_pass1 = st.text_input("Password (min 8 characters)", type="password", key="reg_pass1_input")
            reg_pass2 = st.text_input("Confirm Password", type="password", key="reg_pass2_input")

            st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
            if st.button("Register & Activate Account", type="primary", use_container_width=True, key="reg_submit_btn"):
                if reg_pass1 != reg_pass2:
                    st.error("Passwords do not match. Please verify and re-enter.")
                else:
                    reg_ok, reg_msg = register_user(
                        name=reg_name,
                        username_or_email=reg_user,
                        password=reg_pass1,
                        role=reg_role,
                    )
                    if reg_ok:
                        st.success(reg_msg + " You can now sign in using the 'Sign In' tab.")
                    else:
                        st.error(reg_msg)

        st.markdown("</div>", unsafe_allow_html=True)

    st.stop()


# ================================================================
# ACTIVE SESSION CONTEXT & ROLE-BASED ACCESS
# ================================================================
is_clinician = (st.session_state.auth_role == "Clinician")
is_auditor = (st.session_state.auth_role == "Auditor")


# ================================================================
# SIDEBAR — USER PROFILE & SECURITY GUARDS
# ================================================================
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=110)
    st.markdown("### 🫁 LungCancer.NET")
    st.caption("AI Decision Support & Equity Guardrail")

    st.markdown("---")
    st.markdown("#### 👤 Session Profile")
    st.markdown(f"**Name:** {st.session_state.auth_name}")
    st.markdown(f"**Username:** `{st.session_state.auth_user}`")

    if is_clinician:
        st.markdown('**Role:** <span class="badge-clinician-tag">Clinician (Full Access)</span>', unsafe_allow_html=True)
    else:
        st.markdown('**Role:** <span class="badge-auditor-tag">Auditor (Read-Only)</span>', unsafe_allow_html=True)

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    if st.button("🚪 Sign Out (Clear Session)", use_container_width=True, key="logout_btn_sidebar"):
        log_audit_event("AUTH_LOGOUT", f"User '{st.session_state.auth_user}' signed out")
        purge_ephemeral_patient_data()
        st.session_state.authenticated = False
        st.session_state.auth_user = ""
        st.session_state.auth_role = ""
        st.session_state.auth_name = ""
        st.rerun()

    st.markdown("---")
    st.markdown("#### 🛡️ HIPAA & Privacy Guards")

    deid_toggle = st.toggle(
        "HIPAA Privacy Shield",
        value=st.session_state.deidentify,
        help="Replaces Patient Medical Record Numbers with one-way SHA-256 pseudonyms in both the UI and clinical PDF reports.",
        key="deid_toggle_ui",
    )
    if deid_toggle != st.session_state.deidentify:
        st.session_state.deidentify = deid_toggle
        log_audit_event("TOGGLE_PRIVACY_SHIELD", f"Active: {deid_toggle}")
        st.rerun()

    zero_toggle = st.toggle(
        "Zero-Retention Mode",
        value=st.session_state.zero_retention,
        help="Ensures all clinical biomarkers remain strictly in ephemeral memory and are never written to disk or logs.",
        key="zero_toggle_ui",
    )
    st.session_state.zero_retention = zero_toggle

    st.markdown("---")
    st.markdown("#### ⚙️ Diagnostics & Engine Status")

    ollama_up, _ = check_ollama()
    if ollama_up:
        st.markdown('🟢 **Ollama Local AI:** Online (`qwen2.5:3b`)')
    else:
        st.markdown('🟡 **Ollama Local AI:** Deterministic Fallback')

    if RAG_OK:
        st.markdown('🟢 **USPSTF RAG:** Ready (ChromaDB)')
    else:
        st.markdown('🔴 **USPSTF RAG:** Offline')

    cache = st.session_state.aqi_cache
    n_states = len(cache.get("states", {}))
    if n_states >= len(US_STATES):
        st.markdown('🟢 **Air Quality Cache:** 50/50 States Synced')
    else:
        st.markdown(f'🟡 **Air Quality Cache:** {n_states}/50 Cached')

    if PDF_GENERATOR_OK:
        st.markdown('🟢 **Vector PDF Engine:** Ready')
    else:
        st.markdown('🔴 **Vector PDF Engine:** Missing ReportLab')

    st.markdown("---")
    with st.expander("🔍 Ephemeral Session Audit Trail", expanded=False):
        if st.session_state.audit_log:
            st.caption(f"Recorded Events: {len(st.session_state.audit_log)} (Memory Only)")
            for log in reversed(st.session_state.audit_log[-6:]):
                st.markdown(f"**{log['timestamp']}** — `{log['action']}`")
                st.caption(f"Role: {log['role']} | Hash: `{log['hash']}`")
        else:
            st.caption("No session events logged yet.")


# ================================================================
# CLINICAL HEADER BAR
# ================================================================
role_badge_html = (
    '<span class="badge-clinician-tag">Clinician</span>' if is_clinician
    else '<span class="badge-auditor-tag">Auditor</span>'
)

st.markdown(f"""
<div class="clinical-header-bar">
    <div>
        <h1>🫁 LungCancer.NET</h1>
        <p>Assistive Clinical Decision Support & Population Triage System · AI Builders Congress 2026</p>
    </div>
    <div>
        <div class="user-pill-tag">
            <span>👤 {st.session_state.auth_name}</span>
            {role_badge_html}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Auditor Read-Only Notification Banner
if is_auditor:
    st.markdown("""
    <div class="auditor-banner-box">
        <b>🛡️ AUDITOR READ-ONLY MODE ACTIVE:</b> You are logged in with quality audit privileges.
        Patient intake fields and pre-screening execution buttons are locked to preserve audit integrity.
        You can inspect calibrated risk calculations, verify local SHAP attribution factors, review USPSTF guidelines, and inspect PDF reports.
    </div>
    """, unsafe_allow_html=True)


# ================================================================
# 1-CLICK FAST-EVALUATION PERSONAS
# ================================================================
st.markdown("### ⚡ Fast-Evaluation Clinical Personas")
st.caption("Load validated benchmark patient profiles across risk strata and equity subgroups.")

pcol1, pcol2, pcol3, pcol4 = st.columns(4)

with pcol1:
    if st.button("🔴 High-Risk Smoker", disabled=is_auditor, use_container_width=True, help="Age 66, 32 yr heavy smoking, COPD comorbidity, Ohio", key="btn_p1"):
        load_persona("🔴 High-Risk Smoker")
        st.rerun()
    st.caption("66yo · 48 pk-yr · COPD")

with pcol2:
    if st.button("🟢 Low-Risk Young", disabled=is_auditor, use_container_width=True, help="Age 29, non-smoker, healthy, Maine", key="btn_p2"):
        load_persona("🟢 Low-Risk Young")
        st.rerun()
    st.caption("29yo · 0 pk-yr · Healthy")

with pcol3:
    if st.button("🟡 Borderline Review", disabled=is_auditor, use_container_width=True, help="Age 53, 14 pk-yr, Asthma, California", key="btn_p3"):
        load_persona("🟡 Borderline Review")
        st.rerun()
    st.caption("53yo · 14 pk-yr · Asthma")

with pcol4:
    if st.button("🛡️ Subgroup Equity", disabled=is_auditor, use_container_width=True, help="Age 58, 22 pk-yr, rural access barriers, West Virginia", key="btn_p4"):
        load_persona("🛡️ Subgroup Equity")
        st.rerun()
    st.caption("58yo · Rural · Cost Barrier")

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)


# ================================================================
# LINEAR 4-STEP INTAKE STEPPER
# ================================================================
st.markdown("### 📋 Patient Intake & Clinical Indicators")

step1_tab, step2_tab, step3_tab, step4_tab = st.tabs([
    "1️⃣ Demographics & Location",
    "2️⃣ Inhalation History",
    "3️⃣ Medical History",
    "4️⃣ Access & Equity Safeguards",
])

# ---------- STEP 1: Demographics & Location ----------
with step1_tab:
    st.markdown("#### Step 1: Patient Demographics & Geography")
    c_pid, c_age, c_sex = st.columns([1.5, 1, 1])

    with c_pid:
        raw_pid = st.text_input(
            "Patient Identifier / Medical Record #",
            value=st.session_state.get("patient_id", f"P-{int(time.time()) % 100000:05d}"),
            disabled=is_auditor,
            key="patient_id",
            help="Alphanumeric identifier. Masked automatically when HIPAA Shield is active.",
        )
        patient_id = sanitize_patient_id(raw_pid)
        if st.session_state.deidentify:
            st.caption(f"🔒 Masked Display ID: **{get_display_patient_id(patient_id)}**")

    with c_age:
        age_input = st.number_input(
            "Patient Age in Years (18–100)",
            min_value=18, max_value=100,
            value=int(st.session_state.get("age", 52)),
            disabled=is_auditor,
            key="age",
        )

    with c_sex:
        sex_input = st.radio(
            "Biological Sex at Birth",
            ["Male", "Female"],
            horizontal=True,
            disabled=is_auditor,
            key="sex",
        )
        sex_code = 1 if sex_input == "Male" else 2

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    st.markdown("#### Geographic Environmental Exposure (5-Year Historical Ambient Particulate)")
    c_loc1, c_loc2, c_loc3 = st.columns([1.5, 1, 1])

    with c_loc1:
        default_state = st.session_state.get("sel_state", "Ohio")
        state_idx = list(US_STATES.keys()).index(default_state) if default_state in US_STATES else 0
        selected_state = st.selectbox(
            "US State of Primary Residence",
            list(US_STATES.keys()),
            index=state_idx,
            disabled=is_auditor,
            key="sel_state",
        )

    state_data = get_state_aqi(cache, selected_state) if AQI_MODULE_OK else None
    aqi_5yr = state_data["aqi_5yr"] if state_data else 42.0
    pm25_5yr = state_data["pm25_5yr"] if state_data else 8.5
    badge_label, badge_color = get_aqi_badge(aqi_5yr)

    with c_loc2:
        st.metric("5-Year Historical AQI", f"{aqi_5yr:.1f}")
        st.markdown(f'<span style="color:{badge_color}; font-weight:700;">● Air Quality: {badge_label}</span>', unsafe_allow_html=True)

    with c_loc3:
        st.metric("5-Year Ambient PM2.5", f"{pm25_5yr:.1f} µg/m³")
        st.caption("CDC BRFSS Environmental Benchmark")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    st.markdown("#### Physical Measurements & Body Mass Index (BMI)")
    unit_col, metric_col1, metric_col2, bmi_res_col = st.columns([1.2, 1, 1, 1.2])

    with unit_col:
        unit = st.radio("Measurement Unit System", ["Metric (kg, cm)", "Imperial (lbs, ft/in)"], disabled=is_auditor, key="unit")

    if "Metric" in unit:
        with metric_col1:
            w_kg = st.number_input("Weight (kg)", 30.0, 250.0, float(st.session_state.get("w_kg", 72.0)), disabled=is_auditor, key="w_kg")
        with metric_col2:
            h_cm = st.number_input("Height (cm)", 100.0, 250.0, float(st.session_state.get("h_cm", 172.0)), disabled=is_auditor, key="h_cm")
        bmi_val = w_kg / ((h_cm / 100.0) ** 2)
        hw_display = f"{h_cm:.0f} cm · {w_kg:.0f} kg"
    else:
        with metric_col1:
            w_lbs = st.number_input("Weight (lbs)", 65.0, 500.0, float(st.session_state.get("w_lbs", 165.0)), disabled=is_auditor, key="w_lbs")
        with metric_col2:
            c_ft, c_in = st.columns(2)
            with c_ft:
                h_ft = st.number_input("Height (ft)", 3, 7, int(st.session_state.get("h_ft", 5)), disabled=is_auditor, key="h_ft")
            with c_in:
                h_in = st.number_input("Height (in)", 0, 11, int(st.session_state.get("h_in", 8)), disabled=is_auditor, key="h_in")
        total_inches = (h_ft * 12) + h_in
        bmi_val = (703.0 * w_lbs) / max(total_inches ** 2, 1.0)
        hw_display = f"{h_ft}'{h_in}\" · {w_lbs:.0f} lbs"

    with bmi_res_col:
        st.metric("Calculated BMI", f"{bmi_val:.1f} kg/m²")
        if bmi_val < 18.5:
            st.caption("⚠️ Underweight (<18.5)")
        elif bmi_val > 30.0:
            st.caption("ℹ️ Obese (≥30.0)")
        else:
            st.caption("✓ Normal Range")


# ---------- STEP 2: Inhalation & Tobacco ----------
with step2_tab:
    st.markdown("#### Step 2: Cumulative Tobacco Exposure")
    c_pks, c_yrs, c_calc = st.columns([1.5, 1.5, 1.5])

    with c_pks:
        packs_day = st.number_input(
            "Average Cigarette Packs Smoked Per Day",
            0.0, 8.0, float(st.session_state.get("packs", 0.0)),
            step=0.5, disabled=is_auditor, key="packs",
            help="1 pack = 20 cigarettes. Enter 0 for non-smoker.",
        )
    with c_yrs:
        years_smoked = st.number_input(
            "Total Cumulative Years Smoked",
            0.0, 80.0, float(st.session_state.get("years", 0.0)),
            step=1.0, disabled=is_auditor, key="years",
            help="Total duration of regular tobacco smoking.",
        )

    pack_years = packs_day * years_smoked

    with c_calc:
        st.metric("Cumulative Pack-Years", f"{pack_years:.1f} pk-yrs")
        if pack_years >= 20.0:
            st.markdown('<span style="color:#DC2626; font-weight:700;">🚩 Meets USPSTF High-Risk Benchmark (≥ 20 pk-yrs)</span>', unsafe_allow_html=True)
        elif pack_years > 0:
            st.caption("Moderate Tobacco Exposure (< 20 pk-yrs)")
        else:
            st.caption("Zero Tobacco History (Non-Smoker)")


# ---------- STEP 3: Comorbidities ----------
with step3_tab:
    st.markdown("#### Step 3: Medical History & Comorbidities")
    c_resp, c_cardio = st.columns(2)

    with c_resp:
        st.markdown("**Chronic Respiratory Burden**")
        asthma = st.checkbox("Asthma Diagnosis", value=st.session_state.get("asthma", False), disabled=is_auditor, key="asthma")
        copd = st.checkbox("COPD / Emphysema / Chronic Bronchitis", value=st.session_state.get("copd", False), disabled=is_auditor, key="copd")
        resp_flag = 1 if (asthma or copd) else 0

        if resp_flag:
            st.markdown('<span style="color:#D97706; font-weight:700;">⚠️ Chronic Respiratory Burden Detected</span>', unsafe_allow_html=True)
        else:
            st.caption("No chronic respiratory disease reported")

    with c_cardio:
        st.markdown("**Cardiovascular & Metabolic Comorbidities**")
        heart_attack = st.checkbox("Myocardial Infarction (Heart Attack)", value=st.session_state.get("heart_attack", False), disabled=is_auditor, key="heart_attack")
        chd = st.checkbox("Coronary Heart Disease / Angina", value=st.session_state.get("chd", False), disabled=is_auditor, key="chd")
        stroke = st.checkbox("Stroke / Cerebrovascular Event", value=st.session_state.get("stroke", False), disabled=is_auditor, key="stroke")
        diabetes = st.checkbox("Diabetes Mellitus", value=st.session_state.get("diabetes", False), disabled=is_auditor, key="diabetes")
        chronic_flag = 1 if (heart_attack or chd or stroke or diabetes) else 0

        if chronic_flag:
            st.markdown('<span style="color:#D97706; font-weight:700;">⚠️ Chronic Comorbidities Present</span>', unsafe_allow_html=True)
        else:
            st.caption("No cardiovascular or metabolic conditions reported")


# ---------- STEP 4: Access & Social Determinants ----------
with step4_tab:
    st.markdown("#### Step 4: Healthcare Access & Subgroup Equity Safeguards")
    st.info(
        "**Equity-Aware Subgroup Sensitivity Floor (≥85%):** LungCancer.NET applies an access-aware cost multiplier (1.5x) "
        "and locks rule-out thresholds to prevent premature clearance for individuals facing geographic or financial barriers to care."
    )
    low_access = st.checkbox(
        "Patient faces healthcare access barriers (e.g. cost barrier to care, no annual routine checkup, or rural residence)",
        value=st.session_state.get("low_access", False),
        disabled=is_auditor,
        key="low_access",
    )
    if low_access:
        st.markdown('<span style="color:#0D9488; font-weight:700;">🛡️ Access-Aware Multiplier Engaged — Missed-Case Penalty Weighted Up by 1.5x</span>', unsafe_allow_html=True)

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)


# ================================================================
# PRE-SCREENING EXECUTION CONTROLS
# ================================================================
run_col1, run_col2 = st.columns([3, 1])

with run_col1:
    btn_label = "🚀 Run Pre-Screening Analysis" if is_clinician else "🔒 Run Analysis (Locked in Auditor Mode)"
    run_btn = st.button(
        btn_label,
        type="primary",
        disabled=is_auditor,
        use_container_width=True,
        help="Executes the 9-predictor ensemble ladder and computes XAI factor attributions.",
        key="run_btn",
    )

with run_col2:
    if st.button("🔄 Clear Record", disabled=is_auditor, use_container_width=True, key="clear_top_btn"):
        purge_ephemeral_patient_data()
        log_audit_event("RESET_SESSION", "Cleared ephemeral patient record from RAM")
        st.rerun()


# ================================================================
# PREDICTION COMPUTATION (CLINICIAN ONLY)
# ================================================================
if run_btn and is_clinician:
    with st.spinner("Evaluating multi-predictor ensemble ladder and computing local SHAP factor attributions..."):
        time.sleep(0.3)

        patient_dict = {
            "patient_id": patient_id,
            "age": age_input,
            "sex": sex_code,
            "state": selected_state,
            "bmi": bmi_val,
            "height_weight": hw_display,
            "packs_per_day": packs_day,
            "years_smoked": years_smoked,
            "pack_years": pack_years,
            "asthma": asthma,
            "copd": copd,
            "resp_burden": resp_flag,
            "heart_attack": heart_attack,
            "chd": chd,
            "stroke": stroke,
            "diabetes": diabetes,
            "chronic_burden": chronic_flag,
            "low_access": low_access,
            "aqi_5yr": aqi_5yr,
            "pm25_5yr": pm25_5yr,
        }

        # Run clinical prediction engine
        pred_res = get_prediction(patient_dict)

        # Retrieve matched USPSTF guideline excerpts via local RAG
        guidelines = retrieve_guidelines(
            {"AGE": age_input, "PACK_YEARS": pack_years},
            pred_res["tier"],
        )

        # Generate on-device AI narrative
        ai_narrative = generate_clinical_summary(
            {"AGE": age_input, "PACK_YEARS": pack_years, "RESP_BURDEN": resp_flag, "CHRONIC_BURDEN": chronic_flag, "AQI_5YR": aqi_5yr},
            pred_res["tier"],
            pred_res["recommendation"],
            selected_state,
        )

        st.session_state.analysis = {
            "patient": patient_dict,
            "pred": pred_res,
            "guidelines": guidelines,
            "ai_narrative": ai_narrative,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        st.session_state.pdf_bytes = None
        st.session_state.pdf_name = None

        # Log audit event with one-way hash (Zero PII in logs)
        masked_id_hash = hashlib.sha256(patient_id.encode("utf-8")).hexdigest()[:8]
        log_audit_event(
            "EXECUTE_TRIAGE",
            f"PatientHash={masked_id_hash}, Tier={pred_res['tier']}, Score={pred_res['risk_score']:.6f}",
        )


# ================================================================
# CLINICAL RESULTS DASHBOARD
# ================================================================
if st.session_state.analysis is not None:
    ans = st.session_state.analysis
    patient = ans["patient"]
    p = ans["pred"]
    tier = p["tier"]
    score = p["risk_score"]
    pid_shown = get_display_patient_id(patient["patient_id"])

    st.markdown("---")
    st.markdown("## 📊 Clinical Triage Assessment")

    # Determine Tier Visual Tokens (Color + Icon + Label)
    if tier == "REFER":
        hero_class = "hero-refer"
        tier_icon = "🚩"
        badge_bg = "#DC2626"
        tier_title = "REFERRAL RECOMMENDED · High Probability"
    elif tier == "REVIEW":
        hero_class = "hero-review"
        tier_icon = "🔍"
        badge_bg = "#D97706"
        tier_title = "CLINICAL REVIEW REQUIRED · Shared Decision-Making"
    else:
        hero_class = "hero-ruleout"
        tier_icon = "🛡️"
        badge_bg = "#059669"
        tier_title = "RULE-OUT · Low Probability Routine Annual Screening"

    # Main Hero Result Card (Padding 24px, 32px score)
    st.markdown(f"""
    <div class="triage-hero-box {hero_class}">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px;">
            <div style="flex: 2; min-width: 280px;">
                <span class="tier-badge-pill" style="background-color: {badge_bg};">
                    {tier_icon} TIER: {tier}
                </span>
                <h2 style="margin: 12px 0 6px 0; font-weight: 800; font-size: 22px;">{tier_title}</h2>
                <p style="margin: 0; font-size: 17px; font-weight: 600;">
                    <b>Action Plan:</b> {p['recommendation']}
                </p>
                <div style="margin-top: 10px; font-size: 14px; opacity: 0.85;">
                    Record ID: <b>{pid_shown}</b> · Location: <b>{patient['state']}</b> · Evaluation: <b>{ans['timestamp']}</b>
                </div>
            </div>
            <div style="text-align: right; min-width: 180px;">
                <div style="font-size: 13px; font-weight: 700; opacity: 0.8; letter-spacing: 0.5px;">ESTIMATED RISK SCORE</div>
                <div class="triage-score-display" style="color: {badge_bg};">{score * 100:.2f}%</div>
                <div style="font-size: 14px; opacity: 0.85; margin-top: 4px;">95% CI: [{p['ci_lower']*100:.2f}% – {p['ci_upper']*100:.2f}%]</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Calibrated Triage Boundaries (3-Card Metric Deck)
    st.markdown("#### 📐 Calibrated Triage Cutoffs")
    b_col1, b_col2, b_col3 = st.columns(3)
    with b_col1:
        st.markdown(f"""
        <div class="clinical-metric-card">
            <div class="label">Rule-Out Ceiling (t_out)</div>
            <div class="value" style="color: #059669;">{p['t_out']*100:.4f}%</div>
            <div style="font-size: 13px; opacity: 0.8;">Equity-Protected Clearance Cutoff</div>
        </div>
        """, unsafe_allow_html=True)
    with b_col2:
        st.markdown(f"""
        <div class="clinical-metric-card">
            <div class="label">Patient Risk Score</div>
            <div class="value" style="color: {badge_bg};">{score*100:.4f}%</div>
            <div style="font-size: 13px; opacity: 0.8;">Multi-Model Unified Estimate</div>
        </div>
        """, unsafe_allow_html=True)
    with b_col3:
        st.markdown(f"""
        <div class="clinical-metric-card">
            <div class="label">Referral Floor (t_in)</div>
            <div class="value" style="color: #DC2626;">{p['t_in']*100:.4f}%</div>
            <div style="font-size: 13px; opacity: 0.8;">LDCT Imaging Threshold</div>
        </div>
        """, unsafe_allow_html=True)

    if p.get("equity_guard_triggered"):
        st.markdown("""
        <div style="background-color: var(--card-bg); border-left: 6px solid #D97706; border: 1px solid var(--card-border); padding: 16px 20px; border-radius: 6px; margin: 16px 0;">
            <b>🛡️ Equity Guardrail Engaged:</b> Risk score was below referral threshold, but rule-out was prevented due to model uncertainty or structural access barriers. Tier adjusted to <b>REVIEW</b> to avoid missed clinical triage.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Collapsible Detail Drawers
    with st.expander("🔬 Explainable AI: SHAP Factor Attribution Waterfall", expanded=True):
        st.caption("Decomposition of patient biomarkers relative to the CDC BRFSS normative screening cohort.")
        shap_items = p.get("shap_items", [])
        for item in shap_items:
            impact = item["impact"]
            direction = item["direction"]
            val_str = item["raw_value"]
            lbl = item["label"]

            if direction == "risk":
                badge_html = '<span class="shap-badge-elevate">▲ Elevates Risk</span>'
            elif direction == "protective":
                badge_html = '<span class="shap-badge-protect">▼ Lowers Risk</span>'
            else:
                badge_html = '<span class="shap-badge-neutral">• Neutral</span>'

            col_label, col_val, col_prog = st.columns([2.5, 2, 3.5])
            with col_label:
                st.markdown(f"**{lbl}**")
            with col_val:
                st.markdown(f"`{val_str}` &nbsp; {badge_html}", unsafe_allow_html=True)
            with col_prog:
                st.progress(min(max(float(impact * 1.8), 0.05), 1.0))

    with st.expander("📖 Matched USPSTF Clinical Guidelines (Local RAG)", expanded=False):
        if ans.get("guidelines"):
            for idx, g in enumerate(ans["guidelines"], 1):
                st.markdown(f"**Guideline Evidence Citation #{idx} (Page {g.get('page', '?')}):**")
                st.markdown(f"""
                <div class="guideline-quote-card">
                    "{g.get('text', '')}"
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("USPSTF Standard: Annual screening with LDCT is recommended for adults aged 50–80 years who have a 20 pack-year smoking history.")

    with st.expander("🤖 Pulmonologist AI Narrative Summary", expanded=False):
        st.markdown(f"""
        <div class="ai-summary-box">
            <b>Clinical Narrative:</b><br/>
            {ans.get("ai_narrative", "")}
        </div>
        """, unsafe_allow_html=True)

    with st.expander("📄 Official Hospital-Grade PDF Clinical Report", expanded=True):
        st.caption("Official clinical documentation with XAI SHAP factor breakdown, USPSTF citations, and SHA-256 integrity seal.")

        if PDF_GENERATOR_OK:
            pdf_col1, pdf_col2 = st.columns([2, 2])

            with pdf_col1:
                if st.button("📑 Generate Official PDF Clinical Report", type="primary", use_container_width=True, key="build_pdf_btn"):
                    with st.spinner("Rendering vector PDF clinical report in memory..."):
                        try:
                            pdf_bytes = generate_clinical_report(
                                patient=patient,
                                input_data={"AQI_5YR": aqi_5yr, "PM25_5YR": pm25_5yr, "AQI_CATEGORY": 1},
                                tier=tier,
                                recommendation=p["recommendation"],
                                risk_score=score,
                                contributing_factors=p["contributing_factors"],
                                guidelines=ans.get("guidelines", []),
                                ai_summary=ans.get("ai_narrative", ""),
                                team_info=REPORT_CONFIG,
                                ci_lower=p["ci_lower"],
                                ci_upper=p["ci_upper"],
                                shap_items=shap_items,
                                is_deidentified=st.session_state.deidentify,
                                logo_path=LOGO_PATH if os.path.exists(LOGO_PATH) else None,
                                watermark_path=WATERMARK_PATH if os.path.exists(WATERMARK_PATH) else None,
                            )
                            st.session_state.pdf_bytes = pdf_bytes
                            safe_id = pid_shown.replace("-", "_")
                            st.session_state.pdf_name = f"LungCancer_Report_{safe_id}_{datetime.now():%Y%m%d_%H%M}.pdf"
                            log_audit_event("GENERATE_PDF", f"Report generated for {pid_shown}")
                            st.success("Official PDF Report compiled successfully! Click download below.")
                        except Exception as e:
                            st.error(f"Failed to generate clinical report: {e}")

            with pdf_col2:
                if st.session_state.pdf_bytes is not None:
                    st.download_button(
                        "📥 Download Official PDF Report",
                        data=st.session_state.pdf_bytes,
                        file_name=st.session_state.pdf_name,
                        mime="application/pdf",
                        use_container_width=True,
                        type="primary",
                        key="download_pdf_btn",
                    )
        else:
            st.warning(f"⚠️ PDF generation engine is not available: {_PDF_IMPORT_ERR}")
            st.caption("Run in terminal: `pip install reportlab` to enable PDF export.")


# ================================================================
# CLINICAL FOOTER & REGULATORY DISCLAIMER
# ================================================================
st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
st.markdown("---")
st.markdown("""
<div style="color: var(--text-muted); font-size: 14px; line-height: 1.6;">
    <b>Clinical Advisory & Regulatory Disclaimer:</b> LungCancer.NET is an investigational clinical decision support system
    developed for population pre-screening and early risk stratification. It computes statistical risk from a 9-predictor ensemble
    calibrated on CDC BRFSS epidemiological cohorts. All patient data is ephemeral and never written to disk or logs.
    It does not replace tissue biopsy or radiological evaluation. All triage actions must be confirmed by a licensed medical practitioner.
</div>
""", unsafe_allow_html=True)
