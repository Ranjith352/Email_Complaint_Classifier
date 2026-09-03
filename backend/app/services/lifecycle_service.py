from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.complaint import Complaint, ComplaintEvent, ComplaintStatus, ComplaintEventType

class LifecycleService:
    VALID_STATUSES = {s.value for s in ComplaintStatus}

    @staticmethod
    def record_event(
        db: Session,
        complaint_id: int,
        event_type: str,
        actor: str,
        description: str,
        event_metadata: Optional[Dict[str, Any]] = None
    ) -> ComplaintEvent:
        """Persists a lifecycle transition or audit milestone event in complaint_events."""
        event = ComplaintEvent(
            complaint_id=complaint_id,
            event_type=event_type,
            actor=actor,
            description=description,
            event_metadata=event_metadata or {},
            created_at=datetime.utcnow()
        )
        db.add(event)
        return event

    @classmethod
    def transition_status(
        cls,
        db: Session,
        complaint: Complaint,
        new_status: str,
        actor: str = "SYSTEM",
        description: Optional[str] = None,
        event_metadata: Optional[Dict[str, Any]] = None
    ) -> Complaint:
        """Transitions a complaint to a new lifecycle status and records the transition event."""
        norm_status = new_status.upper()
        if norm_status not in cls.VALID_STATUSES:
            raise ValueError(f"Invalid status '{new_status}'. Allowed statuses: {sorted(cls.VALID_STATUSES)}")

        old_status = complaint.status
        complaint.status = norm_status
        complaint.updated_at = datetime.utcnow()

        if norm_status == ComplaintStatus.RESOLVED.value and not complaint.resolved_at:
            complaint.resolved_at = datetime.utcnow()
        elif norm_status == ComplaintStatus.ESCALATED.value:
            complaint.is_escalated = True

        default_desc = {
            ComplaintStatus.NEW.value: "Complaint received",
            ComplaintStatus.AI_ANALYZING.value: "AI analysis started",
            ComplaintStatus.AI_ANALYZED.value: "AI analysis completed",
            ComplaintStatus.ROUTED.value: f"Routed to department",
            ComplaintStatus.ASSIGNED.value: f"Assigned to specialist agent",
            ComplaintStatus.IN_PROGRESS.value: "Agent started investigation",
            ComplaintStatus.WAITING_FOR_CUSTOMER.value: "Waiting for customer response",
            ComplaintStatus.ESCALATED.value: "Complaint escalated to tier-2 team",
            ComplaintStatus.RESOLVED.value: "Resolution completed",
            ComplaintStatus.CLOSED.value: "Complaint closed"
        }.get(norm_status, f"Status updated to {norm_status}")

        meta = event_metadata or {}
        meta.update({"from_status": old_status, "to_status": norm_status})

        cls.record_event(
            db=db,
            complaint_id=complaint.id,
            event_type=norm_status,
            actor=actor,
            description=description or default_desc,
            event_metadata=meta
        )
        return complaint

    @classmethod
    def get_timeline(cls, db: Session, complaint_id: int) -> List[ComplaintEvent]:
        """Retrieves chronological lifecycle event timeline for a complaint."""
        return (
            db.query(ComplaintEvent)
            .filter(ComplaintEvent.complaint_id == complaint_id)
            .order_by(ComplaintEvent.created_at.asc())
            .all()
        )

lifecycle_service = LifecycleService()
