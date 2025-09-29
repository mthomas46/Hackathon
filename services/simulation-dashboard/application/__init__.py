"""Simulation Dashboard Application Layer.

This module contains the application layer for the Simulation Dashboard service,
implementing Domain-Driven Design (DDD) principles. The application layer
orchestrates domain services and handles use cases.

Key Components:
- Command Handlers: Handle write operations (create, update, delete)
- Query Handlers: Handle read operations (get, list)
- Application Services: Orchestrate complex business operations
- DTOs: Data Transfer Objects for request/response contracts
"""

from .handlers import (
    CreateSimulationHandler,
    UpdateSimulationHandler,
    DeleteSimulationHandler,
    StartSimulationHandler,
    StopSimulationHandler,
)
from .queries import (
    ListSimulationsQuery,
    GetSimulationQuery,
    GetSimulationProgressQuery,
)

__all__ = [
    # Command Handlers
    "CreateSimulationHandler",
    "UpdateSimulationHandler",
    "DeleteSimulationHandler",
    "StartSimulationHandler",
    "StopSimulationHandler",

    # Query Handlers
    "ListSimulationsQuery",
    "GetSimulationQuery",
    "GetSimulationProgressQuery",
]
