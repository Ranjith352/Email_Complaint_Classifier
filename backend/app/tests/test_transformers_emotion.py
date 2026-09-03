import pytest
from app.ai.emotion import (
    BaseEmotionDetector,
    TransformerEmotionDetector,
    EmotionDetector,
    get_emotion_detector,
    emotion_detector,
    TARGET_EMOTIONS
)

def test_target_emotions_set():
    assert set(TARGET_EMOTIONS) == {
        "ANGER",
        "FRUSTRATION",
        "FEAR",
        "SADNESS",
        "NEUTRAL",
        "SATISFACTION"
    }

def test_anger_detection():
    text = "I will sue your company! This is an outrageous scam and fraudulent stealing of my money!"
    res = emotion_detector.detect(text)

    assert res["emotion"] == "ANGER"
    assert res["confidence"] >= 0.80
    assert "ANGER" in res["emotion_scores"]

def test_frustration_detection():
    text = "I was charged twice again and have been waiting forever. Tired of this useless runaround!"
    res = emotion_detector.detect(text)

    assert res["emotion"] == "FRUSTRATION"
    assert res["confidence"] >= 0.80

def test_fear_detection():
    text = "My account was hacked in a security breach, I am terrified my personal identity is compromised and stolen."
    res = emotion_detector.detect(text)

    assert res["emotion"] == "FEAR"
    assert res["confidence"] >= 0.80

def test_sadness_detection():
    text = "I am deeply disappointed and let down by this broken product. It completely ruined our anniversary."
    res = emotion_detector.detect(text)

    assert res["emotion"] == "SADNESS"
    assert res["confidence"] >= 0.80

def test_satisfaction_detection():
    text = "Thank you so much! The agent was wonderfully helpful and resolved everything with great care."
    res = emotion_detector.detect(text)

    assert res["emotion"] == "SATISFACTION"
    assert res["confidence"] >= 0.80

def test_neutral_detection():
    text = "Attached is the requested PDF bank statement regarding transaction #84920."
    res = emotion_detector.detect(text)

    assert res["emotion"] == "NEUTRAL"
    assert 0.0 <= res["confidence"] <= 1.0

def test_configurable_model():
    detector = get_emotion_detector()
    assert isinstance(detector, BaseEmotionDetector)
    assert isinstance(detector, TransformerEmotionDetector)
    assert "distilroberta" in detector.model_name

    # Test dynamic reconfiguration
    detector.set_model("facebook/bart-large-mnli")
    assert detector.model_name == "facebook/bart-large-mnli"

    res = detector.detect("I am furious about this billing mistake!")
    assert res["emotion"] in TARGET_EMOTIONS
