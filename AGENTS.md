# LungCancer.NET — Agent Context

## Project
Composite AI clinical pre-screening system for lung cancer risk using BRFSS
survey data. Targets low-cost, population-level screening for rural and
underserved populations where imaging is not widely available.

## Architecture
- **9-predictor ensemble ladder**: XGBoost + CatBoost + LightGBM, each
  trained with three class weights {1, 5, 10}
- **OOF stacked meta-learner** (logistic regression on logits of the 9
  base OOF predictions) for uncertainty-aware triage
- **Equity-Aware Subgroup Sensitivity Floor** — RULE-OUT only below the
  highest threshold that keeps sensitivity >= floor in every eligible
  demographic subgroup
- **Access-Aware Cost Function** — missed-case cost is weighted up for
  patients with limited follow-up access (cost barrier, no recent checkup,
  rural); referral cost is weighted up for the same group
- **External validation** on LLCP2023 with frozen thresholds

## Stack
- Python 3.10+, scikit-learn, xgboost, catboost, lightgbm, scikit-optimize
- pandas, numpy, scipy, joblib
- SHAP for interpretability, matplotlib for figures
- Streamlit for the demo UI
- Groq (OpenAI-compatible API) for the clinical-summary LLM layer
- Optional: Ollama (local Qwen2.5 / DeepSeek-R1) for offline inference
- Optional: Chroma + sentence-transformers for the USPSTF guideline RAG

## Data
- Inputs: BRFSS 2024 (`LLCP2024.csv`, training) and BRFSS 2023
  (`LLCP2023.csv`, external validation), downloaded from CDC.
- Target: `target_lung` derived from `CNCRTYP2 == 14` (lung cancer)
  vs `CHCOCNC1 == 2` (never had cancer). Ambiguous records → NaN → dropped.

## Conventions for AI assistants
- Class weights {0:1, 1:5, 1:10} — keep consistent across the ladder
- Never drop the equity constraint without re-running the regression eval
- SHAP values required for every prediction (explanation layer)
- Never hardcode paths — use `Path(__file__).parent`
- Preserve the leakage filter (`shared_gpu_utils.filter_leaky`)
- The meta-learner must be fit on OOF predictions only, never in-sample

## Workflows
- Install deps: `pip install -r requirements.txt`
- Train all models: `python orchestrator.py`
- Serve the UI: `streamlit run app.py`
- SHAP only: `python shap_orchestrator.py`
- Generate the A→Z report: `python research_report.py`

## Files that must not be modified casually
- `shared_gpu_utils.py` — `define_target_labels` is the source of truth
- `meta_specialist.py` — the OOF leakage controls are load-bearing
- `specialist.py` — the cross-model voting rule is the paper's main claim