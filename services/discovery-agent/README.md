# Discovery Agent

Navigation: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)

Tests: [tests/unit/discovery_agent](../../tests/unit/discovery_agent)

## Key Features
- Parses inline or remote OpenAPI specs and extracts endpoints.
- **🆕 LangGraph Tool Discovery**: Automatically discovers service operations as LangGraph tools.
- Self-registers services with the orchestrator registry.
- Supports in-process ASGI tests with `http://testserver`.
- Standardized middleware and clients.

## Goal
- Automatically discover service endpoints from OpenAPI and register them with the orchestrator.
- **🆕 Enable automatic LangGraph tool discovery and registration for AI workflows.**

## Overview and role in the ecosystem
- Automates registry population by parsing OpenAPI and informing the Orchestrator about live endpoints.
- Bridges between code/services and system discovery for downstream workflows and UI routing.

## Endpoints
| Method | Path          | Description |
|--------|---------------|-------------|
| GET    | /health       | Liveness |
| POST   | /discover     | Fetch OpenAPI (optional), extract endpoints, register with orchestrator |
| **POST** | **/discover/tools** | **🆕 Discover LangGraph tools from OpenAPI specs and register with orchestrator** |

## Configuration
- `ORCHESTRATOR_URL` (default `http://orchestrator:5099`)
- `LOG_COLLECTOR_URL`: If set, emits structured logs to log-collector.

## Environment
| Name | Description | Default |
|------|-------------|---------|
| ORCHESTRATOR_URL | Orchestrator base URL | http://orchestrator:5099 |
| LOG_COLLECTOR_URL | Optional log endpoint | - |

## Usage
- Call `/discover` for each service (github-agent, jira-agent, confluence-agent, swagger-agent, consistency-engine, reporting, memory-agent, frontend).
- For services exposing OpenAPI (FastAPI), use `<base_url>/openapi.json`.

## 🆕 LangGraph Tool Discovery

The discovery-agent now supports automatic discovery and registration of LangGraph tools from service OpenAPI specifications. This enables seamless integration with AI workflows and LangGraph orchestration.

### Tool Discovery Process
1. **OpenAPI Analysis**: Parses service OpenAPI specs to identify operations
2. **Tool Categorization**: Automatically categorizes operations by functionality (CRUD, analysis, etc.)
3. **Tool Generation**: Creates LangGraph tool definitions with proper parameters
4. **Orchestrator Registration**: Registers discovered tools with the orchestrator for use in workflows

### Tool Categories
- **CRUD Operations**: `create`, `read`, `update`, `delete`
- **Business Logic**: `analysis`, `search`, `notification`, `storage`, `processing`
- **Domain-Specific**: `document`, `prompt`, `code`, `workflow`
- **General**: `general` (fallback category)

### Tool Discovery Endpoint

```bash
POST /discover/tools
Content-Type: application/json

{
  "service_name": "document_store",
  "service_url": "http://llm-document-store:5140",
  "openapi_url": "http://llm-document-store:5140/openapi.json",
  "tool_categories": ["read", "create"],
  "dry_run": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Tool discovery and registration completed",
  "data": {
    "service_name": "document_store",
    "tools_discovered": 5,
    "categories": ["read", "create"],
    "registration_status": "completed",
    "tools": [
      {
        "name": "document_store_list_documents",
        "description": "List documents in the store (Categories: read, document)",
        "categories": ["read", "document"],
        "service_name": "document_store",
        "service_url": "http://llm-document-store:5140",
        "http_method": "GET",
        "path": "/documents"
      }
    ]
  }
}
```

### Orchestrator Integration

The orchestrator provides automatic tool discovery through:

**API Endpoint:**
```bash
POST /tools/discover
```

**Automatic Startup Discovery:**
- Set `AUTO_DISCOVER_TOOLS=true` (default)
- Tools are automatically discovered when orchestrator starts
- Set `DRY_RUN_STARTUP=true` for testing without registration

**Environment Variables:**
- `AUTO_DISCOVER_TOOLS`: Enable/disable startup tool discovery (default: true)
- `DRY_RUN_STARTUP`: Test mode without actual registration (default: false)

## Related
- Orchestrator: [../orchestrator/README.md](../orchestrator/README.md)

## Testing
- Unit tests: [tests/unit/discovery_agent](../../tests/unit/discovery_agent)
- **🆕 Tool Discovery Tests**: [test_tool_discovery.py](./test_tool_discovery.py)
- Strategies:
  - Expect standardized error envelopes for validation/network errors
  - Validation: 422 for malformed JSON (FastAPI default)
  - Self-register and OpenAPI fetch paths with mock HTTP errors handled gracefully
  - **🆕 Tool discovery**: OpenAPI parsing, tool categorization, parameter extraction, orchestrator registration

### Tool Discovery Testing
```bash
# Run tool discovery tests
pytest test_tool_discovery.py -v

# Test specific scenarios
pytest test_tool_discovery.py::TestToolDiscoveryService::test_tool_categorization -v
pytest test_tool_discovery.py::TestDiscoveryHandler::test_discover_tools_dry_run -v
```

## Shared utilities
- Request/metrics middleware: `services/shared/request_id.py`, `services/shared/metrics.py`.
- Config and constants: `services/shared/config.py`, `services/shared/constants.py`.
- JSON HTTP helpers: `services/shared/clients.py`.
