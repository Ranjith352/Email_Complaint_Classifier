import os
import logging
from config import Config

logger = logging.getLogger(__name__)

db = None
_firebase_initialized = False

def init_firebase():
    """Safely initialize Firebase Admin SDK using environment configuration.
    Returns Firestore client or None if credentials are not configured."""
    global db, _firebase_initialized

    if _firebase_initialized:
        return db

    key_path = Config.FIREBASE_KEY_PATH
    if not key_path or not os.path.exists(key_path):
        logger.info("Firebase key not configured or file not found. Running with local storage.")
        return None

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        if not firebase_admin._apps:
            cred = credentials.Certificate(key_path)
            firebase_admin.initialize_app(cred)

        db = firestore.client()
        _firebase_initialized = True
        logger.info("Firebase Firestore successfully initialized.")
        return db
    except Exception as e:
        logger.warning(f"Failed to initialize Firebase: {e}. Falling back to local storage.")
        db = None
        return None

def is_firebase_available():
    return db is not None or (Config.FIREBASE_KEY_PATH and os.path.exists(Config.FIREBASE_KEY_PATH))

# Attempt safe initialization on import
init_firebase()