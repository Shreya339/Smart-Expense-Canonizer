import json
import re
import time
import hashlib
from typing import Optional, Tuple

from .config import (
    OPENAI_API_KEY,
    GEMINI_API_KEY,
    CATEGORY_WHITELIST,
    FEATURE_PII_SAFE_AUDIT_LOGGING,
    AUDIT_LOG_PATH,
    PII_SALT,
    FEATURE_REASON_VALIDATION,
    FEATURE_CROSS_MODEL_SCORING
)

from .guardrails import validate_json_candidate


SYSTEM_PROMPT = f"""
You are a responsible bookkeeping AI.

Your job is to classify an expense into ONE of the allowed categories:

{CATEGORY_WHITELIST}

Rules:
• Always return ONLY JSON. No prose.
• Field `category` must be one of the allowed categories.
• Include a confidence field between 0.0–1.0 (your internal certainty).
• If uncertain, lower confidence — do NOT guess confidently.
• If you cannot decide, use category: "Needs Review" and confidence 0.1
"""


# ======================================
#  OPENAI
# ======================================
def call_openai(description: str, temperature: float) -> Optional[str]:
    """
    Calls OpenAI with an explicit temperature.
    Used for self-consistency by varying temperature slightly.
    """
    if not OPENAI_API_KEY:
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)

        completion = client.responses.create(
            model="gpt-4.1-mini",
            temperature=temperature,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Description: {description}"}
            ]
        )

        # Extract first text block safely
        text = completion.output[0].content[0].text.strip()
        return text.replace("```json", "").replace("```", "").strip()

    except Exception as e:
        print("🔴 OPENAI ERROR:", e)
        return None


# ======================================
#  GEMINI
# ======================================
def call_gemini(description: str, temperature: float) -> Optional[str]:
    """
    Gemini equivalent with temperature variation.
    """
    if not GEMINI_API_KEY:
        return None

    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)

        model = genai.GenerativeModel(
            "gemini-2.0-flash",
            generation_config={"temperature": temperature}
        )

        res = model.generate_content(
            f"{SYSTEM_PROMPT}\n\nDescription: {description}"
        )

        text = (res.text or "").strip()
        return text.replace("```json", "").replace("```", "").strip()

    except Exception as e:
        print("🔴 GEMINI ERROR:", e)
        return None


# ======================================
#  CORE LLM DECISION LOGIC
# ======================================
def classify_with_models(description: str) -> Tuple[Optional[dict], str, list]:
    """
    Strategy:
      ✓ OpenAI twice with temperature variation → self-consistency
      ✓ Gemini twice with temperature variation → fallback self-consistency
      ✓ Strict JSON + whitelist validation
      ✓ Risk flags on disagreement or failure
    """

    risk_flags = []

    def parse(raw: Optional[str]):
        if not raw:
            return None, []
        data, flags = validate_json_candidate(raw)
        return data, flags

    best = None
    source = "none"

    # -------- OPENAI: self-consistency via temperature diff --------
    o1 = call_openai(description, temperature=0.1)
    o2 = call_openai(description, temperature=0.3)

    d1, f1 = parse(o1)
    d2, f2 = parse(o2)

    risk_flags.extend(f1 + f2)

    if d1 and d2:
        if d1.get("category") == d2.get("category"):
            best = d1
            source = "openai"
        else:
            risk_flags.append("openai_self_inconsistent")
    elif d1 or d2:
        best = d1 or d2
        source = "openai"

    # -------- GEMINI: fallback self-consistency --------
    if not best and GEMINI_API_KEY:
        g1 = call_gemini(description, temperature=0.1)
        g2 = call_gemini(description, temperature=0.3)

        d3, f3 = parse(g1)
        d4, f4 = parse(g2)

        risk_flags.extend(f3 + f4)

        if d3 and d4 and d3.get("category") == d4.get("category"):
            best = d3
            source = "gemini"
        elif d3 or d4:
            best = d3 or d4
            source = "gemini"

    if not best:
        return None, "none", risk_flags + ["all_model_calls_failed"]

    return best, source, risk_flags


# ======================================
#  TRUST UTILITIES
# ======================================

SAFE_LOG_PATTERN = re.compile(r"[A-Za-z0-9 _\-\.\,]+")


def pii_hash(text: str) -> str:
    if not text:
        return ""
    return hashlib.sha256((text + PII_SALT).encode()).hexdigest()[:16]


def reason_grounding(description: str, evidence: list):
    """
    Ensures explanations are grounded in the input text.
    """
    issues = []
    desc = (description or "").lower()

    for ev in (evidence or []):
        toks = re.findall(r"[a-z0-9]+", ev.lower())
        if toks and not any(t in desc for t in toks):
            issues.append(f"ungrounded:{ev[:24]}")

    return issues


def agreement_score(categories: list):
    """
    Computes agreement ratio across multiple runs.
    """
    if not categories:
        return 0.0
    total = len(categories)
    best = max(categories.count(c) for c in set(categories))
    return round(best / total, 3)


def write_audit_log(entry: dict):
    """
    PII-safe audit logging.
    """
    if not FEATURE_PII_SAFE_AUDIT_LOGGING:
        return

    e = dict(entry)
    raw = e.pop("raw_description", "")
    e["merchant_hash"] = pii_hash(raw)
    e["ts"] = int(time.time())

    try:
        with open(AUDIT_LOG_PATH, "a") as f:
            f.write(json.dumps(e) + "\n")
    except Exception:
        pass


# ======================================
#  ENHANCED WRAPPER
# ======================================
def enhanced_classify(description: str):
    """
    Runs classification twice to compute agreement score.
    """

    cats = []
    flags = []
    source = None
    res = None

    d1, s1, f1 = classify_with_models(description)
    if d1:
        cats.append(d1.get("category"))
        flags.extend(f1)
        res = d1
        source = s1

    d2, s2, f2 = classify_with_models(description)
    if d2:
        cats.append(d2.get("category"))
        flags.extend(f2)

    score = agreement_score(cats) if FEATURE_CROSS_MODEL_SCORING else None

    if FEATURE_REASON_VALIDATION and res:
        rg = reason_grounding(description, res.get("evidence") or [])
        flags.extend(rg)

    write_audit_log({
        "raw_description": description,
        "categories": cats,
        "agreement_score": score,
        "source": source,
        "risk_flags": flags
    })

    return res, source, score, flags
