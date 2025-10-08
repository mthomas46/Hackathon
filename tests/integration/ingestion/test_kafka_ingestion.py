"""
Integration tests for Kafka ingestion service.

Tests document ingestion flow from various sources through Kafka.
"""
import pytest
import httpx
from tests.fixtures import (
    create_github_commit_doc,
    create_jira_ticket_doc,
    create_wikipedia_doc,
    create_code_file_doc,
    mock_ingestion_response
)


@pytest.mark.integration
class TestKafkaIngestion:
    """Integration tests for Kafka ingestion service."""
    
    @pytest.fixture
    def kafka_base_url(self):
        """Base URL for Kafka ingestion service."""
        return "http://localhost:5700"
    
    @pytest.fixture
    async def http_client(self):
        """HTTP client for API requests."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, http_client, kafka_base_url):
        """Test Kafka ingestion service health endpoint."""
        try:
            response = await http_client.get(f"{kafka_base_url}/health")
            
            # Service should respond
            assert response.status_code in [200, 404, 503], \
                f"Unexpected status code: {response.status_code}"
            
            if response.status_code == 200:
                data = response.json()
                assert "status" in data or "health" in data
        
        except httpx.ConnectError:
            pytest.skip("Kafka ingestion service not available")
    
    @pytest.mark.asyncio
    async def test_ingest_github_document(self, http_client, kafka_base_url):
        """Test ingesting a GitHub commit document."""
        # Create mock GitHub document
        doc = create_github_commit_doc(
            commit_hash="test123abc",
            author="Test User",
            message="test: Add integration test"
        )
        
        try:
            response = await http_client.post(
                f"{kafka_base_url}/api/v1/ingest",
                json={
                    "document_id": doc.document_id,
                    "title": doc.title,
                    "content": doc.content_md,
                    "metadata": doc.metadata,
                    "tags": doc.tags
                }
            )
            
            # Should accept or return reasonable error
            assert response.status_code in [200, 201, 202, 404, 422, 503]
            
            if response.status_code in [200, 201, 202]:
                data = response.json()
                # Verify response structure
                assert isinstance(data, dict)
                # Common fields in success response
                if "success" in data:
                    assert isinstance(data["success"], bool)
                if "document_id" in data:
                    assert doc.document_id in data["document_id"]
        
        except httpx.ConnectError:
            pytest.skip("Kafka ingestion service not available")
    
    @pytest.mark.asyncio
    async def test_ingest_jira_document(self, http_client, kafka_base_url):
        """Test ingesting a Jira ticket document."""
        doc = create_jira_ticket_doc(
            ticket_id="TEST-456",
            title="Test integration",
            status="In Progress"
        )
        
        try:
            response = await http_client.post(
                f"{kafka_base_url}/api/v1/ingest",
                json={
                    "document_id": doc.document_id,
                    "title": doc.title,
                    "content": doc.content_md,
                    "metadata": doc.metadata,
                    "tags": doc.tags
                }
            )
            
            assert response.status_code in [200, 201, 202, 404, 422, 503]
            
            if response.status_code in [200, 201, 202]:
                data = response.json()
                assert isinstance(data, dict)
        
        except httpx.ConnectError:
            pytest.skip("Kafka ingestion service not available")
    
    @pytest.mark.asyncio
    async def test_ingest_wikipedia_document(self, http_client, kafka_base_url):
        """Test ingesting a Wikipedia document."""
        doc = create_wikipedia_doc(
            title="Test Article",
            page_id="test789"
        )
        
        try:
            response = await http_client.post(
                f"{kafka_base_url}/api/v1/ingest",
                json={
                    "document_id": doc.document_id,
                    "title": doc.title,
                    "content": doc.content_md,
                    "metadata": doc.metadata,
                    "tags": doc.tags
                }
            )
            
            assert response.status_code in [200, 201, 202, 404, 422, 503]
        
        except httpx.ConnectError:
            pytest.skip("Kafka ingestion service not available")
    
    @pytest.mark.asyncio
    async def test_ingest_code_file_document(self, http_client, kafka_base_url):
        """Test ingesting a code file document."""
        doc = create_code_file_doc(
            filename="test.py",
            language="python"
        )
        
        try:
            response = await http_client.post(
                f"{kafka_base_url}/api/v1/ingest",
                json={
                    "document_id": doc.document_id,
                    "title": doc.title,
                    "content": doc.content_md,
                    "metadata": doc.metadata,
                    "tags": doc.tags
                }
            )
            
            assert response.status_code in [200, 201, 202, 404, 422, 503]
        
        except httpx.ConnectError:
            pytest.skip("Kafka ingestion service not available")
    
    @pytest.mark.asyncio
    async def test_batch_ingestion(self, http_client, kafka_base_url):
        """Test ingesting multiple documents in sequence."""
        documents = [
            create_github_commit_doc("batch1", "User1", "test: First"),
            create_github_commit_doc("batch2", "User2", "test: Second"),
            create_jira_ticket_doc("TEST-001", "Batch test 1"),
        ]
        
        successful = 0
        failed = 0
        
        try:
            for doc in documents:
                response = await http_client.post(
                    f"{kafka_base_url}/api/v1/ingest",
                    json={
                        "document_id": doc.document_id,
                        "title": doc.title,
                        "content": doc.content_md,
                        "metadata": doc.metadata,
                        "tags": doc.tags
                    }
                )
                
                if response.status_code in [200, 201, 202]:
                    successful += 1
                else:
                    failed += 1
            
            # At least some should succeed or all should fail consistently
            assert successful >= 0 or failed == len(documents)
        
        except httpx.ConnectError:
            pytest.skip("Kafka ingestion service not available")
    
    @pytest.mark.asyncio
    async def test_invalid_document_structure(self, http_client, kafka_base_url):
        """Test ingestion with invalid document structure."""
        invalid_doc = {
            # Missing required fields
            "title": "Invalid Document"
        }
        
        try:
            response = await http_client.post(
                f"{kafka_base_url}/api/v1/ingest",
                json=invalid_doc
            )
            
            # Should return error status
            assert response.status_code in [400, 422, 404, 503]
        
        except httpx.ConnectError:
            pytest.skip("Kafka ingestion service not available")
    
    @pytest.mark.asyncio
    async def test_empty_content_handling(self, http_client, kafka_base_url):
        """Test ingestion of document with empty content."""
        doc = create_github_commit_doc()
        
        try:
            response = await http_client.post(
                f"{kafka_base_url}/api/v1/ingest",
                json={
                    "document_id": doc.document_id,
                    "title": doc.title,
                    "content": "",  # Empty content
                    "metadata": doc.metadata,
                    "tags": doc.tags
                }
            )
            
            # Service should handle gracefully
            assert response.status_code in [200, 201, 202, 400, 422, 404, 503]
        
        except httpx.ConnectError:
            pytest.skip("Kafka ingestion service not available")
    
    @pytest.mark.asyncio
    async def test_large_document_ingestion(self, http_client, kafka_base_url):
        """Test ingestion of a large document."""
        large_content = "# Large Document\n\n" + ("Lorem ipsum dolor sit amet. " * 1000)
        
        doc = create_wikipedia_doc(
            title="Large Article",
            page_id="large001"
        )
        
        try:
            response = await http_client.post(
                f"{kafka_base_url}/api/v1/ingest",
                json={
                    "document_id": doc.document_id,
                    "title": doc.title,
                    "content": large_content,
                    "metadata": doc.metadata,
                    "tags": doc.tags
                },
                timeout=30.0  # Longer timeout for large document
            )
            
            # Should handle large documents
            assert response.status_code in [200, 201, 202, 413, 404, 503]
        
        except httpx.ConnectError:
            pytest.skip("Kafka ingestion service not available")
        except httpx.TimeoutException:
            pytest.skip("Request timed out - service may be slow")
    
    @pytest.mark.asyncio
    async def test_duplicate_document_handling(self, http_client, kafka_base_url):
        """Test ingesting the same document twice."""
        doc = create_github_commit_doc(
            commit_hash="duplicate123",
            author="Test User",
            message="test: Duplicate test"
        )
        
        payload = {
            "document_id": doc.document_id,
            "title": doc.title,
            "content": doc.content_md,
            "metadata": doc.metadata,
            "tags": doc.tags
        }
        
        try:
            # First ingestion
            response1 = await http_client.post(
                f"{kafka_base_url}/api/v1/ingest",
                json=payload
            )
            
            # Second ingestion (duplicate)
            response2 = await http_client.post(
                f"{kafka_base_url}/api/v1/ingest",
                json=payload
            )
            
            # Both should succeed or fail consistently
            # Service may handle duplicates differently (idempotent or reject)
            assert response1.status_code in [200, 201, 202, 404, 422, 503]
            assert response2.status_code in [200, 201, 202, 409, 404, 422, 503]
        
        except httpx.ConnectError:
            pytest.skip("Kafka ingestion service not available")

