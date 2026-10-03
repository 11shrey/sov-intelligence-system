"""Test FastAPI endpoints for SOV Intelligence System."""

import json
from io import BytesIO
from openpyxl import Workbook
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def create_mock_xlsx_bytes() -> bytes:
    """Generate in-memory sample SOV Excel workbook."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Property Schedule"
    ws.append(["Reference", "Address", "City", "State", "Zip", "Building Value", "Occupancy", "Construction"])
    ws.append(["P001", "123 Main St", "Chicago", "IL", "60601", 1000000, "Office", "Masonry"])
    ws.append(["P002", "456 Oak Ave", "Peoria", "IL", "61602", 750000, "Retail", "Frame"])
    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def test_health_check():
    """Verify health check endpoint returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_upload_and_download_formats_xlsx():
    """Verify XLSX upload, review, transform, and download in CSV, XLSX, and JSON formats."""
    file_bytes = create_mock_xlsx_bytes()

    # 1. Upload via /api/jobs/upload
    upload_res = client.post(
        "/api/jobs/upload",
        files={
            "file": (
                "property_portfolio.xlsx",
                file_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert upload_res.status_code == 201
    data = upload_res.json()
    job_id = data["job_id"]
    assert job_id is not None
    assert data["selected_sheet"] == "Property Schedule"
    assert data["header_row"] == 0

    # 2. Get recommendations
    rec_res = client.get(f"/api/jobs/{job_id}/recommendations")
    assert rec_res.status_code == 200
    recommendations = rec_res.json()["recommendations"]
    assert len(recommendations) > 0

    # 3. Submit human review
    review_res = client.post(
        f"/api/jobs/{job_id}/review",
        json={
            "decisions": [
                {
                    "row": recommendations[0]["row"],
                    "field": recommendations[0]["field"],
                    "decision": "approve",
                    "edited_value": None,
                    "reviewer": "underwriter@carrier.com",
                }
            ]
        },
    )
    assert review_res.status_code == 200

    # 4. Transform
    transform_res = client.post(f"/api/jobs/{job_id}/transform")
    assert transform_res.status_code == 200
    assert transform_res.json()["status"] == "completed"

    # 5. Audit
    audit_res = client.get(f"/api/jobs/{job_id}/audit")
    assert audit_res.status_code == 200
    assert audit_res.json()["total_entries"] > 0

    # 6. Download as CSV (default)
    dl_csv = client.get(f"/api/jobs/{job_id}/download")
    assert dl_csv.status_code == 200
    assert "text/csv" in dl_csv.headers.get("content-type", "")
    assert "cleaned_sov_" in dl_csv.headers.get("content-disposition", "")

    # 7. Download as XLSX
    dl_xlsx = client.get(f"/api/jobs/{job_id}/download?format=xlsx")
    assert dl_xlsx.status_code == 200
    assert "spreadsheetml" in dl_xlsx.headers.get("content-type", "")

    # 8. Download as JSON
    dl_json = client.get(f"/api/jobs/{job_id}/download?format=json")
    assert dl_json.status_code == 200
    assert "application/json" in dl_json.headers.get("content-type", "")
    json_data = dl_json.json()
    assert isinstance(json_data, list)
    assert "Building Value" in json_data[0]


def test_upload_csv_format():
    """Verify CSV upload works smoothly through primary endpoint and alias."""
    csv_bytes = b"Reference,Address,City,State,Zip,Building Value\nLOC-1,100 Main St,Austin,TX,78701,5000000\n"

    # Upload via primary route
    res = client.post(
        "/api/jobs/upload",
        files={"file": ("austin_sov.csv", csv_bytes, "text/csv")},
    )
    assert res.status_code == 201
    assert res.json()["selected_sheet"] == "CSV"

    # Upload via alias route
    res_alias = client.post(
        "/api/v1/sov/upload",
        files={"file": ("austin_sov_alias.csv", csv_bytes, "text/csv")},
    )
    assert res_alias.status_code == 201
    assert res_alias.json()["selected_sheet"] == "CSV"


def test_upload_json_format():
    """Verify JSON upload parses properly."""
    json_records = [
        {"Reference": "L-1", "Address": "500 Elm St", "City": "Dallas", "State": "TX", "Zip": "75201", "Building Value": 3000000}
    ]
    json_bytes = json.dumps(json_records).encode("utf-8")

    res = client.post(
        "/api/jobs/upload",
        files={"file": ("properties.json", json_bytes, "application/json")},
    )
    assert res.status_code == 201
    assert res.json()["selected_sheet"] == "JSON"


def test_upload_unsupported_format_returns_415():
    """Verify unsupported file extension returns 415 Unsupported Media Type."""
    pdf_bytes = b"%PDF-1.4 mock pdf content"
    res = client.post(
        "/api/jobs/upload",
        files={"file": ("submission.pdf", pdf_bytes, "application/pdf")},
    )
    assert res.status_code == 415
    assert "Unsupported file format" in res.json()["detail"]


def test_upload_empty_file_returns_400():
    """Verify empty file returns 400 Bad Request."""
    res = client.post(
        "/api/jobs/upload",
        files={"file": ("empty.xlsx", b"", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert res.status_code == 400


def test_job_not_found():
    """Verify 404 for nonexistent job ID across endpoints."""
    assert client.get("/api/jobs/nonexistent-job-id").status_code == 404
    assert client.get("/api/jobs/nonexistent-job-id/recommendations").status_code == 404
    assert client.get("/api/jobs/nonexistent-job-id/audit").status_code == 404
    assert client.get("/api/jobs/nonexistent-job-id/download").status_code == 404
