"""
clinical_agent.py - Pydantic-AI agent wrapping the deterministic ensemble.
"""
import asyncio
from pydantic_ai import Agent
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.providers.ollama import OllamaProvider
from predictor import get_prediction
_model = OllamaModel(
    "qwen2.5:3b",
    provider=OllamaProvider(base_url="http://localhost:11434/v1"),
)
agent = Agent(
    _model,
    system_prompt=(
        "You are a clinical triage assistant for LungCancer.NET. "
        "You MUST call the predict_lung_cancer_risk tool for every patient. "
        "Never invent or estimate a risk score - only report the tool's output. "
        "After calling the tool, write one short factual sentence for the clinician."
    ),
)
@agent.tool_plain
def predict_lung_cancer_risk(
    age: int,
    bmi: float,
    pack_years: float,
    resp_burden: bool,
    chronic_burden: bool,
    state: str = "Ohio",
) -> dict:
    """Run the deterministic 9-predictor ensemble on this patient."""
    result = get_prediction({
        "age": age,
        "bmi": bmi,
        "pack_years": pack_years,
        "resp_burden": int(resp_burden),
        "chronic_burden": int(chronic_burden),
        "low_access": False,
        "sex": 1,
        "state": state,
    })
    return {
        "tier": result["tier"],
        "risk_score": round(result["risk_score"], 6),
        "recommendation": result["recommendation"],
    }
async def _test():
    prompt = (
        "Evaluate this patient: 66-year-old, BMI 27.5, 32 pack-years, "
        "respiratory disease present, chronic disease present, state Ohio. "
        "Call the tool and report the tier."
    )
    result = await agent.run(prompt)
    print("\n=== Agent output ===")
    print(result.output)
    print("\n=== Messages ===")
    for msg in result.all_messages():
        kind = type(msg).__name__
        print(f"  [{kind}]")
        if hasattr(msg, "parts"):
            for part in msg.parts:
                tool_name = getattr(part, "tool_name", None)
                if tool_name:
                    print(f"    -> tool called: {tool_name}")
                    print(f"    -> tool args:   {getattr(part, 'args', '')}")
if __name__ == "__main__":
    asyncio.run(_test())
