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
        """Generates a professional customer email draft ready for human agent review and approval.
        Standard format:
        Dear Customer,

        We have reviewed your complaint regarding ... Our [Department] team is currently ...

        Complaint ID: CMP-10001

        Regards,
        Customer Support Team
        """
        llm = get_llm_provider()

        system_prompt = (
            f"You are a dedicated Customer Success Specialist. Compose a professional, courteous, "
            f"and action-oriented response to the customer in the tone of '{tone}'.\n"
            "Format the email response body EXACTLY following this structure:\n"
            "Dear [Customer Name or Customer],\n\n"
            "We have reviewed your complaint regarding [issue]. Our [Department] team is currently [action] and will [resolution step].\n\n"
            f"Complaint ID: {ticket_number}\n\n"
            "Regards,\n"
            "Customer Support Team\n\n"
            "Output valid JSON with keys 'subject' (e.g. 'Re: ... [Ticket #...]') "
            "and 'body' (the full formatted email text). Do not invent false policy commitments."
        )
        user_prompt = (
            f"Customer Name: {customer_name or 'Customer'}\n"
            f"Ticket Number: {ticket_number}\n"
            f"Department: {department}\n"
            f"Customer Issue Subject: {subject}\n"
            f"Customer Issue Details: {body}\n"
        )

        response_text = await llm.generate_chat(system_prompt, user_prompt, json_mode=True)
        if response_text:
            try:
                data = json.loads(response_text)
                draft_content = data.get("body", "").strip()
                if draft_content:
                    # Guarantee Complaint ID reference is present in the draft
                    if f"Complaint ID: {ticket_number}" not in draft_content and f"{ticket_number}" not in draft_content:
                        draft_content += f"\n\nComplaint ID: {ticket_number}"
                    if "Customer Support Team" not in draft_content:
                        draft_content += "\n\nRegards,\nCustomer Support Team"
                    return {
                        "subject": data.get("subject", f"Re: {subject} [{ticket_number}]"),
                        "body": draft_content,
                        "requires_approval": True,
                        "is_approved": False,
                        "is_sent": False,
                        "provider": llm.provider_name
                    }
            except Exception:
                pass

        # Fallback Professional Template
        cust_greeting = (
            f"Dear {customer_name},"
            if (customer_name and customer_name.strip().lower() not in ["valued customer", "guest", "customer", "none"])
            else "Dear Customer,"
        )

        issue_text = f"{subject} {body}".lower()
        if any(kw in issue_text for kw in ["duplicate", "deducted twice", "charged twice", "double charge", "two times"]):
            issue_phrase = "the duplicate payment"
            action_phrase = "is currently verifying the transaction and will process the necessary refund if the duplicate transaction is confirmed."
        elif "refund" in issue_text:
            issue_phrase = "your refund request"
            action_phrase = "is reviewing the payment records to expedite your refund processing."
        elif any(kw in issue_text for kw in ["login", "portal", "cannot access", "password", "authentication"]):
            issue_phrase = "the portal access and authentication difficulties"
            action_phrase = "is investigating the application logs and working to restore full access."
        elif any(kw in issue_text for kw in ["delay", "delivery", "shipping", "courier", "package"]):
            issue_phrase = "the delivery delay regarding your order"
            action_phrase = "is coordinating with logistics to expedite tracking and dispatch."
        elif any(kw in issue_text for kw in ["billing", "invoice", "overcharge", "fee"]):
            issue_phrase = "the billing discrepancy"
            action_phrase = "is auditing the invoice details and will issue any necessary credits."
        else:
            clean_subj = subject.strip().rstrip(".")
            issue_phrase = f"your inquiry regarding {clean_subj}"
            action_phrase = "is currently reviewing the details and will follow up with the next steps."

        dept_label = f"Our {department} team" if (department and department.lower() not in ["general", "support"]) else "Our Customer Support team"

        draft_body = (
            f"{cust_greeting}\n\n"
            f"We have reviewed your complaint regarding {issue_phrase}. "
            f"{dept_label} {action_phrase}\n\n"
            f"Complaint ID: {ticket_number}\n\n"
            f"Regards,\n"
            f"Customer Support Team"
        )

        return {
            "subject": f"Update regarding your complaint: {subject} [{ticket_number}]",
            "body": draft_body,
            "requires_approval": True,
            "is_approved": False,
            "is_sent": False,
            "provider": "Template Generator Fallback"
        }

response_generator = ResponseGenerator()
