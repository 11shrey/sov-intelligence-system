"""Base interfaces and internal data models for Agent 1 Universal Ingestion."""

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(slots=True)
class RawGrid:
    """Represents a 2D raw cell grid for a single sheet or table."""

    name: str
    matrix: list[list[Any]]
    total_rows: int
    total_cols: int

    @classmethod
    def from_rows(cls, name: str, rows: list[list[Any]]) -> "RawGrid":
        """Construct a RawGrid from a list of rows, computing row/column dimensions."""
        total_rows = len(rows)
        total_cols = max((len(r) for r in rows), default=0)
        return cls(
            name=name,
            matrix=rows,
            total_rows=total_rows,
            total_cols=total_cols,
        )


@dataclass(slots=True)
class IngestedWorkbook:
    """Normalized internal representation produced by any format ingestor.

    Downstream Agent 1 components consume this structure without needing to know
    whether the underlying file was XLSX, CSV, or JSON.
    """

    source_path: str
    file_type: str  # "xlsx" | "csv" | "json"
    tables: dict[str, RawGrid] = field(default_factory=dict)

    def to_dict(self) -> dict[str, list[list[Any]]]:
        """Convert to the canonical conceptual dictionary:

        {
            "table_or_sheet_name": [
                [cell1, cell2, cell3],
                [cell1, cell2, cell3]
            ]
        }
        """
        return {name: grid.matrix for name, grid in self.tables.items()}


class TableIngestor(Protocol):
    """Protocol for file-format specific ingestors."""

    def ingest(
        self, file_path: str, max_rows: int | None = None
    ) -> IngestedWorkbook:
        """Ingest a source file and return an IngestedWorkbook."""
        ...
