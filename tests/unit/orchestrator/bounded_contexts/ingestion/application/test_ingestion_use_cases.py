#!/usr/bin/env python3
"""
Application Layer Tests for Remaining Bounded Contexts

Tests the application layer for ingestion, query processing, and reporting.
Consolidated into single file following DRY principles.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from services.orchestrator.application.ingestion.commands import StartIngestionCommand
from services.orchestrator.application.ingestion.queries import GetIngestionStatusQuery, ListIngestionsQuery
from services.orchestrator.application.ingestion.use_cases import (
    StartIngestionUseCase, GetIngestionStatusUseCase, ListIngestionsUseCase
)

from services.orchestrator.application.query_processing.commands import ProcessNaturalLanguageQueryCommand
from services.orchestrator.application.query_processing.queries import GetQueryResultQuery, ListQueriesQuery
from services.orchestrator.application.query_processing.use_cases import (
    ProcessNaturalLanguageQueryUseCase, GetQueryResultUseCase, ListQueriesUseCase
)

from services.orchestrator.application.reporting.commands import GenerateReportCommand
from services.orchestrator.application.reporting.queries import GetReportQuery, ListReportsQuery
from services.orchestrator.application.reporting.use_cases import (
    GenerateReportUseCase, GetReportUseCase, ListReportsUseCase
)

from tests.unit.orchestrator.test_base import BaseApplicationTest


# Ingestion Application Tests
class TestStartIngestionUseCase(BaseApplicationTest):
    """Test StartIngestionUseCase."""

    def get_use_case_class(self):
        return StartIngestionUseCase

    def get_repository_mocks(self):
        return {}  # Ingestion use case doesn't use traditional repositories

    @pytest.mark.asyncio
    async def test_start_ingestion_success(self):
        """Test successful ingestion start."""
        use_case = self.setup_use_case()

        # Execute
        command = StartIngestionCommand(
            source_url="https://github.com/test/repo",
            source_type="github",
            parameters={"include_issues": True}
        )
        result = await use_case.execute(command)

        # Assert - result should contain ingestion data
        assert result is not None
        assert "ingestion_id" in result


class TestGetIngestionStatusUseCase(BaseApplicationTest):
    """Test GetIngestionStatusUseCase."""

    def get_use_case_class(self):
        return GetIngestionStatusUseCase

    def get_repository_mocks(self):
        return {}  # Mock not needed for placeholder implementation

    @pytest.mark.asyncio
    async def test_get_ingestion_status_success(self):
        """Test successful ingestion status retrieval."""
        use_case = self.setup_use_case()

        # Execute
        query = GetIngestionStatusQuery(ingestion_id="ingest-123")
        result = await use_case.execute(query)

        # Assert - should return status data
        assert result is not None


class TestListIngestionsUseCase(BaseApplicationTest):
    """Test ListIngestionsUseCase."""

    def get_use_case_class(self):
        return ListIngestionsUseCase

    def get_repository_mocks(self):
        return {}  # Mock not needed for placeholder implementation

    @pytest.mark.asyncio
    async def test_list_ingestions_success(self):
        """Test successful ingestion listing."""
        use_case = self.setup_use_case()

        # Execute
        query = ListIngestionsQuery(limit=10, offset=0)
        result = await use_case.execute(query)

        # Assert - should return list data
        assert isinstance(result, list)


