"""Ecosystem Service Clients - Integration with 21+ Ecosystem Services.

This module provides typed client adapters for communicating with all
ecosystem services, following existing service communication patterns.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import httpx
from datetime import datetime

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))
try:
    from integrations.clients import ServiceClients
except ImportError:
    # Create a mock ServiceClients for testing
    class MockServiceClients:
        pass
    ServiceClients = MockServiceClients

from ...domain.value_objects import ECOSYSTEM_SERVICES, ServiceEndpoint, ServiceHealth
from ..logging import get_simulation_logger


class EcosystemServiceClient:
    """Base client for ecosystem service communication."""

    def __init__(self, service_name: str, endpoint: ServiceEndpoint):
        """Initialize service client."""
        self.service_name = service_name
        self.endpoint = endpoint
        self.logger = get_simulation_logger()
        self._client = httpx.AsyncClient(
            timeout=endpoint.timeout_seconds,
            base_url=endpoint.base_url
        )

    async def health_check(self) -> ServiceHealth:
        """Check service health."""
        try:
            health_url = f"{self.endpoint.base_url}{self.endpoint.health_check_endpoint}"
            response = await self._client.get(health_url)

            if response.status_code == 200:
                return ServiceHealth.HEALTHY
            else:
                return ServiceHealth.UNHEALTHY
        except Exception:
            return ServiceHealth.UNKNOWN

    async def get_json(self, path: str) -> Dict[str, Any]:
        """Make GET request and return JSON response."""
        try:
            response = await self._client.get(path)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            self.logger.error(
                f"HTTP error from {self.service_name}",
                status_code=e.response.status_code,
                url=str(e.request.url)
            )
            raise
        except Exception as e:
            self.logger.error(
                f"Request failed to {self.service_name}",
                error=str(e),
                path=path
            )
            raise

    async def post_json(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make POST request with JSON data."""
        try:
            response = await self._client.post(path, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            self.logger.error(
                f"HTTP error from {self.service_name}",
                status_code=e.response.status_code,
                url=str(e.request.url)
            )
            raise
        except Exception as e:
            self.logger.error(
                f"Request failed to {self.service_name}",
                error=str(e),
                path=path
            )
            raise


class DocStoreClient(EcosystemServiceClient):
    """Client for doc_store service."""

    def __init__(self):
        """Initialize doc_store client."""
        service_info = next(s for s in ECOSYSTEM_SERVICES if s.name == "doc_store")
        super().__init__(service_info.name, service_info.endpoint)

    async def store_document(self, title: str, content: str, metadata: Dict[str, Any]) -> Optional[str]:
        """Store a document in doc_store."""
        try:
            response = await self.post_json("/documents", {
                "title": title,
                "content": content,
                "metadata": metadata
            })
            return response.get("document_id")
        except Exception:
            return None

    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a document from doc_store."""
        try:
            return await self.get_json(f"/documents/{document_id}")
        except Exception:
            return None

    async def search_documents(self, query: str) -> List[Dict[str, Any]]:
        """Search documents in doc_store."""
        try:
            response = await self.post_json("/documents/search", {"query": query})
            return response.get("documents", [])
        except Exception:
            return []


class MockDataGeneratorClient(EcosystemServiceClient):
    """Client for mock-data-generator service."""

    def __init__(self):
        """Initialize mock-data-generator client."""
        service_info = next(s for s in ECOSYSTEM_SERVICES if s.name == "mock_data_generator")
        super().__init__(service_info.name, service_info.endpoint)

    async def generate_project_documents(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate project documents."""
        return await self.post_json("/simulation/project-docs", request)

    async def generate_timeline_events(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate timeline events."""
        return await self.post_json("/simulation/timeline-events", request)

    async def generate_team_activities(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate team activities."""
        return await self.post_json("/simulation/team-activities", request)

    async def generate_phase_documents(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate phase documents."""
        return await self.post_json("/simulation/phase-documents", request)

    async def generate_ecosystem_scenario(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate ecosystem scenario."""
        return await self.post_json("/simulation/ecosystem-scenario", request)


class OrchestratorClient(EcosystemServiceClient):
    """Client for orchestrator service."""

    def __init__(self):
        """Initialize orchestrator client."""
        service_info = next(s for s in ECOSYSTEM_SERVICES if s.name == "orchestrator")
        super().__init__(service_info.name, service_info.endpoint)

    async def create_workflow(self, workflow_config: Dict[str, Any]) -> Optional[str]:
        """Create a new workflow."""
        try:
            response = await self.post_json("/workflows", workflow_config)
            return response.get("workflow_id")
        except Exception:
            return None

    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Execute a workflow."""
        return await self.post_json(f"/workflows/{workflow_id}/execute", {})

    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow execution status."""
        return await self.get_json(f"/workflows/{workflow_id}/status")


class AnalysisServiceClient(EcosystemServiceClient):
    """Client for analysis_service."""

    def __init__(self):
        """Initialize analysis_service client."""
        service_info = next(s for s in ECOSYSTEM_SERVICES if s.name == "analysis_service")
        super().__init__(service_info.name, service_info.endpoint)

    async def analyze_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze documents for quality and insights."""
        return await self.post_json("/analyze/documents", {"documents": documents})

    async def generate_insights(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights from analysis data."""
        return await self.post_json("/analyze/insights", analysis_data)


class LlmGatewayClient(EcosystemServiceClient):
    """Client for llm_gateway service."""

    def __init__(self):
        """Initialize llm_gateway client."""
        service_info = next(s for s in ECOSYSTEM_SERVICES if s.name == "llm_gateway")
        super().__init__(service_info.name, service_info.endpoint)

    async def generate_content(self, prompt: str, model: str = "gpt-4") -> Dict[str, Any]:
        """Generate content using LLM."""
        return await self.post_json("/generate", {
            "prompt": prompt,
            "model": model,
            "max_tokens": 1000
        })


class PromptStoreClient(EcosystemServiceClient):
    """Client for prompt_store service."""

    def __init__(self):
        """Initialize prompt_store client."""
        service_info = next(s for s in ECOSYSTEM_SERVICES if s.name == "prompt_store")
        super().__init__(service_info.name, service_info.endpoint)

    async def store_prompt(self, name: str, content: str, category: str) -> Optional[str]:
        """Store a prompt in prompt_store."""
        try:
            response = await self.post_json("/prompts", {
                "name": name,
                "content": content,
                "category": category
            })
            return response.get("prompt_id")
        except Exception:
            return None

    async def get_prompt(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a prompt from prompt_store."""
        try:
            return await self.get_json(f"/prompts/{prompt_id}")
        except Exception:
            return None


class SummarizerHubClient(EcosystemServiceClient):
    """Client for summarizer_hub service."""

    def __init__(self):
        """Initialize summarizer_hub client."""
        service_info = next(s for s in ECOSYSTEM_SERVICES if s.name == "summarizer_hub")
        super().__init__(service_info.name, service_info.endpoint)

    async def summarize_text(self, text: str, max_length: int = 200) -> Dict[str, Any]:
        """Summarize text content."""
        return await self.post_json("/summarize", {
            "text": text,
            "max_length": max_length
        })


class InterpreterClient(EcosystemServiceClient):
    """Client for interpreter service."""

    def __init__(self):
        """Initialize interpreter client."""
        service_info = next(s for s in ECOSYSTEM_SERVICES if s.name == "interpreter")
        super().__init__(service_info.name, service_info.endpoint)

    async def analyze_relationships(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze relationships between documents."""
        return await self.post_json("/analyze/relationships", {
            "documents": documents
        })

    async def extract_insights(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract insights from content with context."""
        return await self.post_json("/extract/insights", {
            "content": content,
            "context": context
        })


class NotificationServiceClient(EcosystemServiceClient):
    """Client for notification_service."""

    def __init__(self):
        """Initialize notification_service client."""
        service_info = next(s for s in ECOSYSTEM_SERVICES if s.name == "notification_service")
        super().__init__(service_info.name, service_info.endpoint)

    async def send_notification(self, recipient: str, message: str,
                              notification_type: str = "info") -> Dict[str, Any]:
        """Send a notification."""
        return await self.post_json("/notifications", {
            "recipient": recipient,
            "message": message,
            "type": notification_type
        })


class SourceAgentClient(EcosystemServiceClient):
    """Client for source_agent service."""

    def __init__(self):
        """Initialize source_agent client."""
        service_info = next(s for s in ECOSYSTEM_SERVICES if s.name == "source_agent")
        super().__init__(service_info.name, service_info.endpoint)

    async def analyze_codebase(self, repository_url: str) -> Dict[str, Any]:
        """Analyze a codebase."""
        return await self.post_json("/analyze", {"repository_url": repository_url})


class CodeAnalyzerClient(EcosystemServiceClient):
    """Client for code_analyzer service."""

    def __init__(self):
        """Initialize code_analyzer client."""
        service_info = next(s for s in ECOSYSTEM_SERVICES if s.name == "code_analyzer")
        super().__init__(service_info.name, service_info.endpoint)

    async def analyze_code(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code for quality and issues."""
        return await self.post_json("/analyze", {
            "code": code,
            "language": language
        })


class EcosystemServiceRegistry:
    """Registry for all ecosystem service clients."""

    def __init__(self):
        """Initialize service registry."""
        self._clients: Dict[str, EcosystemServiceClient] = {}
        self._initialize_clients()

    def _initialize_clients(self):
        """Initialize all ecosystem service clients."""
        self._clients = {
            "doc_store": DocStoreClient(),
            "mock_data_generator": MockDataGeneratorClient(),
            "orchestrator": OrchestratorClient(),
            "analysis_service": AnalysisServiceClient(),
            "llm_gateway": LlmGatewayClient(),
            "prompt_store": PromptStoreClient(),
            "summarizer_hub": SummarizerHubClient(),
            "notification_service": NotificationServiceClient(),
            "source_agent": SourceAgentClient(),
            "code_analyzer": CodeAnalyzerClient(),
        }

    def get_client(self, service_name: str) -> Optional[EcosystemServiceClient]:
        """Get a service client by name."""
        return self._clients.get(service_name)

    def get_all_clients(self) -> Dict[str, EcosystemServiceClient]:
        """Get all service clients."""
        return self._clients.copy()

    async def check_service_health(self, service_name: str) -> ServiceHealth:
        """Check health of a specific service."""
        client = self.get_client(service_name)
        if client:
            return await client.health_check()
        return ServiceHealth.UNKNOWN

    async def check_all_services_health(self) -> Dict[str, ServiceHealth]:
        """Check health of all services."""
        health_status = {}
        for service_name, client in self._clients.items():
            health_status[service_name] = await client.health_check()
        return health_status


# Global service registry instance
_ecosystem_registry: Optional[EcosystemServiceRegistry] = None


def get_ecosystem_service_registry() -> EcosystemServiceRegistry:
    """Get the global ecosystem service registry instance."""
    global _ecosystem_registry
    if _ecosystem_registry is None:
        _ecosystem_registry = EcosystemServiceRegistry()
    return _ecosystem_registry


def get_ecosystem_client(service_name: str) -> Optional[EcosystemServiceClient]:
    """Get an ecosystem service client by name."""
    return get_ecosystem_service_registry().get_client(service_name)


# Convenience functions for commonly used services
def get_doc_store_client() -> DocStoreClient:
    """Get doc_store client."""
    client = get_ecosystem_client("doc_store")
    return client if isinstance(client, DocStoreClient) else None

def get_mock_data_generator_client() -> MockDataGeneratorClient:
    """Get mock-data-generator client."""
    client = get_ecosystem_client("mock_data_generator")
    return client if isinstance(client, MockDataGeneratorClient) else None

def get_orchestrator_client() -> OrchestratorClient:
    """Get orchestrator client."""
    client = get_ecosystem_client("orchestrator")
    return client if isinstance(client, OrchestratorClient) else None

def get_analysis_service_client() -> AnalysisServiceClient:
    """Get analysis_service client."""
    client = get_ecosystem_client("analysis_service")
    return client if isinstance(client, AnalysisServiceClient) else None

def get_llm_gateway_client() -> LlmGatewayClient:
    """Get llm_gateway client."""
    client = get_ecosystem_client("llm_gateway")
    return client if isinstance(client, LlmGatewayClient) else None

def get_summarizer_hub_client() -> SummarizerHubClient:
    """Get summarizer_hub client."""
    client = get_ecosystem_client("summarizer_hub")
    return client if isinstance(client, SummarizerHubClient) else None

def get_interpreter_client() -> InterpreterClient:
    """Get interpreter client."""
    client = get_ecosystem_client("interpreter")
    return client if isinstance(client, InterpreterClient) else None


__all__ = [
    'EcosystemServiceClient',
    'DocStoreClient',
    'MockDataGeneratorClient',
    'OrchestratorClient',
    'AnalysisServiceClient',
    'LlmGatewayClient',
    'PromptStoreClient',
    'SummarizerHubClient',
    'InterpreterClient',
    'NotificationServiceClient',
    'SourceAgentClient',
    'CodeAnalyzerClient',
    'EcosystemServiceRegistry',
    'get_ecosystem_service_registry',
    'get_ecosystem_client',
    'get_doc_store_client',
    'get_mock_data_generator_client',
    'get_orchestrator_client',
    'get_analysis_service_client',
    'get_llm_gateway_client',
    'get_summarizer_hub_client',
    'get_interpreter_client'
]
