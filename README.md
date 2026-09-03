# AutoTriage AI - Intelligent Complaint Classification & Resolution System

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18.2-61DAFB.svg)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC.svg)](https://tailwindcss.com/)
[![PostgreSQL & pgvector](https://img.shields.io/badge/Database-PostgreSQL_%2B_pgvector-336791.svg)](https://github.com/pgvector/pgvector)
[![Pytest Suite](https://img.shields.io/badge/Testing-63%20Passed-brightgreen.svg)](https://pytest.org/)

An enterprise-grade, end-to-end AI platform that automates customer complaint ingestion from Gmail, performs multi-level taxonomy classification, executes Hugging Face sentiment and configurable emotion analysis, extracts 10 core entity types with Named Entity Recognition (NER), manages a 9-stage complaint lifecycle, performs RAG semantic search, and generates empathetic resolution drafts using Groq Cloud and local Ollama LLMs.

---

## 🚀 Key Features

1. **Automated Ingestion**:
   - Gmail API OAuth 2.0 polling and multi-channel ticket ingestion (Email, Web, Manual).
2. **Text Preprocessing Pipeline**:
   - Cleans HTML, strips quoted email replies (`On ... wrote:`), trims signatures, normalizes Unicode, preserves currencies and transaction codes, and detects language.
3. **5-Tier Model Progression & Governance**:
   - Baseline: TF-IDF + Logistic Regression
   - Alternative: TF-IDF + Naive Bayes
   - Transformer: DistilBERT (`distilbert-base-uncased`)
   - Advanced Transformer: RoBERTa / BERT
   - Zero-Shot: BART MNLI (`facebook/bart-large-mnli`)
   - Automated governance selects the simplest model that performs well based on sample size thresholds.
4. **Hugging Face Sentiment Analysis**:
   - Returns standardized `label` (`NEGATIVE`, `POSITIVE`, `NEUTRAL`) and `confidence` score.
5. **Configurable Emotion Analysis**:
   - Classifies customer emotion into 6 core states: `ANGER`, `FRUSTRATION`, `FEAR`, `SADNESS`, `NEUTRAL`, `SATISFACTION`.
   - Supports pluggable checkpoints (`j-hartmann/emotion-english-distilroberta-base`, `SamLowe/roberta-base-go_emotions`, `facebook/bart-large-mnli`).
6. **Named Entity Recognition (NER)**:
   - Extracts 10 critical entity types: `PERSON`, `EMAIL`, `PHONE`, `ORDER_ID`, `TRANSACTION_ID`, `AMOUNT`, `DATE`, `PRODUCT`, `COMPANY`, `LOCATION`.
   - Persists all entities automatically into `complaint_entities` database table.
7. **Complaint Lifecycle State Machine**:
   - 9-stage progression: `NEW` $\rightarrow$ `AI_ANALYZING` $\rightarrow$ `AI_ANALYZED` $\rightarrow$ `ROUTED` $\rightarrow$ `ASSIGNED` $\rightarrow$ `IN_PROGRESS` $\rightarrow$ `WAITING_FOR_CUSTOMER` $\rightarrow$ `ESCALATED` $\rightarrow$ `RESOLVED` $\rightarrow$ `CLOSED`.
   - Immutable audit trail recorded in `complaint_events`.
8. **Intelligent 7-Factor Agent Routing**:
   - Routes tickets based on: (1) Department, (2) Team, (3) Required Skill, (4) Availability, (5) Workload, (6) Max Capacity, (7) Performance Score.
9. **Dual Generative AI & pgvector RAG**:
   - Groq Cloud API (`llama-3.3-70b-versatile`) and local Ollama (`llama3`).
   - pgvector dense semantic retrieval against resolved knowledge and standard operating procedures.
10. **Modern Single Page Application (SPA)**:
    - React 18, Vite, React Router, Axios, and Tailwind CSS.
    - Interactive Recharts analytics, real-time KPI cards, and an interactive AI triage drawer.

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
| **Testing** | Pytest, FastAPI TestClient, Asyncio |
| **Documentation** | Interactive OpenAPI / Swagger (`/docs`), `README.md` |

---

## 🏗️ Architecture & Modular AI Pipeline

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
    ├── 6. Urgency & Priority Calculation (P1 - P4, SLA deadline)
    ├── 7. 384-d Embedding & Duplicate Detection
    ├── 8. Summarization & RAG Recommendation
    └── 9. 7-Factor Agent Routing & Assignment
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

Run the full backend Pytest suite:
```bash
pytest backend/app/tests -v
```

**63 Unit & Integration Tests**:
- `test_transformers_classifier.py`: BaseClassifier abstraction, category/subcategory/department routing.
- `test_model_progression.py`: 5-tier progression and sample-size model governance.
- `test_transformers_sentiment.py`: Hugging Face Transformers pipeline returning `label` and `confidence`.
- `test_transformers_emotion.py`: All 6 emotions (`ANGER`, `FRUSTRATION`, `FEAR`, `SADNESS`, `NEUTRAL`, `SATISFACTION`) and configurable model switching.
- `test_ner.py`: Extraction of all 10 entity types and database persistence in `complaint_entities`.
- `test_preprocessing.py`: Quote, signature, HTML, URL, and punctuation normalization.
- `test_lifecycle.py`: 9-stage state transitions and audit logging in `complaint_events`.
- `test_assignment.py`: 7-factor agent routing scoring algorithm.
- `test_api.py`, `test_complaints.py`, `test_auth.py`, `test_routing.py`, `test_sla.py`.

---

## 🔒 Configuration & Integrations

1. **Groq API**:
   - Set `GROQ_API_KEY=your_key_here` in `.env` for ultra-fast Llama-3 inference.
2. **Local Ollama**:
   - Run `ollama run llama3` and set `OLLAMA_BASE_URL=http://localhost:11434` in `.env`.
3. **Gmail API**:
   - Place OAuth client credentials as `credentials.json` in the root directory.
