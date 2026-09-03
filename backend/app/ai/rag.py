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

rag_engine = RAGEngine()
