import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.complaint import Complaint
from app.ai.embeddings import embeddings_engine
from app.core.database import IS_POSTGRES

logger = logging.getLogger(__name__)

class SemanticSearchService:
    """Enterprise Semantic Search Service.
    Uses dense 384-dimensional embeddings and pgvector (or cosine distance fallback)
    to find conceptually matching complaints even when phrasing and keywords differ entirely.
    """

    @staticmethod
    def search_complaints(
        db: Session,
        query_text: str,
        limit: int = 10,
        threshold: float = 0.50,
        exclude_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Find complaints semantically similar to a search query string."""
        if not query_text or not query_text.strip():
            return []

        query_embedding = embeddings_engine.get_embedding(query_text)

        # 1. PostgreSQL + pgvector execution
        if IS_POSTGRES:
            try:
                emb_str = "[" + ",".join(str(float(x)) for x in query_embedding) + "]"
                sql = text("""
                    SELECT id, ticket_number, subject, description, category, department_id, status,
                           1 - (embedding::vector <=> :vec::vector) AS similarity
                    FROM complaints
                    WHERE embedding IS NOT NULL
                      AND (:exclude_id IS NULL OR id != :exclude_id)
                    ORDER BY embedding::vector <=> :vec::vector ASC
                    LIMIT :limit;
                """)
                rows = db.execute(sql, {
                    "vec": emb_str,
                    "exclude_id": exclude_id,
                    "limit": limit
                }).fetchall()

                results = []
                for row in rows:
                    sim = round(float(row.similarity), 4)
                    if sim >= threshold:
                        results.append({
                            "id": row.id,
                            "ticket_number": row.ticket_number or f"CMP-{row.id}",
                            "subject": row.subject or "",
                            "description": row.description or "",
                            "category": row.category,
                            "department_id": row.department_id,
                            "status": row.status,
                            "similarity_score": sim,
                            "is_duplicate": sim >= 0.85,
                            "display_badge": f"{round(sim * 100)}% Semantic Match"
                        })
                return results
            except Exception as e:
                logger.info(f"pgvector query fallback to in-memory vector math: {e}")

        # 2. SQLite / In-Memory vector cosine similarity fallback
        query = db.query(Complaint)
        if exclude_id:
            query = query.filter(Complaint.id != exclude_id)

        candidates = query.all()
        scored_cases = []

        for c in candidates:
            c_emb = c.embedding
            if not c_emb:
                # Dynamically generate and backfill embedding if missing
                full_txt = f"{c.subject or ''} {c.description or c.body or ''}"
                c_emb = embeddings_engine.get_embedding(full_txt)
                c.embedding = c_emb
                db.flush()

            sim = embeddings_engine.cosine_similarity(query_embedding, c_emb)
            if sim >= threshold:
                scored_cases.append({
                    "id": c.id,
                    "ticket_number": c.ticket_number or f"CMP-{c.id}",
                    "subject": c.subject or "",
                    "description": c.description or c.body or "",
                    "category": c.category,
                    "department_id": c.department_id,
                    "status": c.status,
                    "similarity_score": round(float(sim), 4),
                    "is_duplicate": sim >= 0.85,
                    "display_badge": f"{round(sim * 100)}% Semantic Match"
                })

        scored_cases.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored_cases[:limit]

    @staticmethod
    def find_similar_to_complaint(
        db: Session,
        complaint_id: int,
        limit: int = 10,
        threshold: float = 0.50
    ) -> List[Dict[str, Any]]:
        """'Find complaints similar to this one' using the source complaint's semantic embedding."""
        source_complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not source_complaint:
            raise ValueError(f"Complaint {complaint_id} not found")

        source_text = f"{source_complaint.subject or ''} {source_complaint.description or source_complaint.body or ''}"
        return SemanticSearchService.search_complaints(
            db=db,
            query_text=source_text,
            limit=limit,
            threshold=threshold,
            exclude_id=complaint_id
        )

semantic_search_service = SemanticSearchService()
