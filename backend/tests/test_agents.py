"""Test Agent placeholder modules."""

from app.agents.sheet_agent import SheetIntelligenceAgent
from app.agents.schema_agent import SchemaMappingAgent
from app.agents.quality_agent import DataQualityAgent
from app.agents.transformation_agent import ControlledTransformationAgent
from app.orchestration.state import SOVProcessingState, FileInfo, JobStatus
from app.models.review_models import ReviewDecision


def create_sample_state() -> SOVProcessingState:
    file_info = FileInfo(
        filename="property_schedule.xlsx",
        file_path="data/uploads/property_schedule.xlsx",
        file_size_bytes=1024,
    )
    state = SOVProcessingState(job_id="test-job-456", file_info=file_info)

    # Provide real source columns so Agent 2 can produce mappings
    state.metadata["raw_columns"] = [
        "Loc #", "Street Address", "City", "ST", "Zip Code",
        "County", "Country", "Bldg Repl Cost", "Contents", "BI Limit",
        "Occupancy Type", "Const Type", "Stories", "Building Count",
        "Yr Built", "Fire Prot.", "Other Value",
    ]
    # Provide mapped rows so Agent 3 can analyse data quality
    state.metadata["mapped_rows"] = [
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
        # Duplicate row to trigger at least one quality issue (recommendation)
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
    return state


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


def test_agent_execution_chain():
    """Verify state transitions when stepping through agents."""
    state = create_sample_state()
    assert state.status == JobStatus.PENDING

    # Agent 1
    agent1 = SheetIntelligenceAgent()
    state = agent1.run(state)
    assert state.status == JobStatus.SHEET_ANALYZED
    assert len(state.sheet_analysis) > 0

    # Agent 2
    agent2 = SchemaMappingAgent()
    state = agent2.run(state)
    assert state.status == JobStatus.SCHEMA_MAPPED
    assert len(state.schema_mappings) > 0

    # Agent 3
    agent3 = DataQualityAgent()
    state = agent3.run(state)
    assert state.status == JobStatus.AWAITING_REVIEW
    # At least one quality issue from the duplicate row
    assert len(state.quality_issues) > 0

    # Add Human Review Decision — use quality_issues as source (recommendations may be empty
    # since deterministic recs are conservative; quality_issues always has actionable items)
    first_issue = state.quality_issues[0]
    state.review_decisions.append(
        ReviewDecision(
            row=first_issue.row,
            field=first_issue.field,
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
