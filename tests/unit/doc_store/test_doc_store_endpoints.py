"""Doc Store endpoint coverage for info/config/metrics and enveloped document creation."""

import importlib.util, os
from fastapi.testclient import TestClient
from services.shared.envelopes import DocumentEnvelope


# Load doc-store app via dynamic import
_spec = importlib.util.spec_from_file_location(
    "services.doc-store.main",
    os.path.join(os.getcwd(), 'services', 'doc-store', 'main.py')
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
app = _mod.app


def _assert_http_ok(response):
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


def test_info_config_metrics_endpoints():
    c = TestClient(app)

    r = c.get("/info")
    _assert_http_ok(r)
    data = r.json()
    assert data.get("success") is True
    assert data.get("data", {}).get("service") == "doc-store"

    r = c.get("/config/effective")
    _assert_http_ok(r)
    data = r.json()
    assert data.get("success") is True
    cfg = data.get("data", {})
    assert "db_path" in cfg

    r = c.get("/metrics")
    _assert_http_ok(r)
    data = r.json()
    assert data.get("success") is True
    m = data.get("data", {})
    assert isinstance(m.get("routes"), int)


def test_documents_enveloped_creation_and_fetch():
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

    r = c.post("/documents/enveloped", json=env.model_dump(mode="json"))
    _assert_http_ok(r)
    body = r.json()
    assert body.get("success") is True
    doc_id = body.get("data", {}).get("id")
    assert doc_id

    # Fetch the created document
    r = c.get(f"/documents/{doc_id}")
    _assert_http_ok(r)
    fetched = r.json().get("data", {})
    assert fetched.get("id") == doc_id
    assert fetched.get("metadata", {}).get("type") == "readme"


