"""Test suite for Secure Analyzer unit tests with mocked dependencies.

This module contains unit tests for the Secure Analyzer service, covering:
- Security policy enforcement
- Content analysis and filtering
- Integration with external summarization services

Test Categories:
- Unit tests with mocked dependencies
- Isolated function testing
- Edge case validation

Dependencies:
- pytest testing framework
- FastAPI test client
- Mocking utilities
- Service layer components
"""

import pytest
from starlette.testclient import TestClient

import importlib.util, os
_spec_sa = importlib.util.spec_from_file_location(
    "services.secure-analyzer.main",
    os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'secure-analyzer', 'main.py')
)
_mod_sa = importlib.util.module_from_spec(_spec_sa)
_spec_sa.loader.exec_module(_mod_sa)
sa = _mod_sa.app


@pytest.mark.security
@pytest.mark.mocks
def test_secure_analyzer_summarize_uses_policy_and_calls_hub(monkeypatch):
    """Test secure analyzer summarization with policy enforcement.

    Validates that the secure analyzer correctly applies security policies
    and calls the summarization hub when content is deemed safe.

    Args:
        monkeypatch: pytest fixture for mocking dependencies

    Returns:
        None

    Raises:
        AssertionError: If policy enforcement or hub calling fails
    """
    client = TestClient(sa)

    async def _fake_post_json(self, url, payload, headers=None):  # type: ignore
        # summarizer-hub ensemble returns normalized content
        assert url.endswith("/summarize/ensemble")
        return {"summaries": {"bedrock": "ok"}, "analysis": {"agreed": ["policy ok"]}}

    from services.shared.clients import ServiceClients  # type: ignore
    monkeypatch.setattr(ServiceClients, "post_json", _fake_post_json)

    resp = client.post(
        "/summarize",
        json={
            "content": "Contains API key and client password",
            "providers": [{"name": "openai"}, {"name": "ollama"}],
            "override_policy": False,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    # Ensure hub was invoked and returned analysis payload
    assert "analysis" in body
    assert body.get("analysis", {}).get("agreed") == ["policy ok"]


