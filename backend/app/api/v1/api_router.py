from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, complaints, departments, teams, agents,
    analytics, ai, knowledge, emails, notifications, audit,
    routing_rules
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(complaints.router, prefix="/complaints", tags=["Complaints"])
api_router.include_router(departments.router, prefix="/departments", tags=["Departments"])
api_router.include_router(teams.router, prefix="/teams", tags=["Teams"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI & RAG"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["Knowledge Base"])
api_router.include_router(emails.router, prefix="/emails", tags=["Email Sync"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit Logs"])
api_router.include_router(routing_rules.router, prefix="/routing-rules", tags=["Routing Rules"])
