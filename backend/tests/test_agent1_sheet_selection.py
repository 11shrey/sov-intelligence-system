"""Focused unit tests for Agent 1 Primary Sheet / Table Selector.

Validates multi-sheet workbook evaluation, negative and positive sheet signals,
near-tie handling, size-vs-quality discrimination, and end-to-end integration.
"""

from typing import Any
import pytest

from app.agents.sheet_intelligence.scoring import PrimaryTableSelector


@pytest.fixture
def selector() -> PrimaryTableSelector:
    return PrimaryTableSelector()


# =====================================================================
# 1 & 4. Instructions + Property Schedule (First sheet is not SOV)
# =====================================================================


def test_instructions_and_property_schedule(selector: PrimaryTableSelector):
    """Test 1 & 4: Instructions tab is sheet 0, Property Schedule is sheet 1."""
    workbook = {
        "Instructions": [
            ["Broker Submission Instructions"],
            ["Please ensure all property values are completed accurately."],
            ["Submit by deadline: October 1st."],
        ],
        "Property Schedule": [
            ["Loc ID", "Address", "City", "State", "Zip", "Building Value", "Occupancy"],
            ["001", "100 Main St", "Chicago", "IL", "60601", 1500000, "Office"],
            ["002", "200 State St", "Chicago", "IL", "60602", 3200000, "Retail"],
            ["003", "300 Lake St", "Chicago", "IL", "60603", 4500000, "Hotel"],
        ],
    }

    result = selector.select_primary_table(workbook)

    assert result.selected_sheet == "Property Schedule"
    assert result.selected_header_row == 0
    assert result.confidence >= 0.85
    assert len(result.candidates) == 2


# =====================================================================
# 2. Cover + Summary + Property Schedule
# =====================================================================


def test_cover_summary_property_schedule(selector: PrimaryTableSelector):
    """Test 2: Multiple non-SOV sheets (Cover, Summary) alongside Property Schedule."""
    workbook = {
        "Cover": [
            ["Global Insurance Underwriters"],
            ["Property Submission 2026-2027"],
        ],
        "Summary": [
            ["Portfolio Summary"],
            ["Total TIV", 50000000],
            ["Total Sites", 10],
        ],
        "Property Schedule": [
            ["Ref #", "Site Address", "City", "State", "Postal Code", "Structure Value", "Occupancy"],
            ["LOC-1", "100 Industrial Pkwy", "Dallas", "TX", "75201", 12000000, "Industrial"],
            ["LOC-2", "200 Commerce St", "Dallas", "TX", "75202", 8500000, "Commercial"],
        ],
    }

    result = selector.select_primary_table(workbook)

    assert result.selected_sheet == "Property Schedule"
    assert result.selected_header_row == 0
    assert result.confidence >= 0.80


# =====================================================================
# 3. Largest Sheet is NOT the SOV Sheet
# =====================================================================


def test_largest_sheet_is_not_sov_sheet(selector: PrimaryTableSelector):
    """Test 3: Claims history sheet has 50 rows, but Property Schedule has 5 rows.

    The selector must select Property Schedule based on header & semantic quality, not row count.
    """
    claims_rows = [["Claim ID", "Loss Date", "Paid Amount"]] + [
        [f"CLM-{i}", "2024-01-15", 5000 * i] for i in range(50)
    ]
    sov_rows = [
        ["Loc ID", "Street Address", "City", "State", "Zip", "Building Cost", "Occupancy"],
        ["P01", "100 Main St", "Atlanta", "GA", "30303", 5000000, "Office"],
        ["P02", "200 Main St", "Atlanta", "GA", "30304", 7500000, "Retail"],
    ]

    workbook = {
        "Claims": claims_rows,
        "Locations": sov_rows,
    }

    result = selector.select_primary_table(workbook)

    assert result.selected_sheet == "Locations"
    assert result.selected_header_row == 0


# =====================================================================
# 5 & 6. Misleading Sheet Names vs Content Quality
# =====================================================================


def test_misleading_sheet_name_with_strong_contents(
    selector: PrimaryTableSelector,
):
    """Test 5: Sheet named 'Notes' contains the actual SOV schedule.

    Content evidence must beat the negative sheet name signal.
    """
    workbook = {
        "Notes": [
            ["Loc ID", "Street Address", "City", "State", "Zip", "Building Cost", "Occupancy"],
            ["001", "100 Pine", "Seattle", "WA", "98101", 2000000, "Office"],
            ["002", "200 Pine", "Seattle", "WA", "98102", 3000000, "Retail"],
        ]
    }

    result = selector.select_primary_table(workbook)

    assert result.selected_sheet == "Notes"
    assert result.selected_header_row == 0
    # Negative signal penalty was recorded in candidate reasoning
    assert any("Negative sheet name signal matched" in r for r in result.candidates[0].reasoning)


def test_positive_sheet_name_with_weak_contents(
    selector: PrimaryTableSelector,
):
    """Test 6: Sheet named 'Property Schedule' has only general notes,

    while sheet named 'Data Tab 2' contains actual SOV columns.
    """
    workbook = {
        "Property Schedule": [
            ["Property Schedule Overview"],
            ["Please see attached external systems for full breakdown."],
        ],
        "Data Tab 2": [
            ["Loc ID", "Street Address", "City", "State", "Zip", "Building Cost", "Occupancy"],
            ["001", "100 Pine", "Seattle", "WA", "98101", 2000000, "Office"],
            ["002", "200 Pine", "Seattle", "WA", "98102", 3000000, "Retail"],
        ],
    }

    result = selector.select_primary_table(workbook)

    assert result.selected_sheet == "Data Tab 2"
    assert result.selected_header_row == 0


# =====================================================================
# 7 & 8. Multiple Valid Candidates & Near-Tie Handling
# =====================================================================


def test_near_tie_handling_and_ambiguity_flag(selector: PrimaryTableSelector):
    """Test 8: Two candidates with virtually identical high quality; near-tie is flagged."""
    sheet_a = [
        ["Ref", "Address", "City", "State", "Zip", "Building Value", "Occupancy"],
        ["001", "100 Main", "Chicago", "IL", "60601", 1500000, "Office"],
        ["002", "200 Main", "Chicago", "IL", "60602", 2500000, "Office"],
    ]
    sheet_b = [
        ["Ref", "Address", "City", "State", "Zip", "Building Value", "Occupancy"],
        ["101", "500 Market", "Dallas", "TX", "75201", 3000000, "Retail"],
        ["102", "600 Market", "Dallas", "TX", "75202", 4000000, "Retail"],
    ]

    workbook = {
        "Locations North": sheet_a,
        "Locations South": sheet_b,
    }

    result = selector.select_primary_table(workbook)

    assert result.is_near_tie is True
    assert set(result.near_tie_candidates) == {"Locations North", "Locations South"}
    assert result.selected_sheet in {"Locations North", "Locations South"}
    assert any("Near tie detected" in r for r in result.reasoning)


# =====================================================================
# 9. No Valid SOV Table
# =====================================================================


def test_no_valid_sov_table(selector: PrimaryTableSelector):
    """Test 9: Workbook containing only instructions and legal disclaimers."""
    workbook = {
        "Instructions": [
            ["Instructions for Submission"],
            ["Follow company guidelines."],
        ],
        "Legal": [
            ["Terms and Conditions"],
            ["All rights reserved."],
        ],
    }

    result = selector.select_primary_table(workbook)

    assert result.selected_sheet is None
    assert result.selected_header_row is None
    assert result.confidence == 0.0
    assert result.raw_headers == []
    assert "No sheet qualified as a primary SOV property schedule." in result.reasoning[0]


# =====================================================================
# 10 & 11. Single Table CSV (Valid vs Invalid)
# =====================================================================


def test_single_table_csv_valid(selector: PrimaryTableSelector):
    """Test 10: Single-table format (CSV/JSON) with valid SOV data."""
    table = {
        "default": [
            ["Loc ID", "Address", "City", "State", "Zip", "Building Cost", "Occupancy"],
            ["01", "100 Broad", "New York", "NY", "10001", 50000000, "Office"],
            ["02", "200 Broad", "New York", "NY", "10002", 75000000, "Office"],
        ]
    }

    result = selector.select_primary_table(table)

    assert result.selected_sheet == "default"
    assert result.selected_header_row == 0
    assert result.confidence >= 0.80


def test_single_table_csv_invalid(selector: PrimaryTableSelector):
    """Test 11: Single-table format with non-SOV data."""
    table = {
        "default": [
            ["Invoice #", "Vendor", "Due Date", "Amount"],
            ["INV-01", "Acme IT", "2026-10-01", 1200],
        ]
    }

    result = selector.select_primary_table(table)

    assert result.selected_sheet is None
    assert result.confidence == 0.0


# =====================================================================
# 12. JSON Logical Table
# =====================================================================


def test_json_logical_tables(selector: PrimaryTableSelector):
    """Test 12: JSON data normalized into logical tables."""
    data = {
        "metadata": [["System Export Version 2.0"]],
        "schedule": [
            ["Ref", "Location", "City", "State", "Zip", "Building Value", "Occupancy"],
            ["R1", "100 Main", "Denver", "CO", "80202", 4000000, "Commercial"],
        ],
    }

    result = selector.select_primary_table(data)

    assert result.selected_sheet == "schedule"
    assert result.selected_header_row == 0


# =====================================================================
# 13 & 14. Metadata-Heavy Workbook & "State" Trap in Metadata
# =====================================================================


def test_sheet_with_state_in_metadata_does_not_win(
    selector: PrimaryTableSelector,
):
    """Test 14: Sheet with 'State' in metadata row does not beat actual SOV schedule."""
    workbook = {
        "Submission Info": [
            ["State", "Submission Date"],
            ["CA", "2026-05-01"],
        ],
        "Schedule": [
            ["Ref ID", "Street Address", "City", "State", "Zip", "Building Cost", "Occupancy"],
            ["001", "100 Market St", "San Francisco", "CA", "94105", 15000000, "Office"],
            ["002", "200 Market St", "San Francisco", "CA", "94106", 25000000, "Office"],
        ],
    }

    result = selector.select_primary_table(workbook)

    assert result.selected_sheet == "Schedule"
    assert result.selected_header_row == 0


# =====================================================================
# 15, 16, 17. Raw Header, Header Row Index, Candidate List Preservation
# =====================================================================


def test_raw_header_and_candidate_preservation(selector: PrimaryTableSelector):
    """Test 15, 16, 17: Preserves verbatim raw headers, row index, and audit candidates."""
    workbook = {
        "Cover": [["Cover Text"]],
        "Property Schedule": [
            ["Broker Submission Banner"],
            ["Date: 2026-10-01"],
            [],
            ["Loc ID", "Street Address", "Building Cost ($)", "Occ."],
            ["P-01", "100 Main", 2500000, "Office"],
            ["P-02", "200 Main", 3500000, "Retail"],
        ],
    }

    result = selector.select_primary_table(workbook)

    assert result.selected_sheet == "Property Schedule"
    assert result.selected_header_row == 3
    # Verbatim headers
    assert result.raw_headers == [
        "Loc ID",
        "Street Address",
        "Building Cost ($)",
        "Occ.",
    ]
    # Candidates preserved
    assert len(result.candidates) == 2
    sheet_names = [c.sheet_name for c in result.candidates]
    assert "Cover" in sheet_names
    assert "Property Schedule" in sheet_names


# =====================================================================
# 18 & 19. Determinism and Confidence Bounds
# =====================================================================


def test_determinism_and_confidence_bounds(selector: PrimaryTableSelector):
    """Test 18 & 19: Repeated execution produces identical results with confidence in [0, 1]."""
    workbook = {
        "SOV": [
            ["Reference", "Address", "City", "State", "Zip", "Building Value", "Occupancy"],
            ["LOC-1", "100 Elm", "Chicago", "IL", "60601", 1000000, "Office"],
        ]
    }

    res1 = selector.select_primary_table(workbook)
    res2 = selector.select_primary_table(workbook)

    assert 0.0 <= res1.confidence <= 1.0
    assert res1.selected_sheet == res2.selected_sheet
    assert res1.selected_header_row == res2.selected_header_row
    assert res1.confidence == res2.confidence
    assert res1.raw_headers == res2.raw_headers


# =====================================================================
# 20. Realistic Multi-Sheet Broker Workbook Test (Section 20)
# =====================================================================


def test_realistic_broker_multi_sheet_workbook(selector: PrimaryTableSelector):
    """Section 20: Comprehensive Realistic Broker Workbook Test with Instructions, Summary, Property Schedule."""
    workbook = {
        "Instructions": [
            ["Broker Submission Instructions"],
            ["Complete all required fields"],
        ],
        "Summary": [
            ["Submission Summary"],
            ["Total Locations", 25],
            ["Total Value", 50000000],
        ],
        "Property Schedule": [
            ["ABC Broker"],
            ["Submission Date", "2026-01-01"],
            [],
            ["Loc ID", "Street Address", "City", "State", "Zip", "Building Cost", "Occupancy"],
            ["P001", "100 Main St", "Chicago", "IL", "60601", 1500000, "Office"],
            ["P002", "200 State St", "Chicago", "IL", "60602", 3200000, "Retail"],
        ],
    }

    result = selector.select_primary_table(workbook)

    assert result.selected_sheet == "Property Schedule"
    assert result.selected_header_row == 3
    assert result.confidence >= 0.85
    assert result.raw_headers == [
        "Loc ID",
        "Street Address",
        "City",
        "State",
        "Zip",
        "Building Cost",
        "Occupancy",
    ]
    # Check that Instructions and Summary were scored and retained in candidates
    candidate_map = {c.sheet_name: c for c in result.candidates}
    assert candidate_map["Instructions"].is_candidate is False
    assert candidate_map["Summary"].is_candidate is False
    assert candidate_map["Property Schedule"].is_candidate is True
