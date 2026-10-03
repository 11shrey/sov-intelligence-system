# Agentic SOV Cleansing and Intelligence System

An AI-driven Statement of Values (SOV) processing pipeline for commercial insurance property underwriting. The system automates complex sheet detection, schema mapping to standard SOV fields, data quality checks, human-in-the-loop validation, and auditable data transformations.

---

## 🏗️ Architecture Overview

The system operates via a sequential multi-agent pipeline orchestrated through a unified shared state, with explicit human review gates prior to executing data transformations.

```text
React UI (Frontend)
       │
       ▼
FastAPI Server (Backend)
       │
       ▼
Pipeline Orchestrator
       │
       ▼
  [Shared State]
       │
       ├──► Agent 1: Sheet Intelligence Agent (Detect candidate sheets & header rows)
       │
       ├──► Agent 2: Schema Mapping Agent (Map source columns to 17 standard SOV fields)
       │
       ├──► Agent 3: Data Quality & Reasoning Agent (Detect anomalies, inconsistencies & propose fixes)
       │
       ├──► [Human Review Gate] (Approve, reject, or edit recommendations)
       │
       ├──► Agent 4: Controlled Transformation Agent (Apply approved mutations safely)
       │
       └──► Audit Logger & Export Service (Immutable audit trail & clean Excel/CSV output)
```

---

## 🎯 Target Standard SOV Schema (17 Fields)

The system normalizes incoming commercial property data into the following 17 canonical SOV attributes:

1. `Reference`
2. `Address`
3. `City`
4. `State`
5. `Zip`
6. `County`
7. `Country`
8. `Building Value`
9. `Contents`
10. `BI` (Business Interruption)
11. `Occupancy`
12. `Construction`
13. `Storeys`
14. `Number of Buildings`
15. `Year Built`
16. `Fire Sprinklers (Y/N)`
17. `Other`

---

## 📂 Repository Structure

```text
sov-intelligence-system/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   │
│   │   ├── agents/                   # Agent modules (each teammate owns their agent)
│   │   │   ├── __init__.py
│   │   │   ├── sheet_agent.py        # Agent 1: Sheet Intelligence
│   │   │   ├── schema_agent.py       # Agent 2: Schema Mapping
│   │   │   ├── quality_agent.py      # Agent 3: Data Quality & Reasoning
│   │   │   └── transformation_agent.py # Agent 4: Controlled Transformation
│   │   │
│   │   ├── models/                   # Shared Pydantic data contracts
│   │   │   ├── __init__.py
│   │   │   ├── sheet_models.py       # Sheet analysis schemas
│   │   │   ├── schema_models.py      # Schema mapping schemas & 17 SOV fields
│   │   │   ├── quality_models.py     # Quality issues & recommendations
│   │   │   ├── review_models.py      # Human review decisions
│   │   │   ├── transformation_models.py # Transformation records
│   │   │   └── audit_models.py       # Audit trail entries
│   │   │
│   │   ├── orchestration/            # Pipeline state & execution coordinator
│   │   │   ├── __init__.py
│   │   │   ├── state.py              # SOVProcessingState contract
│   │   │   └── orchestrator.py       # Pipeline orchestrator
│   │   │
│   │   ├── review/                   # Human-in-the-loop review service
│   │   │   ├── __init__.py
│   │   │   └── human_review.py
│   │   │
│   │   ├── audit/                    # Audit trail generation & service
│   │   │   ├── __init__.py
│   │   │   └── audit_service.py
│   │   │
│   │   ├── services/                 # Utility & external integrations
│   │   │   ├── __init__.py
│   │   │   ├── excel_service.py      # OpenPyXL / Pandas parsing & serialization
│   │   │   ├── llm_service.py        # LLM client abstraction (OpenAI / Azure)
│   │   │   └── supabase_service.py   # Database & blob storage integration
│   │   │
│   │   └── main.py                   # FastAPI REST API application
│   │
│   ├── tests/                        # Pytest suite
│   │   ├── test_models.py
│   │   ├── test_agents.py
│   │   ├── test_orchestrator.py
│   │   └── test_api.py
│   ├── requirements.txt
│   └── README.md
│
├── frontend/                         # React UI (Vite / TypeScript / Modern CSS)
│   ├── src/
│   ├── package.json
│   └── README.md
│
├── docs/                             # Architecture, API & Agent specification docs
│   ├── architecture.md               # System architectural blueprints
│   ├── api-contract.md               # REST API endpoints & payloads
│   └── agent-contracts.md            # Agent boundaries & Pydantic contracts
│
├── .env.example                      # Environment variables template
├── .gitignore
├── README.md                         # Project documentation
└── LICENSE                           # MIT License
```

---

## 👥 Team Workstreams & Module Ownership

| Workstream | Directory / File | Key Responsibilities |
| :--- | :--- | :--- |
| **Agent 1: Sheet Intelligence** | `backend/app/agents/sheet_agent.py` | Detect candidate SOV tabs in multi-sheet workbooks, locate header rows, evaluate confidence. |
| **Agent 2: Schema Mapping** | `backend/app/agents/schema_agent.py` | Map raw column headers to the 17 standard SOV fields using semantic & heuristic matching. |
| **Agent 3: Data Quality** | `backend/app/agents/quality_agent.py` | Identify formatting anomalies, currency mismatches, missing values, occupancy/construction validations. Propose recommendations. |
| **Agent 4: Transformation** | `backend/app/agents/transformation_agent.py` | Execute approved changes deterministically on tabular data, ensuring traceability. |
| **Human Review & Audit** | `backend/app/review/` & `backend/app/audit/` | Collect human review decisions, enforce approval gates, record immutable audit logs. |
| **Orchestrator & Backend API** | `backend/app/orchestration/` & `backend/app/main.py` | Manage pipeline lifecycle, state persistence, REST API endpoints. |
| **Frontend UI** | `frontend/` | File upload, interactive sheet selection, schema mapping review, data quality diff table, export manager. |

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ (for frontend)

### Backend Setup
```bash
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
# source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy ..\.env.example .env

# 5. Run tests
pytest

# 6. Start the API server
uvicorn app.main:app --reload --port 8000
```

The Swagger interactive API documentation will be available at: `http://localhost:8000/docs`

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 📖 Documentation
- [Architecture Blueprint](docs/architecture.md)
- [Agent Input / Output Contracts](docs/agent-contracts.md)
- [REST API Specifications](docs/api-contract.md)
