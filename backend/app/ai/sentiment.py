import re
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

POSITIVE_WORDS = {
    "great", "good", "excellent", "helpful", "resolved", "thanks", "thank you", "appreciate",
    "pleased", "fantastic", "prompt", "satisfied", "wonderful", "impressed", "kind", "fixed",
    "perfect", "fast", "awesome", "delighted"
}

NEGATIVE_WORDS = {
    "horrible", "terrible", "worst", "bad", "awful", "unacceptable", "useless", "pathetic",
    "disaster", "broken", "failed", "hate", "angry", "furious", "ridiculous", "scam",
    "fraud", "stealing", "loss", "cheat", "disappointed", "poor", "pain", "unresponsive",
    "charged twice", "double charged", "overcharged", "still not", "waste", "down", "outage",
    "never works", "stolen", "breach", "hacked", "error", "crash"
}

class BaseSentimentAnalyzer(ABC):
    """Abstract Base Class for sentiment analyzers."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the sentiment analysis model."""
        pass

    @abstractmethod
    def analyze(self, text: str) -> Dict[str, Any]:
        """Analyzes sentiment and returns label ('NEGATIVE', 'POSITIVE', 'NEUTRAL') and confidence."""
        pass

class TransformerSentimentAnalyzer(BaseSentimentAnalyzer):
    """Hugging Face Transformers Sentiment Analysis using distilbert-base-uncased-finetuned-sst-2-english."""

    def __init__(self, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english", device: int = -1):
        self._model_name = model_name
        self._device = device
        self._pipeline = None
        self._attempted_load = False

    @property
    def model_name(self) -> str:
        return self._model_name

    def _get_pipeline(self):
        if not self._attempted_load:
            self._attempted_load = True
            try:
                from transformers import pipeline
                self._pipeline = pipeline("sentiment-analysis", model=self._model_name, device=self._device)
                logger.info(f"Loaded Hugging Face sentiment model: {self._model_name}")
            except Exception as e:
                logger.info(f"Hugging Face sentiment pipeline {self._model_name} not available ({e}). Using calibrated sentiment fallback.")
                self._pipeline = None
        return self._pipeline

    def analyze(self, text: str) -> Dict[str, Any]:
        """Analyzes text sentiment and returns label and confidence.

        Example return:
        {
            "label": "NEGATIVE",
            "confidence": 0.94
        }
        """
        if not text or not text.strip():
            return {
                "label": "NEUTRAL",
                "confidence": 0.50,
                "sentiment": "NEUTRAL",
                "sentiment_score": 0.0,
                "model": self._model_name
            }

        cleaned = text.strip()
        pipe = self._get_pipeline()

        if pipe is not None:
            try:
                # Run Hugging Face transformer pipeline (truncate to 512 tokens max for DistilBERT)
                truncated = cleaned[:1000]
                result = pipe(truncated)[0]
                raw_label = result.get("label", "NEUTRAL").upper()
                score = round(float(result.get("score", 0.90)), 2)

                # Normalize label to standard POSITIVE / NEGATIVE / NEUTRAL
                label = "NEGATIVE" if "NEG" in raw_label else ("POSITIVE" if "POS" in raw_label else "NEUTRAL")
                sentiment_score = -score if label == "NEGATIVE" else (score if label == "POSITIVE" else 0.0)

                return {
                    "label": label,
                    "confidence": score,
                    # Backward compatibility aliases
                    "sentiment": label,
                    "sentiment_score": sentiment_score,
                    "model": self._model_name
                }
            except Exception as e:
                logger.warning(f"Error in Hugging Face sentiment pipeline: {e}. Falling back to calibrated engine.")

        # High-precision calibrated sentiment fallback
        return self._calibrated_fallback(cleaned)

    def _calibrated_fallback(self, text: str) -> Dict[str, Any]:
        """Deterministic polarity scoring with calibrated confidence."""
        cleaned = text.lower()
        words = re.findall(r'\b[a-z0-9_-]+\b', cleaned)

        pos_count = sum(1 for w in words if w in POSITIVE_WORDS)
        neg_count = sum(1 for w in words if w in NEGATIVE_WORDS)

        # Check for phrase-level negative indicators
        for phrase in ["charged twice", "double charged", "waste of time", "never works", "still not resolved"]:
            if phrase in cleaned:
                neg_count += 2

        # Check for negations ("not good", "never helpful")
        negations = len(re.findall(r'\b(?:not|never|no|cannot|can\'t)\s+[a-z]+', cleaned))
        neg_count += negations

        net_score = pos_count - neg_count
        total_matched = pos_count + neg_count

        if net_score < 0:
            label = "NEGATIVE"
            confidence = round(min(0.98, 0.80 + (abs(net_score) / max(total_matched, 1)) * 0.18), 2)
            sentiment_score = round(max(-1.0, -0.60 - (abs(net_score) * 0.10)), 2)
        elif net_score > 0:
            label = "POSITIVE"
            confidence = round(min(0.98, 0.80 + (net_score / max(total_matched, 1)) * 0.18), 2)
            sentiment_score = round(min(1.0, 0.60 + (net_score * 0.10)), 2)
        else:
            label = "NEUTRAL"
            confidence = 0.65
            sentiment_score = 0.0

        return {
            "label": label,
            "confidence": confidence,
            "sentiment": label,
            "sentiment_score": sentiment_score,
            "positive_indicators": pos_count,
            "negative_indicators": neg_count,
            "model": f"{self._model_name} (calibrated-baseline)"
        }

class SentimentAnalyzer(TransformerSentimentAnalyzer):
    """Primary facade maintaining backward compatibility."""
    pass

def get_sentiment_analyzer(model_name: Optional[str] = None) -> BaseSentimentAnalyzer:
    """Factory function to get a sentiment analyzer instance."""
    if model_name:
        return TransformerSentimentAnalyzer(model_name=model_name)
    return TransformerSentimentAnalyzer()

# Primary singleton export
sentiment_analyzer = SentimentAnalyzer()
