"""Unit tests for Finding domain entity."""

import pytest
from datetime import datetime, timezone

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from domain.entities.finding import Finding
from domain.value_objects import Confidence, Location
from tests.conftest import assert_validation_error


class TestFindingEntity:
    """Test cases for Finding entity."""

    def test_finding_creation_valid_data(self, sample_finding_data):
        """Test creating a finding with valid data."""
        finding = Finding(**sample_finding_data)

        assert finding.id == sample_finding_data['id']
        assert finding.document_id == sample_finding_data['document_id']
        assert finding.analysis_id == sample_finding_data['analysis_id']
        assert finding.severity == sample_finding_data['severity']
        assert finding.category == sample_finding_data['category']
        assert finding.description == sample_finding_data['description']
        assert isinstance(finding.location, Location)
        assert finding.suggestion == sample_finding_data['suggestion']
        assert isinstance(finding.confidence, Confidence)
        assert finding.created_at is not None

    def test_finding_creation_missing_required_fields(self):
        """Test creating a finding with missing required fields."""
        # Missing document_id
        assert_validation_error(
            Finding,
            id='finding-123',
            analysis_id='analysis-123',
            severity='medium',
            category='consistency',
            description='Test finding'
        )

        # Missing analysis_id
        assert_validation_error(
            Finding,
            id='finding-123',
            document_id='doc-123',
            severity='medium',
            category='consistency',
            description='Test finding'
        )

        # Missing description
        assert_validation_error(
            Finding,
            id='finding-123',
            document_id='doc-123',
            analysis_id='analysis-123',
            severity='medium',
            category='consistency'
        )

    def test_finding_creation_invalid_severity(self):
        """Test creating a finding with invalid severity."""
        assert_validation_error(
            Finding,
            id='finding-123',
            document_id='doc-123',
            analysis_id='analysis-123',
            severity='invalid_severity',
            category='consistency',
            description='Test finding'
        )

    def test_finding_creation_invalid_category(self):
        """Test creating a finding with invalid category."""
        assert_validation_error(
            Finding,
            id='finding-123',
            document_id='doc-123',
            analysis_id='analysis-123',
            severity='medium',
            category='',  # Empty category
            description='Test finding'
        )

    def test_finding_update_severity(self, finding_entity):
        """Test updating finding severity."""
        new_severity = 'high'
        original_updated_at = finding_entity.updated_at

        # Wait a bit to ensure timestamp difference
        import time
        time.sleep(0.001)

        finding_entity.update_severity(new_severity)

        assert finding_entity.severity == new_severity
        assert finding_entity.updated_at > original_updated_at

    def test_finding_update_description(self, finding_entity):
        """Test updating finding description."""
        new_description = 'Updated finding description'
        original_updated_at = finding_entity.updated_at

        # Wait a bit to ensure timestamp difference
        import time
        time.sleep(0.001)

        finding_entity.update_description(new_description)

        assert finding_entity.description == new_description
        assert finding_entity.updated_at > original_updated_at

    def test_finding_update_suggestion(self, finding_entity):
        """Test updating finding suggestion."""
        new_suggestion = 'Updated suggestion for fixing the issue'
        original_updated_at = finding_entity.updated_at

        # Wait a bit to ensure timestamp difference
        import time
        time.sleep(0.001)

        finding_entity.update_suggestion(new_suggestion)

        assert finding_entity.suggestion == new_suggestion
        assert finding_entity.updated_at > original_updated_at

    def test_finding_resolve(self, finding_entity):
        """Test resolving a finding."""
        resolution_note = 'Fixed by updating documentation'
        original_updated_at = finding_entity.updated_at

        # Wait a bit to ensure timestamp difference
        import time
        time.sleep(0.001)

        finding_entity.resolve(resolution_note)

        assert finding_entity.status == 'resolved'
        assert finding_entity.resolution_note == resolution_note
        assert finding_entity.resolved_at is not None
        assert finding_entity.updated_at > original_updated_at

    def test_finding_dismiss(self, finding_entity):
        """Test dismissing a finding."""
        dismissal_reason = 'False positive'
        original_updated_at = finding_entity.updated_at

        # Wait a bit to ensure timestamp difference
        import time
        time.sleep(0.001)

        finding_entity.dismiss(dismissal_reason)

        assert finding_entity.status == 'dismissed'
        assert finding_entity.dismissal_reason == dismissal_reason
        assert finding_entity.dismissed_at is not None
        assert finding_entity.updated_at > original_updated_at

    def test_finding_reopen(self, finding_entity):
        """Test reopening a resolved finding."""
        # First resolve it
        finding_entity.resolve('Fixed')
        original_updated_at = finding_entity.updated_at

        # Wait a bit to ensure timestamp difference
        import time
        time.sleep(0.001)

        # Reopen it
        finding_entity.reopen()

        assert finding_entity.status == 'open'
        assert finding_entity.resolution_note is None
        assert finding_entity.resolved_at is None
        assert finding_entity.updated_at > original_updated_at

    def test_finding_is_resolved(self, finding_entity):
        """Test checking if finding is resolved."""
        assert not finding_entity.is_resolved

        finding_entity.resolve('Fixed')
        assert finding_entity.is_resolved

    def test_finding_is_dismissed(self, finding_entity):
        """Test checking if finding is dismissed."""
        assert not finding_entity.is_dismissed

        finding_entity.dismiss('False positive')
        assert finding_entity.is_dismissed

    def test_finding_is_open(self, finding_entity):
        """Test checking if finding is open."""
        assert finding_entity.is_open  # Default state

        finding_entity.resolve('Fixed')
        assert not finding_entity.is_open

        finding_entity.reopen()
        assert finding_entity.is_open

    def test_finding_severity_score(self, finding_entity):
        """Test severity score calculation."""
        severity_scores = {
            'critical': 1.0,
            'high': 0.75,
            'medium': 0.5,
            'low': 0.25,
            'info': 0.1
        }

        for severity, expected_score in severity_scores.items():
            finding_entity.update_severity(severity)
            assert finding_entity.severity_score == expected_score

    def test_finding_priority_score(self, finding_entity):
        """Test priority score calculation."""
        # Priority score combines severity and confidence
        severity_weight = 0.7
        confidence_weight = 0.3

        expected_priority = (
            finding_entity.severity_score * severity_weight +
            finding_entity.confidence.value * confidence_weight
        )

        assert finding_entity.priority_score == expected_priority

    def test_finding_age_days(self, finding_entity):
        """Test calculating finding age in days."""
        # Mock the created_at to be older
        import time
        from unittest.mock import patch

        past_time = datetime.now(timezone.utc).timestamp() - (5 * 24 * 60 * 60)  # 5 days ago

        with patch('time.time', return_value=past_time):
            finding_entity.created_at = datetime.fromtimestamp(past_time, tz=timezone.utc)

        age_days = finding_entity.age_days
        assert age_days >= 5  # Should be at least 5 days

    def test_finding_to_dict(self, finding_entity):
        """Test converting finding to dictionary."""
        finding_dict = finding_entity.to_dict()

        assert isinstance(finding_dict, dict)
        assert 'id' in finding_dict
        assert 'document_id' in finding_dict
        assert 'severity' in finding_dict
        assert 'category' in finding_dict
        assert 'description' in finding_dict
        assert 'created_at' in finding_dict

    def test_finding_from_dict(self, sample_finding_data):
        """Test creating finding from dictionary."""
        finding = Finding.from_dict(sample_finding_data)

        assert isinstance(finding, Finding)
        assert finding.id == sample_finding_data['id']
        assert finding.document_id == sample_finding_data['document_id']

    def test_finding_equality(self, finding_entity, sample_finding_data):
        """Test finding equality comparison."""
        finding2 = Finding(**sample_finding_data)

        assert finding_entity == finding2
        assert finding_entity.id == finding2.id

    def test_finding_hash(self, finding_entity):
        """Test finding hash for use in sets/dicts."""
        finding_hash = hash(finding_entity)

        assert isinstance(finding_hash, int)
        assert finding_hash == hash(finding_entity.id)

    def test_finding_repr(self, finding_entity):
        """Test finding string representation."""
        repr_str = repr(finding_entity)

        assert 'Finding' in repr_str
        assert finding_entity.id in repr_str
        assert finding_entity.severity in repr_str

    def test_finding_validation_confidence_range(self):
        """Test validation for confidence range."""
        # Valid confidence
        finding = Finding(
            id='finding-123',
            document_id='doc-123',
            analysis_id='analysis-123',
            severity='medium',
            category='consistency',
            description='Test finding',
            confidence=Confidence(value=0.8)
        )
        assert finding.confidence.value == 0.8

        # Confidence too high
        assert_validation_error(
            Finding,
            id='finding-123',
            document_id='doc-123',
            analysis_id='analysis-123',
            severity='medium',
            category='consistency',
            description='Test finding',
            confidence=Confidence(value=1.5)
        )

    def test_finding_validation_location_positive_values(self):
        """Test validation for location with positive values."""
        # Valid location
        finding = Finding(
            id='finding-123',
            document_id='doc-123',
            analysis_id='analysis-123',
            severity='medium',
            category='consistency',
            description='Test finding',
            location=Location(line=10, column=5)
        )
        assert finding.location.line == 10
        assert finding.location.column == 5

        # Negative line number
        assert_validation_error(
            Finding,
            id='finding-123',
            document_id='doc-123',
            analysis_id='analysis-123',
            severity='medium',
            category='consistency',
            description='Test finding',
            location=Location(line=-1, column=5)
        )

    def test_finding_status_transitions(self, finding_entity):
        """Test valid status transitions."""
        # open -> resolved
        finding_entity.resolve('Fixed')
        assert finding_entity.status == 'resolved'

        # resolved -> open
        finding_entity.reopen()
        assert finding_entity.status == 'open'

        # open -> dismissed
        finding_entity.dismiss('False positive')
        assert finding_entity.status == 'dismissed'

    def test_finding_invalid_status_transitions(self, finding_entity):
        """Test invalid status transitions."""
        # Can't resolve already resolved finding
        finding_entity.resolve('Fixed')

        # Should not raise error, but status should remain resolved
        finding_entity.resolve('Fixed again')
        assert finding_entity.status == 'resolved'

    def test_finding_timestamp_behavior(self):
        """Test timestamp behavior."""
        before_creation = datetime.now(timezone.utc)

        finding = Finding(
            id='finding-123',
            document_id='doc-123',
            analysis_id='analysis-123',
            severity='medium',
            category='consistency',
            description='Test finding'
        )

        after_creation = datetime.now(timezone.utc)

        assert before_creation <= finding.created_at <= after_creation
        assert finding.updated_at == finding.created_at  # Equal at creation

        # Test update preserves creation time
        original_created_at = finding.created_at
        finding.update_description('Updated description')

        assert finding.created_at == original_created_at
        assert finding.updated_at > original_created_at
