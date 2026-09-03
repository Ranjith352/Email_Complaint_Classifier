import re
import time
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.ai.preprocessing import preprocessor
from app.ai.classifier import classifier
from app.ai.sentiment import sentiment_analyzer
from app.ai.emotion import emotion_detector
from app.ai.ner import ner_extractor
from app.ai.urgency import urgency_detector
from app.ai.priority import priority_calculator
from app.ai.embeddings import embeddings_engine
from app.ai.duplicate_detector import duplicate_detector
from app.ai.summarizer import summarizer
from app.ai.rag import rag_engine
from app.ai.response_generator import response_generator

logger = logging.getLogger(__name__)

class AIOrchestrator:
    """Coordinates the comprehensive 13-stage AI triage and intelligence analysis pipeline:
    1. Text preprocessing (HTML, signatures, quotes, URLs, whitespace, punctuation, deduplication)
    2. Language detection
    3. Classification (Category & Sub-category)
    4. Sentiment analysis
    5. Emotion detection
    6. Named Entity Recognition (NER)
    7. Urgency determination
    8. Priority scoring & tiering
    9. Embedding generation (384-dimensional dense vectors)
    10. Duplicate & similarity detection
    11. Executive summarization & pain point extraction
    12. Resolution recommendation & RAG policy grounding
    13. Routing information (Department & Team assignment)
    """

    @classmethod
    async def process_complaint_full(
        cls,
        subject: str,
        body: str,
        customer_name: str,
        ticket_number: str,
        db: Session,
        current_complaint_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Orchestrates all 13 AI analysis stages and returns a structured AI analysis object."""
        start_time = time.time()
        combined_text = f"{subject} {body}".strip()

        # ---------------------------------------------------------
        # 1. Text Preprocessing (HTML, signatures, quotes, URLs, whitespace, normalization, duplicates)
        # ---------------------------------------------------------
        prep_res = preprocessor.preprocess(combined_text)
        original_text = prep_res["original_text"]
        processed_text = prep_res["processed_text"]

        # ---------------------------------------------------------
        # 2. Language Detection
        # ---------------------------------------------------------
        language = prep_res["language"]
        language_name = prep_res["language_name"]

        # ---------------------------------------------------------
        # 3. Category & Sub-category Classification
        # ---------------------------------------------------------
        analysis_input = processed_text if processed_text else combined_text
        class_res = classifier.classify(analysis_input)
        category = class_res["category"]
        sub_category = class_res.get("sub_category", "General")
        confidence = class_res.get("confidence", 0.92)

        # ---------------------------------------------------------
        # 4. Sentiment Analysis (Normalized to uppercase)
        # ---------------------------------------------------------
        sentiment_res = sentiment_analyzer.analyze(combined_text)
        raw_sentiment = sentiment_res.get("sentiment", "Neutral").upper()
        sentiment = "NEGATIVE" if "NEG" in raw_sentiment else ("POSITIVE" if "POS" in raw_sentiment else "NEUTRAL")

        # ---------------------------------------------------------
        # 5. Emotion Detection (Normalized to uppercase)
        # ---------------------------------------------------------
        emotion_res = emotion_detector.detect(combined_text)
        raw_emotion = emotion_res.get("emotion", "Neutral").upper()

        # ---------------------------------------------------------
        # 6. Named Entity Recognition (NER)
        # ---------------------------------------------------------
        entities = ner_extractor.extract_entities(combined_text)

        # ---------------------------------------------------------
        # 7. Urgency Determination (Normalized to uppercase)
        # ---------------------------------------------------------
        urgency_res = urgency_detector.detect(combined_text, category=category)
        raw_urgency = urgency_res.get("urgency", "Medium").upper()

        # ---------------------------------------------------------
        # 8. Business Priority Scoring & Tiering
        # ---------------------------------------------------------
        priority_res = priority_calculator.calculate(
            urgency=urgency_res.get("urgency", "Medium"),
            sentiment=sentiment_res.get("sentiment", "Neutral"),
            entities=entities,
            category=category
        )
        priority_level = priority_res.get("priority_level", "P3")
        priority_score = int(round(priority_res.get("priority_score", 50.0)))
        priority_name = {
            "P1": "CRITICAL",
            "P2": "HIGH",
            "P3": "MEDIUM",
            "P4": "LOW"
        }.get(priority_level, "MEDIUM")

        # ---------------------------------------------------------
        # 9. Dense Semantic Embedding Generation (384-dimensional vector)
        # ---------------------------------------------------------
        embedding = embeddings_engine.get_embedding(combined_text)

        # ---------------------------------------------------------
        # 10. Duplicate Detection & Similar Complaints Search
        # ---------------------------------------------------------
        dup_res = duplicate_detector.detect_similar_and_duplicates(
            new_embedding=embedding,
            db=db,
            current_complaint_id=current_complaint_id
        )

        # ---------------------------------------------------------
        # 11. AI Summarization & Pain Points Extraction
        # ---------------------------------------------------------
        summary_res = await summarizer.summarize(subject, body)

        # ---------------------------------------------------------
        # 12. Resolution Recommendation & RAG Policy Grounding
        # ---------------------------------------------------------
        rag_res = await rag_engine.generate_grounded_recommendation(
            complaint_text=combined_text,
            category=category,
            db=db
        )

        draft_res = await response_generator.generate_draft(
            ticket_number=ticket_number,
            customer_name=customer_name,
            subject=subject,
            body=body,
            department=class_res.get("department", "General Support")
        )

        # ---------------------------------------------------------
        # 13. Routing Information (Department & Team)
        # ---------------------------------------------------------
        department = class_res.get("department", "Customer Support")
        team = class_res.get("team", "General Triage")

        # Human Review Required Flag:
        # Triggered if confidence < 0.75, or priority is CRITICAL with NEGATIVE sentiment
        review_required = (confidence < 0.75) or (priority_name == "CRITICAL" and sentiment == "NEGATIVE")

        execution_time_ms = round((time.time() - start_time) * 1000, 2)

        # Return the comprehensive structured AI analysis object
        return {
            # --- Primary Standard Fields ---
            "category": category,
            "sub_category": sub_category,
            "department": department,
            "team": team,
            "sentiment": sentiment,
            "emotion": raw_emotion,
            "urgency": raw_urgency,
            "priority": priority_name,
            "priority_score": priority_score,
            "confidence": confidence,
            "review_required": review_required,
            "language": language,
            "language_name": language_name,

            # --- Rich Coordination Metadata & Pipeline Artifacts ---
            "original_text": original_text,
            "processed_text": processed_text,
            "cleaned_text": processed_text,
            "entities": entities,
            "embedding": embedding,
            "is_duplicate": dup_res.get("is_duplicate", False),
            "duplicate_of_id": dup_res.get("duplicate_of_id"),
            "similar_complaints": dup_res.get("similar_complaints", []),
            "summary": summary_res.get("summary", ""),
            "key_points": summary_res.get("key_points", []),
            "resolution_recommendation": rag_res.get("recommendation", ""),
            "recommended_steps": rag_res.get("recommended_steps", []),
            "cited_documents": rag_res.get("cited_documents", []),
            "draft_response": draft_res,
            "execution_time_ms": execution_time_ms,

            # --- Backward Compatibility Aliases ---
            "department_name": department,
            "team_name": team,
            "priority_level": priority_level,
            "cat_confidence": confidence,
            "sentiment_score": sentiment_res.get("sentiment_score", 0.0),
            "emotion_score": emotion_res.get("emotion_score", 0.85),
            "urgency_score": urgency_res.get("urgency_score", 50.0)
        }

ai_orchestrator = AIOrchestrator()
