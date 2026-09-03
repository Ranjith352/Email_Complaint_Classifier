from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.operations import AuditLog

class AuditService:
    @staticmethod
    def log_event(
        db: Session,
        action: str,
        entity_type: str,
        entity_id: str,
        user_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """Records an immutable audit event in the database."""
        entry = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            user_id=user_id,
            details_json=details or {},
            ip_address=ip_address
        )
        db.add(entry)
        db.commit()
        return entry

audit_service = AuditService()
