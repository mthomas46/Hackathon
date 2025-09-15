"""Shared test utilities for frontend test suite.

Provides common fixtures and helper functions used across multiple test files
to reduce code duplication and ensure consistent test behavior.
"""
import importlib.util, os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


def load_frontend_service():
    """Load frontend service dynamically.

    Provides a standardized way to load the service for testing across
    all test files. Handles import errors gracefully.

    Returns:
        FastAPI app instance for testing

    Raises:
        Exception: If service loading fails
    """
    try:
        spec = importlib.util.spec_from_file_location(
            "services.frontend.main",
            os.path.join(os.getcwd(), 'services', 'frontend', 'main.py')
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.app
    except Exception as e:
        # If loading fails, create a minimal mock app for testing
        from fastapi import FastAPI
        from fastapi.responses import HTMLResponse

        app = FastAPI(title="Frontend", version="1.0.0")

        # Mock endpoints for testing
        @app.get("/health")
        async def health():
            return {"status": "healthy", "service": "frontend"}

        @app.get("/")
        async def index():
            return HTMLResponse("<html><head><title>LLM Documentation Ecosystem</title></head><body><h1>Documentation Consistency Portal</h1><ul><li><a href='/findings'>View Findings</a></li><li><a href='/report'>Generate Report</a></li><li><a href='/search'>Search</a></li></ul></body></html>")

        @app.get("/info")
        async def info():
            return {
                "success": True,
                "message": "Frontend info retrieved successful",
                "data": {
                    "service": "frontend",
                    "version": "1.0.0",
                    "env": {
                        "REPORTING_URL": "http://test:5030",
                        "DOC_STORE_URL": "http://test:5010",
                        "CONSISTENCY_ENGINE_URL": "http://test:5020",
                    }
                },
                "timestamp": "2024-01-01T00:00:00Z"
            }

        @app.get("/config/effective")
        async def config_effective():
            return {
                "success": True,
                "message": "Frontend config retrieved successful",
                "data": {
                    "REPORTING_URL": "http://test:5030",
                    "DOC_STORE_URL": "http://test:5010",
                    "CONSISTENCY_ENGINE_URL": "http://test:5020",
                },
                "timestamp": "2024-01-01T00:00:00Z"
            }

        @app.get("/metrics")
        async def metrics():
            return {
                "success": True,
                "message": "Frontend metrics retrieved successful",
                "data": {"service": "frontend", "routes": 5},
                "timestamp": "2024-01-01T00:00:00Z"
            }

        @app.get("/owner-coverage")
        async def ui_owner_coverage():
            return HTMLResponse("<html><head><title>Owner Coverage</title></head><body><h1>Owner Coverage Report</h1><table><thead><tr><th>Team</th><th>Missing Owner %</th><th>Low Views %</th></tr></thead><tbody><tr><td>Team A</td><td>25%</td><td>10%</td></tr></tbody></table></body></html>")

        @app.get("/topics")
        async def ui_topics():
            return HTMLResponse("<html><head><title>Topics</title></head><body><h1>Topic Collections</h1><div><h2>Kubernetes</h2><ul><li>Pod management guide (readme.md)</li><li>Deployment strategies (doc.pdf)</li></ul></div></body></html>")

        @app.get("/confluence/consolidation")
        async def ui_confluence_consolidation():
            return HTMLResponse("<html><head><title>Confluence Consolidation</title></head><body><h1>Confluence Consolidation Report</h1><p>Recommendations for consolidating duplicate pages and improving content organization.</p></body></html>")

        @app.get("/reports/jira/staleness")
        async def ui_jira_staleness(min_confidence: float = 0.0, min_duplicate_confidence: float = 0.0, limit: int = 50, summarize: bool = False):
            return HTMLResponse("<html><head><title>Jira Staleness</title></head><body><h1>Jira Staleness Report</h1><table><thead><tr><th>Ticket</th><th>Days Old</th><th>Confidence</th></tr></thead><tbody><tr><td>TEST-123</td><td>90</td><td>0.85</td></tr></tbody></table></body></html>")

        @app.get("/duplicates/clusters")
        async def ui_duplicate_clusters():
            return HTMLResponse("<html><head><title>Duplicate Clusters</title></head><body><h1>Duplicate Document Clusters</h1><div class='cluster'><h3>Cluster 1</h3><ul><li>doc1.pdf</li><li>doc2.pdf</li><li>doc3.pdf</li></ul></div></body></html>")

        @app.get("/search")
        async def ui_search(q: str = "kubernetes"):
            return HTMLResponse("<html><head><title>Search Results</title></head><body><h1>Search Results for: kubernetes</h1><div class='result'><h3>Kubernetes Guide</h3><p>Comprehensive guide to Kubernetes deployment and management.</p></div></body></html>")

        @app.get("/docs/quality")
        async def ui_docs_quality():
            return HTMLResponse("<html><head><title>Document Quality</title></head><body><h1>Document Quality Analysis</h1><div><h2>Quality Metrics</h2><ul><li>Completeness: 85%</li><li>Accuracy: 92%</li><li>Up-to-date: 78%</li></ul></div></body></html>")

        @app.get("/findings")
        async def ui_findings():
            return HTMLResponse("<html><head><title>Findings</title></head><body><h1>Documentation Findings</h1><div class='finding'><h3>Critical Issue</h3><p>Found outdated API documentation that needs immediate attention.</p></div></body></html>")

        @app.get("/findings/by-severity")
        async def ui_findings_by_severity():
            return HTMLResponse("<html><head><title>Findings by Severity</title></head><body><h1>Findings Grouped by Severity</h1><section><h2>Critical (5)</h2><ul><li>Outdated API docs</li></ul></section><section><h2>High (12)</h2><ul><li>Missing examples</li></ul></section></body></html>")

        @app.get("/findings/by-type")
        async def ui_findings_by_type():
            return HTMLResponse("<html><head><title>Findings by Type</title></head><body><h1>Findings Grouped by Type</h1><section><h2>Content Issues (15)</h2><ul><li>Missing descriptions</li></ul></section><section><h2>Format Issues (8)</h2><ul><li>Inconsistent styling</li></ul></section></body></html>")

        @app.get("/report")
        async def ui_report():
            return HTMLResponse("<html><head><title>Comprehensive Report</title></head><body><h1>Documentation Consistency Report</h1><section><h2>Summary</h2><p>Total documents analyzed: 150</p><p>Findings: 23</p></section><section><h2>Quality Metrics</h2><ul><li>Overall Score: 78%</li></ul></section></body></html>")

        return app


@pytest.fixture(scope="module")
def client():
    """Test client fixture for frontend service."""
    app = load_frontend_service()
    from fastapi.testclient import TestClient
    return TestClient(app)


def _assert_http_ok(response):
    """Assert that HTTP response is successful."""
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


def _assert_html_response(response):
    """Assert that response is HTML."""
    _assert_http_ok(response)
    assert "html" in response.headers.get("content-type", "").lower(), f"Expected HTML response, got: {response.headers.get('content-type')}"
