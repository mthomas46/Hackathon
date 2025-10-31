# Ecosystem MCP API Examples

**Date:** October 28, 2025  
**Version:** 1.0  
**Base URL:** `http://localhost:8002`

## Table of Contents

1. [Authentication](#authentication)
2. [Health & Status](#health--status)
3. [Ingestion](#ingestion)
4. [RAG Queries](#rag-queries)
5. [Temporal RAG](#temporal-rag)
6. [Context-Aware RAG](#context-aware-rag)
7. [Document Management](#document-management)
8. [Timelines](#timelines)
9. [Admin Operations](#admin-operations)

---

## Authentication

Currently no authentication required. All endpoints are open.

---

## Health & Status

### Check Service Health

```bash
curl http://localhost:8002/health
```

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-10-28T10:00:00Z",
  "database": "connected",
  "chromadb": "connected",
  "ollama": "connected"
}
```

**Python**:
```python
import requests

response = requests.get("http://localhost:8002/health")
print(response.json())
```

---

### Get Service Status

```bash
curl http://localhost:8002/api/v1/status
```

**Response**:
```json
{
  "service": "ecosystem-mcp",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "documents_count": 1234,
  "jobs_count": 56,
  "cache_hit_rate": 0.75
}
```

---

## Ingestion

### Start Snapshot Ingestion

```bash
curl -X POST http://localhost:8002/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "repo_path": "/path/to/repo",
    "mode": "snapshot"
  }'
```

**Response**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "created_at": "2025-10-28T10:00:00Z"
}
```

**Python**:
```python
import requests

response = requests.post(
    "http://localhost:8002/api/v1/ingest",
    json={
        "repo_path": "/path/to/repo",
        "mode": "snapshot"
    }
)
print(f"Job ID: {response.json()['job_id']}")
```

---

### Start Enriched Ingestion (with Git metadata)

```bash
curl -X POST http://localhost:8002/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "repo_path": "/path/to/repo",
    "mode": "enriched"
  }'
```

---

### Start Full Git History Ingestion

```bash
curl -X POST http://localhost:8002/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "repo_path": "/path/to/repo",
    "mode": "full",
    "max_commits": 100
  }'
```

---

### Check Job Status

```bash
curl http://localhost:8002/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000
```

**Response**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "mode": "snapshot",
  "progress": {
    "processed": 100,
    "total": 100,
    "percentage": 100.0
  },
  "stats": {
    "documents_processed": 95,
    "documents_skipped": 5,
    "embeddings_generated": 95,
    "failures": 0
  },
  "created_at": "2025-10-28T10:00:00Z",
  "completed_at": "2025-10-28T10:05:00Z",
  "duration_seconds": 300
}
```

---

## RAG Queries

### Basic RAG Query

```bash
curl -X POST http://localhost:8002/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the ingestion pipeline architecture?",
    "n_results": 10
  }'
```

**Response**:
```json
{
  "question": "What is the ingestion pipeline architecture?",
  "answer": "The ingestion pipeline consists of multiple stages...",
  "documents": [
    {
      "content": "Pipeline stage 1: File discovery...",
      "metadata": {
        "file_path": "/src/services/ingestion/pipeline.py",
        "repo_path": "/path/to/repo"
      },
      "similarity": 0.92
    }
  ],
  "metadata": {
    "model": "llama3",
    "total_documents": 10,
    "processing_time_ms": 250
  }
}
```

**Python**:
```python
import requests

response = requests.post(
    "http://localhost:8002/api/v1/query",
    json={
        "question": "What is the ingestion pipeline architecture?",
        "n_results": 10
    }
)

result = response.json()
print(f"Answer: {result['answer']}")
print(f"Found {len(result['documents'])} documents")
```

---

### RAG Query with Response Length

```bash
curl -X POST http://localhost:8002/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Explain the RAG implementation",
    "n_results": 20,
    "response_length": 800
  }'
```

---

### Enhanced RAG Query (with keywords & focus)

```bash
curl -X POST http://localhost:8002/api/v1/query/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How does error handling work?",
    "n_results": 15,
    "keywords": ["retry", "circuit breaker", "timeout"],
    "focus_areas": ["src/services/ingestion"]
  }'
```

---

### Multi-Pass RAG Query (Deep Research)

```bash
curl -X POST http://localhost:8002/api/v1/query/multi-pass \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Comprehensive overview of the codebase",
    "num_sections": 5,
    "questions_per_section": 5,
    "docs_per_section": 20,
    "temperature": 0.7,
    "response_length": 1000
  }'
```

**Response**:
```json
{
  "question": "Comprehensive overview of the codebase",
  "final_answer": "This codebase implements a comprehensive RAG system...",
  "sections": [
    {
      "title": "Architecture Overview",
      "content": "The system is structured into...",
      "questions_explored": [
        "What is the overall architecture?",
        "How are components organized?"
      ],
      "documents_used": 20
    }
  ],
  "metadata": {
    "total_sections": 5,
    "total_documents": 100,
    "total_questions": 25,
    "processing_time_ms": 15000
  }
}
```

---

## Temporal RAG

### Query Within Date Range

```bash
curl -X POST http://localhost:8002/api/v1/temporal/query/date-range \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What testing was implemented?",
    "start_date": "2025-01-01T00:00:00Z",
    "end_date": "2025-10-28T23:59:59Z",
    "n_results": 10
  }'
```

**Response**:
```json
{
  "question": "What testing was implemented?",
  "answer": "During this period, comprehensive testing was added...",
  "date_range": {
    "start": "2025-01-01T00:00:00Z",
    "end": "2025-10-28T23:59:59Z"
  },
  "documents": [
    {
      "content": "Added unit tests for ingestion pipeline...",
      "metadata": {
        "git_date": "2025-03-15T10:00:00Z",
        "file_path": "/tests/test_ingestion.py"
      },
      "similarity": 0.89
    }
  ],
  "temporal_confidence": 0.95
}
```

---

### Point-in-Time Query

```bash
curl -X POST http://localhost:8002/api/v1/temporal/query/point-in-time \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What was the state of the RAG system?",
    "timestamp": "2025-06-01T00:00:00Z",
    "n_results": 10
  }'
```

---

### Evolution Tracking Query

```bash
curl -X POST http://localhost:8002/api/v1/temporal/query/evolution \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How did error handling evolve?",
    "start_date": "2025-01-01T00:00:00Z",
    "end_date": "2025-10-28T23:59:59Z",
    "n_results": 10
  }'
```

**Response**:
```json
{
  "question": "How did error handling evolve?",
  "evolution_summary": "Error handling evolved from basic try/catch to sophisticated circuit breakers...",
  "phases": [
    {
      "period": "2025-01-01 to 2025-03-31",
      "description": "Basic error handling with retries",
      "key_changes": ["Added retry logic", "Implemented exponential backoff"],
      "document_count": 5
    },
    {
      "period": "2025-04-01 to 2025-06-30",
      "description": "Circuit breakers introduced",
      "key_changes": ["Added CircuitBreaker class", "Integrated with services"],
      "document_count": 8
    }
  ],
  "temporal_confidence": 0.92
}
```

---

## Context-Aware RAG

### Query with File Context

```bash
curl -X POST http://localhost:8002/api/v1/query/context-aware \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How does this file handle errors?",
    "context": {
      "file_path": "/src/services/ingestion/job_processor.py",
      "recent_changes": ["Added retry mechanism", "Improved logging"]
    },
    "n_results": 10
  }'
```

---

## Document Management

### List All Documents

```bash
curl http://localhost:8002/api/v1/documents?limit=10&offset=0
```

**Response**:
```json
{
  "documents": [
    {
      "id": "doc-123",
      "file_path": "/src/api/app.py",
      "repo_path": "/path/to/repo",
      "content_hash": "abc123...",
      "created_at": "2025-10-28T10:00:00Z",
      "git_date": "2025-10-27T15:30:00Z"
    }
  ],
  "total": 1234,
  "limit": 10,
  "offset": 0
}
```

---

### Get Document by ID

```bash
curl http://localhost:8002/api/v1/documents/doc-123
```

---

### Search Documents

```bash
curl -X POST http://localhost:8002/api/v1/documents/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "error handling",
    "n_results": 10,
    "filters": {
      "file_extension": ".py"
    }
  }'
```

---

## Timelines

### Create Timeline

```bash
curl -X POST http://localhost:8002/api/v1/timelines \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Main Development Timeline",
    "description": "Primary development branch timeline",
    "start_date": "2025-01-01T00:00:00Z",
    "end_date": "2025-12-31T23:59:59Z"
  }'
```

**Response**:
```json
{
  "timeline_id": "timeline-456",
  "name": "Main Development Timeline",
  "created_at": "2025-10-28T10:00:00Z"
}
```

---

### List Timelines

```bash
curl http://localhost:8002/api/v1/timelines
```

---

### Get Timeline Details

```bash
curl http://localhost:8002/api/v1/timelines/timeline-456
```

---

### Query Timeline

```bash
curl -X POST http://localhost:8002/api/v1/timelines/timeline-456/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What features were added?",
    "n_results": 10
  }'
```

---

## Admin Operations

### Get System Metrics

```bash
curl http://localhost:8002/api/v1/admin/metrics
```

**Response**:
```json
{
  "database": {
    "total_documents": 1234,
    "total_jobs": 56,
    "active_jobs": 2
  },
  "chromadb": {
    "total_embeddings": 1234,
    "collection_count": 3
  },
  "cache": {
    "hit_rate": 0.75,
    "size_mb": 128
  },
  "performance": {
    "avg_query_time_ms": 250,
    "avg_ingestion_time_s": 300
  }
}
```

---

### List All Jobs

```bash
curl http://localhost:8002/api/v1/admin/jobs?limit=20&status=completed
```

---

### Cancel Job

```bash
curl -X POST http://localhost:8002/api/v1/admin/jobs/550e8400-e29b-41d4-a716-446655440000/cancel
```

---

### Clear Cache

```bash
curl -X POST http://localhost:8002/api/v1/admin/cache/clear
```

---

### Rebuild Search Index

```bash
curl -X POST http://localhost:8002/api/v1/admin/index/rebuild
```

**Response**:
```json
{
  "status": "started",
  "job_id": "rebuild-789",
  "estimated_duration_minutes": 30
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "success": false,
  "error": "Error message description",
  "error_code": "ERROR_CODE",
  "status_code": 400,
  "details": {
    "field": "field_name",
    "message": "Specific field error"
  }
}
```

**Common Error Codes**:
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (resource doesn't exist)
- `422` - Validation Error (invalid data format)
- `500` - Internal Server Error
- `503` - Service Unavailable

---

## Rate Limiting

**Current Limits**:
- 100 requests per minute per IP
- 1000 requests per hour per IP

**Rate Limit Headers**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1635360000
```

---

## Python SDK Example

Complete example using the Python `requests` library:

```python
import requests
from typing import Dict, Any

class EcosystemMCPClient:
    """Simple client for Ecosystem MCP API."""
    
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health(self) -> Dict[str, Any]:
        """Check service health."""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def start_ingestion(
        self,
        repo_path: str,
        mode: str = "snapshot",
        max_commits: int = None
    ) -> str:
        """Start ingestion job and return job_id."""
        payload = {"repo_path": repo_path, "mode": mode}
        if max_commits:
            payload["max_commits"] = max_commits
        
        response = self.session.post(
            f"{self.base_url}/api/v1/ingest",
            json=payload
        )
        response.raise_for_status()
        return response.json()["job_id"]
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get job status."""
        response = self.session.get(
            f"{self.base_url}/api/v1/jobs/{job_id}"
        )
        response.raise_for_status()
        return response.json()
    
    def query(
        self,
        question: str,
        n_results: int = 10,
        response_length: int = None
    ) -> Dict[str, Any]:
        """Execute RAG query."""
        payload = {"question": question, "n_results": n_results}
        if response_length:
            payload["response_length"] = response_length
        
        response = self.session.post(
            f"{self.base_url}/api/v1/query",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def temporal_query(
        self,
        question: str,
        start_date: str,
        end_date: str,
        n_results: int = 10
    ) -> Dict[str, Any]:
        """Execute temporal RAG query."""
        response = self.session.post(
            f"{self.base_url}/api/v1/temporal/query/date-range",
            json={
                "question": question,
                "start_date": start_date,
                "end_date": end_date,
                "n_results": n_results
            }
        )
        response.raise_for_status()
        return response.json()


# Usage example
if __name__ == "__main__":
    client = EcosystemMCPClient()
    
    # Check health
    health = client.health()
    print(f"Service status: {health['status']}")
    
    # Start ingestion
    job_id = client.start_ingestion(
        repo_path="/path/to/repo",
        mode="enriched"
    )
    print(f"Started ingestion job: {job_id}")
    
    # Wait for completion (poll status)
    import time
    while True:
        status = client.get_job_status(job_id)
        print(f"Job status: {status['status']}")
        
        if status['status'] in ['completed', 'failed']:
            break
        
        time.sleep(5)
    
    # Query the ingested documents
    result = client.query(
        question="What is the main purpose of this codebase?",
        n_results=10,
        response_length=500
    )
    print(f"Answer: {result['answer']}")
```

---

## WebSocket Examples (Future)

WebSocket support for real-time updates is planned:

```javascript
// Future feature
const ws = new WebSocket('ws://localhost:8002/ws/jobs/550e8400-e29b-41d4-a716-446655440000');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log(`Progress: ${update.progress}%`);
};
```

---

## More Examples

For more examples and use cases, see:
- [User Guide](../guides/USER_GUIDE.md)
- [Integration Guide](../guides/INTEGRATION_GUIDE.md)
- [API Reference](./API_REFERENCE.md)

---

**Last Updated:** October 28, 2025  
**Version:** 1.0  
**Feedback:** [GitHub Issues](https://github.com/your-org/ecosystem-mcp/issues)

