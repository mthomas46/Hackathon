"""MCP State Value Object.

Represents the lifecycle state of an MCP instance.
State machine: COLD → WARMING → HOT → COOLING → COLD
"""

from enum import Enum
from dataclasses import dataclass
from typing import List


class MCPStateEnum(str, Enum):
    """MCP lifecycle states."""
    
    COLD = "cold"  # Not running, stored in registry
    WARMING = "warming"  # Container starting, loading databases
    HOT = "hot"  # Actively serving queries
    COOLING = "cooling"  # Draining queries, preparing shutdown
    FAILED = "failed"  # Failed to start or crashed


@dataclass(frozen=True)  # Immutable value object
class MCPState:
    """
    Value object representing MCP state.
    
    Immutable and compared by value, not identity.
    Contains business logic for valid state transitions.
    """
    
    state: MCPStateEnum
    
    def __post_init__(self):
        """Validate state value."""
        if not isinstance(self.state, MCPStateEnum):
            raise ValueError(f"Invalid state type: {type(self.state)}")
    
    def can_transition_to(self, new_state: "MCPState") -> bool:
        """
        Check if transition to new state is valid.
        
        Valid transitions:
        - COLD → WARMING
        - WARMING → HOT or FAILED
        - HOT → COOLING or FAILED
        - COOLING → COLD or FAILED
        - FAILED → COLD (manual recovery)
        """
        valid_transitions = {
            MCPStateEnum.COLD: [MCPStateEnum.WARMING],
            MCPStateEnum.WARMING: [MCPStateEnum.HOT, MCPStateEnum.FAILED],
            MCPStateEnum.HOT: [MCPStateEnum.COOLING, MCPStateEnum.FAILED],
            MCPStateEnum.COOLING: [MCPStateEnum.COLD, MCPStateEnum.FAILED],
            MCPStateEnum.FAILED: [MCPStateEnum.COLD],  # Manual recovery only
        }
        
        return new_state.state in valid_transitions.get(self.state, [])
    
    def is_active(self) -> bool:
        """Check if MCP is in an active state (can serve queries)."""
        return self.state == MCPStateEnum.HOT
    
    def is_transitioning(self) -> bool:
        """Check if MCP is in a transitional state."""
        return self.state in [MCPStateEnum.WARMING, MCPStateEnum.COOLING]
    
    def is_stopped(self) -> bool:
        """Check if MCP is stopped."""
        return self.state in [MCPStateEnum.COLD, MCPStateEnum.FAILED]
    
    def requires_resources(self) -> bool:
        """Check if state requires allocated resources (CPU, RAM, etc.)."""
        return self.state in [MCPStateEnum.WARMING, MCPStateEnum.HOT, MCPStateEnum.COOLING]
    
    def next_valid_states(self) -> List[MCPStateEnum]:
        """Get list of valid next states."""
        transitions = {
            MCPStateEnum.COLD: [MCPStateEnum.WARMING],
            MCPStateEnum.WARMING: [MCPStateEnum.HOT, MCPStateEnum.FAILED],
            MCPStateEnum.HOT: [MCPStateEnum.COOLING, MCPStateEnum.FAILED],
            MCPStateEnum.COOLING: [MCPStateEnum.COLD, MCPStateEnum.FAILED],
            MCPStateEnum.FAILED: [MCPStateEnum.COLD],
        }
        return transitions.get(self.state, [])
    
    def __str__(self) -> str:
        return self.state.value
    
    def __repr__(self) -> str:
        return f"MCPState({self.state.value})"


# Convenience constructors
def cold_state() -> MCPState:
    """Create COLD state."""
    return MCPState(MCPStateEnum.COLD)


def warming_state() -> MCPState:
    """Create WARMING state."""
    return MCPState(MCPStateEnum.WARMING)


def hot_state() -> MCPState:
    """Create HOT state."""
    return MCPState(MCPStateEnum.HOT)


def cooling_state() -> MCPState:
    """Create COOLING state."""
    return MCPState(MCPStateEnum.COOLING)


def failed_state() -> MCPState:
    """Create FAILED state."""
    return MCPState(MCPStateEnum.FAILED)

