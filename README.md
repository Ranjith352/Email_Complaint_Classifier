<div align="center">

# ⚡ AutoTriage AI
### Enterprise Complaint Classification, RAG Routing & Resolution Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2-61DAFB.svg?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC.svg?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16_%2B_pgvector-336791.svg?style=for-the-badge&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

<p align="center">
  <b>An end-to-end intelligent complaint management system powering automated email ingestion, multi-level taxonomy classification, deterministic SLA priority scoring, semantic duplicate detection, and strictly grounded RAG responses.</b>
</p>

[Key Features](#-key-features) • [System Architecture](#-system-architecture) • [AI & NLP Pipeline](#-ainlp-pipeline) • [Quick Start](#-quick-start-guide) • [API Reference](#-api-documentation) • [Contributing](#-contributing)

</div>

---

> [!IMPORTANT]
> **Security & Credentials Advisory**: All credentials, secret keys, PostgreSQL database passwords, Google OAuth client secrets, and third-party API keys (e.g., Groq API, Gmail OAuth tokens) must be created and configured by the application owner. Never commit production secrets, tokens, or `.env` files into public source repositories.

---

## 📖 Overview

In modern customer support operations, handling incoming complaints across fragmented communication channels (email, web portals, forms) leads to triage delays, subjective prioritization, and SLA breaches. 

**AutoTriage AI** transforms this process into a fully automated, auditable, and resilient triage pipeline. It connects directly to mailboxes via the Gmail API, strips boilerplate signatures and reply chains, executes multi-task NLP (intent classification, sentiment polarity, 6-target emotion analysis, and 10-class Named Entity Recognition), computes a deterministic mathematical priority score, identifies duplicate tickets through dense vector similarity (`pgvector`), and routes tickets to qualified support agents. Furthermore, support teams are assisted by an enterprise RAG copilot grounded strictly in corporate policies.

```mermaid
flowchart LR
    A[Gmail / Web / API] --> B[Text Cleaner & Normalizer]
    B --> C[AI Multi-Task Orchestrator]
    C --> D[Deterministic Priority Engine]
    C --> E[Semantic Vector Indexing]
    D --> F[Database Routing Rules]
    F --> G[7-Factor Agent Capacity Balancer]
    G --> H[Human-in-the-Loop Response Studio]
```

---

## 🎯 Business Problem & Solution

| Operational Challenge | Traditional Approach | AutoTriage AI Solution |
| :--- | :--- | :--- |
| **High Ticket Influx** | Manual reading and categorization taking 5–15 mins per ticket. | Sub-second classification across 8 core departments and dozens of categories. |
| **Subjective Prioritization** | Arbitrary urgency tags leading to missed P1 customer escalations. | Deterministic mathematical scoring (0–100) combining sentiment, SLA risk, urgency, and impact. |
| **Duplicate Inquiries** | Fragmented context with multiple agents replying to identical issues. | Continuous 384-d vector embeddings detecting duplicates with cosine similarity $\ge 0.85$. |
| **Agent Workload Imbalance** | Round-robin assignment causing burnout of specific team members. | 7-factor verified capacity matching with automatic team queue fallbacks. |
| **AI Hallucination Liability** | Unconstrained generative AI inventing non-existent refund policies. | Strict RAG policy grounding: cited chunk verification or explicit `"No relevant policy found"`. |

---

## ⚡ Key Features

- 🖥️ **Enterprise SaaS Frontend**: Dark-mode interface built with React 18 and Tailwind CSS featuring collapsible drawer navigation, KPI cards, Recharts visualizations, and custom modal confirmation dialogs.
- 🏷️ **Visual Priority Indicators**: Prominent priority beacons (`LOW` in emerald, `MEDIUM` in sky, `HIGH` in amber, and `CRITICAL` with a pulsing crimson beacon).
- 🔄 **Strict Human-in-the-Loop Response Studio**: 4-stage lifecycle (Generate $\to$ Edit $\to$ Approve $\to$ Dispatch) with server-side enforcement blocking unapproved automated sends.
- 🔍 **Dense Semantic Search & Deduplication**: Projects complaints into a 384-dimensional continuous subspace (`all-MiniLM-L6-v2`) to bridge lexical gaps (e.g., matching *"Money was deducted twice"* with *"Charged two times for the same transaction"*).
- 🚨 **Incident Detection**: Sliding-window clustering that synthesizes mass outages into active incident alerts (e.g., detecting 50 login complaints and surfacing a *Portal Authentication Failure* alert).
- 📚 **9-Stage RAG Knowledge Base**: Ingests, chunks, embeds, and manages company policies across 9 document categories with versioning and re-indexing.
- 🛡️ **Role-Based Access Control (RBAC)**: Secure access tiers for `ADMIN`, `MANAGER`, `AGENT`, and `CUSTOMER`.

---

## 🏛️ System Architecture

AutoTriage AI strictly enforces a decoupled 5-tier architecture:

```mermaid
graph TD
    subgraph Client Layer
        UI["React 18 Single Page Application<br/>(Tailwind CSS + Recharts)"]
    end

    subgraph Network Layer
        AX["Axios Client<br/>(JWT Interceptors & Error Normalization)"]
    end

    subgraph Application Server
        API["FastAPI 0.110+ ASGI Application<br/>(Modular Routers & Pydantic v2 Schemas)"]
        SVC["Business Services Layer<br/>(Routing, SLA, Assignment, Preprocessing, Lifecycle)"]
    end

    subgraph Intelligence & Storage
        DB[("PostgreSQL 16 + pgvector<br/>(Alembic Migrations)")]
        AI["AI / NLP Layer<br/>(Transformers, spaCy, Ollama / Groq)"]
    end

    UI -->|User Interactions| AX
    AX -->|REST API Calls / JSON| API
    API -->|Validated DTOs| SVC
    SVC -->|SQLAlchemy 2.0| DB
    SVC -->|Inference Requests| AI
```

### Strict Architectural Boundaries:
1. **No Database Logic inside React**: The frontend communicates exclusively via REST endpoints and never touches SQL or database drivers.
2. **No Business Logic inside React**: Priority calculation formulas, SLA countdown computations, assignment matrices, and routing rules live purely in the backend services.
3. **No AI Model Execution inside React**: Transformer pipelines, vector embeddings, and LLM inference run exclusively on the backend server or containerized model runners.
4. **Standardized JSON Envelope**: All API error responses return uniform, safe envelopes without exposing internal stack traces:
   ```json
   {
     "success": false,
     "message": "Detailed operational error description",
     "error_code": "RESOURCE_NOT_FOUND"
   }
   ```

---

## 🛠️ Technology Stack

```text
├── Frontend UI       : React 18, Vite, Tailwind CSS 3.4, Lucide Icons, Recharts
├── Backend API       : FastAPI, Python 3.12, Pydantic v2, Uvicorn, Starlette
├── Relational DB     : PostgreSQL 16, SQLAlchemy 2.0, Alembic Migrations
├── Vector Database   : pgvector (Cosine Distance <=>) with SQLite Fallback
├── NLP & ML          : Hugging Face Transformers, Sentence Transformers, spaCy, Scikit-learn
├── Generative AI     : Pluggable LLMProvider (Local Ollama, Optional Groq Cloud API)
├── Email Ingestion   : Google Gmail API, Google OAuth 2.0
└── Quality Assurance : Pytest, FastAPI TestClient, 22 Automated Test Suites
```

---

## 🧠 AI/NLP Pipeline

```mermaid
flowchart TD
    Raw[Raw Complaint / Email] --> Clean[1. Text Preprocessor<br/>HTML & Signature Stripping]
    Clean --> Classify[2. Taxonomy Intent Classifier<br/>5-Tier Progressive Hierarchy]
    Clean --> SentEmo[3. Sentiment & Emotion Analyzer<br/>DistilBERT + RoBERTa 6-Class]
    Clean --> NER[4. Named Entity Recognition<br/>10 Structured Entity Types]
    Clean --> Embed[5. Dense Vector Embeddings<br/>Sentence Transformers 384-d]
    
    Classify & SentEmo & NER --> Priority[6. Deterministic Priority Engine<br/>0-100 Score -> LOW / MED / HIGH / CRITICAL]
    Embed --> Dedupe[7. Semantic Duplicate Detection<br/>pgvector Cosine Distance >= 0.85]
    
    Priority & Dedupe --> Route[8. 8-Stage Routing & Workload Balancer<br/>7-Factor Agent Capacity Matching]
    Route --> Event[(Immutable Event Log)]
```

### 1. Progressive Classification Tiers
- **Tier 1 (Baseline)**: TF-IDF + Logistic Regression
- **Tier 2 (Alternative)**: TF-IDF + Multinomial Naive Bayes
- **Tier 3 (Transformer)**: DistilBERT (`distilbert-base-uncased`)
- **Tier 4 (Advanced Transformer)**: RoBERTa (`roberta-base`)
- **Tier 5 (Zero-Shot)**: BART MNLI (`facebook/bart-large-mnli`)

### 2. Sentiment & Emotion Analysis
- **Sentiment**: Calibrated score (-1.0 to +1.0) with discrete labels (`POSITIVE`, `NEGATIVE`, `NEUTRAL`).
- **Emotion**: Categorized into 6 target emotions (`ANGER`, `FRUSTRATION`, `FEAR`, `SADNESS`, `NEUTRAL`, `SATISFACTION`).

### 3. Named Entity Recognition (NER)
Extracts 10 structured entities into the relational `complaint_entities` table:
`PERSON` • `EMAIL` • `PHONE` • `ORDER_ID` • `TRANSACTION_ID` • `AMOUNT` • `DATE` • `PRODUCT` • `COMPANY` • `LOCATION`.

### 4. Deterministic Multi-Factor Priority Engine
$$\text{Priority} = (\text{Urgency} \times 0.30) + (\text{Sentiment} \times 0.15) + (\text{BizImpact} \times 0.20) + (\text{CustImpact} \times 0.15) + (\text{SLARisk} \times 0.20)$$

- `0 – 30`: **LOW**
- `31 – 60`: **MEDIUM**
- `61 – 80`: **HIGH**
- `81 – 100`: **CRITICAL** (Triggers immediate notification beacon and 15-minute response SLA)

---

## 🤗 Hugging Face Models

| Task | Model Checkpoint | Output Specification |
| :--- | :--- | :--- |
| **Dense Vector Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` | 384-dimensional dense semantic vectors |
| **Sentiment Analysis** | `distilbert-base-uncased-finetuned-sst-2-english` | `POSITIVE`, `NEGATIVE`, `NEUTRAL` |
| **Emotion Analysis** | `j-hartmann/emotion-english-distilroberta-base` | 6 discrete target emotions |
| **Zero-Shot Classification**| `facebook/bart-large-mnli` | Dynamic zero-shot category probabilities |
| **Named Entity Extraction** | `dslim/bert-base-NER` / spaCy `en_core_web_sm` | 10 domain entities |

---

## 🤖 LLM Architecture & Boundaries

To preserve strict regulatory compliance and prevent hallucination, generative LLMs are restricted to qualitative tasks, while deterministic code handles operational decisions:

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                           COMPUTATIONAL PARADIGMS BOUNDARY                        │
├───────────────────────────┬───────────────────────────────┬───────────────────────┤
│   Generative LLMs         │   Specialized ML/NLP Models   │   Deterministic Code  │
│   (Ollama / Groq)         │   (High Throughput & Speed)   │   (Zero Hallucination)│
├───────────────────────────┼───────────────────────────────┼───────────────────────┤
│ • 800-Word Summarization  │ • Intent Classification       │ • Priority Scoring    │
│ • Grounded Policy Recomms │ • Sentiment Analysis          │ • SLA Deadlines       │
│ • AI Assistant Copilot    │ • Emotion Analysis            │ • Routing & Tiers     │
│ • Grounded Policy Q&A     │ • Named Entity Rec (NER)      │ • Role Permissions   │
│ • Draft Email Responses   │ • Dense Vector Embeddings     │ • Workload Balancer   │
└───────────────────────────┴───────────────────────────────┴───────────────────────┘
```

- **Pluggable `LLMProvider`**: Dynamic provider interface supporting local Ollama and Groq Cloud.
- **Fail-Safe Resilience**: If Groq rate limits or fails, it automatically falls back to local Ollama. If neither is reachable, extractive fallback templates ensure tickets continue processing without crashing.

---

## ⚙️ Setup & Configuration

### 1. Prerequisites Checklist
- [x] Python 3.12+
- [x] Node.js 18+ and `npm` 9+
- [x] PostgreSQL 16 with `pgvector` *(Optional: SQLite fallback runs automatically)*
- [x] Ollama *(Optional for local LLM)* or Groq Cloud API Key

---

### 2. Environment Configuration

Copy the template to create your `.env` file:
```bash
cp .env.example .env
```

Configure your environment variables:
```env
# ============================================================
# APP SECURITY & JWT
# ============================================================
ENVIRONMENT=development
SECRET_KEY=generate_a_random_32_character_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ALGORITHM=HS256

# ============================================================
# DATABASE (PostgreSQL + pgvector or SQLite)
# ============================================================
# PostgreSQL configuration:
DATABASE_URL=postgresql://complaint_admin:YourSecurePassword123!@localhost:5432/autotriage_db
# SQLite fallback (automatic if PostgreSQL is not running):
# DATABASE_URL=sqlite:///./autotriage.db

# ============================================================
# LLM PROVIDER (Ollama or Groq)
# ============================================================
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3:8b

# Groq Cloud Settings (Optional):
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# ============================================================
# GMAIL INGESTION (Optional)
# ============================================================
GMAIL_CREDENTIALS_PATH=credentials.json
GMAIL_TOKEN_PATH=token.json
```

---

<details>
<summary><b>🦙 Click to expand Ollama Local Setup</b></summary>

1. Download and install Ollama from [ollama.com/download](https://ollama.com/download).
2. Pull a recommended model:
   ```bash
   ollama pull llama3:8b
   # or lightweight:
   ollama pull mistral:7b
   ```
3. Ensure the daemon is running at `http://localhost:11434`.
</details>

<details>
<summary><b>⚡ Click to expand Groq Cloud Setup</b></summary>

1. Sign up for an API key at [console.groq.com](https://console.groq.com/).
2. Set `LLM_PROVIDER=groq` and `GROQ_API_KEY=gsk_...` in your `.env`.
3. Never share or commit your API key.
</details>

<details>
<summary><b>🐘 Click to expand PostgreSQL & pgvector Setup</b></summary>

1. Create the database and user:
   ```sql
   CREATE USER complaint_admin WITH PASSWORD 'YourSecurePassword123!';
   CREATE DATABASE autotriage_db OWNER complaint_admin;
   GRANT ALL PRIVILEGES ON DATABASE autotriage_db TO complaint_admin;
   ```
2. Enable pgvector:
   ```sql
   \c autotriage_db
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
3. Or run using Docker:
   ```bash
   docker run -d --name autotriage-postgres \
     -e POSTGRES_DB=autotriage_db \
     -e POSTGRES_USER=complaint_admin \
     -e POSTGRES_PASSWORD=YourSecurePassword123! \
     -p 5432:5432 \
     pgvector/pgvector:pg16
   ```
</details>

<details>
<summary><b>📧 Click to expand Gmail API OAuth Setup</b></summary>

1. Enable the **Gmail API** in Google Cloud Console.
2. Create **OAuth 2.0 Client ID** credentials (Desktop Application).
3. Download the JSON credential file and save it as `credentials.json` in the project root.
4. On first sync, authorize access via the browser prompt to generate `token.json`.
</details>

---

## 🚀 Quick Start Guide

### 1. Launch FastAPI Backend
```bash
# 1. Activate virtual environment
.\venv\Scripts\activate      # Windows
# source venv/bin/activate    # Linux / macOS

# 2. Install backend dependencies
pip install -r backend/requirements.txt

# 3. Apply Alembic database migrations
alembic upgrade head

# 4. Seed enterprise departments, teams, agents, rules & complaints
python seed.py

# 5. Start development server
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```
- **Backend API**: `http://127.0.0.1:8000`
- **Swagger Documentation**: `http://127.0.0.1:8000/docs`
- **ReDoc Documentation**: `http://127.0.0.1:8000/redoc`

### 2. Launch React Frontend
```bash
# In a new terminal window:
cd frontend

# 1. Install dependencies
npm install

# 2. Start Vite development server
npm run dev
```
- **Web Application**: `http://localhost:5173`

**Default Credentials**:
- **Admin**: `admin@complaints.io` / `admin123`
- **Support Agent**: `agent@complaints.io` / `agent123`

---

## 🗄️ Database Migrations & Seeder

### Alembic Migrations
All database tables, vector indices, and foreign key relations are managed through Alembic migrations. **Do not manually run SQL DDL statements.**

```bash
# Check current migration status
alembic current

# Run pending migrations to head
alembic upgrade head

# Autogenerate a new revision after updating SQLAlchemy models
alembic revision --autogenerate -m "describe_schema_change"
```

### Enterprise Seed Data (`seed.py`)
Populate your environment with realistic corporate data:
```bash
python seed.py
```
- **8 Core Departments**: Finance, IT, HR, Sales, Customer Support, Operations, Logistics, Security
- **18 Specialized Teams & 16 Agents**: With defined skill tags and capacity limits
- **13 Database Routing Rules & SLA Matrix**: Priority escalation and department keyword routing
- **35+ Realistic Fictional Complaints**: Covering Billing, Software, Security, Payroll, Delivery, and Hardware with zero real customer PII
- **RAG Knowledge Base**: Pre-seeded policies across all 9 enterprise categories

---

## 📚 API Documentation

FastAPI exposes an interactive OpenAPI specification at `http://127.0.0.1:8000/docs`.

### Primary Endpoints:

| Category | Method | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **Auth** | `POST` | `/api/v1/auth/login` | Authenticate and obtain JWT access token |
| | `POST` | `/api/v1/auth/register` | Register an agent or administrator account |
| **Complaints** | `GET` | `/api/v1/complaints` | Paginated search, sorting, and multi-filter explorer |
| | `POST` | `/api/v1/complaints` | Ingest complaint and trigger full AI triage pipeline |
| | `GET` | `/api/v1/complaints/{id}` | Retrieve complaint record, entities, and SLA countdown |
| | `POST` | `/api/v1/complaints/{id}/generate-response` | Draft an AI customer reply citing policy |
| | `PUT` | `/api/v1/complaints/{id}/edit-response` | Edit drafted response text |
| | `POST` | `/api/v1/complaints/{id}/approve-response` | Explicit human sign-off on drafted reply |
| | `POST` | `/api/v1/complaints/{id}/send-response` | Dispatch approved email to customer |
| | `GET` | `/api/v1/complaints/{id}/similar` | Find conceptually similar tickets via vector distance |
| | `POST` | `/api/v1/complaints/{id}/merge` | Merge duplicate ticket into primary complaint |
| **Organization**| `GET` | `/api/v1/departments` | List all 8 enterprise departments |
| | `GET` | `/api/v1/teams` | List specialized teams and skill requirements |
| | `GET` | `/api/v1/agents` | List support agents with live workload counts |
| **Analytics** | `GET` | `/api/v1/analytics/dashboard` | 10 executive KPIs and status distributions |
| | `GET` | `/api/v1/analytics/charts` | 9 interactive time-series and breakdown datasets |
| **RAG & KB** | `POST` | `/api/v1/knowledge/upload` | Upload and chunk enterprise policy documents |
| | `POST` | `/api/v1/knowledge/query` | RAG query answering citing company documents |
| **Ingestion** | `POST` | `/api/v1/emails/sync` | Trigger on-demand Gmail inbox ingestion |

---

## 🧪 Testing

The platform includes automated unit, integration, and regression suites:

```bash
# Run full automated test suite
pytest backend/app/tests -v

# Run SaaS architecture and endpoint validation
pytest backend/app/tests/test_saas_architecture_and_endpoints.py -v

# Run model versions and AI assistant tests
pytest backend/app/tests/test_model_versions_and_assistant.py -v

# Run KPI and Recharts dataset verification
pytest backend/app/tests/test_dashboard_and_table_endpoints.py -v
```

**Test Status**: ✅ **22 Automated Test Suites Passed** (100% pass rate with zero regressions).

---

## 📁 Project Structure

```text
Complaint_Classifier/
├── .env.example                               # Environment variable template
├── .gitignore                                 # Git ignore configuration
├── alembic.ini                                # Alembic configuration
├── DATABASE_SETUP.md                          # Database architecture guide
├── README.md                                  # Platform master documentation
├── seed.py                                    # Enterprise database seeder
│
├── backend/
│   ├── alembic/                               # Alembic migration revisions
│   │   ├── env.py
│   │   └── versions/
│   │       └── 888dcd2ef363_enterprise_saas_schema_sync.py
│   ├── requirements.txt                       # Backend dependencies
│   └── app/
│       ├── main.py                            # FastAPI app, routers & structured logging
│       ├── api/                               # 10 Modular REST API routers
│       │   ├── auth.py
│       │   ├── complaints.py
│       │   ├── departments.py
│       │   ├── teams.py
│       │   ├── agents.py
│       │   ├── analytics.py
│       │   ├── ai.py
│       │   ├── emails.py
│       │   ├── notifications.py
│       │   └── knowledge.py
│       ├── core/                              # Security, config & logging
│       ├── db/                                # SQLAlchemy engine & declarative base
│       ├── models/                            # Relational ORM models
│       ├── schemas/                           # Pydantic validation contracts
│       ├── services/                          # Business logic layer
│       ├── ai/                                # Machine learning & RAG engines
│       └── tests/                             # Pytest test suites
│
├── frontend/
│   ├── index.html                             # SPA HTML entry
│   ├── package.json                           # Dependencies & scripts
│   ├── vite.config.js                         # Bundler configuration
│   ├── tailwind.config.js                     # Design system tokens
│   └── src/
│       ├── App.jsx                            # Route tree & providers
│       ├── api/                               # Pure Axios API client
│       ├── components/                        # Badges, tables, skeletons, modals
│       ├── context/                           # Toast & confirmation dialog contexts
│       ├── layouts/                           # Main responsive layout frame
│       └── pages/                             # 14 Full enterprise pages
│
└── ml/                                        # Machine learning training pipelines
    ├── datasets/                              # Synthetic and feedback datasets
    ├── preprocessing/                         # Text cleaning and feature engineering
    ├── training/                              # Model training pipelines
    └── evaluation/                            # Model benchmarks and metrics
```

---

## 📸 Screenshots

| View | Preview |
| :--- | :--- |
| **Executive Triage Command Center** | *Real-time KPI metrics, SLA countdowns, priority breakdowns, and incident alerts.* |
| **Complaints Explorer** | *Multi-filter table with live search, priority beacons, and loading skeletons.* |
| **Human-in-the-Loop Response Studio** | *Grounded draft generation, in-place editing, and explicit human approval.* |
| **Knowledge Base Studio** | *Document upload, vector chunking visualization, and RAG Q&A playground.* |

---

## 🔮 Future Improvements

- [ ] **Multi-Tenant Logical Isolation**: Separate data partitions and customized routing rules per corporate client.
- [ ] **Continuous MLOps Retraining**: Automatic background model fine-tuning triggered when agents modify classifications.
- [ ] **Omnichannel Integrations**: Direct adapters for Zendesk, Freshdesk, Slack, and WhatsApp Business API.
- [ ] **Multilingual Vector Subspace**: Leveraging `paraphrase-multilingual-MiniLM-L12-v2` for cross-lingual complaint deduplication across 50+ languages.

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  <sub>Built with ❤️ for enterprise operational excellence.</sub>
</div>
