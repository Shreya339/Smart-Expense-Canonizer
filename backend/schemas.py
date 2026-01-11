from typing import Optional, List
from pydantic import BaseModel


# =========================================================
# REQUEST MODELS
# =========================================================

class ClassifyRequest(BaseModel):
    """
    Input sent from UI to classify a single expense.
    """
    description: str
    amount: Optional[float] = None
    date: Optional[str] = None


# =========================================================
# DECISION BLOCK
# =========================================================

class DecisionBlock(BaseModel):
    """
    Final decision produced by the system.

    This is what accounting logic ultimately consumes.
    """
    final_category: str
    confidence: float
    needs_review: bool
    risk_level: str
    source: str


# =========================================================
# TRUST SIGNALS BLOCK
# =========================================================

class TrustSignals(BaseModel):
    """
    Signals that explain HOW trustworthy the decision is.
    These are critical for Responsible AI in fintech.
    """
    agreement_score: Optional[float] = None          # Self / cross-model agreement
    self_consistent: Optional[bool] = None           # Same model consistency
    cross_model_used: Optional[bool] = None           # Fallback model triggered
    risk_flags: List[str] = []                        # Why risk increased


# =========================================================
# EVIDENCE BLOCK
# =========================================================

class EvidenceBlock(BaseModel):
    """
    Human-readable explanation trail.
    Enables auditability and customer trust.
    """
    merchant_normalized: Optional[str] = None
    evidence_list: List[str] = []
    summary: Optional[str] = ""


# =========================================================
# RISK BLOCK
# =========================================================

class RiskBlock(BaseModel):
    """
    Quantified system risk assessment.
    Used to decide automation vs review.
    """
    risk_score: float
    needs_review: bool
    pii_redaction: bool
    risk_flags: List[str] = []


# =========================================================
# FULL CLASSIFICATION RESPONSE
# =========================================================

class ClassifyResponse(BaseModel):
    """
    Full structured response returned to the UI.
    """
    decision: DecisionBlock
    trust: TrustSignals
    evidence: EvidenceBlock
    risk: RiskBlock


# =========================================================
# HUMAN-IN-THE-LOOP (HITL) CORRECTION
# =========================================================

class CorrectionRequest(BaseModel):
    """
    Sent when a human corrects the model's decision.

    This is how the system learns SAFELY.
    """
    transaction_id: int
    corrected_category: str


class CorrectionResponse(BaseModel):
    """
    Response after a human correction is applied.
    """
    success: bool
    message: str


# =========================================================
# COUNTERFACTUAL MODELS
# =========================================================

class CounterfactualRequest(BaseModel):
    """
    Used to test 'What-if' reasoning stability.
    """
    description: str
    modifier: str


class CounterfactualResponse(BaseModel):
    """
    Result of counterfactual analysis.
    """
    original_category: str
    new_category: str
    changed: bool
    trigger_words: List[str]
    analysis_summary: str
