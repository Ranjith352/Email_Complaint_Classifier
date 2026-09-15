from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.ai.ai_orchestrator import ai_orchestrator
from app.ai.rag import rag_engine
from app.ai.llm import get_llm_provider
from app.ai.summarizer import summarizer
from app.ai.duplicate_detector import duplicate_detector
from app.models.intelligence import ModelVersion
from app.models.complaint import Complaint

router = APIRouter()

class AnalyzeRequest(BaseModel):
    subject: str
    body: str
    customer_name: Optional[str] = None

class SummarizeRequest(BaseModel):
    text: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    complaint_id: Optional[int] = None

class SimilarRequest(BaseModel):
    subject: Optional[str] = ""
    body: Optional[str] = ""
    text: Optional[str] = None
    complaint_id: Optional[int] = None
    limit: Optional[int] = 5

class GenerateResponseRequest(BaseModel):
    ticket_number: Optional[str] = "CASE-DRAFT"
    customer_name: Optional[str] = "Valued Customer"
    subject: str
    body: str
    department: str
    tone: Optional[str] = "Empathetic & Professional"

class RecommendResolutionRequest(BaseModel):
    complaint_text: Optional[str] = None
    subject: Optional[str] = ""
    body: Optional[str] = ""
    category: Optional[str] = "General"
    complaint_id: Optional[int] = None

class AssistantChatRequest(BaseModel):
    message: str
    conversation_history: Optional[list] = None

# =========================================================================
# Required 68. AI Endpoints
# =========================================================================

@router.post("/analyze")
async def analyze_text(req: AnalyzeRequest, db: Session = Depends(get_db)):
    """Runs complete 14-task NLP triage pipeline on input complaint text."""
    res = await ai_orchestrator.process_complaint_full(
        subject=req.subject,
        body=req.body,
        customer_name=req.customer_name or "Guest",
        ticket_number="PREVIEW-001",
        db=db
    )
    return res

@router.post("/summarize")
async def summarize_complaint(req: SummarizeRequest, db: Session = Depends(get_db)):
    """Generate concise executive summary of a complaint."""
    text = req.text or ""
    if not text and (req.subject or req.body):
        text = f"{req.subject or ''}\n\n{req.body or ''}".strip()
    elif req.complaint_id:
        comp = db.query(Complaint).filter(Complaint.id == req.complaint_id).first()
        if comp:
            text = f"{comp.subject}\n\n{comp.description or ''}"
    
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No text or complaint provided to summarize")

    summary = await summarizer.summarize_text(text)
    return {
        "success": True,
        "summary": summary,
        "length": len(summary)
    }

@router.post("/generate-response")
async def generate_customer_response(req: GenerateResponseRequest):
    """Customer response generation: drafts empathetic customer response email."""
    from app.ai.response_generator import response_generator
    return await response_generator.generate_draft(
        ticket_number=req.ticket_number or "CASE-DRAFT",
        customer_name=req.customer_name or "Valued Customer",
        subject=req.subject,
        body=req.body,
        department=req.department,
        tone=req.tone or "Empathetic & Professional"
    )

@router.post("/similar")
async def find_similar_complaints(req: SimilarRequest, db: Session = Depends(get_db)):
    """Detect similar or duplicate complaints using vector embeddings and semantic search."""
    text = req.text or f"{req.subject or ''} {req.body or ''}".strip()
    if not text and req.complaint_id:
        comp = db.query(Complaint).filter(Complaint.id == req.complaint_id).first()
        if comp:
            text = f"{comp.subject} {comp.description or ''}"
    
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No text or complaint provided to query")

    from app.ai.embeddings import embeddings_engine
    embedding = embeddings_engine.get_embedding(text)
    res = duplicate_detector.detect_similar_and_duplicates(
        db=db,
        new_embedding=embedding,
        complaint_text=text,
        current_complaint_id=req.complaint_id,
        similar_threshold=0.35
    )
    sim_list = res.get("similar_complaints") or []
    return {
        "success": True,
        "is_duplicate": res.get("is_duplicate", False),
        "matches_count": len(sim_list),
        "similar_complaints": sim_list[:req.limit or 5]
    }



@router.post("/recommend-resolution")
@router.post("/recommendations")
async def recommend_resolution(req: RecommendResolutionRequest, db: Session = Depends(get_db)):
    """Grounded resolution recommendations derived from policy documentation."""
    complaint_text = req.complaint_text or f"{req.subject or ''}\n\n{req.body or ''}".strip()
    if not complaint_text and req.complaint_id:
        comp = db.query(Complaint).filter(Complaint.id == req.complaint_id).first()
        if comp:
            complaint_text = f"{comp.subject}\n\n{comp.description or ''}"
            req.category = comp.category or req.category

    return await rag_engine.generate_grounded_recommendation(
        complaint_text=complaint_text or "General Inquiry",
        category=req.category or "General",
        db=db
    )

# =========================================================================
# Additional AI Intelligence Endpoints
# =========================================================================

@router.post("/chat")
async def ai_assistant_chat(req: AssistantChatRequest, db: Session = Depends(get_db)):
    """Internal AI Assistant for policy lookups and guided procedures."""
    from app.api.v1.endpoints.ai import ai_assistant_chat as v1_chat
    return await v1_chat(req, db)

@router.post("/rag/query")
async def rag_question_answering(req: Dict[str, Any], db: Session = Depends(get_db)):
    """RAG question answering over company knowledge base."""
    return await rag_engine.answer_query(
        question=req.get("question", ""),
        db=db,
        limit=req.get("limit", 3)
    )

@router.get("/models")
def get_model_versions(db: Session = Depends(get_db)):
    """List registered model versions and benchmark metrics."""
    return db.query(ModelVersion).order_by(ModelVersion.id.asc()).all()

@router.get("/models/active")
def get_active_model_versions(db: Session = Depends(get_db)):
    """List currently active production models."""
    return db.query(ModelVersion).filter(ModelVersion.is_active == True).all()
