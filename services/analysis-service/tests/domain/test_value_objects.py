"""Unit tests for domain value objects."""

import pytest
from typing import Dict, Any

from ...domain.value_objects import AnalysisType, Confidence, Location, Metrics
from ..conftest import assert_validation_error


class TestAnalysisType:
    """Test cases for AnalysisType value object."""

    def test_valid_analysis_types(self):
        """Test creating valid analysis types."""
        valid_types = [
            'consistency',
            'quality',
            'semantic_similarity',
            'sentiment',
            'tone',
            'trend',
            'risk',
            'maintenance',
            'degradation',
            'change_impact',
            'remediation'
        ]

        for analysis_type in valid_types:
            at = AnalysisType(analysis_type)
            assert at.value == analysis_type
            assert str(at) == analysis_type

    def test_invalid_analysis_type(self):
        """Test creating invalid analysis type."""
        assert_validation_error(AnalysisType, 'invalid_type')

    def test_analysis_type_equality(self):
        """Test analysis type equality."""
        at1 = AnalysisType('consistency')
        at2 = AnalysisType('consistency')
        at3 = AnalysisType('quality')

        assert at1 == at2
        assert at1 != at3
        assert at1 == 'consistency'  # Should work with string comparison

    def test_analysis_type_hash(self):
        """Test analysis type hash."""
        at = AnalysisType('consistency')
        assert hash(at) == hash('consistency')

        # Can be used in sets
        types_set = {at, AnalysisType('quality')}
        assert len(types_set) == 2


class TestConfidence:
    """Test cases for Confidence value object."""

    def test_valid_confidence_values(self):
        """Test creating confidence with valid values."""
        valid_values = [0.0, 0.5, 0.8, 1.0]

        for value in valid_values:
            confidence = Confidence(value=value)
            assert confidence.value == value

    def test_confidence_out_of_range_high(self):
        """Test confidence value too high."""
        assert_validation_error(Confidence, value=1.5)

    def test_confidence_out_of_range_low(self):
        """Test confidence value too low."""
        assert_validation_error(Confidence, value=-0.1)

    def test_confidence_default_value(self):
        """Test confidence default value."""
        confidence = Confidence()
        assert confidence.value == 0.5  # Default should be 0.5

    def test_confidence_equality(self):
        """Test confidence equality."""
        c1 = Confidence(value=0.8)
        c2 = Confidence(value=0.8)
        c3 = Confidence(value=0.9)

        assert c1 == c2
        assert c1 != c3

    def test_confidence_comparison(self):
        """Test confidence comparison operations."""
        c1 = Confidence(value=0.6)
        c2 = Confidence(value=0.8)

        assert c1 < c2
        assert c2 > c1
        assert c1 <= c2
        assert c2 >= c1
        assert c1 <= Confidence(value=0.6)
        assert c1 >= Confidence(value=0.6)

    def test_confidence_arithmetic(self):
        """Test confidence arithmetic operations."""
        c1 = Confidence(value=0.6)
        c2 = Confidence(value=0.2)

        result = c1 + c2
        assert isinstance(result, Confidence)
        assert result.value == 0.8

        result = c1 - c2
        assert isinstance(result, Confidence)
        assert result.value == 0.4

        result = c1 * 0.5
        assert isinstance(result, Confidence)
        assert result.value == 0.3

    def test_confidence_arithmetic_bounds(self):
        """Test confidence arithmetic respects bounds."""
        c1 = Confidence(value=0.9)
        c2 = Confidence(value=0.2)

        # Addition should be clamped to 1.0
        result = c1 + c2
        assert result.value == 1.0

        # Subtraction should be clamped to 0.0
        c_low = Confidence(value=0.1)
        result = c_low - c2
        assert result.value == 0.0

    def test_confidence_to_dict(self):
        """Test confidence to dictionary conversion."""
        confidence = Confidence(value=0.75)
        confidence_dict = confidence.to_dict()

        assert confidence_dict == {'value': 0.75}

    def test_confidence_from_dict(self):
        """Test confidence from dictionary creation."""
        confidence = Confidence.from_dict({'value': 0.85})
        assert confidence.value == 0.85

    def test_confidence_repr(self):
        """Test confidence string representation."""
        confidence = Confidence(value=0.7)
        repr_str = repr(confidence)

        assert 'Confidence' in repr_str
        assert '0.7' in repr_str


class TestLocation:
    """Test cases for Location value object."""

    def test_valid_location_values(self):
        """Test creating location with valid values."""
        location = Location(line=10, column=5)
        assert location.line == 10
        assert location.column == 5

        # Test with optional offset
        location = Location(line=10, column=5, offset=25)
        assert location.offset == 25

    def test_location_zero_values(self):
        """Test location with zero values."""
        location = Location(line=0, column=0)
        assert location.line == 0
        assert location.column == 0

    def test_location_negative_values(self):
        """Test location with negative values."""
        assert_validation_error(Location, line=-1, column=5)
        assert_validation_error(Location, line=10, column=-1)

    def test_location_equality(self):
        """Test location equality."""
        loc1 = Location(line=10, column=5)
        loc2 = Location(line=10, column=5)
        loc3 = Location(line=10, column=6)

        assert loc1 == loc2
        assert loc1 != loc3

    def test_location_tuple_conversion(self):
        """Test location to tuple conversion."""
        location = Location(line=10, column=5)
        location_tuple = location.to_tuple()

        assert location_tuple == (10, 5)

        # With offset
        location = Location(line=10, column=5, offset=25)
        location_tuple = location.to_tuple()

        assert location_tuple == (10, 5, 25)

    def test_location_from_tuple(self):
        """Test location from tuple creation."""
        location = Location.from_tuple((15, 8))
        assert location.line == 15
        assert location.column == 8
        assert location.offset is None

        # With offset
        location = Location.from_tuple((15, 8, 30))
        assert location.line == 15
        assert location.column == 8
        assert location.offset == 30

    def test_location_to_dict(self):
        """Test location to dictionary conversion."""
        location = Location(line=10, column=5, offset=25)
        location_dict = location.to_dict()

        expected = {
            'line': 10,
            'column': 5,
            'offset': 25
        }
        assert location_dict == expected

    def test_location_from_dict(self):
        """Test location from dictionary creation."""
        location_dict = {'line': 20, 'column': 10, 'offset': 50}
        location = Location.from_dict(location_dict)

        assert location.line == 20
        assert location.column == 10
        assert location.offset == 50

    def test_location_repr(self):
        """Test location string representation."""
        location = Location(line=10, column=5)
        repr_str = repr(location)

        assert 'Location' in repr_str
        assert '10' in repr_str
        assert '5' in repr_str


class TestMetrics:
    """Test cases for Metrics value object."""

    def test_metrics_creation_empty(self):
        """Test creating empty metrics."""
        metrics = Metrics()
        assert metrics.data == {}

    def test_metrics_creation_with_data(self):
        """Test creating metrics with initial data."""
        data = {
            'readability_score': 75.5,
            'word_count': 150,
            'sentence_count': 12
        }
        metrics = Metrics(data=data)
        assert metrics.data == data

    def test_metrics_set_value(self):
        """Test setting metric value."""
        metrics = Metrics()

        metrics.set('readability', 85.2)
        assert metrics.get('readability') == 85.2

    def test_metrics_get_value(self):
        """Test getting metric value."""
        metrics = Metrics()

        # Test getting existing value
        metrics.set('score', 90.0)
        assert metrics.get('score') == 90.0

        # Test getting non-existing value
        assert metrics.get('nonexistent') is None
        assert metrics.get('nonexistent', 'default') == 'default'

    def test_metrics_increment(self):
        """Test incrementing metric value."""
        metrics = Metrics()

        metrics.increment('counter')
        assert metrics.get('counter') == 1

        metrics.increment('counter', 5)
        assert metrics.get('counter') == 6

    def test_metrics_add_to_list(self):
        """Test adding to metric list."""
        metrics = Metrics()

        metrics.add_to_list('errors', 'Error 1')
        metrics.add_to_list('errors', 'Error 2')

        errors = metrics.get('errors')
        assert errors == ['Error 1', 'Error 2']

    def test_metrics_merge(self):
        """Test merging metrics."""
        metrics1 = Metrics()
        metrics1.set('score', 85.0)
        metrics1.set('count', 10)

        metrics2 = Metrics()
        metrics2.set('score', 90.0)  # Should override
        metrics2.set('time', 15.5)   # Should be added

        merged = metrics1.merge(metrics2)

        assert merged.get('score') == 90.0  # Overridden
        assert merged.get('count') == 10    # Preserved
        assert merged.get('time') == 15.5   # Added

    def test_metrics_has_key(self):
        """Test checking if metric exists."""
        metrics = Metrics()
        metrics.set('existing', 'value')

        assert metrics.has('existing')
        assert not metrics.has('nonexistent')

    def test_metrics_clear(self):
        """Test clearing all metrics."""
        metrics = Metrics()
        metrics.set('score', 85.0)
        metrics.set('count', 10)

        assert metrics.has('score')
        assert metrics.has('count')

        metrics.clear()

        assert not metrics.has('score')
        assert not metrics.has('count')
        assert metrics.data == {}

    def test_metrics_to_dict(self):
        """Test metrics to dictionary conversion."""
        data = {'score': 85.0, 'count': 10}
        metrics = Metrics(data=data)

        assert metrics.to_dict() == data

    def test_metrics_from_dict(self):
        """Test metrics from dictionary creation."""
        data = {'score': 85.0, 'count': 10}
        metrics = Metrics.from_dict(data)

        assert metrics.data == data

    def test_metrics_iteration(self):
        """Test metrics iteration."""
        data = {'score': 85.0, 'count': 10, 'name': 'test'}
        metrics = Metrics(data=data)

        keys = list(metrics.keys())
        values = list(metrics.values())
        items = list(metrics.items())

        assert set(keys) == {'score', 'count', 'name'}
        assert 85.0 in values
        assert 10 in values
        assert 'test' in values

        assert ('score', 85.0) in items
        assert ('count', 10) in items
        assert ('name', 'test') in items

    def test_metrics_length(self):
        """Test metrics length."""
        metrics = Metrics()
        assert len(metrics) == 0

        metrics.set('score', 85.0)
        assert len(metrics) == 1

        metrics.set('count', 10)
        assert len(metrics) == 2

    def test_metrics_contains(self):
        """Test metrics contains."""
        metrics = Metrics()
        metrics.set('score', 85.0)

        assert 'score' in metrics
        assert 'nonexistent' not in metrics

    def test_metrics_getitem_setitem(self):
        """Test metrics item access."""
        metrics = Metrics()

        # Set item
        metrics['score'] = 85.0
        assert metrics['score'] == 85.0

        # Get item
        assert metrics['score'] == 85.0

        # Get non-existing item
        with pytest.raises(KeyError):
            _ = metrics['nonexistent']

    def test_metrics_delitem(self):
        """Test metrics item deletion."""
        metrics = Metrics()
        metrics.set('score', 85.0)
        metrics.set('count', 10)

        assert 'score' in metrics
        assert 'count' in metrics

        del metrics['score']

        assert 'score' not in metrics
        assert 'count' in metrics

    def test_metrics_repr(self):
        """Test metrics string representation."""
        data = {'score': 85.0, 'count': 10}
        metrics = Metrics(data=data)
        repr_str = repr(metrics)

        assert 'Metrics' in repr_str
        assert 'score' in repr_str or 'count' in repr_str

    def test_metrics_equality(self):
        """Test metrics equality."""
        data1 = {'score': 85.0, 'count': 10}
        data2 = {'score': 85.0, 'count': 10}
        data3 = {'score': 85.0, 'count': 15}

        metrics1 = Metrics(data=data1)
        metrics2 = Metrics(data=data2)
        metrics3 = Metrics(data=data3)

        assert metrics1 == metrics2
        assert metrics1 != metrics3
