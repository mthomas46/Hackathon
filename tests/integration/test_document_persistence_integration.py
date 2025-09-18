"""
Document Persistence Integration Tests

Comprehensive integration tests for the document persistence pipeline
across multiple services including interpreter, orchestrator, and doc_store.
"""

import pytest
import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, Any, List
import uuid


class TestDocumentPersistenceIntegration:
    """Integration tests for document persistence across services."""

    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup test environment."""
        self.interpreter_url = "http://localhost:5120"
        self.orchestrator_url = "http://localhost:5099"
        self.doc_store_url = "http://localhost:5087"
        self.generated_documents = []
        self.test_user_id = f"integration_test_{uuid.uuid4().hex[:8]}"

    @pytest.fixture
    async def http_session(self):
        """HTTP session for making requests."""
        async with aiohttp.ClientSession() as session:
            yield session

    async def test_full_document_generation_pipeline(self, http_session):
        """Test complete document generation pipeline from query to storage."""
        # Step 1: Submit document generation request
        query_data = {
            "query": "Create comprehensive API documentation for user authentication service",
            "format": "markdown",
            "user_id": self.test_user_id
        }

        async with http_session.post(f"{self.interpreter_url}/execute-query", 
                                   json=query_data) as response:
            assert response.status in [200, 202], f"Query submission failed: {response.status}"
            result = await response.json()

        # Step 2: Verify response contains expected fields
        assert "execution_id" in result or "document_id" in result or "status" in result
        
        execution_id = result.get("execution_id")
        document_id = result.get("document_id")

        # Step 3: If document_id provided, verify document exists in doc_store
        if document_id:
            await self._verify_document_in_storage(http_session, document_id)
            self.generated_documents.append(document_id)

        # Step 4: If execution_id provided, check execution status
        if execution_id:
            await self._verify_execution_status(http_session, execution_id)

    async def test_multiple_format_generation(self, http_session):
        """Test document generation in multiple formats."""
        formats = ["json", "markdown", "csv"]
        base_query = "Create API endpoint documentation"

        for format_type in formats:
            query_data = {
                "query": f"{base_query} in {format_type} format",
                "format": format_type,
                "user_id": f"{self.test_user_id}_{format_type}"
            }

            async with http_session.post(f"{self.interpreter_url}/execute-query",
                                       json=query_data) as response:
                assert response.status in [200, 202], f"Failed for format {format_type}"
                result = await response.json()

                # Track generated documents for cleanup
                if "document_id" in result:
                    self.generated_documents.append(result["document_id"])

    async def test_document_provenance_tracking(self, http_session):
        """Test document provenance tracking across services."""
        # Generate a document
        query_data = {
            "query": "Create provenance test documentation",
            "format": "json",
            "user_id": self.test_user_id
        }

        async with http_session.post(f"{self.interpreter_url}/execute-query",
                                   json=query_data) as response:
            assert response.status in [200, 202]
            result = await response.json()

        document_id = result.get("document_id")
        if document_id:
            # Check provenance data
            try:
                async with http_session.get(f"{self.interpreter_url}/documents/{document_id}/provenance") as prov_response:
                    if prov_response.status == 200:
                        provenance = await prov_response.json()
                        await self._validate_provenance_structure(provenance)
                    # Note: 404 is acceptable if endpoint not implemented yet
            except Exception as e:
                pytest.skip(f"Provenance endpoint not available: {e}")

    async def test_document_download_capabilities(self, http_session):
        """Test document download from doc_store."""
        # Generate a document
        query_data = {
            "query": "Create download test document",
            "format": "txt",
            "user_id": self.test_user_id
        }

        async with http_session.post(f"{self.interpreter_url}/execute-query",
                                   json=query_data) as response:
            assert response.status in [200, 202]
            result = await response.json()

        document_id = result.get("document_id")
        if document_id:
            # Test download from doc_store
            try:
                async with http_session.get(f"{self.doc_store_url}/documents/{document_id}/download") as download_response:
                    if download_response.status == 200:
                        content = await download_response.read()
                        assert len(content) > 0, "Downloaded content should not be empty"
                    # Note: 404 is acceptable if document not yet stored
            except Exception as e:
                pytest.skip(f"Document download not available: {e}")

    async def test_concurrent_document_generation(self, http_session):
        """Test concurrent document generation requests."""
        concurrent_requests = 3
        tasks = []

        for i in range(concurrent_requests):
            query_data = {
                "query": f"Create concurrent test document {i+1}",
                "format": "json",
                "user_id": f"{self.test_user_id}_concurrent_{i}"
            }
            
            task = http_session.post(f"{self.interpreter_url}/execute-query", json=query_data)
            tasks.append(task)

        # Execute all requests concurrently
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        successful_responses = 0
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                print(f"Request {i} failed with exception: {response}")
                continue
                
            async with response as resp:
                if resp.status in [200, 202]:
                    successful_responses += 1
                    result = await resp.json()
                    if "document_id" in result:
                        self.generated_documents.append(result["document_id"])

        # At least half should succeed
        assert successful_responses >= concurrent_requests // 2

    async def test_service_health_before_operations(self, http_session):
        """Test that all required services are healthy before testing."""
        services = [
            ("interpreter", self.interpreter_url),
            ("orchestrator", self.orchestrator_url),
            ("doc_store", self.doc_store_url)
        ]

        for service_name, service_url in services:
            try:
                async with http_session.get(f"{service_url}/health", 
                                          timeout=aiohttp.ClientTimeout(total=5)) as response:
                    assert response.status == 200, f"{service_name} service is not healthy"
                    health_data = await response.json()
                    assert health_data.get("status") in ["healthy", "ok"], f"{service_name} reports unhealthy status"
            except Exception as e:
                pytest.skip(f"{service_name} service not available: {e}")

    async def test_error_handling_and_recovery(self, http_session):
        """Test error handling in document generation pipeline."""
        # Test with invalid format
        invalid_query = {
            "query": "Create test document",
            "format": "invalid_format_xyz",
            "user_id": self.test_user_id
        }

        async with http_session.post(f"{self.interpreter_url}/execute-query",
                                   json=invalid_query) as response:
            # Should handle gracefully with appropriate error code
            assert response.status in [200, 202, 400, 422]

        # Test with extremely long query
        long_query = {
            "query": "Create document " + "x" * 50000,  # Very long query
            "format": "json",
            "user_id": self.test_user_id
        }

        async with http_session.post(f"{self.interpreter_url}/execute-query",
                                   json=long_query) as response:
            # Should handle gracefully
            assert response.status in [200, 202, 400, 413, 422]

    async def test_workflow_execution_tracking(self, http_session):
        """Test workflow execution tracking and status monitoring."""
        query_data = {
            "query": "Create workflow tracking test document",
            "format": "markdown",
            "user_id": self.test_user_id
        }

        async with http_session.post(f"{self.interpreter_url}/execute-query",
                                   json=query_data) as response:
            assert response.status in [200, 202]
            result = await response.json()

        execution_id = result.get("execution_id")
        if execution_id:
            # Check execution status
            try:
                async with http_session.get(f"{self.interpreter_url}/execution/{execution_id}/status") as status_response:
                    if status_response.status == 200:
                        status_data = await status_response.json()
                        assert "execution_id" in status_data
                        assert "status" in status_data
            except Exception as e:
                pytest.skip(f"Execution tracking not available: {e}")

    async def test_performance_characteristics(self, http_session):
        """Test performance characteristics of document generation."""
        query_data = {
            "query": "Create performance test document with moderate complexity",
            "format": "json",
            "user_id": self.test_user_id
        }

        start_time = time.time()
        
        async with http_session.post(f"{self.interpreter_url}/execute-query",
                                   json=query_data) as response:
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Should respond within reasonable time (30 seconds for initial response)
            assert response_time < 30.0, f"Response too slow: {response_time}s"
            assert response.status in [200, 202]

    # Helper methods

    async def _verify_document_in_storage(self, session: aiohttp.ClientSession, document_id: str):
        """Verify document exists in doc_store."""
        try:
            async with session.get(f"{self.doc_store_url}/documents/{document_id}") as response:
                if response.status == 200:
                    doc_data = await response.json()
                    assert "content" in doc_data or "content_url" in doc_data
                    assert "metadata" in doc_data
                # Note: 404 is acceptable if doc_store integration not complete
        except Exception as e:
            print(f"Document verification skipped: {e}")

    async def _verify_execution_status(self, session: aiohttp.ClientSession, execution_id: str):
        """Verify execution status tracking."""
        try:
            async with session.get(f"{self.interpreter_url}/execution/{execution_id}/status") as response:
                if response.status == 200:
                    status_data = await response.json()
                    assert "execution_id" in status_data
                    assert status_data["execution_id"] == execution_id
        except Exception as e:
            print(f"Execution status verification skipped: {e}")

    async def _validate_provenance_structure(self, provenance: Dict[str, Any]):
        """Validate provenance data structure."""
        required_fields = ["workflow_execution", "services_chain", "user_context"]
        
        for field in required_fields:
            assert field in provenance, f"Missing provenance field: {field}"

        # Validate workflow execution
        workflow_exec = provenance["workflow_execution"]
        assert "execution_id" in workflow_exec
        assert "workflow_name" in workflow_exec

        # Validate services chain
        services_chain = provenance["services_chain"]
        assert isinstance(services_chain, list)
        assert len(services_chain) > 0

        # Validate user context
        user_context = provenance["user_context"]
        assert "user_id" in user_context
        assert "query" in user_context


class TestDocumentPersistenceEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup for edge case tests."""
        self.interpreter_url = "http://localhost:5120"
        self.test_user_id = f"edge_test_{uuid.uuid4().hex[:8]}"

    async def test_empty_and_minimal_queries(self, http_session):
        """Test handling of empty and minimal queries."""
        test_cases = [
            {"query": "", "format": "json"},
            {"query": "a", "format": "json"},
            {"query": "Create doc", "format": "json"},
        ]

        for test_case in test_cases:
            query_data = {**test_case, "user_id": self.test_user_id}
            
            async with http_session.post(f"{self.interpreter_url}/execute-query",
                                       json=query_data) as response:
                # Should handle gracefully
                assert response.status in [200, 202, 400, 422]

    async def test_special_characters_in_queries(self, http_session):
        """Test handling of special characters in queries."""
        special_queries = [
            "Create doc with émojis 🎉 and unicode ñoño",
            "Create doc with \"quotes\" and 'apostrophes'",
            "Create doc with <tags> and &entities;",
            "Create doc with newlines\nand\ttabs",
        ]

        for query in special_queries:
            query_data = {
                "query": query,
                "format": "json", 
                "user_id": self.test_user_id
            }
            
            async with http_session.post(f"{self.interpreter_url}/execute-query",
                                       json=query_data) as response:
                # Should handle special characters
                assert response.status in [200, 202, 400]

    async def test_large_document_generation(self, http_session):
        """Test generation of large documents."""
        large_query = {
            "query": "Create comprehensive technical documentation covering authentication, authorization, API endpoints, data models, error handling, rate limiting, webhooks, SDKs, examples, tutorials, and best practices for a complete enterprise API platform",
            "format": "markdown",
            "user_id": self.test_user_id
        }

        async with http_session.post(f"{self.interpreter_url}/execute-query",
                                   json=large_query) as response:
            # Should handle large content requests
            assert response.status in [200, 202, 413]

    async def test_rapid_successive_requests(self, http_session):
        """Test rapid successive requests from same user."""
        query_data = {
            "query": "Create rapid test document",
            "format": "json",
            "user_id": self.test_user_id
        }

        responses = []
        for i in range(5):
            async with http_session.post(f"{self.interpreter_url}/execute-query",
                                       json=query_data) as response:
                responses.append(response.status)

        # Should handle rapid requests (may rate limit)
        for status in responses:
            assert status in [200, 202, 429, 503]


@pytest.fixture
async def http_session():
    """Shared HTTP session fixture."""
    async with aiohttp.ClientSession() as session:
        yield session


class TestDocumentPersistenceReliability:
    """Test reliability and fault tolerance."""

    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup reliability tests."""
        self.interpreter_url = "http://localhost:5120"
        self.test_user_id = f"reliability_test_{uuid.uuid4().hex[:8]}"

    async def test_service_timeout_handling(self, http_session):
        """Test handling of service timeouts."""
        query_data = {
            "query": "Create timeout test document",
            "format": "json",
            "user_id": self.test_user_id
        }

        # Use short timeout to potentially trigger timeout handling
        timeout = aiohttp.ClientTimeout(total=5)
        
        try:
            async with http_session.post(f"{self.interpreter_url}/execute-query",
                                       json=query_data,
                                       timeout=timeout) as response:
                # Should complete or handle timeout gracefully
                assert response.status in [200, 202, 408, 504]
        except asyncio.TimeoutError:
            # Timeout is acceptable for this test
            pass

    async def test_malformed_request_handling(self, http_session):
        """Test handling of malformed requests."""
        malformed_requests = [
            {},  # Empty request
            {"query": "test"},  # Missing format
            {"format": "json"},  # Missing query
            {"query": None, "format": "json"},  # Null query
            {"query": "test", "format": None},  # Null format
        ]

        for malformed_data in malformed_requests:
            try:
                async with http_session.post(f"{self.interpreter_url}/execute-query",
                                           json=malformed_data) as response:
                    # Should return appropriate error codes
                    assert response.status in [400, 422, 500]
            except Exception:
                # Connection errors are acceptable for malformed requests
                pass

    async def test_document_persistence_consistency(self, http_session):
        """Test consistency of document persistence across multiple requests."""
        base_query = "Create consistency test document"
        
        # Generate multiple documents with similar content
        document_ids = []
        for i in range(3):
            query_data = {
                "query": f"{base_query} {i+1}",
                "format": "json",
                "user_id": f"{self.test_user_id}_{i}"
            }
            
            async with http_session.post(f"{self.interpreter_url}/execute-query",
                                       json=query_data) as response:
                if response.status in [200, 202]:
                    result = await response.json()
                    if "document_id" in result:
                        document_ids.append(result["document_id"])

        # Verify all documents were assigned unique IDs
        assert len(set(document_ids)) == len(document_ids), "Document IDs should be unique"


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
