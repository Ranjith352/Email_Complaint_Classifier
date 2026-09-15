import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.gmail_service import gmail_service
from app.services.email_processor import email_processor

logger = logging.getLogger(__name__)

class EmailService:
    """Enterprise coordination service for Gmail synchronization and email complaint ingestion.
    Gracefully falls back to manual intake if Gmail is unconfigured.
    """

    @staticmethod
    def get_status() -> Dict[str, Any]:
        """Returns Gmail configuration status and active ingestion mode."""
        configured = gmail_service.is_configured()
        return {
            "configured": configured,
            "mode": "Active Gmail OAuth 2.0 Ingestion" if configured else "Manual Complaint Intake (Gmail Unconfigured)",
            "client_id_configured": bool(getattr(settings, "GMAIL_CLIENT_ID", "")),
            "redirect_uri": getattr(settings, "GMAIL_REDIRECT_URI", ""),
            "manual_intake_available": True,
            "message": (
                "Gmail OAuth credentials are active."
                if configured
                else "Gmail is not configured. Manual complaint creation remains fully available."
            )
        }

    @classmethod
    async def sync_emails(cls, db: Session, max_results: int = 10) -> Dict[str, Any]:
        """Triggers email synchronization: fetches new emails, processes complaints, or returns graceful warning."""
        if not gmail_service.is_configured():
            logger.info("Sync requested but Gmail is unconfigured. Manual intake remains active.")
            return {
                "status": "warning",
                "configured": False,
                "message": "Gmail is not configured in .env (GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET). Manual complaint creation remains fully active.",
                "synced_count": 0,
                "processed_complaints": []
            }

        messages = gmail_service.fetch_new_messages(max_results=max_results)
        processed = []
        for msg in messages:
            res = await email_processor.process_email(
                db=db,
                sender=msg["sender"],
                subject=msg["subject"],
                body=msg["body"],
                message_id=msg.get("message_id")
            )
            processed.append(res)

        return {
            "status": "success",
            "configured": True,
            "synced_count": len(processed),
            "processed_complaints": processed
        }

email_service = EmailService()
