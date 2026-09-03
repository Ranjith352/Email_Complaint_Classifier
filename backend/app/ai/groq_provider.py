import logging
import httpx
from typing import Optional
from app.core.config import settings
from app.ai.llm_provider import LLMProvider

logger = logging.getLogger(__name__)

class GroqProvider(LLMProvider):
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL

    @property
    def provider_name(self) -> str:
        return f"groq ({self.model})"

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

    async def generate_chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        json_mode: bool = False
    ) -> Optional[str]:
        if not self.api_key:
            logger.info("Groq API key not provided; skipping Groq inference.")
            return None

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
                    content = data["choices"][0]["message"]["content"]
                    return content
                else:
                    logger.warning(f"Groq API returned HTTP {res.status_code}: {res.text}")
        except Exception as e:
            logger.warning(f"Groq API call failed ({e}).")
        return None
