import json
from typing import Dict, Any
from app.ai.llm_provider import get_llm_provider

class ResponseGenerator:
    @staticmethod
    async def generate_draft(
        ticket_number: str,
        customer_name: str,
        subject: str,
        body: str,
        department: str,
        tone: str = "Empathetic & Professional"
    ) -> Dict[str, Any]:
        """Generates a customer email draft ready for human agent review and approval."""
        llm = get_llm_provider()

        system_prompt = (
            f"You are a dedicated Customer Success Specialist. Compose an empathetic, polite, "
            f"and action-oriented response to the customer in the tone of '{tone}'. "
            "Output valid JSON with exactly two keys: 'subject' (e.g. 'Re: ... [Ticket #...]') "
            "and 'body' (the full email response draft). NOTE: Do not invent false commitments."
        )
        user_prompt = (
            f"Customer Name: {customer_name or 'Valued Customer'}\n"
            f"Ticket Number: {ticket_number}\n"
            f"Department: {department}\n"
            f"Customer Issue Subject: {subject}\n"
            f"Customer Issue Details: {body}\n"
        )

        response_text = await llm.generate_chat(system_prompt, user_prompt, json_mode=True)
        if response_text:
            try:
                data = json.loads(response_text)
                return {
                    "subject": data.get("subject", f"Re: {subject} [{ticket_number}]"),
                    "body": data.get("body", ""),
                    "requires_approval": True,
                    "provider": llm.provider_name
                }
            except Exception:
                pass

        # Fallback Template Draft
        cust_greeting = f"Dear {customer_name}," if customer_name else "Dear Customer,"
        draft_body = (
            f"{cust_greeting}\n\n"
            f"Thank you for contacting our {department} team regarding \"{subject}\" (Ticket Reference: {ticket_number}).\n\n"
            f"We sincerely apologize for any inconvenience caused. Our team has already begun reviewing "
            f"the details of your request to ensure an expedited resolution.\n\n"
            f"Your case is currently prioritized, and we will reach out as soon as our investigation is complete. "
            f"If you have additional information to provide, please reply directly to this message.\n\n"
            f"Warm regards,\n"
            f"Customer Care & {department} Operations Team"
        )

        return {
            "subject": f"Update regarding your inquiry: {subject} [{ticket_number}]",
            "body": draft_body,
            "requires_approval": True,
            "provider": "Template Generator Fallback"
        }

response_generator = ResponseGenerator()
