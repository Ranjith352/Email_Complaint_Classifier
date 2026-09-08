import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.complaint import Complaint
from app.models.intelligence import AIResponse

def test_generate_ai_customer_response_standard_format(client: TestClient):
    """Verifies that an agent can click 'Generate AI Response' and receive
    a professional customer response with Complaint ID and Customer Support Team sign-off.
    """
    # 1. Create complaint
    create_res = client.post(
        "/api/complaints/",
        json={
            "customer_name": "Rohan Sharma",
            "customer_email": "rohan@example.com",
            "subject": "Duplicate payment deduction",
            "description": "Money was deducted twice for my subscription payment of Rs 5000.",
            "source": "WEB"
        }
    )
    assert create_res.status_code == 201
    c_id = create_res.json()["id"]
    ticket_no = create_res.json()["complaint_number"]

    # 2. Click Generate AI Response
    gen_res = client.post(f"/api/complaints/{c_id}/generate-response", json={"tone": "Empathetic & Professional"})
    assert gen_res.status_code == 200
    gen_data = gen_res.json()
    resp = gen_data["response"]

    assert resp["is_approved"] is False
    assert resp["is_sent"] is False
    assert f"Complaint ID: {ticket_no}" in resp["content"]
    assert "Customer Support Team" in resp["content"]
    assert "duplicate payment" in resp["content"].lower()

def test_response_workflow_generate_edit_approve_send(client: TestClient, db: Session):
    """Verifies the complete 4-step workflow:
    1. Generate
    2. Edit
    3. Approve
    4. Send
    Strictly enforcing that unapproved responses CANNOT be sent.
    """
    # Step 1: Create complaint & Generate
    create_res = client.post(
        "/api/complaints/",
        json={
            "customer_name": "Ananya Patel",
            "customer_email": "ananya@example.com",
            "subject": "Portal authentication login failure",
            "description": "I cannot login to the customer portal to access my statements.",
            "source": "WEB"
        }
    )
    assert create_res.status_code == 201
    c_id = create_res.json()["id"]
    ticket_no = create_res.json()["complaint_number"]

    gen_res = client.post(f"/api/complaints/{c_id}/generate-response")
    assert gen_res.status_code == 200
    resp_id = gen_res.json()["response"]["id"]
    assert gen_res.json()["response"]["is_approved"] is False

    # Attempt to Send WITHOUT approval -> MUST FAIL (HTTP 400)
    unapproved_send = client.post(
        f"/api/complaints/{c_id}/send-response",
        json={"response_id": resp_id, "sender": "Agent Priya"}
    )
    assert unapproved_send.status_code == 400
    assert "explicit human approval" in unapproved_send.json()["detail"].lower()

    # Step 2: Edit Response
    custom_content = (
        f"Dear Ananya Patel,\n\n"
        f"We have reviewed your complaint regarding the portal access issue. "
        f"Our IT team has reset your session credentials. Please attempt login now.\n\n"
        f"Complaint ID: {ticket_no}\n\n"
        f"Regards,\n"
        f"Customer Support Team"
    )
    edit_res = client.put(
        f"/api/complaints/{c_id}/edit-response",
        json={"response_id": resp_id, "content": custom_content}
    )
    assert edit_res.status_code == 200
    edited_data = edit_res.json()["response"]
    assert edited_data["content"] == custom_content
    assert edited_data["is_approved"] is False

    # Still cannot send because it was edited and not approved
    send_after_edit_fail = client.post(
        f"/api/complaints/{c_id}/send-response",
        json={"response_id": resp_id, "sender": "Agent Priya"}
    )
    assert send_after_edit_fail.status_code == 400

    # Step 3: Approve Response
    approve_res = client.post(
        f"/api/complaints/{c_id}/approve-response",
        json={"response_id": resp_id, "approved_by": "Senior Agent Priya"}
    )
    assert approve_res.status_code == 200
    approved_data = approve_res.json()["response"]
    assert approved_data["is_approved"] is True
    assert approved_data["approved_by"] == "Senior Agent Priya"
    assert approved_data["approved_at"] is not None

    # Step 4: Send Response (Now allowed after explicit approval)
    send_res = client.post(
        f"/api/complaints/{c_id}/send-response",
        json={"response_id": resp_id, "sender": "Senior Agent Priya"}
    )
    assert send_res.status_code == 200
    sent_data = send_res.json()
    assert sent_data["message"] == "Customer response successfully sent"
    assert sent_data["response"]["is_sent"] is True

    # Verify event timeline contains RESPONSE_APPROVED and RESPONSE_SENT
    events_res = client.get(f"/api/complaints/{c_id}/events")
    assert events_res.status_code == 200
    events = events_res.json()
    event_types = [e["event_type"] for e in events]
    assert "RESPONSE_APPROVED" in event_types
    assert "RESPONSE_SENT" in event_types

def test_editing_approved_response_resets_approval(client: TestClient):
    """Verifies that editing an already-approved draft automatically resets approval
    status so modifications cannot be sent without human re-approval.
    """
    create_res = client.post(
        "/api/complaints/",
        json={
            "customer_name": "Vikram Seth",
            "customer_email": "vikram@example.com",
            "subject": "Delayed delivery of product",
            "description": "My courier package has not arrived after 10 days.",
            "source": "WEB"
        }
    )
    c_id = create_res.json()["id"]

    # 1. Generate
    client.post(f"/api/complaints/{c_id}/generate-response")

    # 2. Approve
    app_res = client.post(f"/api/complaints/{c_id}/approve-response", json={"approved_by": "Agent Rahul"})
    assert app_res.status_code == 200
    resp_id = app_res.json()["response"]["id"]
    assert app_res.json()["response"]["is_approved"] is True

    # 3. Edit response
    edit_res = client.put(
        f"/api/complaints/{c_id}/edit-response",
        json={"response_id": resp_id, "content": "Modified text..."}
    )
    assert edit_res.status_code == 200
    assert edit_res.json()["response"]["is_approved"] is False  # Must be reset!

    # 4. Attempt to send -> Must fail because approval was reset
    send_res = client.post(f"/api/complaints/{c_id}/send-response", json={"response_id": resp_id})
    assert send_res.status_code == 400
    assert "explicit human approval" in send_res.json()["detail"].lower()

def test_never_auto_send_on_ingestion(client: TestClient, db: Session):
    """Verifies that when a complaint is initially created, all generated drafts
    remain unapproved (is_approved=False) and unsent (is_sent=False).
    """
    create_res = client.post(
        "/api/complaints/",
        json={
            "customer_name": "Test Customer",
            "customer_email": "test@example.com",
            "subject": "Billing issue",
            "description": "Charged twice on card.",
            "source": "WEB"
        }
    )
    c_id = create_res.json()["id"]

    details_res = client.get(f"/api/complaints/{c_id}")
    draft = next(
        (r for r in details_res.json()["ai_responses"] if r["response_type"] == "DRAFT_REPLY"),
        None
    )
    assert draft is not None
    assert draft["is_approved"] is False
    assert draft.get("is_sent", False) is False
