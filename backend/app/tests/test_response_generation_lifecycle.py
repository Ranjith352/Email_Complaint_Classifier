import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.complaint import Complaint
from app.models.intelligence import AIResponse
from app.models.organization import Department
from app.ai.response_generator import response_generator

@pytest.mark.asyncio
async def test_generate_response_draft_format():
    """Verifies that response_generator produces the exact professional customer response:
    Dear Customer,
    We have reviewed your complaint regarding the duplicate payment. Our Finance team is currently verifying the transaction and will process the necessary refund if the duplicate transaction is confirmed.
    Complaint ID: CMP-10001
    Regards,
    Customer Support Team
    """
    res = await response_generator.generate_draft(
        ticket_number="CMP-10001",
        customer_name="",
        subject="Duplicate deduction on credit card",
        body="I was charged twice on my card for subscription. Please refund duplicate charge.",
        department="Finance"
    )

    body = res["body"]
    assert "Dear Customer," in body
    assert "duplicate payment" in body.lower()
    assert "Finance team" in body
    assert "verifying the transaction and will process the necessary refund if the duplicate transaction is confirmed" in body
    assert "Complaint ID: CMP-10001" in body
    assert "Regards," in body
    assert "Customer Support Team" in body
    assert res["requires_approval"] is True
    assert res["is_approved"] is False
    assert res["is_sent"] is False

@pytest.mark.asyncio
async def test_response_lifecycle_generate_edit_approve_send(client: TestClient, db: Session):
    """Verifies full human-in-the-loop lifecycle:
    1. Generate AI Response
    2. Edit Draft (resets approval)
    3. Send blocked without explicit approval
    4. Approve response
    5. Send response successfully
    """
    # Create test complaint
    dept = db.query(Department).filter(Department.name == "Finance").first()
    if not dept:
        dept = Department(name="Finance", code="FIN", is_active=True)
        db.add(dept)
        db.commit()

    comp = db.query(Complaint).filter(Complaint.complaint_number == "CMP-10001").first()
    if not comp:
        comp = Complaint(
            complaint_number="CMP-10001",
            customer_name="Customer",
            customer_email="user@example.com",
            subject="Duplicate deduction on credit card",
            description="Double deduction occurred on my statement.",
            category="Billing / Payment",
            department_id=dept.id,
            urgency="High",
            priority="P2",
            status="NEW"
        )
        db.add(comp)
        db.commit()
        db.refresh(comp)

    # 1. Generate AI Response via API
    gen_res = client.post(f"/api/complaints/{comp.id}/generate-response")
    assert gen_res.status_code == 200
    gen_data = gen_res.json()
    assert "response" in gen_data
    resp_obj = gen_data["response"]
    assert resp_obj["is_approved"] is False
    assert resp_obj["is_sent"] is False
    assert ("Dear Customer," in resp_obj["content"] or f"Dear {comp.customer_name}," in resp_obj["content"])
    assert "Complaint ID: CMP-10001" in resp_obj["content"]

    resp_id = resp_obj["id"]

    # 2. Strict Policy: Try to send without approval -> MUST FAIL
    send_fail_res = client.post(
        f"/api/complaints/{comp.id}/send-response",
        json={"response_id": resp_id, "sender": "Agent Smith"}
    )
    assert send_fail_res.status_code == 400
    assert "explicit human approval" in send_fail_res.json()["detail"].lower()

    # 3. Edit Draft
    edited_text = (
        "Dear Customer,\n\n"
        "We have reviewed your complaint regarding the duplicate payment. Our Finance team is currently verifying the transaction and will process the necessary refund if the duplicate transaction is confirmed.\n\n"
        "Complaint ID: CMP-10001\n\n"
        "Regards,\n"
        "Customer Support Team"
    )
    edit_res = client.put(
        f"/api/complaints/{comp.id}/edit-response",
        json={"response_id": resp_id, "content": edited_text}
    )
    assert edit_res.status_code == 200
    edit_data = edit_res.json()
    assert edit_data["response"]["content"] == edited_text
    assert edit_data["response"]["is_approved"] is False  # Editing resets approval

    # Try to send again without re-approval -> MUST STILL FAIL
    send_fail_res2 = client.post(
        f"/api/complaints/{comp.id}/send-response",
        json={"response_id": resp_id, "sender": "Agent Smith"}
    )
    assert send_fail_res2.status_code == 400

    # 4. Explicit Human Approval
    approve_res = client.post(
        f"/api/complaints/{comp.id}/approve-response",
        json={"response_id": resp_id, "approved_by": "Senior Support Lead"}
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["response"]["is_approved"] is True
    assert approve_res.json()["response"]["approved_by"] == "Senior Support Lead"

    # 5. Send with Explicit Approval -> MUST SUCCEED
    send_success_res = client.post(
        f"/api/complaints/{comp.id}/send-response",
        json={"response_id": resp_id, "sender": "Senior Support Lead"}
    )
    assert send_success_res.status_code == 200
    assert send_success_res.json()["response"]["is_sent"] is True
    assert send_success_res.json()["response"]["sent_by"] == "Senior Support Lead"
