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
    GenerateCustomerResponseRequest, EditResponseRequest, ApproveResponseRequest,
    PriorityUpdateRequest, DepartmentUpdateRequest, TeamUpdateRequest, AgentUpdateRequest, StatusUpdateRequest
)
from app.ai.ai_orchestrator import ai_orchestrator
from app.services.audit_service import audit_service
from app.services.notification_service import notification_service
from app.services.complaint_service import complaint_service
from app.services.semantic_search_service import semantic_search_service
from app.services.lifecycle_service import lifecycle_service
from app.services.sla_service import sla_service
from app.models.complaint import ComplaintStatus
from app.models.user import User
from app.core.security import get_current_user_optional, check_complaint_access, require_roles

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
    category: Optional[str] = None,
    sentiment: Optional[str] = None,
    status: Optional[str] = None,
    is_duplicate: Optional[bool] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    sort_by: Optional[str] = "created_at",
    sort_order: Optional[str] = "desc",
    skip: int = 0,
    limit: int = 100,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    query = db.query(Complaint)

    # Role-Based Data Isolation
    if current_user:
        role = (current_user.role or "").upper()
        if role == "CUSTOMER":
            query = query.filter(Complaint.customer_email.ilike(current_user.email))
        elif role == "AGENT" and not department_id and not assigned_agent_id:
            query = query.filter(
                or_(
                    Complaint.assigned_agent_id == current_user.id,
                    Complaint.department_id == current_user.department_id
                )
            )
        elif role == "MANAGER" and current_user.department_id and not department_id:
            query = query.filter(Complaint.department_id == current_user.department_id)

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
        query = query.filter(Complaint.urgency.ilike(urgency.strip()))
    if priority_level:
        query = query.filter(Complaint.priority.ilike(priority_level.strip()))
    if category:
        query = query.filter(Complaint.category.ilike(f"%{category.strip()}%"))
    if sentiment:
        query = query.filter(Complaint.sentiment.ilike(sentiment.strip()))
    if status:
        query = query.filter(Complaint.status.ilike(status.strip()))
    if is_duplicate is not None:
        query = query.filter(Complaint.is_duplicate == is_duplicate)
    if date_from:
        query = query.filter(Complaint.created_at >= date_from)
    if date_to:
        query = query.filter(Complaint.created_at <= date_to)

    # Dynamic sorting
    sort_column = Complaint.created_at
    if sort_by:
        s_lower = sort_by.lower()
        if s_lower in ("id", "ticket_number", "complaint_number"):
            sort_column = Complaint.id
        elif s_lower == "subject":
            sort_column = Complaint.subject
        elif s_lower in ("customer", "customer_name"):
            sort_column = Complaint.customer_name
        elif s_lower == "category":
            sort_column = Complaint.category
        elif s_lower == "priority":
            sort_column = Complaint.priority
        elif s_lower == "urgency":
            sort_column = Complaint.urgency
        elif s_lower == "status":
            sort_column = Complaint.status
        elif s_lower == "sla_deadline":
            sort_column = Complaint.sla_deadline

    if (sort_order or "desc").lower() == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    complaints = query.offset(skip).limit(limit).all()

    # Populate SLA telemetry for each complaint
    for c in complaints:
        c.sla_metrics = sla_service.get_sla_metrics(c)

    return complaints

@router.get("/track/{ticket_number}")
def track_complaint_status(ticket_number: str, db: Session = Depends(get_db)):
    """Customer portal endpoint: Track complaint status and SLA progression by ticket number."""
    c = db.query(Complaint).filter(Complaint.ticket_number.ilike(ticket_number.strip())).first()
    if not c:
        raise HTTPException(status_code=404, detail=f"Complaint '{ticket_number}' not found")

    events = db.query(ComplaintEvent).filter(ComplaintEvent.complaint_id == c.id).order_by(ComplaintEvent.created_at.asc()).all()
    sla_metrics = sla_service.get_sla_metrics(c)
    return {
        "ticket_number": c.ticket_number,
        "subject": c.subject,
        "status": c.status,
        "urgency": c.urgency,
        "category": c.category,
        "department": c.department.name if c.department else "Customer Support",
        "team": c.team.name if c.team else None,
        "created_at": c.created_at,
        "sla_metrics": sla_metrics,
        "timeline": [
            {
                "action": e.action,
                "user": e.user,
                "timestamp": e.timestamp,
                "description": e.description
            }
            for e in events
        ]
    }

@router.get("/{complaint_id}")
async def get_complaint_details(
    complaint_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Enforce RBAC data access
    if current_user and not check_complaint_access(current_user, c):
        raise HTTPException(status_code=403, detail="Access denied. Customers may only view their own complaints.")

    predictions = db.query(ComplaintPrediction).filter(ComplaintPrediction.complaint_id == complaint_id).all()
    entities = db.query(ComplaintEntity).filter(ComplaintEntity.complaint_id == complaint_id).all()
    ai_responses = db.query(AIResponse).filter(AIResponse.complaint_id == complaint_id).all()

    # Ensure AI Recommended Resolution is present for this complaint
    has_rec = any(r.response_type == "RECOMMENDATION" for r in ai_responses)
    if not has_rec:
        try:
            await complaint_service.recommend_and_store_resolution(db=db, complaint_id=complaint_id)
            ai_responses = db.query(AIResponse).filter(AIResponse.complaint_id == complaint_id).all()
        except Exception:
            pass

    events = db.query(ComplaintEvent).filter(ComplaintEvent.complaint_id == complaint_id).order_by(ComplaintEvent.created_at.asc()).all()
    feedback = db.query(ComplaintFeedback).filter(ComplaintFeedback.complaint_id == complaint_id).all()
    sla_metrics = sla_service.get_sla_metrics(c)

    return {
        "complaint": c,
        "department": c.department,
        "team": c.team,
        "assigned_agent": c.assigned_agent,
        "predictions": predictions,
        "entities": entities,
        "ai_responses": ai_responses,
        "events": events,
        "feedback": feedback,
        "sla_metrics": sla_metrics
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

@router.put("/{complaint_id}", response_model=ComplaintResponse)
def update_complaint(complaint_id: int, update_in: ComplaintUpdate, db: Session = Depends(get_db)):
    """Update complaint metadata, status, priority, or routing assignment."""
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    update_data = update_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        if hasattr(c, field) and val is not None:
            setattr(c, field, val)
    
    db.commit()
    db.refresh(c)
    return c

@router.delete("/{complaint_id}")
def delete_complaint(complaint_id: int, db: Session = Depends(get_db)):
    """Deactivates / soft-deletes a complaint."""
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    c.is_active = False
    db.commit()
    return {"success": True, "message": f"Complaint #{complaint_id} deleted successfully"}


@router.post("/{complaint_id}/assign")
def assign_complaint(
    complaint_id: int,
    req: AssignRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    if current_user and (current_user.role or "").upper() not in ("MANAGER", "ADMIN"):
        raise HTTPException(status_code=403, detail="Access denied. Only MANAGER and ADMIN can assign complaints.")

    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    actor = (current_user.name if current_user else "Supervisor")

    if req.department_id and req.department_id != c.department_id:
        old_dept = c.department.name if c.department else str(c.department_id)
        c.department_id = req.department_id
        db.flush()
        new_dept = c.department.name if c.department else str(c.department_id)
        lifecycle_service.record_event(
            db=db,
            complaint_id=c.id,
            event_type="Department Changed",
            actor=actor,
            description=f"Department changed: {old_dept} -> {new_dept}",
            old_value=old_dept,
            new_value=new_dept,
            event_metadata={"reason": req.reason}
        )

    if req.team_id and req.team_id != c.team_id:
        old_team = c.team.name if c.team else str(c.team_id)
        c.team_id = req.team_id
        db.flush()
        new_team = c.team.name if c.team else str(c.team_id)
        lifecycle_service.record_event(
            db=db,
            complaint_id=c.id,
            event_type="Team Changed",
            actor=actor,
            description=f"Team changed: {old_team} -> {new_team}",
            old_value=old_team,
            new_value=new_team,
            event_metadata={"reason": req.reason}
        )

    if req.agent_id and req.agent_id != c.assigned_agent_id:
        old_agent = c.assigned_agent.name if c.assigned_agent else str(c.assigned_agent_id)
        c.assigned_agent_id = req.agent_id
        c.status = "Assigned"
        db.flush()
        new_agent = c.assigned_agent.name if c.assigned_agent else str(c.assigned_agent_id)
        lifecycle_service.record_event(
            db=db,
            complaint_id=c.id,
            event_type="Agent Assigned",
            actor=actor,
            description=f"Agent assigned: {old_agent} -> {new_agent}",
            old_value=old_agent,
            new_value=new_agent,
            event_metadata={"reason": req.reason}
        )

    db.add(ComplaintAssignment(
        complaint_id=c.id,
        agent_id=req.agent_id,
        team_id=req.team_id,
        department_id=req.department_id,
        reason=req.reason or "Supervisor assignment",
        assigned_by="SUPERVISOR"
    ))

    db.commit()
    db.refresh(c)
    return {"message": "Assignment updated successfully", "complaint": c}

@router.post("/{complaint_id}/reassign")
def reassign_complaint_endpoint(
    complaint_id: int,
    req: AssignRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Reassigns department, team, or specialist agent with justification."""
    return assign_complaint(complaint_id=complaint_id, req=req, current_user=current_user, db=db)

@router.post("/{complaint_id}/priority")
def update_complaint_priority(
    complaint_id: int,
    req: PriorityUpdateRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Changes priority (P1-P4) and recalculates SLA deadline with audit logging."""
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    old_priority = c.priority
    old_urgency = c.urgency
    actor = req.actor or (current_user.name if current_user else "Support Agent")

    c.priority = req.priority.upper()
    if req.urgency:
        c.urgency = req.urgency.title()
    elif req.priority.upper() == "P1":
        c.urgency = "Critical"
    elif req.priority.upper() == "P2":
        c.urgency = "High"
    elif req.priority.upper() == "P3":
        c.urgency = "Medium"
    elif req.priority.upper() == "P4":
        c.urgency = "Low"

    # Recalculate SLA deadline based on new priority/urgency
    rule_hours = sla_service.get_rule_hours(c.urgency)
    c.sla_deadline = c.created_at + timedelta(hours=rule_hours)

    lifecycle_service.record_event(
        db=db,
        complaint_id=c.id,
        event_type="Priority Changed",
        actor=actor,
        description=f"Priority updated: {old_priority} -> {c.priority} (Urgency: {c.urgency})",
        old_value=old_priority,
        new_value=c.priority,
        event_metadata={"reason": req.reason, "urgency": c.urgency, "sla_hours": rule_hours}
    )

    db.commit()
    db.refresh(c)
    return {
        "message": f"Priority updated to {c.priority}",
        "complaint": c,
        "sla_metrics": sla_service.get_sla_metrics(c)
    }

@router.post("/{complaint_id}/department")
def update_complaint_department(
    complaint_id: int,
    req: DepartmentUpdateRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Transfers complaint to another department with audit event."""
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    actor = req.actor or (current_user.name if current_user else "Supervisor")
    old_dept_obj = db.query(Department).filter(Department.id == c.department_id).first() if c.department_id else None
    old_dept = old_dept_obj.name if old_dept_obj else (c.department.name if c.department else str(c.department_id))

    new_dept_obj = db.query(Department).filter(Department.id == req.department_id).first() if req.department_id else None
    new_dept = new_dept_obj.name if new_dept_obj else str(req.department_id)

    c.department_id = req.department_id

    lifecycle_service.record_event(
        db=db,
        complaint_id=c.id,
        event_type="Department Changed",
        actor=actor,
        description=f"Department changed: {old_dept} -> {new_dept}",
        old_value=old_dept,
        new_value=new_dept,
        event_metadata={"reason": req.reason}
    )

    # Record ML Feedback when AI prediction is changed by human
    if old_dept != new_dept:
        feedback_rec = ComplaintFeedback(
            complaint_id=c.id,
            user_id=current_user.id if current_user else None,
            field_name="department",
            prediction=old_dept,
            ai_confidence=c.ai_confidence,
            corrected_value=new_dept,
            corrected_by=actor,
            corrected_at=datetime.utcnow(),
            reason=req.reason,
            complaint_text=f"{c.subject} {c.description}"
        )
        db.add(feedback_rec)

    db.commit()
    db.refresh(c)
    return {"message": f"Department changed to {new_dept}", "complaint": c}

@router.post("/{complaint_id}/team")
def update_complaint_team(
    complaint_id: int,
    req: TeamUpdateRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Assigns complaint to a specific functional team with audit event."""
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    actor = req.actor or (current_user.name if current_user else "Supervisor")
    old_team = c.team.name if c.team else str(c.team_id)
    c.team_id = req.team_id
    db.flush()
    new_team = c.team.name if c.team else str(c.team_id)

    lifecycle_service.record_event(
        db=db,
        complaint_id=c.id,
        event_type="Team Changed",
        actor=actor,
        description=f"Team changed: {old_team} -> {new_team}",
        old_value=old_team,
        new_value=new_team,
        event_metadata={"reason": req.reason}
    )

    db.commit()
    db.refresh(c)
    return {"message": f"Team changed to {new_team}", "complaint": c}

@router.post("/{complaint_id}/agent")
def update_complaint_agent(
    complaint_id: int,
    req: AgentUpdateRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Assigns specialist agent to complaint with audit event."""
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    actor = req.actor or (current_user.name if current_user else "Supervisor")
    old_agent = c.assigned_agent.name if c.assigned_agent else str(c.assigned_agent_id)
    c.assigned_agent_id = req.agent_id
    c.status = "ASSIGNED"
    db.flush()
    new_agent = c.assigned_agent.name if c.assigned_agent else str(c.assigned_agent_id)

    # Adjust workloads
    if req.agent_id:
        new_ag = db.query(Agent).filter(Agent.id == req.agent_id).first()
        if new_ag:
            new_ag.current_workload += 1

    lifecycle_service.record_event(
        db=db,
        complaint_id=c.id,
        event_type="Agent Assigned",
        actor=actor,
        description=f"Agent assigned: {old_agent} -> {new_agent}",
        old_value=old_agent,
        new_value=new_agent,
        event_metadata={"reason": req.reason}
    )

    db.commit()
    db.refresh(c)
    return {"message": f"Agent assigned: {new_agent}", "complaint": c}

@router.post("/{complaint_id}/status")
def update_complaint_status_endpoint(
    complaint_id: int,
    req: StatusUpdateRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Transitions complaint to a specified lifecycle status with audit recording."""
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    actor = req.actor or (current_user.name if current_user else "Support Agent")
    lifecycle_service.transition_status(
        db=db,
        complaint=c,
        new_status=req.status,
        actor=actor,
        description=req.notes
    )
    db.commit()
    db.refresh(c)
    return {"message": f"Status updated to {req.status.upper()}", "complaint": c}

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
    """Transitions complaint to RESOLVED: records 'Complaint Resolved' in complaint_events and audit logs."""
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    old_status = c.status
    lifecycle_service.transition_status(
        db=db,
        complaint=c,
        new_status="RESOLVED",
        actor=req.actor or "Support Agent",
        description="Resolution completed",
        event_metadata={"notes": req.resolution_notes}
    )

    lifecycle_service.record_event(
        db=db,
        complaint_id=c.id,
        event_type="Complaint Resolved",
        actor=req.actor or "Support Agent",
        description=f"Complaint resolved: {req.resolution_notes}",
        old_value=old_status,
        new_value="RESOLVED",
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

@router.post("/{complaint_id}/reopen")
def reopen_complaint(complaint_id: int, actor: str = "Support Agent", reason: Optional[str] = None, db: Session = Depends(get_db)):
    """Transitions complaint to IN_PROGRESS: records 'Complaint Reopened' in complaint_events and audit logs."""
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    old_status = c.status
    c.resolved_at = None
    lifecycle_service.transition_status(
        db=db,
        complaint=c,
        new_status="IN_PROGRESS",
        actor=actor,
        description=reason or "Complaint reopened"
    )

    lifecycle_service.record_event(
        db=db,
        complaint_id=c.id,
        event_type="Complaint Reopened",
        actor=actor,
        description=f"Complaint reopened: {reason or 'Reopened by support agent'}",
        old_value=old_status,
        new_value="IN_PROGRESS",
        event_metadata={"reason": reason}
    )

    db.commit()
    db.refresh(c)
    return {"message": "Complaint reopened successfully", "complaint": c}

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
        event_type="Response Generated",
        actor="AI Assistant",
        description="AI customer response draft generated",
        old_value=None,
        new_value=draft["body"][:120] + "..." if len(draft["body"]) > 120 else draft["body"],
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

    old_content = resp.content if resp else None
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
        event_type="Response Edited",
        actor="Support Agent",
        description="Customer response draft edited by agent",
        old_value=old_content[:120] + "..." if old_content and len(old_content) > 120 else old_content,
        new_value=req.content[:120] + "..." if len(req.content) > 120 else req.content,
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
    """Records 'Response Approved' milestone in complaint_events."""
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
        event_type="Response Approved",
        actor=approver,
        description=f"Customer response approved by {approver}",
        old_value="DRAFT",
        new_value="APPROVED",
        event_metadata={"response_id": resp.id}
    )

    db.commit()
    db.refresh(resp)
    return {"message": "Customer response approved", "response": resp}

@router.post("/{complaint_id}/send-response")
def send_response(complaint_id: int, req: SendResponseRequest, db: Session = Depends(get_db)):
    """Dispatches response to customer and records 'Response Sent' in complaint_events.
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
        event_type="Response Sent",
        actor=req.sender or "Support Agent",
        description="Customer response sent",
        old_value="APPROVED",
        new_value="SENT",
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

@router.get("/{complaint_id}/recommendations")
async def get_complaint_recommendations(complaint_id: int, db: Session = Depends(get_db)):
    """Retrieves the AI Recommended Resolution for a complaint, generating and persisting if not yet stored."""
    try:
        return await complaint_service.recommend_and_store_resolution(
            db=db,
            complaint_id=complaint_id,
            force_regenerate=False
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{complaint_id}/recommendations")
async def refresh_complaint_recommendations(complaint_id: int, db: Session = Depends(get_db)):
    """Re-generates and persists fresh AI Recommended Resolution steps for a complaint."""
    try:
        return await complaint_service.recommend_and_store_resolution(
            db=db,
            complaint_id=complaint_id,
            force_regenerate=True
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))



