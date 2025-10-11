"""
Shared fixtures for workflow tests

Provides WorkflowContext for managing test state and service clients.
"""

import pytest
from typing import Dict, Any, List, Callable
from httpx import AsyncClient


@pytest.fixture
async def workflow_context():
    """
    Provides shared context for workflow tests
    """
    context = WorkflowContext()
    await context.setup()
    yield context
    await context.teardown()


class WorkflowContext:
    """
    Manages state and connections for workflow tests
    """
    
    def __init__(self):
        self.clients: Dict[str, AsyncClient] = {}
        self.test_data: Dict[str, Any] = {}
        self.cleanup_tasks: List[Callable] = []
    
    async def setup(self):
        """Initialize test environment"""
        # Service base URLs (adjust as needed)
        service_urls = {
            "doc_store": "http://localhost:5087",
            "analysis": "http://localhost:5020",
            "source_agent": "http://localhost:5085",
            "notification": "http://localhost:5130",
            "prompt_store": "http://localhost:5110",
        }
        
        # Create HTTP clients for each service
        for service, url in service_urls.items():
            self.clients[service] = AsyncClient(base_url=url)
    
    async def teardown(self):
        """Clean up after tests"""
        # Run cleanup tasks
        for task in self.cleanup_tasks:
            try:
                await task()
            except Exception as e:
                print(f"Warning: Cleanup task failed: {e}")
        
        # Close clients
        for client in self.clients.values():
            await client.aclose()
    
    def get_client(self, service: str, version: str = "v2") -> AsyncClient:
        """Get HTTP client for service"""
        if service not in self.clients:
            raise ValueError(f"Unknown service: {service}")
        
        client = self.clients[service]
        
        # Adjust base URL for version
        if version == "v2":
            # Ensure /api/v2 prefix
            if "/api/v2" not in str(client.base_url):
                client.base_url = f"{client.base_url}/api/v2"
        elif version == "v1":
            # Remove /api/v2 if present
            base_str = str(client.base_url).replace("/api/v2", "")
            client.base_url = base_str
        
        return client
    
    def register_cleanup(self, task: Callable):
        """Register cleanup task to run after test"""
        self.cleanup_tasks.append(task)
    
    def get_test_data(self, key: str) -> Any:
        """Get test data by key"""
        return self.test_data.get(key)
    
    def set_test_data(self, key: str, value: Any):
        """Store test data by key"""
        self.test_data[key] = value
