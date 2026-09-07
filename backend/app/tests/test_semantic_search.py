import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.complaint import Complaint
from app.ai.embeddings import embeddings_engine
from app.services.semantic_search_service import semantic_search_service

def test_semantic_embedding_cosine_similarity():
    """Verifies that dense embeddings bridge the lexical gap between:
    'Money was deducted twice.' and 'I was charged two times for the same transaction.'
    """
    text1 = "Money was deducted twice."
    text2 = "I was charged two times for the same transaction."
    text_unrelated = "Company holiday calendar approval for annual leave."

    emb1 = embeddings_engine.get_embedding(text1)
    emb2 = embeddings_engine.get_embedding(text2)
    emb_unrelated = embeddings_engine.get_embedding(text_unrelated)

    sim_synonym = embeddings_engine.cosine_similarity(emb1, emb2)
    sim_unrelated = embeddings_engine.cosine_similarity(emb1, emb_unrelated)

    assert sim_synonym >= 0.85, f"Expected high semantic similarity for double deduction, got {sim_synonym}"
    assert sim_unrelated < 0.20, f"Expected low similarity for unrelated text, got {sim_unrelated}"

def test_semantic_search_service_retrieval(db: Session):
    """Verifies semantic_search_service finds 'I was charged two times for the same transaction.'
    when searched with 'Money was deducted twice.'
    """
    target_text = "I was charged two times for the same transaction."
    target_emb = embeddings_engine.get_embedding(target_text)

    c_target = Complaint(
        complaint_number="CMP-SEM-1",
        customer_email="customer1@domain.com",
        subject="Payment problem on card",
        description=target_text,
        category="Billing",
        status="NEW",
        embedding=target_emb
    )
    c_other = Complaint(
        complaint_number="CMP-SEM-2",
        customer_email="customer2@domain.com",
        subject="Office temperature issue",
        description="The AC in building 4 is too cold today.",
        category="Facilities",
        status="NEW",
        embedding=embeddings_engine.get_embedding("The AC in building 4 is too cold today.")
    )

    db.add_all([c_target, c_other])
    db.commit()
    db.refresh(c_target)
    db.refresh(c_other)

    results = semantic_search_service.search_complaints(
        db=db,
        query_text="Money was deducted twice.",
        limit=5,
        threshold=0.50
    )

    assert len(results) >= 1
    assert any(r["id"] == c_target.id for r in results)
    target_hit = next(r for r in results if r["id"] == c_target.id)
    assert target_hit["similarity_score"] >= 0.85
    # The AC complaint should not be in the results or scored below threshold
    assert not any(r["id"] == c_other.id for r in results)

def test_find_complaints_similar_to_this_one(db: Session):
    """Verifies 'Find complaints similar to this one' retrieves conceptually similar complaints
    while excluding the source complaint.
    """
    c_source = Complaint(
        complaint_number="CMP-SOURCE-1",
        customer_email="user_a@bank.com",
        subject="Card charge glitch",
        description="Money was deducted twice.",
        category="Billing",
        status="OPEN"
    )
    c_target = Complaint(
        complaint_number="CMP-SIMILAR-1",
        customer_email="user_b@bank.com",
        subject="Double debit notification",
        description="I was charged two times for the same transaction.",
        category="Billing",
        status="IN_PROGRESS"
    )
    db.add_all([c_source, c_target])
    db.commit()
    db.refresh(c_source)
    db.refresh(c_target)

    similar = semantic_search_service.find_similar_to_complaint(
        db=db,
        complaint_id=c_source.id,
        limit=5,
        threshold=0.50
    )

    # Source complaint should be excluded
    matched_ids = [s["id"] for s in similar]
    assert c_source.id not in matched_ids
    assert c_target.id in matched_ids
    assert similar[0]["similarity_score"] >= 0.85

def test_semantic_search_api_endpoint(client: TestClient, db: Session):
    """Test GET /api/complaints/semantic-search HTTP endpoint."""
    text_desc = "I was charged two times for the same transaction."
    c = Complaint(
        complaint_number="CMP-API-SEM-1",
        customer_email="api_user@test.com",
        subject="Duplicate fee issue",
        description=text_desc,
        category="Billing",
        status="NEW",
        embedding=embeddings_engine.get_embedding(text_desc)
    )
    db.add(c)
    db.commit()
    db.refresh(c)

    res = client.get("/api/complaints/semantic-search", params={"query": "Money was deducted twice."})
    assert res.status_code == 200
    data = res.json()
    assert data["total_results"] >= 1
    assert any(item["id"] == c.id for item in data["results"])
    hit = next(item for item in data["results"] if item["id"] == c.id)
    assert hit["similarity_score"] >= 0.85

def test_find_similar_api_endpoint(client: TestClient, db: Session):
    """Test GET /api/complaints/{complaint_id}/find-similar HTTP endpoint."""
    c1 = Complaint(
        complaint_number="CMP-FIND-1",
        customer_email="u1@test.com",
        subject="Debit issue",
        description="Money was deducted twice.",
        category="Billing"
    )
    c2 = Complaint(
        complaint_number="CMP-FIND-2",
        customer_email="u2@test.com",
        subject="Billing mistake",
        description="I was charged two times for the same transaction.",
        category="Billing"
    )
    db.add_all([c1, c2])
    db.commit()
    db.refresh(c1)
    db.refresh(c2)

    res = client.get(f"/api/complaints/{c1.id}/find-similar")
    assert res.status_code == 200
    data = res.json()
    assert data["total_results"] >= 1
    matches = [r["id"] for r in data["results"]]
    assert c1.id not in matches
    assert c2.id in matches
