"""Mock Clients - External service client mocking for testing.

Provides mock implementations of all external service clients used in the
Project Simulation Service, following ecosystem patterns for consistent
test behavior and reliable service isolation.
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from unittest.mock import AsyncMock
from datetime import datetime


class MockEcosystemClient:
    """Base mock ecosystem client with common behavior."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.calls: List[Dict[str, Any]] = []
        self.should_fail = False
        self.delay_seconds = 0
        self.response_override: Optional[Dict[str, Any]] = None

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Mock request implementation."""
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if self.should_fail:
            raise Exception(f"Mock {self.service_name} client failure")

        # Record the call
        self.calls.append({
            "method": method,
            "endpoint": endpoint,
            "kwargs": kwargs,
            "timestamp": datetime.now()
        })

        # Return override if set, otherwise default response
        if self.response_override:
            return self.response_override

        return {"status": "success", "message": f"Mock {method} to {endpoint}"}

    def reset(self):
        """Reset mock state."""
        self.calls.clear()
        self.should_fail = False
        self.delay_seconds = 0
        self.response_override = None


class MockAnalysisServiceClient(MockEcosystemClient):
    """Mock analysis service client."""

    def __init__(self):
        super().__init__("analysis-service")

    async def analyze_document_quality(self, document_ids: List[str], **kwargs) -> Dict[str, Any]:
        """Mock document quality analysis."""
        return await self._make_request("POST", "/analyze/quality", document_ids=document_ids, **kwargs)

    async def analyze_code_complexity(self, **kwargs) -> Dict[str, Any]:
        """Mock code complexity analysis."""
        return await self._make_request("POST", "/analyze/complexity", **kwargs)

    async def analyze_semantic_similarity(self, **kwargs) -> Dict[str, Any]:
        """Mock semantic similarity analysis."""
        return await self._make_request("POST", "/analyze/similarity", **kwargs)

    async def get_code_quality_metrics(self, project_id: str, time_period_days: int) -> Dict[str, Any]:
        """Mock code quality metrics retrieval."""
        return await self._make_request("GET", f"/projects/{project_id}/metrics/quality",
                                      time_period_days=time_period_days)


class MockInterpreterClient(MockEcosystemClient):
    """Mock interpreter service client."""

    def __init__(self):
        super().__init__("interpreter")

    async def generate_insight_content(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock insight content generation."""
        return await self._make_request("POST", "/insights/generate", **request_data)

    async def analyze_text(self, text: str, **kwargs) -> Dict[str, Any]:
        """Mock text analysis."""
        return await self._make_request("POST", "/analyze/text", text=text, **kwargs)

    async def extract_patterns(self, **kwargs) -> Dict[str, Any]:
        """Mock pattern extraction."""
        return await self._make_request("POST", "/patterns/extract", **kwargs)


class MockDocStoreClient(MockEcosystemClient):
    """Mock document store client."""

    def __init__(self):
        super().__init__("doc-store")

    async def store_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Mock document storage."""
        return await self._make_request("POST", "/documents", **document)

    async def get_document(self, document_id: str) -> Dict[str, Any]:
        """Mock document retrieval."""
        return await self._make_request("GET", f"/documents/{document_id}")

    async def search_documents(self, query: str, **kwargs) -> Dict[str, Any]:
        """Mock document search."""
        return await self._make_request("GET", "/documents/search", query=query, **kwargs)

    async def update_document(self, document_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Mock document update."""
        return await self._make_request("PUT", f"/documents/{document_id}", **updates)

    async def delete_document(self, document_id: str) -> Dict[str, Any]:
        """Mock document deletion."""
        return await self._make_request("DELETE", f"/documents/{document_id}")


class MockLLMGatewayClient(MockEcosystemClient):
    """Mock LLM gateway client."""

    def __init__(self):
        super().__init__("llm-gateway")

    async def generate_content(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Mock content generation."""
        return await self._make_request("POST", "/generate", prompt=prompt, **kwargs)

    async def analyze_sentiment(self, text: str, **kwargs) -> Dict[str, Any]:
        """Mock sentiment analysis."""
        return await self._make_request("POST", "/analyze/sentiment", text=text, **kwargs)

    async def extract_keywords(self, text: str, **kwargs) -> Dict[str, Any]:
        """Mock keyword extraction."""
        return await self._make_request("POST", "/extract/keywords", text=text, **kwargs)

    async def summarize_text(self, text: str, **kwargs) -> Dict[str, Any]:
        """Mock text summarization."""
        return await self._make_request("POST", "/summarize", text=text, **kwargs)


class MockNotificationServiceClient(MockEcosystemClient):
    """Mock notification service client."""

    def __init__(self):
        super().__init__("notification-service")

    async def send_notification(self, recipient: str, message: str, **kwargs) -> Dict[str, Any]:
        """Mock notification sending."""
        return await self._make_request("POST", "/notifications", recipient=recipient, message=message, **kwargs)

    async def send_email(self, to: str, subject: str, body: str, **kwargs) -> Dict[str, Any]:
        """Mock email sending."""
        return await self._make_request("POST", "/email", to=to, subject=subject, body=body, **kwargs)

    async def create_webhook(self, url: str, events: List[str], **kwargs) -> Dict[str, Any]:
        """Mock webhook creation."""
        return await self._make_request("POST", "/webhooks", url=url, events=events, **kwargs)


class MockMockDataGeneratorClient(MockEcosystemClient):
    """Mock mock data generator client."""

    def __init__(self):
        super().__init__("mock-data-generator")

    async def generate_project_docs(self, project_config: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Mock project documentation generation."""
        return await self._make_request("POST", "/simulation/project-docs", project_config=project_config, **kwargs)

    async def generate_timeline_events(self, timeline_config: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Mock timeline events generation."""
        return await self._make_request("POST", "/simulation/timeline-events", timeline_config=timeline_config, **kwargs)

    async def generate_team_activities(self, team_config: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Mock team activities generation."""
        return await self._make_request("POST", "/simulation/team-activities", team_config=team_config, **kwargs)

    async def generate_ecosystem_scenario(self, scenario_config: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Mock ecosystem scenario generation."""
        return await self._make_request("POST", "/simulation/ecosystem-scenario", scenario_config=scenario_config, **kwargs)


class MockEcosystemClients:
    """Collection of all mock ecosystem clients."""

    def __init__(self):
        self.analysis_service = MockAnalysisServiceClient()
        self.interpreter = MockInterpreterClient()
        self.doc_store = MockDocStoreClient()
        self.llm_gateway = MockLLMGatewayClient()
        self.notification_service = MockNotificationServiceClient()
        self.mock_data_generator = MockMockDataGeneratorClient()

        # Dictionary access
        self._clients = {
            "analysis_service": self.analysis_service,
            "interpreter": self.interpreter,
            "doc_store": self.doc_store,
            "llm_gateway": self.llm_gateway,
            "notification_service": self.notification_service,
            "mock_data_generator": self.mock_data_generator
        }

    def __getitem__(self, key: str) -> MockEcosystemClient:
        """Get client by service name."""
        return self._clients[key]

    def __getattr__(self, name: str) -> MockEcosystemClient:
        """Get client by attribute name."""
        return self._clients[name]

    def reset_all(self):
        """Reset all mock clients."""
        for client in self._clients.values():
            client.reset()

    def configure_responses(self, service_name: str, response: Dict[str, Any]):
        """Configure response for specific service."""
        if service_name in self._clients:
            self._clients[service_name].response_override = response

    def set_failure_mode(self, service_name: str, should_fail: bool = True):
        """Set failure mode for specific service."""
        if service_name in self._clients:
            self._clients[service_name].should_fail = should_fail

    def set_delay(self, service_name: str, delay_seconds: float):
        """Set response delay for specific service."""
        if service_name in self._clients:
            self._clients[service_name].delay_seconds = delay_seconds

    def get_call_history(self, service_name: str) -> List[Dict[str, Any]]:
        """Get call history for specific service."""
        if service_name in self._clients:
            return self._clients[service_name].calls
        return []

    def get_all_call_history(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get call history for all services."""
        return {name: client.calls for name, client in self._clients.items()}


# Factory functions for easy mock creation
def create_mock_ecosystem_clients(**kwargs) -> MockEcosystemClients:
    """Create configured mock ecosystem clients."""
    clients = MockEcosystemClients()

    # Apply configuration
    for service_name, config in kwargs.items():
        if service_name in clients._clients:
            client = clients._clients[service_name]

            if "response_override" in config:
                client.response_override = config["response_override"]
            if "should_fail" in config:
                client.should_fail = config["should_fail"]
            if "delay_seconds" in config:
                client.delay_seconds = config["delay_seconds"]

    return clients


def create_mock_analysis_client(**kwargs) -> MockAnalysisServiceClient:
    """Create configured mock analysis service client."""
    client = MockAnalysisServiceClient()

    for key, value in kwargs.items():
        if hasattr(client, key):
            setattr(client, key, value)

    return client


def create_mock_interpreter_client(**kwargs) -> MockInterpreterClient:
    """Create configured mock interpreter client."""
    client = MockInterpreterClient()

    for key, value in kwargs.items():
        if hasattr(client, key):
            setattr(client, key, value)

    return client


def create_mock_doc_store_client(**kwargs) -> MockDocStoreClient:
    """Create configured mock doc store client."""
    client = MockDocStoreClient()

    for key, value in kwargs.items():
        if hasattr(client, key):
            setattr(client, key, value)

    return client


def create_mock_llm_gateway_client(**kwargs) -> MockLLMGatewayClient:
    """Create configured mock LLM gateway client."""
    client = MockLLMGatewayClient()

    for key, value in kwargs.items():
        if hasattr(client, key):
            setattr(client, key, value)

    return client


# Pre-configured mock responses for common scenarios
MOCK_RESPONSES = {
    "successful_analysis": {
        "status": "success",
        "overall_score": 0.85,
        "issues": [],
        "recommendations": ["Good quality documentation"]
    },
    "failed_analysis": {
        "status": "error",
        "error": "Analysis service unavailable"
    },
    "successful_generation": {
        "content": "Mock generated content",
        "metadata": {"quality_score": 0.9}
    },
    "successful_storage": {
        "document_id": "mock_doc_001",
        "status": "stored"
    },
    "successful_notification": {
        "notification_id": "mock_notif_001",
        "status": "sent"
    }
}


__all__ = [
    'MockEcosystemClient',
    'MockAnalysisServiceClient',
    'MockInterpreterClient',
    'MockDocStoreClient',
    'MockLLMGatewayClient',
    'MockNotificationServiceClient',
    'MockMockDataGeneratorClient',
    'MockEcosystemClients',
    'create_mock_ecosystem_clients',
    'create_mock_analysis_client',
    'create_mock_interpreter_client',
    'create_mock_doc_store_client',
    'create_mock_llm_gateway_client',
    'MOCK_RESPONSES'
]
