from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.ai.ai_orchestrator import ai_orchestrator
from app.ai.rag import rag_engine
from app.ai.llm import get_llm_provider
from app.models.intelligence import ModelVersion

router = APIRouter()

class AnalyzeRequest(BaseModel):
    subject: str
    body: str
    customer_name: Optional[str] = None

class AssistantChatRequest(BaseModel):
    message: str
    conversation_history: Optional[list] = None

@router.post("/analyze")
async def analyze_text(req: AnalyzeRequest, db: Session = Depends(get_db)):
    """Runs complete 14-task NLP pipeline on input complaint text."""
    res = await ai_orchestrator.process_complaint_full(
        subject=req.subject,
        body=req.body,
        customer_name=req.customer_name or "Guest",
        ticket_number="PREVIEW-001",
        db=db
    )
    return res

@router.post("/chat")
async def ai_assistant_chat(req: AssistantChatRequest, db: Session = Depends(get_db)):
    """Internal AI Assistant that assists human support agents with policy lookups and procedure guidance."""
    # Retrieve relevant SOPs & policies via RAG
    relevant_docs = rag_engine.retrieve_relevant_policies(req.message, db, limit=3)
    context_str = "\n\n".join([f"[{d['title']}]: {d['content_snippet']}" for d in relevant_docs])

    llm = get_llm_provider()
    system_prompt = (
        "You are AutoTriage Assistant, an internal AI copilot assisting enterprise customer support agents. "
        "Answer questions about company policies, department routing, refund rules, and ticket workflows "
        "using the retrieved knowledge base documents below.\n\n"
        f"--- COMPANY KNOWLEDGE BASE ---\n{context_str}\n------------------------------\n"
    )
    user_prompt = req.message

    reply = await llm.generate_chat(system_prompt, user_prompt)
    if not reply:
        reply = (
            f"Here is the relevant guidance from our company knowledge base:\n\n"
            + (relevant_docs[0]["content_snippet"] if relevant_docs else "No specific policy document found for this inquiry.")
        )

    return {
        "reply": reply,
        "cited_documents": relevant_docs,
        "provider": llm.provider_name
    }

@router.get("/models")
def get_model_versions(db: Session = Depends(get_db)):
    return db.query(ModelVersion).all()
