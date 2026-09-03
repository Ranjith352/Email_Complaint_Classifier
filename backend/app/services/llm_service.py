import json
import logging
import httpx
from typing import Dict, Any, List, Optional
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.groq_api_key = settings.GROQ_API_KEY
        self.groq_model = settings.GROQ_MODEL
        self.ollama_base_url = settings.OLLAMA_BASE_URL.rstrip('/')
        self.ollama_model = settings.OLLAMA_MODEL

    async def _call_groq(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> Optional[str]:
        if not self.groq_api_key:
            return None
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.groq_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 1024
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
            
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    logger.warning(f"Groq API returned status {res.status_code}: {res.text}")
        except Exception as e:
            logger.warning(f"Groq API connection error: {e}")
        return None

    async def _call_ollama(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        url = f"{self.ollama_base_url}/api/chat"
        payload = {
            "model": self.ollama_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {"temperature": 0.2}
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data.get("message", {}).get("content")
        except Exception:
            # Ollama not running locally is common, silently move to fallback
            pass
        return None

    async def summarize_complaint(self, text: str) -> Dict[str, Any]:
        """Generate concise executive summary, key pain points, and action items."""
        system_prompt = (
            "You are an expert customer complaint triage analyst. Analyze the user complaint. "
            "Output valid JSON with the keys: 'summary' (2-3 sentences), 'key_points' (list of strings)."
        )
        user_prompt = f"Complaint Text:\n\"\"\"{text}\"\"\""
        
        # Try Groq first
        groq_res = await self._call_groq(system_prompt, user_prompt, json_mode=True)
        if groq_res:
            try:
                data = json.loads(groq_res)
                return {
                    "summary": data.get("summary", ""),
                    "key_points": data.get("key_points", []),
                    "provider": f"Groq ({self.groq_model})"
                }
            except Exception:
                pass
                
        # Try Ollama
        ollama_res = await self._call_ollama(system_prompt, user_prompt)
        if ollama_res:
            try:
                data = json.loads(ollama_res)
                return {
                    "summary": data.get("summary", ""),
                    "key_points": data.get("key_points", []),
                    "provider": f"Ollama ({self.ollama_model})"
                }
            except Exception:
                pass

        # Deterministic NLP Fallback
        sentences = [s.strip() for s in text.replace("\n", ". ").split(". ") if len(s.strip()) > 15]
        summary = ". ".join(sentences[:2]) + ("." if sentences else "Customer inquiry submitted.")
        key_points = [
            f"Core customer complaint: {sentences[0] if sentences else 'Unspecified issue'}",
            f"Customer expressed urgency or impact requiring departmental verification."
        ]
        return {
            "summary": summary,
            "key_points": key_points,
            "provider": "Rule-Based Deterministic Engine"
        }

    async def recommend_resolution(self, text: str, similar_cases: List[Dict[str, Any]], category: str) -> Dict[str, Any]:
        """Generate step-by-step resolution steps augmented with RAG retrieval context."""
        rag_context = "\n".join([
            f"- Prior Case: {c.get('title')} | Solution: {c.get('solution_steps')}"
            for c in similar_cases[:3]
        ])
        
        system_prompt = (
            "You are a Senior Support Engineer. Recommend actionable, concrete resolution steps "
            "for this complaint. Utilize the provided similar solved cases (RAG context) where relevant. "
            "Return JSON with key 'recommended_steps' (list of strings)."
        )
        user_prompt = f"Complaint:\n{text}\n\nCategory: {category}\n\nSimilar Solved Cases:\n{rag_context}"
        
        groq_res = await self._call_groq(system_prompt, user_prompt, json_mode=True)
        if groq_res:
            try:
                data = json.loads(groq_res)
                return {
                    "recommended_steps": data.get("recommended_steps", []),
                    "provider": f"Groq ({self.groq_model})"
                }
            except Exception:
                pass

        ollama_res = await self._call_ollama(system_prompt, user_prompt)
        if ollama_res:
            try:
                data = json.loads(ollama_res)
                return {
                    "recommended_steps": data.get("recommended_steps", []),
                    "provider": f"Ollama ({self.ollama_model})"
                }
            except Exception:
                pass

        # Deterministic RAG Fallback
        steps = []
        if similar_cases:
            top_case = similar_cases[0]
            steps.append(f"Apply proven resolution from matching case #{top_case.get('id')}: {top_case.get('solution_steps')}")
        
        if "Billing" in category:
            steps.extend([
                "Locate the transaction ID in the payment gateway ledger and inspect invoice audit status.",
                "Verify whether duplicate capture occurred; initiate immediate reversal if double billed.",
                "Issue a formal credit note and confirm email receipt with the customer."
            ])
        elif "Technical" in category:
            steps.extend([
                "Cross-check application error logs and telemetry for corresponding user account session.",
                "Verify if system cache or permission lock is blocking the customer's workflow.",
                "Deploy fix or guide user through cleared cache / password re-authentication."
            ])
        elif "Security" in category:
            steps.extend([
                "Immediately terminate all active sessions and trigger security password reset.",
                "Audit IP access logs and check 2FA device binding for anomalies.",
                "Notify security operations lead and secure customer account identity."
            ])
        else:
            steps.extend([
                "Acknowledge customer communication and verify ticket details in CRM.",
                "Dispatch replacement or escalate to responsible regional logistics coordinator.",
                "Follow up within designated SLA window to confirm full customer satisfaction."
            ])

        return {
            "recommended_steps": steps,
            "provider": "Knowledge-Base Grounded Fallback"
        }

    async def generate_response_draft(self, complaint: Dict[str, Any], tone: str = "Empathetic & Professional") -> Dict[str, Any]:
        """Generate empathetic email response draft ready to send."""
        system_prompt = (
            f"You are a dedicated enterprise customer success specialist. Write an empathetic, "
            f"courteous, and action-oriented email reply in the tone of '{tone}'. "
            "Output JSON with keys 'subject' and 'body'."
        )
        user_prompt = (
            f"Complaint Subject: {complaint.get('title')}\n"
            f"Customer Email: {complaint.get('sender_email')}\n"
            f"Department: {complaint.get('department')}\n"
            f"Summary: {complaint.get('ai_summary') or complaint.get('description')[:300]}\n"
        )
        
        groq_res = await self._call_groq(system_prompt, user_prompt, json_mode=True)
        if groq_res:
            try:
                data = json.loads(groq_res)
                return {
                    "subject": data.get("subject", f"Re: {complaint.get('title')} [Ref: {complaint.get('ticket_number')}]"),
                    "body": data.get("body", ""),
                    "provider": f"Groq ({self.groq_model})"
                }
            except Exception:
                pass

        # Fallback Email Draft
        ticket_num = complaint.get("ticket_number", "CMP-10001")
        title = complaint.get("title", "Your Inquiry")
        dept = complaint.get("department", "Support")
        
        body = (
            f"Dear Customer,\n\n"
            f"Thank you for contacting our {dept} team regarding \"{title}\" (Ticket: {ticket_num}).\n\n"
            f"We sincerely apologize for the inconvenience this issue has caused you. We have carefully "
            f"reviewed your situation and our specialist team has already initiated the investigation.\n\n"
            f"Your case is currently prioritized, and we will update you as soon as the verification is complete.\n\n"
            f"If you have any further details or transaction IDs to add, please reply directly to this email.\n\n"
            f"Warm regards,\n"
            f"Customer Care & {dept} Operations Team"
        )
        
        return {
            "subject": f"Update on Your Request: {title} [{ticket_num}]",
            "body": body,
            "provider": "Template Intelligence Generator"
        }

llm_service = LLMService()
