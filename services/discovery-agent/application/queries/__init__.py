"""Application queries for the discovery agent.

This module contains query objects that represent read operations
in the discovery agent. Queries follow the Command Query Responsibility
Segregation (CQRS) pattern and are used to retrieve data from the system
without causing state changes.

Queries are immutable data structures that encapsulate all the
information needed to perform a specific read operation.
"""

from .queries import (
    GetServiceQuery,
    ListServicesQuery,
    GetDiscoveryStatsQuery,
    SearchServicesQuery,
)

__all__ = [
    "GetServiceQuery",
    "ListServicesQuery",
    "GetDiscoveryStatsQuery",
    "SearchServicesQuery",
]
