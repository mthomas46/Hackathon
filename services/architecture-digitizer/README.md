# Architecture Digitizer Service

The Architecture Digitizer service normalizes architectural diagrams from various whiteboard and diagram tools into a standardized JSON schema for use in the LLM Documentation Ecosystem.

## Overview

This service connects to popular diagram tools (Miro, FigJam, Lucid, Confluence) and converts their native formats into a consistent Software Architecture JSON schema with components and connections.

## Features

- **Multi-Platform Support**: Miro, Figma FigJam, Lucidchart, Confluence
- **Standardized Output**: Consistent JSON schema for all diagram types
- **Error Handling**: Robust API error handling and retries
- **Caching**: Optional response caching to reduce API calls
- **Metrics**: Prometheus-compatible metrics for monitoring

## API Endpoints

### POST /normalize

Normalize an architectural diagram from a supported platform.

**Request Body:**
```json
{
  "system": "miro|figjam|lucid|confluence",
  "board_id": "board_or_document_id",
  "token": "api_authentication_token"
}
```

**Response:**
```json
{
  "success": true,
  "system": "miro",
  "board_id": "board123",
  "data": {
    "components": [
      {
        "id": "comp1",
        "type": "service",
        "name": "User Service",
        "description": "Handles user authentication"
      }
    ],
    "connections": [
      {
        "from_id": "comp1",
        "to_id": "comp2",
        "label": "REST API"
      }
    ],
    "metadata": {
      "source": "miro",
      "board_id": "board123"
    }
  },
  "message": "Architecture diagram normalized successfully"
}
```

### GET /supported-systems

Get information about all supported diagram systems.

**Response:**
```json
{
  "systems": [
    {
      "name": "miro",
      "description": "Miro whiteboard diagram normalizer",
      "auth_type": "Bearer token",
      "supported": true
    }
  ],
  "count": 4
}
```

## Supported Systems

| System | Description | Authentication | API Endpoint |
|--------|-------------|----------------|--------------|
| **Miro** | Whiteboard collaboration | Bearer token | `https://api.miro.com/v2/boards/{id}/items` |
| **FigJam** | Figma collaborative whiteboard | X-FIGMA-TOKEN | `https://api.figma.com/v1/files/{id}` |
| **Lucid** | Professional diagramming | Bearer token | `https://lucid.app/api/documents/{id}/export/json` |
| **Confluence** | Atlassian documentation | Bearer token | Wiki REST API |

## Configuration

```yaml
# services/architecture-digitizer/config.yaml
architecture_digitizer:
  supported_systems:
    - miro
    - figjam
    - lucid
    - confluence

  api_timeout_seconds: 30
  max_retries: 3
  cache_enabled: true
  cache_ttl_seconds: 300

external_apis:
  miro:
    base_url: https://api.miro.com/v2
  # ... other system configs
```

## Usage Examples

### Miro Board

```bash
curl -X POST http://localhost:5105/normalize \
  -H "Content-Type: application/json" \
  -d '{
    "system": "miro",
    "board_id": "your_board_id",
    "token": "your_miro_token"
  }'
```

### Figma FigJam

```bash
curl -X POST http://localhost:5105/normalize \
  -H "Content-Type: application/json" \
  -d '{
    "system": "figjam",
    "board_id": "your_figjam_file_id",
    "token": "your_figma_token"
  }'
```

## Integration with Ecosystem

The Architecture Digitizer integrates with other services in the ecosystem:

### Source Agent Integration

The source-agent can use this service to ingest architectural diagrams:

```python
# In source-agent fetch handler
from services.shared.utilities import get_service_client

client = get_service_client()
diagram_data = await client.post(
    "/normalize",
    json={
        "system": "miro",
        "board_id": board_id,
        "token": token
    }
)
```

### Analysis Service Integration

The analysis-service can process normalized architecture data:

```python
# Architecture analysis using normalized diagram
analysis_result = await analysis_service.analyze_architecture(
    diagram_data["data"]
)
```

## Running the Service

### Individual Development

```bash
cd services/architecture-digitizer
docker-compose up
```

### Full Ecosystem

```bash
# Start with AI services (includes architecture-digitizer)
docker-compose --profile ai_services up
```

### Health Check

```bash
curl http://localhost:5105/health
```

## Authentication Setup

### Miro
1. Go to [Miro Developer Portal](https://developers.miro.com/)
2. Create an app and get your access token
3. Use as Bearer token in API calls

### Figma FigJam
1. Go to [Figma Account Settings](https://www.figma.com/settings)
2. Generate a personal access token
3. Use as `X-FIGMA-TOKEN` header

### Lucidchart
1. Go to [Lucid Developer Portal](https://developer.lucid.co/)
2. Create an OAuth app
3. Use Bearer token from OAuth flow

### Confluence
1. Go to [Atlassian Developer Console](https://developer.atlassian.com/)
2. Create an API token
3. Use as Bearer token

## Error Handling

The service provides detailed error messages:

- **400 Bad Request**: Unsupported system or invalid request
- **401 Unauthorized**: Invalid API token
- **404 Not Found**: Board/document not found
- **500 Internal Server Error**: API failures or processing errors

## Metrics and Monitoring

The service exposes Prometheus metrics:

- `architecture_digitizer_requests_total{system, status}`
- `architecture_digitizer_request_duration_seconds{system}`
- `architecture_digitizer_api_failures_total{system}`
- `architecture_digitizer_cache_hits_total`
- `architecture_digitizer_cache_misses_total`

## Development

### Adding New Systems

1. Create a new normalizer class in `modules/normalizers.py`
2. Add it to `SUPPORTED_SYSTEMS` dict
3. Update configuration in `config.yaml`
4. Add API documentation

### Testing

```bash
# Run with mock data for testing
export ENVIRONMENT=test
python services/architecture-digitizer/main.py
```

## Schema Details

The normalized output follows this JSON schema:

```json
{
  "components": [
    {
      "id": "string",
      "type": "service|database|queue|ui|gateway|function|storage|other",
      "name": "string",
      "description": "string (optional)"
    }
  ],
  "connections": [
    {
      "from_id": "string",
      "to_id": "string",
      "label": "string (optional)"
    }
  ],
  "metadata": {
    "source": "miro|figjam|lucid|confluence",
    "board_id": "string"
  }
}
```

This standardized format allows the LLM Documentation Ecosystem to process architectural diagrams consistently, regardless of their original source platform.
