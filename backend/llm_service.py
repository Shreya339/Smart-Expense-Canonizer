from typing import Optional, Tuple, List
from .config import (
    OPENAI_API_KEY,
    GEMINI_API_KEY,
    CATEGORY_WHITELIST,
)
from .guardrails import validate_json_candidate

# ======================
# PROMPT
# ======================
SYSTEM_PROMPT = f"""
You are a responsible bookkeeping AI.

Choose ONE category from:
{CATEGORY_WHITELIST}

Rules:
- Return ONLY valid JSON
- Fields: category, confidence
- confidence must be between 0.0 and 1.0
- If unsure → category = "Needs Review", confidence ≤ 0.2
"""

# ======================
# MODEL CALLS
# ======================
def call_openai(description: str, temperature: float) -> Optional[str]:
    if not OPENAI_API_KEY:
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)

        resp = client.responses.create(
            model="gpt-4.1-mini",
            temperature=temperature,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Description: {description}"}
            ]
        )

        return resp.output[0].content[0].text.strip()

    except Exception as e:
        print("🔴 OPENAI ERROR:", e)
        return None


def call_gemini(description: str, temperature: float) -> Optional[str]:
    if not GEMINI_API_KEY:
        return None

    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)

        model = genai.GenerativeModel(
            "gemini-2.5-flash",
            generation_config={"temperature": temperature}
        )

        res = model.generate_content(
            f"{SYSTEM_PROMPT}\n\nDescription: {description}"
        )

        return (res.text or "").strip()

    except Exception as e:
        print("🔴 GEMINI ERROR:", e)
        return None


# ======================
# TRUST HELPERS
# ======================
def _confidence(c: dict) -> float:
    return float(c.get("confidence", 0.0))


def _confidence_close(a: dict, b: dict, delta: float = 0.15) -> bool:
    return abs(_confidence(a) - _confidence(b)) <= delta


def _self_consistent(a: dict, b: dict) -> bool:
    """
    Self-consistency = same category AND stable confidence.
    """
    return (
        a.get("category") == b.get("category")
        and _confidence_close(a, b)
    )


def _agreement_score(categories: List[str]) -> float:
    best = max(categories.count(c) for c in set(categories))
    return round(best / len(categories), 3)


def _resolve_disagreement(candidates: List[dict]) -> Tuple[Optional[dict], List[str]]:
    """
    Conservative disagreement resolution:
    - Pick highest confidence
    - Surface variance as risk
    """
    if not candidates:
        return None, ["model_disagreement"]

    confidences = [_confidence(c) for c in candidates]
    chosen = max(candidates, key=_confidence)

    flags = ["model_disagreement"]
    if max(confidences) - min(confidences) > 0.3:
        flags.append("high_confidence_variance")

    return chosen, flags


def _reliability_level(meta: dict) -> str:
    """
    Explicitly encode non-guaranteed correctness.
    """
    if meta.get("self_consistent") and meta.get("agreement_score", 0) >= 0.8:
        return "high"
    if meta.get("self_consistent"):
        return "medium"
    return "low"


# ======================
# CORE LOGIC
# ======================
def classify_with_models(description: str):
    """
    LOCKED LOGIC:
    - OpenAI twice → self-consistency
    - Gemini twice ONLY if OpenAI unusable or unstable
    """

    risk_flags = []
    all_categories = []

    # -------- OPENAI --------
    o1_raw = call_openai(description, temperature=0.2)
    o2_raw = call_openai(description, temperature=0.3)

    o1, f1 = validate_json_candidate(o1_raw) if o1_raw else (None, [])
    o2, f2 = validate_json_candidate(o2_raw) if o2_raw else (None, [])

    risk_flags.extend(f1 + f2)

    if o1 and o2:
        all_categories += [o1["category"], o2["category"]]

        if _self_consistent(o1, o2):
            meta = {
                "self_consistent": True,
                "cross_model_used": False,
                "agreement_score": 1.0,
                "risk_flags": risk_flags,
            }
            meta["reliability"] = _reliability_level(meta)
            return o1, meta

        # Resolve OpenAI disagreement intelligently
        chosen, flags = _resolve_disagreement([o1, o2])
        risk_flags.extend(flags)
        risk_flags.append("openai_self_inconsistent")

    elif o1 or o2:
        risk_flags.append("partial_openai_response")

    # -------- GEMINI FALLBACK --------
    g1_raw = call_gemini(description, temperature=0.2)
    g2_raw = call_gemini(description, temperature=0.3)

    g1, f3 = validate_json_candidate(g1_raw) if g1_raw else (None, [])
    g2, f4 = validate_json_candidate(g2_raw) if g2_raw else (None, [])

    risk_flags.extend(f3 + f4)

    candidates = [c for c in [g1, g2] if c]

    if candidates:
        all_categories += [c["category"] for c in candidates]
        agreement = _agreement_score(all_categories)

        chosen, flags = _resolve_disagreement(candidates)
        risk_flags.extend(flags)

        meta = {
            "self_consistent": len(candidates) == 2 and _self_consistent(g1, g2),
            "cross_model_used": True,
            "agreement_score": agreement,
            "risk_flags": risk_flags,
        }
        meta["reliability"] = _reliability_level(meta)
        return chosen, meta

    # -------- TOTAL FAILURE --------
    return (
        None,
        {
            "self_consistent": False,
            "cross_model_used": True,
            "agreement_score": None,
            "risk_flags": risk_flags + ["all_model_calls_failed"],
            "reliability": "low",
        }
    )
