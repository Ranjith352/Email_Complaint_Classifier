from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.notification import Notification
from app.models.event import AuditLog
from app.schemas.operations import NotificationResponse, AuditLogResponse

router = APIRouter()

@router.get("", response_model=List[NotificationResponse])
@router.get("/", response_model=List[NotificationResponse])
def get_notifications(
    recipient_id: int = None,
    unread_only: bool = False,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Retrieve operational notifications."""
    query = db.query(Notification)
    if recipient_id:
        query = query.filter(Notification.recipient_id == recipient_id)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    return query.order_by(Notification.created_at.desc()).limit(limit).all()

@router.post("/{notification_id}/read")
def mark_notification_read(notification_id: int, db: Session = Depends(get_db)):
    """Mark a notification as read."""
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    notif.is_read = True
    db.commit()
    return {"success": True, "message": "Notification marked as read"}

@router.post("/mark-all-read")
def mark_all_notifications_read(recipient_id: int = None, db: Session = Depends(get_db)):
    """Mark all notifications as read."""
    query = db.query(Notification).filter(Notification.is_read == False)
    if recipient_id:
        query = query.filter(Notification.recipient_id == recipient_id)
    query.update({Notification.is_read: True}, synchronize_session=False)
    db.commit()
    return {"success": True, "message": "All notifications marked as read"}

@router.get("/audit", response_model=List[AuditLogResponse])
def get_audit_logs(limit: int = 100, db: Session = Depends(get_db)):
    """Retrieve system security and operation audit trail logs."""
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
