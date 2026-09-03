import re
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# The 6 core customer emotions
TARGET_EMOTIONS = [
    "ANGER",
    "FRUSTRATION",
    "FEAR",
    "SADNESS",
    "NEUTRAL",
    "SATISFACTION"
]

# Lexical mapping for fallback and zero-shot candidate evaluation
EMOTION_LEXICON = {
    "ANGER": [
        "angry", "furious", "outrageous", "pathetic", "ridiculous", "unacceptable",
        "lawsuit", "sue", "terrible", "worst", "hate", "scam", "fraud", "stealing",
        "fuming", "disgusted", "appalling"
    ],
    "FRUSTRATION": [
        "frustrated", "annoying", "tired of", "again", "still not", "twice", "repeatedly",
        "waste of time", "useless", "waiting forever", "charged twice", "double charged",
        "unresponsive", "broken", "runaround", "stuck", "fed up"
    ],
    "FEAR": [
        "scared", "afraid", "worried", "panicking", "panic", "security breach", "hacked",
        "compromised", "identity theft", "unauthorized", "stolen credentials", "loss of money",
        "threat", "emergency", "danger", "vulnerable"
    ],
    "SADNESS": [
        "sad", "disappointed", "let down", "unhappy", "regret", "depressed", "heartbreaking",
        "crying", "miserable", "poor quality", "disheartened", "shame"
    ],
    "SATISFACTION": [
        "satisfied", "happy", "pleased", "great", "thank you", "resolved", "helpful",
        "excellent", "grateful", "delighted", "wonderful", "impressed", "kind", "fast resolution",
        "appreciated", "awesome", "fantastic"
    ],
    "NEUTRAL": [
        "inquiry", "status update", "question", "attachment", "account number", "statement",
        "details", "information", "regarding", "follow up"
    ]
}

# Mapping GoEmotions / Ekman labels to the 6 target emotions
HF_EMOTION_MAPPING = {
    "anger": "ANGER",
    "annoyance": "FRUSTRATION",
    "disapproval": "FRUSTRATION",
    "fear": "FEAR",
    "nervousness": "FEAR",
    "sadness": "SADNESS",
    "grief": "SADNESS",
    "disappointment": "SADNESS",
    "remorse": "SADNESS",
    "joy": "SATISFACTION",
    "gratitude": "SATISFACTION",
    "approval": "SATISFACTION",
    "relief": "SATISFACTION",
    "pride": "SATISFACTION",
    "optimism": "SATISFACTION",
    "love": "SATISFACTION",
    "neutral": "NEUTRAL"
}

class BaseEmotionDetector(ABC):
    """Abstract Base Class for Emotion Detectors."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Configured model name or checkpoint."""
        pass

    @abstractmethod
    def detect(self, text: str) -> Dict[str, Any]:
        """Detects customer emotion and returns primary emotion and confidence."""
        pass

class TransformerEmotionDetector(BaseEmotionDetector):
    """Configurable Hugging Face Transformers Emotion Detector.

    Supports configurable models such as:
    - 'j-hartmann/emotion-english-distilroberta-base'
    - 'SamLowe/roberta-base-go_emotions'
    - 'facebook/bart-large-mnli' (Zero-Shot for target emotions)
    """

    def __init__(self, model_name: str = "j-hartmann/emotion-english-distilroberta-base", device: int = -1):
        self._model_name = model_name
        self._device = device
        self._pipeline = None
        self._attempted_load = False

    @property
    def model_name(self) -> str:
        return self._model_name

    def set_model(self, model_name: str):
        """Allows dynamically reconfiguring the emotion model."""
        if model_name != self._model_name:
            self._model_name = model_name
            self._pipeline = None
            self._attempted_load = False

    def _get_pipeline(self):
        if not self._attempted_load:
            self._attempted_load = True
            try:
                from transformers import pipeline
                # Check if it's zero-shot or sequence-classification
                if "bart" in self._model_name.lower() or "mnli" in self._model_name.lower():
                    self._pipeline = pipeline("zero-shot-classification", model=self._model_name, device=self._device)
                else:
                    self._pipeline = pipeline("text-classification", model=self._model_name, device=self._device, return_all_scores=True)
                logger.info(f"Loaded Transformer emotion model: {self._model_name}")
            except Exception as e:
                logger.info(f"Transformer model {self._model_name} not available ({e}). Using calibrated emotion fallback.")
                self._pipeline = None
        return self._pipeline

    def detect(self, text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return {
                "emotion": "NEUTRAL",
                "confidence": 0.50,
                "emotion_score": 0.50,
                "emotion_scores": {e: (1.0 if e == "NEUTRAL" else 0.0) for e in TARGET_EMOTIONS},
                "model": self._model_name
            }

        cleaned = text.strip()
        pipe = self._get_pipeline()

        if pipe is not None:
            try:
                truncated = cleaned[:1000]
                if "bart" in self._model_name.lower() or "mnli" in self._model_name.lower():
                    # Zero-shot pipeline
                    res = pipe(truncated, candidate_labels=TARGET_EMOTIONS, hypothesis_template="The customer feels {}.")
                    best_emotion = res["labels"][0]
                    confidence = round(float(res["scores"][0]), 2)
                    scores = {label: round(float(score), 2) for label, score in zip(res["labels"], res["scores"])}
                else:
                    # Multi-class transformer pipeline
                    raw_scores = pipe(truncated)[0]
                    scores = {e: 0.05 for e in TARGET_EMOTIONS}
                    for item in raw_scores:
                        mapped = HF_EMOTION_MAPPING.get(item["label"].lower(), item["label"].upper())
                        if mapped in scores:
                            scores[mapped] = max(scores[mapped], round(float(item["score"]), 2))

                    best_emotion = max(scores, key=scores.get)
                    confidence = scores[best_emotion]

                return {
                    "emotion": best_emotion,
                    "confidence": confidence,
                    "emotion_score": confidence,
                    "emotion_scores": scores,
                    "model": self._model_name
                }
            except Exception as e:
                logger.warning(f"Error in transformer emotion detection ({e}). Falling back to calibrated engine.")

        return self._calibrated_detect(cleaned)

    def _calibrated_detect(self, text: str) -> Dict[str, Any]:
        """Calibrated fallback detector mapping text to the 6 target emotions."""
        cleaned = text.lower()
        counts: Dict[str, int] = {e: 0 for e in TARGET_EMOTIONS}

        for emotion, keywords in EMOTION_LEXICON.items():
            for kw in keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', cleaned):
                    counts[emotion] += 2 if " " in kw else 1

        primary = max(counts, key=counts.get)
        max_count = counts[primary]

        total = sum(counts.values())
        if max_count == 0:
            primary = "NEUTRAL"
            confidence = 0.60
            normalized_scores = {e: (0.60 if e == "NEUTRAL" else 0.08) for e in TARGET_EMOTIONS}
        else:
            confidence = round(min(0.96, 0.70 + (max_count / max(total, 1)) * 0.25), 2)
            normalized_scores = {
                e: round(min(0.96, (counts[e] / max(total, 1)) * confidence + 0.05), 2)
                for e in TARGET_EMOTIONS
            }
            normalized_scores[primary] = confidence

        return {
            "emotion": primary,
            "confidence": confidence,
            "emotion_score": confidence,
            "emotion_scores": normalized_scores,
            "model": f"{self._model_name} (calibrated-baseline)"
        }

class EmotionDetector(TransformerEmotionDetector):
    """Facade singleton keeping backward compatibility."""
    pass

def get_emotion_detector(model_name: Optional[str] = None) -> BaseEmotionDetector:
    """Factory creating an emotion detector instance with configurable model."""
    if model_name:
        return TransformerEmotionDetector(model_name=model_name)
    return TransformerEmotionDetector()

# Primary singleton export
emotion_detector = EmotionDetector()
