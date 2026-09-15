from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.operations import Notification, AuditLog
from app.schemas.operations import NotificationResponse, AuditLogResponse
from app.services.notification_service import notification_service

router = APIRouter()

@router.get("", response_model=List[NotificationResponse])
@router.get("/", response_model=List[NotificationResponse])
@router.get("/notifications", response_model=List[NotificationResponse])
def get_notifications(
    unread_only: bool = Query(False, description="Filter only unread alerts"),
    department_id: Optional[int] = Query(None, description="Optional department filter"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Retrieves chronological in-app notification history with structured details."""
    return notification_service.get_notifications(
        db=db,
        unread_only=unread_only,
        department_id=department_id,
        limit=limit
    )

@router.post("/{notification_id}/read")
@router.post("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: int, db: Session = Depends(get_db)):
    """Marks a specific in-app notification as read."""
    success = notification_service.mark_read(db=db, notification_id=notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification marked as read", "notification_id": notification_id}

@router.post("/mark-all-read")
def mark_all_notifications_read(
    department_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Marks all active notifications as read."""
    count = notification_service.mark_all_read(db=db, department_id=department_id)
    return {"message": f"Marked {count} notifications as read", "count": count}

@router.get("/audit", response_model=List[AuditLogResponse])
def get_audit_logs(limit: int = 100, db: Session = Depends(get_db)):
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
