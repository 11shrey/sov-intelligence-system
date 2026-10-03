"""Test FastAPI endpoints."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


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

    # 7. Download Cleaned Output
    download_response = client.get(f"/api/jobs/{job_id}/download")
    assert download_response.status_code == 200
    assert "text/csv" in download_response.headers.get("content-type", "")


def test_job_not_found():
    """Verify 404 for nonexistent job."""
    response = client.get("/api/jobs/nonexistent-job-id")
    assert response.status_code == 404
