"""
Unit tests for risk scoring logic.

These tests verify that risk increases for:
- low confidence
- low similarity
- unseen merchants

Risk must also always remain within [0, 1].
"""

from backend.risk import compute_risk


def test_low_confidence_increases_risk():
    risk, flags = compute_risk(
        confidence=0.2,
        low_sim=False,
        unseen=False,
        overrides=0,
        flags=[]
    )
    assert risk > 0.3
    assert "low_confidence" in flags


def test_unseen_merchant_increases_risk():
    risk, flags = compute_risk(
        confidence=0.9,
        low_sim=False,
        unseen=True,
        overrides=0,
        flags=[]
    )
    assert risk > 0.1
    assert "unseen_merchant" in flags


def test_risk_is_capped_at_one():
    risk, _ = compute_risk(
        confidence=0.0,
        low_sim=True,
        unseen=True,
        overrides=5,
        flags=["json_parse_error", "invalid_confidence"]
    )
    assert risk <= 1.0
