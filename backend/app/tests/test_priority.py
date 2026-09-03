import pytest
from app.ai.priority import (
    PriorityEngine,
    PriorityCalculator,
    get_priority_engine,
    priority_calculator,
    DEFAULT_PRIORITY_WEIGHTS,
    PRIORITY_TIERS
)

def test_exact_user_formula_calculation():
    # User's exact prompt formula:
    # priority_score =
    #     urgency_score * 0.30
    #     + sentiment_score * 0.15
    #     + business_impact * 0.20
    #     + customer_impact * 0.15
    #     + sla_risk * 0.20
    #
    # Test case:
    # urgency_score = 100
    # sentiment_score = 100
    # business_impact = 100
    # customer_impact = 100
    # sla_risk = 100
    # Total = 100 * 1.0 = 100.0 -> CRITICAL
    res = priority_calculator.calculate(
        urgency_score=100.0,
        sentiment_score=100.0,
        business_impact=100.0,
        customer_impact=100.0,
        sla_risk=100.0
    )
    assert res["priority_score"] == 100.0
    assert res["priority"] == "CRITICAL"

def test_priority_tier_ranges():
    # 0-30: LOW
    # 31-60: MEDIUM
    # 61-80: HIGH
    # 81-100: CRITICAL

    # 1. LOW (e.g. all 20 -> 20.0)
    res_low = priority_calculator.calculate(
        urgency_score=20.0,
        sentiment_score=20.0,
        business_impact=20.0,
        customer_impact=20.0,
        sla_risk=20.0
    )
    assert res_low["priority_score"] == 20.0
    assert res_low["priority"] == "LOW"

    # 2. MEDIUM (e.g. all 50 -> 50.0)
    res_med = priority_calculator.calculate(
        urgency_score=50.0,
        sentiment_score=50.0,
        business_impact=50.0,
        customer_impact=50.0,
        sla_risk=50.0
    )
    assert res_med["priority_score"] == 50.0
    assert res_med["priority"] == "MEDIUM"

    # 3. HIGH (e.g. all 70 -> 70.0)
    res_high = priority_calculator.calculate(
        urgency_score=70.0,
        sentiment_score=70.0,
        business_impact=70.0,
        customer_impact=70.0,
        sla_risk=70.0
    )
    assert res_high["priority_score"] == 70.0
    assert res_high["priority"] == "HIGH"

    # 4. CRITICAL (e.g. all 90 -> 90.0)
    res_crit = priority_calculator.calculate(
        urgency_score=90.0,
        sentiment_score=90.0,
        business_impact=90.0,
        customer_impact=90.0,
        sla_risk=90.0
    )
    assert res_crit["priority_score"] == 90.0
    assert res_crit["priority"] == "CRITICAL"

def test_custom_configurable_weights():
    # User requirement: "Keep the scoring weights configurable."
    custom_weights = {
        "urgency": 0.50,
        "sentiment": 0.10,
        "business_impact": 0.10,
        "customer_impact": 0.10,
        "sla_risk": 0.20
    }
    engine = get_priority_engine(weights=custom_weights)

    # urgency_score = 100 * 0.50 = 50.0
    # others = 0
    res = engine.calculate(
        urgency_score=100.0,
        sentiment_score=0.0,
        business_impact=0.0,
        customer_impact=0.0,
        sla_risk=0.0
    )
    assert res["priority_score"] == 50.0
    assert res["priority"] == "MEDIUM"
    assert res["weights"]["urgency"] == 0.50

def test_deterministic_reproducibility():
    # User requirement: "Create a deterministic priority engine. Do not use the LLM as the sole priority decision-maker."
    scores = set()
    for _ in range(50):
        res = priority_calculator.calculate(
            urgency="HIGH",
            sentiment="NEGATIVE",
            category="Billing",
            entities=[{"entity_type": "AMOUNT", "entity_value": "$1200"}]
        )
        scores.add(res["priority_score"])

    # Guaranteed 100% deterministic (exact same single score across 50 executions)
    assert len(scores) == 1
