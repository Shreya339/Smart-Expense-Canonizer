"""
“main.py is The front desk of the system. Its the API layer built with FastAPI.
UI submits → FastAPI receives → pipeline classifies → DB logs → response sent back

It exposes two endpoints — /classify and /counterfactual.

/classify runs the expense description through my layered classification pipeline, computes confidence and risk, stores the decision in SQLite for auditability(HUGE for fintech compliance), and returns a structured JSON response to the UI.

/counterfactual performs a ‘what-if’ analysis by appending a modifier like ‘client dinner’ to the description and checking whether the category changes — which helps detect fragile or high-risk classifications.

Together these endpoints make the system explainable, safe, and production-ready rather than just an AI demo.”
"""


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json

from .db import init_db, get_session
from .models import Transaction
from .schemas import (
    ClassifyRequest,
    ClassifyResponse,
    CounterfactualRequest,
    CounterfactualResponse
)
from .classifier import classify_pipeline
from .rules import clean_text


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


# =========================================================
#   CLASSIFY  —  MAIN API ENDPOINT
# =========================================================
@app.post("/classify")
def classify(req: ClassifyRequest):
    """
    UI --> FastAPI --> classifier pipeline --> SQLite log --> UI

    This endpoint is intentionally thin.
    All intelligence lives in the classifier.
    """

    # ---------- Run classification pipeline ----------
    result, evidence, risk, risk_flags, had_pii = classify_pipeline(
        req.description
    )

    # ---------- Persist decision ----------
    tx = Transaction(
        date=req.date or "",
        description_raw=req.description,
        description_clean=result["normalized_merchant"],
        amount=req.amount,
        predicted_category=result["category"],
        confidence=result["confidence"],
        evidence_json=json.dumps(evidence),
        explanation_summary=result.get("explanation", ""),
        source=result.get("source", ""),
        needs_review=result.get("needs_review", False),
        risk_score=risk,
        risk_flags=json.dumps(risk_flags),
        had_pii_redaction=had_pii,
        final_category=result["category"],
        overridden=False,
    )

    with get_session() as session:
        session.add(tx)
        session.commit()

    # ---------- Risk Level ----------
    risk_level = (
        "High" if risk > 0.6 else
        "Medium" if risk > 0.3 else
        "Low"
    )

    # ---------- Structured Response ----------
    return {
        "decision": {
            "final_category": result["category"],
            "confidence": result["confidence"],
            "needs_review": result.get("needs_review", False),
            "risk_level": risk_level,
            "source": result.get("source", "")
        },

        "trust": {
            "agreement_score": result.get("agreement_score"),
            "self_consistent": result.get("self_consistent"),
            "cross_model_used": result.get("cross_model_used"),
            "risk_flags": risk_flags
        },

        "evidence": {
            "merchant_normalized": result["normalized_merchant"],
            "evidence_list": evidence,
            "summary": result.get("explanation", "")
        },

        "risk": {
            "risk_score": risk,
            "needs_review": result.get("needs_review", False),
            "pii_redaction": had_pii,
            "risk_flags": risk_flags
        }
    }



# =========================================================
#   COUNTERFACTUAL  —  WHAT-IF TESTING
# =========================================================
@app.post("/counterfactual", response_model=CounterfactualResponse)
def counterfactual(req: CounterfactualRequest):
    """
    Ask:
       Does adding text like `client dinner`
       change the expense category?

    This demonstrates reasoning robustness.
    """

    base, _, _, _, _ = classify_pipeline(req.description)

    modified_text = f"{req.description} ({req.modifier})"
    new, _, _, _, _ = classify_pipeline(modified_text)

    changed = base["category"] != new["category"]

    triggers = clean_text(req.modifier).split()

    return CounterfactualResponse(
        original_category=base["category"],
        new_category=new["category"],
        changed=changed,
        trigger_words=triggers,
        analysis_summary=f"Modifier changed category: {changed}"
    )
