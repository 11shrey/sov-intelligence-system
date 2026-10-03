"""Excel Service.

Helper service for interacting with Excel workbooks (.xlsx, .xlsm, .xls), CSVs, TSVs, and JSON files
using Pandas and OpenPyXL.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import pandas as pd
from app.models.schema_models import TARGET_SOV_FIELDS


class UnsupportedFormatError(ValueError):
    """Raised when an uploaded file format is not supported by the system."""
    pass


class ExcelService:
    """Utility service for reading, inspecting, and exporting SOV datasets across multiple file formats."""

    SUPPORTED_EXTENSIONS = {".xlsx", ".xlsm", ".xls", ".csv", ".tsv", ".json"}

    def detect_format(self, file_path: str | Path) -> str:
        """Detect and validate the file format from the file extension.

        Returns:
            str: Lowercase format identifier ('xlsx', 'xlsm', 'xls', 'csv', 'tsv', 'json').

        Raises:
            UnsupportedFormatError: If the extension is not supported.
        """
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext not in self.SUPPORTED_EXTENSIONS:
            raise UnsupportedFormatError(
                f"Unsupported file format '{ext}'. Supported formats: "
                f"{', '.join(sorted(ext.lstrip('.') for ext in self.SUPPORTED_EXTENSIONS))}"
            )

        return ext.lstrip(".")

    def get_sheet_names(self, file_path: str | Path) -> list[str]:
        """Return all sheet/tab names in a workbook or dataset.

        - Excel (.xlsx, .xlsm, .xls): returns all sheet names from workbook.
        - CSV / TSV: returns single logical sheet ['CSV'].
        - JSON:
            - list of records: ['JSON']
            - dict with sheet names as keys: list of keys
            - dict with single wrapper key holding list: [wrapper_key]
        """
        path = Path(file_path)
        fmt = self.detect_format(path)

        if fmt in {"csv", "tsv"}:
            return ["CSV"]

        if fmt in {"xlsx", "xlsm", "xls"}:
            with pd.ExcelFile(path) as excel_file:
                return list(excel_file.sheet_names)

        if fmt == "json":
            data = self._load_json_data(path)
            if isinstance(data, list):
                if not data:
                    raise ValueError("JSON file contains an empty list.")
                return ["JSON"]
            if isinstance(data, dict):
                if not data:
                    raise ValueError("JSON file contains an empty object.")
                # Check if all top-level values are lists of records
                if all(isinstance(v, list) for v in data.values()):
                    return list(data.keys())
                # If there's at least one list in dict, return keys with lists
                list_keys = [k for k, v in data.items() if isinstance(v, list)]
                if list_keys:
                    return list_keys
                return ["JSON"]
            raise ValueError(f"Unexpected JSON root structure: {type(data).__name__}")

        raise UnsupportedFormatError(f"Unsupported file format: {fmt}")

    def read_sheet_sample(
        self,
        file_path: str | Path,
        sheet_name: str,
        max_rows: int = 30,
    ) -> list[list[Any]]:
        """Read a raw preview of a sheet preserving row positions.

        The preview intentionally does not assume that row 0 is the header.
        Agent 1 uses these raw rows to detect the real header row.
        """
        path = Path(file_path)
        fmt = self.detect_format(path)

        if fmt in {"xlsx", "xlsm", "xls"}:
            with pd.ExcelFile(path) as excel_file:
                df = pd.read_excel(
                    excel_file,
                    sheet_name=sheet_name,
                    header=None,
                    nrows=max_rows,
                )
            df = df.astype(object).where(pd.notna(df), None)
            return df.values.tolist()

        if fmt in {"csv", "tsv"}:
            rows = self._read_csv_raw_rows(path, max_rows=max_rows)
            return rows

        if fmt == "json":
            df = self._load_json_dataframe(path, sheet_name)
            # Emit row 0 as column headers, followed by data rows
            header_row = [str(col) for col in df.columns]
            sample_df = df.iloc[: max(0, max_rows - 1)]
            sample_df = sample_df.astype(object).where(pd.notna(sample_df), None)
            data_rows = sample_df.values.tolist()
            return [header_row] + data_rows

        raise UnsupportedFormatError(f"Unsupported file format: {fmt}")

    def read_sheet(
        self,
        file_path: str | Path,
        sheet_name: str,
        header_row: int | None = None,
    ) -> pd.DataFrame:
        """Read the full sheet into a pandas DataFrame using the detected header row.

        Args:
            file_path: Path to dataset.
            sheet_name: Sheet/tab identifier.
            header_row: 0-indexed row number containing headers. If None, read without header.

        Returns:
            pd.DataFrame: Table with NaN/NaT converted to None.
        """
        path = Path(file_path)
        fmt = self.detect_format(path)

        if fmt in {"xlsx", "xlsm", "xls"}:
            with pd.ExcelFile(path) as excel_file:
                df = pd.read_excel(
                    excel_file,
                    sheet_name=sheet_name,
                    header=header_row,
                )
            return df.astype(object).where(pd.notna(df), None)

        if fmt in {"csv", "tsv"}:
            raw_rows = self._read_csv_raw_rows(path, max_rows=None)
            if not raw_rows:
                return pd.DataFrame()
            if header_row is not None and 0 <= header_row < len(raw_rows):
                headers = [
                    str(val).strip() if val is not None and str(val).strip() else f"Unnamed_{i}"
                    for i, val in enumerate(raw_rows[header_row])
                ]
                data_rows = raw_rows[header_row + 1 :]
                df = pd.DataFrame(data_rows, columns=headers)
            else:
                df = pd.DataFrame(raw_rows)
            return df.astype(object).where(pd.notna(df), None)

        if fmt == "json":
            df = self._load_json_dataframe(path, sheet_name)
            return df.astype(object).where(pd.notna(df), None)

        raise UnsupportedFormatError(f"Unsupported file format: {fmt}")

    def load_selected_table(self, state: Any) -> pd.DataFrame:
        """Load the primary selected table from the shared pipeline state.

        Allows Agent 2, Agent 3, and Agent 4 to consume tabular data consistently
        regardless of the underlying input file format.
        """
        if not state.file_info or not state.file_info.file_path:
            raise ValueError("No file path found in pipeline state.")

        file_path = state.file_info.file_path
        sheet_name = state.selected_sheet or self.get_sheet_names(file_path)[0]
        header_row = state.header_row

        return self.read_sheet(file_path, sheet_name, header_row=header_row)

    def export_cleaned_sov(
        self,
        data: list[dict[str, Any]] | pd.DataFrame,
        output_path: str | Path | None = None,
        job_id: str | None = None,
        output_format: str = "csv",
    ) -> str:
        """Standardize and export the cleaned SOV dataset.

        - Guarantees exactly the 17 canonical SOV columns in the standard sequence.
        - Missing columns are populated as empty.
        - Supports 'xlsx', 'csv' (utf-8-sig), and 'json' formats.
        - Writes output to data/output/{job_id}/ directory.

        Returns:
            str: Path to the generated output file.
        """
        # Convert input to DataFrame if necessary
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            df = pd.DataFrame(list(data))

        # Reindex / ensure exactly the 17 standard SOV columns in order
        aligned_df = pd.DataFrame()
        for col in TARGET_SOV_FIELDS:
            if col in df.columns:
                aligned_df[col] = df[col]
            else:
                aligned_df[col] = None

        # Clean NaN/NaT
        aligned_df = aligned_df.astype(object).where(pd.notna(aligned_df), None)

        # Normalize format
        fmt = output_format.lower().lstrip(".")
        if fmt not in {"csv", "xlsx", "json"}:
            fmt = "csv"

        # Determine target file path
        if output_path is None:
            folder = Path(f"data/output/{job_id or 'export'}")
            folder.mkdir(parents=True, exist_ok=True)
            output_file = folder / f"cleaned_sov_{job_id or 'export'}.{fmt}"
        else:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

        if fmt == "csv":
            aligned_df.to_csv(output_file, index=False, encoding="utf-8-sig")
        elif fmt == "xlsx":
            aligned_df.to_excel(output_file, index=False, engine="openpyxl")
        elif fmt == "json":
            records = aligned_df.to_dict(orient="records")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, default=str)

        return str(output_file)

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _read_csv_raw_rows(
        self, file_path: Path, max_rows: int | None = None
    ) -> list[list[Any]]:
        """Read CSV/TSV with automatic delimiter sniffing and encoding fallback."""
        content: str | None = None
        for enc in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, LookupError):
                continue

        if content is None:
            with open(file_path, "r", encoding="latin-1", errors="replace") as f:
                content = f.read()

        if file_path.suffix.lower() == ".tsv":
            delimiter = "\t"
        else:
            sample = content[:4096]
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=";,|\t")
                delimiter = dialect.delimiter
            except Exception:
                # Count delimiter frequencies
                counts = {
                    ",": sample.count(","),
                    ";": sample.count(";"),
                    "\t": sample.count("\t"),
                    "|": sample.count("|"),
                }
                delimiter = max(counts, key=counts.get) if max(counts.values()) > 0 else ","

        lines = content.splitlines()
        if max_rows is not None:
            lines = lines[:max_rows]

        reader = csv.reader(lines, delimiter=delimiter)
        raw_rows: list[list[Any]] = []
        max_cols = 0

        for row in reader:
            raw_rows.append(row)
            if len(row) > max_cols:
                max_cols = len(row)

        # Pad ragged rows so every row has max_cols length
        padded_rows: list[list[Any]] = []
        for row in raw_rows:
            padded = list(row)
            if len(padded) < max_cols:
                padded.extend([None] * (max_cols - len(padded)))
            # Convert empty strings to None
            normalized = [val if val != "" else None for val in padded]
            padded_rows.append(normalized)

        return padded_rows

    def _load_json_data(self, file_path: Path) -> Any:
        """Load JSON file with encoding fallback."""
        for enc in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    return json.load(f)
            except (UnicodeDecodeError, LookupError):
                continue
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON content in {file_path.name}: {exc}") from exc

        raise ValueError(f"Could not decode JSON file {file_path.name}")

    def _load_json_dataframe(self, file_path: Path, sheet_name: str) -> pd.DataFrame:
        """Parse JSON content into a normalized pandas DataFrame."""
        data = self._load_json_data(file_path)

        records: list[Any] = []
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict):
            if sheet_name in data and isinstance(data[sheet_name], list):
                records = data[sheet_name]
            elif len(data) == 1 and isinstance(list(data.values())[0], list):
                records = list(data.values())[0]
            else:
                # If dict is a single record
                records = [data]

        if not records:
            return pd.DataFrame()

        # Flatten nested objects with pandas json_normalize
        df = pd.json_normalize(records)
        return df