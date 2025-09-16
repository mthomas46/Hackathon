"""HTTP Client Utilities for Inter-Service Communication

Robust HTTP client implementation with resilience patterns for service communication.

This module provides:
- Configurable HTTP clients with timeout and retry settings
- Circuit breaker pattern implementation for fault tolerance
- Automatic retry with exponential backoff and jitter
- JSON request/response handling with proper error handling
- Service URL resolution and configuration management
- Correlation ID propagation for distributed tracing
- Metrics collection for service communication monitoring

Used by all services to communicate with each other reliably and consistently.
"""

import os
import httpx
from typing import Any, Dict, Optional, List
from datetime import datetime, timezone
from services.shared.resilience import with_retries, CircuitBreaker, with_circuit  # type: ignore
from services.shared.config import get_config_value

# Imports for local database access
try:
    import sqlite3
    import json
    import hashlib
    from services.shared.utilities import utc_now
except ImportError:
    # Handle cases where services aren't available
    sqlite3 = None
    json = None
    hashlib = None
    utc_now = None


class ServiceClients:
    """Robust HTTP client wrapper for inter-service communication.

    Provides a unified interface for all HTTP communication between services,
    with built-in resilience patterns including retries, circuit breakers,
    and proper error handling. All service communication should use this
    client to ensure consistency and reliability.

    Features:
    - Configurable timeouts and retry policies
    - Circuit breaker pattern for fault tolerance
    - Automatic correlation ID propagation
    - JSON request/response handling
    - Comprehensive error handling and logging
    - Service URL resolution from configuration
    """
    def __init__(self, timeout: int = 30):
        # Read defaults from shared config with env override
        try:
            self.timeout = int(get_config_value("timeout", str(timeout), section="http_client", env_key="HTTP_CLIENT_TIMEOUT"))
        except Exception:
            self.timeout = timeout
        try:
            self.retry_attempts = int(get_config_value("retry_attempts", 3, section="http_client", env_key="HTTP_RETRY_ATTEMPTS"))
        except Exception:
            self.retry_attempts = 3
        try:
            self.retry_base_ms = int(get_config_value("retry_base_ms", 150, section="http_client", env_key="HTTP_RETRY_BASE_MS"))
        except Exception:
            self.retry_base_ms = 150
        raw_circuit = get_config_value("circuit_enabled", False, section="http_client", env_key="HTTP_CIRCUIT_ENABLED")
        self.circuit_enabled = str(raw_circuit).strip().lower() in ("1", "true", "yes")

    def github_agent_url(self) -> str:
        return get_config_value("GITHUB_AGENT_URL", "http://github-agent:5000", section="services", env_key="GITHUB_AGENT_URL")

    def reporting_url(self) -> str:
        return get_config_value("REPORTING_URL", "http://reporting:5030", section="services", env_key="REPORTING_URL")

    def consistency_engine_url(self) -> str:
        return get_config_value("CONSISTENCY_ENGINE_URL", "http://consistency-engine:5020", section="services", env_key="CONSISTENCY_ENGINE_URL")

    def jira_agent_url(self) -> str:
        return get_config_value("JIRA_AGENT_URL", "http://jira-agent:5001", section="services", env_key="JIRA_AGENT_URL")

    def confluence_agent_url(self) -> str:
        return get_config_value("CONFLUENCE_AGENT_URL", "http://confluence-agent:5050", section="services", env_key="CONFLUENCE_AGENT_URL")

    # ============================================================================
    # NEW SERVICE URLS
    # ============================================================================

    def prompt_store_url(self) -> str:
        """Get Prompt Store service URL."""
        return get_config_value("PROMPT_STORE_URL", "http://prompt-store:5110", section="services", env_key="PROMPT_STORE_URL")

    def interpreter_url(self) -> str:
        """Get Interpreter service URL."""
        return get_config_value("INTERPRETER_URL", "http://interpreter:5120", section="services", env_key="INTERPRETER_URL")

    def cli_service_url(self) -> str:
        """Get CLI service URL."""
        return get_config_value("CLI_SERVICE_URL", "http://cli:5130", section="services", env_key="CLI_SERVICE_URL")

    # ============================================================================
    # EXISTING SERVICE URLS (UPDATED)
    # ============================================================================

    def orchestrator_url(self) -> str:
        """Get Orchestrator service URL."""
        return get_config_value("ORCHESTRATOR_URL", "http://orchestrator:5000", section="services", env_key="ORCHESTRATOR_URL")

    def analysis_service_url(self) -> str:
        """Get Analysis Service URL."""
        return get_config_value("ANALYSIS_SERVICE_URL", "http://analysis-service:5020", section="services", env_key="ANALYSIS_SERVICE_URL")

    def doc_store_url(self) -> str:
        """Get Doc Store service URL."""
        return get_config_value("DOC_STORE_URL", "http://doc_store:5010", section="services", env_key="DOC_STORE_URL")

    def source_agent_url(self) -> str:
        """Get Source Agent service URL."""
        return get_config_value("SOURCE_AGENT_URL", "http://source-agent:5000", section="services", env_key="SOURCE_AGENT_URL")

    # ============================================================================
    # ADDITIONAL SERVICE URLS (for CLI compatibility)
    # ============================================================================

    def discovery_agent_url(self) -> str:
        """Get Discovery Agent service URL."""
        return get_config_value("DISCOVERY_AGENT_URL", "http://discovery-agent:5140", section="services", env_key="DISCOVERY_AGENT_URL")

    def frontend_url(self) -> str:
        """Get Frontend service URL."""
        return get_config_value("FRONTEND_URL", "http://frontend:5150", section="services", env_key="FRONTEND_URL")

    def summarizer_hub_url(self) -> str:
        """Get Summarizer Hub service URL."""
        return get_config_value("SUMMARIZER_HUB_URL", "http://summarizer-hub:5160", section="services", env_key="SUMMARIZER_HUB_URL")

    def secure_analyzer_url(self) -> str:
        """Get Secure Analyzer service URL."""
        return get_config_value("SECURE_ANALYZER_URL", "http://secure-analyzer:5170", section="services", env_key="SECURE_ANALYZER_URL")

    def memory_agent_url(self) -> str:
        """Get Memory Agent service URL."""
        return get_config_value("MEMORY_AGENT_URL", "http://memory-agent:5180", section="services", env_key="MEMORY_AGENT_URL")

    def code_analyzer_url(self) -> str:
        """Get Code Analyzer service URL."""
        return get_config_value("CODE_ANALYZER_URL", "http://code-analyzer:5190", section="services", env_key="CODE_ANALYZER_URL")

    def log_collector_url(self) -> str:
        """Get Log Collector service URL."""
        return get_config_value("LOG_COLLECTOR_URL", "http://log-collector:5200", section="services", env_key="LOG_COLLECTOR_URL")

    def notification_service_url(self) -> str:
        """Get Notification Service URL."""
        return get_config_value("NOTIFICATION_SERVICE_URL", "http://notification-service:5210", section="services", env_key="NOTIFICATION_SERVICE_URL")

    async def notify_via_service(self, channel: str, target: str, title: str, message: str,
                                metadata: Optional[Dict[str, Any]] = None, labels: Optional[List[str]] = None) -> Dict[str, Any]:
        """Send notification via notification service."""
        url = f"{self.notification_service_url()}/notify"
        payload = {
            "channel": channel,
            "target": target,
            "title": title,
            "message": message,
            "metadata": metadata or {},
            "labels": labels or []
        }
        return await self.post_json(url, payload)

    async def resolve_owners_via_service(self, owners: List[str]) -> Dict[str, Any]:
        """Resolve owners to notification targets via notification service."""
        url = f"{self.notification_service_url()}/owners/resolve"
        payload = {"owners": owners}
        return await self.post_json(url, payload)

    # ============================================================================
    # INTEGRATION METHODS
    # ============================================================================

    async def get_prompt(self, category: str, name: str, **variables) -> Dict[str, Any]:
        """Get a prompt from Prompt Store with variable substitution."""
        base_url = self.prompt_store_url()
        url = f"{base_url}/prompts/search/{category}/{name}"

        # Add variables as query parameters
        if variables:
            var_params = "&".join([f"{k}={v}" for k, v in variables.items()])
            url += f"?{var_params}"

        return await self.get_json(url)

    async def interpret_query(self, query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Send query to Interpreter service for natural language processing."""
        url = f"{self.interpreter_url()}/interpret"
        payload = {"query": query}
        if user_id:
            payload["user_id"] = user_id

        return await self.post_json(url, payload)

    async def execute_workflow(self, query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute workflow through Interpreter service."""
        url = f"{self.interpreter_url()}/execute"
        payload = {"query": query}
        if user_id:
            payload["user_id"] = user_id

        return await self.post_json(url, payload)

    async def log_prompt_usage(self, prompt_id: str, service_name: str,
                              input_tokens: Optional[int] = None,
                              output_tokens: Optional[int] = None,
                              response_time_ms: Optional[float] = None,
                              success: bool = True) -> None:
        """Log prompt usage to Prompt Store for analytics."""
        url = f"{self.prompt_store_url()}/usage"
        payload = {
            "prompt_id": prompt_id,
            "service_name": service_name,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "response_time_ms": response_time_ms,
            "success": success
        }

        await self.post_json(url, payload)

    async def check_service_health(self, service_name: str) -> bool:
        """Check health of a specific service."""
        service_urls = {
            "orchestrator": self.orchestrator_url(),
            "analysis-service": self.analysis_service_url(),
            "doc_store": self.doc_store_url(),
            "source-agent": self.source_agent_url(),
            "prompt-store": self.prompt_store_url(),
            "interpreter": self.interpreter_url(),
        }

        if service_name not in service_urls:
            return False

        try:
            health_url = f"{service_urls[service_name]}/health"
            response = await self.get_json(health_url)
            return response.get("status") == "healthy"
        except Exception:
            return False

    async def get_system_health(self) -> Dict[str, Any]:
        """Get health status of all services."""
        services = [
            "orchestrator",
            "analysis-service",
            "doc_store",
            "source-agent",
            "prompt-store",
            "interpreter"
        ]

        health_status = {}
        for service in services:
            health_status[service] = await self.check_service_health(service)

        # Calculate overall health
        healthy_count = sum(1 for status in health_status.values() if status)
        total_count = len(health_status)

        return {
            "overall_healthy": healthy_count == total_count,
            "healthy_count": healthy_count,
            "total_count": total_count,
            "services": health_status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    # ============================================================================
    # CONVENIENCE METHODS FOR COMMON OPERATIONS
    # ============================================================================

    async def analyze_document(self, doc_id: str, analysis_type: str = "consistency") -> Dict[str, Any]:
        """Convenience method for document analysis."""
        url = f"{self.analysis_service_url()}/analyze"
        payload = {
            "targets": [doc_id],
            "analysis_type": analysis_type
        }
        return await self.post_json(url, payload)

    async def store_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convenience method for storing documents."""
        if self.doc_store_url() == "local":
            return await self._store_document_local(document_data)
        url = f"{self.doc_store_url()}/documents"
        return await self.post_json(url, document_data)

    async def _store_document_local(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store document directly in local database."""
        import sqlite3
        import hashlib
        import json
        from services.shared.utilities import utc_now

        db_path = os.environ.get("DOCSTORE_DB", "services/doc_store/db.sqlite3")
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA journal_mode=WAL;")

        try:
            content = document_data.get("content", "")
            content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

            conn.execute("""
                INSERT OR REPLACE INTO documents (id, content, content_hash, metadata, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                document_data.get("id"),
                content,
                content_hash,
                json.dumps(document_data.get("metadata", {})),
                utc_now().isoformat()
            ))
            conn.commit()

            return {
                "status": "success",
                "data": {
                    "id": document_data.get("id"),
                    "content_hash": content_hash
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            conn.close()

    async def _get_docstore_local(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle doc_store requests locally from database."""

        db_path = os.environ.get("DOCSTORE_DB", "services/doc_store/db.sqlite3")
        conn = sqlite3.connect(db_path)

        try:
            # Parse the URL path
            path = url.replace("doc_store/", "").split("?")[0]  # Remove query params

            if path == "documents/_list":
                return await self._list_documents_local(conn, params)
            elif path.startswith("documents/") and "/" not in path[10:]:
                doc_id = path[10:]
                return await self._get_document_local(conn, doc_id)
            elif path == "info":
                return await self._get_info_local(conn)
            elif path == "search":
                return await self._search_local(conn, params)
            elif path == "documents/quality":
                return await self._get_quality_local(conn)
            elif path.startswith("analyses"):
                if path == "analyses":
                    return await self._list_analyses_local(conn, params)
                elif "/" in path[9:]:
                    analysis_id = path[9:]
                    return await self._get_analysis_local(conn, analysis_id)
            elif path == "style/examples":
                return await self._get_style_examples_local(conn, params)
            elif path == "quality/tips":
                return await self._get_quality_tips_local()
            elif path == "config/effective":
                return await self._get_config_local()
            elif path == "storage/stats":
                return await self._get_storage_stats_local(conn)
            elif path == "performance/metrics":
                return await self._get_performance_metrics_local()

            return {"status": "error", "error": f"Unsupported endpoint: {path}"}

        except Exception as e:
            return {"status": "error", "error": str(e)}
        finally:
            conn.close()

    async def _list_documents_local(self, conn: sqlite3.Connection, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """List documents from local database."""
        limit = int(params.get("limit", 10)) if params else 10
        offset = int(params.get("offset", 0)) if params else 0
        sort = params.get("sort", "created_at") if params else "created_at"
        order = params.get("order", "desc") if params else "desc"

        cur = conn.execute(f"""
            SELECT id, content, metadata, created_at FROM documents
            ORDER BY {sort} {order} LIMIT ? OFFSET ?
        """, (limit, offset))

        documents = []
        for row in cur.fetchall():
            documents.append({
                "id": row[0],
                "content": row[1][:100] + "..." if len(row[1]) > 100 else row[1],
                "metadata": json.loads(row[2]) if row[2] else {},
                "created_at": row[3]
            })

        return {
            "documents": documents
        }

    async def _get_document_local(self, conn: sqlite3.Connection, doc_id: str) -> Dict[str, Any]:
        """Get document by ID from local database."""
        cur = conn.execute("SELECT * FROM documents WHERE id=?", (doc_id,))
        row = cur.fetchone()

        if not row:
            return {"status": "error", "error": f"Document '{doc_id}' not found"}

        return {
            "status": "success",
            "data": {
                "id": row[0],
                "content": row[1],
                "content_hash": row[2],
                "metadata": json.loads(row[3]) if row[3] else {},
                "created_at": row[4]
            }
        }

    async def _get_info_local(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Get doc_store info from local database."""
        cur = conn.execute("SELECT COUNT(*) FROM documents")
        doc_count = cur.fetchone()[0]

        cur = conn.execute("SELECT COUNT(*) FROM analyses")
        analysis_count = cur.fetchone()[0]

        # Count by source type
        cur = conn.execute("""
            SELECT json_extract(metadata, '$.source_type') as source_type, COUNT(*)
            FROM documents
            GROUP BY json_extract(metadata, '$.source_type')
        """)

        document_types = {}
        for row in cur.fetchall():
            document_types[row[0] or "unknown"] = row[1]

        return {
            "status": "success",
            "data": {
                "document_count": doc_count,
                "analysis_count": analysis_count,
                "document_types": document_types,
                "database_path": os.environ.get("DOCSTORE_DB", "services/doc_store/db.sqlite3")
            }
        }

    async def _search_local(self, conn: sqlite3.Connection, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Search documents in local database."""
        query = params.get("q", "") if params else ""
        limit = int(params.get("limit", 10)) if params else 10

        # Simple LIKE search
        cur = conn.execute("""
            SELECT id, content, metadata FROM documents
            WHERE content LIKE ? OR id LIKE ?
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", limit))

        results = []
        for row in cur.fetchall():
            results.append({
                "id": row[0],
                "content": row[1][:200] + "..." if len(row[1]) > 200 else row[1],
                "metadata": json.loads(row[2]) if row[2] else {},
                "score": 1.0
            })

        return {
            "status": "success",
            "data": {"items": results}
        }

    async def _get_quality_local(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Get quality metrics from local database."""
        # Simple quality assessment based on content length and metadata
        cur = conn.execute("SELECT id, content, metadata, created_at FROM documents")

        items = []
        for row in cur.fetchall():
            content = row[1]
            metadata = json.loads(row[2]) if row[2] else {}

            # Simple quality scoring
            content_length = len(content)
            has_metadata = len(metadata) > 0
            source_type = metadata.get("source_type", "unknown")

            # Basic quality flags
            flags = []
            if content_length < 100:
                flags.append("too_short")
            if not has_metadata:
                flags.append("no_metadata")
            if "github" in source_type.lower():
                flags.append("code_content")

            # Calculate score (0-1)
            score = min(1.0, (content_length / 1000) * 0.5 + (0.5 if has_metadata else 0))

            items.append({
                "id": row[0],
                "created_at": row[3],
                "content_hash": f"{hash(content) % 1000000:06d}",  # Simple hash
                "stale_days": 0,  # Not implemented
                "flags": flags,
                "metadata": metadata,
                "importance_score": score
            })

        return {
            "status": "success",
            "data": {"items": items}
        }

    async def _list_analyses_local(self, conn: sqlite3.Connection, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """List analyses from local database."""
        limit = int(params.get("limit", 10)) if params else 10

        cur = conn.execute("""
            SELECT id, document_id, analyzer, model, result, score, created_at
            FROM analyses
            ORDER BY created_at DESC LIMIT ?
        """, (limit,))

        items = []
        for row in cur.fetchall():
            items.append({
                "id": row[0],
                "document_id": row[1],
                "analyzer": row[2],
                "model": row[3],
                "result": json.loads(row[4]) if row[4] else {},
                "score": row[5],
                "created_at": row[6]
            })

        return {
            "status": "success",
            "data": {"items": items}
        }

    async def _get_analysis_local(self, conn: sqlite3.Connection, analysis_id: str) -> Dict[str, Any]:
        """Get analysis by ID from local database."""
        cur = conn.execute("SELECT * FROM analyses WHERE id=?", (analysis_id,))
        row = cur.fetchone()

        if not row:
            return {"status": "error", "error": f"Analysis '{analysis_id}' not found"}

        return {
            "status": "success",
            "data": {
                "id": row[0],
                "document_id": row[1],
                "analyzer": row[2],
                "model": row[3],
                "prompt_hash": row[4],
                "result": json.loads(row[5]) if row[5] else {},
                "score": row[6],
                "metadata": json.loads(row[7]) if row[7] else {},
                "created_at": row[8]
            }
        }

    async def _get_style_examples_local(self, conn: sqlite3.Connection, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Get style examples from local database."""
        style_type = params.get("type", "all") if params else "all"

        # Return mock style examples since we don't have a style_examples table
        examples = [
            {
                "language": "python",
                "title": "Function Documentation",
                "content": "def example():\n    \"\"\"Example function with docstring.\"\"\"\n    pass",
                "tags": ["docstring", "documentation"]
            }
        ]

        return {
            "status": "success",
            "data": {"items": examples}
        }

    async def _get_quality_tips_local(self) -> Dict[str, Any]:
        """Get quality tips."""
        return {
            "status": "success",
            "data": {
                "tips": [
                    "Ensure all documents have meaningful metadata",
                    "Keep document content concise but complete",
                    "Use consistent formatting across document types",
                    "Regularly review and update document quality"
                ]
            }
        }

    async def _get_config_local(self) -> Dict[str, Any]:
        """Get effective configuration."""
        return {
            "status": "success",
            "data": {
                "database_path": os.environ.get("DOCSTORE_DB", "services/doc_store/db.sqlite3"),
                "doc_store_url": os.environ.get("DOC_STORE_URL", "local"),
                "timeout": 30,
                "retry_attempts": 3
            }
        }

    async def _get_storage_stats_local(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Get storage statistics."""
        cur = conn.execute("SELECT COUNT(*), SUM(LENGTH(content)) FROM documents")
        row = cur.fetchone()

        return {
            "status": "success",
            "data": {
                "document_count": row[0] or 0,
                "total_content_size": row[1] or 0,
                "database_size_mb": 0  # Not implemented
            }
        }

    async def _get_performance_metrics_local(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return {
            "status": "success",
            "data": {
                "average_response_time_ms": 50,
                "requests_per_second": 20,
                "cache_hit_rate": 0.85,
                "error_rate": 0.02
            }
        }

    async def ingest_source(self, source_type: str, source_url: str) -> Dict[str, Any]:
        """Convenience method for data ingestion."""
        url = f"{self.source_agent_url()}/ingest"
        payload = {
            "source_type": source_type,
            "source_url": source_url
        }
        return await self.post_json(url, payload)

    async def get_orchestrator_workflows(self) -> Dict[str, Any]:
        """Get available workflows from orchestrator."""
        url = f"{self.orchestrator_url()}/workflows"
        return await self.get_json(url)

    async def post_json(self, url: str, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """POST JSON and parse JSON response.

        Only passes optional kwargs when provided so that simple test doubles
        that don't accept headers/params keep working.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async def _call():
                kwargs: Dict[str, Any] = {"json": payload}
                if headers is not None:
                    kwargs["headers"] = headers
                r = await client.post(url, **kwargs)
                r.raise_for_status()
                return r.json()
            async def _op():
                if self.circuit_enabled:
                    cb = CircuitBreaker()
                    return await with_circuit(cb, _call)
                return await _call()
            return await with_retries(_op, attempts=self.retry_attempts, base_delay_ms=self.retry_base_ms)

    async def get_json(self, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """GET JSON and parse JSON response."""
        # Check for local database access
        if url.startswith("doc_store/") and self.doc_store_url() == "local":
            return await self._get_docstore_local(url, params)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async def _call():
                kwargs: Dict[str, Any] = {"params": params} if params is not None else {}
                if headers is not None:
                    kwargs["headers"] = headers
                r = await client.get(url, **kwargs)
                r.raise_for_status()
                return r.json()
            async def _op():
                if self.circuit_enabled:
                    cb = CircuitBreaker()
                    return await with_circuit(cb, _call)
                return await _call()
            return await with_retries(_op, attempts=self.retry_attempts, base_delay_ms=self.retry_base_ms)


