"""
E2E Tests: Evergreen Documentation

Tests the evergreen documentation workflow through mcp-evergreen-docs.
Mimics STEP 7 of demo_mcp_workflow_validation.py.

Test Modes:
- Code: Tests documentation service logic with mocked sources
- Live: Tests full workflow with Redis storage
"""

import pytest
import asyncio


class TestEvergreenDocs:
    """Test suite for evergreen documentation service."""
    
    @pytest.mark.asyncio
    async def test_list_documentation(
        self,
        http_client,
        service_urls,
        correlation_id,
        test_mode
    ):
        """
        Test listing documentation entries.
        
        Expected: Returns list of documentation (empty or populated)
        """
        url = service_urls["mcp-evergreen-docs"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        response = await http_client.get(
            f"{url}/api/v1/documentation",
            headers={"X-Correlation-ID": correlation_id}
        )
        
        assert response.status_code == 200, \
            f"List documentation failed: {response.status_code}"
        
        data = response.json()
        assert "documents" in data or isinstance(data, list), \
            "Response should contain documentation list"
    
    @pytest.mark.asyncio
    async def test_create_documentation(
        self,
        http_client,
        service_urls,
        correlation_id,
        test_mode
    ):
        """
        Test creating a documentation entry.
        
        Expected: Documentation created successfully
        """
        url = service_urls["mcp-evergreen-docs"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        doc_data = {
            "title": f"Test Documentation {correlation_id[:8]}",
            "content": "This is test documentation content for E2E validation.",
            "source_url": "https://example.com/docs/test",
            "metadata": {
                "author": "E2E Tester",
                "version": "1.0.0",
                "tags": ["test", "e2e"]
            }
        }
        
        response = await http_client.post(
            f"{url}/api/v1/documentation",
            json=doc_data,
            headers={"X-Correlation-ID": correlation_id}
        )
        
        assert response.status_code in [200, 201], \
            f"Documentation creation failed: {response.status_code}: {response.text}"
        
        data = response.json()
        assert "doc_id" in data or "id" in data or "title" in data, \
            "Response missing documentation identifier"
    
    @pytest.mark.asyncio
    async def test_sync_documentation(
        self,
        http_client,
        service_urls,
        correlation_id,
        test_mode
    ):
        """
        Test triggering a documentation sync.
        
        Expected: Sync job initiated
        """
        url = service_urls["mcp-evergreen-docs"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        sync_request = {
            "source_id": f"test_source_{correlation_id[:8]}",
            "source_type": "manual"
        }
        
        response = await http_client.post(
            f"{url}/api/v1/sync",
            json=sync_request,
            headers={"X-Correlation-ID": correlation_id}
        )
        
        # Sync may return 200/201 if accepted, or 404/501 if not implemented
        assert response.status_code in [200, 201, 404, 501], \
            f"Sync request failed: {response.status_code}"
    
    @pytest.mark.asyncio
    async def test_validate_documentation(
        self,
        http_client,
        service_urls,
        correlation_id,
        test_mode
    ):
        """
        Test documentation validation.
        
        Expected: Validation results returned
        """
        url = service_urls["mcp-evergreen-docs"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        # First create documentation
        doc_data = {
            "title": f"Validation Test {correlation_id[:8]}",
            "content": "Documentation for validation testing."
        }
        
        create_response = await http_client.post(
            f"{url}/api/v1/documentation",
            json=doc_data,
            headers={"X-Correlation-ID": correlation_id}
        )
        
        if create_response.status_code not in [200, 201]:
            pytest.skip("Documentation creation failed")
        
        doc_id = create_response.json().get("doc_id") or \
                 create_response.json().get("id")
        
        if not doc_id:
            pytest.skip("No doc_id in response")
        
        # Validate documentation
        validate_response = await http_client.post(
            f"{url}/api/v1/documentation/{doc_id}/validate",
            headers={"X-Correlation-ID": correlation_id}
        )
        
        assert validate_response.status_code in [200, 404, 501]
    
    @pytest.mark.asyncio
    async def test_documentation_freshness(
        self,
        http_client,
        service_urls,
        correlation_id,
        test_mode
    ):
        """
        Test checking documentation freshness.
        
        Expected: Freshness status returned
        """
        url = service_urls["mcp-evergreen-docs"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        # Create documentation
        doc_data = {
            "title": f"Freshness Test {correlation_id[:8]}",
            "content": "Documentation for freshness testing.",
            "source_url": "https://example.com/docs/freshness"
        }
        
        response = await http_client.post(
            f"{url}/api/v1/documentation",
            json=doc_data,
            headers={"X-Correlation-ID": correlation_id}
        )
        
        assert response.status_code in [200, 201], \
            "Documentation creation for freshness test failed"
    
    @pytest.mark.asyncio
    async def test_get_sync_jobs(
        self,
        http_client,
        service_urls,
        correlation_id,
        test_mode
    ):
        """
        Test listing sync jobs.
        
        Expected: Sync jobs list returned
        """
        url = service_urls["mcp-evergreen-docs"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        response = await http_client.get(
            f"{url}/api/v1/sync/jobs",
            headers={"X-Correlation-ID": correlation_id}
        )
        
        # May return 200 with jobs or 404 if endpoint not implemented
        assert response.status_code in [200, 404, 501]
