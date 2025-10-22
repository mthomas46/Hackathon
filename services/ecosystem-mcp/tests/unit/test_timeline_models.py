"""
Unit tests for timeline Pydantic models.

Tests model validation, serialization, and business logic.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from src.models.timeline import (
    Timeline,
    TimelineCreate,
    TimelineUpdate,
    TimePeriod,
    TimePeriodCreate,
    DocumentPlacement,
    DocumentPlacementCreate,
    TemporalConfidence,
    PeriodStrategy,
    PlacementSource,
    ConfidenceMetadata,
    TimelineMetadata,
    PeriodMetadata,
    PlacementMetadata,
)


class TestTemporalConfidence:
    """Test TemporalConfidence enum."""
    
    def test_confidence_levels(self):
        """Test all confidence levels are defined."""
        assert TemporalConfidence.HIGH.value == "HIGH"
        assert TemporalConfidence.MEDIUM.value == "MEDIUM"
        assert TemporalConfidence.LOW.value == "LOW"
        assert TemporalConfidence.NONE.value == "NONE"


class TestPeriodStrategy:
    """Test PeriodStrategy enum."""
    
    def test_strategies(self):
        """Test all strategies are defined."""
        assert PeriodStrategy.MONTHLY.value == "monthly"
        assert PeriodStrategy.QUARTERLY.value == "quarterly"
        assert PeriodStrategy.ADAPTIVE.value == "adaptive"


class TestPlacementSource:
    """Test PlacementSource enum."""
    
    def test_sources(self):
        """Test all sources are defined."""
        assert PlacementSource.GIT_COMMIT.value == "git_commit"
        assert PlacementSource.CREATED_AT.value == "created_at"
        assert PlacementSource.MANUAL.value == "manual"


class TestConfidenceMetadata:
    """Test ConfidenceMetadata model."""
    
    def test_valid_confidence_metadata(self):
        """Test creating valid confidence metadata."""
        metadata = ConfidenceMetadata(
            total_documents=100,
            git_history_documents=95,
            snapshot_documents=5,
            git_percentage=95.0,
            can_show_evolution=True,
            can_detect_drift=True,
            can_show_timeline=True,
            can_compare_periods=True,
            fallback_strategy="minimal_fallback",
            warnings=[],
            calculated_at=datetime.utcnow()
        )
        
        assert metadata.total_documents == 100
        assert metadata.git_percentage == 95.0
        assert metadata.can_show_evolution is True
    
    def test_invalid_git_percentage(self):
        """Test validation of git percentage."""
        with pytest.raises(ValueError):
            ConfidenceMetadata(
                total_documents=100,
                git_history_documents=95,
                snapshot_documents=5,
                git_percentage=150.0,  # Invalid: > 100
                can_show_evolution=True,
                can_detect_drift=True,
                can_show_timeline=True,
                can_compare_periods=True,
                fallback_strategy="minimal_fallback"
            )


class TestTimelineCreate:
    """Test TimelineCreate model."""
    
    def test_valid_timeline_create(self):
        """Test creating valid timeline."""
        start = datetime(2025, 1, 1)
        end = datetime(2025, 12, 31)
        
        timeline = TimelineCreate(
            name="Test Timeline",
            description="Test description",
            service_name="test-service",
            repo_path="/path/to/repo",
            start_date=start,
            end_date=end,
            period_strategy=PeriodStrategy.MONTHLY
        )
        
        assert timeline.name == "Test Timeline"
        assert timeline.service_name == "test-service"
        assert timeline.start_date == start
        assert timeline.end_date == end
    
    def test_invalid_date_range(self):
        """Test validation of date range."""
        start = datetime(2025, 12, 31)
        end = datetime(2025, 1, 1)  # Before start!
        
        with pytest.raises(ValueError, match="end_date must be after start_date"):
            TimelineCreate(
                name="Test Timeline",
                service_name="test-service",
                repo_path="/path/to/repo",
                start_date=start,
                end_date=end
            )
    
    def test_empty_name(self):
        """Test validation of empty name."""
        with pytest.raises(ValueError):
            TimelineCreate(
                name="",  # Empty name
                service_name="test-service",
                repo_path="/path/to/repo",
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2025, 12, 31)
            )


class TestTimeline:
    """Test Timeline model."""
    
    def test_full_timeline_model(self):
        """Test complete timeline with all fields."""
        timeline_id = uuid4()
        start = datetime(2025, 1, 1)
        end = datetime(2025, 12, 31)
        
        confidence = ConfidenceMetadata(
            total_documents=100,
            git_history_documents=95,
            snapshot_documents=5,
            git_percentage=95.0,
            can_show_evolution=True,
            can_detect_drift=True,
            can_show_timeline=True,
            can_compare_periods=True,
            fallback_strategy="minimal_fallback"
        )
        
        timeline = Timeline(
            id=timeline_id,
            name="Test Timeline",
            description="Test description",
            service_name="test-service",
            repo_path="/path/to/repo",
            start_date=start,
            end_date=end,
            confidence_level=TemporalConfidence.HIGH,
            confidence_metadata=confidence,
            period_strategy=PeriodStrategy.MONTHLY,
            created_by="test_user",
            metadata=TimelineMetadata(
                total_commits=100,
                total_documents=95,
                primary_authors=["user1", "user2"],
                tags=["test"]
            )
        )
        
        assert timeline.id == timeline_id
        assert timeline.confidence_level == TemporalConfidence.HIGH
        assert timeline.period_strategy == PeriodStrategy.MONTHLY
    
    def test_timeline_serialization(self):
        """Test timeline can be serialized to dict."""
        timeline = Timeline(
            name="Test Timeline",
            service_name="test-service",
            repo_path="/path/to/repo",
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 12, 31),
            confidence_level=TemporalConfidence.HIGH,
            confidence_metadata=ConfidenceMetadata(
                total_documents=100,
                git_history_documents=95,
                snapshot_documents=5,
                git_percentage=95.0,
                can_show_evolution=True,
                can_detect_drift=True,
                can_show_timeline=True,
                can_compare_periods=True,
                fallback_strategy="minimal_fallback"
            )
        )
        
        data = timeline.model_dump()
        assert isinstance(data, dict)
        assert data["name"] == "Test Timeline"
        assert data["service_name"] == "test-service"


class TestTimePeriod:
    """Test TimePeriod model."""
    
    def test_valid_period(self):
        """Test creating valid time period."""
        timeline_id = uuid4()
        period_id = uuid4()
        start = datetime(2025, 1, 1)
        end = datetime(2025, 1, 31, 23, 59, 59)
        
        period = TimePeriod(
            id=period_id,
            timeline_id=timeline_id,
            name="January 2025",
            description="First month of 2025",
            start_date=start,
            end_date=end,
            sequence_number=1,
            document_count=42,
            commit_count=156
        )
        
        assert period.id == period_id
        assert period.timeline_id == timeline_id
        assert period.name == "January 2025"
        assert period.sequence_number == 1
    
    def test_invalid_sequence_number(self):
        """Test validation of sequence number."""
        with pytest.raises(ValueError):
            TimePeriod(
                timeline_id=uuid4(),
                name="Test Period",
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2025, 1, 31),
                sequence_number=0  # Must be >= 1
            )
    
    def test_invalid_date_range(self):
        """Test validation of period date range."""
        with pytest.raises(ValueError, match="end_date must be after start_date"):
            TimePeriod(
                timeline_id=uuid4(),
                name="Test Period",
                start_date=datetime(2025, 1, 31),
                end_date=datetime(2025, 1, 1),  # Before start!
                sequence_number=1
            )
    
    def test_negative_counts(self):
        """Test validation of negative counts."""
        with pytest.raises(ValueError):
            TimePeriod(
                timeline_id=uuid4(),
                name="Test Period",
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2025, 1, 31),
                sequence_number=1,
                document_count=-1  # Invalid
            )


class TestDocumentPlacement:
    """Test DocumentPlacement model."""
    
    def test_valid_placement(self):
        """Test creating valid document placement."""
        placement_id = uuid4()
        period_id = uuid4()
        document_id = uuid4()
        placement_date = datetime(2025, 1, 15, 10, 30)
        
        placement = DocumentPlacement(
            id=placement_id,
            period_id=period_id,
            document_id=document_id,
            placement_date=placement_date,
            placement_source=PlacementSource.GIT_COMMIT,
            git_commit_sha="a" * 40,
            relevance_score=1.0
        )
        
        assert placement.id == placement_id
        assert placement.period_id == period_id
        assert placement.document_id == document_id
        assert placement.placement_source == PlacementSource.GIT_COMMIT
    
    def test_invalid_git_sha_length(self):
        """Test validation of git commit SHA."""
        with pytest.raises(ValueError):
            DocumentPlacement(
                period_id=uuid4(),
                document_id=uuid4(),
                placement_date=datetime.utcnow(),
                placement_source=PlacementSource.GIT_COMMIT,
                git_commit_sha="short"  # Must be 40 chars
            )
    
    def test_invalid_relevance_score(self):
        """Test validation of relevance score range."""
        with pytest.raises(ValueError):
            DocumentPlacement(
                period_id=uuid4(),
                document_id=uuid4(),
                placement_date=datetime.utcnow(),
                placement_source=PlacementSource.CREATED_AT,
                relevance_score=1.5  # Must be <= 1.0
            )
        
        with pytest.raises(ValueError):
            DocumentPlacement(
                period_id=uuid4(),
                document_id=uuid4(),
                placement_date=datetime.utcnow(),
                placement_source=PlacementSource.CREATED_AT,
                relevance_score=-0.1  # Must be >= 0.0
            )
    
    def test_placement_with_metadata(self):
        """Test placement with metadata."""
        placement = DocumentPlacement(
            period_id=uuid4(),
            document_id=uuid4(),
            placement_date=datetime.utcnow(),
            placement_source=PlacementSource.GIT_COMMIT,
            git_commit_sha="a" * 40,
            metadata=PlacementMetadata(
                commit_message="Initial commit",
                author="test_user",
                tags=["important"]
            )
        )
        
        assert placement.metadata.commit_message == "Initial commit"
        assert placement.metadata.author == "test_user"
        assert "important" in placement.metadata.tags


class TestTimelineUpdate:
    """Test TimelineUpdate model."""
    
    def test_partial_update(self):
        """Test partial update with only some fields."""
        update = TimelineUpdate(
            name="Updated Name",
            description="Updated description"
        )
        
        assert update.name == "Updated Name"
        assert update.description == "Updated description"
        assert update.end_date is None  # Not set
    
    def test_empty_update(self):
        """Test update with no fields set."""
        update = TimelineUpdate()
        
        # Should be valid but all fields None
        assert update.name is None
        assert update.description is None
        assert update.end_date is None

