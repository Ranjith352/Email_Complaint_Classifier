# Database Setup & Migrations Guide

AutoTriage AI uses an enterprise-grade relational database architecture supporting **PostgreSQL with pgvector** for production environments and an automated **SQLite fallback** for local zero-dependency testing.

---

## 1. Prerequisites & Environment Configuration

Copy `.env.example` to `.env` in the repository root and configure your database connection string:

```bash
cp .env.example .env
```

Key environment variables in `.env`:

```ini
# PostgreSQL Connection (Production / Development)
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/complaints_db

# SQLite Fallback (Auto-selected if PostgreSQL is unreachable)
SQLITE_FALLBACK_URL=sqlite:///./autotriage.db
```

> [!NOTE]
> If PostgreSQL or the `vector` extension is unavailable, the application gracefully initializes a local SQLite instance at `autotriage.db` with dense vector semantic projection, ensuring zero downtime.

---

## 2. Database Migrations with Alembic

Database schema migrations are managed strictly through **Alembic**. Users and administrators never need to manually alter database tables.

### A. Apply Migrations to Latest Head
To apply all pending migrations and bring the database schema completely up to date:

```powershell
# From project root:
.\venv\Scripts\python -m alembic upgrade head

# Or directly if venv is activated:
alembic upgrade head
```

### B. Generate a New Schema Migration
When database models are modified in `backend/app/models/`, generate a new automated migration revision:

```powershell
.\venv\Scripts\python -m alembic revision --autogenerate -m "describe_migration_here"
```

Review the newly generated file in `backend/alembic/versions/` and apply it:

```powershell
.\venv\Scripts\python -m alembic upgrade head
```

### C. Inspect Current Migration State
```powershell
# Show currently applied revision
.\venv\Scripts\python -m alembic current

# Show migration history
.\venv\Scripts\python -m alembic history --verbose
```

---

## 3. Seeding Fictional Enterprise Data

To populate the database with realistic demonstration and testing data, run the unified seeder script:

```powershell
# From repository root:
.\venv\Scripts\python seed.py

# Or from backend directory:
.\venv\Scripts\python backend/seed.py
```

### Seeded Enterprise Entities:
1. **8 Core Departments**:
   - **Finance**: Billing discrepancies, refunds, payment processing, fraud chargebacks.
   - **IT**: Server outages, application bugs, account access, login timeouts, VPN issues.
   - **HR**: Employee benefits, payroll queries, leave requests, workplace policies.
   - **Sales**: Contract terms, renewal pricing, quote disputes, enterprise agreements.
   - **Customer Support**: General inquiries, VIP escalations, onboarding assistance.
   - **Operations**: Facilities, vendor management, process integrity, audits.
   - **Logistics**: Shipment tracking, courier delays, damaged goods, RMA returns.
   - **Security**: Phishing threats, unauthorized access, credential stuffing, compliance.
2. **Specialized Functional Teams**: 18 functional teams across all 8 departments (e.g., *Billing & Invoicing*, *Infrastructure & Network*, *Incident Response*).
3. **16 Fictional Agents**: Fully provisioned with department affiliations, skill tags, and workload capacity ratings.
4. **SLA Rules Matrix**: Response and resolution thresholds for `CRITICAL` (1h/4h), `HIGH` (2h/8h), `MEDIUM` (4h/24h), and `LOW` (8h/48h).
5. **Configurable Dynamic Routing Rules**: 13 automated keyword and pattern routing triggers.
6. **35+ Realistic Fictional Complaints**: Spanning Payment, Refund, Billing, Login, Network, Software, Security, Payroll, Leave, Delivery, Product, and Customer Support.
7. **RAG Policy Knowledge Base**: Seeded standard SOPs, SLA guides, and company policy manuals with semantic vector embeddings.

---

## 4. Verification & Testing

Verify that all database connections, migrations, and endpoints are healthy by executing the automated test suite:

```powershell
$env:PYTHONPATH="backend"
.\venv\Scripts\python -m pytest backend/app/tests/test_saas_architecture_and_endpoints.py -v
```
