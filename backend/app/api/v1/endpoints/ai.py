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
    """Internal AI Assistant that assists human support agents with policy lookups and procedure guidance.
    Policy Grounding Constraints:
    - The AI must not invent company policies.
    - Only use retrieved knowledge when available.
    - Clearly indicate "Based on company policy..." or "No relevant company policy was found."
    - Do not present unsupported information as official company policy.
    """
    # Retrieve relevant SOPs & policies via RAG
    relevant_docs = rag_engine.retrieve_relevant_policies(req.message, db, limit=3, min_similarity=0.30)
    llm = get_llm_provider()

    is_policy_inquiry = any(kw in req.message.lower() for kw in ["policy", "refund", "sla", "rule", "procedure", "sop", "guideline", "reimbursement", "escalat"])

    # Verify substantive topic alignment
    stopwords = {
        "what", "is", "the", "company", "policy", "for", "and", "regarding", "of",
        "to", "in", "a", "an", "on", "official", "our", "are", "how", "who", "when",
        "where", "does", "do", "we", "have", "any", "about", "with", "from", "by",
        "at", "this", "that", "these", "those", "can", "should", "would", "could",
        "please", "tell", "me", "give", "rules", "guidelines", "invent", "new",
        "granting", "employees", "employee", "customer", "customers", "user", "users"
    }
    import re
    is_invention_request = bool(re.search(r"\b(invent|fabricate|make up|hallucinate)\b", req.message.lower()))
    query_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", req.message.lower())) - stopwords
    has_topic_match = True
    if query_words and relevant_docs:
        combined_corpus = " ".join([f"{d['title']} {d['content_snippet']}" for d in relevant_docs]).lower()
        has_topic_match = any(
            re.search(rf"\b{re.escape(w)}\b", combined_corpus) or (len(w) >= 5 and w[:4] in combined_corpus)
            for w in query_words
        )

    if is_invention_request or (is_policy_inquiry and (not relevant_docs or not has_topic_match)):
        return {
            "reply": "No relevant company policy was found.",
            "cited_documents": [],
            "provider": llm.provider_name
        }

    context_str = "\n\n".join([f"[{d['title']}] ({d['document_type']}): {d['content_snippet']}" for d in relevant_docs])

    system_prompt = (
        "You are AutoTriage Assistant, an internal AI copilot assisting enterprise customer support agents.\n"
        "CRITICAL ANTI-HALLUCINATION & POLICY GROUNDING RULES:\n"
        "1. The AI must NOT invent company policies under any circumstances.\n"
        "2. For policy questions, ONLY use retrieved knowledge when available.\n"
        "3. Do NOT present unsupported information as official company policy.\n"
        "4. If the retrieved context contains relevant policy rules answering the question, clearly indicate and begin your response with: "
        "\"Based on company policy...\"\n"
        "5. If the retrieved context does NOT contain relevant information answering the question, you MUST respond EXACTLY with: "
        "\"No relevant company policy was found.\""
    )
    user_prompt = (
        f"Retrieved Company Policy Context:\n{context_str or 'No relevant policy documents found.'}\n\n"
        f"Agent Question:\n{req.message}"
    )

    reply = await llm.generate_chat(system_prompt, user_prompt)
    if reply:
        reply_clean = reply.strip()
        neg_indicators = [
            "no relevant company policy was found",
            "no company policy was found",
            "no policy was found",
            "no policy covers",
            "no relevant policy",
            "not found in"
        ]
        if any(ind in reply_clean.lower() for ind in neg_indicators):
            reply = "No relevant company policy was found."
            relevant_docs = []
        elif is_policy_inquiry and relevant_docs:
            import re
            if not re.match(r"^based on (our |the |official )?company policy", reply_clean, re.IGNORECASE):
                reply = f"Based on company policy, {reply_clean}"
            else:
                reply = reply_clean
    else:
        if relevant_docs:
            reply = f"Based on company policy [{relevant_docs[0]['title']}]: {relevant_docs[0]['content_snippet'][:300]}..."
        else:
            reply = "No relevant company policy was found."

    return {
        "reply": reply,
        "cited_documents": relevant_docs,
        "provider": llm.provider_name
    }


class RecommendationsRequest(BaseModel):
    complaint_text: str
    category: str = "General"


class RAGQueryRequest(BaseModel):
    question: str
    limit: int = 3


class GenerateResponseRequest(BaseModel):
    ticket_number: str
    customer_name: Optional[str] = "Valued Customer"
    subject: str
    body: str
    department: str
    tone: Optional[str] = "Empathetic & Professional"


class ExplainComplaintRequest(BaseModel):
    subject: str
    body: str
    category: str = "General"
    department: str = "Customer Support"
    entities: Optional[list] = None


class PolicyReasoningRequest(BaseModel):
    complaint_text: str
    category: str = "General"


@router.post("/recommendations")
async def generate_resolution_recommendations(req: RecommendationsRequest, db: Session = Depends(get_db)):
    """2. Resolution recommendations: generates resolution steps grounded on company policies."""
    return await rag_engine.generate_grounded_recommendation(
        complaint_text=req.complaint_text,
        category=req.category,
        db=db
    )


@router.post("/rag/query")
async def rag_question_answering(req: RAGQueryRequest, db: Session = Depends(get_db)):
    """4. RAG question answering: answers user/agent questions using retrieved knowledge documents."""
    return await rag_engine.answer_query(
        question=req.question,
        db=db,
        limit=req.limit
    )


@router.post("/generate-response")
async def generate_customer_response(req: GenerateResponseRequest):
    """5. Customer response generation: drafts empathetic customer response email."""
    from app.ai.response_generator import response_generator
    return await response_generator.generate_draft(
        ticket_number=req.ticket_number,
        customer_name=req.customer_name or "Valued Customer",
        subject=req.subject,
        body=req.body,
        department=req.department,
        tone=req.tone or "Empathetic & Professional"
    )


@router.post("/explain")
async def explain_complaint(req: ExplainComplaintRequest, db: Session = Depends(get_db)):
    """6. Internal complaint explanation: provides internal technical diagnostic briefing for agents."""
    return await rag_engine.explain_complaint(
        subject=req.subject,
        body=req.body,
        category=req.category,
        department=req.department,
        entities=req.entities,
        db=db
    )


@router.post("/reasoning")
async def policy_reasoning(req: PolicyReasoningRequest, db: Session = Depends(get_db)):
    """7. Reasoning over retrieved complaint/policy information: evaluates claim eligibility against policy terms."""
    return await rag_engine.reason_over_complaint_and_policies(
        complaint_text=req.complaint_text,
        category=req.category,
        db=db
    )


@router.get("/models")
def get_model_versions(db: Session = Depends(get_db)):
    return db.query(ModelVersion).all()


class LLMConfigRequest(BaseModel):
    provider: Optional[str] = None
    ollama_model: Optional[str] = None
    ollama_base_url: Optional[str] = None


@router.get("/llm/status")
async def get_llm_status():
    """Checks LLM provider connectivity and local Ollama model installation without crashing."""
    from app.core.config import settings
    provider = get_llm_provider()
    if hasattr(provider, "check_availability"):
        status = await provider.check_availability()
    else:
        status = {
            "available": provider.is_available,
            "error": None,
            "download_url": "https://ollama.com/download"
        }
    status["active_provider"] = provider.provider_name
    status["configured_llm_provider"] = settings.LLM_PROVIDER
    status["configured_ollama_base_url"] = settings.OLLAMA_BASE_URL
    status["configured_ollama_model"] = settings.OLLAMA_MODEL or "(none)"
    return status


@router.post("/llm/config")
async def configure_llm(req: LLMConfigRequest):
    """Allows user to configure LLM provider, Ollama model, or Ollama base URL at runtime."""
    from app.core.config import settings
    if req.provider:
        settings.LLM_PROVIDER = req.provider.strip().lower()
    if req.ollama_model is not None:
        settings.OLLAMA_MODEL = req.ollama_model.strip()
    if req.ollama_base_url:
        settings.OLLAMA_BASE_URL = req.ollama_base_url.strip()

    provider = get_llm_provider()
    status = await provider.check_availability() if hasattr(provider, "check_availability") else {"available": provider.is_available}
    return {
        "message": "LLM configuration updated successfully.",
        "configuration": {
            "LLM_PROVIDER": settings.LLM_PROVIDER,
            "OLLAMA_BASE_URL": settings.OLLAMA_BASE_URL,
            "OLLAMA_MODEL": settings.OLLAMA_MODEL,
        },
        "status": status
    }


@router.get("/llm/models")
async def list_ollama_models():
    """Lists models installed in local Ollama daemon or returns clear installation instructions."""
    from app.ai.ollama_provider import OllamaProvider, OLLAMA_DOWNLOAD_URL
    from app.core.config import settings
    provider = OllamaProvider()
    installed = await provider.get_installed_models()
    return {
        "installed_models": installed,
        "configured_model": settings.OLLAMA_MODEL or None,
        "online": len(installed) > 0,
        "download_url": OLLAMA_DOWNLOAD_URL,
        "instructions": [
            f"1. Download and install Ollama from {OLLAMA_DOWNLOAD_URL}",
            f"2. Launch Ollama daemon (runs on {settings.OLLAMA_BASE_URL})",
            "3. Run 'ollama pull llama3' (or any model) in your terminal",
            "4. Configure OLLAMA_MODEL=llama3 via POST /api/ai/llm/config or in your .env file"
        ]
    }
