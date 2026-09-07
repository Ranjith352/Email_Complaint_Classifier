import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.complaint import Complaint
from app.models.organization import Department
from app.models.incident import Incident
from app.services.incident_service import incident_service

def test_portal_authentication_failure_incident_detection(db: Session):
    """Verifies user exact scenario:
    50 complaints arrive within a short time window:
    'Portal is not working.', 'Cannot login.', 'Account access unavailable.'
    System output:
      Potential Incident Detected
      Incident: Portal Authentication Failure
      Affected complaints: 50
      Department: IT
      Severity: HIGH
    """
    # Ensure IT department exists
    it_dept = db.query(Department).filter(Department.name == "IT").first()
    if not it_dept:
        it_dept = Department(name="IT", code="IT", description="Information Technology")
        db.add(it_dept)
        db.commit()
        db.refresh(it_dept)

    # Generate 50 semantically similar complaints within the past 2 hours
    sample_phrases = [
        "Portal is not working.",
        "Cannot login.",
        "Account access unavailable.",
        "Unable to sign in to the web portal.",
        "Portal login page gives authentication error."
    ]

    now = datetime.utcnow()
    created_complaints = []
    for i in range(50):
        phrase = sample_phrases[i % len(sample_phrases)]
        c = Complaint(
            complaint_number=f"CMP-INC-TEST-{i+1:03d}",
            customer_email=f"user{i+1}@domain.com",
            customer_name=f"Customer {i+1}",
            subject=f"Access Error: {phrase}",
            description=f"Urgent assistance needed: {phrase} System shows credentials invalid or timeout.",
            category="IT",
            department_id=it_dept.id,
            status="NEW",
            urgency="High",
            created_at=now - timedelta(minutes=i * 2)
        )
        db.add(c)
        created_complaints.append(c)

    db.commit()

    # Run incident detection scan
    res = incident_service.detect_incidents(
        db=db,
        window_hours=6,
        min_complaints=5,
        similarity_threshold=0.60
    )

    # 1. System: Potential Incident Detected
    assert res["detected"] is True, "Expected potential incident to be detected"
    assert res["total_detected"] >= 1

    # Find the detected Portal incident
    portal_inc = next((inc for inc in res["incidents"] if "Portal" in inc.title or "Authentication" in inc.title), None)
    assert portal_inc is not None, f"Portal incident not found in {res['incidents']}"

    # 2. Incident: Portal Authentication Failure
    assert portal_inc.title == "Portal Authentication Failure"

    # 3. Department: IT
    assert portal_inc.department_name == "IT"

    # 4. Severity: HIGH
    assert portal_inc.severity == "HIGH"

    # 5. Affected complaints: 50
    assert portal_inc.affected_count >= 50
    assert len(portal_inc.complaint_ids) >= 50

def test_manager_acknowledge_and_resolve_incident(db: Session):
    """Verifies manager can acknowledge and resolve detected incidents."""
    inc = Incident(
        incident_number="INC-2026-TEST-001",
        title="Portal Authentication Failure",
        description="50 users reporting login failure on customer portal",
        department_name="IT",
        severity="HIGH",
        status="DETECTED",
        affected_count=50,
        complaint_ids=[101, 102],
        sample_complaints=["Portal is not working.", "Cannot login."]
    )
    db.add(inc)
    db.commit()
    db.refresh(inc)

    # 1. Manager Acknowledges
    ack = incident_service.acknowledge_incident(
        db=db,
        incident_id=inc.id,
        manager_name="IT Operations Manager",
        notes="Engineering team dispatched to investigate SSO gateway."
    )
    assert ack.status == "ACKNOWLEDGED"
    assert ack.acknowledged_by == "IT Operations Manager"
    assert ack.acknowledged_at is not None

    # 2. Active incidents check includes acknowledged
    active = incident_service.get_active_incidents(db=db)
    assert any(i.id == inc.id for i in active)

    # 3. Manager Resolves
    res = incident_service.resolve_incident(
        db=db,
        incident_id=inc.id,
        manager_name="IT Operations Manager",
        resolution_notes="Auth certificate renewed and portal restarted."
    )
    assert res.status == "RESOLVED"
    assert res.resolved_by == "IT Operations Manager"
    assert res.resolved_at is not None

    # 4. No longer in active incidents
    active_after = incident_service.get_active_incidents(db=db)
    assert not any(i.id == inc.id for i in active_after)

def test_incident_api_endpoints(client: TestClient, db: Session):
    """Verifies REST API endpoints for incident detection and manager alerts."""
    now = datetime.utcnow()
    for i in range(4):
        c = Complaint(
            complaint_number=f"CMP-API-INC-{i+1}",
            customer_email=f"api_u{i+1}@test.com",
            subject="Cannot login to portal",
            description="Portal is not working. Account access unavailable.",
            category="IT",
            status="NEW",
            created_at=now - timedelta(minutes=5)
        )
        db.add(c)
    db.commit()

    # Trigger detection via REST
    detect_res = client.post("/api/incidents/detect", json={
        "window_hours": 12,
        "min_complaints": 3,
        "similarity_threshold": 0.60
    })
    assert detect_res.status_code == 200
    data = detect_res.json()
    assert data["detected"] is True
    assert data["total_detected"] >= 1

    # Get active incidents
    active_res = client.get("/api/incidents/active")
    assert active_res.status_code == 200
    active_list = active_res.json()
    assert len(active_list) >= 1
    target = active_list[0]
    assert "Portal" in target["title"] or "IT" in target["department_name"]

    # Manager Acknowledge via REST
    inc_id = target["id"]
    ack_res = client.post(f"/api/incidents/{inc_id}/acknowledge", json={
        "manager_name": "Operations Lead",
        "notes": "Acknowledged alert from executive dashboard."
    })
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "ACKNOWLEDGED"

    # Manager Resolve via REST
    res_res = client.post(f"/api/incidents/{inc_id}/resolve", json={
        "manager_name": "Operations Lead",
        "resolution_notes": "Patched upstream SSO issue."
    })
    assert res_res.status_code == 200
    assert res_res.json()["status"] == "RESOLVED"
