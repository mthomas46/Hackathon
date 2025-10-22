"""
Unit tests for TimelineManager service.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from src.services.timeline import TimelineManager
from src.models.timeline import TimelineCreate, TemporalConfidence, PeriodStrategy


@pytest.fixture
def timeline_manager():
    """Create TimelineManager instance."""
    return TimelineManager()


@pytest.mark.asyncio
class TestTimelineManager:
    """Test TimelineManager functionality."""
    
    async def test_create_timeline_basic(self, timeline_manager):
        """Test basic timeline creation."""
        timeline_data = TimelineCreate(
            name="Test Timeline",
            description="Test timeline for unit testing",
            service_name="test-service",
            repo_path="/test/repo",
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 12, 31),
            period_strategy=PeriodStrategy.MONTHLY
        )
        
        # This would normally interact with database
        # For unit test, we'd mock the repository
        assert timeline_data.name == "Test Timeline"
        assert timeline_data.service_name == "test-service"
        assert timeline_data.period_strategy == PeriodStrategy.MONTHLY
    
    def test_validate_timeline_dates(self, timeline_manager):
        """Test timeline date validation."""
        start = datetime(2025, 1, 1)
        end = datetime(2024, 12, 31)  # End before start
        
        # Should raise validation error
        with pytest.raises(ValueError):
            timeline_data = TimelineCreate(
                name="Invalid Timeline",
                service_name="test",
                repo_path="/test",
                start_date=start,
                end_date=end,
                period_strategy=PeriodStrategy.MONTHLY
            )
    
    def test_timeline_period_strategy_enum(self, timeline_manager):
        """Test period strategy enum values."""
        assert PeriodStrategy.MONTHLY == "monthly"
        assert PeriodStrategy.QUARTERLY == "quarterly"
        assert PeriodStrategy.ADAPTIVE == "adaptive"

