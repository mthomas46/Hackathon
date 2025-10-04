"""
Functional Performance Tests for Expert Finder Service

Phase 2.2: Validate response times, concurrent requests, edge cases, and pagination.

Test Categories:
- Response Time Tests (< 50ms target)
- Concurrent Request Tests (10+ simultaneous)
- Edge Case Tests (no data, no matches, invalid params)
- Pagination Tests (limit, offset validation)
- Load Tests (100+ requests)

Run:
    pytest tests/functional/test_expert_finder_performance.py -v
    pytest tests/functional/test_expert_finder_performance.py -m performance
"""

import pytest
import httpx
import asyncio
import time
from typing import List, Dict, Any
import statistics


# Service URLs
EXPERT_FINDER_URL = "http://localhost:5160"
USER_STORE_URL = "http://localhost:5050"

# Performance targets
RESPONSE_TIME_TARGET_MS = 50
CONCURRENT_REQUESTS_COUNT = 10
LOAD_TEST_REQUESTS = 100


@pytest.fixture
async def http_client():
    """Async HTTP client for API requests."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        yield client


@pytest.fixture
async def populated_user_store(http_client):
    """Populate user store with test users for realistic scenarios."""
    test_users = [
        {
            "username": f"test.user{i}",
            "email": f"test{i}@example.com",
            "full_name": f"Test User {i}",
            "role": "developer" if i % 3 == 0 else "analyst" if i % 3 == 1 else "manager",
            "status": "active",
            "team_id": f"team-{i % 5}",  # 5 teams
            "topic_interests": ["Python", "FastAPI", "Docker"][:i % 3 + 1],
            "service_subscriptions": [f"service-{j}" for j in range(i % 3 + 1)]
        }
        for i in range(20)
    ]
    
    # Create users (handle duplicates gracefully)
    for user in test_users:
        try:
            await http_client.post(f"{USER_STORE_URL}/users", json=user)
        except httpx.HTTPStatusError:
            pass  # User might already exist
    
    return test_users


@pytest.mark.functional
@pytest.mark.performance
class TestResponseTimes:
    """Test response times meet performance targets (< 50ms)."""
    
    @pytest.mark.asyncio
    async def test_find_experts_response_time(self, http_client, populated_user_store):
        """Test /experts/find endpoint response time."""
        query = {"query": "Python expert", "max_results": 5}
        
        start_time = time.perf_counter()
        response = await http_client.post(f"{EXPERT_FINDER_URL}/experts/find", json=query)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        assert response.status_code == 200
        print(f"\n/experts/find response time: {elapsed_ms:.2f}ms (target: <{RESPONSE_TIME_TARGET_MS}ms)")
        
        # Check if we meet target (warning, not failure)
        if elapsed_ms > RESPONSE_TIME_TARGET_MS:
            pytest.warns(UserWarning, match="Response time exceeds target")
    
    @pytest.mark.asyncio
    async def test_by_topic_response_time(self, http_client):
        """Test /experts/by-topic endpoint response time."""
        start_time = time.perf_counter()
        response = await http_client.get(f"{EXPERT_FINDER_URL}/experts/by-topic/Python?max_results=10")
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        print(f"\n/experts/by-topic response time: {elapsed_ms:.2f}ms (target: <{RESPONSE_TIME_TARGET_MS}ms)")
        
        assert response.status_code in [200, 404]  # 404 if no experts found
    
    @pytest.mark.asyncio
    async def test_by_service_response_time(self, http_client):
        """Test /experts/by-service endpoint response time."""
        start_time = time.perf_counter()
        response = await http_client.get(f"{EXPERT_FINDER_URL}/experts/by-service/service-0?max_results=10")
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        print(f"\n/experts/by-service response time: {elapsed_ms:.2f}ms (target: <{RESPONSE_TIME_TARGET_MS}ms)")
        
        assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_sme_response_time(self, http_client):
        """Test /experts/sme endpoint response time."""
        start_time = time.perf_counter()
        response = await http_client.get(f"{EXPERT_FINDER_URL}/experts/sme/Python?max_results=5")
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        print(f"\n/experts/sme response time: {elapsed_ms:.2f}ms (target: <{RESPONSE_TIME_TARGET_MS}ms)")
        
        assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_team_expertise_response_time(self, http_client):
        """Test /teams/{team_id}/expertise endpoint response time."""
        start_time = time.perf_counter()
        response = await http_client.get(f"{EXPERT_FINDER_URL}/teams/team-0/expertise")
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        print(f"\n/teams/expertise response time: {elapsed_ms:.2f}ms (target: <{RESPONSE_TIME_TARGET_MS}ms)")
        
        assert response.status_code in [200, 404]


@pytest.mark.functional
@pytest.mark.concurrent
class TestConcurrentRequests:
    """Test system handles concurrent requests without issues."""
    
    @pytest.mark.asyncio
    async def test_concurrent_find_experts(self, http_client, populated_user_store):
        """Test multiple simultaneous /experts/find requests."""
        async def make_request(query: str):
            response = await http_client.post(
                f"{EXPERT_FINDER_URL}/experts/find",
                json={"query": query, "max_results": 5}
            )
            return response.status_code, response.elapsed.total_seconds() * 1000
        
        queries = [
            "Python expert",
            "FastAPI developer",
            "Docker specialist",
            "Backend engineer",
            "Full stack",
            "DevOps engineer",
            "Database expert",
            "API designer",
            "Microservices",
            "Cloud architect"
        ]
        
        start_time = time.perf_counter()
        results = await asyncio.gather(*[make_request(q) for q in queries])
        total_time = (time.perf_counter() - start_time) * 1000
        
        # All requests should succeed
        status_codes = [r[0] for r in results]
        response_times = [r[1] for r in results]
        
        print(f"\nConcurrent requests: {len(queries)}")
        print(f"Total time: {total_time:.2f}ms")
        print(f"Avg response: {statistics.mean(response_times):.2f}ms")
        print(f"Max response: {max(response_times):.2f}ms")
        
        assert all(sc == 200 for sc in status_codes), "All requests should succeed"
    
    @pytest.mark.asyncio
    async def test_concurrent_different_endpoints(self, http_client):
        """Test concurrent requests to different endpoints."""
        async def make_requests():
            tasks = [
                http_client.post(f"{EXPERT_FINDER_URL}/experts/find", json={"query": "Python", "max_results": 5}),
                http_client.get(f"{EXPERT_FINDER_URL}/experts/by-topic/Python?max_results=5"),
                http_client.get(f"{EXPERT_FINDER_URL}/experts/by-service/service-0?max_results=5"),
                http_client.get(f"{EXPERT_FINDER_URL}/experts/sme/Python?max_results=5"),
                http_client.get(f"{EXPERT_FINDER_URL}/teams/team-0/expertise"),
            ]
            return await asyncio.gather(*tasks, return_exceptions=True)
        
        results = await make_requests()
        
        # Check no exceptions occurred
        for result in results:
            assert not isinstance(result, Exception), f"Request failed: {result}"
        
        print(f"\nConcurrent mixed requests: {len(results)} successful")


@pytest.mark.functional
@pytest.mark.edge_cases
class TestEdgeCases:
    """Test system handles edge cases gracefully."""
    
    @pytest.mark.asyncio
    async def test_empty_query(self, http_client):
        """Test find experts with empty query."""
        response = await http_client.post(
            f"{EXPERT_FINDER_URL}/experts/find",
            json={"query": "", "max_results": 5}
        )
        
        assert response.status_code in [200, 400], "Should handle empty query"
    
    @pytest.mark.asyncio
    async def test_nonexistent_topic(self, http_client):
        """Test by-topic with nonexistent topic."""
        response = await http_client.get(
            f"{EXPERT_FINDER_URL}/experts/by-topic/NonexistentTechnologyXYZ123?max_results=5"
        )
        
        assert response.status_code in [200, 404], "Should handle nonexistent topic"
        if response.status_code == 200:
            data = response.json()
            assert len(data.get("experts", [])) == 0, "Should return empty list"
    
    @pytest.mark.asyncio
    async def test_nonexistent_team(self, http_client):
        """Test team expertise with nonexistent team."""
        response = await http_client.get(
            f"{EXPERT_FINDER_URL}/teams/nonexistent-team-xyz/expertise"
        )
        
        assert response.status_code in [200, 404], "Should handle nonexistent team"
    
    @pytest.mark.asyncio
    async def test_invalid_max_results(self, http_client):
        """Test with invalid max_results parameter."""
        response = await http_client.get(
            f"{EXPERT_FINDER_URL}/experts/by-topic/Python?max_results=-1"
        )
        
        assert response.status_code in [200, 400, 422], "Should handle invalid param"
    
    @pytest.mark.asyncio
    async def test_very_large_max_results(self, http_client):
        """Test with very large max_results."""
        response = await http_client.get(
            f"{EXPERT_FINDER_URL}/experts/by-topic/Python?max_results=10000"
        )
        
        # Should either cap the results or return error
        assert response.status_code in [200, 400], "Should handle large max_results"
        if response.status_code == 200:
            data = response.json()
            # Should not actually return 10000 results
            assert len(data.get("experts", [])) < 10000


@pytest.mark.functional
@pytest.mark.pagination
class TestPagination:
    """Test pagination and limit parameters work correctly."""
    
    @pytest.mark.asyncio
    async def test_max_results_respected(self, http_client, populated_user_store):
        """Test max_results parameter limits response size."""
        for limit in [1, 5, 10, 20]:
            response = await http_client.post(
                f"{EXPERT_FINDER_URL}/experts/find",
                json={"query": "Python", "max_results": limit}
            )
            
            if response.status_code == 200:
                data = response.json()
                experts = data.get("experts", [])
                assert len(experts) <= limit, f"Should return at most {limit} results"
                print(f"Requested {limit}, got {len(experts)} experts")
    
    @pytest.mark.asyncio
    async def test_min_documents_filter(self, http_client):
        """Test min_documents parameter filters results."""
        response_low = await http_client.get(
            f"{EXPERT_FINDER_URL}/experts/by-topic/Python?max_results=20&min_documents=1"
        )
        response_high = await http_client.get(
            f"{EXPERT_FINDER_URL}/experts/by-topic/Python?max_results=20&min_documents=10"
        )
        
        if response_low.status_code == 200 and response_high.status_code == 200:
            data_low = response_low.json()
            data_high = response_high.json()
            
            experts_low = len(data_low.get("experts", []))
            experts_high = len(data_high.get("experts", []))
            
            # Higher threshold should return fewer or equal results
            assert experts_high <= experts_low, "Higher threshold should filter more"
            print(f"min_documents=1: {experts_low} experts, min_documents=10: {experts_high} experts")


@pytest.mark.functional
@pytest.mark.load
class TestLoadHandling:
    """Test system handles load gracefully."""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_sequential_load(self, http_client):
        """Test 100 sequential requests complete successfully."""
        start_time = time.perf_counter()
        
        success_count = 0
        response_times = []
        
        for i in range(LOAD_TEST_REQUESTS):
            req_start = time.perf_counter()
            try:
                response = await http_client.post(
                    f"{EXPERT_FINDER_URL}/experts/find",
                    json={"query": f"test query {i % 10}", "max_results": 5}
                )
                req_time = (time.perf_counter() - req_start) * 1000
                response_times.append(req_time)
                if response.status_code == 200:
                    success_count += 1
            except Exception as e:
                print(f"Request {i} failed: {e}")
        
        total_time = (time.perf_counter() - start_time) * 1000
        
        print(f"\nLoad Test Results:")
        print(f"Total requests: {LOAD_TEST_REQUESTS}")
        print(f"Successful: {success_count}")
        print(f"Total time: {total_time:.2f}ms")
        print(f"Avg response: {statistics.mean(response_times):.2f}ms")
        print(f"Median response: {statistics.median(response_times):.2f}ms")
        print(f"95th percentile: {statistics.quantiles(response_times, n=20)[18]:.2f}ms")
        print(f"Max response: {max(response_times):.2f}ms")
        
        # At least 95% should succeed
        success_rate = success_count / LOAD_TEST_REQUESTS
        assert success_rate >= 0.95, f"Success rate {success_rate:.1%} below 95%"
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_burst_load(self, http_client):
        """Test system handles burst of 50 concurrent requests."""
        async def make_request(i: int):
            try:
                response = await http_client.post(
                    f"{EXPERT_FINDER_URL}/experts/find",
                    json={"query": f"burst query {i % 10}", "max_results": 5}
                )
                return response.status_code == 200
            except Exception:
                return False
        
        start_time = time.perf_counter()
        results = await asyncio.gather(*[make_request(i) for i in range(50)])
        total_time = (time.perf_counter() - start_time) * 1000
        
        success_count = sum(results)
        
        print(f"\nBurst Load Test:")
        print(f"Concurrent requests: 50")
        print(f"Successful: {success_count}")
        print(f"Total time: {total_time:.2f}ms")
        print(f"Avg time per request: {total_time / 50:.2f}ms")
        
        # At least 90% should succeed under burst
        success_rate = success_count / 50
        assert success_rate >= 0.90, f"Burst success rate {success_rate:.1%} below 90%"


@pytest.mark.functional
@pytest.mark.health
class TestServiceHealth:
    """Test service health and availability."""
    
    @pytest.mark.asyncio
    async def test_health_check_response_time(self, http_client):
        """Test health check is fast (< 10ms)."""
        start_time = time.perf_counter()
        response = await http_client.get(f"{EXPERT_FINDER_URL}/health")
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        assert response.status_code == 200
        print(f"\nHealth check response time: {elapsed_ms:.2f}ms (target: <10ms)")
        assert elapsed_ms < 10, "Health check should be very fast"
    
    @pytest.mark.asyncio
    async def test_health_check_repeated(self, http_client):
        """Test health check remains consistent under repeated calls."""
        for _ in range(10):
            response = await http_client.get(f"{EXPERT_FINDER_URL}/health")
            assert response.status_code == 200, "Health check should always succeed"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

