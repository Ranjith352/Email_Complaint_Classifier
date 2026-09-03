import re
import math
import logging
from typing import Dict, Any, List, Tuple, Optional
import numpy as np

logger = logging.getLogger(__name__)

# Try loading sentence-transformers, fallback to deterministic TF-IDF/bag-of-words vectorizer
try:
    from sentence_transformers import SentenceTransformer
    _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    logger.info("Loaded SentenceTransformer ('all-MiniLM-L6-v2') successfully.")
except Exception as e:
    logger.warning(f"SentenceTransformer not initialized ({e}). Using deterministic lexical embedding.")
    _embedder = None

# Try loading spaCy, fallback to regex-based NER
try:
    import spacy
    _nlp = spacy.load("en_core_web_sm")
    logger.info("Loaded spaCy en_core_web_sm successfully.")
except Exception as e:
    logger.info(f"spaCy model not pre-installed ({e}). Using regex and linguistic heuristics.")
    _nlp = None

CATEGORY_TAXONOMY = {
    "Billing / Payment": {
        "department": "Finance",
        "keywords": [
            "charged", "charge", "refund", "paid", "payment", "bank", "credit card", "debit card",
            "transaction", "invoice", "receipt", "deducted", "double charged", "twice", "overcharged",
            "fee", "billing", "money", "rupees", "inr", "usd", "dollar", "emi", "wallet", "subscription",
            "pricing", "unauthorized charge", "cashback", "tax", "gst"
        ],
        "sub_departments": {
            "Payments & Refunds": ["refund", "double", "twice", "twice for", "duplicate", "deducted", "reversal", "failed transaction"],
            "Billing & Invoicing": ["invoice", "receipt", "gst", "tax", "statement", "bill", "overcharge"],
            "Subscription Services": ["subscription", "renew", "renewal", "membership", "plan", "cancel subscription"],
            "Fraud & Chargebacks": ["fraud", "unauthorized", "stolen", "scam", "compromised card"]
        }
    },
    "Technical Problem": {
        "department": "IT",
        "keywords": [
            "bug", "error", "crash", "glitch", "broken", "down", "outage", "slow", "server", "loading",
            "failed", "connection", "offline", "api", "app", "database", "login failed", "not working",
            "500", "404", "freeze", "white screen", "timeout", "latency", "dns"
        ],
        "sub_departments": {
            "System & Server Outages": ["down", "outage", "offline", "server", "maintenance", "unreachable", "500"],
            "Software Bug & Glitch": ["bug", "glitch", "crash", "error", "freeze", "button not working", "exception"],
            "Account Access & Login": ["login", "signin", "password", "reset", "otp", "2fa", "blocked account", "lockout"],
            "Network & Connectivity": ["slow", "latency", "timeout", "bandwidth", "disconnecting", "dns", "wifi"]
        }
    },
    "Security Issue": {
        "department": "Security",
        "keywords": [
            "hack", "hacked", "breach", "security", "vulnerability", "phishing", "spam", "malware",
            "unauthorized access", "suspicious", "leak", "compromised", "identity theft", "attacker",
            "stolen credentials", "data privacy", "gdpr", "permission"
        ],
        "sub_departments": {
            "Account Compromise": ["hacked", "unauthorized access", "compromised", "intruder", "hijacked"],
            "Data Privacy & Compliance": ["privacy", "gdpr", "leak", "personal data", "exposed", "confidential"],
            "Phishing & Suspicious Activity": ["phishing", "suspicious", "fake email", "spoof", "malware"],
            "Permission & Identity": ["permission", "identity", "privilege", "impersonation", "credentials"]
        }
    },
    "Customer Support": {
        "department": "Support",
        "keywords": [
            "delivery", "shipping", "order", "product", "damaged", "delayed", "tracking", "courier",
            "package", "item", "wrong item", "return", "exchange", "support", "help", "agent",
            "service", "customer care", "warranty", "missing"
        ],
        "sub_departments": {
            "Order Tracking & Shipping": ["tracking", "where is", "dispatch", "courier", "delayed delivery", "transit"],
            "Returns & Replacements": ["return", "replacement", "damaged", "broken item", "exchange", "wrong item"],
            "Product Inquiries": ["product", "specifications", "manual", "warranty", "feature", "availability"],
            "General Customer Service": ["help", "representative", "contact", "assistance", "inquiry"]
        }
    },
    "Operations & Admin": {
        "department": "Operations",
        "keywords": [
            "academic", "admission", "grade", "university", "faculty", "policy", "terms", "contract",
            "legal", "management", "escalation", "campus", "course", "facility", "staff", "behavior",
            "complaint against", "unprofessional", "manager"
        ],
        "sub_departments": {
            "Academic / Campus Admin": ["academic", "admission", "grade", "faculty", "course", "exam", "campus"],
            "Service Escalations": ["manager", "supervisor", "escalation", "escalate", "unacceptable behavior"],
            "Policy & Terms Enforcement": ["policy", "terms", "agreement", "rules", "contract", "compliance"],
            "Vendor Management": ["vendor", "contractor", "third-party", "partner", "facility"]
        }
    }
}

EMOTION_KEYWORDS = {
    "Anger": ["angry", "furious", "outrageous", "pathetic", "ridiculous", "unacceptable", "lawsuit", "sue", "terrible", "worst", "hate"],
    "Frustration": ["frustrated", "annoying", "tired of", "again", "still not", "twice", "repeatedly", "waste of time", "useless", "immediately"],
    "Anxiety": ["worried", "urgent", "emergency", "scared", "panicking", "afraid", "critical", "loss", "stolen"],
    "Disappointment": ["disappointed", "expected better", "let down", "unhappy", "poor quality", "regret", "bad experience"],
    "Gratitude": ["thank you", "appreciate", "helpful", "grateful", "glad"],
}

URGENCY_KEYWORDS = {
    "Critical": ["immediately", "asap", "emergency", "urgent", "critical", "blocked", "hacked", "breach", "legal action", "unauthorized", "right now", "severe"],
    "High": ["soon", "priority", "important", "double charged", "twice", "not working", "cannot access", "deadline", "fast", "today"],
    "Medium": ["please look into", "check", "issue", "problem", "inconvenience", "waiting"],
    "Low": ["whenever possible", "general question", "just wondering", "feedback", "suggestion", "inquiry"]
}

class NLPEngine:
    @staticmethod
    def get_embedding(text: str) -> List[float]:
        """Generate 384-dimensional dense semantic embedding vector."""
        if _embedder is not None:
            try:
                emb = _embedder.encode(text, normalize_embeddings=True)
                return emb.tolist()
            except Exception as e:
                logger.error(f"Embedding error with SentenceTransformer: {e}")
                
        # Deterministic 384-dimensional pseudo-embedding based on hash projection
        vec = [0.0] * 384
        words = re.findall(r'\w+', text.lower())
        if not words:
            return vec
        for i, word in enumerate(words):
            idx = abs(hash(word)) % 384
            vec[idx] += 1.0 / (1.0 + (i * 0.05))
            
        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    @staticmethod
    def extract_entities(text: str) -> Dict[str, Any]:
        """Extract named entities such as transaction IDs, amounts, dates, and order numbers."""
        entities: Dict[str, Any] = {
            "transaction_ids": [],
            "amounts": [],
            "dates": [],
            "emails": [],
            "order_ids": []
        }
        
        # spaCy extraction if present
        if _nlp is not None:
            try:
                doc = _nlp(text[:2000])
                for ent in doc.ents:
                    if ent.label_ in ("MONEY", "PERCENT"):
                        entities["amounts"].append(ent.text)
                    elif ent.label_ in ("DATE", "TIME"):
                        entities["dates"].append(ent.text)
            except Exception:
                pass
                
        # Regex extraction
        tx_matches = re.findall(r'\b(?:TXN|REF|TRX|INV|ORD)[-_]?[A-Z0-9]{4,12}\b', text, re.IGNORECASE)
        entities["transaction_ids"].extend(list(set(tx_matches)))
        
        order_matches = re.findall(r'#(?:[0-9]{4,10})', text)
        entities["order_ids"].extend(list(set(order_matches)))
        
        email_matches = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        entities["emails"].extend(list(set(email_matches)))
        
        amount_matches = re.findall(r'(?:[\$€£₹]|INR|USD)\s?[0-9]+(?:,[0-9]{3})*(?:\.[0-9]{2})?', text, re.IGNORECASE)
        entities["amounts"].extend(list(set(amount_matches)))
        
        return entities

    @classmethod
    def classify_complaint(cls, text: str) -> Dict[str, Any]:
        """Perform comprehensive classification: Category, Department, Sub-department, Urgency, Sentiment, and Confidence."""
        cleaned = text.lower()
        
        # Category scoring
        category_scores: Dict[str, float] = {}
        for cat, data in CATEGORY_TAXONOMY.items():
            score = 0
            for kw in data["keywords"]:
                if re.search(r'\b' + re.escape(kw) + r'\b', cleaned):
                    score += 2 if len(kw.split()) > 1 else 1
            category_scores[cat] = score
            
        best_cat = max(category_scores, key=category_scores.get)
        cat_score = category_scores[best_cat]
        
        if cat_score == 0:
            best_cat = "Customer Support"
            department = "Support"
            sub_department = "General Customer Service"
            confidence = 0.65
        else:
            department = CATEGORY_TAXONOMY[best_cat]["department"]
            # Sub department determination
            sub_dept_scores = {}
            for sub, kws in CATEGORY_TAXONOMY[best_cat]["sub_departments"].items():
                s_score = sum(1 for kw in kws if kw in cleaned)
                sub_dept_scores[sub] = s_score
            sub_department = max(sub_dept_scores, key=sub_dept_scores.get) if sub_dept_scores else None
            confidence = min(0.98, 0.70 + (cat_score * 0.04))

        # Urgency scoring
        urgency_scores = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for level, keywords in URGENCY_KEYWORDS.items():
            for kw in keywords:
                if kw in cleaned:
                    urgency_scores[level] += 2 if level == "Critical" else 1
        
        # Security issues or financial loss default to at least High
        if best_cat == "Security Issue":
            urgency_scores["Critical"] += 2
        elif best_cat == "Billing / Payment" and any(k in cleaned for k in ["double", "unauthorized", "stolen", "fraud"]):
            urgency_scores["High"] += 2
            
        best_urgency = max(urgency_scores, key=urgency_scores.get)
        if urgency_scores[best_urgency] == 0:
            best_urgency = "Medium"

        # Sentiment scoring
        sentiment_scores = {e: 0 for e in EMOTION_KEYWORDS}
        for emo, keywords in EMOTION_KEYWORDS.items():
            for kw in keywords:
                if kw in cleaned:
                    sentiment_scores[emo] += 1
        best_sentiment = max(sentiment_scores, key=sentiment_scores.get)
        if sentiment_scores[best_sentiment] == 0:
            best_sentiment = "Frustration" if best_urgency in ("Critical", "High") else "Neutral"

        entities = cls.extract_entities(text)

        return {
            "category": best_cat,
            "department": department,
            "sub_department": sub_department,
            "urgency": best_urgency,
            "sentiment": best_sentiment,
            "confidence": round(confidence, 2),
            "entities": entities
        }

nlp_engine = NLPEngine()
