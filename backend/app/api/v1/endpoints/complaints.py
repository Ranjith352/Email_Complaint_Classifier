from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.core.config import settings
from app.models.complaint import Complaint, ComplaintAssignment, ComplaintEvent, ComplaintFeedback
from app.models.organization import Department, Team, Agent
from app.models.intelligence import ComplaintPrediction, ComplaintEntity, AIResponse
from app.models.knowledge import KnowledgeDocument
from app.schemas.complaint import (
    ComplaintCreate, ComplaintResponse, ComplaintUpdate,
    AssignRequest, ResolveRequest, FeedbackCreate, FeedbackResponse,
    EscalateRequest, SendResponseRequest, StatusTransitionRequest,
    ComplaintEventResponse, ComplaintEntityResponse, ComplaintReviewRequest,
    ComplaintLinkRequest, ComplaintMergeRequest, ComplaintIgnoreDuplicateRequest,
    DuplicateSearchResponse, SemanticSearchResultItem, SemanticSearchResponse,
    GenerateCustomerResponseRequest, EditResponseRequest, ApproveResponseRequest
)
from app.ai.ai_orchestrator import ai_orchestrator
from app.services.audit_service import audit_service
from app.services.notification_service import notification_service
from app.services.complaint_service import complaint_service
from app.services.semantic_search_service import semantic_search_service
from app.services.lifecycle_service import lifecycle_service
from app.models.complaint import ComplaintStatus

router = APIRouter()

@router.get("/semantic-search", response_model=SemanticSearchResponse)
def semantic_search_complaints(
    query: str = Query(..., description="Natural language search query to find conceptually similar complaints"),
    limit: int = Query(10, ge=1, le=100),
    threshold: float = Query(0.40, ge=0.0, le=1.0),
    db: Session = Depends(get_db)
):
    """Semantic search using dense sentence embeddings and pgvector (or cosine similarity fallback)."""
    results = semantic_search_service.search_complaints(
        db=db,
        query_text=query,
        limit=limit,
        threshold=threshold
    )
    return {
        "query": query,
        "total_results": len(results),
        "results": results
    }

@router.get("/", response_model=List[ComplaintResponse])
def get_complaints(
    search: Optional[str] = None,
    department_id: Optional[int] = None,
    team_id: Optional[int] = None,
    assigned_agent_id: Optional[int] = None,
    urgency: Optional[str] = None,
    priority_level: Optional[str] = None,
    status: Optional[str] = None,
    is_duplicate: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Complaint)

    if search:
        s = f"%{search.lower()}%"
        query = query.filter(
            or_(
                Complaint.ticket_number.ilike(s),
                Complaint.subject.ilike(s),
                Complaint.body.ilike(s),
                Complaint.customer_name.ilike(s),
                Complaint.customer_email.ilike(s)
            )
        )
    if department_id:
        query = query.filter(Complaint.department_id == department_id)
    if team_id:
        query = query.filter(Complaint.team_id == team_id)
    if assigned_agent_id:
        query = query.filter(Complaint.assigned_agent_id == assigned_agent_id)
    if urgency:
        query = query.filter(Complaint.urgency == urgency)
    if priority_level:
        query = query.filter(Complaint.priority == priority_level)
    if status:
        query = query.filter(Complaint.status == status.upper())
    if is_duplicate is not None:
        query = query.filter(Complaint.is_duplicate == is_duplicate)

    complaints = query.order_by(Complaint.created_at.desc()).offset(skip).limit(limit).all()
    return complaints

@router.get("/{complaint_id}")
def get_complaint_details(complaint_id: int, db: Session = Depends(get_db)):
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    predictions = db.query(ComplaintPrediction).filter(ComplaintPrediction.complaint_id == complaint_id).all()
    entities = db.query(ComplaintEntity).filter(ComplaintEntity.complaint_id == complaint_id).all()
    ai_responses = db.query(AIResponse).filter(AIResponse.complaint_id == complaint_id).all()
    events = db.query(ComplaintEvent).filter(ComplaintEvent.complaint_id == complaint_id).order_by(ComplaintEvent.created_at.asc()).all()
    feedback = db.query(ComplaintFeedback).filter(ComplaintFeedback.complaint_id == complaint_id).all()

    return {
        "complaint": c,
        "department": c.department,
        "team": c.team,
        "assigned_agent": c.assigned_agent,
        "predictions": predictions,
        "entities": entities,
        "ai_responses": ai_responses,
        "events": events,
        "feedback": feedback
    }

@router.get("/{complaint_id}/events", response_model=List[ComplaintEventResponse])
def get_complaint_events(complaint_id: int, db: Session = Depends(get_db)):
    """Retrieves full chronological timeline of all lifecycle events for a complaint."""
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return lifecycle_service.get_timeline(db, complaint_id)

@router.post("/", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
async def create_complaint(complaint_in: ComplaintCreate, db: Session = Depends(get_db)):
    """Ingests complaint and executes full AI triage lifecycle: NEW -> AI_ANALYZING -> AI_ANALYZED -> ROUTED -> ASSIGNED."""
    complaint = await complaint_service.process_and_create_complaint(db, complaint_in)
    return complaint

@router.post("/{complaint_id}/assign")
def assign_complaint(complaint_id: int, req: AssignRequest, db: Session = Depends(get_db)):
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if req.agent_id:
        c.assigned_agent_id = req.agent_id
        c.status = "Assigned"
    if req.team_id:
        c.team_id = req.team_id
    if req.department_id:
        c.department_id = req.department_id

    db.add(ComplaintAssignment(
        complaint_id=c.id,
        agent_id=req.agent_id,
        team_id=req.team_id,
        department_id=req.department_id,
        reason=req.reason or "Manual supervisor assignment",
        assigned_by="SUPERVISOR"
    ))

    db.add(ComplaintEvent(
        complaint_id=c.id,
        event_type="ASSIGNED",
        actor="Supervisor",
        notes=f"Reassigned ticket. Reason: {req.reason or 'N/A'}"
    ))

    db.commit()
    db.refresh(c)
    return {"message": "Assignment updated successfully", "complaint": c}

@router.post("/{complaint_id}/start-investigation")
def start_investigation(complaint_id: int, actor: str = "Assigned Agent", db: Session = Depends(get_db)):
    """Transitions complaint to IN_PROGRESS: records 'Agent started investigation' in complaint_events."""
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    lifecycle_service.transition_status(
        db=db,
        complaint=c,
        new_status="IN_PROGRESS",
        actor=actor,
        description="Agent started investigation"
    )
    db.commit()
    db.refresh(c)
    return {"message": "Investigation started", "complaint": c}

@router.post("/{complaint_id}/waiting-customer")
def waiting_for_customer(complaint_id: int, actor: str = "Support Agent", notes: Optional[str] = None, db: Session = Depends(get_db)):
    """Transitions complaint to WAITING_FOR_CUSTOMER: records event in complaint_events."""
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    lifecycle_service.transition_status(
        db=db,
        complaint=c,
        new_status="WAITING_FOR_CUSTOMER",
        actor=actor,
        description=notes or "Waiting for customer response"
    )
    db.commit()
    db.refresh(c)
    return {"message": "Status updated to Waiting for Customer", "complaint": c}

@router.post("/{complaint_id}/escalate")
def escalate_complaint(complaint_id: int, req: EscalateRequest, db: Session = Depends(get_db)):
    """Transitions complaint to ESCALATED: flags ticket and records event in complaint_events."""
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    c.is_escalated = True
    lifecycle_service.transition_status(
        db=db,
        complaint=c,
        new_status="ESCALATED",
        actor=req.actor or "Lead Agent",
        description=f"Complaint escalated: {req.reason}",
        event_metadata={"reason": req.reason}
    )
    db.commit()
    db.refresh(c)
    return {"message": "Complaint successfully escalated", "complaint": c}

@router.post("/{complaint_id}/resolve")
def resolve_complaint(complaint_id: int, req: ResolveRequest, db: Session = Depends(get_db)):
    """Transitions complaint to RESOLVED: records 'Resolution completed' in complaint_events."""
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    lifecycle_service.transition_status(
        db=db,
        complaint=c,
        new_status="RESOLVED",
        actor=req.actor or "Support Agent",
        description="Resolution completed",
        event_metadata={"notes": req.resolution_notes}
    )

    # Decrement agent workload
    if c.assigned_agent:
        c.assigned_agent.current_workload = max(0, c.assigned_agent.current_workload - 1)

    # Add to RAG Knowledge Base if requested
    if req.mark_as_policy_knowledge:
        from app.ai.embeddings import embeddings_engine
        text_to_embed = f"{c.subject} {c.category} {req.resolution_notes}"
        emb = embeddings_engine.get_embedding(text_to_embed)
        db.add(KnowledgeDocument(
            title=f"Resolved Case: {c.subject}",
            category=c.category,
            department_id=c.department_id,
            document_type="SOP",
            content_text=f"Problem: {c.description}\nSolution: {req.resolution_notes}",
            chunk_text=f"Resolution: {req.resolution_notes}",
            embedding=emb
        ))

    db.commit()
    db.refresh(c)
    return {"message": "Complaint marked as Resolved", "complaint": c}

@router.post("/{complaint_id}/feedback", response_model=FeedbackResponse)
def submit_feedback(complaint_id: int, fb_in: FeedbackCreate, db: Session = Depends(get_db)):
    """Collects human-in-the-loop agent feedback on AI predictions to inform future retraining."""
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    fb = ComplaintFeedback(
        complaint_id=complaint_id,
        is_category_correct=fb_in.is_category_correct,
        corrected_category=fb_in.corrected_category,
        is_sentiment_correct=fb_in.is_sentiment_correct,
        rating=fb_in.rating,
        notes=fb_in.notes
    )
    db.add(fb)

    # If category was corrected by human, update complaint
    if not fb_in.is_category_correct and fb_in.corrected_category:
        c.category = fb_in.corrected_category

    lifecycle_service.record_event(
        db=db,
        complaint_id=c.id,
        event_type="FEEDBACK_COLLECTED",
        actor="Human Agent",
        description=f"Agent rated AI triage {fb_in.rating}/5. Corrected category: {fb_in.corrected_category or 'None'}"
    )

    db.commit()
    db.refresh(fb)
    return fb

@router.post("/{complaint_id}/generate-response")
async def generate_complaint_response(
    complaint_id: int,
    req: Optional[GenerateCustomerResponseRequest] = None,
    db: Session = Depends(get_db)
):
    """Allows the agent to click 'Generate AI Response' to create a professional customer response."""
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    tone = req.tone if (req and req.tone) else "Empathetic & Professional"
    dept_name = c.department.name if c.department else (c.category or "Customer Support")

    from app.ai.response_generator import response_generator
    draft = await response_generator.generate_draft(
        ticket_number=c.complaint_number,
        customer_name=c.customer_name or "Customer",
        subject=c.subject,
        body=c.description,
        department=dept_name,
        tone=tone
    )

    # Upsert DRAFT_REPLY for this complaint
    resp = (
        db.query(AIResponse)
        .filter(AIResponse.complaint_id == complaint_id, AIResponse.response_type == "DRAFT_REPLY")
        .first()
    )

    if resp:
        resp.content = draft["body"]
        resp.provider = draft["provider"]
        resp.is_approved = False  # Reset approval upon fresh generation
        resp.approved_by = None
        resp.approved_at = None
        resp.is_sent = False
        resp.sent_by = None
        resp.sent_at = None
    else:
        resp = AIResponse(
            complaint_id=c.id,
            provider=draft["provider"],
            model="Configured-LLM",
            response_type="DRAFT_REPLY",
            content=draft["body"],
            is_approved=False,
            is_sent=False
        )
        db.add(resp)

    lifecycle_service.record_event(
        db=db,
        complaint_id=complaint_id,
        event_type="AI_RESPONSE_GENERATED",
        actor="AI Assistant",
        description="AI customer response draft generated",
        event_metadata={"provider": draft["provider"]}
    )

    db.commit()
    db.refresh(resp)
    return {"message": "AI customer response draft generated successfully", "response": resp}

@router.put("/{complaint_id}/edit-response")
def edit_complaint_response(
    complaint_id: int,
    req: EditResponseRequest,
    db: Session = Depends(get_db)
):
    """Allows the agent to edit the customer response draft before approving or sending.
    Note: Editing automatically resets approval so modified text requires human approval.
    """
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    query = db.query(AIResponse).filter(AIResponse.complaint_id == complaint_id, AIResponse.response_type == "DRAFT_REPLY")
    if req.response_id:
        query = query.filter(AIResponse.id == req.response_id)
    resp = query.first()

    if not resp:
        resp = AIResponse(
            complaint_id=complaint_id,
            provider="Human Agent Editor",
            model="Agent-Edited",
            response_type="DRAFT_REPLY",
            content=req.content,
            is_approved=False,
            is_sent=False
        )
        db.add(resp)
    else:
        resp.content = req.content
        resp.is_approved = False  # Editing resets approval
        resp.approved_by = None
        resp.approved_at = None

    lifecycle_service.record_event(
        db=db,
        complaint_id=complaint_id,
        event_type="RESPONSE_EDITED",
        actor="Support Agent",
        description="Customer response draft edited by agent",
        event_metadata={"response_id": resp.id}
    )

    db.commit()
    db.refresh(resp)
    return {"message": "Customer response draft updated successfully", "response": resp}

@router.post("/{complaint_id}/approve-response")
def approve_response(
    complaint_id: int,
    response_id: Optional[int] = None,
    approved_by: str = "Lead Agent",
    req: Optional[ApproveResponseRequest] = None,
    db: Session = Depends(get_db)
):
    """Records 'Customer response approved' milestone in complaint_events."""
    target_resp_id = req.response_id if (req and req.response_id) else response_id
    approver = req.approved_by if (req and req.approved_by) else approved_by

    query = db.query(AIResponse).filter(AIResponse.complaint_id == complaint_id)
    if target_resp_id:
        query = query.filter(AIResponse.id == target_resp_id)
    else:
        query = query.filter(AIResponse.response_type == "DRAFT_REPLY").order_by(AIResponse.created_at.desc())
    resp = query.first()

    if not resp:
        raise HTTPException(status_code=404, detail="AI response draft not found")

    resp.is_approved = True
    resp.approved_by = approver
    resp.approved_at = datetime.utcnow()

    lifecycle_service.record_event(
        db=db,
        complaint_id=complaint_id,
        event_type="RESPONSE_APPROVED",
        actor=approver,
        description=f"Customer response approved by {approver}",
        event_metadata={"response_id": resp.id}
    )

    db.commit()
    db.refresh(resp)
    return {"message": "Customer response approved", "response": resp}

@router.post("/{complaint_id}/send-response")
def send_response(complaint_id: int, req: SendResponseRequest, db: Session = Depends(get_db)):
    """Dispatches response to customer and records 'Customer response sent' in complaint_events.
    CRITICAL: Never send automatically without explicit human approval.
    """
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Locate the target response draft
    query = db.query(AIResponse).filter(AIResponse.complaint_id == complaint_id)
    if req.response_id:
        query = query.filter(AIResponse.id == req.response_id)
    else:
        query = query.filter(AIResponse.response_type == "DRAFT_REPLY").order_by(AIResponse.created_at.desc())
    resp = query.first()

    if not resp:
        raise HTTPException(status_code=404, detail="No customer response draft found to send.")

    # STRICT GUARD: Never send automatically without explicit human approval
    if not resp.is_approved:
        raise HTTPException(
            status_code=400,
            detail="Cannot send response without explicit human approval. Please approve the response before sending."
        )

    resp.is_sent = True
    resp.sent_by = req.sender or "Support Agent"
    resp.sent_at = datetime.utcnow()

    lifecycle_service.record_event(
        db=db,
        complaint_id=complaint_id,
        event_type="RESPONSE_SENT",
        actor=req.sender or "Support Agent",
        description="Customer response sent",
        event_metadata={"response_id": resp.id, "customer_email": c.customer_email}
    )

    db.commit()
    db.refresh(resp)
    return {"message": "Customer response successfully sent", "complaint": c, "response": resp}

@router.post("/{complaint_id}/close")
def close_complaint(complaint_id: int, actor: str = "Support Lead", notes: Optional[str] = None, db: Session = Depends(get_db)):
    """Transitions complaint to CLOSED: records 'Complaint closed' in complaint_events."""
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    lifecycle_service.transition_status(
        db=db,
        complaint=c,
        new_status="CLOSED",
        actor=actor,
        description=notes or "Complaint closed"
    )
    db.commit()
    db.refresh(c)
    return {"message": "Complaint successfully closed", "complaint": c}

@router.post("/{complaint_id}/transition")
def custom_status_transition(complaint_id: int, req: StatusTransitionRequest, db: Session = Depends(get_db)):
    """Generic status transition endpoint supporting any valid complaint lifecycle state."""
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    try:
        lifecycle_service.transition_status(
            db=db,
            complaint=c,
            new_status=req.status,
            actor=req.actor or "Operator",
            description=req.notes,
            event_metadata=req.metadata
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    db.commit()
    db.refresh(c)
    return {"message": f"Successfully transitioned to {req.status.upper()}", "complaint": c}

@router.get("/{complaint_id}/entities", response_model=List[ComplaintEntityResponse])
def get_complaint_entities(complaint_id: int, db: Session = Depends(get_db)):
    """Fetches all structured entities extracted for a complaint and stored in complaint_entities."""
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    entities = db.query(ComplaintEntity).filter(ComplaintEntity.complaint_id == complaint_id).all()
    return entities

@router.post("/{complaint_id}/review", response_model=ComplaintResponse)
def review_complaint(complaint_id: int, req: ComplaintReviewRequest, db: Session = Depends(get_db)):
    """Completes human review for a complaint, updating review_required, reviewed_by, reviewed_at, and finalizing department."""
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaint_service.review_complaint(
        db=db,
        complaint=c,
        department_id=req.department_id,
        team_id=req.team_id,
        assigned_agent_id=req.assigned_agent_id,
        reviewer_name=req.reviewer_name,
        notes=req.notes
    )

@router.post("/{complaint_id}/duplicate/link", response_model=ComplaintResponse)
def link_duplicate_complaint(complaint_id: int, req: ComplaintLinkRequest, db: Session = Depends(get_db)):
    """Links a duplicate complaint to a parent/target complaint."""
    try:
        return complaint_service.link_duplicate_complaint(
            db=db,
            complaint_id=complaint_id,
            target_complaint_id=req.target_complaint_id,
            notes=req.notes,
            actor=req.actor or "Support Agent"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{complaint_id}/duplicate/merge", response_model=ComplaintResponse)
def merge_duplicate_complaint(complaint_id: int, req: ComplaintMergeRequest, db: Session = Depends(get_db)):
    """Merges a duplicate complaint into a primary complaint and marks duplicate ticket resolved/merged."""
    try:
        return complaint_service.merge_duplicate_complaint(
            db=db,
            complaint_id=complaint_id,
            primary_complaint_id=req.primary_complaint_id,
            reason=req.reason,
            actor=req.actor or "Support Agent"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{complaint_id}/duplicate/ignore", response_model=ComplaintResponse)
def ignore_duplicate_warning(complaint_id: int, req: ComplaintIgnoreDuplicateRequest, db: Session = Depends(get_db)):
    """Dismisses duplicate warning for a complaint and marks duplicate_status as IGNORED."""
    try:
        return complaint_service.ignore_duplicate_warning(
            db=db,
            complaint_id=complaint_id,
            reason=req.reason,
            actor=req.actor or "Support Agent"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{complaint_id}/similar", response_model=DuplicateSearchResponse)
def get_similar_complaints(complaint_id: int, db: Session = Depends(get_db)):
    """Retrieves similar complaints and duplicate matches using Sentence Transformers + pgvector and TF-IDF baseline."""
    try:
        return complaint_service.get_similar_complaints(db=db, complaint_id=complaint_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{complaint_id}/find-similar", response_model=SemanticSearchResponse)
def find_similar_to_complaint(
    complaint_id: int,
    limit: int = Query(10, ge=1, le=100),
    threshold: float = Query(0.40, ge=0.0, le=1.0),
    db: Session = Depends(get_db)
):
    """'Find complaints similar to this one': retrieves conceptually similar complaints using dense embeddings."""
    try:
        results = semantic_search_service.find_similar_to_complaint(
            db=db,
            complaint_id=complaint_id,
            limit=limit,
            threshold=threshold
        )
        return {
            "query": f"Complaint #{complaint_id}",
            "total_results": len(results),
            "results": results
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{complaint_id}/summarize")
async def summarize_complaint(
    complaint_id: int,
    provider: Optional[str] = Query(None, description="Optional LLM provider preference: 'ollama' or 'groq'"),
    model: Optional[str] = Query(None, description="Optional model name override for the LLM provider"),
    db: Session = Depends(get_db)
):
    """Summarizes complaint using Ollama/Groq (or configured LLMProvider) and persists the summary."""
    try:
        return await complaint_service.summarize_and_store_complaint(
            db=db,
            complaint_id=complaint_id,
            provider=provider,
            model=model
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{complaint_id}/summary")
def get_complaint_summary(complaint_id: int, db: Session = Depends(get_db)):
    """Retrieves the stored summary of a complaint."""
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail=f"Complaint {complaint_id} not found")
    return {
        "complaint_id": c.id,
        "ticket_number": c.ticket_number,
        "summary": c.summary
    }



