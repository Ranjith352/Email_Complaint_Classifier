from typing import Dict, Any

URGENCY_KEYWORDS = {
    "Critical": [
        "immediately", "asap", "emergency", "urgent", "critical", "blocked", "hacked", "breach",
        "legal action", "lawyer", "police", "unauthorized", "right now", "severe", "outage", "down for everyone"
    ],
    "High": [
        "soon", "priority", "important", "double charged", "twice", "not working", "cannot access",
        "deadline", "fast", "today", "money deducted", "failed transaction"
    ],
    "Medium": [
        "please look into", "check", "issue", "problem", "inconvenience", "waiting", "delay", "trouble"
    ],
    "Low": [
        "whenever possible", "general question", "just wondering", "feedback", "suggestion", "inquiry", "minor"
    ]
}

class UrgencyDetector:
    @staticmethod
    def detect(text: str, category: str = None) -> Dict[str, Any]:
        """Determines urgency level and score."""
        cleaned = text.lower()
        scores = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        
        for level, keywords in URGENCY_KEYWORDS.items():
            for kw in keywords:
                if kw in cleaned:
                    scores[level] += 2 if level in ("Critical", "High") else 1

        # Domain adjustments: Security breaches default to at least High
        if category == "Security Issue":
            scores["Critical"] += 2
        elif category in ("Billing", "Billing / Payment") and any(k in cleaned for k in ["double", "unauthorized", "stolen", "fraud"]):
            scores["High"] += 2

        primary = max(scores, key=scores.get)
        if scores[primary] == 0:
            primary = "Medium"

        score_mapping = {"Critical": 0.95, "High": 0.75, "Medium": 0.50, "Low": 0.25}

        return {
            "urgency": primary,
            "urgency_score": score_mapping[primary],
            "urgency_scores": scores
        }

urgency_detector = UrgencyDetector()
