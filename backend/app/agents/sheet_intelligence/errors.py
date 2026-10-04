"""Agent 1 Domain Exceptions.

Provides controlled, structured exceptions for Agent 1 operations,
specifically universal ingestion failures, malformed structures,
and unsupported formats.
"""

from typing import Any


class IngestionError(Exception):
    """Base exception for all ingestion layer errors."""

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.file_path = file_path
        self.details = details or {}

    def __str__(self) -> str:
        ctx = f" [file: {self.file_path}]" if self.file_path else ""
        return f"{self.message}{ctx}"


class FileNotFoundIngestionError(IngestionError):
    """Raised when the specified file path does not exist on disk."""

    pass


class UnsupportedFormatError(IngestionError):
    """Raised when the file extension is not among supported formats (.xlsx, .csv, .json)."""

    pass


class EmptyFileError(IngestionError):
    """Raised when the file is 0 bytes or completely empty of tabular content."""

    pass


class CorruptedFileError(IngestionError):
    """Raised when an XLSX, CSV, or JSON file is physically corrupted or unreadable."""

    pass


class MalformedCSVError(IngestionError):
    """Raised when a CSV cannot be parsed due to encoding or structural corruption."""

    pass


class MalformedJSONError(IngestionError):
    """Raised when a JSON file contains invalid syntax."""

    pass


class UnsupportedJSONStructureError(IngestionError):
    """Raised when JSON has valid syntax but does not match any approved tabular shape."""

    pass
