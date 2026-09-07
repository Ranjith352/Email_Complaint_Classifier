import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.complaint import Complaint
from app.models.intelligence import AIResponse
from app.ai.llm_provider import LLMProvider, get_llm_provider
from app.ai.ollama_provider import OllamaProvider
from app.ai.groq_provider import GroqProvider
from app.ai.summarizer import summarizer
from app.services.complaint_service import complaint_service

def test_llm_provider_abstraction():
    """Verifies LLMProvider abstract base class and factory behavior for:
    LLM_PROVIDER=ollama and LLM_PROVIDER=groq.
    The rest of the application must not depend on the specific provider.
    """
    ollama_p = get_llm_provider("ollama")
    assert isinstance(ollama_p, LLMProvider)
    assert isinstance(ollama_p, OllamaProvider)
    assert "ollama" in ollama_p.provider_name.lower()

    groq_p = get_llm_provider("groq")
    assert isinstance(groq_p, LLMProvider)
    assert isinstance(groq_p, GroqProvider)
    assert "groq" in groq_p.provider_name.lower()

@pytest.mark.asyncio
async def test_800_word_complaint_summarization():
    """Verifies user exact scenario:
    Original complaint: 800 words describing a duplicate payment of ₹5,000.
    AI Summary:
      'Customer reports a duplicate payment of ₹5,000.
       The payment occurred today and the customer is requesting
       an immediate refund.'
    """
    # Construct an 800-word verbose complaint narrative
    filler_narrative = (
        "I am writing this detailed statement because I am extremely concerned with the state of my account transactions. "
        "Every single month I carefully balance my finances and ensure that no erroneous debits are made. "
        "Earlier this morning I attempted to checkout on the mobile application for my regular monthly service charges. "
        "The screen showed a processing spinner for an unusually long time, approximately three minutes, without confirming. "
        "Thinking the internet connection had dropped, I refreshed the application and retried the transaction. "
        "To my utmost shock and dismay, when I opened my bank statement, I noticed that the exact charge went through twice. "
    )
    long_800_words = (
        "URGENT ATTENTION REQUIRED: Customer reports a duplicate payment of ₹5,000 today. "
        + (filler_narrative * 12)  # Generates ~850 words
        + "The payment occurred today and the customer is requesting an immediate refund to the source account without any delay."
    )
    word_count = len(long_800_words.split())
    assert word_count >= 800, f"Expected at least 800 words, got {word_count}"

    # Generate AI Summary using LLMProvider interface
    result = await summarizer.summarize(
        subject="Duplicate deduction on card checkout",
        body=long_800_words
    )

    summary_text = result["summary"]
    assert summary_text is not None and len(summary_text) > 20
    # Must capture duplicate payment of ₹5,000
    assert "duplicate payment" in summary_text.lower()
    assert "5,000" in summary_text or "5000" in summary_text
    # Must capture requested refund
    assert "refund" in summary_text.lower()
    # Executive summary should be concise (under 50 words)
    assert len(summary_text.split()) <= 50

@pytest.mark.asyncio
async def test_summarize_and_store_in_database(db: Session):
    """Verifies summary is persisted to the database on complaint.summary
    and in the ai_responses table.
    """
    body_text = (
        "Customer reports a duplicate payment of ₹5,000. "
        "The payment occurred today and the customer is requesting an immediate refund."
    )
    c = Complaint(
        complaint_number="CMP-SUMM-STORE-001",
        customer_email="finance_user@test.com",
        customer_name="Ranjith Customer",
        subject="Duplicate Payment Deduction ₹5,000",
        description=body_text,
        category="Billing",
        status="NEW"
    )
    db.add(c)
    db.commit()
    db.refresh(c)

    # Initial summary should be empty
    assert c.summary is None

    # Summarize and store
    res = await complaint_service.summarize_and_store_complaint(
        db=db,
        complaint_id=c.id
    )

    assert res["stored"] is True
    assert res["summary"] is not None

    # Verify complaint record in database has stored summary
    db.refresh(c)
    assert c.summary is not None
    assert "duplicate payment" in c.summary.lower()
    assert "refund" in c.summary.lower()

    # Verify AIResponse table contains response_type="SUMMARY"
    ai_resp = db.query(AIResponse).filter(
        AIResponse.complaint_id == c.id,
        AIResponse.response_type == "SUMMARY"
    ).first()
    assert ai_resp is not None
    assert ai_resp.content == c.summary

def test_summarize_api_endpoint(client: TestClient, db: Session):
    """Verifies POST /api/complaints/{id}/summarize and GET /api/complaints/{id}/summary."""
    c = Complaint(
        complaint_number="CMP-API-SUMM-001",
        customer_email="user_api@domain.com",
        subject="Duplicate payment issue",
        description="Customer reports a duplicate payment of ₹5,000. The payment occurred today and customer is requesting an immediate refund.",
        category="Billing",
        status="NEW"
    )
    db.add(c)
    db.commit()
    db.refresh(c)

    # POST to trigger summarization
    post_res = client.post(f"/api/complaints/{c.id}/summarize")
    assert post_res.status_code == 200
    data = post_res.json()
    assert data["stored"] is True
    assert "duplicate payment" in data["summary"].lower()

    # GET to retrieve stored summary
    get_res = client.get(f"/api/complaints/{c.id}/summary")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["summary"] == data["summary"]
