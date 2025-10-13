"""
Integration tests for Multi-Pass Query API.

Tests API endpoints, request/response handling, and tier integration.
"""

import pytest
import httpx
from datetime import datetime


@pytest.fixture
def api_client():
    """HTTP client for API testing."""
    return httpx.AsyncClient(base_url="http://localhost:8000", timeout=900.0)


@pytest.fixture
async def cleanup_client(api_client):
    """Cleanup client after tests."""
    yield api_client
    await api_client.aclose()


class TestMultiPassEndpoint:
    """Test /api/v1/query/multi-pass endpoint."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multi_pass_basic_query(self, cleanup_client):
        """Test basic multi-pass query."""
        request = {
            "query": "What is Python?",
            "num_passes": 2,
            "num_secondary_questions": 2,
            "n_results": 5,
            "temperature": 0.7,
            "stream": False
        }
        
        response = await cleanup_client.post(
            "/api/v1/query/multi-pass",
            json=request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "original_query" in data
        assert "num_passes" in data
        assert "sections" in data
        assert "final_synthesis" in data
        assert "total_questions_asked" in data
        assert "total_sources_used" in data
        
        # Verify values
        assert data["original_query"] == request["query"]
        assert data["num_passes"] == request["num_passes"]
        assert len(data["sections"]) == request["num_passes"]
        assert data["total_questions_asked"] == request["num_passes"] * request["num_secondary_questions"]
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multi_pass_with_different_configurations(self, cleanup_client):
        """Test multi-pass with various configurations."""
        configurations = [
            {"num_passes": 1, "num_secondary_questions": 1},
            {"num_passes": 3, "num_secondary_questions": 3},
            {"num_passes": 2, "num_secondary_questions": 4},
        ]
        
        for config in configurations:
            request = {
                "query": "Test query",
                **config,
                "n_results": 5
            }
            
            response = await cleanup_client.post(
                "/api/v1/query/multi-pass",
                json=request
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["sections"]) == config["num_passes"]
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multi_pass_sections_structure(self, cleanup_client):
        """Test that sections have correct structure."""
        request = {
            "query": "How does caching work?",
            "num_passes": 2,
            "num_secondary_questions": 2
        }
        
        response = await cleanup_client.post(
            "/api/v1/query/multi-pass",
            json=request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for section in data["sections"]:
            assert "section_index" in section
            assert "section_name" in section
            assert "section_description" in section
            assert "questions" in section
            assert "synthesis" in section
            assert "duration_seconds" in section
            assert "timestamp" in section
            
            # Verify questions structure
            for question in section["questions"]:
                assert "question" in question
                assert "answer" in question
                assert "sources" in question
                assert "confidence" in question
                assert "duration_seconds" in question
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multi_pass_parameter_validation(self, cleanup_client):
        """Test parameter validation."""
        # Missing required field
        response = await cleanup_client.post(
            "/api/v1/query/multi-pass",
            json={}
        )
        assert response.status_code == 422  # Validation error
        
        # Invalid num_passes (too high)
        response = await cleanup_client.post(
            "/api/v1/query/multi-pass",
            json={
                "query": "Test",
                "num_passes": 100  # Max is 10
            }
        )
        assert response.status_code == 422
        
        # Invalid temperature
        response = await cleanup_client.post(
            "/api/v1/query/multi-pass",
            json={
                "query": "Test",
                "temperature": 2.0  # Max is 1.0
            }
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multi_pass_with_sources(self, cleanup_client):
        """Test that sources are included in results."""
        request = {
            "query": "How does the RAG system work?",
            "num_passes": 2,
            "num_secondary_questions": 2,
            "n_results": 10
        }
        
        response = await cleanup_client.post(
            "/api/v1/query/multi-pass",
            json=request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have sources
        assert data["total_sources_used"] > 0
        
        # Check that questions have sources
        for section in data["sections"]:
            for question in section["questions"]:
                if question["sources"]:
                    # Verify source structure
                    for source in question["sources"]:
                        assert "file_path" in source or "id" in source


class TestEnhancedQueryWithTiers:
    """Test enhanced query endpoint with tier selection."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_query_with_auto_tier(self, cleanup_client):
        """Test query with automatic tier selection."""
        request = {
            "question": "What is caching?",
            "mode": "rag",
            "tier": "auto",
            "n_results": 5
        }
        
        response = await cleanup_client.post(
            "/api/v1/query/enhanced",
            json=request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "tier_used" in data
        assert "tier_requested" in data
        assert data["tier_requested"] == "auto"
        assert data["tier_used"] in ["cursor", "desktop", "docker"]
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_query_with_docker_tier(self, cleanup_client):
        """Test query with docker tier (always available)."""
        request = {
            "question": "Test query",
            "mode": "basic",
            "tier": "docker",
            "max_retries": 0
        }
        
        response = await cleanup_client.post(
            "/api/v1/query/enhanced",
            json=request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["tier_used"] == "docker"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_tier_fallback_behavior(self, cleanup_client):
        """Test that tier fallback works correctly."""
        # Request cursor tier (likely unavailable)
        request = {
            "question": "Test",
            "mode": "basic",
            "tier": "cursor",
            "max_retries": 2
        }
        
        response = await cleanup_client.post(
            "/api/v1/query/enhanced",
            json=request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have fallen back to available tier
        assert "tier_used" in data
        assert data["tier_used"] in ["desktop", "docker"]
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_all_three_modes(self, cleanup_client):
        """Test all three query modes."""
        modes = ["rag", "contextual", "basic"]
        
        for mode in modes:
            request = {
                "question": "What is Python?",
                "mode": mode,
                "tier": "docker",
                "n_results": 5
            }
            
            response = await cleanup_client.post(
                "/api/v1/query/enhanced",
                json=request
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["mode"] == mode


class TestTierStatus:
    """Test tier status endpoint."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_tier_status_endpoint(self, cleanup_client):
        """Test tier status endpoint returns correct structure."""
        response = await cleanup_client.get("/api/v1/query/tier-status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "tiers" in data
        assert "recommendation" in data
        
        tiers = data["tiers"]
        assert "cursor" in tiers
        assert "desktop" in tiers
        assert "docker" in tiers
        
        # Verify tier structure
        for tier_name, tier_info in tiers.items():
            assert "tier" in tier_info
            assert "name" in tier_info
            assert "available" in tier_info
            assert "model" in tier_info
            assert "use_case" in tier_info
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_docker_tier_always_available(self, cleanup_client):
        """Test that docker tier is always reported as available."""
        response = await cleanup_client.get("/api/v1/query/tier-status")
        
        assert response.status_code == 200
        data = response.json()
        
        docker_tier = data["tiers"]["docker"]
        assert docker_tier["available"] is True


class TestQueryInfo:
    """Test query info endpoints."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multi_pass_info_endpoint(self, cleanup_client):
        """Test multi-pass info endpoint."""
        response = await cleanup_client.get("/api/v1/query/multi-pass/info")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "description" in data
        assert "workflow" in data
        assert "parameters" in data
        assert "example_usage" in data
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_query_modes_endpoint(self, cleanup_client):
        """Test query modes info endpoint."""
        response = await cleanup_client.get("/api/v1/query/modes")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "modes" in data
        assert "tiers" in data
        
        modes = data["modes"]
        assert "rag" in modes
        assert "contextual" in modes
        assert "basic" in modes


class TestPerformance:
    """Test performance characteristics."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_large_query_completes_within_timeout(self, cleanup_client):
        """Test that large queries complete within timeout."""
        request = {
            "query": "Explain the complete system architecture",
            "num_passes": 5,
            "num_secondary_questions": 4,
            "n_results": 10
        }
        
        # Should complete within 900s timeout
        response = await cleanup_client.post(
            "/api/v1/query/multi-pass",
            json=request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify it completed
        assert data["total_duration_seconds"] > 0
        assert data["total_duration_seconds"] < 900  # Within timeout
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_concurrent_queries(self, cleanup_client):
        """Test handling of concurrent queries."""
        import asyncio
        
        requests = [
            {
                "question": f"Test query {i}",
                "mode": "basic",
                "tier": "docker"
            }
            for i in range(3)
        ]
        
        # Send concurrent requests
        responses = await asyncio.gather(*[
            cleanup_client.post("/api/v1/query/enhanced", json=req)
            for req in requests
        ])
        
        # All should succeed
        assert all(r.status_code == 200 for r in responses)


class TestErrorHandling:
    """Test error handling."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_invalid_json(self, cleanup_client):
        """Test handling of invalid JSON."""
        response = await cleanup_client.post(
            "/api/v1/query/multi-pass",
            content="invalid json"
        )
        
        assert response.status_code == 422  # Unprocessable entity
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_empty_query(self, cleanup_client):
        """Test handling of empty query."""
        request = {
            "query": "",
            "num_passes": 2
        }
        
        response = await cleanup_client.post(
            "/api/v1/query/multi-pass",
            json=request
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_query_too_long(self, cleanup_client):
        """Test handling of too-long query."""
        request = {
            "query": "x" * 3000,  # Max is 2000
            "num_passes": 2
        }
        
        response = await cleanup_client.post(
            "/api/v1/query/multi-pass",
            json=request
        )
        
        assert response.status_code == 422

