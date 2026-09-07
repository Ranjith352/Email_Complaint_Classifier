import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.knowledge import KnowledgeDocument, KnowledgeChunk, ChunkEmbedding
from app.services.knowledge_service import knowledge_service

def test_admin_upload_and_separate_storage(db: Session, client: TestClient):
    """Verifies that Admin upload stores KnowledgeDocument, KnowledgeChunk,
    and ChunkEmbedding in 3 separate relational tables.
    """
    sample_content = (
        "# Cloud Platform Security & IAM Protocol\n\n"
        "## 1. Multi-Factor Authentication Requirements\n"
        "All employee accounts accessing staging or production systems must enforce hardware or TOTP 2FA.\n\n"
        "## 2. Token Invalidation Upon Deprovisioning\n"
        "Upon employee offboarding or role transfer, all API keys, session cookies, and OAuth access tokens "
        "must be immediately revoked within 15 minutes of HR notification."
    )

    file_bytes = io.BytesIO(sample_content.encode("utf-8"))
    res = client.post(
        "/api/knowledge/upload",
        files={"file": ("cloud_security_iam.md", file_bytes, "text/markdown")},
        data={
            "document_name": "Cloud Platform Security & IAM Protocol",
            "document_type": "SECURITY_POLICY",
            "department": "Security & Compliance",
            "uploaded_by": "Security Admin Lead"
        }
    )
    assert res.status_code == 200, res.text
    data = res.json()
    doc_id = data["id"]

    # 1. Verify KnowledgeDocument metadata
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    assert doc is not None
    assert doc.title == "Cloud Platform Security & IAM Protocol"
    assert doc.document_name == "Cloud Platform Security & IAM Protocol"
    assert doc.document_type == "SECURITY_POLICY"
    assert doc.department == "Security & Compliance"
    assert doc.version == 1
    assert doc.uploaded_by == "Security Admin Lead"
    assert doc.created_at is not None

    # 2. Verify KnowledgeChunk separate table
    chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == doc_id).all()
    assert len(chunks) >= 1
    for chunk in chunks:
        assert chunk.document_id == doc_id
        assert len(chunk.chunk_text) > 0

    # 3. Verify ChunkEmbedding separate table
    embeddings = db.query(ChunkEmbedding).filter(ChunkEmbedding.document_id == doc_id).all()
    assert len(embeddings) == len(chunks)
    for emb in embeddings:
        assert emb.document_id == doc_id
        assert emb.chunk_id in [c.id for c in chunks]
        assert emb.model_name == "all-MiniLM-L6-v2"
        assert emb.dimension == 384
        assert len(emb.embedding) == 384

def test_document_metadata_fields_stored(client: TestClient, db: Session):
    """Verifies that document name, document type, department, version,
    uploaded_by, and created_at are properly returned and queried.
    """
    res = client.post(
        "/api/knowledge/",
        json={
            "document_name": "Executive Compensation Governance",
            "document_type": "FINANCE_POLICY",
            "department": "Finance & Treasury",
            "uploaded_by": "Chief Financial Officer",
            "content_text": "Financial settlements exceeding ₹500,000 require joint authorization from CFO and Legal."
        }
    )
    assert res.status_code == 200
    doc_data = res.json()
    assert doc_data["document_name"] == "Executive Compensation Governance"
    assert doc_data["document_type"] == "FINANCE_POLICY"
    assert doc_data["department"] == "Finance & Treasury"
    assert doc_data["version"] == 1
    assert doc_data["uploaded_by"] == "Chief Financial Officer"
    assert doc_data["created_at"] is not None

def test_admin_update_document_and_versioning(client: TestClient, db: Session):
    """Verifies that updating document content or metadata increments the version."""
    # 1. Create document
    create_res = client.post(
        "/api/knowledge/",
        json={
            "document_name": "Warranty Replacement SLA",
            "document_type": "SLA_POLICY",
            "department": "Operations",
            "uploaded_by": "Ops Manager",
            "content_text": "Hardware warranty replacements must ship within 72 hours of verification."
        }
    )
    assert create_res.status_code == 200
    doc_id = create_res.json()["id"]
    assert create_res.json()["version"] == 1

    # 2. Update document content
    update_res = client.put(
        f"/api/knowledge/{doc_id}",
        json={
            "document_name": "Warranty Replacement SLA (Amended 2026)",
            "department": "Customer Operations",
            "content_text": "Hardware warranty replacements must ship within 24 hours of verification for Gold tier.",
            "reindex": True
        }
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["document_name"] == "Warranty Replacement SLA (Amended 2026)"
    assert updated["department"] == "Customer Operations"
    assert updated["version"] == 2

    # Check database persistence and updated chunks & embeddings
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    assert doc.version == 2
    chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == doc_id).all()
    assert any("24 hours" in c.chunk_text for c in chunks)
    embeddings = db.query(ChunkEmbedding).filter(ChunkEmbedding.document_id == doc_id).all()
    assert len(embeddings) == len(chunks)

def test_admin_reindex_document(client: TestClient, db: Session):
    """Verifies that calling the reindex endpoint refreshes chunks and embeddings,
    and increments the version.
    """
    create_res = client.post(
        "/api/knowledge/",
        json={
            "document_name": "API Rate Limiting Guidelines",
            "document_type": "IT_TROUBLESHOOTING_GUIDE",
            "department": "IT Support",
            "uploaded_by": "Platform Lead",
            "content_text": "Client applications are throttled at 100 requests per minute per IP address."
        }
    )
    doc_id = create_res.json()["id"]
    assert create_res.json()["version"] == 1

    # Call reindex
    reindex_res = client.post(f"/api/knowledge/{doc_id}/reindex")
    assert reindex_res.status_code == 200
    reindexed = reindex_res.json()
    assert reindexed["version"] == 2

    # Verify embeddings refreshed
    embeddings = db.query(ChunkEmbedding).filter(ChunkEmbedding.document_id == doc_id).all()
    assert len(embeddings) >= 1
    assert len(embeddings[0].embedding) == 384

def test_admin_delete_document_cascade(client: TestClient, db: Session):
    """Verifies that deleting a document cascades removal of its separate chunks and embeddings."""
    create_res = client.post(
        "/api/knowledge/",
        json={
            "document_name": "Temporary Deletion Test Policy",
            "document_type": "HR_POLICY",
            "department": "HR",
            "content_text": "This policy will be deleted to test cascading removal of chunks and embeddings."
        }
    )
    doc_id = create_res.json()["id"]

    # Verify chunks and embeddings exist prior to deletion
    assert db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == doc_id).count() >= 1
    assert db.query(ChunkEmbedding).filter(ChunkEmbedding.document_id == doc_id).count() >= 1

    # Delete
    del_res = client.delete(f"/api/knowledge/{doc_id}")
    assert del_res.status_code == 200

    # Verify cascading removal
    assert db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first() is None
    assert db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == doc_id).count() == 0
    assert db.query(ChunkEmbedding).filter(ChunkEmbedding.document_id == doc_id).count() == 0

@pytest.mark.asyncio
async def test_rag_query_with_separate_embeddings(client: TestClient, db: Session):
    """Verifies that RAG semantic retrieval performs cosine similarity against
    the dedicated ChunkEmbedding records and returns grounded answers.
    """
    knowledge_service.seed_default_knowledge_base(db)

    res = client.post(
        "/api/knowledge/query",
        json={
            "question": "What is the authorization limit for Tier-1 agents according to the Finance Policy?",
            "limit": 3
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["grounded"] is True
    top_chunk = data["cited_chunks"][0]
    assert top_chunk["similarity_score"] >= 0.25
    assert "answer" in data
    assert "Based on company policy" in data["answer"]
