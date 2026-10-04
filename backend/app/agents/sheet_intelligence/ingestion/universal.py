"""Universal Ingestion interface for Agent 1.

Routes source files to the appropriate format-specific ingestor based on
deterministic file type detection (.xlsx, .csv, .json) and returns a uniform
IngestedWorkbook.
"""

from pathlib import Path

from app.agents.sheet_intelligence.errors import (
    FileNotFoundIngestionError,
    UnsupportedFormatError,
)
from app.agents.sheet_intelligence.ingestion.base import (
    IngestedWorkbook,
    TableIngestor,
)
from app.agents.sheet_intelligence.ingestion.csv_ingestor import CSVIngestor
from app.agents.sheet_intelligence.ingestion.excel_ingestor import ExcelIngestor
from app.agents.sheet_intelligence.ingestion.json_ingestor import JSONIngestor


class UniversalIngestor:
    """Universal facade for ingesting XLSX, CSV, and JSON files into a common internal representation."""

    SUPPORTED_EXTENSIONS: dict[str, type[TableIngestor]] = {
        ".xlsx": ExcelIngestor,
        ".csv": CSVIngestor,
        ".json": JSONIngestor,
    }

    def __init__(self) -> None:
        self._ingestors: dict[str, TableIngestor] = {
            ext: cls() for ext, cls in self.SUPPORTED_EXTENSIONS.items()
        }

    def ingest(
        self, file_path: str | Path, max_rows: int | None = None
    ) -> IngestedWorkbook:
        """Ingests a file of supported format (.xlsx, .csv, .json) into an IngestedWorkbook.

        Args:
            file_path: Path to the target file.
            max_rows: Optional row count limit for early-window inspection.

        Returns:
            IngestedWorkbook: Normalized tabular representation.

        Raises:
            FileNotFoundIngestionError: If file does not exist.
            UnsupportedFormatError: If file extension is not supported.
            EmptyFileError: If file has 0 bytes.
            CorruptedFileError: If file binary is damaged/unreadable.
            MalformedCSVError: If CSV cannot be parsed.
            MalformedJSONError: If JSON syntax is invalid.
            UnsupportedJSONStructureError: If JSON structure is not tabular.
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundIngestionError(
                f"File not found: {path}", file_path=str(path)
            )

        ext = path.suffix.lower()

        if ext not in self._ingestors:
            supported = ", ".join(sorted(self.SUPPORTED_EXTENSIONS.keys()))
            raise UnsupportedFormatError(
                f"Unsupported file format '{ext}'. Supported formats are: {supported}",
                file_path=str(path),
                details={"extension": ext, "supported": list(self.SUPPORTED_EXTENSIONS.keys())},
            )

        ingestor = self._ingestors[ext]
        return ingestor.ingest(file_path=path, max_rows=max_rows)
