from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.knowledge import KnowledgeDocument
from app.schemas.knowledge import (
    KnowledgeDocumentCreate, KnowledgeDocumentResponse, KnowledgeDocumentDetailResponse,
    RAGQueryRequest, RAGQueryResponse, SupportedDocumentType
)
from app.services.knowledge_service import knowledge_service

router = APIRouter()

@router.get("", response_model=List[KnowledgeDocumentResponse])
@router.get("/", response_model=List[KnowledgeDocumentResponse])
def list_knowledge_documents(
    department: Optional[str] = None,
    document_type: Optional[str] = None,
    is_active: Optional[bool] = True,
    db: Session = Depends(get_db)
):
    """Retrieve all company knowledge documents and policy SOPs."""
    query = db.query(KnowledgeDocument)
    if department:
        query = query.filter(KnowledgeDocument.department == department)
    if document_type:
        query = query.filter(KnowledgeDocument.document_type == document_type)
    if is_active is not None:
        query = query.filter(KnowledgeDocument.is_active == is_active)
    return query.order_by(KnowledgeDocument.created_at.desc()).all()

@router.post("", response_model=KnowledgeDocumentResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=KnowledgeDocumentResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_document(doc_in: KnowledgeDocumentCreate, db: Session = Depends(get_db)):
    """Create and index a new policy or SOP document into the knowledge base."""
    chosen_name = doc_in.document_name or doc_in.title or "Untitled Document"
    content = doc_in.content_text or doc_in.content or ""
    doc = knowledge_service.ingest_document(
        db=db,
        document_name=chosen_name,
        document_type=doc_in.document_type,
        content_text=content,
        category=doc_in.category,
        department=doc_in.department,
        department_id=doc_in.department_id,
        uploaded_by=doc_in.uploaded_by or "Admin",
        version=1
    )
    return doc


@router.get("/{id}", response_model=KnowledgeDocumentDetailResponse)
def get_knowledge_document(id: int, db: Session = Depends(get_db)):
    """Retrieve a single knowledge document with chunk and vector status."""
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge document not found")
    return doc

@router.delete("/{id}")
def delete_knowledge_document(id: int, db: Session = Depends(get_db)):
    """Delete a knowledge document and its associated vector embeddings."""
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge document not found")
    title = doc.title
    db.delete(doc)
    db.commit()
    return {"success": True, "message": f"Knowledge document #{id} deleted successfully", "title": title}


@router.post("/query", response_model=RAGQueryResponse)
def query_knowledge_base(query_req: RAGQueryRequest, db: Session = Depends(get_db)):
    """Perform RAG semantic search across policy documents."""
    return knowledge_service.search_knowledge_base(
        db=db,
        query=query_req.query,
        department=query_req.department,
        top_k=query_req.top_k,
        min_similarity=query_req.min_similarity
    )
