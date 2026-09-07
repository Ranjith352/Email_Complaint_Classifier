import math
import re
import logging
from typing import List, Dict, Set, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

_transformer_model = None

def get_embedder():
    global _transformer_model
    if _transformer_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _transformer_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
            logger.info(f"Loaded SentenceTransformer: {settings.EMBEDDING_MODEL_NAME}")
        except Exception as e:
            logger.info(f"SentenceTransformer not loaded ({e}). Using dense semantic concept vector projection.")
    return _transformer_model

# Curated semantic concept spaces for cross-wording semantic matching
SEMANTIC_CONCEPT_CLUSTERS: Dict[str, Dict[str, Any]] = {
    "FINANCIAL_DEBIT_CHARGE": {
        "base_idx": 0,
        "span": 40,
        "weight": 3.5,
        "terms": [
            "money", "funds", "deducted", "deduct", "deduction", "deducting",
            "charged", "charge", "charges", "charging", "debited", "debit", "debits",
            "paid", "pay", "payment", "payments", "transaction", "transactions",
            "billed", "billing", "bill", "bills", "fee", "fees", "cost", "amount",
            "rupees", "inr", "usd", "dollars", "bank", "card", "statement", "account"
        ]
    },
    "MULTIPLICITY_DUPLICATE": {
        "base_idx": 40,
        "span": 40,
        "weight": 4.0,
        "terms": [
            "twice", "two times", "2 times", "double", "duplicate", "second time",
            "repeated", "again", "two fold", "twice for", "double charged",
            "charged twice", "deducted twice", "two charges", "two deductions"
        ]
    },
    "REFUND_REVERSAL": {
        "base_idx": 80,
        "span": 35,
        "weight": 3.0,
        "terms": [
            "refund", "refunds", "refunded", "refunding", "reversal", "reverse",
            "reversed", "chargeback", "return", "returned", "reimburse",
            "reimbursement", "cashback", "credit note", "give back"
        ]
    },
    "TECHNICAL_OUTAGE_CRASH": {
        "base_idx": 115,
        "span": 35,
        "weight": 3.5,
        "terms": [
            "outage", "down", "crash", "crashed", "crashing", "broken", "500",
            "503", "502", "internal server error", "error", "errors", "offline",
            "unreachable", "timeout", "latency", "slow", "freeze", "frozen",
            "glitch", "bug", "exception", "failed to load", "white screen"
        ]
    },
    "ACCOUNT_AUTHENTICATION": {
        "base_idx": 150,
        "span": 35,
        "weight": 3.0,
        "terms": [
            "login", "log in", "signin", "sign in", "password", "auth",
            "authentication", "credentials", "otp", "2fa", "lockout", "locked",
            "blocked", "reset password", "access portal", "cannot login"
        ]
    },
    "SECURITY_BREACH_COMPROMISE": {
        "base_idx": 185,
        "span": 35,
        "weight": 4.0,
        "terms": [
            "hack", "hacked", "hacker", "breach", "compromised", "unauthorized",
            "stolen", "phishing", "malware", "intruder", "hijacked", "leak",
            "suspicious activity", "suspicious login", "identity theft"
        ]
    },
    "LOGISTICS_SHIPPING_DELIVERY": {
        "base_idx": 220,
        "span": 35,
        "weight": 3.0,
        "terms": [
            "delivery", "deliver", "delivered", "shipping", "shipment", "package",
            "parcel", "courier", "tracking", "transit", "lost parcel",
            "damaged item", "damaged goods", "delayed delivery", "dispatch"
        ]
    },
    "HR_PAYROLL_LEAVE": {
        "base_idx": 255,
        "span": 30,
        "weight": 3.0,
        "terms": [
            "salary", "payroll", "payslip", "leave", "vacation", "sick leave",
            "employee", "workplace", "hr", "benefits", "tax deduction", "bonus"
        ]
    }
}

class EmbeddingsEngine:
    @staticmethod
    def get_embedding(text: str) -> List[float]:
        """Generate 384-dimensional dense semantic embedding vector.
        Uses Sentence Transformers when available, or continuous semantic concept subspace projection.
        """
        embedder = get_embedder()
        if embedder is not None:
            try:
                vec = embedder.encode(text, normalize_embeddings=True)
                return vec.tolist()
            except Exception as e:
                logger.warning(f"Transformer encoding error: {e}")

        dim = settings.VECTOR_DIMENSION
        vec = [0.0] * dim
        cleaned = (text or "").lower()

        # 1. Semantic Concept Subspace Projection
        for concept_name, config in SEMANTIC_CONCEPT_CLUSTERS.items():
            base_idx = config["base_idx"]
            span = config["span"]
            weight = config["weight"]
            terms = config["terms"]

            # Check for matches of terms (supporting phrases and words)
            matched_terms = 0
            for term in terms:
                if " " in term:
                    if term in cleaned:
                        matched_terms += 2
                else:
                    pattern = rf"\b{re.escape(term)}\b"
                    if re.search(pattern, cleaned):
                        matched_terms += 1

            if matched_terms > 0:
                activation = math.log1p(matched_terms) * weight
                for offset in range(span):
                    idx = (base_idx + offset) % dim
                    # Smooth Gaussian/sine continuous distribution across the concept subspace
                    sub_weight = activation * (0.8 + 0.4 * math.sin(offset * 0.5))
                    vec[idx] += sub_weight

        # 2. Lexical & Contextual Subword Projection (dimensions 285..383)
        lexical_base = 285
        lexical_span = dim - lexical_base
        words = re.findall(r'\w+', cleaned)
        for i, word in enumerate(words):
            idx = lexical_base + (abs(hash(word)) % lexical_span)
            pos_weight = 1.0 / (1.0 + (i * 0.05))
            vec[idx] += pos_weight * 0.5

        # 3. L2 Normalization
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [round(x / norm, 6) for x in vec]
        return vec

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

embeddings_engine = EmbeddingsEngine()
