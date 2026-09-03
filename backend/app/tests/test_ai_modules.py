import pytest
from app.ai.embeddings import embeddings_engine
from app.ai.classifier import classifier
from app.ai.sentiment import sentiment_analyzer
from app.ai.emotion import emotion_detector
from app.ai.ner import ner_extractor
from app.ai.urgency import urgency_detector
from app.ai.priority import priority_calculator
from app.ai.summarizer import summarizer
from app.ai.response_generator import response_generator

def test_embeddings_dimension_and_cosine():
    text1 = "Payment double charged on credit card"
    text2 = "Payment double charged on card again"
    text3 = "University campus semester exam grade"

    v1 = embeddings_engine.get_embedding(text1)
    v2 = embeddings_engine.get_embedding(text2)
    v3 = embeddings_engine.get_embedding(text3)

    assert len(v1) == 384
    sim_similar = embeddings_engine.cosine_similarity(v1, v2)
    sim_unrelated = embeddings_engine.cosine_similarity(v1, v3)
    assert sim_similar > sim_unrelated

def test_classifier_taxonomy():
    res = classifier.classify("I was double charged on my bank invoice and need a refund")
    assert res["category"] in ("Billing", "Billing / Payment")
    assert res["department"] == "Finance"
    assert res["team"] in ("Payments & Refunds", "Billing & Invoicing", "Duplicate Payment", "Refund Request")
    assert 0.0 < res["confidence"] <= 1.0

def test_sentiment_and_emotion():
    text = "I am furious and angry! This pathetic service is completely broken and failed repeatedly."
    sent = sentiment_analyzer.analyze(text)
    assert sent["sentiment"].upper() == "NEGATIVE"
    assert sent["sentiment_score"] < 0

    emo = emotion_detector.detect(text)
    assert emo["emotion"].upper() in ("ANGER", "FRUSTRATION")

def test_ner_extraction():
    text = "Please check invoice INV-99201 for order #ORD-44919 with amount $450.00 charged on my card."
    entities = ner_extractor.extract_entities(text)
    types = {e["entity_type"] for e in entities}
    assert "TRANSACTION_ID" in types or "ORDER_ID" in types or "AMOUNT" in types

def test_urgency_and_priority():
    urg = urgency_detector.detect("System outage right now! Critical production crash!", category="Technical Problem")
    assert urg["urgency"] == "Critical"

    prio = priority_calculator.calculate(
        urgency="Critical",
        sentiment="Negative",
        entities=[{"entity_type": "AMOUNT", "entity_value": "$500"}],
        category="Technical Problem"
    )
    assert prio["priority_level"] == "P1"
    assert prio["priority_score"] >= 80.0

@pytest.mark.asyncio
async def test_summarizer_and_response_generator():
    summary_res = await summarizer.summarize("Login issue", "I cannot access my portal and keep getting timeout error.")
    assert "summary" in summary_res
    assert len(summary_res["key_points"]) > 0

    draft_res = await response_generator.generate_draft(
        ticket_number="CMP-10001",
        customer_name="Alice",
        subject="Login issue",
        body="Cannot login",
        department="IT"
    )
    assert draft_res["requires_approval"] is True
    assert "CMP-10001" in draft_res["subject"] or "CMP-10001" in draft_res["body"]

def test_modular_llm_providers():
    from app.ai.llm_provider import get_llm_provider, LLMProvider
    from app.ai.ollama_provider import OllamaProvider
    from app.ai.groq_provider import GroqProvider

    provider = get_llm_provider()
    assert isinstance(provider, LLMProvider)
    assert provider.provider_name != ""

    ollama = OllamaProvider()
    assert "ollama" in ollama.provider_name

    groq = GroqProvider()
    assert "groq" in groq.provider_name

@pytest.mark.asyncio
async def test_ai_orchestrator_structured_object(db):
    from app.ai.ai_orchestrator import ai_orchestrator

    analysis = await ai_orchestrator.process_complaint_full(
        subject="Double charged on invoice INV-9910",
        body="I was charged twice $149.00 on my credit card. Immediate refund needed!",
        customer_name="Sarah Connor",
        ticket_number="CMP-99001",
        db=db
    )

    # Verify structured analysis contract
    assert "category" in analysis
    assert "sub_category" in analysis
    assert "department" in analysis
    assert "team" in analysis
    assert "sentiment" in analysis
    assert "emotion" in analysis
    assert "urgency" in analysis
    assert "priority" in analysis
    assert "priority_score" in analysis
    assert "confidence" in analysis
    assert "review_required" in analysis
    assert "language" in analysis

    assert analysis["department"] == "Finance"
    assert analysis["sentiment"] in ("NEGATIVE", "NEUTRAL", "POSITIVE")
    assert isinstance(analysis["priority_score"], int)
    assert 0.0 <= analysis["confidence"] <= 1.0
    assert isinstance(analysis["review_required"], bool)
    assert analysis["language"] == "en"


