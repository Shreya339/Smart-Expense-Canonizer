from typing import Optional, List
from pydantic import BaseModel


# ================== REQUEST MODELS ==================

class ClassifyRequest(BaseModel):
    description: str
    amount: Optional[float] = None
    date: Optional[str] = None



# ================== DECISION BLOCK ==================

class DecisionBlock(BaseModel):
    final_category: str
    confidence: float
    needs_review: bool
    risk_level: str
    source: str



# ================== TRUST SIGNAL BLOCK ==================

class TrustSignals(BaseModel):
    agreement_score: Optional[float] = None
    self_consistent: Optional[bool] = None
    cross_model_used: Optional[bool] = None
    risk_flags: List[str] = []



# ================== EVIDENCE BLOCK ==================

class EvidenceBlock(BaseModel):
    merchant_normalized: Optional[str] = None
    evidence_list: List[str] = []
    summary: Optional[str] = ""



# ================== RISK BLOCK ==================

class RiskBlock(BaseModel):
    risk_score: float
    needs_review: bool
    pii_redaction: bool
    risk_flags: List[str] = []



# ================== FULL CLASSIFY RESPONSE ==================

class ClassifyResponse(BaseModel):
    decision: DecisionBlock
    trust: TrustSignals
    evidence: EvidenceBlock
    risk: RiskBlock



# ================== COUNTERFACTUAL MODELS ==================

class CounterfactualRequest(BaseModel):
    description: str
    modifier: str


class CounterfactualResponse(BaseModel):
    original_category: str
    new_category: str
    changed: bool
    trigger_words: List[str]
    analysis_summary: str
