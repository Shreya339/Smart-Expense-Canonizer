"""
Unit tests for deterministic rules engine.

Rules provide predictable, auditable behavior
before any AI model is invoked.
"""

from backend.rules import rules_classify


def test_uber_maps_to_travel():
    assert rules_classify("uber ride downtown") == "Travel"


def test_starbucks_maps_to_meals():
    assert rules_classify("starbucks latte") == "Meals & Entertainment"
