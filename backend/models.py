from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


# ==========================================================
# TABLE 1 — TRANSACTION HISTORY & AUDIT LOG
# ==========================================================
class Transaction(SQLModel, table=True):

    # Primary key — unique ID for every record
    id: Optional[int] = Field(default=None, primary_key=True)

    # Transaction date (optional — user may not always provide it)
    date: Optional[str] = None

    # What the user originally typed / raw bank memo
    description_raw: str

    # Normalized version (lowercased, punctuation removed, etc.)
    description_clean: str

    # Optional monetary amount
    amount: Optional[float] = None


    # ------------------------------
    # MODEL PREDICTION DATA
    # ------------------------------

    # What category the model predicted
    predicted_category: Optional[str] = None

    # Confidence value from the pipeline
    confidence: Optional[float] = None

    # JSON explaining why the decision happened
    # stored as string so UI or audits can read it later
    evidence_json: Optional[str] = None

    # Short human-readable summary of why the decision was made
    explanation_summary: Optional[str] = None

    # Where the answer came from:
    # "rules" | "embedding" | "openai" | "gemini" | "none"
    source: Optional[str] = None

    # Whether this result should be reviewed manually
    needs_review: bool = False


    # ------------------------------
    # RISK + TRUST SIGNALS
    # ------------------------------

    # Final computed risk score (0–1)
    risk_score: Optional[float] = None

    # JSON list of risk flags (like "missing_confidence")
    risk_flags: Optional[str] = None

    # Whether PII was detected + redacted from the original input
    had_pii_redaction: bool = False


    # ------------------------------
    # HUMAN OVERRIDE INFO
    # ------------------------------

    # Final category after review
    # (may be same as predicted OR corrected)
    final_category: Optional[str] = None

    # Whether a human changed the AI’s answer
    overridden: bool = False

    # What the human changed it to
    override_category: Optional[str] = None

    # Timestamp when override occurred
    override_timestamp: Optional[datetime] = None


    # ------------------------------
    # METADATA
    # ------------------------------

    # When the record was created
    created_at: datetime = Field(default_factory=datetime.utcnow)




# ==========================================================
# TABLE 2 — MERCHANT MEMORY / EMBEDDINGS DATABASE
# ==========================================================
class MerchantEmbedding(SQLModel, table=True):

    # Unique ID for each stored merchant record
    id: Optional[int] = Field(default=None, primary_key=True)

    # Canonical merchant name (cleaned text)
    merchant_name: str

    # Embedding vector stored as JSON string
    embedding_json: str

    # The most recent category label we associated with this merchant
    category_label: Optional[str] = None

    # How many times we've seen this merchant in history
    num_seen: int = 0

    # How many times humans corrected this merchant's category
    num_overrides: int = 0

    # When this record was last updated
    last_updated: datetime = Field(default_factory=datetime.utcnow)



"""
Table -1 - Transaction — Your Audit Ledger

Every transaction stores:

✔ the raw description
✔ the cleaned description
✔ the predicted category
✔ the confidence score used
✔ the explanation
✔ the source
✔ the risk score
✔ the risk flags
✔ whether PII was detected
✔ whether a human corrected it
✔ when it happened

This makes your AI auditable + trustworthy.

This is HUGE

They care deeply about:

customer trust
data lineage
human review controls
explainability
reversibility

MerchantEmbedding — Your Learning Memory

This table lets your system learn over time without retraining a model.

Each merchant stores:

✔ merchant name
✔ embedding
✔ category label
✔ number of times seen
✔ number of human overrides
✔ last updated time

So your app can say:

“We’ve seen Southwest Airlines 27 times
confidence is high
users never override
so we trust it.”

This is the same pattern used by real fintech AI systems.

🧠 Key Business/AI Concepts You’re Demonstrating

This file proves you understand:

✔ Explainable AI

Because you store evidence + explanations

✔ AI Risk Governance

Because you store risk flags & override history

✔ Human-in-the-Loop Learning

Because overrides are tracked

✔ Merchant Normalization / Memory

Your AI gets smarter without retraining models

✔ Compliance Readiness

If a regulator asked:

Why did we classify this transaction that way?

Your answer would be:

Here is the stored reason, timestamp, risk data, and who changed it.

Very powerful.

I persisted not just the transaction, but also the model’s reasoning, risk score, and human override history into SQL tables. That way, the system is fully auditable — we can reconstruct why every decision was made, detect recurring risk signals, and build merchant-level memory so future decisions get smarter without retraining a model.

This also supports human-in-the-loop workflows — if a reviewer corrects a category, I increment override counts so future risk scores adjust accordingly.
"""