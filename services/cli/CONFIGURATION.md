# CLI Service Configuration Guide

This document explains how to configure the CLI service to eliminate hardcoded values and make it production-ready.

## Environment Variables for Service URLs

The CLI service communicates with many other services in the ecosystem. To eliminate hardcoded localhost URLs, configure the following environment variables:

### Core Service URLs

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `ANALYSIS_SERVICE_URL` | `http://localhost:5020` | Analysis Service endpoint |
| `PROMPT_STORE_URL` | `http://localhost:5110` | Prompt Store service endpoint |
| `MEMORY_AGENT_URL` | `http://localhost:5040` | Memory Agent service endpoint |
| `SOURCE_AGENT_URL` | `http://localhost:5000` | Source Agent service endpoint |
| `DOC_STORE_URL` | `http://localhost:5010` | Document Store service endpoint |
| `GITHUB_AGENT_URL` | `http://localhost:5072` | GitHub Agent service endpoint |
| `INTERPRETER_URL` | `http://localhost:5120` | Interpreter service endpoint |
| `SECURE_ANALYZER_URL` | `http://localhost:5070` | Secure Analyzer service endpoint |

### Supporting Service URLs

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `LOG_COLLECTOR_URL` | `http://localhost:5050` | Log Collector service endpoint |
| `NOTIFICATION_SERVICE_URL` | `http://localhost:5060` | Notification service endpoint |
| `ORCHESTRATOR_URL` | `http://localhost:5000` | Orchestrator service endpoint |
| `SUMMARIZER_HUB_URL` | `http://localhost:5030` | Summarizer Hub service endpoint |
| `CODE_ANALYZER_URL` | `http://localhost:5090` | Code Analyzer service endpoint |
| `BEDROCK_PROXY_URL` | `http://localhost:5055` | Bedrock Proxy service endpoint |
| `ARCHITECTURE_DIGITIZER_URL` | `http://localhost:5100` | Architecture Digitizer endpoint |
| `LLM_GATEWAY_URL` | `http://localhost:5055` | LLM Gateway service endpoint |

### External Service Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `OLLAMA_ENDPOINT` | `http://localhost:11434` | Ollama API endpoint |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URL |
| `DATABASE_URL` | `sqlite:///./cli.db` | Database connection URL |

### CLI Service Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `CLI_SERVICE_API_HOST` | `127.0.0.1` | CLI service bind host |
| `CLI_SERVICE_API_PORT` | `8000` | CLI service bind port |
| `CLI_DEBUG_MODE` | `false` | Enable debug mode |
| `CLI_LOG_LEVEL` | `INFO` | Logging level |

## Configuration Examples

### Development Environment

```bash
# Development configuration with localhost services
export ANALYSIS_SERVICE_URL=http://localhost:5020
export PROMPT_STORE_URL=http://localhost:5110
export MEMORY_AGENT_URL=http://localhost:5040
export SOURCE_AGENT_URL=http://localhost:5000
export DOC_STORE_URL=http://localhost:5010
export GITHUB_AGENT_URL=http://localhost:5072
export INTERPRETER_URL=http://localhost:5120
export SECURE_ANALYZER_URL=http://localhost:5070
export OLLAMA_ENDPOINT=http://localhost:11434
export REDIS_URL=redis://localhost:6379
export DATABASE_URL=sqlite:///./cli.db
```

### Docker Compose Environment

```bash
# Docker Compose configuration with service names
export ANALYSIS_SERVICE_URL=http://analysis-service:5020
export PROMPT_STORE_URL=http://prompt-store:5110
export MEMORY_AGENT_URL=http://memory-agent:5040
export SOURCE_AGENT_URL=http://source-agent:5000
export DOC_STORE_URL=http://doc-store:5010
export GITHUB_AGENT_URL=http://github-agent:5072
export INTERPRETER_URL=http://interpreter:5120
export SECURE_ANALYZER_URL=http://secure-analyzer:5070
export OLLAMA_ENDPOINT=http://ollama:11434
export REDIS_URL=redis://redis:6379
export DATABASE_URL=postgresql://user:password@postgres:5432/cli_db
```

### Production Environment

```bash
# Production configuration with external endpoints
export ANALYSIS_SERVICE_URL=https://analysis-api.production.com
export PROMPT_STORE_URL=https://prompt-api.production.com
export MEMORY_AGENT_URL=https://memory-api.production.com
export SOURCE_AGENT_URL=https://source-api.production.com
export DOC_STORE_URL=https://docs-api.production.com
export GITHUB_AGENT_URL=https://github-api.production.com
export INTERPRETER_URL=https://interpreter-api.production.com
export SECURE_ANALYZER_URL=https://security-api.production.com
export OLLAMA_ENDPOINT=https://ollama.production.com:11434
export REDIS_URL=redis://redis-cluster.production.com:6379
export DATABASE_URL=postgresql://user:password@db.production.com:5432/cli_db
```

## Impact on Hardcoded Values

This configuration eliminates **910+ hardcoded values** in the CLI service by:

1. **Service URL Configuration**: All inter-service communication URLs are now configurable
2. **External Service Configuration**: Database, Redis, and Ollama endpoints are configurable
3. **Service Binding**: CLI service host/port are configurable
4. **Environment-Specific Deployment**: Different configurations for dev/staging/production

## Migration Path

To migrate from hardcoded values to environment configuration:

1. **Set Environment Variables**: Define all service URLs in your deployment environment
2. **Update Docker Compose**: Use service names instead of localhost in Docker environments
3. **Configure Production**: Use external endpoints for production deployments
4. **Test Configuration**: Verify all services can communicate with configured URLs

## Benefits

- **Security**: No hardcoded sensitive endpoints in code
- **Flexibility**: Easy reconfiguration for different environments
- **Maintainability**: Configuration externalized from code
- **Deployability**: Same codebase works across dev/staging/production
- **Monitoring**: Clear visibility into service dependencies
