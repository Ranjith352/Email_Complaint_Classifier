import re
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# The 4 standardized urgency tiers
URGENCY_TIERS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

# Core Urgency Score Mapping
SCORE_MAPPING = {
    "CRITICAL": 0.95,
    "HIGH": 0.75,
    "MEDIUM": 0.50,
    "LOW": 0.25
}

# -------------------------------------------------------------
# Business Rules Pattern Definitions
# -------------------------------------------------------------

# Rule 1: Security & Account Compromise -> CRITICAL
CRITICAL_SECURITY_PATTERNS = [
    r'\bhack(?:ed|ing)?\b',
    r'\baccount\s+(?:has\s+been\s+|was\s+)?hacked\b',
    r'\bsecurity\s+breach\b',
    r'\bcompromised\b',
    r'\bunauthorized\s+access\b',
    r'\bstolen\s+credentials\b',
    r'\bransomware\b',
    r'\bidentity\s+theft\b'
]

# Rule 2: Legal, Law enforcement, & Regulatory Escalations -> CRITICAL
CRITICAL_LEGAL_PATTERNS = [
    r'\blawyer\b',
    r'\battorney\b',
    r'\blawsuit\b',
    r'\bsue\s+(?:you|your\s+company)\b',
    r'\blegal\s+action\b',
    r'\bpolice\s+report\b',
    r'\bregulatory\s+complaint\b',
    r'\bcfpb\b'
]

# Rule 3: Major Production Outage / Total System Failure -> CRITICAL
CRITICAL_OUTAGE_PATTERNS = [
    r'\bsystem\s+outage\b',
    r'\bserver\s+down\b',
    r'\bproduction\s+crash\b',
    r'\boutage\s+for\s+everyone\b',
    r'\btotal\s+blackout\b',
    r'\bemergency\s+downtime\b'
]

# Rule 4: Financial Distress / Fraud / Repeated Failures -> HIGH
HIGH_FINANCIAL_PATTERNS = [
    r'\bdouble\s+charged?\b',
    r'\bcharged\s+twice\b',
    r'\bunauthorized\s+(?:charge|transaction|deduction)\b',
    r'\bmoney\s+(?:was\s+)?deducted\b',
    r'\bcannot\s+access\s+account\b',
    r'\blocked\s+out\b',
    r'\bfraud(?:ulent)?\b'
]

# Rule 5: Explicit High Urgency Adverbs -> HIGH
HIGH_URGENCY_WORDS = [
    r'\basap\b',
    r'\burgent(?:ly)?\b',
    r'\bimmediate(?:ly)?\b',
    r'\bright\s+now\b',
    r'\bcritical\s+deadline\b'
]

# Rule 6: General Inquiries, Subscription Details, Informational -> LOW
LOW_INQUIRY_PATTERNS = [
    r'\bneed\s+information\s+(?:about|regarding|on)\b',
    r'\binformation\s+about\s+(?:your\s+)?(?:subscription|plans|pricing|service)\b',
    r'\bgeneral\s+question\b',
    r'\bjust\s+wondering\b',
    r'\bcan\s+you\s+(?:please\s+)?(?:tell|inform|guide)\s+me\b',
    r'\bfeature\s+request\b',
    r'\bfeedback\b',
    r'\bsuggestion\b',
    r'\bhow\s+do\s+i\b',
    r'\bpricing\s+details\b'
]

class BaseUrgencyDetector(ABC):
    """Abstract Base Class for Urgency Detectors."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass

    @abstractmethod
    def detect(self, text: str, category: Optional[str] = None, entities: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Detects urgency tier combining model analysis with business rules."""
        pass

class RuleEnhancedUrgencyDetector(BaseUrgencyDetector):
    """Urgency Detector combining machine learning / transformer probability estimation with business rules.

    Tiers:
    - LOW
    - MEDIUM
    - HIGH
    - CRITICAL
    """

    def __init__(self, model_name: str = "distilbert-base-uncased-urgency"):
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    def detect(self, text: str, category: Optional[str] = None, entities: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        if not text or not text.strip():
            return {
                "urgency": "LOW",
                "urgency_score": 0.25,
                "confidence": 0.50,
                "applied_rules": ["DEFAULT_EMPTY_INPUT"],
                "urgency_scores": {"LOW": 0.70, "MEDIUM": 0.15, "HIGH": 0.10, "CRITICAL": 0.05},
                "model": self._model_name
            }

        cleaned = text.lower()
        applied_rules: List[str] = []

        # -------------------------------------------------------------
        # 1. Base Model / Lexical Probability Distribution
        # -------------------------------------------------------------
        model_scores = {
            "LOW": 0.25,
            "MEDIUM": 0.50,
            "HIGH": 0.15,
            "CRITICAL": 0.10
        }

        # Medium indicators
        if any(w in cleaned for w in ["issue", "problem", "delay", "waiting", "not working", "help", "trouble"]):
            model_scores["MEDIUM"] += 0.25
            model_scores["LOW"] -= 0.10

        # -------------------------------------------------------------
        # 2. Business Rules Evaluation
        # -------------------------------------------------------------
        rule_urgency: Optional[str] = None

        # Rule A: Security Compromise & Hacked Accounts -> CRITICAL (Highest priority override)
        for pattern in CRITICAL_SECURITY_PATTERNS:
            if re.search(pattern, cleaned):
                rule_urgency = "CRITICAL"
                applied_rules.append(f"BUSINESS_RULE: Account compromise / security breach ({pattern})")
                break

        # Rule B: Legal Action & Lawsuits -> CRITICAL
        if not rule_urgency:
            for pattern in CRITICAL_LEGAL_PATTERNS:
                if re.search(pattern, cleaned):
                    rule_urgency = "CRITICAL"
                    applied_rules.append("BUSINESS_RULE: Legal or regulatory escalation detected")
                    break

        # Rule C: Outage / System Crash -> CRITICAL
        if not rule_urgency:
            for pattern in CRITICAL_OUTAGE_PATTERNS:
                if re.search(pattern, cleaned):
                    rule_urgency = "CRITICAL"
                    applied_rules.append("BUSINESS_RULE: Production system outage detected")
                    break

        # Rule D: Financial Loss / Unauthorized Transactions -> HIGH
        if not rule_urgency:
            for pattern in HIGH_FINANCIAL_PATTERNS:
                if re.search(pattern, cleaned):
                    rule_urgency = "HIGH"
                    applied_rules.append("BUSINESS_RULE: Financial impact / double charge detected")
                    break

        # Rule E: Urgent SLA Adverbs -> HIGH
        if not rule_urgency:
            for pattern in HIGH_URGENCY_WORDS:
                if re.search(pattern, cleaned):
                    rule_urgency = "HIGH"
                    applied_rules.append("BUSINESS_RULE: Explicit urgent action keywords")
                    break

        # Rule F: Informational / Subscription Inquiries -> LOW
        if not rule_urgency:
            for pattern in LOW_INQUIRY_PATTERNS:
                if re.search(pattern, cleaned):
                    rule_urgency = "LOW"
                    applied_rules.append("BUSINESS_RULE: General information or subscription inquiry")
                    break

        # Domain adjustments: Security Issue category defaults to at least HIGH or CRITICAL
        if category and "security" in category.lower() and rule_urgency != "CRITICAL":
            rule_urgency = "CRITICAL" if any(w in cleaned for w in ["breach", "hack", "stolen"]) else "HIGH"
            applied_rules.append("BUSINESS_RULE: Security category threshold applied")

        # -------------------------------------------------------------
        # 3. Decision Fusion (Model + Business Rules)
        # -------------------------------------------------------------
        if rule_urgency:
            final_urgency = rule_urgency
            confidence = 0.95 if final_urgency in ("CRITICAL", "LOW") else 0.88
        else:
            final_urgency = max(model_scores, key=model_scores.get)
            confidence = 0.70
            applied_rules.append("MODEL_PROBABILITY_ESTIMATION")

        # Normalize score distribution
        final_scores = {tier: 0.05 for tier in URGENCY_TIERS}
        final_scores[final_urgency] = confidence

        return {
            "urgency": final_urgency,
            "urgency_score": SCORE_MAPPING.get(final_urgency, 0.50),
            "confidence": confidence,
            "applied_rules": applied_rules,
            "urgency_scores": final_scores,
            "model": f"{self._model_name}+BusinessRules"
        }

class UrgencyDetector(RuleEnhancedUrgencyDetector):
    """Facade singleton maintaining backwards compatibility."""
    pass

def get_urgency_detector() -> BaseUrgencyDetector:
    """Factory function for urgency detector."""
    return UrgencyDetector()

# Primary singleton export
urgency_detector = UrgencyDetector()
