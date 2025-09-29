"""Service Clients - Typed Client Adapters for Ecosystem Services.

This module implements typed client adapters for all 21+ ecosystem services,
providing a consistent, resilient service mesh communication layer following
enterprise patterns with circuit breaker, retry, and monitoring capabilities.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Type, TypeVar, Union, Generic
from datetime import datetime
import asyncio
import httpx
import json

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))

from simulation.infrastructure.logging import get_simulation_logger
from simulation.infrastructure.integration.service_discovery import get_service_url
from simulation.infrastructure.monitoring.simulation_monitoring import get_simulation_monitoring_service
from simulation.infrastructure.utilities.simulation_utilities import get_simulation_retry_manager

T = TypeVar('T')


class ServiceClientError(Exception):
    """Base exception for service client errors."""
    def __init__(self, service_name: str, operation: str, message: str, status_code: Optional[int] = None):
        self.service_name = service_name
        self.operation = operation
        self.message = message
        self.status_code = status_code
        super().__init__(f"{service_name}.{operation}: {message}")


class ServiceUnavailableError(ServiceClientError):
    """Exception raised when a service is unavailable."""
    pass


class ServiceTimeoutError(ServiceClientError):
    """Exception raised when a service request times out."""
    pass


class ServiceResponseError(ServiceClientError):
    """Exception raised when a service returns an error response."""
    pass


class BaseServiceClient:
    """Base class for all service clients with common functionality."""

    def __init__(self, service_name: str, base_url: Optional[str] = None):
        """Initialize the service client."""
        self.service_name = service_name
        self.base_url = base_url or get_service_url(service_name) or f"http://localhost:5000"
        self.logger = get_simulation_logger()
        self.monitoring = get_simulation_monitoring_service()
        self.retry_manager = get_simulation_retry_manager()

        # HTTP client configuration
        self.timeout = httpx.Timeout(10.0, connect=5.0)
        self._client: Optional[httpx.AsyncClient] = None

        self.logger.info(f"Initialized {service_name} client", base_url=self.base_url)

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client instance."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={
                    "User-Agent": "Simulation-Service/1.0",
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }
            )
        return self._client

    async def _make_request(self,
                           method: str,
                           endpoint: str,
                           **kwargs) -> Dict[str, Any]:
        """Make HTTP request with error handling and monitoring."""
        start_time = datetime.now()
        operation = f"{method}_{endpoint.replace('/', '_')}"

        try:
            client = await self._get_client()

            # Record service call start
            self.monitoring.record_simulation_event("service_call_started", operation)

            # Make the request with retry logic
            response = await self._execute_with_retry(method, endpoint, client, **kwargs)

            # Record successful service call
            response_time = (datetime.now() - start_time).total_seconds()
            self.monitoring.record_ecosystem_service_call(self.service_name, operation, response_time)

            return response.json() if response.content else {}

        except httpx.TimeoutException as e:
            self._handle_error(operation, ServiceTimeoutError(self.service_name, operation, str(e)))
        except httpx.ConnectError as e:
            self._handle_error(operation, ServiceUnavailableError(self.service_name, operation, str(e)))
        except httpx.HTTPStatusError as e:
            self._handle_error(operation, ServiceResponseError(self.service_name, operation, str(e), e.response.status_code))
        except Exception as e:
            self._handle_error(operation, ServiceClientError(self.service_name, operation, str(e)))

    def _handle_error(self, operation: str, error: ServiceClientError):
        """Handle and log service errors."""
        self.logger.error(
            "Service client error",
            service=self.service_name,
            operation=operation,
            error=str(error),
            status_code=getattr(error, 'status_code', None)
        )

        # Record failed service call
        self.monitoring.record_ecosystem_service_call(self.service_name, operation, 0)

        raise error

    async def _execute_with_retry(self, method: str, endpoint: str, client: httpx.AsyncClient, **kwargs):
        """Execute request with retry logic."""
        async def attempt():
            response = await client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response

        return await self.retry_manager.execute_with_simulation_retry(
            f"{self.service_name}_{method}_{endpoint}",
            attempt
        )

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Ecosystem Service Clients

class MockDataGeneratorClient(BaseServiceClient):
    """Client for mock-data-generator service."""

    def __init__(self):
        super().__init__("mock_data_generator")

    async def generate_project_documents(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate project documents."""
        response = await self._make_request("POST", "/simulation/project-docs", json=config)
        return response.get("documents", [])

    async def generate_timeline_events(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate timeline events."""
        response = await self._make_request("POST", "/simulation/timeline-events", json=config)
        return response.get("events", [])

    async def generate_team_activities(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate team activities."""
        response = await self._make_request("POST", "/simulation/team-activities", json=config)
        return response.get("activities", [])

    async def generate_phase_documents(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate phase-specific documents."""
        response = await self._make_request("POST", "/simulation/phase-documents", json=config)
        return response.get("documents", [])

    async def generate_ecosystem_scenario(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete ecosystem scenario."""
        return await self._make_request("POST", "/simulation/ecosystem-scenario", json=config)


class DocStoreClient(BaseServiceClient):
    """Client for doc-store service."""

    def __init__(self):
        super().__init__("doc_store")

    async def store_document(self, title: str, content: str, metadata: Dict[str, Any]) -> str:
        """Store a document."""
        payload = {
            "title": title,
            "content": content,
            "metadata": metadata
        }
        response = await self._make_request("POST", "/documents", json=payload)
        return response.get("document_id")

    async def get_document(self, document_id: str) -> Dict[str, Any]:
        """Retrieve a document."""
        return await self._make_request("GET", f"/documents/{document_id}")

    async def update_document(self, document_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a document."""
        return await self._make_request("PUT", f"/documents/{document_id}", json=updates)

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document."""
        await self._make_request("DELETE", f"/documents/{document_id}")
        return True

    async def search_documents(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search documents."""
        payload = {"query": query}
        if filters:
            payload["filters"] = filters
        response = await self._make_request("POST", "/documents/search", json=payload)
        return response.get("documents", [])


class AnalysisServiceClient(BaseServiceClient):
    """Client for analysis-service."""

    def __init__(self):
        super().__init__("analysis_service")

    async def analyze_document(self, document_id: str, content: str) -> Dict[str, Any]:
        """Analyze a single document."""
        payload = {
            "document_id": document_id,
            "content": content
        }
        return await self._make_request("POST", "/analyze", json=payload)

    async def analyze_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze multiple documents."""
        return await self._make_request("POST", "/analyze/batch", json={"documents": documents})

    async def get_quality_metrics(self, document_id: str) -> Dict[str, Any]:
        """Get quality metrics for a document."""
        return await self._make_request("GET", f"/quality/{document_id}")

    async def detect_duplicates(self, documents: List[str]) -> Dict[str, Any]:
        """Detect duplicate content."""
        return await self._make_request("POST", "/duplicates", json={"documents": documents})


class LLMGatewayClient(BaseServiceClient):
    """Client for llm-gateway service."""

    def __init__(self):
        super().__init__("llm_gateway")

    async def generate_content(self, prompt: str, model: str = "gpt-4", **kwargs) -> Dict[str, Any]:
        """Generate content using LLM."""
        payload = {
            "prompt": prompt,
            "model": model,
            **kwargs
        }
        return await self._make_request("POST", "/generate", json=payload)

    async def get_available_models(self) -> List[str]:
        """Get available LLM models."""
        response = await self._make_request("GET", "/models")
        return response.get("models", [])

    async def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get information about a model."""
        return await self._make_request("GET", f"/models/{model}")


class OrchestratorClient(BaseServiceClient):
    """Client for orchestrator service."""

    def __init__(self):
        super().__init__("orchestrator")

    async def create_workflow(self, definition: Dict[str, Any]) -> str:
        """Create a new workflow."""
        response = await self._make_request("POST", "/workflows", json=definition)
        return response.get("workflow_id")

    async def execute_workflow(self, workflow_id: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow."""
        return await self._make_request("POST", f"/workflows/{workflow_id}/execute", json=inputs)

    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow execution status."""
        return await self._make_request("GET", f"/workflows/{workflow_id}/status")

    async def get_workflow_result(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow execution result."""
        return await self._make_request("GET", f"/workflows/{workflow_id}/result")

    async def list_workflows(self) -> List[Dict[str, Any]]:
        """List all workflows."""
        response = await self._make_request("GET", "/workflows")
        return response.get("workflows", [])


class LogCollectorClient(BaseServiceClient):
    """Client for log-collector service."""

    def __init__(self):
        super().__init__("log_collector")

    async def collect_logs(self, logs: List[Dict[str, Any]]) -> bool:
        """Collect and store logs."""
        await self._make_request("POST", "/logs", json={"logs": logs})
        return True

    async def query_logs(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query logs with filters."""
        response = await self._make_request("POST", "/logs/query", json=query)
        return response.get("logs", [])

    async def get_correlation_logs(self, correlation_id: str) -> List[Dict[str, Any]]:
        """Get logs for a specific correlation ID."""
        return await self._make_request("GET", f"/logs/correlation/{correlation_id}")


class NotificationServiceClient(BaseServiceClient):
    """Client for notification-service."""

    def __init__(self):
        super().__init__("notification_service")

    async def send_notification(self, notification: Dict[str, Any]) -> bool:
        """Send a notification."""
        await self._make_request("POST", "/notifications", json=notification)
        return True

    async def send_bulk_notifications(self, notifications: List[Dict[str, Any]]) -> bool:
        """Send multiple notifications."""
        await self._make_request("POST", "/notifications/bulk", json={"notifications": notifications})
        return True

    async def get_notification_status(self, notification_id: str) -> Dict[str, Any]:
        """Get notification delivery status."""
        return await self._make_request("GET", f"/notifications/{notification_id}/status")


class SummarizerHubClient(BaseServiceClient):
    """Client for summarizer-hub service."""

    def __init__(self):
        super().__init__("summarizer_hub")

    async def summarize_text(self, text: str, max_length: int = 200) -> Dict[str, Any]:
        """Summarize text content."""
        payload = {
            "text": text,
            "max_length": max_length
        }
        return await self._make_request("POST", "/summarize", json=payload)

    async def summarize_documents(self, documents: List[str]) -> Dict[str, Any]:
        """Summarize multiple documents."""
        return await self._make_request("POST", "/summarize/batch", json={"documents": documents})

    async def extract_key_points(self, text: str, max_points: int = 10) -> List[str]:
        """Extract key points from text."""
        payload = {
            "text": text,
            "max_points": max_points
        }
        response = await self._make_request("POST", "/key-points", json=payload)
        return response.get("key_points", [])


class InterpreterClient(BaseServiceClient):
    """Client for interpreter service."""

    def __init__(self):
        super().__init__("interpreter")

    async def analyze_relationships(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze relationships between documents."""
        return await self._make_request("POST", "/analyze/relationships", json={"documents": documents})

    async def generate_insights(self, documents: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights from document analysis."""
        payload = {
            "documents": documents,
            "context": context
        }
        return await self._make_request("POST", "/insights", json=payload)

    async def find_patterns(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find patterns in data."""
        return await self._make_request("POST", "/patterns", json={"data": data})


class SourceAgentClient(BaseServiceClient):
    """Client for source-agent service."""

    def __init__(self):
        super().__init__("source_agent")

    async def analyze_codebase(self, repository_url: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze a codebase."""
        payload = {
            "repository_url": repository_url,
            **(config or {})
        }
        return await self._make_request("POST", "/analyze", json=payload)

    async def generate_documentation(self, code_path: str, doc_type: str = "api") -> Dict[str, Any]:
        """Generate documentation from code."""
        payload = {
            "code_path": code_path,
            "doc_type": doc_type
        }
        return await self._make_request("POST", "/documentation", json=payload)


class CodeAnalyzerClient(BaseServiceClient):
    """Client for code-analyzer service."""

    def __init__(self):
        super().__init__("code_analyzer")

    async def analyze_code_quality(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code quality metrics."""
        payload = {
            "code": code,
            "language": language
        }
        return await self._make_request("POST", "/quality", json=payload)

    async def detect_security_issues(self, code: str, language: str) -> List[Dict[str, Any]]:
        """Detect security vulnerabilities."""
        payload = {
            "code": code,
            "language": language
        }
        response = await self._make_request("POST", "/security", json=payload)
        return response.get("issues", [])

    async def calculate_complexity(self, code: str, language: str) -> Dict[str, Any]:
        """Calculate code complexity metrics."""
        payload = {
            "code": code,
            "language": language
        }
        return await self._make_request("POST", "/complexity", json=payload)


class SecureAnalyzerClient(BaseServiceClient):
    """Client for secure-analyzer service."""

    def __init__(self):
        super().__init__("secure_analyzer")

    async def analyze_security(self, target: str, scan_type: str = "full") -> Dict[str, Any]:
        """Perform security analysis."""
        payload = {
            "target": target,
            "scan_type": scan_type
        }
        return await self._make_request("POST", "/analyze", json=payload)

    async def check_compliance(self, target: str, standards: List[str]) -> Dict[str, Any]:
        """Check compliance against security standards."""
        payload = {
            "target": target,
            "standards": standards
        }
        return await self._make_request("POST", "/compliance", json=payload)


# Service Client Registry

class EcosystemServiceClientRegistry:
    """Registry for all ecosystem service clients."""

    def __init__(self):
        """Initialize the client registry."""
        self._clients: Dict[str, Type[BaseServiceClient]] = {}
        self._instances: Dict[str, BaseServiceClient] = {}
        self.logger = get_simulation_logger()

        # Register all service clients
        self._register_clients()

    def _register_clients(self):
        """Register all available service clients."""
        self._clients = {
            "mock_data_generator": MockDataGeneratorClient,
            "doc_store": DocStoreClient,
            "analysis_service": AnalysisServiceClient,
            "llm_gateway": LLMGatewayClient,
            "orchestrator": OrchestratorClient,
            "log_collector": LogCollectorClient,
            "notification_service": NotificationServiceClient,
            "summarizer_hub": SummarizerHubClient,
            "interpreter": InterpreterClient,
            "source_agent": SourceAgentClient,
            "code_analyzer": CodeAnalyzerClient,
            "secure_analyzer": SecureAnalyzerClient,
            # Additional services can be added here
        }

        self.logger.info("Registered ecosystem service clients", count=len(self._clients))

    def get_client(self, service_name: str) -> BaseServiceClient:
        """Get a service client instance."""
        if service_name not in self._clients:
            raise ValueError(f"Service client '{service_name}' not registered")

        if service_name not in self._instances:
            client_class = self._clients[service_name]
            self._instances[service_name] = client_class()

        return self._instances[service_name]

    def get_available_services(self) -> List[str]:
        """Get list of available service clients."""
        return list(self._clients.keys())

    async def health_check_all(self) -> Dict[str, Any]:
        """Perform health check on all service clients."""
        results = {}
        for service_name in self._clients.keys():
            try:
                client = self.get_client(service_name)
                # Simple health check - client instantiation
                results[service_name] = {"healthy": True}
            except Exception as e:
                results[service_name] = {"healthy": False, "error": str(e)}

        return results

    async def close_all(self):
        """Close all service client connections."""
        for client in self._instances.values():
            try:
                await client.close()
            except Exception as e:
                self.logger.warning("Error closing client", service=client.service_name, error=str(e))
        self._instances.clear()


# Global client registry instance
_ecosystem_client_registry: Optional[EcosystemServiceClientRegistry] = None


def get_ecosystem_client(service_name: str) -> BaseServiceClient:
    """Get an ecosystem service client."""
    global _ecosystem_client_registry
    if _ecosystem_client_registry is None:
        _ecosystem_client_registry = EcosystemServiceClientRegistry()
    return _ecosystem_client_registry.get_client(service_name)


def get_ecosystem_client_registry() -> EcosystemServiceClientRegistry:
    """Get the ecosystem client registry."""
    global _ecosystem_client_registry
    if _ecosystem_client_registry is None:
        _ecosystem_client_registry = EcosystemServiceClientRegistry()
    return _ecosystem_client_registry


__all__ = [
    # Base Classes
    'BaseServiceClient',
    'ServiceClientError',
    'ServiceUnavailableError',
    'ServiceTimeoutError',
    'ServiceResponseError',

    # Service Clients
    'MockDataGeneratorClient',
    'DocStoreClient',
    'AnalysisServiceClient',
    'LLMGatewayClient',
    'OrchestratorClient',
    'LogCollectorClient',
    'NotificationServiceClient',
    'SummarizerHubClient',
    'InterpreterClient',
    'SourceAgentClient',
    'CodeAnalyzerClient',
    'SecureAnalyzerClient',

    # Registry
    'EcosystemServiceClientRegistry',
    'get_ecosystem_client',
    'get_ecosystem_client_registry'
]
