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

    # Storage Provider: 'sqlite' or 'firestore'
    STORAGE_PROVIDER = os.getenv("STORAGE_PROVIDER", "sqlite").lower()
    SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "complaints.db")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR / SQLITE_DB_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Optional Firebase configuration
    FIREBASE_KEY_PATH = os.getenv("FIREBASE_KEY_PATH", "")
    FIREBASE_CONFIGURED = bool(
        FIREBASE_KEY_PATH and (BASE_DIR / FIREBASE_KEY_PATH).exists()
    )

    # Optional Gmail configuration
    GMAIL_CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH", "")
    GMAIL_TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH", "token.json")
    GMAIL_COMPLAINTS_LABEL = os.getenv("GMAIL_COMPLAINTS_LABEL", "Complaints")
    GMAIL_CONFIGURED = bool(
        GMAIL_CREDENTIALS_PATH and (BASE_DIR / GMAIL_CREDENTIALS_PATH).exists()
    )

    # Optional AI LLM APIs
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

    # AI & Business Logic Thresholds
    AI_CONFIDENCE_THRESHOLD = float(os.getenv("AI_CONFIDENCE_THRESHOLD", 0.75))
    DUPLICATE_SIMILARITY_THRESHOLD = float(os.getenv("DUPLICATE_SIMILARITY_THRESHOLD", 0.65))

    # SLA targets in hours
    SLA_HOURS = {
        "Critical": int(os.getenv("SLA_CRITICAL_HOURS", 4)),
        "High": int(os.getenv("SLA_HIGH_HOURS", 8)),
        "Medium": int(os.getenv("SLA_MEDIUM_HOURS", 24)),
        "Low": int(os.getenv("SLA_LOW_HOURS", 48)),
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
