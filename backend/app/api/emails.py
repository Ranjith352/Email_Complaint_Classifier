from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.email_service import email_service

router = APIRouter()

@router.post("/sync")
async def sync_emails(db: Session = Depends(get_db)):
    """Poll Gmail inbox and trigger automated AI triage pipeline for new emails."""
    result = await email_service.sync_emails(db=db)
    return result

@router.get("/status")
def get_email_status():
    """Retrieve current Gmail ingestion service status and connection health."""
    return email_service.get_status()
