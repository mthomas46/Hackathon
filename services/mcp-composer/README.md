# MCP Composer Service

Multi-MCP composition and orchestration service for the MCP ecosystem.

## Overview

The MCP Composer Service enables orchestration of multiple Model Context Protocol (MCP) instances through declarative composition specifications. It provides:

- **Multi-MCP Routing**: Route queries to multiple MCPs using different strategies
- **Conflict Resolution**: Intelligently resolve conflicts between MCP responses
- **Composition Specifications**: Define MCP compositions using `mcp-compose.yaml`
- **Pattern Composition**: Combine different LLM patterns across MCPs

## Features

### Composition Strategies

1. **Sequential**: Execute MCPs in sequence, passing context forward
2. **Parallel**: Execute all MCPs simultaneously
3. **Hierarchical**: Execute tier-by-tier (ecosystem → team → project → client)
4. **Weighted**: Combine responses using weighted averages
5. **Fallback**: Try MCPs in order until one succeeds

### Conflict Resolution

1. **Priority**: Use highest priority MCP
2. **Merge**: Intelligently merge all responses
3. **Vote**: Democratic voting on answers
4. **Expert**: Defer to expert MCP (highest tier)
5. **Latest**: Use most recent response
6. **Consensus**: Require agreement threshold

## Quick Start

### Example Composition

```yaml
# mcp-compose.yaml
spec_version: "1.0"
name: "Multi-Tier Knowledge"
strategy: "hierarchical"
conflict_resolution: "merge"

mcps:
  - mcp_id: "ecosystem-core"
    tier: "ecosystem"
    priority: 1
  - mcp_id: "team-backend"
    tier: "team"
    priority: 2
  - mcp_id: "project-api"
    tier: "project"
    priority: 3
```

### Execute Query

```bash
curl -X POST http://localhost:5646/api/v1/compose/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How does authentication work in our API?",
    "composition_yaml": "..."
  }'
```

## API Endpoints

### Compositions

- `POST /api/v1/compositions` - Create composition
- `GET /api/v1/compositions` - List compositions
- `GET /api/v1/compositions/{id}` - Get composition

### Queries

- `POST /api/v1/compose/query` - Execute composed query

### Examples

- `GET /api/v1/examples/composition` - Get example YAML

## Architecture

```
┌─────────────────────────────────────┐
│      MCP Composer Service           │
├─────────────────────────────────────┤
│  ┌─────────────────────────────┐   │
│  │   YAML Parser               │   │
│  │   - Parse mcp-compose.yaml  │   │
│  │   - Validate specifications │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │   Routing Engine            │   │
│  │   - Sequential routing      │   │
│  │   - Parallel routing        │   │
│  │   - Hierarchical routing    │   │
│  │   - Weighted routing        │   │
│  │   - Fallback routing        │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │   Conflict Resolver         │   │
│  │   - Priority resolution     │   │
│  │   - Merge responses         │   │
│  │   - Voting mechanism        │   │
│  │   - Expert selection        │   │
│  │   - Consensus checking      │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
           ↓
    ┌──────────────┐
    │ MCP Gateway  │
    └──────────────┘
           ↓
  ┌────────────────────┐
  │  MCP Instances     │
  └────────────────────┘
```

## Configuration

Environment variables:

```bash
MCP_GATEWAY_URL=http://mcp-gateway:5641
SERVICE_PORT=5646
LOG_LEVEL=INFO
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python main.py

# Run tests
pytest tests/
```

## Docker

```bash
# Build
docker build -t mcp-composer .

# Run
docker run -p 5646:5646 mcp-composer
```

## License

Part of the MCP System
