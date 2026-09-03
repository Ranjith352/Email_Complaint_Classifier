import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Guarantee that 'app' can be imported whether run from root or from backend/
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.organization import Department, Team, Agent, RoutingRule
from app.models.complaint import Complaint
from app.models.knowledge import KnowledgeDocument
from app.models.intelligence import ModelVersion
from app.models.operations import SLARule
from app.ai.embeddings import embeddings_engine
from app.api.v1.api_router import api_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("autotriage_ai")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise AI Complaint Management, Department Routing, and Policy RAG Assistant",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def seed_enterprise_data():
    """Initializes tables and seeds default organization hierarchy, policies, and fictional demonstration records."""
    db = SessionLocal()
    try:
        # Create all 17 tables in database
        Base.metadata.create_all(bind=engine)

        # 1. Seed Admin User
        admin = db.query(User).filter(User.email == "admin@complaints.io").first()
        if not admin:
            admin = User(
                name="Lead Operations Admin",
                email="admin@complaints.io",
                password_hash=get_password_hash("admin123"),
                role="ADMIN",
                is_active=True
            )
            db.add(admin)
            db.commit()
            logger.info("Seeded default admin (admin@complaints.io / admin123) with ADMIN role.")

        # 2. Seed Departments & Teams
        if db.query(Department).count() == 0:
            dept_specs = [
                {
                    "name": "Finance",
                    "code": "FIN",
                    "description": "Billing discrepancies, refunds, payment processing, fraud chargebacks",
                    "email": "finance@company.com",
                    "lead_name": "Eleanor Vance",
                    "keywords": ["refund", "billing", "charge", "invoice", "payment", "bank", "overcharge"],
                    "sla_hours": 8,
                    "teams": [
                        {"name": "Billing Team", "code": "FIN-BILL", "keywords": ["invoice", "statement", "receipt", "billing discrepancy"]},
                        {"name": "Payments Team", "code": "FIN-PAY", "keywords": ["payment", "processing", "gateway", "charge", "card"]},
                        {"name": "Refund Team", "code": "FIN-REF", "keywords": ["refund", "reimbursement", "chargeback", "reversed"]}
                    ]
                },
                {
                    "name": "IT",
                    "code": "IT",
                    "description": "Server outages, application bugs, account access, login timeouts",
                    "email": "it-ops@company.com",
                    "lead_name": "Marcus Brody",
                    "keywords": ["crash", "server", "outage", "bug", "login", "error", "portal", "software"],
                    "sla_hours": 4,
                    "teams": [
                        {"name": "Technical Support", "code": "IT-TECH", "keywords": ["hardware", "desktop", "crash", "frozen", "screen"]},
                        {"name": "Network Team", "code": "IT-NET", "keywords": ["network", "wifi", "vpn", "connectivity", "latency"]},
                        {"name": "Application Support", "code": "IT-APP", "keywords": ["software", "portal", "app bug", "glitch", "database"]},
                        {"name": "Cybersecurity Team", "code": "IT-SEC", "keywords": ["phishing", "compromise", "unauthorized", "suspicious"]}
                    ]
                },
                {
                    "name": "HR",
                    "code": "HR",
                    "description": "Employee relations, workplace conduct, payroll inquiries, recruitment",
                    "email": "hr@company.com",
                    "lead_name": "Sarah Connor",
                    "keywords": ["employee", "recruitment", "interview", "payroll", "workplace", "harassment", "staff"],
                    "sla_hours": 24,
                    "teams": [
                        {"name": "Payroll", "code": "HR-PAY", "keywords": ["salary", "payslip", "payroll", "tax deduction", "bonus"]},
                        {"name": "Recruitment", "code": "HR-REC", "keywords": ["interview", "candidate", "hiring", "job offer"]},
                        {"name": "Employee Relations", "code": "HR-REL", "keywords": ["conduct", "harassment", "dispute", "workplace"]}
                    ]
                },
                {
                    "name": "Sales",
                    "code": "SALES",
                    "description": "Enterprise sales contracts, pricing negotiations, product demos, licensing",
                    "email": "sales@company.com",
                    "lead_name": "Jordan Belfort",
                    "keywords": ["pricing", "quotation", "discount", "demo", "subscription", "contract", "purchase"],
                    "sla_hours": 12,
                    "teams": ["Inbound Sales", "Enterprise Accounts", "Contract Negotiations"]
                },
                {
                    "name": "Customer Support",
                    "code": "CS",
                    "description": "General user inquiries, tier-1 technical triage, product assistance",
                    "email": "support@company.com",
                    "lead_name": "David Sterling",
                    "keywords": ["help", "assistance", "agent", "inquiry", "representative", "service", "complaint"],
                    "sla_hours": 4,
                    "teams": ["Frontline Support", "VIP Escalations", "Self-Service Support"]
                },
                {
                    "name": "Operations",
                    "code": "OPS",
                    "description": "Service continuity, facility operations, process workflow optimizations",
                    "email": "operations@company.com",
                    "lead_name": "Regina Phalange",
                    "keywords": ["process", "workflow", "facility", "operational", "maintenance", "service delay"],
                    "sla_hours": 12,
                    "teams": ["Process Optimization", "Facilities & Workflow", "Service Delivery"]
                },
                {
                    "name": "Logistics",
                    "code": "LOG",
                    "description": "Package shipment tracking, courier disputes, customs, lost transit items",
                    "email": "logistics@company.com",
                    "lead_name": "James Holden",
                    "keywords": ["delivery", "shipping", "tracking", "courier", "package", "transit", "lost parcel"],
                    "sla_hours": 8,
                    "teams": ["Delivery & Tracking", "Courier Management", "Returns & Warehousing"]
                },
                {
                    "name": "Legal",
                    "code": "LEGAL",
                    "description": "Regulatory compliance, contractual disputes, privacy & GDPR requests",
                    "email": "legal@company.com",
                    "lead_name": "Harvey Specter",
                    "keywords": ["compliance", "lawsuit", "terms", "gdpr", "privacy", "dispute", "contract violation"],
                    "sla_hours": 48,
                    "teams": ["Regulatory Compliance", "Privacy & GDPR", "Contract Disputes"]
                },
                {
                    "name": "Security",
                    "code": "SEC",
                    "description": "Vulnerability triage, account compromise, suspicious logins, phishing",
                    "email": "security@company.com",
                    "lead_name": "Talia Al Ghul",
                    "keywords": ["data breach", "hack", "phishing", "unauthorized", "vulnerability", "password reset"],
                    "sla_hours": 2,
                    "teams": ["Incident Response", "Identity Protection", "Threat Detection"]
                },
                {
                    "name": "Procurement",
                    "code": "PROC",
                    "description": "Supplier management, purchase order validations, vendor contracts",
                    "email": "procurement@company.com",
                    "lead_name": "Claire Underwood",
                    "keywords": ["vendor", "supplier", "purchase order", "sourcing", "rfp", "materials"],
                    "sla_hours": 24,
                    "teams": ["Vendor Relations", "Purchase Orders", "Strategic Sourcing"]
                },
                {
                    "name": "Administration",
                    "code": "ADMIN",
                    "description": "Office facilities, visitor access, corporate management, resources",
                    "email": "admin@company.com",
                    "lead_name": "Arthur Dent",
                    "keywords": ["office", "badge", "reception", "supplies", "access card", "visitor"],
                    "sla_hours": 24,
                    "teams": ["Office Management", "Access & Badging", "Corporate Services"]
                }
            ]

            for d_spec in dept_specs:
                dept = Department(
                    name=d_spec["name"],
                    code=d_spec["code"],
                    description=d_spec["description"],
                    email=d_spec["email"],
                    lead_name=d_spec["lead_name"],
                    keywords=d_spec["keywords"],
                    sla_hours=d_spec["sla_hours"],
                    is_active=True
                )
                db.add(dept)
                db.flush()

                for t_item in d_spec["teams"]:
                    if isinstance(t_item, dict):
                        t_name = t_item["name"]
                        t_code = t_item.get("code")
                        t_keywords = t_item.get("keywords", [])
                    else:
                        t_name = t_item
                        t_code = f"{dept.code}-{t_name[:4].upper()}"
                        t_keywords = []

                    team = Team(
                        department_id=dept.id,
                        name=t_name,
                        code=t_code,
                        keywords=t_keywords,
                        description=f"{t_name} team handling specialized tier tickets.",
                        is_active=True
                    )
                    db.add(team)
                    db.flush()

                    # Seed an agent for the team
                    agent = Agent(
                        department_id=dept.id,
                        team_id=team.id,
                        employee_id=f"EMP-{dept.code}-{team.id}",
                        full_name=f"{d_spec['code']} Specialist {team.id}",
                        email=f"agent.{team.id}@{dept.code.lower()}.company.com",
                        skills=[dept.code.lower(), "triage"],
                        max_active_tickets=10,
                        current_workload=0
                    )
                    db.add(agent)

            db.commit()
            logger.info("Seeded 5 enterprise departments, 17 functional teams, and agents.")

        # 3. Seed Company Policies & SOPs in Knowledge Documents for RAG
        if db.query(KnowledgeDocument).count() == 0:
            policies = [
                {
                    "title": "Corporate Refund & Double-Billing Policy (REF-2026)",
                    "category": "Billing / Payment",
                    "document_type": "REFUND_GUIDELINE",
                    "content": "All duplicate credit card charges or unauthorized debits must be verified against transaction logs within 4 hours. If verified duplicate, an automated Stripe/payment gateway reversal is initiated immediately. Customers receive full credit plus an official credit memorandum within 24 hours."
                },
                {
                    "title": "Critical Production Outage & Service Incident SOP (SOP-IT-01)",
                    "category": "Technical Problem",
                    "document_type": "SOP",
                    "content": "When HTTP 500 or gateway timeout errors affect more than 5% of users, incident priority is automatically set to P1 (Critical, 4h SLA). Engineers must inspect connection pool health, restart degraded pod clusters, and update the status dashboard within 30 minutes of notification."
                },
                {
                    "title": "Account Security Compromise & Takeover Response (SEC-POL-04)",
                    "category": "Security Issue",
                    "document_type": "POLICY",
                    "content": "Upon report of suspicious unrecognized login or unauthorized credential alteration: 1. Immediately invalidate all active JWT tokens and sessions. 2. Lock outbound transactions. 3. Dispatch out-of-band verification challenge to customer's verified mobile number. 4. Enforce mandatory 2FA setup upon restoration."
                },
                {
                    "title": "Damaged Package & Missing Goods Courier Guideline (CS-SOP-09)",
                    "category": "Customer Support",
                    "document_type": "SOP",
                    "content": "Customers reporting damaged shipments or missing items (#ORD-*) do not need to return the broken parcel if photographic evidence is submitted. Immediate priority courier replacement is dispatched, accompanied by a 15% promotional store credit code."
                }
            ]

            for p in policies:
                emb = embeddings_engine.get_embedding(f"{p['title']} {p['category']} {p['content']}")
                doc = KnowledgeDocument(
                    title=p["title"],
                    category=p["category"],
                    document_type=p["document_type"],
                    content_text=p["content"],
                    chunk_text=p["content"],
                    embedding=emb
                )
                db.add(doc)

            db.commit()
            logger.info("Seeded official company policies & SOPs for RAG semantic retrieval.")

        # 4. Seed Fictional Demonstration Complaints
        if db.query(Complaint).count() == 0:
            demo_tickets = [
                {
                    "subject": "Unauthorized charge and double billing deduction on credit card",
                    "body": "I noticed an unauthorized deduction of $149.00 on my bank statement on March 2nd (TXN-948210). My subscription was charged twice! Please reverse this duplicate transaction immediately.",
                    "customer_name": "Sarah Connor",
                    "customer_email": "sarah.connor@example.com",
                    "category": "Billing / Payment",
                    "urgency": "High",
                    "priority_level": "P2",
                    "status": "In Investigation"
                },
                {
                    "subject": "500 Internal server error and connection timeouts on checkout",
                    "body": "Our engineering checkout integration is completely down with 500 internal server error. All customers are blocked from finalizing transactions. This is an urgent production emergency!",
                    "customer_name": "DevOps Lead",
                    "customer_email": "devops@clientcorp.com",
                    "category": "Technical Problem",
                    "urgency": "Critical",
                    "priority_level": "P1",
                    "status": "New"
                },
                {
                    "subject": "Suspicious login attempt and password reset notification",
                    "body": "I received an alert that someone accessed my account from an unknown IP in Europe. I did not authorize this and cannot log in now. Freeze my account immediately!",
                    "customer_name": "Alex Mercer",
                    "customer_email": "alex.m@securemail.com",
                    "category": "Security Issue",
                    "urgency": "Critical",
                    "priority_level": "P1",
                    "status": "Assigned"
                }
            ]

            for idx, t in enumerate(demo_tickets, start=1):
                emb = embeddings_engine.get_embedding(f"{t['subject']} {t['body']}")
                sla_hours = 4 if t["urgency"] == "Critical" else 8
                comp = Complaint(
                    complaint_number=f"CMP-{10000 + idx}",
                    customer_name=t["customer_name"],
                    customer_email=t["customer_email"],
                    subject=t["subject"],
                    description=t["body"],
                    cleaned_text=t["body"].lower(),
                    category=t["category"],
                    urgency=t["urgency"],
                    priority=t["priority_level"],
                    priority_score=90.0 if t["urgency"] == "Critical" else 70.0,
                    ai_confidence=0.95,
                    review_required=False,
                    ai_status="COMPLETED",
                    status="IN_INVESTIGATION" if t["status"] == "In Investigation" else ("ASSIGNED" if t["status"] == "Assigned" else "NEW"),
                    source="WEB",
                    summary=t["subject"],
                    sla_deadline=datetime.utcnow() + timedelta(hours=sla_hours),
                    embedding=emb
                )
                db.add(comp)

            db.commit()
            logger.info("Seeded fictional demonstration complaints.")

        # 5. Seed Configurable Routing Rules
        if db.query(RoutingRule).count() == 0:
            rules_to_seed = [
                {"trigger_keyword": "Billing", "department_name": "Finance", "team_name": None, "description": "Billing queries -> Finance"},
                {"trigger_keyword": "Payment", "department_name": "Finance", "team_name": "Payments", "description": "Payment queries -> Finance / Payments"},
                {"trigger_keyword": "Refund", "department_name": "Finance", "team_name": "Refunds", "description": "Refund requests -> Finance / Refunds"},
                {"trigger_keyword": "Login", "department_name": "IT", "team_name": "Application Support", "description": "Login queries -> IT / Application Support"},
                {"trigger_keyword": "Network", "department_name": "IT", "team_name": "Network Team", "description": "Network connectivity -> IT / Network"},
                {"trigger_keyword": "Security Breach", "department_name": "Security", "team_name": "Incident Response", "priority_override": "CRITICAL", "sla_hours": 2, "description": "Security breaches -> Security"},
                {"trigger_keyword": "Payroll", "department_name": "HR", "team_name": "Payroll", "description": "Payroll inquiries -> HR / Payroll"},
                {"trigger_keyword": "Leave", "department_name": "HR", "team_name": "Employee Relations", "description": "Leave requests -> HR / Employee Relations"},
                {"trigger_keyword": "Delivery", "department_name": "Logistics", "team_name": "Delivery & Tracking", "description": "Delivery issues -> Logistics"}
            ]
            for r in rules_to_seed:
                db.add(RoutingRule(**r))
            db.commit()
            logger.info("Seeded enterprise configurable routing rules.")
    except Exception as e:
        logger.error(f"Error during enterprise database seeding: {e}")
    finally:
        db.close()

@app.on_event("startup")
def on_startup():
    seed_enterprise_data()

# Mount API v1 router at /api
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "active",
        "docs": "/docs",
        "api": settings.API_V1_STR
    }
