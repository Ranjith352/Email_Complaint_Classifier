import pytest
from app.ai.classifier import (
    BaseClassifier,
    ZeroShotClassifier,
    TransformerClassifier,
    ComplaintClassifier,
    get_classifier,
    classifier
)

def test_user_exact_example_classification():
    # User's exact prompt specification:
    # Input: "I was charged twice for my subscription."
    # Output:
    # Category: Billing
    # Subcategory: Duplicate Payment
    # Department: Finance
    # Confidence: 0.94
    user_input = "I was charged twice for my subscription."
    zero_shot = ZeroShotClassifier(model_name="facebook/bart-large-mnli")
    res = zero_shot.classify(user_input)

    assert res["category"] == "Billing"
    assert res["sub_category"] == "Duplicate Payment"
    assert res["department"] == "Finance"
    assert res["confidence"] >= 0.90

def test_classifier_abstraction():
    # Verify BaseClassifier hierarchy
    zero_shot = get_classifier("zero-shot")
    assert isinstance(zero_shot, BaseClassifier)
    assert zero_shot.model_name == "facebook/bart-large-mnli"

    transformer = get_classifier("transformer")
    assert isinstance(transformer, BaseClassifier)
    assert "distilbert" in transformer.model_name

def test_technical_problem_classification():
    input_text = "Our production server is completely down with 500 internal server error and system outage."
    res = classifier.classify(input_text)

    assert res["category"] == "Technical Problem"
    assert res["department"] == "IT"
    assert res["sub_category"] in ("System Outage", "Software Bug")
    assert res["confidence"] >= 0.80

def test_security_issue_classification():
    input_text = "My account was hacked and unauthorized access was detected with stolen credentials."
    res = classifier.classify(input_text)

    assert res["category"] == "Security Issue"
    assert res["department"] == "Security"
    assert res["sub_category"] in ("Account Compromise", "Unauthorized Access")
    assert res["confidence"] >= 0.80

def test_customer_support_classification():
    input_text = "Where is my package? The delivery is delayed and tracking number is not updating."
    res = classifier.classify(input_text)

    assert res["category"] == "Customer Support"
    assert res["department"] == "Customer Support"
    assert res["sub_category"] == "Order Tracking & Shipping"
    assert res["confidence"] >= 0.80
