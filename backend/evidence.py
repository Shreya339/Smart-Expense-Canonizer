from typing import List


def build_evidence(rule_hit, rule_token, emb_match, emb_sim, override_count, source):
    """
    Build a human-readable explanation trail that documents
    WHY the system chose a category.

    Example output:
      [
        "Embedding similarity 0.97 to 'southwest airlines'",
        "Previously overridden 2 times",
        "Confirmed by openai"
      ]

    This supports:
      • auditability
      • trust & transparency
      • debugging model behavior
      • customer-facing explanations
      • regulator / compliance review in fintech
    """

    # We return an ordered list of explanation statements
    evidence: List[str] = []

    # ----------------------------------------------------
    # RULE MATCH
    # ----------------------------------------------------
    # If a deterministic rule triggered (ex: Uber → Travel)
    # include the matched keyword so the user understands why.
    if rule_hit and rule_token:
        evidence.append(f"Matched rule token '{rule_token}'")

    # ----------------------------------------------------
    # EMBEDDING MATCH
    # ----------------------------------------------------
    # If semantic merchant similarity lookup succeeded
    # we explain the similarity score.
    if emb_match and emb_sim is not None:
        evidence.append(f"Embedding similarity {emb_sim:.2f} to '{emb_match}'")

    # ----------------------------------------------------
    # HUMAN OVERRIDES
    # ----------------------------------------------------
    # If humans previously corrected this merchant category,
    # it signals uncertainty — so we show that transparently.
    if override_count and override_count > 0:
        evidence.append(f"Previously overridden {override_count} times")

    # ----------------------------------------------------
    # MODEL SOURCE
    # ----------------------------------------------------
    # State which layer produced the decision.
    # This improves explainability & supports audit trails.
    if source in ("openai", "gemini", "rules", "embedding"):
        evidence.append(f"Confirmed by {source}")

    # ----------------------------------------------------
    # FALLBACK CLARITY
    # ----------------------------------------------------
    # If something else classified it (future safety layers),
    # we still produce *some* explanation instead of silence.
    elif source:
        evidence.append(f"Decision made via {source}")

    # ----------------------------------------------------
    # ALWAYS RETURN A LIST
    # ----------------------------------------------------
    # Evidence is always safe & user-presentable
    return evidence
