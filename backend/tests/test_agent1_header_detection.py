"""Focused unit tests for Agent 1 Header Row Detection Engine.

Validates candidate row identification, early-window inspection,
metadata row bypassing, data density validation, and exact raw text preservation.
"""

from typing import Any
import pytest

from app.agents.sheet_intelligence.detection import HeaderDetector


@pytest.fixture
def detector() -> HeaderDetector:
    return HeaderDetector()


# =====================================================================
# 1. Header at Row 0
# =====================================================================


def test_header_at_row_0(detector: HeaderDetector):
    """Test 1: Standard clean table where row 0 is the true header."""
    table = [
        [
            "Loc ID",
            "Street Address",
            "City",
            "State",
            "Zip",
            "Building Cost",
            "Occupancy",
        ],
        ["P001", "100 Main St", "Chicago", "IL", "60601", 1500000, "Office"],
        ["P002", "200 State St", "Chicago", "IL", "60602", 3200000, "Retail"],
        ["P003", "300 Lake St", "Chicago", "IL", "60603", 4500000, "Hotel"],
    ]

    result = detector.detect_header_row(table)

    assert result.header_row == 0
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
    assert set(result.detected_concepts) == {
        "ref",
        "addr",
        "city",
        "state",
        "zip",
        "val_bldg",
        "occ",
    }


# =====================================================================
# 2, 3, 4. Header at Row 4 with Metadata, Blanks, and Title Above
# =====================================================================


def test_header_at_row_4_with_metadata_and_blanks(detector: HeaderDetector):
    """Test 2, 3, 4, 12: Header at Row 4 preceded by banner, metadata, and blank rows."""
    table = [
        ["Acme Commercial Insurance Brokerage"],  # Row 0
        ["Property Schedule Submission - 2026"],  # Row 1
        ["Policy Number", "POL-99281"],  # Row 2
        [],  # Row 3
        [
            "Reference",
            "Site Address",
            "City",
            "State",
            "Postal Code",
            "Structure Value",
            "Contents",
            "BI",
        ],  # Row 4 (header)
        [
            "LOC-1",
            "500 Industrial Pkwy",
            "Dallas",
            "TX",
            "75201",
            12000000,
            2500000,
            1000000,
        ],  # Row 5 (data)
        [
            "LOC-2",
            "600 Commerce St",
            "Dallas",
            "TX",
            "75202",
            8500000,
            1200000,
            500000,
        ],  # Row 6 (data)
    ]

    result = detector.detect_header_row(table)

    assert result.header_row == 4
    assert result.confidence >= 0.85
    assert result.raw_headers[0] == "Reference"
    assert result.raw_headers[1] == "Site Address"
    assert result.raw_headers[5] == "Structure Value"


# =====================================================================
# 5, 7, 11. Unknown Columns and Mixed Fields Preservation
# =====================================================================


def test_header_with_unknown_and_mixed_columns(detector: HeaderDetector):
    """Test 5, 7, 11: Known concepts provide evidence; unknown fields are preserved verbatim."""
    table = [
        [
            "Loc ID",
            "Street Address",
            "City",
            "State",
            "Zip",
            "Building Cost ($)",
            "Internal Broker Code",
            "Special Coverage Notes",
        ],
        [
            "P101",
            "77 Elm St",
            "Boston",
            "MA",
            "02108",
            2100000,
            "IBC-X",
            "Near coastline",
        ],
        [
            "P102",
            "88 Oak St",
            "Boston",
            "MA",
            "02109",
            3400000,
            "IBC-Y",
            "Sprinkler retrofit 2024",
        ],
    ]

    result = detector.detect_header_row(table)

    assert result.header_row == 0
    # Verbatim strings preserved
    assert "Building Cost ($)" in result.raw_headers
    assert "Internal Broker Code" in result.raw_headers
    assert "Special Coverage Notes" in result.raw_headers
    assert len(result.raw_headers) == 8


# =====================================================================
# 6. Duplicate / Repeated Semantic Labels
# =====================================================================


def test_header_with_duplicate_labels(detector: HeaderDetector):
    """Test 6: Repeating the same concept does not artificially inflate diversity."""
    table = [
        [
            "Location",
            "Location",
            "Building Value",
            "Building Value",
            "Occupancy",
        ],
        ["Loc 1", "Site A", 5000000, 5000000, "Commercial"],
        ["Loc 2", "Site B", 3000000, 3000000, "Industrial"],
    ]

    result = detector.detect_header_row(table)

    assert result.header_row == 0
    # Raw headers retain both duplicate columns
    assert result.raw_headers == [
        "Location",
        "Location",
        "Building Value",
        "Building Value",
        "Occupancy",
    ]
    # Distinct core concepts only counts val_bldg and occ
    assert "val_bldg" in result.detected_concepts
    assert "occ" in result.detected_concepts


# =====================================================================
# 8. Data Density Lookahead: Density Distinguishes True Headers
# =====================================================================


def test_candidate_rows_distinguished_by_data_density(
    detector: HeaderDetector,
):
    """Test 8: Two candidates with similar concepts; the one atop dense data wins."""
    table = [
        # Candidate A: Row 0 has concepts, but followed only by blanks/metadata
        ["Reference", "Address", "City", "State"],
        [],
        ["End of Section A"],
        [],
        # Candidate B: Row 4 has concepts, followed by real records
        ["Ref ID", "Street Address", "City", "State", "Zip", "Building Value"],
        ["001", "100 Pine", "Seattle", "WA", "98101", 9000000],
        ["002", "200 Pine", "Seattle", "WA", "98102", 4500000],
        ["003", "300 Pine", "Seattle", "WA", "98103", 6200000],
    ]

    result = detector.detect_header_row(table)

    assert result.header_row == 4
    assert result.raw_headers[0] == "Ref ID"


# =====================================================================
# 9. Concept Diversity: Complete SOV Wins Over Sparse Row
# =====================================================================


def test_candidate_with_more_distinct_concepts_wins(detector: HeaderDetector):
    """Test 9: Row with 7 diverse concepts beats a row with only 2 concepts."""
    table = [
        ["Notes", "Information"],
        ["Address", "City"],  # 2 concepts
        [
            "Reference",
            "Address",
            "City",
            "State",
            "Zip",
            "Building Value",
            "Occupancy",
        ],  # 7 concepts
        ["R-1", "100 Main", "Chicago", "IL", "60601", 1000000, "Office"],
        ["R-2", "200 Main", "Chicago", "IL", "60601", 2000000, "Retail"],
    ]

    result = detector.detect_header_row(table)

    assert result.header_row == 2
    assert len(result.detected_concepts) == 7


# =====================================================================
# 10. No Valid Header Detected
# =====================================================================


def test_no_valid_header_empty_table(detector: HeaderDetector):
    """Test 10a: Completely empty table returns header_row=None, confidence=0.0."""
    result = detector.detect_header_row([])
    assert result.header_row is None
    assert result.confidence == 0.0
    assert result.raw_headers == []


def test_no_valid_header_unrelated_text(detector: HeaderDetector):
    """Test 10b: Table containing only legal or non-SOV text returns header_row=None."""
    table = [
        ["Legal Terms and Confidentiality Notice"],
        ["This document is intended solely for authorized recipients."],
        ["Any unauthorized copying or distribution is strictly prohibited."],
        ["Published by Risk Compliance Department"],
    ]

    result = detector.detect_header_row(table)

    assert result.header_row is None
    assert result.confidence == 0.0
    assert result.raw_headers == []
    assert "No sufficiently strong SOV header candidate detected." in result.reasoning[0]


# =====================================================================
# 13, 14. Confidence Bounds & Deterministic Execution
# =====================================================================


def test_confidence_bounds_and_determinism(detector: HeaderDetector):
    """Test 13, 14: Confidence must be strictly between 0 and 1, and repeated execution identical."""
    table = [
        ["Reference", "Address", "City", "State", "Building Value"],
        ["001", "100 Market St", "San Francisco", "CA", 15000000],
        ["002", "200 Market St", "San Francisco", "CA", 12000000],
    ]

    res1 = detector.detect_header_row(table)
    res2 = detector.detect_header_row(table)

    assert 0.0 <= res1.confidence <= 1.0
    assert res1.header_row == res2.header_row
    assert res1.confidence == res2.confidence
    assert res1.raw_headers == res2.raw_headers


# =====================================================================
# 15. Metadata Row Containing "State" Does NOT Win
# =====================================================================


def test_metadata_row_with_state_does_not_beat_real_header(
    detector: HeaderDetector,
):
    """Test 15: A metadata row like ['State', 'Submission Date'] must not beat the real SOV header."""
    table = [
        ["Broker Submission Information"],
        ["State", "Submission Date"],  # 1 concept + metadata
        ["IL", "2026-10-01"],
        [],
        [
            "Reference",
            "Address",
            "City",
            "State",
            "Zip",
            "Building Value",
            "Occupancy",
        ],  # real header
        ["P01", "100 Main St", "Chicago", "IL", "60601", 2500000, "Office"],
        ["P02", "200 Main St", "Chicago", "IL", "60602", 3500000, "Retail"],
    ]

    result = detector.detect_header_row(table)

    assert result.header_row == 4
    assert result.raw_headers[0] == "Reference"


# =====================================================================
# 20. Realistic Broker Cases (Case A, B, C)
# =====================================================================


def test_realistic_broker_case_a(detector: HeaderDetector):
    """CASE A from prompt."""
    table = [
        ["Broker Submission"],
        ["Client", "ABC Corp"],
        [],
        ["Property Schedule"],
        [
            "Loc ID",
            "Address",
            "City",
            "State",
            "Zip",
            "Building Value",
            "Occupancy",
        ],
        ["P001", "100 Main St", "Chicago", "IL", "60601", "1500000", "Office"],
        ["P002", "200 State St", "Chicago", "IL", "60602", "3200000", "Retail"],
    ]

    result = detector.detect_header_row(table)

    assert result.header_row == 4
    assert result.raw_headers == [
        "Loc ID",
        "Address",
        "City",
        "State",
        "Zip",
        "Building Value",
        "Occupancy",
    ]


def test_realistic_broker_case_b(detector: HeaderDetector):
    """CASE B from prompt."""
    table = [
        ["Submission Information"],
        ["State", "IL"],
        ["Date", "2026-01-01"],
        [],
        [
            "Location",
            "Street Address",
            "City",
            "State",
            "Postal Code",
            "Building Cost",
            "TIV",
        ],
        [
            "LOC-1",
            "500 Main St",
            "Peoria",
            "IL",
            "61602",
            "5000000",
            "5000000",
        ],
        [
            "LOC-2",
            "600 Main St",
            "Peoria",
            "IL",
            "61602",
            "7000000",
            "7000000",
        ],
    ]

    result = detector.detect_header_row(table)

    assert result.header_row == 4
    assert result.raw_headers[0] == "Location"
    assert result.raw_headers[1] == "Street Address"


def test_realistic_broker_case_c(detector: HeaderDetector):
    """CASE C from prompt."""
    table = [
        ["Notes"],
        ["Address", "City"],
        [],
        [
            "Reference",
            "Address",
            "City",
            "State",
            "Zip",
            "Building Value",
            "Occupancy",
        ],
        ["R-1", "100 Main", "Chicago", "IL", "60601", "1000000", "Office"],
        ["R-2", "200 Main", "Chicago", "IL", "60601", "2000000", "Retail"],
    ]

    result = detector.detect_header_row(table)

    assert result.header_row == 3
    assert result.raw_headers[0] == "Reference"
    assert len(result.detected_concepts) == 7
