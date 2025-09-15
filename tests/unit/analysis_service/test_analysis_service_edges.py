"""Analysis Service edge-case tests with realistic scenarios and dynamic imports."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from .test_utils import load_analysis_service, _assert_http_ok


@pytest.fixture(scope="module")
def client():
    """Test client fixture for analysis service."""
    app = load_analysis_service()
    from fastapi.testclient import TestClient
    return TestClient(app)




def test_analyze_empty_targets_graceful_handling(client):
    """Analysis handles empty targets gracefully."""
    # Client fixture used
    response = client.post("/analyze", json={"targets": [], "analysis_type": "consistency"})
    # Real service validates empty targets
    assert response.status_code == 422
    data = response.json()
    # Pydantic validation error format
    assert "detail" in data or "error" in data


def test_findings_endpoint_structure(client):
    """Findings endpoint returns proper structure."""
    # Client fixture used
    response = client.get("/findings", params={"severity": "high"})
    _assert_http_ok(response)
    data = response.json()
    # Should return proper structure
    assert "findings" in data
    assert "count" in data
    assert "severity_counts" in data


def test_analysis_type_validation(client):
    """Analysis endpoint handles valid analysis_type."""
    # Client fixture used
    response = client.post("/analyze", json={"targets": ["doc1"], "analysis_type": "consistency"})
    # Should accept valid analysis type
    _assert_http_ok(response)
    data = response.json()
    # Should return analysis results structure
    assert "findings" in data
    assert "severity_counts" in data


def test_confluence_consolidation_report(client):
    """Confluence consolidation report endpoint works correctly."""
    # Client fixture used
    response = client.get("/reports/confluence/consolidation")
    _assert_http_ok(response)
    data = response.json()
    # Should return report structure
    assert "items" in data
    assert "summary" in data
    assert "total" in data
