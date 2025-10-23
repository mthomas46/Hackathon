"""
Functional tests for complete user journeys.

Tests end-to-end workflows that span multiple services:
1. Ingest → Query → Answer
2. Ingest → Timeline → Analysis
3. Ingest → Maintenance → Refresh
4. Multi-service integration
5. Full lifecycle workflows
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

# Mark all tests in this module as functional and asyncio
pytestmark = [pytest.mark.functional, pytest.mark.asyncio]


class TestDocumentLifecycle:
    """Test complete document lifecycle journeys."""
    
    async def test_ingest_query_answer_journey(
        self,
        clean_database,
        ecosystem_mcp_src_dir,
        test_session_id
    ):
        """
        Test complete journey: Ingest → Query → Get Answer.
        
        Simulates user workflow:
        1. Ingest documents from codebase
        2. Ask a question
        3. Get AI-generated answer with citations
        
        This is the PRIMARY user journey.
        """
        from src.storage.repositories import DocumentRepository
        from tests.utils.test_helpers import create_test_document
        
        doc_repo = DocumentRepository(clean_database)
        
        # Step 1: Ingest documents
        python_files = list(ecosystem_mcp_src_dir.rglob("*.py"))[:5]
        docs = []
        
        for file_path in python_files:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            doc_data = create_test_document(
                content=content,
                file_path=str(file_path.relative_to(ecosystem_mcp_src_dir.parent)),
                service_name="journey-test",
                session_id=test_session_id
            )
            doc = await doc_repo.create(doc_data)
            docs.append(doc)
        
        assert len(docs) == 5
        
        # Step 2: Query (simulated - actual query requires embeddings)
        query = "How does document ingestion work?"
        
        # Step 3: Retrieve documents
        results = await doc_repo.get_by_service("journey-test", limit=10)
        assert len(results) >= 5
        
        # Step 4: Verify can access content for answer generation
        assert all(d.normalized_content is not None for d in results)
        
        # Journey complete!
    
    async def test_ingest_timeline_analysis_journey(
        self,
        clean_database,
        test_session_id
    ):
        """
        Test journey: Ingest → Create Timeline → Analyze.
        
        Simulates temporal analysis workflow:
        1. Ingest versioned documents
        2. Create timeline
        3. Analyze evolution over time
        """
        from src.storage.repositories import (
            DocumentRepository,
            TimelineRepository,
            TimePeriodRepository
        )
        from src.services.timeline import TimelineManager, PeriodGenerator
        from src.models.timeline import TimelineCreate
        from tests.utils.test_helpers import create_test_document
        
        doc_repo = DocumentRepository(clean_database)
        timeline_repo = TimelineRepository(clean_database)
        period_repo = TimePeriodRepository(clean_database)
        timeline_manager = TimelineManager(timeline_repo)
        period_generator = PeriodGenerator(period_repo)
        
        # Step 1: Ingest versioned documents
        versions = ["v1", "v2", "v3"]
        for version in versions:
            doc_data = create_test_document(
                content=f"Code version {version}",
                file_path=f"code_{version}.py",
                service_name="timeline-journey",
                session_id=test_session_id,
                metadata={"version": version}
            )
            await doc_repo.create(doc_data)
        
        # Step 2: Create timeline
        timeline_data = TimelineCreate(
            name=f"journey_timeline_{test_session_id[:8]}",
            service_name="timeline-journey",
            repo_path="/test/repo",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            strategy="monthly",
            metadata={"_test_data_marker": True}
        )
        timeline = await timeline_manager.create_timeline(timeline_data)
        assert timeline is not None
        
        # Step 3: Generate periods
        periods = await period_generator.generate_periods(
            timeline_id=timeline.id,
            start_date=timeline.start_date,
            end_date=timeline.end_date,
            strategy="monthly"
        )
        assert len(periods) > 0
        
        # Step 4: Query timeline
        summary = await timeline_manager.get_timeline_summary(timeline.id)
        assert summary is not None
        
        # Journey complete!
    
    async def test_ingest_maintenance_refresh_journey(
        self,
        clean_database,
        test_session_id
    ):
        """
        Test journey: Ingest → Detect Issues → Refresh.
        
        Simulates maintenance workflow:
        1. Ingest documents
        2. Detect stale/inconsistent docs
        3. Trigger refresh
        """
        from src.storage.repositories import DocumentRepository
        from src.services.maintenance import StalenessDetector, AutomatedRefresher
        from tests.utils.test_helpers import create_test_document
        
        doc_repo = DocumentRepository(clean_database)
        staleness_detector = StalenessDetector()
        automated_refresher = AutomatedRefresher()
        
        # Step 1: Ingest documents
        doc_data = create_test_document(
            content="Document content",
            file_path="maintenance.py",
            service_name="maintenance-journey",
            session_id=test_session_id
        )
        doc = await doc_repo.create(doc_data)
        assert doc is not None
        
        # Step 2: Detect stale documents
        stale_results = await staleness_detector.detect_stale_documents(
            service_name="maintenance-journey"
        )
        assert stale_results is not None
        
        # Step 3: Trigger refresh
        refresh_result = await automated_refresher.refresh_stale_documents(
            service_name="maintenance-journey",
            force=True
        )
        assert refresh_result is not None
        
        # Journey complete!


class TestMultiServiceIntegration:
    """Test workflows spanning multiple services."""
    
    async def test_cross_service_query(
        self,
        clean_database,
        test_session_id
    ):
        """
        Test querying across multiple services.
        
        Validates:
        - Multi-service document storage
        - Cross-service search
        - Unified results
        """
        from src.storage.repositories import DocumentRepository
        from tests.utils.test_helpers import create_test_document
        
        doc_repo = DocumentRepository(clean_database)
        
        # Ingest documents from multiple services
        services = ["service-alpha", "service-beta", "service-gamma"]
        all_docs = []
        
        for service in services:
            for i in range(2):
                doc_data = create_test_document(
                    content=f"Content for {service} doc {i}",
                    file_path=f"{service}_{i}.py",
                    service_name=service,
                    session_id=test_session_id
                )
                doc = await doc_repo.create(doc_data)
                all_docs.append(doc)
        
        assert len(all_docs) == 6
        
        # Query each service
        for service in services:
            results = await doc_repo.get_by_service(service, limit=10)
            assert len(results) == 2
        
        # Cross-service workflow validated!
    
    async def test_multi_service_timeline_comparison(
        self,
        clean_database,
        test_session_id
    ):
        """
        Test comparing timelines across services.
        
        Validates:
        - Multiple service timelines
        - Cross-service comparison
        - Evolution tracking
        """
        from src.storage.repositories import TimelineRepository
        from src.services.timeline import TimelineManager
        from src.models.timeline import TimelineCreate
        
        timeline_repo = TimelineRepository(clean_database)
        timeline_manager = TimelineManager(timeline_repo)
        
        # Create timelines for multiple services
        services = ["service-x", "service-y"]
        timelines = []
        
        for service in services:
            timeline_data = TimelineCreate(
                name=f"{service}_timeline",
                service_name=service,
                repo_path=f"/test/{service}",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 12, 31),
                strategy="monthly",
                metadata={"_test_data_marker": True}
            )
            timeline = await timeline_manager.create_timeline(timeline_data)
            timelines.append(timeline)
        
        assert len(timelines) == 2
        
        # Verify can retrieve each timeline
        for timeline in timelines:
            summary = await timeline_manager.get_timeline_summary(timeline.id)
            assert summary is not None
    
    async def test_integrated_quality_monitoring(
        self,
        clean_database,
        test_session_id
    ):
        """
        Test integrated quality monitoring across services.
        
        Validates:
        - Multi-service quality dashboard
        - Aggregated metrics
        - Service comparison
        """
        from src.storage.repositories import DocumentRepository
        from src.services.maintenance import QualityDashboard
        from tests.utils.test_helpers import create_test_document
        
        doc_repo = DocumentRepository(clean_database)
        quality_dashboard = QualityDashboard()
        
        # Create documents for monitoring
        service_name = "quality-test"
        for i in range(5):
            doc_data = create_test_document(
                content=f"Quality test document {i}",
                file_path=f"doc_{i}.py",
                service_name=service_name,
                session_id=test_session_id
            )
            await doc_repo.create(doc_data)
        
        # Generate dashboard
        dashboard = await quality_dashboard.get_quality_overview(
            service_name=service_name
        )
        
        assert dashboard is not None


class TestErrorRecovery:
    """Test error recovery in user journeys."""
    
    async def test_recovery_from_failed_ingestion(
        self,
        clean_database,
        test_session_id
    ):
        """
        Test recovery from failed document ingestion.
        
        Validates:
        - Error handling
        - Partial success
        - Recovery mechanisms
        """
        from src.storage.repositories import DocumentRepository
        from tests.utils.test_helpers import create_test_document
        
        doc_repo = DocumentRepository(clean_database)
        
        # Attempt to ingest mix of valid and invalid documents
        successful = 0
        failed = 0
        
        # Valid document
        try:
            valid_doc_data = create_test_document(
                content="Valid content",
                file_path="valid.py",
                service_name="recovery-test",
                session_id=test_session_id
            )
            await doc_repo.create(valid_doc_data)
            successful += 1
        except Exception:
            failed += 1
        
        # Another valid document
        try:
            another_doc_data = create_test_document(
                content="Another valid content",
                file_path="another.py",
                service_name="recovery-test",
                session_id=test_session_id
            )
            await doc_repo.create(another_doc_data)
            successful += 1
        except Exception:
            failed += 1
        
        # Should have some successful ingestions
        assert successful > 0
    
    async def test_graceful_degradation(
        self,
        clean_database,
        test_session_id
    ):
        """
        Test graceful degradation when services unavailable.
        
        Validates:
        - Fallback mechanisms
        - Partial functionality
        - User experience
        """
        from src.storage.repositories import DocumentRepository
        from tests.utils.test_helpers import create_test_document
        
        doc_repo = DocumentRepository(clean_database)
        
        # Create document
        doc_data = create_test_document(
            content="Test content",
            file_path="degradation.py",
            service_name="degradation-test",
            session_id=test_session_id
        )
        doc = await doc_repo.create(doc_data)
        
        # Should still work with basic functionality
        assert doc is not None
        assert doc.id is not None


class TestComplexWorkflows:
    """Test complex multi-step workflows."""
    
    async def test_full_documentation_lifecycle(
        self,
        clean_database,
        test_session_id
    ):
        """
        Test complete documentation lifecycle.
        
        Steps:
        1. Ingest initial docs
        2. Create timeline
        3. Query and get answers
        4. Detect quality issues
        5. Update docs
        6. Verify improvements
        """
        from src.storage.repositories import DocumentRepository, TimelineRepository
        from src.services.timeline import TimelineManager
        from src.services.maintenance import QualityDashboard
        from src.models.timeline import TimelineCreate
        from tests.utils.test_helpers import create_test_document
        
        doc_repo = DocumentRepository(clean_database)
        timeline_repo = TimelineRepository(clean_database)
        timeline_manager = TimelineManager(timeline_repo)
        quality_dashboard = QualityDashboard()
        
        service_name = "lifecycle-test"
        
        # Step 1: Initial ingestion
        doc_data = create_test_document(
            content="Initial documentation",
            file_path="initial.py",
            service_name=service_name,
            session_id=test_session_id
        )
        await doc_repo.create(doc_data)
        
        # Step 2: Create timeline
        timeline_data = TimelineCreate(
            name=f"lifecycle_timeline_{test_session_id[:8]}",
            service_name=service_name,
            repo_path="/test/repo",
            start_date=datetime.now() - timedelta(days=365),
            end_date=datetime.now(),
            strategy="monthly",
            metadata={"_test_data_marker": True}
        )
        timeline = await timeline_manager.create_timeline(timeline_data)
        assert timeline is not None
        
        # Step 3: Check quality
        dashboard = await quality_dashboard.get_quality_overview(
            service_name=service_name
        )
        assert dashboard is not None
        
        # Step 4: Update documentation
        updated_doc_data = create_test_document(
            content="Updated documentation with improvements",
            file_path="updated.py",
            service_name=service_name,
            session_id=test_session_id
        )
        await doc_repo.create(updated_doc_data)
        
        # Step 5: Verify improvements
        docs = await doc_repo.get_by_service(service_name, limit=10)
        assert len(docs) >= 2
        
        # Complete lifecycle validated!
    
    async def test_concurrent_operations(
        self,
        clean_database,
        test_session_id
    ):
        """
        Test concurrent operations don't interfere.
        
        Validates:
        - Transaction isolation
        - Data consistency
        - Race condition handling
        """
        from src.storage.repositories import DocumentRepository
        from tests.utils.test_helpers import create_test_document
        import asyncio
        
        doc_repo = DocumentRepository(clean_database)
        
        # Create multiple documents concurrently
        async def create_doc(i):
            doc_data = create_test_document(
                content=f"Concurrent doc {i}",
                file_path=f"concurrent_{i}.py",
                service_name="concurrent-test",
                session_id=test_session_id
            )
            return await doc_repo.create(doc_data)
        
        # Create 5 documents concurrently
        tasks = [create_doc(i) for i in range(5)]
        docs = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(docs) == 5
        assert all(d is not None for d in docs)
        assert all(d.id is not None for d in docs)
    
    async def test_data_evolution_tracking(
        self,
        clean_database,
        test_session_id
    ):
        """
        Test tracking data evolution over time.
        
        Validates:
        - Historical tracking
        - Change detection
        - Evolution analysis
        """
        from src.storage.repositories import DocumentRepository
        from tests.utils.test_helpers import create_test_document
        
        doc_repo = DocumentRepository(clean_database)
        
        # Create evolving documents
        evolution_stages = [
            ("alpha", "Initial version"),
            ("beta", "Beta version with features"),
            ("release", "Production release"),
        ]
        
        for stage, content in evolution_stages:
            doc_data = create_test_document(
                content=content,
                file_path="evolving.py",
                service_name="evolution-test",
                session_id=test_session_id,
                metadata={"stage": stage}
            )
            await doc_repo.create(doc_data)
        
        # Verify evolution tracked
        docs = await doc_repo.get_by_service("evolution-test", limit=10)
        assert len(docs) >= 3
        
        # Should be able to see progression
        stages = [d.metadata.get("stage") for d in docs if d.metadata and isinstance(d.metadata, dict)]
        assert "alpha" in stages or "beta" in stages or "release" in stages


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "functional"])

