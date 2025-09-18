# Service Port Mappings

This document defines the standardized port mappings for all ecosystem services.

## Port Registry

| Service | External Port | Internal Port | Health Endpoint | Required for Production |
|---------|---------------|---------------|-----------------|------------------------|
| redis | 6379 | 6379 | / | ✅ |
| doc_store | 5087 | 5010 | /health | ✅ |
| orchestrator | 5099 | 5099 | /health | ✅ |
| llm-gateway | 5055 | 5055 | /health | ✅ |
| analysis-service | 5080 | 5020 | /health | ✅ |
| discovery-agent | 5045 | 5045 | /health | ✅ |
| notification-service | 5130 | 5020 | /health | ✅ |
| code-analyzer | 5025 | 5025 | /health | ✅ |
| source-agent | 5085 | 5070 | /health | ✅ |
| frontend | 3000 | 3000 | / | ✅ |
| ollama | 11434 | 11434 | /api/tags | ✅ |

## Service Dependencies

- **doc_store**: depends on redis
- **orchestrator**: depends on redis
- **llm-gateway**: depends on ollama
- **analysis-service**: depends on doc_store, llm-gateway
- **discovery-agent**: depends on orchestrator
- **source-agent**: depends on doc_store
- **frontend**: depends on orchestrator

## Environment Variables

### doc_store
- `SERVICE_PORT`: 5010
- `REDIS_URL`: redis://redis:6379

### orchestrator
- `SERVICE_PORT`: 5099
- `REDIS_URL`: redis://redis:6379

### llm-gateway
- `SERVICE_PORT`: 5055
- `OLLAMA_ENDPOINT`: http://ollama:11434

### analysis-service
- `SERVICE_PORT`: 5020
- `DOC_STORE_URL`: http://doc_store:5010
- `LLM_GATEWAY_URL`: http://llm-gateway:5055

### discovery-agent
- `SERVICE_PORT`: 5045
- `ORCHESTRATOR_URL`: http://orchestrator:5099

### notification-service
- `SERVICE_PORT`: 5020

### code-analyzer
- `SERVICE_PORT`: 5025

### source-agent
- `SERVICE_PORT`: 5070
- `DOC_STORE_URL`: http://doc_store:5010

### frontend
- `REACT_APP_API_URL`: http://localhost:5099

