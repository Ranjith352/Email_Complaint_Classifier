# AutoTriage AI - Enterprise Complaint Classification, Routing & Resolution Platform

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18.2-61DAFB.svg)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC.svg)](https://tailwindcss.com/)
[![PostgreSQL & pgvector](https://img.shields.io/badge/Database-PostgreSQL_%2B_pgvector-336791.svg)](https://github.com/pgvector/pgvector)
[![Pytest Suite](https://img.shields.io/badge/Testing-135%20Passed-brightgreen.svg)](https://pytest.org/)

An enterprise-grade, end-to-end AI platform that automates customer complaint ingestion from Gmail, performs multi-level taxonomy classification, executes Hugging Face sentiment and configurable emotion analysis, extracts 10 core entity types with Named Entity Recognition (NER), runs hybrid urgency detection, calculates deterministic multi-factor priority scores, applies confidence-tiered routing with human-in-the-loop review, manages database-configured routing rules, verifies 7-step agent capacity assignments with team queue fallbacks, integrates a pluggable `LLMProvider` abstraction (`OllamaProvider` and `GroqProvider` via `LLM_PROVIDER`), generates high-fidelity AI summaries for 800+ word complaints, and drafts empathetic RAG-backed resolutions.

---

## 🚀 Key Modules & Architecture

### 1. Automated Ingestion & Preprocessing
- **Multi-Channel Ingestion**: Polling via Gmail API OAuth 2.0, Web Portal, and REST API.
- **Preprocessing Pipeline**: Cleans raw HTML, strips quoted email reply chains (`On ... wrote:`), trims signatures, normalizes Unicode whitespace, preserves currencies/transaction IDs, and detects language.
- **Dual Text Storage**: Retains both `description` (original verbatim text) and `cleaned_text` (normalized NLP input) for complete audit transparency.

### 2. 5-Tier Classification Model Progression & Governance
- **Tier 1 (Baseline)**: TF-IDF + Logistic Regression
- **Tier 2 (Alternative)**: TF-IDF + Multinomial Naive Bayes
- **Tier 3 (Transformer)**: DistilBERT (`distilbert-base-uncased`)
- **Tier 4 (Advanced Transformer)**: RoBERTa / BERT (`roberta-base`)
- **Tier 5 (Zero-Shot)**: BART MNLI (`facebook/bart-large-mnli`)
- **Model Governance**: Automatically selects the simplest high-performing model based on data scale thresholds.

### 3. Sentiment & Configurable Emotion Analysis
- **Sentiment**: Standardized output (`label`: `NEGATIVE`, `POSITIVE`, `NEUTRAL` with `confidence` score).
- **Emotion Analysis**: Classifies emotion into 6 target categories:
  `ANGER` • `FRUSTRATION` • `FEAR` • `SADNESS` • `NEUTRAL` • `SATISFACTION`
- **Configurable Models**: Dynamically toggle between Hugging Face model checkpoints (`j-hartmann/emotion-english-distilroberta-base`, `SamLowe/roberta-base-go_emotions`, `facebook/bart-large-mnli`).

### 4. Named Entity Recognition (NER)
Extracts 10 domain entities and stores them in the `complaint_entities` relational database table:
- `PERSON` • `EMAIL` • `PHONE` • `ORDER_ID` • `TRANSACTION_ID`
- `AMOUNT` • `DATE` • `PRODUCT` • `COMPANY` • `LOCATION`

### 5. Hybrid Urgency Detection
Evaluates operational urgency into 4 distinct levels:
- `LOW` • `MEDIUM` • `HIGH` • `CRITICAL`
- Combines machine learning classification with critical business rules (e.g. security compromises, outages, regulatory/legal threats escalate directly to `CRITICAL`).

### 6. Deterministic Multi-Factor Priority Engine
Priority decisions are calculated deterministically without relying on LLM hallucination:
$$\text{priority\_score} = (\text{urgency} \times 0.30) + (\text{sentiment} \times 0.15) + (\text{biz\_impact} \times 0.20) + (\text{cust\_impact} \times 0.15) + (\text{sla\_risk} \times 0.20)$$

- **0 – 30**: `LOW` (P4)
- **31 – 60**: `MEDIUM` (P3)
- **61 – 80**: `HIGH` (P2)
- **81 – 100**: `CRITICAL` (P1)
- Scoring weights are fully configurable at runtime.

### 7. Confidence-Based Routing & Human Review Workflow
- **$\ge 0.85$ (High Confidence)**: Automatically routes to the target department and assigns/enqueues without manual intervention.
- **$0.60 - 0.84$ (Medium Confidence)**: Routes provisionally to department/team, but flags `review_required = True`.
- **$< 0.60$ (Low Confidence)**: Does not finalize department (`department_id = None`, `team_id = None`, `assigned_agent_id = None`). Held for human review (`review_required = True`).
- **Review Persistence**: Stores `ai_confidence`, `review_required`, `reviewed_by`, and `reviewed_at` with review completion endpoint `POST /api/complaints/{id}/review`.

### 8. End-to-End 8-Stage Routing Pipeline (`routing_service.py`)
Executes the sequential enterprise routing flow:
```
AI Classification ──> Category ──> Subcategory ──> Department ──> Team ──> Required Skills ──> Available Agents ──> Workload Evaluation ──> Assignment
```

### 9. Database-Stored Configurable Routing Rules
Zero rules are hardcoded in React. All routing rules are stored dynamically in the `routing_rules` database table and consumed via REST API:
- `Billing` $\rightarrow$ `Finance`
- `Payment` $\rightarrow$ `Finance / Payments`
- `Refund` $\rightarrow$ `Finance / Refunds`
- `Login` $\rightarrow$ `IT / Application Support`
- `Network` $\rightarrow$ `IT / Network Team`
- `Security Breach` $\rightarrow$ `Security`
- `Payroll` $\rightarrow$ `HR / Payroll`
- `Leave` $\rightarrow$ `HR / Employee Relations`
- `Delivery` $\rightarrow$ `Logistics`
- Full CRUD REST API at `/api/routing-rules` with dynamic frontend client at `frontend/src/api/routingRules.js`.

### 10. 7-Step Verified Agent Assignment & Team Queue Fallback
When assigning human agents:
1. **Verify department**: Candidate must match the resolved department.
2. **Verify team**: Prioritizes candidate agents under the resolved team.
3. **Verify skills**: Evaluates overlap between complaint required skills and agent skills.
4. **Check availability**: Must be online and active (`availability=True`, `is_active=True`).
5. **Check current workload**: Tracks real-time active assigned ticket count.
6. **Check maximum workload**: Enforces capacity constraint (`current_workload < max_workload`).
7. **Prefer suitable lower-workload agents**: Prioritizes agents with the lowest current workload / highest remaining capacity.
- **Team Queue Fallback**: If no suitable agent exists (e.g. team is offline or at maximum capacity), the ticket is routed directly to the **Team Queue** (`complaint.status = "ROUTED"`, `complaint.assigned_agent_id = None`, `ENQUEUED_IN_TEAM_QUEUE`). **The complaint is preserved with zero data loss.**

### 11. Semantic Duplicate Detection & Agent Resolution Actions
- **Baseline Benchmark**: TF-IDF feature extraction with cosine similarity comparison preserved for reference.
- **Primary Engine (Sentence Transformers + pgvector)**:
  ```
  Complaint ──> Embedding (384-d dense vector) ──> pgvector ──> Similarity Search ──> Similar Complaints
  ```
- **Detection Output**: Returns `matched_complaint_id` and `similarity_score`.
- **Threshold Escalation**: Similarity score $\ge 0.85$ (e.g. 0.91) flags `is_duplicate = True` and renders **"Possible duplicate complaint"**.
- **Human Agent Resolution Actions**:
  - **Link Complaints**: Connects duplicate ticket to the primary complaint (`POST /api/complaints/{id}/duplicate/link`), keeping both tickets active and audited.
  - **Merge Complaints**: Merges duplicate ticket into primary complaint (`POST /api/complaints/{id}/duplicate/merge`), transitioning status to `RESOLVED`/`MERGED` and transferring context.
  - **Ignore Duplicate Warning**: Dismisses the warning (`POST /api/complaints/{id}/duplicate/ignore`), clearing the duplicate flag.

### 12. Dense Vector Semantic Search & "Find Complaints Similar to This One"
- **Concept Subspace Semantic Embeddings**: Continuous 384-dimensional dense semantic vectors project natural language queries and complaint bodies into shared semantic conceptual spaces.
- **Find Complaints Similar to This One**:
  - Input Complaint: `"Money was deducted twice."`
  - Retrieved Complaint: `"I was charged two times for the same transaction."`
  - Conceptually identical even though vocabulary, token tokens, and grammar share zero overlap.
- **pgvector & Cosine Fallback Execution**: Executes native pgvector `<=>` cosine distance queries when connected to PostgreSQL and seamless in-memory normalized dot products on SQLite.
- **Dedicated REST API Endpoints**:
  - `GET /api/complaints/semantic-search?query=...&threshold=0.40`: Natural language conceptual search across all complaints.
  - `GET /api/complaints/{id}/find-similar`: Retrieves top conceptually matching complaints for a specific ticket, excluding the source ticket.
- **Frontend Explorer & Triage Integration**:
  - Semantic Search mode in the Complaints Explorer with instant example chips and similarity percentage badges.
  - "Find complaints similar to this one" drawer in the ticket detail view with direct Link, Merge, and Inspect actions.

### 13. Semantic Incident Detection & Executive Manager Alerting
- **Sliding Window Semantic Clustering**: Evaluates complaints arriving within a short time window (e.g. 1h, 6h, 24h) and clusters semantically related issues using dense Sentence Transformers vectors.
- **Automated Incident Synthesis**:
  - **Example**:
    - Incoming complaints (50 tickets):
      - *"Portal is not working."*
      - *"Cannot login."*
      - *"Account access unavailable."*
    - **System Detection**:
      - **Status**: `Potential Incident Detected`
      - **Incident Title**: `Portal Authentication Failure`
      - **Affected complaints**: `50`
      - **Department**: `IT`
      - **Severity**: `HIGH`
- **Manager Command Center Visibility**:
  - Prominent real-time incident alert cards surfaced to managers in the Executive Triage Command Center.
  - Provides instant root cause context, sample complaint quotations, and one-click **Acknowledge Incident** and **Resolve Incident** workflows.

### 14. Pluggable `LLMProvider` Architecture & Default Local Ollama
- **Default Local LLM**: Ollama is configured as the default local LLM (`LLM_PROVIDER=ollama`).
- **Configuration**:
  ```env
  LLM_PROVIDER=ollama
  OLLAMA_BASE_URL=http://localhost:11434
  OLLAMA_MODEL=
  ```
- **Do Not Assume a Model is Installed**: `OLLAMA_MODEL` defaults to empty; the application dynamically discovers installed models via `GET /api/tags`.
- **User Configurable**: The user can configure the active model via `.env`, query parameters, or runtime API endpoint `POST /api/ai/llm/config`.
- **Optional Groq Cloud Provider with Automatic Fallback**:
  - Groq is an optional provider configured via `GROQ_API_KEY=` and `GROQ_MODEL=`.
  - **Key Security**: The API key is strictly loaded from the environment (`.env`) and is **never hardcoded** in code and **never committed** to source control (`.gitignore` protects all `.env` files).
  - **Automatic Fallback to Ollama**: If Groq is unavailable (missing API key, rate limit, network disruption, or model unavailable), the application automatically falls back to configured local Ollama seamlessly.
- **Graceful Error Handling & Non-Crashing Resilience**:
  - If the model or Ollama daemon is unavailable, the provider returns a **clear, actionable error** along with the official installation link: [https://ollama.com/download](https://ollama.com/download).
  - **Does NOT crash the entire application**: summarization falls back gracefully to calibrated extraction.
  - **Allows other functionality to continue**: ticket ingestion, 5-tier classification, emotion/sentiment analysis, NER extraction, priority calculation, routing rules, agent assignment, team queue fallback, duplicate detection, semantic search, and incident detection continue without interruption.
- **Provider Decoupling**: Application modules interact solely through `get_llm_provider()` and the `LLMProvider` abstract contract. Switching between providers requires zero code modifications.

### 15. AI Complaint Summarization (800-Word Compression & Storage)
- **High-Fidelity Information Extraction**: Analyzes lengthy, verbose customer narratives (e.g., 800+ words) and generates a concise 2-3 sentence executive summary preserving essential details: customer issue, specific amounts, temporal context, and requested resolution.
- **Example**:
  - **Original Complaint**: 800-word narrative detailing multi-step transaction dispute.
  - **AI Summary**:
    > *"Customer reports a duplicate payment of ₹5,000. The payment occurred today and the customer is requesting an immediate refund."*
- **Persistent Dual Storage**:
  - Persisted directly on `complaint.summary` for instantaneous dashboard view and fast vector searching.
  - Stored in the relational `ai_responses` audit log (`response_type="SUMMARY"`, `provider="ollama"`/`"groq"`).
  - Emits an audited lifecycle transition event `AI_ANALYSIS_COMPLETED` (actor: `SUMMARIZER`).
- **REST Endpoints & Frontend**:
  - `POST /api/complaints/{id}/summarize?provider=ollama|groq&model=...`: Triggers on-demand AI summarization with optional model override.
  - `GET /api/complaints/{id}/summary`: Retrieves the current persisted summary and metadata.
  - Interactive **Summarize with AI** action and provider tag in the Complaint Detail modal & detail page.

### 16. Strict Boundary Separation: Generative LLMs vs. Specialized Models vs. Deterministic Code
To prevent hallucination, eliminate latency bottlenecks, and preserve strict regulatory auditability, **the system does NOT use LLMs for every task**. The platform enforces three distinct computational paradigms:

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                           COMPUTATIONAL PARADIGMS BOUNDARY                        │
├───────────────────────────┬───────────────────────────────┬───────────────────────┤
│   Generative LLMs         │   Specialized ML/NLP Models   │   Deterministic Code  │
│   (Ollama / Groq)         │   (High Throughput & Speed)   │   (Zero Hallucination)│
├───────────────────────────┼───────────────────────────────┼───────────────────────┤
│ 1. Complaint Summarization│ • Intent Classification       │ • Priority Scoring    │
│ 2. Resolution Recomms     │   (5-Tier Model Progression)  │ • SLA Deadlines       │
│ 3. AI Assistant Copilot   │ • Sentiment Analysis          │ • Routing & Tiers     │
│ 4. RAG Question Answering │   (DistilBERT on SST-2)       │ • Permissions (RBAC)  │
│ 5. Customer Response Draft│ • Named Entity Rec (NER)      │ • Agent Assignment    │
│ 6. Technical Explanation  │   (BERT NER / SpaCy patterns) │   (7-Step Verification│
│ 7. Policy Reasoning       │ • Dense Vector Embeddings     │   & Queue Fallback)   │
│                           │   (Sentence Transformers 384d)│                       │
└───────────────────────────┴───────────────────────────────┴───────────────────────┘
```

#### 1. Generative LLMs (Ollama / Groq) for 7 High-Level Generative Tasks
1. **Complaint Summarization**: Synthesizes lengthy, unstructured customer complaints into concise 2-sentence executive summaries preserving key facts, amounts, timing, and requested actions.
2. **Resolution Recommendations**: Generates grounded, step-by-step resolution advice for support agents based on retrieved enterprise documents (`rag_engine.generate_grounded_recommendation`).
3. **AI Assistant Copilot**: Conversational interactive agent copilot assisting customer service representatives in navigating triage procedures and inquiries (`/api/ai/chat`).
4. **RAG Question Answering**: Synthesizes factually grounded answers to operational queries citing internal knowledge base documents (`rag_engine.answer_query`).
5. **Customer Response Generation**: Produces personalized, empathetic draft email replies ready for agent review (`response_generator.generate_draft`).
6. **Internal Complaint Explanation**: Delivers clear technical explanations, root causes, and debugging clues for internal engineering teams (`rag_engine.explain_complaint`).
7. **Reasoning Over Retrieved Information**: Performs multi-hop logical deductions over complaint facts cross-referenced against company policies and warranty terms (`rag_engine.reason_over_complaint_and_policies`).

#### 2. Specialized Models for Core Extraction (Fast, Reproducible, High-Throughput)
- **Intent Classification**: 5-Tier progressive model selection (TF-IDF + Logistic Regression, Naive Bayes, DistilBERT, RoBERTa, BART MNLI).
- **Sentiment Analysis**: Dedicated DistilBERT checkpoint fine-tuned on SST-2 returning calibrated polarity score (-1.0 to +1.0) and discrete labels (`NEGATIVE`, `POSITIVE`, `NEUTRAL`).
- **Named Entity Recognition (NER)**: High-speed BERT NER / SpaCy pattern matching extracting 10 core entity types (`AMOUNT`, `DATE`, `ORDER_ID`, `TRANSACTION_ID`, etc.) directly into relational tables.
- **Dense Vector Embeddings**: Sentence Transformers (`all-MiniLM-L6-v2`, 384-dimensional dense vectors) for vector search, semantic clustering, and pgvector cosine indexing.

#### 3. Deterministic Code for Critical Business Decisions (Zero Hallucination)
- **Priority Calculation**: Weighted mathematical formula:
  $$\text{Priority} = (\text{Urgency} \times 0.30) + (\text{Sentiment} \times 0.15) + (\text{BizImpact} \times 0.20) + (\text{CustImpact} \times 0.15) + (\text{SLARisk} \times 0.20)$$
- **SLA Calculation & Breaches**: Exact millisecond timestamps derived from business calendar hours without stochastic variability.
- **Routing & Confidence Tiers**: Explicit mathematical thresholds ($\ge 0.85$ Auto-Route, $0.60-0.84$ Provisional Route, $<0.60$ Hold for Review) and relational `routing_rules`.
- **Permissions & Security**: Strict Role-Based Access Control (RBAC) bitmasks and enum validations (`ADMIN`, `MANAGER`, `AGENT`, `CUSTOMER`).
- **Agent Workload & Assignment**: 7-factor deterministic capacity matching (Department $\to$ Team $\to$ Skills $\to$ Availability $\to$ Workload $\to$ Capacity $\to$ Lowest Load Selection $\to$ Team Queue Fallback).

### 17. Enterprise RAG Knowledge Base & 9-Stage Ingestion Pipeline
Centralized corporate knowledge repository supporting 9 official document types with end-to-end vector ingestion and grounded RAG question answering.

#### 1. The 9 Supported Enterprise Documents
1. **Refund Policy**: Unconditional 30-day duplicate charge reversal rules, payment gateway turnaround times (UPI 2-5 days, Credit Card 5-7 days), and required transaction verification.
2. **Billing Policy**: Monthly subscription billing cycles, 3-retry automated payment workflows, 5-day grace period, and 60-day invoice dispute windows.
3. **Customer Support SOP**: Empathetic interaction etiquette, ticket intake checklists, root-cause tagging, and 24-hour CSAT follow-up standards.
4. **SLA Policy**: Commitments across priority tiers (P1 Critical: 15m/4h, P2 High: 1h/8h, P3 Medium: 4h/24h, P4 Low: 12h/48h) and 75% warning auto-escalation.
5. **Escalation Policy**: 3-Tier hierarchy (Tier-1 Frontline $\to$ Tier-2 Leads $\to$ Tier-3 Engineering Directors) and mandatory handoff documentation.
6. **IT Troubleshooting Guide**: Web portal 500 error diagnostics, Redis auth session validation, JWT expiry checks, and payment gateway webhook reconciliations.
7. **Security Policy**: AES-256 / TLS 1.3 encryption, compromised account containment protocol, and out-of-band 2FA identity challenge procedures.
8. **HR Policy**: Support agent workload limits (max 10 concurrent high-priority tickets), mandatory 15-minute wellness breaks, and non-retaliation grievance procedures.
9. **Finance Policy**: Financial delegation of authority matrix (Tier-1: ₹5,000, Leads: ₹25,000, Dept Heads: ₹100,000, CFO: > ₹100,000) and chargeback reconciliation rules.

#### 2. The Complete 9-Stage RAG Pipeline
```
Document Upload (.txt, .md, .pdf, .json)
       │
       ▼
Text Extraction (UTF-8/Latin-1 auto-decoding & JSON unwrap)
       │
       ▼
Cleaning (Whitespace normalization, line ending standardization, noise removal)
       │
       ▼
Chunking (Sliding window with overlap, 500 characters, sentence boundary preservation)
       │
       ▼
Sentence Transformer (all-MiniLM-L6-v2)
       │
       ▼
Embedding (384-dimensional dense semantic vectors)
       │
       ▼
pgvector (PostgreSQL pgvector <=> cosine indexing with SQLite fallback)
       │
       ▼
Semantic Retrieval (Top-k relevant chunks filtered by similarity threshold)
       │
       ▼
Relevant Context (Structured context with document titles, types, and scores)
       │
       ▼
Ollama / Groq (LLMProvider prompt execution with strict anti-hallucination guardrails)
       │
       ▼
Grounded Answer (Verifiable answers with direct chunk citations and provider metadata)
```

#### 3. Out-of-the-Box Pre-Seeding & Frontend Studio
- **Pre-Seeded Corpus**: Automatically seeds all 9 official policies into `knowledge_documents` and `knowledge_chunks` on first database startup.
- **Frontend Studio (`/knowledge-base`)**:
  - **Documents Library**: Filter by the 9 policy types with chunk count badges, search, view, edit, re-index, and delete actions.
  - **Document Ingestion Studio**: Drag-and-drop file upload with custom document name, department, and author tags, plus animated visual pipeline progress (Upload $\to$ Extract $\to$ Clean $\to$ Chunk $\to$ MiniLM $\to$ pgvector).
  - **RAG Q&A Playground**: Interactive Q&A interface with sample query chips, real-time vector retrieval, cited chunk snippets, and grounded answers from Ollama/Groq.

#### 4. Admin Knowledge Base Lifecycle & Separate Storage Architecture
Enterprise knowledge base administration provides full lifecycle control over operational documents with decoupled chunk and embedding storage:

- **Admin Operations**:
  - **Upload Documents (`POST /api/knowledge/upload`, `POST /api/knowledge`)**: Ingests policy files (.txt, .md, .pdf, .json) or raw text with metadata attribution (`document_name`, `document_type`, `department`, `uploaded_by`).
  - **View Documents (`GET /api/knowledge/{id}`)**: Inspects comprehensive document details, version history, raw text, granular chunks, token counts, and linked embedding IDs.
  - **Delete Documents (`DELETE /api/knowledge/{id}`)**: Cascades deletion across document records, associated text chunks, and vector embeddings.
  - **Update Documents (`PUT /api/knowledge/{id}`)**: Modifies document name, department, or content. Automatically increments the revision `version` (`v1` $\to$ `v2`) and triggers asynchronous or synchronous re-indexing.
  - **Re-index Documents (`POST /api/knowledge/{id}/reindex`)**: Re-cleans, re-chunks, and recalculates Sentence Transformer dense embeddings on-demand, bumping document version.
- **Stored Metadata Fields**:
  - `document_name`: Canonical business title of the knowledge document.
  - `document_type`: Standardized policy category (e.g., Refund Policy, Billing Policy, SLA Policy).
  - `department`: Target operational department (`General`, `Finance`, `Support`, `IT`, `HR`, `Security`).
  - `version`: Monotonically increasing revision counter tracking modifications.
  - `uploaded_by`: User or administrator principal who ingested the document (`Admin`, etc.).
  - `created_at`: ISO UTC timestamp of initial document ingestion.
- **Separate 3-Tier Storage Architecture**:
  ```
  ┌────────────────────────────────────────────────────────────────────────┐
  │                    SEPARATE KNOWLEDGE STORAGE TIERS                   │
  ├──────────────────────┬──────────────────────┬──────────────────────────┤
  │ knowledge_documents  │ knowledge_chunks     │ chunk_embeddings         │
  ├──────────────────────┼──────────────────────┼──────────────────────────┤
  │ • id (UUID / PK)     │ • id (UUID / PK)     │ • id (UUID / PK)         │
  │ • document_name      │ • document_id (FK)   │ • chunk_id (FK)          │
  │ • document_type      │ • chunk_index        │ • document_id (FK)       │
  │ • department         │ • chunk_text         │ • embedding (Vector 384) │
  │ • version            │ • token_count        │ • model_name (MiniLM-L6) │
  │ • uploaded_by        │ • created_at         │ • dimension (384)        │
  │ • raw_text           │                      │ • created_at             │
  │ • created_at         │                      │                          │
  └──────────────────────┴──────────────────────┴──────────────────────────┘
  ```
  Decoupling `chunk_embeddings` from `knowledge_chunks` allows vector re-indexing without altering raw text or chunk segmentation, supports model migrations without schema rewrites, and maintains clean database normalization.

#### 5. Strict Anti-Hallucination & Policy Grounding Guardrails
To prevent AI hallucination and protect corporate liability, strict grounding constraints are enforced across all policy endpoints (`/api/knowledge/query`, `/api/ai/chat`, `/api/ai/rag-query`):
- **Never Invent Policies**: The AI must not invent, speculate, or fabricate company policies under any circumstance.
- **Retrieved Knowledge Only**: Policy answers rely exclusively on retrieved and verified chunks from official company documents.
- **Mandatory Clear Indicator Phrasing**:
  - Grounded policy answer: Clearly indicates and begins with:
    > `"Based on company policy..."`
  - Unretrieved, ungrounded, or out-of-scope inquiry: Clearly indicates and responds with:
    > `"No relevant company policy was found."`
- **Substantive Topic Verification**: Stopword-filtered keyword matching ensures that spurious cosine similarities (e.g. from generic conversational syntax) cannot trigger policy citations for ungrounded or out-of-domain queries (e.g., speculative starship parking regulations or malicious policy invention requests).
- **Zero Unsupported Exposure**: Unsupported information is never presented as official company policy; out-of-domain and invention attempts are rejected with `grounded=False` and `cited_chunks=[]`.

### 18. Human-in-the-Loop Customer Response Studio (Generate, Edit, Approve, Send)
Enterprise customer communications are governed by a human-in-the-loop workflow:
- **Professional Standard Structure**:
  ```text
  Dear Customer,

  We have reviewed your complaint regarding the duplicate payment. Our Finance team is currently verifying the transaction and will process the necessary refund if the duplicate transaction is confirmed.

  Complaint ID: CMP-10001

  Regards,
  Customer Support Team
  ```
- **The 4 Agent Operations**:
  1. **Generate (`POST /api/complaints/{id}/generate-response`)**: Allows the agent to click **"Generate AI Response"** to draft a tailored, empathetic response using Ollama/Groq or fallback template. Initialized with `is_approved=False` and `is_sent=False`.
  2. **Edit (`PUT /api/complaints/{id}/edit-response`)**: Provides an in-place editing studio with word/character counts. Modifying draft content automatically resets `is_approved=False` so changes cannot bypass human review.
  3. **Approve (`POST /api/complaints/{id}/approve-response`)**: Explicit human sign-off recording approver identity (`approved_by`) and timestamp (`approved_at`).
  4. **Send (`POST /api/complaints/{id}/send-response`)**: Dispatches response to the customer and records the `RESPONSE_SENT` lifecycle milestone.
- **Strict Anti-Automation Guardrail**:
  - **Never send automatically**: The backend strictly enforces human approval, rejecting any send attempt on unapproved drafts with `HTTP 400 Bad Request`.
  - The UI disables dispatch until an agent explicitly approves the response.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, Vite, React Router, Axios, Tailwind CSS, Recharts, Lucide Icons |
| **Backend** | FastAPI, Python 3.12, Pydantic v2, SQLAlchemy 2.0, Alembic, JWT Auth |
| **Database & Vector** | PostgreSQL 16, `pgvector` (with automatic SQLite fallback for local testing) |
| **NLP & AI** | Hugging Face Transformers, Sentence Transformers, spaCy, Scikit-learn |
| **Generative AI** | Pluggable `LLMProvider` (Default local Ollama at `http://localhost:11434`, Optional Groq Cloud API with Ollama fallback), RAG Pipeline |
| **Email Ingestion** | Gmail API, Google OAuth 2.0 |
| **Testing** | Pytest, FastAPI TestClient, Asyncio (135 passing automated tests) |


---

## 🏗️ Architecture Flow

```
Raw Complaint (Email / Web / Manual)
    │
    ▼
[Text Preprocessor] ──> HTML / Signature / Quote Stripping
    │
    ▼
[AI Orchestrator]
    ├── 1. Language Detection
    ├── 2. Classification (5-Tier Progression)
    ├── 3. Sentiment Analysis (Hugging Face Transformers)
    ├── 4. Emotion Detection (6 Target Emotions)
    ├── 5. Named Entity Recognition (10 Entity Types -> complaint_entities)
    ├── 6. Hybrid Urgency Detection (LOW, MEDIUM, HIGH, CRITICAL)
    ├── 7. Deterministic Priority Engine (0-100 Score -> P1-P4)
    ├── 8. 384-d Embedding & Duplicate Detection
    ├── 9. Summarization & RAG Policy Search
    │
    ▼
[Routing Engine]
    ├── Confidence Threshold Evaluation (>=0.85, 0.60-0.84, <0.60)
    ├── Configurable Database Routing Rules (routing_rules table)
    └── 8-Stage Sequential Flow (AI -> Category -> Subcategory -> Dept -> Team)
    │
    ▼
[Assignment Engine]
    ├── 7-Step Verification (Dept, Team, Skills, Availability, Workload, Capacity, Load Priority)
    └── Fallback: Enqueue in Team Queue (Ticket Preserved, Zero Loss)
    │
    ▼
[Lifecycle Engine] ──> Event Logged to complaint_events
```

---

## ⚡ Quick Start Guide

### 1. Clone the Repository & Configure Environment
```bash
git clone https://github.com/Ranjith352/Email_Complaint_Classifier.git
cd Email_Complaint_Classifier
cp .env.example .env
```

Configure `.env` with your settings:
```env
# Pluggable LLM Provider (ollama or groq)
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
OLLAMA_BASE_URL=http://localhost:11434

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/complaint_classifier
```
*(Note: If PostgreSQL is not running locally, the system automatically falls back to local SQLite `autotriage.db`).*

### 2. Launch FastAPI Backend
```bash
# Activate Python virtual environment
.\venv\Scripts\activate      # On Windows
# source venv/bin/activate    # On Linux/macOS

# Install backend dependencies
pip install -r backend/requirements.txt

# Launch FastAPI development server
uvicorn backend.app.main:app --reload --port 8000
```
Interactive Swagger API documentation is available at: **http://127.0.0.1:8000/docs**

### 3. Launch React Frontend
```bash
cd frontend
npm install
npm run dev
```
Open your browser at: **http://localhost:5173**

**Default Demo Credentials**:
- **Email**: `admin@complaints.io`
- **Password**: `admin123`

---

## 🧪 Running Automated Tests

Run the complete backend test suite across all 112 unit and integration tests:
```bash
pytest backend/app/tests -v
```

### Test Coverage (112 Tests Passing):
- **`test_summarization.py`**: Pluggable `LLMProvider` abstraction (`OllamaProvider`, `GroqProvider`, `LLM_PROVIDER` environment configuration), default local Ollama configuration (`OLLAMA_BASE_URL=http://localhost:11434`, `OLLAMA_MODEL=`), dynamic model configuration without assuming pre-installation, clear error handling when model/daemon is unavailable, official Ollama download link (`https://ollama.com/download`), Groq optional provider credential security (never hardcoded, never committed), automatic seamless fallback to Ollama when Groq is unavailable, non-crashing application resilience, 800-word complaint summarization extracting duplicate payment of ₹5,000, timing ("today"), and immediate refund request, database persistence in `complaint.summary` and `ai_responses` (`response_type="SUMMARY"`), and REST endpoints (`POST /api/complaints/{id}/summarize`, `GET /api/complaints/{id}/summary`, `GET /api/ai/llm/status`, `GET /api/ai/llm/models`, `POST /api/ai/llm/config`).
- **`test_incidents.py`**: Semantic incident detection over sliding time windows, user exact scenario (50 complaints with "Portal is not working.", "Cannot login.", "Account access unavailable." -> Potential Incident Detected, "Portal Authentication Failure", IT department, HIGH severity, 50 affected), manager actions (Acknowledge, Resolve), and REST endpoints (`/api/incidents/detect`, `/api/incidents/active`, `/api/incidents/{id}/acknowledge`, `/api/incidents/{id}/resolve`).
- **`test_semantic_search.py`**: Dense vector concept embeddings, lexical gap bridging ("Money was deducted twice." vs "I was charged two times for the same transaction." similarity $\ge 0.85$), `search_complaints` retrieval, `find_similar_to_complaint`, and REST endpoints (`/semantic-search`, `/{id}/find-similar`).
- **`test_duplicate_detection.py`**: Sentence Transformers + pgvector flow, TF-IDF baseline, $\ge 0.85$ duplicate warning, and agent actions (Link, Merge, Ignore).
- **`test_agent_assignment.py`**: 7-step criteria verification, lower-workload priority, and team queue fallback.
- **`test_routing_rules.py`**: REST CRUD for configurable rules, user exact rule mappings, and dynamic runtime additions.
- **`test_routing_pipeline.py`**: Complete 8-stage routing pipeline breakdown and user duplicate payment verification.
- **`test_confidence_routing.py`**: $\ge 0.85$ auto-routing, $0.60 - 0.84$ provisional routing, $< 0.60$ unfinalized human review hold, and manual review resolution.
- **`test_priority.py`**: Deterministic formula calculation, tier ranges (0-30, 31-60, 61-80, 81-100), and custom configurable weights.
- **`test_urgency.py`**: Urgency tiers (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), model output integration, and business rule escalations.
- **`test_transformers_emotion.py`**: All 6 target emotions (`ANGER`, `FRUSTRATION`, `FEAR`, `SADNESS`, `NEUTRAL`, `SATISFACTION`) and configurable model switching.
- **`test_ner.py`**: Extraction of 10 target entity types and database persistence in `complaint_entities`.
- **`test_transformers_sentiment.py`**: Standardized sentiment labels (`NEGATIVE`, `POSITIVE`, `NEUTRAL`) and confidence scores.
- **`test_model_progression.py`**: 5-tier classification progression and governance switching.
- **`test_preprocessing.py`**: HTML cleaning, email signature removal, quoted reply stripping, and Unicode normalization.
- **`test_lifecycle.py`**: 9-stage state machine transitions and audit event logs.
- **`test_assignment.py`**: 7-factor agent routing scoring algorithm.
- **`test_api.py`, `test_complaints.py`, `test_auth.py`, `test_routing.py`, `test_sla.py`**: Core REST API and operational flows.

---

## 🔒 Configuration & Integrations

1. **Default Local Ollama (`OLLAMA_BASE_URL` & `OLLAMA_MODEL`)**:
   - Download Ollama: [https://ollama.com/download](https://ollama.com/download)
   - Default configuration in `.env`:
     ```env
     LLM_PROVIDER=ollama
     OLLAMA_BASE_URL=http://localhost:11434
     OLLAMA_MODEL=
     ```
   - Does not assume a model is pre-installed; allows user to configure any model (`llama3`, `mistral`, `qwen2.5`, `phi3`, etc.).
   - If the model or daemon is unavailable, returns a clear error and allows all other application operations to continue without crashing.
2. **Groq Cloud API (Optional Cloud Provider with Ollama Fallback)**:
   - Configure in `.env`:
     ```env
     GROQ_API_KEY=your_groq_api_key_here
     GROQ_MODEL=llama-3.3-70b-versatile
     ```
   - **Never hardcoded; never committed** (`.env` is excluded in `.gitignore`).
   - If Groq is unavailable, the provider automatically falls back to configured local Ollama without crashing.
3. **Gmail API**:
   - Place OAuth client credentials as `credentials.json` in the root directory.
4. **Configurable Database Rules**:
   - Manage routing rules dynamically via `POST /api/routing-rules` or the frontend settings interface without code deployments.
