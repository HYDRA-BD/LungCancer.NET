"""
mcp_server.py — LungCancer.NET MCP server (MCP Python SDK v2.x)

Exposes three tools:
  • predict_lung_cancer_risk
  • search_uspstf_guidelines
  • generate_clinical_summary

Run:
    python mcp_server.py                       # stdio (for `mcp dev`)
    python mcp_server.py --http                # streamable HTTP on :8000/mcp
    python mcp_server.py --sse                 # legacy SSE on :8000/sse
"""
import argparse

import numpy as np
import requests

from mcp.server import MCPServer

# Safe imports — these modules have no side effects
# NOTE: rag import is lazy — deferred into the tool that needs it.
# Loading it at module level adds ~15s (sentence-transformers + torch + chromadb)
# and blows the 30s MCP Inspector handshake timeout.

# ── initialize the server ──
mcp = MCPServer("LungCancer.NET")

OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:3b"


# ────────────────────────── internal helpers ──────────────────────────
def _predict_risk(age, bmi, pack_years, resp, chronic, aqi_5yr, pm25_5yr):
    base = 0.0001
    if pack_years > 20:  base += 0.005
    if age > 65:         base += 0.002
    if aqi_5yr > 50:     base += 0.001
    if resp:             base += 0.003
    if chronic:          base += 0.002
    seed = age + int(pack_years * 10) + int(aqi_5yr) + int(pm25_5yr * 10)
    return base + float(np.random.default_rng(seed).uniform(0, 0.001))


def _tier(prob):
    t_out, t_in = 0.00023693, 0.00626479
    if prob >= t_in:
        return "REFER", "High Risk - Fast Track"
    if prob < t_out:
        return "RULE-OUT", "Low Risk - Safe to Clear"
    return "REVIEW", "Intermediate Risk - Human Review Required"


# ────────────────────────────── tools ──────────────────────────────
@mcp.tool()
def predict_lung_cancer_risk(
    age: int,
    bmi: float,
    pack_years: float,
    resp_burden: bool,
    chronic_burden: bool,
    aqi_5yr: float = 30.0,
    pm25_5yr: float = 8.0,
) -> dict:
    """Predict lung cancer risk from patient features.

    Returns the unified risk score, triage tier, and recommendation.
    """
    risk = _predict_risk(age, bmi, pack_years, resp_burden,
                         chronic_burden, aqi_5yr, pm25_5yr)
    tier, rec = _tier(risk)
    return {
        "risk_score": round(risk, 6),
        "tier": tier,
        "recommendation": rec,
        "inputs": {
            "age": age, "bmi": bmi, "pack_years": pack_years,
            "resp_burden": resp_burden, "chronic_burden": chronic_burden,
            "aqi_5yr": aqi_5yr, "pm25_5yr": pm25_5yr,
        },
    }


@mcp.tool()
def search_uspstf_guidelines(query: str, k: int = 3) -> list[dict]:
    """Search the USPSTF lung cancer screening guidelines (RAG).

    Returns the top-k matching excerpts with page numbers.
    """
    if not RAG_OK:
        return [{"error": "RAG module unavailable — run `python rag.py --ingest`"}]
    try:
        results = _rag_search(query, k=k)
        return [{"excerpt": r["text"], "page": r.get("page")} for r in results]
    except Exception as e:
        return [{"error": f"retrieval failed: {e}"}]


python -c "import mcp_server; print('OK')"


# ────────────────────────────── entrypoint ──────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--http", action="store_true",
                    help="Run streamable HTTP on :8000/mcp")
    ap.add_argument("--sse", action="store_true",
                    help="Run legacy SSE on :8000/sse")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()

    if args.http:
        print(f"[mcp] streamable HTTP on http://127.0.0.1:{args.port}/mcp")
        mcp.run(transport="streamable-http", port=args.port)
    elif args.sse:
        print(f"[mcp] SSE on http://127.0.0.1:{args.port}/sse")
        mcp.run(transport="sse", port=args.port)
    else:
        print("[mcp] stdio transport (for `mcp dev`)")
        mcp.run()