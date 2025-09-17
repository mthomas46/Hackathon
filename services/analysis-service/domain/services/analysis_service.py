"""Analysis domain service."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..entities import Document, Analysis, AnalysisId, AnalysisStatus
from ..entities.value_objects import AnalysisType, AnalysisConfiguration


class AnalysisService:
    """Domain service for analysis operations."""

    def __init__(self, analysis_engines: Dict[str, Any]):
        """Initialize analysis service with available engines."""
        self.analysis_engines = analysis_engines

    def create_analysis(self, document: Document, analysis_type: AnalysisType,
                       configuration: AnalysisConfiguration) -> Analysis:
        """Create a new analysis for a document."""
        analysis_id = AnalysisId(f"analysis_{datetime.now().timestamp()}_{document.id.value}")

        analysis = Analysis(
            id=analysis_id,
            document_id=document.id,
            analysis_type=analysis_type.value,
            configuration=configuration.__dict__
        )

        return analysis

    def execute_analysis(self, analysis: Analysis) -> Dict[str, Any]:
        """Execute an analysis using the appropriate engine."""
        if analysis.analysis_type not in self.analysis_engines:
            raise ValueError(f"No engine available for analysis type: {analysis.analysis_type}")

        engine = self.analysis_engines[analysis.analysis_type]

        try:
            # Execute the analysis
            result = engine.execute(analysis)

            # Validate result structure
            self._validate_analysis_result(result)

            return result

        except Exception as e:
            raise RuntimeError(f"Analysis execution failed: {str(e)}")

    def validate_analysis_configuration(self, analysis_type: AnalysisType,
                                       configuration: AnalysisConfiguration) -> bool:
        """Validate analysis configuration."""
        if analysis_type.value not in self.analysis_engines:
            return False

        engine = self.analysis_engines[analysis_type.value]
        return engine.validate_configuration(configuration)

    def get_supported_analysis_types(self) -> List[str]:
        """Get list of supported analysis types."""
        return list(self.analysis_engines.keys())

    def estimate_analysis_time(self, analysis_type: AnalysisType,
                             document_size: int) -> float:
        """Estimate execution time for an analysis."""
        if analysis_type.value not in self.analysis_engines:
            raise ValueError(f"Unsupported analysis type: {analysis_type.value}")

        engine = self.analysis_engines[analysis_type.value]
        return engine.estimate_execution_time(document_size)

    def _validate_analysis_result(self, result: Dict[str, Any]) -> None:
        """Validate analysis result structure."""
        required_fields = ['status', 'timestamp', 'results']

        for field in required_fields:
            if field not in result:
                raise ValueError(f"Analysis result missing required field: {field}")

        if result['status'] not in ['success', 'partial', 'failed']:
            raise ValueError("Invalid analysis result status")

        if not isinstance(result['results'], dict):
            raise ValueError("Analysis results must be a dictionary")


class AnalysisEngine(ABC):
    """Abstract base class for analysis engines."""

    @abstractmethod
    def execute(self, analysis: Analysis) -> Dict[str, Any]:
        """Execute the analysis."""
        pass

    @abstractmethod
    def validate_configuration(self, configuration: AnalysisConfiguration) -> bool:
        """Validate analysis configuration."""
        pass

    @abstractmethod
    def estimate_execution_time(self, document_size: int) -> float:
        """Estimate execution time based on document size."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Get engine name."""
        pass
