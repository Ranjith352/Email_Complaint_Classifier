from app.ai.preprocessing import preprocessor, TextPreprocessor
from app.ai.embeddings import embeddings_engine
from app.ai.classifier import (
    classifier,
    BaseClassifier,
    TFIDFLogisticRegressionClassifier,
    BaselineClassifier,
    TFIDFNaiveBayesClassifier,
    DistilBERTClassifier,
    TransformerClassifier,
    AdvancedTransformerClassifier,
    ZeroShotClassifier,
    BARTZeroShotClassifier,
    ProgressiveClassifier,
    ModelGovernance,
    get_classifier
)
from app.ai.sentiment import (
    sentiment_analyzer,
    BaseSentimentAnalyzer,
    TransformerSentimentAnalyzer,
    get_sentiment_analyzer
)
from app.ai.emotion import (
    emotion_detector,
    BaseEmotionDetector,
    TransformerEmotionDetector,
    get_emotion_detector,
    TARGET_EMOTIONS
)
from app.ai.ner import (
    ner_extractor,
    BaseNERExtractor,
    HybridNERExtractor,
    EntityExtractor,
    TARGET_ENTITY_TYPES
)
from app.ai.urgency import (
    urgency_detector,
    BaseUrgencyDetector,
    RuleEnhancedUrgencyDetector,
    UrgencyDetector,
    get_urgency_detector,
    URGENCY_TIERS
)
from app.ai.priority import (
    priority_calculator,
    PriorityEngine,
    PriorityCalculator,
    get_priority_engine,
    DEFAULT_PRIORITY_WEIGHTS,
    PRIORITY_TIERS
)
from app.ai.duplicate_detector import duplicate_detector
from app.ai.summarizer import summarizer
from app.ai.rag import rag_engine
from app.ai.response_generator import response_generator
from app.ai.llm_provider import LLMProvider, get_llm_provider
from app.ai.ollama_provider import OllamaProvider
from app.ai.groq_provider import GroqProvider
from app.ai.ai_orchestrator import ai_orchestrator

__all__ = [
    "preprocessor",
    "TextPreprocessor",
    "embeddings_engine",
    "classifier",
    "BaseClassifier",
    "TFIDFLogisticRegressionClassifier",
    "BaselineClassifier",
    "TFIDFNaiveBayesClassifier",
    "DistilBERTClassifier",
    "TransformerClassifier",
    "AdvancedTransformerClassifier",
    "ZeroShotClassifier",
    "BARTZeroShotClassifier",
    "ProgressiveClassifier",
    "ModelGovernance",
    "get_classifier",
    "sentiment_analyzer",
    "BaseSentimentAnalyzer",
    "TransformerSentimentAnalyzer",
    "get_sentiment_analyzer",
    "emotion_detector",
    "BaseEmotionDetector",
    "TransformerEmotionDetector",
    "get_emotion_detector",
    "TARGET_EMOTIONS",
    "ner_extractor",
    "BaseNERExtractor",
    "HybridNERExtractor",
    "EntityExtractor",
    "TARGET_ENTITY_TYPES",
    "urgency_detector",
    "BaseUrgencyDetector",
    "RuleEnhancedUrgencyDetector",
    "UrgencyDetector",
    "get_urgency_detector",
    "URGENCY_TIERS",
    "priority_calculator",
    "PriorityEngine",
    "PriorityCalculator",
    "get_priority_engine",
    "DEFAULT_PRIORITY_WEIGHTS",
    "PRIORITY_TIERS",
    "duplicate_detector",
    "summarizer",
    "rag_engine",
    "response_generator",
    "LLMProvider",
    "get_llm_provider",
    "OllamaProvider",
    "GroqProvider",
    "ai_orchestrator"
]
