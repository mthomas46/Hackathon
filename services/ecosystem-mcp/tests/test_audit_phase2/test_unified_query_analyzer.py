"""
Unit tests for UnifiedQueryAnalyzer (Phase 2A Audit Fix)

Tests the unified analyzer that replaces separate difficulty + intent calls.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from services.rag.unified_query_analyzer import (
    UnifiedQueryAnalyzer,
    QueryFeatures,
    get_unified_query_analyzer
)


class TestUnifiedQueryAnalyzer:
    """Test unified query analyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Get analyzer instance."""
        return UnifiedQueryAnalyzer()
    
    def test_initialization(self, analyzer):
        """Test analyzer initializes correctly."""
        assert analyzer is not None
        assert len(analyzer.vague_terms) > 0
        assert len(analyzer.technical_terms) > 0
        assert len(analyzer.intent_patterns) > 0
    
    def test_singleton_pattern(self):
        """Test singleton returns same instance."""
        analyzer1 = get_unified_query_analyzer()
        analyzer2 = get_unified_query_analyzer()
        assert analyzer1 is analyzer2
    
    def test_analyze_simple_query(self, analyzer):
        """Test analysis of simple query."""
        result = analyzer.analyze("What is Docker?")
        
        # Check structure
        assert "difficulty" in result
        assert "intent" in result
        assert "elapsed_ms" in result
        assert "analyzer_version" in result
        
        # Check difficulty
        difficulty = result["difficulty"]
        assert difficulty["difficulty_level"] == "easy"  # Short, clear question
        assert difficulty["difficulty_score"] < 50
        
        # Check intent
        intent = result["intent"]
        assert intent["type"] == "factual"  # "What is" pattern
        assert intent["complexity"] == "simple"
        assert intent["enable_reranking"] is False  # Simple doesn't need reranking
    
    def test_analyze_vague_query(self, analyzer):
        """Test analysis of vague query."""
        result = analyzer.analyze("something about stuff")
        
        difficulty = result["difficulty"]
        assert difficulty["difficulty_level"] == "hard"
        assert difficulty["difficulty_score"] > 70
        assert len(difficulty["suggestions"]) > 0
        assert "vague" in difficulty["suggestions"][0].lower()
    
    def test_analyze_complex_query(self, analyzer):
        """Test analysis of complex query."""
        result = analyzer.analyze(
            "How do I compare and evaluate multiple embedding models "
            "for semantic search in a production environment?"
        )
        
        difficulty = result["difficulty"]
        assert difficulty["difficulty_level"] in ["easy", "medium"]  # Has technical terms
        
        intent = result["intent"]
        assert intent["complexity"] == "complex"  # Long, multiple indicators
        assert intent["enable_reranking"] is True  # Complex needs reranking
        assert intent["n_results"] >= 12  # Complex needs more results
    
    def test_analyze_procedural_query(self, analyzer):
        """Test analysis of procedural/how-to query."""
        result = analyzer.analyze("How to set up Docker containers for MCP?")
        
        intent = result["intent"]
        assert intent["type"] == "procedural"  # "How to" pattern
        assert intent["strategy"] in ["balanced", "relevance_first"]
    
    def test_analyze_comparative_query(self, analyzer):
        """Test analysis of comparative query."""
        result = analyzer.analyze("Compare Docker and Kubernetes for deployment")
        
        intent = result["intent"]
        assert intent["type"] == "comparative"  # "Compare" pattern
        assert intent["factors"]["comparison"] is True
    
    def test_analyze_temporal_query(self, analyzer):
        """Test analysis of temporal/recent query."""
        result = analyzer.analyze("What are the latest features in Docker?")
        
        intent = result["intent"]
        assert intent["type"] == "temporal"  # "latest" pattern
        assert intent["factors"]["temporal"] is True
    
    def test_feature_extraction(self, analyzer):
        """Test feature extraction."""
        features = analyzer._extract_features("How to setup Docker API server?")
        
        assert isinstance(features, QueryFeatures)
        assert features.word_count > 0
        assert features.char_count > 0
        assert features.has_question_mark is True
        assert features.technical_term_count > 0  # docker, api, server
    
    def test_difficulty_with_no_question_mark(self, analyzer):
        """Test difficulty increases without question mark."""
        with_q = analyzer.analyze("How does Docker work?")
        without_q = analyzer.analyze("Docker work")
        
        assert without_q["difficulty"]["difficulty_score"] > with_q["difficulty"]["difficulty_score"]
    
    def test_difficulty_with_technical_terms(self, analyzer):
        """Test difficulty decreases with technical terms."""
        vague = analyzer.analyze("something about stuff")
        technical = analyzer.analyze("Docker container orchestration with Kubernetes")
        
        assert vague["difficulty"]["difficulty_score"] > technical["difficulty"]["difficulty_score"]
    
    def test_intent_confidence_high(self, analyzer):
        """Test high confidence intent detection."""
        result = analyzer.analyze("What is Docker?")
        
        intent = result["intent"]
        assert intent["confidence"] >= 0.7  # Clear "What is" pattern
    
    def test_intent_default_for_ambiguous(self, analyzer):
        """Test default intent for ambiguous queries."""
        result = analyzer.analyze("Tell me about something")
        
        intent = result["intent"]
        assert intent["type"] == "conceptual"  # Default
        assert intent["confidence"] <= 0.6
    
    def test_complexity_indicators(self, analyzer):
        """Test complexity indicator detection."""
        simple = analyzer.analyze("What is Docker?")
        complex = analyzer.analyze(
            "What is Docker and how does it compare to Kubernetes "
            "in terms of container orchestration?"
        )
        
        assert simple["intent"]["complexity"] == "simple"
        assert complex["intent"]["complexity"] in ["moderate", "complex"]
    
    def test_n_results_adaptation(self, analyzer):
        """Test n_results adapts to complexity."""
        simple = analyzer.analyze("What is Docker?")
        complex = analyzer.analyze(
            "Compare and analyze multiple container orchestration platforms"
        )
        
        assert simple["intent"]["n_results"] < complex["intent"]["n_results"]
    
    def test_strategy_adaptation(self, analyzer):
        """Test strategy adapts to intent type."""
        factual = analyzer.analyze("What is Docker?")
        procedural = analyzer.analyze("How to deploy with Docker?")
        
        # Different intents may prefer different strategies
        assert "strategy" in factual["intent"]
        assert "strategy" in procedural["intent"]
    
    def test_performance(self, analyzer):
        """Test performance is reasonable."""
        import time
        
        start = time.time()
        for _ in range(10):
            analyzer.analyze("How does Docker container orchestration work?")
        elapsed = time.time() - start
        
        avg_ms = (elapsed / 10) * 1000
        assert avg_ms < 5  # Should be < 5ms per analysis
    
    def test_error_handling(self, analyzer):
        """Test graceful error handling."""
        # Empty query
        result = analyzer.analyze("")
        assert "difficulty" in result
        assert "intent" in result
        
        # None query (should raise, but be handled)
        with pytest.raises(Exception):
            analyzer.analyze(None)
    
    def test_default_difficulty(self, analyzer):
        """Test default difficulty fallback."""
        default = analyzer._default_difficulty()
        
        assert default["difficulty_level"] == "medium"
        assert default["difficulty_score"] == 50.0
        assert default["expected_confidence"] == 50.0
    
    def test_default_intent(self, analyzer):
        """Test default intent fallback."""
        default = analyzer._default_intent()
        
        assert default["type"] == "conceptual"
        assert default["complexity"] == "moderate"
        assert default["n_results"] == 10


class TestUnifiedVsSeparate:
    """Compare unified analyzer to separate difficulty + intent."""
    
    def test_unified_faster_than_separate(self):
        """Test unified is faster than separate calls."""
        from services.rag.query_difficulty_estimator import get_query_difficulty_estimator
        from services.rag.query_intent_classifier import get_query_intent_classifier
        
        unified = get_unified_query_analyzer()
        difficulty_est = get_query_difficulty_estimator()
        intent_clf = get_query_intent_classifier()
        
        query = "How do I set up Docker containers for production deployment?"
        
        # Time unified
        import time
        start = time.time()
        for _ in range(10):
            unified.analyze(query)
        unified_time = time.time() - start
        
        # Time separate
        start = time.time()
        for _ in range(10):
            difficulty_est.estimate(query)
            intent_clf.classify_heuristic(query)
        separate_time = time.time() - start
        
        # Unified should be faster or roughly equal
        # Allow for variance, but unified shouldn't be significantly slower
        assert unified_time <= separate_time * 1.2  # Within 20%
        
        print(f"\nPerformance comparison:")
        print(f"  Unified:  {unified_time*1000/10:.2f}ms per query")
        print(f"  Separate: {separate_time*1000/10:.2f}ms per query")
        print(f"  Speedup:  {separate_time/unified_time:.2f}x")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

