from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.gmail_service import gmail_service

router = APIRouter()

@router.post("/sync")
async def sync_emails_manual(db: Session = Depends(get_db)):
    """Manual trigger to poll Gmail inbox and execute AI triage pipeline."""
    result = await gmail_service.sync_emails(db=db)
    return result

@router.get("/status")
def get_email_status():
    """Returns whether Gmail OAuth credentials are configured."""
    configured = gmail_service.is_configured()
    return {
        "configured": configured,
        "mode": "Active OAuth 2.0 Ingestion" if configured else "Manual Intake Only (No OAuth)",
        "endpoint": "POST /api/emails/sync"
    }
