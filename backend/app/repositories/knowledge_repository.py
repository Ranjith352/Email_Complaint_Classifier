from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.knowledge import KnowledgeDocument

class KnowledgeRepository:
    @staticmethod
    def list_all(db: Session, limit: int = 100) -> List[KnowledgeDocument]:
        return db.query(KnowledgeDocument).filter(KnowledgeDocument.is_active == True).limit(limit).all()

    @staticmethod
    def get_by_id(db: Session, doc_id: int) -> Optional[KnowledgeDocument]:
        return db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()

    @staticmethod
    def create(db: Session, doc: KnowledgeDocument) -> KnowledgeDocument:
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

knowledge_repository = KnowledgeRepository()
