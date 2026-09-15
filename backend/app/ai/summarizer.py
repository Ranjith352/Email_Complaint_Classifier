from typing import Dict, Any, List, Optional
from app.ai.llm_provider import get_llm_provider

class ComplaintSummarizer:
    @staticmethod
    async def summarize(
        subject: str,
        body: str,
        provider_preference: Optional[str] = None,
        model_preference: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generates an executive summary using the configured LLMProvider (Ollama / Groq).
        The rest of the application interacts strictly through the LLMProvider abstraction.
        """
        llm = get_llm_provider(provider_preference, model=model_preference)
        return await llm.summarize(text=body, subject=subject)

    @staticmethod
    async def summarize_text(text: str) -> str:
        """Helper to summarize arbitrary complaint text."""
        llm = get_llm_provider()
        res = await llm.summarize(text=text, subject="Complaint Summary")
        if isinstance(res, dict):
            return res.get("summary") or res.get("text") or str(res)
        return str(res)

summarizer = ComplaintSummarizer()

