"""
End-to-end tests for host path ingestion.

Tests complete workflows from path resolution to ingestion.
"""

import pytest
import httpx
import asyncio
from pathlib import Path


API_BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 60.0


class TestCompleteHostPathWorkflow:
    """E2E tests for complete host path ingestion workflow."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.slow
    async def test_complete_workflow_host_project(self):
        """
        Test complete workflow: resolve → validate → ingest.
        
        Flow:
        1. Resolve a host machine path
        2. Validate it's a git repository
        3. Check mount requirements
        4. Start ingestion (if mount available)
        """
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            test_path = "/Users/mykalthomas/Documents/work/Hackathon"
            
            print(f"\n🔍 Step 1: Resolving path {test_path}")
            
            # 1. Resolve path
            resolve_response = await client.post(
                f"{API_BASE_URL}/api/v1/path/resolve",
                json={"path": test_path}
            )
            
            assert resolve_response.status_code == 200
            resolved = resolve_response.json()
            
            print(f"✅ Git root: {resolved['git_root']}")
            print(f"   Is git repo: {resolved['is_git_repo']}")
            print(f"   Is subdirectory: {resolved.get('is_subdirectory', False)}")
            
            assert resolved["is_git_repo"] is True
            
            # 2. Validate path
            print(f"\n🔍 Step 2: Validating path")
            
            validate_response = await client.post(
                f"{API_BASE_URL}/api/v1/path/validate",
                json={"path": test_path}
            )
            
            assert validate_response.status_code == 200
            validation = validate_response.json()
            
            print(f"✅ Valid: {validation['is_valid']}")
            print(f"   Message: {validation['message']}")
            
            assert validation["is_valid"] is True
            
            # 3. Check mount requirements
            if resolved.get("is_host_mount"):
                print(f"\n⚙️  Step 3: Checking mount requirements")
                
                mount_response = await client.post(
                    f"{API_BASE_URL}/api/v1/path/suggest-mount",
                    json={"path": test_path}
                )
                
                assert mount_response.status_code == 200
                mount_info = mount_response.json()
                
                print(f"   Needs mount: {mount_info['needs_mount']}")
                
                if mount_info["needs_mount"]:
                    print(f"   Mount config needed - see suggestion")
                    # In real scenario, would configure mount here
            
            # 4. Attempt ingestion (may fail if mount not configured)
            print(f"\n🚀 Step 4: Starting ingestion")
            
            ingest_response = await client.post(
                f"{API_BASE_URL}/api/v1/admin/ingest",
                json={
                    "repo_path": test_path,
                    "mode": "quick",
                    "resolve_host_path": True
                }
            )
            
            # Should either succeed or give clear error
            assert ingest_response.status_code in [200, 400]
            
            if ingest_response.status_code == 200:
                result = ingest_response.json()
                print(f"✅ Ingestion started: {result.get('job_id')}")
            else:
                error = ingest_response.json()
                print(f"⚠️  Ingestion blocked: {error.get('detail', 'Unknown error')[:100]}")
            
            print(f"\n✅ E2E workflow complete")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_subdirectory_targeting_workflow(self):
        """
        Test workflow for targeting a specific subdirectory.
        
        Flow:
        1. Point to a subdirectory in a repo
        2. System detects git root
        3. System identifies subdirectory target
        4. Ingestion uses git root but targets subdirectory
        """
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            # Target a subdirectory
            test_path = "/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp"
            
            print(f"\n📁 Testing subdirectory targeting: {test_path}")
            
            # Resolve the subdirectory path
            response = await client.post(
                f"{API_BASE_URL}/api/v1/path/resolve",
                json={"path": test_path}
            )
            
            assert response.status_code == 200
            resolved = response.json()
            
            print(f"✅ Git root detected: {resolved['git_root']}")
            print(f"   Target subdirectory: {resolved.get('target_subdir')}")
            print(f"   Is subdirectory: {resolved.get('is_subdirectory')}")
            
            # Should detect parent git root
            assert resolved["is_git_repo"] is True
            assert "Hackathon" in resolved["git_root"]
            
            # Should identify subdirectory targeting
            if resolved.get("is_subdirectory"):
                assert resolved["target_subdir"] is not None
                assert "services" in resolved["target_subdir"]
                print(f"✅ Subdirectory targeting detected correctly")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_multiple_projects_validation(self):
        """
        Test validating multiple project paths in batch.
        
        Simulates user checking multiple projects before ingestion.
        """
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            test_paths = [
                "/Users/mykalthomas/Documents/work/Hackathon",
                "/Users/mykalthomas/Documents/work/Hackathon/services",
                "/tmp",  # Not a git repo
            ]
            
            results = []
            
            print(f"\n📊 Validating {len(test_paths)} paths")
            
            for path in test_paths:
                response = await client.post(
                    f"{API_BASE_URL}/api/v1/path/validate",
                    json={"path": path}
                )
                
                assert response.status_code == 200
                result = response.json()
                results.append((path, result))
                
                status = "✅ Valid" if result["is_valid"] else "❌ Invalid"
                print(f"{status}: {path}")
            
            # First two should be valid (git repos)
            assert results[0][1]["is_valid"] is True
            assert results[1][1]["is_valid"] is True
            
            # Third should be invalid (not a git repo)
            assert results[2][1]["is_valid"] is False
            
            print(f"✅ Batch validation complete")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_error_handling_workflow(self):
        """
        Test error handling in host path workflow.
        
        Tests:
        - Non-existent path
        - Non-git directory
        - Sensitive directory
        """
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            print(f"\n🧪 Testing error handling")
            
            test_cases = [
                ("/nonexistent/path/12345", "non-existent"),
                ("/tmp", "non-git"),
                ("/etc", "sensitive"),
            ]
            
            for path, case_type in test_cases:
                print(f"\n   Testing {case_type}: {path}")
                
                response = await client.post(
                    f"{API_BASE_URL}/api/v1/path/validate",
                    json={"path": path}
                )
                
                assert response.status_code == 200
                result = response.json()
                
                # Should be invalid
                assert result["is_valid"] is False
                print(f"   ✅ Correctly rejected: {result['message'][:60]}")
            
            print(f"\n✅ Error handling verified")


class TestHostPathPerformance:
    """E2E tests for performance characteristics."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_resolution_performance(self):
        """Test that path resolution completes quickly."""
        import time
        
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            start = time.time()
            
            response = await client.post(
                f"{API_BASE_URL}/api/v1/path/resolve",
                json={"path": "/Users/mykalthomas/Documents/work/Hackathon"}
            )
            
            elapsed = time.time() - start
            
            assert response.status_code == 200
            assert elapsed < 2.0  # Should be fast
            
            print(f"\n⚡ Path resolution took {elapsed:.3f}s")


class TestRealWorldScenarios:
    """E2E tests for real-world usage scenarios."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_user_ingests_personal_project(self):
        """
        Simulate user ingesting their own project.
        
        Scenario:
        - User has a project at ~/Documents/work/MyProject
        - User wants to ingest it into the system
        - System should handle everything automatically
        """
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            # Use Hackathon as example project
            user_project = "/Users/mykalthomas/Documents/work/Hackathon"
            
            print(f"\n👤 User scenario: Ingesting personal project")
            print(f"   Project: {user_project}")
            
            # User validates the path first (via dashboard)
            response = await client.post(
                f"{API_BASE_URL}/api/v1/path/validate",
                json={"path": user_project}
            )
            
            assert response.status_code == 200
            validation = response.json()
            
            if validation["is_valid"]:
                print(f"   ✅ Path is valid")
                
                # User starts ingestion
                response = await client.post(
                    f"{API_BASE_URL}/api/v1/admin/ingest",
                    json={
                        "repo_path": user_project,
                        "mode": "quick",
                        "resolve_host_path": True
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ Ingestion started: {result.get('job_id')}")
                else:
                    error = response.json()
                    print(f"   ℹ️  Mount required: {error.get('detail', '')[:60]}")
            else:
                print(f"   ❌ Path validation failed: {validation['message']}")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_user_ingests_specific_directory(self):
        """
        Simulate user ingesting only a specific directory.
        
        Scenario:
        - User has large repo
        - Only wants to ingest /docs folder
        - System should detect and handle subdirectory targeting
        """
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            # Target docs directory
            target_path = "/Users/mykalthomas/Documents/work/Hackathon/docs"
            
            print(f"\n📁 User scenario: Ingesting specific directory")
            print(f"   Target: {target_path}")
            
            response = await client.post(
                f"{API_BASE_URL}/api/v1/path/resolve",
                json={"path": target_path}
            )
            
            assert response.status_code == 200
            resolved = response.json()
            
            if resolved.get("is_subdirectory"):
                print(f"   ✅ Subdirectory detected: {resolved['target_subdir']}")
                print(f"   📂 Will use git root: {resolved['git_root']}")
                print(f"   📁 But only ingest: {resolved['target_subdir']}")
            else:
                print(f"   ℹ️  Not a subdirectory (might be the root)")


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

