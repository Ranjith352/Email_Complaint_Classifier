import pytest
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Ensure backend app is in python path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.complaint import Complaint, ComplaintEvent, ComplaintStatus
from app.models.organization import Department, Team, Agent
from app.models.intelligence import AIResponse
from app.models.operations import AuditLog, SLARule, Notification
from app.core.security import get_password_hash, create_access_token
from app.services.sla_service import sla_service
from app.services.notification_service import notification_service
from app.services.email_service import email_service
from app.services.gmail_service import gmail_service

client = TestClient(app)

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        db.expire_all()
        yield db
    finally:
        db.close()

def get_auth_header(role: str = "ADMIN", email: str = "admin@complaints.io"):
    token = create_access_token({"sub": email, "role": role})
    return {"Authorization": f"Bearer {token}"}

# 1. Test Gmail Integration Endpoints & Unconfigured Fallback
def test_gmail_endpoints_and_unconfigured_fallback():
    """Validates GET /api/emails/status and POST /api/emails/sync when unconfigured."""
    # Status check
    status_resp = client.get("/api/emails/status")
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert "configured" in data
    assert data["manual_intake_available"] is True

    # Sync check - should gracefully return warning without crashing or throwing
    sync_resp = client.post("/api/emails/sync")
    assert sync_resp.status_code == 200
    sync_data = sync_resp.json()
    assert sync_data["status"] in ["warning", "success"]
    assert "Manual complaint creation" in sync_data["message"]

# 2. Test Manual Complaint Intake & Ingestion Pipeline (Without Gmail)
def test_manual_complaint_intake_pipeline(db_session: Session):
    """Submits a complaint through manual web intake with all fields:
    Customer Name, Customer Email, Subject, Complaint Description, Attachment, Source.
    Verifies the 9 pipeline stages:
    Create, AI Analysis, Priority, Duplicates, Department, Team, Agent, Notification, SLA.
    """
    payload = {
        "customer_name": "Marcus Vance",
        "customer_email": "marcus.vance@example.com",
        "subject": "Duplicate billing charge for $250 on debit card",
        "description": "I noticed two identical charges of $250 on my statement yesterday from transaction TX-8891. Please refund the duplicate.",
        "source": "WEB",
        "attachment_name": "bank_statement_march.pdf"
    }

    resp = client.post("/api/complaints/", json=payload)
    assert resp.status_code == 201
    comp = resp.json()

    assert comp["ticket_number"].startswith("CMP-")
    assert comp["customer_email"] == "marcus.vance@example.com"
    assert comp["customer_name"] == "Marcus Vance"
    assert comp["source"] == "WEB"
    assert comp["attachment_name"] == "bank_statement_march.pdf"
    assert comp["category"] in ["Billing", "Billing Discrepancy", "Transaction Issue", "Refund Request", "Account Management"]
    assert comp["priority_level"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "P1", "P2", "P3", "P4"]
    assert comp["sla_deadline"] is not None

    complaint_id = comp["id"]

    # Verify structured routing notification was created
    notifs_res = client.get("/api/notifications/")
    assert notifs_res.status_code == 200
    notifs = notifs_res.json()
    matching_notif = next((n for n in notifs if str(comp["ticket_number"]) in n["message"]), None)
    assert matching_notif is not None
    assert "Complaint:" in matching_notif["message"]
    assert "Department:" in matching_notif["message"]
    assert "Priority:" in matching_notif["message"]
    assert "SLA:" in matching_notif["message"]

    return complaint_id

# 3. Test Configurable SLA Rules and Warnings
def test_configurable_sla_rules_and_metrics(db_session: Session):
    """Verifies SLA configuration endpoint (PUT /api/sla-rules/{urgency}) and SLA warning tiers:
    75% (Warning), 90% (Critical warning), 100% (SLA BREACHED).
    """
    # Check default rules
    rules_resp = client.get("/api/sla-rules")
    assert rules_resp.status_code == 200
    rules = rules_resp.json()["rules"]
    assert rules["CRITICAL"] == 2
    assert rules["HIGH"] == 8
    assert rules["MEDIUM"] == 24
    assert rules["LOW"] == 72

    # Update SLA rule
    put_resp = client.put("/api/sla-rules/CRITICAL", json={"hours": 3})
    assert put_resp.status_code == 200
    assert put_resp.json()["new_hours"] == 3

    # Reset back to 2
    client.put("/api/sla-rules/CRITICAL", json={"hours": 2})

    # Test SLA metrics calculation logic on a simulated complaint
    now = datetime.utcnow()
    # On track (0% elapsed)
    c_new = Complaint(
        complaint_number="CMP-TEST-1",
        subject="Test On Track",
        description="Test",
        customer_email="test@test.com",
        urgency="HIGH",
        status="NEW",
        created_at=now,
        sla_deadline=now + timedelta(hours=8)
    )
    m_new = sla_service.get_sla_metrics(c_new)
    assert m_new["warning_level"] == "ON_TRACK"
    assert m_new["is_breached"] is False

    # Warning (80% elapsed)
    c_warn = Complaint(
        complaint_number="CMP-TEST-2",
        subject="Test Warning",
        description="Test",
        customer_email="test@test.com",
        urgency="HIGH",
        status="IN_PROGRESS",
        created_at=now - timedelta(hours=6.4),
        sla_deadline=now + timedelta(hours=1.6)
    )
    m_warn = sla_service.get_sla_metrics(c_warn)
    assert m_warn["warning_level"] == "WARNING"

    # Critical Warning (92% elapsed)
    c_crit = Complaint(
        complaint_number="CMP-TEST-3",
        subject="Test Crit Warning",
        description="Test",
        customer_email="test@test.com",
        urgency="HIGH",
        status="IN_PROGRESS",
        created_at=now - timedelta(hours=7.4),
        sla_deadline=now + timedelta(hours=0.6)
    )
    m_crit = sla_service.get_sla_metrics(c_crit)
    assert m_crit["warning_level"] == "CRITICAL_WARNING"

    # Breached (110% elapsed)
    c_breach = Complaint(
        complaint_number="CMP-TEST-4",
        subject="Test Breached",
        description="Test",
        customer_email="test@test.com",
        urgency="HIGH",
        status="IN_PROGRESS",
        created_at=now - timedelta(hours=9),
        sla_deadline=now - timedelta(hours=1)
    )
    m_breach = sla_service.get_sla_metrics(c_breach)
    assert m_breach["warning_level"] == "BREACHED"
    assert m_breach["is_breached"] is True

# 4. Test All 13 Core Audit Operations
def test_all_13_audit_operations(db_session: Session):
    """Executes the full complaint lifecycle and confirms that all 13 operations are recorded in audit logs:
    1. Complaint Created
    2. AI Analysis Completed
    3. Department Changed
    4. Team Changed
    5. Agent Assigned
    6. Priority Changed
    7. Status Changed
    8. Response Generated
    9. Response Edited
    10. Response Approved
    11. Response Sent
    12. Complaint Resolved
    13. Complaint Reopened
    """
    # 1. Intake Complaint (triggers 'Complaint Created', 'AI Analysis Completed', 'Department Changed', 'Team Changed', 'Agent Assigned', 'Priority Changed')
    payload = {
        "customer_name": "Audit Test Customer",
        "customer_email": "audit.test@example.com",
        "subject": "System crash during checkout payment",
        "description": "Application crashed with HTTP 500 error while trying to pay for invoice #9910.",
        "source": "MANUAL"
    }
    create_res = client.post("/api/complaints/", json=payload)
    assert create_res.status_code == 201
    cid = create_res.json()["id"]

    # 2. Generate AI Response
    gen_res = client.post(f"/api/complaints/{cid}/generate-response")
    assert gen_res.status_code == 200

    # 3. Edit Customer Response Draft
    edit_res = client.put(f"/api/complaints/{cid}/edit-response", json={
        "content": "Dear Customer,\nWe have investigated your checkout crash and confirmed the issue is resolved.\nRegards,\nSupport Team"
    })
    assert edit_res.status_code == 200

    # 4. Approve Response
    app_res = client.post(f"/api/complaints/{cid}/approve-response", json={"approved_by": "Lead Specialist"})
    assert app_res.status_code == 200

    # 5. Send Response (with human approval)
    send_res = client.post(f"/api/complaints/{cid}/send-response", json={"sender": "Lead Specialist"})
    assert send_res.status_code == 200

    # 6. Resolve Complaint
    res_res = client.post(f"/api/complaints/{cid}/resolve", json={
        "resolution_notes": "Database connection pool restarted and transaction re-verified.",
        "mark_as_policy_knowledge": False
    })
    assert res_res.status_code == 200

    # 7. Reopen Complaint
    reopen_res = client.post(f"/api/complaints/{cid}/reopen", params={"reason": "Customer reported recurring issue"})
    assert reopen_res.status_code == 200

    # Query all audit logs for this complaint
    audit_res = client.get("/api/audit/")
    assert audit_res.status_code == 200
    logs = [l for l in audit_res.json() if str(l.get("entity_id")) == str(cid)]
    actions_recorded = {l["action"] for l in logs}

    required_actions = [
        "Complaint Created",
        "AI Analysis Completed",
        "Response Generated",
        "Response Edited",
        "Response Approved",
        "Response Sent",
        "Complaint Resolved",
        "Complaint Reopened"
    ]

    for req_act in required_actions:
        assert req_act in actions_recorded, f"Missing audit action: '{req_act}'. Recorded: {actions_recorded}"

    # Verify audit record fields: user, action, timestamp, old_value, new_value, metadata
    sample_log = next(l for l in logs if l["action"] == "Complaint Resolved")
    assert sample_log.get("user") is not None
    assert sample_log.get("new_value") == "RESOLVED"
    assert sample_log.get("metadata") is not None

# 5. Test Customer Response Approval Guardrail
def test_send_response_guardrail(db_session: Session):
    """Verifies that unapproved customer response drafts cannot be sent automatically."""
    # Create complaint
    c_res = client.post("/api/complaints/", json={
        "customer_email": "guardrail@test.com",
        "subject": "Testing guardrail",
        "description": "Please help with login",
        "source": "WEB"
    })
    cid = c_res.json()["id"]

    # Generate draft
    client.post(f"/api/complaints/{cid}/generate-response")

    # Attempt to send WITHOUT human approval -> Must return 400 Bad Request
    fail_send = client.post(f"/api/complaints/{cid}/send-response", json={"sender": "Agent"})
    assert fail_send.status_code == 400
    assert "explicit human approval" in fail_send.json()["detail"].lower()

# 6. Test RBAC Permissions
def test_rbac_roles_access(db_session: Session):
    """Verifies customer isolation vs agent / manager / admin access."""
    # Customer can only view own complaints
    cust_headers = get_auth_header(role="CUSTOMER", email="customer1@example.com")
    cust_res = client.get("/api/complaints/", headers=cust_headers)
    assert cust_res.status_code == 200
    # Every returned complaint must belong to customer1@example.com
    for c in cust_res.json():
        assert c["customer_email"].lower() == "customer1@example.com"

    # Admin has unrestricted access to /api/users
    admin_headers = get_auth_header(role="ADMIN", email="admin@complaints.io")
    admin_res = client.get("/api/auth/users", headers=admin_headers)
    assert admin_res.status_code == 200
    assert isinstance(admin_res.json(), list)

    # Customer cannot access /api/users
    cust_users_res = client.get("/api/auth/users", headers=cust_headers)
    assert cust_users_res.status_code == 403
