"""Tests for domain value objects."""

import pytest
from typing import Dict, Any

from ...domain.value_objects.confidence import Confidence
from ...domain.value_objects.analysis_type import AnalysisType
from ...domain.value_objects.location import FileLocation, CodeLocation
from ...domain.value_objects.metrics import AnalysisMetrics, QualityMetrics


class TestConfidenceValueObject:
    """Test cases for Confidence value object."""

    def test_confidence_creation_valid_values(self):
        """Test creating confidence with valid values."""
        confidence = Confidence(0.85)
        assert confidence.value == 0.85

        confidence = Confidence(0.0)
        assert confidence.value == 0.0

        confidence = Confidence(1.0)
        assert confidence.value == 1.0

    def test_confidence_creation_invalid_values(self):
        """Test creating confidence with invalid values."""
        with pytest.raises(ValueError):
            Confidence(-0.1)

        with pytest.raises(ValueError):
            Confidence(1.1)

        with pytest.raises(ValueError):
            Confidence(2.0)

    def test_confidence_equality(self):
        """Test confidence equality comparison."""
        conf1 = Confidence(0.75)
        conf2 = Confidence(0.75)
        conf3 = Confidence(0.85)

        assert conf1 == conf2
        assert conf1 != conf3

    def test_confidence_hash(self):
        """Test confidence hash for use in sets."""
        conf1 = Confidence(0.8)
        conf2 = Confidence(0.8)

        conf_set = {conf1, conf2}
        assert len(conf_set) == 1

    def test_confidence_string_representation(self):
        """Test confidence string representation."""
        confidence = Confidence(0.75)
        str_repr = str(confidence)
        assert '0.75' in str_repr

    def test_confidence_comparison(self, confidence_high, confidence_medium, confidence_low):
        """Test confidence comparison operations."""
        assert confidence_high > confidence_medium
        assert confidence_medium > confidence_low
        assert confidence_low < confidence_high

        assert confidence_high >= confidence_medium
        assert confidence_medium >= confidence_low
        assert confidence_high >= confidence_high

    def test_confidence_level_classification(self):
        """Test confidence level classification."""
        high_conf = Confidence(0.9)
        medium_conf = Confidence(0.7)
        low_conf = Confidence(0.3)

        # These would be methods in a real implementation
        assert high_conf.value >= 0.8  # High confidence
        assert 0.6 <= medium_conf.value < 0.8  # Medium confidence
        assert low_conf.value < 0.6  # Low confidence


class TestAnalysisTypeValueObject:
    """Test cases for AnalysisType value object."""

    def test_analysis_type_enum_values(self):
        """Test analysis type enum values."""
        assert AnalysisType.SEMANTIC_SIMILARITY.value == 'semantic_similarity'
        assert AnalysisType.CODE_QUALITY.value == 'code_quality'
        assert AnalysisType.SECURITY_SCAN.value == 'security_scan'
        assert AnalysisType.CROSS_REPOSITORY.value == 'cross_repository'

    def test_analysis_type_string_representation(self):
        """Test analysis type string representation."""
        analysis_type = AnalysisType.SEMANTIC_SIMILARITY
        assert str(analysis_type) == 'AnalysisType.SEMANTIC_SIMILARITY'

    def test_analysis_type_iteration(self):
        """Test iterating over analysis types."""
        types = list(AnalysisType)
        assert len(types) >= 4  # At least the basic types
        assert AnalysisType.SEMANTIC_SIMILARITY in types


class TestLocationValueObjects:
    """Test cases for location value objects."""

    def test_file_location_creation(self, file_location: FileLocation):
        """Test creating file location."""
        assert file_location.file_path == '/src/main.py'
        assert file_location.line_number == 42

    def test_file_location_string_representation(self, file_location: FileLocation):
        """Test file location string representation."""
        str_repr = str(file_location)
        assert '/src/main.py' in str_repr
        assert '42' in str_repr

    def test_code_location_creation(self, code_location: CodeLocation):
        """Test creating code location."""
        assert code_location.file_path == '/src/utils.py'
        assert code_location.start_line == 10
        assert code_location.end_line == 15
        assert code_location.start_column == 5
        assert code_location.end_column == 25

    def test_code_location_validation(self):
        """Test code location validation."""
        # Valid location
        location = CodeLocation(
            file_path='/src/file.py',
            start_line=10,
            end_line=15,
            start_column=5,
            end_column=20
        )
        assert location.start_line < location.end_line
        assert location.start_column < location.end_column

    def test_code_location_string_representation(self, code_location: CodeLocation):
        """Test code location string representation."""
        str_repr = str(code_location)
        assert '/src/utils.py' in str_repr
        assert '10:15' in str_repr

    def test_location_equality(self):
        """Test location equality."""
        loc1 = FileLocation('/src/main.py', 42)
        loc2 = FileLocation('/src/main.py', 42)
        loc3 = FileLocation('/src/main.py', 43)

        assert loc1 == loc2
        assert loc1 != loc3


class TestAnalysisMetricsValueObject:
    """Test cases for AnalysisMetrics value object."""

    def test_analysis_metrics_creation(self, analysis_metrics: AnalysisMetrics):
        """Test creating analysis metrics."""
        assert analysis_metrics.processing_time_seconds == 3.5
        assert analysis_metrics.memory_usage_mb == 75.0
        assert analysis_metrics.confidence_score == 0.82

    def test_analysis_metrics_validation(self):
        """Test analysis metrics validation."""
        # Valid metrics
        metrics = AnalysisMetrics(
            processing_time_seconds=5.0,
            memory_usage_mb=100.0,
            confidence_score=0.9
        )
        assert metrics.processing_time_seconds == 5.0

        # Test negative values (should be allowed for metrics)
        metrics = AnalysisMetrics(
            processing_time_seconds=-1.0,  # Might indicate error
            memory_usage_mb=0.0,
            confidence_score=0.5
        )
        assert metrics.processing_time_seconds == -1.0

    def test_analysis_metrics_string_representation(self, analysis_metrics: AnalysisMetrics):
        """Test analysis metrics string representation."""
        str_repr = str(analysis_metrics)
        assert '3.5' in str_repr
        assert '75.0' in str_repr

    def test_analysis_metrics_equality(self):
        """Test analysis metrics equality."""
        metrics1 = AnalysisMetrics(3.5, 75.0, 0.82)
        metrics2 = AnalysisMetrics(3.5, 75.0, 0.82)
        metrics3 = AnalysisMetrics(4.0, 80.0, 0.85)

        assert metrics1 == metrics2
        assert metrics1 != metrics3


class TestQualityMetricsValueObject:
    """Test cases for QualityMetrics value object."""

    def test_quality_metrics_creation(self, quality_metrics: QualityMetrics):
        """Test creating quality metrics."""
        assert quality_metrics.readability_score == 85.0
        assert quality_metrics.complexity_score == 25.0
        assert quality_metrics.maintainability_index == 78.0
        assert quality_metrics.duplication_percentage == 5.2

    def test_quality_metrics_validation(self):
        """Test quality metrics validation."""
        # Test boundary values
        metrics = QualityMetrics(
            readability_score=0.0,
            complexity_score=0.0,
            maintainability_index=0.0,
            duplication_percentage=0.0
        )
        assert metrics.readability_score == 0.0

        metrics = QualityMetrics(
            readability_score=100.0,
            complexity_score=100.0,
            maintainability_index=100.0,
            duplication_percentage=100.0
        )
        assert metrics.readability_score == 100.0

    def test_quality_metrics_ranges(self):
        """Test quality metrics typical ranges."""
        metrics = QualityMetrics(85.0, 25.0, 78.0, 5.2)

        # Readability should typically be 0-100
        assert 0 <= metrics.readability_score <= 100

        # Complexity score is typically a positive number
        assert metrics.complexity_score >= 0

        # Maintainability index is typically 0-100
        assert 0 <= metrics.maintainability_index <= 100

        # Duplication percentage is typically 0-100
        assert 0 <= metrics.duplication_percentage <= 100

    def test_quality_metrics_string_representation(self, quality_metrics: QualityMetrics):
        """Test quality metrics string representation."""
        str_repr = str(quality_metrics)
        assert '85.0' in str_repr
        assert '25.0' in str_repr

    def test_quality_metrics_equality(self):
        """Test quality metrics equality."""
        metrics1 = QualityMetrics(85.0, 25.0, 78.0, 5.2)
        metrics2 = QualityMetrics(85.0, 25.0, 78.0, 5.2)
        metrics3 = QualityMetrics(90.0, 30.0, 80.0, 8.0)

        assert metrics1 == metrics2
        assert metrics1 != metrics3


class TestValueObjectImmutability:
    """Test immutability of value objects."""

    def test_confidence_immutability(self):
        """Test that confidence is immutable."""
        confidence = Confidence(0.75)

        # Value should not be changeable after creation
        with pytest.raises(AttributeError):
            confidence.value = 0.85

        assert confidence.value == 0.75

    def test_location_immutability(self, file_location: FileLocation):
        """Test that locations are immutable."""
        # File path should not be changeable
        with pytest.raises(AttributeError):
            file_location.file_path = '/new/path.py'

        # Line number should not be changeable
        with pytest.raises(AttributeError):
            file_location.line_number = 100

        assert file_location.file_path == '/src/main.py'
        assert file_location.line_number == 42

    def test_metrics_immutability(self, analysis_metrics: AnalysisMetrics):
        """Test that metrics are immutable."""
        # Processing time should not be changeable
        with pytest.raises(AttributeError):
            analysis_metrics.processing_time_seconds = 10.0

        # Memory usage should not be changeable
        with pytest.raises(AttributeError):
            analysis_metrics.memory_usage_mb = 200.0

        assert analysis_metrics.processing_time_seconds == 3.5
        assert analysis_metrics.memory_usage_mb == 75.0


class TestValueObjectHashAndEquality:
    """Test hash and equality for value objects."""

    def test_confidence_hash_consistency(self):
        """Test that equal confidences have equal hashes."""
        conf1 = Confidence(0.8)
        conf2 = Confidence(0.8)

        assert conf1 == conf2
        assert hash(conf1) == hash(conf2)

    def test_location_hash_consistency(self):
        """Test that equal locations have equal hashes."""
        loc1 = FileLocation('/src/main.py', 42)
        loc2 = FileLocation('/src/main.py', 42)

        assert loc1 == loc2
        assert hash(loc1) == hash(loc2)

    def test_metrics_hash_consistency(self):
        """Test that equal metrics have equal hashes."""
        metrics1 = AnalysisMetrics(3.5, 75.0, 0.82)
        metrics2 = AnalysisMetrics(3.5, 75.0, 0.82)

        assert metrics1 == metrics2
        assert hash(metrics1) == hash(metrics2)


class TestValueObjectEdgeCases:
    """Test edge cases for value objects."""

    def test_confidence_edge_values(self):
        """Test confidence edge values."""
        # Exactly 0
        conf = Confidence(0.0)
        assert conf.value == 0.0

        # Exactly 1
        conf = Confidence(1.0)
        assert conf.value == 1.0

        # Very close to boundaries
        conf = Confidence(0.000001)
        assert conf.value == 0.000001

        conf = Confidence(0.999999)
        assert conf.value == 0.999999

    def test_location_edge_cases(self):
        """Test location edge cases."""
        # Line 1 (first line)
        loc = FileLocation('/file.py', 1)
        assert loc.line_number == 1

        # Very large line number
        loc = FileLocation('/file.py', 1000000)
        assert loc.line_number == 1000000

        # Empty file path (should this be allowed?)
        loc = FileLocation('', 1)
        assert loc.file_path == ''

    def test_metrics_edge_cases(self):
        """Test metrics edge cases."""
        # Zero values
        metrics = AnalysisMetrics(0.0, 0.0, 0.0)
        assert metrics.processing_time_seconds == 0.0
        assert metrics.memory_usage_mb == 0.0
        assert metrics.confidence_score == 0.0

        # Very large values
        metrics = AnalysisMetrics(1000000.0, 1000000.0, 1.0)
        assert metrics.processing_time_seconds == 1000000.0
        assert metrics.memory_usage_mb == 1000000.0

        # Very small positive values
        metrics = AnalysisMetrics(0.000001, 0.000001, 0.000001)
        assert metrics.processing_time_seconds == 0.000001