from datetime import datetime, timedelta
from app.core.config import settings

class SLAService:
    @staticmethod
    def calculate_deadline(urgency: str) -> datetime:
        """Calculates SLA target completion deadline based on urgency tier."""
        hours_map = {
            "critical": settings.SLA_HOURS_CRITICAL,
            "high": settings.SLA_HOURS_HIGH,
            "medium": settings.SLA_HOURS_MEDIUM,
            "low": settings.SLA_HOURS_LOW
        }
        hours = hours_map.get((urgency or "medium").lower(), 24)
        return datetime.utcnow() + timedelta(hours=hours)

    @staticmethod
    def is_breached(deadline: datetime) -> bool:
        """Checks if a deadline has been breached."""
        if not deadline:
            return False
        return datetime.utcnow() > deadline

sla_service = SLAService()
