"""CSV Ingestion implementation using pandas with encoding and dialect detection."""

import csv
from pathlib import Path
from typing import Any
import pandas as pd

from app.agents.sheet_intelligence.errors import (
    EmptyFileError,
    FileNotFoundIngestionError,
    MalformedCSVError,
)
from app.agents.sheet_intelligence.ingestion.base import (
    IngestedWorkbook,
    RawGrid,
    TableIngestor,
)


class CSVIngestor(TableIngestor):
    """Ingests CSV files into a single logical table without assuming row 0 is header."""

    CANDIDATE_ENCODINGS = ("utf-8-sig", "utf-8", "latin-1", "cp1252")

    def ingest(
        self, file_path: str | Path, max_rows: int | None = None
    ) -> IngestedWorkbook:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundIngestionError(
                f"File not found: {path}", file_path=str(path)
            )

        if path.stat().st_size == 0:
            raise EmptyFileError(
                f"File is empty (0 bytes): {path}", file_path=str(path)
            )

        # Detect encoding and delimiter
        encoding = self._detect_encoding(path)
        delimiter = self._detect_delimiter(path, encoding)

        try:
            raw_rows: list[list[Any]] = []
            with open(path, "r", encoding=encoding, errors="replace", newline="") as f:
                reader = csv.reader(f, delimiter=delimiter)
                for row_idx, row in enumerate(reader):
                    if max_rows is not None and row_idx >= max_rows:
                        break
                    # Normalize empty strings to None, preserve strings and numbers
                    cleaned_row = [None if cell == "" else cell for cell in row]
                    raw_rows.append(cleaned_row)
        except Exception as exc:
            raise MalformedCSVError(
                f"Failed to parse CSV file: {exc}",
                file_path=str(path),
                details={"error": str(exc), "encoding": encoding},
            ) from exc

        # Strip trailing completely empty rows while preserving leading and interior blanks
        last_data_idx = -1
        for idx, r in enumerate(raw_rows):
            if any(cell is not None and str(cell).strip() != "" for cell in r):
                last_data_idx = idx

        if last_data_idx >= 0:
            trimmed_rows = raw_rows[: last_data_idx + 1]
        else:
            trimmed_rows = []

        # Pad rows to max_cols to ensure consistent column grid alignment
        max_cols = max((len(r) for r in trimmed_rows), default=0)
        padded_rows = [
            r + [None] * (max_cols - len(r)) for r in trimmed_rows
        ]

        grid = RawGrid.from_rows(name="default", rows=padded_rows)

        return IngestedWorkbook(
            source_path=str(path),
            file_type="csv",
            tables={"default": grid},
        )

    def _detect_encoding(self, path: Path) -> str:
        """Deterministically test candidate encodings with BOM signature checking."""
        with open(path, "rb") as f:
            raw_sample = f.read(32768)

        if raw_sample.startswith(b"\xef\xbb\xbf"):
            return "utf-8-sig"

        for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
            try:
                raw_sample.decode(enc)
                return enc
            except (UnicodeDecodeError, LookupError):
                continue

        return "latin-1"

    def _detect_delimiter(self, path: Path, encoding: str) -> str:
        """Sniff delimiter from sample lines, defaulting to comma."""
        try:
            with open(path, "r", encoding=encoding, errors="replace") as f:
                sample = "".join(f.readline() for _ in range(20))
            if not sample.strip():
                return ","
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample, delimiters=",;\t|")
            return dialect.delimiter
        except Exception:
            return ","
