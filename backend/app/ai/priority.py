import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Default scoring weights matching the deterministic formula
DEFAULT_PRIORITY_WEIGHTS = {
    "urgency": 0.30,
    "sentiment": 0.15,
    "business_impact": 0.20,
    "customer_impact": 0.15,
    "sla_risk": 0.20
}

# The 4 priority tiers and their thresholds
# 0-30: LOW
# 31-60: MEDIUM
# 61-80: HIGH
# 81-100: CRITICAL
PRIORITY_TIERS = {
    "CRITICAL": (81.0, 100.0, "P1"),
    "HIGH": (61.0, 80.0, "P2"),
    "MEDIUM": (31.0, 60.0, "P3"),
    "LOW": (0.0, 30.0, "P4")
}

class PriorityEngine:
    """Deterministic Multi-Factor Priority Engine.

    Calculates priority deterministically using:
    priority_score =
        urgency_score * 0.30
        + sentiment_score * 0.15
        + business_impact * 0.20
        + customer_impact * 0.15
        + sla_risk * 0.20

    Tier Mapping:
    - 0-30:   LOW
    - 31-60:  MEDIUM
    - 61-80:  HIGH
    - 81-100: CRITICAL

    Weights are fully configurable.
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self._weights = self._normalize_weights(weights or DEFAULT_PRIORITY_WEIGHTS)

    @property
    def weights(self) -> Dict[str, float]:
        return dict(self._weights)

    def set_weights(self, weights: Dict[str, float]):
        """Configures priority scoring weights."""
        self._weights = self._normalize_weights(weights)

    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Validates and ensures weights sum to 1.0."""
        expected_keys = ["urgency", "sentiment", "business_impact", "customer_impact", "sla_risk"]
        sanitized = {k: float(weights.get(k, DEFAULT_PRIORITY_WEIGHTS.get(k, 0.20))) for k in expected_keys}
        total = sum(sanitized.values())
        if total > 0 and not (0.99 <= total <= 1.01):
            # Scale proportionally if sum is not 1.0
            sanitized = {k: round(v / total, 4) for k, v in sanitized.items()}
        return sanitized

    def calculate(
        self,
        urgency: Optional[str] = None,
        sentiment: Optional[str] = None,
        entities: Optional[List[Dict[str, Any]]] = None,
        category: Optional[str] = None,
        emotion: Optional[str] = None,
        urgency_score: Optional[float] = None,
        sentiment_score: Optional[float] = None,
        business_impact: Optional[float] = None,
        customer_impact: Optional[float] = None,
        sla_risk: Optional[float] = None,
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Calculates deterministic multi-factor priority score (0-100) and tier."""
        entities = entities or []
        active_weights = self._normalize_weights(weights) if weights else self._weights

        # -------------------------------------------------------------
        # 1. Resolve Factor 1: Urgency Score (0 - 100)
        # -------------------------------------------------------------
        if urgency_score is not None:
            f_urgency = float(urgency_score) if urgency_score > 1.0 else float(urgency_score) * 100.0
        else:
            urg_key = (urgency or "MEDIUM").upper()
            urg_map = {
                "CRITICAL": 100.0,
                "HIGH": 75.0,
                "MEDIUM": 50.0,
                "LOW": 25.0
            }
            f_urgency = urg_map.get(urg_key, 50.0)

        # -------------------------------------------------------------
        # 2. Resolve Factor 2: Sentiment Score (0 - 100)
        # (Customer negativity/distress directly boosts urgency & priority)
        # -------------------------------------------------------------
        if sentiment_score is not None:
            if sentiment_score < 0:
                # Negative polarity (-1.0 to 0.0) maps to (50.0 to 100.0)
                f_sentiment = round(50.0 - (sentiment_score * 50.0), 1)
            else:
                f_sentiment = float(sentiment_score)
        else:
            sent_key = (sentiment or "NEUTRAL").upper()
            if "NEG" in sent_key:
                f_sentiment = 90.0
            elif "POS" in sent_key:
                f_sentiment = 15.0
            else:
                f_sentiment = 45.0

        # -------------------------------------------------------------
        # 3. Resolve Factor 3: Business Impact (0 - 100)
        # -------------------------------------------------------------
        if business_impact is not None:
            f_business = float(business_impact) if business_impact > 1.0 else float(business_impact) * 100.0
        else:
            f_business = 40.0
            cat_lower = (category or "").lower()

            # High stakes categories
            if any(k in cat_lower for k in ["security", "fraud", "breach", "outage", "system"]):
                f_business = 95.0
            elif any(k in cat_lower for k in ["billing", "payment", "refund", "payroll"]):
                f_business = 75.0
            elif any(k in cat_lower for k in ["technical", "hardware", "network", "application"]):
                f_business = 65.0
            elif any(k in cat_lower for k in ["general", "inquiry", "feedback", "suggestion"]):
                f_business = 20.0

            # Presence of financial entities elevates business impact
            has_amount = any(e.get("entity_type") == "AMOUNT" for e in entities)
            has_txn = any(e.get("entity_type") in ("TRANSACTION_ID", "ORDER_ID") for e in entities)
            if has_amount or has_txn:
                f_business = min(100.0, f_business + 10.0)

        # -------------------------------------------------------------
        # 4. Resolve Factor 4: Customer Impact (0 - 100)
        # -------------------------------------------------------------
        if customer_impact is not None:
            f_customer = float(customer_impact) if customer_impact > 1.0 else float(customer_impact) * 100.0
        else:
            emo_key = (emotion or "").upper()
            if emo_key in ("ANGER", "FEAR"):
                f_customer = 95.0
            elif emo_key == "FRUSTRATION":
                f_customer = 80.0
            elif emo_key == "SADNESS":
                f_customer = 65.0
            elif emo_key == "SATISFACTION":
                f_customer = 15.0
            elif emo_key == "NEUTRAL":
                f_customer = 35.0
            else:
                f_customer = 50.0

        # -------------------------------------------------------------
        # 5. Resolve Factor 5: SLA Risk (0 - 100)
        # -------------------------------------------------------------
        if sla_risk is not None:
            f_sla = float(sla_risk) if sla_risk > 1.0 else float(sla_risk) * 100.0
        else:
            urg_key = (urgency or "MEDIUM").upper()
            sla_map = {
                "CRITICAL": 95.0,  # 4-hour SLA target
                "HIGH": 75.0,      # 8-hour SLA target
                "MEDIUM": 45.0,    # 24-hour SLA target
                "LOW": 20.0        # 48-hour SLA target
            }
            f_sla = sla_map.get(urg_key, 45.0)

        # -------------------------------------------------------------
        # 6. Apply Configurable Weighted Deterministic Formula
        # -------------------------------------------------------------
        priority_score = (
            f_urgency * active_weights["urgency"]
            + f_sentiment * active_weights["sentiment"]
            + f_business * active_weights["business_impact"]
            + f_customer * active_weights["customer_impact"]
            + f_sla * active_weights["sla_risk"]
        )
        final_score = round(min(100.0, max(0.0, priority_score)), 1)

        # -------------------------------------------------------------
        # 7. Map Score to Explicit Thresholds
        # 0-30:   LOW
        # 31-60:  MEDIUM
        # 61-80:  HIGH
        # 81-100: CRITICAL
        # -------------------------------------------------------------
        if final_score >= 81.0:
            tier = "CRITICAL"
            code = "P1"
        elif final_score >= 61.0:
            tier = "HIGH"
            code = "P2"
        elif final_score >= 31.0:
            tier = "MEDIUM"
            code = "P3"
        else:
            tier = "LOW"
            code = "P4"

        return {
            "priority": tier,
            "priority_score": final_score,
            "priority_level": code,
            "priority_code": code,
            "tier": tier,
            "factors": {
                "urgency_score": f_urgency,
                "sentiment_score": f_sentiment,
                "business_impact": f_business,
                "customer_impact": f_customer,
                "sla_risk": f_sla
            },
            "weights": active_weights
        }

class PriorityCalculator(PriorityEngine):
    """Facade singleton keeping backwards compatibility."""
    pass

def get_priority_engine(weights: Optional[Dict[str, float]] = None) -> PriorityEngine:
    """Factory function to get a PriorityEngine instance."""
    return PriorityEngine(weights=weights)

# Primary singleton export
priority_calculator = PriorityCalculator()
