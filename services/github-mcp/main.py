"""Service: GitHub MCP (Model Context Protocol) local server

Endpoints:
- GET /health
- GET /info
- GET /tools
- POST /tools/{tool}/invoke

Responsibilities: Provide local MCP-like tools to interact with GitHub data and
proxy or synthesize outputs for other services in the ecosystem. Supports mock mode
for tests and local dev without external network calls.
"""
from typing import Dict, Any, List, Optional, Set
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from services.shared.middleware import RequestIdMiddleware, RequestMetricsMiddleware  # type: ignore
from services.shared.utilities import attach_self_register, setup_common_middleware  # type: ignore
from services.shared.constants_new import ServiceNames  # type: ignore

from services.shared.clients import ServiceClients  # type: ignore

SERVICE_TITLE = "GitHub MCP"
SERVICE_VERSION = "0.1.0"

app = FastAPI(title=SERVICE_TITLE, version=SERVICE_VERSION)
setup_common_middleware(app, ServiceNames.GITHUB if hasattr(ServiceNames, "GITHUB") else "github-mcp")
attach_self_register(app, ServiceNames.GITHUB if hasattr(ServiceNames, "GITHUB") else "github-mcp")


class ToolDescription(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]


class InvokeRequest(BaseModel):
    arguments: Dict[str, Any] = {}
    correlation_id: Optional[str] = None
    mock: Optional[bool] = None
    write: Optional[bool] = None


class InvokeResponse(BaseModel):
    tool: str
    success: bool
    result: Dict[str, Any]


# Tool catalog with coarse-grained toolset classification similar to github-mcp-server
# Reference: GitHub MCP Server toolsets (repos, issues, pull_requests, actions, code_security, users)
_TOOLSET_BY_TOOL: Dict[str, str] = {
    # repos
    "github.search_repos": "repos",
    "github.get_repo": "repos",
    # pull requests
    "github.list_prs": "pull_requests",
    "github.get_pr_diff": "pull_requests",
    # issues
    "github.search_issues": "issues",
    # actions (placeholder)
    "github.list_workflows": "actions",
    # code security
    "github.list_global_security_advisories": "code_security",
    # users
    "github.search_users": "users",
    # write tools (issues)
    "github.create_issue": "issues",
    "github.add_issue_comment": "issues",
}

_MOCK_TOOLS: List[ToolDescription] = [
    ToolDescription(
        name="github.search_repos",
        description="Search repositories by keyword",
        input_schema={"type": "object", "properties": {"q": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["q"]},
    ),
    ToolDescription(
        name="github.get_repo",
        description="Get repository metadata",
        input_schema={"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}}, "required": ["owner", "repo"]},
    ),
    ToolDescription(
        name="github.list_prs",
        description="List pull requests for a repository",
        input_schema={"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "state": {"type": "string"}}, "required": ["owner", "repo"]},
    ),
    ToolDescription(
        name="github.get_pr_diff",
        description="Get the diff for a pull request",
        input_schema={"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "number": {"type": "integer"}}, "required": ["owner", "repo", "number"]},
    ),
    ToolDescription(
        name="github.search_issues",
        description="Search issues by query",
        input_schema={"type": "object", "properties": {"q": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["q"]},
    ),
    ToolDescription(
        name="github.list_workflows",
        description="List GitHub Actions workflows for a repo (mock)",
        input_schema={"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}}, "required": ["owner", "repo"]},
    ),
    ToolDescription(
        name="github.list_global_security_advisories",
        description="List global security advisories (mock)",
        input_schema={"type": "object", "properties": {"severity": {"type": "string"}, "limit": {"type": "integer"}}},
    ),
    ToolDescription(
        name="github.search_users",
        description="Search users (mock)",
        input_schema={"type": "object", "properties": {"query": {"type": "string"}, "perPage": {"type": "integer"}, "page": {"type": "integer"}}, "required": ["query"]},
    ),
    ToolDescription(
        name="github.create_issue",
        description="Create a new issue (write tool; gated by read-only)",
        input_schema={
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "repo": {"type": "string"},
                "title": {"type": "string"},
                "body": {"type": "string"}
            },
            "required": ["owner", "repo", "title"]
        },
    ),
    ToolDescription(
        name="github.add_issue_comment",
        description="Add a comment to an issue (write tool; gated by read-only)",
        input_schema={
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "repo": {"type": "string"},
                "issue_number": {"type": "integer"},
                "comment": {"type": "string"}
            },
            "required": ["owner", "repo", "issue_number", "comment"]
        },
    ),
]


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "github-mcp"}


def _parse_toolsets_from_env() -> Optional[Set[str]]:
    env = os.environ.get("GITHUB_TOOLSETS", "").strip()
    if not env:
        return None
    parts = [p.strip() for p in env.split(",") if p.strip()]
    return set(parts) if parts else None


def _is_dynamic_enabled() -> bool:
    return os.environ.get("GITHUB_DYNAMIC_TOOLSETS", "0") in ("1", "true", "TRUE")


def _is_read_only() -> bool:
    return os.environ.get("GITHUB_READ_ONLY", "0") in ("1", "true", "TRUE")


@app.get("/info")
async def info():
    return {
        "service": "github-mcp",
        "version": SERVICE_VERSION,
        "mock_mode_default": bool(os.environ.get("GITHUB_MOCK", "1") == "1"),
        "toolsets": list(_parse_toolsets_from_env() or []),
        "dynamic_toolsets": _is_dynamic_enabled(),
        "read_only": _is_read_only(),
        "github_host": os.environ.get("GITHUB_HOST"),
        "token_present": bool(os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")),
    }


def _filter_tools_by_toolsets(toolsets: Optional[Set[str]]) -> List[ToolDescription]:
    if toolsets is None or "all" in toolsets:
        return _MOCK_TOOLS
    allowed = []
    for td in _MOCK_TOOLS:
        ts = _TOOLSET_BY_TOOL.get(td.name, None)
        if ts and ts in toolsets:
            allowed.append(td)
    return allowed


@app.get("/tools", response_model=List[ToolDescription])
async def list_tools(toolsets: Optional[str] = None):
    # Determine effective toolsets from query (if dynamic) or env
    effective: Optional[Set[str]] = None
    if toolsets and _is_dynamic_enabled():
        effective = set([p.strip() for p in toolsets.split(",") if p.strip()])
    else:
        effective = _parse_toolsets_from_env()
    # If dynamic enabled and nothing specified, default to repos only for lower cognitive load
    if _is_dynamic_enabled() and not effective:
        effective = {"repos"}
    return _filter_tools_by_toolsets(effective)


async def _invoke_mock(tool: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if tool == "github.search_repos":
        q = str(args.get("q", ""))
        limit = int(args.get("limit", 5))
        return {
            "items": [
                {"full_name": f"example/{q}-repo-{i}", "stars": 100 - i, "language": "python"}
                for i in range(max(0, min(limit, 10)))
            ]
        }
    if tool == "github.get_repo":
        owner = args.get("owner", "example")
        repo = args.get("repo", "demo")
        return {
            "full_name": f"{owner}/{repo}",
            "description": "Demo repository",
            "topics": ["docs", "fastapi", "testing"],
            "stars": 123,
        }
    if tool == "github.list_prs":
        owner = args.get("owner", "example")
        repo = args.get("repo", "demo")
        state = args.get("state", "open")
        return {
            "items": [
                {"number": n, "title": f"PR {n}", "state": state, "head": {"ref": f"feature-{n}"}}
                for n in range(1, 4)
            ],
            "repo": f"{owner}/{repo}",
        }
    if tool == "github.get_pr_diff":
        number = args.get("number", 1)
        return {
            "number": number,
            "diff": """diff --git a/app.py b/app.py
index 111..222 100644
--- a/app.py
+++ b/app.py
@@ -1,3 +1,5 @@
+print('hello')
+print('world')
""",
        }
    if tool == "github.search_issues":
        q = str(args.get("q", ""))
        limit = int(args.get("limit", 3))
        return {
            "items": [
                {"number": i, "title": f"Issue {i} about {q}", "state": "open"}
                for i in range(1, limit + 1)
            ]
        }
    if tool == "github.list_workflows":
        owner = args.get("owner", "example"); repo = args.get("repo", "demo")
        return {"repo": f"{owner}/{repo}", "workflows": [{"name": "ci", "on": ["push", "pull_request"]}]}
    if tool == "github.list_global_security_advisories":
        severity = args.get("severity", "moderate")
        return {"items": [{"ghsaId": "GHSA-xxxx-xxxx-xxxx", "severity": severity}]}
    if tool == "github.search_users":
        query = args.get("query", "dev"); per_page = int(args.get("perPage", 2))
        return {"items": [{"login": f"user{i}", "score": 10 - i} for i in range(per_page)]}
    if tool == "github.create_issue":
        # no-op stub: return created issue metadata
        return {
            "issue": {
                "number": 1,
                "title": args.get("title", ""),
                "html_url": f"https://github.com/{args.get('owner','org')}/{args.get('repo','repo')}/issues/1",
            },
            "status": "created"
        }
    if tool == "github.add_issue_comment":
        return {
            "comment": {
                "id": 1001,
                "issue_number": args.get("issue_number", 1),
                "body": args.get("comment", "")
            },
            "status": "created"
        }
    raise HTTPException(status_code=404, detail=f"Unknown tool: {tool}")


async def _invoke_real(tool: str, args: Dict[str, Any]) -> Dict[str, Any]:
    # Optional: real mode can delegate to source-agent if available
    endpoint_map = {
        "github.search_repos": ("source-agent", "github/search"),
        "github.get_repo": ("source-agent", "github/repo"),
        "github.list_prs": ("source-agent", "github/prs"),
        "github.get_pr_diff": ("source-agent", "github/pr/diff"),
    }
    if tool not in endpoint_map:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {tool}")
    svc_name, path = endpoint_map[tool]
    clients = ServiceClients(timeout=30)
    # Compose URL like "source-agent/..."
    url = f"{svc_name}/{path}"
    return await clients.post_json(url, args)


@app.post("/tools/{tool}/invoke", response_model=InvokeResponse)
async def invoke(tool: str, payload: InvokeRequest):
    use_mock_env_default = bool(os.environ.get("GITHUB_MOCK", "1") == "1")
    use_mock = payload.mock if payload.mock is not None else use_mock_env_default
    # Gate write tools if read-only
    if _is_read_only() and payload.write:
        raise HTTPException(status_code=403, detail="Read-only mode enabled")
    # Optional proxy to official server
    if os.environ.get("USE_OFFICIAL_GH_MCP", "0") in ("1", "true", "TRUE"):
        base = os.environ.get("OFFICIAL_GH_MCP_BASE_URL", "http://github-mcp-server:8060")
        try:
            from services.shared.clients import ServiceClients  # type: ignore
            clients = ServiceClients(timeout=60)
            proxied = await clients.post_json(f"{base}/tools/{tool}/invoke", payload.model_dump())
            return InvokeResponse(tool=tool, success=True, result=proxied)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Upstream MCP error: {e}")
    try:
        if use_mock:
            result = await _invoke_mock(tool, payload.arguments)
        else:
            result = await _invoke_real(tool, payload.arguments)
        # Optional downstream integrations
        await _maybe_emit_events(tool, result)
        return InvokeResponse(tool=tool, success=True, result=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _maybe_emit_events(tool: str, result: Dict[str, Any]) -> None:
    # Simple fan-out integration examples
    # - If PR diff returned, send to code-analyzer
    # - If repo metadata returned, store to doc-store as metadata document
    clients = ServiceClients(timeout=15)
    try:
        if tool == "github.get_pr_diff" and result.get("diff"):
            await clients.post_json("code-analyzer/analyze/text", {"content": result["diff"]})
        if tool == "github.get_repo" and result.get("full_name"):
            await clients.post_json("doc-store/documents", {
                "content": f"Repository: {result['full_name']}",
                "metadata": {"repo": result["full_name"], "stars": result.get("stars", 0)}
            })
    except Exception:
        # Best-effort integrations; ignore failures in fire-and-forget style
        pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5072)
