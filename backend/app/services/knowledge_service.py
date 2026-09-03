from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.knowledge import KnowledgeDocument
from app.schemas.knowledge import KnowledgeDocumentCreate
from app.ai.embeddings import embeddings_engine
from app.ai.rag import rag_engine

class KnowledgeService:
    @staticmethod
    def create_document(db: Session, doc_in: KnowledgeDocumentCreate) -> KnowledgeDocument:
        """Embeds document content into 384d dense vector and persists to knowledge_documents table."""
        chunk_text = doc_in.content_text[:1000]
        embedding = embeddings_engine.get_embedding(f"{doc_in.title} {doc_in.category} {chunk_text}")

        doc = KnowledgeDocument(
            title=doc_in.title,
            category=doc_in.category,
            document_type=doc_in.document_type,
            content_text=doc_in.content_text,
            chunk_index=0,
            chunk_text=chunk_text,
            embedding=embedding,
            department_id=doc_in.department_id
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def query_rag(db: Session, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Retrieves semantic policy matches using dense vector cosine similarity."""
        return rag_engine.retrieve_relevant_policies(query, db, limit=limit)

knowledge_service = KnowledgeService()
