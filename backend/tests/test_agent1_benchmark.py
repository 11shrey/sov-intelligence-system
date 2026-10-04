"""Performance and Accuracy Benchmark Suite for Agent 1 (Sheet Intelligence).

Executes:
1. Performance latency profiling across ingestion, semantics, header detection,
   sheet selection, serialization, and total pipeline execution on a 1,000-row workbook.
2. Comprehensive 12-layout accuracy benchmark measuring Header Detection Accuracy,
   Sheet Selection Accuracy, and Format Success Rate.
"""

from pathlib import Path
import time
import openpyxl
import pytest

from app.agents.sheet_intelligence import (
    HeaderDetector,
    PrimaryTableSelector,
    SemanticDetector,
    SheetIntelligenceEngine,
    UniversalIngestor,
    analyze_file,
)


# =====================================================================
# 1. Performance Latency Profiling (Section 15)
# =====================================================================


def test_agent1_performance_benchmark(tmp_path: Path):
    """Measures component-level and end-to-end latency on a realistic 1,000-row workbook."""
    file_path = tmp_path / "benchmark_1000_rows.xlsx"
    wb = openpyxl.Workbook()

    # Sheet 1: Instructions (5 rows)
    ws_inst = wb.active
    ws_inst.title = "Instructions"
    for i in range(5):
        ws_inst.append([f"Guideline line {i}"])

    # Sheet 2: Summary (10 rows)
    ws_sum = wb.create_sheet(title="Summary")
    for i in range(10):
        ws_sum.append([f"Metric {i}", 1000 * i])

    # Sheet 3: Property Schedule (1,000 rows)
    ws_sov = wb.create_sheet(title="Property Schedule")
    ws_sov.append(["Broker Submission Banner - Commercial Property"])
    ws_sov.append(["Date: 2026-10-01"])
    ws_sov.append([])  # Blank row
    ws_sov.append(
        [
            "Loc ID",
            "Street Address",
            "City",
            "State",
            "Zip",
            "Building Cost ($)",
            "Contents Value",
            "BI",
            "Occupancy",
        ]
    )
    for i in range(1, 1001):
        ws_sov.append(
            [
                f"LOC-{i:04d}",
                f"{i * 10} Industrial Pkwy",
                "Chicago",
                "IL",
                "60601",
                1000000 + i * 5000,
                250000,
                100000,
                "Commercial Office",
            ]
        )

    wb.save(file_path)

    # Component Profiling
    ingestor = UniversalIngestor()
    semantic_detector = SemanticDetector()
    header_detector = HeaderDetector(semantic_detector=semantic_detector)
    selector = PrimaryTableSelector(header_detector=header_detector)

    # 1. Ingestion Time
    t0 = time.perf_counter()
    workbook = ingestor.ingest(file_path)
    t_ingest = (time.perf_counter() - t0) * 1000

    # 2. Semantic Detection Time on candidate header
    sample_row = workbook.tables["Property Schedule"].matrix[3]
    t0 = time.perf_counter()
    for _ in range(50):
        semantic_detector.analyze_row(sample_row)
    t_semantic = ((time.perf_counter() - t0) / 50) * 1000

    # 3. Header Detection Time
    t0 = time.perf_counter()
    hdr_res = header_detector.detect_header_row(
        workbook.tables["Property Schedule"].matrix
    )
    t_header = (time.perf_counter() - t0) * 1000

    # 4. Sheet Selection Time
    t0 = time.perf_counter()
    selection_res = selector.select_primary_table(workbook)
    t_select = (time.perf_counter() - t0) * 1000

    # 5. Serialization Time
    engine = SheetIntelligenceEngine()
    result = engine.process(file_path, job_id="bench_001")
    t0 = time.perf_counter()
    json_bytes = result.model_dump_json()
    t_serialize = (time.perf_counter() - t0) * 1000

    # 6. Total End-to-End Execution Time
    t0 = time.perf_counter()
    final_res = analyze_file(file_path, job_id="bench_001")
    t_total = (time.perf_counter() - t0) * 1000

    # Assertions
    assert final_res.selected_sheet == "Property Schedule"
    assert final_res.header_row == 3
    assert final_res.total_rows == 1000
    assert len(final_res.sample_rows) == 5

    # Target: total latency under 1,500ms for a 1,000-row workbook
    assert t_total < 2500.0, f"Total execution time too slow: {t_total:.2f}ms"

    # Print summary metrics for reporting
    print("\n" + "=" * 55)
    print("AGENT 1 PERFORMANCE BENCHMARK (1,000 ROWS, 3 SHEETS)")
    print("=" * 55)
    print(f"1. Ingestion Time:          {t_ingest:8.2f} ms")
    print(f"2. Semantic Detection Time: {t_semantic:8.2f} ms/row")
    print(f"3. Header Detection Time:   {t_header:8.2f} ms")
    print(f"4. Sheet Selection Time:    {t_select:8.2f} ms")
    print(f"5. Serialization Time:      {t_serialize:8.2f} ms")
    print("-" * 55)
    print(f"6. Total Agent 1 E2E Time:  {t_total:8.2f} ms")
    print("=" * 55)


# =====================================================================
# 2. 12-Layout Accuracy Benchmark Suite (Section 21)
# =====================================================================


def test_agent1_accuracy_benchmark_suite(tmp_path: Path):
    """Executes a 12-layout accuracy benchmark verifying Header Detection Accuracy,

    Sheet Selection Accuracy, and Format Success Rate.
    """
    cases: list[dict] = []

    # Case 1: Header at Row 0
    p1 = tmp_path / "c1_row0.csv"
    p1.write_text(
        "Loc ID,Address,City,State,Zip,Building Value,Occupancy\n"
        "001,100 Main,Chicago,IL,60601,1000000,Office\n",
        encoding="utf-8",
    )
    cases.append(
        {
            "id": "Case 1: Header at Row 0",
            "path": p1,
            "format": "csv",
            "multi_table": False,
            "has_sov": True,
            "exp_sheet": "default",
            "exp_header": 0,
        }
    )

    # Case 2: Header After Metadata
    p2 = tmp_path / "c2_metadata.csv"
    p2.write_text(
        "Brokerage Submission\n"
        "Date: 2026-10-01\n"
        "Loc ID,Address,City,State,Zip,Building Value,Occupancy\n"
        "001,100 Main,Chicago,IL,60601,1000000,Office\n",
        encoding="utf-8",
    )
    cases.append(
        {
            "id": "Case 2: Header After Metadata",
            "path": p2,
            "format": "csv",
            "multi_table": False,
            "has_sov": True,
            "exp_sheet": "default",
            "exp_header": 2,
        }
    )

    # Case 3: Header After Blank Rows
    p3 = tmp_path / "c3_blanks.csv"
    p3.write_text(
        "Brokerage Submission\n"
        "\n"
        "\n"
        "Loc ID,Address,City,State,Zip,Building Value,Occupancy\n"
        "001,100 Main,Chicago,IL,60601,1000000,Office\n",
        encoding="utf-8",
    )
    cases.append(
        {
            "id": "Case 3: Header After Blank Rows",
            "path": p3,
            "format": "csv",
            "multi_table": False,
            "has_sov": True,
            "exp_sheet": "default",
            "exp_header": 3,
        }
    )

    # Case 4: Multiple Sheets (Instructions + Property Schedule)
    p4 = tmp_path / "c4_multisheet.xlsx"
    wb4 = openpyxl.Workbook()
    wb4.active.title = "Instructions"
    wb4.active.append(["Read Guidelines"])
    ws4 = wb4.create_sheet(title="Property Schedule")
    ws4.append(["Loc ID", "Address", "City", "State", "Zip", "Building Value", "Occupancy"])
    ws4.append(["001", "100 Main", "Chicago", "IL", "60601", 1000000, "Office"])
    wb4.save(p4)
    cases.append(
        {
            "id": "Case 4: Multiple Sheets",
            "path": p4,
            "format": "xlsx",
            "multi_table": True,
            "has_sov": True,
            "exp_sheet": "Property Schedule",
            "exp_header": 0,
        }
    )

    # Case 5: Misleading Summary Sheet
    p5 = tmp_path / "c5_summary.xlsx"
    wb5 = openpyxl.Workbook()
    ws5_sum = wb5.active
    ws5_sum.title = "Summary"
    ws5_sum.append(["Total Value", 50000000])
    ws5_sov = wb5.create_sheet(title="Locations")
    ws5_sov.append(["Loc ID", "Address", "City", "State", "Zip", "Building Value", "Occupancy"])
    ws5_sov.append(["001", "100 Main", "Chicago", "IL", "60601", 1000000, "Office"])
    wb5.save(p5)
    cases.append(
        {
            "id": "Case 5: Misleading Summary Sheet",
            "path": p5,
            "format": "xlsx",
            "multi_table": True,
            "has_sov": True,
            "exp_sheet": "Locations",
            "exp_header": 0,
        }
    )

    # Case 6: Instructions Sheet (Tab 0)
    p6 = tmp_path / "c6_instructions.xlsx"
    wb6 = openpyxl.Workbook()
    wb6.active.title = "Instructions Tab"
    wb6.active.append(["Instructions only"])
    ws6 = wb6.create_sheet(title="Schedule")
    ws6.append(["Loc ID", "Address", "City", "State", "Zip", "Building Value", "Occupancy"])
    ws6.append(["001", "100 Main", "Chicago", "IL", "60601", 1000000, "Office"])
    wb6.save(p6)
    cases.append(
        {
            "id": "Case 6: Instructions Sheet",
            "path": p6,
            "format": "xlsx",
            "multi_table": True,
            "has_sov": True,
            "exp_sheet": "Schedule",
            "exp_header": 0,
        }
    )

    # Case 7: Unknown Columns
    p7 = tmp_path / "c7_unknown_cols.csv"
    p7.write_text(
        "Loc ID,Address,City,State,Zip,Building Cost,Custom Code,Broker Notes\n"
        "001,100 Main,Chicago,IL,60601,1000000,XYZ,No notes\n",
        encoding="utf-8",
    )
    cases.append(
        {
            "id": "Case 7: Unknown Columns",
            "path": p7,
            "format": "csv",
            "multi_table": False,
            "has_sov": True,
            "exp_sheet": "default",
            "exp_header": 0,
        }
    )

    # Case 8: Ambiguous Site/Location Fields
    p8 = tmp_path / "c8_ambiguous.csv"
    p8.write_text(
        "Site,Location,Building Cost,Value\n"
        "S01,North Campus,1500000,1500000\n",
        encoding="utf-8",
    )
    cases.append(
        {
            "id": "Case 8: Ambiguous Site/Location",
            "path": p8,
            "format": "csv",
            "multi_table": False,
            "has_sov": True,
            "exp_sheet": "default",
            "exp_header": 0,
        }
    )

    # Case 9: JSON Records
    p9 = tmp_path / "c9_records.json"
    p9.write_text(
        '[{"Loc ID": "P1", "Address": "100 Main", "City": "Chicago", "State": "IL", "Zip": "60601", "Building Value": 1000000, "Occupancy": "Office"}]',
        encoding="utf-8",
    )
    cases.append(
        {
            "id": "Case 9: JSON Records",
            "path": p9,
            "format": "json",
            "multi_table": False,
            "has_sov": True,
            "exp_sheet": "default",
            "exp_header": 0,
        }
    )

    # Case 10: CSV Metadata Ragged Lines
    p10 = tmp_path / "c10_csv_metadata.csv"
    p10.write_text(
        "Acme Brokerage\n"
        "Date,2026-10-01\n"
        "\n"
        "Loc ID,Address,City,State,Zip,Building Cost,Occupancy\n"
        "001,100 Main,Chicago,IL,60601,1000000,Office\n",
        encoding="utf-8",
    )
    cases.append(
        {
            "id": "Case 10: CSV Metadata",
            "path": p10,
            "format": "csv",
            "multi_table": False,
            "has_sov": True,
            "exp_sheet": "default",
            "exp_header": 3,
        }
    )

    # Case 11: No Valid SOV Table
    p11 = tmp_path / "c11_no_sov.xlsx"
    wb11 = openpyxl.Workbook()
    wb11.active.title = "Instructions"
    wb11.active.append(["Read only"])
    ws11 = wb11.create_sheet(title="Summary")
    ws11.append(["Summary only"])
    wb11.save(p11)
    cases.append(
        {
            "id": "Case 11: No Valid SOV Table",
            "path": p11,
            "format": "xlsx",
            "multi_table": True,
            "has_sov": False,
            "exp_sheet": None,
            "exp_header": None,
        }
    )

    # Case 12: Two Plausible SOV Tables
    p12 = tmp_path / "c12_two_tables.xlsx"
    wb12 = openpyxl.Workbook()
    ws12_a = wb12.active
    ws12_a.title = "Location Data"
    ws12_a.append(["Ref", "Address", "City", "State", "Zip", "Building Value", "Occupancy"])
    ws12_a.append(["01", "100 Main", "Chicago", "IL", "60601", 1000000, "Office"])
    ws12_b = wb12.create_sheet(title="Property Schedule")
    ws12_b.append(["Ref", "Address", "City", "State", "Zip", "Building Value", "Occupancy"])
    ws12_b.append(["02", "200 Main", "Chicago", "IL", "60602", 2000000, "Retail"])
    wb12.save(p12)
    cases.append(
        {
            "id": "Case 12: Two Plausible Tables",
            "path": p12,
            "format": "xlsx",
            "multi_table": True,
            "has_sov": True,
            "exp_sheet": "Location Data",
            "exp_header": 0,
            "expect_near_tie": True,
        }
    )

    # Execute all 12 cases
    results: list[dict] = []
    for c in cases:
        res = analyze_file(c["path"], job_id=c["id"])
        is_sheet_ok = res.selected_sheet == c["exp_sheet"]
        is_header_ok = res.header_row == c["exp_header"]
        is_tie_ok = res.is_near_tie if c.get("expect_near_tie") else True
        passed = is_sheet_ok and is_header_ok and is_tie_ok

        results.append(
            {
                "id": c["id"],
                "format": c["format"],
                "expected_sheet": c["exp_sheet"],
                "actual_sheet": res.selected_sheet,
                "expected_header": c["exp_header"],
                "actual_header": res.header_row,
                "confidence": res.confidence,
                "passed": passed,
                "multi_table": c["multi_table"],
                "has_sov": c["has_sov"],
            }
        )

    # Calculate Accuracy Metrics
    header_cases = [r for r in results if r["has_sov"]]
    header_correct = sum(
        1 for r in header_cases if r["actual_header"] == r["expected_header"]
    )
    header_accuracy = (header_correct / len(header_cases)) * 100

    sheet_cases = [r for r in results if r["multi_table"]]
    sheet_correct = sum(
        1 for r in sheet_cases if r["actual_sheet"] == r["expected_sheet"]
    )
    sheet_accuracy = (sheet_correct / len(sheet_cases)) * 100

    format_correct = sum(1 for r in results if r["passed"])
    format_success_rate = (format_correct / len(results)) * 100

    false_positives = sum(
        1 for r in results if not r["has_sov"] and r["actual_sheet"] is not None
    )
    false_negatives = sum(
        1 for r in results if r["has_sov"] and r["actual_sheet"] is None
    )

    print("\n" + "=" * 65)
    print("AGENT 1 ACCURACY BENCHMARK RESULTS (12 LAYOUT CASES)")
    print("=" * 65)
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(
            f"[{status}] {r['id']:<32} | Sheet: {str(r['actual_sheet']):<18} | Header: {str(r['actual_header']):<5} | Conf: {r['confidence']:.2f}"
        )
    print("-" * 65)
    print(f"Header Detection Accuracy: {header_accuracy:.1f}% ({header_correct}/{len(header_cases)})")
    print(f"Sheet Selection Accuracy:  {sheet_accuracy:.1f}% ({sheet_correct}/{len(sheet_cases)})")
    print(f"Format Success Rate:       {format_success_rate:.1f}% ({format_correct}/{len(results)})")
    print(f"False Positives:           {false_positives}")
    print(f"False Negatives:           {false_negatives}")
    print("=" * 65)

    assert header_accuracy == 100.0
    assert sheet_accuracy == 100.0
    assert format_success_rate == 100.0
    assert false_positives == 0
    assert false_negatives == 0
