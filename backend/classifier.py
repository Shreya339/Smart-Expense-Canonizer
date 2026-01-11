# ---------- Imports ----------
from .rules import clean_text, rules_classify
from .llm_service import classify_with_models
from .config import CONFIDENCE_THRESHOLD, EMBEDDING_SIMILARITY_THRESHOLD
from .embeddings import compute_and_track_embedding, find_similar, upsert_merchant
from .evidence import build_evidence
from .risk import compute_risk
from .pii import redact


# =====================================================
# MAIN PIPELINE (DRIFT + HUMAN-IN-THE-LOOP AWARE)
# =====================================================
def classify_pipeline(description: str):

    # -------------------------------------------------
    # STEP 1 — REDACT PII
    # -------------------------------------------------
    red_desc, had_pii, pii_flags = redact(description)

    # -------------------------------------------------
    # STEP 2 — NORMALIZE TEXT
    # -------------------------------------------------
    clean = clean_text(red_desc)

    # -------------------------------------------------
    # STEP 3 — EMBED + TRACK DRIFT
    # -------------------------------------------------
    emb, drift_flag = compute_and_track_embedding(clean)

    emb_match_name = None
    emb_sim = None
    override_count = 0
    unseen = True

    # -------------------------------------------------
    # STEP 4 — SEARCH MERCHANT MEMORY
    # -------------------------------------------------
    if emb:
        match, sim = find_similar(emb)

        if match:
            unseen = False
            emb_match_name = match.merchant_name
            emb_sim = sim
            override_count = match.num_overrides

            # =====================================================
            # 🔒 HUMAN-VERIFIED MERCHANT (HIGHEST PRIORITY)
            # =====================================================
            if (
                match.num_overrides > 0
                and match.category_label
                and sim >= EMBEDDING_SIMILARITY_THRESHOLD
            ):

                result = {
                    "category": match.category_label,
                    "confidence": 0.95,
                    "explanation": "Human-verified merchant override.",
                    "normalized_merchant": clean,
                    "source": "human_verified",
                    "needs_review": False,
                }

                evidence = [
                    f"Human corrected merchant '{match.merchant_name}'",
                    f"Embedding similarity {sim:.2f}",
                    "Locked by human override",
                ]

                risk, risk_flags = compute_risk(
                    confidence=0.95,
                    low_sim=False,
                    unseen=False,
                    overrides=match.num_overrides,
                    flags=[]
                )

                return result, evidence, risk, risk_flags, had_pii

            # -------------------------------------------------
            # HIGH-CONFIDENCE EMBEDDING AUTO-CLASSIFY
            # -------------------------------------------------
            if sim >= EMBEDDING_SIMILARITY_THRESHOLD and match.category_label:

                result = {
                    "category": match.category_label,
                    "confidence": 0.9,
                    "explanation": "Embedding merchant match.",
                    "normalized_merchant": clean,
                    "source": "embedding",
                }

                evidence = build_evidence(
                    False,
                    None,
                    emb_match_name,
                    emb_sim,
                    override_count,
                    "embedding",
                )

                extra_flags = []
                if drift_flag:
                    extra_flags.append("embedding_drift_detected")
                    evidence.append(
                        "Embedding drift detected vs historical merchant patterns"
                    )

                risk, risk_flags = compute_risk(
                    result["confidence"],
                    low_sim=False,
                    unseen=unseen,
                    overrides=override_count,
                    flags=extra_flags + pii_flags,
                )

                return result, evidence, risk, risk_flags, had_pii

    # -------------------------------------------------
    # STEP 5 — RULE ENGINE
    # -------------------------------------------------
    rc = rules_classify(clean)

    if rc == "AMBIGUOUS":
        result = {
            "category": "Needs Review",
            "confidence": 0.0,
            "explanation": "Multiple conflicting merchant matches detected",
            "normalized_merchant": clean,
            "source": "rules",
            "needs_review": True,
        }

        evidence = [
            "Rules engine detected multiple merchant matches mapping to different categories"
        ]

        risk, risk_flags = compute_risk(
            result["confidence"],
            low_sim=False,
            unseen=unseen,
            overrides=override_count,
            flags=["ambiguous_rules_match"] + pii_flags,
        )

        return result, evidence, risk, risk_flags, had_pii

    elif rc:
        result = {
            "category": rc,
            "confidence": 0.95,
            "explanation": "Rule-based classification",
            "normalized_merchant": clean,
            "source": "rules",
            "needs_review": False,
        }

        evidence = build_evidence(
            True,
            None,
            emb_match_name,
            emb_sim,
            override_count,
            "rules",
        )

        risk, risk_flags = compute_risk(
            result["confidence"],
            low_sim=False,
            unseen=unseen,
            overrides=override_count,
            flags=pii_flags,
        )

        return result, evidence, risk, risk_flags, had_pii

    # -------------------------------------------------
    # STEP 6 — LLM FALLBACK (LAST RESORT)
    # -------------------------------------------------
    res, meta = classify_with_models(description)

    if not res:
        return {
            "category": "Needs Review",
            "confidence": 0.0,
            "explanation": "All model calls failed",
            "normalized_merchant": clean,
            "source": "llm",
            "needs_review": True,
        }, [], 1.0, ["model_failure"], had_pii

    needs_review = (
        float(res.get("confidence", 0)) < CONFIDENCE_THRESHOLD
        or res.get("category") == "Needs Review"
    )

    result = {
        "category": res.get("category", "Needs Review"),
        "confidence": float(res.get("confidence", 0)),
        "explanation": res.get("explanation", ""),
        "normalized_merchant": clean,
        "source": "llm",
        "needs_review": needs_review,
        "agreement_score": meta.get("agreement_score"),
        "self_consistent": meta.get("self_consistent"),
        "cross_model_used": meta.get("cross_model_used"),
    }

    # -------------------------------------------------
    # STEP 7 — BUILD EVIDENCE + RISK
    # -------------------------------------------------
    low_sim = emb_sim is not None and emb_sim < EMBEDDING_SIMILARITY_THRESHOLD

    evidence = build_evidence(
        False,
        None,
        emb_match_name,
        emb_sim,
        override_count,
        "llm",
    )

    extra_flags = meta.get("risk_flags", []) + pii_flags

    if drift_flag:
        extra_flags.append("embedding_drift_detected")
        evidence.append(
            "Embedding drift detected vs historical merchant patterns"
        )

    risk, risk_flags = compute_risk(
        result["confidence"],
        low_sim=low_sim,
        unseen=unseen,
        overrides=override_count,
        flags=extra_flags,
    )

    # -------------------------------------------------
    # STEP 8 — UPDATE MEMORY (AI LEARNING ONLY IF NO OVERRIDE)
    # -------------------------------------------------
    upsert_merchant(clean, emb, result["category"])

    return result, evidence, risk, risk_flags, had_pii





"""
My classifier is intentionally layered for safety, cost-efficiency, and explainability.

First, I redact any PII because we’re dealing with financial data.

Then I normalize the merchant description and try a semantic embedding lookup so previously-seen merchants are classified consistently. If the similarity is above 0.90, I accept that with high confidence.

If there’s no strong match, I fall back to deterministic business rules — for example, Uber always maps to Travel.

Only when both fail do I call an LLM, with JSON guardrails and Gemini as fallback. If the model confidence drops below a threshold, I mark the transaction as Needs Review rather than guessing.

Every decision also produces human-readable evidence and a risk score so the system is auditable — which is critical in fintech.

Why not do rules first?

Because embeddings allow:

✔ spelling variations
✔ abbreviations
✔ merchant growth over time
✔ proper flow if low similarity

But rules still serve as:

✔ deterministic audit proof
✔ high confidence autopost
✔ cost saving
✔ fast fallback


"""