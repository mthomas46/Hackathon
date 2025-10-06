"""Unit tests for value objects."""

import pytest

from services.mcp_infrastructure.domain.value_objects.mcp_context_type import MCPContextType
from services.mcp_infrastructure.domain.value_objects.training_phase import TrainingPhase


class TestMCPContextType:
    """Tests for MCPContextType value object."""
    
    def test_all_context_types_exist(self):
        """Test that all expected context types are defined."""
        expected_types = [
            "instance", "training", "knowledge", "performance",
            "coordination", "query", "relationship", "error"
        ]
        
        for type_name in expected_types:
            assert hasattr(MCPContextType, type_name.upper())
    
    def test_context_type_values(self):
        """Test context type string values."""
        assert MCPContextType.INSTANCE.value == "instance"
        assert MCPContextType.TRAINING.value == "training"
        assert MCPContextType.KNOWLEDGE.value == "knowledge"
        assert MCPContextType.PERFORMANCE.value == "performance"
    
    def test_context_type_default_ttls(self):
        """Test that all context types have default TTLs."""
        for context_type in MCPContextType:
            ttl = context_type.default_ttl
            assert isinstance(ttl, int)
            assert ttl > 0
    
    def test_specific_ttl_values(self):
        """Test specific TTL values for context types."""
        assert MCPContextType.INSTANCE.default_ttl == 7200  # 2 hours
        assert MCPContextType.TRAINING.default_ttl == 86400  # 24 hours
        assert MCPContextType.PERFORMANCE.default_ttl == 3600  # 1 hour
    
    def test_context_type_from_string(self):
        """Test creating context type from string."""
        context_type = MCPContextType("instance")
        assert context_type == MCPContextType.INSTANCE
    
    def test_invalid_context_type_raises_error(self):
        """Test that invalid context type raises ValueError."""
        with pytest.raises(ValueError):
            MCPContextType("invalid_type")


class TestTrainingPhase:
    """Tests for TrainingPhase value object."""
    
    def test_all_training_phases_exist(self):
        """Test that all expected training phases are defined."""
        expected_phases = [
            "idle", "extraction", "normalization", "embedding",
            "graph_build", "validation", "deployment",
            "complete", "failed", "cancelled"
        ]
        
        for phase_name in expected_phases:
            assert hasattr(TrainingPhase, phase_name.upper())
    
    def test_training_phase_values(self):
        """Test training phase string values."""
        assert TrainingPhase.IDLE.value == "idle"
        assert TrainingPhase.EXTRACTION.value == "extraction"
        assert TrainingPhase.COMPLETE.value == "complete"
    
    def test_training_phase_progress_percentages(self):
        """Test that all phases have progress percentages."""
        for phase in TrainingPhase:
            progress = phase.progress_percentage
            assert isinstance(progress, float)
            assert 0.0 <= progress <= 1.0
    
    def test_specific_progress_values(self):
        """Test specific progress values."""
        assert TrainingPhase.IDLE.progress_percentage == 0.0
        assert TrainingPhase.EXTRACTION.progress_percentage == 0.15
        assert TrainingPhase.EMBEDDING.progress_percentage == 0.55
        assert TrainingPhase.COMPLETE.progress_percentage == 1.0
    
    def test_is_active_property(self):
        """Test is_active property for phases."""
        # Active phases
        assert TrainingPhase.EXTRACTION.is_active is True
        assert TrainingPhase.EMBEDDING.is_active is True
        assert TrainingPhase.VALIDATION.is_active is True
        
        # Inactive phases
        assert TrainingPhase.IDLE.is_active is False
        assert TrainingPhase.COMPLETE.is_active is False
        assert TrainingPhase.FAILED.is_active is False
    
    def test_is_terminal_property(self):
        """Test is_terminal property for phases."""
        # Terminal phases
        assert TrainingPhase.COMPLETE.is_terminal is True
        assert TrainingPhase.FAILED.is_terminal is True
        assert TrainingPhase.CANCELLED.is_terminal is True
        
        # Non-terminal phases
        assert TrainingPhase.IDLE.is_terminal is False
        assert TrainingPhase.EXTRACTION.is_terminal is False
        assert TrainingPhase.EMBEDDING.is_terminal is False
    
    def test_training_phase_from_string(self):
        """Test creating training phase from string."""
        phase = TrainingPhase("embedding")
        assert phase == TrainingPhase.EMBEDDING
    
    def test_invalid_training_phase_raises_error(self):
        """Test that invalid phase raises ValueError."""
        with pytest.raises(ValueError):
            TrainingPhase("invalid_phase")

