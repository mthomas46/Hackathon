"""Code Analyzer endpoint coverage for /health, /analyze/files, and style examples get."""

import importlib.util, os
from fastapi.testclient import TestClient


# Load code-analyzer app via dynamic import
_spec = importlib.util.spec_from_file_location(
    "services.code-analyzer.main",
    os.path.join(os.getcwd(), 'services', 'code-analyzer', 'main.py')
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
app = _mod.app


def _assert_http_ok(response):
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


def test_health_endpoint():
    c = TestClient(app)
    r = c.get("/health")
    _assert_http_ok(r)
    body = r.json()
    assert body.get("status") == "healthy"
    assert body.get("service") == "code-analyzer"


def test_analyze_files_mixed_and_empty():
    c = TestClient(app)
    files = [
        {"path": "main.py", "content": "@app.get('/ping')\nasync def ping(): return 'ok'"},
        {"path": "routes.js", "content": "router.post('/login', handler)"},
    ]
    r = c.post("/analyze/files", json={"files": files, "language": "python"})
    _assert_http_ok(r)
    doc = r.json().get("document", {})
    assert "/ping" in doc.get("content", "")
    assert "/login" in doc.get("content", "")

    # Empty files list still returns a valid structure
    r = c.post("/analyze/files", json={"files": []})
    _assert_http_ok(r)
    doc = r.json().get("document", {})
    assert doc.get("content") == "(no endpoints)"


def test_style_examples_get_after_set():
    c = TestClient(app)
    # Ensure language registry has at least one entry
    r = c.post("/style/examples", json={"items": [{"language": "go", "snippet": "func main(){}"}]})
    _assert_http_ok(r)

    # Fetch all languages list
    r = c.get("/style/examples")
    _assert_http_ok(r)
    items = r.json().get("items", [])
    assert any(it.get("language") == "go" for it in items)

    # Fetch specific language
    r = c.get("/style/examples", params={"language": "go"})
    _assert_http_ok(r)
    items = r.json().get("items", [])
    assert any("snippet" in it for it in items)


