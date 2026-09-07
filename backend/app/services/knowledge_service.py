import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.knowledge import KnowledgeDocument, KnowledgeChunk
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
    """Enterprise RAG Knowledge Base Service implementing the 9-stage pipeline:
    Document Upload -> Text Extraction -> Cleaning -> Chunking -> Sentence Transformer ->
    Embedding -> pgvector -> Semantic Retrieval -> Relevant Context -> Ollama/Groq -> Grounded Answer.
    """

    @staticmethod
    def get_supported_document_types() -> List[Dict[str, str]]:
        """Returns the 9 officially supported document types."""
        return SUPPORTED_DOCUMENT_TYPES

    @staticmethod
    def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
        """Stage 2: Text Extraction from raw uploaded file bytes (.txt, .md, .json, .csv, plain text)."""
        if not file_bytes:
            return ""

        fn_lower = filename.lower()
        try:
            # Decode text from UTF-8 or Latin-1
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = file_bytes.decode("latin-1")
            except Exception as e:
                logger.warning(f"Error decoding file {filename}: {e}")
                text = str(file_bytes)

        # Basic JSON unwrapping if file is JSON
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
        """Stage 3: Cleaning text - normalizes whitespace and removes noise while preserving
        markdown section titles, bullet lists, numeric tables, and legal/policy codes.
        """
        if not raw_text:
            return ""

        # Normalize line endings
        text = raw_text.replace("\r\n", "\n").replace("\r", "\n")

        # Strip unprintable control characters except tabs and newlines
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)

        # Replace excessive consecutive newlines with double newline (paragraph boundary)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Normalize horizontal whitespace (multiple spaces/tabs to single space) on each line
        lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in text.split('\n')]
        cleaned = '\n'.join(lines).strip()

        return cleaned

    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = 500,
        chunk_overlap: int = 80
    ) -> List[str]:
        """Stage 4: Semantic Chunking with sliding overlap.
        Splits text into logical chunks respecting sentence and paragraph boundaries.
        """
        if not text:
            return []

        # If text is already shorter than chunk size, return single chunk
        if len(text) <= chunk_size:
            return [text]

        # Break text by paragraphs or double newlines first
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""

        for p in paragraphs:
            p = p.strip()
            if not p:
                continue

            # If adding paragraph exceeds chunk size, try splitting sentences
            if len(current_chunk) + len(p) + 2 > chunk_size and len(current_chunk) >= (chunk_size - chunk_overlap):
                chunks.append(current_chunk.strip())
                # Sliding overlap: carry over trailing words
                overlap_text = current_chunk[-chunk_overlap:].strip()
                current_chunk = overlap_text + " " + p if overlap_text else p
            else:
                current_chunk = (current_chunk + "\n\n" + p).strip() if current_chunk else p

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        # Fallback if any single chunk is excessively large (no paragraph breaks)
        final_chunks = []
        for c in chunks:
            if len(c) > (chunk_size * 2):
                # Split by sentence boundaries (.!?)
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
        title: str,
        document_type: str,
        content_text: str,
        category: Optional[str] = None,
        department_id: Optional[int] = None
    ) -> KnowledgeDocument:
        """Executes the complete ingestion pipeline:
        Cleaning -> Chunking -> Sentence Transformer -> Embedding -> pgvector/DB Persistence.
        """
        # Step 1: Clean
        cleaned = cls.clean_text(content_text)

        # Step 2: Chunk
        chunks = cls.chunk_text(cleaned, chunk_size=500, chunk_overlap=80)
        if not chunks:
            chunks = [cleaned[:500] if cleaned else title]

        # Step 3 & 4: Sentence Transformer Embeddings for Chunks (384-d dense vector)
        doc_header = f"{title} [{document_type}]"
        primary_chunk = chunks[0]
        primary_vector = embeddings_engine.get_embedding(f"{doc_header}\n{primary_chunk}")

        # Resolve category and department defaults if not provided
        resolved_category = category
        if not resolved_category:
            for s in SUPPORTED_DOCUMENT_TYPES:
                if s["type"] == document_type:
                    resolved_category = s["category"]
                    break
        resolved_category = resolved_category or "Corporate Policy"

        # Step 5: pgvector/DB Persistence for Document Header
        doc = KnowledgeDocument(
            title=title,
            category=resolved_category,
            document_type=document_type,
            content_text=cleaned,
            chunk_index=0,
            chunk_text=primary_chunk,
            embedding=primary_vector,
            department_id=department_id,
            is_active=True
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Persist granular KnowledgeChunk records with individual 384d embeddings
        chunk_objects = []
        for idx, chunk_str in enumerate(chunks):
            chunk_vector = embeddings_engine.get_embedding(f"{doc_header}\n{chunk_str}")
            chunk_obj = KnowledgeChunk(
                document_id=doc.id,
                chunk_index=idx,
                chunk_text=chunk_str,
                embedding=chunk_vector,
                token_count=len(chunk_str.split())
            )
            chunk_objects.append(chunk_obj)

        db.add_all(chunk_objects)
        db.commit()
        db.refresh(doc)

        logger.info(f"Ingested KnowledgeDocument '{title}' ({document_type}) with {len(chunks)} chunks.")
        return doc

    @classmethod
    def seed_default_knowledge_base(cls, db: Session) -> int:
        """Seeds the 9 official enterprise policy documents if they are not already present."""
        existing_titles = {d.title for d in db.query(KnowledgeDocument.title).all()}
        seeded_count = 0

        for pol in SEED_POLICIES:
            existing_doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.title == pol["title"]).first()
            if existing_doc:
                c_count = db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == existing_doc.id).count()
                if c_count == 0:
                    cleaned = cls.clean_text(existing_doc.content_text)
                    chunks = cls.chunk_text(cleaned, chunk_size=500, chunk_overlap=80)
                    doc_header = f"{existing_doc.title} [{existing_doc.document_type}]"
                    for idx, chunk_str in enumerate(chunks):
                        chunk_vector = embeddings_engine.get_embedding(f"{doc_header}\n{chunk_str}")
                        db.add(KnowledgeChunk(
                            document_id=existing_doc.id,
                            chunk_index=idx,
                            chunk_text=chunk_str,
                            embedding=chunk_vector,
                            token_count=len(chunk_str.split())
                        ))
                    db.commit()
                continue

            cls.ingest_document(
                db=db,
                title=pol["title"],
                document_type=pol["document_type"],
                content_text=pol["content_text"],
                category=pol["category"]
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
        """Stage 7: Semantic Retrieval across granular chunks using Sentence Transformer cosine similarity."""
        query_vector = embeddings_engine.get_embedding(query)

        # Query active chunks joined with parent document
        q = db.query(KnowledgeChunk, KnowledgeDocument).join(
            KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id
        ).filter(KnowledgeDocument.is_active == True)

        if document_type:
            q = q.filter(KnowledgeDocument.document_type == document_type)

        results = q.all()
        scored = []

        for chunk, doc in results:
            if not chunk.embedding:
                continue
            sim = embeddings_engine.cosine_similarity(query_vector, chunk.embedding)
            if sim >= min_similarity:
                scored.append({
                    "chunk_id": chunk.id,
                    "document_id": doc.id,
                    "document_title": doc.title,
                    "document_type": doc.document_type,
                    "category": doc.category,
                    "chunk_index": chunk.chunk_index,
                    "chunk_text": chunk.chunk_text,
                    "similarity_score": round(sim, 4)
                })

        scored.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored[:limit]

knowledge_service = KnowledgeService()
