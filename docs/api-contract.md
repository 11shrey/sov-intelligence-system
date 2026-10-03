# REST API Contract

This document outlines the API endpoints provided by the FastAPI backend for orchestrating the SOV Cleansing and Intelligence pipeline.

Base URL: `http://localhost:8000`

---

## Endpoints Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/jobs/upload` | Upload an SOV workbook and initialize processing |
| `GET` | `/api/jobs/{job_id}` | Retrieve overall job status and current pipeline state |
| `GET` | `/api/jobs/{job_id}/recommendations` | Fetch quality issues and proposed recommendations for review |
| `POST` | `/api/jobs/{job_id}/review` | Submit human review decisions (approve / reject / edit) |
| `POST` | `/api/jobs/{job_id}/transform` | Trigger Agent 4 execution on approved decisions |
| `GET` | `/api/jobs/{job_id}/audit` | Retrieve complete audit trail for a job |
| `GET` | `/api/jobs/{job_id}/download` | Download the standardized, cleaned SOV file |
| `GET` | `/health` | Service health status check |

---

## Endpoint Details

### 1. Upload SOV File
- **URL:** `/api/jobs/upload`
- **Method:** `POST`
- **Content-Type:** `multipart/form-data`
- **Request Body:**
  - `file`: Excel file (`.xlsx`, `.xls`)
- **Response (201 Created):**
```json
{
  "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "pending",
  "file_info": {
    "filename": "property_schedule_2026.xlsx",
    "file_size": 1048576,
    "uploaded_at": "2026-10-03T10:00:00Z"
  },
  "message": "File uploaded successfully. Processing initialized."
}
```

---

### 2. Get Job Status & State
- **URL:** `/api/jobs/{job_id}`
- **Method:** `GET`
- **Response (200 OK):**
```json
{
  "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "awaiting_review",
  "selected_sheet": "Location Schedule",
  "header_row": 2,
  "sheet_analysis": [
    {
      "sheet_name": "Location Schedule",
      "is_candidate": true,
      "header_row": 2,
      "confidence": 0.98,
      "reasoning": "Contains address, TIV, and occupancy column signatures."
    }
  ],
  "schema_mappings": [
    {
      "source_column": "Loc #",
      "target_field": "Reference",
      "confidence": 0.95,
      "method": "llm_semantic",
      "reasoning": "Standard location identifier."
    }
  ],
  "total_issues": 12,
  "total_recommendations": 12
}
```

---

### 3. Get Recommendations for Review
- **URL:** `/api/jobs/{job_id}/recommendations`
- **Method:** `GET`
- **Response (200 OK):**
```json
{
  "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "recommendations": [
    {
      "row": 4,
      "field": "Zip",
      "action": "fix_zip",
      "current_value": "6060",
      "proposed_value": "06060",
      "confidence": 0.99,
      "reasoning": "Prepended missing leading zero in US 5-digit postal code."
    },
    {
      "row": 8,
      "field": "Building Value",
      "action": "format_currency",
      "current_value": "$1,250,000 USD",
      "proposed_value": 1250000.0,
      "confidence": 1.0,
      "reasoning": "Normalized string currency to float numeric value."
    }
  ],
  "quality_issues": [
    {
      "row": 4,
      "field": "Zip",
      "issue": "Invalid postal code format length",
      "severity": "warning",
      "current_value": "6060",
      "recommendation": "fix_zip",
      "confidence": 0.99,
      "reasoning": "Length is 4 characters instead of standard 5."
    }
  ]
}
```

---

### 4. Submit Human Review Decisions
- **URL:** `/api/jobs/{job_id}/review`
- **Method:** `POST`
- **Request Body:**
```json
{
  "decisions": [
    {
      "row": 4,
      "field": "Zip",
      "decision": "approve",
      "edited_value": null,
      "reviewer": "underwriter_alex@carrier.com",
      "timestamp": "2026-10-03T10:05:00Z"
    },
    {
      "row": 8,
      "field": "Building Value",
      "decision": "edit",
      "edited_value": 1300000.0,
      "reviewer": "underwriter_alex@carrier.com",
      "timestamp": "2026-10-03T10:05:00Z"
    }
  ]
}
```
- **Response (200 OK):**
```json
{
  "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "decisions_recorded": 2,
  "status": "review_completed",
  "message": "Human review decisions recorded successfully."
}
```

---

### 5. Execute Controlled Transformations
- **URL:** `/api/jobs/{job_id}/transform`
- **Method:** `POST`
- **Request Body:** (Optional parameter options)
```json
{
  "apply_approved_only": true
}
```
- **Response (200 OK):**
```json
{
  "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "completed",
  "transformations_applied": 2,
  "download_url": "/api/jobs/3fa85f64-5717-4562-b3fc-2c963f66afa6/download"
}
```

---

### 6. Get Audit Log
- **URL:** `/api/jobs/{job_id}/audit`
- **Method:** `GET`
- **Response (200 OK):**
```json
{
  "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "audit_trail": [
    {
      "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "user_id": "underwriter_alex@carrier.com",
      "action": "applied_transformation",
      "source": "Zip",
      "target": "Zip",
      "before": "6060",
      "after": "06060",
      "confidence": 0.99,
      "approver": "underwriter_alex@carrier.com",
      "timestamp": "2026-10-03T10:06:00Z"
    }
  ]
}
```

---

### 7. Download Cleaned SOV
- **URL:** `/api/jobs/{job_id}/download`
- **Method:** `GET`
- **Response (200 OK):**
  - Binary streaming response with `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` or CSV.
