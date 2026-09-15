import json
from datetime import datetime
from typing import Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from app.models.operations import AuditLog

class AuditService:
    @staticmethod
    def _format_value(val: Any) -> Optional[str]:
        if val is None:
            return None
        if isinstance(val, (dict, list)):
            return json.dumps(val)
        return str(val)

    @classmethod
    def log_event(
        cls,
        db: Session,
        action: str,
        user: Optional[str] = "SYSTEM",
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
        entity_type: str = "COMPLAINT",
        entity_id: Optional[str] = None,
        user_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """
        Records an immutable audit event storing:
        user, action, timestamp, old_value, new_value, metadata.
        """
        meta = metadata if metadata is not None else (details or {})
        entry = AuditLog(
            user=user or "SYSTEM",
            action=action,
            old_value=cls._format_value(old_value),
            new_value=cls._format_value(new_value),
            details_json=meta,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            user_id=user_id,
            ip_address=ip_address,
            created_at=datetime.utcnow()
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

audit_service = AuditService()
