# AutoTriage AI - Intelligent Complaint Classification & Resolution System

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18.2-61DAFB.svg)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC.svg)](https://tailwindcss.com/)
[![PostgreSQL & pgvector](https://img.shields.io/badge/Database-PostgreSQL_%2B_pgvector-336791.svg)](https://github.com/pgvector/pgvector)
[![Pytest Suite](https://img.shields.io/badge/Testing-Pytest-yellow.svg)](https://pytest.org/)

An enterprise-grade, end-to-end AI platform that automates customer complaint ingestion from Gmail, performs multi-label categorization and SLA urgency assignment, executes pgvector RAG semantic search, and generates empathetic resolution drafts using Groq Cloud and local Ollama LLMs.

---

## 🚀 Key Features

1. **Automated Gmail Ingestion**: Seamless OAuth 2.0 integration polling labeled incoming messages.
2. **NLP & Semantic Embeddings**: Generates 384-dimensional dense semantic vectors using `sentence-transformers` (`all-MiniLM-L6-v2`) with `spaCy` entity extraction.
3. **pgvector RAG Retrieval**: Queries PostgreSQL `pgvector` for highest cosine similarity matches against historical resolutions and standard operating procedures (SOPs).
4. **Dual Generative AI Engine**:
   - **Groq API**: Sub-second cloud inference (`llama-3.3-70b-versatile`).
   - **Local Ollama**: 100% private offline inference (`llama3`, `mistral`).
   - **Deterministic Fallback**: In-memory rule engine guarantees 100% system uptime.
5. **Modern Single Page Application (SPA)**:
   - React 18, Vite, React Router, and Tailwind CSS with custom glassmorphic styling.
   - Interactive Recharts analytics (Department volume velocity, SLA tracking, Emotion radar).
   - Real-time AI Triage Drawer (Executive summary, RAG advice, 1-click draft response generator).
6. **Robust Backend API**:
   - FastAPI REST API with automatic interactive Swagger/OpenAPI documentation (`/docs`).
   - JWT stateless Bearer authentication with bcrypt password security.
   - SQLAlchemy 2.0 with automated fallback to SQLite if PostgreSQL is unconfigured.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React, Vite, React Router, Axios, Tailwind CSS, Recharts, Lucide Icons |
| **Backend** | FastAPI, Python 3.12, Pydantic v2, SQLAlchemy 2.0, Alembic, JWT Auth |
| **Database & Vector** | PostgreSQL 16, `pgvector` (with SQLite fallback) |
| **NLP & AI** | Hugging Face Transformers, Sentence Transformers, spaCy, Scikit-learn |
| **Generative AI** | Groq Cloud API, Ollama (Local LLM), RAG Pipeline |
| **Email Ingestion** | Gmail API, Google OAuth 2.0 |
| **Testing** | Pytest, FastAPI TestClient, Asyncio |
| **Documentation** | Swagger/OpenAPI, `README.md`, `ARCHITECTURE.md` |

---

## ⚡ Quick Start Guide

### 1. Clone the Repository & Configure Environment
```bash
git clone https://github.com/Ranjith352/Email_Complaint_Classifier.git
cd Email_Complaint_Classifier
cp .env.example .env
```

### 2. (Optional) Launch PostgreSQL with pgvector via Docker
If you wish to run a dedicated PostgreSQL 16 instance with `pgvector`:
```bash
docker-compose up -d
```
> **Note**: If you don't run PostgreSQL, the backend automatically initializes an in-memory/local SQLite database with cosine vector support so you can test instantly.

### 3. Start the FastAPI Backend
```bash
# Create and activate Python virtual environment
python -m venv venv
.\venv\Scripts\activate      # On Windows
# source venv/bin/activate    # On Linux/macOS

# Install backend dependencies
pip install -r backend/requirements.txt

# Launch FastAPI development server
uvicorn backend.app.main:app --reload --port 8000
```
Interactive Swagger API documentation will be available at: **http://127.0.0.1:8000/docs**

### 4. Start the React Frontend
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

Run the backend Pytest suite:
```bash
pytest backend/app/tests -v
```

Tests include:
- `test_api_auth.py`: JWT token generation, unauthorized access protection, `/me` profile retrieval.
- `test_api_complaints.py`: CRUD lifecycle, dynamic SLA deadlines, ticket resolution, knowledge base indexing.
- `test_ai_services.py`: Sentence Transformer embeddings, cosine similarity RAG, Groq/Ollama LLM fallbacks.

---

## 📖 System Architecture

For in-depth architectural diagrams, database ERD, sequence diagrams, and pipeline design, review:
👉 **[ARCHITECTURE.md](ARCHITECTURE.md)**

---

## 🔒 Security & OAuth Configuration

1. **Gmail API**:
   - Create a Google Cloud project with the Gmail API enabled.
   - Download OAuth 2.0 client credentials as `credentials.json` in the project root.
   - Run the sync from the UI or call `/api/v1/gmail/sync` to authorize the read-only scope.
2. **Groq API**:
   - Obtain a free API key from [Groq Cloud Console](https://console.groq.com/).
   - Add `GROQ_API_KEY=your-key-here` to your `.env` file.
3. **Local Ollama**:
   - Install [Ollama](https://ollama.com/) and run `ollama run llama3`.
   - Set `OLLAMA_BASE_URL=http://localhost:11434` in `.env`.
