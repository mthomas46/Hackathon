# Source Agent (Consolidated)

Navigation: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)

Tests: [tests/unit/source_agent](../../tests/unit/source_agent)

## Overview

The **Source Agent** is a consolidated service that combines the functionality of the individual GitHub, Jira, and Confluence agents into a single, unified service. This consolidation reduces code duplication and simplifies deployment while maintaining all the original capabilities.

## Key Features

- **Multi-Source Support**: Handles GitHub, Jira, and Confluence data sources
- **Unified API**: Single endpoint interface for all source operations
- **Code Analysis**: Integrated code analysis for API endpoint detection
- **Normalization**: Consistent document normalization across all sources
- **Caching**: HTTP caching for improved performance
- **Rate Limiting**: Built-in rate limiting for API protection

## Architecture

The Source Agent consolidates the following services:

### GitHub Agent Features
- README fetching and normalization
- Pull request normalization
- Code analysis and endpoint extraction
- Owner derivation from GitHub metadata

### Jira Agent Features
- Issue normalization and summarization
- Status and priority tracking
- Assignee and reporter information

### Confluence Agent Features
- Page normalization with HTML-to-text conversion
- Space and version tracking
- Content structure preservation

## API Endpoints
| Method | Path        | Description |
|--------|-------------|-------------|
| POST   | /docs/fetch | Fetch documents from sources |
| POST   | /normalize  | Normalize raw data to DocumentEnvelope |
| POST   | /code/analyze | Analyze code text for endpoints |
| GET    | /sources    | List supported sources and capabilities |

### Core Endpoints

#### `POST /docs/fetch`
Fetch documents from specified sources.

**Request:**
```json
{
  "source": "github",
  "identifier": "owner:repo",
  "scope": {"include_readme": true}
}
```

**Response:**
```json
{
  "document": {...},
  "source": "github"
}
```

#### `POST /normalize`
Normalize raw data from any supported source.

**Request:**
```json
{
  "source": "github",
  "data": {"type": "pr", "number": 123, "title": "..."},
  "correlation_id": "trace-123"
}
```

**Response:**
```json
{
  "envelope": {
    "id": "env:github:pr:123",
    "correlation_id": "trace-123",
    "document": {...}
  }
}
```

#### `POST /code/analyze`
Analyze code text for API endpoints and patterns.

**Request:**
```json
{
  "text": "app.get('/users', handler); @app.post('/orders')"
}
```

**Response:**
```json
{
  "analysis": "app.get('/users', handler)\n@app.post('/orders')",
  "endpoint_count": 2,
  "patterns_found": ["Express", "FastAPI"]
}
```

#### `GET /sources`
List supported sources and their capabilities.

**Response:**
```json
{
  "sources": ["github", "jira", "confluence"],
  "capabilities": {
    "github": ["readme_fetch", "pr_normalization", "code_analysis"],
    "jira": ["issue_normalization"],
    "confluence": ["page_normalization"]
  }
}
```

### Standard Endpoints

#### `GET /health`
Health check endpoint.

## Related
- Doc Store: [../doc-store/README.md](../doc-store/README.md)
- Orchestrator: [../orchestrator/README.md](../orchestrator/README.md)

## Testing
- Unit tests: [tests/unit/source_agent](../../tests/unit/source_agent)
- Strategies:
  - Endpoint normalization and code analysis routes
  - Mock external APIs and validate DocumentEnvelope structure

#### `GET /service-info`
Basic service information.

#### `GET /agent-info`
Agent-specific information including capabilities.

#### `GET /info`
Detailed service information.

#### `GET /config/effective`
Effective configuration (redacted).

## Configuration

### Environment Variables

```bash
# Service Configuration
PORT=5000
ENVIRONMENT=production
LOG_LEVEL=INFO

# GitHub Configuration
GITHUB_TOKEN=your_github_token
GITHUB_API_BASE=https://api.github.com

# Jira Configuration
JIRA_BASE_URL=https://company.atlassian.net
JIRA_USERNAME=your_username
JIRA_API_TOKEN=your_api_token

# Confluence Configuration
CONFLUENCE_BASE_URL=https://company.atlassian.net
CONFLUENCE_USERNAME=your_username
CONFLUENCE_API_TOKEN=your_api_token

# Caching Configuration
CACHE_TTL_SECONDS=300
ENABLE_HTTP_CACHE=true

# Rate Limiting
RATE_LIMIT_ENABLED=true

# Self-Registration
ENABLE_SELF_REGISTER=true
SERVICE_BASE_URL=http://source-agent:5000
ORCHESTRATOR_URL=http://orchestrator:5099
```

### Configuration File

```yaml
# config.yaml
server:
  host: 0.0.0.0
  port: 5000

sources:
  github:
    api_base: https://api.github.com
    timeout: 30
  jira:
    base_url: https://company.atlassian.net
    timeout: 30
  confluence:
    base_url: https://company.atlassian.net
    timeout: 30

cache:
  enabled: true
  ttl_seconds: 300

rate_limiting:
  enabled: true
  limits:
    "/docs/fetch": [10, 20]
    "/normalize": [20, 50]
    "/code/analyze": [15, 30]
```

## Secrets
- Use `services/shared/credentials.get_secret("GITHUB_TOKEN")`, `get_secret("JIRA_API_TOKEN")`, `get_secret("CONFLUENCE_API_TOKEN")`.
- Pass via env or compose/K8s secrets; do not commit.

## Usage Examples

### Fetch GitHub README

```bash
curl -X POST http://localhost:5000/docs/fetch \
  -H "Content-Type: application/json" \
  -d '{
    "source": "github",
    "identifier": "microsoft:vscode"
  }'
```

### Normalize GitHub Pull Request

```bash
curl -X POST http://localhost:5000/normalize \
  -H "Content-Type: application/json" \
  -d '{
    "source": "github",
    "data": {
      "type": "pr",
      "number": 123,
      "title": "Add new feature",
      "body": "This PR adds...",
      "html_url": "https://github.com/owner/repo/pull/123",
      "base": {"repo": {"full_name": "owner/repo"}}
    },
    "correlation_id": "trace-123"
  }'
```

### Analyze Code for Endpoints

```bash
curl -X POST http://localhost:5000/code/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "@app.get(\"/users\")\napp.post(\"/orders\", handler)\ndef create_order():\n    return {\"status\": \"ok\"}"
  }'
```

## Integration

### With Orchestrator

The Source Agent integrates seamlessly with the Orchestrator for workflow orchestration:

1. **Ingestion Requests**: Orchestrator sends ingestion requests to `/docs/fetch`
2. **Normalization**: Raw data is normalized through `/normalize`
3. **Analysis**: Code analysis via `/code/analyze`
4. **Event Emission**: Normalized documents are emitted as events

### With Consistency Engine

The Source Agent provides normalized documents to the Consistency Engine:

1. **Document Envelope**: Structured document format
2. **Correlation Tracking**: Request tracing across services
3. **Metadata Enrichment**: Source-specific metadata inclusion

### With Doc Store

Documents are persisted with full metadata:

```json
{
  "id": "github:owner/repo:readme",
  "source_type": "github",
  "source_id": "owner/repo",
  "title": "README.md",
  "content": "# Project Title...",
  "content_hash": "abc123...",
  "url": "https://github.com/owner/repo",
  "project": "owner/repo",
  "metadata": {
    "type": "readme",
    "source_link": {"repo": "owner/repo"},
    "owner": ["developer1", "developer2"]
  }
}
```

## Benefits of Consolidation

### Code Reduction
- **Before**: 4 separate services (~2,000 lines each)
- **After**: 1 consolidated service (~800 lines)
- **Reduction**: ~75% code reduction

### Simplified Deployment
- Single service instead of 4 services
- Unified configuration management
- Consistent logging and monitoring

### Improved Maintainability
- Single codebase for source operations
- Shared utilities and patterns
- Consistent error handling

### Performance Benefits
- Reduced inter-service communication
- Shared connection pools
- Unified caching layer

## Migration Guide

### From Individual Agents

1. **Update Orchestrator Configuration**:
   ```yaml
   # Before
   github_agent_url: http://github-agent:5000
   jira_agent_url: http://jira-agent:5001
   confluence_agent_url: http://confluence-agent:5050

   # After
   source_agent_url: http://source-agent:5000
   ```

2. **Update API Calls**:
   ```python
   # Before
   await github_agent.post_json("/docs/readme", {"owner": "org", "repo": "repo"})

   # After
   await source_agent.post_json("/docs/fetch", {
     "source": "github",
     "identifier": "org:repo"
   })
   ```

3. **Update Environment Variables**:
   - Consolidate source-specific configs
   - Remove duplicate service URLs
   - Update health check endpoints

## Monitoring and Observability

### Metrics
- **Request Rate**: Per-source request rates
- **Response Time**: Average response times by operation
- **Error Rate**: Per-source error rates
- **Cache Hit Rate**: HTTP cache performance

### Logging
- **Structured Logs**: JSON-formatted logs with correlation IDs
- **Source Tracking**: Source-specific operation logging
- **Performance Metrics**: Operation timing and resource usage

### Health Checks
- **Service Health**: Overall service availability
- **Source Connectivity**: Per-source API connectivity
- **Cache Health**: Cache system performance
- **Rate Limit Status**: Current rate limit utilization

## Troubleshooting

### Common Issues

1. **Source API Errors**:
   - Check API credentials and endpoints
   - Verify network connectivity
   - Review rate limit status

2. **Normalization Failures**:
   - Validate input data structure
   - Check source-specific requirements
   - Review error logs for details

3. **Cache Issues**:
   - Verify Redis connectivity
   - Check cache TTL settings
   - Monitor cache hit rates

4. **Performance Problems**:
   - Monitor request rates
   - Check resource utilization
   - Review slow query logs

### Debug Mode

Enable debug logging for detailed operation tracing:

```bash
export LOG_LEVEL=DEBUG
export DEBUG=true
```

## Future Enhancements

### Planned Features
- **Webhook Support**: Real-time source updates
- **Batch Operations**: Bulk document processing
- **Advanced Caching**: Intelligent cache invalidation
- **Metrics Export**: Prometheus metrics integration

### Extensibility
- **Plugin Architecture**: Add new source types
- **Custom Normalizers**: Source-specific normalization logic
- **Advanced Analysis**: ML-powered code analysis

The consolidated Source Agent provides a robust, efficient, and maintainable solution for multi-source document ingestion and normalization, significantly reducing complexity while maintaining full functionality.
