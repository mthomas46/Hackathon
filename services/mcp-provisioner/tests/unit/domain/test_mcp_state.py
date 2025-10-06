"""Unit tests for MCPState value object."""

import pytest
from domain.value_objects.mcp_state import (
    MCPState,
    MCPStateEnum,
    cold_state,
    warming_state,
    hot_state,
    cooling_state,
    failed_state,
)


class TestMCPStateTransitions:
    """Test state transition logic."""
    
    def test_cold_to_warming_is_valid(self):
        """COLD → WARMING is valid transition."""
        cold = cold_state()
        warming = warming_state()
        
        assert cold.can_transition_to(warming)
    
    def test_cold_to_hot_is_invalid(self):
        """COLD → HOT is invalid (must go through WARMING)."""
        cold = cold_state()
        hot = hot_state()
        
        assert not cold.can_transition_to(hot)
    
    def test_warming_to_hot_is_valid(self):
        """WARMING → HOT is valid transition."""
        warming = warming_state()
        hot = hot_state()
        
        assert warming.can_transition_to(hot)
    
    def test_warming_to_failed_is_valid(self):
        """WARMING → FAILED is valid (startup failure)."""
        warming = warming_state()
        failed = failed_state()
        
        assert warming.can_transition_to(failed)
    
    def test_hot_to_cooling_is_valid(self):
        """HOT → COOLING is valid (graceful shutdown)."""
        hot = hot_state()
        cooling = cooling_state()
        
        assert hot.can_transition_to(cooling)
    
    def test_hot_to_failed_is_valid(self):
        """HOT → FAILED is valid (crash)."""
        hot = hot_state()
        failed = failed_state()
        
        assert hot.can_transition_to(failed)
    
    def test_cooling_to_cold_is_valid(self):
        """COOLING → COLD is valid (shutdown complete)."""
        cooling = cooling_state()
        cold = cold_state()
        
        assert cooling.can_transition_to(cold)
    
    def test_failed_to_cold_is_valid(self):
        """FAILED → COLD is valid (manual recovery)."""
        failed = failed_state()
        cold = cold_state()
        
        assert failed.can_transition_to(cold)


class TestMCPStateQueries:
    """Test state query methods."""
    
    def test_hot_is_active(self):
        """HOT state is active."""
        assert hot_state().is_active()
    
    def test_cold_is_not_active(self):
        """COLD state is not active."""
        assert not cold_state().is_active()
    
    def test_warming_is_transitioning(self):
        """WARMING state is transitioning."""
        assert warming_state().is_transitioning()
    
    def test_cooling_is_transitioning(self):
        """COOLING state is transitioning."""
        assert cooling_state().is_transitioning()
    
    def test_hot_is_not_transitioning(self):
        """HOT state is not transitioning."""
        assert not hot_state().is_transitioning()
    
    def test_cold_is_stopped(self):
        """COLD state is stopped."""
        assert cold_state().is_stopped()
    
    def test_failed_is_stopped(self):
        """FAILED state is stopped."""
        assert failed_state().is_stopped()
    
    def test_hot_requires_resources(self):
        """HOT state requires resources."""
        assert hot_state().requires_resources()
    
    def test_cold_does_not_require_resources(self):
        """COLD state does not require resources."""
        assert not cold_state().requires_resources()


class TestMCPStateImmutability:
    """Test that MCPState is immutable."""
    
    def test_cannot_modify_state(self):
        """Cannot modify state after creation."""
        state = cold_state()
        
        with pytest.raises(Exception):  # dataclass frozen
            state.state = MCPStateEnum.HOT


class TestMCPStateNextStates:
    """Test next valid states."""
    
    def test_cold_next_states(self):
        """COLD can only go to WARMING."""
        next_states = cold_state().next_valid_states()
        
        assert next_states == [MCPStateEnum.WARMING]
    
    def test_warming_next_states(self):
        """WARMING can go to HOT or FAILED."""
        next_states = warming_state().next_valid_states()
        
        assert set(next_states) == {MCPStateEnum.HOT, MCPStateEnum.FAILED}
    
    def test_hot_next_states(self):
        """HOT can go to COOLING or FAILED."""
        next_states = hot_state().next_valid_states()
        
        assert set(next_states) == {MCPStateEnum.COOLING, MCPStateEnum.FAILED}

