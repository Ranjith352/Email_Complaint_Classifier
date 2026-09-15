from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.operations import SLARule

class SLAService:
    DEFAULT_RULES = {
        "critical": 2,
        "high": 8,
        "medium": 24,
        "low": 72
    }

    @classmethod
    def get_sla_hours_for_urgency(cls, urgency: str, db: Optional[Session] = None) -> int:
        """Retrieves target SLA hours for urgency level from DB or config defaults."""
        urgency_clean = (urgency or "medium").strip().lower()
        if db:
            rule = db.query(SLARule).filter(
                SLARule.urgency_level.ilike(urgency_clean),
                SLARule.is_active == True
            ).first()
            if rule and rule.max_resolution_hours:
                return rule.max_resolution_hours

        config_hours = getattr(settings, f"SLA_HOURS_{urgency_clean.upper()}", None)
        if config_hours is not None:
            return config_hours

        return cls.DEFAULT_RULES.get(urgency_clean, 24)

    @classmethod
    def get_rule_hours(cls, urgency: str, db: Optional[Session] = None) -> int:
        return cls.get_sla_hours_for_urgency(urgency, db)

    @classmethod
    def calculate_deadline(cls, urgency: str, created_at: Optional[datetime] = None, db: Optional[Session] = None) -> datetime:
        """Calculates SLA target completion deadline based on urgency tier."""
        hours = cls.get_sla_hours_for_urgency(urgency, db)
        start_time = created_at or datetime.utcnow()
        return start_time + timedelta(hours=hours)

    @staticmethod
    def is_breached(deadline: Optional[datetime]) -> bool:
        """Checks if a deadline has been breached."""
        if not deadline:
            return False
        return datetime.utcnow() > deadline

    @classmethod
    def get_sla_metrics(cls, complaint) -> Dict[str, Any]:
        """
        Calculates real-time SLA metrics:
        - SLA deadline
        - Time remaining
        - SLA percentage elapsed
        - Warnings:
            75% elapsed -> Warning
            90% elapsed -> Critical warning
            100% -> SLA BREACHED
        - Allow escalation
        """
        now = datetime.utcnow()
        created_at = getattr(complaint, "created_at", None) or (now - timedelta(hours=1))
        deadline = getattr(complaint, "sla_deadline", None)

        if not deadline:
            urgency = getattr(complaint, "urgency", "Medium")
            deadline = cls.calculate_deadline(urgency, created_at)

        total_duration_seconds = max(1.0, (deadline - created_at).total_seconds())
        elapsed_seconds = max(0.0, (now - created_at).total_seconds())
        remaining_seconds = (deadline - now).total_seconds()

        percentage_elapsed = round(min(150.0, max(0.0, (elapsed_seconds / total_duration_seconds) * 100.0)), 1)
        is_breached = remaining_seconds <= 0

        # Warning threshold logic
        if percentage_elapsed >= 100.0 or is_breached:
            warning_level = "BREACHED"
            warning_label = "SLA BREACHED"
            warning_description = "Resolution target has exceeded the contractual SLA commitment."
            color_tier = "red"
        elif percentage_elapsed >= 90.0:
            warning_level = "CRITICAL_WARNING"
            warning_label = "Critical warning"
            warning_description = "90% of allocated SLA duration elapsed. Immediate intervention required."
            color_tier = "rose"
        elif percentage_elapsed >= 75.0:
            warning_level = "WARNING"
            warning_label = "Warning"
            warning_description = "75% of SLA duration elapsed. Approaching breach boundary."
            color_tier = "amber"
        else:
            warning_level = "ON_TRACK"
            warning_label = "On Track"
            warning_description = "Operating comfortably within designated resolution targets."
            color_tier = "emerald"

        # Formatted remaining string
        if remaining_seconds > 0:
            rem_hours = int(remaining_seconds // 3600)
            rem_mins = int((remaining_seconds % 3600) // 60)
            time_remaining_str = f"{rem_hours}h {rem_mins}m remaining" if rem_hours > 0 else f"{rem_mins}m remaining"
        else:
            over_seconds = abs(remaining_seconds)
            over_hours = int(over_seconds // 3600)
            over_mins = int((over_seconds % 3600) // 60)
            time_remaining_str = f"Breached by {over_hours}h {over_mins}m" if over_hours > 0 else f"Breached by {over_mins}m"

        is_escalated = bool(getattr(complaint, "is_escalated", False))
        status = str(getattr(complaint, "status", "NEW")).upper()
        can_escalate = (status not in ("RESOLVED", "CLOSED")) and not is_escalated

        return {
            "sla_deadline": deadline.isoformat() if hasattr(deadline, "isoformat") else str(deadline),
            "time_remaining_seconds": int(remaining_seconds),
            "time_remaining_formatted": time_remaining_str,
            "percentage_elapsed": percentage_elapsed,
            "warning_level": warning_level,
            "warning_label": warning_label,
            "warning_description": warning_description,
            "color_tier": color_tier,
            "is_breached": is_breached,
            "is_escalated": is_escalated,
            "can_escalate": can_escalate
        }

    @classmethod
    def get_all_rules(cls, db: Session) -> List[Dict[str, Any]]:
        """Retrieves configurable rules list."""
        rules = db.query(SLARule).filter(SLARule.is_active == True).all()
        if not rules:
            return [
                {"urgency": k.capitalize(), "hours": v, "default": True}
                for k, v in cls.DEFAULT_RULES.items()
            ]
        return [
            {
                "id": r.id,
                "urgency": r.urgency_level.capitalize(),
                "hours": r.max_resolution_hours,
                "priority_level": r.priority_level,
                "escalation_email": r.escalation_email
            }
            for r in rules
        ]

sla_service = SLAService()
