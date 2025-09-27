"""Application commands for the discovery agent.

This module contains command objects that represent user intentions
and business operations in the discovery agent. Commands follow
the Command Query Responsibility Segregation (CQRS) pattern and
are used to trigger state changes in the system.

Commands are immutable data structures that encapsulate all the
information needed to perform a specific operation.
"""

from .commands import (
    RegisterServiceCommand,
    UnregisterServiceCommand,
    UpdateServiceCommand,
    DiscoverServicesCommand,
)

__all__ = [
    "RegisterServiceCommand",
    "UnregisterServiceCommand",
    "UpdateServiceCommand",
    "DiscoverServicesCommand",
]
