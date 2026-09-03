import pytest
from app.ai.classifier import (
    BaseClassifier,
    TFIDFLogisticRegressionClassifier,
    TFIDFNaiveBayesClassifier,
    DistilBERTClassifier,
    AdvancedTransformerClassifier,
    ZeroShotClassifier,
    ProgressiveClassifier,
    ModelGovernance,
    get_classifier
)

def test_baseline_tfidf_logistic_regression():
    baseline = TFIDFLogisticRegressionClassifier()
    assert isinstance(baseline, BaseClassifier)
    assert baseline.model_tier == "Baseline"

    res = baseline.classify("I was charged twice for my subscription.")
    assert res["category"] == "Billing"
    assert res["sub_category"] == "Duplicate Payment"
    assert res["department"] == "Finance"
    assert res["confidence"] >= 0.85

def test_alternative_tfidf_naive_bayes():
    nb = TFIDFNaiveBayesClassifier()
    assert isinstance(nb, BaseClassifier)
    assert nb.model_tier == "Alternative"

    res = nb.classify("Double charged on credit card invoice")
    assert res["category"] == "Billing"
    assert res["department"] == "Finance"
    assert res["confidence"] >= 0.80

def test_transformer_distilbert():
    distil = DistilBERTClassifier()
    assert isinstance(distil, BaseClassifier)
    assert "DistilBERT" in distil.model_tier

    res = distil.classify("Our production server is completely down with 500 error outage")
    assert res["category"] == "Technical Problem"
    assert res["department"] == "IT"
    assert res["confidence"] >= 0.80

def test_advanced_transformer_roberta():
    roberta = AdvancedTransformerClassifier()
    assert isinstance(roberta, BaseClassifier)
    assert "Advanced Transformer" in roberta.model_tier

    res = roberta.classify("My account was hacked and unauthorized login was detected")
    assert res["category"] == "Security Issue"
    assert res["department"] == "Security"
    assert res["confidence"] >= 0.80

def test_zero_shot_bart_mnli():
    bart = ZeroShotClassifier(model_name="facebook/bart-large-mnli")
    assert isinstance(bart, BaseClassifier)
    assert "Zero-Shot" in bart.model_tier

    res = bart.classify("Where is my order package delivery is delayed")
    assert res["category"] == "Customer Support"
    assert res["department"] == "Customer Support"
    assert res["confidence"] >= 0.80

def test_model_governance_rules():
    # Rule 1: Cold start / no labeled data -> Zero-shot BART MNLI (Do not fine-tune without data)
    assert ModelGovernance.select_appropriate_model(labeled_samples=0) == "zero-shot"

    # Rule 2: Low-data regime (<500 samples) -> Simplest model that performs well (Baseline TF-IDF + LR)
    assert ModelGovernance.select_appropriate_model(labeled_samples=150) == "baseline"

    # Rule 3: Moderate labeled data (500 - 5000 samples) -> DistilBERT
    assert ModelGovernance.select_appropriate_model(labeled_samples=1200) == "distilbert"

    # Rule 4: Large scale labeled data (>5000 samples) -> RoBERTa / BERT
    assert ModelGovernance.select_appropriate_model(labeled_samples=8000) == "advanced"

def test_progressive_classifier_factory():
    clf_baseline = get_classifier("baseline")
    assert isinstance(clf_baseline, TFIDFLogisticRegressionClassifier)

    clf_nb = get_classifier("alternative")
    assert isinstance(clf_nb, TFIDFNaiveBayesClassifier)

    clf_distil = get_classifier("distilbert")
    assert isinstance(clf_distil, DistilBERTClassifier)

    clf_adv = get_classifier("roberta")
    assert isinstance(clf_adv, AdvancedTransformerClassifier)

    clf_zero = get_classifier("bart-mnli")
    assert isinstance(clf_zero, ZeroShotClassifier)

    prog = get_classifier("progressive")
    assert isinstance(prog, ProgressiveClassifier)
    res = prog.classify("I was charged twice for my subscription.")
    assert res["category"] == "Billing"
    assert res["department"] == "Finance"
