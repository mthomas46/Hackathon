"""Unit tests for Analysis domain entity."""

import pytest
from datetime import datetime, timezone

from ...domain.entities.analysis import Analysis
from ...domain.value_objects import AnalysisType
from ..conftest import assert_validation_error


class TestAnalysisEntity:
    """Test cases for Analysis entity."""

    def test_analysis_creation_valid_data(self, sample_analysis_data):
        """Test creating an analysis with valid data."""
        analysis = Analysis(**sample_analysis_data)

        assert analysis.id == sample_analysis_data['id']
        assert analysis.document_id == sample_analysis_data['document_id']
        assert analysis.analysis_type == sample_analysis_data['analysis_type']
        assert analysis.status == sample_analysis_data['status']
        assert analysis.results == sample_analysis_data['results']
        assert analysis.metadata == sample_analysis_data['metadata']
        assert analysis.created_at is not None
        assert analysis.completed_at is None  # Not completed yet

    def test_analysis_creation_missing_required_fields(self):
        """Test creating an analysis with missing required fields."""
        # Missing document_id
        assert_validation_error(
            Analysis,
            id='analysis-123',
            analysis_type=AnalysisType.CONSISTENCY,
            status='pending'
        )

        # Missing analysis_type
        assert_validation_error(
            Analysis,
            id='analysis-123',
            document_id='doc-123',
            status='pending'
        )

    def test_analysis_creation_invalid_status(self):
        """Test creating an analysis with invalid status."""
        assert_validation_error(
            Analysis,
            id='analysis-123',
            document_id='doc-123',
            analysis_type=AnalysisType.CONSISTENCY,
            status='invalid_status'
        )

    def test_analysis_start_execution(self, analysis_entity):
        """Test starting analysis execution."""
        original_status = analysis_entity.status

        analysis_entity.start_execution()

        assert analysis_entity.status == 'running'
        assert analysis_entity.started_at is not None
        assert analysis_entity.started_at >= analysis_entity.created_at

    def test_analysis_complete_execution(self, analysis_entity):
        """Test completing analysis execution."""
        # Start execution first
        analysis_entity.start_execution()
        start_time = analysis_entity.started_at

        # Complete execution
        results = {'score': 0.95, 'issues': ['Issue 1', 'Issue 2']}
        analysis_entity.complete_execution(results)

        assert analysis_entity.status == 'completed'
        assert analysis_entity.completed_at is not None
        assert analysis_entity.completed_at >= start_time
        assert analysis_entity.results == results

    def test_analysis_fail_execution(self, analysis_entity):
        """Test failing analysis execution."""
        # Start execution first
        analysis_entity.start_execution()

        # Fail execution
        error_message = "Analysis failed due to processing error"
        analysis_entity.fail_execution(error_message)

        assert analysis_entity.status == 'failed'
        assert analysis_entity.completed_at is not None
        assert analysis_entity.error_message == error_message

    def test_analysis_cancel_execution(self, analysis_entity):
        """Test canceling analysis execution."""
        # Start execution first
        analysis_entity.start_execution()

        # Cancel execution
        analysis_entity.cancel_execution()

        assert analysis_entity.status == 'cancelled'
        assert analysis_entity.completed_at is not None

    def test_analysis_update_progress(self, analysis_entity):
        """Test updating analysis progress."""
        # Start execution first
        analysis_entity.start_execution()

        # Update progress
        progress = 75.5
        message = "Processing semantic analysis"
        analysis_entity.update_progress(progress, message)

        assert analysis_entity.progress == progress
        assert analysis_entity.status_message == message

    def test_analysis_duration_calculation(self, analysis_entity):
        """Test analysis duration calculation."""
        # Start and complete execution
        analysis_entity.start_execution()

        # Simulate time passing
        import time
        time.sleep(0.01)

        analysis_entity.complete_execution({})

        duration = analysis_entity.duration
        assert duration is not None
        assert duration > 0

    def test_analysis_duration_not_started(self, analysis_entity):
        """Test duration calculation when analysis hasn't started."""
        duration = analysis_entity.duration
        assert duration is None

    def test_analysis_duration_not_completed(self, analysis_entity):
        """Test duration calculation when analysis hasn't completed."""
        analysis_entity.start_execution()

        duration = analysis_entity.duration
        assert duration is None

    def test_analysis_is_running(self, analysis_entity):
        """Test checking if analysis is running."""
        assert not analysis_entity.is_running

        analysis_entity.start_execution()
        assert analysis_entity.is_running

        analysis_entity.complete_execution({})
        assert not analysis_entity.is_running

    def test_analysis_is_completed(self, analysis_entity):
        """Test checking if analysis is completed."""
        assert not analysis_entity.is_completed

        analysis_entity.start_execution()
        assert not analysis_entity.is_completed

        analysis_entity.complete_execution({})
        assert analysis_entity.is_completed

    def test_analysis_is_failed(self, analysis_entity):
        """Test checking if analysis is failed."""
        assert not analysis_entity.is_failed

        analysis_entity.start_execution()
        assert not analysis_entity.is_failed

        analysis_entity.fail_execution("Error")
        assert analysis_entity.is_failed

    def test_analysis_reset_execution(self, analysis_entity):
        """Test resetting analysis execution."""
        # Start and complete
        analysis_entity.start_execution()
        analysis_entity.complete_execution({'result': 'done'})

        # Reset
        analysis_entity.reset_execution()

        assert analysis_entity.status == 'pending'
        assert analysis_entity.started_at is None
        assert analysis_entity.completed_at is None
        assert analysis_entity.progress == 0.0
        assert analysis_entity.error_message is None
        assert analysis_entity.results == {}

    def test_analysis_to_dict(self, analysis_entity):
        """Test converting analysis to dictionary."""
        analysis_dict = analysis_entity.to_dict()

        assert isinstance(analysis_dict, dict)
        assert 'id' in analysis_dict
        assert 'document_id' in analysis_dict
        assert 'analysis_type' in analysis_dict
        assert 'status' in analysis_dict
        assert 'created_at' in analysis_dict

    def test_analysis_from_dict(self, sample_analysis_data):
        """Test creating analysis from dictionary."""
        analysis = Analysis.from_dict(sample_analysis_data)

        assert isinstance(analysis, Analysis)
        assert analysis.id == sample_analysis_data['id']
        assert analysis.document_id == sample_analysis_data['document_id']

    def test_analysis_equality(self, analysis_entity, sample_analysis_data):
        """Test analysis equality comparison."""
        analysis2 = Analysis(**sample_analysis_data)

        assert analysis_entity == analysis2
        assert analysis_entity.id == analysis2.id

    def test_analysis_hash(self, analysis_entity):
        """Test analysis hash for use in sets/dicts."""
        analysis_hash = hash(analysis_entity)

        assert isinstance(analysis_hash, int)
        assert analysis_hash == hash(analysis_entity.id)

    def test_analysis_repr(self, analysis_entity):
        """Test analysis string representation."""
        repr_str = repr(analysis_entity)

        assert 'Analysis' in repr_str
        assert analysis_entity.id in repr_str
        assert analysis_entity.document_id in repr_str

    def test_analysis_validation_analysis_type_enum(self):
        """Test validation for analysis type enum."""
        # Valid enum value
        analysis = Analysis(
            id='analysis-123',
            document_id='doc-123',
            analysis_type=AnalysisType.CONSISTENCY,
            status='pending'
        )
        assert analysis.analysis_type == AnalysisType.CONSISTENCY

        # Invalid value
        assert_validation_error(
            Analysis,
            id='analysis-123',
            document_id='doc-123',
            analysis_type='invalid_type',
            status='pending'
        )

    def test_analysis_validation_status_values(self):
        """Test validation for status values."""
        valid_statuses = ['pending', 'running', 'completed', 'failed', 'cancelled']

        for status in valid_statuses:
            analysis = Analysis(
                id='analysis-123',
                document_id='doc-123',
                analysis_type=AnalysisType.CONSISTENCY,
                status=status
            )
            assert analysis.status == status

    def test_analysis_validation_progress_range(self):
        """Test validation for progress range."""
        # Valid progress
        analysis = Analysis(
            id='analysis-123',
            document_id='doc-123',
            analysis_type=AnalysisType.CONSISTENCY,
            status='running',
            progress=75.5
        )
        assert analysis.progress == 75.5

        # Progress too high
        assert_validation_error(
            Analysis,
            id='analysis-123',
            document_id='doc-123',
            analysis_type=AnalysisType.CONSISTENCY,
            status='running',
            progress=150.0
        )

        # Progress negative
        assert_validation_error(
            Analysis,
            id='analysis-123',
            document_id='doc-123',
            analysis_type=AnalysisType.CONSISTENCY,
            status='running',
            progress=-10.0
        )

    def test_analysis_state_transitions(self, analysis_entity):
        """Test valid state transitions."""
        # pending -> running
        analysis_entity.start_execution()
        assert analysis_entity.status == 'running'

        # running -> completed
        analysis_entity.complete_execution({})
        assert analysis_entity.status == 'completed'

        # completed -> pending (reset)
        analysis_entity.reset_execution()
        assert analysis_entity.status == 'pending'

        # pending -> running -> failed
        analysis_entity.start_execution()
        assert analysis_entity.status == 'running'

        analysis_entity.fail_execution("Error")
        assert analysis_entity.status == 'failed'

    def test_analysis_invalid_state_transitions(self, analysis_entity):
        """Test invalid state transitions are handled gracefully."""
        # Can't complete without starting
        with pytest.raises(ValueError):
            analysis_entity.complete_execution({})

        # Can't fail without starting
        with pytest.raises(ValueError):
            analysis_entity.fail_execution("Error")

        # Can't cancel without starting
        with pytest.raises(ValueError):
            analysis_entity.cancel_execution()

        # Can't update progress without starting
        with pytest.raises(ValueError):
            analysis_entity.update_progress(50.0, "Processing")
