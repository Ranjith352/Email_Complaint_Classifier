from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.complaint import Complaint
from app.models.organization import Department

class AnalyticsRepository:
    @staticmethod
    def get_all_complaints(db: Session) -> List[Complaint]:
        return db.query(Complaint).all()

    @staticmethod
    def get_all_departments(db: Session) -> List[Department]:
        return db.query(Department).all()

analytics_repository = AnalyticsRepository()
