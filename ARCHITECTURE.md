# AutoTriage AI - System Architecture & Technical Specification

## 1. Executive Summary
**AutoTriage AI** is a production-grade, enterprise-ready Complaint Classification, Department Routing, and Retrieval-Augmented Generation (RAG) Platform. The system automatically ingests incoming customer complaints from Gmail, extracts semantic embeddings, performs multi-label categorization and urgency scoring, retrieves relevant historical resolutions via vector search (`pgvector`), and drafts empathetic customer replies with actionable resolution advice using Generative AI (Groq API & local Ollama).

---

## 2. Technology Stack Overview

| Domain | Technology | Purpose & Capability |
| :--- | :--- | :--- |
| **Frontend** | React 18, Vite | High-performance Single Page Application (SPA) |
| **Routing** | React Router v6 | Client-side routing with guarded authentication |
| **Styling** | Tailwind CSS, CSS Glassmorphism | Bespoke dark-mode UI with fluid responsive layouts |
| **Data Viz** | Recharts | Interactive real-time metrics, SLA health & trend charts |
| **API Client** | Axios | Intercepted HTTP client managing JWT Bearer tokens |
| **Backend API** | FastAPI, Python 3.12 | Asynchronous high-throughput REST API with OpenAPI/Swagger |
| **Validation** | Pydantic v2 | Strict schema validation and serialization |
| **ORM & DB** | SQLAlchemy 2.0, Alembic | Declarative persistence with multi-engine support |
| **Primary Database**| PostgreSQL 16 | ACID-compliant relational data store |
| **Vector Search** | `pgvector` | 384-dimensional dense vector indexing & cosine similarity |
| **NLP & ML** | Sentence Transformers (`all-MiniLM-L6-v2`) | High-accuracy semantic embedding generation |
| **Linguistics** | spaCy & Scikit-learn | Named entity extraction, tokenization, classification |
| **Cloud GenAI** | Groq API (`llama-3.3-70b-versatile`) | Ultra-low latency cloud LLM inference |
| **Local GenAI** | Ollama (`llama3`, `mistral`) | 100% private offline LLM execution |
| **Ingestion** | Gmail API, OAuth 2.0 | Automated polling and MIME email message decoding |
| **Testing** | Pytest, FastAPI TestClient | Comprehensive automated unit and integration suite |

---

## 3. High-Level System Architecture

```mermaid
graph TD
    subgraph Client Layer
        A[React 18 + Vite SPA]
        A1[Recharts Dashboard]
        A2[Complaints Explorer]
        A3[AI Triage & Draft Drawer]
    end

    subgraph API Gateway & Authentication
        B[FastAPI REST API /docs]
        B1[JWT Bearer Security Middleware]
        B2[CORS Middleware]
    end

    subgraph Data & Vector Persistence
        C[(PostgreSQL 16)]
        C1[pgvector Extension - 384d Vectors]
        C2[Complaints & Users Tables]
        C3[KnowledgeItems / SOPs Table]
    end

    subgraph AI / NLP Intelligence Engine
        D[Sentence Transformers MiniLM-L6]
        D1[spaCy Entity Extraction]
        D2[Multi-Label Rule & Keyword Classifier]
        D3[Cosine Similarity RAG Engine]
    end

    subgraph Generative AI Provider Layer
        E[Unified LLM Service]
        E1[Groq API Cloud Llama-3.3]
        E2[Ollama Local Private Llama-3]
        E3[Deterministic Fallback Engine]
    end

    subgraph External Email Ingestion
        F[Gmail API via OAuth 2.0]
        F1[Target Label: 'Complaints']
    end

    A -->|HTTP / Axios with JWT| B
    B --> B1
    B --> C
    F -->|Poll & Parse| B
    B -->|Text for Vectorization| D
    D -->|Compute 384d Embeddings| C1
    C1 -->|Retrieve Top-K Historical Matches| D3
    D3 -->|Grounding Context| E
    E -->|Summary, Steps, Reply Draft| B
    B -->|Enriched Ticket & Analytics| A
```

---

## 4. End-to-End Ingestion & Triage Data Flow

```mermaid
sequenceDiagram
    autonumber
    actor Customer as Customer / Inquirer
    participant Gmail as Gmail Inbox
    participant Worker as Gmail Ingestion Service
    participant NLP as SentenceTransformers & spaCy
    participant VectorDB as PostgreSQL / pgvector
    participant LLM as Groq / Ollama LLM Service
    participant DB as Relational Database
    actor Agent as Support Specialist

    Customer->>Gmail: Sends complaint email
    Worker->>Gmail: Polls messages labeled 'Complaints' (OAuth 2.0)
    Worker->>Worker: Decodes MIME body, extracts sender & subject
    Worker->>NLP: Sends raw text for analysis
    NLP->>NLP: Computes Category, Department, Urgency, Entities
    NLP->>NLP: Generates 384d dense semantic embedding
    Worker->>VectorDB: Performs cosine similarity query for historical SOPs
    VectorDB-->>Worker: Returns top matching resolutions
    Worker->>LLM: Requests Summary, Recommendation & Draft Response
    LLM-->>Worker: Returns structured JSON outputs
    Worker->>DB: Persists Complaint with SLA deadline & AI metadata
    Agent->>DB: Opens Complaint in React UI
    Agent->>Agent: Reviews AI recommendations & 1-click sends response
    Agent->>DB: Marks ticket 'Resolved' -> Auto-indexes to RAG Knowledge Base
```

---

## 5. Database Schema & Entity Relationships

```mermaid
erDiagram
    USERS ||--o{ COMPLAINTS : manages
    USERS {
        int id PK
        string email UK
        string hashed_password
        string full_name
        string role
        string department
        boolean is_active
        datetime created_at
    }

    COMPLAINTS {
        int id PK
        string ticket_number UK
        string title
        text description
        string sender_email
        string category
        string department
        string sub_department
        string urgency
        string sentiment
        float confidence
        string status
        boolean is_escalated
        string assigned_to
        text ai_summary
        text ai_recommended_action
        text ai_draft_response
        text resolution_notes
        datetime created_at
        datetime resolved_at
        datetime sla_due_at
        json entities
    }

    KNOWLEDGE_ITEMS {
        int id PK
        string title
        string category
        string department
        text problem_summary
        text solution_steps
        json embedding
        datetime created_at
    }
```

---

## 6. Service Layer Specifications

### 6.1 NLP Classification Engine (`nlp_engine.py`)
- **Semantic Vector Generation**: `sentence-transformers/all-MiniLM-L6-v2` produces a 384-dimensional dense vector normalized with L2 Euclidean distance.
- **Entity Extraction**: Uses `spaCy` linguistic analysis (`en_core_web_sm`) and enterprise regexes to isolate transaction codes (`TXN-...`), order IDs (`#ORD-...`), currency figures (`$`, `USD`, `INR`), dates, and emails.
- **Urgency Matrix**:
  - `Critical` (4-hour SLA): Financial loss, service outages, security compromises.
  - `High` (8-hour SLA): Billing discrepancies, inaccessible portals, urgent deadlines.
  - `Medium` (24-hour SLA): Inconveniences, functional glitches.
  - `Low` (48-hour SLA): General queries and feedback.

### 6.2 Unified LLM Provider Interface (`llm_service.py`)
Provides automated resilience through a 3-tier cascade:
1. **Tier 1 (Groq API)**: Sub-second cloud inference with `llama-3.3-70b-versatile`.
2. **Tier 2 (Ollama Local)**: Air-gapped on-premise execution via `http://localhost:11434`.
3. **Tier 3 (Deterministic Heuristic Engine)**: Rule-based template generator that guarantees the application **never fails or hangs** if network or LLMs are unavailable.

### 6.3 Retrieval-Augmented Generation (`rag_service.py`)
When a complaint is triaged:
1. The complaint's semantic vector is queried against `KnowledgeItem` records.
2. Top-K similar cases with cosine similarity $\ge 0.70$ are supplied as authoritative operational context to the LLM.
3. Upon ticket resolution, support agents can toggle "Index solution into RAG Knowledge Base", facilitating continuous organizational learning.

---

## 7. Security & API Authentication
- **Authentication**: Stateless JSON Web Tokens (JWT) signed with HMAC-SHA256 (`HS256`).
- **Password Security**: Passwords hashed using `bcrypt` via PassLib.
- **CORS**: Configurable cross-origin resource sharing headers.
- **Gmail OAuth 2.0**: Read-only least-privilege scope (`https://www.googleapis.com/auth/gmail.readonly`).
