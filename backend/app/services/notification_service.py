from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.operations import Notification

class NotificationService:
    @staticmethod
    def create_notification(
        db: Session,
        title: str,
        message: str,
        notification_type: str = "INFO",
        recipient_id: Optional[int] = None,
        department_id: Optional[int] = None,
        link_url: Optional[str] = None
    ) -> Notification:
        """Dispatches an enterprise in-app alert notification."""
        note = Notification(
            title=title,
            message=message,
            notification_type=notification_type,
            recipient_id=recipient_id,
            department_id=department_id,
            link_url=link_url
        )
        db.add(note)
        db.commit()
        db.refresh(note)
        return note

    @classmethod
    def create_routing_notification(
        cls,
        db: Session,
        ticket_number: str,
        department_name: str,
        team_name: str,
        priority: str,
        sla_hours: int = 24,
        department_id: Optional[int] = None,
        complaint_id: Optional[int] = None
    ) -> Notification:
        """
        Dispatches in-app notification when a complaint is routed.
        Format:
        New Critical Complaint
        Complaint:
        CMP-10001
        Department:
        Finance
        Team:
        Payments
        Priority:
        Critical
        SLA:
        2 hours
        """
        clean_priority = (priority or "Medium").capitalize()
        title = f"New {clean_priority} Complaint"
        message = (
            f"Complaint:\n{ticket_number}\n"
            f"Department:\n{department_name or 'General'}\n"
            f"Team:\n{team_name or 'General Triage'}\n"
            f"Priority:\n{clean_priority}\n"
            f"SLA:\n{sla_hours} hours"
        )
        link_url = f"/complaints/{complaint_id}" if complaint_id else None
        return cls.create_notification(
            db=db,
            title=title,
            message=message,
            notification_type="ROUTED_COMPLAINT" if clean_priority != "Critical" else "CRITICAL_TICKET",
            department_id=department_id,
            link_url=link_url
        )

    @staticmethod
    def get_notifications(
        db: Session,
        unread_only: bool = False,
        department_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Notification]:
        """Fetches chronological in-app notification history."""
        query = db.query(Notification)
        if unread_only:
            query = query.filter(Notification.is_read == False)
        if department_id:
            query = query.filter(Notification.department_id == department_id)
        return query.order_by(Notification.created_at.desc()).limit(limit).all()

    @staticmethod
    def mark_read(db: Session, notification_id: int) -> bool:
        """Marks an in-app notification as read."""
        note = db.query(Notification).filter(Notification.id == notification_id).first()
        if not note:
            return False
        note.is_read = True
        db.commit()
        return True

    @staticmethod
    def mark_all_read(db: Session, department_id: Optional[int] = None) -> int:
        """Marks all active notifications as read."""
        query = db.query(Notification).filter(Notification.is_read == False)
        if department_id:
            query = query.filter(Notification.department_id == department_id)
        notes = query.all()
        for note in notes:
            note.is_read = True
        db.commit()
        return len(notes)

notification_service = NotificationService()
