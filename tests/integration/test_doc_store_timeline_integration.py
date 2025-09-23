"""Integration Tests for Doc-Store Timeline Integration

This module contains tests to verify that doc-store documents can be properly
integrated with simulation timelines.
"""

import pytest
import asyncio
import httpx
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List


class TestDocStoreTimelineIntegration:
    """Test doc-store timeline integration functionality."""

    @pytest.fixture
    def simulation_service_url(self):
        """URL for simulation service."""
        return "http://localhost:5075"

    @pytest.fixture
    def doc_store_service_url(self):
        """URL for doc-store service."""
        return "http://localhost:5051"

    @pytest.fixture
    def sample_mock_documents(self) -> List[Dict[str, Any]]:
        """Sample mock documents for testing."""
        return [
            {
                "id": "mock_doc_001",
                "title": "Mock Requirements Document",
                "content": "This is a mock requirements document for testing.",
                "dateCreated": "2024-01-01T10:00:00Z",
                "dateUpdated": "2024-01-05T14:30:00Z",
                "source": "mock"
            },
            {
                "id": "mock_doc_002",
                "title": "Mock Technical Specification",
                "content": "Technical specification for the mock system.",
                "dateCreated": "2024-01-03T09:15:00Z",
                "dateUpdated": "2024-01-08T16:45:00Z",
                "source": "mock"
            }
        ]

    @pytest.fixture
    def sample_doc_store_documents(self) -> List[Dict[str, Any]]:
        """Sample doc-store documents for testing."""
        return [
            {
                "id": "doc_store_001",
                "title": "Real API Documentation",
                "content": "This is real API documentation from the doc-store.",
                "created_at": "2024-01-02T08:30:00Z",
                "updated_at": "2024-01-07T12:20:00Z",
                "metadata": {"type": "api_docs", "version": "1.0"}
            },
            {
                "id": "doc_store_002",
                "title": "Architecture Overview",
                "content": "System architecture overview from the doc-store.",
                "created_at": "2024-01-04T11:45:00Z",
                "updated_at": "2024-01-10T15:30:00Z",
                "metadata": {"type": "architecture", "author": "team"}
            }
        ]

    @pytest.fixture
    def sample_timeline(self) -> Dict[str, Any]:
        """Sample timeline for testing."""
        return {
            "phases": [
                {"name": "Planning", "start_week": 0, "duration_weeks": 2},
                {"name": "Development", "start_week": 2, "duration_weeks": 4},
                {"name": "Testing", "start_week": 6, "duration_weeks": 2}
            ]
        }

    @pytest.mark.asyncio
    async def test_doc_store_service_discovery(self):
        """Test that doc-store service discovery works."""
        # This test verifies the service discovery functions
        # In a real environment, these would connect to actual services

        # Mock the service discovery
        with patch('services.project_simulation.main._get_doc_store_service_url') as mock_get_url:
            mock_get_url.return_value = "http://localhost:5051"

            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client

                # Mock successful health check
                mock_response = Mock()
                mock_response.status_code = 200
                mock_client.get.return_value = mock_response

                # Import and test the function
                from services.project_simulation.main import get_doc_store_service_url

                result = await get_doc_store_service_url()
                assert result == "http://localhost:5051"

    @pytest.mark.asyncio
    async def test_doc_store_document_retrieval(self):
        """Test retrieving documents from doc-store service."""
        with patch('services.project_simulation.main.get_doc_store_service_url', new_callable=AsyncMock) as mock_get_url:
            mock_get_url.return_value = "http://localhost:5051"

            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client

                # Mock doc-store API response
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "documents": [
                        {
                            "id": "doc_001",
                            "title": "Test Document",
                            "content": "Test content",
                            "created_at": "2024-01-01T10:00:00Z",
                            "updated_at": "2024-01-02T10:00:00Z",
                            "metadata": {"type": "test"}
                        }
                    ]
                }
                mock_client.get.return_value = mock_response

                from services.project_simulation.main import retrieve_documents_from_doc_store

                result = await retrieve_documents_from_doc_store(query="test", limit=10)

                assert len(result) == 1
                assert result[0]["id"] == "doc_001"
                assert result[0]["title"] == "Test Document"
                assert result[0]["source"] == "doc_store"

    @pytest.mark.asyncio
    async def test_doc_store_integration_with_mock_documents(self, sample_mock_documents, sample_doc_store_documents, sample_timeline):
        """Test integrating doc-store documents with mock documents."""
        with patch('services.project_simulation.main.retrieve_documents_from_doc_store', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.return_value = sample_doc_store_documents

            from services.project_simulation.main import integrate_doc_store_documents_with_timeline

            result = await integrate_doc_store_documents_with_timeline(
                simulation_id="test_sim_123",
                mock_documents=sample_mock_documents,
                timeline=sample_timeline
            )

            # Should have both mock and doc-store documents
            assert len(result) == 4  # 2 mock + 2 doc-store

            # Check that doc-store documents are marked properly
            doc_store_docs = [doc for doc in result if doc.get("source") == "doc_store"]
            assert len(doc_store_docs) == 2

            # Check timeline placement metadata
            for doc in doc_store_docs:
                assert "timeline_placement" in doc
                assert doc["timeline_placement"]["placed"] is True
                assert doc["timeline_placement"]["method"] == "doc_store_integration"

    @pytest.mark.asyncio
    async def test_doc_store_service_unavailable_graceful_fallback(self, sample_mock_documents):
        """Test graceful fallback when doc-store service is unavailable."""
        with patch('services.project_simulation.main.retrieve_documents_from_doc_store', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.return_value = []  # No documents available

            from services.project_simulation.main import integrate_doc_store_documents_with_timeline

            result = await integrate_doc_store_documents_with_timeline(
                simulation_id="test_sim_123",
                mock_documents=sample_mock_documents,
                timeline=None
            )

            # Should return original mock documents
            assert len(result) == len(sample_mock_documents)
            assert all(doc.get("source") == "mock" for doc in result)

    @pytest.mark.asyncio
    async def test_document_deduplication_in_integration(self):
        """Test that duplicate documents are properly handled."""
        mock_docs = [
            {
                "id": "duplicate_doc",
                "title": "Duplicate Document",
                "content": "This document appears in both mock and doc-store",
                "source": "mock"
            }
        ]

        doc_store_docs = [
            {
                "id": "duplicate_doc",  # Same ID as mock doc
                "title": "Duplicate Document from Doc-Store",
                "content": "This is the same document from doc-store",
                "source": "doc_store"
            }
        ]

        with patch('services.project_simulation.main.retrieve_documents_from_doc_store', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.return_value = doc_store_docs

            from services.project_simulation.main import integrate_doc_store_documents_with_timeline

            result = await integrate_doc_store_documents_with_timeline(
                simulation_id="test_sim_123",
                mock_documents=mock_docs,
                timeline=None
            )

            # Should only have one document (no duplicates)
            assert len(result) == 1
            assert result[0]["source"] == "mock"  # Mock document takes precedence

    @pytest.mark.asyncio
    async def test_timeline_integration_metadata(self, sample_mock_documents, sample_timeline):
        """Test that timeline integration adds proper metadata."""
        doc_store_docs = [
            {
                "id": "timeline_doc_001",
                "title": "Timeline Document",
                "content": "This document should be placed on timeline",
                "created_at": "2024-01-01T10:00:00Z"
            }
        ]

        with patch('services.project_simulation.main.retrieve_documents_from_doc_store', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.return_value = doc_store_docs

            from services.project_simulation.main import integrate_doc_store_documents_with_timeline

            result = await integrate_doc_store_documents_with_timeline(
                simulation_id="test_sim_123",
                mock_documents=sample_mock_documents,
                timeline=sample_timeline
            )

            # Find the doc-store document
            timeline_doc = next((doc for doc in result if doc["id"] == "timeline_doc_001"), None)
            assert timeline_doc is not None

            # Check timeline placement metadata
            placement = timeline_doc.get("timeline_placement", {})
            assert placement.get("placed") is True
            assert placement.get("method") == "doc_store_integration"
            assert "timestamp" in placement

    @pytest.mark.asyncio
    async def test_doc_store_query_parameter_handling(self):
        """Test that query parameters are properly handled for doc-store."""
        with patch('services.project_simulation.main.get_doc_store_service_url', new_callable=AsyncMock) as mock_get_url:
            mock_get_url.return_value = "http://localhost:5051"

            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client

                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"documents": []}
                mock_client.get.return_value = mock_response

                from services.project_simulation.main import retrieve_documents_from_doc_store

                # Test with query parameter
                await retrieve_documents_from_doc_store(query="simulation:test_sim_123", limit=25)

                # Verify the request was made with correct parameters
                mock_client.get.assert_called_once()
                call_args = mock_client.get.call_args
                assert "params" in call_args.kwargs
                params = call_args.kwargs["params"]
                assert params["query"] == "simulation:test_sim_123"
                assert params["limit"] == 25

    @pytest.mark.asyncio
    async def test_error_handling_doc_store_unavailable(self, sample_mock_documents):
        """Test error handling when doc-store service is completely unavailable."""
        with patch('services.project_simulation.main.retrieve_documents_from_doc_store', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.side_effect = Exception("Doc-store service unavailable")

            from services.project_simulation.main import integrate_doc_store_documents_with_timeline

            result = await integrate_doc_store_documents_with_timeline(
                simulation_id="test_sim_123",
                mock_documents=sample_mock_documents,
                timeline=None
            )

            # Should return original mock documents despite error
            assert len(result) == len(sample_mock_documents)
            assert all(doc.get("source") == "mock" for doc in result)

    @pytest.mark.asyncio
    async def test_environment_variable_service_discovery(self):
        """Test that environment variables override default service URLs."""
        with patch.dict('os.environ', {'DOC_STORE_URL': 'http://custom-doc-store:9090'}):
            from services.project_simulation.main import _get_doc_store_service_url

            result = _get_doc_store_service_url()
            assert result == 'http://custom-doc-store:9090'

    @pytest.mark.asyncio
    async def test_docker_environment_detection(self):
        """Test Docker environment detection for service URLs."""
        with patch('builtins.open') as mock_open:
            mock_file = Mock()
            mock_file.read.return_value = "docker"
            mock_open.return_value.__enter__.return_value = mock_file

            from services.project_simulation.main import _get_doc_store_service_url

            result = _get_doc_store_service_url()
            assert result == "http://doc-store:5051"

    @pytest.mark.asyncio
    async def test_integration_with_full_workflow(self, sample_mock_documents, sample_timeline):
        """Test the complete integration workflow."""
        # Mock the entire chain
        doc_store_docs = [
            {
                "id": "workflow_doc_001",
                "title": "Workflow Integration Test",
                "content": "This document tests the full workflow integration",
                "created_at": "2024-01-01T10:00:00Z"
            }
        ]

        with patch('services.project_simulation.main.retrieve_documents_from_doc_store', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.return_value = doc_store_docs

            with patch('services.project_simulation.main.generate_mock_simulation_data', new_callable=AsyncMock) as mock_generate:
                mock_generate.return_value = {
                    "documents": sample_mock_documents,
                    "timeline": sample_timeline,
                    "team_size": 5,
                    "technologies": ["Python", "FastAPI"]
                }

                # Import the function under test
                from services.project_simulation.main import create_simulation_from_interpreter

                # This would be a full integration test, but we'll just verify the components work
                # In a real test, we'd need to mock the entire application_service

                # Verify that our integration functions work correctly
                from services.project_simulation.main import integrate_doc_store_documents_with_timeline

                result = await integrate_doc_store_documents_with_timeline(
                    simulation_id="test_workflow_sim",
                    mock_documents=sample_mock_documents,
                    timeline=sample_timeline
                )

                assert len(result) == 3  # 2 mock + 1 doc-store
                assert any(doc.get("source") == "doc_store" for doc in result)
                assert all("timeline_placement" in doc for doc in result if doc.get("source") == "doc_store")


if __name__ == "__main__":
    print("🧪 Doc-Store Timeline Integration Tests")
    print("Run with: python -m pytest tests/integration/test_doc_store_timeline_integration.py -v")
    print("Requires simulation service running on localhost:5075")
