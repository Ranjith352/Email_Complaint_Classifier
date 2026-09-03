import pytest
from unittest.mock import patch, AsyncMock
from app.models.complaint import Complaint
from app.models.organization import Department

@pytest.fixture(autouse=True)
def ensure_departments(db):
    if not db.query(Department).filter(Department.name == "Finance").first():
        db.add(Department(name="Finance", code="FIN", description="Finance and Billing", is_active=True))
    if not db.query(Department).filter(Department.name == "IT").first():
        db.add(Department(name="IT", code="IT", description="Information Technology", is_active=True))
    db.commit()

def test_high_confidence_automatic_routing(client, db):
    # confidence >= 0.85: Automatically route, review_required = False
    mock_res = {
        "category": "Billing",
        "sub_category": "Duplicate Payment",
        "department": "Finance",
        "team": "Payments",
        "department_name": "Finance",
        "team_name": "Payments",
        "sentiment": "NEGATIVE",
        "emotion": "FRUSTRATION",
        "urgency": "HIGH",
        "priority": "HIGH",
        "priority_level": "P2",
        "priority_score": 75,
        "confidence": 0.94,  # >= 0.85
        "cat_confidence": 0.94,
        "review_required": False,
        "language": "en",
        "cleaned_text": "Charged twice",
        "entities": [],
        "draft_response": {"provider": "Mock", "body": "Draft"},
        "is_duplicate": False,
        "duplicate_of_id": None,
        "duplicate_similarity": 0.0,
        "embedding": [0.1] * 384,
        "summary": "High confidence test complaint",
        "execution_time_ms": 10.0
    }
    with patch("app.ai.ai_orchestrator.ai_orchestrator.process_complaint_full", new_callable=AsyncMock) as mock_full:
        mock_full.return_value = mock_res

        res = client.post("/api/complaints/", json={
            "subject": "Charged twice for subscription",
            "description": "I was charged twice on my card.",
            "customer_email": "customer@test.com",
            "source": "WEB"
        })
        assert res.status_code == 201
        data = res.json()

        # Check high confidence behavior
        assert data["ai_confidence"] == 0.94
        assert data["review_required"] is False
        assert data["department_id"] is not None
        assert data["status"] in ("ROUTED", "ASSIGNED")
        assert data["reviewed_by"] is None
        assert data["reviewed_at"] is None

def test_medium_confidence_provisional_routing(client, db):
    # confidence 0.60 - 0.84: Route but mark review_required = True
    mock_res = {
        "category": "Technical Problem",
        "sub_category": "Application Support",
        "department": "IT",
        "team": "Application Support",
        "department_name": "IT",
        "team_name": "Application Support",
        "sentiment": "NEUTRAL",
        "emotion": "NEUTRAL",
        "urgency": "MEDIUM",
        "priority": "MEDIUM",
        "priority_level": "P3",
        "priority_score": 45,
        "confidence": 0.72,  # 0.60 - 0.84
        "cat_confidence": 0.72,
        "review_required": True,
        "language": "en",
        "cleaned_text": "Trouble logging in",
        "entities": [],
        "draft_response": {"provider": "Mock", "body": "Draft"},
        "is_duplicate": False,
        "duplicate_of_id": None,
        "duplicate_similarity": 0.0,
        "embedding": [0.1] * 384,
        "summary": "Medium confidence test complaint",
        "execution_time_ms": 12.0
    }
    with patch("app.ai.ai_orchestrator.ai_orchestrator.process_complaint_full", new_callable=AsyncMock) as mock_full:
        mock_full.return_value = mock_res

        res = client.post("/api/complaints/", json={
            "subject": "Trouble logging in",
            "description": "The login button sometimes spins without loading.",
            "customer_email": "user@test.com",
            "source": "WEB"
        })
        assert res.status_code == 201
        data = res.json()

        # Check medium confidence behavior
        assert data["ai_confidence"] == 0.72
        assert data["review_required"] is True
        assert data["department_id"] is not None
        assert data["status"] in ("ROUTED", "ASSIGNED")

def test_low_confidence_unfinalized_department(client, db):
    # confidence < 0.60: Do not automatically finalize department, require human review
    mock_res = {
        "category": "Customer Support",
        "sub_category": "General Inquiry",
        "department": "Operations",
        "team": "General Triage",
        "department_name": "Operations",
        "team_name": "General Triage",
        "sentiment": "NEUTRAL",
        "emotion": "NEUTRAL",
        "urgency": "LOW",
        "priority": "LOW",
        "priority_level": "P4",
        "priority_score": 25,
        "confidence": 0.45,  # < 0.60
        "cat_confidence": 0.45,
        "review_required": True,
        "language": "en",
        "cleaned_text": "Vague question",
        "entities": [],
        "draft_response": {"provider": "Mock", "body": "Draft"},
        "is_duplicate": False,
        "duplicate_of_id": None,
        "duplicate_similarity": 0.0,
        "embedding": [0.1] * 384,
        "summary": "Low confidence ambiguous complaint",
        "execution_time_ms": 15.0
    }
    with patch("app.ai.ai_orchestrator.ai_orchestrator.process_complaint_full", new_callable=AsyncMock) as mock_full:
        mock_full.return_value = mock_res

        res = client.post("/api/complaints/", json={
            "subject": "Ambiguous message",
            "description": "Something happened with my account thing.",
            "customer_email": "ambiguous@test.com",
            "source": "WEB"
        })
        assert res.status_code == 201
        data = res.json()
        c_id = data["id"]

        # Department must NOT be automatically finalized
        assert data["ai_confidence"] == 0.45
        assert data["review_required"] is True
        assert data["department_id"] is None
        assert data["team_id"] is None
        assert data["assigned_agent_id"] is None

        # Fetch department id for Finance
        finance_dept = db.query(Department).filter(Department.name == "Finance").first()
        target_dept_id = finance_dept.id if finance_dept else 1

        # Test Human Review Workflow
        # Reviewer manually reviews and finalizes department to Finance
        rev_res = client.post(f"/api/complaints/{c_id}/review", json={
            "department_id": target_dept_id,
            "reviewer_name": "Sarah Connor",
            "notes": "Clarified with customer, this belongs to Finance"
        })
        assert rev_res.status_code == 200
        rev_data = rev_res.json()

        assert rev_data["review_required"] is False
        assert rev_data["reviewed_by"] == "Sarah Connor"
        assert rev_data["reviewed_at"] is not None
        assert rev_data["department_id"] == target_dept_id
        assert rev_data["status"] == "ROUTED"
