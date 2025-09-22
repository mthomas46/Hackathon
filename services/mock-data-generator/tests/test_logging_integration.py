"""Tests for Mock Data Generator logging integration with LogCollectorClient."""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import httpx

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import app, logger_client
from services.shared.utilities.logging_client import LogCollectorClient


class TestMockDataGeneratorLoggingIntegration:
    """Test Mock Data Generator logging integration with LogCollectorClient."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_logger_client(self):
        """Mock LogCollectorClient."""
        mock_client = AsyncMock(spec=LogCollectorClient)
        return mock_client

    @pytest.fixture(autouse=True)
    async def setup_logger_client(self, mock_logger_client):
        """Setup mock logger client for all tests."""
        global logger_client
        logger_client = mock_logger_client
        yield
        logger_client = None

    @pytest.mark.asyncio
    async def test_mock_data_generation_successful_logging(self, client, mock_logger_client):
        """Test successful mock data generation logging."""
        # Mock the generator methods
        with patch('main.generator') as mock_generator:
            # Setup mock generator
            mock_data = {"id": "test_123", "content": "Test generated content"}
            mock_generator.generate_with_llm.return_value = mock_data
            mock_generator.store_in_doc_store.return_value = "doc_12345"

            # Make request
            request_data = {
                "data_type": "source_code",
                "count": 2,
                "store_in_doc_store": True,
                "context": {"language": "python"},
                "parameters": {"framework": "fastapi"}
            }

            response = client.post("/generate", json=request_data)
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # start and completion
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check business events
            business_calls = [call for call in mock_logger_client.log_business_event.call_args_list
                            if call[0][0] in ['mock_data_generation_started', 'mock_data_generation_completed']]

            assert len(business_calls) == 2

            # Check start event
            start_call = next(call for call in business_calls if call[0][0] == 'mock_data_generation_started')
            start_data = start_call[0][1]
            assert start_data['data_type'] == 'source_code'
            assert start_data['count_requested'] == 2
            assert start_data['store_in_doc_store'] is True
            assert start_data['llm_enhanced'] is True
            assert 'request_id' in start_data

            # Check completion event
            completion_call = next(call for call in business_calls if call[0][0] == 'mock_data_generation_completed')
            completion_data = completion_call[0][1]
            assert completion_data['data_type'] == 'source_code'
            assert completion_data['items_generated'] == 2
            assert completion_data['items_stored'] == 2
            assert completion_data['storage_success_rate'] == 1.0  # 2/2
            assert completion_data['success'] is True
            assert 'processing_time_seconds' in completion_data

            # Check performance metric
            perf_call = mock_logger_client.log_performance_metric.call_args
            assert perf_call[0][0] == 'mock_data_generation'
            assert 'generation_success' in perf_call[0][2]
            assert perf_call[0][2]['generation_success'] is True

    @pytest.mark.asyncio
    async def test_bulk_collection_generation_successful_logging(self, client, mock_logger_client):
        """Test successful bulk collection generation logging."""
        # Mock the generator
        with patch('main.generator') as mock_generator:
            # Create mock response
            mock_response = MagicMock()
            mock_response.documents_created = [
                {"id": "doc1", "type": "source_code"},
                {"id": "doc2", "type": "llm_prompt"},
                {"id": "doc3", "type": "analysis_report"}
            ]
            mock_response.stored_documents = ["stored_doc1", "stored_doc2", "stored_doc3"]
            mock_generator.generate_bulk_collection.return_value = mock_response

            # Make request
            request_data = {
                "name": "test_collection",
                "distribution": {
                    "source_code": 10,
                    "llm_prompt": 5,
                    "analysis_report": 3
                },
                "store_in_doc_store": True,
                "include_relationships": True,
                "metadata": {"tags": ["test", "bulk"]}
            }

            response = client.post("/collections/generate", json=request_data)
            assert response.status_code == 200

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # start and completion
            assert mock_logger_client.log_performance_metric.call_count == 1

            # Check start event
            start_events = [call for call in mock_logger_client.log_business_event.call_args_list
                          if call[0][0] == 'bulk_collection_generation_started']
            assert len(start_events) >= 1

            start_data = start_events[0][0][1]
            assert start_data['collection_name'] == 'test_collection'
            assert start_data['data_types'] == ['source_code', 'llm_prompt', 'analysis_report']
            assert start_data['total_items_requested'] == 18  # 10 + 5 + 3
            assert start_data['store_in_doc_store'] is True
            assert start_data['include_relationships'] is True

            # Check completion event
            completion_events = [call for call in mock_logger_client.log_business_event.call_args_list
                               if call[0][0] == 'bulk_collection_generation_completed']
            assert len(completion_events) >= 1

            completion_data = completion_events[0][0][1]
            assert completion_data['collection_name'] == 'test_collection'
            assert completion_data['documents_created'] == 3
            assert completion_data['documents_stored'] == 3
            assert completion_data['success'] is True

    @pytest.mark.asyncio
    async def test_mock_data_generation_failure_logging(self, client, mock_logger_client):
        """Test failed mock data generation logging."""
        # Mock the generator to raise an exception
        with patch('main.generator') as mock_generator:
            mock_generator.generate_with_llm.side_effect = Exception("LLM service unavailable")

            # Make request
            request_data = {
                "data_type": "source_code",
                "count": 1,
                "store_in_doc_store": False
            }

            response = client.post("/generate", json=request_data)
            assert response.status_code == 500

            # Verify error logging
            assert mock_logger_client.log_error.call_count >= 1
            assert mock_logger_client.log_business_event.call_count >= 2  # start and failure

            # Check error call
            error_call = mock_logger_client.log_error.call_args
            assert 'Mock data generation failed: LLM service unavailable' in error_call[0][0]
            assert error_call[0][1]['data_type'] == 'source_code'
            assert error_call[0][1]['count_requested'] == 1
            assert error_call[0][1]['error_type'] == 'Exception'

            # Check failure business event
            failure_events = [call for call in mock_logger_client.log_business_event.call_args_list
                            if call[0][0] == 'mock_data_generation_failed']
            assert len(failure_events) >= 1

            failure_data = failure_events[0][0][1]
            assert failure_data['data_type'] == 'source_code'
            assert failure_data['error_type'] == 'Exception'
            assert 'LLM service unavailable' in failure_data['error_message']

    @pytest.mark.asyncio
    async def test_bulk_collection_generation_failure_logging(self, client, mock_logger_client):
        """Test failed bulk collection generation logging."""
        # Mock the generator to raise an exception
        with patch('main.generator') as mock_generator:
            mock_generator.generate_bulk_collection.side_effect = Exception("Storage service error")

            # Make request
            request_data = {
                "name": "failed_collection",
                "distribution": {"source_code": 5},
                "store_in_doc_store": True
            }

            response = client.post("/collections/generate", json=request_data)
            assert response.status_code >= 400  # Should fail

            # Verify error logging
            assert mock_logger_client.log_error.call_count >= 1
            assert mock_logger_client.log_business_event.call_count >= 2

            # Check error call
            error_call = mock_logger_client.log_error.call_args
            assert 'Bulk collection generation failed: Storage service error' in error_call[0][0]
            assert error_call[0][1]['collection_name'] == 'failed_collection'
            assert error_call[0][1]['data_types_count'] == 1

    @pytest.mark.asyncio
    async def test_storage_success_rate_calculation(self, client, mock_logger_client):
        """Test that storage success rate is calculated correctly."""
        with patch('main.generator') as mock_generator:
            # Setup mock with partial storage success
            mock_data1 = {"id": "test1", "content": "Content 1"}
            mock_data2 = {"id": "test2", "content": "Content 2"}
            mock_data3 = {"id": "test3", "content": "Content 3"}

            mock_generator.generate_with_llm.side_effect = [mock_data1, mock_data2, mock_data3]
            # Only first two get stored successfully
            mock_generator.store_in_doc_store.side_effect = ["doc_1", "doc_2", None]

            request_data = {
                "data_type": "source_code",
                "count": 3,
                "store_in_doc_store": True
            }

            response = client.post("/generate", json=request_data)
            assert response.status_code == 200

            # Check that storage success rate is 2/3 = 0.667
            completion_events = [call for call in mock_logger_client.log_business_event.call_args_list
                               if call[0][0] == 'mock_data_generation_completed']
            assert len(completion_events) >= 1

            completion_data = completion_events[0][0][1]
            assert completion_data['items_generated'] == 3
            assert completion_data['items_stored'] == 2
            assert abs(completion_data['storage_success_rate'] - (2/3)) < 0.01  # Allow small floating point difference

    @pytest.mark.asyncio
    async def test_startup_logging(self, mock_logger_client):
        """Test service startup logging."""
        from main import startup_event

        await startup_event()

        # Verify startup logging
        assert mock_logger_client.log_business_event.call_count >= 1
        assert mock_logger_client.log_info.call_count >= 1

        # Check startup business event
        business_call = mock_logger_client.log_business_event.call_args
        assert business_call[0][0] == 'mock_data_generator_startup'
        startup_data = business_call[0][1]
        assert 'capabilities' in startup_data
        assert 'data_types' in startup_data
        assert 'features' in startup_data

        # Check info logging
        info_call = mock_logger_client.log_info.call_args
        assert 'Mock Data Generator service started' in info_call[0][0]

    @pytest.mark.asyncio
    async def test_shutdown_logging(self, mock_logger_client):
        """Test service shutdown logging."""
        from main import shutdown_event

        # Set logger client
        global logger_client
        logger_client = mock_logger_client

        await shutdown_event()

        # Verify shutdown logging
        assert mock_logger_client.log_info.call_count >= 1

        info_call = mock_logger_client.log_info.call_args
        assert 'Mock Data Generator service shutting down' in info_call[0][0]

    @pytest.mark.asyncio
    async def test_logging_disabled_graceful_handling(self, client):
        """Test graceful handling when logging is disabled."""
        # Set logger client to None
        global logger_client
        logger_client = None

        # Mock the generator
        with patch('main.generator') as mock_generator:
            mock_data = {"id": "test", "content": "Test content"}
            mock_generator.generate_with_llm.return_value = mock_data
            mock_generator.store_in_doc_store.return_value = None

            # Make request - should still work without logging
            request_data = {
                "data_type": "source_code",
                "count": 1,
                "store_in_doc_store": False
            }

            response = client.post("/generate", json=request_data)
            assert response.status_code == 200

    def test_request_id_generation(self, client, mock_logger_client):
        """Test that request IDs are properly generated."""
        with patch('main.generator') as mock_generator:
            mock_data = {"id": "test", "content": "Test content"}
            mock_generator.generate_with_llm.return_value = mock_data
            mock_generator.store_in_doc_store.return_value = None

            request_data = {
                "data_type": "source_code",
                "count": 1,
                "store_in_doc_store": False
            }

            client.post("/generate", json=request_data)

            # Check that request IDs are generated and used consistently
            business_calls = mock_logger_client.log_business_event.call_args_list
            perf_calls = mock_logger_client.log_performance_metric.call_args_list

            # Extract request IDs from all calls
            request_ids = set()
            for call in business_calls + perf_calls:
                if len(call[0]) > 1 and isinstance(call[0][1], dict):
                    request_id = call[0][1].get('request_id')
                    if request_id:
                        request_ids.add(request_id)

            # All calls should use the same request ID
            assert len(request_ids) == 1
            request_id = list(request_ids)[0]
            assert request_id.startswith('mock_gen_')

    @pytest.mark.asyncio
    async def test_performance_metric_accuracy(self, client, mock_logger_client):
        """Test that performance metrics are accurately measured."""
        with patch('main.generator') as mock_generator:
            mock_data = {"id": "test", "content": "Test content"}
            mock_generator.generate_with_llm.return_value = mock_data
            mock_generator.store_in_doc_store.return_value = None

            # Add small delay to ensure measurable processing time
            await asyncio.sleep(0.01)

            request_data = {
                "data_type": "source_code",
                "count": 1,
                "store_in_doc_store": False
            }

            response = client.post("/generate", json=request_data)
            assert response.status_code == 200

            # Check performance metric
            perf_call = mock_logger_client.log_performance_metric.call_args
            processing_time = perf_call[0][1]

            # Processing time should be reasonable (between 0 and 1 second)
            assert 0 <= processing_time <= 1

            # Should be at least the sleep time we added
            assert processing_time >= 0.01

    @pytest.mark.asyncio
    async def test_bulk_request_id_generation(self, client, mock_logger_client):
        """Test that bulk collection request IDs are properly generated."""
        with patch('main.generator') as mock_generator:
            mock_response = MagicMock()
            mock_response.documents_created = [{"id": "test"}]
            mock_response.stored_documents = ["doc_1"]
            mock_generator.generate_bulk_collection.return_value = mock_response

            request_data = {
                "name": "test_bulk",
                "distribution": {"source_code": 1},
                "store_in_doc_store": True
            }

            client.post("/collections/generate", json=request_data)

            # Check that request IDs are generated and used consistently
            business_calls = mock_logger_client.log_business_event.call_args_list
            perf_calls = mock_logger_client.log_performance_metric.call_args_list

            # Extract request IDs from all calls
            request_ids = set()
            for call in business_calls + perf_calls:
                if len(call[0]) > 1 and isinstance(call[0][1], dict):
                    request_id = call[0][1].get('request_id')
                    if request_id:
                        request_ids.add(request_id)

            # All calls should use the same request ID
            assert len(request_ids) == 1
            request_id = list(request_ids)[0]
            assert request_id.startswith('bulk_gen_')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
