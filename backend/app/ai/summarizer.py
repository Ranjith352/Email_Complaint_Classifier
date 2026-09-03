import json
from typing import Dict, Any, List
from app.ai.llm_provider import get_llm_provider

class ComplaintSummarizer:
    @staticmethod
    async def summarize(subject: str, body: str) -> Dict[str, Any]:
        """Generates an executive summary and key pain points using Ollama/Groq with fallback."""
        llm = get_llm_provider()
        
        system_prompt = (
            "You are an expert customer complaint triage analyst. Summarize the complaint concisely. "
            "Output valid JSON with exactly two keys: 'summary' (a clear 2-sentence executive summary), "
            "and 'key_points' (a list of 2 to 3 concise bullet points identifying the core issues)."
        )
        user_prompt = f"Subject: {subject}\nBody:\n{body}"

        response_text = await llm.generate_chat(system_prompt, user_prompt, json_mode=True)
        if response_text:
            try:
                data = json.loads(response_text)
                return {
                    "summary": data.get("summary", ""),
                    "key_points": data.get("key_points", []),
                    "provider": llm.provider_name
                }
            except Exception:
                pass

        # Deterministic Extractive Fallback
        safe_body = body or ""
        sentences = [s.strip() for s in safe_body.replace("\n", ". ").split(". ") if len(s.strip()) > 15]
        summary_text = (
            f"Customer submitted complaint regarding \"{subject}\". "
            + (sentences[0] + "." if sentences else "Awaiting specialist review.")
        )
        key_points = [
            f"Core issue reported: {subject}",
            f"Customer expressed urgent impact requiring departmental verification."
        ]
        return {
            "summary": summary_text,
            "key_points": key_points,
            "provider": "Extractive Heuristic Fallback"
        }

summarizer = ComplaintSummarizer()
