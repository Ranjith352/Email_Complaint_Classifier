import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "AutoTriage AI - Enterprise Complaint Management"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api"
    
    # Security & JWT Authentication
    SECRET_KEY: str = Field(default="dev-jwt-secret-key-change-in-production-2026", env="JWT_SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]
    
    # PostgreSQL & pgvector Database Configuration
    DATABASE_URL: str = Field(
        default="postgresql+psycopg2://postgres:postgres@localhost:5432/complaints_db",
        env="DATABASE_URL"
    )
    SQLITE_FALLBACK_URL: str = "sqlite:///./autotriage.db"
    
    # Vector Search & Semantic Embeddings
    VECTOR_DIMENSION: int = 384  # Default for all-MiniLM-L6-v2
    EMBEDDING_MODEL_NAME: str = Field(default="all-MiniLM-L6-v2", env="EMBEDDING_MODEL_NAME")
    
    # Generative AI Provider: 'ollama' (default local) or 'groq' (optional cloud)
    LLM_PROVIDER: str = Field(default="ollama", env="LLM_PROVIDER")
    
    # Local Ollama Configuration
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    OLLAMA_MODEL: str = Field(default="llama3.2", env="OLLAMA_MODEL")
    
    # Cloud Groq Configuration (Optional)
    GROQ_API_KEY: str = Field(default="", env="GROQ_API_KEY")
    GROQ_MODEL: str = Field(default="llama-3.3-70b-versatile", env="GROQ_MODEL")
    
    # Gmail API OAuth 2.0 Ingestion
    GMAIL_CLIENT_ID: str = Field(default="", env="GMAIL_CLIENT_ID")
    GMAIL_CLIENT_SECRET: str = Field(default="", env="GMAIL_CLIENT_SECRET")
    GMAIL_REDIRECT_URI: str = Field(default="http://localhost:8000/api/emails/callback", env="GMAIL_REDIRECT_URI")
    GMAIL_CREDENTIALS_PATH: str = Field(default="credentials.json", env="GMAIL_CREDENTIALS_PATH")
    GMAIL_TOKEN_PATH: str = Field(default="token.json", env="GMAIL_TOKEN_PATH")
    GMAIL_COMPLAINTS_LABEL: str = Field(default="Complaints", env="GMAIL_COMPLAINTS_LABEL")
    
    # SLA Target Deadlines (Hours)
    SLA_HOURS_CRITICAL: int = 4
    SLA_HOURS_HIGH: int = 8
    SLA_HOURS_MEDIUM: int = 24
    SLA_HOURS_LOW: int = 48

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
