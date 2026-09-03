from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.ai.embeddings import embeddings_engine
from app.models.complaint import Complaint

class DuplicateDetector:
    @staticmethod
    def detect_similar_and_duplicates(
        new_embedding: List[float],
        db: Session,
        current_complaint_id: Optional[int] = None,
        duplicate_threshold: float = 0.85,
        similar_threshold: float = 0.65
    ) -> Dict[str, Any]:
        """Detects if a complaint is a duplicate or finds top similar tickets."""
        if not new_embedding:
            return {"is_duplicate": False, "duplicate_of_id": None, "similar_complaints": []}

        query = db.query(Complaint).filter(Complaint.embedding.isnot(None))
        if current_complaint_id:
            query = query.filter(Complaint.id != current_complaint_id)

        candidates = query.all()
        scored_cases = []

        is_duplicate = False
        duplicate_of_id = None

        for c in candidates:
            if not c.embedding:
                continue
            sim = embeddings_engine.cosine_similarity(new_embedding, c.embedding)
            if sim >= duplicate_threshold and not is_duplicate:
                is_duplicate = True
                duplicate_of_id = c.id
            if sim >= similar_threshold:
                scored_cases.append({
                    "id": c.id,
                    "ticket_number": c.ticket_number,
                    "subject": c.subject,
                    "category": c.category,
                    "department_id": c.department_id,
                    "status": c.status,
                    "similarity": round(sim, 4)
                })

        scored_cases.sort(key=lambda x: x["similarity"], reverse=True)

        return {
            "is_duplicate": is_duplicate,
            "duplicate_of_id": duplicate_of_id,
            "similar_complaints": scored_cases[:5]
        }

duplicate_detector = DuplicateDetector()
