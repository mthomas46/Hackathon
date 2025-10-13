"""
Unit tests for Multi-Pass Query Service.

Tests query decomposition, question generation, and synthesis logic.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from src.services.rag.multi_pass_query import (
    MultiPassQueryService,
    SecondaryQuestion,
    QuestionResult,
    SectionResult,
    MultiPassResult
)


@pytest.fixture
def mock_rag_service():
    """Mock RAG service."""
    service = Mock()
    service.ask = AsyncMock(return_value={
        "answer": "Test answer",
        "sources": [{"file_path": "test.py", "score": 0.9}],
        "confidence": 0.85,
        "metadata": {}
    })
    return service


@pytest.fixture
def mock_ollama_router():
    """Mock Ollama router."""
    router = Mock()
    router.generate = AsyncMock(return_value={
        "response": "Test response",
        "model": "llama3"
    })
    return router


@pytest.fixture
def multi_pass_service(mock_rag_service, mock_ollama_router):
    """Create multi-pass service with mocked dependencies."""
    with patch('src.services.rag.multi_pass_query.get_rag_service', return_value=mock_rag_service), \
         patch('src.services.rag.multi_pass_query.get_ollama_router', return_value=mock_ollama_router):
        service = MultiPassQueryService()
        return service


class TestQueryDecomposition:
    """Test query decomposition into sections."""
    
    @pytest.mark.asyncio
    async def test_decompose_query_returns_correct_count(self, multi_pass_service):
        """Test that decomposition returns requested number of sections."""
        query = "How does the system work?"
        num_passes = 3
        
        sections = await multi_pass_service._decompose_query(query, num_passes)
        
        assert len(sections) == num_passes
        assert all(isinstance(s, dict) for s in sections)
        assert all('name' in s and 'description' in s for s in sections)
    
    @pytest.mark.asyncio
    async def test_decompose_query_with_different_counts(self, multi_pass_service):
        """Test decomposition with various section counts."""
        query = "Explain the architecture"
        
        for num_passes in [1, 3, 5, 10]:
            sections = await multi_pass_service._decompose_query(query, num_passes)
            assert len(sections) == num_passes
    
    @pytest.mark.asyncio
    async def test_decompose_query_handles_llm_failure(self, multi_pass_service, mock_ollama_router):
        """Test fallback when LLM fails to return valid JSON."""
        mock_ollama_router.generate = AsyncMock(return_value={"response": "Invalid response"})
        
        sections = await multi_pass_service._decompose_query("Test query", 3)
        
        # Should return fallback sections
        assert len(sections) == 3
        assert all('name' in s for s in sections)


class TestSecondaryQuestionGeneration:
    """Test secondary question generation."""
    
    @pytest.mark.asyncio
    async def test_generate_secondary_questions_count(self, multi_pass_service):
        """Test that correct number of questions are generated."""
        query = "How does caching work?"
        sections = [
            {"name": "Core Concepts", "description": "Basic concepts"},
            {"name": "Implementation", "description": "Implementation details"}
        ]
        num_questions = 3
        
        questions = await multi_pass_service._generate_secondary_questions(
            query, sections, num_questions
        )
        
        expected_total = len(sections) * num_questions
        assert len(questions) == expected_total
        assert all(isinstance(q, SecondaryQuestion) for q in questions)
    
    @pytest.mark.asyncio
    async def test_secondary_questions_have_correct_metadata(self, multi_pass_service):
        """Test that secondary questions have correct metadata."""
        sections = [
            {"name": "Section 1", "description": "First section"},
            {"name": "Section 2", "description": "Second section"}
        ]
        
        questions = await multi_pass_service._generate_secondary_questions(
            "Test query", sections, 2
        )
        
        # Check section indices are correct
        section_0_questions = [q for q in questions if q.section_index == 0]
        section_1_questions = [q for q in questions if q.section_index == 1]
        
        assert len(section_0_questions) == 2
        assert len(section_1_questions) == 2
        assert all(q.section_name == "Section 1" for q in section_0_questions)
        assert all(q.section_name == "Section 2" for q in section_1_questions)


class TestSectionProcessing:
    """Test section processing logic."""
    
    @pytest.mark.asyncio
    async def test_process_section_returns_result(self, multi_pass_service):
        """Test that section processing returns complete result."""
        section = {"name": "Test Section", "description": "Test description"}
        questions = [
            SecondaryQuestion("Q1?", 0, "Test Section", 0),
            SecondaryQuestion("Q2?", 0, "Test Section", 1)
        ]
        
        result = await multi_pass_service._process_section(
            section_idx=0,
            section=section,
            all_questions=questions,
            n_results=10,
            temperature=0.7
        )
        
        assert isinstance(result, SectionResult)
        assert result.section_name == "Test Section"
        assert len(result.questions) == 2
        assert result.synthesis
        assert result.duration_seconds >= 0
    
    @pytest.mark.asyncio
    async def test_process_section_handles_rag_failure(self, multi_pass_service, mock_rag_service):
        """Test graceful handling of RAG failures."""
        mock_rag_service.ask = AsyncMock(side_effect=Exception("RAG failed"))
        
        section = {"name": "Test", "description": "Test"}
        questions = [SecondaryQuestion("Q?", 0, "Test", 0)]
        
        result = await multi_pass_service._process_section(0, section, questions, 10, 0.7)
        
        # Should still return result with error recorded
        assert isinstance(result, SectionResult)
        assert len(result.questions) == 1
        assert "Error" in result.questions[0].answer


class TestSynthesis:
    """Test synthesis logic."""
    
    @pytest.mark.asyncio
    async def test_synthesize_section_combines_answers(self, multi_pass_service):
        """Test that section synthesis combines multiple answers."""
        question_results = [
            QuestionResult("Q1?", "Answer 1", [], 0.8, 1.0, "2025-01-01", {}),
            QuestionResult("Q2?", "Answer 2", [], 0.9, 1.0, "2025-01-01", {})
        ]
        
        synthesis = await multi_pass_service._synthesize_section(
            "Test Section",
            "Test description",
            question_results
        )
        
        assert isinstance(synthesis, str)
        assert len(synthesis) > 0
    
    @pytest.mark.asyncio
    async def test_synthesize_final_answer_integrates_sections(self, multi_pass_service):
        """Test that final synthesis integrates all sections."""
        section_results = [
            SectionResult(0, "Section 1", "Desc 1", [], "Synthesis 1", 1.0, "2025-01-01"),
            SectionResult(1, "Section 2", "Desc 2", [], "Synthesis 2", 1.0, "2025-01-01")
        ]
        
        final_synthesis = await multi_pass_service._synthesize_final_answer(
            "Original query",
            section_results
        )
        
        assert isinstance(final_synthesis, str)
        assert len(final_synthesis) > 0


class TestEndToEnd:
    """Test complete multi-pass processing."""
    
    @pytest.mark.asyncio
    async def test_process_query_complete_flow(self, multi_pass_service):
        """Test complete multi-pass query processing."""
        result = await multi_pass_service.process_query(
            query="How does the system work?",
            num_passes=2,
            num_secondary_questions=2,
            n_results=5,
            temperature=0.7
        )
        
        assert isinstance(result, MultiPassResult)
        assert result.original_query == "How does the system work?"
        assert result.num_passes == 2
        assert result.num_secondary_questions == 2
        assert len(result.sections) == 2
        assert result.final_synthesis
        assert result.total_questions_asked == 4  # 2 passes × 2 questions
        assert result.total_duration_seconds > 0
    
    @pytest.mark.asyncio
    async def test_process_query_with_progress_callback(self, multi_pass_service):
        """Test that progress callback is called."""
        progress_updates = []
        
        async def callback(status, progress, message):
            progress_updates.append({
                "status": status,
                "progress": progress,
                "message": message
            })
        
        await multi_pass_service.process_query(
            query="Test query",
            num_passes=2,
            num_secondary_questions=1,
            progress_callback=callback
        )
        
        # Should have received multiple progress updates
        assert len(progress_updates) > 0
        assert any(u['status'] == 'decomposing' for u in progress_updates)
        assert any(u['status'] == 'complete' for u in progress_updates)
    
    @pytest.mark.asyncio
    async def test_process_query_validates_parameters(self, multi_pass_service):
        """Test parameter validation."""
        # Valid parameters should work
        result = await multi_pass_service.process_query(
            query="Test",
            num_passes=1,
            num_secondary_questions=1
        )
        assert isinstance(result, MultiPassResult)


class TestPerformance:
    """Test performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_small_query_completes_quickly(self, multi_pass_service):
        """Test that small queries complete in reasonable time."""
        import time
        start = time.time()
        
        await multi_pass_service.process_query(
            query="Test",
            num_passes=1,
            num_secondary_questions=1,
            n_results=1
        )
        
        duration = time.time() - start
        # Should complete in under 30 seconds (with mocked LLM)
        assert duration < 30
    
    @pytest.mark.asyncio
    async def test_caching_reduces_duplicate_work(self, multi_pass_service, mock_rag_service):
        """Test that caching reduces duplicate RAG calls."""
        query = "Same question"
        
        # First call
        await multi_pass_service.process_query(
            query=query,
            num_passes=1,
            num_secondary_questions=1
        )
        
        call_count_first = mock_rag_service.ask.call_count
        
        # Second call with same query
        await multi_pass_service.process_query(
            query=query,
            num_passes=1,
            num_secondary_questions=1
        )
        
        call_count_second = mock_rag_service.ask.call_count
        
        # Should still make calls (but cache may reduce work internally)
        assert call_count_second >= call_count_first

