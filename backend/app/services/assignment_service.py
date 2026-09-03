from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.organization import Agent

class AssignmentService:
    @staticmethod
    def select_best_agent(
        db: Session,
        department_id: Optional[int] = None,
        team_id: Optional[int] = None,
        required_skills: Optional[List[str]] = None
    ) -> Optional[Agent]:
        """Intelligently assigns the optimal human agent using 7 business criteria:
        1. Correct department
        2. Correct team
        3. Required skill match
        4. Availability (must be available / online)
        5. Current workload (lower workload prioritized)
        6. Maximum workload (must not exceed max capacity)
        7. Historical performance & average resolution time
        """
        if not department_id:
            return None

        # Base query: 1. Correct department, 4. Availability & Active, 6. Under Max Workload
        candidates = db.query(Agent).filter(
            Agent.department_id == department_id,
            Agent.availability == True,
            Agent.is_active == True,
            Agent.current_workload < Agent.max_workload
        ).all()

        # Fallback: if no available agents in department, look across all available agents
        if not candidates:
            candidates = db.query(Agent).filter(
                Agent.availability == True,
                Agent.is_active == True,
                Agent.current_workload < Agent.max_workload
            ).all()

        if not candidates:
            return None

        req_skills_set = {s.lower().strip() for s in (required_skills or [])}

        def score_candidate(agent: Agent) -> float:
            score = 0.0

            # 2. Correct Team (+50 points)
            if team_id is not None and agent.team_id == team_id:
                score += 50.0

            # 3. Required Skills (+25 points per matching skill)
            if req_skills_set and agent.skills:
                agent_skills = {str(s).lower().strip() for s in agent.skills}
                matches = len(req_skills_set.intersection(agent_skills))
                score += matches * 25.0

            # 5 & 6. Current Workload vs Maximum Capacity (+40 points for completely free, 0 at capacity)
            if agent.max_workload > 0:
                capacity_ratio = 1.0 - (agent.current_workload / agent.max_workload)
                score += max(0.0, capacity_ratio * 40.0)

            # 7. Historical Performance (+0 to +25 points based on 0-100 performance score)
            perf = agent.performance_score if agent.performance_score is not None else 80.0
            score += (perf / 100.0) * 25.0

            # 7. Average Resolution Time Bonus (faster resolution = up to +15 points)
            avg_time = agent.average_resolution_time if agent.average_resolution_time is not None else 4.0
            time_bonus = max(0.0, 15.0 - (avg_time * 1.5))
            score += time_bonus

            return score

        # Rank candidates by composite score descending
        best_agent = max(candidates, key=score_candidate)

        # Increment assigned workload
        best_agent.current_workload += 1
        db.flush()

        return best_agent

assignment_service = AssignmentService()
