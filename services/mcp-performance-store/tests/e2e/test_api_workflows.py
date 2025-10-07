"""End-to-end API workflow tests for MCP Performance Store.

These tests verify complete workflows through the API, ensuring that
all components work together correctly.
"""

import pytest
import httpx
import asyncio
from datetime import datetime
import uuid

# Service URL (assumes service is running)
BASE_URL = "http://localhost:5649"


@pytest.fixture
def sample_execution_data():
    """Generate sample execution data for testing."""
    return {
        "orchestration_id": str(uuid.uuid4()),
        "mcp_id": "test-mcp-001",
        "query": "Test query for E2E workflow",
        "status": "success",
        "started_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat(),
        "duration_ms": 1500,
        "patterns_used": ["RAG", "ChainOfThought"],
        "context": {"test": True},
        "metadata": {"environment": "test"}
    }


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_health_check():
    """Test that the service health check endpoint works."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "service" in data
            assert "version" in data
        except httpx.ConnectError:
            pytest.skip("Service not running - start with: docker-compose up -d")


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_record_and_retrieve_execution(sample_execution_data):
    """Test the complete workflow of recording and retrieving an execution."""
    async with httpx.AsyncClient() as client:
        try:
            # Step 1: Record an execution
            response = await client.post(
                f"{BASE_URL}/api/v1/executions",
                json=sample_execution_data
            )
            assert response.status_code in [200, 201]
            recorded = response.json()
            assert "execution_id" in recorded
            execution_id = recorded["execution_id"]
            
            # Step 2: Retrieve the execution
            response = await client.get(f"{BASE_URL}/api/v1/executions/{execution_id}")
            assert response.status_code == 200
            retrieved = response.json()
            assert retrieved["execution_id"] == execution_id
            assert retrieved["mcp_id"] == sample_execution_data["mcp_id"]
            assert retrieved["status"] == sample_execution_data["status"]
            
            # Step 3: Get recent executions (should include our execution)
            response = await client.get(f"{BASE_URL}/api/v1/executions/recent?limit=10")
            assert response.status_code == 200
            recent = response.json()
            assert isinstance(recent, list)
            execution_ids = [e["execution_id"] for e in recent]
            assert execution_id in execution_ids
            
        except httpx.ConnectError:
            pytest.skip("Service not running")


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_performance_metrics_workflow():
    """Test the workflow for performance metrics and analytics."""
    async with httpx.AsyncClient() as client:
        try:
            # Step 1: Get performance summary
            response = await client.get(
                f"{BASE_URL}/api/v1/performance/summary?time_window_hours=24"
            )
            assert response.status_code == 200
            summary = response.json()
            assert "average_duration_ms" in summary or "total_executions" in summary
            
            # Step 2: Get orchestration trends
            response = await client.get(
                f"{BASE_URL}/api/v1/analytics/trends/orchestration?time_window_days=7"
            )
            assert response.status_code == 200
            trends = response.json()
            assert isinstance(trends, dict)
            
            # Step 3: Compare patterns
            response = await client.get(f"{BASE_URL}/api/v1/analytics/compare/patterns")
            assert response.status_code == 200
            comparison = response.json()
            assert isinstance(comparison, (list, dict))
            
        except httpx.ConnectError:
            pytest.skip("Service not running")


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_anomaly_detection_workflow():
    """Test the anomaly detection workflow."""
    async with httpx.AsyncClient() as client:
        try:
            # Step 1: Detect orchestration anomalies
            response = await client.get(
                f"{BASE_URL}/api/v1/anomalies/detect/orchestration?days=7"
            )
            assert response.status_code == 200
            anomalies = response.json()
            assert "anomalies" in anomalies or "anomaly_count" in anomalies
            
            # Step 2: Check pattern-specific anomalies (if patterns exist)
            response = await client.get(
                f"{BASE_URL}/api/v1/anomalies/detect/pattern/RAG?days=7"
            )
            # This might return 404 if no data exists yet, which is okay for E2E
            assert response.status_code in [200, 404]
            
        except httpx.ConnectError:
            pytest.skip("Service not running")


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_multiple_executions_workflow(sample_execution_data):
    """Test recording multiple executions and analyzing them."""
    async with httpx.AsyncClient() as client:
        try:
            execution_ids = []
            
            # Step 1: Record multiple executions
            for i in range(5):
                data = sample_execution_data.copy()
                data["orchestration_id"] = str(uuid.uuid4())
                data["duration_ms"] = 1000 + (i * 100)  # Varying durations
                
                response = await client.post(
                    f"{BASE_URL}/api/v1/executions",
                    json=data
                )
                assert response.status_code in [200, 201]
                result = response.json()
                execution_ids.append(result["execution_id"])
            
            # Step 2: Verify all executions were recorded
            response = await client.get(f"{BASE_URL}/api/v1/executions/recent?limit=10")
            assert response.status_code == 200
            recent = response.json()
            recent_ids = [e["execution_id"] for e in recent]
            
            # At least some of our executions should be in recent
            found = sum(1 for eid in execution_ids if eid in recent_ids)
            assert found > 0
            
            # Step 3: Get performance summary (should reflect new data)
            response = await client.get(
                f"{BASE_URL}/api/v1/performance/summary?time_window_hours=1"
            )
            assert response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Service not running")


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_error_handling():
    """Test API error handling."""
    async with httpx.AsyncClient() as client:
        try:
            # Test 1: Get non-existent execution
            response = await client.get(
                f"{BASE_URL}/api/v1/executions/nonexistent-id-12345"
            )
            assert response.status_code == 404
            
            # Test 2: Invalid execution data
            response = await client.post(
                f"{BASE_URL}/api/v1/executions",
                json={"invalid": "data"}
            )
            assert response.status_code in [400, 422]  # Bad request or validation error
            
        except httpx.ConnectError:
            pytest.skip("Service not running")


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_pagination_and_filtering():
    """Test pagination and filtering capabilities."""
    async with httpx.AsyncClient() as client:
        try:
            # Test pagination
            response = await client.get(
                f"{BASE_URL}/api/v1/executions/recent?limit=5&offset=0"
            )
            assert response.status_code == 200
            page1 = response.json()
            
            response = await client.get(
                f"{BASE_URL}/api/v1/executions/recent?limit=5&offset=5"
            )
            assert response.status_code == 200
            page2 = response.json()
            
            # Pages should be different (if enough data exists)
            if len(page1) > 0 and len(page2) > 0:
                assert page1[0]["execution_id"] != page2[0]["execution_id"]
            
        except httpx.ConnectError:
            pytest.skip("Service not running")


if __name__ == "__main__":
    # Run tests with: pytest tests/e2e/test_api_workflows.py -v -m e2e
    print("Run E2E tests with: pytest tests/e2e/test_api_workflows.py -v -m e2e")
    print("Make sure the service is running: docker-compose up -d")
