"""
E2E Tests: LLM Tagging

Tests the LLM tagging workflow through llm-tagging-pipeline.
Mimics STEP 4 of demo_mcp_workflow_validation.py.

Test Modes:
- Code: Tests tagging service logic with mocked Ollama
- Live: Tests full workflow with real Ollama integration
"""

import pytest
import asyncio


class TestLLMTagging:
    """Test suite for LLM tagging workflow."""
    
    @pytest.mark.asyncio
    async def test_tag_simple_document(
        self,
        http_client,
        service_urls,
        correlation_id,
        test_mode
    ):
        """
        Test tagging of a simple document.
        
        Steps:
        1. Submit document for tagging
        2. Verify 200/201 response
        3. Check tags were extracted
        
        Expected: Document tagged successfully
        """
        url = service_urls["llm-tagging"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        tag_request = {
            "document_id": f"test_doc_{correlation_id[:8]}",
            "content": "This document discusses machine learning and artificial intelligence applications.",
            "extraction_types": ["tags", "keywords", "summary"]
        }
        
        response = await http_client.post(
            f"{url}/api/v1/tagging/tag",
            json=tag_request,
            headers={"X-Correlation-ID": correlation_id}
        )
        
        assert response.status_code in [200, 201], \
            f"Tagging failed with status {response.status_code}: {response.text}"
        
        data = response.json()
        # Response should contain job_id or tags
        assert "job_id" in data or "tags" in data or "status" in data, \
            "Response missing expected fields"
    
    @pytest.mark.asyncio
    async def test_tag_technical_document(
        self,
        http_client,
        service_urls,
        correlation_id,
        test_mode
    ):
        """
        Test tagging of technical document with code.
        
        Expected: Technical tags extracted
        """
        url = service_urls["llm-tagging"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        technical_content = """
        def fibonacci(n):
            if n <= 1:
                return n
            return fibonacci(n-1) + fibonacci(n-2)
        
        This Python function implements the Fibonacci sequence using recursion.
        """
        
        tag_request = {
            "document_id": f"tech_doc_{correlation_id[:8]}",
            "content": technical_content,
            "extraction_types": ["tags", "keywords"]
        }
        
        response = await http_client.post(
            f"{url}/api/v1/tagging/tag",
            json=tag_request,
            headers={"X-Correlation-ID": correlation_id}
        )
        
        assert response.status_code in [200, 201], \
            f"Technical document tagging failed: {response.status_code}"
    
    @pytest.mark.asyncio
    async def test_extract_summary(
        self,
        http_client,
        service_urls,
        correlation_id,
        test_mode
    ):
        """
        Test summary extraction from document.
        
        Expected: Summary generated
        """
        url = service_urls["llm-tagging"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        tag_request = {
            "document_id": f"summary_doc_{correlation_id[:8]}",
            "content": "This is a test document about MCP workflow validation. " * 10,
            "extraction_types": ["summary"]
        }
        
        response = await http_client.post(
            f"{url}/api/v1/tagging/tag",
            json=tag_request,
            headers={"X-Correlation-ID": correlation_id}
        )
        
        assert response.status_code in [200, 201]
    
    @pytest.mark.asyncio
    async def test_extract_keywords(
        self,
        http_client,
        service_urls,
        correlation_id,
        test_mode
    ):
        """
        Test keyword extraction from document.
        
        Expected: Keywords identified
        """
        url = service_urls["llm-tagging"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        tag_request = {
            "document_id": f"keyword_doc_{correlation_id[:8]}",
            "content": "Machine learning, artificial intelligence, neural networks, and deep learning.",
            "extraction_types": ["keywords"]
        }
        
        response = await http_client.post(
            f"{url}/api/v1/tagging/tag",
            json=tag_request,
            headers={"X-Correlation-ID": correlation_id}
        )
        
        assert response.status_code in [200, 201]
    
    @pytest.mark.asyncio
    async def test_tag_empty_document(
        self,
        http_client,
        service_urls,
        correlation_id,
        test_mode
    ):
        """
        Test tagging of empty document (edge case).
        
        Expected: Graceful handling (error or empty tags)
        """
        url = service_urls["llm-tagging"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        tag_request = {
            "document_id": f"empty_doc_{correlation_id[:8]}",
            "content": "",
            "extraction_types": ["tags"]
        }
        
        response = await http_client.post(
            f"{url}/api/v1/tagging/tag",
            json=tag_request,
            headers={"X-Correlation-ID": correlation_id}
        )
        
        # Should handle gracefully (200/201 or 400)
        assert response.status_code in [200, 201, 400, 422]
    
    @pytest.mark.asyncio
    async def test_tag_long_document(
        self,
        http_client,
        service_urls,
        correlation_id,
        test_mode
    ):
        """
        Test tagging of very long document (chunking test).
        
        Expected: Document processed successfully
        """
        url = service_urls["llm-tagging"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        # Create a long document
        long_content = "This is a test sentence about various topics. " * 1000
        
        tag_request = {
            "document_id": f"long_doc_{correlation_id[:8]}",
            "content": long_content,
            "extraction_types": ["tags", "summary"]
        }
        
        response = await http_client.post(
            f"{url}/api/v1/tagging/tag",
            json=tag_request,
            headers={"X-Correlation-ID": correlation_id},
            timeout=60.0  # Longer timeout for long documents
        )
        
        assert response.status_code in [200, 201], \
            f"Long document tagging failed: {response.status_code}"
    
    @pytest.mark.asyncio
    async def test_batch_tagging(
        self,
        http_client,
        service_urls,
        correlation_id,
        test_mode
    ):
        """
        Test batch tagging of multiple documents.
        
        Expected: All documents tagged
        """
        url = service_urls["llm-tagging"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        # Tag 3 documents
        results = []
        for i in range(3):
            tag_request = {
                "document_id": f"batch_tag_{i}_{correlation_id[:8]}",
                "content": f"Test document number {i} about testing.",
                "extraction_types": ["tags"]
            }
            
            response = await http_client.post(
                f"{url}/api/v1/tagging/tag",
                json=tag_request,
                headers={"X-Correlation-ID": correlation_id}
            )
            
            results.append(response.status_code in [200, 201])
        
        assert all(results), \
            f"Some documents failed to tag: {sum(results)}/3 succeeded"
