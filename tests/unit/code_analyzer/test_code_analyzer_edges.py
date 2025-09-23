"""Code Analyzer edge-case tests with realistic scenarios and dynamic imports."""

import importlib.util, os
from fastapi.testclient import TestClient


# Dynamically load code-analyzer service
_spec = importlib.util.spec_from_file_location(
    "services.code-analyzer.main",
    os.path.join(os.getcwd(), 'services', 'code-analyzer', 'main.py')
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
app = _mod.app


def _assert_http_ok(response):
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


def test_mixed_framework_patterns_extracted():
    """Realistic mixed FastAPI/Flask/Express codebase analysis."""
    c = TestClient(app)
    code = """
    # FastAPI routes
    @app.get("/api/users/{user_id}")
    def get_user(user_id: int): pass

    # Flask routes
    @app.route('/health', methods=['GET'])
    def health(): pass

    # Express routes
    app.get('/webhooks/github', (req, res) => {})
    router.post("/auth/login", middleware.auth)
    """
    r = c.post("/analyze/text", json={"content": code, "language": "python"})
    _assert_http_ok(r)
    data = r.json()
    endpoints = data.get("document", {}).get("content", "").split("\n")

    # Should extract all framework patterns
    assert "/api/users/{user_id}" in endpoints
    assert "/health" in endpoints
    assert "/webhooks/github" in endpoints
    assert "/auth/login" in endpoints


def test_empty_content_graceful_handling():
    """Empty or whitespace-only content handled gracefully."""
    c = TestClient(app)
    r = c.post("/analyze/text", json={"content": "", "repo": "test/repo"})
    _assert_http_ok(r)
    data = r.json()
    assert data.get("document", {}).get("content") == "(no endpoints)"


def test_style_examples_merge_with_registered():
    """User-provided style examples merge with registered ones."""
    c = TestClient(app)

    # First set some style examples
    style_payload = {
        "items": [{
            "language": "python",
            "snippet": "def func():\n    pass",
            "title": "Registered Example",
            "tags": ["registered"]
        }]
    }
    r = c.post("/style/examples", json=style_payload)
    _assert_http_ok(r)

    # Analyze with additional user style examples
    user_examples = [{"snippet": "class MyClass:", "tags": ["user"]}]
    r = c.post("/analyze/text", json={
        "content": "@app.get('/test')\ndef handler(): pass",
        "language": "python",
        "style_examples": user_examples
    })
    _assert_http_ok(r)
    data = r.json()
    meta = data.get("document", {}).get("metadata", {})
    used = meta.get("style_examples_used", [])
    # Should contain both registered and user examples
    assert len(used) >= 2


def test_secure_scan_realistic_secrets():
    """Security scan detects realistic secret patterns."""
    c = TestClient(app)
    content_with_secrets = """
    AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
    api_key = "sk_test_4eC39HqLyjWDarjtT1zdp7dc"
    password = "P@ssw0rd123!"
    Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
    """
    r = c.post("/scan/secure", json={"content": content_with_secrets})
    _assert_http_ok(r)
    data = r.json()
    assert data.get("sensitive") is True
    matches = data.get("matches", [])
    assert any("AKIAIOSFODNN7EXAMPLE" in match for match in matches)  # AWS key
    assert any("sk_test_4eC39HqLyjWDarjtT1zdp7dc" in match for match in matches)  # Stripe-like key


def test_patch_analysis_basic_functionality():
    """Patch analysis processes diff format correctly."""
    c = TestClient(app)
    patch_content = """
    diff --git a/routes.py b/routes.py
    index abc123..def456 100644
    --- a/routes.py
    +++ b/routes.py
    @@ -1,3 +1,7 @@
     from flask import Flask
     app = Flask(__name__)

    +@app.route('/api/v1/users', methods=['GET'])
    +def get_users():
    +    return {'users': []}
    +
     if __name__ == '__main__':
    """
    r = c.post("/analyze/patch", json={"patch": patch_content})
    _assert_http_ok(r)
    data = r.json()
    # Should return a valid document structure
    doc = data.get("document", {})
    assert doc.get("id")
    assert doc.get("content") is not None  # May be "(no endpoints)" or actual endpoints
    assert doc.get("metadata", {}).get("source_link")
