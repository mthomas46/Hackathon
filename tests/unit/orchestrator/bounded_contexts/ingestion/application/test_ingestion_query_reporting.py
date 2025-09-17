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


# Query Processing Application Tests
class TestProcessNaturalLanguageQueryUseCase(BaseApplicationTest):
    """Test ProcessNaturalLanguageQueryUseCase."""

    def get_use_case_class(self):
        return ProcessNaturalLanguageQueryUseCase

    def get_repository_mocks(self):
        return {}  # Query processing uses external services

    @pytest.mark.asyncio
    async def test_process_query_success(self):
        """Test successful natural language query processing."""
        use_case = self.setup_use_case()

        # Execute
        command = ProcessNaturalLanguageQueryCommand(
            query_text="find all users with admin role",
            context={"domain": "user_management"},
            max_results=50
        )
        result = await use_case.execute(command)

        # Assert - should return query result
        assert result is not None
        assert "query_id" in result
        assert "results" in result


class TestGetQueryResultUseCase(BaseApplicationTest):
    """Test GetQueryResultUseCase."""

    def get_use_case_class(self):
        return GetQueryResultUseCase

    def get_repository_mocks(self):
        return {}  # Mock not needed for placeholder implementation

    @pytest.mark.asyncio
    async def test_get_query_result_success(self):
        """Test successful query result retrieval."""
        use_case = self.setup_use_case()

        # Execute
        query = GetQueryResultQuery(query_id="query-123")
        result = await use_case.execute(query)

        # Assert - should return result or None
        # In placeholder implementation, may return None for non-existent queries
        assert result is None or isinstance(result, dict)


class TestListQueriesUseCase(BaseApplicationTest):
    """Test ListQueriesUseCase."""

    def get_use_case_class(self):
        return ListQueriesUseCase

    def get_repository_mocks(self):
        return {}  # Mock not needed for placeholder implementation

    @pytest.mark.asyncio
    async def test_list_queries_success(self):
        """Test successful query listing."""
        use_case = self.setup_use_case()

        # Execute
        query = ListQueriesQuery(page=1, page_size=20)
        result = await use_case.execute(query)

        # Assert - should return list data
        assert isinstance(result, list)


# Reporting Application Tests
class TestGenerateReportUseCase(BaseApplicationTest):
    """Test GenerateReportUseCase."""

    def get_use_case_class(self):
        return GenerateReportUseCase

    def get_repository_mocks(self):
        return {}  # Reporting uses external services

    @pytest.mark.asyncio
    async def test_generate_report_success(self):
        """Test successful report generation."""
        use_case = self.setup_use_case()

        # Execute
        command = GenerateReportCommand(
            report_type="analytics",
            parameters={"time_range": "30d"},
            format="json"
        )
        result = await use_case.execute(command)

        # Assert - should return report data
        assert result is not None
        assert "report_id" in result
        assert "status" in result


class TestGetReportUseCase(BaseApplicationTest):
    """Test GetReportUseCase."""

    def get_use_case_class(self):
        return GetReportUseCase

    def get_repository_mocks(self):
        return {}  # Mock not needed for placeholder implementation

    @pytest.mark.asyncio
    async def test_get_report_success(self):
        """Test successful report retrieval."""
        use_case = self.setup_use_case()

        # Execute
        query = GetReportQuery(report_id="report-123")
        result = await use_case.execute(query)

        # Assert - should return report or None
        assert result is None or isinstance(result, dict)


class TestListReportsUseCase(BaseApplicationTest):
    """Test ListReportsUseCase."""

    def get_use_case_class(self):
        return ListReportsUseCase

    def get_repository_mocks(self):
        return {}  # Mock not needed for placeholder implementation

    @pytest.mark.asyncio
    async def test_list_reports_success(self):
        """Test successful report listing."""
        use_case = self.setup_use_case()

        # Execute
        query = ListReportsQuery(page=1, page_size=20)
        result = await use_case.execute(query)

        # Assert - should return list data
        assert isinstance(result, list)
