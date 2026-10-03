# Backend - Agentic SOV Cleansing and Intelligence System

FastAPI backend application implementing the multi-agent pipeline for commercial property SOV processing.

---

## 📁 Backend Directory Structure

```text
backend/
├── app/
│   ├── __init__.py
│   │
│   ├── agents/                   # Multi-Agent Modules
│   │   ├── __init__.py
│   │   ├── sheet_agent.py        # Agent 1: Sheet Intelligence
│   │   ├── schema_agent.py       # Agent 2: Schema Mapping (17 standard SOV fields)
│   │   ├── quality_agent.py      # Agent 3: Data Quality & Reasoning
│   │   └── transformation_agent.py # Agent 4: Controlled Transformation
│   │
│   ├── models/                   # Pydantic Schemas (Integration Contracts)
│   │   ├── __init__.py
│   │   ├── sheet_models.py
│   │   ├── schema_models.py
│   │   ├── quality_models.py
│   │   ├── review_models.py
│   │   ├── transformation_models.py
│   │   └── audit_models.py
│   │
│   ├── orchestration/            # State & Pipeline Coordinator
│   │   ├── __init__.py
│   │   ├── state.py              # SOVProcessingState
│   │   └── orchestrator.py       # PipelineOrchestrator
│   │
│   ├── review/                   # Human Review Service
│   │   ├── __init__.py
│   │   └── human_review.py
│   │
│   ├── audit/                    # Audit Trail Service
│   │   ├── __init__.py
│   │   └── audit_service.py
│   │
│   ├── services/                 # Utility Integrations
│   │   ├── __init__.py
│   │   ├── excel_service.py      # Spreadsheet I/O (Pandas / OpenPyXL)
│   │   ├── llm_service.py        # LLM Client (OpenAI / Azure)
│   │   └── supabase_service.py   # Persistence & storage
│   │
│   └── main.py                   # FastAPI REST API
│
├── tests/                        # Pytest Test Suite
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_agents.py
│   ├── test_orchestrator.py
│   └── test_api.py
├── pytest.ini
├── requirements.txt
└── README.md
```

---

## 🛠️ Setup & Local Development

### 1. Create Virtual Environment
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Tests
```bash
pytest
```

### 4. Start the Development Server
```bash
uvicorn app.main:app --reload --port 8000
```

Access Swagger UI at: `http://localhost:8000/docs`
