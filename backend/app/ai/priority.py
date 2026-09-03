from typing import Dict, Any, List

class PriorityCalculator:
    @staticmethod
    def calculate(
        urgency: str,
        sentiment: str,
        entities: List[Dict[str, Any]],
        category: str
    ) -> Dict[str, Any]:
        """Calculates multi-factor business priority score (0-100) and tier (P1-P4)."""
        base_scores = {
            "Critical": 80.0,
            "High": 60.0,
            "Medium": 40.0,
            "Low": 20.0
        }
        score = base_scores.get(urgency, 40.0)

        # Negative sentiment or anger escalates priority
        if str(sentiment).upper() == "NEGATIVE":
            score += 10.0

        # Presence of monetary transaction or large amount escalates priority
        has_amount = any(e.get("entity_type") == "AMOUNT" for e in entities)
        has_txn = any(e.get("entity_type") == "TRANSACTION_ID" for e in entities)
        if has_amount or has_txn:
            score += 8.0

        # Security category gets dedicated priority bump
        if category == "Security Issue":
            score += 12.0

        # Bound score between 0 and 100
        final_score = round(min(100.0, max(0.0, score)), 1)

        # Map to enterprise P1-P4
        if final_score >= 85.0:
            level = "P1"  # Immediate escalation (4-hour SLA)
        elif final_score >= 65.0:
            level = "P2"  # Urgent (8-hour SLA)
        elif final_score >= 40.0:
            level = "P3"  # Standard (24-hour SLA)
        else:
            level = "P4"  # Low (48-hour SLA)

        return {
            "priority_score": final_score,
            "priority_level": level
        }

priority_calculator = PriorityCalculator()
