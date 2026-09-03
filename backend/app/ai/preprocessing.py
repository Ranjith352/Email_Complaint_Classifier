import re
import html
import unicodedata
from typing import Dict, Any, List, Optional

class TextPreprocessor:
    """Enterprise text preprocessor for customer complaints, emails, and tickets.

    Capabilities:
    1. HTML removal and entity unescaping
    2. Email signature stripping
    3. Quoted reply chains removal
    4. Excessive/unnecessary whitespace normalization
    5. URL normalization/sanitization
    6. Unicode & typography normalization
    7. Punctuation normalization (preserves currencies, codes, punctuation semantics)
    8. Duplicate text/sentence removal
    9. Language detection
    10. Safe handling of empty/whitespace-only input
    11. Retains both original_text and processed_text
    """

    # Common email quote indicators
    QUOTE_PATTERNS = [
        r'^-+\s*Original Message\s*-+',
        r'^-+\s*Forwarded message\s*-+',
        r'^From:\s*.*?\nSent:\s*.*?\nTo:\s*.*?\nSubject:',
        r'(?i)^\s*On\s+.+?(?:wrote|wrote:)\s*$',
        r'^_{10,}',
        r'^\*{10,}',
    ]

    # Common email signature sign-offs
    SIGNATURE_PATTERNS = [
        r'(?i)^\s*--\s*$',
        r'(?i)^\s*--\s*\n',
        r'(?i)^\s*(?:Best regards|Kind regards|Warm regards|Regards|Thanks & regards|Thanks|Sincerely|Yours truly|Yours faithfully|Cheerfully|Cheers),?\s*$',
        r'(?i)^\s*Sent from my (?:iPhone|iPad|Android|Galaxy|mobile device).*$',
        r'(?i)^\s*Get Outlook for (?:iOS|Android).*$',
        r'(?i)This message and any attachments are confidential.*$',
        r'(?i)Notice: This email contains privileged information.*$',
        r'(?i)Disclaimer: The information contained in this communication.*$'
    ]

    # Multilingual common stop words for high-confidence language detection
    LANGUAGE_KEYWORDS = {
        "en": {
            "name": "English",
            "words": {"the", "and", "is", "in", "to", "of", "that", "it", "with", "for", "as", "was", "on", "at", "by", "this", "my", "please", "issue", "refund", "not", "have", "you"}
        },
        "es": {
            "name": "Spanish",
            "words": {"el", "la", "de", "que", "y", "en", "un", "por", "con", "no", "una", "su", "para", "es", "al", "lo", "como", "mas", "cuenta", "pago", "servicio"}
        },
        "fr": {
            "name": "French",
            "words": {"le", "la", "de", "et", "en", "un", "une", "du", "des", "pour", "dans", "qui", "sur", "avec", "est", "ce", "que", "compte", "facture", "remboursement"}
        },
        "de": {
            "name": "German",
            "words": {"der", "die", "das", "und", "in", "den", "von", "zu", "mit", "sich", "des", "auf", "fuer", "ist", "nicht", "eine", "einen", "rechnung", "bitte"}
        }
    }

    @classmethod
    def strip_html(cls, text: str) -> str:
        """Removes HTML elements, script/style tags, comments, and unescapes entities."""
        if not text:
            return ""

        # Unescape HTML entities (&amp;, &lt;, &gt;, &quot;, &#39;, &nbsp;, etc.)
        unescaped = html.unescape(text)

        # Remove script and style blocks
        cleaned = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', unescaped, flags=re.DOTALL | re.IGNORECASE)

        # Remove HTML comments
        cleaned = re.sub(r'<!--.*?-->', ' ', cleaned, flags=re.DOTALL)

        # Convert line break / paragraph tags to explicit newlines
        cleaned = re.sub(r'<(?:br|br/|/p|/div|/tr|/li)[^>]*>', '\n', cleaned, flags=re.IGNORECASE)

        # Strip remaining HTML tags
        cleaned = re.sub(r'<[^>]+>', ' ', cleaned)

        return cleaned

    @classmethod
    def strip_quoted_replies(cls, text: str) -> str:
        """Strips quoted replies and email thread histories from previous communications."""
        lines = text.splitlines()
        kept_lines = []

        for line in lines:
            stripped = line.strip()

            # Ignore lines prefixed with standard quote marks ('>', '|')
            if re.match(r'^\s*[>|]', line):
                continue

            # Check if this line signals the start of a quoted reply thread
            is_quote_start = False
            for pattern in cls.QUOTE_PATTERNS:
                if re.search(pattern, stripped, flags=re.MULTILINE | re.IGNORECASE):
                    is_quote_start = True
                    break

            if is_quote_start:
                # Stop parsing further to omit historical reply chain
                break

            kept_lines.append(line)

        return "\n".join(kept_lines)

    @classmethod
    def strip_signatures(cls, text: str) -> str:
        """Removes common email signatures and automated disclaimer footers."""
        # Strip inline mobile signatures anywhere in text
        text = re.sub(r'(?i)\bSent from my (?:iPhone|iPad|Android|Galaxy|mobile device).*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'(?i)\bGet Outlook for (?:iOS|Android).*$', '', text, flags=re.MULTILINE)

        lines = text.splitlines()
        cleaned_lines = []

        for idx, line in enumerate(lines):
            stripped = line.strip()

            is_signature = False
            for pattern in cls.SIGNATURE_PATTERNS:
                if re.match(pattern, stripped):
                    is_signature = True
                    break

            if is_signature:
                # If a sign-off or delimiter is encountered in the latter half of the email, trim it
                if idx >= max(1, len(lines) // 3):
                    break

            cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    @classmethod
    def normalize_unicode_and_typography(cls, text: str) -> str:
        """Normalizes Unicode encoding, smart quotes, dashes, ligatures, and control characters."""
        if not text:
            return ""

        # NFKC normalization
        normalized = unicodedata.normalize('NFKC', text)

        # Typography conversions
        normalized = re.sub(r'[\u2018\u2019\u201A\u201B]', "'", normalized)
        normalized = re.sub(r'[\u201C\u201D\u201E\u201F]', '"', normalized)
        normalized = re.sub(r'[\u2013\u2014]', '-', normalized)
        normalized = re.sub(r'\u2026', '...', normalized)

        # Remove zero-width & non-breaking spaces
        normalized = re.sub(r'[\u200B-\u200D\uFEFF]', '', normalized)
        normalized = re.sub(r'[\u00A0\u2000-\u200A]', ' ', normalized)

        # Strip unprintable control chars (preserve standard \n, \t)
        normalized = "".join(ch for ch in normalized if unicodedata.category(ch)[0] != 'C' or ch in ('\n', '\t'))

        return normalized

    @classmethod
    def clean_urls(cls, text: str) -> str:
        """Replaces long tracking URLs with clean [URL] placeholder while preserving semantics."""
        # Replace full URLs starting with http:// or https://
        return re.sub(r'https?://\S+', '[URL]', text)

    @classmethod
    def normalize_punctuation(cls, text: str) -> str:
        """Compresses repetitive punctuation spam without destroying currency symbols, codes, or sentence boundaries."""
        # Compress multiple question marks & exclamation marks
        cleaned = re.sub(r'\?{2,}', '?', text)
        cleaned = re.sub(r'!{2,}', '!', cleaned)
        cleaned = re.sub(r'\.{4,}', '...', cleaned)

        # Normalize multiple dashes (unless part of a code like TXN-123)
        cleaned = re.sub(r'(?<![A-Za-z0-9])-{2,}(?![A-Za-z0-9])', ' - ', cleaned)

        return cleaned

    @classmethod
    def deduplicate_text(cls, text: str) -> str:
        """Removes consecutive duplicate sentences or identical repeated paragraphs."""
        paragraphs = text.split("\n\n")
        seen_paragraphs = []
        for p in paragraphs:
            p_strip = p.strip()
            if not p_strip:
                continue
            # Keep unique or non-consecutive paragraphs
            if not seen_paragraphs or seen_paragraphs[-1].lower() != p_strip.lower():
                seen_paragraphs.append(p_strip)

        deduped = "\n\n".join(seen_paragraphs)

        # Sentence-level duplicate removal within paragraphs
        sentences = re.split(r'(?<=[.!?])\s+', deduped)
        kept_sentences = []
        for s in sentences:
            s_clean = s.strip()
            if not s_clean:
                continue
            if not kept_sentences or kept_sentences[-1].lower() != s_clean.lower():
                kept_sentences.append(s_clean)

        return " ".join(kept_sentences)

    @classmethod
    def clean_whitespace(cls, text: str) -> str:
        """Normalizes horizontal spaces, tabs, and limits consecutive newlines."""
        if not text:
            return ""

        # Normalize spaces/tabs on each line
        lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in text.splitlines()]

        # Recombine and compress excessive blank lines (max 2 consecutive newlines)
        recombined = "\n".join(lines)
        cleaned = re.sub(r'\n{3,}', '\n\n', recombined)

        return cleaned.strip()

    @classmethod
    def detect_language(cls, text: str) -> Dict[str, Any]:
        """Detects language of the cleaned text with confidence scoring."""
        cleaned = text.lower()
        words = set(re.findall(r'\b[a-z]{2,}\b', cleaned))
        if not words:
            return {"language": "en", "language_name": "English", "confidence": 0.90}

        lang_scores: Dict[str, int] = {}
        for code, data in cls.LANGUAGE_KEYWORDS.items():
            matches = len(words.intersection(data["words"]))
            lang_scores[code] = matches

        best_code = max(lang_scores, key=lang_scores.get)
        best_score = lang_scores[best_code]

        if best_score == 0:
            return {"language": "en", "language_name": "English", "confidence": 0.70}

        conf = min(0.99, max(0.75, round(best_score / max(1, min(len(words), 6)), 2)))
        return {
            "language": best_code,
            "language_name": cls.LANGUAGE_KEYWORDS[best_code]["name"],
            "confidence": conf
        }

    @classmethod
    def preprocess(cls, text: Optional[str]) -> Dict[str, Any]:
        """Main entrypoint: executes full preprocessing pipeline.

        Returns structured object containing both original_text and processed_text.
        """
        original = text or ""
        if not original.strip():
            return {
                "original_text": original,
                "processed_text": "",
                "language": "en",
                "language_name": "English",
                "language_confidence": 0.50,
                "is_empty": True,
                "original_length": len(original),
                "processed_length": 0
            }

        # Pipeline stages
        step1 = cls.strip_html(original)
        step2 = cls.strip_quoted_replies(step1)
        step3 = cls.strip_signatures(step2)
        step4 = cls.normalize_unicode_and_typography(step3)
        step5 = cls.clean_urls(step4)
        step6 = cls.normalize_punctuation(step5)
        step7 = cls.deduplicate_text(step6)
        processed = cls.clean_whitespace(step7)

        # Fallback if text was entirely signatures/HTML
        if not processed:
            processed = cls.clean_whitespace(cls.strip_html(original))

        lang_info = cls.detect_language(processed)

        return {
            "original_text": original,
            "processed_text": processed,
            "language": lang_info["language"],
            "language_name": lang_info["language_name"],
            "language_confidence": lang_info["confidence"],
            "is_empty": len(processed) == 0,
            "original_length": len(original),
            "processed_length": len(processed)
        }

    # Backward compatibility helper
    @classmethod
    def clean(cls, text: str) -> str:
        """Returns only the cleaned text for simple callers."""
        return cls.preprocess(text)["processed_text"]

preprocessor = TextPreprocessor()
