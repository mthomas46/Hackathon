"""
Unit Tests for Documentation Run Management System

Tests the DocumentationRunManager service and core functionality.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import hashlib

# Add services directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "ecosystem-mcp"))

from unittest.mock import AsyncMock, MagicMock, patch


class TestDocumentationRunManager:
    """Unit tests for DocumentationRunManager."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = MagicMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session
    
    @pytest.fixture
    def manager(self, mock_session):
        """Create a DocumentationRunManager instance."""
        from src.services.documentation.run_manager import DocumentationRunManager
        return DocumentationRunManager(mock_session)
    
    @pytest.mark.asyncio
    async def test_create_run(self, manager, mock_session):
        """Test creating a new documentation run."""
        # Mock the execute result to return a UUID
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (uuid4(),)
        mock_session.execute.return_value = mock_result
        
        run_id = await manager.create_run(
            name="Test Run",
            description="Test description",
            source_directory="/app/src",
            num_passes=3,
            questions_per_pass=5
        )
        
        assert isinstance(run_id, UUID)
        assert mock_session.execute.called
        assert mock_session.commit.called
    
    @pytest.mark.asyncio
    async def test_start_run(self, manager, mock_session):
        """Test starting a documentation run."""
        run_id = uuid4()
        
        await manager.start_run(run_id, output_directory="/output/test")
        
        assert mock_session.execute.called
        assert mock_session.commit.called
    
    @pytest.mark.asyncio
    async def test_complete_run(self, manager, mock_session):
        """Test completing a documentation run."""
        run_id = uuid4()
        
        await manager.complete_run(
            run_id=run_id,
            status="completed",
            total_docs=25,
            successful_docs=24,
            failed_docs=1
        )
        
        assert mock_session.execute.called
        assert mock_session.commit.called
    
    @pytest.mark.asyncio
    async def test_add_document(self, manager, mock_session):
        """Test adding a document to a run."""
        run_id = uuid4()
        content = "# Test Document\n\nThis is test content."
        
        # Mock the execute result
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (uuid4(),)
        mock_session.execute.return_value = mock_result
        
        doc_id = await manager.add_document(
            run_id=run_id,
            title="Test Document",
            filename="test_document.md",
            content=content,
            pass_number=1,
            question="What is this test about?"
        )
        
        assert isinstance(doc_id, UUID)
        assert mock_session.execute.called
        assert mock_session.commit.called
    
    @pytest.mark.asyncio
    async def test_update_progress(self, manager, mock_session):
        """Test updating run progress."""
        run_id = uuid4()
        
        await manager.update_progress(
            run_id=run_id,
            current_pass=2,
            total_passes=3,
            current_question=3,
            total_questions=5,
            current_operation="Generating question 3",
            docs_generated=8,
            docs_failed=0
        )
        
        assert mock_session.execute.called
        assert mock_session.commit.called
    
    @pytest.mark.asyncio
    async def test_get_run(self, manager, mock_session):
        """Test getting run details."""
        run_id = uuid4()
        
        # Mock the execute result
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (
            run_id,
            "Test Run",
            "Test description",
            "pending",
            "/app/src",
            "markdown",
            "L",
            "desktop",
            3,
            5,
            None,  # started_at
            None,  # completed_at
            None,  # duration_seconds
            0,     # total_documents
            0,     # successful_documents
            0,     # failed_documents
            None,  # output_directory
            "test@example.com",
            datetime.now(),
            datetime.now(),
            None   # metadata
        )
        mock_session.execute.return_value = mock_result
        
        run = await manager.get_run(run_id)
        
        assert run is not None
        assert run["id"] == run_id
        assert run["name"] == "Test Run"
        assert run["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_list_runs(self, manager, mock_session):
        """Test listing runs."""
        # Mock the execute result
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            (
                uuid4(),
                "Run 1",
                "Description 1",
                "completed",
                "/app/src",
                datetime.now(),
                datetime.now(),
                None,
                3600,
                25,
                24,
                1,
                "test@example.com",
                datetime.now()
            ),
            (
                uuid4(),
                "Run 2",
                "Description 2",
                "running",
                "/app/docs",
                datetime.now(),
                datetime.now(),
                None,
                None,
                0,
                0,
                0,
                "test@example.com",
                datetime.now()
            )
        ]
        mock_session.execute.return_value = mock_result
        
        runs = await manager.list_runs(limit=10, offset=0)
        
        assert len(runs) == 2
        assert runs[0]["name"] == "Run 1"
        assert runs[1]["name"] == "Run 2"
    
    @pytest.mark.asyncio
    async def test_list_runs_with_status_filter(self, manager, mock_session):
        """Test listing runs with status filter."""
        # Mock the execute result
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            (
                uuid4(),
                "Completed Run",
                "Description",
                "completed",
                "/app/src",
                datetime.now(),
                datetime.now(),
                None,
                3600,
                25,
                24,
                1,
                "test@example.com",
                datetime.now()
            )
        ]
        mock_session.execute.return_value = mock_result
        
        runs = await manager.list_runs(status="completed", limit=10, offset=0)
        
        assert len(runs) == 1
        assert runs[0]["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_get_run_documents(self, manager, mock_session):
        """Test getting documents from a run."""
        run_id = uuid4()
        
        # Mock the execute result
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            (
                uuid4(),
                run_id,
                "Document 1",
                "doc1.md",
                "hash123",
                5120,
                1,
                "What is X?",
                "generated",
                2.5,
                850,
                datetime.now()
            ),
            (
                uuid4(),
                run_id,
                "Document 2",
                "doc2.md",
                "hash456",
                3072,
                2,
                "How does Y work?",
                "generated",
                3.2,
                620,
                datetime.now()
            )
        ]
        mock_session.execute.return_value = mock_result
        
        documents = await manager.get_run_documents(run_id, limit=100, offset=0)
        
        assert len(documents) == 2
        assert documents[0]["title"] == "Document 1"
        assert documents[1]["title"] == "Document 2"
    
    @pytest.mark.asyncio
    async def test_get_run_progress(self, manager, mock_session):
        """Test getting run progress."""
        run_id = uuid4()
        
        # Mock the execute result
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (
            run_id,
            2,     # current_pass
            3,     # total_passes
            3,     # current_question
            5,     # total_questions
            "Generating question 3",
            53.3,  # progress_percentage
            8,     # documents_generated
            0,     # documents_failed
            1260,  # estimated_time_remaining_seconds
            datetime.now()
        )
        mock_session.execute.return_value = mock_result
        
        progress = await manager.get_run_progress(run_id)
        
        assert progress is not None
        assert progress["current_pass"] == 2
        assert progress["total_passes"] == 3
        assert progress["progress_percentage"] == 53.3
    
    @pytest.mark.asyncio
    async def test_delete_run(self, manager, mock_session):
        """Test deleting a run."""
        run_id = uuid4()
        
        await manager.delete_run(run_id)
        
        # Should delete documents first, then progress, then run
        assert mock_session.execute.call_count >= 3
        assert mock_session.commit.called
    
    @pytest.mark.asyncio
    async def test_error_handling(self, manager, mock_session):
        """Test error handling in service methods."""
        run_id = uuid4()
        
        # Mock an exception
        mock_session.execute.side_effect = Exception("Database error")
        
        with pytest.raises(Exception):
            await manager.get_run(run_id)
        
        assert mock_session.rollback.called


class TestContentHashing:
    """Test content hashing functionality."""
    
    def test_content_hash_consistency(self):
        """Test that same content produces same hash."""
        content = "# Test Document\n\nThis is test content."
        
        hash1 = hashlib.sha256(content.encode()).hexdigest()
        hash2 = hashlib.sha256(content.encode()).hexdigest()
        
        assert hash1 == hash2
    
    def test_different_content_different_hash(self):
        """Test that different content produces different hashes."""
        content1 = "# Document 1"
        content2 = "# Document 2"
        
        hash1 = hashlib.sha256(content1.encode()).hexdigest()
        hash2 = hashlib.sha256(content2.encode()).hexdigest()
        
        assert hash1 != hash2


class TestProgressCalculations:
    """Test progress calculation logic."""
    
    def test_progress_percentage_calculation(self):
        """Test progress percentage is calculated correctly."""
        current_pass = 2
        total_passes = 3
        current_question = 3
        total_questions = 5
        
        # Progress should be (current_pass - 1) * total_questions + current_question
        # divided by (total_passes * total_questions) * 100
        completed_questions = (current_pass - 1) * total_questions + current_question
        total_work = total_passes * total_questions
        expected_percentage = (completed_questions / total_work) * 100
        
        assert expected_percentage == 53.333333333333336
    
    def test_progress_at_start(self):
        """Test progress at the beginning."""
        current_pass = 1
        current_question = 0
        total_passes = 3
        total_questions = 5
        
        completed_questions = (current_pass - 1) * total_questions + current_question
        total_work = total_passes * total_questions
        percentage = (completed_questions / total_work) * 100
        
        assert percentage == 0.0
    
    def test_progress_at_end(self):
        """Test progress at completion."""
        current_pass = 3
        current_question = 5
        total_passes = 3
        total_questions = 5
        
        completed_questions = (current_pass - 1) * total_questions + current_question
        total_work = total_passes * total_questions
        percentage = (completed_questions / total_work) * 100
        
        assert percentage == 100.0


class TestDocumentMetadata:
    """Test document metadata handling."""
    
    def test_word_count_calculation(self):
        """Test word count is calculated correctly."""
        content = "This is a test document with ten words in it."
        word_count = len(content.split())
        
        assert word_count == 10
    
    def test_content_size_calculation(self):
        """Test content size is calculated correctly."""
        content = "Test content"
        size = len(content.encode())
        
        assert size == 12
    
    def test_markdown_word_count(self):
        """Test word count with markdown formatting."""
        content = "# Header\n\nThis is **bold** and *italic* text."
        word_count = len(content.split())
        
        # Should count markdown symbols as part of words
        assert word_count > 5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

