"""Tests for quality service functions."""

import pytest
from datetime import datetime, timedelta
from domain.services.quality_service import (
    _analyze_metadata_flags,
    _extract_metadata_fields,
    _calculate_updated_stale_days,
    _check_recently_viewed,
    _analyze_basic_metadata,
    _analyze_label_quality,
)


class TestExtractMetadataFields:
    """Test metadata field extraction."""

    def test_extract_metadata_fields_complete(self):
        """Test extracting all metadata fields."""
        metadata = {
            "views": 100,
            "updated_at": "2024-01-01T10:00:00",
            "last_viewed": "2024-01-15T10:00:00",
            "owner": "test_user",
            "labels": ["important", "urgent"]
        }
        result = _extract_metadata_fields(metadata)

        assert result["views"] == 100
        assert result["updated_at"] == "2024-01-01T10:00:00"
        assert result["last_viewed"] == "2024-01-15T10:00:00"
        assert result["owner"] == "test_user"
        assert result["labels"] == ["important", "urgent"]

    def test_extract_metadata_fields_missing(self):
        """Test extracting metadata with missing fields."""
        metadata = {"views": 50}
        result = _extract_metadata_fields(metadata)

        assert result["views"] == 50
        assert result["updated_at"] is None
        assert result["last_viewed"] is None
        assert result["owner"] is None
        assert result["labels"] is None


class TestCalculateUpdatedStaleDays:
    """Test updated stale days calculation."""

    def test_calculate_updated_stale_days_no_updated_at(self):
        """Test calculation with no updated_at."""
        now = datetime.now()
        result = _calculate_updated_stale_days(None, now, 30)
        assert result == 30

    def test_calculate_updated_stale_days_recent_update(self):
        """Test calculation with recent update."""
        now = datetime.now()
        recent_update = (now - timedelta(days=5)).isoformat()
        result = _calculate_updated_stale_days(recent_update, now, 30)
        assert result == 5

    def test_calculate_updated_stale_days_invalid_format(self):
        """Test calculation with invalid datetime format."""
        now = datetime.now()
        result = _calculate_updated_stale_days("invalid-date", now, 30)
        assert result == 30


class TestCheckRecentlyViewed:
    """Test recently viewed check."""

    def test_check_recently_viewed_not_stale(self):
        """Test when document is not stale."""
        now = datetime.now()
        result = _check_recently_viewed("2024-01-01T10:00:00", 100, now)
        assert result is False

    def test_check_recently_viewed_stale_recent_view(self):
        """Test when document is stale but recently viewed."""
        now = datetime.now()
        recent_view = (now - timedelta(days=7)).isoformat()
        result = _check_recently_viewed(recent_view, 200, now)
        assert result is True

    def test_check_recently_viewed_stale_old_view(self):
        """Test when document is stale and not recently viewed."""
        now = datetime.now()
        old_view = (now - timedelta(days=60)).isoformat()
        result = _check_recently_viewed(old_view, 200, now)
        assert result is False

    def test_check_recently_viewed_no_last_viewed(self):
        """Test when no last_viewed is provided."""
        now = datetime.now()
        result = _check_recently_viewed(None, 200, now)
        assert result is False


class TestAnalyzeBasicMetadata:
    """Test basic metadata analysis."""

    def test_analyze_basic_metadata_low_views(self):
        """Test low views detection."""
        flags = _analyze_basic_metadata(5, "owner", 10)
        assert "low_views" in flags

    def test_analyze_basic_metadata_missing_owner(self):
        """Test missing owner detection."""
        flags = _analyze_basic_metadata(100, None, 10)
        assert "missing_owner" in flags

    def test_analyze_basic_metadata_normal(self):
        """Test normal metadata."""
        flags = _analyze_basic_metadata(100, "owner", 10)
        assert len(flags) == 0


class TestAnalyzeLabelQuality:
    """Test label quality analysis."""

    def test_analyze_label_quality_generic(self):
        """Test generic label detection."""
        flags = _analyze_label_quality(["documentation", "important"])
        assert "generic_labels" in flags

    def test_analyze_label_quality_good(self):
        """Test good label quality."""
        flags = _analyze_label_quality(["backend", "api", "urgent"])
        assert len(flags) == 0

    def test_analyze_label_quality_not_list(self):
        """Test non-list labels."""
        flags = _analyze_label_quality("not_a_list")
        assert len(flags) == 0


class TestAnalyzeMetadataFlags:
    """Test comprehensive metadata flags analysis."""

    def test_analyze_metadata_flags_complete(self):
        """Test complete metadata analysis."""
        now = datetime.now()
        metadata = {
            "views": 5,  # Low views
            "updated_at": (now - timedelta(days=10)).isoformat(),
            "last_viewed": (now - timedelta(days=200)).isoformat(),  # Old view
            "owner": None,  # Missing owner
            "labels": ["documentation", "misc"]  # Generic labels
        }

        flags = _analyze_metadata_flags(metadata, 10, now, 100)

        assert "low_views" in flags
        assert "missing_owner" in flags
        assert "generic_labels" in flags

    def test_analyze_metadata_flags_recently_viewed(self):
        """Test recently viewed flag despite staleness."""
        now = datetime.now()
        metadata = {
            "views": 100,
            "updated_at": (now - timedelta(days=200)).isoformat(),
            "last_viewed": (now - timedelta(days=7)).isoformat(),  # Recent view
            "owner": "user",
            "labels": ["good", "label"]
        }

        flags = _analyze_metadata_flags(metadata, 10, now, 250)

        assert "recently_viewed" in flags
        assert "low_views" not in flags
        assert "missing_owner" not in flags
        assert "generic_labels" not in flags

    def test_analyze_metadata_flags_empty_metadata(self):
        """Test with empty metadata."""
        now = datetime.now()
        metadata = {}

        flags = _analyze_metadata_flags(metadata, 10, now, 30)

        # Should not crash and return minimal flags
        assert isinstance(flags, list)
