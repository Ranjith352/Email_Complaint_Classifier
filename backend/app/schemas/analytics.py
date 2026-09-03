from typing import List, Dict, Any
from pydantic import BaseModel

class DashboardKPIs(BaseModel):
    total_complaints: int
    open_cases: int
    in_progress: int
    resolved_cases: int
    critical_cases: int
    resolution_rate: float
    sla_compliance_rate: float
    avg_resolution_hours: float

class DepartmentVolume(BaseModel):
    department: str
    count: int
    open: int
    resolved: int

class UrgencyDistribution(BaseModel):
    urgency: str
    count: int
    percentage: float

class TrendPoint(BaseModel):
    date: str
    created: int
    resolved: int

class AnalyticsResponse(BaseModel):
    kpis: DashboardKPIs
    department_volumes: List[DepartmentVolume]
    urgency_distributions: List[UrgencyDistribution]
    trends: List[TrendPoint]
    category_counts: Dict[str, int]
    sentiment_breakdown: Dict[str, int]
