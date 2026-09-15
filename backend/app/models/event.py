from app.models.complaint import ComplaintEvent
from app.models.operations import AuditLog

Event = ComplaintEvent
__all__ = ["Event", "ComplaintEvent", "AuditLog"]
