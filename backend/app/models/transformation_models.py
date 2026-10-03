from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field


class Transformation(BaseModel):
    """Record of an approved and executed data transformation."""

    row: int = Field(..., description="1-indexed row number in the dataset")
    field: str = Field(..., description="Field/column name transformed")
    before: Any = Field(..., description="Value prior to transformation")
    after: Any = Field(..., description="Value after transformation")
    transformation: str = Field(
        ...,
        description="Description of the transformation applied (e.g. 'currency_formatting', 'human_edit')",
    )
    approved_by: str = Field(
        ..., description="Identifier of the human reviewer who authorized this change"
    )
    approved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the change was authorized/executed",
    )


class TransformationReport(BaseModel):
    """Summary of all transformations applied to a dataset."""

    job_id: str = Field(..., description="Associated job ID")
    total_transformations: int = Field(default=0, description="Total changes executed")
    transformations: list[Transformation] = Field(
        default_factory=list, description="Detailed list of transformations"
    )
    output_file_path: str | None = Field(
        default=None, description="Path or reference to the cleaned output file"
    )
