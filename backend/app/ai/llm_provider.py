from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from app.core.config import settings

class LLMProvider(ABC):
    """Abstract Base Class for LLM Providers (Ollama, Groq, Fallback)."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider, e.g. 'ollama' or 'groq'."""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check whether the provider is currently reachable."""
        pass

    @abstractmethod
    async def generate_chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        json_mode: bool = False
    ) -> Optional[str]:
        """Generate a chat completion from the LLM."""
        pass

_ollama_instance = None
_groq_instance = None

def get_llm_provider() -> LLMProvider:
    """Returns configured LLM provider (Ollama by default, or Groq if selected)."""
    global _ollama_instance, _groq_instance
    from app.ai.ollama_provider import OllamaProvider
    from app.ai.groq_provider import GroqProvider

    provider_type = (settings.LLM_PROVIDER or "ollama").lower()

    if provider_type == "groq" and settings.GROQ_API_KEY:
        if _groq_instance is None:
            _groq_instance = GroqProvider()
        return _groq_instance

    if _ollama_instance is None:
        _ollama_instance = OllamaProvider()
    return _ollama_instance
