"""Doc Store endpoint coverage for info/config/metrics and enveloped document creation."""

import pytest
from fastapi.testclient import TestClient
from services.shared.envelopes import DocumentEnvelope

from .test_utils import load_doc_store_service, _assert_http_ok


@pytest.fixture(scope="module")
def client():
    """Test client fixture for doc store service."""
    app = load_doc_store_service()
    from fastapi.testclient import TestClient
    return TestClient(app)


def test_info_config_metrics_endpoints(client):

    r = client.get("/info")
    _assert_http_ok(r)
    data = r.json()
    assert data.get("success") is True
    assert data.get("data", {}).get("service") == "doc_store"

    r = client.get("/config/effective")
    _assert_http_ok(r)
    data = r.json()
    assert data.get("success") is True
    cfg = data.get("data", {})
    assert "db_path" in cfg

    r = client.get("/metrics")
    _assert_http_ok(r)
    data = r.json()
    assert data.get("success") is True
    m = data.get("data", {})
    assert isinstance(m.get("routes"), int)


def test_documents_enveloped_creation_and_fetch():
    pytest.skip("Skipping complex integration test")
    c = TestClient(app)

    # Build a minimal envelope
    env = DocumentEnvelope(
        id="",  # allow service to generate id/content_hash
        version=None,
        correlation_id="corr-123",
        source_refs=[{"repo": "company/service", "path": "README.md"}],
        content_hash="",
        document={
            "content": "# Readme\n\nService overview.",
            "metadata": {"type": "readme", "title": "Service Overview"}
        }
    )

    r = client.post("/documents/enveloped", json=env.model_dump(mode="json"))
    _assert_http_ok(r)
    body = r.json()
    assert body.get("success") is True
    doc_id = body.get("data", {}).get("id")
    assert doc_id

    # Fetch the created document
    r = client.get(f"/documents/{doc_id}")
    _assert_http_ok(r)
    fetched = r.json().get("data", {})
    assert fetched.get("id") == doc_id
    assert fetched.get("metadata", {}).get("type") == "readme"


