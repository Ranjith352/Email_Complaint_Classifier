import os
import sys
import random
from datetime import datetime, timedelta
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) in sys.path:
    sys.path.remove(str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR))

# Remove root dir from sys.path[1] if present so app.py doesn't shadow app package
for p in list(sys.path):
    if str(Path(p).resolve()) == str(ROOT_DIR.resolve()) and p != "":
        sys.path.remove(p)

from app.db.database import SessionLocal, Base, engine

from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.team import Team
from app.models.agent import Agent
from app.models.complaint import Complaint, ComplaintStatus, ComplaintSource
from app.models.prediction import ComplaintPrediction, AIResponse
from app.models.sla import SLARule
from app.models.organization import RoutingRule
from app.models.event import ComplaintEvent, AuditLog
from app.ai.embeddings import embeddings_engine

def run_seed():
    """Seeds the database with 8 departments, fictional teams, agents, routing rules,

    SLA rules, and at least 35 realistic fictional customer complaints.
    """
    db = SessionLocal()
    try:
        # Create all tables if not already present
        Base.metadata.create_all(bind=engine)
        print("Ensuring database tables exist...")

        # 1. Seed Default Admin & Agent Users
        admin_user = db.query(User).filter(User.email == "admin@complaints.io").first()
        if not admin_user:
            admin_user = User(
                name="Executive Admin",
                email="admin@complaints.io",
                password_hash=get_password_hash("admin123"),
                role="ADMIN",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            print("Seeded default admin (admin@complaints.io / admin123)")

        # 2. Seed 8 Required Departments
        dept_configs = [
            {
                "name": "Finance",
                "code": "FIN",
                "description": "Billing discrepancies, refunds, payment processing, fraud chargebacks",
                "email": "finance@fictionalcorp.io",
                "lead_name": "Eleanor Vance",
                "sla_hours": 8,
                "keywords": ["refund", "billing", "charge", "invoice", "payment", "bank", "overcharge", "stripe"],
                "teams": [
                    {"name": "Billing & Invoicing", "code": "FIN-BILL", "keywords": ["invoice", "statement", "receipt", "billing discrepancy"]},
                    {"name": "Payments & Gateways", "code": "FIN-PAY", "keywords": ["payment", "processing", "gateway", "charge", "card"]},
                    {"name": "Refunds & Adjustments", "code": "FIN-REF", "keywords": ["refund", "reimbursement", "chargeback", "reversed"]}
                ]
            },
            {
                "name": "IT",
                "code": "IT",
                "description": "Server outages, application bugs, account access, login timeouts, VPN",
                "email": "it-ops@fictionalcorp.io",
                "lead_name": "Marcus Brody",
                "sla_hours": 4,
                "keywords": ["crash", "server", "outage", "bug", "login", "error", "portal", "software", "vpn", "network"],
                "teams": [
                    {"name": "Application Support", "code": "IT-APP", "keywords": ["software", "portal", "app bug", "glitch", "database"]},
                    {"name": "Infrastructure & Network", "code": "IT-NET", "keywords": ["network", "wifi", "vpn", "connectivity", "latency", "dns"]},
                    {"name": "Access & Identity", "code": "IT-IAM", "keywords": ["login", "sso", "password", "mfa", "permission", "locked"]}
                ]
            },
            {
                "name": "HR",
                "code": "HR",
                "description": "Employee benefits, payroll queries, leave requests, workplace policies",
                "email": "hr@fictionalcorp.io",
                "lead_name": "Sophia Bennett",
                "sla_hours": 24,
                "keywords": ["payroll", "salary", "leave", "vacation", "benefits", "bonus", "timesheet"],
                "teams": [
                    {"name": "Payroll Operations", "code": "HR-PAY", "keywords": ["payroll", "salary", "direct deposit", "w2", "tax"]},
                    {"name": "Employee Relations & Leave", "code": "HR-REL", "keywords": ["leave", "pto", "bereavement", "maternity", "vacation"]}
                ]
            },
            {
                "name": "Sales",
                "code": "SALES",
                "description": "Contract terms, renewal pricing, quote disputes, enterprise agreements",
                "email": "sales-support@fictionalcorp.io",
                "lead_name": "Julian Hayes",
                "sla_hours": 12,
                "keywords": ["contract", "quote", "discount", "renewal", "sales", "upgrade", "pricing"],
                "teams": [
                    {"name": "Enterprise Accounts", "code": "SALES-ENT", "keywords": ["enterprise", "custom agreement", "msa", "sla terms"]},
                    {"name": "Commercial Renewals", "code": "SALES-REN", "keywords": ["renewal", "tier upgrade", "billing cycle"]}
                ]
            },
            {
                "name": "Customer Support",
                "code": "Customer Support",
                "description": "General customer inquiries, onboarding help, account support, feedback",
                "email": "support@fictionalcorp.io",
                "lead_name": "Clara Oswald",
                "sla_hours": 6,
                "keywords": ["help", "service", "representative", "delay", "rude", "satisfaction", "agent"],
                "teams": [
                    {"name": "Tier 1 Customer Helpdesk", "code": "CS-T1", "keywords": ["general", "how to", "getting started"]},
                    {"name": "VIP & Priority Support", "code": "CS-VIP", "keywords": ["executive", "vip", "urgent escalation", "unresolved"]}
                ]
            },
            {
                "name": "Operations",
                "code": "OPS",
                "description": "Facilities, vendor agreements, compliance adherence, inventory coordination",
                "email": "ops@fictionalcorp.io",
                "lead_name": "David Sterling",
                "sla_hours": 16,
                "keywords": ["facility", "vendor", "service level", "workflow", "process", "audit"],
                "teams": [
                    {"name": "Process & Vendor Management", "code": "OPS-VEND", "keywords": ["vendor", "contractor", "procurement"]},
                    {"name": "Facilities & Workplace", "code": "OPS-FAC", "keywords": ["office", "building", "access badge", "equipment"]}
                ]
            },
            {
                "name": "Logistics",
                "code": "Logistics",
                "description": "Shipment tracking, courier delays, damaged goods, returns, customs",
                "email": "logistics@fictionalcorp.io",
                "lead_name": "Liam Gallagher",
                "sla_hours": 12,
                "keywords": ["delivery", "shipment", "courier", "tracking", "damaged", "package", "transit", "rma"],
                "teams": [
                    {"name": "Freight & Dispatch", "code": "LOG-DISP", "keywords": ["freight", "customs", "export", "warehouse"]},
                    {"name": "Last-Mile Delivery & RMA", "code": "LOG-LAST", "keywords": ["delivery", "courier", "missing package", "return", "rma"]}
                ]
            },
            {
                "name": "Security",
                "code": "Security",
                "description": "Phishing threats, unauthorized access, data leaks, credential stuffing",
                "email": "security-response@fictionalcorp.io",
                "lead_name": "Rachel Zane",
                "sla_hours": 2,
                "keywords": ["security", "breach", "phishing", "compromised", "unauthorized", "leak", "hacked", "malware"],
                "teams": [
                    {"name": "Incident Response", "code": "SEC-IR", "keywords": ["incident", "breach", "emergency", "containment"]},
                    {"name": "Threat Intelligence & Compliance", "code": "SEC-THREAT", "keywords": ["phishing", "audit", "cve", "vulnerability"]}
                ]
            }
        ]

        created_departments = {}
        created_teams = {}

        for d_info in dept_configs:
            dept = db.query(Department).filter(Department.name == d_info["name"]).first()
            if not dept:
                dept = Department(
                    name=d_info["name"],
                    code=d_info["code"],
                    description=d_info["description"],
                    email=d_info["email"],
                    lead_name=d_info["lead_name"],
                    sla_hours=d_info["sla_hours"],
                    keywords=d_info["keywords"],
                    is_active=True
                )
                db.add(dept)
                db.commit()
                db.refresh(dept)
            created_departments[dept.name] = dept

            for t_info in d_info["teams"]:
                team = db.query(Team).filter(Team.department_id == dept.id, Team.name == t_info["name"]).first()
                if not team:
                    team = Team(
                        department_id=dept.id,
                        name=t_info["name"],
                        code=t_info["code"],
                        keywords=t_info["keywords"],
                        is_active=True
                    )
                    db.add(team)
                    db.commit()
                    db.refresh(team)
                created_teams[f"{dept.name}::{team.name}"] = team

        print(f"Verified/Seeded 8 Departments and {len(created_teams)} Teams.")

        # 3. Seed Fictional Agents
        agent_roster = [
            ("Sarah Chen", "sarah.chen@fictionalcorp.io", "Finance", "Billing & Invoicing", ["billing", "invoicing", "vat"]),
            ("Michael Ross", "michael.ross@fictionalcorp.io", "Finance", "Refunds & Adjustments", ["refunds", "disputes", "chargebacks"]),
            ("Devon Harris", "devon.harris@fictionalcorp.io", "IT", "Infrastructure & Network", ["network", "vpn", "dns", "firewall"]),
            ("Priya Patel", "priya.patel@fictionalcorp.io", "IT", "Application Support", ["app bug", "crash", "sql", "api"]),
            ("Carlos Mendez", "carlos.mendez@fictionalcorp.io", "IT", "Access & Identity", ["login", "sso", "mfa", "accounts"]),
            ("Emma Watson", "emma.watson@fictionalcorp.io", "HR", "Payroll Operations", ["payroll", "salary", "compensation"]),
            ("Lucas Vance", "lucas.vance@fictionalcorp.io", "HR", "Employee Relations & Leave", ["leave", "pto", "benefits"]),
            ("Olivia Dunn", "olivia.dunn@fictionalcorp.io", "Sales", "Enterprise Accounts", ["contracts", "pricing", "enterprise"]),
            ("Noah Miller", "noah.miller@fictionalcorp.io", "Sales", "Commercial Renewals", ["renewals", "subscriptions"]),
            ("Aiden Brooks", "aiden.brooks@fictionalcorp.io", "Customer Support", "Tier 1 Customer Helpdesk", ["general", "helpdesk", "triage"]),
            ("Maya Lin", "maya.lin@fictionalcorp.io", "Customer Support", "VIP & Priority Support", ["vip", "escalations", "retention"]),
            ("Kenji Sato", "kenji.sato@fictionalcorp.io", "Operations", "Process & Vendor Management", ["procurement", "vendors"]),
            ("Chloe Taylor", "chloe.taylor@fictionalcorp.io", "Logistics", "Freight & Dispatch", ["freight", "customs", "export"]),
            ("Zack Ramirez", "zack.ramirez@fictionalcorp.io", "Logistics", "Last-Mile Delivery & RMA", ["delivery", "rma", "returns"]),
            ("Alexander Frost", "alexander.frost@fictionalcorp.io", "Security", "Incident Response", ["malware", "compromise", "incident"]),
            ("Nadia Al-Mansoor", "nadia.almansoor@fictionalcorp.io", "Security", "Threat Intelligence & Compliance", ["phishing", "audit"])
        ]

        created_agents = []
        for name, email, dept_name, team_name, skills in agent_roster:
            agent = db.query(Agent).filter(Agent.email == email).first()
            dept = created_departments.get(dept_name)
            team = created_teams.get(f"{dept_name}::{team_name}")
            if not agent:
                agent = Agent(
                    name=name,
                    email=email,
                    department_id=dept.id if dept else None,
                    team_id=team.id if team else None,
                    skills=skills,
                    availability=True,
                    current_workload=random.randint(1, 5),
                    max_workload=10,
                    performance_score=round(random.uniform(92.0, 98.5), 1),
                    average_resolution_time=round(random.uniform(1.8, 5.2), 1),
                    is_active=True
                )
                db.add(agent)
                db.commit()
                db.refresh(agent)
            created_agents.append(agent)

        print(f"Verified/Seeded {len(created_agents)} Fictional Agents.")

        # 4. Seed SLA Rules
        sla_matrix = [
            ("CRITICAL", "Critical", 1, 4),
            ("HIGH", "High", 2, 8),
            ("MEDIUM", "Medium", 4, 24),
            ("LOW", "Low", 8, 48)
        ]
        for p_code, urg_label, max_resp, max_resol in sla_matrix:
            rule = db.query(SLARule).filter(SLARule.priority_level == p_code).first()
            if not rule:
                rule = SLARule(
                    priority_level=p_code,
                    urgency_level=urg_label,
                    max_response_hours=max_resp,
                    max_resolution_hours=max_resol,
                    escalation_email="sla-alerts@fictionalcorp.io",
                    is_active=True
                )
                db.add(rule)
        db.commit()
        print("Verified/Seeded SLA rules matrix.")

        # 5. Seed Configurable Routing Rules
        routing_configs = [
            ("Billing", "Finance", "Billing & Invoicing", "HIGH", 8, "Invoice and billing discrepancy routing"),
            ("Payment", "Finance", "Payments & Gateways", "HIGH", 4, "Payment processing failure routing"),
            ("Refund", "Finance", "Refunds & Adjustments", "HIGH", 8, "Refund and chargeback routing"),
            ("Login", "IT", "Access & Identity", "HIGH", 4, "Authentication and SSO issues"),
            ("Network", "IT", "Infrastructure & Network", "HIGH", 4, "VPN, latency and infrastructure connectivity"),
            ("Software", "IT", "Application Support", "MEDIUM", 8, "Application crash and platform glitches"),
            ("Security", "Security", "Incident Response", "CRITICAL", 1, "Suspicious login or unauthorized access attempt"),
            ("Phishing", "Security", "Threat Intelligence & Compliance", "CRITICAL", 2, "Reported fraudulent emails and phishing lures"),
            ("Payroll", "HR", "Payroll Operations", "HIGH", 8, "Salary, bonus, and direct deposit issues"),
            ("Leave", "HR", "Employee Relations & Leave", "MEDIUM", 24, "PTO, bereavement, and parental leave inquiries"),
            ("Delivery", "Logistics", "Last-Mile Delivery & RMA", "HIGH", 8, "Damaged or delayed shipments"),
            ("Contract", "Sales", "Enterprise Accounts", "MEDIUM", 12, "Enterprise MSA and renewal agreements"),
            ("Customer Support", "Customer Support", "Tier 1 Customer Helpdesk", "MEDIUM", 6, "General support and guidance")
        ]
        for trig, d_name, t_name, prio, sla_h, desc in routing_configs:
            rule = db.query(RoutingRule).filter(RoutingRule.trigger_keyword == trig).first()
            if not rule:
                rule = RoutingRule(
                    trigger_keyword=trig,
                    department_name=d_name,
                    team_name=t_name,
                    priority_override=prio,
                    sla_hours=sla_h,
                    description=desc,
                    is_active=True
                )
                db.add(rule)
        db.commit()
        print("Verified/Seeded Routing Rules.")

        # 6. Seed at least 35 Realistic Fictional Complaints
        fictional_complaints_data = [
            # Payment
            ("CMP-2026-101", "Fictional Client Alpha", "alpha.billing@example.org", "Double charge on checkout for order #ORD-4491",
             "I attempted to complete payment for our SaaS license renewal and was charged twice ($450 each) on our corporate Visa. Please reverse the duplicate charge immediately.",
             "Payment", "Finance", "Payments & Gateways", "CRITICAL", "Critical", "Frustration", "Negative", ComplaintStatus.IN_PROGRESS),

            ("CMP-2026-102", "Globex Dynamics", "procure@globex-example.com", "Payment gateway 502 Bad Gateway during subscription payment",
             "During our monthly invoice settlement on the portal, the payment screen timed out with a 502 Bad Gateway error. Our credit card shows pending, but the invoice still appears unpaid.",
             "Payment", "Finance", "Payments & Gateways", "HIGH", "High", "Anxiety", "Negative", ComplaintStatus.NEW),

            ("CMP-2026-103", "Apex Logistics Ltd", "accounting@apex-example.net", "Wire transfer payment not reflected in account balance",
             "We submitted international wire transfer of $12,500 with reference #WIRE-8812 over five business days ago. The account is threatening suspension for non-payment.",
             "Payment", "Finance", "Payments & Gateways", "HIGH", "High", "Frustration", "Negative", ComplaintStatus.ASSIGNED),

            # Refund
            ("CMP-2026-104", "Initech Software", "peter.g@initech-example.com", "Refund requested for cancelled annual subscription #SUB-891",
             "We submitted an official cancellation request 3 weeks ago within our 30-day trial period. Our account manager confirmed a full refund of $3,200, but no credit has appeared.",
             "Refund", "Finance", "Refunds & Adjustments", "HIGH", "High", "Frustration", "Negative", ComplaintStatus.ASSIGNED),

            ("CMP-2026-105", "Acme Retailers", "orders@acme-retail-example.com", "Partial refund calculated incorrectly on bulk return",
             "We returned 15 units under RMA #RMA-9021. The credit memo received was for $1,200 instead of the invoice value of $1,800. Please reconcile the remaining $600 difference.",
             "Refund", "Finance", "Refunds & Adjustments", "MEDIUM", "Medium", "Neutral", "Neutral", ComplaintStatus.NEW),

            ("CMP-2026-106", "Starlight Media", "finance@starlight-example.org", "Missing tax refund following tax exemption certificate upload",
             "Our 501(c)(3) tax exemption was verified by your team in January, but February and March invoices still included state sales tax. Please issue a refund of $384.20.",
             "Refund", "Finance", "Refunds & Adjustments", "MEDIUM", "Medium", "Neutral", "Neutral", ComplaintStatus.RESOLVED),

            # Billing
            ("CMP-2026-107", "Cyberdyne Systems", "accounts@cyberdyne-example.com", "Unexpected overage charges on March invoice #INV-99214",
             "Our monthly billing statement jumped from $500 to $2,450. The line item claims 20,000 API calls overage, but our telemetry logs indicate only 4,500 calls were made.",
             "Billing", "Finance", "Billing & Invoicing", "HIGH", "High", "Anger", "Negative", ComplaintStatus.IN_PROGRESS),

            ("CMP-2026-108", "Wayne Enterprises", "it-pay@wayne-example.com", "Incorrect billing address causing corporate card declination",
             "Our corporate procurement department updated our billing address last month, but your recurring billing system still tries to charge the old address.",
             "Billing", "Finance", "Billing & Invoicing", "LOW", "Low", "Neutral", "Neutral", ComplaintStatus.RESOLVED),

            ("CMP-2026-109", "Pied Piper Cloud", "richard@piedpiper-example.io", "Duplicate line item for Premium SLA Support on invoice",
             "Invoice #INV-2026-03 contains two identical line items of $350 each for 'Enterprise Support SLA'. We only have one tenant instance.",
             "Billing", "Finance", "Billing & Invoicing", "MEDIUM", "Medium", "Frustration", "Negative", ComplaintStatus.NEW),

            # Login
            ("CMP-2026-110", "Dunder Mifflin", "jim.halpert@dunder-example.com", "SSO Okta SAML login loop failing for all regional employees",
             "All 45 team members at our branch are unable to access the portal. When clicking 'Log in with SAML', it loops back to the login screen with 'Invalid RelayState'.",
             "Login", "IT", "Access & Identity", "CRITICAL", "Critical", "Anger", "Negative", ComplaintStatus.ESCALATED),

            ("CMP-2026-111", "Vandelay Industries", "george@vandelay-example.com", "MFA verification SMS codes not arriving on mobile carrier",
             "I am completely locked out of my administrative dashboard. I click 'Resend SMS code' and receive nothing. Need urgent reset to authenticator app.",
             "Login", "IT", "Access & Identity", "HIGH", "High", "Anxiety", "Negative", ComplaintStatus.ASSIGNED),

            ("CMP-2026-112", "Hooli Tech", "gavin@hooli-example.com", "Account locked out after 3 failed password attempts by automated script",
             "Our CI/CD testing pipeline triggered account lockout on our service account `ci-deploy@hooli-example.com`. Please unlock this service account.",
             "Login", "IT", "Access & Identity", "HIGH", "High", "Urgent", "Neutral", ComplaintStatus.RESOLVED),

            # Network
            ("CMP-2026-113", "Massive Dynamic", "infra@massivedynamic-example.com", "Corporate VPN tunnel disconnects every 10 minutes",
             "The IPsec site-to-site VPN to the data center is experiencing packet loss exceeding 40%. Remote development workflows are completely halted.",
             "Network", "IT", "Infrastructure & Network", "CRITICAL", "Critical", "Frustration", "Negative", ComplaintStatus.IN_PROGRESS),

            ("CMP-2026-114", "Umbrella Corp", "sec-admin@umbrella-example.com", "Internal DNS resolving webhook endpoints to incorrect internal IP",
             "Our automated notifications stopped working because the platform's internal DNS resolver is returning a stale IP for `webhooks.internal.net`.",
             "Network", "IT", "Infrastructure & Network", "HIGH", "High", "Neutral", "Negative", ComplaintStatus.ASSIGNED),

            ("CMP-2026-115", "Nakatomi Trading", "support@nakatomi-example.com", "High latency and 504 timeouts on European API endpoints",
             "Our Frankfurt server cluster is measuring average latency of 1,850ms on all POST requests, frequently resulting in HTTP 504 Gateway Timeouts.",
             "Network", "IT", "Infrastructure & Network", "HIGH", "High", "Frustration", "Negative", ComplaintStatus.NEW),

            # Software
            ("CMP-2026-116", "Soylent Corp", "ops@soylent-example.com", "Web dashboard crashes with unhandled JavaScript error when exporting CSV",
             "Whenever any team member attempts to export a report of more than 500 rows to CSV, the UI freezes with a browser tab crash.",
             "Software", "IT", "Application Support", "MEDIUM", "Medium", "Frustration", "Negative", ComplaintStatus.ASSIGNED),

            ("CMP-2026-117", "Oscorp Tech", "dev@oscorp-example.com", "Webhook events arriving out of chronological order",
             "We configured webhooks for ticket status changes. Events for `CLOSED` are arriving before `IN_PROGRESS` events, corrupting our warehouse sync.",
             "Software", "IT", "Application Support", "MEDIUM", "Medium", "Neutral", "Neutral", ComplaintStatus.NEW),

            ("CMP-2026-118", "Monsters Logistics", "mike@monsters-example.com", "Search filter does not return records with special characters",
             "Searching for complaints containing hyphens or forward slashes returns zero results even when the records exist in the table.",
             "Software", "IT", "Application Support", "LOW", "Low", "Neutral", "Neutral", ComplaintStatus.RESOLVED),

            # Security
            ("CMP-2026-119", "Spectre Holdings", "ciso@spectre-example.com", "Suspicious login alerts triggered from unknown IP in unfamiliar country",
             "Our automated SIEM flagged 12 administrative login attempts from IP 185.220.101.5. None of our staff reside in that region. Please revoke active sessions.",
             "Security", "Security", "Incident Response", "CRITICAL", "Critical", "Fear", "Negative", ComplaintStatus.ESCALATED),

            ("CMP-2026-120", "Tyrell Corporation", "eldon@tyrell-example.com", "Phishing email spoofing corporate executive received by finance staff",
             "An email impersonating our CFO with subject 'Urgent Vendor Wire Instruction' was delivered to 8 staff members. Requesting immediate domain blocklist.",
             "Security", "Security", "Threat Intelligence & Compliance", "CRITICAL", "Critical", "Anxiety", "Negative", ComplaintStatus.IN_PROGRESS),

            ("CMP-2026-121", "Wonka Confectionery", "charlie@wonka-example.com", "API Secret key inadvertently committed to public repository",
             "A junior engineer pushed an API secret key to GitHub. We need an immediate hard revocation and regeneration of client token #TOK-9921.",
             "Security", "Security", "Incident Response", "CRITICAL", "Critical", "Panic", "Negative", ComplaintStatus.RESOLVED),

            # Payroll
            ("CMP-2026-122", "Staff Member A", "contractor1@fictionalstaff.io", "Missing holiday overtime premium on March 15 pay stub",
             "I worked 16 hours over the holiday weekend as pre-approved by my manager. My pay slip only reflects standard 40 hours without overtime calculation.",
             "Payroll", "HR", "Payroll Operations", "HIGH", "High", "Frustration", "Negative", ComplaintStatus.ASSIGNED),

            ("CMP-2026-123", "Staff Member B", "employee2@fictionalstaff.io", "Direct deposit routed to closed banking institution",
             "I submitted a direct deposit change form two weeks prior to payroll cutoff, but my monthly compensation was transmitted to my discontinued bank account.",
             "Payroll", "HR", "Payroll Operations", "HIGH", "High", "Anxiety", "Negative", ComplaintStatus.IN_PROGRESS),

            ("CMP-2026-124", "Staff Member C", "employee3@fictionalstaff.io", "Incorrect tax bracket deduction applied on annual bonus distribution",
             "My bonus compensation had state supplemental withholding calculated at 42% instead of the mandatory 22% rate for supplemental wages.",
             "Payroll", "HR", "Payroll Operations", "MEDIUM", "Medium", "Neutral", "Neutral", ComplaintStatus.RESOLVED),

            # Leave
            ("CMP-2026-125", "Staff Member D", "employee4@fictionalstaff.io", "Maternity leave entitlement balance showing 0 days in employee self-service portal",
             "My physician documentation was submitted and approved by HR last month. However, the portal claims my leave balance is zero days available.",
             "Leave", "HR", "Employee Relations & Leave", "HIGH", "High", "Anxiety", "Negative", ComplaintStatus.NEW),

            ("CMP-2026-126", "Staff Member E", "employee5@fictionalstaff.io", "Bereavement leave request not approved prior to scheduled departure",
             "I submitted immediate bereavement leave following the passing of a family member. System still marks my absence as 'Unexcused / Pending'.",
             "Leave", "HR", "Employee Relations & Leave", "HIGH", "High", "Grief", "Negative", ComplaintStatus.RESOLVED),

            ("CMP-2026-127", "Staff Member F", "employee6@fictionalstaff.io", "Annual PTO rollover days expired unexpectedly on calendar renewal",
             "According to employee handbook clause 4.2, up to 5 PTO days carry over into Q1. My portal shows 5 days were deducted without credit.",
             "Leave", "HR", "Employee Relations & Leave", "LOW", "Low", "Neutral", "Neutral", ComplaintStatus.ASSIGNED),

            # Delivery
            ("CMP-2026-128", "Oceanic Shipping", "dispatch@oceanic-example.com", "Urgent hardware replacement delayed past guaranteed overnight SLA",
             "Shipment #TRK-881920 containing mission-critical router parts was scheduled for 9:00 AM delivery. Tracking indicates it is still sitting at distribution depot.",
             "Delivery", "Logistics", "Last-Mile Delivery & RMA", "CRITICAL", "Critical", "Anger", "Negative", ComplaintStatus.ESCALATED),

            ("CMP-2026-129", "Initech Warehouse", "receiving@initech-example.com", "Pallet arrived with severe water damage and crushed packaging",
             "Order #PO-9912 consisting of 8 server chassis arrived with packaging soaked through. The delivery manifest was signed as damaged upon receipt.",
             "Delivery", "Logistics", "Freight & Dispatch", "HIGH", "High", "Frustration", "Negative", ComplaintStatus.IN_PROGRESS),

            ("CMP-2026-130", "Gekko Partners", "operations@gekko-example.com", "Incorrect delivery address utilized by courier despite confirmation email",
             "Our replacement terminals were sent to our secondary office in Chicago instead of our primary New York headquarters, leaving our desk unequipped.",
             "Delivery", "Logistics", "Last-Mile Delivery & RMA", "MEDIUM", "Medium", "Frustration", "Negative", ComplaintStatus.ASSIGNED),

            # Product
            ("CMP-2026-131", "Sovereign Health", "biomed@sovereign-example.org", "Hardware sensor unit failing self-calibration check on startup",
             "Unit serial #SN-88219 fails POST self-test with error code ERR_CALIBRATION_DRIFT. Need emergency replacement unit sent under warranty.",
             "Product", "Customer Support", "Tier 1 Customer Helpdesk", "HIGH", "High", "Anxiety", "Negative", ComplaintStatus.NEW),

            ("CMP-2026-132", "Delos Destinations", "tech@delos-example.com", "License validation key rejected after annual subscription renewal",
             "We renewed our 50-seat license yesterday. The license key generator provided key #LIC-8821-XP which the client application rejects as expired.",
             "Product", "Sales", "Commercial Renewals", "HIGH", "High", "Frustration", "Negative", ComplaintStatus.ASSIGNED),

            ("CMP-2026-133", "Stark Industries", "tony@stark-example.com", "Firmware update v2.4 bricked auxiliary sensor module interface",
             "Following the automated over-the-air firmware push, the auxiliary telemetry interface fails to communicate over CAN bus.",
             "Product", "IT", "Application Support", "HIGH", "High", "Anger", "Negative", ComplaintStatus.IN_PROGRESS),

            # Customer Support
            ("CMP-2026-134", "Bluth Company", "michael@bluth-example.com", "Critical ticket #TKT-8812 unattended for over 48 hours without update",
             "We filed an urgent ticket regarding data export failures two days ago. No support representative has acknowledged or responded to the inquiry.",
             "Customer Support", "Customer Support", "VIP & Priority Support", "HIGH", "High", "Anger", "Negative", ComplaintStatus.ESCALATED),

            ("CMP-2026-135", "Prestige Worldwide", "dale@prestige-example.com", "Support ticket closed by agent without resolving root problem",
             "Agent closed ticket #TKT-7719 stating 'User error' without reading the attached diagnostic crash dump. Problem is persistent across all users.",
             "Customer Support", "Customer Support", "VIP & Priority Support", "MEDIUM", "Medium", "Frustration", "Negative", ComplaintStatus.ASSIGNED),

            ("CMP-2026-136", "Sterling Cooper", "don@sterling-example.com", "Unprofessional and dismissive conduct during telephone escalation",
             "When escalating our billing inquiry on the support hotline, the phone agent hung up rather than transferring to a shift supervisor.",
             "Customer Support", "Customer Support", "VIP & Priority Support", "HIGH", "High", "Anger", "Negative", ComplaintStatus.NEW)
        ]

        complaint_count = 0
        for item in fictional_complaints_data:
            c_num, c_name, c_email, subj, desc, cat, d_name, t_name, prio, urg, emot, sent, st = item
            existing_c = db.query(Complaint).filter(Complaint.complaint_number == c_num).first()
            if existing_c:
                continue

            dept = created_departments.get(d_name)
            team = created_teams.get(f"{d_name}::{t_name}")

            # Assign an appropriate agent from this department if available
            eligible_agents = [a for a in created_agents if a.department_id == (dept.id if dept else None)]
            assigned_agent = random.choice(eligible_agents) if eligible_agents else None

            created_time = datetime.utcnow() - timedelta(days=random.randint(0, 14), hours=random.randint(1, 23))
            resolved_time = created_time + timedelta(hours=random.randint(2, 24)) if st in (ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED) else None

            complaint = Complaint(
                complaint_number=c_num,
                customer_name=c_name,
                customer_email=c_email,
                subject=subj,
                description=desc,
                source=ComplaintSource.WEB.value if random.random() > 0.4 else ComplaintSource.EMAIL.value,
                category=cat,
                sub_category=t_name,
                department_id=dept.id if dept else None,
                team_id=team.id if team else None,
                assigned_agent_id=assigned_agent.id if assigned_agent else None,
                sentiment=sent,
                emotion=emot,
                urgency=urg,
                priority=prio,
                priority_score=90.0 if prio == "CRITICAL" else (70.0 if prio == "HIGH" else (50.0 if prio == "MEDIUM" else 25.0)),
                ai_confidence=round(random.uniform(0.88, 0.98), 2),
                review_required=True if prio == "CRITICAL" else False,
                ai_status="COMPLETED",
                status=st.value if hasattr(st, "value") else str(st),
                summary=f"Fictional {cat} inquiry regarding {subj}. Priority {prio}, urgency {urg}.",
                sla_deadline=created_time + timedelta(hours=dept.sla_hours if dept else 24),
                is_escalated=(st == ComplaintStatus.ESCALATED or prio == "CRITICAL"),
                is_duplicate=False,
                duplicate_status="NONE",
                embedding=embeddings_engine.get_embedding(f"{subj} {desc}"),
                created_at=created_time,
                updated_at=datetime.utcnow(),
                resolved_at=resolved_time
            )
            db.add(complaint)
            db.commit()
            db.refresh(complaint)

            # Add AI Prediction metadata record
            pred = ComplaintPrediction(
                complaint_id=complaint.id,
                model_name="AutoTriage-Ensemble-v2",
                model_version="2.0.0",
                predicted_category=cat,
                category_confidence=complaint.ai_confidence,
                predicted_dept=d_name,
                dept_confidence=complaint.ai_confidence,
                urgency=urg,
                urgency_score=0.9 if urg == "Critical" else (0.75 if urg == "High" else 0.5),
                sentiment=sent,
                sentiment_score=-0.8 if sent == "Negative" else 0.0,
                emotion=emot,
                emotion_score=0.85,
                execution_time_ms=124.5,
                created_at=created_time
            )
            db.add(pred)

            # Add lifecycle event
            ev = ComplaintEvent(
                complaint_id=complaint.id,
                event_type="INGESTION",
                actor="System Ingestion Gateway",
                old_value=None,
                new_value=ComplaintStatus.NEW.value,
                description=f"Complaint ingested from {complaint.source} and triaged by AutoTriage AI.",
                created_at=created_time
            )

            db.add(ev)

            db.commit()
            complaint_count += 1

        print(f"Verified/Seeded {complaint_count} realistic fictional complaints (Total in DB: {db.query(Complaint).count()}).")

        # 7. Seed Official Knowledge Base Documents
        from app.services.knowledge_service import knowledge_service
        knowledge_service.seed_default_knowledge_base(db)
        print("Verified/Seeded standard enterprise knowledge base policy documents.")

        print("\nAll fictional company data seeded successfully:")
        print(f"  - Departments: {db.query(Department).count()}")
        print(f"  - Teams: {db.query(Team).count()}")
        print(f"  - Agents: {db.query(Agent).count()}")
        print(f"  - Routing Rules: {db.query(RoutingRule).count()}")
        print(f"  - SLA Rules: {db.query(SLARule).count()}")
        print(f"  - Complaints: {db.query(Complaint).count()}")

    except Exception as e:
        db.rollback()
        print(f"Error during enterprise database seeding: {e}", file=sys.stderr)
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("============================================================")
    print("AutoTriage AI - Fictional Company Data Seeder")
    print("============================================================")
    run_seed()
