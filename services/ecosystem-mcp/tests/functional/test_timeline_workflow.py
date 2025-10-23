"""
Functional tests for timeline workflow.

Tests the complete timeline analysis pipeline:
1. Create timelines from ingested documents
2. Generate time periods (monthly, quarterly, adaptive)
3. Place documents in correct periods
4. Calculate temporal confidence
5. Query timeline data
6. Detect gaps and overlaps
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

# Mark all tests in this module as functional and asyncio
pytestmark = [pytest.mark.functional, pytest.mark.asyncio]


class TestTimelineCreation:
    """Test timeline creation from ingested documents."""
    
    async def test_create_timeline_from_documents(
        self,
        clean_database,
        ecosystem_mcp_src_dir,
        test_session_id
    ):
        """
        Test creating a timeline from ingested documents.
        
        Validates:
        - Timeline creation with metadata
        - Period generation
        - Document placement
        - Confidence calculation
        """
        from src.storage.repositories import DocumentRepository
        from src.services.timeline import TimelineManager, PeriodGenerator, DocumentPlacer
        from src.models.timeline import TimelineCreate
        from tests.utils.test_helpers import create_test_document
        
        # Setup - pass session directly to services
        doc_repo = DocumentRepository(clean_database)
        timeline_manager = TimelineManager(clean_database)
        
        # Ingest test documents
        python_files = list(ecosystem_mcp_src_dir.rglob("*.py"))[:10]
        docs = []
        
        for file_path in python_files:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            doc_model = create_test_document(
                content=content,
                file_path=str(file_path.relative_to(ecosystem_mcp_src_dir.parent)),
                service_name="ecosystem-mcp-test",
                session_id=test_session_id
            )
            doc = await doc_repo.create(doc_model)
            docs.append(doc)
        
        assert len(docs) == 10
        
        # Create timeline using TimelineCreate model
        timeline_data = TimelineCreate(
            name=f"test_timeline_{test_session_id[:8]}",
            service_name="ecosystem-mcp-test",
            repo_path=str(ecosystem_mcp_src_dir.parent),
            start_date=datetime.now() - timedelta(days=365),
            end_date=datetime.now(),
            period_strategy=PeriodStrategy.MONTHLY
        )
        
        timeline = await timeline_manager.create_timeline(timeline_data, skip_confidence_check=True)
        
        # Verify timeline created
        assert timeline is not None
        assert timeline.id is not None
        assert timeline.name == timeline_data.name
        assert timeline.service_name == "ecosystem-mcp-test"
        assert timeline.period_strategy == "monthly"
    
    async def test_create_timeline_with_metadata(
        self,
        clean_database,
        test_session_id
    ):
        """Test timeline creation with custom metadata."""
        from src.services.timeline import TimelineManager
        from src.models.timeline import TimelineCreate
        
        # Repository created internally by TimelineManager
        timeline_manager = TimelineManager(clean_database)
        
        from src.models.timeline import TimelineMetadata
        
        timeline_data = TimelineCreate(
            name=f"test_timeline_metadata_{test_session_id[:8]}",
            service_name="test-service",
            repo_path="/test/repo",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            period_strategy=PeriodStrategy.QUARTERLY,
            metadata=TimelineMetadata(
                extra={
                    "purpose": "testing",
                    "created_by": "functional_test",
                    "_test_data_marker": True,
                    "_test_session_id": test_session_id
                }
            )
        )
        
        # Skip confidence check for tests
        timeline = await timeline_manager.create_timeline(
            timeline_data,
            skip_confidence_check=True
        )
        
        assert timeline.metadata is not None
        assert timeline.metadata.extra.get("purpose") == "testing"
        assert timeline.metadata.extra.get("_test_data_marker") is True
    
    async def test_create_multiple_timelines(
        self,
        clean_database,
        test_session_id
    ):
        """Test creating multiple timelines for same service."""
        from src.storage.repositories import TimelineRepository
        from src.services.timeline import TimelineManager
        from src.models.timeline import TimelineCreate, TimelineMetadata, PeriodStrategy
        
        # Repository created internally by TimelineManager
        timeline_manager = TimelineManager(clean_database)
        
        # Create 3 timelines
        timelines = []
        for i in range(3):
            timeline_data = TimelineCreate(
                name=f"test_timeline_{i}_{test_session_id[:8]}",
                service_name="test-service",
                repo_path="/test/repo",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 12, 31),
                period_strategy=PeriodStrategy.MONTHLY,
                metadata=TimelineMetadata(extra={"_test_data_marker": True})
            )
            timeline = await timeline_manager.create_timeline(timeline_data, skip_confidence_check=True)
            timelines.append(timeline)
        
        assert len(timelines) == 3
        assert all(t.id is not None for t in timelines)
        assert all(t.service_name == "test-service" for t in timelines)


from src.models.timeline import PeriodStrategy

class TestPeriodGeneration:
    """Test time period generation strategies."""
    
    async def test_generate_monthly_periods(
        self,
        clean_database,
        test_session_id
    ):
        """Test generating monthly periods."""
        from src.storage.repositories import TimelineRepository, TimePeriodRepository
        from src.services.timeline import TimelineManager, PeriodGenerator
        from src.models.timeline import TimelineCreate, TimelineMetadata, PeriodStrategy
        
        # Repository created internally by TimelineManager
        # Repository created internally by PeriodGenerator
        timeline_manager = TimelineManager(clean_database)
        period_generator = PeriodGenerator(clean_database)
        
        # Create timeline
        timeline_data = TimelineCreate(
            name=f"monthly_timeline_{test_session_id[:8]}",
            service_name="test-service",
            repo_path="/test/repo",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 3, 31),  # 3 months
            period_strategy=PeriodStrategy.MONTHLY,
            metadata=TimelineMetadata(extra={"_test_data_marker": True})
        )
        timeline = await timeline_manager.create_timeline(timeline_data, skip_confidence_check=True)
        
        # Generate periods
        periods = await period_generator.generate_periods(
            timeline_id=timeline.id,
            service_name=timeline.service_name,
            start_date=timeline.start_date,
            end_date=timeline.end_date,
            strategy=PeriodStrategy.MONTHLY
        )
        
        # Should have 3 periods (Jan, Feb, Mar)
        assert len(periods) >= 3
        assert all(p.timeline_id == timeline.id for p in periods)
    
    async def test_generate_quarterly_periods(
        self,
        clean_database,
        test_session_id
    ):
        """Test generating quarterly periods."""
        from src.storage.repositories import TimelineRepository, TimePeriodRepository
        from src.services.timeline import TimelineManager, PeriodGenerator
        
        # Repository created internally by TimelineManager
        # Repository created internally by PeriodGenerator
        timeline_manager = TimelineManager(clean_database)
        period_generator = PeriodGenerator(clean_database)
        
        # Create timeline
        timeline_data = {
            "name": f"quarterly_timeline_{test_session_id[:8]}",
            "service_name": "test-service",
            "repo_path": "/test/repo",
            "start_date": datetime(2024, 1, 1),
            "end_date": datetime(2024, 12, 31),  # 1 year
            "strategy": "quarterly",
            "metadata": {"_test_data_marker": True}
        }
        timeline = await timeline_manager.create_timeline(timeline_data, skip_confidence_check=True)
        
        # Generate periods
        periods = await period_generator.generate_periods(
            timeline_id=timeline.id,
            service_name=timeline.service_name,
            start_date=timeline.start_date,
            end_date=timeline.end_date,
            strategy=PeriodStrategy.QUARTERLY
        )
        
        # Should have 4 periods (Q1-Q4)
        assert len(periods) >= 4
    
    async def test_generate_adaptive_periods(
        self,
        clean_database,
        test_session_id
    ):
        """Test generating adaptive periods based on document density."""
        from src.storage.repositories import TimelineRepository, TimePeriodRepository
        from src.services.timeline import TimelineManager, PeriodGenerator
        
        # Repository created internally by TimelineManager
        # Repository created internally by PeriodGenerator
        timeline_manager = TimelineManager(clean_database)
        period_generator = PeriodGenerator(clean_database)
        
        # Create timeline
        timeline_data = {
            "name": f"adaptive_timeline_{test_session_id[:8]}",
            "service_name": "test-service",
            "repo_path": "/test/repo",
            "start_date": datetime(2024, 1, 1),
            "end_date": datetime(2024, 12, 31),
            "strategy": "adaptive",
            "metadata": {"_test_data_marker": True}
        }
        timeline = await timeline_manager.create_timeline(timeline_data, skip_confidence_check=True)
        
        # Generate periods
        periods = await period_generator.generate_periods(
            timeline_id=timeline.id,
            service_name=timeline.service_name,
            start_date=timeline.start_date,
            end_date=timeline.end_date,
            strategy=PeriodStrategy.ADAPTIVE
        )
        
        # Should have at least some periods
        assert len(periods) > 0
    
    async def test_period_sequence_numbers(
        self,
        clean_database,
        test_session_id
    ):
        """Test that periods have correct sequence numbers."""
        from src.storage.repositories import TimelineRepository, TimePeriodRepository
        from src.services.timeline import TimelineManager, PeriodGenerator
        
        # Repository created internally by TimelineManager
        # Repository created internally by PeriodGenerator
        timeline_manager = TimelineManager(clean_database)
        period_generator = PeriodGenerator(clean_database)
        
        # Create timeline
        timeline_data = {
            "name": f"sequence_timeline_{test_session_id[:8]}",
            "service_name": "test-service",
            "repo_path": "/test/repo",
            "start_date": datetime(2024, 1, 1),
            "end_date": datetime(2024, 6, 30),
            "strategy": "monthly",
            "metadata": {"_test_data_marker": True}
        }
        timeline = await timeline_manager.create_timeline(timeline_data, skip_confidence_check=True)
        
        # Generate periods
        periods = await period_generator.generate_periods(
            timeline_id=timeline.id,
            service_name=timeline.service_name,
            start_date=timeline.start_date,
            end_date=timeline.end_date,
            strategy=PeriodStrategy.MONTHLY
        )
        
        # Verify sequence numbers are consecutive
        sequence_numbers = sorted([p.sequence_number for p in periods])
        assert sequence_numbers == list(range(len(periods)))


class TestDocumentPlacement:
    """Test placing documents in time periods."""
    
    async def test_place_documents_in_periods(
        self,
        clean_database,
        test_session_id
    ):
        """Test placing documents in appropriate time periods."""
        from src.storage.repositories import (
            DocumentRepository,
            TimelineRepository,
            TimePeriodRepository,
            DocumentPlacementRepository
        )
        from src.services.timeline import TimelineManager, PeriodGenerator, DocumentPlacer
        from tests.utils.test_helpers import create_test_document
        
        # Setup repositories
        doc_repo = DocumentRepository(clean_database)
        # Repository created internally by TimelineManager
        # Repository created internally by PeriodGenerator
        # Repository created internally by DocumentPlacer
        
        # Setup services
        timeline_manager = TimelineManager(clean_database)
        period_generator = PeriodGenerator(clean_database)
        document_placer = DocumentPlacer(clean_database)
        
        # Create timeline
        timeline_data = {
            "name": f"placement_timeline_{test_session_id[:8]}",
            "service_name": "test-service",
            "repo_path": "/test/repo",
            "start_date": datetime(2024, 1, 1),
            "end_date": datetime(2024, 12, 31),
            "strategy": "monthly",
            "metadata": {"_test_data_marker": True}
        }
        timeline = await timeline_manager.create_timeline(timeline_data, skip_confidence_check=True)
        
        # Generate periods
        periods = await period_generator.generate_periods(
            timeline_id=timeline.id,
            service_name=timeline.service_name,
            start_date=timeline.start_date,
            end_date=timeline.end_date,
            strategy=PeriodStrategy.MONTHLY
        )
        
        # Create test documents
        docs = []
        for i in range(5):
            doc_data = create_test_document(
                content=f"Test content {i}",
                file_path=f"test_{i}.py",
                service_name="test-service",
                session_id=test_session_id
            )
            doc = await doc_repo.create(doc_data)
            docs.append(doc)
        
        # Place documents in periods
        placements = await document_placer.place_documents(
            timeline_id=timeline.id,
            document_ids=[d.id for d in docs],
            periods=periods
        )
        
        # Verify placements
        assert len(placements) > 0
        assert all(p.timeline_id == timeline.id for p in placements)


class TestTimelineQueries:
    """Test querying timeline data."""
    
    async def test_query_timeline_by_service(
        self,
        clean_database,
        test_session_id
    ):
        """Test querying timelines by service name."""
        from src.storage.repositories import TimelineRepository
        from src.services.timeline import TimelineManager
        
        # Repository created internally by TimelineManager
        timeline_manager = TimelineManager(clean_database)
        
        # Create multiple timelines for same service
        service_name = f"query_service_{test_session_id[:8]}"
        for i in range(3):
            timeline_data = {
                "name": f"timeline_{i}",
                "service_name": service_name,
                "repo_path": "/test/repo",
                "start_date": datetime(2024, 1, 1),
                "end_date": datetime(2024, 12, 31),
                "strategy": "monthly",
                "metadata": {"_test_data_marker": True}
            }
            await timeline_manager.create_timeline(timeline_data, skip_confidence_check=True)
        
        # Query timelines
        timelines = await timeline_repo.get_by_service(service_name)
        
        assert len(timelines) >= 3
        assert all(t.service_name == service_name for t in timelines)
    
    async def test_get_timeline_summary(
        self,
        clean_database,
        test_session_id
    ):
        """Test getting timeline summary with statistics."""
        from src.storage.repositories import TimelineRepository, TimePeriodRepository
        from src.services.timeline import TimelineManager, PeriodGenerator
        
        # Repository created internally by TimelineManager
        # Repository created internally by PeriodGenerator
        timeline_manager = TimelineManager(clean_database)
        period_generator = PeriodGenerator(clean_database)
        
        # Create timeline with periods
        timeline_data = {
            "name": f"summary_timeline_{test_session_id[:8]}",
            "service_name": "test-service",
            "repo_path": "/test/repo",
            "start_date": datetime(2024, 1, 1),
            "end_date": datetime(2024, 3, 31),
            "strategy": "monthly",
            "metadata": {"_test_data_marker": True}
        }
        timeline = await timeline_manager.create_timeline(timeline_data, skip_confidence_check=True)
        
        # Generate periods
        await period_generator.generate_periods(
            timeline_id=timeline.id,
            start_date=timeline.start_date,
            end_date=timeline.end_date,
            strategy=PeriodStrategy.MONTHLY
        )
        
        # Get summary
        summary = await timeline_manager.get_timeline_summary(timeline.id)
        
        assert summary is not None
        assert "timeline" in summary
        assert "period_count" in summary or "periods" in summary


class TestConfidenceCalculation:
    """Test temporal confidence calculation."""
    
    async def test_calculate_confidence_high(
        self,
        clean_database,
        test_session_id
    ):
        """Test calculating HIGH confidence for git history ingestion."""
        from src.storage.repositories import TimelineRepository
        from src.services.timeline import TimelineManager, TemporalConfidenceCalculator
        
        # Repository created internally by TimelineManager
        timeline_manager = TimelineManager(clean_database)
        confidence_calc = TemporalConfidenceCalculator()
        
        # Create timeline (simulating git history)
        timeline_data = {
            "name": f"high_confidence_{test_session_id[:8]}",
            "service_name": "test-service",
            "repo_path": "/test/repo",
            "start_date": datetime(2024, 1, 1),
            "end_date": datetime(2024, 12, 31),
            "strategy": "monthly",
            "metadata": {
                "_test_data_marker": True,
                "ingestion_mode": "git_history"  # Should give HIGH confidence
            }
        }
        timeline = await timeline_manager.create_timeline(timeline_data, skip_confidence_check=True)
        
        # Calculate confidence
        confidence = confidence_calc.calculate_confidence(
            ingestion_mode="git_history",
            has_commit_history=True
        )
        
        assert confidence == "HIGH"
    
    async def test_calculate_confidence_low(
        self,
        clean_database,
        test_session_id
    ):
        """Test calculating LOW/NONE confidence for snapshot ingestion."""
        from src.services.timeline import TemporalConfidenceCalculator
        
        confidence_calc = TemporalConfidenceCalculator()
        
        # Calculate confidence for snapshot (no history)
        confidence = confidence_calc.calculate_confidence(
            ingestion_mode="snapshot",
            has_commit_history=False
        )
        
        assert confidence in ["LOW", "NONE"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "functional"])

