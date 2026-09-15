import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.complaint import Complaint
from app.models.organization import Department, Agent
from app.models.operations import AuditLog

def test_get_analytics_overview(client: TestClient, db: Session):
    """Verifies GET /api/analytics/overview returns all requested core metrics."""
    # Seed a couple test complaints
    c1 = Complaint(
        complaint_number="CMP-AN-001",
        customer_email="user1@example.com",
        subject="Overview Test 1",
        description="Test description",
        category="Billing",
        status="RESOLVED",
        urgency="Critical",
        priority="P1",
        ai_confidence=0.95,
        ai_status="COMPLETED",
        created_at=datetime.utcnow() - timedelta(hours=4),
        resolved_at=datetime.utcnow() - timedelta(hours=1),
        sla_deadline=datetime.utcnow() + timedelta(hours=2),
        is_duplicate=False
    )
    c2 = Complaint(
        complaint_number="CMP-AN-002",
        customer_email="user2@example.com",
        subject="Overview Test 2",
        description="Test description duplicate",
        category="Technical",
        status="IN_PROGRESS",
        urgency="Low",
        priority="P4",
        ai_confidence=0.88,
        ai_status="COMPLETED",
        review_required=True,
        created_at=datetime.utcnow() - timedelta(hours=2),
        sla_deadline=datetime.utcnow() + timedelta(hours=48),
        is_duplicate=True
    )
    db.add_all([c1, c2])
    db.commit()

    res = client.get("/api/analytics/overview")
    assert res.status_code == 200
    data = res.json()

    # Core metrics calculated
    assert "total_complaints" in data
    assert data["total_complaints"] >= 2
    assert "resolution_rate" in data
    assert isinstance(data["resolution_rate"], (int, float))
    assert "average_resolution_time" in data
    assert "sla_compliance" in data
    assert "duplicate_rate" in data
    assert "ai_routing_rate" in data
    assert "human_review_rate" in data
    assert "human_correction_rate" in data
    assert "trends" in data
    assert isinstance(data["trends"], list)


def test_get_analytics_departments(client: TestClient, db: Session):
    """Verifies GET /api/analytics/departments returns department workload."""
    dept = Department(name="Modular Analytics Dept", code="MODAN", description="Finance dept for test")
    db.add(dept)
    db.commit()

    c = Complaint(
        complaint_number="CMP-DEPT-001",
        customer_email="user@finance.com",
        subject="Finance query",
        description="Payment failed",
        category="Billing",
        department_id=dept.id,
        status="OPEN",
        urgency="High",
        priority="P2",
        ai_confidence=0.92,
        sla_deadline=datetime.utcnow() + timedelta(hours=8)
    )
    db.add(c)
    db.commit()

    res = client.get("/api/analytics/departments")
    assert res.status_code == 200
    data = res.json()

    assert "department_workload" in data
    assert isinstance(data["department_workload"], list)
    assert len(data["department_workload"]) >= 1

    dept_wl = next((d for d in data["department_workload"] if d["department_id"] == dept.id), None)
    assert dept_wl is not None
    assert dept_wl["department_name"] == "Modular Analytics Dept"
    assert dept_wl["total_complaints"] >= 1
    assert "workload_percentage" in dept_wl
    assert "active_agents_count" in dept_wl
    assert "sla_compliance" in dept_wl


def test_get_analytics_categories(client: TestClient, db: Session):
    """Verifies GET /api/analytics/categories returns category distribution."""
    c = Complaint(
        complaint_number="CMP-CAT-001",
        customer_email="cat@test.com",
        subject="Category Test",
        description="Refunds inquiry",
        category="Refunds",
        sub_category="Bank Transfer",
        status="OPEN",
        urgency="Medium",
        priority="P3",
        sla_deadline=datetime.utcnow() + timedelta(hours=24)
    )
    db.add(c)
    db.commit()

    res = client.get("/api/analytics/categories")
    assert res.status_code == 200
    data = res.json()

    assert "category_distribution" in data
    assert isinstance(data["category_distribution"], list)
    refunds_cat = next((x for x in data["category_distribution"] if x["category"] == "Refunds"), None)
    assert refunds_cat is not None
    assert refunds_cat["count"] >= 1
    assert "percentage" in refunds_cat
    assert "open_count" in refunds_cat
    assert "subcategories" in refunds_cat


def test_get_analytics_sentiment(client: TestClient, db: Session):
    """Verifies GET /api/analytics/sentiment returns sentiment distribution."""
    c = Complaint(
        complaint_number="CMP-SENT-001",
        customer_email="sentiment@test.com",
        subject="Sentiment test",
        description="Bad service",
        category="Support",
        sentiment="Negative",
        status="OPEN",
        urgency="High",
        priority="P2",
        sla_deadline=datetime.utcnow() + timedelta(hours=8)
    )
    db.add(c)
    db.commit()

    res = client.get("/api/analytics/sentiment")
    assert res.status_code == 200
    data = res.json()

    assert "sentiment_distribution" in data
    assert isinstance(data["sentiment_distribution"], list)
    sentiments = [s["sentiment"] for s in data["sentiment_distribution"]]
    assert "Positive" in sentiments
    assert "Neutral" in sentiments
    assert "Negative" in sentiments
    for s in data["sentiment_distribution"]:
        assert "count" in s
        assert "percentage" in s
        assert "average_confidence" in s


def test_get_analytics_emotions(client: TestClient, db: Session):
    """Verifies GET /api/analytics/emotions returns emotion distribution."""
    c = Complaint(
        complaint_number="CMP-EMO-001",
        customer_email="emotion@test.com",
        subject="Emotion test",
        description="Frustrated customer",
        category="Support",
        emotion="Frustration",
        status="OPEN",
        urgency="Critical",
        priority="P1",
        sla_deadline=datetime.utcnow() + timedelta(hours=2)
    )
    db.add(c)
    db.commit()

    res = client.get("/api/analytics/emotions")
    assert res.status_code == 200
    data = res.json()

    assert "emotion_distribution" in data
    assert isinstance(data["emotion_distribution"], list)
    frust = next((e for e in data["emotion_distribution"] if e["emotion"] == "Frustration"), None)
    assert frust is not None
    assert frust["count"] >= 1
    assert "percentage" in frust
    assert "dominant_sentiment" in frust
    assert "critical_count" in frust


def test_get_analytics_priority(client: TestClient, db: Session):
    """Verifies GET /api/analytics/priority returns priority distribution."""
    res = client.get("/api/analytics/priority")
    assert res.status_code == 200
    data = res.json()

    assert "priority_distribution" in data
    assert isinstance(data["priority_distribution"], list)
    priorities = [p["priority"] for p in data["priority_distribution"]]
    assert priorities == ["P1", "P2", "P3", "P4"]
    for p in data["priority_distribution"]:
        assert "target_sla_hours" in p
        assert "count" in p
        assert "percentage" in p
        assert "sla_compliance" in p


def test_get_analytics_sla(client: TestClient, db: Session):
    """Verifies GET /api/analytics/sla returns SLA compliance metrics."""
    res = client.get("/api/analytics/sla")
    assert res.status_code == 200
    data = res.json()

    assert "sla_compliance" in data
    assert "sla_breaches" in data
    assert "sla_approaching" in data
    assert "sla_compliant" in data
    assert "average_resolution_time" in data
    assert "compliance_by_priority" in data
    assert "compliance_by_department" in data


def test_get_analytics_agents(client: TestClient, db: Session):
    """Verifies GET /api/analytics/agents returns agent workload metrics."""
    agent = Agent(
        name="Test Agent Analytics",
        email="agent.analytics@test.com",
        current_workload=3,
        max_workload=10,
        performance_score=4.9,
        is_active=True
    )
    db.add(agent)
    db.commit()

    res = client.get("/api/analytics/agents")
    assert res.status_code == 200
    data = res.json()

    assert "agent_workload" in data
    assert isinstance(data["agent_workload"], list)
    found_agent = next((a for a in data["agent_workload"] if a["agent_id"] == agent.id), None)
    assert found_agent is not None
    assert found_agent["current_workload"] == 3
    assert found_agent["max_workload"] == 10
    assert found_agent["utilization_rate"] == 30.0


def test_get_analytics_ai_performance(client: TestClient, db: Session):
    """Verifies GET /api/analytics/ai-performance returns AI performance & human correction metrics."""
    res = client.get("/api/analytics/ai-performance")
    assert res.status_code == 200
    data = res.json()

    assert "ai_routing_rate" in data
    assert "ai_confidence" in data
    assert "human_review_rate" in data
    assert "human_correction_rate" in data
    assert "duplicate_rate" in data
    assert "confidence_distribution" in data
    assert isinstance(data["confidence_distribution"], list)
