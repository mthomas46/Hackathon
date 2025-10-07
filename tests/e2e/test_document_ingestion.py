"""
E2E Tests: Document Ingestion

Tests the complete document ingestion workflow through kafka-ingestion-service.
Mimics STEP 3 of demo_mcp_workflow_validation.py.

Test Modes:
- Code: Tests ingestion service logic with mocked Kafka/Redis
- Live: Tests full workflow with real Kafka/Redis
"""

import pytest
import asyncio


class TestDocumentIngestion:
    """Test suite for document ingestion workflow."""
    
    @pytest.mark.asyncio
    async def test_ingest_single_document(
        self,
        http_client,
        service_urls,
        sample_document,
        correlation_id,
        test_mode
    ):
        """
        Test successful ingestion of a single document.
        
        Steps:
        1. Submit document to kafka-ingestion
        2. Verify 200/201 response
        3. Check response contains document_id
        
        Expected: Document accepted for ingestion
        """
        url = service_urls["kafka-ingestion"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        response = await http_client.post(
            f"{url}/api/v1/ingestion/ingest",
            json=sample_document,
            headers={"X-Correlation-ID": correlation_id}
        )
        
        assert response.status_code in [200, 201], \
            f"Ingestion failed with status {response.status_code}: {response.text}"
        
        data = response.json()
        assert "document_id" in data or "status" in data, \
            "Response missing expected fields"
    
    @pytest.mark.asyncio
    async def test_ingest_large_document(
        self,
        http_client,
        service_urls,
        sample_large_document,
        correlation_id,
        test_mode
    ):
        """
        Test ingestion of a large document (>100KB).
        
        Expected: Document accepted, no size rejection
        """
        url = service_urls["kafka-ingestion"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        response = await http_client.post(
            f"{url}/api/v1/ingestion/ingest",
            json=sample_large_document,
            headers={"X-Correlation-ID": correlation_id}
        )
        
        assert response.status_code in [200, 201], \
            f"Large document ingestion failed: {response.status_code}"
    
    @pytest.mark.asyncio
    async def test_ingest_invalid_document(
        self,
        http_client,
        service_urls,
        correlation_id,
        test_mode
    ):
        """
        Test ingestion of invalid document (missing required fields).
        
        Expected: 400 Bad Request or graceful error
        """
        url = service_urls["kafka-ingestion"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        invalid_document = {
            "document_id": "invalid_doc",
            # Missing required fields
        }
        
        response = await http_client.post(
            f"{url}/api/v1/ingestion/ingest",
            json=invalid_document,
            headers={"X-Correlation-ID": correlation_id}
        )
        
        # Should either reject (400) or accept with error status
        assert response.status_code in [400, 422, 200, 201], \
            f"Unexpected status code: {response.status_code}"
    
    @pytest.mark.asyncio
    async def test_ingest_batch_documents(
        self,
        http_client,
        service_urls,
        correlation_id,
        test_mode
    ):
        """
        Test batch ingestion of multiple documents.
        
        Expected: All documents accepted
        """
        url = service_urls["kafka-ingestion"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        # Ingest 5 documents sequentially
        results = []
        for i in range(5):
            doc = {
                "document_id": f"batch_doc_{i}",
                "event_type": "DOCUMENT_CREATED",
                "source": "e2e_test",
                "content": f"Batch test document {i}",
                "metadata": {"index": i}
            }
            
            response = await http_client.post(
                f"{url}/api/v1/ingestion/ingest",
                json=doc,
                headers={"X-Correlation-ID": correlation_id}
            )
            
            results.append(response.status_code in [200, 201])
        
        assert all(results), \
            f"Some documents failed to ingest: {sum(results)}/5 succeeded"
    
    @pytest.mark.asyncio
    async def test_ingestion_idempotency(
        self,
        http_client,
        service_urls,
        sample_document,
        correlation_id,
        test_mode
    ):
        """
        Test that ingesting the same document twice is idempotent.
        
        Expected: Both requests succeed (or second returns existing)
        """
        url = service_urls["kafka-ingestion"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        # First ingestion
        response1 = await http_client.post(
            f"{url}/api/v1/ingestion/ingest",
            json=sample_document,
            headers={"X-Correlation-ID": correlation_id}
        )
        
        assert response1.status_code in [200, 201]
        
        # Second ingestion (same document)
        response2 = await http_client.post(
            f"{url}/api/v1/ingestion/ingest",
            json=sample_document,
            headers={"X-Correlation-ID": correlation_id}
        )
        
        # Should either succeed or indicate duplicate
        assert response2.status_code in [200, 201, 409], \
            f"Unexpected status for duplicate: {response2.status_code}"
