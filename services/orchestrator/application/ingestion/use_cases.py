"""Ingestion Application Use Cases"""

from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod

from .commands import StartIngestionCommand, CancelIngestionCommand, RetryIngestionCommand
from .queries import GetIngestionStatusQuery, ListIngestionsQuery


class UseCase(ABC):
    """Base use case class."""

    @abstractmethod
    async def execute(self, *args, **kwargs):
        """Execute the use case."""
        pass


class StartIngestionUseCase(UseCase):
    """Use case for starting document ingestion."""

    async def execute(self, command: StartIngestionCommand) -> Dict[str, Any]:
        """Execute the start ingestion use case."""
        # Placeholder implementation
        return {
            "ingestion_id": "placeholder-id",
            "status": "started",
            "source_url": command.source_url,
            "source_type": command.source_type
        }


class GetIngestionStatusUseCase(UseCase):
    """Use case for getting ingestion status."""

    async def execute(self, query: GetIngestionStatusQuery) -> Optional[Dict[str, Any]]:
        """Execute the get ingestion status use case."""
        # Placeholder implementation
        return {
            "ingestion_id": query.ingestion_id,
            "status": "completed",
            "progress_percentage": 100
        }


class ListIngestionsUseCase(UseCase):
    """Use case for listing ingestions."""

    async def execute(self, query: ListIngestionsQuery) -> List[Dict[str, Any]]:
        """Execute the list ingestions use case."""
        # Placeholder implementation
        return [
            {
                "ingestion_id": "sample-1",
                "status": "completed",
                "source_url": "https://example.com",
                "source_type": "github"
            }
        ]
