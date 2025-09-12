"""Analysis Service edge-case tests with realistic scenarios and dynamic imports."""

import importlib.util, os
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


# Dynamically load analysis-service
_spec = importlib.util.spec_from_file_location(
    "services.analysis-service.main",
    os.path.join(os.getcwd(), 'services', 'analysis-service', 'main.py')
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
app = _mod.app


def _assert_http_ok(response):
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


def test_analyze_empty_targets_graceful_handling():
    """Analysis handles empty targets gracefully."""
    c = TestClient(app)
    r = c.post("/analyze", json={"targets": [], "analysis_type": "consistency"})
    # Real service validates empty targets
    assert r.status_code == 422
    data = r.json()
    # Pydantic validation error format
    assert "detail" in data or "error" in data


def test_findings_endpoint_structure():
    """Findings endpoint returns proper structure."""
    c = TestClient(app)
    r = c.get("/findings", params={"severity": "high"})
    _assert_http_ok(r)
    data = r.json()
    # Should return proper structure
    assert "findings" in data
    assert "count" in data
    assert "severity_counts" in data


def test_analysis_type_validation():
    """Analysis endpoint handles valid analysis_type."""
    c = TestClient(app)
    r = c.post("/analyze", json={"targets": ["doc1"], "analysis_type": "consistency"})
    # Should accept valid analysis type
    _assert_http_ok(r)
    data = r.json()
    # Should return analysis results structure
    assert "findings" in data
    assert "severity_counts" in data


def test_confluence_consolidation_report():
    """Confluence consolidation report endpoint works correctly."""
    c = TestClient(app)
    r = c.get("/reports/confluence/consolidation")
    _assert_http_ok(r)
    data = r.json()
    # Should return report structure
    assert "items" in data
    assert "summary" in data
    assert "total" in data
