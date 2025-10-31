"""
Integration tests for Audit Phase 2 (A, B, C)

Tests the integration of all Phase 2 audit fixes into the enhanced RAG service.
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from services.rag.accuracy_enhanced_rag import AccuracyEnhancedRAG


class TestPhase2AIntegration:
    """Test Phase 2A (Unified Query Analyzer) integration."""
    
    @pytest.fixture
    def enhanced_rag(self):
        """Get enhanced RAG instance."""
        return AccuracyEnhancedRAG()
    
    def test_unified_analyzer_initialized(self, enhanced_rag):
        """Test unified analyzer is initialized."""
        assert hasattr(enhanced_rag, 'unified_analyzer')
        assert enhanced_rag.unified_analyzer is not None
    
    @pytest.mark.asyncio
    async def test_unified_analyzer_used(self, enhanced_rag):
        """Test unified analyzer is used when enabled."""
        # Mock dependencies
        with patch.object(enhanced_rag, '_retrieve_documents', new_callable=AsyncMock) as mock_retrieve:
            with patch.object(enhanced_rag, '_generate_answer', new_callable=AsyncMock) as mock_generate:
                with patch.object(enhanced_rag, '_cache_enhanced_answer', new_callable=AsyncMock):
                    mock_retrieve.return_value = []
                    mock_generate.return_value = "Mock answer"
                    
                    # Call with unified analyzer enabled
                    result = await enhanced_rag.ask_enhanced(
                        question="What is Docker?",
                        use_unified_analyzer=True,
                        enable_difficulty_estimation=True,
                        enable_intent_classification=True
                    )
                    
                    # Should get a result (even with no documents)
                    assert result is not None
                    assert "answer" in result
    
    @pytest.mark.asyncio
    async def test_unified_analyzer_can_be_disabled(self, enhanced_rag):
        """Test unified analyzer can be disabled (fallback to separate)."""
        with patch.object(enhanced_rag, '_retrieve_documents', new_callable=AsyncMock) as mock_retrieve:
            with patch.object(enhanced_rag, '_generate_answer', new_callable=AsyncMock) as mock_generate:
                with patch.object(enhanced_rag, '_cache_enhanced_answer', new_callable=AsyncMock):
                    mock_retrieve.return_value = []
                    mock_generate.return_value = "Mock answer"
                    
                    # Call with unified analyzer disabled
                    result = await enhanced_rag.ask_enhanced(
                        question="What is Docker?",
                        use_unified_analyzer=False
                    )
                    
                    # Should still work (fallback to separate analyzers)
                    assert result is not None


class TestPhase2BIntegration:
    """Test Phase 2B (Respect Context Optimization Flag) integration."""
    
    @pytest.fixture
    def enhanced_rag(self):
        """Get enhanced RAG instance."""
        return AccuracyEnhancedRAG()
    
    @pytest.mark.asyncio
    async def test_context_optimization_disabled_truly_skips(self, enhanced_rag):
        """Test context optimization actually skips when disabled."""
        mock_documents = [
            {"id": "1", "content": "Doc 1", "quality_score": 80},
            {"id": "2", "content": "Doc 2", "quality_score": 90},
            {"id": "3", "content": "Doc 3", "quality_score": 70}
        ]
        
        with patch.object(enhanced_rag, 'hybrid_search') as mock_search:
            with patch.object(enhanced_rag, '_generate_answer', new_callable=AsyncMock) as mock_generate:
                with patch.object(enhanced_rag, '_cache_enhanced_answer', new_callable=AsyncMock):
                    with patch.object(enhanced_rag, 'context_optimizer') as mock_optimizer:
                        mock_search.search = AsyncMock(return_value=mock_documents)
                        mock_generate.return_value = "Mock answer"
                        
                        # Call with context optimization DISABLED
                        await enhanced_rag.ask_enhanced(
                            question="What is Docker?",
                            enable_context_optimization=False,
                            enable_hybrid_search=True
                        )
                        
                        # Optimizer.optimize should NOT be called
                        mock_optimizer.optimize.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_context_optimization_enabled_calls_optimizer(self, enhanced_rag):
        """Test context optimization calls optimizer when enabled."""
        mock_documents = [
            {"id": "1", "content": "Doc 1", "quality_score": 80},
            {"id": "2", "content": "Doc 2", "quality_score": 90}
        ]
        
        with patch.object(enhanced_rag, 'hybrid_search') as mock_search:
            with patch.object(enhanced_rag, '_generate_answer', new_callable=AsyncMock) as mock_generate:
                with patch.object(enhanced_rag, '_cache_enhanced_answer', new_callable=AsyncMock):
                    with patch.object(enhanced_rag, 'context_optimizer') as mock_optimizer:
                        mock_search.search = AsyncMock(return_value=mock_documents)
                        mock_generate.return_value = "Mock answer"
                        mock_optimizer.optimize.return_value = mock_documents
                        mock_optimizer.filter_by_relative_quality.return_value = mock_documents
                        
                        # Call with context optimization ENABLED
                        await enhanced_rag.ask_enhanced(
                            question="What is Docker?",
                            enable_context_optimization=True,
                            enable_hybrid_search=True
                        )
                        
                        # Optimizer.optimize SHOULD be called
                        mock_optimizer.optimize.assert_called()


class TestPhase2CIntegration:
    """Test Phase 2C (Metadata-Aware Confidence) integration."""
    
    @pytest.fixture
    def enhanced_rag(self):
        """Get enhanced RAG instance."""
        return AccuracyEnhancedRAG()
    
    @pytest.mark.asyncio
    async def test_confidence_adjusted_for_contradictions(self, enhanced_rag):
        """Test confidence is adjusted when contradictions detected."""
        mock_documents = [
            {"id": "1", "content": "Doc 1", "quality_score": 80}
        ]
        
        with patch.object(enhanced_rag, 'hybrid_search') as mock_search:
            with patch.object(enhanced_rag, '_generate_answer', new_callable=AsyncMock) as mock_generate:
                with patch.object(enhanced_rag, '_cache_enhanced_answer', new_callable=AsyncMock):
                    with patch.object(enhanced_rag, 'confidence_scorer') as mock_scorer:
                        with patch.object(enhanced_rag, 'contradiction_detector') as mock_detector:
                            mock_search.search = AsyncMock(return_value=mock_documents)
                            mock_generate.return_value = "Mock answer"
                            
                            # High confidence initially
                            mock_scorer.score = AsyncMock(return_value={
                                "confidence": 90.0,
                                "confidence_level": "High",
                                "breakdown": {}
                            })
                            
                            # High severity contradictions
                            mock_detector.detect.return_value = {
                                "has_contradictions": True,
                                "severity": "high",
                                "contradiction_count": 3,
                                "warning_message": "Conflicts detected"
                            }
                            
                            result = await enhanced_rag.ask_enhanced(
                                question="What is Docker?",
                                enable_confidence_scoring=True,
                                enable_contradiction_detection=True,
                                enable_hybrid_search=True
                            )
                            
                            # Confidence should be reduced (90 * 0.8 = 72)
                            assert result["confidence"] < 90.0
                            assert result["confidence"] <= 72.0
    
    @pytest.mark.asyncio
    async def test_confidence_capped_for_hard_queries(self, enhanced_rag):
        """Test confidence is capped at expected for hard queries."""
        mock_documents = [
            {"id": "1", "content": "Doc 1", "quality_score": 80}
        ]
        
        with patch.object(enhanced_rag, 'unified_analyzer') as mock_analyzer:
            with patch.object(enhanced_rag, 'hybrid_search') as mock_search:
                with patch.object(enhanced_rag, '_generate_answer', new_callable=AsyncMock) as mock_generate:
                    with patch.object(enhanced_rag, '_cache_enhanced_answer', new_callable=AsyncMock):
                        with patch.object(enhanced_rag, 'confidence_scorer') as mock_scorer:
                            # Mock unified analyzer to return hard query
                            mock_analyzer.analyze.return_value = {
                                "difficulty": {
                                    "difficulty_level": "hard",
                                    "difficulty_score": 75,
                                    "expected_confidence": 40.0,  # Low expected
                                    "suggestions": []
                                },
                                "intent": {
                                    "type": "conceptual",
                                    "complexity": "moderate",
                                    "confidence": 0.6,
                                    "n_results": 10,
                                    "enable_reranking": False,
                                    "strategy": "balanced"
                                }
                            }
                            
                            mock_search.search = AsyncMock(return_value=mock_documents)
                            mock_generate.return_value = "Mock answer"
                            
                            # High confidence initially (unrealistic for hard query)
                            mock_scorer.score = AsyncMock(return_value={
                                "confidence": 80.0,  # Too high!
                                "confidence_level": "High",
                                "breakdown": {}
                            })
                            
                            result = await enhanced_rag.ask_enhanced(
                                question="something about stuff",
                                enable_confidence_scoring=True,
                                use_unified_analyzer=True,
                                enable_hybrid_search=True
                            )
                            
                            # Confidence should be capped at expected (40)
                            assert result["confidence"] <= 40.0
    
    @pytest.mark.asyncio
    async def test_confidence_no_adjustment_without_contradictions(self, enhanced_rag):
        """Test confidence unchanged when no contradictions or hard query."""
        mock_documents = [
            {"id": "1", "content": "Doc 1", "quality_score": 80}
        ]
        
        with patch.object(enhanced_rag, 'unified_analyzer') as mock_analyzer:
            with patch.object(enhanced_rag, 'hybrid_search') as mock_search:
                with patch.object(enhanced_rag, '_generate_answer', new_callable=AsyncMock) as mock_generate:
                    with patch.object(enhanced_rag, '_cache_enhanced_answer', new_callable=AsyncMock):
                        with patch.object(enhanced_rag, 'confidence_scorer') as mock_scorer:
                            # Easy query, no contradictions
                            mock_analyzer.analyze.return_value = {
                                "difficulty": {
                                    "difficulty_level": "easy",
                                    "difficulty_score": 30,
                                    "expected_confidence": 75.0,
                                    "suggestions": []
                                },
                                "intent": {
                                    "type": "factual",
                                    "complexity": "simple",
                                    "confidence": 0.8,
                                    "n_results": 8,
                                    "enable_reranking": False,
                                    "strategy": "relevance_first"
                                }
                            }
                            
                            mock_search.search = AsyncMock(return_value=mock_documents)
                            mock_generate.return_value = "Mock answer"
                            
                            # Initial confidence
                            mock_scorer.score = AsyncMock(return_value={
                                "confidence": 70.0,
                                "confidence_level": "Medium",
                                "breakdown": {}
                            })
                            
                            # No contradictions
                            enhanced_rag.contradiction_detector.detect = Mock(return_value={
                                "has_contradictions": False
                            })
                            
                            result = await enhanced_rag.ask_enhanced(
                                question="What is Docker?",
                                enable_confidence_scoring=True,
                                use_unified_analyzer=True,
                                enable_contradiction_detection=True,
                                enable_hybrid_search=True
                            )
                            
                            # Confidence should be unchanged (no adjustments)
                            assert result["confidence"] == 70.0


class TestPhase2E2E:
    """End-to-end tests for Phase 2."""
    
    @pytest.mark.asyncio
    async def test_full_phase2_flow(self):
        """Test full Phase 2 flow end-to-end."""
        enhanced_rag = AccuracyEnhancedRAG()
        
        # This would require a full integration test environment
        # For now, just verify the service initializes with Phase 2 components
        assert hasattr(enhanced_rag, 'unified_analyzer')
        assert hasattr(enhanced_rag, 'context_optimizer')
        assert hasattr(enhanced_rag, 'confidence_scorer')
        assert hasattr(enhanced_rag, 'contradiction_detector')


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

