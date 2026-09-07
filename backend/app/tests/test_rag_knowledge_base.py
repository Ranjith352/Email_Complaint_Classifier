import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.knowledge import KnowledgeDocument, KnowledgeChunk
from app.services.knowledge_service import knowledge_service, SUPPORTED_DOCUMENT_TYPES
from app.schemas.knowledge import RAGQueryRequest

EXPECTED_9_TYPES = [
    "REFUND_POLICY",
    "BILLING_POLICY",
    "CUSTOMER_SUPPORT_SOP",
    "SLA_POLICY",
    "ESCALATION_POLICY",
    "IT_TROUBLESHOOTING_GUIDE",
    "SECURITY_POLICY",
    "HR_POLICY",
    "FINANCE_POLICY"
]

def test_seed_9_supported_document_types(db: Session):
    """Verifies that all 9 officially supported enterprise document types
    can be seeded into the knowledge base with granular chunks and 384d vectors.
    """
    count = knowledge_service.seed_default_knowledge_base(db)
    docs = db.query(KnowledgeDocument).all()
    assert len(docs) >= 9

    doc_types = {d.document_type for d in docs}
    for expected_type in EXPECTED_9_TYPES:
        assert expected_type in doc_types, f"Missing expected document type: {expected_type}"

    # Verify each seeded document has 384-d embedding and granular chunks
    for expected_type in EXPECTED_9_TYPES:
        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.document_type == expected_type).first()
        assert doc is not None
        assert doc.embedding is not None
        assert len(doc.embedding) == 384
        assert doc.content_text is not None and len(doc.content_text) > 100
        chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == doc.id).all()
        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk.embedding is not None
            assert len(chunk.embedding) == 384
            assert len(chunk.chunk_text) > 0

def test_rag_ingestion_pipeline_upload(db: Session, client: TestClient):
    """Tests the complete 9-stage ingestion pipeline:
    Document Upload -> Text Extraction -> Cleaning -> Chunking -> Sentence Transformer -> Embedding -> pgvector
    """
    sample_policy = (
        "# VIP Loyalty & Expedited Escalation SOP\n\n"
        "## 1. Scope & Eligibility\n"
        "This standard operating procedure governs expedited dispute resolution for Tier-1 Enterprise clients.\n\n"
        "## 2. Mandatory Timelines\n"
        "All escalated VIP tickets must be acknowledged within 5 minutes and resolved within 2 hours.\n"
        "If unresolved within 90 minutes, automatic SMS notification is dispatched to the VP of Customer Experience.\n\n"
        "## 3. Financial Discretion\n"
        "Authorized agents possess direct credit approval authority up to ₹50,000 for verified duplicate debit errors."
    )

    file_bytes = io.BytesIO(sample_policy.encode("utf-8"))
    response = client.post(
        "/api/knowledge/upload",
        files={"file": ("vip_escalation_sop.md", file_bytes, "text/markdown")},
        data={
            "title": "VIP Loyalty & Expedited Escalation SOP",
            "document_type": "ESCALATION_POLICY",
            "category": "Customer Support"
        }
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] is not None
    assert data["title"] == "VIP Loyalty & Expedited Escalation SOP"
    assert data["document_type"] == "ESCALATION_POLICY"
    assert data["chunk_count"] >= 1

    # Verify database persistence of document and chunks
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == data["id"]).first()
    assert doc is not None
    assert doc.category == "Customer Support"
    assert len(doc.embedding) == 384

    chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == doc.id).all()
    assert len(chunks) >= 1
    assert any("5 minutes" in c.chunk_text for c in chunks)

def test_semantic_retrieval_and_chunk_matching(db: Session):
    """Stage 7: Tests semantic retrieval across granular chunks using Sentence Transformer cosine similarity."""
    knowledge_service.seed_default_knowledge_base(db)

    # 1. Query Refund Policy
    refund_chunks = knowledge_service.semantic_retrieve_chunks(
        query="What is the refund timeline for duplicate card deductions?",
        db=db,
        limit=3,
        min_similarity=0.35
    )
    assert len(refund_chunks) > 0
    top_hit = refund_chunks[0]
    assert top_hit["document_type"] in ["REFUND_POLICY", "BILLING_POLICY"]
    assert top_hit["similarity_score"] >= 0.35
    assert any(term in top_hit["chunk_text"].lower() for term in ["refund", "duplicate", "deduction", "day"])

    # 2. Query IT Troubleshooting Guide
    it_chunks = knowledge_service.semantic_retrieve_chunks(
        query="How to diagnose portal 500 internal server error and login failure?",
        db=db,
        limit=3,
        min_similarity=0.35
    )
    assert len(it_chunks) > 0
    assert any("it_troubleshooting_guide" in c["document_type"].lower() or "500" in c["chunk_text"] for c in it_chunks)

    # 3. Query Security Policy
    sec_chunks = knowledge_service.semantic_retrieve_chunks(
        query="What is the immediate protocol for compromised user account?",
        db=db,
        limit=3,
        min_similarity=0.35
    )
    assert len(sec_chunks) > 0
    assert any("security" in c["document_type"].lower() or "compromis" in c["chunk_text"].lower() for c in sec_chunks)

@pytest.mark.asyncio
async def test_grounded_answer_generation_ollama_groq(db: Session, client: TestClient):
    """Stage 8-10: Tests end-to-end RAG question answering:
    Semantic Retrieval -> Relevant Context -> Ollama/Groq -> Grounded Answer.
    """
    knowledge_service.seed_default_knowledge_base(db)

    res = client.post(
        "/api/knowledge/query",
        json={
            "question": "What is the policy for duplicate payment refunds?",
            "limit": 3
        }
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["grounded"] is True
    assert len(data["cited_chunks"]) > 0
    assert "answer" in data
    assert len(data["answer"]) > 10
    assert data["confidence_score"] >= 0.35
    assert any(p in data["provider"].lower() for p in ["ollama", "groq", "mock", "fallback"])

def test_supported_types_and_crud_endpoints(client: TestClient, db: Session):
    """Tests GET /supported-types, GET /, GET /{id}, and DELETE /{id}."""
    knowledge_service.seed_default_knowledge_base(db)

    # 1. Supported Types
    types_res = client.get("/api/knowledge/supported-types")
    assert types_res.status_code == 200
    types = types_res.json()
    assert len(types) == 9
    type_keys = [t["type"] for t in types]
    for exp in EXPECTED_9_TYPES:
        assert exp in type_keys

    # 2. List Documents
    list_res = client.get("/api/knowledge/")
    assert list_res.status_code == 200
    docs = list_res.json()
    assert len(docs) >= 9

    # 3. Get Document Detail
    first_id = docs[0]["id"]
    detail_res = client.get(f"/api/knowledge/{first_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert "chunks" in detail
    assert len(detail["chunks"]) >= 1

    # 4. Create via JSON
    create_res = client.post(
        "/api/knowledge/",
        json={
            "title": "Test Temp Policy",
            "document_type": "HR_POLICY",
            "category": "Human Resources",
            "content_text": "Temporary HR workplace testing policy for CRUD verification."
        }
    )
    assert create_res.status_code == 200
    new_id = create_res.json()["id"]

    # 5. Delete Document
    del_res = client.delete(f"/api/knowledge/{new_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"
