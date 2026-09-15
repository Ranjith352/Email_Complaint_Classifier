import base64
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailService:
    """Handles Gmail API communication using GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET from .env.
    NEVER hardcodes developer credentials.
    """

    @staticmethod
    def is_configured() -> bool:
        """Returns True only if user has configured GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET in .env."""
        client_id = getattr(settings, "GMAIL_CLIENT_ID", "") or ""
        client_secret = getattr(settings, "GMAIL_CLIENT_SECRET", "") or ""
        return bool(client_id.strip() and client_secret.strip())

    @classmethod
    def get_client(cls):
        """Constructs Gmail API client if credentials are configured."""
        if not cls.is_configured():
            return None

        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build

            # In production OAuth flow, credentials would be obtained via OAuth token exchange with GMAIL_CLIENT_ID/SECRET
            creds = Credentials(
                None,
                client_id=settings.GMAIL_CLIENT_ID,
                client_secret=settings.GMAIL_CLIENT_SECRET,
                scopes=SCOPES
            )
            return build('gmail', 'v1', credentials=creds)
        except Exception as e:
            logger.warning(f"Failed to initialize Gmail API client: {e}")
            return None

    @classmethod
    def fetch_new_messages(cls, max_results: int = 10) -> List[Dict[str, Any]]:
        """Fetches new messages and extracts sender, subject, and body."""
        if not cls.is_configured():
            logger.info("Gmail integration is unconfigured. Skipping message fetch.")
            return []

        service = cls.get_client()
        if not service:
            return []

        messages_data = []
        try:
            label_name = getattr(settings, "GMAIL_COMPLAINTS_LABEL", "Complaints")
            # Query messages with complaints label or INBOX
            res = service.users().messages().list(userId='me', maxResults=max_results, q=f"label:{label_name}").execute()
            messages = res.get('messages', [])

            for msg_meta in messages:
                msg_id = msg_meta['id']
                raw_msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
                headers = raw_msg.get('payload', {}).get('headers', [])

                subject = "Customer Complaint"
                sender = "customer@example.com"
                for h in headers:
                    if h.get('name', '').lower() == 'subject':
                        subject = h.get('value', subject)
                    elif h.get('name', '').lower() == 'from':
                        sender = h.get('value', sender)

                body = cls._extract_body(raw_msg.get('payload', {}))
                messages_data.append({
                    "message_id": msg_id,
                    "sender": sender,
                    "subject": subject,
                    "body": body or subject,
                    "received_at": datetime.utcnow()
                })
        except Exception as e:
            logger.error(f"Error fetching Gmail messages: {e}")

        return messages_data

    @staticmethod
    def _extract_body(payload: Dict[str, Any]) -> str:
        """Recursively parses email body from multipart payload."""
        body = ""
        if 'parts' in payload:
            for part in payload['parts']:
                mime = part.get('mimeType', '')
                data = part.get('body', {}).get('data')
                if data and mime in ['text/plain', 'text/html']:
                    try:
                        decoded = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        if mime == 'text/plain':
                            return decoded.strip()
                        body = decoded.strip()
                    except Exception:
                        pass
                elif 'parts' in part:
                    sub_body = GmailService._extract_body(part)
                    if sub_body:
                        return sub_body
        else:
            data = payload.get('body', {}).get('data')
            if data:
                try:
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore').strip()
                except Exception:
                    pass
        return body

gmail_service = GmailService()
