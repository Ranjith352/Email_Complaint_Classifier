import logging
import httpx
from typing import Optional, Dict, Any, List
from app.core.config import settings
from app.ai.llm_provider import LLMProvider

logger = logging.getLogger(__name__)

OLLAMA_DOWNLOAD_URL = "https://ollama.com/download"

class OllamaProvider(LLMProvider):
    """Local Ollama LLM Provider.
    Default local LLM running at http://localhost:11434.
    Does not assume a model is pre-installed.
    Allows user to configure the model, returns clear errors when unavailable,
    and prevents application crashes.
    """

    DOWNLOAD_URL = OLLAMA_DOWNLOAD_URL

    def __init__(self, model: Optional[str] = None, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip('/')
        # Do not assume a model is installed - user configurable
        self.model = (model if model is not None else settings.OLLAMA_MODEL).strip()
        self.last_error: Optional[str] = None

    def set_model(self, model_name: str) -> None:
        """Allows configuring or updating the Ollama model at runtime."""
        self.model = (model_name or "").strip()
        self.last_error = None
        logger.info(f"OllamaProvider active model set to: '{self.model}'")

    @property
    def provider_name(self) -> str:
        if self.model:
            return f"ollama ({self.model})"
        return "ollama (unconfigured model)"

    @property
    def is_available(self) -> bool:
        """Returns True if a model and base URL are configured."""
        return bool(self.model and self.base_url)

    async def get_installed_models(self) -> List[str]:
        """Queries local Ollama daemon for currently installed models.
        Returns list of model names or empty list if offline. Does not crash.
        """
        url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    models = data.get("models", [])
                    return [m.get("name", "") for m in models if m.get("name")]
        except Exception as e:
            logger.debug(f"Could not connect to Ollama daemon at {self.base_url}: {e}")
        return []

    async def check_availability(self) -> Dict[str, Any]:
        """Checks local Ollama server connectivity and model installation.
        Returns a clear error if unavailable, without crashing the application.
        """
        # 1. Check if model is configured
        if not self.model:
            err = (
                "No Ollama model is configured. Please configure a model by setting OLLAMA_MODEL "
                f"in .env (e.g. OLLAMA_MODEL=llama3) or configuring it via the LLM settings. "
                f"Download Ollama from {OLLAMA_DOWNLOAD_URL} and run 'ollama run llama3'."
            )
            self.last_error = err
            return {
                "available": False,
                "online": False,
                "model_configured": False,
                "configured_model": "",
                "installed_models": [],
                "error": err,
                "download_url": OLLAMA_DOWNLOAD_URL,
                "instructions": [
                    f"1. Download and install Ollama from {OLLAMA_DOWNLOAD_URL}",
                    "2. Start Ollama (runs locally on port 11434)",
                    "3. Run 'ollama run llama3' in your terminal",
                    "4. Set OLLAMA_MODEL=llama3 in your .env configuration"
                ]
            }

        # 2. Check if local Ollama daemon is reachable
        installed_models: List[str] = []
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    installed_models = [m.get("name", "") for m in res.json().get("models", []) if m.get("name")]
                else:
                    err = f"Ollama daemon returned HTTP status {res.status_code} at {self.base_url}"
                    self.last_error = err
                    return {
                        "available": False,
                        "online": False,
                        "model_configured": True,
                        "configured_model": self.model,
                        "installed_models": [],
                        "error": err,
                        "download_url": OLLAMA_DOWNLOAD_URL,
                        "instructions": [
                            f"Check if Ollama is running at {self.base_url}",
                            f"Download Ollama from {OLLAMA_DOWNLOAD_URL}"
                        ]
                    }
        except Exception as e:
            err = (
                f"Cannot connect to local Ollama service at {self.base_url} ({type(e).__name__}). "
                f"Please ensure Ollama is installed and running locally. "
                f"Download Ollama from: {OLLAMA_DOWNLOAD_URL}"
            )
            self.last_error = err
            return {
                "available": False,
                "online": False,
                "model_configured": True,
                "configured_model": self.model,
                "installed_models": [],
                "error": err,
                "download_url": OLLAMA_DOWNLOAD_URL,
                "instructions": [
                    f"1. Download and install Ollama: {OLLAMA_DOWNLOAD_URL}",
                    f"2. Launch Ollama (runs at {self.base_url})",
                    f"3. Run 'ollama pull {self.model}' in terminal"
                ]
            }

        # 3. Check if configured model is installed
        target = self.model.lower()
        matched = any(
            target == m.lower() or target == m.split(":")[0].lower() or m.lower().startswith(f"{target}:")
            for m in installed_models
        )

        if not matched:
            err = (
                f"Configured model '{self.model}' is not installed in local Ollama. "
                f"Installed models: {installed_models if installed_models else 'none'}. "
                f"Please run 'ollama pull {self.model}' or 'ollama run {self.model}' in your terminal. "
                f"Download Ollama from: {OLLAMA_DOWNLOAD_URL}"
            )
            self.last_error = err
            return {
                "available": False,
                "online": True,
                "model_configured": True,
                "configured_model": self.model,
                "installed_models": installed_models,
                "error": err,
                "download_url": OLLAMA_DOWNLOAD_URL,
                "instructions": [
                    f"Run 'ollama pull {self.model}' to install this model",
                    f"Available installed models: {installed_models or 'none'}"
                ]
            }

        self.last_error = None
        return {
            "available": True,
            "online": True,
            "model_configured": True,
            "configured_model": self.model,
            "installed_models": installed_models,
            "error": None,
            "download_url": OLLAMA_DOWNLOAD_URL,
            "instructions": [f"Model '{self.model}' is installed and ready for inference."]
        }

    async def generate_chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        json_mode: bool = False
    ) -> Optional[str]:
        """Generates chat completion without crashing if model or daemon is unavailable."""
        if not self.model:
            self.last_error = (
                "No Ollama model configured. Please set OLLAMA_MODEL in .env or configure a model. "
                f"Download Ollama from {OLLAMA_DOWNLOAD_URL}"
            )
            logger.warning(self.last_error)
            return None

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
                    self.last_error = None
                    return data.get("message", {}).get("content")
                elif res.status_code == 404:
                    self.last_error = (
                        f"Model '{self.model}' not found in local Ollama. "
                        f"Please install it using 'ollama pull {self.model}'. "
                        f"Download Ollama: {OLLAMA_DOWNLOAD_URL}"
                    )
                    logger.warning(self.last_error)
                else:
                    self.last_error = f"Ollama returned HTTP status {res.status_code}: {res.text}"
                    logger.warning(self.last_error)
        except Exception as e:
            self.last_error = (
                f"Local Ollama instance not reachable at {self.base_url} ({type(e).__name__}). "
                f"Download and start Ollama from {OLLAMA_DOWNLOAD_URL}. Continuing with fallback."
            )
            logger.info(self.last_error)

        return None
