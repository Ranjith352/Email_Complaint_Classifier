# AutoTriage AI - Enterprise Complaint Classification, Routing & Resolution Platform

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18.2-61DAFB.svg)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC.svg)](https://tailwindcss.com/)
[![PostgreSQL & pgvector](https://img.shields.io/badge/Database-PostgreSQL_%2B_pgvector-336791.svg)](https://github.com/pgvector/pgvector)
[![Pytest Suite](https://img.shields.io/badge/Testing-86%20Passed-brightgreen.svg)](https://pytest.org/)

An enterprise-grade, end-to-end AI platform that automates customer complaint ingestion from Gmail, performs multi-level taxonomy classification, executes Hugging Face sentiment and configurable emotion analysis, extracts 10 core entity types with Named Entity Recognition (NER), runs hybrid urgency detection, calculates deterministic multi-factor priority scores, applies confidence-tiered routing with human-in-the-loop review, manages database-configured routing rules, verifies 7-step agent capacity assignments with team queue fallbacks, and drafts empathetic RAG-backed resolutions using Groq Cloud (`llama-3.3-70b-versatile`) and local Ollama (`llama3`).

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

### 11. Dual Generative AI & pgvector RAG
- **Groq Cloud**: Ultra-fast inference with `llama-3.3-70b-versatile`.
- **Local Ollama**: Offline fallback with `llama3`.
- **pgvector Semantic Search**: 384-dimensional embeddings match incoming complaints against company SOPs, refund policies, and historical resolutions.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, Vite, React Router, Axios, Tailwind CSS, Recharts, Lucide Icons |
| **Backend** | FastAPI, Python 3.12, Pydantic v2, SQLAlchemy 2.0, Alembic, JWT Auth |
| **Database & Vector** | PostgreSQL 16, `pgvector` (with automatic SQLite fallback for local testing) |
| **NLP & AI** | Hugging Face Transformers, Sentence Transformers, spaCy, Scikit-learn |
| **Generative AI** | Groq Cloud API, Ollama (Local LLM), RAG Pipeline |
| **Email Ingestion** | Gmail API, Google OAuth 2.0 |
| **Testing** | Pytest, FastAPI TestClient, Asyncio (86 passing automated tests) |

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
GROQ_API_KEY=your_groq_api_key_here
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

Run the complete backend test suite across all 86 unit and integration tests:
```bash
pytest backend/app/tests -v
```

### Test Coverage (86 Tests Passing):
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

1. **Groq Cloud API**:
   - Set `GROQ_API_KEY=your_key_here` in `.env` for ultra-fast Llama-3 inference.
2. **Local Ollama**:
   - Run `ollama run llama3` and set `OLLAMA_BASE_URL=http://localhost:11434` in `.env`.
3. **Gmail API**:
   - Place OAuth client credentials as `credentials.json` in the root directory.
4. **Configurable Database Rules**:
   - Manage routing rules dynamically via `POST /api/routing-rules` or the frontend settings interface without code deployments.
