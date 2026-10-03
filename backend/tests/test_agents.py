"""Test Agent placeholder modules."""

from pathlib import Path
from openpyxl import Workbook
import pytest

from app.agents.sheet_agent import SheetIntelligenceAgent
from app.agents.schema_agent import SchemaMappingAgent
from app.agents.quality_agent import DataQualityAgent
from app.agents.transformation_agent import ControlledTransformationAgent
from app.orchestration.state import SOVProcessingState, FileInfo, JobStatus
from app.models.review_models import ReviewDecision


def create_sample_state(tmp_path: Path) -> SOVProcessingState:
    wb = Workbook()
    ws = wb.active
    ws.title = "Property Schedule"
    ws.append(["Reference", "Address", "City", "State", "Zip", "Building Value"])
    ws.append(["LOC-1", "100 Main St", "Chicago", "IL", "60601", 1000000])

    file_path = tmp_path / "property_schedule.xlsx"
    wb.save(file_path)

    file_info = FileInfo(
        filename=file_path.name,
        file_path=str(file_path),
        file_size_bytes=1024,
    )
    return SOVProcessingState(job_id="test-job-456", file_info=file_info)


def test_agent_instantiation():
    """Verify all 4 agent classes can be instantiated."""
    agent1 = SheetIntelligenceAgent()
    agent2 = SchemaMappingAgent()
    agent3 = DataQualityAgent()
    agent4 = ControlledTransformationAgent()

    assert agent1 is not None
    assert agent2 is not None
    assert agent3 is not None
    assert agent4 is not None


def test_agent_execution_chain(tmp_path):
    """Verify state transitions when stepping through agent placeholders."""
    state = create_sample_state(tmp_path)
    assert state.status == JobStatus.PENDING

    # Agent 1
    agent1 = SheetIntelligenceAgent()
    state = agent1.run(state)
    assert state.status == JobStatus.SHEET_ANALYZED
    assert len(state.sheet_analysis) > 0
    assert state.selected_sheet == "Property Schedule"

    # Agent 2
    agent2 = SchemaMappingAgent()
    state = agent2.run(state)
    assert state.status == JobStatus.SCHEMA_MAPPED
    assert len(state.schema_mappings) > 0

    # Agent 3
    agent3 = DataQualityAgent()
    state = agent3.run(state)
    assert state.status == JobStatus.AWAITING_REVIEW
    assert len(state.recommendations) > 0

    # Add Human Review Decision
    state.review_decisions.append(
        ReviewDecision(
            row=2,
            field="Zip",
            decision="approve",
            reviewer="risk_engineer@carrier.com",
        )
    )

    # Agent 4
    agent4 = ControlledTransformationAgent()
    state = agent4.run(state)
    assert state.status == JobStatus.COMPLETED
    assert len(state.approved_transformations) == 1
    assert state.final_output_path is not None
