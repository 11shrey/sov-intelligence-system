"""Test FastAPI endpoints."""

from fastapi.testclient import TestClient
from app.main import app, orchestrator

client = TestClient(app)

_SAMPLE_COLUMNS = [
    "Loc #", "Street Address", "City", "ST", "Zip Code",
    "County", "Country", "Bldg Repl Cost", "Contents", "BI Limit",
    "Occupancy Type", "Const Type", "Stories", "Building Count",
    "Yr Built", "Fire Prot.", "Other Value",
]

_SAMPLE_MAPPED_ROWS = [
    {
        "Reference": "LOC-001",
        "Address": "100 Main St",
        "City": "Houston",
        "State": "TX",
        "Zip": "77001",
        "County": "Harris",
        "Country": "USA",
        "Building Value": 5_000_000,
        "Contents": 500_000,
        "BI": 200_000,
        "Occupancy": "Office",
        "Construction": "Masonry",
        "Storeys": 4,
        "Number of Buildings": 1,
        "Year Built": 2010,
        "Fire Sprinklers (Y/N)": "Y",
        "Other": 50_000,
    },
    # Duplicate record to generate quality defect and recommendation
    {
        "Reference": "LOC-001",
        "Address": "100 Main St",
        "City": "Houston",
        "State": "TX",
        "Zip": "77001",
        "County": "Harris",
        "Country": "USA",
        "Building Value": 5_000_000,
        "Contents": 500_000,
        "BI": 200_000,
        "Occupancy": "Office",
        "Construction": "Masonry",
        "Storeys": 4,
        "Number of Buildings": 1,
        "Year Built": 2010,
        "Fire Sprinklers (Y/N)": "Y",
        "Other": 50_000,
    },
]


def test_health_check():
    """Verify health check endpoint returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_full_api_workflow():
    """Verify upload -> get status -> get recommendations -> review -> transform -> audit -> download."""
    # 1. Upload
    file_content = b"Mock Excel binary payload"
    upload_response = client.post(
        "/api/jobs/upload",
        files={"file": ("test_portfolio.xlsx", file_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert upload_response.status_code == 201
    job_data = upload_response.json()
    job_id = job_data["job_id"]
    assert job_id is not None
    assert job_data["status"] == "awaiting_review"

    # Inject sample metadata for Agent 2 & Agent 3 (since Agent 1 is a stub workbook reader)
    orchestrator._jobs[job_id].metadata["raw_columns"] = _SAMPLE_COLUMNS
    orchestrator._jobs[job_id].metadata["mapped_rows"] = _SAMPLE_MAPPED_ROWS
    orchestrator.run_analysis_pipeline(job_id)

    # 2. Get Job Status
    status_response = client.get(f"/api/jobs/{job_id}")
    assert status_response.status_code == 200
    assert status_response.json()["job_id"] == job_id

    # 3. Get Recommendations
    rec_response = client.get(f"/api/jobs/{job_id}/recommendations")
    assert rec_response.status_code == 200
    recommendations = rec_response.json()["recommendations"]
    assert len(recommendations) > 0

    # 4. Submit Human Review Decision
    review_payload = {
        "decisions": [
            {
                "row": recommendations[0]["row"],
                "field": recommendations[0]["field"],
                "decision": "approve",
                "edited_value": None,
                "reviewer": "api_tester@carrier.com",
            }
        ],
        "notes": "Automated test approval",
    }
    review_response = client.post(f"/api/jobs/{job_id}/review", json=review_payload)
    assert review_response.status_code == 200
    assert review_response.json()["decisions_recorded"] == 1

    # 5. Execute Transformation
    transform_response = client.post(f"/api/jobs/{job_id}/transform")
    assert transform_response.status_code == 200
    assert transform_response.json()["status"] == "completed"

    # 6. Retrieve Audit Trail
    audit_response = client.get(f"/api/jobs/{job_id}/audit")
    assert audit_response.status_code == 200
    assert audit_response.json()["total_entries"] > 0

    # 7. Download Cleaned Output (.xlsx default, or .csv if requested)
    download_response = client.get(f"/api/jobs/{job_id}/download")
    assert download_response.status_code == 200
    assert (
        "application/vnd.openxmlformats" in download_response.headers.get("content-type", "")
        or "text/csv" in download_response.headers.get("content-type", "")
    )

    download_csv_response = client.get(f"/api/jobs/{job_id}/download?format=csv")
    assert download_csv_response.status_code == 200
    assert "text/csv" in download_csv_response.headers.get("content-type", "")


def test_job_not_found():
    """Verify 404 for nonexistent job."""
    response = client.get("/api/jobs/nonexistent-job-id")
    assert response.status_code == 404


def _get_sample_file_bytes() -> bytes:
    from pathlib import Path
    fixture_path = Path("tests/fixtures/sample_messy_sov.xlsx")
    assert fixture_path.exists(), "Sample SOV fixture not found"
    with open(fixture_path, "rb") as f:
        return f.read()


def test_api_upload_to_awaiting_review():
    """Requirement: POST /jobs accepts SOV file, runs Agent 1 -> Agent 2 -> Agent 3, returns job_id and AWAITING_REVIEW."""
    file_bytes = _get_sample_file_bytes()
    response = client.post(
        "/jobs",
        files={"file": ("sample_messy_sov.xlsx", file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert response.status_code == 201
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "awaiting_review"
    assert data["selected_sheet"] == "Sheet1"
    assert data["header_row"] is not None
    assert data["total_issues"] > 0
    assert data["total_recommendations"] > 0


def test_api_review_data_retrieval():
    """Requirement: GET /jobs/{job_id}/review returns schema mappings, quality issues, recommendations, status."""
    file_bytes = _get_sample_file_bytes()
    upload_res = client.post(
        "/jobs",
        files={"file": ("sample_messy_sov.xlsx", file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    job_id = upload_res.json()["job_id"]

    review_res = client.get(f"/jobs/{job_id}/review")
    assert review_res.status_code == 200
    data = review_res.json()
    assert data["job_id"] == job_id
    assert data["status"] == "awaiting_review"
    assert "schema_mappings" in data and len(data["schema_mappings"]) > 0
    assert "quality_issues" in data and len(data["quality_issues"]) > 0
    assert "recommendations" in data and len(data["recommendations"]) > 0
    assert "quality_report" in data


def test_api_agent4_cannot_run_without_human_review():
    """Requirement: Agent 4 cannot run without human review decisions."""
    file_bytes = _get_sample_file_bytes()
    upload_res = client.post(
        "/jobs",
        files={"file": ("sample_messy_sov.xlsx", file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    job_id = upload_res.json()["job_id"]

    # Attempt output download before review
    download_res = client.get(f"/jobs/{job_id}/output")
    assert download_res.status_code == 400
    assert "not been generated yet" in download_res.json()["detail"].lower()

    # Attempt review submission with empty decisions
    empty_review_res = client.post(
        f"/jobs/{job_id}/review",
        json={"decisions": [], "notes": "Empty submission"},
    )
    assert empty_review_res.status_code == 400
    assert "at least one human review decision is required" in empty_review_res.json()["detail"].lower()

    # Job status must remain awaiting_review
    state_res = client.get(f"/jobs/{job_id}/review")
    assert state_res.json()["status"] == "awaiting_review"


def test_api_review_submission_to_agent4():
    """Requirement: POST /jobs/{job_id}/review accepts decisions, invokes Agent 4, returns final status and output info."""
    file_bytes = _get_sample_file_bytes()
    upload_res = client.post(
        "/jobs",
        files={"file": ("sample_messy_sov.xlsx", file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    job_id = upload_res.json()["job_id"]

    # Fetch review recommendations
    review_res = client.get(f"/jobs/{job_id}/review")
    recommendations = review_res.json()["recommendations"]
    assert len(recommendations) > 0

    first_rec = recommendations[0]
    submission = {
        "decisions": [
            {
                "row": first_rec["row"],
                "field": first_rec["field"],
                "decision": "approve",
                "reviewer": "underwriter@reinsurance.com",
            }
        ],
        "notes": "Approved by senior underwriter",
    }

    submit_res = client.post(f"/jobs/{job_id}/review", json=submission)
    assert submit_res.status_code == 200
    submit_data = submit_res.json()
    assert submit_data["job_id"] == job_id
    assert submit_data["status"] == "completed"
    assert submit_data["decisions_recorded"] == 1
    assert submit_data["transformations_applied"] >= 1
    assert submit_data["final_output_path"] is not None
    assert submit_data["download_url"] == f"/jobs/{job_id}/output"


def test_api_output_download():
    """Requirement: GET /jobs/{job_id}/output downloads generated Cleaned_SOV.xlsx."""
    file_bytes = _get_sample_file_bytes()
    upload_res = client.post(
        "/jobs",
        files={"file": ("sample_messy_sov.xlsx", file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    job_id = upload_res.json()["job_id"]

    review_res = client.get(f"/jobs/{job_id}/review")
    rec = review_res.json()["recommendations"][0]

    # Submit review to trigger Agent 4 and generate output
    client.post(
        f"/jobs/{job_id}/review",
        json={
            "decisions": [
                {
                    "row": rec["row"],
                    "field": rec["field"],
                    "decision": "approve",
                    "reviewer": "test_user",
                }
            ]
        },
    )

    # Download output
    download_res = client.get(f"/jobs/{job_id}/output")
    assert download_res.status_code == 200
    assert "application/vnd.openxmlformats" in download_res.headers.get("content-type", "")
    assert "attachment" in download_res.headers.get("content-disposition", "") or "Cleaned_SOV.xlsx" in download_res.headers.get("content-disposition", "")
    assert len(download_res.content) > 500


def test_api_audit_trail_preserved():
    """Requirement: Preserve the existing audit log throughout the FastAPI flow."""
    file_bytes = _get_sample_file_bytes()
    upload_res = client.post(
        "/jobs",
        files={"file": ("sample_messy_sov.xlsx", file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    job_id = upload_res.json()["job_id"]

    # Verify audit trail has Phase A events
    audit_res_phase_a = client.get(f"/api/jobs/{job_id}/audit")
    assert audit_res_phase_a.status_code == 200
    entries_a = audit_res_phase_a.json()["entries"]
    action_types_a = [e["action"] for e in entries_a]
    assert "job_created" in action_types_a
    assert "sheet_analysis_completed" in action_types_a
    assert "schema_mapping_completed" in action_types_a
    assert "quality_inspection_completed" in action_types_a

    # Submit review
    review_res = client.get(f"/jobs/{job_id}/review")
    rec = review_res.json()["recommendations"][0]
    client.post(
        f"/jobs/{job_id}/review",
        json={
            "decisions": [
                {
                    "row": rec["row"],
                    "field": rec["field"],
                    "decision": "approve",
                    "reviewer": "audit_auditor@carrier.com",
                }
            ]
        },
    )

    # Verify audit trail has Review and Agent 4 transformation events
    audit_res_final = client.get(f"/api/jobs/{job_id}/audit")
    assert audit_res_final.status_code == 200
    entries_final = audit_res_final.json()["entries"]
    action_types_final = [e["action"] for e in entries_final]
    assert any("review_decision" in a for a in action_types_final)
    assert "transformations_applied" in action_types_final


