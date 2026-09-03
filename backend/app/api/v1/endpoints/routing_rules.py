import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.organization import RoutingRule
from app.schemas.operations import RoutingRuleCreate, RoutingRuleUpdate, RoutingRuleResponse

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=List[RoutingRuleResponse])
def list_routing_rules(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Fetches all configurable routing rules stored in the database."""
    query = db.query(RoutingRule)
    if is_active is not None:
        query = query.filter(RoutingRule.is_active == is_active)
    return query.order_by(RoutingRule.id.asc()).all()

@router.post("/", response_model=RoutingRuleResponse, status_code=status.HTTP_201_CREATED)
def create_routing_rule(
    rule_in: RoutingRuleCreate,
    db: Session = Depends(get_db)
):
    """Creates a new configurable routing rule in the database."""
    existing = db.query(RoutingRule).filter(
        RoutingRule.trigger_keyword.ilike(rule_in.trigger_keyword.strip())
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Routing rule for trigger '{rule_in.trigger_keyword}' already exists."
        )

    rule = RoutingRule(
        trigger_keyword=rule_in.trigger_keyword.strip(),
        department_name=rule_in.department_name.strip(),
        team_name=rule_in.team_name.strip() if rule_in.team_name else None,
        priority_override=rule_in.priority_override,
        sla_hours=rule_in.sla_hours,
        description=rule_in.description,
        is_active=rule_in.is_active
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    logger.info(f"Created configurable routing rule: {rule.trigger_keyword} -> {rule.department_name}/{rule.team_name}")
    return rule

@router.get("/{rule_id}", response_model=RoutingRuleResponse)
def get_routing_rule(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """Fetches a specific configurable routing rule by ID."""
    rule = db.query(RoutingRule).filter(RoutingRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Routing rule not found")
    return rule

@router.put("/{rule_id}", response_model=RoutingRuleResponse)
def update_routing_rule(
    rule_id: int,
    rule_in: RoutingRuleUpdate,
    db: Session = Depends(get_db)
):
    """Updates an existing configurable routing rule in the database."""
    rule = db.query(RoutingRule).filter(RoutingRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Routing rule not found")

    update_data = rule_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        if val is not None and isinstance(val, str):
            val = val.strip()
        setattr(rule, field, val)

    db.commit()
    db.refresh(rule)
    return rule

@router.delete("/{rule_id}", status_code=status.HTTP_200_OK)
def delete_routing_rule(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """Deletes a configurable routing rule from the database."""
    rule = db.query(RoutingRule).filter(RoutingRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Routing rule not found")

    db.delete(rule)
    db.commit()
    return {"message": f"Routing rule {rule_id} deleted successfully"}
