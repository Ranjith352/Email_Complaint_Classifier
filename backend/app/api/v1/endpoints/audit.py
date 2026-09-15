from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.operations import AuditLog
from app.schemas.operations import AuditLogResponse

router = APIRouter()

@router.get("/", response_model=List[AuditLogResponse])
def get_audit_logs(limit: int = 100, db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "user": l.user or (f"User #{l.user_id}" if l.user_id else "SYSTEM"),
            "user_id": l.user_id,
            "action": l.action,
            "entity_type": l.entity_type or "COMPLAINT",
            "entity_id": l.entity_id,
            "old_value": l.old_value,
            "new_value": l.new_value,
            "metadata": l.get_metadata(),
            "ip_address": l.ip_address,
            "timestamp": l.created_at,
            "created_at": l.created_at,
        }
        for l in logs
    ]
