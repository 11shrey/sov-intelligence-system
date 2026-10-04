"""Tests for ExcelService multi-format input and export capabilities."""

import io
import json
import pandas as pd
import pytest
from openpyxl import Workbook

from app.models.schema_models import TARGET_SOV_FIELDS
from app.services.excel_service import ExcelService, UnsupportedFormatError


@pytest.fixture
def service():
    return ExcelService()


def test_detect_format_supported(service):
    """Test format detection for supported file extensions."""
    assert service.detect_format("test.xlsx") == "xlsx"
    assert service.detect_format("test.xlsm") == "xlsm"
    assert service.detect_format("test.xls") == "xls"
    assert service.detect_format("test.csv") == "csv"
    assert service.detect_format("test.tsv") == "tsv"
    assert service.detect_format("test.json") == "json"


def test_detect_format_unsupported(service):
    """Test UnsupportedFormatError raised on unsupported file extensions."""
    with pytest.raises(UnsupportedFormatError):
        service.detect_format("test.pdf")
    with pytest.raises(UnsupportedFormatError):
        service.detect_format("test.docx")
    with pytest.raises(UnsupportedFormatError):
        service.detect_format("test.txt")


def test_csv_semicolon_and_cp1252(service, tmp_path):
    """Test CSV with semicolon delimiter and cp1252 encoding."""
    csv_file = tmp_path / "german_schedule.csv"
    content = "Reference;Address;City;State;Zip;Building Value\nLOC-01;Münchener Str. 12;München;BY;80331;2500000\nLOC-02;Kölner Str. 4;Köln;NW;50667;1800000\n"
    csv_file.write_bytes(content.encode("cp1252"))

    sheet_names = service.get_sheet_names(csv_file)
    assert sheet_names == ["CSV"]

    sample = service.read_sheet_sample(csv_file, "CSV", max_rows=10)
    assert len(sample) == 3
    assert sample[0][0] == "Reference"
    assert sample[0][1] == "Address"
    assert sample[1][1] == "Münchener Str. 12"

    df = service.read_sheet(csv_file, "CSV", header_row=0)
    assert list(df.columns) == ["Reference", "Address", "City", "State", "Zip", "Building Value"]
    assert len(df) == 2
    assert df.iloc[0]["City"] == "München"


def test_json_shape_a_list_of_records(service, tmp_path):
    """Test JSON Shape (a): List of record objects -> single sheet ['JSON']."""
    json_file = tmp_path / "shape_a.json"
    data = [
        {"Address": "100 Broadway", "City": "New York", "Building Value": 5000000},
        {"Address": "200 Market St", "City": "Philadelphia", "Building Value": 3000000},
    ]
    json_file.write_text(json.dumps(data), encoding="utf-8")

    assert service.get_sheet_names(json_file) == ["JSON"]
    sample = service.read_sheet_sample(json_file, "JSON")
    assert sample[0] == ["Address", "City", "Building Value"]
    assert sample[1] == ["100 Broadway", "New York", 5000000]

    df = service.read_sheet(json_file, "JSON", header_row=0)
    assert len(df) == 2
    assert df.iloc[0]["Address"] == "100 Broadway"


def test_json_shape_b_dict_of_sheets(service, tmp_path):
    """Test JSON Shape (b): Dict of {sheet_name: list of records} -> multi-sheet."""
    json_file = tmp_path / "shape_b.json"
    data = {
        "Locations": [
            {"Address": "123 Main St", "City": "Dallas", "Building Value": 1500000},
            {"Address": "456 Elm St", "City": "Austin", "Building Value": 2200000},
        ],
        "Summary": [
            {"Total Locations": 2, "Total TIV": 3700000},
        ],
    }
    json_file.write_text(json.dumps(data), encoding="utf-8")

    sheet_names = service.get_sheet_names(json_file)
    assert "Locations" in sheet_names
    assert "Summary" in sheet_names

    loc_sample = service.read_sheet_sample(json_file, "Locations")
    assert "Address" in loc_sample[0]

    df = service.read_sheet(json_file, "Locations", header_row=0)
    assert len(df) == 2
    assert df.iloc[0]["City"] == "Dallas"


def test_json_shape_c_wrapper_key(service, tmp_path):
    """Test JSON Shape (c): Dict with wrapper key holding a list."""
    json_file = tmp_path / "shape_c.json"
    data = {
        "properties": [
            {"Address": "789 Pine Rd", "City": "Denver", "Building Value": 900000},
        ]
    }
    json_file.write_text(json.dumps(data), encoding="utf-8")

    assert service.get_sheet_names(json_file) == ["properties"]
    sample = service.read_sheet_sample(json_file, "properties")
    assert sample[0] == ["Address", "City", "Building Value"]
    assert sample[1][0] == "789 Pine Rd"


def test_json_shape_d_nested_flattened(service, tmp_path):
    """Test JSON Shape (d): Nested objects flattened with dot-separated names."""
    json_file = tmp_path / "shape_d.json"
    data = [
        {
            "location": {"address": "55 Wall St", "city": "NYC"},
            "values": {"building": 12000000, "contents": 4000000},
        }
    ]
    json_file.write_text(json.dumps(data), encoding="utf-8")

    sample = service.read_sheet_sample(json_file, "JSON")
    assert "location.address" in sample[0]
    assert "values.building" in sample[0]
    assert sample[1][sample[0].index("location.address")] == "55 Wall St"


def test_json_invalid_or_empty_raises(service, tmp_path):
    """Test invalid or empty JSON raises ValueError."""
    empty_file = tmp_path / "empty.json"
    empty_file.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError):
        service.get_sheet_names(empty_file)

    corrupt_file = tmp_path / "corrupt.json"
    corrupt_file.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(ValueError):
        service.get_sheet_names(corrupt_file)


def test_export_cleaned_sov_17_columns(service, tmp_path):
    """Test export_cleaned_sov produces exactly 17 columns in standard order for csv, xlsx, json."""
    sample_data = [
        {
            "Reference": "LOC-1",
            "Address": "123 Main St",
            "City": "Chicago",
            "State": "IL",
            "Zip": "60601",
            "Building Value": 1000000,
            "Unrelated Extra Field": "Will be omitted",
        }
    ]

    # 1. CSV Export
    csv_out = tmp_path / "out.csv"
    res_csv = service.export_cleaned_sov(sample_data, output_path=csv_out, output_format="csv")
    df_csv = pd.read_csv(res_csv, encoding="utf-8-sig")
    assert list(df_csv.columns) == TARGET_SOV_FIELDS
    assert len(df_csv.columns) == 17
    assert df_csv.iloc[0]["Address"] == "123 Main St"
    assert "Unrelated Extra Field" not in df_csv.columns

    # 2. XLSX Export
    xlsx_out = tmp_path / "out.xlsx"
    res_xlsx = service.export_cleaned_sov(sample_data, output_path=xlsx_out, output_format="xlsx")
    df_xlsx = pd.read_excel(res_xlsx)
    assert list(df_xlsx.columns) == TARGET_SOV_FIELDS
    assert len(df_xlsx.columns) == 17

    # 3. JSON Export
    json_out = tmp_path / "out.json"
    res_json = service.export_cleaned_sov(sample_data, output_path=json_out, output_format="json")
    with open(res_json, "r", encoding="utf-8") as f:
        records = json.load(f)
    assert len(records) == 1
    assert list(records[0].keys()) == TARGET_SOV_FIELDS
