import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ai.rag import rag_engine
from app.services.complaint_service import complaint_service
from app.models.complaint import Complaint
from app.models.intelligence import AIResponse

@pytest.mark.asyncio
async def test_ai_recommended_resolution_structure(db: Session):
    """Verifies that AI Recommended Resolution provides:
    1. Header: 'AI GENERATED RECOMMENDATION'
    2. Disclaimer: 'The agent remains responsible for the final decision.'
    3. Actionable sequential resolution steps.
    """
    rec_res = await rag_engine.generate_grounded_recommendation(
        complaint_text="My subscription was charged twice. Please reverse duplicate charge.",
        category="Billing",
        db=db
    )

    assert rec_res["header"] == "AI GENERATED RECOMMENDATION"
    assert rec_res["disclaimer"] == "The agent remains responsible for the final decision."
    assert "recommended_steps" in rec_res
    steps = rec_res["recommended_steps"]
    assert len(steps) >= 5

    # Check duplicate billing sequential resolution steps
    assert any("transaction id" in s.lower() for s in steps)
    assert any("payment gateway" in s.lower() for s in steps)
    assert any("settled" in s.lower() for s in steps)
    assert any("refund" in s.lower() for s in steps)
    assert any("customer" in s.lower() for s in steps)

    # Check formatted block contains header, numbered steps, and disclaimer
    formatted = rec_res["formatted_recommendation"]
    assert "AI GENERATED RECOMMENDATION" in formatted
    assert "The agent remains responsible for the final decision." in formatted
    assert "1. " in formatted

@pytest.mark.asyncio
async def test_complaint_endpoint_recommendations(client: TestClient, db: Session):
    """Verifies that complaint details and recommendation endpoints return AI Recommended Resolution."""
    # Create test complaint
    comp = Complaint(
        complaint_number="TEST-REC-001",
        customer_name="John Doe",
        customer_email="john@example.com",
        subject="Duplicate credit card charge",
        description="I noticed duplicate deduction for transaction TXN-12345. Double charge settled.",
        category="Billing",
        urgency="High",
        priority="P2",
        status="NEW"
    )
    db.add(comp)
    db.commit()
    db.refresh(comp)

    # Test GET /api/complaints/{id}/recommendations
    res = client.get(f"/api/complaints/{comp.id}/recommendations")
    assert res.status_code == 200
    data = res.json()
    assert data["header"] == "AI GENERATED RECOMMENDATION"
    assert data["disclaimer"] == "The agent remains responsible for the final decision."
    assert len(data["recommended_steps"]) >= 4

    # Verify AIResponse is saved in database
    ai_resp = db.query(AIResponse).filter(
        AIResponse.complaint_id == comp.id,
        AIResponse.response_type == "RECOMMENDATION"
    ).first()
    assert ai_resp is not None
    assert "AI GENERATED RECOMMENDATION" in ai_resp.content
    assert "The agent remains responsible for the final decision." in ai_resp.content

    # Test GET /api/complaints/{id} details contains RECOMMENDATION in ai_responses
    detail_res = client.get(f"/api/complaints/{comp.id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    recs = [r for r in detail_data.get("ai_responses", []) if r["response_type"] == "RECOMMENDATION"]
    assert len(recs) == 1
    assert "The agent remains responsible for the final decision." in recs[0]["content"]

    # Test POST /api/complaints/{id}/recommendations (refresh)
    post_res = client.post(f"/api/complaints/{comp.id}/recommendations")
    assert post_res.status_code == 200
    post_data = post_res.json()
    assert post_data["header"] == "AI GENERATED RECOMMENDATION"
    assert post_data["disclaimer"] == "The agent remains responsible for the final decision."
