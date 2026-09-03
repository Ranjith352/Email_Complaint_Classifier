import logging
from config import Config
from storage.repository import ComplaintRepository
from storage.sqlite_repo import SQLiteComplaintRepository

logger = logging.getLogger(__name__)

_repo_instance = None

def get_repository() -> ComplaintRepository:
    """Returns the singleton repository instance based on configuration."""
    global _repo_instance
    if _repo_instance is not None:
        return _repo_instance

    provider = Config.STORAGE_PROVIDER.lower()
    if provider == "firestore":
        try:
            from storage.firebase_repo import FirebaseComplaintRepository
            _repo_instance = FirebaseComplaintRepository()
            logger.info("Using Firebase Firestore repository.")
            return _repo_instance
        except Exception as e:
            logger.warning(f"Failed to initialize Firestore repository: {e}. Falling back to SQLite.")

    _repo_instance = SQLiteComplaintRepository()
    logger.info("Using SQLite repository.")
    return _repo_instance
