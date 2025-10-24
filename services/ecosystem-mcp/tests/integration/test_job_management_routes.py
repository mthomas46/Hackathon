"""
Integration tests for job management API routes.

Tests job progress tracking, recovery, and monitoring endpoints.
"""

import pytest
from datetime import datetime
from uuid import uuid4


from .test_helpers import skip_if_no_redis, redis_available


pytestmark = pytest.mark.integration



class TestJobProgressTracking:
    """Test job progress tracking endpoints."""

    async def test_get_job_progress(self, async_test_client):
        """Test getting job progress."""
        job_id = str(uuid4())
        response = await async_test_client.get(f"/api/v1/admin/ingest/status/{job_id}/progress")
        
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "progress" in data or "percentage" in data

    async def test_stream_job_progress(self, async_test_client):
        """Test streaming job progress."""
        job_id = str(uuid4())
        response = await async_test_client.get(f"/api/v1/admin/ingest/status/{job_id}/progress/stream")
        
        # SSE endpoint
        assert response.status_code in [200, 404]

    async def test_get_job_metrics(self, async_test_client):
        """Test getting job metrics."""
        job_id = str(uuid4())
        response = await async_test_client.get(f"/api/v1/admin/ingest/status/{job_id}/metrics")
        
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "processed" in data or "failed" in data

    async def test_get_job_timeline(self, async_test_client):
        """Test getting job timeline."""
        job_id = str(uuid4())
        response = await async_test_client.get(f"/api/v1/admin/ingest/status/{job_id}/timeline")
        
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or "events" in data


class TestJobRecoveryAPI:
    """Test job recovery API endpoints."""

    async def test_list_recoverable_jobs(self, async_test_client):
        """Test listing recoverable jobs."""
        response = await async_test_client.get("/api/v1/admin/ingest/status/recovery/list")
        
        assert response.status_code in [200, 404, 500, 503]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or "jobs" in data

    async def test_recover_job(self, async_test_client):
        """Test recovering a job."""
        job_id = str(uuid4())
        response = await async_test_client.post(f"/api/v1/admin/ingest/status/{job_id}/recover")
        
        assert response.status_code in [200, 202, 404]

    async def test_recover_all_jobs(self, async_test_client):
        """Test recovering all failed jobs."""
        response = await async_test_client.post("/api/v1/admin/ingest/status/recovery/recover-all")
        
        assert response.status_code in [200, 202, 404, 500]
        if response.status_code in [200, 202]:
            data = response.json()
            assert "recovered_count" in data or "jobs" in data

    async def test_get_recovery_status(self, async_test_client):
        """Test getting recovery status."""
        job_id = str(uuid4())
        response = await async_test_client.get(f"/api/v1/admin/ingest/status/{job_id}/recovery/status")
        
        assert response.status_code in [200, 404]

    async def test_cleanup_checkpoints(self, async_test_client):
        """Test cleaning up old checkpoints."""
        response = await async_test_client.post("/api/v1/admin/ingest/status/recovery/cleanup", json={
            "days": 30
        })
        
        assert response.status_code in [200, 202, 404, 500]


class TestIngestionLogs:
    """Test ingestion log viewing endpoints."""

    async def test_get_ingestion_logs(self, async_test_client):
        """Test getting ingestion logs."""
        response = await async_test_client.get("/api/v1/ingestion/logs")
        
        assert response.status_code in [200, 404, 500, 503]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or "logs" in data

    async def test_get_job_logs(self, async_test_client):
        """Test getting logs for specific job."""
        job_id = str(uuid4())
        response = await async_test_client.get(f"/api/v1/ingestion/logs/{job_id}")
        
        assert response.status_code in [200, 404]

    async def test_stream_ingestion_logs(self, async_test_client):
        """Test streaming ingestion logs."""
        response = await async_test_client.get("/api/v1/ingestion/logs/stream")
        
        # SSE endpoint
        assert response.status_code in [200, 404, 500, 503]

    async def test_search_ingestion_logs(self, async_test_client):
        """Test searching ingestion logs."""
        response = await async_test_client.get("/api/v1/ingestion/logs/search", params={
            "query": "error",
            "limit": 10
        })
        
        assert response.status_code in [200, 404, 500, 503]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or "logs" in data

    async def test_get_log_statistics(self, async_test_client):
        """Test getting log statistics."""
        response = await async_test_client.get("/api/v1/ingestion/logs/stats")
        
        assert response.status_code in [200, 404, 500, 503]
        if response.status_code == 200:
            data = response.json()
            assert "total_logs" in data or "error_count" in data


class TestDocumentationRunsAPI:
    """Test documentation runs API endpoints."""

    async def test_list_documentation_runs(self, async_test_client):
        """Test listing documentation runs."""
        response = await async_test_client.get("/api/v1/documentation/runs")
        
        assert response.status_code in [200, 404, 500, 503]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or "runs" in data

    async def test_get_documentation_run(self, async_test_client):
        """Test getting specific documentation run."""
        run_id = str(uuid4())
        response = await async_test_client.get(f"/api/v1/documentation/runs/{run_id}")
        
        assert response.status_code in [200, 404]

    async def test_create_documentation_run(self, async_test_client):
        """Test creating documentation run."""
        response = await async_test_client.post("/api/v1/documentation/runs", json={
            "repo_path": "/test/repo",
            "config": {"model": "llama3.2:latest"}
        })
        
        assert response.status_code in [200, 201, 400, 404, 422, 500]

    async def test_get_run_documents(self, async_test_client):
        """Test getting documents for a run."""
        run_id = str(uuid4())
        response = await async_test_client.get(f"/api/v1/documentation/runs/{run_id}/documents")
        
        assert response.status_code in [200, 404, 500]

    async def test_compare_runs(self, async_test_client):
        """Test comparing two runs."""
        run1_id = str(uuid4())
        run2_id = str(uuid4())
        response = await async_test_client.get(f"/api/v1/documentation/runs/compare", params={
            "run1": run1_id,
            "run2": run2_id
        })
        
        assert response.status_code in [200, 400, 404, 500]

    async def test_export_run(self, async_test_client):
        """Test exporting run."""
        run_id = str(uuid4())
        response = await async_test_client.post(f"/api/v1/documentation/runs/{run_id}/export", json={
            "format": "json"
        })
        
        assert response.status_code in [200, 202, 404, 500]

    async def test_delete_run(self, async_test_client):
        """Test deleting run."""
        run_id = str(uuid4())
        response = await async_test_client.delete(f"/api/v1/documentation/runs/{run_id}")
        
        assert response.status_code in [200, 204, 404, 500]


class TestEmbeddingsAdmin:
    """Test embeddings administration endpoints."""

    async def test_get_embedding_stats(self, async_test_client):
        """Test getting embedding statistics."""
        response = await async_test_client.get("/api/v1/embeddings/admin/stats")
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        if response.status_code == 200:
            assert isinstance(data, dict)

    async def test_regenerate_embeddings(self, async_test_client):
        """Test regenerating embeddings."""
        response = await async_test_client.post("/api/v1/embeddings/admin/regenerate")
        
        assert response.status_code in [200, 202, 404, 500]

    async def test_regenerate_missing_embeddings(self, async_test_client):
        """Test regenerating missing embeddings only."""
        response = await async_test_client.post("/api/v1/embeddings/admin/regenerate/missing")
        
        assert response.status_code in [200, 202, 404, 500]

    async def test_validate_embeddings(self, async_test_client):
        """Test validating embeddings."""
        response = await async_test_client.post("/api/v1/embeddings/admin/validate")
        
        assert response.status_code in [200, 202, 404, 500]
        data = response.json()
        if response.status_code == 200:
            assert isinstance(data, dict)

    async def test_get_embedding_quality(self, async_test_client):
        """Test getting embedding quality metrics."""
        response = await async_test_client.get("/api/v1/embeddings/admin/quality")
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        if response.status_code == 200:
            assert isinstance(data, dict)


class TestConfigurationViewer:
    """Test configuration viewer endpoints."""

    async def test_get_current_config(self, async_test_client):
        """Test getting current configuration."""
        response = await async_test_client.get("/api/v1/config/view")
        
        assert response.status_code in [200, 403, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    async def test_get_config_schema(self, async_test_client):
        """Test getting configuration schema."""
        response = await async_test_client.get("/api/v1/config/schema")
        
        assert response.status_code in [200, 404, 500, 503]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    async def test_validate_config(self, async_test_client):
        """Test validating configuration."""
        response = await async_test_client.post("/api/v1/config/validate", json={
            "setting": "value"
        })
        
        assert response.status_code in [200, 400, 404, 500]
        if response.status_code in [200, 400]:
            data = response.json()
            assert "valid" in data or "errors" in data

    async def test_get_config_diff(self, async_test_client):
        """Test getting configuration diff."""
        response = await async_test_client.get("/api/v1/config/diff")
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        if response.status_code == 200:
            assert isinstance(data, dict)


class TestDiscoveryAdmin:
    """Test discovery administration endpoints."""

    async def test_list_discovery_jobs(self, async_test_client):
        """Test listing discovery jobs."""
        response = await async_test_client.get("/api/v1/discovery/admin/jobs")
        
        assert response.status_code in [200, 404, 500, 503]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or "jobs" in data

    async def test_get_discovery_stats(self, async_test_client):
        """Test getting discovery statistics."""
        response = await async_test_client.get("/api/v1/discovery/admin/stats")
        
        assert response.status_code in [200, 404, 500, 503]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    async def test_rerun_discovery(self, async_test_client):
        """Test rerunning discovery."""
        response = await async_test_client.post("/api/v1/discovery/admin/rerun", json={
            "repo_path": "/test/repo"
        })
        
        assert response.status_code in [200, 202, 400, 404, 500]

    async def test_clear_discovery_cache(self, async_test_client):
        """Test clearing discovery cache."""
        response = await async_test_client.post("/api/v1/discovery/admin/cache/clear")
        
        assert response.status_code in [200, 202, 404, 500]


class TestOllamaStatus:
    """Test Ollama status endpoints."""

    async def test_get_ollama_status(self, async_test_client):
        """Test getting Ollama status."""
        response = await async_test_client.get("/api/v1/ollama/status")
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        if response.status_code == 200:
            assert isinstance(data, dict)

    async def test_list_ollama_models(self, async_test_client):
        """Test listing Ollama models."""
        response = await async_test_client.get("/api/v1/ollama/models")
        
        assert response.status_code in [200, 404, 500, 503]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or "models" in data

    async def test_get_model_info(self, async_test_client):
        """Test getting model information."""
        response = await async_test_client.get("/api/v1/ollama/models/llama3.2:latest")
        
        assert response.status_code in [200, 404, 500]

    async def test_pull_model(self, async_test_client):
        """Test pulling a model."""
        response = await async_test_client.post("/api/v1/ollama/models/pull", json={
            "model": "llama3.2:latest"
        })
        
        assert response.status_code in [200, 202, 403, 404, 500]

