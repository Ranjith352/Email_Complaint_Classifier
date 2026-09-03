import math
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.vector_embedding import KnowledgeItem
from backend.app.services.nlp_engine import nlp_engine

logger = logging.getLogger(__name__)

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)

class RAGService:
    @staticmethod
    def seed_initial_knowledge(db: Session):
        """Seed default enterprise SOPs and resolution templates if table is empty."""
        count = db.query(KnowledgeItem).count()
        if count > 0:
            return
            
        initial_sops = [
            {
                "title": "Duplicate Payment & Double Charging Procedure",
                "category": "Billing / Payment",
                "department": "Finance",
                "problem_summary": "Customer charged twice for the same purchase, invoice, or subscription period.",
                "solution_steps": "1. Pull payment gateway transaction logs for the customer's payment reference. 2. Verify duplicate auth tokens with the acquiring bank. 3. Process immediate automated refund for the second transaction. 4. Send confirmation receipt to customer."
            },
            {
                "title": "Critical Server Outage & 500 Internal Error Incident Response",
                "category": "Technical Problem",
                "department": "IT",
                "problem_summary": "Service inaccessible, returning HTTP 500 or connection timeouts for users.",
                "solution_steps": "1. Check cloud load balancer status and container orchestrator restarts. 2. Review application error logs in Datadog/Sentry for unhandled database connection pool exhaustion. 3. Restart degraded worker nodes or roll back recent deployment. 4. Publish incident status post-mortem."
            },
            {
                "title": "Suspected Account Takeover & Security Compromise",
                "category": "Security Issue",
                "department": "Security",
                "problem_summary": "Customer reports unauthorized login attempts, changed passwords, or unknown IP access.",
                "solution_steps": "1. Instantly invalidate all active OAuth JWT sessions and user access tokens. 2. Lock account from further transactions. 3. Dispatch an identity verification challenge to customer's verified phone/backup email. 4. Require 2FA re-enrollment upon restoration."
            },
            {
                "title": "Damaged Package & Delayed Order Resolution",
                "category": "Customer Support",
                "department": "Support",
                "problem_summary": "Customer item arrived damaged, missing contents, or shipment delayed beyond estimated delivery date.",
                "solution_steps": "1. Review carrier tracking scan history and shipping insurance coverage. 2. Authorize immediate priority courier replacement without requiring returned damaged goods. 3. Issue a 15% goodwill store credit."
            },
            {
                "title": "Academic Enrollment & Course Registration Error",
                "category": "Operations & Admin",
                "department": "Operations",
                "problem_summary": "Student unable to enroll in required semester courses due to prerequisite override or portal freeze.",
                "solution_steps": "1. Manually check academic standing and prerequisite waiver approval in SIS. 2. Grant temporary departmental override flag in registrar portal. 3. Notify student advisor and confirm enrollment."
            }
        ]
        
        for sop in initial_sops:
            text_to_embed = f"{sop['title']} {sop['category']} {sop['problem_summary']} {sop['solution_steps']}"
            emb = nlp_engine.get_embedding(text_to_embed)
            item = KnowledgeItem(
                title=sop["title"],
                category=sop["category"],
                department=sop["department"],
                problem_summary=sop["problem_summary"],
                solution_steps=sop["solution_steps"],
                embedding=emb
            )
            db.add(item)
            
        db.commit()
        logger.info(f"Seeded {len(initial_sops)} enterprise RAG knowledge items.")

    @staticmethod
    def search_similar_cases(query_text: str, db: Session, limit: int = 3, category: str = None) -> List[Dict[str, Any]]:
        """Perform semantic search against indexed knowledge base items."""
        query_vector = nlp_engine.get_embedding(query_text)
        
        query = db.query(KnowledgeItem)
        if category:
            query = query.filter(KnowledgeItem.category == category)
            
        items = query.all()
        if not items:
            items = db.query(KnowledgeItem).all()
            
        scored = []
        for item in items:
            score = cosine_similarity(query_vector, item.embedding)
            scored.append({
                "id": item.id,
                "title": item.title,
                "problem_summary": item.problem_summary,
                "solution_steps": item.solution_steps,
                "similarity_score": round(score, 4)
            })
            
        scored.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored[:limit]

rag_service = RAGService()
