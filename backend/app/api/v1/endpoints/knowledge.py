import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.knowledge import KnowledgeDocument, KnowledgeChunk
from app.schemas.knowledge import (
    KnowledgeDocumentCreate,
    KnowledgeDocumentResponse,
    KnowledgeDocumentDetailResponse,
    SupportedDocumentType,
    RAGQueryRequest,
    RAGQueryResponse,
    CitedChunk
)
from app.services.knowledge_service import knowledge_service, SUPPORTED_DOCUMENT_TYPES
from app.ai.rag import rag_engine
from app.ai.llm_provider import get_llm_provider

router = APIRouter()

@router.get("/supported-types", response_model=List[SupportedDocumentType])
def get_supported_document_types():
    """Returns the 9 officially supported enterprise document types."""
    return SUPPORTED_DOCUMENT_TYPES

@router.get("/", response_model=List[KnowledgeDocumentResponse])
def get_knowledge_documents(db: Session = Depends(get_db)):
    """Lists all active knowledge base documents with their chunk counts."""
    docs = db.query(KnowledgeDocument).filter(KnowledgeDocument.is_active == True).order_by(KnowledgeDocument.created_at.desc()).all()
    results = []
    for d in docs:
        c_count = db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == d.id).count()
        results.append(KnowledgeDocumentResponse(
            id=d.id,
            title=d.title,
            category=d.category,
            document_type=d.document_type,
            chunk_text=d.chunk_text,
            is_active=d.is_active,
            created_at=d.created_at,
            chunk_count=max(1, c_count)
        ))
    return results

@router.get("/{doc_id}", response_model=KnowledgeDocumentDetailResponse)
def get_knowledge_document(doc_id: int, db: Session = Depends(get_db)):
    """Retrieves document details and all granular semantic chunks."""
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Knowledge document not found")
    return doc

@router.post("/upload", response_model=KnowledgeDocumentResponse)
async def upload_knowledge_document_file(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    document_type: str = Form("REFUND_POLICY"),
    category: Optional[str] = Form(None),
    department_id: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """Stage 1-6: Document Upload & Ingestion Pipeline.
    Document Upload -> Text Extraction -> Cleaning -> Chunking -> Sentence Transformer -> Embedding -> pgvector
    """
    file_bytes = await file.read()
    filename = file.filename or "uploaded_policy.txt"
    doc_title = title.strip() if title and title.strip() else filename.rsplit(".", 1)[0].replace("_", " ").title()

    # Stage 2: Text Extraction
    raw_text = knowledge_service.extract_text_from_file(file_bytes, filename)
    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text content from the uploaded file.")

    # Stage 3-6: Cleaning -> Chunking -> Sentence Transformer -> Embedding -> pgvector/DB Persistence
    doc = knowledge_service.ingest_document(
        db=db,
        title=doc_title,
        document_type=document_type,
        content_text=raw_text,
        category=category,
        department_id=department_id
    )

    c_count = db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == doc.id).count()
    return KnowledgeDocumentResponse(
        id=doc.id,
        title=doc.title,
        category=doc.category,
        document_type=doc.document_type,
        chunk_text=doc.chunk_text,
        is_active=doc.is_active,
        created_at=doc.created_at,
        chunk_count=c_count
    )

@router.post("/", response_model=KnowledgeDocumentResponse)
def create_knowledge_document_json(doc_in: KnowledgeDocumentCreate, db: Session = Depends(get_db)):
    """Ingests a document provided via JSON payload through the complete 9-stage pipeline."""
    doc = knowledge_service.ingest_document(
        db=db,
        title=doc_in.title,
        document_type=doc_in.document_type,
        content_text=doc_in.content_text,
        category=doc_in.category,
        department_id=doc_in.department_id
    )
    c_count = db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == doc.id).count()
    return KnowledgeDocumentResponse(
        id=doc.id,
        title=doc.title,
        category=doc.category,
        document_type=doc.document_type,
        chunk_text=doc.chunk_text,
        is_active=doc.is_active,
        created_at=doc.created_at,
        chunk_count=c_count
    )

@router.post("/query", response_model=RAGQueryResponse)
async def query_knowledge_rag(req: RAGQueryRequest, db: Session = Depends(get_db)):
    """Stage 7-10: RAG Knowledge Querying.
    Semantic Retrieval (Sentence Transformer / pgvector) -> Relevant Context -> Ollama/Groq -> Grounded Answer.
    """
    # Stage 7: Semantic Retrieval
    chunks = knowledge_service.semantic_retrieve_chunks(
        query=req.question,
        db=db,
        limit=req.limit,
        min_similarity=req.min_similarity,
        document_type=req.document_type
    )

    # Fallback to document level retrieval if chunks empty
    if not chunks:
        doc_fallbacks = rag_engine.retrieve_relevant_policies(req.question, db, limit=req.limit, min_similarity=0.25)
        for d in doc_fallbacks:
            chunks.append({
                "chunk_id": None,
                "document_id": d["id"],
                "document_title": d["title"],
                "document_type": d.get("document_type", "POLICY"),
                "category": d.get("category", "General"),
                "chunk_index": 0,
                "chunk_text": d.get("content_snippet", ""),
                "similarity_score": d.get("similarity", 0.3)
            })

    # Stage 8: Assemble Relevant Context
    context_blocks = []
    for c in chunks:
        context_blocks.append(
            f"--- Document: {c['document_title']} ({c['document_type']}) [Chunk #{c['chunk_index']} | Similarity: {c['similarity_score']:.2f}] ---\n"
            f"{c['chunk_text']}"
        )
    context_str = "\n\n".join(context_blocks)

    # Stage 9 & 10: Ollama/Groq Grounded Answer Generation
    llm = get_llm_provider()
    system_prompt = (
        "You are the official Enterprise Knowledge Base Assistant for AutoTriage AI. "
        "Answer the user's inquiry based STRICTLY and ONLY on the retrieved official company documents below. "
        "Cite the document name and specific policy rules (such as refund timelines, SLA hours, or diagnostic steps). "
        "If the query cannot be answered from the provided documents, state clearly: "
        "'Based on the official company knowledge base, no policy covers this request.' "
        "DO NOT hallucinate or assume facts not present in the context."
    )
    user_prompt = (
        f"Retrieved Company Policy Context:\n{context_str or 'No relevant policy documents found.'}\n\n"
        f"User Inquiry:\n{req.question}"
    )

    grounded_answer = await llm.generate_chat(system_prompt, user_prompt)
    if not grounded_answer:
        if chunks:
            grounded_answer = f"Based on our official '{chunks[0]['document_title']}':\n{chunks[0]['chunk_text'][:350]}..."
        else:
            grounded_answer = "Based on the official company knowledge base, no policy covers this request."

    cited = [CitedChunk(**c) for c in chunks]
    confidence = chunks[0]["similarity_score"] if chunks else 0.0

    return RAGQueryResponse(
        question=req.question,
        answer=grounded_answer.strip(),
        grounded=bool(chunks),
        cited_chunks=cited,
        provider=llm.provider_name,
        confidence_score=confidence
    )

@router.post("/seed")
def seed_knowledge_base(db: Session = Depends(get_db)):
    """Seeds the 9 official enterprise policy documents if they are not already present."""
    count = knowledge_service.seed_default_knowledge_base(db)
    return {
        "status": "success",
        "seeded_documents": count,
        "supported_types_count": len(SUPPORTED_DOCUMENT_TYPES)
    }

@router.delete("/{doc_id}")
def delete_knowledge_document(doc_id: int, db: Session = Depends(get_db)):
    """Removes a knowledge document and cascades deletion of its chunks."""
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Knowledge document not found")
    
    db.delete(doc)
    db.commit()
    return {"status": "deleted", "id": doc_id, "title": doc.title}
