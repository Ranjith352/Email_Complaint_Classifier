import pytest
from app.ai.sentiment import (
    BaseSentimentAnalyzer,
    TransformerSentimentAnalyzer,
    SentimentAnalyzer,
    get_sentiment_analyzer,
    sentiment_analyzer
)

def test_user_exact_example_sentiment():
    # User's exact prompt specification:
    # Return:
    # label
    # confidence
    # Example:
    # {
    #     "label": "NEGATIVE",
    #     "confidence": 0.94
    # }
    text = "I was charged twice for my subscription and the payment failed. Unacceptable horrible service!"
    res = sentiment_analyzer.analyze(text)

    assert "label" in res
    assert "confidence" in res
    assert res["label"] == "NEGATIVE"
    assert isinstance(res["confidence"], float)
    assert res["confidence"] >= 0.85

def test_positive_sentiment():
    text = "Thank you so much! My refund was processed quickly, fantastic and helpful support team."
    res = sentiment_analyzer.analyze(text)

    assert res["label"] == "POSITIVE"
    assert res["confidence"] >= 0.80

def test_neutral_sentiment():
    text = "Account statement for the month of February 2026."
    res = sentiment_analyzer.analyze(text)

    assert res["label"] == "NEUTRAL"
    assert 0.0 <= res["confidence"] <= 1.0

def test_sentiment_abstraction_and_factory():
    analyzer = get_sentiment_analyzer()
    assert isinstance(analyzer, BaseSentimentAnalyzer)
    assert isinstance(analyzer, TransformerSentimentAnalyzer)
    assert "distilbert" in analyzer.model_name

    custom = get_sentiment_analyzer(model_name="cardiffnlp/twitter-roberta-base-sentiment-latest")
    assert custom.model_name == "cardiffnlp/twitter-roberta-base-sentiment-latest"
    res = custom.analyze("This broken app crashed again, angry and frustrated.")
    assert res["label"] == "NEGATIVE"
