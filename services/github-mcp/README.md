# GitHub MCP

Navigation: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)
Local MCP-like server exposing GitHub-oriented tools (mock-first).

- **Port**: 5072
- **Endpoints**: `/health`, `/info`, `/tools`, `/tools/{tool}/invoke`
- **Tests**: [tests/unit/github_mcp](../../tests/unit/github_mcp)

## Overview and role in the ecosystem
- Exposes a mock-friendly tool interface inspired by GitHub MCP servers for local development.
- Allows the ecosystem to simulate GitHub operations (repos, PRs, issues) and feed data to Code Analyzer and Doc Store.

## Features
- Dynamic tool filtering by toolset (repos/issues/etc.)
- Read-only gating for write tools
- Optional proxying to an external MCP server

## Environment
- `GITHUB_MOCK` (default 1)
- `GITHUB_TOOLSETS` (e.g. `repos,issues`)
- `GITHUB_DYNAMIC_TOOLSETS` (1 enables query param control)
- `GITHUB_READ_ONLY` (1 gates write tools)

## Example
```bash
curl http://localhost:5072/tools
curl -X POST http://localhost:5072/tools/github.search_repos/invoke \
  -H 'Content-Type: application/json' -d '{"arguments":{"q":"docs","limit":2}}'
```

## Related
- Source Agent: [../source-agent/README.md](../source-agent/README.md)
- Code Analyzer: [../code-analyzer/README.md](../code-analyzer/README.md)
- Services index: [../README_SERVICES.md](../README_SERVICES.md)

## Testing
- Unit tests: [tests/unit/github_mcp](../../tests/unit/github_mcp)
- Strategies:
  - Mock tool invocation responses and read-only gating

## API
| Method | Path                      | Description |
|--------|---------------------------|-------------|
| GET    | /health                   | Health check |
| GET    | /info                     | Service info and flags |
| GET    | /tools                    | List tools (by toolsets) |
| POST   | /tools/{tool}/invoke      | Invoke a tool |

## Environment
| Name | Description | Default |
|------|-------------|---------|
| GITHUB_MOCK | Use mock responses | 1 |
| GITHUB_TOOLSETS | Allowed toolsets (e.g., repos,issues) | - |
| GITHUB_DYNAMIC_TOOLSETS | Enable query param toolsets | 0 |
| GITHUB_READ_ONLY | Gate write tools | 0 |
