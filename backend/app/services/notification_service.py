from typing import Optional
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
        return note

notification_service = NotificationService()
