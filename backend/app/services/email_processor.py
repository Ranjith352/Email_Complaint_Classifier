import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.schemas.complaint import ComplaintCreate
from app.models.operations import EmailMessage
from app.services.complaint_service import complaint_service

logger = logging.getLogger(__name__)

class EmailProcessor:
    """Processes inbound emails through the complete complaint lifecycle:
    Gmail -> New Email -> Extract (sender, subject, body) -> Create Complaint ->
    AI Analysis -> Department Routing -> Team Assignment -> Agent Assignment -> Notification.
    """

    @staticmethod
    async def process_email(
        db: Session,
        sender: str,
        subject: str,
        body: str,
        message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Executes the complete ingestion and triage pipeline for an incoming email."""
        # 1. Deduplication check if message_id is provided
        if message_id:
            existing = db.query(EmailMessage).filter(EmailMessage.message_id == message_id).first()
            if existing:
                logger.info(f"Email {message_id} already ingested as Complaint #{existing.complaint_id}")
                return {
                    "status": "skipped",
                    "reason": "duplicate_message",
                    "complaint_id": existing.complaint_id
                }

        # 2. Extract sender details
        customer_email = sender
        customer_name = "Email Customer"
        if "<" in sender and ">" in sender:
            parts = sender.split("<")
            customer_name = parts[0].strip(' "')
            customer_email = parts[1].strip("> ").strip()
        elif "@" in sender:
            customer_name = sender.split("@")[0].replace(".", " ").title()

        # 3. Create Complaint & trigger AI Analysis -> Department -> Team -> Agent -> Notification
        complaint_in = ComplaintCreate(
            subject=subject.strip() or "Inbound Support Email",
            body=body.strip() or subject.strip() or "No email body provided.",
            customer_email=customer_email,
            customer_name=customer_name or "Customer",
            source="EMAIL"
        )

        complaint = await complaint_service.process_and_create_complaint(db, complaint_in)

        # 4. Record inbound email log
        email_record = EmailMessage(
            message_id=message_id or f"manual-{complaint.id}-{int(datetime.utcnow().timestamp())}",
            complaint_id=complaint.id,
            sender=sender,
            recipient="support@company.com",
            subject=subject,
            body_text=body,
            status="PROCESSED",
            received_at=datetime.utcnow()
        )
        db.add(email_record)
        db.commit()
        db.refresh(email_record)

        logger.info(
            f"Successfully processed email -> Complaint #{complaint.id} ({complaint.complaint_number}), "
            f"Dept: {complaint.department.name if complaint.department else 'Unassigned'}, "
            f"Priority: {complaint.priority_level}"
        )

        return {
            "status": "success",
            "complaint_id": complaint.id,
            "ticket_number": complaint.complaint_number,
            "department": complaint.department.name if complaint.department else "Unassigned",
            "team": complaint.team.name if complaint.team else "Unassigned",
            "priority": complaint.priority_level,
            "urgency": complaint.urgency,
            "sla_deadline": complaint.sla_deadline.isoformat() if complaint.sla_deadline else None
        }

email_processor = EmailProcessor()
