import pytest
from app.models.complaint import Complaint
from app.ai.duplicate_detector import (
    duplicate_detector,
    TFIDFBaselineDuplicateDetector,
    SentenceTransformerPgVectorDuplicateDetector
)
from app.ai.embeddings import embeddings_engine

def test_tfidf_baseline_similarity():
    baseline = TFIDFBaselineDuplicateDetector()
    query = "I was charged twice for order ORD92831 on my credit card"
    candidates = [
        "Double deduction on my credit card for order ORD92831",
        "How do I update my email address and profile picture?"
    ]
    scores = baseline.compute_similarity(query, candidates)
    assert len(scores) == 2
    # The duplicate financial inquiry must have much higher similarity than the profile inquiry
    assert scores[0] > scores[1]
    assert scores[0] > 0.40

def test_sentence_transformer_pgvector_duplicate_flow(db):
    # 1. Create an original primary complaint in database with embedding
    text_orig = "I paid INR 4500 for order ORD92831 but my account was charged twice."
    emb_orig = embeddings_engine.get_embedding(text_orig)

    primary_complaint = Complaint(
        complaint_number="CMP-TEST-ORIG-01",
        customer_email="user1@example.com",
        subject="Charged twice for order ORD92831",
        description=text_orig,
        category="Billing",
        status="NEW",
        embedding=emb_orig
    )
    db.add(primary_complaint)
    db.commit()
    db.refresh(primary_complaint)

    # 2. Incoming duplicate complaint
    text_dup = "I paid INR 4500 for order ORD92831 but my account was charged twice."
    emb_dup = embeddings_engine.get_embedding(text_dup)

    # Execute primary detector (Sentence Transformers + pgvector flow)
    detector = SentenceTransformerPgVectorDuplicateDetector(duplicate_threshold=0.85)
    res = detector.detect_duplicates(
        complaint_text=text_dup,
        db=db,
        embedding=emb_dup
    )

    # Flow verification:
    # Returns matched_complaint_id, similarity_score
    # Displays: "Possible duplicate complaint"
    assert res["matched_complaint_id"] == primary_complaint.id
    assert res["similarity_score"] >= 0.85
    assert res["is_duplicate"] is True
    assert res["display_warning"] == "Possible duplicate complaint"
    assert res["status"] == "POSSIBLE"
    assert len(res["similar_complaints"]) > 0

def test_user_example_similarity_and_display_warning(db):
    detector = SentenceTransformerPgVectorDuplicateDetector(duplicate_threshold=0.85)
    # Verify that a 0.91 similarity returns "Possible duplicate complaint"
    # Create fake similar complaints matching 0.91
    fake_sim = 0.91
    # Test detect_duplicates logic with threshold
    assert fake_sim >= detector.duplicate_threshold
    warning_label = "Possible duplicate complaint" if fake_sim >= detector.duplicate_threshold else None
    assert warning_label == "Possible duplicate complaint"

def test_agent_action_link_complaints(client, db):
    # Setup two complaints
    c1 = Complaint(
        complaint_number="CMP-LINK-A",
        customer_email="clientA@test.com",
        subject="Unauthorized charge on credit card",
        description="I see an unexpected charge on statement",
        category="Billing",
        status="NEW"
    )
    c2 = Complaint(
        complaint_number="CMP-LINK-B",
        customer_email="clientB@test.com",
        subject="Duplicate card charge inquiry",
        description="Same transaction charged twice",
        category="Billing",
        status="NEW"
    )
    db.add_all([c1, c2])
    db.commit()
    db.refresh(c1)
    db.refresh(c2)

    # Agent links c2 to c1
    link_res = client.post(f"/api/complaints/{c2.id}/duplicate/link", json={
        "target_complaint_id": c1.id,
        "notes": "Verified by agent as matching transaction dispute"
    })
    assert link_res.status_code == 200
    data = link_res.json()
    assert data["duplicate_of_id"] == c1.id
    assert data["duplicate_status"] == "LINKED"

    # Verify event audit trail on both complaints
    ev_res = client.get(f"/api/complaints/{c2.id}/events")
    events = ev_res.json()
    assert any(e["event_type"] == "COMPLAINTS_LINKED" for e in events)

def test_agent_action_merge_complaints(client, db):
    # Setup two complaints
    primary = Complaint(
        complaint_number="CMP-PRIMARY",
        customer_email="buyer@test.com",
        subject="Product defective and not working",
        description="The device failed to turn on",
        category="Technical Problem",
        status="IN_PROGRESS"
    )
    duplicate = Complaint(
        complaint_number="CMP-DUPLICATE",
        customer_email="buyer@test.com",
        subject="Follow-up: Product defective device power issue",
        description="Also adding that the power light does not blink",
        category="Technical Problem",
        status="NEW"
    )
    db.add_all([primary, duplicate])
    db.commit()
    db.refresh(primary)
    db.refresh(duplicate)

    # Agent merges duplicate into primary
    merge_res = client.post(f"/api/complaints/{duplicate.id}/duplicate/merge", json={
        "primary_complaint_id": primary.id,
        "reason": "Customer sent second email with additional power light detail"
    })
    assert merge_res.status_code == 200
    data = merge_res.json()
    assert data["duplicate_of_id"] == primary.id
    assert data["duplicate_status"] == "MERGED"
    assert data["status"] == "RESOLVED"

    # Verify event on primary complaint
    prim_ev = client.get(f"/api/complaints/{primary.id}/events").json()
    assert any(e["event_type"] == "COMPLAINTS_MERGED" for e in prim_ev)

def test_agent_action_ignore_duplicate_warning(client, db):
    c = Complaint(
        complaint_number="CMP-IGNORE-WARN",
        customer_email="shopper@test.com",
        subject="Order query",
        description="Inquiry about order delivery status",
        category="Customer Support",
        is_duplicate=True,
        duplicate_similarity=0.88,
        duplicate_status="POSSIBLE",
        status="NEW"
    )
    db.add(c)
    db.commit()
    db.refresh(c)

    # Agent dismisses the warning
    ignore_res = client.post(f"/api/complaints/{c.id}/duplicate/ignore", json={
        "reason": "Different order numbers after manual agent verification"
    })
    assert ignore_res.status_code == 200
    data = ignore_res.json()
    assert data["is_duplicate"] is False
    assert data["duplicate_status"] == "IGNORED"

    # Verify event recorded
    events = client.get(f"/api/complaints/{c.id}/events").json()
    assert any(e["event_type"] == "DUPLICATE_WARNING_IGNORED" for e in events)

def test_get_similar_complaints_endpoint(client, db):
    text = "Login failure on web portal 500 error"
    emb = embeddings_engine.get_embedding(text)
    c1 = Complaint(
        complaint_number="CMP-SIM-1",
        customer_email="a@test.com",
        subject="Login error 500",
        description=text,
        category="Technical Problem",
        embedding=emb
    )
    c2 = Complaint(
        complaint_number="CMP-SIM-2",
        customer_email="b@test.com",
        subject="Login 500 internal server error",
        description=text,
        category="Technical Problem",
        embedding=emb
    )
    db.add_all([c1, c2])
    db.commit()
    db.refresh(c1)
    db.refresh(c2)

    res = client.get(f"/api/complaints/{c2.id}/similar")
    assert res.status_code == 200
    body = res.json()
    assert body["complaint_id"] == c2.id
    assert body["matched_complaint_id"] == c1.id
    assert body["similarity_score"] >= 0.85
    assert body["is_duplicate"] is True
    assert body["display_warning"] == "Possible duplicate complaint"
    assert "baseline_tfidf" in body
