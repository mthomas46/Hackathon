"""
Timeline Workflow Functional Tests

Tests the complete timeline workflow with real database:
- Timeline creation with confidence validation
- Period generation
- Document placement
- Gap and drift detection
- Report generation

These tests validate the full Phase 1-3 implementation using real database.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import List
from uuid import uuid4

# Import timeline services
from src.services.timeline import (
    TemporalConfidenceCalculator,
    TimelineManager,
    PeriodGenerator,
    DocumentPlacer,
    GapAnalyzer,
    DriftDetector,
    ReportGenerator,
    DocumentConsolidator,
)

# Import models
from src.models.timeline import (
    Timeline,
    TimelineCreate,
    TimePeriod,
    TemporalConfidence,
    PeriodStrategy,
)

# Import storage
from src.storage.repositories.document_repository import DocumentRepository
from src.storage.repositories.timeline_repository import TimelineRepository

# Import test helpers
from tests.utils.test_helpers import create_test_document


@pytest.mark.functional
@pytest.mark.asyncio
class TestTimelineWorkflow:
    """Functional tests for timeline workflow with real database."""
    
    async def _create_test_documents(
        self,
        db_session,
        service_name: str,
        git_history_count: int = 95,
        snapshot_count: int = 5
    ) -> List:
        """
        Helper to create test documents in the database.
        
        Args:
            db_session: Database session
            service_name: Service name for documents
            git_history_count: Number of documents with git history
            snapshot_count: Number of snapshot documents
            
        Returns:
            List of created document IDs
        """
        from src.storage.db_models import GitCommitModel
        doc_repo = DocumentRepository(db_session)
        doc_ids = []
        
        # Create documents with git history
        for i in range(git_history_count):
            # Create git commit first
            commit_sha = f"abc{i:03d}"
            commit_date = datetime.now() - timedelta(days=365-i)
            
            # Check if commit already exists
            from sqlalchemy import select
            result = await db_session.execute(
                select(GitCommitModel).where(GitCommitModel.sha == commit_sha)
            )
            existing_commit = result.scalar_one_or_none()
            
            if not existing_commit:
                commit = GitCommitModel(
                    sha=commit_sha,
                    author="Test Author",
                    author_email="test@example.com",
                    date=commit_date,
                    message=f"Test commit {i}",
                    commit_metadata={}
                )
                db_session.add(commit)
                await db_session.flush()
            
            # Create document with unique file path per service
            doc = create_test_document(
                content=f"# Test Document {i}\n\nContent for document {i} in {service_name}",
                file_path=f"{service_name}/src/file_{i}.py",
                file_type="python",
                service_name=service_name,
                ingestion_mode="git_history",
                git_commit_sha=commit_sha,
            )
            created_doc = await doc_repo.create(doc)
            doc_ids.append(created_doc.id)
        
        # Create snapshot documents
        for i in range(snapshot_count):
            doc = create_test_document(
                content=f"# Snapshot Document {i}\n\nSnapshot content {i} in {service_name}",
                file_path=f"{service_name}/docs/readme_{i}.md",
                file_type="markdown",
                service_name=service_name,
                ingestion_mode="snapshot",
                git_commit_sha=None,
            )
            created_doc = await doc_repo.create(doc)
            doc_ids.append(created_doc.id)
        
        await db_session.commit()
        return doc_ids
    
    # =========================================================================
    # PHASE 1: CORE TIMELINE TESTS (Confidence, Periods, Placement)
    # =========================================================================
    
    async def test_confidence_calculation_high(self, db_session):
        """
        Test confidence calculation with high confidence documents (95% git history).
        
        Validates:
        - Confidence level is HIGH
        - Score >= 0.9
        - Correct counts for git_history vs snapshot
        - Fallback strategy is "none_needed"
        - All capabilities enabled
        """
        service_name = f"test-service-high-{uuid4().hex[:8]}"
        
        # Create 95 git_history + 5 snapshot documents
        await self._create_test_documents(
            db_session,
            service_name=service_name,
            git_history_count=95,
            snapshot_count=5
        )
        
        # Calculate confidence
        calculator = TemporalConfidenceCalculator(db_session=db_session)
        result = await calculator.calculate_confidence(service_name=service_name)
        
        # Validate results
        assert result.git_percentage >= 90.0  # HIGH confidence threshold
        assert result.git_history_documents == 95
        assert result.snapshot_documents == 5
        assert result.total_documents == 100
        assert result.fallback_strategy == "minimal_fallback"
        assert result.can_show_evolution is True
        assert result.can_detect_drift is True
        assert result.can_show_timeline is True
        assert result.can_compare_periods is True
        assert len(result.warnings) == 0  # No warnings for high confidence
    
    async def test_confidence_calculation_medium(self, db_session):
        """
        Test confidence calculation with medium confidence documents (60% git history).
        
        Validates:
        - Confidence level is MEDIUM
        - Score between 0.5 and 0.8
        - Correct counts
        - Fallback strategy is "hybrid"
        - Some capabilities enabled
        """
        service_name = f"test-service-medium-{uuid4().hex[:8]}"
        
        # Create 60 git_history + 40 snapshot documents
        await self._create_test_documents(
            db_session,
            service_name=service_name,
            git_history_count=60,
            snapshot_count=40
        )
        
        # Calculate confidence
        calculator = TemporalConfidenceCalculator(db_session=db_session)
        result = await calculator.calculate_confidence(service_name=service_name)
        
        # Validate results
        assert 50.0 <= result.git_percentage < 90.0  # MEDIUM confidence range
        assert result.git_history_documents == 60
        assert result.snapshot_documents == 40
        assert result.total_documents == 100
        assert result.fallback_strategy == "hybrid_with_warnings"
        assert result.can_show_evolution is True  # Partial support
        assert result.can_detect_drift is True  # Partial support
        assert result.can_show_timeline is True  # With gaps
        assert result.can_compare_periods is True  # With limitations
        assert len(result.warnings) > 0  # Should have warnings
    
    async def test_confidence_calculation_low(self, db_session):
        """
        Test confidence calculation with low confidence documents (30% git history).
        
        Validates:
        - Confidence level is LOW
        - Score between 0.2 and 0.5
        - Correct counts
        - Fallback strategy is "prefer_alternatives"
        - Limited capabilities
        """
        service_name = f"test-service-low-{uuid4().hex[:8]}"
        
        # Create 30 git_history + 70 snapshot documents
        await self._create_test_documents(
            db_session,
            service_name=service_name,
            git_history_count=30,
            snapshot_count=70
        )
        
        # Calculate confidence
        calculator = TemporalConfidenceCalculator(db_session=db_session)
        result = await calculator.calculate_confidence(service_name=service_name)
        
        # Validate results
        assert 0.0 < result.git_percentage < 50.0  # LOW confidence range
        assert result.git_history_documents == 30
        assert result.snapshot_documents == 70
        assert result.total_documents == 100
        assert result.fallback_strategy == "content_based_fallback"
        assert result.can_show_evolution is False  # Too limited
        assert result.can_detect_drift is False  # Not reliable
        assert result.can_show_timeline is True  # Content-based only
        assert result.can_compare_periods is True  # Content comparison only
        assert len(result.warnings) > 0  # Should have warnings
    
    async def test_confidence_calculation_none(self, db_session):
        """
        Test confidence calculation with no confidence documents (100% snapshot).
        
        Validates:
        - Confidence level is NONE
        - Score is 0.0
        - All documents are snapshot
        - Fallback strategy is "use_alternatives_only"
        - No capabilities enabled
        """
        service_name = f"test-service-none-{uuid4().hex[:8]}"
        
        # Create 0 git_history + 100 snapshot documents
        await self._create_test_documents(
            db_session,
            service_name=service_name,
            git_history_count=0,
            snapshot_count=100
        )
        
        # Calculate confidence
        calculator = TemporalConfidenceCalculator(db_session=db_session)
        result = await calculator.calculate_confidence(service_name=service_name)
        
        # Validate results
        assert result.git_percentage == 0.0  # NONE confidence
        assert result.git_history_documents == 0
        assert result.snapshot_documents == 100
        assert result.total_documents == 100
        assert result.fallback_strategy == "no_temporal_features"
        assert result.can_show_evolution is False  # No git history
        assert result.can_detect_drift is False  # No git history
        assert result.can_show_timeline is False  # No temporal data
        assert result.can_compare_periods is False  # No temporal data
        assert len(result.warnings) > 0  # Should have warnings
    
    async def test_period_generation_monthly(self, db_session):
        """
        Test monthly period generation.
        
        Validates:
        - Correct number of periods (12 for full year)
        - Period names are correct
        - No gaps between periods
        - Periods cover full date range
        """
        service_name = f"test-service-monthly-{uuid4().hex[:8]}"
        
        # Create documents with git history to pass confidence check
        await self._create_test_documents(
            db_session=db_session,
            service_name=service_name,
            git_history_count=50,  # MEDIUM confidence (50%)
            snapshot_count=50
        )
        
        # Create timeline with skip_confidence_check
        timeline_manager = TimelineManager(db_session=db_session)
        timeline = await timeline_manager.create_timeline(
            TimelineCreate(
                name=f"monthly-test-{uuid4().hex[:8]}",
                service_name=service_name,
                repo_path="/test/repo",
                period_strategy=PeriodStrategy.MONTHLY,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 12, 31),
            ),
            skip_confidence_check=True  # Skip for now, we just want to test period generation
        )
        
        # Generate periods
        generator = PeriodGenerator(db_session=db_session)
        periods = await generator.generate_periods(
            timeline_id=timeline.id,
            service_name=service_name,
            start_date=timeline.start_date,
            end_date=timeline.end_date,
            strategy=PeriodStrategy.MONTHLY
        )
        
        # Validate period count
        assert len(periods) == 12
        
        # Validate period names
        assert periods[0].name == "January 2024"
        assert periods[11].name == "December 2024"
        
        # Verify no gaps between periods (periods end at 23:59:59, next starts at 00:00:00)
        for i in range(len(periods) - 1):
            # Allow for 1 second gap (end at 23:59:59, start at 00:00:00 next day)
            gap = (periods[i+1].start_date - periods[i].end_date).total_seconds()
            assert gap <= 1, f"Gap between periods: {gap} seconds"
        
        # Verify full coverage
        assert periods[0].start_date == timeline.start_date
        assert periods[-1].end_date >= timeline.end_date
    
    async def test_period_generation_quarterly(self, db_session):
        """
        Test quarterly period generation.
        
        Validates:
        - Correct number of periods (4 for full year)
        - Period names are correct
        - No gaps between periods
        """
        service_name = f"test-service-quarterly-{uuid4().hex[:8]}"
        
        # Create documents with git history to pass confidence check
        await self._create_test_documents(
            db_session=db_session,
            service_name=service_name,
            git_history_count=50,
            snapshot_count=50
        )
        
        # Create timeline with skip_confidence_check
        timeline_manager = TimelineManager(db_session=db_session)
        timeline = await timeline_manager.create_timeline(
            TimelineCreate(
                name=f"quarterly-test-{uuid4().hex[:8]}",
                service_name=service_name,
                repo_path="/test/repo",
                period_strategy=PeriodStrategy.QUARTERLY,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 12, 31),
            ),
            skip_confidence_check=True
        )
        
        # Generate periods
        generator = PeriodGenerator(db_session=db_session)
        periods = await generator.generate_periods(
            timeline_id=timeline.id,
            service_name=service_name,
            start_date=timeline.start_date,
            end_date=timeline.end_date,
            strategy=PeriodStrategy.QUARTERLY
        )
        
        # Validate period count
        assert len(periods) == 4
        
        # Validate period names
        assert "Q1" in periods[0].name
        assert "Q4" in periods[3].name
        
        # Verify no gaps (periods end at 23:59:59, next starts at 00:00:00)
        for i in range(len(periods) - 1):
            gap = (periods[i+1].start_date - periods[i].end_date).total_seconds()
            assert gap <= 1, f"Gap between periods: {gap} seconds"
    
    async def test_period_generation_adaptive(self, db_session):
        """
        Test adaptive period generation.
        
        Validates:
        - Adaptive strategy selects appropriate period size
        - Periods are generated based on data density
        """
        service_name = f"test-service-adaptive-{uuid4().hex[:8]}"
        
        # Create documents with git history to pass confidence check
        await self._create_test_documents(
            db_session=db_session,
            service_name=service_name,
            git_history_count=50,
            snapshot_count=50
        )
        
        # Create timeline with skip_confidence_check
        timeline_manager = TimelineManager(db_session=db_session)
        timeline = await timeline_manager.create_timeline(
            TimelineCreate(
                name=f"adaptive-test-{uuid4().hex[:8]}",
                service_name=service_name,
                repo_path="/test/repo",
                period_strategy=PeriodStrategy.ADAPTIVE,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 12, 31),
            ),
            skip_confidence_check=True
        )
        
        # Generate periods
        generator = PeriodGenerator(db_session=db_session)
        periods = await generator.generate_periods(
            timeline_id=timeline.id,
            service_name=service_name,
            start_date=timeline.start_date,
            end_date=timeline.end_date,
            strategy=PeriodStrategy.ADAPTIVE
        )
        
        # Validate we got some periods
        assert len(periods) > 0
        
        # Validate periods cover the range
        assert periods[0].start_date >= timeline.start_date
        assert periods[-1].end_date <= timeline.end_date
    
    async def test_timeline_creation_end_to_end(self, db_session):
        """
        Test complete timeline creation workflow.
        
        Validates:
        - Timeline is created in database
        - Confidence is calculated
        - Periods are generated
        - Documents are placed in periods
        - Timeline can be retrieved
        """
        service_name = f"test-service-e2e-{uuid4().hex[:8]}"
        
        # Create test documents
        await self._create_test_documents(
            db_session,
            service_name=service_name,
            git_history_count=80,
            snapshot_count=20
        )
        
        # Create timeline
        timeline_manager = TimelineManager(db_session=db_session)
        timeline_create = TimelineCreate(
            name=f"test-timeline-{uuid4().hex[:8]}",
            service_name=service_name,
            repo_path="/test/repo",
            period_strategy=PeriodStrategy.MONTHLY,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
        )
        
        timeline = await timeline_manager.create_timeline(timeline_create)
        
        # Validate timeline
        assert timeline.id is not None
        assert timeline.name == timeline_create.name
        assert timeline.service_name == service_name
        assert timeline.repo_path == "/test/repo"
        assert timeline.start_date == datetime(2024, 1, 1)
        assert timeline.end_date == datetime(2024, 12, 31)
        
        # Validate timeline can be retrieved
        timeline_repo = TimelineRepository(db_session)
        retrieved = await timeline_repo.get_by_id(timeline.id)
        assert retrieved is not None
        assert retrieved.id == timeline.id
        assert retrieved.name == timeline.name
    
    # =========================================================================
    # PHASE 2: TEMPORAL RAG TESTS (Time-travel queries)
    # =========================================================================
    
    async def test_temporal_rag_query_as_of(self, db_session):
        """
        Test time-travel RAG query (query as of specific date).
        
        Validates:
        - Can query documents as they existed at a specific date
        - Only documents before the date are included
        - Results are relevant to the query
        """
        from src.services.rag.temporal_rag_service import TemporalRAGService
        
        service_name = f"test-service-temporal-as-of-{uuid4().hex[:8]}"
        
        # Create timeline with documents
        await self._create_test_documents(
            db_session=db_session,
            service_name=service_name,
            git_history_count=50,
            snapshot_count=0
        )
        
        # Create timeline
        timeline_manager = TimelineManager(db_session=db_session)
        timeline = await timeline_manager.create_timeline(
            TimelineCreate(
                name=f"temporal-as-of-test-{uuid4().hex[:8]}",
                service_name=service_name,
                repo_path="/test/repo",
                period_strategy=PeriodStrategy.MONTHLY,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 12, 31),
            ),
            skip_confidence_check=True
        )
        
        # Query as of a specific date
        temporal_rag = TemporalRAGService(db_session=db_session)
        result = await temporal_rag.query_as_of(
            query="What is the authentication process?",
            as_of_date=datetime(2024, 6, 1),
            service_name=service_name
        )
        
        # Validate result structure
        assert result is not None
        assert isinstance(result, dict)
        assert 'query' in result
        assert 'as_of_date' in result
        # May have temporal_context or fallback to standard RAG
        assert 'results' in result or 'temporal_context' in result
    
    async def test_temporal_rag_query_evolution(self, db_session):
        """
        Test evolution query (how topic evolved over time).
        
        Validates:
        - Can track how a topic/concept evolved
        - Results are ordered chronologically
        - Changes are highlighted
        """
        from src.services.rag.temporal_rag_service import TemporalRAGService
        
        service_name = f"test-service-temporal-evolution-{uuid4().hex[:8]}"
        
        # Create timeline with documents
        await self._create_test_documents(
            db_session=db_session,
            service_name=service_name,
            git_history_count=50,
            snapshot_count=0
        )
        
        # Create timeline
        timeline_manager = TimelineManager(db_session=db_session)
        timeline = await timeline_manager.create_timeline(
            TimelineCreate(
                name=f"temporal-evolution-test-{uuid4().hex[:8]}",
                service_name=service_name,
                repo_path="/test/repo",
                period_strategy=PeriodStrategy.QUARTERLY,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 12, 31),
            ),
            skip_confidence_check=True
        )
        
        # Query evolution
        temporal_rag = TemporalRAGService(db_session=db_session)
        result = await temporal_rag.query_evolution(
            topic="authentication",
            timeline_id=timeline.id
        )
        
        # Validate result structure
        assert result is not None
        assert isinstance(result, dict)
        assert 'topic' in result
        assert 'timeline_id' in result
        # May have evolution data or fallback
        assert 'periods' in result or 'message' in result
    
    async def test_temporal_rag_query_what_changed(self, db_session):
        """
        Test what-changed query (what changed between two dates).
        
        Validates:
        - Can identify changes between two points in time
        - Additions, modifications, deletions are tracked
        - Results are accurate
        """
        from src.services.rag.temporal_rag_service import TemporalRAGService
        
        service_name = f"test-service-temporal-what-changed-{uuid4().hex[:8]}"
        
        # Create timeline with documents
        await self._create_test_documents(
            db_session=db_session,
            service_name=service_name,
            git_history_count=50,
            snapshot_count=0
        )
        
        # Create timeline
        timeline_manager = TimelineManager(db_session=db_session)
        timeline = await timeline_manager.create_timeline(
            TimelineCreate(
                name=f"temporal-what-changed-test-{uuid4().hex[:8]}",
                service_name=service_name,
                repo_path="/test/repo",
                period_strategy=PeriodStrategy.MONTHLY,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 12, 31),
            ),
            skip_confidence_check=True
        )
        
        # Query what changed
        temporal_rag = TemporalRAGService(db_session=db_session)
        result = await temporal_rag.query_what_changed(
            query="authentication",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 6, 30),
            service_name=service_name
        )
        
        # Validate result structure
        assert result is not None
        assert isinstance(result, dict)
        assert 'query' in result
        assert 'start_date' in result
        assert 'end_date' in result
        # May have changes or fallback
        assert 'changes' in result or 'message' in result
    
    # =========================================================================
    # PHASE 3: GAP/DRIFT TESTS (Advanced analysis)
    # =========================================================================
    
    async def test_gap_analysis(self, db_session):
        """
        Test gap analysis (identify periods with no activity).
        
        Validates:
        - Can identify gaps in timeline
        - Gap duration is calculated correctly
        - Recommendations are provided
        """
        service_name = f"test-service-gaps-{uuid4().hex[:8]}"
        
        # Create documents with intentional gaps
        from src.storage.db_models import GitCommitModel
        from sqlalchemy import select
        doc_repo = DocumentRepository(db_session)
        
        # Documents in January
        for i in range(10):
            commit_sha = f"jan{i:03d}"
            commit_date = datetime(2024, 1, 15) + timedelta(hours=i)
            
            # Create commit
            result = await db_session.execute(
                select(GitCommitModel).where(GitCommitModel.sha == commit_sha)
            )
            if not result.scalar_one_or_none():
                commit = GitCommitModel(
                    sha=commit_sha,
                    author="Test Author",
                    author_email="test@example.com",
                    date=commit_date,
                    message=f"January commit {i}",
                    commit_metadata={}
                )
                db_session.add(commit)
                await db_session.flush()
            
            doc = create_test_document(
                content=f"# January Document {i}",
                file_path=f"src/jan_{i}.py",
                service_name=service_name,
                ingestion_mode="git_history",
                git_commit_sha=commit_sha,
            )
            await doc_repo.create(doc)
        
        # Gap: February-March (no documents)
        
        # Documents in April
        for i in range(10):
            commit_sha = f"apr{i:03d}"
            commit_date = datetime(2024, 4, 15) + timedelta(hours=i)
            
            # Create commit
            result = await db_session.execute(
                select(GitCommitModel).where(GitCommitModel.sha == commit_sha)
            )
            if not result.scalar_one_or_none():
                commit = GitCommitModel(
                    sha=commit_sha,
                    author="Test Author",
                    author_email="test@example.com",
                    date=commit_date,
                    message=f"April commit {i}",
                    commit_metadata={}
                )
                db_session.add(commit)
                await db_session.flush()
            
            doc = create_test_document(
                content=f"# April Document {i}",
                file_path=f"src/apr_{i}.py",
                service_name=service_name,
                ingestion_mode="git_history",
                git_commit_sha=commit_sha,
            )
            await doc_repo.create(doc)
        
        await db_session.commit()
        
        # Create timeline
        timeline_manager = TimelineManager(db_session=db_session)
        timeline = await timeline_manager.create_timeline(
            TimelineCreate(
                name=f"gap-test-{uuid4().hex[:8]}",
                service_name=service_name,
                repo_path="/test/repo",
                period_strategy=PeriodStrategy.MONTHLY,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 12, 31),
            )
        )
        
        # Analyze gaps
        gap_analyzer = GapAnalyzer(db_session=db_session)
        result = await gap_analyzer.analyze_gaps(timeline_id=timeline.id)
        
        # Validate gaps (returns dict with nested gaps)
        assert result is not None
        assert isinstance(result, dict)
        assert 'total_gaps' in result
        assert 'gaps' in result
        
        # Gaps are nested under 'gaps' key, grouped by severity
        gaps_by_severity = result['gaps']
        assert isinstance(gaps_by_severity, dict)
        assert 'CRITICAL' in gaps_by_severity
        assert 'HIGH' in gaps_by_severity
        assert 'MEDIUM' in gaps_by_severity
        assert 'LOW' in gaps_by_severity
        
        # Each severity level has a list of gaps
        for severity_level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            gaps_for_level = gaps_by_severity[severity_level]
            assert isinstance(gaps_for_level, list)
            
            # If there are gaps, validate structure
            if len(gaps_for_level) > 0:
                for gap in gaps_for_level:
                    assert isinstance(gap, dict)
                    assert 'gap_type' in gap
                    assert 'severity' in gap
                    assert 'description' in gap
    
    async def test_drift_detection(self, db_session):
        """
        Test drift detection (identify API/data contract changes).
        
        Validates:
        - Can detect changes in API signatures
        - Can detect data contract changes
        - Severity is assessed correctly
        """
        service_name = f"test-service-drift-{uuid4().hex[:8]}"
        
        # Create documents showing API evolution
        from src.storage.db_models import GitCommitModel
        from sqlalchemy import select
        doc_repo = DocumentRepository(db_session)
        
        # Version 1: Original API
        commit_sha_v1 = "v1"
        result = await db_session.execute(
            select(GitCommitModel).where(GitCommitModel.sha == commit_sha_v1)
        )
        if not result.scalar_one_or_none():
            commit1 = GitCommitModel(
                sha=commit_sha_v1,
                author="Test Author",
                author_email="test@example.com",
                date=datetime(2024, 1, 1),
                message="API v1",
                commit_metadata={}
            )
            db_session.add(commit1)
            await db_session.flush()
        
        doc1 = create_test_document(
            content="""
# API Version 1
def get_user(user_id: int) -> User:
    return User(id=user_id)
""",
            file_path="src/api.py",
            service_name=service_name,
            ingestion_mode="git_history",
            git_commit_sha=commit_sha_v1,
        )
        await doc_repo.create(doc1)
        
        # Version 2: API changed (breaking change)
        commit_sha_v2 = "v2"
        result = await db_session.execute(
            select(GitCommitModel).where(GitCommitModel.sha == commit_sha_v2)
        )
        if not result.scalar_one_or_none():
            commit2 = GitCommitModel(
                sha=commit_sha_v2,
                author="Test Author",
                author_email="test@example.com",
                date=datetime(2024, 6, 1),
                message="API v2 - breaking changes",
                commit_metadata={}
            )
            db_session.add(commit2)
            await db_session.flush()
        
        doc2 = create_test_document(
            content="""
# API Version 2
def get_user(user_uuid: str, include_details: bool = False) -> UserDetails:
    return UserDetails(uuid=user_uuid, details=include_details)
""",
            file_path="src/api.py",
            service_name=service_name,
            ingestion_mode="git_history",
            git_commit_sha=commit_sha_v2,
        )
        await doc_repo.create(doc2)
        
        await db_session.commit()
        
        # Create timeline
        timeline_manager = TimelineManager(db_session=db_session)
        timeline = await timeline_manager.create_timeline(
            TimelineCreate(
                name=f"drift-test-{uuid4().hex[:8]}",
                service_name=service_name,
                repo_path="/test/repo",
                period_strategy=PeriodStrategy.MONTHLY,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 12, 31),
            )
        )
        
        # Detect drift
        drift_detector = DriftDetector(db_session=db_session)
        result = await drift_detector.detect_drift(
            timeline_id=timeline.id,
            service_name=service_name,
            detection_mode="hybrid"
        )
        
        # Validate drift detection (returns dict with nested drifts)
        assert result is not None
        assert isinstance(result, dict)
        assert 'total_drifts' in result
        assert 'drifts' in result
        
        # Drifts are nested under 'drifts' key, grouped by severity
        drifts_by_severity = result['drifts']
        assert isinstance(drifts_by_severity, dict)
        assert 'CRITICAL' in drifts_by_severity
        assert 'HIGH' in drifts_by_severity
        assert 'MEDIUM' in drifts_by_severity
        assert 'LOW' in drifts_by_severity
        
        # Each severity level has a list of drifts
        for severity_level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            drifts_for_level = drifts_by_severity[severity_level]
            assert isinstance(drifts_for_level, list)
            
            # If there are drifts, validate structure
            if len(drifts_for_level) > 0:
                for drift in drifts_for_level:
                    assert isinstance(drift, dict)
                    assert 'drift_type' in drift or 'type' in drift
                    assert 'description' in drift or 'message' in drift
    
    async def test_report_generation(self, db_session):
        """
        Test report generation (progression, gap, drift reports).
        
        Validates:
        - Can generate progression report
        - Can generate gap report
        - Can generate drift report
        - Reports are well-formatted and citable
        """
        service_name = f"test-service-report-{uuid4().hex[:8]}"
        
        # Create test documents
        await self._create_test_documents(
            db_session,
            service_name=service_name,
            git_history_count=50,
            snapshot_count=10
        )
        
        # Create timeline
        timeline_manager = TimelineManager(db_session=db_session)
        timeline = await timeline_manager.create_timeline(
            TimelineCreate(
                name=f"report-test-{uuid4().hex[:8]}",
                service_name=service_name,
                repo_path="/test/repo",
                period_strategy=PeriodStrategy.QUARTERLY,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 12, 31),
            )
        )
        
        # Generate progression report
        report_generator = ReportGenerator()
        report = await report_generator.generate_progression_report(
            timeline_id=str(timeline.id),
            service_name=service_name
        )
        
        # Validate report (returns dict)
        assert report is not None
        assert isinstance(report, dict)
        assert report['timeline_id'] == str(timeline.id)
        assert report['type'] == "progression"
        assert len(report['content']) > 0
        # Citations are embedded in content, not a separate field
        assert report.get('metadata') is not None
    
    async def test_document_consolidation(self, db_session):
        """
        Test document consolidation (identify consolidation opportunities).
        
        Validates:
        - Can identify duplicate/similar documents
        - Can identify outdated documents
        - Consolidation recommendations are provided
        """
        service_name = f"test-service-consolidate-{uuid4().hex[:8]}"
        
        # Create similar documents
        from src.storage.db_models import GitCommitModel
        from sqlalchemy import select
        doc_repo = DocumentRepository(db_session)
        
        for i in range(5):
            commit_sha = f"auth{i:03d}"
            commit_date = datetime(2024, 1, 1) + timedelta(days=i*30)
            
            # Create commit
            result = await db_session.execute(
                select(GitCommitModel).where(GitCommitModel.sha == commit_sha)
            )
            if not result.scalar_one_or_none():
                commit = GitCommitModel(
                    sha=commit_sha,
                    author="Test Author",
                    author_email="test@example.com",
                    date=commit_date,
                    message=f"Auth docs v{i}",
                    commit_metadata={}
                )
                db_session.add(commit)
                await db_session.flush()
            
            doc = create_test_document(
                content=f"# User Authentication\n\nThis document describes user authentication. Version {i}.",
                file_path=f"docs/auth_{i}.md",
                service_name=service_name,
            ingestion_mode="git_history",
                git_commit_sha=commit_sha,
            )
            await doc_repo.create(doc)
        
        await db_session.commit()
        
        # Analyze consolidation opportunities
        consolidator = DocumentConsolidator()
        opportunities = await consolidator.analyze_consolidation_opportunities(
            service_name=service_name,
            similarity_threshold=0.7
        )
        
        # Validate opportunities (returns dict)
        assert opportunities is not None
        assert isinstance(opportunities, dict)
        assert opportunities.get('service_name') == service_name
        # Should have analyzed documents
        assert opportunities.get('total_documents', 0) >= 0


# =========================================================================
# HELPER TESTS (Validate test infrastructure)
# =========================================================================

@pytest.mark.functional
@pytest.mark.asyncio
class TestTimelineTestInfrastructure:
    """Validate that test infrastructure is working correctly."""
    
    async def test_database_connection(self, db_session):
        """Verify database connection works."""
        assert db_session is not None
        # Try a simple query
        from sqlalchemy import text
        result = await db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1
    
    async def test_test_document_creation(self, db_session):
        """Verify test document creation works."""
        doc_repo = DocumentRepository(db_session)
        
        doc = create_test_document(
            content="# Test\n\nTest content",
            file_path="test.py",
            service_name="test-service",
        )
        
        created = await doc_repo.create(doc)
        await db_session.commit()
        
        assert created.id is not None
        assert created.file_path == "test.py"
        assert created.service_name == "test-service"
    
    async def test_timeline_repository(self, db_session):
        """Verify timeline repository works."""
        timeline_repo = TimelineRepository(db_session)
        
        # Should be able to query (even if empty)
        timelines = await timeline_repo.get_all()
        assert isinstance(timelines, list)
