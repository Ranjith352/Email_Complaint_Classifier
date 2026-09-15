import re
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Regular Expression Patterns for PII and Sensitive Identifiers
EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
PHONE_REGEX = re.compile(r'(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,5}[-.\s]?\d{3,5}\b')
# Credit / Debit Cards (13-19 digits with optional spaces or dashes)
CARD_REGEX = re.compile(r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11}|(?:\d{4}[-\s]?){3}\d{4})\b')
# UPI ID pattern (e.g. user@okhdfcbank, name@upi)
UPI_REGEX = re.compile(r'\b[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}\b')
# Bank Account Numbers & CVVs
CVV_REGEX = re.compile(r'\b(?:cvv|cvc|security code)[:\s]+(\d{3,4})\b', re.IGNORECASE)
ACCOUNT_NUM_REGEX = re.compile(r'\b(?:account|acct|acc)(?:\s+no|\s+number)?[:\s]+(\d{8,18})\b', re.IGNORECASE)
# Sensitive IDs: SSN (###-##-####), Aadhaar (#### #### ####), API Tokens
SSN_REGEX = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
AADHAAR_REGEX = re.compile(r'\b\d{4}[-\s]\d{4}[-\s]\d{4}\b')
TOKEN_REGEX = re.compile(r'\b(?:bearer\s+[a-zA-Z0-9_\-\.]{20,}|(?:ghp|gho|eyJh)[a-zA-Z0-9_\-\.]{15,})\b', re.IGNORECASE)

def is_luhn_valid(card_number_str: str) -> bool:
    """Validates credit card checksum via the Luhn algorithm."""
    digits = [int(d) for d in re.sub(r'\D', '', card_number_str)]
    if len(digits) < 10 or len(digits) > 19:
        return False
    checksum = 0
    reverse_digits = digits[::-1]
    for i, d in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = d * 2
            checksum += doubled - 9 if doubled > 9 else doubled
        else:
            checksum += d
    return checksum % 10 == 0

class PrivacyService:
    """Enterprise Privacy, PII Detection, and Sensitive Data Protection Engine."""

    @staticmethod
    def detect_pii(text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detects Emails, Phone Numbers, Payment Information, and Sensitive Identifiers.
        Returns structured locations and categories.
        """
        if not text:
            return {
                "emails": [],
                "phones": [],
                "payment_info": [],
                "sensitive_identifiers": []
            }

        detected = {
            "emails": [],
            "phones": [],
            "payment_info": [],
            "sensitive_identifiers": []
        }

        # 1. Emails
        for m in EMAIL_REGEX.finditer(text):
            detected["emails"].append({
                "value": m.group(0),
                "start": m.start(),
                "end": m.end()
            })

        # 2. Payment Cards & Accounts
        for m in CARD_REGEX.finditer(text):
            raw_card = m.group(0)
            if is_luhn_valid(raw_card) or len(re.sub(r'\D', '', raw_card)) == 16:
                detected["payment_info"].append({
                    "type": "CARD_NUMBER",
                    "value": raw_card,
                    "start": m.start(),
                    "end": m.end()
                })

        for m in CVV_REGEX.finditer(text):
            detected["payment_info"].append({
                "type": "CVV",
                "value": m.group(1),
                "start": m.start(1),
                "end": m.end(1)
            })

        for m in ACCOUNT_NUM_REGEX.finditer(text):
            detected["payment_info"].append({
                "type": "BANK_ACCOUNT",
                "value": m.group(1),
                "start": m.start(1),
                "end": m.end(1)
            })

        # 3. Phones (filter out strings that are cards or account numbers)
        for m in PHONE_REGEX.finditer(text):
            val = m.group(0).strip()
            digits = re.sub(r'\D', '', val)
            if 7 <= len(digits) <= 15:
                # Exclude if it's already captured as a card
                is_card = any(p["start"] <= m.start() and m.end() <= p["end"] for p in detected["payment_info"])
                if not is_card:
                    detected["phones"].append({
                        "value": val,
                        "start": m.start(),
                        "end": m.end()
                    })

        # 4. Sensitive Identifiers (SSN, Aadhaar, Tokens)
        for m in SSN_REGEX.finditer(text):
            detected["sensitive_identifiers"].append({
                "type": "SSN",
                "value": m.group(0),
                "start": m.start(),
                "end": m.end()
            })

        for m in AADHAAR_REGEX.finditer(text):
            detected["sensitive_identifiers"].append({
                "type": "NATIONAL_ID",
                "value": m.group(0),
                "start": m.start(),
                "end": m.end()
            })

        for m in TOKEN_REGEX.finditer(text):
            detected["sensitive_identifiers"].append({
                "type": "SECRET_TOKEN",
                "value": m.group(0),
                "start": m.start(),
                "end": m.end()
            })

        return detected

    @classmethod
    def mask_pii_for_external_llm(cls, text: str) -> Tuple[str, bool]:
        """
        Redacts PII before sending to external cloud LLMs (Groq, OpenAI, etc.).
        Returns (sanitized_text, contains_sensitive_data).
        """
        if not text:
            return text, False

        has_sensitive = False
        redacted = text

        # Redact payment cards
        for m in CARD_REGEX.finditer(text):
            card_val = m.group(0)
            if is_luhn_valid(card_val) or len(re.sub(r'\D', '', card_val)) == 16:
                redacted = redacted.replace(card_val, "[PAYMENT_CARD_REDACTED]")
                has_sensitive = True

        # Redact CVVs and Account numbers
        redacted = CVV_REGEX.sub(r"cvv: [CVV_REDACTED]", redacted)
        redacted = ACCOUNT_NUM_REGEX.sub(r"account: [BANK_ACCOUNT_REDACTED]", redacted)

        # Redact Sensitive Identifiers
        redacted = SSN_REGEX.sub("[SSN_REDACTED]", redacted)
        redacted = AADHAAR_REGEX.sub("[NATIONAL_ID_REDACTED]", redacted)
        redacted = TOKEN_REGEX.sub("[AUTH_TOKEN_REDACTED]", redacted)

        # Redact Emails & Phones
        redacted = EMAIL_REGEX.sub("[EMAIL_REDACTED]", redacted)
        for m in PHONE_REGEX.finditer(text):
            val = m.group(0).strip()
            digits = re.sub(r'\D', '', val)
            if 7 <= len(digits) <= 15:
                redacted = redacted.replace(val, "[PHONE_REDACTED]")

        if redacted != text:
            has_sensitive = True

        return redacted, has_sensitive

    @classmethod
    def sanitize_log(cls, message: str) -> str:
        """
        Ensures log messages NEVER expose PII in stdout, stderr, or log files.
        """
        if not message or not isinstance(message, str):
            return message

        sanitized, _ = cls.mask_pii_for_external_llm(message)
        return sanitized

    @staticmethod
    def mask_customer_display(email: Optional[str] = None, phone: Optional[str] = None, name: Optional[str] = None) -> Dict[str, str]:
        """
        Masks unnecessary customer information for support views.
        Example: 'ranjith@example.com' -> 'r***@example.com'
        """
        masked = {
            "masked_email": "Unknown",
            "masked_phone": "N/A",
            "masked_name": name or "Customer"
        }

        if email and "@" in email:
            user, domain = email.split("@", 1)
            masked_user = (user[0] + "***") if len(user) > 1 else "***"
            masked["masked_email"] = f"{masked_user}@{domain}"

        if phone:
            digits = re.sub(r'\D', '', phone)
            if len(digits) >= 4:
                masked["masked_phone"] = f"***-***-{digits[-4:]}"
            else:
                masked["masked_phone"] = "***-****"

        return masked

privacy_service = PrivacyService()
