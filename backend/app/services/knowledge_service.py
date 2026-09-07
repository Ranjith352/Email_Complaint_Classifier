import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.knowledge import KnowledgeDocument, KnowledgeChunk, ChunkEmbedding
from app.ai.embeddings import embeddings_engine

logger = logging.getLogger(__name__)

# The 9 official supported enterprise document types
SUPPORTED_DOCUMENT_TYPES = [
    {
        "type": "REFUND_POLICY",
        "name": "Refund Policy",
        "category": "Billing / Payment",
        "department": "Finance",
        "description": "Rules, eligibility windows, and processing timelines for customer refunds and reversals."
    },
    {
        "type": "BILLING_POLICY",
        "name": "Billing Policy",
        "category": "Billing / Payment",
        "department": "Finance",
        "description": "Invoicing cycles, charge dispute workflows, payment gateways, and recurring subscriptions."
    },
    {
        "type": "CUSTOMER_SUPPORT_SOP",
        "name": "Customer Support SOP",
        "category": "Customer Support",
        "department": "Customer Support",
        "description": "Standard operating procedures for customer inquiry intake, tone, and resolution etiquette."
    },
    {
        "type": "SLA_POLICY",
        "name": "SLA Policy",
        "category": "Operations & Admin",
        "department": "Customer Support",
        "description": "Service Level Agreement tiers, first-response deadlines, and resolution target times (P1 to P4)."
    },
    {
        "type": "ESCALATION_POLICY",
        "name": "Escalation Policy",
        "category": "Operations & Admin",
        "department": "Customer Support",
        "description": "Criteria and tier hierarchies for transferring tickets to supervisors and engineering leads."
    },
    {
        "type": "IT_TROUBLESHOOTING_GUIDE",
        "name": "IT Troubleshooting Guide",
        "category": "Technical Problem",
        "department": "IT Support",
        "description": "Diagnostic steps for portal outages, authentication 500 errors, VPN, and account access."
    },
    {
        "type": "SECURITY_POLICY",
        "name": "Security Policy",
        "category": "Security Issue",
        "department": "Security & Compliance",
        "description": "Data privacy safeguards, credential compromise handling, 2FA protocols, and breach reporting."
    },
    {
        "type": "HR_POLICY",
        "name": "HR Policy",
        "category": "Human Resources",
        "department": "Human Resources",
        "description": "Workplace code of conduct, agent scheduling rules, grievance handling, and ethics policies."
    },
    {
        "type": "FINANCE_POLICY",
        "name": "Finance Policy",
        "category": "Finance Ops",
        "department": "Finance",
        "description": "Corporate audit standards, high-value reimbursement authorizations, and chargeback reconciliation."
    }
]

# Comprehensive Seed Corpus for the 9 Supported Policies
SEED_POLICIES = [
    {
        "title": "Corporate Refund & Reversal Policy",
        "document_type": "REFUND_POLICY",
        "category": "Billing / Payment",
        "department": "Finance",
        "content_text": """# Corporate Refund & Reversal Policy

## 1. Overview and Scope
This policy governs all refund and reversal requests submitted by customers across digital channels, web subscriptions, and automated payment gateways.

## 2. Eligibility Windows & Criteria
- **Duplicate Charges & Erroneous Deductions**: Customers reporting duplicate billing or identical debits within 30 days are entitled to an immediate 100% unconditional refund.
- **Service Non-Delivery & Downtime**: If customer accounts experience unplanned outages exceeding 24 consecutive hours, prorated subscription credits or full monthly refunds will be approved.
- **Buyer's Remorse / Cancellation**: Subscription cancellation requests submitted within 7 business days of renewal qualify for full refund minus processing fees.

## 3. Processing Timelines & Gateways
- **Instant Gateway Reversals**: Payments processed via UPI, NetBanking, or Debit Cards are initiated within 4 hours and settle in 2 to 5 business days.
- **Credit Card Chargebacks**: Processed in accordance with card network guidelines within 5 to 7 business days.
- **Customer Notification**: Automated email receipts and SMS confirmations containing the transaction refund reference ID must be issued immediately upon trigger.

## 4. Required Documentation
Agents must verify:
1. Customer Account ID / Registered Email.
2. Gateway Transaction Reference Number (e.g. TXN-123456).
3. Timestamp and deducted amount in local currency (e.g. ₹5,000)."""
    },
    {
        "title": "Customer Billing & Subscription Policy",
        "document_type": "BILLING_POLICY",
        "category": "Billing / Payment",
        "department": "Finance",
        "content_text": """# Customer Billing & Subscription Policy

## 1. Billing Cycles & Invoicing
All recurring service charges are billed on the 1st day of the calendar month or on the anniversary date of account activation. Tax invoices are delivered via email within 24 hours of successful debit.

## 2. Failed Transactions & Grace Period
- When an automated subscription payment fails, our retry system executes up to 3 automated retries over 72 hours.
- A 5-day grace period is granted to customers before account suspension or feature downgrades.
- Support agents must contact customers experiencing repeated payment gateway 402 errors to offer alternative payment links.

## 3. Disputed Charges & Overbilling
- Customers disputing an invoice must submit an inquiry within 60 calendar days of invoice date.
- The Billing Operations team must pause automated collection workflows while an active dispute investigation is underway.
- If overbilling is confirmed due to calculation or tariff glitches, immediate credit adjustment is applied to the next billing cycle or refunded directly."""
    },
    {
        "title": "Customer Support Standard Operating Procedure (SOP)",
        "document_type": "CUSTOMER_SUPPORT_SOP",
        "category": "Customer Support",
        "department": "Customer Support",
        "content_text": """# Customer Support Standard Operating Procedure (SOP)

## 1. Customer Interaction & Etiquette Guidelines
Customer service representatives represent AutoTriage AI and must adhere to empathetic, courteous, and professional communication at all times.
- Greet customers by name with warmth and acknowledge their frustration immediately.
- Never use defensive or dismissive language regarding system errors.
- Always provide realistic timelines and transparent progress updates.

## 2. Triage & Ticket Intake Workflow
1. **Verification**: Confirm customer identity via registered email, customer ID, or phone number.
2. **Categorization**: Ensure AI category, sentiment, and urgency annotations accurately reflect the customer narrative.
3. **Internal Documentation**: Record root cause hypotheses and customer expectations in private notes before routing.

## 3. Resolution Verification & Follow-Up
- Verify that customer issues are completely resolved in staging or production before moving tickets to RESOLVED status.
- Solicit customer feedback (1-5 star CSAT score) within 24 hours of ticket closure."""
    },
    {
        "title": "Service Level Agreement (SLA) & Response Policy",
        "document_type": "SLA_POLICY",
        "category": "Operations & Admin",
        "department": "Customer Support",
        "content_text": """# Service Level Agreement (SLA) & Response Policy

## 1. Priority Tiers and Response Targets
AutoTriage AI operates 24/7/365 multi-tier SLA commitments defined by priority scores:
- **P1 - CRITICAL (Priority 81-100)**:
  - First Response Time: Under 15 minutes.
  - Resolution Target: Under 4 hours.
  - Coverage: Production outages, severe security incidents, portal authentication lockouts.
- **P2 - HIGH (Priority 61-80)**:
  - First Response Time: Under 1 hour.
  - Resolution Target: Under 8 hours.
  - Coverage: Duplicate billing deductions, VIP account issues, major feature degradation.
- **P3 - MEDIUM (Priority 31-60)**:
  - First Response Time: Under 4 hours.
  - Resolution Target: Under 24 hours.
  - Coverage: General technical bugs, account configuration, non-urgent payment questions.
- **P4 - LOW (Priority 0-30)**:
  - First Response Time: Under 12 hours.
  - Resolution Target: Under 48 hours.
  - Coverage: Feature requests, documentation clarification, feedback inquiries.

## 2. SLA Breach Prevention & Auto-Alerts
When tickets reach 75% of their SLA deadline without first response or resolution, automated escalation triggers notify team managers and re-prioritize ticket placement in agent queues."""
    },
    {
        "title": "Incident Escalation & Hierarchy Policy",
        "document_type": "ESCALATION_POLICY",
        "category": "Operations & Admin",
        "department": "Customer Support",
        "content_text": """# Incident Escalation & Hierarchy Policy

## 1. Escalation Thresholds
Tickets must be escalated when:
1. First contact resolution is unachievable within Tier-1 team capabilities.
2. The customer expresses intent to initiate legal action or file regulatory complaints.
3. Repeated identical complaints exceed incident detection thresholds (e.g. 10+ similar portal failure reports within 1 hour).
4. SLA remaining time drops below 30 minutes without active resolution in progress.

## 2. Tier Hierarchy & Handoff
- **Tier 1 (Frontline Agents)**: Initial ingestion, identity verification, general refunds under ₹10,000, and standard SOP guidance.
- **Tier 2 (Senior Specialists & Team Leads)**: High-value refunds (₹10,000 - ₹100,000), complex technical troubleshooting, and priority customer care.
- **Tier 3 (Engineering & Operations Directors)**: Platform outages, database corruption, security compromises, and executive complaints.

## 3. Escalation Handoff Checklist
The escalating agent must summarize:
- Root cause identified to date.
- Steps already attempted and customer reactions.
- Explicit action requested from the escalation assignee."""
    },
    {
        "title": "IT Application & Infrastructure Troubleshooting Guide",
        "document_type": "IT_TROUBLESHOOTING_GUIDE",
        "category": "Technical Problem",
        "department": "IT Support",
        "content_text": """# IT Application & Infrastructure Troubleshooting Guide

## 1. Web Portal 500 Internal Server Errors & Authentication Failures
- **Symptoms**: Customer reports 'Cannot login', 'Portal is not working', or 'HTTP 500 error on checkout'.
- **Diagnostic Steps**:
  1. Check status of auth service cluster and Redis session store.
  2. Inspect database connection pool health and active connection saturation.
  3. Verify JWT token signature validity and expiry timestamps.
  4. Instruct user to clear browser local storage and cookies or attempt login via Incognito mode.

## 2. Payment Gateway Timeout & Callback Errors
- **Symptoms**: Money debited from customer bank account but order status remains 'Pending' or 'Failed'.
- **Diagnostic Steps**:
  1. Query payment gateway webhook delivery logs for missing event receipts.
  2. Trigger manual transaction status poll against merchant bank API.
  3. If bank reports 'SUCCESS' but internal state is 'FAILED', trigger idempotent reconciler script."""
    },
    {
        "title": "Information Security & Data Privacy Policy",
        "document_type": "SECURITY_POLICY",
        "category": "Security Issue",
        "department": "Security & Compliance",
        "content_text": """# Information Security & Data Privacy Policy

## 1. Data Protection & Confidentiality
Customer Personally Identifiable Information (PII)—including names, email addresses, phone numbers, and payment credentials—must be protected in compliance with global data privacy standards (GDPR, ISO 27001).
- All PII stored in databases must be encrypted at rest (AES-256) and in transit (TLS 1.3).
- Support agents must never request full credit card numbers or account passwords over chat or email.

## 2. Compromised Account Containment Protocol
Upon report or suspicion of unauthorized account access:
1. **Immediate Invalidation**: Revoke all active session tokens and terminate active OAuth credentials immediately.
2. **Access Lockout**: Place account in temporary security containment mode.
3. **Identity Challenge**: Authenticate customer via out-of-band verified secondary communication channel before issuing password reset links.
4. **Audit Logging**: Preserve all IP access logs, geolocation headers, and audit trails for digital forensics."""
    },
    {
        "title": "Human Resources Workplace & Agent Conduct Policy",
        "document_type": "HR_POLICY",
        "category": "Human Resources",
        "department": "Human Resources",
        "content_text": """# Human Resources Workplace & Agent Conduct Policy

## 1. Agent Workload & Wellness Standards
To ensure consistent support quality and employee well-being:
- Full-time customer support agents have a maximum active workload cap of 10 concurrent high-priority tickets.
- Mandatory 15-minute wellness breaks are scheduled after every 2 hours of continuous frontline queue handling.
- Overtime shifts must receive prior managerial authorization.

## 2. Workplace Ethics & Non-Discrimination
- Zero tolerance for harassment, discrimination, or abusive conduct toward colleagues or customers.
- Customer communications must remain strictly neutral, objective, and supportive regardless of customer demeanor.

## 3. Internal Grievance Resolution Workflow
- Agents experiencing unfair workload distribution or workplace grievances may submit confidential reports directly to HR.
- HR mediation begins within 48 hours of ticket submission with guaranteed non-retaliation protection."""
    },
    {
        "title": "Corporate Finance & Fiscal Governance Policy",
        "document_type": "FINANCE_POLICY",
        "category": "Finance Ops",
        "department": "Finance",
        "content_text": """# Corporate Finance & Fiscal Governance Policy

## 1. Financial Authorization Matrix
Disbursements, compensation payments, and goodwill refunds must satisfy internal delegation of authority:
- Tier-1 Agents: Authorized up to ₹5,000 per incident.
- Team Leads / Supervisors: Authorized up to ₹25,000 per incident.
- Department Heads (Finance/Ops): Authorized up to ₹100,000 per incident.
- CFO / Executive Approval: Required for any settlement exceeding ₹100,000.

## 2. Chargeback & Reconciliation Operations
- Weekly reconciliation between merchant bank statements and internal ledger records is mandatory.
- Unidentified chargeback notifications must be investigated within 3 business days to prevent merchant payment processor penalties.
- All goodwill fee waivers must be accompanied by verified ticket audit trails."""
    }
]

class KnowledgeService:
    """Enterprise RAG Knowledge Base Service implementing Admin Lifecycle & Separate Storage:
    1. Document Upload, View, Update, Delete, Re-index
    2. Store metadata: document name, document type, department, version, uploaded_by, created_at
    3. Separate storage: KnowledgeDocument (metadata) | KnowledgeChunk (text chunks) | ChunkEmbedding (vectors).
    """

    @staticmethod
    def get_supported_document_types() -> List[Dict[str, str]]:
        return SUPPORTED_DOCUMENT_TYPES

    @staticmethod
    def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
        if not file_bytes:
            return ""

        fn_lower = filename.lower()
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = file_bytes.decode("latin-1")
            except Exception as e:
                logger.warning(f"Error decoding file {filename}: {e}")
                text = str(file_bytes)

        if fn_lower.endswith(".json"):
            try:
                import json
                data = json.loads(text)
                if isinstance(data, dict):
                    text = data.get("content", data.get("text", data.get("body", text)))
                elif isinstance(data, list):
                    text = "\n".join([str(item) for item in data])
            except Exception:
                pass

        return text

    @staticmethod
    def clean_text(raw_text: str) -> str:
        if not raw_text:
            return ""

        text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in text.split('\n')]
        return '\n'.join(lines).strip()

    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = 500,
        chunk_overlap: int = 80
    ) -> List[str]:
        if not text:
            return []

        if len(text) <= chunk_size:
            return [text]

        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""

        for p in paragraphs:
            p = p.strip()
            if not p:
                continue

            if len(current_chunk) + len(p) + 2 > chunk_size and len(current_chunk) >= (chunk_size - chunk_overlap):
                chunks.append(current_chunk.strip())
                overlap_text = current_chunk[-chunk_overlap:].strip()
                current_chunk = overlap_text + " " + p if overlap_text else p
            else:
                current_chunk = (current_chunk + "\n\n" + p).strip() if current_chunk else p

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        final_chunks = []
        for c in chunks:
            if len(c) > (chunk_size * 2):
                sentences = re.split(r'(?<=[.!?])\s+', c)
                sub_chunk = ""
                for s in sentences:
                    if len(sub_chunk) + len(s) + 1 > chunk_size and len(sub_chunk) > 0:
                        final_chunks.append(sub_chunk.strip())
                        sub_chunk = s
                    else:
                        sub_chunk = (sub_chunk + " " + s).strip()
                if sub_chunk.strip():
                    final_chunks.append(sub_chunk.strip())
            else:
                final_chunks.append(c)

        return [fc for fc in final_chunks if len(fc.strip()) >= 15]

    @classmethod
    def ingest_document(
        cls,
        db: Session,
        title: Optional[str] = None,
        document_name: Optional[str] = None,
        document_type: str = "REFUND_POLICY",
        content_text: str = "",
        category: Optional[str] = None,
        department: Optional[str] = None,
        department_id: Optional[int] = None,
        uploaded_by: str = "Admin",
        version: int = 1
    ) -> KnowledgeDocument:
        """Upload & Ingestion Pipeline storing Document, Chunks, and Embeddings separately."""
        final_name = (document_name or title or "Untitled Document").strip()

        # Step 1: Clean
        cleaned = cls.clean_text(content_text)

        # Step 2: Chunk
        chunks = cls.chunk_text(cleaned, chunk_size=500, chunk_overlap=80)
        if not chunks:
            chunks = [cleaned[:500] if cleaned else final_name]

        # Resolve category & department
        resolved_category = category
        resolved_department = department
        if not resolved_category or not resolved_department:
            for s in SUPPORTED_DOCUMENT_TYPES:
                if s["type"] == document_type:
                    resolved_category = resolved_category or s["category"]
                    resolved_department = resolved_department or s["department"]
                    break
        resolved_category = resolved_category or "Corporate Policy"
        resolved_department = resolved_department or "General"

        # Step 3: Document Header Embedding
        doc_header = f"{final_name} [{document_type}] ({resolved_department})"
        primary_chunk = chunks[0]
        primary_vector = embeddings_engine.get_embedding(f"{doc_header}\n{primary_chunk}")

        # Step 4: Persist KnowledgeDocument (metadata & raw text)
        doc = KnowledgeDocument(
            title=final_name,
            category=resolved_category,
            document_type=document_type,
            department=resolved_department,
            department_id=department_id,
            version=version,
            uploaded_by=uploaded_by or "Admin",
            content_text=cleaned,
            chunk_index=0,
            chunk_text=primary_chunk,
            embedding=primary_vector,
            is_active=True
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Step 5 & 6: Persist KnowledgeChunks and ChunkEmbeddings separately
        for idx, chunk_str in enumerate(chunks):
            chunk_obj = KnowledgeChunk(
                document_id=doc.id,
                chunk_index=idx,
                chunk_text=chunk_str,
                token_count=len(chunk_str.split()),
                embedding=None  # Maintained as None in chunks table; stored in dedicated ChunkEmbedding
            )
            db.add(chunk_obj)
            db.commit()
            db.refresh(chunk_obj)

            # Generate 384d vector and store in dedicated ChunkEmbedding table
            chunk_vector = embeddings_engine.get_embedding(f"{doc_header}\n{chunk_str}")
            chunk_obj.embedding = chunk_vector  # keep on chunk for transparent backwards compatibility
            
            chunk_emb = ChunkEmbedding(
                chunk_id=chunk_obj.id,
                document_id=doc.id,
                embedding=chunk_vector,
                model_name="all-MiniLM-L6-v2",
                dimension=384
            )
            db.add(chunk_emb)

        db.commit()
        db.refresh(doc)
        logger.info(f"Ingested '{final_name}' v{doc.version} by '{doc.uploaded_by}' with {len(chunks)} chunks and separate embeddings.")
        return doc

    @classmethod
    def update_document(
        cls,
        db: Session,
        doc_id: int,
        document_name: Optional[str] = None,
        title: Optional[str] = None,
        document_type: Optional[str] = None,
        category: Optional[str] = None,
        department: Optional[str] = None,
        content_text: Optional[str] = None,
        uploaded_by: Optional[str] = None,
        reindex: bool = True
    ) -> KnowledgeDocument:
        """Admin Update: Updates document metadata and content, optionally re-indexing chunks and embeddings."""
        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
        if not doc:
            raise ValueError("Knowledge document not found")

        new_name = (document_name or title)
        if new_name:
            doc.title = new_name.strip()
        if document_type:
            doc.document_type = document_type
        if category:
            doc.category = category
        if department:
            doc.department = department
        if uploaded_by:
            doc.uploaded_by = uploaded_by

        content_changed = False
        if content_text is not None and content_text.strip() != doc.content_text.strip():
            doc.content_text = content_text
            content_changed = True

        doc.version += 1
        doc.updated_at = datetime.utcnow()
        db.commit()

        if reindex or content_changed:
            cls.reindex_document(db, doc.id, bump_version=False)

        db.refresh(doc)
        return doc

    @classmethod
    def reindex_document(cls, db: Session, doc_id: int, bump_version: bool = True) -> KnowledgeDocument:
        """Admin Re-index: Cleans text, re-chunks, recalculates Sentence Transformer vectors,
        refreshes dedicated ChunkEmbedding table, and optionally increments document version.
        """
        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
        if not doc:
            raise ValueError("Knowledge document not found")

        # Delete existing separate embeddings and chunks for this document
        db.query(ChunkEmbedding).filter(ChunkEmbedding.document_id == doc.id).delete()
        db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == doc.id).delete()
        db.commit()

        # Re-clean and re-chunk
        cleaned = cls.clean_text(doc.content_text)
        doc.content_text = cleaned
        chunks = cls.chunk_text(cleaned, chunk_size=500, chunk_overlap=80)
        if not chunks:
            chunks = [cleaned[:500] if cleaned else doc.title]

        doc_header = f"{doc.title} [{doc.document_type}] ({doc.department})"
        doc.chunk_text = chunks[0]
        doc.embedding = embeddings_engine.get_embedding(f"{doc_header}\n{chunks[0]}")

        if bump_version:
            doc.version += 1
        doc.updated_at = datetime.utcnow()
        db.commit()

        # Recreate chunks and separate embeddings
        for idx, chunk_str in enumerate(chunks):
            chunk_obj = KnowledgeChunk(
                document_id=doc.id,
                chunk_index=idx,
                chunk_text=chunk_str,
                token_count=len(chunk_str.split()),
                embedding=None
            )
            db.add(chunk_obj)
            db.commit()
            db.refresh(chunk_obj)

            chunk_vector = embeddings_engine.get_embedding(f"{doc_header}\n{chunk_str}")
            chunk_obj.embedding = chunk_vector

            chunk_emb = ChunkEmbedding(
                chunk_id=chunk_obj.id,
                document_id=doc.id,
                embedding=chunk_vector,
                model_name="all-MiniLM-L6-v2",
                dimension=384
            )
            db.add(chunk_emb)

        db.commit()
        db.refresh(doc)
        logger.info(f"Re-indexed KnowledgeDocument '{doc.title}' to v{doc.version} with {len(chunks)} chunks and embeddings.")
        return doc

    @classmethod
    def seed_default_knowledge_base(cls, db: Session) -> int:
        """Seeds the 9 official enterprise policy documents with separate chunks and embeddings."""
        seeded_count = 0

        for pol in SEED_POLICIES:
            existing_doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.title == pol["title"]).first()
            if existing_doc:
                # Ensure department, version, and uploaded_by are set
                if not existing_doc.department:
                    existing_doc.department = pol.get("department", "General")
                if not existing_doc.uploaded_by:
                    existing_doc.uploaded_by = "System Seed"
                db.commit()

                # Verify chunks and separate embeddings exist
                c_count = db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == existing_doc.id).count()
                e_count = db.query(ChunkEmbedding).filter(ChunkEmbedding.document_id == existing_doc.id).count()
                if c_count == 0 or e_count == 0:
                    cls.reindex_document(db, existing_doc.id, bump_version=False)
                continue

            cls.ingest_document(
                db=db,
                title=pol["title"],
                document_type=pol["document_type"],
                content_text=pol["content_text"],
                category=pol["category"],
                department=pol.get("department", "General"),
                uploaded_by="System Seed",
                version=1
            )
            seeded_count += 1

        if seeded_count > 0:
            logger.info(f"Seeded {seeded_count} official company knowledge base documents.")
        return seeded_count

    @classmethod
    def semantic_retrieve_chunks(
        cls,
        query: str,
        db: Session,
        limit: int = 4,
        min_similarity: float = 0.35,
        document_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Semantic Retrieval across separate ChunkEmbedding records."""
        query_vector = embeddings_engine.get_embedding(query)

        # Primary: Join ChunkEmbedding with KnowledgeChunk and KnowledgeDocument
        q = db.query(ChunkEmbedding, KnowledgeChunk, KnowledgeDocument).join(
            KnowledgeChunk, ChunkEmbedding.chunk_id == KnowledgeChunk.id
        ).join(
            KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id
        ).filter(KnowledgeDocument.is_active == True)

        if document_type:
            q = q.filter(KnowledgeDocument.document_type == document_type)

        results = q.all()
        scored = []

        for emb, chunk, doc in results:
            if not emb.embedding:
                continue
            sim = embeddings_engine.cosine_similarity(query_vector, emb.embedding)
            if sim >= min_similarity:
                scored.append({
                    "chunk_id": chunk.id,
                    "document_id": doc.id,
                    "document_title": doc.title,
                    "document_name": doc.title,
                    "document_type": doc.document_type,
                    "department": doc.department,
                    "version": doc.version,
                    "category": doc.category,
                    "chunk_index": chunk.chunk_index,
                    "chunk_text": chunk.chunk_text,
                    "similarity_score": round(sim, 4)
                })

        # Fallback if separate embeddings table not populated yet
        if not scored:
            q_chunk = db.query(KnowledgeChunk, KnowledgeDocument).join(
                KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id
            ).filter(KnowledgeDocument.is_active == True)
            if document_type:
                q_chunk = q_chunk.filter(KnowledgeDocument.document_type == document_type)
            for chunk, doc in q_chunk.all():
                if not chunk.embedding:
                    continue
                sim = embeddings_engine.cosine_similarity(query_vector, chunk.embedding)
                if sim >= min_similarity:
                    scored.append({
                        "chunk_id": chunk.id,
                        "document_id": doc.id,
                        "document_title": doc.title,
                        "document_name": doc.title,
                        "document_type": doc.document_type,
                        "department": doc.department,
                        "version": doc.version,
                        "category": doc.category,
                        "chunk_index": chunk.chunk_index,
                        "chunk_text": chunk.chunk_text,
                        "similarity_score": round(sim, 4)
                    })

        scored.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored[:limit]

knowledge_service = KnowledgeService()
