"""JSON Ingestion implementation using orjson for fast tabular normalization."""

from pathlib import Path
from typing import Any
import orjson

from app.agents.sheet_intelligence.errors import (
    EmptyFileError,
    FileNotFoundIngestionError,
    MalformedJSONError,
    UnsupportedJSONStructureError,
)
from app.agents.sheet_intelligence.ingestion.base import (
    IngestedWorkbook,
    RawGrid,
    TableIngestor,
)


class JSONIngestor(TableIngestor):
    """Ingests supported tabular JSON shapes and normalizes them into 2D row grids."""

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

        try:
            content = path.read_bytes()
            data = orjson.loads(content)
        except orjson.JSONDecodeError as exc:
            raise MalformedJSONError(
                f"Invalid JSON syntax: {exc}",
                file_path=str(path),
                details={"error": str(exc)},
            ) from exc

        tables: dict[str, RawGrid] = {}

        if isinstance(data, list):
            tables["default"] = self._normalize_list(
                name="default", items=data, max_rows=max_rows
            )
        elif isinstance(data, dict):
            tables = self._normalize_dict(data=data, max_rows=max_rows)
        else:
            raise UnsupportedJSONStructureError(
                f"Unsupported JSON root type: expected list or object, got {type(data).__name__}",
                file_path=str(path),
            )

        return IngestedWorkbook(
            source_path=str(path),
            file_type="json",
            tables=tables,
        )

    def _normalize_list(
        self, name: str, items: list[Any], max_rows: int | None = None
    ) -> RawGrid:
        """Normalize a JSON array: either an array of objects or an array of arrays."""
        if not items:
            return RawGrid.from_rows(name=name, rows=[])

        first_item = items[0]

        # Case 1: List of Dictionaries / Objects
        if isinstance(first_item, dict):
            keys: list[str] = []
            seen_keys: set[str] = set()

            for item in items:
                if not isinstance(item, dict):
                    raise UnsupportedJSONStructureError(
                        f"Inconsistent list elements in table '{name}': expected dict, got {type(item).__name__}"
                    )
                for k in item.keys():
                    if k not in seen_keys:
                        seen_keys.add(k)
                        keys.append(k)

            # Row 0: Original keys verbatim
            rows: list[list[Any]] = [list(keys)]

            target_items = items
            if max_rows is not None:
                # 1 row already taken by header
                target_items = items[: max(0, max_rows - 1)]

            for item in target_items:
                rows.append([item.get(k) for k in keys])

            return RawGrid.from_rows(name=name, rows=rows)

        # Case 2: List of Lists (2D Array)
        if isinstance(first_item, list):
            target_items = items
            if max_rows is not None:
                target_items = items[:max_rows]

            rows = []
            for row in target_items:
                if not isinstance(row, list):
                    raise UnsupportedJSONStructureError(
                        f"Inconsistent 2D array row in table '{name}': expected list, got {type(row).__name__}"
                    )
                rows.append(list(row))
            return RawGrid.from_rows(name=name, rows=rows)

        raise UnsupportedJSONStructureError(
            f"Unsupported JSON list contents in table '{name}': elements must be objects or arrays, got {type(first_item).__name__}"
        )

    def _normalize_dict(
        self, data: dict[str, Any], max_rows: int | None = None
    ) -> dict[str, RawGrid]:
        """Normalize a JSON dictionary containing tables or column-oriented data."""
        if not data:
            return {"default": RawGrid.from_rows(name="default", rows=[])}

        # Check if all values are lists
        all_lists = all(isinstance(v, list) for v in data.values())

        # Sub-case A: Check if this is a column-oriented dictionary (e.g. {"ColA": [1, 2], "ColB": [3, 4]})
        # where list elements are scalar values (not dicts or lists)
        if all_lists and data:
            all_scalar_lists = True
            for v in data.values():
                if v and (isinstance(v[0], dict) or isinstance(v[0], list)):
                    all_scalar_lists = False
                    break
            if all_scalar_lists:
                keys = list(data.keys())
                rows: list[list[Any]] = [keys]
                max_len = max((len(data[k]) for k in keys), default=0)
                if max_rows is not None:
                    max_len = min(max_len, max(0, max_rows - 1))
                for idx in range(max_len):
                    row = [
                        data[k][idx] if idx < len(data[k]) else None
                        for k in keys
                    ]
                    rows.append(row)
                return {"default": RawGrid.from_rows(name="default", rows=rows)}

        # Sub-case B: Dictionary containing one or more tables (list of dicts or list of lists)
        tables: dict[str, RawGrid] = {}
        for key, val in data.items():
            if isinstance(val, list):
                tables[key] = self._normalize_list(
                    name=key, items=val, max_rows=max_rows
                )
            elif isinstance(val, dict):
                # Nested table or column-oriented table under a key
                nested = self._normalize_dict(data=val, max_rows=max_rows)
                for nested_name, nested_grid in nested.items():
                    combined_name = (
                        key if nested_name == "default" else f"{key}_{nested_name}"
                    )
                    tables[combined_name] = RawGrid.from_rows(
                        name=combined_name, rows=nested_grid.matrix
                    )

        if tables:
            return tables

        raise UnsupportedJSONStructureError(
            "Unsupported JSON structure: dictionary does not contain tabular lists or column vectors"
        )
