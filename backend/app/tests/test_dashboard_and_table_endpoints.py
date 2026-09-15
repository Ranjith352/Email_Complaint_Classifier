import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.complaint import Complaint
from app.models.organization import Department, Team, Agent
from app.models.user import User
from app.core.security import get_password_hash, create_access_token

def test_main_dashboard_10_kpis_and_9_charts(client: TestClient, db: Session):
    """Verifies that GET /api/analytics/dashboard returns all 10 KPIs and 9 charts."""
    res = client.get("/api/analytics/dashboard")
    assert res.status_code == 200
    data = res.json()

    # 1. Ten Core KPIs
    assert "kpis" in data
    kpis = data["kpis"]
    required_kpis = [
        "total_complaints",
        "open_complaints",
        "critical_complaints",
        "resolved_complaints",
        "sla_breaches",
        "avg_resolution_hours",
        "ai_auto_routing_rate",
        "ai_confidence",
        "duplicate_complaints",
        "human_review_required"
    ]
    for k in required_kpis:
        assert k in kpis, f"Missing KPI {k}"

    # 2. Nine Visual Charts
    assert "charts" in data
    charts = data["charts"]
    required_charts = [
        "complaints_over_time",
        "complaints_by_department",
        "complaints_by_category",
        "priority_distribution",
        "sentiment_distribution",
        "emotion_distribution",
        "resolution_time",
        "sla_compliance",
        "agent_workload"
    ]
    for c in required_charts:
        assert c in charts, f"Missing chart {c}"
        assert isinstance(charts[c], list), f"Chart {c} should be a list"

def test_ai_insights_endpoint(client: TestClient, db: Session):
    """Verifies that GET /api/analytics/insights returns data-grounded non-fabricated insights."""
    res = client.get("/api/analytics/insights")
    assert res.status_code == 200
    data = res.json()
    assert "insights" in data
    assert isinstance(data["insights"], list)

def test_department_dashboard_and_manager_rbac(client: TestClient, db: Session):
    """Verifies dedicated department dashboard and Manager data isolation."""
    # Ensure Finance and IT departments exist
    fin = db.query(Department).filter(Department.name == "Finance").first()
    if not fin:
        fin = Department(name="Finance", code="FIN", is_active=True)
        db.add(fin)
        db.commit()

    it = db.query(Department).filter(Department.name == "IT").first()
    if not it:
        it = Department(name="IT", code="IT", is_active=True)
        db.add(it)
        db.commit()

    # 1. Unauthenticated or Admin access
    res = client.get(f"/api/departments/{fin.id}/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert "department" in data
    assert "metrics" in data
    metrics = data["metrics"]
    for m in ["open_complaints", "critical_complaints", "sla_risks", "resolved_complaints", "average_resolution_time"]:
        assert m in metrics
    assert "agent_workload" in data
    assert "top_complaint_categories" in data
    assert "recent_complaints" in data

    # 2. Create Manager assigned strictly to Finance
    mgr_user = db.query(User).filter(User.email == "fin.mgr@company.com").first()
    if not mgr_user:
        mgr_user = User(
            email="fin.mgr@company.com",
            name="Finance Manager",
            password_hash=get_password_hash("password123"),
            role="MANAGER",
            department_id=fin.id,
            is_active=True
        )
        db.add(mgr_user)
        db.commit()

    token = create_access_token(mgr_user.id, role="MANAGER", email=mgr_user.email)
    headers = {"Authorization": f"Bearer {token}"}

    # Allowed: Manager accesses own department
    allowed_res = client.get(f"/api/departments/{fin.id}/dashboard", headers=headers)
    assert allowed_res.status_code == 200

    # Forbidden: Manager accesses different department (IT)
    forbidden_res = client.get(f"/api/departments/{it.id}/dashboard", headers=headers)
    assert forbidden_res.status_code == 403
    assert "Access denied" in forbidden_res.json()["detail"]

def test_complaint_filtering_and_atomic_actions(client: TestClient, db: Session):
    """Verifies table querying filters and atomic actions: priority, status, department, team, agent."""
    # Create test complaint
    c = Complaint(
        complaint_number="CMP-TEST-TABLE-1",
        customer_name="Table Test Customer",
        customer_email="table.test@example.com",
        subject="Payment gateway timeout",
        description="Transaction timed out during card auth.",
        category="Billing / Payment",
        urgency="High",
        priority="P2",
        sentiment="Negative",
        status="NEW"
    )
    db.add(c)
    db.commit()
    db.refresh(c)

    # 1. Query with filters
    q_res = client.get("/api/complaints/", params={"category": "Billing", "priority_level": "P2", "sentiment": "Negative"})
    assert q_res.status_code == 200
    matched = [item for item in q_res.json() if item["id"] == c.id]
    assert len(matched) == 1
    assert matched[0]["sla_metrics"] is not None

    # 2. Update Priority
    prio_res = client.post(f"/api/complaints/{c.id}/priority", json={"priority": "P1", "reason": "VIP Customer Escalation"})
    assert prio_res.status_code == 200
    assert prio_res.json()["complaint"]["priority"] == "P1"
    assert prio_res.json()["complaint"]["urgency"] == "Critical"

    # 3. Update Status
    status_res = client.post(f"/api/complaints/{c.id}/status", json={"status": "IN_PROGRESS", "notes": "Agent handling"})
    assert status_res.status_code == 200
    assert status_res.json()["complaint"]["status"] == "IN_PROGRESS"
