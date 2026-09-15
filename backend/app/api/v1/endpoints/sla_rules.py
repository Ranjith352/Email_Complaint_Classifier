from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.operations import SLARule
from app.services.sla_service import sla_service

router = APIRouter()

class SLARuleUpdate(BaseModel):
    hours: int
    urgency: Optional[str] = None

@router.get("")
@router.get("/")
def get_sla_rules(db: Session = Depends(get_db)):
    """Returns active configurable SLA target hours."""
    rules_list = sla_service.get_all_rules(db)
    rules_dict = {r["urgency"].upper(): r["hours"] for r in rules_list}
    return {
        "rules": rules_dict,
        "list": rules_list
    }

@router.put("/{urgency}", response_model=Dict[str, Any])
def update_sla_rule(urgency: str, update: SLARuleUpdate, db: Session = Depends(get_db)):
    """Updates the target SLA resolution hours for a specific urgency level."""
    urg = urgency.strip().lower()
    rule = db.query(SLARule).filter(SLARule.urgency_level.ilike(urg)).first()
    if not rule:
        rule = SLARule(
            priority_level="P1" if urg == "critical" else "P2" if urg == "high" else "P3" if urg == "medium" else "P4",
            urgency_level=urg.capitalize(),
            max_resolution_hours=update.hours,
            is_active=True
        )
        db.add(rule)
    else:
        rule.max_resolution_hours = update.hours
        rule.is_active = True
    db.commit()
    db.refresh(rule)
    return {
        "urgency": rule.urgency_level,
        "hours": rule.max_resolution_hours,
        "new_hours": rule.max_resolution_hours,
        "message": f"SLA for {rule.urgency_level} updated to {rule.max_resolution_hours} hours."
    }
