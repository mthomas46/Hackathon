"""GitHub MCP Service core tests."""

import pytest
import importlib.util, os
from fastapi.testclient import TestClient

from .test_utils import load_github_mcp_service, _assert_http_ok


@pytest.fixture(scope="module")
def client():
    """Test client fixture for github mcp service."""
    app = load_github_mcp_service()
    from fastapi.testclient import TestClient
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    j = r.json()
    assert j.get("status") == "healthy"


def test_info(client, monkeypatch):
    monkeypatch.setenv("GITHUB_TOOLSETS", "repos,issues")
    monkeypatch.setenv("GITHUB_DYNAMIC_TOOLSETS", "1")
    monkeypatch.setenv("GITHUB_READ_ONLY", "1")
    monkeypatch.setenv("GITHUB_PERSONAL_ACCESS_TOKEN", "x")
    monkeypatch.setenv("GITHUB_HOST", "https://ghe.example.org")
    r = client.get("/info")
    assert r.status_code == 200
    j = r.json()
    assert j.get("service") == "github-mcp"
    assert set(j.get("toolsets", [])) == {"repos", "issues"}
    assert j.get("dynamic_toolsets") is True
    assert j.get("read_only") is True
    assert j.get("token_present") is True
    assert j.get("github_host") == "https://ghe.example.org"


def test_list_tools_env_toolsets(client, monkeypatch):
    monkeypatch.setenv("GITHUB_TOOLSETS", "repos,pull_requests")
    r = client.get("/tools")
    assert r.status_code == 200
    names = [t["name"] for t in r.json()]
    # Should include repos and prs tools, exclude issues/users/actions/security
    assert "github.search_repos" in names
    assert "github.get_pr_diff" in names
    assert "github.search_issues" not in names
    assert "github.search_users" not in names


def test_list_tools_dynamic_query_param(client, monkeypatch):
    monkeypatch.delenv("GITHUB_TOOLSETS", raising=False)
    monkeypatch.setenv("GITHUB_DYNAMIC_TOOLSETS", "1")
    r = client.get("/tools?toolsets=issues,users")
    assert r.status_code == 200
    names = [t["name"] for t in r.json()]
    assert "github.search_issues" in names
    assert "github.search_users" in names
    assert "github.search_repos" not in names


def test_invoke_mock_search(client, monkeypatch):
    monkeypatch.setenv("GITHUB_MOCK", "1")
    r = client.post("/tools/github.search_repos/invoke", json={"arguments": {"q": "hackathon", "limit": 2}})
    assert r.status_code == 200
    j = r.json()
    assert j.get("success") is True
    assert len(j.get("result", {}).get("items", [])) == 2


def test_invoke_mock_get_repo(client, monkeypatch):
    monkeypatch.setenv("GITHUB_MOCK", "1")
    r = client.post("/tools/github.get_repo/invoke", json={"arguments": {"owner": "org", "repo": "proj"}})
    assert r.status_code == 200
    j = r.json()
    assert j.get("result", {}).get("full_name") == "org/proj"


def test_read_only_blocks_write(client, monkeypatch):
    monkeypatch.setenv("GITHUB_READ_ONLY", "1")
    r = client.post("/tools/github.search_repos/invoke", json={"arguments": {"q": "x"}, "write": True})
    assert r.status_code == 403


def test_write_tools_allowed_when_not_read_only(client, monkeypatch):
    monkeypatch.delenv("GITHUB_READ_ONLY", raising=False)
    monkeypatch.setenv("GITHUB_MOCK", "1")
    # create issue
    r1 = client.post("/tools/github.create_issue/invoke", json={"arguments": {"owner": "o", "repo": "r", "title": "Bug"}, "write": True})
    assert r1.status_code == 200
    # add comment
    r2 = client.post("/tools/github.add_issue_comment/invoke", json={"arguments": {"owner": "o", "repo": "r", "issue_number": 1, "comment": "hi"}, "write": True})
    assert r2.status_code == 200
