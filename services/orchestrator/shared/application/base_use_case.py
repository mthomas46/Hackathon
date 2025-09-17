"""Base Use Case Class

Shared base class for all use cases across bounded contexts.
Provides consistent interface and error handling patterns.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T = TypeVar('T')


class UseCase(ABC):
    """Base class for all use cases.

    Provides a consistent interface for executing business operations
    across all bounded contexts in the system.
    """

    @abstractmethod
    async def execute(self, *args, **kwargs):
        """Execute the use case.

        Args:
            *args: Positional arguments specific to the use case
            **kwargs: Keyword arguments specific to the use case

        Returns:
            Result of the use case execution (varies by implementation)
        """
        pass
