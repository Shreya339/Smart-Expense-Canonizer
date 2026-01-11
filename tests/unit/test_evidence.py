"""
Unit tests for explainability evidence builder.

These tests ensure that human-readable explanations
are deterministic and auditable.
"""

from backend.evidence import build_evidence


def test_embedding_evidence_is_rendered():
    evidence = build_evidence(
        rule_hit=False,
        rule_token=None,
        emb_match="delta airlines",
        emb_sim=0.95,
        override_count=0,
        source="embedding"
    )

    assert any("Embedding similarity" in e for e in evidence)
    assert any("Confirmed by embedding" in e for e in evidence)
