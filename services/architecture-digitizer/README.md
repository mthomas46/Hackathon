# Architecture Digitizer Service

The Architecture Digitizer service normalizes architectural diagrams from various whiteboard and diagram tools into a standardized JSON schema for use in the LLM Documentation Ecosystem.

## Overview

This service connects to popular diagram tools (Miro, FigJam, Lucid, Confluence) and converts their native formats into a consistent Software Architecture JSON schema with components and connections.

## Features

- **Multi-Platform Support**: Miro, Figma FigJam, Lucidchart, Confluence
- **Dual Input Methods**: API-based fetching or direct file upload
- **Multiple File Formats**: JSON, XML, HTML export processing
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

### POST /normalize-file

Upload and normalize a diagram file exported from a supported system.

**Request (multipart/form-data):**
- `file`: The exported diagram file (max 10MB)
- `system`: Diagram system (miro, figjam, lucid, confluence)
- `file_format`: File format (json, xml, html)

**Response:**
```json
{
  "success": true,
  "system": "miro",
  "file_format": "json",
  "filename": "architecture_diagram.json",
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
      "filename": "architecture_diagram.json",
      "format": "json"
    }
  },
  "message": "File architecture_diagram.json normalized successfully"
}
```

### GET /supported-file-formats/{system}

Get supported file formats for a specific diagram system.

**Response:**
```json
{
  "system": "miro",
  "supported_formats": [
    {
      "format": "json",
      "description": "Miro JSON export (developer format)",
      "capabilities": ["full_structural_data"],
      "export_method": "Miro Developer API or manual export"
    }
  ],
  "count": 1
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

### API-Based Normalization

#### Miro Board

```bash
curl -X POST http://localhost:5105/normalize \
  -H "Content-Type: application/json" \
  -d '{
    "system": "miro",
    "board_id": "your_board_id",
    "token": "your_miro_token"
  }'
```

#### Figma FigJam

```bash
curl -X POST http://localhost:5105/normalize \
  -H "Content-Type: application/json" \
  -d '{
    "system": "figjam",
    "board_id": "your_figjam_file_id",
    "token": "your_figma_token"
  }'
```

### File Upload Normalization

#### Upload Exported File

```bash
# Using curl with multipart/form-data
curl -X POST http://localhost:5105/normalize-file \
  -F "file=@my_diagram.json" \
  -F "system=miro" \
  -F "file_format=json"
```

#### Python Example

```python
import requests

# API-based normalization
response = requests.post('http://localhost:5105/normalize', json={
    'system': 'miro',
    'board_id': 'your_board_id',
    'token': 'your_token'
})

# File upload normalization
with open('diagram.json', 'rb') as f:
    files = {'file': f}
    data = {'system': 'miro', 'file_format': 'json'}
    response = requests.post('http://localhost:5105/normalize-file',
                           files=files, data=data)
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

## File Upload Support

The service supports direct file uploads for offline processing of exported diagrams. This is useful when you have already exported diagrams from your diagramming tools.

### Supported File Formats by System

| System | File Formats | Description | Export Method |
|--------|-------------|-------------|---------------|
| **Miro** | JSON | Developer format with full structural data | Miro Developer API or manual export |
| **FigJam** | JSON | Figma's internal JSON format | File > Export > JSON |
| **Lucid** | JSON | Lucid's export format | Lucid API or manual JSON export |
| **Confluence** | XML, HTML | Space/page exports | Space Tools > Content Tools > Export |

### File Upload Examples

#### Upload Miro JSON Export

```bash
curl -X POST http://localhost:5105/normalize-file \
  -F "file=@architecture_diagram.json" \
  -F "system=miro" \
  -F "file_format=json"
```

#### Upload Confluence XML Export

```bash
curl -X POST http://localhost:5105/normalize-file \
  -F "file=@confluence_export.xml" \
  -F "system=confluence" \
  -F "file_format=xml"
```

#### Check Supported Formats

```bash
curl http://localhost:5105/supported-file-formats/miro
```

### Export Instructions

#### Miro JSON Export
1. Use the [Miro Developer API](https://developers.miro.com/) to export board data
2. Or manually export using developer tools
3. Save as JSON file

#### FigJam JSON Export
1. Open your FigJam file in Figma
2. Go to File > Export
3. Select "JSON" format
4. Save the file

#### Lucid JSON Export
1. Use the [Lucid Developer API](https://developer.lucid.co/) to export documents
2. Or export manually through Lucid's export options
3. Save as JSON file

#### Confluence XML/HTML Export
1. Go to your Confluence space
2. Click Space Tools > Content Tools > Export
3. Choose "XML" or "HTML" export
4. Download the export file

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
