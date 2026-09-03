from typing import Dict, Any
from sqlalchemy.orm import Session
from app.schemas.complaint import ComplaintCreate
from app.services.complaint_service import complaint_service

class EmailProcessor:
    @staticmethod
    async def process_inbound_email(
        db: Session,
        sender: str,
        subject: str,
        body: str
    ) -> Dict[str, Any]:
        """Parses an inbound email, normalizes metadata, and triggers automated complaint triage."""
        complaint_in = ComplaintCreate(
            subject=subject,
            body=body or subject,
            customer_email=sender if "@" in sender else "customer@example.com",
            customer_name=sender.split("<")[0].strip() or "Email User",
            source="Email"
        )
        complaint = await complaint_service.process_and_create_complaint(db, complaint_in)
        return {
            "ticket_number": complaint.ticket_number,
            "category": complaint.category,
            "urgency": complaint.urgency,
            "priority": complaint.priority_level
        }

email_processor = EmailProcessor()
