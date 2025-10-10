# 🌐 ECOSYSTEM MCP - API SPECIFICATION

## Overview

**Dual Interface Architecture**:
1. **MCP Protocol**: AI agent access (stdio-based)
2. **REST API**: Human/ops access (HTTP-based, OpenAPI documented)

---

## 🎯 REST API Endpoints

### **1. Health & Status**

#### `GET /health`
**Purpose**: Service health check  
**OpenAPI**: ✅ Yes

```yaml
/health:
  get:
    summary: Health check
    tags: [System]
    responses:
      200:
        description: Service is healthy
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: "healthy"
                timestamp:
                  type: string
                  format: date-time
                services:
                  type: object
                  properties:
                    database:
                      type: boolean
                    redis:
                      type: boolean
                    chromadb:
                      type: boolean
```

#### `GET /metrics`
**Purpose**: Prometheus metrics  
**OpenAPI**: ⚠️ No (Prometheus format)

---

### **2. Ingestion Management**

#### `POST /api/v1/ingestion/start`
**Purpose**: Start ingestion job  
**OpenAPI**: ✅ Yes

```yaml
/api/v1/ingestion/start:
  post:
    summary: Start ingestion job
    tags: [Ingestion]
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              mode:
                type: string
                enum: [quick, standard, historical, full]
              repo_path:
                type: string
            required: [mode]
    responses:
      201:
        description: Job started
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/IngestionJob'
```

#### `GET /api/v1/ingestion/jobs`
**Purpose**: List ingestion jobs  
**OpenAPI**: ✅ Yes

```yaml
/api/v1/ingestion/jobs:
  get:
    summary: List ingestion jobs
    tags: [Ingestion]
    parameters:
      - name: status
        in: query
        schema:
          type: string
          enum: [pending, running, completed, failed]
      - name: limit
        in: query
        schema:
          type: integer
          default: 10
      - name: offset
        in: query
        schema:
          type: integer
          default: 0
    responses:
      200:
        description: List of jobs
        content:
          application/json:
            schema:
              type: object
              properties:
                jobs:
                  type: array
                  items:
                    $ref: '#/components/schemas/IngestionJob'
                total:
                  type: integer
```

#### `GET /api/v1/ingestion/jobs/{job_id}`
**Purpose**: Get job details  
**OpenAPI**: ✅ Yes

#### `POST /api/v1/ingestion/jobs/{job_id}/cancel`
**Purpose**: Cancel running job  
**OpenAPI**: ✅ Yes

---

### **3. Document Management**

#### `GET /api/v1/documents`
**Purpose**: Query documents  
**OpenAPI**: ✅ Yes

```yaml
/api/v1/documents:
  get:
    summary: Query documents
    tags: [Documents]
    parameters:
      - name: service
        in: query
        schema:
          type: string
      - name: file_path
        in: query
        schema:
          type: string
      - name: limit
        in: query
        schema:
          type: integer
          default: 50
      - name: offset
        in: query
        schema:
          type: integer
          default: 0
    responses:
      200:
        description: List of documents
        content:
          application/json:
            schema:
              type: object
              properties:
                documents:
                  type: array
                  items:
                    $ref: '#/components/schemas/Document'
                total:
                  type: integer
```

#### `GET /api/v1/documents/{document_id}`
**Purpose**: Get document details  
**OpenAPI**: ✅ Yes

#### `GET /api/v1/documents/{document_id}/versions`
**Purpose**: Get document version history  
**OpenAPI**: ✅ Yes

---

### **4. Search API**

#### `POST /api/v1/search`
**Purpose**: Semantic search  
**OpenAPI**: ✅ Yes

```yaml
/api/v1/search:
  post:
    summary: Semantic search across documents
    tags: [Search]
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              query:
                type: string
                example: "How to implement standard endpoints?"
              service_filter:
                type: string
              limit:
                type: integer
                default: 10
            required: [query]
    responses:
      200:
        description: Search results
        content:
          application/json:
            schema:
              type: object
              properties:
                results:
                  type: array
                  items:
                    type: object
                    properties:
                      document_id:
                        type: string
                        format: uuid
                      service_name:
                        type: string
                      file_path:
                        type: string
                      relevance_score:
                        type: number
                      snippet:
                        type: string
                query:
                  type: string
                total_results:
                  type: integer
```

---

### **5. Statistics & Analytics**

#### `GET /api/v1/stats/overview`
**Purpose**: Overall statistics  
**OpenAPI**: ✅ Yes

```yaml
/api/v1/stats/overview:
  get:
    summary: Overall ecosystem statistics
    tags: [Statistics]
    responses:
      200:
        description: Statistics overview
        content:
          application/json:
            schema:
              type: object
              properties:
                documents:
                  type: object
                  properties:
                    total:
                      type: integer
                    by_service:
                      type: object
                embeddings:
                  type: object
                  properties:
                    total:
                      type: integer
                    total_cost_usd:
                      type: number
                ingestion:
                  type: object
                  properties:
                    jobs_completed:
                      type: integer
                    jobs_running:
                      type: integer
```

#### `GET /api/v1/stats/cost`
**Purpose**: Cost breakdown  
**OpenAPI**: ✅ Yes

```yaml
/api/v1/stats/cost:
  get:
    summary: Cost breakdown and tracking
    tags: [Statistics]
    parameters:
      - name: period
        in: query
        schema:
          type: string
          enum: [today, week, month, all]
          default: month
    responses:
      200:
        description: Cost statistics
        content:
          application/json:
            schema:
              type: object
              properties:
                total_cost_usd:
                  type: number
                by_model:
                  type: object
                  additionalProperties:
                    type: number
                by_task_type:
                  type: object
                daily_budget:
                  type: number
                budget_remaining:
                  type: number
```

#### `GET /api/v1/stats/services`
**Purpose**: Service-level statistics  
**OpenAPI**: ✅ Yes

---

### **6. Admin Operations**

#### `POST /api/v1/admin/rebuild-index`
**Purpose**: Rebuild ChromaDB index  
**OpenAPI**: ✅ Yes

```yaml
/api/v1/admin/rebuild-index:
  post:
    summary: Rebuild vector database index
    tags: [Admin]
    security:
      - ApiKeyAuth: []
    responses:
      202:
        description: Rebuild started
```

#### `POST /api/v1/admin/clear-cache`
**Purpose**: Clear Redis cache  
**OpenAPI**: ✅ Yes

#### `GET /api/v1/admin/queue-status`
**Purpose**: Get queue depths  
**OpenAPI**: ✅ Yes

```yaml
/api/v1/admin/queue-status:
  get:
    summary: Get queue status
    tags: [Admin]
    responses:
      200:
        description: Queue status
        content:
          application/json:
            schema:
              type: object
              properties:
                ingestion_queue:
                  type: integer
                embedding_queue:
                  type: integer
                failed_queue:
                  type: integer
```

---

## 🔌 MCP Protocol Endpoints

**Note**: These are NOT REST endpoints. They use stdio protocol.

### Available Tools

1. **`analyze_service`**
   - Analyze service with refactoring recommendations
   - Input: `service_name`, `focus_areas`
   - Output: Analysis report

2. **`compare_services`**
   - Compare services and find patterns
   - Input: `service_name`, `compare_to`
   - Output: Comparison report

3. **`search_documentation`**
   - Semantic search across all docs
   - Input: `query`, `service_filter`, `limit`
   - Output: Search results

4. **`suggest_optimizations`**
   - Get optimization suggestions
   - Input: `service_name`, `current_phase`
   - Output: Optimization suggestions

5. **`get_refactoring_pattern`**
   - Get refactoring pattern with examples
   - Input: `pattern_name`, `service_context`
   - Output: Pattern documentation

### Available Resources

- `ecosystem://docs/{service_name}` - Service documentation
- `ecosystem://patterns/{pattern_name}` - Refactoring patterns
- `ecosystem://metrics/overview` - Ecosystem metrics

---

## 📦 OpenAPI Schema Components

```yaml
components:
  schemas:
    Document:
      type: object
      properties:
        id:
          type: string
          format: uuid
        service_name:
          type: string
        file_path:
          type: string
        content_hash:
          type: string
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time
        is_latest:
          type: boolean
        metadata:
          type: object
    
    IngestionJob:
      type: object
      properties:
        id:
          type: string
          format: uuid
        mode:
          type: string
          enum: [quick, standard, historical, full]
        status:
          type: string
          enum: [pending, running, paused, completed, failed]
        started_at:
          type: string
          format: date-time
        completed_at:
          type: string
          format: date-time
        documents_processed:
          type: integer
        documents_total:
          type: integer
        progress_percentage:
          type: number
        total_cost_usd:
          type: number
    
    Error:
      type: object
      properties:
        error:
          type: string
        message:
          type: string
        details:
          type: object
  
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
```

---

## 🎯 Implementation Requirements

### FastAPI Setup

```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="Ecosystem MCP Service",
    description="Intelligent refactoring knowledge base with MCP integration",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Ecosystem MCP API",
        version="0.1.0",
        description="REST API for Ecosystem MCP Service",
        routes=app.routes,
    )
    
    # Add custom info
    openapi_schema["info"]["x-logo"] = {
        "url": "https://..."
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### Route Decorators

```python
@app.get(
    "/api/v1/documents",
    response_model=DocumentListResponse,
    summary="Query documents",
    description="Search and filter documents with pagination",
    tags=["Documents"],
    responses={
        200: {"description": "List of documents"},
        400: {"description": "Invalid parameters"},
        500: {"description": "Server error"}
    }
)
async def list_documents(
    service: Optional[str] = Query(None, description="Filter by service name"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    ...
```

---

## 🔄 Updated Implementation Plan

### Phase 1.6: MCP Server + REST API

**Tasks**:
1. ✅ MCP protocol implementation (for AI agents)
2. **NEW**: FastAPI REST API setup
3. **NEW**: OpenAPI/Swagger documentation
4. **NEW**: Admin endpoints
5. **NEW**: Search API endpoints
6. **NEW**: Statistics endpoints
7. **NEW**: Health & metrics endpoints

**Deliverables**:
- MCP server (stdio-based)
- REST API (HTTP-based)
- Complete OpenAPI spec
- Interactive docs at `/docs`
- ReDoc at `/redoc`

---

## 🎯 Benefits

### For Developers
- Interactive API documentation
- Easy testing via Swagger UI
- Clear contracts
- Auto-generated clients

### For Operations
- Health monitoring
- Job management
- Cost tracking
- Queue monitoring

### For AI Agents
- MCP protocol for natural access
- Semantic search via tools
- Context-aware suggestions

---

**Status**: Specification complete, ready for implementation  
**Next**: Continue Phase 1.3 (Redis), then implement REST API in Phase 1.6

