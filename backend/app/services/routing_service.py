from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from app.models.organization import Department, Team

class RoutingService:
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
        """Dynamically matches complaint text or category against departments and their specialized teams stored in PostgreSQL."""
        active_depts = db.query(Department).filter(Department.is_active == True).all()
        if not active_depts:
            return None, None, None

        # 1. Match by department name if provided
        if department_name:
            dept_lower = department_name.lower()
            for dept in active_depts:
                if dept.name.lower() in dept_lower or dept_lower in dept.name.lower():
                    team_id = RoutingService._find_team_id(db, dept.id, team_name, text_content)
                    return dept.id, team_id, dept.name

        # 2. Dynamic database keywords matching from PostgreSQL
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
