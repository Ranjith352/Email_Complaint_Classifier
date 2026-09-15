import re
import html
from typing import Optional, List

# Common English contractions dictionary
CONTRACTIONS = {
    "can't": "cannot",
    "won't": "will not",
    "n't": " not",
    "'re": " are",
    "'s": " is",
    "'d": " would",
    "'ll": " will",
    "'t": " not",
    "'ve": " have",
    "'m": " am"
}

class ComplaintCleaner:
    """Production-grade text cleaning and normalization for customer complaint tickets."""

    def __init__(self, preserve_entities: bool = True):
        self.preserve_entities = preserve_entities

    def clean(self, text: Optional[str]) -> str:
        if not text or not isinstance(text, str):
            return ""

        # 1. Unescape HTML entities (&amp;, &lt;, &gt;, etc.)
        cleaned = html.unescape(text)

        # 2. Strip HTML tags
        cleaned = re.sub(r"<[^>]+>", " ", cleaned)

        # 3. Strip email headers and signatures (e.g., 'From:', 'Sent:', 'Regards,')
        cleaned = re.sub(r"(?i)\b(from|to|sent|subject|date):\s*.*", " ", cleaned)
        cleaned = re.sub(r"(?i)\b(best regards|warm regards|thanks and regards|sincerely|cheers),?.*", " ", cleaned)

        # 4. Expand contractions
        for contraction, expansion in CONTRACTIONS.items():
            cleaned = re.sub(re.escape(contraction), expansion, cleaned, flags=re.IGNORECASE)

        # 5. Entity handling (mask or normalize identifiers for clean text representation)
        if self.preserve_entities:
            # Preserve transaction IDs e.g. TXN123456 -> normalized token
            cleaned = re.sub(r"\bTXN\d+\b", "TRANSACTION_ID", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\bORD[-_]?\d+\b", "ORDER_ID", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"[\$€£₹]\s*\d+(?:[.,]\d+)?", "CURRENCY_AMOUNT", cleaned)
            cleaned = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "EMAIL_ADDR", cleaned)
            cleaned = re.sub(r"\b(?:\+?\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}\b", "PHONE_NUM", cleaned)

        # 6. Remove excess non-alphanumeric noise while retaining punctuation useful for sentiment
        cleaned = re.sub(r"[^\w\s.,!?-]", " ", cleaned)

        # 7. Normalize multiple whitespaces and newlines
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        return cleaned.lower()

    def clean_batch(self, texts: List[str]) -> List[str]:
        return [self.clean(t) for t in texts]

cleaner = ComplaintCleaner()

if __name__ == "__main__":
    sample = "Hello, <p>I can't access my account! Charged $150.00 twice for TXN99124.</p> Best regards,<br>John."
    cleaned_sample = cleaner.clean(sample)
    print("Original:\n", sample)
    print("\nCleaned:\n", cleaned_sample)
