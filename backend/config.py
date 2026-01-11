
import os
from dotenv import load_dotenv
from pathlib import Path

# LOAD .env FILE
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ---------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------

# SQLite DB connection string — default file name is transactions.db
DB_URL = os.getenv("DB_URL", "sqlite:///./transactions.db")

# ---------------------------------------------------
# MODEL + PIPELINE TUNING PARAMETERS
# ---------------------------------------------------

# Minimum acceptable model confidence before we mark as risky - helps avoid bad auto-classification
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.65"))

# Embedding similarity must be >= THIS to auto-accept. Below that — AI or review handles it.
EMBEDDING_SIMILARITY_THRESHOLD = float(os.getenv("EMBEDDING_SIMILARITY_THRESHOLD", "0.90"))

# Number of user overrides required before we “trust” a correction
OVERRIDE_TRUST_THRESHOLD = int(os.getenv("OVERRIDE_TRUST_THRESHOLD", "2"))


# ---------------------------------------------------
# ALLOWED OUTPUT CATEGORIES — SAFETY WHITELIST
# ---------------------------------------------------

#strict whitelist of allowed accounting categories to prevent model hallucinations — which is essential in financial products where classification integrity matters.
CATEGORY_WHITELIST = [
    "Travel",
    "Meals & Entertainment",
    "Software / SaaS",
    "Office Supplies",
    "Utilities",
    "Subscriptions",
    "Income",
    "Rent",
    "Contractors",
    "Advertising & Marketing",
    "Other Expenses",
    "Needs Review"
]


# ==== Safety Feature Flags ====
FEATURE_SELF_CONSISTENCY = True
FEATURE_CROSS_MODEL_SCORING = True
FEATURE_REASON_VALIDATION = True
FEATURE_PII_SAFE_AUDIT_LOGGING = True

AUDIT_LOG_PATH = "backend/audit/decision_log.jsonl"
PII_SALT = os.getenv("PII_SALT", "dev_salt")

AGREEMENT_BASE_WEIGHT = 0.5
SELF_CONSIST_WEIGHT = 0.3
EMBED_AGREEMENT_WEIGHT = 0.2

