from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.knowledge import KnowledgeDocument
from app.schemas.knowledge import (
    KnowledgeDocumentCreate, KnowledgeDocumentResponse, RAGQueryRequest, RAGQueryResponse
)
from app.ai.embeddings import embeddings_engine
from app.ai.rag import rag_engine
from app.ai.llm import get_llm_provider

router = APIRouter()

@router.get("/", response_model=List[KnowledgeDocumentResponse])
def get_knowledge_documents(db: Session = Depends(get_db)):
    return db.query(KnowledgeDocument).filter(KnowledgeDocument.is_active == True).all()

@router.post("/", response_model=KnowledgeDocumentResponse)
def create_knowledge_document(doc_in: KnowledgeDocumentCreate, db: Session = Depends(get_db)):
    # Generate 384d semantic vector for chunk
    chunk_text = doc_in.content_text[:1000]
    embedding = embeddings_engine.get_embedding(f"{doc_in.title} {doc_in.category} {chunk_text}")

    doc = KnowledgeDocument(
        title=doc_in.title,
        category=doc_in.category,
        document_type=doc_in.document_type,
        content_text=doc_in.content_text,
        chunk_index=0,
        chunk_text=chunk_text,
        embedding=embedding,
        department_id=doc_in.department_id
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

@router.post("/query", response_model=RAGQueryResponse)
async def query_knowledge_rag(req: RAGQueryRequest, db: Session = Depends(get_db)):
    """Executes RAG semantic retrieval over company policies and generates a grounded response."""
    relevant_docs = rag_engine.retrieve_relevant_policies(req.question, db, limit=req.limit)
    
    context_str = "\n\n".join([
        f"Document: {d['title']} ({d['document_type']}):\n{d['content_snippet']}"
        for d in relevant_docs
    ])

    llm = get_llm_provider()
    system_prompt = (
        "You are the internal Corporate Policy & SOP Assistant for AutoTriage AI. "
        "Answer the user's inquiry based strictly on the retrieved official company documents below. "
        "If the answer is not in the documents, state clearly that no company policy covers it.\n\n"
        f"--- OFFICIAL POLICIES ---\n{context_str}\n-------------------------\n"
    )
    user_prompt = f"Inquiry: {req.question}"

    answer = await llm.generate_chat(system_prompt, user_prompt)
    if not answer:
        answer = f"Based on our active company policy database: {relevant_docs[0]['content_snippet'] if relevant_docs else 'No matching company policy found for this query.'}"

    return RAGQueryResponse(
        answer=answer,
        cited_documents=relevant_docs,
        provider=llm.provider_name
    )
