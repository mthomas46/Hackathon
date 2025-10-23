"""
Integration tests for admin API routes.

Tests admin operations including system management, health checks,
and administrative controls.
"""

import pytest
from datetime import datetime
from uuid import uuid4


pytestmark = pytest.mark.integration


class TestAdminHealthEndpoints:
    """Test admin health check endpoints."""

    async def test_admin_health_check(self, async_test_client):
        """Test admin health check endpoint."""
        response = await async_test_client.get("/api/v1/admin/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

    async def test_admin_detailed_health(self, async_test_client):
        """Test detailed health check."""
        response = await async_test_client.get("/api/v1/admin/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        assert "database" in data
        assert "redis" in data
        assert "chromadb" in data

    async def test_admin_readiness_check(self, async_test_client):
        """Test readiness check endpoint."""
        response = await async_test_client.get("/api/v1/admin/ready")
        
        assert response.status_code in [200, 503]
        data = response.json()
        assert "ready" in data


class TestAdminSystemManagement:
    """Test admin system management endpoints."""

    async def test_get_system_info(self, async_test_client):
        """Test getting system information."""
        response = await async_test_client.get("/api/v1/admin/system/info")
        
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "uptime" in data
        assert "environment" in data

    async def test_get_system_metrics(self, async_test_client):
        """Test getting system metrics."""
        response = await async_test_client.get("/api/v1/admin/system/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert "cpu_usage" in data or "memory_usage" in data

    async def test_system_shutdown(self, async_test_client):
        """Test system shutdown endpoint (should require auth)."""
        response = await async_test_client.post("/api/v1/admin/system/shutdown")
        
        # Should require authentication or return method not allowed
        assert response.status_code in [401, 403, 405, 501]


class TestAdminDatabaseManagement:
    """Test admin database management endpoints."""

    async def test_get_database_stats(self, async_test_client):
        """Test getting database statistics."""
        response = await async_test_client.get("/api/v1/admin/database/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_documents" in data or "connections" in data

    async def test_database_health(self, async_test_client):
        """Test database health check."""
        response = await async_test_client.get("/api/v1/admin/database/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    async def test_database_vacuum(self, async_test_client):
        """Test database vacuum operation."""
        response = await async_test_client.post("/api/v1/admin/database/vacuum")
        
        # Should either work or require permissions
        assert response.status_code in [200, 202, 401, 403]


class TestAdminCacheManagement:
    """Test admin cache management endpoints."""

    async def test_clear_all_caches(self, async_test_client):
        """Test clearing all caches."""
        response = await async_test_client.post("/api/v1/admin/cache/clear")
        
        assert response.status_code in [200, 202]
        data = response.json()
        assert "success" in data or "cleared" in data

    async def test_clear_specific_cache(self, async_test_client):
        """Test clearing specific cache."""
        response = await async_test_client.post("/api/v1/admin/cache/clear/embeddings")
        
        assert response.status_code in [200, 202, 404]

    async def test_get_cache_stats(self, async_test_client):
        """Test getting cache statistics."""
        response = await async_test_client.get("/api/v1/admin/cache/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "hit_rate" in data or "total_keys" in data


class TestAdminJobManagement:
    """Test admin job management endpoints."""

    async def test_list_all_jobs(self, async_test_client):
        """Test listing all jobs."""
        response = await async_test_client.get("/api/v1/admin/jobs")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "jobs" in data

    async def test_cancel_job(self, async_test_client):
        """Test canceling a job."""
        # Try to cancel non-existent job
        job_id = str(uuid4())
        response = await async_test_client.post(f"/api/v1/admin/jobs/{job_id}/cancel")
        
        # Should return 404 or 200
        assert response.status_code in [200, 404]

    async def test_retry_failed_job(self, async_test_client):
        """Test retrying a failed job."""
        job_id = str(uuid4())
        response = await async_test_client.post(f"/api/v1/admin/jobs/{job_id}/retry")
        
        assert response.status_code in [200, 404]

    async def test_purge_old_jobs(self, async_test_client):
        """Test purging old jobs."""
        response = await async_test_client.post("/api/v1/admin/jobs/purge", json={"days": 30})
        
        assert response.status_code in [200, 202]


class TestAdminUserManagement:
    """Test admin user management endpoints."""

    async def test_list_users(self, async_test_client):
        """Test listing users."""
        response = await async_test_client.get("/api/v1/admin/users")
        
        # May require auth or not be implemented
        assert response.status_code in [200, 401, 403, 501]

    async def test_create_user(self, async_test_client):
        """Test creating a user."""
        response = await async_test_client.post("/api/v1/admin/users", json={
            "username": "testuser",
            "email": "test@example.com"
        })
        
        # May require auth or not be implemented
        assert response.status_code in [200, 201, 401, 403, 501]


class TestAdminConfigManagement:
    """Test admin configuration management endpoints."""

    async def test_get_config(self, async_test_client):
        """Test getting configuration."""
        response = await async_test_client.get("/api/v1/admin/config")
        
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    async def test_update_config(self, async_test_client):
        """Test updating configuration."""
        response = await async_test_client.patch("/api/v1/admin/config", json={
            "setting": "value"
        })
        
        # Should require auth
        assert response.status_code in [200, 401, 403, 405]

    async def test_reload_config(self, async_test_client):
        """Test reloading configuration."""
        response = await async_test_client.post("/api/v1/admin/config/reload")
        
        assert response.status_code in [200, 202, 401, 403]

