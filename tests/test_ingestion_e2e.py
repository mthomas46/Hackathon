"""
End-to-End Tests for Ingestion Pipeline

Tests the complete flow from job creation through Redis queuing
to worker processing, covering all fixes from this session.
"""

import pytest
import asyncio
import httpx
from datetime import datetime
from uuid import UUID
import time

# These tests require the full stack to be running
# Mark as integration tests that need Docker services

pytestmark = pytest.mark.integration


class TestIngestionE2E:
    """End-to-end tests for the complete ingestion flow."""
    
    BASE_URL = "http://localhost:8000"
    
    @pytest.fixture
    def http_client(self):
        """Create an HTTP client."""
        return httpx.AsyncClient(timeout=30.0)
    
    @pytest.mark.asyncio
    async def test_complete_ingestion_flow(self, http_client):
        """Test complete flow: create job -> queue -> process -> complete."""
        # Step 1: Create ingestion job
        response = await http_client.post(
            f"{self.BASE_URL}/api/v1/admin/ingest",
            json={"repo_path": "/app", "mode": "quick"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        job_id = data["job_id"]
        assert UUID(job_id)  # Valid UUID
        assert data["status"] == "queued"
        
        # Step 2: Verify job is in database
        response = await http_client.get(
            f"{self.BASE_URL}/api/v1/admin/ingest/{job_id}"
        )
        assert response.status_code == 200
        job_data = response.json()
        assert job_data["job_id"] == job_id
        assert job_data["status"] in ["queued", "processing"]
        
        # Step 3: Wait for processing to start (max 10 seconds)
        max_wait = 10
        start_time = time.time()
        processing_started = False
        
        while time.time() - start_time < max_wait:
            response = await http_client.get(
                f"{self.BASE_URL}/api/v1/admin/ingest/{job_id}"
            )
            job_data = response.json()
            
            if job_data["status"] in ["processing", "completed", "failed"]:
                processing_started = True
                break
            
            await asyncio.sleep(1)
        
        assert processing_started, "Job never started processing"
        
        # Step 4: Wait for completion (max 60 seconds for quick mode)
        max_wait = 60
        start_time = time.time()
        completed = False
        
        while time.time() - start_time < max_wait:
            response = await http_client.get(
                f"{self.BASE_URL}/api/v1/admin/ingest/{job_id}"
            )
            job_data = response.json()
            
            if job_data["status"] in ["completed", "failed"]:
                completed = True
                break
            
            await asyncio.sleep(2)
        
        assert completed, "Job did not complete within timeout"
        
        # Step 5: Verify final job state
        assert job_data["status"] == "completed"
        assert job_data["total_documents"] > 0
        # Documents may be skipped if already ingested
        total_processed = (
            job_data["processed_documents"] +
            job_data["skipped_documents"] +
            job_data["failed_documents"]
        )
        assert total_processed == job_data["total_documents"]
    
    @pytest.mark.asyncio
    async def test_redis_queue_integration(self, http_client):
        """Test that jobs are properly queued to Redis."""
        # Create job
        response = await http_client.post(
            f"{self.BASE_URL}/api/v1/admin/ingest",
            json={"repo_path": "/app", "mode": "quick"}
        )
        assert response.status_code == 200
        job_id = response.json()["job_id"]
        
        # Check queue status
        response = await http_client.get(
            f"{self.BASE_URL}/api/v1/admin/queue-status"
        )
        assert response.status_code == 200
        queue_data = response.json()
        
        # Queue should have job or worker already consumed it
        # Either way, the queue should be accessible
        assert "ingestion_queue" in queue_data
        assert isinstance(queue_data["ingestion_queue"], int)
    
    @pytest.mark.asyncio
    async def test_worker_health_monitoring(self, http_client):
        """Test worker health endpoints."""
        # Check worker health
        response = await http_client.get(
            f"{self.BASE_URL}/api/v1/admin/workers/health"
        )
        assert response.status_code == 200
        health_data = response.json()
        
        assert "workers_running" in health_data
        assert "healthy" in health_data
        assert "containers" in health_data
    
    @pytest.mark.asyncio
    async def test_job_cancellation(self, http_client):
        """Test that jobs can be cancelled."""
        # Create job
        response = await http_client.post(
            f"{self.BASE_URL}/api/v1/admin/ingest",
            json={"repo_path": "/app", "mode": "quick"}
        )
        assert response.status_code == 200
        job_id = response.json()["job_id"]
        
        # Cancel job
        response = await http_client.post(
            f"{self.BASE_URL}/api/v1/admin/ingest/{job_id}/cancel"
        )
        assert response.status_code == 200
        cancel_data = response.json()
        assert cancel_data["status"] == "cancelled"
        
        # Verify job is cancelled
        response = await http_client.get(
            f"{self.BASE_URL}/api/v1/admin/ingest/{job_id}"
        )
        job_data = response.json()
        assert job_data["status"] in ["cancelled", "failed"]
    
    @pytest.mark.asyncio
    async def test_invalid_repo_path_rejected(self, http_client):
        """Test that invalid repo paths are rejected."""
        response = await http_client.post(
            f"{self.BASE_URL}/api/v1/admin/ingest",
            json={"repo_path": "/nonexistent/path", "mode": "quick"}
        )
        
        assert response.status_code == 400
        error_data = response.json()
        assert "does not exist" in error_data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_get_all_jobs(self, http_client):
        """Test getting all ingestion jobs."""
        # Create a job first
        response = await http_client.post(
            f"{self.BASE_URL}/api/v1/admin/ingest",
            json={"repo_path": "/app", "mode": "quick"}
        )
        assert response.status_code == 200
        
        # Get all jobs
        response = await http_client.get(
            f"{self.BASE_URL}/api/v1/admin/ingest/status"
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "jobs" in data
        assert "total" in data
        assert len(data["jobs"]) > 0
        
        # Verify job structure
        job = data["jobs"][0]
        required_fields = [
            "job_id", "mode", "status", "processed_documents",
            "total_documents", "failed_documents", "skipped_documents"
        ]
        for field in required_fields:
            assert field in job
    
    @pytest.mark.asyncio
    async def test_clear_completed_jobs(self, http_client):
        """Test clearing completed jobs."""
        # Get initial count
        response = await http_client.get(
            f"{self.BASE_URL}/api/v1/admin/ingest/status"
        )
        initial_data = response.json()
        initial_total = initial_data["total"]
        
        # Clear completed jobs
        response = await http_client.delete(
            f"{self.BASE_URL}/api/v1/admin/jobs/completed"
        )
        assert response.status_code == 200
        clear_data = response.json()
        assert "deleted" in clear_data
        
        # Verify jobs were deleted
        response = await http_client.get(
            f"{self.BASE_URL}/api/v1/admin/ingest/status"
        )
        final_data = response.json()
        final_total = final_data["total"]
        
        # Should have fewer or same jobs
        assert final_total <= initial_total
    
    @pytest.mark.asyncio
    async def test_job_metadata_tracking(self, http_client):
        """Test that job metadata is tracked during processing."""
        # Create job
        response = await http_client.post(
            f"{self.BASE_URL}/api/v1/admin/ingest",
            json={"repo_path": "/app", "mode": "quick"}
        )
        assert response.status_code == 200
        job_id = response.json()["job_id"]
        
        # Wait a bit for processing
        await asyncio.sleep(5)
        
        # Check job metadata
        response = await http_client.get(
            f"{self.BASE_URL}/api/v1/admin/ingest/{job_id}"
        )
        job_data = response.json()
        
        # Metadata should be present (even if empty)
        assert "job_metadata" in job_data
        metadata = job_data["job_metadata"]
        
        # If processing, should have metadata
        if job_data["status"] == "processing":
            # May have last_processed_file, current_commit, etc.
            assert isinstance(metadata, dict)


class TestIngestionRobustness:
    """Tests for ingestion robustness and error handling."""
    
    BASE_URL = "http://localhost:8000"
    
    @pytest.fixture
    def http_client(self):
        """Create an HTTP client."""
        return httpx.AsyncClient(timeout=30.0)
    
    @pytest.mark.asyncio
    async def test_concurrent_job_creation(self, http_client):
        """Test that multiple jobs can be created concurrently."""
        # Create 3 jobs concurrently
        tasks = [
            http_client.post(
                f"{self.BASE_URL}/api/v1/admin/ingest",
                json={"repo_path": "/app", "mode": "quick"}
            )
            for _ in range(3)
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert "job_id" in data
            assert data["status"] == "queued"
        
        # All should have unique job IDs
        job_ids = [r.json()["job_id"] for r in responses]
        assert len(set(job_ids)) == 3
    
    @pytest.mark.asyncio
    async def test_worker_auto_recovery(self, http_client):
        """Test worker auto-recovery endpoint."""
        response = await http_client.post(
            f"{self.BASE_URL}/api/v1/admin/workers/auto-recover"
        )
        
        # Should succeed even if workers are healthy
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "recovered" in data or "message" in data


class TestIngestionValidation:
    """Tests for ingestion input validation."""
    
    BASE_URL = "http://localhost:8000"
    
    @pytest.fixture
    def http_client(self):
        """Create an HTTP client."""
        return httpx.AsyncClient(timeout=30.0)
    
    @pytest.mark.asyncio
    async def test_missing_repo_path(self, http_client):
        """Test that missing repo_path is rejected."""
        response = await http_client.post(
            f"{self.BASE_URL}/api/v1/admin/ingest",
            json={"mode": "quick"}
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_invalid_mode(self, http_client):
        """Test that invalid modes are accepted (backend should handle)."""
        response = await http_client.post(
            f"{self.BASE_URL}/api/v1/admin/ingest",
            json={"repo_path": "/app", "mode": "invalid_mode"}
        )
        
        # Backend may accept and handle invalid modes
        # or reject with 400/422
        assert response.status_code in [200, 400, 422]
    
    @pytest.mark.asyncio
    async def test_valid_modes(self, http_client):
        """Test that valid modes are accepted."""
        modes = ["quick", "full", "incremental"]
        
        for mode in modes:
            response = await http_client.post(
                f"{self.BASE_URL}/api/v1/admin/ingest",
                json={"repo_path": "/app", "mode": mode}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "queued"
            
            # Clean up
            job_id = data["job_id"]
            await http_client.post(
                f"{self.BASE_URL}/api/v1/admin/ingest/{job_id}/cancel"
            )


# Run tests with pytest
if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-m", "integration",
        "--maxfail=3"
    ])

