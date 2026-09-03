from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.services.gmail_service import gmail_service

router = APIRouter()

@router.post("/sync")
def sync_gmail(db: Session = Depends(get_db)):
    """Triggers Gmail inbox polling and sync."""
    result = gmail_service.sync_emails(db=db)
    return result

@router.get("/status")
def gmail_status():
    """Returns the current Gmail OAuth integration status."""
    configured = gmail_service.is_configured()
    return {
        "configured": configured,
        "mode": "Active OAuth 2.0 Ingestion" if configured else "Setup Required",
        "description": "Polls labeled emails from Gmail and processes them through the NLP triage pipeline."
    }
