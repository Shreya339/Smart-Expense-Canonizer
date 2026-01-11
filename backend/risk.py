def compute_risk(confidence, low_sim, unseen, overrides, flags):
    """
    Compute a numeric risk score (0.0 → 1.0) and
    generate explainability flags indicating WHY risk increased.

    Risk is used to decide:
      • whether we should trust the category
      • whether human review is recommended
      • how safe the AI decision is in a financial system

    Inputs:
      confidence  → model-reported confidence (0–1)
      low_sim     → embedding similarity below threshold?
      unseen      → merchant never seen before?
      overrides   → how many times humans corrected it?
      flags       → upstream system warnings (guardrails etc)

    Returns:
      (risk_score, risk_flags)
    """

    # --------------------------------------------------------
    # Start at zero → assume safe until proven risky
    # --------------------------------------------------------
    risk = 0.0

    # We ALSO return human-readable reason codes
    risk_flags = []


    # --------------------------------------------------------
    # MODEL CONFIDENCE TOO LOW
    # --------------------------------------------------------
    # If LLM / model returns confidence < 0.5 → do NOT trust
    # This is the biggest penalty — finance should not “guess”
    if confidence < 0.5:
        risk += 0.4
        risk_flags.append("low_confidence")


    # --------------------------------------------------------
    # EMBEDDING MATCH WAS WEAK
    # --------------------------------------------------------
    # Means: we *thought* we saw the merchant, but similarity
    # dropped below your threshold (ex: < 0.90)
    if low_sim:
        risk += 0.2
        risk_flags.append("low_embedding_similarity")


    # --------------------------------------------------------
    # NEW / UNSEEN MERCHANT
    # --------------------------------------------------------
    # First-time vendors historically increase risk of
    # misclassification — so we raise risk slightly.
    if unseen:
        risk += 0.2
        risk_flags.append("unseen_merchant")


    # --------------------------------------------------------
    # HUMANS REPEATEDLY OVERRULE SYSTEM
    # --------------------------------------------------------
    # Overrides tell you where AI historically struggles.
    # If >1 overrides → the model hasn’t learned pattern yet.
    if overrides and overrides > 1:
        risk += 0.2
        risk_flags.append("high_override_rate")


    # --------------------------------------------------------
    # ADD PENALTY FOR OTHER WARNINGS / SYSTEM FLAGS
    # --------------------------------------------------------
    # Examples include:
    #   • json_parse_error
    #   • invalid_confidence
    #   • ambiguous_rules_match
    #   • ungrounded_reasoning
    #
    # We do not duplicate flags already above — this list is
    # **informational only** from previous pipeline stages.
    # Each adds a small increment.
    # --------------------------------------------------------
    other_flag_penalty = 0.1 * len(flags)
    risk += other_flag_penalty

    # Merge upstream flags into risk output (uniquely)
    for f in flags:
        if f not in risk_flags:
            risk_flags.append(f)


    # --------------------------------------------------------
    # CAP FINAL RISK BETWEEN 0–1
    # --------------------------------------------------------
    if risk > 1.0:
        risk = 1.0
    if risk < 0.0:
        risk = 0.0


    # --------------------------------------------------------
    # Return BOTH:
    #   numeric score → for system logic
    #   textual flags → explainability
    # --------------------------------------------------------
    return risk, risk_flags
