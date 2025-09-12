"""Doc Store edge-case tests with realistic data and dynamic imports."""

import importlib.util, os, json
import pytest
from fastapi.testclient import TestClient


# Dynamically load doc-store service from hyphenated path
_spec = importlib.util.spec_from_file_location(
    "services.doc-store.main",
    os.path.join(os.getcwd(), 'services', 'doc-store', 'main.py')
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)  # type: ignore
app = _mod.app


def _assert_http_ok(response):
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


def test_create_with_invalid_metadata_sets_defaults_and_content_length():
    c = TestClient(app)
    payload = {
        "content": "API Overview\n\nThis API supports CRUD operations.",
        "metadata": "not-a-dict"
    }
    r = c.post("/documents", json=payload)
    _assert_http_ok(r)
    data = r.json()["data"]
    assert "id" in data and data["id"]

    # Fetch the document and verify metadata normalized and enriched
    r = c.get(f"/documents/{data['id']}")
    _assert_http_ok(r)
    doc = r.json()["data"]
    assert isinstance(doc.get("metadata"), dict)
    # content_length is added by server logic
    assert doc["metadata"].get("content_length") == len(payload["content"])  # realistic derived field


def test_get_nonexistent_document_returns_error_response():
    c = TestClient(app)
    r = c.get("/documents/does:not:exist")
    _assert_http_ok(r)
    body = r.json()
    # Standardized error envelope
    assert body.get("success") is False
    assert body.get("error_code") in ("DOCUMENT_NOT_FOUND", "DATABASE_ERROR", "document_not_found", "database_error")


def test_analyses_validation_requires_document_id_or_content():
    c = TestClient(app)
    r = c.post("/analyses", json={"result": {"score": 0.9}})
    _assert_http_ok(r)
    body = r.json()
    assert body.get("success") is False
    assert body.get("error_code") in ("VALIDATION_ERROR", "validation_error")


def test_analyses_with_content_creates_doc_and_analysis_and_lists():
    c = TestClient(app)
    # Provide only content; service should create a document implicitly
    analysis_payload = {
        "content": "POST /users creates a user",
        "analyzer": "unit-test-analyzer",
        "model": "gpt-test",
        "prompt": "analyze this",
        "result": {"score": 0.8, "findings": ["ok"]},
        "score": 0.8,
        "metadata": {"origin": "unit-test"}
    }
    r = c.post("/analyses", json=analysis_payload)
    _assert_http_ok(r)
    body = r.json()
    assert body.get("success") is True
    data = body.get("data", {})
    assert data.get("id") and data.get("document_id")

    # List analyses filtered by document
    r = c.get("/analyses", params={"document_id": data["document_id"]})
    _assert_http_ok(r)
    listed = r.json()["data"]["items"]
    assert any(item.get("id") == data["id"] for item in listed)


def test_search_semantic_fallback_and_results_format():
    c = TestClient(app)
    # Create a couple of docs
    docs = [
        {"content": "Authentication guide: Use JWT tokens", "metadata": {"title": "Auth"}},
        {"content": "Users API: GET /users, POST /users", "metadata": {"title": "Users API", "tags": ["api", "users"]}},
    ]
    for d in docs:
        _assert_http_ok(c.post("/documents", json=d))

    # Query that likely triggers either FTS or fallback
    r = c.get("/search", params={"q": "users", "limit": 10})
    _assert_http_ok(r)
    items = r.json()["data"]["items"]
    # Ensure realistic structure of returned items
    assert isinstance(items, list)
    assert all("id" in it and "content_hash" in it for it in items)


def test_patch_metadata_merges_updates_and_persists():
    c = TestClient(app)
    # Create a document with some metadata
    r = c.post("/documents", json={"content": "Observability setup", "metadata": {"owner": "platform"}})
    _assert_http_ok(r)
    doc_id = r.json()["data"]["id"]

    # Patch metadata (note: this endpoint returns raw dict, not envelope)
    patch = {"updates": {"owner": "platform-team", "views": 5}}
    r = c.patch(f"/documents/{doc_id}/metadata", json=patch)
    _assert_http_ok(r)
    assert r.json()["metadata"]["owner"] == "platform-team"
    assert r.json()["metadata"]["views"] == 5

    # Fetch and verify persisted
    r = c.get(f"/documents/{doc_id}")
    _assert_http_ok(r)
    meta = r.json()["data"]["metadata"]
    assert meta.get("owner") == "platform-team"
    assert meta.get("views") == 5


