"""Simulation Dashboard Queries.

Query objects representing read operations in the simulation dashboard.
Following CQRS pattern for clear separation of read and write operations.
"""

from .simulation_queries import (
    ListSimulationsQuery,
    GetSimulationQuery,
    GetSimulationProgressQuery,
)

__all__ = [
    "ListSimulationsQuery",
    "GetSimulationQuery",
    "GetSimulationProgressQuery",
]
