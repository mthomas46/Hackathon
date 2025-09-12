import os
import httpx
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from services.shared.resilience import with_retries, CircuitBreaker, with_circuit  # type: ignore
from services.shared.config import get_config_value


class ServiceClients:
    """Minimal JSON-focused HTTP client wrapper.

    Centralizes timeouts, retries with jitter, and circuit-breaker behavior
    to keep inter-service calls consistent and testable.
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
        return get_config_value("DOC_STORE_URL", "http://doc-store:5010", section="services", env_key="DOC_STORE_URL")

    def source_agent_url(self) -> str:
        """Get Source Agent service URL."""
        return get_config_value("SOURCE_AGENT_URL", "http://source-agent:5000", section="services", env_key="SOURCE_AGENT_URL")

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
            "doc-store": self.doc_store_url(),
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
            "doc-store",
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
        url = f"{self.doc_store_url()}/documents"
        return await self.post_json(url, document_data)

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


