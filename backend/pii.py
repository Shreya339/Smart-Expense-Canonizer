
import re
from typing import Tuple

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+")
PHONE_RE = re.compile(r"(\+?\d[\d\s\-]{7,}\d)")
CARD_RE = re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b")

def redact(text: str) -> Tuple[str, bool, list]:
    """
    Detect and safely remove PII (emails, phones, cards)
    BEFORE text is sent to any AI model.

    Returns:
        redacted_text  → sanitized input
        had            → boolean flag if any PII was found
        flags          → list like ["email","phone"]
    """
    had = False
    flags = []
    def go(pat, repl, label, t):
        nonlocal had, flags
        if pat.search(t):
            had = True
            flags.append(label)
        return pat.sub(repl, t)

    red = text
    red = go(EMAIL_RE, "[REDACTED_EMAIL]", "email", red)
    red = go(PHONE_RE, "[REDACTED_PHONE]", "phone", red)
    red = go(CARD_RE, "[REDACTED_CARD]", "card", red)

    return red, had, flags
