# System Architecture: Agentic SOV Cleansing & Intelligence System

## 1. Architectural Vision

The **Agentic SOV Cleansing and Intelligence System** is an AI-assisted pipeline designed to process messy, heterogeneous Statement of Values (SOV) Excel workbooks submitted by commercial insurance brokers.

The architecture emphasizes:
1. **Separation of Concerns:** Each intelligence capability is encapsulated within a dedicated agent.
2. **Explicit Integration Contracts:** Communication between agents occurs strictly through Pydantic data schemas.
3. **Deterministic Human-in-the-Loop:** Automated fixes are treated as *recommendations* until explicitly reviewed and approved by human risk engineers / underwriters.
4. **End-to-End Auditability:** Every data transformation records before/after state, justification, confidence, and approver identity.
5. **Hackathon-Friendly Simplicity:** Lightweight, unified FastAPI backend without excessive microservice overhead.

---

## 2. High-Level Flow Diagram

```text
+-------------------------------------------------------------+
|                      React UI (Frontend)                    |
|  - File Upload & Sheet Selector                             |
|  - Schema Mapping Alignment Table                           |
|  - Data Quality Issue Review & Fix Approvals                |
|  - Audit Log Viewer & SOV Export                            |
+------------------------------+------------------------------+
                               │ HTTP / JSON
                               ▼
+-------------------------------------------------------------+
|                     FastAPI REST Backend                    |
|  - /api/jobs/upload                                         |
|  - /api/jobs/{id}/recommendations                           |
|  - /api/jobs/{id}/review                                    |
|  - /api/jobs/{id}/transform                                 |
|  - /api/jobs/{id}/download                                  |
+------------------------------+------------------------------+
                               │
                               ▼
+-------------------------------------------------------------+
|                   Pipeline Orchestrator                     |
|  Manages lifecycle transitions & pipeline progression       |
+------------------------------+------------------------------+
                               │
                               ▼
+-------------------------------------------------------------+
|                     Shared State Object                     |
|                   (SOVProcessingState)                      |
|                                                             |
|  [Sheet Info] -> [Schema Map] -> [Issues] -> [Decisions]    |
+--------------+---------------+--------------+---------------+
               │               │              │               │
               ▼               ▼              ▼               ▼
        +--------------+ +------------+ +------------+ +--------------+
        |   Agent 1    | |  Agent 2   | |  Agent 3   | |   Agent 4    |
        |    Sheet     | |   Schema   | |    Data    | |  Controlled  |
        | Intelligence | |  Mapping   | |  Quality   | |Transformation|
        +--------------+ +------------+ +------------+ +--------------+
                                               │
                                               ▼
                                    +--------------------+
                                    | Human Review Gate  |
                                    | (Approve / Edit /  |
                                    |     Reject)        |
                                    +--------------------+
                                               │
                                               ▼
+-------------------------------------------------------------+
|                  Audit & Export Services                    |
|  - Structured audit trail (AuditEntry records)              |
|  - Export standardized SOV Excel workbook (17 columns)      |
|  - Supabase database & storage integration                  |
+-------------------------------------------------------------+
```

---

## 3. Component Breakdown

### 3.1 Frontend (React UI)
- **File Upload:** Uploads `.xlsx` or `.xls` workbooks with live progress indicators.
- **Sheet Intelligence View:** Displays candidate sheets with confidence scores, allowing manual override if needed.
- **Schema Mapping Table:** Side-by-side mapping between raw columns and the 17 standard SOV fields with confidence badges.
- **Quality & Recommendation Grid:** Shows detected issues (missing zip codes, invalid occupancy codes, currency anomalies) and proposed fixes.
- **Review Controls:** One-click approve/reject or inline editing for each recommendation.
- **Export & Audit:** Download cleaned SOV spreadsheet and view complete transformation history.

### 3.2 Backend API (FastAPI)
- Acts as the API gateway and coordinator.
- Stateless HTTP request handling backed by file storage and Supabase for job persistence.
- Async support for non-blocking agent pipeline execution.

### 3.3 Pipeline Orchestrator
- Coordinates execution flow from file ingest to final export.
- Passes the `SOVProcessingState` container through each pipeline stage.
- Enforces execution gates (ensuring Agent 4 never runs without human review decisions).

### 3.4 The Four Intelligence Agents

#### Agent 1: Sheet Intelligence Agent
- **Purpose:** Identifies which sheet(s) in a multi-tab workbook contain property schedules.
- **Mechanism:** Inspects sheet names, dimensions, cell contents, and candidate header rows.
- **Output:** List of `SheetAnalysis` objects and selected primary candidate.

#### Agent 2: Schema Mapping Agent
- **Purpose:** Maps heterogeneous source column names to the standard 17 SOV fields.
- **Mechanism:** Rule-based heuristics, fuzzy string matching, and LLM semantic mapping.
- **Output:** List of `SchemaMapping` objects.

#### Agent 3: Data Quality & Reasoning Agent
- **Purpose:** Scans the mapped SOV data for anomalies, missing fields, format errors, and domain inconsistencies (e.g. invalid construction codes, negative values).
- **Mechanism:** Deterministic validation rules combined with LLM semantic reasoning for ambiguity.
- **Output:** List of `QualityIssue` items and actionable `Recommendation` proposals.

#### Agent 4: Controlled Transformation Agent
- **Purpose:** Safely executes data mutations corresponding *only* to approved human review decisions.
- **Mechanism:** Deterministic row/column transformations; generates `Transformation` and `AuditEntry` records.
- **Output:** Cleaned dataset and transformation ledger.

### 3.5 Human Review & Audit System
- **Human Review Service:** Ingests reviewer decisions (`approve`, `reject`, `edit`) and validates payload integrity.
- **Audit Service:** Records an immutable timeline of changes detailing:
  - Timestamp
  - Row & Field
  - Value Before vs. Value After
  - Agent confidence & Human reviewer ID

### 3.6 Services Layer
- **Excel Service (`excel_service.py`):** OpenPyXL / Pandas wrapper for reading raw sheets, header extraction, and writing standardized output files.
- **LLM Service (`llm_service.py`):** Centralized LLM client interface (supports structured JSON outputs with Pydantic).
- **Supabase Service (`supabase_service.py`):** Persistence layer for storing job states, audit logs, and file artifacts.

---

## 4. Target Standard SOV Schema

The system standardizes all inputs into the canonical 17 property underwriting fields:

| Field Name | Description | Example Values |
| :--- | :--- | :--- |
| `Reference` | Internal or location ID | `LOC-001`, `Bldg A` |
| `Address` | Street address line | `123 Commercial Way` |
| `City` | Municipality | `Chicago` |
| `State` | 2-letter state or province code | `IL`, `CA`, `NY` |
| `Zip` | Postal / Zip code | `60601`, `90210-1234` |
| `County` | County name | `Cook`, `Orange` |
| `Country` | Country name / ISO code | `USA`, `United States` |
| `Building Value` | Replacement cost of structure | `$2,500,000`, `2500000` |
| `Contents` | Business personal property value | `$500,000`, `500000` |
| `BI` | Business Interruption limit/value | `$1,000,000` |
| `Occupancy` | Building occupancy / usage description | `Office`, `Warehouse`, `Retail` |
| `Construction` | Construction type (e.g. ISO classes) | `MFR`, `Frame`, `Joisted Masonry` |
| `Storeys` | Number of floors | `4`, `12` |
| `Number of Buildings` | Building count on site | `1`, `3` |
| `Year Built` | Year of initial construction | `1998`, `2015` |
| `Fire Sprinklers (Y/N)` | Fire suppression system presence | `Y`, `N`, `Yes`, `No` |
| `Other` | Additional coverages / unmapped attributes | `Pool, Fence` |
