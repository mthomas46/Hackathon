"""Simulation Execution Infrastructure - Core Business Logic Integration.

This package provides the core simulation execution engine that integrates
the domain layer (DDD aggregates) with the actual simulation execution logic.
"""

from .simulation_execution_engine import SimulationExecutionEngine

__all__ = [
    'SimulationExecutionEngine'
]
