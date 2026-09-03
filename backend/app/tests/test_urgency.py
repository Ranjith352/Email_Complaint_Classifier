import pytest
from app.ai.urgency import (
    BaseUrgencyDetector,
    RuleEnhancedUrgencyDetector,
    UrgencyDetector,
    get_urgency_detector,
    urgency_detector,
    URGENCY_TIERS
)

def test_user_exact_critical_example():
    # User exact example 1:
    # "My account has been hacked." -> CRITICAL
    text = "My account has been hacked."
    res = urgency_detector.detect(text)

    assert res["urgency"] == "CRITICAL"
    assert res["confidence"] >= 0.90
    assert any("Account compromise" in rule or "hacked" in rule for rule in res["applied_rules"])

def test_user_exact_low_example():
    # User exact example 2:
    # "I need information about your subscription." -> LOW
    text = "I need information about your subscription."
    res = urgency_detector.detect(text)

    assert res["urgency"] == "LOW"
    assert res["confidence"] >= 0.85
    assert any("General information" in rule for rule in res["applied_rules"])

def test_urgency_tiers_complete():
    assert set(URGENCY_TIERS) == {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

def test_critical_legal_and_outage_rules():
    # Legal rule
    legal_text = "I am speaking with my attorney and will file a lawsuit in court for damages."
    legal_res = urgency_detector.detect(legal_text)
    assert legal_res["urgency"] == "CRITICAL"

    # Outage rule
    outage_text = "Total system outage right now! Production server down for everyone!"
    outage_res = urgency_detector.detect(outage_text)
    assert outage_res["urgency"] == "CRITICAL"

def test_high_financial_and_asap_rules():
    # Double charge
    fin_text = "I was charged twice on order ORD-9912, please refund immediately."
    fin_res = urgency_detector.detect(fin_text)
    assert fin_res["urgency"] == "HIGH"

    # Explicit urgent adverb
    urgent_text = "I need this resolved ASAP right now, critical deadline today."
    urgent_res = urgency_detector.detect(urgent_text)
    assert urgent_res["urgency"] == "HIGH"

def test_medium_operational_baseline():
    text = "I noticed a minor delay in loading my transaction history, please check into this."
    res = urgency_detector.detect(text)
    assert res["urgency"] == "MEDIUM"

def test_urgency_detector_abstraction():
    detector = get_urgency_detector()
    assert isinstance(detector, BaseUrgencyDetector)
    assert isinstance(detector, RuleEnhancedUrgencyDetector)
    assert "BusinessRules" in detector.detect("My account was hacked")["model"]
