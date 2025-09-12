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
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from services.shared.middleware import RequestIdMiddleware, RequestMetricsMiddleware  # type: ignore
from services.shared.utilities import attach_self_register, setup_common_middleware  # type: ignore
from services.shared.constants_new import ServiceNames  # type: ignore
from services.shared.clients import ServiceClients  # type: ignore

from .modules.config import config
from .modules.tool_registry import tool_registry, ToolDescription
from .modules.mock_implementations import mock_implementations
from .modules.real_implementations import real_implementations
from .modules.event_system import event_system

SERVICE_TITLE = "GitHub MCP"
SERVICE_VERSION = "0.1.0"

app = FastAPI(title=SERVICE_TITLE, version=SERVICE_VERSION)
setup_common_middleware(app, ServiceNames.GITHUB if hasattr(ServiceNames, "GITHUB") else "github-mcp")
attach_self_register(app, ServiceNames.GITHUB if hasattr(ServiceNames, "GITHUB") else "github-mcp")


class InvokeRequest(BaseModel):
    arguments: Dict[str, Any] = {}
    correlation_id: Optional[str] = None
    mock: Optional[bool] = None
    write: Optional[bool] = None


class InvokeResponse(BaseModel):
    tool: str
    success: bool
    result: Dict[str, Any]


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "github-mcp"}


@app.get("/info")
async def info():
    return {
        "service": "github-mcp",
        "version": SERVICE_VERSION,
        "mock_mode_default": config.is_mock_default(),
        "toolsets": list(config.parse_toolsets_from_env() or []),
        "dynamic_toolsets": config.is_dynamic_enabled(),
        "read_only": config.is_read_only(),
        "github_host": config.get_github_host(),
        "token_present": config.has_github_token(),
    }


@app.get("/tools", response_model=List[ToolDescription])
async def list_tools(toolsets: Optional[str] = None):
    # Determine effective toolsets from query (if dynamic) or env
    effective: Optional[Set[str]] = None
    if toolsets and config.is_dynamic_enabled():
        effective = set([p.strip() for p in toolsets.split(",") if p.strip()])
    else:
        effective = config.parse_toolsets_from_env()
    # If dynamic enabled and nothing specified, default to repos only for lower cognitive load
    if config.is_dynamic_enabled() and not effective:
        effective = {"repos"}
    return tool_registry.filter_tools_by_toolsets(effective)




@app.post("/tools/{tool}/invoke", response_model=InvokeResponse)
async def invoke(tool: str, payload: InvokeRequest):
    use_mock = payload.mock if payload.mock is not None else config.is_mock_default()
    # Gate write tools if read-only
    if config.is_read_only() and payload.write:
        raise HTTPException(status_code=403, detail="Read-only mode enabled")
    # Optional proxy to official server
    if config.should_use_official_mcp():
        base = config.get_official_mcp_base_url()
        try:
            clients = ServiceClients(timeout=60)
            proxied = await clients.post_json(f"{base}/tools/{tool}/invoke", payload.model_dump())
            return InvokeResponse(tool=tool, success=True, result=proxied)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Upstream MCP error: {e}")
    try:
        if use_mock:
            result = await mock_implementations.invoke_tool(tool, payload.arguments)
        else:
            result = await real_implementations.invoke_tool(tool, payload.arguments)
        # Optional downstream integrations
        await event_system.maybe_emit_events(tool, result)
        return InvokeResponse(tool=tool, success=True, result=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5072)
