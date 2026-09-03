from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

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
