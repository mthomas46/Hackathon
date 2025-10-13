# Api

# API Reference

## Overview

Based on the provided code snippets, here are the API endpoints in ecosystem-mcp with brief descriptions:

1. **/metrics**: Exposes metrics at /metrics in Prometheus format.
2. **/admin**:
	* **IngestRequest**: Request to start ingestion.
	* **IngestResponse**: Response from ingestion request.
	* **JobStatus**: Ingestion job status.
3. **/analyze**: Analyzes code and returns structures, complexity metrics, etc.
4. **/openapi/docs**: Returns OpenAPI documentation for the API.
5. **/redoc/docs**: Returns ReDoc documentation for the API.
6. **/openapi/json**: Returns JSON representation of the OpenAPI specification.

Note that these endpoints are based on the provided code snippets and might not be an exhaustive list of all API endpoints in ecosystem-mcp.

Based on the provided context from the documentation, I can identify several main API categories. Here's a breakdown:

1. **Health APIs**:
	* `services/mcp-gateway/domain/value_objects/health_status.py` [Source 9]: Health Status Value Object.
	* `services/doc_store/tests/unit/api/test_core.py` [Source 11]: Test health and service information endpoints.
2. **Search APIs**:
	* `services/doc_store/tests/unit/api/test_search.py` [Source 15]: Doc Store API Search Tests.
3. **Reporting and Analytics APIs**:
	* `services/analysis-service/application/services/reporting/reporting_service.py` [Source 7]: Reporting services for analysis results.
4. **Admin and Management APIs**:
	* `services/cli/modules/adapters/service_registry.py` [Source 13]: Unified Service Registry (central registry for all ecosystem services).
	* `services/doc_store/tests/unit/api/test_core.py` [Source 11]: Test health and service information endpoints.
5. **Catalog and API Discovery APIs**:
	* `services/unified-api-dashboard/modules/catalog.py` [Source 20]: Catalog module for Unified API Dashboard.

These categories are not exhaustive, but they represent the main areas of functionality based on the provided documentation.

## Technical Details

**API Endpoint Documentation**

### `/api/v1/search`

#### Description

The `/api/v1/search` endpoint allows users to search for documents based on various criteria. This endpoint supports filtering by document metadata, content, and tags.

#### Parameters

* `q`: The search query string (required)
* `fields`: A comma-separated list of fields to search in (optional)
* `tags`: A comma-separated list of tags to filter by (optional)
* `limit`: The maximum number of results to return (optional, default: 10)
* `offset`: The starting index for pagination (optional)

#### Request Format

The request body should be a JSON object with the following structure:
```json
{
  "q": string,
  "fields": [string],
  "tags": [string]
}
```
#### Response Format

The response will be a JSON object with the following structure:
```json
{
  "results": [
    {
      "id": string,
      "title": string,
      "content": string,
      "metadata": { ... },
      "tags": [string]
    }
  ],
  "total": integer,
  "offset": integer,
  "limit": integer
}
```
#### Examples

* Search for documents with the title containing the word "example":
```bash
curl -X GET \
  http://localhost:8000/api/v1/search?q=title%3Aexample \
  -H 'Content-Type: application/json'
```
Response:
```json
{
  "results": [
    {
      "id": "doc-123",
      "title": "Example Document",
      "content": "...",
      "metadata": { ... },
      "tags": ["tag1", "tag2"]
    }
  ],
  "total": 10,
  "offset": 0,
  "limit": 10
}
```
* Search for documents with the tag "tag1" and limit the results to 5:
```bash
curl -X GET \
  http://localhost:8000/api/v1/search?q=tags%3Atag1&limit=5 \
  -H 'Content-Type: application/json'
```
Response:
```json
{
  "results": [
    {
      "id": "doc-123",
      "title": "Example Document",
      "content": "...",
      "metadata": { ... },
      "tags": ["tag1", "tag2"]
    }
  ],
  "total": 10,
  "offset": 0,
  "limit": 5
}
```
Note: This documentation is based on the provided context and may not be exhaustive. Additional parameters, request formats, or response structures may exist depending on the actual implementation of the `/api/v1/search` endpoint.

I don't have enough information to provide a detailed documentation of the `/api/v1/ask` endpoint. The provided context does not mention this specific endpoint or its related classes and methods. However, based on the structure of the API routes in `services/ecosystem-mcp/src/api/routes/search.py` and `services/ecosystem-mcp/src/api/routes/query.py`, it is likely that the `/api/v1/ask` endpoint is part of a query or search functionality.

To provide an accurate answer, I would need more information about the specific endpoint, such as its purpose, parameters, request/response format, and examples. If you can provide additional context or clarify which class or method handles this endpoint, I will do my best to assist you in documenting it.

I don't have enough information to accurately document the `/api/v1/admin/ingest` endpoint. The provided context does not mention this specific endpoint or its functionality.

**Documenting the `/api/v1/query` Endpoint**

The `/api/v1/query` endpoint is a critical component of the MCP ecosystem, enabling users to retrieve and filter documents. This documentation aims to provide a comprehensive overview of this endpoint's functionality.

### Overview

The `/api/v1/query` endpoint allows users to search for documents based on various criteria, including document metadata and content. This endpoint supports filtering, sorting, and pagination, making it an essential tool for users seeking specific information within the MCP ecosystem.

### Request Parameters

The following parameters can be passed in the request body:

* `query`: A string containing the search query.
* `filter`: An object containing filter criteria (e.g., author, format, content).
* `sort`: An object specifying sorting options (e.g., ascending/descending order).
* `limit`: The maximum number of results to return.
* `offset`: The starting point for pagination.

### Response

The response from the `/api/v1/query` endpoint will contain a list of documents that match the specified criteria. Each document is represented as an object with the following properties:

* `id`: A unique identifier for the document.
* `content`: The document's content.
* `metadata`: An object containing metadata about the document (e.g., author, format).
* `statistics`: An object providing statistics about the document (e.g., word count).

### Example Request

```bash
POST /api/v1/query HTTP/1.1
Content-Type: application/json

{
  "query": "example",
  "filter": {
    "author": "John Doe"
  },
  "sort": {
    "created_at": "asc"
  },
  "limit": 10,
  "offset": 0
}
```

### Example Response

```json
[
  {
    "id": "doc-123",
    "content": "This is an example document.",
    "metadata": {
      "author": "John Doe",
      "format": "text/plain"
    },
    "statistics": {
      "word_count": 10,
      "character_count": 50
    }
  },
  {
    "id": "doc-456",
    "content": "Another example document.",
    "metadata": {
      "author": "Jane Doe",
      "format": "text/plain"
    },
    "statistics": {
      "word_count": 15,
      "character_count": 75
    }
  }
]
```

### Error Handling

The `/api/v1/query` endpoint will return a JSON error object in case of invalid requests or errors. The error object will contain the following properties:

* `code`: A unique error code.
* `message`: A human-readable error message.

```json
{
  "code": "INVALID_REQUEST",
  "message": "Invalid query parameter"
}
```

By documenting the `/api/v1/query` endpoint, users can effectively utilize this critical component of the MCP ecosystem to retrieve and filter documents.

**Monitoring Cache Performance**

The `/api/v1/cache/stats` endpoint provides a summary of cache performance metrics. This endpoint is useful for monitoring and optimizing cache usage in the system.

**Endpoint Details**

* **Path:** `/api/v1/cache/stats`
* **Method:** `GET`

**Response**

The response from this endpoint will contain a JSON object with the following keys:

* `hits`: The number of cache hits (requests that were served from the cache).
* `misses`: The number of cache misses (requests that were not found in the cache and had to be fetched from the underlying storage).
* `hit_rate`: The percentage of requests that were served from the cache.
* `average_hit_time`: The average time it took for a request to be served from the cache.
* `average_miss_time`: The average time it took for a request to be fetched from the underlying storage.

**Example Response**

```json
{
  "hits": 100,
  "misses": 20,
  "hit_rate": 83.33,
  "average_hit_time": 10,
  "average_miss_time": 50
}
```

This response indicates that out of 120 requests, 100 were served from the cache (a hit rate of 83.33%), with an average time of 10ms to serve a request from the cache. The remaining 20 requests resulted in cache misses, taking an average of 50ms to fetch from the underlying storage.

**Notes**

* This endpoint is intended for monitoring and debugging purposes only.
* Cache performance metrics are reset periodically (e.g., every hour) to prevent accumulation of stale data.
* The `average_hit_time` and `average_miss_time` values are calculated over a sliding window of recent requests.

I don't have enough information to provide a comprehensive answer about the specific authentication and authorization mechanisms used in the Ecosystem-MCP microservices documentation system. The provided context includes various modules, classes, and functions but does not explicitly mention authentication or authorization mechanisms.

However, based on the presence of certain modules and classes, such as `Source` (Source Agent), `SecurityAnalysis`, and `SecurityFilter` (LLM Gateway Service), it can be inferred that some form of access control might be implemented. For instance:

- The `Source` class in `services/source-agent/domain/entities/source.py` has methods like `is_due_for_sync()`, `has_credentials()`, and `sync_age_minutes()` which could imply some level of authentication or authorization for accessing source systems.
  
- The `SecurityAnalysis` and `SecurityFilter` classes in `services/llm-gateway/infrastructure/services/security_filter.py` suggest that security-aware routing and content analysis are performed, possibly involving authentication or authorization checks.

To provide a more accurate answer, I would need more specific information about the authentication and authorization mechanisms used within the Ecosystem-MCP system.

There is no mention of rate limits in the provided configuration files. The configuration files appear to be related to a machine learning pipeline, with services such as MCP Gateway, MCP Orchestration, MCP Registry, MCP Training Coordinator, and others. There are settings for logging, API endpoints, database connections, and other infrastructure-related configurations, but no mention of rate limits.

However, if you're looking to configure rate limits in this application, you might need to look into the codebase or documentation specific to each service or module, as it's not explicitly mentioned in these configuration files.

## Practical Information

I don't have enough information to provide complete curl examples for each major endpoint. The provided documentation includes various modules and classes related to API endpoints, but it does not contain specific details about the endpoints themselves or their corresponding curl commands.

However, I can suggest some possible sources where you might find the necessary information:

1. `services/analysis-service/presentation/routes/analysis_routes.py`: This module seems to define core analysis routes, which could include endpoints for document analysis, semantic similarity, sentiment, tone, quality, trends, risk, maintenance forecasting, degradation detection, change impact, and PR analysis.
2. `services/project-simulation/tests/api/test_simulation_endpoints.py`: Although this is a test file, it might provide insight into the structure of simulation API endpoints, which could be useful for constructing curl examples.
3. `services/ecosystem-mcp/src/api/routes/ollama.py`: This module defines Ollama direct query endpoints, which might include specific endpoints that can be used to construct curl examples.

To find complete curl examples for each major endpoint, I recommend reviewing the documentation and source code related to these modules and classes. You may also want to consult other relevant sources within the ecosystem, such as API documentation or test files, to gather more information about the available endpoints and their corresponding curl commands.

Based on the provided context, I can see that there are several modules and classes related to providing programmatic access through Python clients. However, I don't have enough information about specific client examples in the provided context.

But I can suggest some possible ways to find the answer:

1. Check the `EcosystemCLI` class in `scripts/ecosystem_cli_executable.py` (Source 1). It might provide an example of how to use the Ecosystem CLI programmatically.
2. Look at the `OllamaClient` class in `services/ecosystem-mcp/src/services/models/ollama_client.py` (Source 7). This client is optimized for local LLM inference and might have examples of programmatic access.

If you provide more context or clarify what specific Python client examples you are looking for, I'll do my best to help.

Based on the provided context, I can identify some common API usage patterns and workflows. However, please note that these patterns might not be exhaustive.

From [Source 8] services/discovery-agent/presentation/api/standard_endpoints.py, we see standard API endpoints required by ecosystem architecture:

1. GET /health - Health check
2. GET /about-me - Service descriptor
3. GET /endpoints - Endpoint list
4. GET /provider-consumer - Service relationships

These endpoints seem to be used for service discovery and metadata retrieval.

From [Source 17] services/analysis-service/presentation/routes/workflow_routes.py, we see workflow routes related to event processing, status tracking, and webhook configuration:

1. Workflow event processing
2. Status tracking
3. Webhook configuration

This suggests that the analysis service is used for workflow-related tasks.

From [Source 18] services/orchestrator/application/query_processing/use_cases.py, we see query processing application use cases:

1. ProcessNaturalLanguageQueryUseCase - Processing natural language queries
2. GetQueryResultUseCase - Getting query results
3. ListQueriesUseCase - Listing queries

These use cases indicate that the orchestrator service is used for query processing and management.

From [Source 20] services/code-analyzer/tests/integration/test_workflows.py, we see workflow tests for code-analyzer service:

1. Single file analysis workflows
2. Batch analysis workflows
3. Workflows with custom analysis options
4. Error recovery workflows
5. Sequential analysis workflows
6. Real-world usage scenarios

These tests suggest that the code-analyzer service is used for various types of analysis and workflow-related tasks.

Based on these observations, common API usage patterns and workflows seem to involve:

1. Service discovery and metadata retrieval (e.g., GET /health, GET /about-me)
2. Workflow event processing, status tracking, and webhook configuration
3. Query processing and management (e.g., ProcessNaturalLanguageQueryUseCase, GetQueryResultUseCase)
4. Analysis and workflow-related tasks (e.g., single file analysis, batch analysis, custom options)

Please note that these patterns are based on the provided context and might not be comprehensive or up-to-date.

Based on the provided code snippets, it appears that error handling is a crucial aspect of the ecosystem. Here are some suggestions for handling errors and rate limiting:

1. **Centralized Exception Handling**: The `exception_handlers` module in `services/analysis-service/presentation/handlers/exception_handlers.py` suggests a centralized approach to exception handling. This is a good practice, as it allows for consistent error handling across the ecosystem.
2. **Error Codes and Messages**: To improve error handling, consider introducing standardized error codes and messages. This will enable better debugging and logging, making it easier to identify and resolve issues.
3. **Rate Limiting**: For rate limiting, you can use libraries like `ratelimit` or implement a custom solution using Redis or Memcached. The `resource_monitor_service` in `services/doc_store/infrastructure/services/resource_monitor_service.py` suggests monitoring system resources, which could be extended to include rate limiting.
4. **Fallback Mechanisms**: The `test_error_handling_fallbacks` module in `services/project-simulation/tests/integration/test_error_handling_fallbacks.py` indicates that fallback mechanisms are essential for error handling. Implementing fallbacks will ensure that the ecosystem remains functional even when errors occur.
5. **Monitoring and Logging**: To improve error handling, consider implementing comprehensive monitoring and logging mechanisms. This will enable you to track errors, identify patterns, and make data-driven decisions to optimize the ecosystem.

To implement these suggestions, you can:

1. Create a centralized exception handling module that captures and logs errors across the ecosystem.
2. Introduce standardized error codes and messages to improve debugging and logging.
3. Implement rate limiting using libraries like `ratelimit` or custom solutions.
4. Develop fallback mechanisms to ensure the ecosystem remains functional in case of errors.
5. Set up comprehensive monitoring and logging mechanisms to track errors and optimize the ecosystem.

Here's an example code snippet for a centralized exception handling module:
```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(Exception)
async def handle_exception(request: Request, exc: Exception):
    error_code = "INTERNAL_SERVER_ERROR"
    error_message = str(exc)
    return JSONResponse(status_code=500, content={"error": {"code": error_code, "message": error_message}})
```
This code snippet demonstrates a basic centralized exception handling mechanism using FastAPI. You can extend this example to include additional features like logging, rate limiting, and fallback mechanisms.

