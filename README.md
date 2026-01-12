# Smart Expense Canonizer - Trust‑First AI Classification System

Smart Expense Canonizer is a **financial‑grade, explainable AI system** that classifies expense transactions while prioritizing **trust, safety, and auditability** over raw automation.

This project is intentionally designed **not** as a “smart model demo”, but as a **production‑style AI decision system** suitable for fintech environments.

---

## Why This Project Exists

This project started with a simple question:

**Can we really trust AI when it touches our money?**

Over the past year, I’d been experimenting deeply with the GenAI ecosystem, working with models from OpenAI, Gemini, Llama, Hugging Face, and tools like vector databases. Getting models to do impressive things was fun, and frankly, not that hard.

But I realized that wasn’t the real challenge.

_The real problem is trust._

If an AI summarizes a poem incorrectly, that’s harmless.
If it misclassifies a financial transaction, the consequences are very real - taxes, reporting errors, audits, and compliance risk.

As I explored this space, a few core issues became obvious:

- Most AI systems still operate as black boxes. They produce answers without clearly explaining why.

- Models often respond confidently even when they’re uncertain or guessing.

- In financial workflows, misclassification isn’t just a mistake, it’s a risk.

## The Mission

The goal of this project is simple and deliberate:

> **Build AI that explains its decisions.**

Surface uncertainty instead of hiding it.

Keep humans in the loop when accuracy truly matters.

This isn’t about flashy demos or blind automation.
It’s about designing AI systems people can understand, trust, and rely on - especially when the stakes are financial.

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
│  Streamlit │   ← UI (Streamlit Web Interface)
└─────┬──────┘
      │
      ▼
┌─────────────────┐
│  FastAPI        │   ← API Layer
│  /classify      │   ← Main classification endpoint
│  /correct       │   ← Human correction endpoint
│ /counterfactual │ ← What-if testing endpoint
└─────┬───────────┘
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
- Merchant descriptions are embedded using OpenAI's text-embedding-3-small
- Compared against historical transactions using cosine similarity
- High similarity (≥0.90) ⇒ **reuse past category confidently**
- **Human-verified merchants** (previously corrected) are prioritized
- Fast, cheap, consistent, explainable
- Supports spelling variations and merchant name evolution

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

- **Confidence Score** (model certainty, 0.0-1.0)
- **Risk Score** (system‑level safety, 0.0-1.0)
- **Needs Review flag** (should human review this?)
- **Evidence Trail** (human-readable explanation of decision)
- **Source Attribution** (embedding / rules / llm / human_verified)
- **Trust Signals** (self-consistency, cross-model agreement, risk flags)
- **PII Redaction Flags** (whether sensitive data was detected and removed)

No silent failures. No black boxes.

### Source Types

- **`rules`**: Deterministic rule-based classification (confidence: 0.95)
- **`embedding`**: Semantic similarity match from merchant memory (confidence: 0.90)
- **`human_verified`**: Previously corrected by human (confidence: 0.95, highest priority)
- **`llm`**: AI model classification (confidence: varies based on model certainty)

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

## Model Orchestration & Decision Flow

This system uses a trust-first orchestration strategy for LLM-based classification.
It prioritizes self-agreement within a single model, escalates on instability, and never hides uncertainty.

```
OPENAI (PRIMARY MODEL)
────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

┌──────────────────────────────┐   ┌──────────────────────────────┐   ┌──────────────────────────────┐   ┌──────────────────────────────┐
│ O1: BOTH CALLS SUCCEED       │ → │ O2: BOTH CALLS SUCCEED       │ → │ O3: PARTIAL OPENAI SUCCESS   │ → │ O4: OPENAI TOTAL FAILURE     │
│ AND SELF-CONSISTENT          │   │ BUT DISAGREE                 │   │                              │   │                              │
│                              │   │                              │   │ • One call fails             │   │ • Both calls fail            │
│ • Same category              │   │ • Category mismatch OR       │   │ • One valid response         │   │                              │
│ • Stable confidence          │   │ • High confidence variance   │   │                              │   │ → No OpenAI candidate        │
│                              │   │                              │   │ → Add partial_openai flag    │   │ → Fallback to Gemini         │
│ → RETURN IMMEDIATELY         │   │ → Add risk flags             │   │ → DO NOT RETURN              │   │                              │
│ → Gemini NOT called          │   │ → Temp best guess            │   │ → Fallback to Gemini         │   │ WHY: Availability > silence  │
│ → reliability = HIGH         │   │ → Fallback to Gemini         │   │                              │   │ but never blind trust        │
│                              │   │                              │   │ WHY: Single response is      │   │                              │
│ WHY: Model agrees with       │   │ WHY: Instability detected    │   │ insufficient for trust       │   │                              │
│ itself under randomness      │   │ — trust cannot be assumed    │   │                              │   │                              │
└──────────────────────────────┘   └──────────────────────────────┘   └──────────────────────────────┘   └──────────────────────────────┘



GEMINI (FALLBACK VALIDATOR)
────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

┌──────────────────────────────┐   ┌──────────────────────────────┐   ┌──────────────────────────────┐   ┌──────────────────────────────┐
│ G1: BOTH CALLS SUCCEED       │ → │ G2: BOTH CALLS SUCCEED       │ → │ G3: PARTIAL GEMINI SUCCESS   │ → │ G4: GEMINI TOTAL FAILURE     │
│ AND SELF-CONSISTENT          │   │ BUT DISAGREE                 │   │                              │   │                              │
│                              │   │                              │   │ • One valid response         │   │ • All model calls fail       │
│ • Same category              │   │ • Category mismatch OR       │   │                              │   │                              │
│ • Stable confidence          │   │ • Confidence variance        │   │ → Pick available candidate   │   │ → RETURN None                │
│                              │   │                              │   │ → Add partial_gemini flag    │   │ → reliability = LOW          │
│ → Compute cross-model        │   │ → Resolve disagreement       │   │ → RETURN with low trust      │   │ → needs human review         │
│   agreement score            │   │ → Add strong risk flags      │   │                              │   │                              │
│ → RETURN RESULT              │   │ → RETURN best-effort result  │   │ WHY: Degraded operation is   │   │ WHY: System must admit it    │
│ → reliability = MEDIUM/LOW   │   │                              │   │ better than silent failure   │   │ cannot decide                │
│                              │   │ WHY: Even fallback model is  │   │                              │   │                              │
│ WHY: Gemini is stable, but   │   │ unstable → lowest trust      │   │                              │   │                              │
│ OpenAI instability lowers    │   │                              │   │                              │   │                              │
│ overall trust                │   │                              │   │                              │   │                              │
└──────────────────────────────┘   └──────────────────────────────┘   └──────────────────────────────┘   └──────────────────────────────┘

```
<br>
<br>

---

##  Counterfactual Reasoning

The `/counterfactual` endpoint answers:

> "If the description changed slightly, would the category change?"

This detects **fragile or unstable decisions**, which is critical in financial workflows.

Example:
- Base: "Dinner at restaurant" → "Meals & Entertainment"
- With modifier "client dinner": Still "Meals & Entertainment" (stable) or changes (fragile)

---

##  Human-in-the-Loop Learning

The `/correct` endpoint enables safe learning from human corrections:

### How It Works

1. **Human Reviews Transaction**: When a transaction is flagged as "Needs Review" or user wants to correct it
2. **Correction Submitted**: User submits corrected category via `/correct` endpoint
3. **Safe Learning**: 
   - Transaction is marked as overridden in the database
   - Merchant embedding is computed and stored with corrected category
   - Merchant memory is updated with human-verified label
4. **Future Classifications**: 
   - When the same merchant appears again, the system uses the human-verified category
   - Source shows as "human_verified" with high confidence (0.95)
   - System prioritizes human corrections over AI predictions

### Key Safety Features

-  Corrections are explicitly tracked (no silent overrides)
-  Embeddings are computed during correction for future similarity matching
-  Double-correction is prevented (transactions can only be corrected once)
-  Full audit trail in database
-  Human-verified merchants are prioritized over other classification paths

---

##  API Endpoints

### `POST /classify`
Main classification endpoint. Accepts expense description and returns classification with confidence, risk, and evidence.

**Request:**
```json
{
  "description": "LAX metro ride",
  "amount": 45.50,
  "date": "2024-01-15"
}
```

**Response:**
```json
{
  "transaction_id": 7,
  "decision": {
    "final_category": "Travel",
    "confidence": 0.8,
    "needs_review": false,
    "risk_level": "Medium",
    "source": "llm"
  },
  "trust": {
    "agreement_score": 1,
    "self_consistent": true,
    "cross_model_used": false,
    "risk_flags": [
      "low_embedding_similarity",
      "embedding_drift_detected"
    ]
  },
  "evidence": {
    "merchant_normalized": "lax metro",
    "evidence_list": [
      "Embedding similarity 0.58 to 'flyaway lax'",
      "Decision made via llm",
      "Embedding drift detected vs historical merchant patterns"
    ],
    "summary": ""
  },
  "risk": {
    "risk_score": 0.30000000000000004,
    "needs_review": false,
    "pii_redaction": false,
    "risk_flags": [
      "low_embedding_similarity",
      "embedding_drift_detected"
    ]
  }
}
```

**Evidence Trail**
```json
{
  "merchant_normalized": "lax metro",
  "evidence_list": [
    "Embedding similarity 0.58 to 'flyaway lax'",
    "Decision made via llm",
    "Embedding drift detected vs historical merchant patterns"
  ],
  "summary": ""
}
```

### `POST /correct`
Human correction endpoint. Updates transaction category and merchant memory.

**Request:**
```json
{
  "transaction_id": 123,
  "corrected_category": "Travel"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Category corrected from 'Needs Review' to 'Travel'"
}
```

### `POST /counterfactual`
What-if testing endpoint. Tests if adding a modifier changes the classification.

**Request:**
```json
{
  "description": "Dinner at restaurant",
  "modifier": "client dinner"
}
```

**Response:**
```json
{
  "original_category": "Meals & Entertainment",
  "new_category": "Meals & Entertainment",
  "changed": false,
  "trigger_words": ["client", "dinner"],
  "analysis_summary": "Modifier changed category: false"
}
```

Example:
- Base: "Dinner at restaurant" → "Meals & Entertainment"
- With modifier "client dinner": Still "Meals & Entertainment" (stable) or changes (fragile)

---

##  Testing Strategy

- **Unit tests** for:
  - Risk scoring (`test_risk.py`)
  - Evidence generation (`test_evidence.py`)
  - Guardrails (`test_guardrails.py`)
  - Rules engine (`test_rules.py`)
- **Integration tests** for:
  - `/classify` endpoint (`test_classify_api.py`)
  - End‑to‑end API behavior

Tests are written with clarity and comments — like production code.

Run tests with:
```bash
pytest
```

---

##  Running the Project

### Prerequisites

1. **Environment Setup**: Create `backend/.env` file with:
   ```
   OPENAI_API_KEY=your_openai_key_here
   GEMINI_API_KEY=your_gemini_key_here
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Virtual Environment (Recommended)

**Windows:**
```bash
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

The UI provides:
- **Single Entry**: Classify individual transactions
- **CSV Upload**: Batch processing of transactions
- **Counterfactual Testing**: What-if analysis interface
- **Human Correction Interface**: Review and correct classifications
- **Real-time Results**: View confidence, risk, evidence, and trust signals

The UI will open in your browser (typically `http://localhost:8501`)

### Tests
```bash
pytest
```

### Database

The system uses SQLite with two main tables:

- **`transaction`**: Audit log of all classifications
  - Stores raw/cleaned descriptions, predictions, confidence, risk scores
  - Tracks overrides and human corrections
  - Full audit trail for compliance

- **`merchantembedding`**: Merchant memory/learning database
  - Stores merchant names, embeddings, category labels
  - Tracks how many times each merchant was seen
  - Tracks human override counts
  - Enables fast similarity matching for future classifications

**Reset database:**
```bash
sqlite3 transactions.db
.tables
DELETE FROM merchantembedding;
DELETE FROM "transaction";
```

**View transactions:**
```sql
SELECT id, description_clean, predicted_category, confidence, source, overridden 
FROM "transaction" 
ORDER BY created_at DESC 
LIMIT 10;
```

**View merchant memory:**
```sql
SELECT merchant_name, category_label, num_seen, num_overrides 
FROM merchantembedding 
ORDER BY num_seen DESC;
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
