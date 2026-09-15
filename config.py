import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    """Central application configuration with environment variables and secure defaults."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-complaint-system-secret-key-2026")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")
    PORT = int(os.getenv("PORT", 5000))

    # Storage Provider: PostgreSQL complaint_db primary with SQLite fallback
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:ranjupriya@localhost:5432/complaint_db")
    SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "autotriage.db")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Optional Gmail configuration via .env
    GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID", "")
    GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET", "")
    GMAIL_REDIRECT_URI = os.getenv("GMAIL_REDIRECT_URI", "http://localhost:8000/api/emails/callback")
    GMAIL_COMPLAINTS_LABEL = os.getenv("GMAIL_COMPLAINTS_LABEL", "Complaints")
    GMAIL_CONFIGURED = bool(GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET)

    # Optional AI LLM APIs
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

    # AI & Business Logic Thresholds
    AI_CONFIDENCE_THRESHOLD = float(os.getenv("AI_CONFIDENCE_THRESHOLD", 0.75))
    DUPLICATE_SIMILARITY_THRESHOLD = float(os.getenv("DUPLICATE_SIMILARITY_THRESHOLD", 0.65))

    # SLA targets in hours
    SLA_HOURS = {
        "Critical": int(os.getenv("SLA_HOURS_CRITICAL", 2)),
        "High": int(os.getenv("SLA_HOURS_HIGH", 8)),
        "Medium": int(os.getenv("SLA_HOURS_MEDIUM", 24)),
        "Low": int(os.getenv("SLA_HOURS_LOW", 72)),
    }

    # Department & Sub-department taxonomy
    DEPARTMENTS = {
        "Finance": {
            "name": "Finance Department",
            "icon": "💰",
            "sub_departments": [
                "Payments & Refunds",
                "Billing & Invoicing",
                "Subscription Services",
                "Fraud & Chargebacks"
            ]
        },
        "IT": {
            "name": "IT & Infrastructure",
            "icon": "🖥️",
            "sub_departments": [
                "System & Server Outages",
                "Software Bug & Glitch",
                "Account Access & Login",
                "Network & Connectivity"
            ]
        },
        "Security": {
            "name": "Security & Compliance",
            "icon": "🔒",
            "sub_departments": [
                "Account Compromise",
                "Data Privacy & Compliance",
                "Phishing & Suspicious Activity",
                "Permission & Identity"
            ]
        },
        "Support": {
            "name": "Customer Support",
            "icon": "🎧",
            "sub_departments": [
                "Order Tracking & Shipping",
                "Product Inquiries",
                "Returns & Replacements",
                "General Customer Service"
            ]
        },
        "Operations": {
            "name": "Operations & Administration",
            "icon": "🏢",
            "sub_departments": [
                "Service Escalations",
                "Policy & Terms Enforcement",
                "Academic / Campus Admin",
                "Vendor Management"
            ]
        }
    }
