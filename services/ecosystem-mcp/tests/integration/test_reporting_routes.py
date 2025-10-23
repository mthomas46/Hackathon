"""
Integration tests for reporting and metrics API routes.

Tests report generation, metrics collection, and performance optimization endpoints.
"""

import pytest
import httpx
from datetime import datetime
from uuid import uuid4


pytestmark = pytest.mark.integration


@pytest.fixture
async def http_client():
    """HTTP client for API testing."""
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=30.0) as client:
        yield client


class TestReportGeneration:
    """Test report generation endpoints."""

    async def test_generate_system_report(self, http_client):
        """Test generating system report."""
        response = await http_client.post("/api/v1/reports/generate/system")
        
        assert response.status_code in [200, 202]
        data = response.json()
        assert "report_id" in data or "status" in data

    async def test_generate_ingestion_report(self, http_client):
        """Test generating ingestion report."""
        response = await http_client.post("/api/v1/reports/generate/ingestion", json={
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        })
        
        assert response.status_code in [200, 202]

    async def test_generate_performance_report(self, http_client):
        """Test generating performance report."""
        response = await http_client.post("/api/v1/reports/generate/performance")
        
        assert response.status_code in [200, 202]

    async def test_generate_quality_report(self, http_client):
        """Test generating quality report."""
        response = await http_client.post("/api/v1/reports/generate/quality")
        
        assert response.status_code in [200, 202]

    async def test_list_reports(self, http_client):
        """Test listing reports."""
        response = await http_client.get("/api/v1/reports")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "reports" in data

    async def test_get_report(self, http_client):
        """Test getting specific report."""
        report_id = str(uuid4())
        response = await http_client.get(f"/api/v1/reports/{report_id}")
        
        assert response.status_code in [200, 404]

    async def test_download_report(self, http_client):
        """Test downloading report."""
        report_id = str(uuid4())
        response = await http_client.get(f"/api/v1/reports/{report_id}/download")
        
        assert response.status_code in [200, 404]

    async def test_delete_report(self, http_client):
        """Test deleting report."""
        report_id = str(uuid4())
        response = await http_client.delete(f"/api/v1/reports/{report_id}")
        
        assert response.status_code in [200, 204, 404]


class TestMetricsCollection:
    """Test metrics collection endpoints."""

    async def test_get_all_metrics(self, http_client):
        """Test getting all metrics."""
        response = await http_client.get("/api/v1/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    async def test_get_system_metrics(self, http_client):
        """Test getting system metrics."""
        response = await http_client.get("/api/v1/metrics/system")
        
        assert response.status_code == 200
        data = response.json()
        assert "cpu" in data or "memory" in data

    async def test_get_application_metrics(self, http_client):
        """Test getting application metrics."""
        response = await http_client.get("/api/v1/metrics/application")
        
        assert response.status_code == 200
        data = response.json()
        assert "requests" in data or "response_time" in data

    async def test_get_database_metrics(self, http_client):
        """Test getting database metrics."""
        response = await http_client.get("/api/v1/metrics/database")
        
        assert response.status_code == 200
        data = response.json()
        assert "connections" in data or "queries" in data

    async def test_export_metrics(self, http_client):
        """Test exporting metrics."""
        response = await http_client.get("/api/v1/metrics/export", params={
            "format": "prometheus"
        })
        
        assert response.status_code == 200


class TestPerformanceOptimization:
    """Test performance optimization endpoints."""

    async def test_get_optimization_recommendations(self, http_client):
        """Test getting optimization recommendations."""
        response = await http_client.get("/api/v1/performance/recommendations")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "recommendations" in data

    async def test_analyze_bottlenecks(self, http_client):
        """Test analyzing bottlenecks."""
        response = await http_client.post("/api/v1/performance/analyze/bottlenecks")
        
        assert response.status_code in [200, 202]
        data = response.json()
        assert "bottlenecks" in data or "analysis_id" in data

    async def test_optimize_queries(self, http_client):
        """Test query optimization."""
        response = await http_client.post("/api/v1/performance/optimize/queries")
        
        assert response.status_code in [200, 202]

    async def test_optimize_cache(self, http_client):
        """Test cache optimization."""
        response = await http_client.post("/api/v1/performance/optimize/cache")
        
        assert response.status_code in [200, 202]

    async def test_get_performance_baseline(self, http_client):
        """Test getting performance baseline."""
        response = await http_client.get("/api/v1/performance/baseline")
        
        assert response.status_code == 200
        data = response.json()
        assert "baseline" in data or "metrics" in data


class TestTemporalVersioningAPI:
    """Test temporal versioning API endpoints."""

    async def test_get_document_versions(self, http_client):
        """Test getting document versions."""
        doc_id = str(uuid4())
        response = await http_client.get(f"/api/v1/versioning/documents/{doc_id}/versions")
        
        assert response.status_code in [200, 404]

    async def test_get_version_by_hash(self, http_client):
        """Test getting version by content hash."""
        content_hash = "abc123"
        response = await http_client.get(f"/api/v1/versioning/hash/{content_hash}")
        
        assert response.status_code in [200, 404]

    async def test_compare_versions(self, http_client):
        """Test comparing versions."""
        v1_id = str(uuid4())
        v2_id = str(uuid4())
        response = await http_client.get(f"/api/v1/versioning/compare", params={
            "version1": v1_id,
            "version2": v2_id
        })
        
        assert response.status_code in [200, 404]

    async def test_get_version_timeline(self, http_client):
        """Test getting version timeline."""
        file_path = "test.md"
        response = await http_client.get(f"/api/v1/versioning/timeline", params={
            "file_path": file_path
        })
        
        assert response.status_code in [200, 404]

    async def test_cleanup_old_versions(self, http_client):
        """Test cleaning up old versions."""
        response = await http_client.post("/api/v1/versioning/cleanup", json={
            "days": 90
        })
        
        assert response.status_code in [200, 202]


class TestPathResolver:
    """Test path resolver endpoints."""

    async def test_resolve_path(self, http_client):
        """Test resolving path."""
        response = await http_client.post("/api/v1/path/resolve", json={
            "path": "/test/repo"
        })
        
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            assert "resolved_path" in data or "absolute_path" in data

    async def test_validate_path(self, http_client):
        """Test validating path."""
        response = await http_client.post("/api/v1/path/validate", json={
            "path": "/test/repo"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data

    async def test_get_path_info(self, http_client):
        """Test getting path information."""
        response = await http_client.post("/api/v1/path/info", json={
            "path": "/test/repo"
        })
        
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "exists" in data or "type" in data

    async def test_find_git_root(self, http_client):
        """Test finding git root."""
        response = await http_client.post("/api/v1/path/git-root", json={
            "path": "/test/repo/subdir"
        })
        
        assert response.status_code in [200, 404]


class TestConsolidationAPI:
    """Test document consolidation API endpoints."""

    async def test_detect_duplicates(self, http_client):
        """Test detecting duplicate documents."""
        response = await http_client.post("/api/v1/consolidation/detect-duplicates")
        
        assert response.status_code in [200, 202]
        data = response.json()
        assert "duplicates" in data or "analysis_id" in data

    async def test_find_similar_documents(self, http_client):
        """Test finding similar documents."""
        response = await http_client.post("/api/v1/consolidation/find-similar", json={
            "threshold": 0.8
        })
        
        assert response.status_code in [200, 202]

    async def test_get_merge_recommendations(self, http_client):
        """Test getting merge recommendations."""
        response = await http_client.get("/api/v1/consolidation/recommendations")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "recommendations" in data

    async def test_merge_documents(self, http_client):
        """Test merging documents."""
        response = await http_client.post("/api/v1/consolidation/merge", json={
            "document_ids": [str(uuid4()), str(uuid4())]
        })
        
        assert response.status_code in [200, 400, 404]

    async def test_consolidate_service(self, http_client):
        """Test consolidating service documents."""
        response = await http_client.post("/api/v1/consolidation/service", json={
            "service_name": "test-service"
        })
        
        assert response.status_code in [200, 202, 404]


class TestLogsViewer:
    """Test logs viewer endpoints."""

    async def test_get_logs(self, http_client):
        """Test getting logs."""
        response = await http_client.get("/api/v1/logs")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "logs" in data

    async def test_get_logs_by_level(self, http_client):
        """Test getting logs by level."""
        response = await http_client.get("/api/v1/logs/level/error")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "logs" in data

    async def test_search_logs(self, http_client):
        """Test searching logs."""
        response = await http_client.get("/api/v1/logs/search", params={
            "query": "error",
            "limit": 10
        })
        
        assert response.status_code == 200

    async def test_stream_logs(self, http_client):
        """Test streaming logs."""
        response = await http_client.get("/api/v1/logs/stream")
        
        # SSE endpoint
        assert response.status_code == 200

    async def test_export_logs(self, http_client):
        """Test exporting logs."""
        response = await http_client.post("/api/v1/logs/export", json={
            "format": "json",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        })
        
        assert response.status_code in [200, 202]

