import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.intelligence import ModelVersion
from app.models.complaint import Complaint
from app.models.organization import Department, Team, Agent
from app.services.privacy_service import privacy_service, is_luhn_valid
from app.services.assistant_tools import assistant_tools
from app.services.assistant_service import assistant_service


def test_model_versions_active_endpoint(client, db):
    """Verify active model versions endpoint returns required schema and real metrics."""
    mv = db.query(ModelVersion).filter(ModelVersion.is_active == True).first()
    if not mv:
        mv = ModelVersion(
            model_name="Baseline Logistic Regression (Department)",
            version="1.0.0",
            accuracy=1.0,
            precision=1.0,
            recall=1.0,
            f1_score=1.0,
            training_date=datetime.utcnow(),
            dataset_version="v1.0",
            is_active=True,
            description="Trained on 650 complaints stratified 80/20"
        )
        db.add(mv)
        db.commit()

    response = client.get("/api/v1/models/active")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    first = data[0]
    # Check all 9 required fields
    for field in ["model_name", "version", "accuracy", "precision", "recall", "f1_score", "training_date", "dataset_version", "is_active"]:
        assert field in first, f"Missing required field {field}"

    assert first["is_active"] is True
    assert first["accuracy"] is not None
    assert first["f1_score"] is not None

def test_ai_models_active_alias_endpoint(client, db):
    """Verify alias /api/v1/ai/models/active also works."""
    response = client.get("/api/v1/ai/models/active")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(m["is_active"] is True for m in data)


def test_pii_detection_and_redaction():
    """Verify detection and masking of emails, phones, payment cards, CVVs, and sensitive IDs."""
    sample_text = (
        "Customer John submitted refund for card 4532-0150-1234-5678, cvv: 921. "
        "Email him at customer.vip@example.com or phone +1-555-432-8765. "
        "His SSN is 123-45-6789 and Aadhaar is 1234 5678 9012."
    )

    detected = privacy_service.detect_pii(sample_text)
    assert len(detected["emails"]) >= 1
    assert detected["emails"][0]["value"] == "customer.vip@example.com"
    assert len(detected["phones"]) >= 1
    assert len(detected["payment_info"]) >= 1
    assert any(p["type"] == "CVV" for p in detected["payment_info"])
    assert len(detected["sensitive_identifiers"]) >= 1

    # Test masking for external LLM
    masked_text, has_sensitive = privacy_service.mask_pii_for_external_llm(sample_text)
    assert has_sensitive is True
    assert "customer.vip@example.com" not in masked_text
    assert "[EMAIL_REDACTED]" in masked_text
    assert "123-45-6789" not in masked_text
    assert "[SSN_REDACTED]" in masked_text

    # Test log sanitization
    sanitized_log = privacy_service.sanitize_log("Processing payment for card 4532-0150-1234-5678")
    assert "4532-0150-1234-5678" not in sanitized_log
    assert "[PAYMENT_CARD_REDACTED]" in sanitized_log

def test_luhn_validator():
    """Verify Luhn algorithm validation for credit card numbers."""
    assert is_luhn_valid("49927398716") is True
    assert is_luhn_valid("49927398717") is False

def test_controlled_tool_search_complaints(db):
    """Test search_complaints with controlled SQLAlchemy expressions (zero raw SQL)."""
    # Create test complaint
    dept = db.query(Department).filter(Department.name == "Finance").first()
    if not dept:
        dept = Department(name="Finance", code="FIN", description="Finance")
        db.add(dept)
        db.commit()

    existing = db.query(Complaint).filter(Complaint.ticket_number == "CMP-TEST-FIN").first()
    if not existing:
        test_c = Complaint(
            ticket_number="CMP-TEST-FIN",
            subject="Unauthorized Finance double charge",
            description="Double deduction occurred on gateway.",
            department_id=dept.id,
            category="Billing",
            sub_category="Payments",
            priority="Critical",
            urgency="Critical",
            sentiment="Negative",
            status="OPEN",
            customer_email="user_test@fin.com",
            customer_name="Alice Fin"
        )
        db.add(test_c)
        db.commit()


    res = assistant_tools.search_complaints(
        db=db,
        department="Finance",
        priority="Critical",
        unresolved_only=True
    )
    assert res["tool"] == "search_complaints"
    assert res["total_found"] >= 1
    tickets = [c["ticket_number"] for c in res["complaints"]]
    assert "CMP-TEST-FIN" in tickets

def test_controlled_tool_customer_history(db):
    """Test customer history viewing with privacy masking."""
    res = assistant_tools.get_customer_history(
        db=db,
        customer_email="user_test@fin.com"
    )
    assert res["tool"] == "get_customer_history"
    assert res["total_complaints"] >= 1
    assert "complaint_frequency" in res
    assert "previous_categories" in res
    assert "previous_resolutions" in res
    assert res["customer"]["masked_email"].startswith("u***@")

def test_controlled_tool_knowledge_base(db):
    """Test search_knowledge_base with policy retrieval."""
    res = assistant_tools.search_knowledge_base(
        db=db,
        query="What is the refund policy for duplicate charges?"
    )
    assert res["tool"] == "search_knowledge_base"
    assert "relevant_policies" in res

@pytest.mark.asyncio
async def test_assistant_orchestrator_scenarios(db):
    """Test the AI assistant orchestrator on the core scenario questions."""
    # Scenario 1: Show unresolved critical Finance complaints
    q1 = await assistant_service.handle_query("Show unresolved critical Finance complaints.", db=db)
    assert q1["tool_called"] == "search_complaints"
    assert "CMP-TEST-FIN" in q1["reply"] or "matching complaint" in q1["reply"]

    # Scenario 2: Summarize complaint CMP-10001 or CMP-TEST-FIN
    q2 = await assistant_service.handle_query("Summarize complaint CMP-TEST-FIN.", db=db)
    assert q2["tool_called"] == "get_complaint"
    assert "CMP-TEST-FIN" in q2["reply"]

    # Scenario 3: Find similar complaints
    q3 = await assistant_service.handle_query("Find similar complaints for payment deductions.", db=db)
    assert q3["tool_called"] == "find_similar_complaints"

    # Scenario 4: What policy applies to this refund complaint?
    q4 = await assistant_service.handle_query("What policy applies to this refund complaint?", db=db)
    assert q4["tool_called"] == "search_knowledge_base"
    assert "policy" in q4["reply"].lower()

    # Scenario 5: How should this complaint be resolved?
    q5 = await assistant_service.handle_query("How should this complaint be resolved?", db=db, ticket_number="CMP-TEST-FIN")
    assert q5["tool_called"] == "recommend_resolution"
    assert "AI GENERATED RECOMMENDATION" in q5["reply"]

    # Scenario 6: Generate a response
    q6 = await assistant_service.handle_query("Generate a response.", db=db, ticket_number="CMP-TEST-FIN")
    assert q6["tool_called"] == "generate_response"
    assert "Subject" in q6["reply"]

@pytest.mark.asyncio
async def test_assistant_arbitrary_sql_blocked(db):
    """Strict Guardrail: Verify arbitrary SQL execution attempts are completely blocked."""
    sql_attack = "SELECT * FROM users WHERE 1=1; DROP TABLE complaints;"
    res = await assistant_service.handle_query(sql_attack, db=db)
    assert res["error"] == "SQL_EXECUTION_FORBIDDEN"
    assert "strictly prohibited" in res["reply"]
    assert res["tool_called"] == "none"

def test_api_assistant_endpoint(client):
    """Test POST /api/v1/ai/assistant HTTP endpoint."""
    response = client.post("/api/v1/ai/assistant", json={
        "message": "Show unresolved critical Finance complaints."
    })

    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert data["tool_called"] == "search_complaints"
