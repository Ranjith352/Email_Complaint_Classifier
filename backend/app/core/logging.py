import logging
import json
import sys
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Formats log records as structured JSON without exposing internal stack traces."""
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "client_ip"):
            log_entry["client_ip"] = record.client_ip
        if hasattr(record, "method") and hasattr(record, "path"):
            log_entry["http"] = {"method": record.method, "path": record.path}
        if record.exc_info and not record.exc_text:
            # Note exception class name only, without raw stack traces in production output
            log_entry["exception_type"] = record.exc_info[0].__name__ if record.exc_info[0] else "Unknown"
        return json.dumps(log_entry)

def setup_logging(level: str = "INFO", json_format: bool = False):
    """Configures structured enterprise application logging."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    handler = logging.StreamHandler(sys.stdout)
    if json_format:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"))
    
    root_logger.addHandler(handler)

logger = logging.getLogger("autotriage_ai")
