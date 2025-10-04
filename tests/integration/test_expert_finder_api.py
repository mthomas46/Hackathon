"""
Integration tests for Expert Finder Service API.

These tests verify the expert-finder-service API endpoints with both
mocked and live service dependencies.
"""

import pytest
import httpx
import asyncio
from typing import Dict, Any, List
import time


# Service URLs
EXPERT_FINDER_URL = "http://localhost:5160"
USER_STORE_URL = "http://localhost:5150"


class TestHealthEndpoint:
    """Test /health endpoint."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_health_check_returns_200(self):
        """Test that health check returns 200 OK."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{EXPERT_FINDER_URL}/health", timeout=5.0)
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "healthy"
                assert data["service"] == "expert-finder-service"
                assert "version" in data
                assert "timestamp" in data
            except httpx.ConnectError:
                pytest.skip("expert-finder-service not running")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_health_check_includes_dependencies(self):
        """Test that health check includes dependency URLs."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{EXPERT_FINDER_URL}/health", timeout=5.0)
                
                assert response.status_code == 200
                data = response.json()
                
                assert "dependencies" in data
                assert "user_store" in data["dependencies"]
                assert "doc_store" in data["dependencies"]
                assert "external_service_store" in data["dependencies"]
            except httpx.ConnectError:
                pytest.skip("expert-finder-service not running")


class TestNaturalLanguageExpertSearch:
    """Test /experts/find endpoint (natural language queries)."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_find_experts_basic_query(self):
        """Test basic natural language expert search."""
        async with httpx.AsyncClient() as client:
            try:
                query = {
                    "query": "Who knows Python backend development?",
                    "max_results": 5
                }
                
                response = await client.post(
                    f"{EXPERT_FINDER_URL}/experts/find",
                    json=query,
                    timeout=10.0
                )
                
                # Should return 200 even if no results
                assert response.status_code == 200
                
                data = response.json()
                assert "query" in data
                assert "experts" in data
                assert isinstance(data["experts"], list)
                assert "execution_time_ms" in data
                
                # Execution time should be reasonable
                assert data["execution_time_ms"] < 1000  # Less than 1 second
                
            except httpx.ConnectError:
                pytest.skip("expert-finder-service not running")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_find_experts_with_max_results(self):
        """Test that max_results parameter is respected."""
        async with httpx.AsyncClient() as client:
            try:
                query = {
                    "query": "Find developers",
                    "max_results": 3
                }
                
                response = await client.post(
                    f"{EXPERT_FINDER_URL}/experts/find",
                    json=query,
                    timeout=10.0
                )
                
                assert response.status_code == 200
                data = response.json()
                
                # Should not return more than max_results
                assert len(data["experts"]) <= 3
                
            except httpx.ConnectError:
                pytest.skip("expert-finder-service not running")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_find_experts_with_min_score(self):
        """Test that min_score parameter filters results."""
        async with httpx.AsyncClient() as client:
            try:
                query = {
                    "query": "Python experts",
                    "min_score": 0.5,
                    "max_results": 10
                }
                
                response = await client.post(
                    f"{EXPERT_FINDER_URL}/experts/find",
                    json=query,
                    timeout=10.0
                )
                
                assert response.status_code == 200
                data = response.json()
                
                # All returned experts should have score >= 0.5
                for expert in data["experts"]:
                    assert expert["relevance_score"] >= 0.5
                
            except httpx.ConnectError:
                pytest.skip("expert-finder-service not running")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_find_experts_with_team_filter(self):
        """Test team_id filtering."""
        async with httpx.AsyncClient() as client:
            try:
                query = {
                    "query": "backend developers",
                    "team_id": "team_12345",
                    "exclude_team": False,
                    "max_results": 5
                }
                
                response = await client.post(
                    f"{EXPERT_FINDER_URL}/experts/find",
                    json=query,
                    timeout=10.0
                )
                
                assert response.status_code == 200
                data = response.json()
                
                # Should only return team members
                for expert in data["experts"]:
                    if "metadata" in expert and "team_id" in expert["metadata"]:
                        assert expert["metadata"]["team_id"] == "team_12345"
                
            except httpx.ConnectError:
                pytest.skip("expert-finder-service not running")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_find_experts_exclude_team(self):
        """Test excluding team members from search."""
        async with httpx.AsyncClient() as client:
            try:
                query = {
                    "query": "Python experts",
                    "team_id": "team_12345",
                    "exclude_team": True,
                    "max_results": 5
                }
                
                response = await client.post(
                    f"{EXPERT_FINDER_URL}/experts/find",
                    json=query,
                    timeout=10.0
                )
                
                assert response.status_code == 200
                data = response.json()
                
                # Should NOT return team members
                for expert in data["experts"]:
                    if "metadata" in expert and "team_id" in expert["metadata"]:
                        assert expert["metadata"]["team_id"] != "team_12345"
                
            except httpx.ConnectError:
                pytest.skip("expert-finder-service not running")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_find_experts_relevance_scoring(self):
        """Test that relevance scores are between 0 and 1."""
        async with httpx.AsyncClient() as client:
            try:
                query = {
                    "query": "senior backend engineers",
                    "max_results": 10
                }
                
                response = await client.post(
                    f"{EXPERT_FINDER_URL}/experts/find",
                    json=query,
                    timeout=10.0
                )
                
                assert response.status_code == 200
                data = response.json()
                
                for expert in data["experts"]:
                    assert 0.0 <= expert["relevance_score"] <= 1.0
                    assert "explanation" in expert
                    assert "evidence" in expert
                    assert isinstance(expert["evidence"], list)
                
            except httpx.ConnectError:
                pytest.skip("expert-finder-service not running")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_find_experts_results_sorted_by_score(self):
        """Test that results are sorted by relevance score (descending)."""
        async with httpx.AsyncClient() as client:
            try:
                query = {
                    "query": "Python developers",
                    "max_results": 10
                }
                
                response = await client.post(
                    f"{EXPERT_FINDER_URL}/experts/find",
                    json=query,
                    timeout=10.0
                )
                
                assert response.status_code == 200
                data = response.json()
                
                if len(data["experts"]) > 1:
                    scores = [e["relevance_score"] for e in data["experts"]]
                    # Check that scores are in descending order
                    assert scores == sorted(scores, reverse=True)
                
            except httpx.ConnectError:
                pytest.skip("expert-finder-service not running")


class TestTopicBasedSearch:
    """Test /experts/by-topic/{topic} endpoint."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_find_experts_by_topic(self):
        """Test finding experts by specific topic."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{EXPERT_FINDER_URL}/experts/by-topic/Python",
                    timeout=10.0
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert "topic" in data
                assert data["topic"] == "Python"
                assert "experts" in data
                assert isinstance(data["experts"], list)
                
            except httpx.ConnectError:
                pytest.skip("expert-finder-service not running")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_find_experts_by_topic_with_max_results(self):
        """Test max_results parameter for topic search."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{EXPERT_FINDER_URL}/experts/by-topic/Backend",
                    params={"max_results": 2},
                    timeout=10.0
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert len(data["experts"]) <= 2
                
            except httpx.ConnectError:
                pytest.skip("expert-finder-service not running")


class TestServiceBasedSearch:
    """Test /experts/by-service/{service} endpoint."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_find_experts_by_service(self):
        """Test finding experts by service they worked on."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{EXPERT_FINDER_URL}/experts/by-service/user-service",
                    timeout=10.0
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert "service" in data
                assert data["service"] == "user-service"
                assert "experts" in data
                assert isinstance(data["experts"], list)
                
            except httpx.ConnectError:
                pytest.skip("expert-finder-service not running")


class TestSMESearch:
    """Test /experts/sme/{area} endpoint."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_find_sme_in_area(self):
        """Test finding subject matter experts in specific area."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{EXPERT_FINDER_URL}/experts/sme/Python",
                    timeout=10.0
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert "area" in data
                assert data["area"] == "Python"
                assert "subject_matter_experts" in data
                assert isinstance(data["subject_matter_experts"], list)
                
            except httpx.ConnectError:
                pytest.skip("expert-finder-service not running")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_find_sme_with_min_documents(self):
        """Test SME search with minimum document threshold."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{EXPERT_FINDER_URL}/experts/sme/Backend",
                    params={"min_documents": 5},
                    timeout=10.0
                )
                
                assert response.status_code == 200
                data = response.json()
                
                # All SMEs should have at least min_documents
                for sme in data["subject_matter_experts"]:
                    if "metadata" in sme and "document_count" in sme["metadata"]:
                        assert sme["metadata"]["document_count"] >= 5
                
            except httpx.ConnectError:
                pytest.skip("expert-finder-service not running")


class TestTeammateDiscovery:
    """Test /experts/teammates/{user_id} endpoint."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_find_potential_teammates(self):
        """Test finding potential teammates for a user."""
        async with httpx.AsyncClient() as client:
            try:
                # Use a test user ID
                user_id = "test_user_001"
                
                response = await client.get(
                    f"{EXPERT_FINDER_URL}/experts/teammates/{user_id}",
                    timeout=10.0
                )
                
                # Should return 200 even if user doesn't exist
                assert response.status_code in [200, 404]
                
                if response.status_code == 200:
                    data = response.json()
                    assert "user_id" in data
                    assert "potential_teammates" in data
                    assert isinstance(data["potential_teammates"], list)
                
            except httpx.ConnectError:
                pytest.skip("expert-finder-service not running")


class TestTeamExpertise:
    """Test /teams/{team_id}/expertise endpoint."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_team_expertise_summary(self):
        """Test getting expertise summary for a team."""
        async with httpx.AsyncClient() as client:
            try:
                team_id = "team_12345"
                
                response = await client.get(
                    f"{EXPERT_FINDER_URL}/teams/{team_id}/expertise",
                    timeout=10.0
                )
                
                # Should return 200 even if team doesn't exist
                assert response.status_code in [200, 404]
                
                if response.status_code == 200:
                    data = response.json()
                    assert "team_id" in data
                    assert "member_count" in data
                    assert "topics" in data or "expertise_areas" in data
                
            except httpx.ConnectError:
                pytest.skip("expert-finder-service not running")


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_find_experts_empty_query(self):
        """Test handling of empty query string."""
        async with httpx.AsyncClient() as client:
            try:
                query = {
                    "query": "",
                    "max_results": 5
                }
                
                response = await client.post(
                    f"{EXPERT_FINDER_URL}/experts/find",
                    json=query,
                    timeout=10.0
                )
                
                # Should handle gracefully
                assert response.status_code in [200, 400, 422]
                
            except httpx.ConnectError:
                pytest.skip("expert-finder-service not running")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_find_experts_invalid_max_results(self):
        """Test handling of invalid max_results parameter."""
        async with httpx.AsyncClient() as client:
            try:
                query = {
                    "query": "Python developers",
                    "max_results": -1  # Invalid
                }
                
                response = await client.post(
                    f"{EXPERT_FINDER_URL}/experts/find",
                    json=query,
                    timeout=10.0
                )
                
                # Should return validation error
                assert response.status_code == 422
                
            except httpx.ConnectError:
                pytest.skip("expert-finder-service not running")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_find_experts_invalid_min_score(self):
        """Test handling of invalid min_score parameter."""
        async with httpx.AsyncClient() as client:
            try:
                query = {
                    "query": "developers",
                    "min_score": 1.5  # Invalid (> 1.0)
                }
                
                response = await client.post(
                    f"{EXPERT_FINDER_URL}/experts/find",
                    json=query,
                    timeout=10.0
                )
                
                # Should return validation error
                assert response.status_code == 422
                
            except httpx.ConnectError:
                pytest.skip("expert-finder-service not running")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_nonexistent_endpoint(self):
        """Test accessing non-existent endpoint."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{EXPERT_FINDER_URL}/nonexistent",
                    timeout=5.0
                )
                
                # Should return 404
                assert response.status_code == 404
                
            except httpx.ConnectError:
                pytest.skip("expert-finder-service not running")


class TestPerformance:
    """Test performance characteristics."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_find_experts_response_time(self):
        """Test that expert search completes within acceptable time."""
        async with httpx.AsyncClient() as client:
            try:
                query = {
                    "query": "Python backend developers",
                    "max_results": 10
                }
                
                start_time = time.time()
                response = await client.post(
                    f"{EXPERT_FINDER_URL}/experts/find",
                    json=query,
                    timeout=10.0
                )
                end_time = time.time()
                
                assert response.status_code == 200
                
                # Should complete within 1 second
                response_time = end_time - start_time
                assert response_time < 1.0
                
            except httpx.ConnectError:
                pytest.skip("expert-finder-service not running")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        async with httpx.AsyncClient() as client:
            try:
                # Create 5 concurrent requests
                queries = [
                    {"query": "Python developers", "max_results": 5},
                    {"query": "Backend engineers", "max_results": 5},
                    {"query": "Frontend experts", "max_results": 5},
                    {"query": "DevOps specialists", "max_results": 5},
                    {"query": "Database administrators", "max_results": 5}
                ]
                
                tasks = [
                    client.post(
                        f"{EXPERT_FINDER_URL}/experts/find",
                        json=query,
                        timeout=10.0
                    )
                    for query in queries
                ]
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                # All requests should succeed
                for response in responses:
                    if not isinstance(response, Exception):
                        assert response.status_code == 200
                
            except httpx.ConnectError:
                pytest.skip("expert-finder-service not running")


# ============================================================================
# INTEGRATION WITH USER-STORE
# ============================================================================

class TestUserStoreIntegration:
    """Test integration with user-store service."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_expert_finder_queries_user_store(self):
        """Test that expert-finder successfully queries user-store."""
        async with httpx.AsyncClient() as client:
            try:
                # First check if user-store is accessible
                user_store_response = await client.get(
                    f"{USER_STORE_URL}/health",
                    timeout=5.0
                )
                
                if user_store_response.status_code != 200:
                    pytest.skip("user-store not accessible")
                
                # Now query expert-finder
                query = {
                    "query": "Find Python developers",
                    "max_results": 5
                }
                
                response = await client.post(
                    f"{EXPERT_FINDER_URL}/experts/find",
                    json=query,
                    timeout=10.0
                )
                
                assert response.status_code == 200
                data = response.json()
                
                # If users exist in user-store, we should get results
                if data.get("total_candidates", 0) > 0:
                    assert len(data["experts"]) > 0
                
            except httpx.ConnectError:
                pytest.skip("Services not running")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_expert_metadata_from_user_store(self):
        """Test that expert metadata comes from user-store."""
        async with httpx.AsyncClient() as client:
            try:
                query = {
                    "query": "backend developers",
                    "max_results": 3
                }
                
                response = await client.post(
                    f"{EXPERT_FINDER_URL}/experts/find",
                    json=query,
                    timeout=10.0
                )
                
                assert response.status_code == 200
                data = response.json()
                
                # Check that expert data has expected fields from user-store
                for expert in data["experts"]:
                    assert "user_id" in expert or "username" in expert
                    assert "display_name" in expert
                    # May have metadata from user-store
                    if "metadata" in expert:
                        assert isinstance(expert["metadata"], dict)
                
            except httpx.ConnectError:
                pytest.skip("Services not running")

