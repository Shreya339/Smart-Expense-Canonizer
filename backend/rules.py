
import re
from typing import Optional

RULE_MAP = {
    "uber": "Travel",
    "lyft": "Travel",
    "delta": "Travel",
    "united": "Travel",
    "american airlines": "Travel",
    "starbucks": "Meals & Entertainment",
    "mcdonald": "Meals & Entertainment",
    "ubereats": "Meals & Entertainment",
    "uber eats": "Meals & Entertainment",
    "dropbox": "Software / SaaS",
    "atlassian": "Software / SaaS",
    "slack": "Software / SaaS",
    "spotify": "Subscriptions",
    "netflix": "Subscriptions",
    "verizon": "Utilities",
    "t-mobile": "Utilities",
    "comcast": "Utilities"
}

CLEAN_RE = re.compile(r"[^a-zA-Z\s]")

# Normalize Text
def clean_text(text: str) -> str:
    t = text.lower()  # convert to lowercase
    t = CLEAN_RE.sub(" ", t)  # replace non-letters with spaces
    t = re.sub(r"\s+", " ", t).strip()  # collapse multiple spaces → 1 space
    return t

from typing import Optional

def rules_classify(text: str) -> Optional[str]:
    t = text.lower()

    # STEP 1 — sort rules by longest key first
    # This ensures "uber eats" wins before "uber"
    sorted_rules = sorted(
        RULE_MAP.items(),
        key=lambda x: len(x[0]),
        reverse=True
    )

    matched_categories = []
    matched_merchants = []

    # STEP 2 — collect ALL matches
    for merchant, category in sorted_rules:
        if merchant in t:
            matched_categories.append(category)
            matched_merchants.append(merchant)

    # No matches at all
    if not matched_categories:
        return None

    # STEP 3 — if more than one DISTINCT category is hit -> ambiguous
    if len(set(matched_categories)) > 1:
        return "AMBIGUOUS"

    # STEP 4 — otherwise return the SINGLE agreed category
    # (even if multiple merchant names map to same category)
    return matched_categories[0]



# NOTE: Ambiguity in merchant text is a data quality problem, not an AI understanding problem.
# we do NOT send to the LLM
# in finance:
# when the data itself is suspicious, we STOP, don’t infer
# AI should not overrule known ambiguity. LLM should NOT resolve conflict - humans should
