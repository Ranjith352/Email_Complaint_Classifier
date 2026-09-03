import logging
import httpx
from typing import Optional
from app.core.config import settings
from app.ai.llm_provider import LLMProvider

logger = logging.getLogger(__name__)

class OllamaProvider(LLMProvider):
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip('/')
        self.model = settings.OLLAMA_MODEL
        self._tested_connection = False
        self._is_online = False

    @property
    def provider_name(self) -> str:
        return f"ollama ({self.model})"

    @property
    def is_available(self) -> bool:
        return True

    async def generate_chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        json_mode: bool = False
    ) -> Optional[str]:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        if json_mode:
            payload["format"] = "json"

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    content = data.get("message", {}).get("content")
                    return content
                else:
                    logger.warning(f"Ollama returned HTTP status {res.status_code}: {res.text}")
        except Exception as e:
            logger.info(f"Ollama local instance not reachable at {self.base_url} ({e}). Gracefully falling back.")
        return None
