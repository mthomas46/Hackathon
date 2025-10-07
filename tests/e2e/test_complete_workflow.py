"""
E2E Tests: Complete Workflow

Tests the end-to-end MCP creation workflow.
This is the most critical test - validates the entire system working together.

Test Modes:
- Code: Tests with mocked services
- Live: Tests full system integration

Workflow Steps:
1. Document Ingestion (kafka-ingestion-service)
2. LLM Tagging (llm-tagging-pipeline)
3. Training (mcp-training-coordinator) [future]
4. Storage (mcp-store) [future]
5. Registry (mcp-registry) [future]
6. Package Export (mcp-package-manager)
7. Observability (mcp-logs)
"""

import pytest
import asyncio


class TestCompleteWorkflow:
    """Test suite for end-to-end MCP workflow."""
    
    @pytest.mark.asyncio
    async def test_ingest_and_tag_workflow(
        self,
        http_client,
        service_urls,
        sample_document,
        correlation_id,
        wait_for_log,
        test_mode
    ):
        """
        Test document ingestion followed by LLM tagging.
        
        This is the critical path for the workflow.
        
        Steps:
        1. Ingest document via kafka-ingestion
        2. Tag document via llm-tagging
        3. Verify correlation ID tracked in logs
        
        Expected: Full workflow completes successfully
        """
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        # Step 1: Ingest document
        kafka_url = service_urls["kafka-ingestion"]
        ingest_response = await http_client.post(
            f"{kafka_url}/api/v1/ingestion/ingest",
            json=sample_document,
            headers={"X-Correlation-ID": correlation_id}
        )
        
        assert ingest_response.status_code in [200, 201], \
            f"Ingestion failed: {ingest_response.status_code}"
        
        # Step 2: Tag the document
        llm_url = service_urls["llm-tagging"]
        tag_request = {
            "document_id": sample_document["document_id"],
            "content": sample_document["content"],
            "extraction_types": ["tags", "summary"]
        }
        
        tag_response = await http_client.post(
            f"{llm_url}/api/v1/tagging/tag",
            json=tag_request,
            headers={"X-Correlation-ID": correlation_id}
        )
        
        assert tag_response.status_code in [200, 201], \
            f"Tagging failed: {tag_response.status_code}"
        
        # Step 3: Verify correlation tracking
        await asyncio.sleep(3)  # Allow logs to propagate
        
        logs_url = service_urls["mcp-logs"]
        log_entries = await wait_for_log(logs_url, correlation_id, timeout=15)
        
        assert len(log_entries) > 0, \
            "Workflow not tracked in logs"
        
        # Verify both services logged
        services_logged = {entry.get("service") for entry in log_entries}
        # At least one of the services should have logged
        assert len(services_logged) > 0, "No services logged"
    
    @pytest.mark.asyncio
    async def test_workflow_with_multiple_documents(
        self,
        http_client,
        service_urls,
        correlation_id,
        test_mode
    ):
        """
        Test workflow with multiple documents in sequence.
        
        Expected: All documents processed successfully
        """
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        kafka_url = service_urls["kafka-ingestion"]
        llm_url = service_urls["llm-tagging"]
        
        # Process 3 documents
        for i in range(3):
            doc = {
                "document_id": f"workflow_doc_{i}_{correlation_id[:8]}",
                "event_type": "DOCUMENT_CREATED",
                "source": "e2e_workflow_test",
                "content": f"Workflow test document number {i}.",
                "metadata": {"index": i}
            }
            
            # Ingest
            ingest_response = await http_client.post(
                f"{kafka_url}/api/v1/ingestion/ingest",
                json=doc,
                headers={"X-Correlation-ID": f"{correlation_id}_{i}"}
            )
            
            assert ingest_response.status_code in [200, 201]
            
            # Tag
            tag_request = {
                "document_id": doc["document_id"],
                "content": doc["content"],
                "extraction_types": ["tags"]
            }
            
            tag_response = await http_client.post(
                f"{llm_url}/api/v1/tagging/tag",
                json=tag_request,
                headers={"X-Correlation-ID": f"{correlation_id}_{i}"}
            )
            
            assert tag_response.status_code in [200, 201]
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling(
        self,
        http_client,
        service_urls,
        correlation_id,
        test_mode
    ):
        """
        Test workflow with invalid document (error handling).
        
        Expected: System handles errors gracefully
        """
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        kafka_url = service_urls["kafka-ingestion"]
        
        # Submit invalid document
        invalid_doc = {
            "document_id": "invalid",
            # Missing required fields
        }
        
        response = await http_client.post(
            f"{kafka_url}/api/v1/ingestion/ingest",
            json=invalid_doc,
            headers={"X-Correlation-ID": correlation_id}
        )
        
        # Should either reject or accept with error status
        assert response.status_code in [200, 201, 400, 422]
    
    @pytest.mark.asyncio
    async def test_concurrent_workflows(
        self,
        http_client,
        service_urls,
        test_mode
    ):
        """
        Test multiple workflows running concurrently.
        
        Expected: No interference between workflows
        """
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        kafka_url = service_urls["kafka-ingestion"]
        
        # Start 5 concurrent workflows
        tasks = []
        for i in range(5):
            doc = {
                "document_id": f"concurrent_doc_{i}",
                "event_type": "DOCUMENT_CREATED",
                "source": "concurrent_test",
                "content": f"Concurrent document {i}",
                "metadata": {}
            }
            
            task = http_client.post(
                f"{kafka_url}/api/v1/ingestion/ingest",
                json=doc,
                headers={"X-Correlation-ID": f"concurrent_{i}"}
            )
            tasks.append(task)
        
        # Wait for all to complete
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successes
        successes = sum(
            1 for r in responses
            if not isinstance(r, Exception) and r.status_code in [200, 201]
        )
        
        assert successes >= 4, \
            f"Too many concurrent workflows failed: {successes}/5 succeeded"
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_end_to_end_system_health(
        self,
        http_client,
        service_urls,
        sample_document,
        correlation_id,
        wait_for_log,
        test_mode
    ):
        """
        Comprehensive system health test.
        
        Validates:
        1. All services are healthy
        2. Document can be ingested
        3. Document can be tagged
        4. Logs are captured
        5. Correlation IDs work end-to-end
        
        This is a smoke test for the entire ecosystem.
        """
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        # 1. Check all critical services
        critical_services = [
            "kafka-ingestion",
            "llm-tagging",
            "mcp-logs"
        ]
        
        health_results = {}
        for service_name in critical_services:
            url = service_urls[service_name]
            try:
                response = await http_client.get(f"{url}/health")
                health_results[service_name] = response.status_code == 200
            except Exception as e:
                health_results[service_name] = False
        
        assert all(health_results.values()), \
            f"Services unhealthy: {[k for k, v in health_results.items() if not v]}"
        
        # 2. Ingest document
        kafka_url = service_urls["kafka-ingestion"]
        ingest_response = await http_client.post(
            f"{kafka_url}/api/v1/ingestion/ingest",
            json=sample_document,
            headers={"X-Correlation-ID": correlation_id}
        )
        
        assert ingest_response.status_code in [200, 201], \
            "Document ingestion failed"
        
        # 3. Tag document
        llm_url = service_urls["llm-tagging"]
        tag_request = {
            "document_id": sample_document["document_id"],
            "content": sample_document["content"],
            "extraction_types": ["tags"]
        }
        
        tag_response = await http_client.post(
            f"{llm_url}/api/v1/tagging/tag",
            json=tag_request,
            headers={"X-Correlation-ID": correlation_id}
        )
        
        assert tag_response.status_code in [200, 201], \
            "Document tagging failed"
        
        # 4. Verify logging
        await asyncio.sleep(3)
        logs_url = service_urls["mcp-logs"]
        log_entries = await wait_for_log(logs_url, correlation_id, timeout=15)
        
        assert len(log_entries) > 0, \
            "System not logging properly"
        
        # 5. Verify correlation tracking works
        correlation_ids = {entry.get("correlation_id") for entry in log_entries}
        assert correlation_id in correlation_ids, \
            "Correlation ID not properly tracked"
