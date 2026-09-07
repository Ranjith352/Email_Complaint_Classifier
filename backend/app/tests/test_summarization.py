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

def test_ollama_default_configuration_and_model_configuration():
    """Verifies:
    1. Ollama is the default local LLM.
    2. Default base URL is http://localhost:11434.
    3. Does not assume a model is pre-installed.
    4. Allows the user to configure the model.
    """
    from app.core.config import settings
    assert settings.LLM_PROVIDER == "ollama"
    assert "http://localhost:11434" in settings.OLLAMA_BASE_URL

    # Test that OllamaProvider allows model configuration
    provider = OllamaProvider()
    assert provider.base_url == "http://localhost:11434"

    # Dynamic user configuration
    provider.set_model("llama3")
    assert provider.model == "llama3"
    assert "llama3" in provider.provider_name

    provider.set_model("mistral")
    assert provider.model == "mistral"
    assert "mistral" in provider.provider_name

    # Factory instantiation with explicit model override
    custom_provider = get_llm_provider("ollama", model="qwen2.5")
    assert custom_provider.model == "qwen2.5"

@pytest.mark.asyncio
async def test_ollama_unavailable_model_clear_error_and_no_crash():
    """Verifies:
    If the model is unavailable:
    - Return a clear error.
    - Do not crash the entire application.
    - Provides official download link https://ollama.com/download.
    """
    # 1. Unconfigured model scenario
    empty_provider = OllamaProvider(model="")
    health = await empty_provider.check_availability()
    assert health["available"] is False
    assert "No Ollama model is configured" in health["error"]
    assert "https://ollama.com/download" in health["download_url"]

    # generate_chat should not crash and return None with clear warning
    chat_res = await empty_provider.generate_chat("System", "User")
    assert chat_res is None
    assert "No Ollama model configured" in empty_provider.last_error

    # summarize should not crash, returns clear fallback and error metadata
    summ_res = await empty_provider.summarize(
        text="Customer reports a duplicate payment of ₹5,000 today and requests an immediate refund.",
        subject="Duplicate charge"
    )
    assert summ_res["status"] == "fallback"
    assert summ_res["error"] is not None
    assert "5,000" in summ_res["summary"]
    assert "https://ollama.com/download" in summ_res["download_url"]

    # 2. Unavailable server scenario (pointing to non-existent port)
    unreachable_provider = OllamaProvider(model="llama3", base_url="http://127.0.0.1:59999")
    unreach_health = await unreachable_provider.check_availability()
    assert unreach_health["available"] is False
    assert "Cannot connect to local Ollama service" in unreach_health["error"]
    assert "https://ollama.com/download" in unreach_health["download_url"]

    # Must not crash when querying unavailable endpoint
    unreach_chat = await unreachable_provider.generate_chat("System", "User")
    assert unreach_chat is None
    assert "not reachable" in unreachable_provider.last_error

@pytest.mark.asyncio
async def test_application_continues_when_model_unavailable(db: Session):
    """Verifies that other functionality continues smoothly without crashing
    even if the local Ollama model is completely unavailable.
    """
    from app.ai.ai_orchestrator import ai_orchestrator

    # Even if Ollama is offline or unconfigured, full complaint processing proceeds
    res = await ai_orchestrator.process_complaint_full(
        subject="Portal access failure",
        body="I cannot login to my account on the web portal since this morning. Please unlock my credentials.",
        customer_name="Test Customer",
        ticket_number="CONT-001",
        db=db
    )

    # Core AI functionality succeeded
    assert res["language"] == "en"
    assert res["sentiment"] in ["NEGATIVE", "POSITIVE", "NEUTRAL"]
    assert res["emotion"] in ["ANGER", "FRUSTRATION", "FEAR", "SADNESS", "NEUTRAL", "SATISFACTION"]
    assert res["urgency"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert res["priority_score"] >= 0
    assert res["confidence"] > 0
    assert res["embedding"] is not None
    assert res["summary"] is not None

def test_llm_management_api_endpoints(client: TestClient):
    """Verifies REST endpoints for LLM status, models listing, and runtime configuration."""
    # 1. GET /api/ai/llm/status
    status_res = client.get("/api/ai/llm/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert "active_provider" in status_data
    assert "download_url" in status_data
    assert "https://ollama.com/download" in status_data["download_url"]

    # 2. GET /api/ai/llm/models
    models_res = client.get("/api/ai/llm/models")
    assert models_res.status_code == 200
    models_data = models_res.json()
    assert "installed_models" in models_data
    assert "https://ollama.com/download" in models_data["download_url"]

    # 3. POST /api/ai/llm/config
    config_res = client.post("/api/ai/llm/config", json={
        "provider": "ollama",
        "ollama_model": "llama3",
        "ollama_base_url": "http://localhost:11434"
    })
    assert config_res.status_code == 200
    config_data = config_res.json()
    assert config_data["configuration"]["OLLAMA_MODEL"] == "llama3"
    assert config_data["configuration"]["OLLAMA_BASE_URL"] == "http://localhost:11434"

def test_groq_optional_provider_and_env_config():
    """Verifies:
    1. Groq is an optional provider.
    2. Environment uses GROQ_API_KEY and GROQ_MODEL.
    3. Never hardcode the key; never commit the key.
    """
    from app.core.config import settings
    groq_p = GroqProvider()
    assert isinstance(groq_p, LLMProvider)
    # API key is sourced from settings/env
    assert groq_p.api_key == settings.GROQ_API_KEY
    assert groq_p.model == settings.GROQ_MODEL

    # Key is dynamically passed, never hardcoded in provider class
    custom_p = GroqProvider(api_key="test-ephemeral-key", model="llama-3.3-70b-versatile")
    assert custom_p.api_key == "test-ephemeral-key"
    assert "llama-3.3-70b-versatile" in custom_p.provider_name

@pytest.mark.asyncio
async def test_groq_unavailable_falls_back_to_configured_ollama(monkeypatch):
    """Verifies:
    If Groq is unavailable:
    Fall back to Ollama when configured.
    """
    from app.core.config import settings
    # Configure Ollama model
    monkeypatch.setattr(settings, "OLLAMA_MODEL", "llama3")

    # Instantiate Groq provider with missing/invalid API key
    groq_p = GroqProvider(api_key="", model="llama-3.3-70b-versatile")

    # Check availability reflects fallback
    avail = await groq_p.check_availability()
    assert avail["available"] is False
    assert avail["fallback_to_ollama"] is True
    assert avail["ollama_model"] == "llama3"

    # Summarize should fall back to Ollama / calibrated extraction without crashing
    res = await groq_p.summarize(
        text="Customer reports a duplicate payment of ₹5,000 today and is requesting an immediate refund.",
        subject="Duplicate charge"
    )
    assert res is not None
    assert "duplicate payment" in res["summary"].lower()
    assert "5,000" in res["summary"] or "5000" in res["summary"]

@pytest.mark.asyncio
async def test_groq_network_failure_falls_back_without_crash(monkeypatch):
    """Verifies that when Groq encounters a network/API failure,
    it falls back to Ollama or calibrated extraction without crashing.
    """
    from app.core.config import settings
    monkeypatch.setattr(settings, "OLLAMA_MODEL", "llama3")

    # Provide an arbitrary invalid key that will fail API calls
    failing_groq = GroqProvider(api_key="gsk_invalid_test_key_for_fallback", model="llama-3.3-70b-versatile")

    # Calling generate_chat should not raise unhandled exception; falls back safely
    reply = await failing_groq.generate_chat("System prompt", "User prompt")
    # Should safely return string or None without crashing
    assert failing_groq.last_error is not None


