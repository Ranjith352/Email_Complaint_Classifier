def test_complete_complaint_lifecycle(client):
    # 1. Intake Complaint: NEW -> AI_ANALYZING -> AI_ANALYZED -> ROUTED -> ASSIGNED
    create_res = client.post("/api/complaints/", json={
        "subject": "Double charged on credit card for invoice INV-88910",
        "description": "I was charged twice $199.00 on my bank statement on March 2nd. Please refund my payment immediately.",
        "customer_email": "sarah.connor@example.com",
        "customer_name": "Sarah Connor",
        "source": "WEB"
    })
    assert create_res.status_code == 201
    c_data = create_res.json()
    c_id = c_data["id"]
    assert c_data["complaint_number"].startswith("CMP-")
    assert c_data["status"] in ("ROUTED", "ASSIGNED")

    # Fetch initial events
    events_res = client.get(f"/api/complaints/{c_id}/events")
    assert events_res.status_code == 200
    events = events_res.json()
    event_descriptions = [e["description"] for e in events]

    assert any("Complaint received" in d for d in event_descriptions)
    assert any("AI analysis started" in d for d in event_descriptions)
    assert any("AI analysis completed" in d for d in event_descriptions)
    assert any("Routed to" in d for d in event_descriptions)

    # 2. Agent starts investigation -> IN_PROGRESS
    inv_res = client.post(f"/api/complaints/{c_id}/start-investigation", params={"actor": "Agent A"})
    assert inv_res.status_code == 200
    assert inv_res.json()["complaint"]["status"] == "IN_PROGRESS"

    # 3. Waiting for customer -> WAITING_FOR_CUSTOMER
    wait_res = client.post(f"/api/complaints/{c_id}/waiting-customer", params={"actor": "Agent A", "notes": "Waiting for bank statement copy"})
    assert wait_res.status_code == 200
    assert wait_res.json()["complaint"]["status"] == "WAITING_FOR_CUSTOMER"

    # 4. Escalation -> ESCALATED
    esc_res = client.post(f"/api/complaints/{c_id}/escalate", json={"reason": "Payment gateway discrepancy", "actor": "Agent A"})
    assert esc_res.status_code == 200
    assert esc_res.json()["complaint"]["status"] == "ESCALATED"
    assert esc_res.json()["complaint"]["is_escalated"] is True

    # 5. Resolution completed -> RESOLVED
    res_res = client.post(f"/api/complaints/{c_id}/resolve", json={
        "resolution_notes": "Issued $199.00 credit reversal to card ending 4012.",
        "mark_as_policy_knowledge": True,
        "actor": "Agent A"
    })
    assert res_res.status_code == 200
    assert res_res.json()["complaint"]["status"] == "RESOLVED"

    # 6. Customer response approved
    details_res = client.get(f"/api/complaints/{c_id}")
    ai_responses = details_res.json()["ai_responses"]
    if ai_responses:
        resp_id = ai_responses[0]["id"]
        app_res = client.post(f"/api/complaints/{c_id}/approve-response", params={"response_id": resp_id, "approved_by": "Lead Supervisor"})
        assert app_res.status_code == 200

    # 7. Customer response sent
    send_res = client.post(f"/api/complaints/{c_id}/send-response", json={"sender": "Lead Supervisor"})
    assert send_res.status_code == 200

    # 8. Complaint closed -> CLOSED
    close_res = client.post(f"/api/complaints/{c_id}/close", params={"actor": "Lead Supervisor", "notes": "Complaint closed"})
    assert close_res.status_code == 200
    assert close_res.json()["complaint"]["status"] == "CLOSED"

    # 9. Verify full chronological timeline
    timeline_res = client.get(f"/api/complaints/{c_id}/events")
    assert timeline_res.status_code == 200
    timeline = timeline_res.json()
    final_descriptions = [e["description"] for e in timeline]

    assert any("Complaint received" in d for d in final_descriptions)
    assert any("AI analysis started" in d for d in final_descriptions)
    assert any("AI analysis completed" in d for d in final_descriptions)
    assert any("Agent started investigation" in d for d in final_descriptions)
    assert any("Resolution completed" in d for d in final_descriptions)
    assert any("Customer response approved" in d for d in final_descriptions)
    assert any("Customer response sent" in d for d in final_descriptions)
    assert any("Complaint closed" in d for d in final_descriptions)
