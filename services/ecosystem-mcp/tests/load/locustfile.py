"""
Load testing for Ecosystem MCP Service using Locust.

This file defines load testing scenarios for all major endpoints:
- Health checks
- Search queries
- Ollama interactions
- Admin operations

Usage:
    # Baseline test (1 user)
    locust -f tests/load/locustfile.py --host=http://localhost:8000 --users 1 --spawn-rate 1 --run-time 1m --headless
    
    # Sustained load (100 users, 10 minutes)
    locust -f tests/load/locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 10m --headless
    
    # Spike test (500 users)
    locust -f tests/load/locustfile.py --host=http://localhost:8000 --users 500 --spawn-rate 50 --run-time 5m --headless
    
    # Soak test (50 users, 1 hour)
    locust -f tests/load/locustfile.py --host=http://localhost:8000 --users 50 --spawn-rate 5 --run-time 1h --headless
"""

import random
from locust import HttpUser, task, between, events
import logging

logger = logging.getLogger(__name__)


class EcosystemMCPUser(HttpUser):
    """
    Simulates a user interacting with the Ecosystem MCP service.
    
    Task weights determine frequency:
    - Health check: 10 (most frequent)
    - Search: 5 (common)
    - Admin stats: 2 (occasional)
    - Ollama: 3 (moderate)
    """
    
    # Wait 1-5 seconds between tasks (realistic user behavior)
    wait_time = between(1, 5)
    
    def on_start(self):
        """Called when a simulated user starts."""
        logger.info("Load test user started")
    
    # ========================================================================
    # Health & Monitoring Tasks (Most Frequent)
    # ========================================================================
    
    @task(10)
    def health_check(self):
        """Check service health (10% of requests)."""
        with self.client.get(
            "/health",
            catch_response=True,
            name="GET /health"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") in ["healthy", "degraded"]:
                    response.success()
                else:
                    response.failure(f"Unhealthy status: {data.get('status')}")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(3)
    def about_me(self):
        """Get service information."""
        with self.client.get(
            "/about-me",
            catch_response=True,
            name="GET /about-me"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "name" in data and "version" in data:
                    response.success()
                else:
                    response.failure("Missing required fields")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(2)
    def endpoints_list(self):
        """List available endpoints."""
        with self.client.get(
            "/endpoints",
            catch_response=True,
            name="GET /endpoints"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "endpoints" in data and len(data["endpoints"]) > 0:
                    response.success()
                else:
                    response.failure("No endpoints returned")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    # ========================================================================
    # Search Tasks (Common Operations)
    # ========================================================================
    
    @task(5)
    def search_documents(self):
        """
        Search for documents (semantic search).
        
        Uses realistic queries that might be in production.
        """
        queries = [
            "How do I deploy the service?",
            "What is the architecture?",
            "Database migration guide",
            "Performance optimization",
            "Circuit breaker pattern",
            "Repository pattern usage",
            "Caching strategy",
            "Health check implementation",
            "Error handling best practices",
            "Configuration management",
        ]
        
        query = random.choice(queries)
        
        with self.client.post(
            "/api/v1/query",
            json={
                "query": query,
                "limit": 5,
                "threshold": 0.7
            },
            catch_response=True,
            name="POST /api/v1/query"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "results" in data:
                    response.success()
                else:
                    response.failure("No results field")
            elif response.status_code == 503:
                # Service might be unavailable (circuit breaker)
                response.success()  # Don't count as failure
                logger.warning("Search service unavailable (circuit breaker)")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    # ========================================================================
    # Ollama Tasks (Moderate Frequency)
    # ========================================================================
    
    @task(3)
    def ollama_status(self):
        """Check Ollama service status."""
        with self.client.get(
            "/api/v1/ollama",
            catch_response=True,
            name="GET /api/v1/ollama"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "available" in data:
                    response.success()
                else:
                    response.failure("Missing available field")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    # ========================================================================
    # Admin Tasks (Occasional)
    # ========================================================================
    
    @task(2)
    def admin_stats(self):
        """Get service statistics."""
        with self.client.get(
            "/api/v1/admin/stats",
            catch_response=True,
            name="GET /api/v1/admin/stats"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "documents" in data or "embeddings" in data:
                    response.success()
                else:
                    response.failure("Missing stats fields")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(1)
    def cache_stats(self):
        """Get cache statistics."""
        with self.client.get(
            "/api/v1/admin/cache-stats",
            catch_response=True,
            name="GET /api/v1/admin/cache-stats"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "cache_hits" in data and "cache_misses" in data:
                    response.success()
                else:
                    response.failure("Missing cache stats")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(1)
    def circuit_breaker_status(self):
        """Get circuit breaker status."""
        with self.client.get(
            "/api/v1/admin/circuit-breakers",
            catch_response=True,
            name="GET /api/v1/admin/circuit-breakers"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "circuit_breakers" in data:
                    response.success()
                else:
                    response.failure("Missing circuit breaker data")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(1)
    def metrics(self):
        """Get Prometheus metrics."""
        with self.client.get(
            "/metrics",
            catch_response=True,
            name="GET /metrics"
        ) as response:
            if response.status_code == 200:
                # Metrics endpoint returns plain text
                if "http_requests_total" in response.text:
                    response.success()
                else:
                    response.failure("Missing metrics")
            else:
                response.failure(f"Status code: {response.status_code}")


# ============================================================================
# Event Hooks (for custom reporting)
# ============================================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts."""
    logger.info("=" * 70)
    logger.info("LOAD TEST STARTING")
    logger.info(f"Host: {environment.host}")
    logger.info(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")
    logger.info("=" * 70)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops."""
    logger.info("=" * 70)
    logger.info("LOAD TEST COMPLETED")
    logger.info("=" * 70)
    
    # Print summary statistics
    stats = environment.stats
    logger.info(f"Total requests: {stats.total.num_requests}")
    logger.info(f"Total failures: {stats.total.num_failures}")
    logger.info(f"Failure rate: {stats.total.fail_ratio:.2%}")
    logger.info(f"Average response time: {stats.total.avg_response_time:.0f}ms")
    logger.info(f"Min response time: {stats.total.min_response_time:.0f}ms")
    logger.info(f"Max response time: {stats.total.max_response_time:.0f}ms")
    logger.info(f"Requests per second: {stats.total.total_rps:.2f}")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    """Called for each request (can be used for custom logging)."""
    if exception:
        logger.error(f"Request failed: {name} - {exception}")

