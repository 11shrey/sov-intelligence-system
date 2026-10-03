# Agent Integration Contracts

This document specifies the exact data contracts, inputs, outputs, and integration boundaries for each agent in the SOV Cleansing pipeline.

All inter-agent communication is governed strictly by the shared Pydantic models in `backend/app/models/` and coordinated via `SOVProcessingState` in `backend/app/orchestration/state.py`.

---

## 1. Summary of Contracts

| Agent | Input Contract | Output Contract | Primary Target Model |
| :--- | :--- | :--- | :--- |
| **Agent 1: Sheet Intelligence** | Raw Excel file / Sheet metadata | Candidate sheets & Header row indices | `SheetAnalysis` |
| **Agent 2: Schema Mapping** | Raw headers & sample rows from selected sheet | Mappings to the 17 Standard SOV Fields | `SchemaMapping` |
| **Agent 3: Data Quality** | Tabular data aligned to mapped schema | Detected quality issues & proposed fixes | `QualityIssue`, `Recommendation` |
| **Human Review Gate** | List of `Recommendation` items | Human decisions (`approve`, `reject`, `edit`) | `ReviewDecision` |
| **Agent 4: Transformation** | Tabular data + approved `ReviewDecision` items | Transformed clean dataset & mutation log | `Transformation`, `AuditEntry` |

---

## 2. Shared Data Models

### 2.1 Standard SOV Schema Target Fields

The canonical schema contains exactly 17 target fields:
```python
TARGET_SOV_FIELDS = [
    "Reference",
    "Address",
    "City",
    "State",
    "Zip",
    "County",
    "Country",
    "Building Value",
    "Contents",
    "BI",
    "Occupancy",
    "Construction",
    "Storeys",
    "Number of Buildings",
    "Year Built",
    "Fire Sprinklers (Y/N)",
    "Other",
]
```

---

### 2.2 Sheet Intelligence (`SheetAnalysis`)

```python
class SheetAnalysis(BaseModel):
    sheet_name: str
    is_candidate: bool
    header_row: int | None
    confidence: float  # Value between 0.0 and 1.0
    reasoning: str
```

**Agent 1 Behavior:**
- Analyzes every tab in the uploaded Excel workbook.
- Predicts `is_candidate = True` for tabs containing location listings.
- Identifies the 0-indexed or 1-indexed `header_row`.
- Populates `state.sheet_analysis` and selects `state.selected_sheet`.

---

### 2.3 Schema Mapping (`SchemaMapping`)

```python
class SchemaMapping(BaseModel):
    source_column: str
    target_field: str  # Must be one of the 17 TARGET_SOV_FIELDS or 'Unmapped'
    confidence: float  # Value between 0.0 and 1.0
    method: str  # e.g., 'exact_match', 'fuzzy_match', 'llm_semantic'
    reasoning: str
```

**Agent 2 Behavior:**
- Takes the headers from `state.selected_sheet` starting at `state.header_row`.
- Maps each source column to one of the 17 standard SOV fields.
- Populates `state.schema_mappings`.

---

### 2.4 Data Quality & Reasoning (`QualityIssue` & `Recommendation`)

```python
class QualityIssue(BaseModel):
    row: int
    field: str
    issue: str
    severity: str  # 'info', 'warning', 'error', 'critical'
    current_value: Any
    recommendation: str | None = None
    confidence: float = 1.0
    reasoning: str = ""


class Recommendation(BaseModel):
    row: int
    field: str
    action: str  # e.g., 'format_currency', 'impute_state', 'standardize_occupancy', 'fix_zip'
    current_value: Any
    proposed_value: Any
    confidence: float  # Value between 0.0 and 1.0
    reasoning: str
```

**Agent 3 Behavior:**
- Scans the normalized dataframe rows.
- Flags validation issues (missing zip codes, unparseable currency formats, unstandardized occupancy codes).
- Proposes explicit value fixes in `state.recommendations`.

---

### 2.5 Human Review Decision (`ReviewDecision`)

```python
class ReviewDecision(BaseModel):
    row: int
    field: str
    decision: Literal["approve", "reject", "edit"]
    edited_value: Any | None = None
    reviewer: str = "human"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

**Human Review Behavior:**
- Reviews each item in `state.recommendations`.
- Submits review decisions back to the API.
- Populates `state.review_decisions`.

---

### 2.6 Controlled Transformation (`Transformation`)

```python
class Transformation(BaseModel):
    row: int
    field: str
    before: Any
    after: Any
    transformation: str  # e.g., 'applied_currency_formatting', 'applied_human_edit'
    approved_by: str
    approved_at: datetime = Field(default_factory=datetime.utcnow)
```

**Agent 4 Behavior:**
- Executes *only* approved decisions (`decision == 'approve'` or `decision == 'edit'`).
- Rejects non-approved changes.
- Records all mutations in `state.approved_transformations`.
- Generates the final cleaned dataset.

---

### 2.7 Audit Entry (`AuditEntry`)

```python
class AuditEntry(BaseModel):
    job_id: str
    user_id: str
    action: str
    source: str
    target: str
    before: Any
    after: Any
    confidence: float | None = None
    approver: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

---

## 3. Shared State Pipeline Container (`SOVProcessingState`)

```python
class SOVProcessingState(BaseModel):
    job_id: str
    file_info: FileInfo
    status: JobStatus = JobStatus.PENDING

    # Step 1: Sheet Intelligence
    sheet_analysis: list[SheetAnalysis] = []
    selected_sheet: str | None = None
    header_row: int | None = None

    # Step 2: Schema Mapping
    schema_mappings: list[SchemaMapping] = []

    # Step 3: Data Quality
    quality_issues: list[QualityIssue] = []
    recommendations: list[Recommendation] = []

    # Step 4: Human Review Gate
    review_decisions: list[ReviewDecision] = []

    # Step 5: Controlled Transformation
    approved_transformations: list[Transformation] = []
    final_output_path: str | None = None

    # Audit Log
    audit_log: list[AuditEntry] = []

    metadata: dict[str, Any] = {}
    errors: list[str] = []
```

---

## 4. Workstream Guidelines for Teammates

1. **Do not modify the model schemas directly** without consulting the team, as other agents rely on these exact types.
2. Implement your logic inside your respective agent file:
   - `sheet_agent.py` for Sheet Intelligence
   - `schema_agent.py` for Schema Mapping
   - `quality_agent.py` for Quality & Recommendations
   - `transformation_agent.py` for Controlled Transformations
3. Each agent must implement a `run(state: SOVProcessingState) -> SOVProcessingState` method.
