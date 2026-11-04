"""
main.py — LungCancer.NET FastAPI backend.

Wraps predictor.py, rag.py, report_generator.py, aqi_cache.py into a REST API
consumed by the React frontend.

Run:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

Swagger docs (test endpoints in the browser):
    http://localhost:8000/docs
"""
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field

from predictor import get_prediction
import os
_DISABLE_RAG = os.environ.get("DISABLE_RAG", "0") == "1"


def search_guidelines(query, k=3):
    """Lazy wrapper — loads rag.py only when called, and only if enabled."""
    if _DISABLE_RAG:
        return []
    try:
        from rag import search_guidelines as _rag
        return _rag(query, k=k)
    except Exception as e:
        logger.warning(f"RAG unavailable: {e}")
        return []
from aqi_cache import _load_cache, get_state_aqi
from report_generator import generate_clinical_report
from auth import (
    create_token, create_user, decode_token, get_user_by_email,
    get_user_by_id, init_db, update_last_login, verify_password,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("lungcancer.api")

# ── Config ────────────────────────────────────────────────────────
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")
ASSETS_DIR = Path(__file__).parent / "assets"
LOGO_PATH = str(ASSETS_DIR / "logo.png")
WATERMARK_PATH = str(ASSETS_DIR / "watermark.png")

REPORT_CONFIG = {
    "team_name": "Team LungCancer.NET",
    "institution": "LungCancer.NET Clinical AI Lab",
    "department": "Preventive Pulmonology & Population Screening",
    "address": "AI Builders Congress 2026 Showcase",
    "contact": "research@lungcancer.net",
}

_aqi_cache: dict = {"states": {}, "errors": {}}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _aqi_cache
    init_db()
    try:
        _aqi_cache = _load_cache()
        logger.info(f"AQI cache: {len(_aqi_cache.get('states', {}))} states")
    except Exception as e:
        logger.warning(f"AQI cache load failed: {e}")


app = FastAPI(
    title="LungCancer.NET API",
    version="1.0.0",
    description="Clinical pre-screening API for LungCancer.NET.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer(auto_error=False)


# ── Pydantic models ───────────────────────────────────────────────
class PatientInput(BaseModel):
    age: int = Field(..., ge=18, le=120)
    bmi: float = Field(..., ge=8, le=100)
    pack_years: float = Field(..., ge=0, le=300)
    resp_burden: bool = False
    chronic_burden: bool = False
    low_access: bool = False
    sex: int = Field(1, ge=1, le=2)
    state: str = ""
    patient_id: str = ""
    packs_per_day: float = 0.0
    years_smoked: float = 0.0
    asthma: bool = False
    copd: bool = False
    heart_attack: bool = False
    chd: bool = False
    stroke: bool = False
    diabetes: bool = False
    height_weight: str = ""


class SignupInput(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field("clinician")


class LoginInput(BaseModel):
    email: EmailStr
    password: str


class GuidelineQuery(BaseModel):
    query: str = Field(..., min_length=1)
    k: int = Field(3, ge=1, le=10)


# ── Auth dependencies ─────────────────────────────────────────────
def require_auth(creds: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    if creds is None:
        raise HTTPException(401, "Missing Authorization header",
                            headers={"WWW-Authenticate": "Bearer"})
    payload = decode_token(creds.credentials)
    if payload is None:
        raise HTTPException(401, "Invalid or expired token",
                            headers={"WWW-Authenticate": "Bearer"})
    return payload


def require_clinician(payload: dict = Depends(require_auth)) -> dict:
    if payload.get("role") != "clinician":
        raise HTTPException(403, "Clinician role required")
    return payload


# ── Helpers ───────────────────────────────────────────────────────
def _build_patient_dict(p: PatientInput) -> dict:
    return {
        "patient_id": p.patient_id or f"P-{int(datetime.now().timestamp()) % 100000:05d}",
        "age": p.age, "sex": p.sex, "state": p.state, "bmi": p.bmi,
        "height_weight": p.height_weight,
        "packs_per_day": p.packs_per_day, "years_smoked": p.years_smoked,
        "pack_years": p.pack_years,
        "asthma": p.asthma, "copd": p.copd, "resp_burden": int(p.resp_burden),
        "heart_attack": p.heart_attack, "chd": p.chd, "stroke": p.stroke,
        "diabetes": p.diabetes, "chronic_burden": int(p.chronic_burden),
        "low_access": p.low_access,
    }


def _get_aqi_for_state(state: str):
    if not state:
        return None, None, None
    data = get_state_aqi(_aqi_cache, state)
    if not data:
        return None, None, None
    aqi, pm25 = data.get("aqi_5yr"), data.get("pm25_5yr")
    cat = None
    if aqi is not None:
        cat = 0 if aqi < 50 else 1 if aqi < 100 else 2 if aqi < 150 else 3 if aqi < 200 else 4
    return aqi, pm25, cat


def _generate_clinical_summary(patient: dict, tier: str, recommendation: str,
                                aqi_5yr: Optional[float]) -> str:
    age = patient.get("age", 50)
    pkyrs = patient.get("pack_years", 0.0)
    resp = "Present" if patient.get("resp_burden") else "Absent"
    chronic = "Present" if patient.get("chronic_burden") else "Absent"
    aqi_val = aqi_5yr if aqi_5yr is not None else "unknown"
    state = patient.get("state", "Unknown")

    fallback = (
        f"Clinical Evaluation: Patient presents with cumulative tobacco exposure of "
        f"{pkyrs:.1f} pack-years and {resp.lower()} respiratory burden. With 5-year "
        f"ambient exposure (AQI {aqi_val}) in {state}, the ensemble stratifies this "
        f"patient into the '{tier}' category. Recommendation: {recommendation}"
    )

    prompt = f"""You are a clinical pulmonologist writing a concise 2-sentence chart note.

- Age: {age} years
- Pack-Years: {pkyrs:.1f}
- Respiratory Burden: {resp}
- Chronic Disease: {chronic}
- Region: {state} (5-yr AQI: {aqi_val})
- Triage: {tier}

Write an objective, factual clinical assessment without bullet points."""

    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False,
                  "options": {"temperature": 0.2, "num_predict": 200}},
            timeout=30,
        )
        if r.status_code == 200:
            txt = r.json().get("response", "").strip()
            if txt:
                return txt
    except Exception as e:
        logger.warning(f"Ollama summary failed: {e}")
    return fallback


# ── Health ────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "status": "ok",
        "aqi_states_cached": len(_aqi_cache.get("states", {})),
        "timestamp": datetime.now().isoformat(),
    }


# ── Auth endpoints ────────────────────────────────────────────────
@app.post("/auth/signup")
def signup(body: SignupInput):
    if body.role not in ("clinician", "auditor"):
        raise HTTPException(400, "role must be 'clinician' or 'auditor'")
    if get_user_by_email(body.email):
        raise HTTPException(409, "Email already registered")
    user_id = create_user(body.name, body.email, body.password, body.role)
    token = create_token(user_id, body.email.lower(), body.role)
    return {
        "token": token,
        "user": {"id": user_id, "name": body.name, "email": body.email.lower(), "role": body.role},
    }


@app.post("/auth/login")
def login(body: LoginInput):
    user = get_user_by_email(body.email)
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(401, "Invalid email or password")
    update_last_login(user["id"])
    token = create_token(user["id"], user["email"], user["role"])
    return {
        "token": token,
        "user": {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]},
    }


@app.get("/auth/me")
def me(payload: dict = Depends(require_auth)):
    user = get_user_by_id(int(payload["sub"]))
    if not user:
        raise HTTPException(404, "User not found")
    return {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]}


# ── Data endpoints ────────────────────────────────────────────────
@app.get("/api/states")
def get_states():
    out = []
    for name, data in _aqi_cache.get("states", {}).items():
        aqi = data.get("aqi_5yr")
        out.append({
            "name": name,
            "aqi_5yr": aqi,
            "pm25_5yr": data.get("pm25_5yr"),
            "aqi_category": None if aqi is None else (
                0 if aqi < 50 else 1 if aqi < 100 else 2 if aqi < 150 else 3 if aqi < 200 else 4
            ),
        })
    return sorted(out, key=lambda x: x["name"])


@app.get("/api/aqi/{state}")
def get_aqi(state: str):
    aqi, pm25, cat = _get_aqi_for_state(state)
    if aqi is None:
        raise HTTPException(404, f"No AQI data for state: {state}")
    return {"state": state, "aqi_5yr": aqi, "pm25_5yr": pm25, "aqi_category": cat}


# ── Clinical endpoints ────────────────────────────────────────────
@app.post("/api/predict")
def predict(patient: PatientInput, payload: dict = Depends(require_auth)):
    patient_dict = _build_patient_dict(patient)
    aqi, pm25, cat = _get_aqi_for_state(patient.state)
    patient_dict["aqi_5yr"] = aqi
    patient_dict["pm25_5yr"] = pm25
    try:
        result = get_prediction(patient_dict)
    except Exception as e:
        logger.exception("Prediction failed")
        raise HTTPException(500, f"Prediction failed: {e}")
    return {
        "prediction": result,
        "aqi": {"aqi_5yr": aqi, "pm25_5yr": pm25, "aqi_category": cat},
    }


@app.post("/api/guidelines")
def guidelines(body: GuidelineQuery, payload: dict = Depends(require_auth)):
    try:
        results = search_guidelines(body.query, k=body.k)
    except Exception as e:
        logger.exception("RAG failed")
        raise HTTPException(500, f"RAG failed: {e}")
    return {"guidelines": results}


@app.post("/api/analyze")
def analyze(patient: PatientInput, include_summary: bool = True,
            payload: dict = Depends(require_auth)):
    """One-shot: predict + guidelines + summary. The endpoint the frontend calls."""
    patient_dict = _build_patient_dict(patient)
    aqi, pm25, cat = _get_aqi_for_state(patient.state)
    patient_dict["aqi_5yr"] = aqi
    patient_dict["pm25_5yr"] = pm25

    try:
        prediction = get_prediction(patient_dict)
    except Exception as e:
        logger.exception("Prediction failed")
        raise HTTPException(500, f"Prediction failed: {e}")

    tier = prediction["tier"]
    recommendation = prediction["recommendation"]

    query = f"lung cancer screening age {patient.age} pack-years {patient.pack_years:.1f} tier {tier}"
    try:
        guidelines_list = search_guidelines(query, k=3)
    except Exception as e:
        logger.warning(f"RAG failed: {e}")
        guidelines_list = []

    summary_text = ""
    if include_summary:
        summary_text = _generate_clinical_summary(patient_dict, tier, recommendation, aqi)

    return {
        "prediction": prediction,
        "guidelines": guidelines_list,
        "summary": summary_text,
        "aqi": {"aqi_5yr": aqi, "pm25_5yr": pm25, "aqi_category": cat},
        "patient": patient_dict,
    }


@app.post("/api/report")
def report(patient: PatientInput, payload: dict = Depends(require_clinician)):
    """Generate PDF report. Clinician role only."""
    patient_dict = _build_patient_dict(patient)
    aqi, pm25, cat = _get_aqi_for_state(patient.state)
    patient_dict["aqi_5yr"] = aqi
    patient_dict["pm25_5yr"] = pm25

    try:
        prediction = get_prediction(patient_dict)
    except Exception as e:
        logger.exception("Prediction failed")
        raise HTTPException(500, f"Prediction failed: {e}")

    query = f"lung cancer screening age {patient.age} pack-years {patient.pack_years:.1f} tier {prediction['tier']}"
    try:
        guidelines_list = search_guidelines(query, k=3)
    except Exception:
        guidelines_list = []

    summary_text = _generate_clinical_summary(
        patient_dict, prediction["tier"], prediction["recommendation"], aqi
    )

    try:
        pdf_bytes = generate_clinical_report(
            patient=patient_dict,
            input_data={"AQI_5YR": aqi, "PM25_5YR": pm25, "AQI_CATEGORY": cat},
            tier=prediction["tier"],
            recommendation=prediction["recommendation"],
            risk_score=prediction["risk_score"],
            contributing_factors=prediction.get("contributing_factors", []),
            guidelines=guidelines_list,
            ai_summary=summary_text,
            team_info=REPORT_CONFIG,
            ci_lower=prediction.get("ci_lower"),
            ci_upper=prediction.get("ci_upper"),
            shap_items=prediction.get("shap_items", []),
            is_deidentified=False,
            logo_path=LOGO_PATH if os.path.exists(LOGO_PATH) else None,
            watermark_path=WATERMARK_PATH if os.path.exists(WATERMARK_PATH) else None,
        )
    except Exception as e:
        logger.exception("PDF generation failed")
        raise HTTPException(500, f"PDF generation failed: {e}")

    filename = f"LungCancer_{patient_dict['patient_id']}_{datetime.now():%Y%m%d_%H%M}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)