import re
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# The 10 enterprise entity types
TARGET_ENTITY_TYPES = [
    "PERSON",
    "EMAIL",
    "PHONE",
    "ORDER_ID",
    "TRANSACTION_ID",
    "AMOUNT",
    "DATE",
    "PRODUCT",
    "COMPANY",
    "LOCATION"
]

KNOWN_COMPANIES = {
    "google", "microsoft", "apple", "amazon", "stripe", "paypal", "netflix",
    "uber", "spotify", "meta", "fincorp", "shopify", "fedex", "ups", "dhl",
    "salesforce", "oracle", "adobe", "samsung", "honda", "walmart", "target"
}

KNOWN_PRODUCTS = {
    "subscription", "membership", "software license", "cloud storage", "iphone",
    "macbook", "laptop", "pro plan", "annual plan", "premium tier", "credit card",
    "debit card", "gift card", "smart watch", "headphones", "tablet", "monitor",
    "router", "modem", "cable", "warranty"
}

KNOWN_LOCATIONS = {
    "new york", "california", "san francisco", "london", "mumbai", "delhi",
    "bengaluru", "bangalore", "chicago", "toronto", "texas", "seattle", "boston",
    "berlin", "paris", "tokyo", "singapore", "sydney", "dubai", "los angeles"
}

_spacy_nlp = None

def get_spacy():
    global _spacy_nlp
    if _spacy_nlp is None:
        try:
            import spacy
            _spacy_nlp = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy model for NER.")
        except Exception:
            _spacy_nlp = False
    return _spacy_nlp if _spacy_nlp is not False else None

class BaseNERExtractor(ABC):
    """Abstract Base Class for Named Entity Recognition."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass

    @abstractmethod
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extracts structured entities matching the 10 target entity types."""
        pass

class HybridNERExtractor(BaseNERExtractor):
    """High-precision hybrid NER extractor combining pattern recognition and transformer / spaCy models.

    Extracts:
    - PERSON
    - EMAIL
    - PHONE
    - ORDER_ID
    - TRANSACTION_ID
    - AMOUNT
    - DATE
    - PRODUCT
    - COMPANY
    - LOCATION
    """

    def __init__(self, transformer_model: str = "dslim/bert-base-NER"):
        self._transformer_model = transformer_model
        self._pipeline = None
        self._attempted_pipeline = False

    @property
    def model_name(self) -> str:
        return f"HybridNER ({self._transformer_model})"

    def _get_pipeline(self):
        if not self._attempted_pipeline:
            self._attempted_pipeline = True
            try:
                from transformers import pipeline
                self._pipeline = pipeline("ner", model=self._transformer_model, grouped_entities=True)
                logger.info(f"Loaded Hugging Face NER pipeline: {self._transformer_model}")
            except Exception as e:
                logger.info(f"Hugging Face NER model {self._transformer_model} not available ({e}). Using pattern & spaCy extraction.")
                self._pipeline = None
        return self._pipeline

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        if not text or not text.strip():
            return []

        entities: List[Dict[str, Any]] = []

        # -------------------------------------------------------------
        # 1. AMOUNT: Currency symbols (₹, $, €, £, INR, USD, EUR, Rs.)
        # -------------------------------------------------------------
        amount_patterns = [
            r'(?:[\$€£₹]|INR|USD|EUR|Rs\.?)\s*[0-9]+(?:,[0-9]{3})*(?:\.[0-9]{2})?',
            r'\b[0-9]+(?:,[0-9]{3})*(?:\.[0-9]{2})?\s*(?:INR|USD|EUR|rupees|dollars|bucks|pounds|euros)\b'
        ]
        for pattern in amount_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append({
                    "entity_type": "AMOUNT",
                    "entity_value": match.group(0).strip(),
                    "start_char": match.start(),
                    "end_char": match.end(),
                    "confidence": 0.98
                })

        # -------------------------------------------------------------
        # 2. ORDER_ID: Specific order identifiers (e.g. ORD92831, ORD-1092, #94829, order #48291)
        # -------------------------------------------------------------
        order_patterns = [
            r'\b(?:order\s+(?:number\s+|id\s+|#)?)?(ORD[-_]?[0-9A-Z]{4,14})\b',
            r'\b(?:order\s+(?:id\s+|number\s+|#)?)\s*#?([0-9]{5,12})\b',
            r'#ORD[-_]?[0-9A-Z]{4,14}\b'
        ]
        for pattern in order_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                val = match.group(1) if match.groups() and match.group(1) else match.group(0)
                entities.append({
                    "entity_type": "ORDER_ID",
                    "entity_value": val.strip('# '),
                    "start_char": match.start(),
                    "end_char": match.end(),
                    "confidence": 0.95
                })

        # -------------------------------------------------------------
        # 3. TRANSACTION_ID: TXN, REF, TRX, INV, BILL, PAY codes
        # -------------------------------------------------------------
        txn_patterns = [
            r'\b(?:TXN|REF|TRX|INV|BILL|PAY|RCPT)[-_]?[A-Z0-9]{4,16}\b',
            r'\b(?:transaction\s+(?:id\s+|#)?)\s*#?([A-Z0-9_-]{6,20})\b',
            r'\b(?:invoice\s+(?:id\s+|number\s+|#)?)\s*#?([A-Z0-9_-]{5,20})\b'
        ]
        for pattern in txn_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                val = match.group(1) if match.groups() and match.group(1) else match.group(0)
                entities.append({
                    "entity_type": "TRANSACTION_ID",
                    "entity_value": val.strip('# '),
                    "start_char": match.start(),
                    "end_char": match.end(),
                    "confidence": 0.95
                })

        # -------------------------------------------------------------
        # 4. EMAIL: Standard RFC compliant email regex
        # -------------------------------------------------------------
        for match in re.finditer(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text):
            entities.append({
                "entity_type": "EMAIL",
                "entity_value": match.group(0),
                "start_char": match.start(),
                "end_char": match.end(),
                "confidence": 0.99
            })

        # -------------------------------------------------------------
        # 5. PHONE: North American & International phone numbers
        # -------------------------------------------------------------
        phone_patterns = [
            r'(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
            r'(?:\+\d{1,3}[-.\s]?)?\d{3}[-.\s]?\d{4}\b',
            r'(?:\+91[-.\s]?)?[6-9]\d{9}\b'
        ]
        for pattern in phone_patterns:
            for match in re.finditer(pattern, text):
                val = match.group(0).strip()
                # Skip if it's just pure numbers matching an amount or order
                digits = re.sub(r'\D', '', val)
                if 7 <= len(digits) <= 15:
                    entities.append({
                        "entity_type": "PHONE",
                        "entity_value": val,
                        "start_char": match.start(),
                        "end_char": match.end(),
                        "confidence": 0.90
                    })

        # -------------------------------------------------------------
        # 6. DATE: ISO, American/European formats, named months
        # -------------------------------------------------------------
        date_patterns = [
            r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+\d{4})?\b',
            r'\b\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)(?:,?\s+\d{4})?\b',
            r'\b\d{4}-\d{2}-\d{2}\b',
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b(?:yesterday|today|tomorrow|last week|last month)\b'
        ]
        for pattern in date_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append({
                    "entity_type": "DATE",
                    "entity_value": match.group(0),
                    "start_char": match.start(),
                    "end_char": match.end(),
                    "confidence": 0.90
                })

        # -------------------------------------------------------------
        # 7. COMPANY: High-frequency known enterprise organizations
        # -------------------------------------------------------------
        for company in KNOWN_COMPANIES:
            pattern = r'\b' + re.escape(company) + r'\b'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append({
                    "entity_type": "COMPANY",
                    "entity_value": match.group(0).title(),
                    "start_char": match.start(),
                    "end_char": match.end(),
                    "confidence": 0.92
                })

        # -------------------------------------------------------------
        # 8. PRODUCT: Consumer, hardware, and SaaS subscriptions
        # -------------------------------------------------------------
        for product in KNOWN_PRODUCTS:
            pattern = r'\b' + re.escape(product) + r'\b'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append({
                    "entity_type": "PRODUCT",
                    "entity_value": match.group(0).title(),
                    "start_char": match.start(),
                    "end_char": match.end(),
                    "confidence": 0.88
                })

        # -------------------------------------------------------------
        # 9. LOCATION: Major cities, states, and geographic locations
        # -------------------------------------------------------------
        for loc in KNOWN_LOCATIONS:
            pattern = r'\b' + re.escape(loc) + r'\b'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append({
                    "entity_type": "LOCATION",
                    "entity_value": match.group(0).title(),
                    "start_char": match.start(),
                    "end_char": match.end(),
                    "confidence": 0.90
                })

        # -------------------------------------------------------------
        # 10. PERSON: Self-identifications or signatures
        # -------------------------------------------------------------
        person_patterns = [
            r'(?i)\b(?:my name is|customer name is|i am)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b',
            r'(?i)\b(?:regards|sincerely|thanks),?\s*\n+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b'
        ]
        for pattern in person_patterns:
            for match in re.finditer(pattern, text):
                if match.groups() and match.group(1):
                    val = match.group(1).strip()
                    entities.append({
                        "entity_type": "PERSON",
                        "entity_value": val,
                        "start_char": match.start(1),
                        "end_char": match.end(1),
                        "confidence": 0.90
                    })

        # -------------------------------------------------------------
        # SpaCy Linguistic Enhancement (PERSON, ORG -> COMPANY, GPE -> LOCATION, DATE)
        # -------------------------------------------------------------
        nlp = get_spacy()
        if nlp:
            try:
                doc = nlp(text[:2000])
                for ent in doc.ents:
                    etype = None
                    if ent.label_ == "PERSON":
                        etype = "PERSON"
                    elif ent.label_ in ("ORG", "NORP"):
                        etype = "COMPANY"
                    elif ent.label_ in ("GPE", "LOC"):
                        etype = "LOCATION"
                    elif ent.label_ in ("DATE", "TIME"):
                        etype = "DATE"

                    if etype:
                        entities.append({
                            "entity_type": etype,
                            "entity_value": ent.text.strip(),
                            "start_char": ent.start_char,
                            "end_char": ent.end_char,
                            "confidence": 0.88
                        })
            except Exception:
                pass

        # -------------------------------------------------------------
        # Hugging Face Transformer NER Pipeline Enhancement
        # -------------------------------------------------------------
        pipe = self._get_pipeline()
        if pipe:
            try:
                hf_results = pipe(text[:1000])
                mapping = {"PER": "PERSON", "ORG": "COMPANY", "LOC": "LOCATION", "MISC": "PRODUCT"}
                for ent in hf_results:
                    etype = mapping.get(ent.get("entity_group", ent.get("entity")))
                    if etype:
                        entities.append({
                            "entity_type": etype,
                            "entity_value": ent["word"].strip(),
                            "start_char": ent.get("start"),
                            "end_char": ent.get("end"),
                            "confidence": round(float(ent.get("score", 0.90)), 2)
                        })
            except Exception:
                pass

        # -------------------------------------------------------------
        # Deduplication & Filtering
        # -------------------------------------------------------------
        unique_entities: List[Dict[str, Any]] = []
        seen = set()

        for e in entities:
            clean_val = e["entity_value"].strip()
            if not clean_val or len(clean_val) < 2:
                continue
            key = (e["entity_type"], clean_val.lower())
            if key not in seen:
                seen.add(key)
                unique_entities.append(e)

        return unique_entities

class EntityExtractor(HybridNERExtractor):
    """Singleton facade keeping backwards compatibility."""
    pass

ner_extractor = EntityExtractor()
