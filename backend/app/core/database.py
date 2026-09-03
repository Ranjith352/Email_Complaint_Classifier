import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

engine = None
SessionLocal = None
IS_POSTGRES = False

def init_db():
    global engine, SessionLocal, IS_POSTGRES
    db_url = settings.DATABASE_URL
    
    if db_url and "postgresql" in db_url:
        try:
            test_engine = create_engine(db_url, pool_pre_ping=True)
            with test_engine.connect() as conn:
                try:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                    conn.commit()
                    logger.info("PostgreSQL pgvector extension verified/enabled.")
                except Exception as ext_err:
                    logger.warning(f"Note on pgvector extension: {ext_err}")
            engine = test_engine
            IS_POSTGRES = True
            logger.info(f"Connected successfully to PostgreSQL at {db_url.split('@')[-1] if '@' in db_url else 'local'}")
        except Exception as e:
            logger.warning(f"PostgreSQL connection failed ({e}). Falling back to local SQLite database: {settings.SQLITE_FALLBACK_URL}")
            engine = create_engine(settings.SQLITE_FALLBACK_URL, connect_args={"check_same_thread": False})
            IS_POSTGRES = False
    else:
        engine = create_engine(settings.SQLITE_FALLBACK_URL, connect_args={"check_same_thread": False})
        IS_POSTGRES = False

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

init_db()

def get_database_url():
    """Returns active database connection URL."""
    return settings.DATABASE_URL if IS_POSTGRES else settings.SQLITE_FALLBACK_URL

def get_db():
    """FastAPI Dependency for database session injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
