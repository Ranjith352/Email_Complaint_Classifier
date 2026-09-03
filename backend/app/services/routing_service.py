import logging
from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy.orm import Session

from app.models.organization import Department, Team, Agent
from app.ai.classifier import progressive_classifier

logger = logging.getLogger(__name__)

# Predefined skill taxonomy for standard category/subcategory pairs
SKILL_TAXONOMY_MAP = {
    ("Billing", "Duplicate Payment"): ["billing", "payments", "duplicate payment", "refunds"],
    ("Billing", "Refund Request"): ["billing", "refunds", "payments"],
    ("Billing", "Unauthorized Charge"): ["billing", "fraud", "payments", "security"],
    ("Billing", "Invoice Dispute"): ["billing", "invoicing", "accounts receivable"],
    ("Billing", "Subscription Cancellation"): ["billing", "subscriptions", "retention"],
    ("Technical Problem", "Application Support"): ["technical support", "application support", "troubleshooting"],
    ("Technical Problem", "Software Bug"): ["software bug", "debugging", "engineering"],
    ("Technical Problem", "System Outage"): ["infrastructure", "devops", "system outage"],
    ("Technical Problem", "Login Issues"): ["auth", "account access", "technical support"],
    ("Security Issue", "Account Takeover / Breach"): ["security", "incident response", "investigation"],
    ("Security Issue", "Credential Theft"): ["security", "auth", "threat analysis"],
    ("Security Issue", "Phishing"): ["security", "threat intelligence"],
    ("Customer Support", "General Inquiry"): ["customer support", "general inquiry", "triage"],
    ("Customer Support", "Feedback"): ["customer support", "product feedback"]
}

class RoutingService:
    """Enterprise 8-Stage Routing & Assignment Service.

    Flow:
    AI Classification
           |
           v
        Category
           |
           v
      Subcategory
           |
           v
       Department
           |
           v
          Team
           |
           v
     Required Skills
           |
           v
    Available Agents
           |
           v
        Workload
           |
           v
       Assignment
    """

    # -------------------------------------------------------------------------
    # Stage 1-3: AI Classification -> Category -> Subcategory
    # -------------------------------------------------------------------------
    @staticmethod
    def classify_complaint(
        text: str,
        ai_classification: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Classifies incoming complaint text into Category, Subcategory, Department, and Team."""
        if ai_classification:
            category = ai_classification.get("category", "Customer Support")
            subcategory = ai_classification.get("sub_category", ai_classification.get("subcategory", "General Inquiry"))
            department = ai_classification.get("department", ai_classification.get("department_name", "Customer Support"))
            team = ai_classification.get("team", ai_classification.get("team_name", "General Triage"))
            confidence = float(ai_classification.get("confidence", ai_classification.get("cat_confidence", 0.90)))
            return {
                "category": category,
                "subcategory": subcategory,
                "department": department,
                "team": team,
                "confidence": confidence
            }

        # Run AI classifier
        cls_res = progressive_classifier.classify(text)
        category = cls_res.get("category", "Customer Support")
        subcategory = cls_res.get("sub_category", "General Inquiry")
        department = cls_res.get("department", "Customer Support")
        confidence = float(cls_res.get("confidence", 0.90))

        # Infer team based on subcategory
        sub_lower = subcategory.lower()
        if "duplicate" in sub_lower or "payment" in sub_lower or "charge" in sub_lower:
            team = "Payments"
        elif "refund" in sub_lower:
            team = "Refunds"
        elif "invoice" in sub_lower:
            team = "Billing"
        elif "bug" in sub_lower or "software" in sub_lower:
            team = "Application Support"
        elif "outage" in sub_lower or "server" in sub_lower:
            team = "Infrastructure"
        elif "security" in sub_lower or "breach" in sub_lower or "hack" in sub_lower:
            team = "Security Operations"
        else:
            team = cls_res.get("team", "General Triage")

        return {
            "category": category,
            "subcategory": subcategory,
            "department": department,
            "team": team,
            "confidence": confidence
        }

    # -------------------------------------------------------------------------
    # Stage 4: Resolve Department in Database
    # -------------------------------------------------------------------------
    @staticmethod
    def resolve_department(db: Session, department_name: str) -> Optional[Department]:
        """Resolves active department by exact match or substring fallback."""
        active_depts = db.query(Department).filter(Department.is_active == True).all()
        if not active_depts:
            return None

        dept_lower = department_name.strip().lower()

        # Prioritize exact match first
        for d in active_depts:
            if d.name.strip().lower() == dept_lower:
                return d

        # Substring match fallback
        for d in active_depts:
            if d.name.strip().lower() in dept_lower or dept_lower in d.name.strip().lower():
                return d

        # Fallback to first available department
        return active_depts[0]

    # -------------------------------------------------------------------------
    # Stage 5: Resolve Team under Department
    # -------------------------------------------------------------------------
    @staticmethod
    def resolve_team(db: Session, department_id: int, team_name: Optional[str] = None) -> Optional[Team]:
        """Resolves active team within department by exact match or substring fallback."""
        teams = db.query(Team).filter(
            Team.department_id == department_id,
            Team.is_active == True
        ).all()
        if not teams:
            return None

        if team_name:
            t_lower = team_name.strip().lower()
            # Prioritize exact match
            for t in teams:
                if t.name.strip().lower() == t_lower:
                    return t
            # Substring fallback
            for t in teams:
                if t.name.strip().lower() in t_lower or t_lower in t.name.strip().lower():
                    return t

        return teams[0]

    # -------------------------------------------------------------------------
    # Stage 6: Derive Required Skills
    # -------------------------------------------------------------------------
    @staticmethod
    def derive_required_skills(category: str, subcategory: str, team_name: Optional[str] = None) -> List[str]:
        """Derives required agent skills based on category, subcategory, and specialized team."""
        # 1. Lookup in predefined taxonomy
        key = (category, subcategory)
        if key in SKILL_TAXONOMY_MAP:
            return list(SKILL_TAXONOMY_MAP[key])

        # 2. Dynamic generation
        skills = []
        if category:
            skills.append(category.lower().strip())
        if subcategory:
            skills.append(subcategory.lower().strip())
            for tok in subcategory.lower().split():
                if len(tok) > 3 and tok not in skills:
                    skills.append(tok)
        if team_name:
            t_clean = team_name.lower().strip()
            if t_clean not in skills:
                skills.append(t_clean)
        return skills

    # -------------------------------------------------------------------------
    # Stage 7 & 8: Filter Available Agents & Evaluate Workload
    # -------------------------------------------------------------------------
    @staticmethod
    def find_available_agents(
        db: Session,
        department_id: int,
        team_id: Optional[int] = None
    ) -> List[Agent]:
        """Fetches active, online agents with available workload capacity."""
        # Query active & available agents in the department under maximum workload capacity
        candidates = db.query(Agent).filter(
            Agent.department_id == department_id,
            Agent.availability == True,
            Agent.is_active == True,
            Agent.current_workload < Agent.max_workload
        ).all()

        # If no department agents available, check across enterprise active agents
        if not candidates:
            candidates = db.query(Agent).filter(
                Agent.availability == True,
                Agent.is_active == True,
                Agent.current_workload < Agent.max_workload
            ).all()

        return candidates

    @staticmethod
    def rank_and_assign_agent(
        db: Session,
        candidates: List[Agent],
        team_id: Optional[int] = None,
        required_skills: Optional[List[str]] = None
    ) -> Optional[Agent]:
        """Ranks candidate agents by team match, skill match, and workload capacity."""
        if not candidates:
            return None

        req_skills_set = {s.lower().strip() for s in (required_skills or [])}

        def score_agent(agent: Agent) -> float:
            score = 0.0

            # 1. Team Affinity (+60 points for exact team match)
            if team_id is not None and agent.team_id == team_id:
                score += 60.0

            # 2. Skill Overlap (+20 points per matching skill)
            if req_skills_set and agent.skills:
                agent_skills = {str(s).lower().strip() for s in agent.skills}
                matches = len(req_skills_set.intersection(agent_skills))
                score += matches * 20.0

            # 3. Workload Evaluation (+0 to +40 points: lower workload = higher score)
            if agent.max_workload > 0:
                capacity_ratio = 1.0 - (agent.current_workload / agent.max_workload)
                score += max(0.0, capacity_ratio * 40.0)

            # 4. Performance Tie-Breaker (+0 to +15 points)
            perf = agent.performance_score if agent.performance_score is not None else 80.0
            score += (perf / 100.0) * 15.0

            return score

        # Select the candidate with highest score (lowest workload, highest skill & team match)
        best_agent = max(candidates, key=score_agent)

        # Increment workload for chosen agent
        best_agent.current_workload += 1
        db.flush()

        return best_agent

    # -------------------------------------------------------------------------
    # Master Flow: Complete 8-Stage Routing Pipeline
    # -------------------------------------------------------------------------
    def execute_routing_pipeline(
        self,
        db: Session,
        complaint_text: str,
        ai_classification: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Executes the complete 8-stage routing pipeline:
        AI Classification -> Category -> Subcategory -> Department -> Team -> Required Skills -> Available Agents -> Workload -> Assignment
        """
        # Stage 1: AI Classification
        ai_meta = self.classify_complaint(complaint_text, ai_classification)

        # Stage 2: Category
        category = ai_meta["category"]

        # Stage 3: Subcategory
        subcategory = ai_meta["subcategory"]

        # Stage 4: Department
        dept = self.resolve_department(db, ai_meta["department"])
        dept_id = dept.id if dept else None
        dept_name = dept.name if dept else ai_meta["department"]

        # Stage 5: Team
        team = self.resolve_team(db, dept_id, ai_meta.get("team")) if dept_id else None
        team_id = team.id if team else None
        team_name = team.name if team else ai_meta.get("team")

        # Stage 6: Required Skills
        required_skills = self.derive_required_skills(category, subcategory, team_name)

        # Stage 7: Available Agents
        candidates = self.find_available_agents(db, dept_id, team_id) if dept_id else []

        # Stage 8 & 9: Workload Evaluation & Assignment
        assigned_agent = self.rank_and_assign_agent(
            db=db,
            candidates=candidates,
            team_id=team_id,
            required_skills=required_skills
        )

        return {
            "flow_status": "COMPLETED",
            "complaint_text": complaint_text,
            "classification": {
                "category": category,
                "subcategory": subcategory,
                "department": dept_name,
                "team": team_name,
                "confidence": ai_meta["confidence"]
            },
            "category": category,
            "subcategory": subcategory,
            "department_id": dept_id,
            "department_name": dept_name,
            "team_id": team_id,
            "team_name": team_name,
            "required_skills": required_skills,
            "available_agents_count": len(candidates),
            "assigned_agent_id": assigned_agent.id if assigned_agent else None,
            "assigned_agent_name": assigned_agent.name if assigned_agent else None,
            "assigned_agent_email": assigned_agent.email if assigned_agent else None,
            "assigned_agent_workload": assigned_agent.current_workload if assigned_agent else None
        }

    # -------------------------------------------------------------------------
    # Backward Compatibility Methods
    # -------------------------------------------------------------------------
    @staticmethod
    def get_configured_departments(db: Session) -> List[Department]:
        """Loads all active departments stored in PostgreSQL."""
        return db.query(Department).filter(Department.is_active == True).all()

    @staticmethod
    def get_teams_for_department(db: Session, department_id: int) -> List[Team]:
        """Loads all active teams under a department."""
        return db.query(Team).filter(Team.department_id == department_id, Team.is_active == True).all()

    @staticmethod
    def route_complaint(
        db: Session,
        department_name: Optional[str] = None,
        team_name: Optional[str] = None,
        text_content: Optional[str] = None
    ) -> Tuple[Optional[int], Optional[int], Optional[str]]:
        """Dynamically matches complaint text or category against departments and their specialized teams."""
        active_depts = db.query(Department).filter(Department.is_active == True).all()
        if not active_depts:
            return None, None, None

        # 1. Match by department name if provided
        if department_name:
            dept_lower = department_name.strip().lower()
            # Prioritize exact match first
            for dept in active_depts:
                if dept.name.strip().lower() == dept_lower:
                    team_id = RoutingService._find_team_id(db, dept.id, team_name, text_content)
                    return dept.id, team_id, dept.name
            # Substring fallback
            for dept in active_depts:
                if dept.name.strip().lower() in dept_lower or dept_lower in dept.name.strip().lower():
                    team_id = RoutingService._find_team_id(db, dept.id, team_name, text_content)
                    return dept.id, team_id, dept.name

        # 2. Dynamic database keywords matching
        if text_content:
            cleaned = text_content.lower()
            best_dept = None
            highest_score = 0
            for dept in active_depts:
                score = 0
                if dept.name.lower() in cleaned:
                    score += 5
                if dept.keywords:
                    for kw in dept.keywords:
                        if kw.lower() in cleaned:
                            score += 2
                if score > highest_score:
                    highest_score = score
                    best_dept = dept

            if best_dept:
                team_id = RoutingService._find_team_id(db, best_dept.id, team_name, text_content)
                return best_dept.id, team_id, best_dept.name

        # 3. Fallback to Customer Support or first configured department
        best_dept = next((d for d in active_depts if "Support" in d.name), active_depts[0])
        team_id = RoutingService._find_team_id(db, best_dept.id, team_name, text_content)
        return best_dept.id, team_id, best_dept.name

    @staticmethod
    def _find_team_id(
        db: Session,
        dept_id: int,
        team_name: Optional[str] = None,
        text_content: Optional[str] = None
    ) -> Optional[int]:
        teams = db.query(Team).filter(Team.department_id == dept_id, Team.is_active == True).all()
        if not teams:
            return None

        # Direct name match
        if team_name:
            t_lower = team_name.lower()
            for t in teams:
                if t.name.lower() in t_lower or t_lower in t.name.lower():
                    return t.id

        # Match team keywords against complaint text
        if text_content:
            cleaned = text_content.lower()
            best_team = None
            highest_score = 0
            for t in teams:
                score = 0
                if t.name.lower() in cleaned:
                    score += 5
                if t.keywords:
                    for kw in t.keywords:
                        if kw.lower() in cleaned:
                            score += 2
                if score > highest_score:
                    highest_score = score
                    best_team = t
            if best_team:
                return best_team.id

        # Fallback to first configured team in department
        return teams[0].id

routing_service = RoutingService()
