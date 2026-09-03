def test_create_and_route_complaint(client):
    payload = {
        "subject": "Double charged on credit card for invoice INV-88910",
        "description": "I was charged twice $199.00 on my bank statement on March 2nd. Please refund my payment immediately.",
        "customer_email": "customer@example.com",
        "customer_name": "Jane Doe",
        "source": "WEB"
    }
    res = client.post("/api/complaints/", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["complaint_number"].startswith("CMP-")
    assert data["category"] in ("Billing", "Billing / Payment")
    assert data["source"] == "WEB"
    assert data["urgency"].upper() in ("CRITICAL", "HIGH")
    assert data["priority"].upper() in ("CRITICAL", "HIGH", "P1", "P2", "P3", "P4")
    assert data["status"].upper() in ("NEW", "ROUTED", "ASSIGNED")
    assert "ai_confidence" in data
    assert "review_required" in data
    assert "ai_status" in data
    assert "summary" in data

def test_list_complaints(client):
    res = client.get("/api/complaints/")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1

def test_resolve_complaint(client):
    # Create first
    create_res = client.post("/api/complaints/", json={
        "subject": "Damaged package delivered",
        "description": "The box was torn open and items are missing #ORD-4491.",
        "customer_email": "buyer@test.com",
        "source": "WEB"
    })
    c_id = create_res.json()["id"]

    # Resolve
    resolve_res = client.post(f"/api/complaints/{c_id}/resolve", json={
        "resolution_notes": "Shipped replacement with priority tracking #EXP-9921.",
        "mark_as_policy_knowledge": True
    })
    assert resolve_res.status_code == 200
    assert resolve_res.json()["complaint"]["status"].upper() == "RESOLVED"

def test_feedback_submission(client):
    create_res = client.post("/api/complaints/", json={
        "subject": "Login error on portal",
        "description": "Getting timeout 500 error when clicking submit.",
        "customer_email": "user@portal.com",
        "source": "WEB"
    })
    c_id = create_res.json()["id"]

    fb_res = client.post(f"/api/complaints/{c_id}/feedback", json={
        "is_category_correct": True,
        "is_sentiment_correct": True,
        "rating": 5,
        "notes": "Accurately routed to IT."
    })
    assert fb_res.status_code == 200
    assert fb_res.json()["rating"] == 5
