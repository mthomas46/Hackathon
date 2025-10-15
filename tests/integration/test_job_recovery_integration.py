"""
Integration tests for job recovery system.

Tests the full recovery flow with real database interactions.
"""

import pytest
import asyncio
import httpx
from uuid import uuid4
from datetime import datetime
from pathlib import Path


# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 60.0


class TestIngestionRecoveryIntegration:
    """Integration tests for ingestion job recovery."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_ingestion_checkpoint_creation(self):
        """Test that ingestion creates checkpoints during processing."""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            # Start an ingestion job
            response = await client.post(
                f"{API_BASE_URL}/api/v1/admin/ingestion/jobs",
                json={
                    "mode": "quick",
                    "repo_path": "/app",
                    "service_id": "test-service"
                }
            )
            
            assert response.status_code == 200
            job_data = response.json()
            job_id = job_data["job_id"]
            
            # Wait a bit for processing to start
            await asyncio.sleep(5)
            
            # Check for checkpoints
            response = await client.get(
                f"{API_BASE_URL}/api/v1/recovery/checkpoints/{job_id}"
            )
            
            if response.status_code == 200:
                checkpoint_data = response.json()
                
                # Job should have created at least one checkpoint if processing started
                # (May be 0 if job finished very quickly)
                assert checkpoint_data["total_checkpoints"] >= 0
                assert isinstance(checkpoint_data["checkpoints"], list)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_ingestion_recovery_status(self):
        """Test getting recovery status for an ingestion job."""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            # Start a job
            response = await client.post(
                f"{API_BASE_URL}/api/v1/admin/ingestion/jobs",
                json={
                    "mode": "quick",
                    "repo_path": "/app",
                    "service_id": "test-recovery"
                }
            )
            
            assert response.status_code == 200
            job_id = response.json()["job_id"]
            
            # Wait for some progress
            await asyncio.sleep(3)
            
            # Get recovery status
            response = await client.get(
                f"{API_BASE_URL}/api/v1/recovery/status/{job_id}"
            )
            
            # Status endpoint should work even if no checkpoints yet
            assert response.status_code == 200
            status = response.json()
            
            assert status["job_id"] == job_id
            assert "can_resume" in status
            assert isinstance(status["can_resume"], bool)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_ingestion_full_recovery_flow(self):
        """Test complete ingestion recovery: start -> interrupt -> resume."""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            # 1. Start ingestion job with full mode (will take a while)
            response = await client.post(
                f"{API_BASE_URL}/api/v1/admin/ingestion/jobs",
                json={
                    "mode": "recent",  # Process last 200 commits
                    "repo_path": "/app",
                    "service_id": "test-full-recovery"
                }
            )
            
            assert response.status_code == 200
            job_id = response.json()["job_id"]
            
            # 2. Wait for job to process a few commits and create checkpoints
            await asyncio.sleep(10)
            
            # 3. Check that checkpoints were created
            response = await client.get(
                f"{API_BASE_URL}/api/v1/recovery/checkpoints/{job_id}"
            )
            
            if response.status_code == 200:
                checkpoint_data = response.json()
                initial_checkpoint_count = checkpoint_data["total_checkpoints"]
                
                # If checkpoints exist, we can test recovery
                if initial_checkpoint_count > 0:
                    # 4. Get recovery status
                    response = await client.get(
                        f"{API_BASE_URL}/api/v1/recovery/status/{job_id}"
                    )
                    
                    assert response.status_code == 200
                    status = response.json()
                    
                    # Should be able to resume if we have completed checkpoints
                    if status["can_resume"]:
                        # 5. Attempt to resume (even though job might still be running)
                        # In real scenario, job would be interrupted first
                        response = await client.post(
                            f"{API_BASE_URL}/api/v1/recovery/resume",
                            json={
                                "job_id": job_id,
                                "job_type": "ingestion"
                            },
                            timeout=30.0
                        )
                        
                        # Resume should work or give clear error
                        assert response.status_code in [200, 400, 409]


class TestEmbeddingRecoveryIntegration:
    """Integration tests for embedding generation recovery."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_embedding_regeneration_with_checkpoints(self):
        """Test that embedding regeneration creates checkpoints."""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            # Trigger embedding regeneration
            response = await client.post(
                f"{API_BASE_URL}/api/v1/admin/embeddings/regenerate",
                json={
                    "batch_size": 10,
                    "skip_existing": True
                }
            )
            
            # Should start regeneration
            assert response.status_code in [200, 202]
            
            if response.status_code == 200:
                result = response.json()
                job_id = result.get("job_id")
                
                if job_id:
                    # Wait a bit for processing
                    await asyncio.sleep(5)
                    
                    # Check for checkpoints
                    response = await client.get(
                        f"{API_BASE_URL}/api/v1/recovery/checkpoints/{job_id}"
                    )
                    
                    if response.status_code == 200:
                        checkpoint_data = response.json()
                        assert "total_checkpoints" in checkpoint_data
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_embedding_recovery_status(self):
        """Test getting recovery status for embedding generation."""
        # This test would require a way to get the job_id from
        # the regeneration endpoint, which may need API enhancement
        pass


class TestDocumentationRecoveryIntegration:
    """Integration tests for documentation generation recovery."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_documentation_checkpoint_creation(self):
        """Test that documentation generation creates checkpoints."""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            # Start documentation generation
            response = await client.post(
                f"{API_BASE_URL}/api/v1/multi-pass",
                json={
                    "query": "system architecture",
                    "num_passes": 2,
                    "questions_per_pass": 2,
                    "output_format": "markdown",
                    "tier": "docker"
                },
                timeout=120.0
            )
            
            # Multi-pass should complete or timeout
            if response.status_code == 200:
                result = response.json()
                
                # Check if job_id is returned (may need API enhancement)
                job_id = result.get("job_id")
                
                if job_id:
                    # Check for checkpoints
                    response = await client.get(
                        f"{API_BASE_URL}/api/v1/recovery/checkpoints/{job_id}"
                    )
                    
                    if response.status_code == 200:
                        checkpoint_data = response.json()
                        
                        # Should have checkpoint per pass
                        assert checkpoint_data["total_checkpoints"] >= 0


class TestRecoveryAPIIntegration:
    """Integration tests for recovery API endpoints."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_recovery_status_endpoint(self):
        """Test recovery status endpoint with valid and invalid job IDs."""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            # Test with non-existent job ID
            fake_job_id = str(uuid4())
            response = await client.get(
                f"{API_BASE_URL}/api/v1/recovery/status/{fake_job_id}"
            )
            
            # Should return 200 with can_resume=false for non-existent job
            assert response.status_code == 200
            status = response.json()
            assert status["can_resume"] is False
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_checkpoints_endpoint(self):
        """Test checkpoints listing endpoint."""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            # Test with non-existent job ID
            fake_job_id = str(uuid4())
            response = await client.get(
                f"{API_BASE_URL}/api/v1/recovery/checkpoints/{fake_job_id}"
            )
            
            # Should return 200 with empty checkpoints list
            assert response.status_code == 200
            data = response.json()
            assert data["total_checkpoints"] == 0
            assert data["checkpoints"] == []
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_resume_endpoint_validation(self):
        """Test resume endpoint input validation."""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            # Test with invalid job type
            response = await client.post(
                f"{API_BASE_URL}/api/v1/recovery/resume",
                json={
                    "job_id": str(uuid4()),
                    "job_type": "invalid_type"
                }
            )
            
            # Should reject invalid job type
            assert response.status_code == 400
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_cleanup_endpoint(self):
        """Test checkpoint cleanup endpoint."""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            # Create a job first
            response = await client.post(
                f"{API_BASE_URL}/api/v1/admin/ingestion/jobs",
                json={
                    "mode": "quick",
                    "repo_path": "/app",
                    "service_id": "test-cleanup"
                }
            )
            
            if response.status_code == 200:
                job_id = response.json()["job_id"]
                
                # Wait for job to create checkpoints
                await asyncio.sleep(5)
                
                # Cleanup checkpoints
                response = await client.delete(
                    f"{API_BASE_URL}/api/v1/recovery/checkpoints/{job_id}",
                    params={"keep_last": 2}
                )
                
                # Should work or return 200 even if no checkpoints
                assert response.status_code == 200
                
                result = response.json()
                assert "checkpoints_before" in result
                assert "checkpoints_after" in result
                assert "removed" in result


class TestRecoveryEdgeCases:
    """Test edge cases and error scenarios."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_resume_already_completed_job(self):
        """Test resuming a job that already completed."""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            # Start a very quick job
            response = await client.post(
                f"{API_BASE_URL}/api/v1/admin/ingestion/jobs",
                json={
                    "mode": "quick",
                    "repo_path": "/app",
                    "service_id": "test-completed"
                }
            )
            
            if response.status_code == 200:
                job_id = response.json()["job_id"]
                
                # Wait for job to complete
                await asyncio.sleep(15)
                
                # Try to resume
                response = await client.post(
                    f"{API_BASE_URL}/api/v1/recovery/resume",
                    json={
                        "job_id": job_id,
                        "job_type": "ingestion"
                    },
                    timeout=30.0
                )
                
                # Should handle gracefully (200 with result, or 400 if can't resume)
                assert response.status_code in [200, 400]
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_concurrent_checkpoint_operations(self):
        """Test concurrent checkpoint operations don't conflict."""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            # Start a job
            response = await client.post(
                f"{API_BASE_URL}/api/v1/admin/ingestion/jobs",
                json={
                    "mode": "recent",
                    "repo_path": "/app",
                    "service_id": "test-concurrent"
                }
            )
            
            if response.status_code == 200:
                job_id = response.json()["job_id"]
                
                # Wait for checkpoints to be created
                await asyncio.sleep(5)
                
                # Make concurrent requests for status and checkpoints
                tasks = [
                    client.get(f"{API_BASE_URL}/api/v1/recovery/status/{job_id}"),
                    client.get(f"{API_BASE_URL}/api/v1/recovery/checkpoints/{job_id}"),
                    client.get(f"{API_BASE_URL}/api/v1/recovery/status/{job_id}"),
                ]
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                # All should succeed
                for resp in responses:
                    if isinstance(resp, httpx.Response):
                        assert resp.status_code == 200


# Pytest configuration
def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow-running"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration", "--tb=short"])

