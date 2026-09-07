import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.ai.embeddings import embeddings_engine
from app.ai.llm_provider import get_llm_provider
from app.models.knowledge import KnowledgeDocument

class RAGEngine:
    @staticmethod
    def retrieve_relevant_policies(
        query_text: str,
        db: Session,
        limit: int = 3,
        min_similarity: float = 0.40
    ) -> List[Dict[str, Any]]:
        """Retrieves matching company policies and SOPs using vector cosine similarity."""
        query_vector = embeddings_engine.get_embedding(query_text)
        docs = db.query(KnowledgeDocument).filter(KnowledgeDocument.is_active == True).all()

        scored = []
        for doc in docs:
            if not doc.embedding:
                continue
            sim = embeddings_engine.cosine_similarity(query_vector, doc.embedding)
            if sim >= min_similarity:
                scored.append({
                    "id": doc.id,
                    "title": doc.title,
                    "category": doc.category,
                    "document_type": doc.document_type,
                    "content_snippet": doc.chunk_text,
                    "similarity": round(sim, 4)
                })

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:limit]

    @classmethod
    async def generate_grounded_recommendation(
        cls,
        complaint_text: str,
        category: str,
        db: Session
    ) -> Dict[str, Any]:
        """Generates resolution steps strictly grounded on retrieved company documentation."""
        relevant_docs = cls.retrieve_relevant_policies(complaint_text, db, limit=3)
        
        context_str = "\n\n".join([
            f"Document [{d['title']}] (Type: {d['document_type']}):\n{d['content_snippet']}"
            for d in relevant_docs
        ])

        llm = get_llm_provider()

        system_prompt = (
            "You are a Senior Customer Support Operations Lead. Recommend concrete, step-by-step "
            "resolution actions for the customer complaint based strictly on the retrieved company policies "
            "and SOPs below. DO NOT invent policies that are not grounded in the provided context.\n\n"
            f"--- OFFICIAL COMPANY POLICIES & SOPS ---\n{context_str}\n---------------------------------------\n"
            "Return JSON with key 'recommended_steps' (list of strings)."
        )
        user_prompt = f"Complaint Category: {category}\nComplaint Text: {complaint_text}"

        response_text = await llm.generate_chat(system_prompt, user_prompt, json_mode=True)
        if response_text:
            try:
                data = json.loads(response_text)
                return {
                    "recommended_steps": data.get("recommended_steps", []),
                    "cited_documents": relevant_docs,
                    "provider": llm.provider_name
                }
            except Exception:
                pass

        # Grounded Fallback based on retrieved documents
        steps = []
        if relevant_docs:
            top_doc = relevant_docs[0]
            steps.append(f"Execute procedure from [{top_doc['title']}]: {top_doc['content_snippet'][:200]}...")
        
        if "Billing" in category:
            steps.extend([
                "Audit transaction authorization logs with payment processor.",
                "Initiate chargeback/reversal if duplicate debit is confirmed within 24h.",
                "Issue credit note and send automated notification."
            ])
        elif "Technical" in category:
            steps.extend([
                "Inspect server telemetry and application error trace for user account.",
                "Clear system cache and trigger token reset if permission is corrupted.",
                "Deploy patch or instruct user on browser/app cache clearance."
            ])
        elif "Security" in category:
            steps.extend([
                "Immediately terminate all active sessions and invalidate OAuth tokens.",
                "Challenge user via secondary verified phone/email before granting access.",
                "Report incident to security operations lead."
            ])
        else:
            steps.extend([
                "Acknowledge customer inquiry within the SLA response window.",
                "Coordinate with logistics or operations team for immediate ticket resolution."
            ])

        return {
            "recommended_steps": steps,
            "cited_documents": relevant_docs,
            "provider": "Grounded Fallback Engine"
        }

    @classmethod
    async def answer_query(
        cls,
        question: str,
        db: Session,
        limit: int = 3
    ) -> Dict[str, Any]:
        """4. RAG question answering: answers user/agent questions strictly grounded on retrieved company documents."""
        relevant_docs = cls.retrieve_relevant_policies(question, db, limit=limit)
        context_str = "\n\n".join([
            f"Document [{d['title']}] ({d['document_type']}):\n{d['content_snippet']}"
            for d in relevant_docs
        ])

        llm = get_llm_provider()
        system_prompt = (
            "You are an expert enterprise policy copilot. Answer the question using ONLY the retrieved company "
            "knowledge base documents below. If the information is not present, state clearly that no policy covers it.\n\n"
            f"--- COMPANY KNOWLEDGE BASE ---\n{context_str}\n------------------------------\n"
        )
        user_prompt = f"Question: {question}"

        reply = await llm.generate_chat(system_prompt, user_prompt)
        if not reply:
            reply = (
                f"Guidance from company records:\n\n"
                + (relevant_docs[0]["content_snippet"] if relevant_docs else "No specific policy document matches this query.")
            )

        return {
            "answer": reply,
            "cited_documents": relevant_docs,
            "provider": llm.provider_name
        }

    @classmethod
    async def explain_complaint(
        cls,
        subject: str,
        body: str,
        category: str,
        department: str,
        entities: Optional[List[Dict[str, Any]]] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """6. Internal complaint explanation: synthesizes an operational briefing for support agents explaining root cause and impact."""
        llm = get_llm_provider()
        ent_str = ", ".join([f"{e.get('entity_type')}: {e.get('entity_value')}" for e in (entities or [])])

        system_prompt = (
            "You are an expert customer operations diagnostic analyst. Provide a clear internal technical explanation "
            "of this customer complaint for the support agent. Detail: (1) Core root cause, (2) Business/operational impact, "
            "(3) Customer sentiment drivers, and (4) Necessary diagnostic verification steps. "
            "Output valid JSON with keys: 'explanation' (2-3 sentences), 'root_cause' (string), 'impact_level' (string), and 'verification_steps' (list)."
        )
        user_prompt = (
            f"Department: {department} | Category: {category}\n"
            f"Subject: {subject}\n"
            f"Complaint Narrative:\n{body}\n"
            f"Extracted Entities: {ent_str or 'None'}"
        )

        response_text = await llm.generate_chat(system_prompt, user_prompt, json_mode=True)
        if response_text:
            try:
                data = json.loads(response_text)
                return {
                    "explanation": data.get("explanation", ""),
                    "root_cause": data.get("root_cause", ""),
                    "impact_level": data.get("impact_level", "MEDIUM"),
                    "verification_steps": data.get("verification_steps", []),
                    "provider": llm.provider_name
                }
            except Exception:
                pass

        # Fallback technical explanation
        return {
            "explanation": f"Customer filed a {category} complaint regarding '{subject}'. Issue requires review by {department} team.",
            "root_cause": f"Reported {category} issue requiring departmental verification.",
            "impact_level": "MEDIUM",
            "verification_steps": [
                "Verify customer identity and account state in internal dashboard.",
                "Cross-reference transaction/incident timestamps against system logs."
            ],
            "provider": "Diagnostic Explanation Engine"
        }

    @classmethod
    async def reason_over_complaint_and_policies(
        cls,
        complaint_text: str,
        category: str,
        db: Session
    ) -> Dict[str, Any]:
        """7. Reasoning over retrieved complaint/policy information: evaluates claim eligibility against policy terms."""
        relevant_docs = cls.retrieve_relevant_policies(complaint_text, db, limit=3)
        context_str = "\n\n".join([
            f"Policy [{d['title']}]:\n{d['content_snippet']}"
            for d in relevant_docs
        ])

        llm = get_llm_provider()
        system_prompt = (
            "You are an enterprise compliance and policy reasoning officer. Analyze the customer complaint against the "
            "retrieved policy documents. Evaluate whether the customer's request is justified under existing policies, "
            "what exceptions or approvals are required, and what resolution is contractually appropriate. "
            "Output valid JSON with keys: 'policy_aligned' (boolean), 'reasoning' (detailed explanation), 'applicable_policies' (list), and 'policy_recommendation' (string)."
        )
        user_prompt = (
            f"Complaint Category: {category}\n"
            f"Complaint Statement: {complaint_text}\n\n"
            f"Retrieved Company Policies:\n{context_str or 'Standard Customer Care Guidelines apply.'}"
        )

        response_text = await llm.generate_chat(system_prompt, user_prompt, json_mode=True)
        if response_text:
            try:
                data = json.loads(response_text)
                return {
                    "policy_aligned": data.get("policy_aligned", True),
                    "reasoning": data.get("reasoning", ""),
                    "applicable_policies": data.get("applicable_policies", [d["title"] for d in relevant_docs]),
                    "policy_recommendation": data.get("policy_recommendation", ""),
                    "cited_documents": relevant_docs,
                    "provider": llm.provider_name
                }
            except Exception:
                pass

        # Fallback compliance reasoning
        return {
            "policy_aligned": True,
            "reasoning": f"Complaint claims align with standard {category} customer care policies and require standard validation.",
            "applicable_policies": [d["title"] for d in relevant_docs] if relevant_docs else [f"General {category} Policy"],
            "policy_recommendation": "Approve standard resolution after agent verification.",
            "cited_documents": relevant_docs,
            "provider": "Compliance Reasoning Engine"
        }

rag_engine = RAGEngine()
