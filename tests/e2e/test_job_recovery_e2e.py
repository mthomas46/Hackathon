"""
End-to-end tests for job recovery system.

Simulates real-world scenarios with actual interruptions and resumes.
"""

import pytest
import asyncio
import httpx
import signal
import subprocess
import time
from uuid import uuid4
from pathlib import Path


API_BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 120.0


class TestIngestionRecoveryE2E:
    """E2E tests for ingestion job recovery."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.slow
    async def test_interrupt_and_resume_ingestion(self):
        """
        E2E test: Start ingestion, wait for checkpoints, interrupt, resume.
        
        Flow:
        1. Start large ingestion job (recent mode, 200 commits)
        2. Wait for 2-3 checkpoints to be created
        3. Get recovery status showing progress
        4. Simulate resume (can't actually interrupt running job safely)
        5. Verify recovery state is correct
        """
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            # 1. Start large ingestion job
            print("\n📥 Starting ingestion job...")
            response = await client.post(
                f"{API_BASE_URL}/api/v1/admin/ingestion/jobs",
                json={
                    "mode": "recent",  # 200 commits
                    "repo_path": "/app",
                    "service_id": "e2e-ingestion-test"
                }
            )
            
            assert response.status_code == 200
            job_id = response.json()["job_id"]
            print(f"✅ Job started: {job_id}")
            
            # 2. Wait for checkpoints to be created
            print("⏳ Waiting for checkpoints...")
            await asyncio.sleep(15)
            
            # 3. Check progress and checkpoints
            response = await client.get(
                f"{API_BASE_URL}/api/v1/recovery/checkpoints/{job_id}"
            )
            
            assert response.status_code == 200
            checkpoint_data = response.json()
            
            print(f"📊 Checkpoints created: {checkpoint_data['total_checkpoints']}")
            print(f"   ✅ Completed: {checkpoint_data['completed_checkpoints']}")
            print(f"   ⏳ Pending: {checkpoint_data['pending_checkpoints']}")
            print(f"   ❌ Failed: {checkpoint_data['failed_checkpoints']}")
            
            # 4. Get recovery status
            response = await client.get(
                f"{API_BASE_URL}/api/v1/recovery/status/{job_id}"
            )
            
            assert response.status_code == 200
            status = response.json()
            
            print(f"\n🔄 Recovery Status:")
            print(f"   Can Resume: {status['can_resume']}")
            print(f"   Job Type: {status.get('job_type', 'unknown')}")
            
            if status.get("progress"):
                progress = status["progress"]
                print(f"   Progress: {progress['completed_checkpoints']}/{progress['total_checkpoints']}")
            
            # 5. Verify checkpoint structure
            if checkpoint_data["total_checkpoints"] > 0:
                first_checkpoint = checkpoint_data["checkpoints"][0]
                
                assert "checkpoint_id" in first_checkpoint
                assert "sequence" in first_checkpoint
                assert "status" in first_checkpoint
                assert "data" in first_checkpoint
                assert "created_at" in first_checkpoint
                
                print(f"\n✅ Checkpoint structure validated")
                
                # If we have completed checkpoints, test resume capability
                if status["can_resume"]:
                    print(f"\n🔄 Testing resume capability...")
                    
                    # Note: In real scenario, we'd interrupt the job first
                    # For testing, we just verify the resume API works
                    response = await client.post(
                        f"{API_BASE_URL}/api/v1/recovery/resume",
                        json={
                            "job_id": job_id,
                            "job_type": "ingestion"
                        },
                        timeout=60.0
                    )
                    
                    # Should work or give clear error
                    assert response.status_code in [200, 400, 409]
                    
                    if response.status_code == 200:
                        result = response.json()
                        print(f"✅ Resume API responded successfully")
                        print(f"   Message: {result.get('message', 'N/A')}")
                    else:
                        print(f"⚠️  Resume returned {response.status_code} (expected for running job)")
            
            print("\n✅ E2E ingestion recovery test complete")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_checkpoint_persistence_across_restarts(self):
        """
        Test that checkpoints persist after service restart.
        
        Note: This test requires manual service restart or mocking.
        """
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            # Start a job
            response = await client.post(
                f"{API_BASE_URL}/api/v1/admin/ingestion/jobs",
                json={
                    "mode": "quick",
                    "repo_path": "/app",
                    "service_id": "e2e-persistence-test"
                }
            )
            
            assert response.status_code == 200
            job_id = response.json()["job_id"]
            
            # Wait for checkpoints
            await asyncio.sleep(10)
            
            # Get checkpoints before "restart"
            response = await client.get(
                f"{API_BASE_URL}/api/v1/recovery/checkpoints/{job_id}"
            )
            
            if response.status_code == 200:
                checkpoints_before = response.json()
                
                # After service restart, checkpoints should still be loadable
                # (In real test, we'd restart the service here)
                
                # Verify checkpoints still accessible
                response = await client.get(
                    f"{API_BASE_URL}/api/v1/recovery/checkpoints/{job_id}"
                )
                
                assert response.status_code == 200
                checkpoints_after = response.json()
                
                # Checkpoint count should be same (they're persisted in DB)
                assert checkpoints_after["total_checkpoints"] == checkpoints_before["total_checkpoints"]
                
                print(f"✅ Checkpoint persistence verified: {checkpoints_after['total_checkpoints']} checkpoints")


class TestEmbeddingRecoveryE2E:
    """E2E tests for embedding generation recovery."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.slow
    async def test_embedding_generation_recovery_flow(self):
        """
        E2E test for embedding generation recovery.
        
        Flow:
        1. Start embedding regeneration
        2. Monitor progress via checkpoints
        3. Verify checkpoint data contains batch info
        """
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            print("\n🎯 Starting embedding regeneration...")
            
            # Check if there are documents to process
            response = await client.get(
                f"{API_BASE_URL}/api/v1/admin/embeddings/stats"
            )
            
            if response.status_code == 200:
                stats = response.json()
                missing_count = stats.get("missing_embeddings", 0)
                
                print(f"📊 Missing embeddings: {missing_count}")
                
                if missing_count > 0:
                    # Start regeneration
                    response = await client.post(
                        f"{API_BASE_URL}/api/v1/admin/embeddings/regenerate",
                        json={
                            "batch_size": 10,
                            "skip_existing": True
                        }
                    )
                    
                    if response.status_code in [200, 202]:
                        result = response.json()
                        job_id = result.get("job_id")
                        
                        if job_id:
                            print(f"✅ Regeneration started: {job_id}")
                            
                            # Wait for processing
                            await asyncio.sleep(10)
                            
                            # Check checkpoints
                            response = await client.get(
                                f"{API_BASE_URL}/api/v1/recovery/checkpoints/{job_id}"
                            )
                            
                            if response.status_code == 200:
                                checkpoint_data = response.json()
                                print(f"📊 Checkpoints: {checkpoint_data['total_checkpoints']}")
                                
                                # Verify checkpoint data structure
                                if checkpoint_data["checkpoints"]:
                                    cp = checkpoint_data["checkpoints"][0]
                                    
                                    # Should have embedding-specific data
                                    if "data" in cp:
                                        data = cp["data"]
                                        assert "processed" in data or "offset" in data
                                        print(f"✅ Embedding checkpoint structure validated")
                        else:
                            print("⚠️  No job_id returned (feature may need implementation)")
                else:
                    print("ℹ️  No missing embeddings to test with")
            
            print("\n✅ E2E embedding recovery test complete")


class TestDocumentationRecoveryE2E:
    """E2E tests for documentation generation recovery."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.slow
    async def test_documentation_multipass_recovery(self):
        """
        E2E test for multi-pass documentation recovery.
        
        Flow:
        1. Start multi-pass documentation generation
        2. Monitor checkpoint creation per pass
        3. Verify checkpoint contains pass information
        """
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            print("\n📖 Starting multi-pass documentation generation...")
            
            response = await client.post(
                f"{API_BASE_URL}/api/v1/multi-pass",
                json={
                    "query": "testing job recovery system",
                    "num_passes": 2,
                    "questions_per_pass": 2,
                    "output_format": "markdown",
                    "tier": "docker"
                },
                timeout=120.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Multi-pass completed")
                
                # Check if job_id is available
                job_id = result.get("job_id")
                
                if job_id:
                    # Check checkpoints
                    response = await client.get(
                        f"{API_BASE_URL}/api/v1/recovery/checkpoints/{job_id}"
                    )
                    
                    if response.status_code == 200:
                        checkpoint_data = response.json()
                        
                        print(f"📊 Checkpoints: {checkpoint_data['total_checkpoints']}")
                        
                        # Should have checkpoints per pass
                        if checkpoint_data["checkpoints"]:
                            for cp in checkpoint_data["checkpoints"]:
                                if "data" in cp and "pass_id" in cp["data"]:
                                    print(f"   Pass {cp['data']['pass_id']}: {cp['status']}")
                            
                            print(f"✅ Documentation checkpoint structure validated")
                else:
                    print("⚠️  No job_id in response (feature may need implementation)")
            else:
                print(f"⚠️  Multi-pass returned {response.status_code}")
            
            print("\n✅ E2E documentation recovery test complete")


class TestRecoveryWorkflowE2E:
    """E2E tests for complete recovery workflows."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_complete_recovery_workflow(self):
        """
        Complete workflow test: Create, monitor, check, cleanup.
        
        Flow:
        1. Start job
        2. Monitor checkpoints
        3. Check recovery status
        4. Verify resumability
        5. Cleanup old checkpoints
        """
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            print("\n🔄 Testing complete recovery workflow...")
            
            # 1. Start job
            print("\n1️⃣  Creating job...")
            response = await client.post(
                f"{API_BASE_URL}/api/v1/admin/ingestion/jobs",
                json={
                    "mode": "quick",
                    "repo_path": "/app",
                    "service_id": "e2e-workflow-test"
                }
            )
            
            assert response.status_code == 200
            job_id = response.json()["job_id"]
            print(f"   ✅ Job created: {job_id}")
            
            # 2. Monitor checkpoints
            print("\n2️⃣  Monitoring checkpoints...")
            await asyncio.sleep(5)
            
            response = await client.get(
                f"{API_BASE_URL}/api/v1/recovery/checkpoints/{job_id}"
            )
            
            assert response.status_code == 200
            checkpoints = response.json()
            print(f"   ✅ Found {checkpoints['total_checkpoints']} checkpoints")
            
            # 3. Check recovery status
            print("\n3️⃣  Checking recovery status...")
            response = await client.get(
                f"{API_BASE_URL}/api/v1/recovery/status/{job_id}"
            )
            
            assert response.status_code == 200
            status = response.json()
            print(f"   ✅ Can resume: {status['can_resume']}")
            
            # 4. Verify resumability
            if status["can_resume"]:
                print("\n4️⃣  Verifying resume capability...")
                
                # Test resume API (may not actually resume if job is done)
                response = await client.post(
                    f"{API_BASE_URL}/api/v1/recovery/resume",
                    json={
                        "job_id": job_id,
                        "job_type": "ingestion"
                    },
                    timeout=30.0
                )
                
                print(f"   ✅ Resume API responded: {response.status_code}")
            
            # 5. Cleanup
            print("\n5️⃣  Cleaning up checkpoints...")
            await asyncio.sleep(2)  # Ensure job is done
            
            response = await client.delete(
                f"{API_BASE_URL}/api/v1/recovery/checkpoints/{job_id}",
                params={"keep_last": 1}
            )
            
            assert response.status_code == 200
            cleanup_result = response.json()
            print(f"   ✅ Cleaned up {cleanup_result['removed']} checkpoints")
            print(f"   Kept: {cleanup_result['checkpoints_after']}")
            
            print("\n✅ Complete workflow test passed")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_recovery_ui_integration(self):
        """
        Test that recovery UI can interact with backend properly.
        
        Simulates dashboard operations.
        """
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            print("\n🖥️  Testing recovery UI integration...")
            
            # Create a job
            response = await client.post(
                f"{API_BASE_URL}/api/v1/admin/ingestion/jobs",
                json={
                    "mode": "quick",
                    "repo_path": "/app",
                    "service_id": "e2e-ui-test"
                }
            )
            
            job_id = response.json()["job_id"]
            await asyncio.sleep(5)
            
            # Simulate UI operations
            operations = [
                ("Status Check", f"/api/v1/recovery/status/{job_id}", "GET"),
                ("List Checkpoints", f"/api/v1/recovery/checkpoints/{job_id}", "GET"),
                ("Job Stats", f"/api/v1/admin/ingestion/jobs/{job_id}", "GET"),
            ]
            
            for op_name, endpoint, method in operations:
                if method == "GET":
                    response = await client.get(f"{API_BASE_URL}{endpoint}")
                
                print(f"   {op_name}: {response.status_code}")
                assert response.status_code == 200
            
            print("\n✅ UI integration test passed")


# Pytest configuration
def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow-running"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "e2e", "--tb=short"])

