import json
from .config import CATEGORY_WHITELIST


# ------------------------------------------------------------
# Normalizes the raw model output so it becomes plain JSON text
# ------------------------------------------------------------
def normalize_json_text(text: str) -> str:
    # Trim whitespace first
    text = (text or "").strip()

    # Sometimes LLMs wrap JSON in Markdown code fences like:
    # ```json
    # { ... }
    # ```
    # This removes those backticks if present
    if text.startswith("```"):
        # remove backticks everywhere
        text = text.replace("```", "").strip()

        # If the text begins with the label "json"
        # e.g. json{...}
        # remove the word "json"
        if text.lower().startswith("json"):
            text = text[4:].strip()

    # Return the cleaned result
    return text.strip()



# ------------------------------------------------------------
# Validate + sanitize the JSON returned by the LLM
# Returns:
#   (validated_json_dict, list_of_risk_flags)
# or:
#   (None, ["json_parse_error"])
# ------------------------------------------------------------
def validate_json_candidate(raw: str):

    if not raw:
        return None, ["empty_response"]

    try:
        # First normalize any markdown wrappers, etc.
        clean = normalize_json_text(raw)

        # Try to parse the JSON
        data = json.loads(clean)

    except Exception:
        # If JSON parsing fails → reject & flag it
        return None, ["json_parse_error"]

    # We'll collect warnings / risk signals here
    flags = []

    # Ensure we always return a dict
    if not isinstance(data, dict):
        return None, ["invalid_json_structure"]

    # ------------------------------------------------------------
    # ENSURE ALL EXPECTED FIELDS EXIST
    # ------------------------------------------------------------
    cat = data.get("category")
    conf = data.get("confidence", 0.0)
    expl = data.get("explanation", "")

    # Backwards-compat keys we allow LLMs to return
    normalized = data.get("normalized_merchant", "")

    # ------------------------------------------------------------
    # CATEGORY CHECK
    # ------------------------------------------------------------
    # If category is NOT in the allowed list…
    if cat not in CATEGORY_WHITELIST:
        flags.append("invalid_category")

        # Force a safe fallback category
        data["category"] = "Needs Review"

    # ------------------------------------------------------------
    # CONFIDENCE CHECK
    # ------------------------------------------------------------
    try:
        # Ensure confidence is numeric
        conf = float(conf)
    except Exception:
        flags.append("invalid_confidence")
        conf = 0.0

    # Force into range 0–1
    if conf < 0:
        flags.append("negative_confidence")
        conf = 0.0
    elif conf > 1:
        flags.append("confidence_out_of_range")
        conf = 1.0

    data["confidence"] = conf

    # ------------------------------------------------------------
    # EXPLANATION CHECK
    # ------------------------------------------------------------
    if not isinstance(expl, str):
        flags.append("invalid_explanation")
        expl = ""

    data["explanation"] = expl

    # ------------------------------------------------------------
    # NORMALIZED MERCHANT CHECK
    # ------------------------------------------------------------
    if not isinstance(normalized, str):
        flags.append("invalid_normalized_merchant")
        data["normalized_merchant"] = ""
    else:
        data["normalized_merchant"] = normalized

    # ------------------------------------------------------------
    # DETECT SUSPICIOUS / EMPTY OUTPUTS
    # ------------------------------------------------------------
    if not data["category"]:
        flags.append("missing_category")

    if data["confidence"] == 0:
        flags.append("low_confidence")

    # ------------------------------------------------------------
    # Return sanitized JSON + any flags we generated
    # ------------------------------------------------------------
    return data, flags
