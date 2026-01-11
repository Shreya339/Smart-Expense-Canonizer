"""
Unit tests for LLM guardrails.

These tests ensure that model outputs are NEVER trusted blindly
and always validated before being used.
"""

from backend.guardrails import validate_json_candidate


def test_valid_json_passes():
    raw = '{ "category": "Travel", "confidence": 0.8 }'
    data, flags = validate_json_candidate(raw)
    assert data["category"] == "Travel"
    assert flags == []


def test_invalid_category_is_forced_to_needs_review():
    raw = '{ "category": "RandomStuff", "confidence": 0.9 }'
    data, flags = validate_json_candidate(raw)
    assert data["category"] == "Needs Review"
    assert "invalid_category" in flags


def test_invalid_confidence_is_sanitized():
    raw = '{ "category": "Meals & Entertainment", "confidence": "high" }'
    data, flags = validate_json_candidate(raw)
    assert data["confidence"] == 0.0
    assert "invalid_confidence" in flags
