import os
import base64
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.complaint import Complaint
from app.models.operations import EmailMessage
from app.models.organization import Department
from app.ai.ai_orchestrator import ai_orchestrator
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailIngestionService:
    @staticmethod
    def is_configured() -> bool:
        """Checks if Google OAuth client secrets or active token file exists."""
        return os.path.exists(settings.GMAIL_CREDENTIALS_PATH) or os.path.exists(settings.GMAIL_TOKEN_PATH)

    @classmethod
    def get_gmail_client(cls):
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        creds = None
        if os.path.exists(settings.GMAIL_TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(settings.GMAIL_TOKEN_PATH, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            elif os.path.exists(settings.GMAIL_CREDENTIALS_PATH):
                flow = InstalledAppFlow.from_client_secrets_file(settings.GMAIL_CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)
            else:
                raise FileNotFoundError(f"Google Cloud credentials not found at {settings.GMAIL_CREDENTIALS_PATH}")

            with open(settings.GMAIL_TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())

        return build('gmail', 'v1', credentials=creds)

    @classmethod
    async def sync_emails(cls, db: Session, max_results: int = 10) -> Dict[str, Any]:
        """Manually triggered Gmail ingestion: polls labeled messages, runs AI pipeline, and routes."""
        if not cls.is_configured():
            return {
                "status": "warning",
                "message": "Gmail OAuth credentials not configured on the local system. Manual web intake remains active.",
                "synced_count": 0,
                "timestamp": datetime.utcnow().isoformat()
            }

        try:
            service = cls.get_gmail_client()
            label_name = settings.GMAIL_COMPLAINTS_LABEL
            
            # Find label id
            labels_res = service.users().labels().list(userId='me').execute()
            label_id = None
            for lbl in labels_res.get('labels', []):
                if lbl['name'].lower() == label_name.lower():
                    label_id = lbl['id']
                    break

            kwargs = {"userId": "me", "maxResults": max_results}
            if label_id:
                kwargs["labelIds"] = [label_id]

            messages_res = service.users().messages().list(**kwargs).execute()
            messages = messages_res.get('messages', [])

            synced_count = 0
            for msg_meta in messages:
                msg_id = msg_meta['id']

                # Check if already imported
                existing_email = db.query(EmailMessage).filter(EmailMessage.message_id == msg_id).first()
                if existing_email:
                    continue

                msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
                headers = msg.get('payload', {}).get('headers', [])

                subject = "Customer Complaint"
                sender = "customer@example.com"
                for h in headers:
                    if h['name'].lower() == 'subject':
                        subject = h['value']
                    elif h['name'].lower() == 'from':
                        sender = h['value']

                body = ""
                payload = msg.get('payload', {})
                if 'parts' in payload:
                    for part in payload['parts']:
                        if part.get('mimeType') == 'text/plain':
                            data = part.get('body', {}).get('data', '')
                            if data:
                                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                                break
                else:
                    data = payload.get('body', {}).get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')

                # Generate Ticket Number
                total_tickets = db.query(Complaint).count() + 10001
                ticket_num = f"CMP-{total_tickets}"

                # Run Full AI Analysis Pipeline
                ai_res = await ai_orchestrator.process_complaint_full(
                    subject=subject,
                    body=body or subject,
                    customer_name=sender.split('<')[0].strip(),
                    ticket_number=ticket_num,
                    db=db
                )

                # Find or assign department ID
                dept_obj = db.query(Department).filter(Department.name.ilike(f"%{ai_res['department_name']}%")).first()
                dept_id = dept_obj.id if dept_obj else None

                # Calculate SLA deadline
                sla_hours = getattr(settings, f"SLA_HOURS_{ai_res['urgency'].upper()}", 24)
                sla_deadline = datetime.utcnow() + timedelta(hours=sla_hours)

                # Persist Complaint
                complaint = Complaint(
                    ticket_number=ticket_num,
                    customer_name=sender.split('<')[0].strip(),
                    customer_email=sender,
                    subject=subject,
                    body=body or subject,
                    cleaned_text=ai_res["cleaned_text"],
                    category=ai_res["category"],
                    sub_category=ai_res["sub_category"],
                    department_id=dept_id,
                    urgency=ai_res["urgency"],
                    priority_score=ai_res["priority_score"],
                    priority_level=ai_res["priority_level"],
                    sentiment=ai_res["sentiment"],
                    emotion=ai_res["emotion"],
                    status="New",
                    source="Email",
                    sla_deadline=sla_deadline,
                    is_duplicate=ai_res["is_duplicate"],
                    duplicate_of_id=ai_res["duplicate_of_id"],
                    embedding=ai_res["embedding"]
                )
                db.add(complaint)
                db.flush()

                # Record Email Ingestion Message
                email_record = EmailMessage(
                    complaint_id=complaint.id,
                    message_id=msg_id,
                    direction="INBOUND",
                    sender=sender,
                    recipient="support@company.com",
                    subject=subject,
                    body_text=body
                )
                db.add(email_record)

                # Dispatch Notification
                notification_service.create_notification(
                    db=db,
                    title=f"New {ai_res['urgency']} Ticket: {ticket_num}",
                    message=f"Ingested from Gmail: {subject[:80]} -> Routed to {ai_res['department_name']}",
                    notification_type="CRITICAL_TICKET" if ai_res["urgency"] == "Critical" else "INFO",
                    department_id=dept_id,
                    link_url=f"/complaints/{complaint.id}"
                )

                synced_count += 1

            db.commit()
            return {
                "status": "success",
                "message": f"Polled Gmail inbox. Ingested and triaged {synced_count} new tickets.",
                "synced_count": synced_count,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Gmail synchronization failed: {e}")
            return {
                "status": "error",
                "message": f"Gmail synchronization failed: {str(e)}",
                "synced_count": 0,
                "timestamp": datetime.utcnow().isoformat()
            }

gmail_service = GmailIngestionService()
