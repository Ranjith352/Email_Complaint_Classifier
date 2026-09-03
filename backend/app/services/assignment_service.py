import logging
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.organization import Agent, Department, Team
from app.models.complaint import Complaint

logger = logging.getLogger(__name__)

class AssignmentService:
    """Agent Assignment Engine.

    When assigning:
    1. Verify department.
    2. Verify team.
    3. Verify skills.
    4. Check availability.
    5. Check current workload.
    6. Check maximum workload.
    7. Prefer suitable lower-workload agents.

    Fallback:
    If no suitable agent exists:
    Route to the team queue.
    Do not lose the complaint.
    """

    @staticmethod
    def select_best_agent(
        db: Session,
        department_id: Optional[int] = None,
        team_id: Optional[int] = None,
        required_skills: Optional[List[str]] = None,
        strict_skills: bool = False
    ) -> Optional[Agent]:
        """Evaluates candidates against the 7 verified assignment criteria:
        1. Verify department (must match department_id)
        2. Verify team (must match team_id if provided)
        3. Verify skills (must match required skills)
        4. Check availability (availability == True and is_active == True)
        5. Check current workload (tracked in real-time)
        6. Check maximum workload (current_workload < max_workload)
        7. Prefer suitable lower-workload agents (lower workload / higher remaining capacity prioritized)
        """
        # Step 1: Verify department
        if not department_id:
            logger.info("Assignment skipped: No department specified. Route to triage queue.")
            return None

        req_skills_clean = [str(s).lower().strip() for s in (required_skills or []) if s]
        req_skills_set = set(req_skills_clean)

        # Step 1, 4, 5, 6: Department match, Available & Active, Under Max Capacity
        candidates = db.query(Agent).filter(
            Agent.department_id == department_id,
            Agent.availability == True,
            Agent.is_active == True,
            Agent.current_workload < Agent.max_workload
        ).all()

        # Step 2: Verify team
        # If team_id is provided, look for team candidates first
        if team_id is not None:
            team_candidates = [a for a in candidates if a.team_id == team_id]
            if team_candidates:
                candidates = team_candidates

        if not candidates:
            logger.info(f"No available agents in department {department_id} (team {team_id}). Route to team queue.")
            return None

        # Step 3: Verify skills
        def get_matching_skills(agent: Agent) -> int:
            if not req_skills_set or not agent.skills:
                return 0
            agent_skills = {str(s).lower().strip() for s in agent.skills}
            return len(req_skills_set.intersection(agent_skills))

        if strict_skills and req_skills_set:
            skilled_candidates = [a for a in candidates if get_matching_skills(a) > 0]
            if not skilled_candidates:
                logger.info(f"No agents with required skills {req_skills_clean}. Route to team queue.")
                return None
            candidates = skilled_candidates

        # Step 7: Prefer suitable lower-workload agents
        def candidate_priority_key(agent: Agent) -> Tuple[int, int, float, float]:
            # Priority tuple (all elements sorted descending):
            # 1. Exact team match (1 if matched, 0 otherwise)
            team_match = 1 if (team_id is not None and agent.team_id == team_id) else 0

            # 2. Number of matching required skills
            skill_score = get_matching_skills(agent)

            # 3. Prefer lower-workload: remaining capacity (max_workload - current_workload)
            # More capacity remaining = lower current workload = higher priority
            remaining_capacity = float(agent.max_workload - agent.current_workload)

            # 4. Historical performance tie-breaker
            perf = agent.performance_score if agent.performance_score is not None else 80.0

            return (team_match, skill_score, remaining_capacity, perf)

        # Select the best agent
        best_agent = max(candidates, key=candidate_priority_key)

        # Increment assigned workload
        best_agent.current_workload += 1
        db.flush()

        logger.info(
            f"Assigned to Agent {best_agent.name} (ID: {best_agent.id}, "
            f"Team: {best_agent.team_id}, Workload: {best_agent.current_workload}/{best_agent.max_workload})"
        )
        return best_agent

    @staticmethod
    def assign_to_agent_or_queue(
        db: Session,
        complaint: Complaint,
        department_id: Optional[int] = None,
        team_id: Optional[int] = None,
        required_skills: Optional[List[str]] = None,
        strict_skills: bool = False
    ) -> Dict[str, Any]:
        """Executes the full assignment workflow.
        If no suitable agent exists, routes the ticket safely to the team queue without losing it.
        """
        # Ensure complaint is anchored to department and team
        if department_id is not None:
            complaint.department_id = department_id
        if team_id is not None:
            complaint.team_id = team_id

        agent = AssignmentService.select_best_agent(
            db=db,
            department_id=complaint.department_id,
            team_id=complaint.team_id,
            required_skills=required_skills,
            strict_skills=strict_skills
        )

        if agent:
            complaint.assigned_agent_id = agent.id
            complaint.status = "ASSIGNED"
            db.flush()
            return {
                "assigned": True,
                "agent_id": agent.id,
                "agent_name": agent.name,
                "agent_email": agent.email,
                "current_workload": agent.current_workload,
                "max_workload": agent.max_workload,
                "team_queue": False,
                "status": "ASSIGNED"
            }
        else:
            # If no suitable agent exists: Route to the team queue. Do not lose the complaint.
            complaint.assigned_agent_id = None
            if complaint.status in ("NEW", "AI_ANALYZED"):
                complaint.status = "ROUTED"
            db.flush()

            team_obj = db.query(Team).filter(Team.id == complaint.team_id).first() if complaint.team_id else None
            team_title = team_obj.name if team_obj else "Department"

            logger.info(f"Complaint {complaint.id} safely routed to {team_title} queue. Complaint preserved.")
            return {
                "assigned": False,
                "agent_id": None,
                "team_queue": True,
                "queue_name": f"{team_title} Queue",
                "department_id": complaint.department_id,
                "team_id": complaint.team_id,
                "status": complaint.status,
                "message": f"No suitable agent available matching criteria. Routed to {team_title} queue. Complaint preserved."
            }

assignment_service = AssignmentService()
