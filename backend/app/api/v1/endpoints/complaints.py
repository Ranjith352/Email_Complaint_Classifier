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
    ComplaintEventResponse, ComplaintEntityResponse, ComplaintReviewRequest
)
from app.ai.ai_orchestrator import ai_orchestrator
from app.services.audit_service import audit_service
from app.services.notification_service import notification_service
from app.services.complaint_service import complaint_service
from app.services.lifecycle_service import lifecycle_service
from app.models.complaint import ComplaintStatus

router = APIRouter()

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

@router.post("/{complaint_id}/approve-response")
def approve_response(complaint_id: int, response_id: int, approved_by: str = "Lead Agent", db: Session = Depends(get_db)):
    """Records 'Customer response approved' milestone in complaint_events."""
    resp = db.query(AIResponse).filter(AIResponse.id == response_id, AIResponse.complaint_id == complaint_id).first()
    if not resp:
        raise HTTPException(status_code=404, detail="AI response draft not found")

    resp.is_approved = True
    resp.approved_by = approved_by
    resp.approved_at = datetime.utcnow()

    lifecycle_service.record_event(
        db=db,
        complaint_id=complaint_id,
        event_type="RESPONSE_APPROVED",
        actor=approved_by,
        description="Customer response approved",
        event_metadata={"response_id": response_id}
    )

    db.commit()
    return {"message": "Customer response approved", "response": resp}

@router.post("/{complaint_id}/send-response")
def send_response(complaint_id: int, req: SendResponseRequest, db: Session = Depends(get_db)):
    """Dispatches response to customer and records 'Customer response sent' in complaint_events."""
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    lifecycle_service.record_event(
        db=db,
        complaint_id=complaint_id,
        event_type="RESPONSE_SENT",
        actor=req.sender or "Support Agent",
        description="Customer response sent",
        event_metadata={"response_id": req.response_id, "customer_email": c.customer_email}
    )

    db.commit()
    return {"message": "Customer response successfully sent", "complaint": c}

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

