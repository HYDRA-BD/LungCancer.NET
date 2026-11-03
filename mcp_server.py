"""
mcp_server.py — LungCancer.NET Secured Model Context Protocol (MCP) Server.

Architecture & Permissions Policy:
  • Read-Only Operations Only: No write tools, no database alterations, no file system writes.
  • Zero Shell Execution: No subprocess execution, no shell spawning, no eval/exec.
  • Strict Input Validation: All parameters are strictly sanitized and clamped to clinical ranges.
  • Ephemeral Data Handling: No patient identifiers or biometrics are ever persisted to disk.

Exposes three secured read-only tools:
  1. predict_lung_cancer_risk: Runs the calibrated 9-predictor ensemble & XAI SHAP engine.
  2. search_uspstf_guidelines: Semantic RAG search across the USPSTF guideline vector store.
  3. get_clinical_summary: Generates an evidence-based clinical pulmonology assessment.
"""
from __future__ import annotations

import argparse
import re
from typing import Any, Dict, List, Optional

from mcp.server import MCPServer

# Lazy / safe imports from core modular components
try:
    from predictor import get_prediction
    PREDICTOR_OK = True
except Exception as _e:
    PREDICTOR_OK = False
    _PRED_ERR = str(_e)

try:
    from rag import search_guidelines
    RAG_OK = True
except Exception as _e:
    RAG_OK = False
    _RAG_ERR = str(_e)

# Initialize MCP Server instance with minimal permissions
mcp = MCPServer("LungCancer.NET-Clinical-Server")


# ────────────────────────── Security Helpers ──────────────────────────
def _sanitize_query(text: str, max_len: int = 200) -> str:
    """Sanitizes text queries against injection and limits length."""
    if not text:
        return ""
    clean = re.sub(r"[^\w\s\-\.,\?]", "", str(text))
    return clean.strip()[:max_len]


def _clamp(val: float, min_v: float, max_v: float) -> float:
    """Clamps a floating point value between min and max bounds."""
    try:
        return max(min_v, min(float(val), max_v))
    except (TypeError, ValueError):
        return min_v


# ────────────────────────────── MCP Tools ──────────────────────────────
@mcp.tool()
def predict_lung_cancer_risk(
    age: int,
    bmi: float,
    pack_years: float,
    resp_burden: bool,
    chronic_burden: bool,
    aqi_5yr: float = 42.0,
    pm25_5yr: float = 8.5,
    low_access: bool = False,
) -> Dict[str, Any]:
    """
    Predicts lung cancer risk tier, unified score, and SHAP feature attribution.
    Read-only tool: Does not persist data or execute system commands.

    Args:
        age: Patient age in years (18 to 120).
        bmi: Body Mass Index (10.0 to 80.0).
        pack_years: Cumulative smoking exposure in pack-years (0.0 to 200.0).
        resp_burden: Presence of chronic respiratory condition (COPD/Asthma).
        chronic_burden: Presence of cardiovascular or metabolic comorbidities.
        aqi_5yr: 5-year historical average Air Quality Index (0.0 to 500.0).
        pm25_5yr: 5-year ambient fine particulate matter in µg/m³ (0.0 to 500.0).
        low_access: Indicates patient faces structural/rural healthcare access barriers.

    Returns:
        Structured prediction output with unified risk score, triage tier, and SHAP attribution.
    """
    if not PREDICTOR_OK:
        return {"error": f"Predictor engine unavailable: {_PRED_ERR}"}

    # Strict input validation and range clamping
    safe_age = int(_clamp(age, 18, 120))
    safe_bmi = _clamp(bmi, 10.0, 80.0)
    safe_pack_years = _clamp(pack_years, 0.0, 200.0)
    safe_aqi = _clamp(aqi_5yr, 0.0, 500.0)
    safe_pm25 = _clamp(pm25_5yr, 0.0, 500.0)
    safe_resp = bool(resp_burden)
    safe_chronic = bool(chronic_burden)
    safe_low_access = bool(low_access)

    patient_payload = {
        "age": safe_age,
        "bmi": safe_bmi,
        "pack_years": safe_pack_years,
        "resp_burden": 1 if safe_resp else 0,
        "chronic_burden": 1 if safe_chronic else 0,
        "aqi_5yr": safe_aqi,
        "pm25_5yr": safe_pm25,
        "low_access": safe_low_access,
    }

    result = get_prediction(patient_payload)
    return {
        "risk_score": round(result["risk_score"], 6),
        "risk_percentage": round(result["risk_score"] * 100, 4),
        "tier": result["tier"],
        "tier_label": result["tier_label"],
        "recommendation": result["recommendation"],
        "confidence_interval": [round(result["ci_lower"], 6), round(result["ci_upper"], 6)],
        "equity_guard_triggered": result["equity_guard_triggered"],
        "top_contributing_factors": result["contributing_factors"],
    }


@mcp.tool()
def search_uspstf_guidelines(query: str, k: int = 3) -> List[Dict[str, Any]]:
    """
    Searches the official USPSTF Lung Cancer Screening Guidelines vector database.
    Read-only tool: Does not persist data or execute system commands.

    Args:
        query: Clinical query string (e.g., 'screening eligibility 50 pack years').
        k: Maximum number of guideline excerpts to return (1 to 5).

    Returns:
        List of matching guideline excerpts with page references.
    """
    if not RAG_OK:
        return [{"error": f"RAG vector store unavailable: {_RAG_ERR}"}]

    clean_q = _sanitize_query(query, max_len=200)
    if not clean_q:
        return [{"error": "Empty or invalid query provided."}]

    safe_k = int(_clamp(k, 1, 5))
    try:
        results = search_guidelines(clean_q, k=safe_k)
        if not results:
            return [{"info": "No matching guideline excerpts retrieved for the specified query."}]
        return [{"excerpt": r["text"], "page": r.get("page", "?")} for r in results]
    except Exception as e:
        return [{"error": f"Guideline retrieval error: {str(e)}"}]


@mcp.tool()
def get_clinical_summary(
    age: int,
    pack_years: float,
    resp_burden: bool,
    chronic_burden: bool,
    tier: str,
    recommendation: str,
) -> Dict[str, str]:
    """
    Generates a deterministic clinical narrative assessment for medical records.
    Read-only tool: Does not persist data or execute system commands.

    Args:
        age: Patient age in years.
        pack_years: Cumulative pack-years.
        resp_burden: Whether respiratory comorbidities are present.
        chronic_burden: Whether chronic comorbidities are present.
        tier: Algorithmic triage tier (REFER, REVIEW, RULE-OUT).
        recommendation: Recommended clinical action plan.

    Returns:
        Structured clinical summary statement.
    """
    safe_age = int(_clamp(age, 18, 120))
    safe_pkyrs = _clamp(pack_years, 0.0, 200.0)
    resp_str = "Present" if resp_burden else "Absent"
    chronic_str = "Present" if chronic_burden else "Absent"
    clean_tier = _sanitize_query(tier, max_len=20).upper()
    clean_rec = _sanitize_query(recommendation, max_len=250)

    narrative = (
        f"Clinical Pre-Screening Summary: Patient ({safe_age} years of age) presents with a cumulative "
        f"tobacco exposure of {safe_pkyrs:.1f} pack-years. Chronic respiratory burden is {resp_str.lower()}, "
        f"and comorbid chronic burden is {chronic_str.lower()}. Calibrated multi-predictor ensemble stratifies "
        f"patient into the '{clean_tier}' classification band. Recommended clinical next step: {clean_rec}"
    )
    return {"clinical_summary": narrative}


# ────────────────────────────── Entrypoint ──────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="LungCancer.NET Secured MCP Server")
    ap.add_argument("--http", action="store_true", help="Run streamable HTTP on :8000/mcp")
    ap.add_argument("--sse", action="store_true", help="Run legacy SSE on :8000/sse")
    ap.add_argument("--port", type=int, default=8000, help="Port to bind server to")
    args = ap.parse_args()

    # Enforce safe port boundaries
    safe_port = int(_clamp(args.port, 1024, 65535))

    if args.http:
        print(f"[mcp-secure] Streamable HTTP active on http://127.0.0.1:{safe_port}/mcp (Read-Only)")
        mcp.run(transport="streamable-http", port=safe_port)
    elif args.sse:
        print(f"[mcp-secure] SSE active on http://127.0.0.1:{safe_port}/sse (Read-Only)")
        mcp.run(transport="sse", port=safe_port)
    else:
        print("[mcp-secure] Standard I/O transport active (Read-Only, Zero Shell/Write Access)")
        mcp.run()
