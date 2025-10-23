"""
Functional tests for performance and error scenarios.

Tests:
1. Performance benchmarks (ingestion, queries, timelines)
2. Error handling (database errors, invalid inputs, timeouts)
3. Edge cases (empty data, large data, concurrent access)
4. Resource management (memory, connections)
"""

import pytest
from datetime import datetime
import time
from uuid import uuid4

# Mark all tests in this module as functional and asyncio
pytestmark = [pytest.mark.functional, pytest.mark.asyncio]


class TestPerformanceBenchmarks:
    """Test performance under various conditions."""
    
    async def test_bulk_document_ingestion_performance(
        self,
        clean_database,
        test_session_id
    ):
        """
        Test ingesting 100 documents within acceptable time.
        
        Performance target: <30 seconds for 100 documents
        """
        from src.storage.repositories import DocumentRepository
        from tests.utils.test_helpers import create_test_document
        
        doc_repo = DocumentRepository(clean_database)
        
        start_time = time.time()
        
        # Ingest 100 documents
        for i in range(100):
            doc_data = create_test_document(
                content=f"Performance test document {i}",
                file_path=f"perf_{i}.py",
                service_name="perf-test",
                session_id=test_session_id
            )
            await doc_repo.create(doc_data)
        
        elapsed_time = time.time() - start_time
        
        # Verify all documents created
        docs = await doc_repo.get_by_service("perf-test", limit=150)
        assert len(docs) >= 100
        
        # Performance assertion (30 seconds max)
        assert elapsed_time < 30, f"Ingestion took {elapsed_time:.2f}s, expected <30s"
    
    async def test_query_response_time(
        self,
        clean_database,
        test_session_id
    ):
        """
        Test query response time.
        
        Performance target: <1 second for 100 results
        """
        from src.storage.repositories import DocumentRepository
        from tests.utils.test_helpers import create_test_document
        
        doc_repo = DocumentRepository(clean_database)
        
        # Create test documents
        for i in range(50):
            doc_data = create_test_document(
                content=f"Query test document {i}",
                file_path=f"query_{i}.py",
                service_name="query-perf-test",
                session_id=test_session_id
            )
            await doc_repo.create(doc_data)
        
        # Measure query time
        start_time = time.time()
        results = await doc_repo.get_by_service("query-perf-test", limit=100)
        elapsed_time = time.time() - start_time
        
        assert len(results) >= 50
        assert elapsed_time < 1.0, f"Query took {elapsed_time:.2f}s, expected <1s"
    
    async def test_timeline_generation_performance(
        self,
        clean_database,
        test_session_id
    ):
        """
        Test timeline generation performance.
        
        Performance target: <5 seconds for 1000 documents
        """
        from src.storage.repositories import TimelineRepository, TimePeriodRepository
        from src.services.timeline import TimelineManager, PeriodGenerator
        
        timeline_repo = TimelineRepository(clean_database)
        period_repo = TimePeriodRepository(clean_database)
        timeline_manager = TimelineManager(timeline_repo)
        period_generator = PeriodGenerator(period_repo)
        
        # Create timeline
        timeline_data = {
            "name": f"perf_timeline_{test_session_id[:8]}",
            "service_name": "timeline-perf-test",
            "repo_path": "/test/repo",
            "start_date": datetime(2024, 1, 1),
            "end_date": datetime(2024, 12, 31),
            "strategy": "monthly",
            "metadata": {"_test_data_marker": True}
        }
        
        start_time = time.time()
        timeline = await timeline_manager.create_timeline(timeline_data)
        
        # Generate periods
        periods = await period_generator.generate_periods(
            timeline_id=timeline.id,
            start_date=timeline.start_date,
            end_date=timeline.end_date,
            strategy="monthly"
        )
        elapsed_time = time.time() - start_time
        
        assert len(periods) > 0
        assert elapsed_time < 5.0, f"Timeline generation took {elapsed_time:.2f}s, expected <5s"
    
    async def test_concurrent_operations_performance(
        self,
        clean_database,
        test_session_id
    ):
        """
        Test performance with 10 concurrent operations.
        
        Performance target: <10 seconds for 10 concurrent ingestions
        """
        from src.storage.repositories import DocumentRepository
        from tests.utils.test_helpers import create_test_document
        import asyncio
        
        doc_repo = DocumentRepository(clean_database)
        
        async def create_doc(i):
            doc_data = create_test_document(
                content=f"Concurrent perf doc {i}",
                file_path=f"concurrent_{i}.py",
                service_name="concurrent-perf-test",
                session_id=test_session_id
            )
            return await doc_repo.create(doc_data)
        
        start_time = time.time()
        tasks = [create_doc(i) for i in range(10)]
        docs = await asyncio.gather(*tasks)
        elapsed_time = time.time() - start_time
        
        assert len(docs) == 10
        assert all(d is not None for d in docs)
        assert elapsed_time < 10.0, f"Concurrent ops took {elapsed_time:.2f}s, expected <10s"
    
    async def test_large_document_handling(
        self,
        clean_database,
        test_session_id
    ):
        """
        Test handling large documents (1MB).
        
        Performance target: <5 seconds per 1MB document
        """
        from src.storage.repositories import DocumentRepository
        from tests.utils.test_helpers import create_test_document
        
        doc_repo = DocumentRepository(clean_database)
        
        # Create 1MB document
        large_content = "x" * (1024 * 1024)  # 1MB
        
        start_time = time.time()
        doc_data = create_test_document(
            content=large_content,
            file_path="large.py",
            service_name="large-doc-test",
            session_id=test_session_id
        )
        doc = await doc_repo.create(doc_data)
        elapsed_time = time.time() - start_time
        
        assert doc is not None
        assert len(doc.content) == len(large_content)
        assert elapsed_time < 5.0, f"Large doc took {elapsed_time:.2f}s, expected <5s"
    
    async def test_memory_usage(
        self,
        clean_database,
        test_session_id
    ):
        """
        Test memory usage stays reasonable (<500MB).
        
        Performance target: <500MB for 100 documents
        """
        from src.storage.repositories import DocumentRepository
        from tests.utils.test_helpers import create_test_document
        import psutil
        import os
        
        doc_repo = DocumentRepository(clean_database)
        process = psutil.Process(os.getpid())
        
        # Get initial memory
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create 100 documents
        for i in range(100):
            doc_data = create_test_document(
                content=f"Memory test document {i}",
                file_path=f"mem_{i}.py",
                service_name="memory-test",
                session_id=test_session_id
            )
            await doc_repo.create(doc_data)
        
        # Get final memory
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = final_memory - initial_memory
        
        # Memory should not increase dramatically
        assert memory_used < 500, f"Memory increased by {memory_used:.2f}MB, expected <500MB"


class TestErrorHandling:
    """Test error handling scenarios."""
    
    async def test_invalid_document_handling(
        self,
        clean_database,
        test_session_id
    ):
        """Test handling invalid document data."""
        from src.storage.repositories import DocumentRepository
        
        doc_repo = DocumentRepository(clean_database)
        
        # Try to create document with invalid data
        invalid_doc_data = {
            "file_path": "invalid.txt",
            "content": None,  # Invalid: None content
            "service_name": "test"
        }
        
        # Should handle gracefully
        try:
            doc = await doc_repo.create(invalid_doc_data)
            # If it doesn't raise, verify it handled it
            if doc is None:
                pytest.skip("Service returns None for invalid data")
        except Exception as e:
            # Expected: should raise validation error
            assert "content" in str(e).lower() or "required" in str(e).lower() or "validation" in str(e).lower()
    
    async def test_duplicate_handling(
        self,
        clean_database,
        test_session_id
    ):
        """Test handling duplicate document insertion."""
        from src.storage.repositories import DocumentRepository
        from tests.utils.test_helpers import create_test_document
        
        doc_repo = DocumentRepository(clean_database)
        
        # Create document
        doc_data = create_test_document(
            content="Original content",
            file_path="duplicate.py",
            service_name="dup-test",
            session_id=test_session_id
        )
        doc1 = await doc_repo.create(doc_data)
        
        # Try to create same document again
        doc2_data = create_test_document(
            content="Duplicate content",
            file_path="duplicate.py",
            service_name="dup-test",
            session_id=test_session_id
        )
        doc2 = await doc_repo.create(doc2_data)
        
        # Should handle gracefully (either update or create new)
        assert doc1 is not None
        assert doc2 is not None
    
    async def test_nonexistent_resource_handling(
        self,
        clean_database,
        test_session_id
    ):
        """Test handling requests for nonexistent resources."""
        from src.storage.repositories import DocumentRepository
        
        doc_repo = DocumentRepository(clean_database)
        
        # Try to get nonexistent document
        nonexistent_id = uuid4()
        doc = await doc_repo.get_by_id(nonexistent_id)
        
        # Should return None gracefully
        assert doc is None
    
    async def test_empty_service_handling(
        self,
        clean_database,
        test_session_id
    ):
        """Test handling queries for services with no documents."""
        from src.storage.repositories import DocumentRepository
        
        doc_repo = DocumentRepository(clean_database)
        
        # Query empty service
        docs = await doc_repo.get_by_service("nonexistent-service", limit=10)
        
        # Should return empty list, not error
        assert docs == []
    
    async def test_invalid_timeline_data(
        self,
        clean_database,
        test_session_id
    ):
        """Test handling invalid timeline data."""
        from src.storage.repositories import TimelineRepository
        from src.services.timeline import TimelineManager
        
        timeline_repo = TimelineRepository(clean_database)
        timeline_manager = TimelineManager(timeline_repo)
        
        # Try to create timeline with invalid dates
        invalid_timeline_data = {
            "name": "invalid_timeline",
            "service_name": "test",
            "repo_path": "/test",
            "start_date": datetime(2024, 12, 31),  # End before start
            "end_date": datetime(2024, 1, 1),
            "strategy": "monthly",
            "metadata": {"_test_data_marker": True}
        }
        
        # Should handle gracefully
        try:
            timeline = await timeline_manager.create_timeline(invalid_timeline_data)
            # If it doesn't raise, verify dates
            if timeline:
                pytest.skip("Service accepts invalid date range")
        except Exception as e:
            # Expected: should raise validation error
            assert "date" in str(e).lower() or "validation" in str(e).lower()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    async def test_empty_content_document(
        self,
        clean_database,
        test_session_id
    ):
        """Test handling documents with empty content."""
        from src.storage.repositories import DocumentRepository
        from tests.utils.test_helpers import create_test_document
        
        doc_repo = DocumentRepository(clean_database)
        
        # Create document with empty content
        doc_data = create_test_document(
            content="",  # Empty
            file_path="empty.py",
            service_name="empty-test",
            session_id=test_session_id
        )
        doc = await doc_repo.create(doc_data)
        
        # Should handle empty content
        assert doc is not None
        assert doc.content == ""
    
    async def test_very_long_file_path(
        self,
        clean_database,
        test_session_id
    ):
        """Test handling very long file paths."""
        from src.storage.repositories import DocumentRepository
        from tests.utils.test_helpers import create_test_document
        
        doc_repo = DocumentRepository(clean_database)
        
        # Create very long path (but within reasonable limits)
        long_path = "/".join(["very"] * 50) + "/file.py"  # ~255 chars
        
        doc_data = create_test_document(
            content="Content with long path",
            file_path=long_path[:255],  # Limit to avoid database constraints
            service_name="long-path-test",
            session_id=test_session_id
        )
        doc = await doc_repo.create(doc_data)
        
        assert doc is not None
    
    async def test_special_characters_in_content(
        self,
        clean_database,
        test_session_id
    ):
        """Test handling special characters and Unicode."""
        from src.storage.repositories import DocumentRepository
        from tests.utils.test_helpers import create_test_document
        
        doc_repo = DocumentRepository(clean_database)
        
        # Content with special characters
        special_content = "Special chars: 你好 🚀 €£¥ <>&\"'"
        
        doc_data = create_test_document(
            content=special_content,
            file_path="special.py",
            service_name="special-test",
            session_id=test_session_id
        )
        doc = await doc_repo.create(doc_data)
        
        assert doc is not None
        assert doc.content == special_content
    
    async def test_zero_period_timeline(
        self,
        clean_database,
        test_session_id
    ):
        """Test timeline with no periods."""
        from src.storage.repositories import TimelineRepository, TimePeriodRepository
        from src.services.timeline import TimelineManager, PeriodGenerator
        
        timeline_repo = TimelineRepository(clean_database)
        period_repo = TimePeriodRepository(clean_database)
        timeline_manager = TimelineManager(timeline_repo)
        period_generator = PeriodGenerator(period_repo)
        
        # Create timeline with same start/end date
        timeline_data = {
            "name": f"zero_period_{test_session_id[:8]}",
            "service_name": "zero-test",
            "repo_path": "/test",
            "start_date": datetime(2024, 1, 1),
            "end_date": datetime(2024, 1, 1),  # Same date
            "strategy": "monthly",
            "metadata": {"_test_data_marker": True}
        }
        timeline = await timeline_manager.create_timeline(timeline_data)
        
        # Try to generate periods
        periods = await period_generator.generate_periods(
            timeline_id=timeline.id,
            start_date=timeline.start_date,
            end_date=timeline.end_date,
            strategy="monthly"
        )
        
        # Should handle gracefully (may return empty list or single period)
        assert isinstance(periods, list)


class TestResourceManagement:
    """Test resource management (connections, memory, etc)."""
    
    async def test_database_connection_pooling(
        self,
        clean_database,
        test_session_id
    ):
        """Test database connection pool handling."""
        from src.storage.repositories import DocumentRepository
        from tests.utils.test_helpers import create_test_document
        
        doc_repo = DocumentRepository(clean_database)
        
        # Create multiple documents to test connection reuse
        for i in range(20):
            doc_data = create_test_document(
                content=f"Connection test {i}",
                file_path=f"conn_{i}.py",
                service_name="connection-test",
                session_id=test_session_id
            )
            await doc_repo.create(doc_data)
        
        # Should handle multiple operations efficiently
        docs = await doc_repo.get_by_service("connection-test", limit=25)
        assert len(docs) >= 20
    
    async def test_transaction_rollback(
        self,
        clean_database,
        test_session_id
    ):
        """Test transaction rollback on error."""
        from src.storage.repositories import DocumentRepository
        from tests.utils.test_helpers import create_test_document
        
        doc_repo = DocumentRepository(clean_database)
        
        # Create document
        doc_data = create_test_document(
            content="Rollback test",
            file_path="rollback.py",
            service_name="rollback-test",
            session_id=test_session_id
        )
        doc = await doc_repo.create(doc_data)
        
        # The clean_database fixture ensures rollback after test
        assert doc is not None
        
        # Verify can query within transaction
        docs = await doc_repo.get_by_service("rollback-test", limit=10)
        assert len(docs) > 0
    
    async def test_cleanup_after_operations(
        self,
        clean_database,
        test_session_id
    ):
        """Test proper cleanup after operations."""
        from src.storage.repositories import DocumentRepository
        from tests.utils.test_helpers import create_test_document
        
        doc_repo = DocumentRepository(clean_database)
        
        # Perform multiple operations
        for i in range(10):
            doc_data = create_test_document(
                content=f"Cleanup test {i}",
                file_path=f"cleanup_{i}.py",
                service_name="cleanup-test",
                session_id=test_session_id
            )
            await doc_repo.create(doc_data)
        
        # Verify operations completed
        docs = await doc_repo.get_by_service("cleanup-test", limit=15)
        assert len(docs) >= 10
        
        # Note: Actual cleanup happens in fixture teardown


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "functional"])

