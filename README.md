# Smart Expense Canonizer — Trust‑First AI Classification System

Smart Expense Canonizer is a **financial‑grade, explainable AI system** that classifies expense transactions while prioritizing **trust, safety, and auditability** over raw automation.

This project is intentionally designed **not** as a “smart model demo”, but as a **production‑style AI decision system** suitable for fintech environments.

---

##  Core Philosophy

> **Accuracy is not enough. Trust is the real problem.**

Every design decision in this system follows four principles:

- **Trust before flash**
- **Explainability over opacity**
- **Human‑in‑the‑loop by default**
- **Fail safe, never silently**

The system is built to **know when not to guess**.

---

##  What the System Does

When a user submits an expense description:

- The system classifies the transaction
- Computes **confidence** and **risk**
- Generates **human‑readable evidence**
- Flags uncertainty instead of guessing
- Logs decisions for auditability
- Learns safely from corrections

Instead of saying:

> “This is Meals & Entertainment”

It says:

> “This is Meals & Entertainment, with 92% confidence,  
> because similar merchants were classified this way in the past.”

---

##  High‑Level Architecture

```
┌────────────┐
│  Streamlit │   ← UI
└─────┬──────┘
      │
      ▼
┌────────────┐
│  FastAPI   │   ← API Layer
│  /classify │
│ /counterf. │
└─────┬──────┘
      │
      ▼
┌───────────────────────────────────────┐
│        Classification Pipeline        │
│                                       │
│ 1. PII Redaction                      │
│ 2. Text Normalization                 │
│ 3. Embedding Similarity (Memory)      │
│ 4. Deterministic Rules Engine         │
│ 5. LLM Fallback (OpenAI → Gemini)     │
│ 6. Confidence & Risk Scoring          │
│ 7. Evidence Generation                │
│ 8. Drift Awareness                    │
└─────┬─────────────────────────────────┘
      │
      ▼
┌────────────┐
│   SQLite   │  ← Audit Log / Memory
└────────────┘
```

---

##  Decision Layers (In Order)

### 1️. PII Redaction
Sensitive data (emails, phone numbers, etc.) is removed **before any AI decision**.

### 2️. Embedding Similarity (Primary Path)
- Merchant descriptions are embedded
- Compared against historical transactions
- High similarity ⇒ **reuse past category confidently**
- Fast, cheap, consistent, explainable

### 3️. Rules Engine (Deterministic Safety Net)
- Explicit mappings (e.g., Uber → Travel)
- Predictable and auditable behavior
- Prevents unnecessary LLM calls

### 4️. LLM Fallback (Last Resort)
- OpenAI called first (self‑consistency logic)
- Gemini used as fallback
- Strict JSON validation + category whitelist
- If models fail → **Needs Review**

AI is used **only when necessary**.

---

##  Trust & Safety Outputs

Every classification returns:

- **Confidence Score** (model certainty)
- **Risk Score** (system‑level safety)
- **Needs Review flag**
- **Evidence Trail** (why this decision happened)
- **Source Attribution** (embedding / rules / LLM)

No silent failures. No black boxes.

---

##  Risk Scoring Logic

Risk increases when:
- Confidence is low
- Similarity is weak
- Merchant is unseen
- Overrides are frequent
- Drift is detected
- Validation flags appear

Risk is capped at **1.0** and mapped to:
- Low
- Medium
- High

---

##  Counterfactual Reasoning

The `/counterfactual` endpoint answers:

> “If the description changed slightly, would the category change?”

This detects **fragile or unstable decisions**, which is critical in financial workflows.

---

##  Testing Strategy

- **Unit tests** for:
  - Risk scoring
  - Evidence generation
  - Guardrails
- **Integration tests** for:
  - `/classify` endpoint
  - End‑to‑end API behavior

Tests are written with clarity and comments — like production code.

---

##  Running the Project

Provide OPENAI_API_KEY and GEMINI_API_KEY in backend/.env

### VENV
```
.venv\Scripts\activate
```

### Backend
```bash
python -m uvicorn backend.main:app --reload
```

### UI
```bash
cd ui
streamlit run app.py
```

### Tests
```bash
pytest
```
### DB
```bash
sqlite3 transactions.db
.tables
DELETE FROM merchantembedding;
DELETE FROM "transaction";
```
---

##  Why This Matters

Financial systems cannot afford:
- Confidently wrong AI
- Silent failures
- Unexplainable decisions

This system is built to:
- Surface uncertainty
- Preserve human control
- Earn trust incrementally

---

##  Final Note

This project reflects how I think about **responsible AI systems**:

> Not just *what* the model predicts —  
> but *when it should refuse*, *how it explains itself*,  
> and *how humans stay in control*.

That mindset is what turns AI from a demo into a platform.
