import logging
import httpx
from typing import Optional, Dict, Any, List
from app.core.config import settings
from app.ai.llm_provider import LLMProvider

logger = logging.getLogger(__name__)

class GroqProvider(LLMProvider):
    """Optional Groq Cloud LLM Provider.
    Reads credentials strictly from environment variables (GROQ_API_KEY, GROQ_MODEL).
    Never hardcodes or commits secret keys.
    If Groq is unavailable (missing key, network failure, or API error),
    gracefully falls back to configured local Ollama without crashing.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        # Strictly read from settings/environment - never hardcoded
        self.api_key = (api_key if api_key is not None else settings.GROQ_API_KEY).strip()
        self.model = (model if model is not None else settings.GROQ_MODEL).strip()
        self.last_error: Optional[str] = None

    @property
    def provider_name(self) -> str:
        return f"groq ({self.model})"

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

    def _get_ollama_fallback(self) -> Optional[Any]:
        """Returns configured OllamaProvider if Ollama model is configured."""
        try:
            from app.ai.ollama_provider import OllamaProvider
            ollama = OllamaProvider()
            if ollama.model:
                return ollama
        except Exception as e:
            logger.debug(f"Could not load Ollama fallback provider: {e}")
        return None

    async def check_availability(self) -> Dict[str, Any]:
        """Checks Groq availability and verifies fallback to Ollama."""
        ollama = self._get_ollama_fallback()
        ollama_configured = ollama is not None and bool(ollama.model)

        if not self.api_key:
            err = "GROQ_API_KEY environment variable is not configured. Groq is an optional provider."
            self.last_error = err
            return {
                "available": False,
                "provider": self.provider_name,
                "model": self.model,
                "error": err,
                "fallback_to_ollama": ollama_configured,
                "ollama_model": ollama.model if ollama else None
            }

        return {
            "available": True,
            "provider": self.provider_name,
            "model": self.model,
            "error": None,
            "fallback_to_ollama": ollama_configured,
            "ollama_model": ollama.model if ollama else None
        }

    async def generate_chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        json_mode: bool = False
    ) -> Optional[str]:
        """Generates chat completion via Groq API, with automatic fallback to Ollama when unavailable."""
        # 1. Check if Groq API key is configured
        if not self.api_key:
            self.last_error = "Groq API key not provided (GROQ_API_KEY). Groq is unavailable."
            logger.info(f"{self.last_error} Attempting fallback to configured Ollama...")
            ollama = self._get_ollama_fallback()
            if ollama:
                logger.info(f"Falling back from Groq to configured Ollama ({ollama.model}).")
                return await ollama.generate_chat(system_prompt, user_prompt, temperature, max_tokens, json_mode)
            return None

        # 2. Attempt Groq Cloud API request
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    self.last_error = None
                    return data["choices"][0]["message"]["content"]
                else:
                    self.last_error = f"Groq API returned HTTP {res.status_code}: {res.text}"
                    logger.warning(f"{self.last_error}. Attempting fallback to configured Ollama...")
        except Exception as e:
            self.last_error = f"Groq API request failed ({type(e).__name__}: {e})"
            logger.warning(f"{self.last_error}. Attempting fallback to configured Ollama...")

        # 3. If Groq is unavailable or failed, fall back to Ollama when configured
        ollama = self._get_ollama_fallback()
        if ollama:
            logger.info(f"Falling back from Groq to configured Ollama ({ollama.model}).")
            return await ollama.generate_chat(system_prompt, user_prompt, temperature, max_tokens, json_mode)

        return None

    async def summarize(
        self,
        text: str,
        subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """Summarizes complaint using Groq, or falls back to Ollama when Groq is unavailable."""
        # Try generation via Groq or Ollama fallback
        result = await super().summarize(text, subject)

        # If generation fell back to deterministic because Groq failed, check if Ollama can summarize
        if result.get("status") == "fallback":
            ollama = self._get_ollama_fallback()
            if ollama:
                ollama_res = await ollama.summarize(text, subject)
                if ollama_res.get("status") == "generated":
                    ollama_res["provider"] = f"{self.provider_name} -> {ollama.provider_name}"
                    ollama_res["fallback_from"] = self.provider_name
                    return ollama_res

        return result
