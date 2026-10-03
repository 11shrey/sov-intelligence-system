"""Excel Service & Excel Output Service

Helper service for interacting with Excel workbooks (.xlsx, .xls) and CSVs
using Pandas and OpenPyXL.
Integrates Member 3 ExcelOutputService for standardized 17-column SOV export.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


# ---------------------------------------------------------------------------
# Canonical schema — the ONE source of truth for column names and order
# ---------------------------------------------------------------------------

STRING_FIELDS: List[str] = [
    "Reference",
    "Zip",
    "County",
    "Other",
]

STANDARD_FIELDS: List[str] = [
    "Reference",
    "Address",
    "City",
    "State",
    "Zip",
    "County",
    "Country",
    "Building Value",
    "Contents",
    "BI",
    "Occupancy",
    "Construction",
    "Storeys",
    "Number of Buildings",
    "Year Built",
    "Fire Sprinklers (Y/N)",
    "Other",
]

WORKSHEET_NAME = "Cleaned SOV"


# ---------------------------------------------------------------------------
# ExcelOutputService — Member 3 Cleaned SOV Writer
# ---------------------------------------------------------------------------

class ExcelOutputService:
    """
    Writes the final Cleaned SOV workbook.

    Usage
    ~~~~~
        service = ExcelOutputService()
        service.write(
            records=[
                {"Reference": "LOC-001", "Building Value": 1_250_000.0, ...},
                {"Reference": "LOC-002", "Building Value":   900_000.0, ...},
            ],
            output_path="output/Cleaned_SOV.xlsx",
        )
    """

    def write(
        self,
        records: List[Dict[str, Any]],
        output_path: str | Path,
    ) -> Path:
        """
        Build and write the Cleaned_SOV.xlsx workbook.

        Parameters
        ----------
        records     : List of transformed SOV row dicts (from Agent 4).
                      May be empty — an empty workbook with 17 headers is valid.
        output_path : Destination file path (.xlsx).
                      Parent directory is created automatically.

        Returns
        -------
        The resolved absolute Path where the file was written.

        Raises
        ------
        ValueError  if schema validation fails (wrong columns / wrong order).
        """
        output_path = Path(output_path)

        # Build the standardised DataFrame
        df = self._build_dataframe(records)

        # Validate before touching the filesystem
        self._validate_schema(df)

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the workbook then apply text-format to identifier columns
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=WORKSHEET_NAME, index=False)

            # Force text number-format on columns that carry identifier / code
            # values so leading zeros (e.g. "02110") are preserved.
            ws = writer.sheets[WORKSHEET_NAME]
            self._apply_text_format(ws, df)

        return output_path.resolve()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_dataframe(records: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convert a list of transformed records into a standardised DataFrame.

        Steps:
        1. For each record, keep only the 17 standard fields.
        2. Fill missing standard fields with None.
        3. Order columns exactly as STANDARD_FIELDS.
        4. Original record dicts are not mutated (we work on copies).
        """
        rows: List[Dict[str, Any]] = []

        for record in records:
            row: Dict[str, Any] = {}
            for field in STANDARD_FIELDS:
                row[field] = record.get(field, None)
            rows.append(row)

        if rows:
            df = pd.DataFrame(rows, columns=STANDARD_FIELDS)
        else:
            df = pd.DataFrame(columns=STANDARD_FIELDS)

        return df

    @staticmethod
    def _apply_text_format(ws, df: pd.DataFrame) -> None:
        """
        Walk the header row to find STRING_FIELDS columns and set the
        openpyxl number-format on every data cell in those columns to '@'
        (plain text), preventing Excel from coercing values like '02110'.
        """
        for col_idx, col_name in enumerate(df.columns, start=1):
            if col_name not in STRING_FIELDS:
                continue
            for row_idx in range(2, len(df) + 2):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.number_format = "@"
                if cell.value is not None:
                    cell.value = str(cell.value)

    @staticmethod
    def _validate_schema(df: pd.DataFrame) -> None:
        """
        Assert the DataFrame has exactly the 17 standard columns in order.

        Raises ValueError with a clear message if anything is wrong.
        """
        actual_columns = list(df.columns)

        if len(actual_columns) != len(STANDARD_FIELDS):
            raise ValueError(
                f"Schema validation failed: expected {len(STANDARD_FIELDS)} columns, "
                f"got {len(actual_columns)}.\n"
                f"  Expected : {STANDARD_FIELDS}\n"
                f"  Actual   : {actual_columns}"
            )

        if actual_columns != STANDARD_FIELDS:
            raise ValueError(
                f"Schema validation failed: columns do not match STANDARD_FIELDS.\n"
                f"  Expected : {STANDARD_FIELDS}\n"
                f"  Actual   : {actual_columns}"
            )


# ---------------------------------------------------------------------------
# ExcelService — team utility service extending ExcelOutputService
# ---------------------------------------------------------------------------

class ExcelService(ExcelOutputService):
    """Utility service for reading, parsing, inspecting, and writing SOV spreadsheets."""

    def get_sheet_names(self, file_path: str | Path) -> list[str]:
        """
        Inspect workbook and return all sheet/tab names.

        Args:
            file_path: Path to the target spreadsheet.

        Returns:
            list[str]: Names of sheets found in the workbook.
        """
        # Placeholder for phase 3: openpyxl.load_workbook(file_path, read_only=True).sheetnames
        return ["Sheet1", "Locations", "Summary"]

    def read_sheet_sample(
        self, file_path: str | Path, sheet_name: str, max_rows: int = 15
    ) -> list[list[Any]]:
        """
        Read preview/sample rows from a specific sheet.

        Args:
            file_path: Path to the workbook.
            sheet_name: Target sheet name.
            max_rows: Number of top rows to sample.

        Returns:
            list[list[Any]]: Matrix of cell values.
        """
        # Placeholder for phase 3: pandas or openpyxl sample extraction
        return []

    def export_cleaned_sov(
        self, data: list[dict[str, Any]], output_path: str | Path
    ) -> str:
        """
        Write standardized 17-column SOV data to Excel.

        Args:
            data: Standardized record dictionaries.
            output_path: Target path for the output file.

        Returns:
            str: Path to written file.
        """
        resolved = self.write(records=data, output_path=output_path)
        return str(resolved)
