"""
Unit tests for EnhancementConfig and presets.

Tests all configuration presets to ensure correct settings.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services/ecosystem-mcp/src'))

import pytest
from services.rag.enhancements import EnhancementConfig


class TestEnhancementConfig:
    """Test EnhancementConfig class and presets."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = EnhancementConfig.default()
        
        # Phase 1: Core features enabled
        assert config.enable_hybrid_search is True
        assert config.enable_query_rewriting is True
        assert config.enable_confidence_scoring is True
        
        # Phase 2: Context optimization only
        assert config.enable_reranking is False
        assert config.enable_context_optimization is True
        assert config.enable_metadata_filtering is True
        
        # Phase 5R: Fast intent
        assert config.enable_intent_classification is True
        assert config.enable_llm_intent is False
        
        # Phase 7R: All enabled
        assert config.enable_contradiction_detection is True
        assert config.enable_difficulty_estimation is True
    
    def test_temporal_default_config(self):
        """Test temporal-optimized configuration."""
        config = EnhancementConfig.temporal_default()
        
        # Should have hybrid and rewriting
        assert config.enable_hybrid_search is True
        assert config.enable_query_rewriting is True
        
        # Should skip intent and difficulty (temporal queries explicit)
        assert config.enable_intent_classification is False
        assert config.enable_difficulty_estimation is False
        
        # Should skip reranking (temporal filter is primary)
        assert config.enable_reranking is False
    
    def test_context_aware_default_config(self):
        """Test context-aware-optimized configuration."""
        config = EnhancementConfig.context_aware_default()
        
        # Should enable reranking (good for hierarchical filtering)
        assert config.enable_reranking is True
        
        # Should disable metadata filtering (context filters are primary)
        assert config.enable_metadata_filtering is False
        
        # Should use relevance_first strategy
        assert config.context_strategy == "relevance_first"
    
    def test_multipass_default_config(self):
        """Test multi-pass-optimized configuration."""
        config = EnhancementConfig.multipass_default()
        
        # Should enable hybrid (better per-question coverage)
        assert config.enable_hybrid_search is True
        
        # Should disable expensive features
        assert config.enable_query_rewriting is False  # Questions already specific
        assert config.enable_reranking is False  # Too expensive for N×M
        assert config.enable_contradiction_detection is False  # Too expensive
        assert config.enable_difficulty_estimation is False  # Questions pre-validated
        
        # Should use quality_first strategy
        assert config.context_strategy == "quality_first"
    
    def test_fast_config(self):
        """Test fast configuration."""
        config = EnhancementConfig.fast()
        
        # Should only enable hybrid search
        assert config.enable_hybrid_search is True
        
        # Everything else disabled
        assert config.enable_query_rewriting is False
        assert config.enable_confidence_scoring is False
        assert config.enable_reranking is False
        assert config.enable_context_optimization is False
        assert config.enable_metadata_filtering is False
        assert config.enable_intent_classification is False
        assert config.enable_contradiction_detection is False
        assert config.enable_difficulty_estimation is False
    
    def test_max_quality_config(self):
        """Test maximum quality configuration."""
        config = EnhancementConfig.max_quality()
        
        # All features should be enabled
        assert config.enable_hybrid_search is True
        assert config.enable_query_rewriting is True
        assert config.enable_confidence_scoring is True
        assert config.enable_reranking is True  # ✅ Expensive but enabled
        assert config.enable_context_optimization is True
        assert config.enable_metadata_filtering is True
        assert config.enable_intent_classification is True
        assert config.enable_llm_intent is True  # ✅ Expensive but enabled
        assert config.enable_contradiction_detection is True
        assert config.enable_difficulty_estimation is True
        
        # Should have high quality threshold
        assert config.quality_threshold == 60.0
    
    def test_minimal_config(self):
        """Test minimal configuration."""
        config = EnhancementConfig.minimal()
        
        # Only hybrid search enabled
        assert config.enable_hybrid_search is True
        
        # Everything else disabled
        assert config.enable_query_rewriting is False
        assert config.enable_confidence_scoring is False
        assert config.enable_reranking is False
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = EnhancementConfig.default()
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert "enable_hybrid_search" in config_dict
        assert config_dict["enable_hybrid_search"] is True
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        config_dict = {
            "enable_hybrid_search": True,
            "enable_query_rewriting": False,
            "enable_confidence_scoring": True
        }
        
        config = EnhancementConfig.from_dict(config_dict)
        
        assert config.enable_hybrid_search is True
        assert config.enable_query_rewriting is False
        assert config.enable_confidence_scoring is True
    
    def test_all_presets_valid(self):
        """Test that all presets can be created."""
        presets = [
            EnhancementConfig.default(),
            EnhancementConfig.temporal_default(),
            EnhancementConfig.context_aware_default(),
            EnhancementConfig.multipass_default(),
            EnhancementConfig.fast(),
            EnhancementConfig.max_quality(),
            EnhancementConfig.minimal()
        ]
        
        for preset in presets:
            assert isinstance(preset, EnhancementConfig)
            assert preset.to_dict() is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

