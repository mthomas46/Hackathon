"""Tests for Analysis domain entity."""

import pytest
from datetime import datetime, timezone
from typing import Dict, Any

from ...domain.entities.analysis import Analysis, AnalysisStatus
from ...domain.value_objects.analysis_type import AnalysisType
from ...domain.value_objects.confidence import Confidence
from ...domain.value_objects.metrics import AnalysisMetrics


class TestAnalysisEntity:
    """Test cases for Analysis entity."""

    def test_analysis_creation_valid_data(self, sample_analysis_data: Dict[str, Any]):
        """Test creating an analysis with valid data."""
        analysis = Analysis(**sample_analysis_data)

        assert analysis.id == sample_analysis_data['id']
        assert analysis.document_id == sample_analysis_data['document_id']
        assert analysis.analysis_type == AnalysisType.SEMANTIC_SIMILARITY
        assert analysis.status == AnalysisStatus.COMPLETED
        assert analysis.confidence == Confidence(0.85)
        assert isinstance(analysis.metrics, AnalysisMetrics)
        assert analysis.results == sample_analysis_data['results']
        assert analysis.metadata == sample_analysis_data['metadata']
        assert isinstance(analysis.created_at, datetime)
        assert isinstance(analysis.completed_at, datetime)

    def test_analysis_creation_with_defaults(self):
        """Test creating an analysis with minimal required data."""
        minimal_data = {
            'id': 'minimal-analysis',
            'document_id': 'doc-001',
            'analysis_type': AnalysisType.CODE_QUALITY
        }

        analysis = Analysis(**minimal_data)

        assert analysis.id == 'minimal-analysis'
        assert analysis.document_id == 'doc-001'
        assert analysis.analysis_type == AnalysisType.CODE_QUALITY
        assert analysis.status == AnalysisStatus.PENDING
        assert analysis.confidence is None
        assert analysis.results == {}
        assert analysis.metadata == {}

    def test_analysis_creation_validation(self):
        """Test analysis creation validation."""
        with pytest.raises(ValueError):
            Analysis(id='', document_id='doc-001', analysis_type=AnalysisType.CODE_QUALITY)

        with pytest.raises(ValueError):
            Analysis(id='test', document_id='', analysis_type=AnalysisType.CODE_QUALITY)

    def test_analysis_status_transitions(self, sample_analysis: Analysis):
        """Test analysis status transitions."""
        assert sample_analysis.status == AnalysisStatus.COMPLETED

        sample_analysis.status = AnalysisStatus.RUNNING
        assert sample_analysis.status == AnalysisStatus.RUNNING

        sample_analysis.status = AnalysisStatus.FAILED
        assert sample_analysis.status == AnalysisStatus.FAILED

    def test_analysis_type_validation(self):
        """Test analysis type validation."""
        for analysis_type in AnalysisType:
            analysis = Analysis(
                id=f'test-{analysis_type.value}',
                document_id='doc-001',
                analysis_type=analysis_type
            )
            assert analysis.analysis_type == analysis_type

    def test_analysis_confidence_handling(self):
        """Test analysis confidence handling."""
        analysis = Analysis(
            id='confidence-test',
            document_id='doc-001',
            analysis_type=AnalysisType.SEMANTIC_SIMILARITY
        )

        assert analysis.confidence is None

        analysis.confidence = Confidence(0.75)
        assert analysis.confidence == Confidence(0.75)

        with pytest.raises(ValueError):
            analysis.confidence = Confidence(1.5)

    def test_analysis_metrics_integration(self, analysis_metrics: AnalysisMetrics):
        """Test analysis metrics integration."""
        analysis = Analysis(
            id='metrics-test',
            document_id='doc-001',
            analysis_type=AnalysisType.CODE_QUALITY,
            metrics=analysis_metrics
        )

        assert analysis.metrics == analysis_metrics
        assert analysis.metrics.processing_time_seconds == 3.5

    def test_analysis_equality(self):
        """Test analysis equality comparison."""
        analysis1 = Analysis(
            id='equal-analysis',
            document_id='doc-001',
            analysis_type=AnalysisType.CODE_QUALITY
        )

        analysis2 = Analysis(
            id='equal-analysis',
            document_id='doc-001',
            analysis_type=AnalysisType.CODE_QUALITY
        )

        analysis3 = Analysis(
            id='different-analysis',
            document_id='doc-001',
            analysis_type=AnalysisType.SEMANTIC_SIMILARITY
        )

        assert analysis1 == analysis2
        assert analysis1 != analysis3

    def test_analysis_factory_integration(self, analysis_factory, sample_analysis_data):
        """Test analysis creation through factory."""
        analysis = analysis_factory.create_analysis(**sample_analysis_data)

        assert isinstance(analysis, Analysis)
        assert analysis.id == sample_analysis_data['id']
        assert analysis.analysis_type == AnalysisType.SEMANTIC_SIMILARITY