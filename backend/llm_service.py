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
# CORE LOGIC
# ======================
def _self_consistent(a: dict, b: dict) -> bool:
    return a.get("category") == b.get("category")


def _agreement_score(categories: List[str]) -> float:
    best = max(categories.count(c) for c in set(categories))
    return round(best / len(categories), 3)


def classify_with_models(description: str):
    """
    LOCKED LOGIC:
    - OpenAI twice → self-consistency
    - Gemini twice ONLY if OpenAI unusable
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
            return (
                o1,
                {
                    "self_consistent": True,
                    "cross_model_used": False,
                    "agreement_score": 1.0,
                    "risk_flags": risk_flags
                }
            )
        else:
            risk_flags.append("openai_self_inconsistent")
            # don't return, continue to gemini

    elif o1 or o2:
        chosen = o1 or o2
        all_categories.append(chosen["category"])
        risk_flags.append("partial_openai_response");

        # if one call fails, don't return, continue to gemini

        # return (
        #     chosen,
        #     {
        #         "self_consistent": False,
        #         "cross_model_used": False,
        #         "agreement_score": None,
        #         "risk_flags": risk_flags + ["partial_openai_response"]
        #     }
        # )

    # -------- GEMINI FALLBACK --------
    g1_raw = call_gemini(description, temperature=0.2)
    g2_raw = call_gemini(description, temperature=0.3)

    g1, f3 = validate_json_candidate(g1_raw) if g1_raw else (None, [])
    g2, f4 = validate_json_candidate(g2_raw) if g2_raw else (None, [])

    risk_flags.extend(f3 + f4)

    if g1 and g2:
        all_categories += [g1["category"], g2["category"]]

        agreement = _agreement_score(all_categories)

        return (
            g1 if _self_consistent(g1, g2) else g1,
            {
                "self_consistent": _self_consistent(g1, g2),
                "cross_model_used": True,
                "agreement_score": agreement,
                "risk_flags": risk_flags
            }
        )

    elif g1 or g2:
        chosen = g1 or g2
        all_categories.append(chosen["category"])
        risk_flags.append("partial_gemini_response");

        # if one call fails, don't return, escalate to total failure
        # return (
        #     chosen,
        #     {
        #         "self_consistent": False,
        #         "cross_model_used": True,
        #         "agreement_score": None,
        #         "risk_flags": risk_flags + ["partial_gemini_response"]
        #     }
        # )

    # -------- TOTAL FAILURE --------
    return (
        None,
        {
            "self_consistent": False,
            "cross_model_used": True,
            "agreement_score": None,
            "risk_flags": risk_flags + ["all_model_calls_failed"]
        }
    )
