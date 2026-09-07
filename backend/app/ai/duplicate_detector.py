import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.ai.embeddings import embeddings_engine
from app.models.complaint import Complaint
from app.core.database import IS_POSTGRES

logger = logging.getLogger(__name__)

# =============================================================================
# 1. Baseline: TF-IDF + Cosine Similarity Detector
# =============================================================================
class TFIDFBaselineDuplicateDetector:
    """Baseline duplicate detection using TF-IDF feature extraction and cosine similarity."""

    def __init__(self):
        self._vectorizer = None

    def compute_similarity(self, query_text: str, candidate_texts: List[str]) -> List[float]:
        """Calculates cosine similarity between a query text and candidate texts using TF-IDF."""
        if not query_text or not candidate_texts:
            return [0.0] * len(candidate_texts)

        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            corpus = [query_text] + candidate_texts
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, stop_words="english")
            tfidf_matrix = vectorizer.fit_transform(corpus)

            sim_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
            return [round(float(s), 4) for s in sim_matrix[0]]
        except Exception as e:
            logger.warning(f"TF-IDF similarity calculation fallback error: {e}")
            # Fallback simple lexical token overlap
            q_tokens = set(query_text.lower().split())
            scores = []
            for ct in candidate_texts:
                c_tokens = set(ct.lower().split())
                if not q_tokens or not c_tokens:
                    scores.append(0.0)
                else:
                    overlap = len(q_tokens.intersection(c_tokens))
                    union = len(q_tokens.union(c_tokens))
                    scores.append(round(overlap / union, 4) if union else 0.0)
            return scores

    def detect_duplicates(
        self,
        query_text: str,
        db: Session,
        current_complaint_id: Optional[int] = None,
        duplicate_threshold: float = 0.85
    ) -> Dict[str, Any]:
        """Performs baseline duplicate search against active database complaints."""
        query = db.query(Complaint)
        if current_complaint_id:
            query = query.filter(Complaint.id != current_complaint_id)

        candidates = query.all()
        if not candidates or not query_text:
            return {
                "engine": "TF-IDF (Baseline)",
                "is_duplicate": False,
                "matched_complaint_id": None,
                "similarity_score": 0.0,
                "similar_complaints": []
            }

        candidate_texts = [(c.subject or "") + " " + (c.description or "") for c in candidates]
        scores = self.compute_similarity(query_text, candidate_texts)

        scored = []
        for c, score in zip(candidates, scores):
            if score > 0.3:
                scored.append({
                    "id": c.id,
                    "ticket_number": c.ticket_number or f"CMP-{c.id}",
                    "subject": c.subject,
                    "similarity": score
                })

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        top_match = scored[0] if scored else None
        top_score = top_match["similarity"] if top_match else 0.0
        is_dup = top_score >= duplicate_threshold

        return {
            "engine": "TF-IDF (Baseline)",
            "is_duplicate": is_dup,
            "matched_complaint_id": top_match["id"] if is_dup and top_match else None,
            "similarity_score": top_score,
            "display_warning": "Possible duplicate complaint" if is_dup else None,
            "similar_complaints": scored[:5]
        }


# =============================================================================
# 2. Primary: Sentence Transformers + pgvector Similarity Search
# =============================================================================
class SentenceTransformerPgVectorDuplicateDetector:
    """Primary duplicate detection engine.
    Flow:
    Complaint -> Embedding (Sentence Transformers) -> pgvector (or cosine similarity) -> Similarity Search -> Similar Complaints
    """

    def __init__(self, duplicate_threshold: float = 0.85, similar_threshold: float = 0.65):
        self.duplicate_threshold = duplicate_threshold
        self.similar_threshold = similar_threshold

    def search_similar_complaints(
        self,
        db: Session,
        embedding: List[float],
        current_complaint_id: Optional[int] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Executes similarity search via pgvector if available, or in-memory vector cosine distance."""
        if not embedding:
            return []

        # Try pgvector query if connected to PostgreSQL
        if IS_POSTGRES:
            try:
                emb_str = "[" + ",".join(str(float(x)) for x in embedding) + "]"
                sql = text("""
                    SELECT id, ticket_number, subject, category, department_id, status,
                           1 - (embedding::vector <=> :vec::vector) AS similarity
                    FROM complaints
                    WHERE embedding IS NOT NULL
                      AND (:current_id IS NULL OR id != :current_id)
                    ORDER BY embedding::vector <=> :vec::vector ASC
                    LIMIT :limit;
                """)
                res = db.execute(sql, {
                    "vec": emb_str,
                    "current_id": current_complaint_id,
                    "limit": top_k
                }).fetchall()

                results = []
                for row in res:
                    sim = round(float(row.similarity), 4)
                    if sim >= self.similar_threshold:
                        results.append({
                            "id": row.id,
                            "ticket_number": row.ticket_number or f"CMP-{row.id}",
                            "subject": row.subject,
                            "category": row.category,
                            "department_id": row.department_id,
                            "status": row.status,
                            "similarity": sim
                        })
                return results
            except Exception as pg_err:
                logger.info(f"pgvector query fallback to vector math: {pg_err}")

        # Local SQLite / Fallback vector cosine calculation
        query = db.query(Complaint).filter(Complaint.embedding.isnot(None))
        if current_complaint_id:
            query = query.filter(Complaint.id != current_complaint_id)

        candidates = query.all()
        scored_cases = []

        for c in candidates:
            if not c.embedding:
                continue
            sim = embeddings_engine.cosine_similarity(embedding, c.embedding)
            if sim >= self.similar_threshold:
                scored_cases.append({
                    "id": c.id,
                    "ticket_number": c.ticket_number or f"CMP-{c.id}",
                    "subject": c.subject,
                    "category": c.category,
                    "department_id": c.department_id,
                    "status": c.status,
                    "similarity": round(float(sim), 4)
                })

        scored_cases.sort(key=lambda x: x["similarity"], reverse=True)
        # Filter by threshold, but always preserve the top match if available
        filtered = [c for c in scored_cases[:top_k] if c["similarity"] >= self.similar_threshold]
        if not filtered and scored_cases:
            filtered = [scored_cases[0]]
        return filtered

    def detect_duplicates(
        self,
        complaint_text: str,
        db: Session,
        embedding: Optional[List[float]] = None,
        current_complaint_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Executes full duplicate detection flow:
        Complaint -> Embedding -> pgvector -> Similarity Search -> Similar Complaints
        Returns:
        matched_complaint_id
        similarity_score
        Display: "Possible duplicate complaint" if similarity >= threshold (e.g. 0.91)
        """
        if not embedding:
            embedding = embeddings_engine.get_embedding(complaint_text)

        similar_complaints = self.search_similar_complaints(
            db=db,
            embedding=embedding,
            current_complaint_id=current_complaint_id
        )

        top_match = similar_complaints[0] if similar_complaints else None
        top_score = top_match["similarity"] if top_match else 0.0

        is_duplicate = top_score >= self.duplicate_threshold
        matched_complaint_id = top_match["id"] if top_match else None
        duplicate_of_id = top_match["id"] if (is_duplicate and top_match) else None

        display_warning = "Possible duplicate complaint" if is_duplicate else None

        return {
            "engine": "Sentence Transformers + pgvector",
            "is_duplicate": is_duplicate,
            "matched_complaint_id": matched_complaint_id,
            "similarity_score": top_score,
            "display_warning": display_warning,
            "duplicate_of_id": duplicate_of_id,
            "status": "POSSIBLE" if is_duplicate else "NONE",
            "similar_complaints": similar_complaints
        }


# =============================================================================
# 3. Unified Duplicate Detection Facade
# =============================================================================
class DuplicateDetector:
    """Unified detector coordinating Sentence Transformers + pgvector with TF-IDF baseline."""

    def __init__(self):
        self.baseline_engine = TFIDFBaselineDuplicateDetector()
        self.primary_engine = SentenceTransformerPgVectorDuplicateDetector()

    def detect_similar_and_duplicates(
        self,
        new_embedding: Optional[List[float]],
        db: Session,
        current_complaint_id: Optional[int] = None,
        duplicate_threshold: float = 0.85,
        similar_threshold: float = 0.65,
        complaint_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Primary interface invoked by AI Orchestrator and Complaint Service."""
        self.primary_engine.duplicate_threshold = duplicate_threshold
        self.primary_engine.similar_threshold = similar_threshold

        if not new_embedding and complaint_text:
            new_embedding = embeddings_engine.get_embedding(complaint_text)

        if not new_embedding:
            return {
                "is_duplicate": False,
                "duplicate_of_id": None,
                "matched_complaint_id": None,
                "similarity_score": 0.0,
                "display_warning": None,
                "status": "NONE",
                "similar_complaints": []
            }

        res = self.primary_engine.detect_duplicates(
            complaint_text=complaint_text or "",
            db=db,
            embedding=new_embedding,
            current_complaint_id=current_complaint_id
        )

        return res

    def compare_with_baseline(
        self,
        query_text: str,
        db: Session,
        current_complaint_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Compares primary Sentence Transformers + pgvector against TF-IDF baseline."""
        primary_res = self.primary_engine.detect_duplicates(
            complaint_text=query_text,
            db=db,
            current_complaint_id=current_complaint_id
        )
        baseline_res = self.baseline_engine.detect_duplicates(
            query_text=query_text,
            db=db,
            current_complaint_id=current_complaint_id
        )

        return {
            "query_text": query_text,
            "primary": primary_res,
            "baseline": baseline_res,
            "comparison": {
                "primary_score": primary_res["similarity_score"],
                "baseline_score": baseline_res["similarity_score"],
                "score_delta": round(primary_res["similarity_score"] - baseline_res["similarity_score"], 4),
                "agreement": primary_res["is_duplicate"] == baseline_res["is_duplicate"]
            }
        }

duplicate_detector = DuplicateDetector()
