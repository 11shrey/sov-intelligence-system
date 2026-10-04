"""Agent 1 (Sheet Intelligence) package."""

from app.agents.sheet_intelligence.errors import (
    CorruptedFileError,
    EmptyFileError,
    FileNotFoundIngestionError,
    IngestionError,
    MalformedCSVError,
    MalformedJSONError,
    UnsupportedFormatError,
    UnsupportedJSONStructureError,
)
from app.agents.sheet_intelligence.ingestion import (
    CSVIngestor,
    ExcelIngestor,
    IngestedWorkbook,
    JSONIngestor,
    RawGrid,
    UniversalIngestor,
)

from app.agents.sheet_intelligence.semantics import (
    CellDetection,
    MatchedConcept,
    RowDetection,
    SemanticDetector,
)

from app.agents.sheet_intelligence.detection import (
    CandidateRowDetail,
    HeaderDetectionResult,
    HeaderDetector,
)

from app.agents.sheet_intelligence.scoring import (
    PrimaryTableSelector,
    TableCandidateSummary,
    TableSelectionResult,
)

from app.agents.sheet_intelligence.contracts import (
    Agent1HandoffResult,
    SemanticEvidenceItem,
    SheetEvaluationAudit,
)
from app.agents.sheet_intelligence.agent import (
    SheetIntelligenceEngine,
    analyze_file,
)

__all__ = [
    "IngestionError",
    "FileNotFoundIngestionError",
    "UnsupportedFormatError",
    "EmptyFileError",
    "CorruptedFileError",
    "MalformedCSVError",
    "MalformedJSONError",
    "UnsupportedJSONStructureError",
    "RawGrid",
    "IngestedWorkbook",
    "ExcelIngestor",
    "CSVIngestor",
    "JSONIngestor",
    "UniversalIngestor",
    "SemanticDetector",
    "MatchedConcept",
    "CellDetection",
    "RowDetection",
    "HeaderDetector",
    "HeaderDetectionResult",
    "CandidateRowDetail",
    "PrimaryTableSelector",
    "TableCandidateSummary",
    "TableSelectionResult",
    "Agent1HandoffResult",
    "SemanticEvidenceItem",
    "SheetEvaluationAudit",
    "SheetIntelligenceEngine",
    "analyze_file",
]
