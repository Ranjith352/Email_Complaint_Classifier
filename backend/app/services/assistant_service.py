import re
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.services.assistant_tools import assistant_tools
from app.services.privacy_service import privacy_service
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

# Pattern for prohibited SQL execution attempts
PROHIBITED_SQL_PATTERNS = [
    r'\bselect\b.*\bfrom\b',
    r'\bdrop\s+table\b',
    r'\binsert\s+into\b',
    r'\bupdate\b.*\bset\b',
    r'\bdelete\s+from\b',
    r'\bunion\s+select\b',
    r'\bexec\b',
    r'\bexecute\s+sql\b',
    r'\balter\s+table\b'
]

class AIAssistantService:
    """
    AI Copilot Orchestrator for Support Agents and Managers.
    - Strictly tool-governed: NEVER allows arbitrary SQL execution.
    - Executes only authorized backend tools.
    - Grounded responses with citations and data payloads.
    """

    ALLOWED_TOOLS = {
        "search_complaints": assistant_tools.search_complaints,
        "get_complaint": assistant_tools.get_complaint,
        "find_similar_complaints": assistant_tools.find_similar_complaints,
        "search_knowledge_base": assistant_tools.search_knowledge_base,
        "get_customer_history": assistant_tools.get_customer_history,
        "get_department": assistant_tools.get_department,
        "get_agent_workload": assistant_tools.get_agent_workload,
        "generate_response": assistant_tools.generate_response,
    }

    async def handle_query(
        self,
        message: str,
        db: Session,
        complaint_id: Optional[int] = None,
        ticket_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """Processes agent/manager query through intent recognition and controlled tool invocation."""
        raw_msg = message.strip()
        msg_lower = raw_msg.lower()

        # -------------------------------------------------------------
        # 1. Strict Security Guardrail: Reject Arbitrary SQL Execution
        # -------------------------------------------------------------
        for pat in PROHIBITED_SQL_PATTERNS:
            if re.search(pat, msg_lower):
                logger.warning(f"Prohibited SQL query execution attempt blocked: {privacy_service.sanitize_log(raw_msg)}")
                return {
                    "reply": "Direct SQL execution is strictly prohibited. The AI assistant exclusively accesses data through controlled, secure backend tools.",
                    "tool_called": "none",
                    "error": "SQL_EXECUTION_FORBIDDEN",
                    "data": None
                }

        # Extract ticket number from text if not explicitly provided
        if not ticket_number:
            t_match = re.search(r'\b(CMP-[A-Z0-9_\-]+)\b', raw_msg, re.IGNORECASE)
            if t_match:
                ticket_number = t_match.group(1).upper()

        # -------------------------------------------------------------
        # 2. Intent 1: "Show unresolved critical Finance complaints" / Complaint Search
        # -------------------------------------------------------------
        if any(w in msg_lower for w in ["unresolved", "open complaints", "critical complaints", "find complaints", "show complaints", "search complaints"]):
            dept = None
            for d in ["finance", "it", "customer support", "logistics", "security"]:
                if d in msg_lower:
                    dept = d.title()
                    break

            prio = None
            if any(w in msg_lower for w in ["critical", "p1", "urgent"]):
                prio = "Critical"
            elif any(w in msg_lower for w in ["high", "p2"]):
                prio = "High"

            unres = any(w in msg_lower for w in ["unresolved", "open", "pending"])

            tool_res = assistant_tools.search_complaints(
                db=db,
                department=dept,
                priority=prio,
                unresolved_only=unres,
                limit=10
            )

            complaints = tool_res.get("complaints", [])
            total = tool_res.get("total_found", 0)

            if total == 0:
                reply = f"No unresolved {prio or ''} {dept or ''} complaints found in the active queue."
            else:
                lines = [f"Found {total} matching complaint(s) in {dept or 'all departments'} (Priority: {prio or 'All'}):"]
                for c in complaints[:5]:
                    lines.append(f"- **{c['ticket_number']}**: {c['subject']} (Priority: {c['priority']}, Status: {c['status']}, Assigned: {c['assigned_agent']})")
                reply = "\n".join(lines)

            return {
                "reply": reply,
                "tool_called": "search_complaints",
                "tool_args": {"department": dept, "priority": prio, "unresolved_only": unres},
                "data": tool_res
            }

        # -------------------------------------------------------------
        # 3. Intent 2: "Summarize complaint CMP-10001" / Get Complaint
        # -------------------------------------------------------------
        if "summarize" in msg_lower or ("summary" in msg_lower and ticket_number):
            if not ticket_number and not complaint_id:
                return {
                    "reply": "Please specify a complaint ID or ticket number (e.g. 'Summarize CMP-10001').",
                    "tool_called": "none"
                }

            complaint_data = assistant_tools.get_complaint(
                db=db,
                complaint_id=complaint_id,
                ticket_number=ticket_number
            )

            if "error" in complaint_data:
                return {"reply": complaint_data["error"], "tool_called": "get_complaint", "data": complaint_data}

            # Generate concise summary
            text_to_sum = f"{complaint_data['subject']}. {complaint_data['description']}"
            summary_info = await llm_service.summarize_complaint(text_to_sum)

            reply = (
                f"### Executive Summary for {complaint_data['ticket_number']}\n"
                f"- **Department**: {complaint_data['department']} | **Priority**: {complaint_data['priority']} | **Status**: {complaint_data['status']}\n"
                f"- **Customer**: {complaint_data['customer']['masked_name']} ({complaint_data['customer']['masked_email']})\n\n"
                f"**Summary**: {summary_info.get('summary', complaint_data.get('ai_summary', 'Customer reported an operational issue requiring departmental review.'))}\n\n"
                f"**Key Points**:\n" +
                "\n".join([f"- {p}" for p in summary_info.get("key_points", ["Customer requested resolution."])])
            )

            return {
                "reply": reply,
                "tool_called": "get_complaint",
                "tool_args": {"ticket_number": ticket_number, "complaint_id": complaint_id},
                "data": {**complaint_data, "summary_nlp": summary_info}
            }

        # -------------------------------------------------------------
        # 4. Intent 3: "Find similar complaints"
        # -------------------------------------------------------------
        if "similar" in msg_lower or "duplicate" in msg_lower:
            similar_res = assistant_tools.find_similar_complaints(
                db=db,
                complaint_id=complaint_id,
                text=raw_msg if not complaint_id else None,
                limit=5
            )

            cases = similar_res.get("similar_cases", [])
            if not cases:
                reply = "No closely matching previous complaints were found."
            else:
                lines = [f"Found {len(cases)} similar historical case(s):"]
                for sc in cases:
                    lines.append(f"- **{sc['ticket_number']}** ({sc['department']}): {sc['subject']} [Similarity: {int(sc['similarity_score']*100)}%]")
                reply = "\n".join(lines)

            return {
                "reply": reply,
                "tool_called": "find_similar_complaints",
                "tool_args": {"complaint_id": complaint_id},
                "data": similar_res
            }

        # -------------------------------------------------------------
        # 5. Intent 4: "What policy applies to this refund complaint?" / Knowledge Search
        # -------------------------------------------------------------
        if any(w in msg_lower for w in ["policy", "refund policy", "billing policy", "sla rule", "guideline", "sop"]):
            kb_res = assistant_tools.search_knowledge_base(
                db=db,
                query=raw_msg,
                limit=3
            )

            policies = kb_res.get("relevant_policies", [])
            if not policies:
                reply = "No relevant company policy was found."
            else:
                top_p = policies[0]
                reply = (
                    f"Based on company policy **{top_p['title']}**:\n\n"
                    f"{top_p['key_clauses']}\n\n"
                    f"*(Referenced document: {top_p['title']} [{top_p['document_type']}])* "
                )

            return {
                "reply": reply,
                "tool_called": "search_knowledge_base",
                "tool_args": {"query": raw_msg},
                "data": kb_res
            }

        # -------------------------------------------------------------
        # 6. Intent 5: "How should this complaint be resolved?" / Resolution Recommendation
        # -------------------------------------------------------------
        if any(w in msg_lower for w in ["how should this complaint be resolved", "how to resolve", "recommend resolution", "resolution steps"]):
            complaint_text = raw_msg
            cat = "General Inquiry"
            if complaint_id or ticket_number:
                c_data = assistant_tools.get_complaint(db=db, complaint_id=complaint_id, ticket_number=ticket_number)
                if "subject" in c_data:
                    complaint_text = f"{c_data['subject']}. {c_data['description']}"
                    cat = c_data.get("category", "General Inquiry")

            # Check similar cases
            sim = assistant_tools.find_similar_complaints(db=db, complaint_id=complaint_id, text=complaint_text)
            res_info = await llm_service.recommend_resolution(
                text=complaint_text,
                similar_cases=sim.get("similar_cases", []),
                category=cat
            )

            steps_formatted = "\n".join([f"{i+1}. {s}" for i, s in enumerate(res_info.get("recommended_steps", []))])
            reply = (
                f"### {res_info.get('header', 'AI GENERATED RECOMMENDATION')}\n\n"
                f"{steps_formatted}\n\n"
                f"*{res_info.get('disclaimer', 'The agent remains responsible for the final decision.')}*"
            )

            return {
                "reply": reply,
                "tool_called": "recommend_resolution",
                "tool_args": {"complaint_id": complaint_id, "category": cat},
                "data": res_info
            }

        # -------------------------------------------------------------
        # 7. Intent 6: "Generate a response"
        # -------------------------------------------------------------
        if any(w in msg_lower for w in ["generate a response", "draft response", "generate response", "reply draft", "draft email"]):
            resp_data = await assistant_tools.generate_response(
                db=db,
                complaint_id=complaint_id,
                text=raw_msg if not complaint_id else None
            )

            reply = (
                f"### Generated Response Draft\n\n"
                f"**Subject**: {resp_data.get('subject')}\n\n"
                f"```text\n{resp_data.get('body')}\n```\n\n"
                f"*Privacy sanitized: {resp_data.get('privacy_sanitized', False)} | Provider: {resp_data.get('provider')}*"
            )

            return {
                "reply": reply,
                "tool_called": "generate_response",
                "tool_args": {"complaint_id": complaint_id},
                "data": resp_data
            }

        # -------------------------------------------------------------
        # 8. Customer History: "Customer history" / "Previous complaints"
        # -------------------------------------------------------------
        if any(w in msg_lower for w in ["customer history", "previous complaints", "complaint frequency", "customer previous"]):
            hist_res = assistant_tools.get_customer_history(
                db=db,
                complaint_id=complaint_id
            )
            if "error" in hist_res:
                reply = "Please specify a customer email or complaint ID to view customer history."
            else:
                reply = (
                    f"### Customer History ({hist_res['customer']['masked_name']})\n"
                    f"- **Total Complaints**: {hist_res['total_complaints']} (Open: {hist_res['open_complaints']}, Closed: {hist_res['closed_complaints']})\n"
                    f"- **Frequency**: {hist_res['complaint_frequency']}\n"
                    f"- **Categories**: {', '.join(hist_res['previous_categories']) or 'None'}\n"
                )
            return {
                "reply": reply,
                "tool_called": "get_customer_history",
                "tool_args": {"complaint_id": complaint_id},
                "data": hist_res
            }

        # -------------------------------------------------------------
        # 9. Agent Workload: "agent workload" / "agent capacity"
        # -------------------------------------------------------------
        if "workload" in msg_lower or "capacity" in msg_lower or "agent roster" in msg_lower:
            wl_res = assistant_tools.get_agent_workload(db=db)
            agents = wl_res.get("agents", [])
            lines = [f"### Agent Workload Roster ({len(agents)} agents):"]
            for a in agents[:5]:
                lines.append(f"- **{a['name']}** ({a['department']}): {a['current_workload']}/{a['max_workload']} tickets ({a['utilization_pct']}%) - {'Available' if a['availability'] else 'Unavailable'}")
            reply = "\n".join(lines)
            return {
                "reply": reply,
                "tool_called": "get_agent_workload",
                "data": wl_res
            }

        # Default fallback: General policy inquiry or assistant greeting
        kb_res = assistant_tools.search_knowledge_base(db=db, query=raw_msg, limit=2)
        if kb_res.get("relevant_policies"):
            p = kb_res["relevant_policies"][0]
            reply = f"Based on company policy **{p['title']}**:\n\n{p['key_clauses']}"
            return {
                "reply": reply,
                "tool_called": "search_knowledge_base",
                "data": kb_res
            }

        return {
            "reply": "I am AutoTriage Copilot. You can ask me to:\n"
                     "- \"Show unresolved critical Finance complaints.\"\n"
                     "- \"Summarize complaint CMP-10001.\"\n"
                     "- \"Find similar complaints.\"\n"
                     "- \"What policy applies to this refund complaint?\"\n"
                     "- \"How should this complaint be resolved?\"\n"
                     "- \"Generate a response.\"",
            "tool_called": "none",
            "data": None
        }

assistant_service = AIAssistantService()
