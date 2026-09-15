from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.email_service import email_service

router = APIRouter()

@router.post("/sync")
async def sync_emails_manual(db: Session = Depends(get_db)):
    """Manual trigger to poll Gmail inbox and execute AI triage pipeline.
    If Gmail is not configured, returns a clear warning and manual complaint intake remains available.
    """
    result = await email_service.sync_emails(db=db)
    return result

@router.get("/status")
def get_email_status():
    """Returns Gmail integration configuration status and active intake mode."""
    return email_service.get_status()
