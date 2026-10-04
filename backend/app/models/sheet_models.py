from pydantic import BaseModel, Field


class SheetAnalysis(BaseModel):
    """Analysis of an individual sheet within an uploaded Excel workbook."""

    sheet_name: str = Field(..., description="Name of the sheet tab")
    is_candidate: bool = Field(
        ..., description="Whether this sheet is identified as a candidate SOV table"
    )
    header_row: int | None = Field(
        default=None,
        description="0-indexed row number containing headers (matches pandas header=N, UI may display +1), or None if not identified",
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0"
    )
    reasoning: str = Field(
        ..., description="Rationale for candidate classification and header detection"
    )


class SheetAnalysisReport(BaseModel):
    """Aggregate analysis across all sheets in a workbook."""

    sheets: list[SheetAnalysis] = Field(
        default_factory=list, description="List of per-sheet analyses"
    )
    selected_sheet: str | None = Field(
        default=None, description="Primary sheet selected for SOV processing"
    )
    header_row: int | None = Field(
        default=None, description="Header row for the selected sheet"
    )
