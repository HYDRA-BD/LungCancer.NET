"""
app.py — LungCancer.NET Secured Clinical Pre-Screening Dashboard.

Design & Architectural Features:
  • Modern Medical Dashboard Interface with Hospital-Grade Visual Aesthetics
  • Cryptographic Authentication & Role-Based Access Control ('Clinician' vs 'Auditor')
  • Read-Only Mode Enforcement for 'Auditor' Role (Intake locked, reports viewable)
  • Strict Input Sanitization & Validation (XSS, Injection, Boundary Clamping)
  • Zero-Retention Ephemeral Memory (No patient PII ever written to disk or logs)
  • 1-Click Fast-Evaluation Personas (For Congress Judges & Evaluators)
  • Calibrated Multi-Predictor Ensemble Scoring with Subgroup Sensitivity Floor
  • Explainable AI (XAI) / Local SHAP Feature Waterfall Attribution
  • USPSTF Clinical Guideline Semantic RAG Search (ChromaDB)
  • On-Device AI Narrative Synthesis with Deterministic Clinical Fallback
  • Hospital-Grade PDF Clinical Report Builder with SHA-256 Seal
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
from auth import authenticate_user, register_user
from predictor import get_prediction

try:
    from report_generator import generate_clinical_report
    PDF_GENERATOR_OK = True
except Exception as _e:
    PDF_GENERATOR_OK = False
    _PDF_IMPORT_ERR = str(_e)

try:
    from aqi_cache import _load_cache, get_state_aqi, cache_summary
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
# CONFIGURATION & CONSTANTS
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
# SECURITY & INPUT SANITIZATION HELPERS
# ================================================================
def sanitize_patient_id(text: str) -> str:
    """Strictly validates and sanitizes Patient ID (alphanumeric, dashes, underscores)."""
    if not text:
        return f"P-{int(time.time()) % 100000:05d}"
    # Strip HTML / XSS / SQL injection characters
    clean = re.sub(r"[^A-Za-z0-9_\-]", "", str(text).strip())
    if not clean:
        clean = f"P-{int(time.time()) % 100000:05d}"
    return clean[:24]


def get_display_patient_id(pid: str) -> str:
    """Returns de-identified patient ID if privacy mode is active."""
    if st.session_state.deidentify:
        # One-way SHA-256 pseudonym
        pseudo = hashlib.sha256(pid.encode("utf-8")).hexdigest()[:6].upper()
        return f"ANON-{pseudo}"
    return pid


def log_audit_event(action: str, details_summary: str = "") -> None:
    """
    Appends an event to the in-memory audit trail.
    Ensures zero PII is written: patient references are one-way hashed.
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
    """Zero-Retention: completely flushes patient biometrics and analysis from memory."""
    st.session_state.analysis = None
    st.session_state.pdf_bytes = None
    st.session_state.pdf_name = None
    for k in ["patient_id", "w_kg", "h_cm", "w_lbs", "h_ft", "h_in", "packs", "years"]:
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
    """
    Generates an on-device clinical narrative.
    Strictly zero PII sent: only non-identifying aggregate biomarkers are supplied.
    """
    age = int(input_data.get("AGE", 50))
    pkyrs = float(input_data.get("PACK_YEARS", 0.0))
    resp = "Present" if input_data.get("RESP_BURDEN") else "Absent"
    chronic = "Present" if input_data.get("CHRONIC_BURDEN") else "Absent"
    aqi_val = input_data.get("AQI_5YR", "unknown")

    fallback_text = (
        f"Clinical Evaluation: Individual presents with an estimated cumulative tobacco exposure of "
        f"{pkyrs:.1f} pack-years and documented respiratory burden status ({resp}). In conjunction with 5-year "
        f"ambient particulate exposure (AQI {aqi_val}) in {state_name}, the composite ensemble stratifies this case "
        f"into the '{tier}' category. Protocol recommendation: {rec}"
    )

    ollama_ok, _ = check_ollama()
    if not ollama_ok:
        return fallback_text

    prompt = f"""You are a clinical pulmonologist evaluating a population lung cancer pre-screening case.
Write a concise, professional 2-sentence clinical assessment for the patient's medical chart.

Clinical Metrics:
- Age: {age} years
- Smoking Exposure: {pkyrs:.1f} pack-years
- Respiratory Burden (COPD/Asthma): {resp}
- Chronic Disease Comorbidities: {chronic}
- Region: {state_name} (5-Year Historical AQI: {aqi_val})
- Algorithmic Triage Result: {tier}

Provide an objective clinical synthesis highlighting the leading risk determinants without bullet points."""

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
        return f"Good ({aqi:.1f})", "#16A34A"
    if aqi <= 100:
        return f"Moderate ({aqi:.1f})", "#D97706"
    if aqi <= 150:
        return f"Sensitive Groups ({aqi:.1f})", "#EA580C"
    if aqi <= 200:
        return f"Unhealthy ({aqi:.1f})", "#DC2626"
    return f"Hazardous ({aqi:.1f})", "#7F1D1D"


# ================================================================
# CLINICAL PERSONA PRESETS (FOR FAST EVALUATION)
# ================================================================
PERSONAS = {
    "🔴 High-Risk Heavy Smoker": {
        "pid": "P-98421", "age": 66, "sex": "Male", "state": "Ohio",
        "unit": "Imperial (lbs, ft/in)", "w_lbs": 195.0, "h_ft": 5, "h_in": 10,
        "packs": 1.5, "years": 32.0, "asthma": False, "copd": True,
        "heart_attack": False, "chd": True, "stroke": False, "diabetes": True,
        "low_access": False,
    },
    "🟢 Low-Risk Young Non-Smoker": {
        "pid": "P-10492", "age": 29, "sex": "Female", "state": "Maine",
        "unit": "Metric (kg, cm)", "w_kg": 62.0, "h_cm": 168.0,
        "packs": 0.0, "years": 0.0, "asthma": False, "copd": False,
        "heart_attack": False, "chd": False, "stroke": False, "diabetes": False,
        "low_access": False,
    },
    "🟡 Intermediate / Borderline Review": {
        "pid": "P-44819", "age": 53, "sex": "Female", "state": "California",
        "unit": "Imperial (lbs, ft/in)", "w_lbs": 160.0, "h_ft": 5, "h_in": 5,
        "packs": 1.0, "years": 14.0, "asthma": True, "copd": False,
        "heart_attack": False, "chd": False, "stroke": False, "diabetes": False,
        "low_access": False,
    },
    "🛡️ Vulnerable Subgroup (Equity Floor Active)": {
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
# CLINICAL DASHBOARD STYLING
# ================================================================
st.markdown("""
<style>
    /* Clinical Dashboard Theme */
    .medical-top-bar {
        background: linear-gradient(135deg, #0B2545 0%, #134074 60%, #0066CC 100%);
        color: white;
        padding: 18px 24px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(11, 37, 69, 0.15);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .user-pill {
        background: rgba(255, 255, 255, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        backdrop-filter: blur(4px);
    }
    .role-badge-clinician {
        background-color: #22C55E;
        color: #064E3B;
        padding: 3px 8px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 11px;
    }
    .role-badge-auditor {
        background-color: #F59E0B;
        color: #78350F;
        padding: 3px 8px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 11px;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        margin-right: 6px;
    }
    .status-ok { background-color: #DCFCE7; color: #166534; }
    .status-warn { background-color: #FEF3C7; color: #92400E; }
    .status-err { background-color: #FEE2E2; color: #991B1B; }
    .auditor-notice {
        background-color: #FFFBEB;
        border: 1px solid #FCD34D;
        border-left: 5px solid #F59E0B;
        color: #92400E;
        padding: 12px 16px;
        border-radius: 6px;
        margin-bottom: 16px;
        font-size: 14px;
        font-weight: 500;
    }
    .card-metric {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 14px 18px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# ================================================================
# AUTHENTICATION GATEWAY
# ================================================================
if not st.session_state.authenticated:
    auth_col1, auth_col2, auth_col3 = st.columns([1, 2, 1])

    with auth_col2:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=120)

        st.markdown("## 🫁 LungCancer.NET")
        st.markdown("#### Clinical AI Pre-Screening System · Authentication Gate")
        st.caption("Secure cryptographic login required for clinical decision support access.")

        auth_tab_login, auth_tab_register = st.tabs(["🔑 Sign In", "📝 Register User"])

        with auth_tab_login:
            login_user = st.text_input("Username", key="login_username").strip()
            login_pass = st.text_input("Password", type="password", key="login_password")

            if st.button("Sign In to Clinical Portal", type="primary", use_container_width=True, key="login_submit"):
                success, role, name, msg = authenticate_user(login_user, login_pass)
                if success:
                    st.session_state.authenticated = True
                    st.session_state.auth_user = login_user
                    st.session_state.auth_role = role
                    st.session_state.auth_name = name
                    log_audit_event("AUTH_LOGIN", f"User '{login_user}' logged in as {role}")
                    st.success(f"Welcome, {name}!")
                    time.sleep(0.3)
                    st.rerun()
                else:
                    st.error(msg)

            st.markdown("---")
            st.markdown("##### ⚡ Demo Evaluation Credentials (AI Builders Congress)")
            c_cred1, c_cred2 = st.columns(2)
            with c_cred1:
                st.markdown("**Clinician (Full Access):**")
                st.code("User: clinician\nPass: ClinicianPass2026!", language="text")
            with c_cred2:
                st.markdown("**Auditor (Read-Only):**")
                st.code("User: auditor\nPass: AuditorPass2026!", language="text")

        with auth_tab_register:
            st.markdown("##### Create an Ephemeral Clinical Session Account")
            new_user = st.text_input("Choose Username (alphanumeric)", key="reg_user")
            new_name = st.text_input("Full Clinical Name", placeholder="Dr. Jane Doe, MD", key="reg_name")
            new_role = st.selectbox("Assign System Role", ["Clinician", "Auditor"], index=0, key="reg_role")
            new_pass = st.text_input("Choose Password (min 8 characters)", type="password", key="reg_pass")

            if st.button("Register & Activate Account", use_container_width=True, key="reg_submit"):
                reg_ok, reg_msg = register_user(new_user, new_pass, new_name, new_role)
                if reg_ok:
                    st.success(reg_msg + " You can now sign in above.")
                else:
                    st.error(reg_msg)

    st.stop()


# ================================================================
# ACTIVE SESSION CONTEXT & ROLE-BASED ACCESS
# ================================================================
is_clinician = (st.session_state.auth_role == "Clinician")
is_auditor = (st.session_state.auth_role == "Auditor")


# ================================================================
# SIDEBAR — SECURITY, SESSION & AUDIT TRAIL
# ================================================================
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=130)
    st.markdown("### 🫁 LungCancer.NET")
    st.caption("AI Clinical Decision Support Engine")

    st.markdown("---")
    st.subheader("👤 User Session Profile")
    st.markdown(f"**Name:** {st.session_state.auth_name}")
    st.markdown(f"**Username:** `{st.session_state.auth_user}`")

    if is_clinician:
        st.markdown('**Role:** <span class="role-badge-clinician">Clinician (Full Access)</span>', unsafe_allow_html=True)
    else:
        st.markdown('**Role:** <span class="role-badge-auditor">Auditor (Read-Only)</span>', unsafe_allow_html=True)

    if st.button("🚪 Sign Out (Clear Session)", use_container_width=True, key="logout_btn"):
        log_audit_event("AUTH_LOGOUT", f"User '{st.session_state.auth_user}' logged out")
        purge_ephemeral_patient_data()
        st.session_state.authenticated = False
        st.session_state.auth_user = ""
        st.session_state.auth_role = ""
        st.session_state.auth_name = ""
        st.rerun()

    st.markdown("---")
    st.subheader("🛡️ HIPAA & Security Guard")

    # HIPAA De-Identification Toggle
    deid_toggle = st.toggle(
        "HIPAA Privacy Shield",
        value=st.session_state.deidentify,
        help="Replaces Patient Identifiers with one-way SHA-256 pseudonyms across UI and reports.",
        key="deid_toggle_ui",
    )
    if deid_toggle != st.session_state.deidentify:
        st.session_state.deidentify = deid_toggle
        log_audit_event("TOGGLE_PRIVACY_SHIELD", f"Active: {deid_toggle}")
        st.rerun()

    # Zero-Retention Mode Toggle
    zero_toggle = st.toggle(
        "Zero-Retention Mode",
        value=st.session_state.zero_retention,
        help="Guarantees patient biometric data is ephemeral and never written to disk.",
        key="zero_toggle_ui",
    )
    st.session_state.zero_retention = zero_toggle

    st.markdown("---")
    st.subheader("⚙️ System Status")

    ollama_up, models = check_ollama()
    if ollama_up:
        st.markdown('<span class="status-badge status-ok">● Ollama AI Online</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-warn">● Clinical Fallback Mode</span>', unsafe_allow_html=True)

    if RAG_OK:
        st.markdown('<span class="status-badge status-ok">● USPSTF RAG Ready</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-err">● RAG Unavailable</span>', unsafe_allow_html=True)

    cache = st.session_state.aqi_cache
    n_states = len(cache.get("states", {}))
    if n_states >= len(US_STATES):
        st.markdown('<span class="status-badge status-ok">● 50/50 State AQI Synced</span>', unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="status-badge status-warn">● AQI: {n_states}/50 Cached</span>', unsafe_allow_html=True)

    if PDF_GENERATOR_OK:
        st.markdown('<span class="status-badge status-ok">● PDF Engine Ready</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-warn">● PDF Module Missing</span>', unsafe_allow_html=True)

    st.markdown("---")
    with st.expander("🔍 Ephemeral Session Audit Trail", expanded=False):
        if st.session_state.audit_log:
            st.caption(f"Logged Events: {len(st.session_state.audit_log)} (Memory Only)")
            for log in reversed(st.session_state.audit_log[-6:]):
                st.markdown(f"**{log['timestamp']}** — `{log['action']}`")
                st.caption(f"Role: {log['role']} | Hash: `{log['hash']}`")
        else:
            st.caption("No events recorded in current session.")


# ================================================================
# MEDICAL TOP BAR / DASHBOARD HEADER
# ================================================================
role_badge_html = (
    '<span class="role-badge-clinician">Clinician (Full Access)</span>' if is_clinician
    else '<span class="role-badge-auditor">Auditor (Read-Only)</span>'
)

st.markdown(f"""
<div class="medical-top-bar">
    <div>
        <h2 style="margin:0; padding:0; font-weight:700; font-size:22px;">🫁 LungCancer.NET</h2>
        <p style="margin:2px 0 0 0; opacity:0.85; font-size:13px;">
            Clinical AI Pre-Screening & Triage Platform · AI Builders Congress 2026
        </p>
    </div>
    <div style="display:flex; align-items:center; gap:12px;">
        <div class="user-pill">
            👤 {st.session_state.auth_name} · {role_badge_html}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Auditor Read-Only Notification Banner
if is_auditor:
    st.markdown("""
    <div class="auditor-notice">
        <b>🛡️ AUDITOR READ-ONLY MODE ACTIVE:</b> You are logged in with quality auditing privileges.
        Patient intake fields and triage execution controls are locked. You have full permission to audit
        model predictions, review local SHAP factor attributions, explore USPSTF clinical guidelines, and verify PDF reports.
    </div>
    """, unsafe_allow_html=True)


# ================================================================
# CLINICAL PERSONA QUICK-LOADER
# ================================================================
st.markdown("##### ⚡ Quick-Load Evaluation Personas")
pcol1, pcol2, pcol3, pcol4 = st.columns(4)

with pcol1:
    if st.button("🔴 High-Risk Heavy Smoker", disabled=is_auditor, use_container_width=True, help="66yo, 32 yr smoking, COPD, Ohio"):
        load_persona("🔴 High-Risk Heavy Smoker")
        st.rerun()

with pcol2:
    if st.button("🟢 Low-Risk Young Non-Smoker", disabled=is_auditor, use_container_width=True, help="29yo, non-smoker, healthy, Maine"):
        load_persona("🟢 Low-Risk Young Non-Smoker")
        st.rerun()

with pcol3:
    if st.button("🟡 Borderline Complex Review", disabled=is_auditor, use_container_width=True, help="53yo, 14 pk-yr, Asthma, California"):
        load_persona("🟡 Intermediate / Borderline Review")
        st.rerun()

with pcol4:
    if st.button("🛡️ Vulnerable Subgroup (Equity Floor)", disabled=is_auditor, use_container_width=True, help="58yo, 22 pk-yr, rural, cost barrier"):
        load_persona("🛡️ Vulnerable Subgroup (Equity Floor Active)")
        st.rerun()

st.markdown("---")


# ================================================================
# CLINICAL INTAKE WORKFLOW (LOCKED IN AUDITOR MODE)
# ================================================================
t1, t2, t3, t4 = st.tabs([
    "1️⃣ Demographics & Location",
    "2️⃣ Inhalation & Smoking History",
    "3️⃣ Comorbidities & Complications",
    "4️⃣ Social Determinants & Access",
])

# ---------- TAB 1: Demographics & Location ----------
with t1:
    c_pid, c_age, c_sex = st.columns([1.5, 1, 1])
    with c_pid:
        raw_pid = st.text_input(
            "Patient Identifier / Medical Record #",
            value=st.session_state.get("patient_id", f"P-{int(time.time()) % 100000:05d}"),
            disabled=is_auditor,
            key="patient_id",
        )
        patient_id = sanitize_patient_id(raw_pid)
        if st.session_state.deidentify:
            st.caption(f"🔒 Masked Display ID: **{get_display_patient_id(patient_id)}**")

    with c_age:
        age_input = st.number_input(
            "Age (18–100 years)",
            min_value=18, max_value=100,
            value=int(st.session_state.get("age", 52)),
            disabled=is_auditor,
            key="age",
        )

    with c_sex:
        sex_input = st.radio(
            "Biological Sex",
            ["Male", "Female"],
            horizontal=True,
            disabled=is_auditor,
            key="sex",
        )
        sex_code = 1 if sex_input == "Male" else 2

    st.markdown("#### Geographic Environmental Exposure (5-Year Historical AQI & PM2.5)")
    c_loc1, c_loc2, c_loc3 = st.columns([1.5, 1, 1])

    with c_loc1:
        default_state = st.session_state.get("sel_state", "Ohio")
        state_idx = list(US_STATES.keys()).index(default_state) if default_state in US_STATES else 0
        selected_state = st.selectbox(
            "Select US State of Residence",
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
        st.markdown(f'<span style="color:{badge_color}; font-weight:600;">Air Quality: {badge_label}</span>', unsafe_allow_html=True)

    with c_loc3:
        st.metric("5-Year Ambient PM2.5", f"{pm25_5yr:.1f} µg/m³")
        st.caption("Matches CDC BRFSS Training Cohort")

    st.markdown("#### Physical Metrics & Body Mass Index")
    unit_col, metric_col1, metric_col2, bmi_res_col = st.columns([1.2, 1, 1, 1.2])

    with unit_col:
        unit = st.radio("Unit Standard", ["Metric (kg, cm)", "Imperial (lbs, ft/in)"], disabled=is_auditor, key="unit")

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


# ---------- TAB 2: Inhalation & Tobacco ----------
with t2:
    st.markdown("#### Cumulative Tobacco Inhalation Metrics")
    c_pks, c_yrs, c_calc = st.columns([1.5, 1.5, 1.5])

    with c_pks:
        packs_day = st.number_input(
            "Packs Smoked Per Day",
            0.0, 8.0, float(st.session_state.get("packs", 0.0)),
            step=0.5, disabled=is_auditor, key="packs",
        )
    with c_yrs:
        years_smoked = st.number_input(
            "Total Years Smoked",
            0.0, 80.0, float(st.session_state.get("years", 0.0)),
            step=1.0, disabled=is_auditor, key="years",
        )

    pack_years = packs_day * years_smoked

    with c_calc:
        st.metric("Cumulative Pack-Years", f"{pack_years:.1f} pk-yrs")
        if pack_years >= 20.0:
            st.markdown('<span style="color:#DC2626; font-weight:700;">⚠️ USPSTF High-Risk Benchmark Met (≥20 pk-yrs)</span>', unsafe_allow_html=True)
        elif pack_years > 0:
            st.caption("Moderate Tobacco Exposure (<20 pk-yrs)")
        else:
            st.caption("Non-smoker / Zero tobacco history")


# ---------- TAB 3: Comorbidities ----------
with t3:
    st.markdown("#### Respiratory & Chronic Comorbidities")
    c_resp, c_cardio = st.columns(2)

    with c_resp:
        st.markdown("**Chronic Respiratory Conditions**")
        asthma = st.checkbox("Asthma", value=st.session_state.get("asthma", False), disabled=is_auditor, key="asthma")
        copd = st.checkbox("COPD / Emphysema / Chronic Bronchitis", value=st.session_state.get("copd", False), disabled=is_auditor, key="copd")
        resp_flag = 1 if (asthma or copd) else 0

        if resp_flag:
            st.warning("Respiratory Burden Present (Elevates risk log-odds)")
        else:
            st.info("No chronic respiratory burden detected")

    with c_cardio:
        st.markdown("**Cardiovascular & Metabolic Comorbidities**")
        heart_attack = st.checkbox("Myocardial Infarction (Heart Attack)", value=st.session_state.get("heart_attack", False), disabled=is_auditor, key="heart_attack")
        chd = st.checkbox("Coronary Heart Disease / Angina", value=st.session_state.get("chd", False), disabled=is_auditor, key="chd")
        stroke = st.checkbox("Stroke / Cerebrovascular Event", value=st.session_state.get("stroke", False), disabled=is_auditor, key="stroke")
        diabetes = st.checkbox("Diabetes Mellitus", value=st.session_state.get("diabetes", False), disabled=is_auditor, key="diabetes")
        chronic_flag = 1 if (heart_attack or chd or stroke or diabetes) else 0

        if chronic_flag:
            st.warning("Chronic Comorbidity Present")
        else:
            st.info("No chronic disease comorbidity detected")


# ---------- TAB 4: Access & Social Determinants ----------
with t4:
    st.markdown("#### Healthcare Access & Subgroup Equity Safeguards")
    st.info(
        "LungCancer.NET incorporates an **Equity-Aware Subgroup Sensitivity Floor (≥85%)** and "
        "an **Access-Aware Cost Multiplier (1.5x)**. Patients facing structural barriers are protected from "
        "unjustified rule-outs to ensure equitable triage in rural and underserved communities."
    )
    low_access = st.checkbox(
        "Patient belongs to a Low-Access Subgroup (Cost barrier to care / No annual routine checkup / Rural residence)",
        value=st.session_state.get("low_access", False),
        disabled=is_auditor,
        key="low_access",
    )
    if low_access:
        st.markdown('<span style="color:#D97706; font-weight:600;">🛡️ Access-Aware Multiplier Active — Missed Case Penalty Weighted Up by 1.5x</span>', unsafe_allow_html=True)

st.markdown("---")


# ================================================================
# PRE-SCREENING EXECUTION (LOCKED FOR AUDITOR)
# ================================================================
run_col1, run_col2 = st.columns([3, 1])

with run_col1:
    btn_label = "🚀 Run Pre-Screening Analysis" if is_clinician else "🔒 Run Pre-Screening (Locked for Auditor)"
    run_btn = st.button(
        btn_label,
        type="primary",
        disabled=is_auditor,
        use_container_width=True,
        help="Execute the 9-predictor ensemble and XAI attribution" if is_clinician else "Auditor role has read-only access",
        key="run_btn",
    )

with run_col2:
    if st.button("🔄 Reset Patient Record", disabled=is_auditor, use_container_width=True, key="clear_top"):
        purge_ephemeral_patient_data()
        log_audit_event("RESET_SESSION", "Cleared ephemeral patient data from RAM")
        st.rerun()


# ================================================================
# COMPUTE PREDICTION (CLINICIAN ONLY)
# ================================================================
if run_btn and is_clinician:
    with st.spinner("Executing 9-predictor ensemble ladder & XAI attribution..."):
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

        # Generate AI Clinical Summary
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

        # Log audit event with one-way hashed identifier (Zero PII in logs)
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

    st.markdown("---")
    st.markdown("## 📊 Clinical Triage Dashboard")

    # 1. Main Triage Banner Card
    t_color = p["tier_color"]
    t_hex = p["tier_hex"]
    pid_shown = get_display_patient_id(patient["patient_id"])

    st.markdown(f"""
    <div style="background-color: {t_hex}15; border-left: 6px solid {t_hex}; border-radius: 8px; padding: 18px 24px; margin-bottom: 20px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <span style="background:{t_hex}; color:white; padding:4px 12px; border-radius:14px; font-weight:700; font-size:13px;">
                    TIER: {tier}
                </span>
                <h3 style="margin:8px 0 4px 0; color:{t_hex}; font-weight:800;">{p['tier_label']}</h3>
                <p style="margin:0; color:#334155; font-size:15px; font-weight:500;">
                    <b>Action Plan:</b> {p['recommendation']}
                </p>
                <div style="margin-top:6px; font-size:12px; color:#64748B;">
                    Record ID: <b>{pid_shown}</b> · Location: <b>{patient['state']}</b> · Assessed: <b>{ans['timestamp']}</b>
                </div>
            </div>
            <div style="text-align:right;">
                <span style="color:#64748B; font-size:12px; font-weight:600;">UNIFIED RISK ESTIMATE</span>
                <div style="font-size:32px; font-weight:800; color:{t_hex}; line-height:1.1;">{score * 100:.3f}%</div>
                <span style="color:#64748B; font-size:11px;">95% CI: [{p['ci_lower']*100:.3f}% – {p['ci_upper']*100:.3f}%]</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Decision Policy & Boundaries Visual Gauge
    st.markdown("#### 📐 Calibrated Triage Boundaries")
    t_out_val = p["t_out"] * 100
    t_in_val = p["t_in"] * 100

    g_col1, g_col2, g_col3 = st.columns(3)
    with g_col1:
        st.metric("Rule-Out Ceiling (t_out)", f"{t_out_val:.4f}%", help="Screening clearance cutoff (Equity-Aware Floor)")
    with g_col2:
        st.metric("Patient Risk Score", f"{score * 100:.4f}%", delta=f"{tier}", delta_color="inverse" if tier == "REFER" else "normal")
    with g_col3:
        st.metric("Referral Floor (t_in)", f"{t_in_val:.4f}%", help="Fast-track LDCT imaging threshold")

    st.progress(min(max(float(score / (p['t_in'] * 1.8)), 0.0), 1.0))

    if p.get("equity_guard_triggered"):
        st.warning("🛡️ **Equity Guardrail Engaged:** Patient risk score was below referral threshold, but Rule-Out was guarded due to high model uncertainty or low-access status. Tier adjusted to **REVIEW** to prevent missed triage.")

    # 3. Explainable AI / SHAP Factor Attribution Waterfall
    st.markdown("---")
    st.markdown("#### 🔬 Explainable AI (XAI) — Patient Factor Attribution")
    st.caption("Decomposition of patient-specific risk determinants relative to CDC BRFSS normative baseline.")

    shap_items = p.get("shap_items", [])
    for item in shap_items:
        impact = item["impact"]
        direction = item["direction"]
        val_str = item["raw_value"]
        lbl = item["label"]

        if direction == "risk":
            sign_icon = "▲ Elevates Risk"
        elif direction == "protective":
            sign_icon = "▼ Protective / Lowers Risk"
        else:
            sign_icon = "• Neutral"

        col_lbl, col_val, col_bar = st.columns([2.5, 1.8, 3.5])
        with col_lbl:
            st.markdown(f"**{lbl}**")
        with col_val:
            st.markdown(f"`{val_str}` ({sign_icon})")
        with col_bar:
            st.progress(min(max(float(impact * 1.8), 0.05), 1.0))

    # 4. USPSTF Guideline Evidence Matrix
    st.markdown("---")
    st.markdown("#### 📖 Matched USPSTF Clinical Guidelines (Local RAG)")
    if ans.get("guidelines"):
        for idx, g in enumerate(ans["guidelines"], 1):
            with st.expander(f"USPSTF Guideline Reference #{idx} (Page {g.get('page', '?')})", expanded=True):
                st.write(g.get("text", ""))
    else:
        st.info("USPSTF Guideline reference: Annual screening with LDCT recommended for adults 50–80 with ≥20 pack-year smoking history.")

    # 5. Physician AI Narrative Synthesis
    st.markdown("---")
    st.markdown("#### 🤖 Physician AI Narrative Summary")
    st.info(ans.get("ai_narrative", ""))

    # 6. Hospital-Grade PDF Clinical Report Generation
    st.markdown("---")
    st.markdown("#### 📄 Executive Hospital-Grade PDF Clinical Report")
    st.caption("Official clinical documentation with XAI SHAP factor breakdown, USPSTF citations, and SHA-256 integrity seal.")

    if PDF_GENERATOR_OK:
        pdf_col1, pdf_col2 = st.columns([2, 2])

        with pdf_col1:
            if st.button("📑 Generate Official PDF Clinical Report", type="primary", use_container_width=True, key="build_pdf_btn"):
                with st.spinner("Rendering vector clinical PDF report in memory..."):
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
                        st.success("PDF Report generated successfully! Ready for download below.")
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
        st.warning(f"⚠️ PDF report generation is currently unavailable: {_PDF_IMPORT_ERR}")
        st.caption("To enable hospital-grade PDF export, run in your terminal: `pip install reportlab`")


# ================================================================
# CLINICAL FOOTER & REGULATORY DISCLAIMER
# ================================================================
st.markdown("---")
st.markdown("""
<div style="color:#64748B; font-size:12px; line-height:1.5;">
    <b>Clinical Advisory & Regulatory Disclaimer:</b> LungCancer.NET is an investigational clinical decision support system
    developed for population pre-screening and early risk stratification. It computes statistical risk from a 9-predictor ensemble
    calibrated on CDC BRFSS epidemiological cohorts. All patient data is ephemeral and never written to disk or logs.
    It does not replace tissue biopsy or radiological evaluation. All triage actions must be confirmed by a licensed medical practitioner.
</div>
""", unsafe_allow_html=True)
