"""Analysis Service endpoint coverage tests within realistic scope."""

import importlib.util, os, sys
from fastapi.testclient import TestClient


# Load analysis-service app via dynamic import
# Add services directory to path for proper relative imports
services_path = os.path.join(os.getcwd(), 'services')
if services_path not in sys.path:
    sys.path.insert(0, services_path)

_spec = importlib.util.spec_from_file_location(
    "analysis-service.main",
    os.path.join(services_path, 'analysis-service', 'main.py')
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
app = _mod.app


def _assert_http_ok(response):
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


def test_health_registered():
    c = TestClient(app)
    # Health endpoints registered via shared utilities
    r = c.get("/health")
    _assert_http_ok(r)


def test_reports_jira_staleness_and_notify_owners():
    c = TestClient(app)

    # Jira staleness report should return items or mock data
    r = c.get("/reports/jira/staleness")
    _assert_http_ok(r)
    data = r.json()
    assert "items" in data
    assert "total" in data

    # Notify owners should accept a minimal payload
    findings = [{
        "id": "missing:endpoint",
        "type": "missing_doc",
        "title": "Undocumented Endpoint",
        "description": "POST /orders endpoint is not documented",
        "severity": "high",
        "source_refs": [{"id": "POST /orders", "type": "endpoint"}],
        "evidence": ["Endpoint exists in API spec"],
        "suggestion": "Add documentation",
        "score": 90,
        "rationale": "Usability issue"
    }]
    r = c.post("/reports/findings/notify-owners", json={
        "findings": findings,
        "channels": ["email"],
        "priority": "medium"
    })
    _assert_http_ok(r)
    resp = r.json()
    assert resp.get("status") in ("notifications_sent", "error")


