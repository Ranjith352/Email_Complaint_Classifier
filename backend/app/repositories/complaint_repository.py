from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.complaint import Complaint, ComplaintAssignment, ComplaintEvent, ComplaintFeedback

class ComplaintRepository:
    @staticmethod
    def get_by_id(db: Session, complaint_id: int) -> Optional[Complaint]:
        return db.query(Complaint).filter(Complaint.id == complaint_id).first()

    @staticmethod
    def get_by_ticket_number(db: Session, ticket_number: str) -> Optional[Complaint]:
        return db.query(Complaint).filter(Complaint.ticket_number == ticket_number).first()

    @staticmethod
    def list_complaints(
        db: Session,
        search: Optional[str] = None,
        department_id: Optional[int] = None,
        team_id: Optional[int] = None,
        assigned_agent_id: Optional[int] = None,
        urgency: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Complaint]:
        q = db.query(Complaint)
        if search:
            s = f"%{search.lower()}%"
            q = q.filter(
                or_(
                    Complaint.ticket_number.ilike(s),
                    Complaint.subject.ilike(s),
                    Complaint.body.ilike(s),
                    Complaint.customer_email.ilike(s),
                    Complaint.customer_name.ilike(s)
                )
            )
        if department_id:
            q = q.filter(Complaint.department_id == department_id)
        if team_id:
            q = q.filter(Complaint.team_id == team_id)
        if assigned_agent_id:
            q = q.filter(Complaint.assigned_agent_id == assigned_agent_id)
        if urgency:
            q = q.filter(Complaint.urgency == urgency)
        if status:
            q = q.filter(Complaint.status == status)

        return q.order_by(Complaint.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def create(db: Session, complaint: Complaint) -> Complaint:
        db.add(complaint)
        db.commit()
        db.refresh(complaint)
        return complaint

    @staticmethod
    def count(db: Session) -> int:
        return db.query(Complaint).count()

complaint_repository = ComplaintRepository()
