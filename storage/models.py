import json
from datetime import datetime, timedelta

def generate_complaint_id(seq_num: int = 10001) -> str:
    """Generates standard enterprise Complaint ID format CMP-XXXXX."""
    return f"CMP-{seq_num}"

class ComplaintDict(dict):
    """Dictionary representation of a Complaint with convenient attribute access."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            return None

    def __setattr__(self, name, value):
        self[name] = value

    def to_dict(self):
        d = dict(self)
        # Parse entities if it's a JSON string
        if isinstance(d.get("entities"), str):
            try:
                d["entities"] = json.loads(d["entities"])
            except Exception:
                pass
        return d
