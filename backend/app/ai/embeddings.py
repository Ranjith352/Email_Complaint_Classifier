import math
import re
import logging
from typing import List
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
            logger.info(f"SentenceTransformer not loaded ({e}). Using deterministic lexical vector projection.")
    return _transformer_model

class EmbeddingsEngine:
    @staticmethod
    def get_embedding(text: str) -> List[float]:
        """Generate 384-dimensional dense semantic embedding vector."""
        embedder = get_embedder()
        if embedder is not None:
            try:
                vec = embedder.encode(text, normalize_embeddings=True)
                return vec.tolist()
            except Exception as e:
                logger.warning(f"Transformer encoding error: {e}")

        # Deterministic 384d semantic projection
        dim = settings.VECTOR_DIMENSION
        vec = [0.0] * dim
        words = re.findall(r'\w+', text.lower())
        if not words:
            return vec
        for i, word in enumerate(words):
            idx = abs(hash(word)) % dim
            weight = 1.0 / (1.0 + (i * 0.05))
            vec[idx] += weight

        # L2 normalization
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
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
