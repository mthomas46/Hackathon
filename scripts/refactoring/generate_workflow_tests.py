#!/usr/bin/env python3
"""
Generate Workflow Test Templates

This script generates workflow test templates based on service analysis.

Usage:
    python scripts/refactoring/generate_workflow_tests.py <service-name>
    
Example:
    python scripts/refactoring/generate_workflow_tests.py doc_store
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class WorkflowTestGenerator:
    """Generate workflow test templates for a service"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.service_path = project_root / "services" / service_name
        if not self.service_path.exists():
            self.service_path = project_root / "services" / service_name.replace("-", "_")
        self.workflows: List[Dict] = []
        
    def analyze_service(self):
        """Analyze service to identify workflows"""
        print(f"🔍 Analyzing {self.service_name} for workflows...")
        
        # Load audit data if available
        audit_file = project_root / "docs" / "refactoring" / "audits" / f"{self.service_name}_audit.json"
        if audit_file.exists():
            with open(audit_file) as f:
                audit_data = json.load(f)
                endpoints = audit_data.get("api_endpoints", {}).get("endpoints", [])
                dependencies = audit_data.get("dependencies", {})
                
                print(f"   Found {len(endpoints)} endpoints")
                print(f"   Found dependencies: {dependencies.get('total_dependencies', 0)}")
        
        # Identify common workflows
        self._identify_crud_workflows()
        self._identify_integration_workflows()
        self._identify_version_compatibility_workflows()
        
        print(f"   ✓ Identified {len(self.workflows)} workflows")
    
    def _identify_crud_workflows(self):
        """Identify CRUD workflows"""
        self.workflows.append({
            "name": "create_retrieve_workflow",
            "description": "Create resource and retrieve it",
            "type": "single_service",
            "steps": [
                "Create resource via POST",
                "Retrieve resource via GET",
                "Verify data matches"
            ]
        })
        
        self.workflows.append({
            "name": "full_crud_workflow",
            "description": "Complete CRUD lifecycle",
            "type": "single_service",
            "steps": [
                "Create resource",
                "Read resource",
                "Update resource",
                "Delete resource",
                "Verify deletion"
            ]
        })
    
    def _identify_integration_workflows(self):
        """Identify integration workflows"""
        # Common integration patterns
        integrations = {
            "doc_store": ["analysis-service", "source-agent", "prompt_store"],
            "analysis-service": ["doc_store", "notification-service"],
            "source-agent": ["doc_store", "github-mcp"],
        }
        
        if self.service_name in integrations:
            for dep_service in integrations[self.service_name]:
                self.workflows.append({
                    "name": f"{self.service_name}_to_{dep_service}_workflow",
                    "description": f"Integration with {dep_service}",
                    "type": "integration",
                    "services": [self.service_name, dep_service],
                    "steps": [
                        f"Create data in {self.service_name}",
                        f"Trigger processing in {dep_service}",
                        "Wait for completion",
                        "Verify results"
                    ]
                })
    
    def _identify_version_compatibility_workflows(self):
        """Identify version compatibility workflows"""
        self.workflows.append({
            "name": "v1_to_v2_compatibility",
            "description": "Test v1 client with v2 backend",
            "type": "compatibility",
            "steps": [
                "Create via v1 API",
                "Process via v2 API",
                "Retrieve via v1 API",
                "Verify compatibility"
            ]
        })
        
        self.workflows.append({
            "name": "v2_to_v1_compatibility",
            "description": "Test v2 client with v1 backend",
            "type": "compatibility",
            "steps": [
                "Create via v2 API",
                "Process via v1 API",
                "Retrieve via v2 API",
                "Verify compatibility"
            ]
        })
    
    def generate_test_file(self) -> str:
        """Generate workflow test file"""
        test_content = self._generate_test_header()
        test_content += self._generate_test_class()
        test_content += self._generate_helper_methods()
        
        return test_content
    
    def _generate_test_header(self) -> str:
        """Generate test file header"""
        return f'''"""
Workflow Tests for {self.service_name}

Generated: {datetime.now().isoformat()}
Auto-generated by: generate_workflow_tests.py

These tests verify end-to-end workflows for the {self.service_name} service,
including single-service workflows, multi-service integrations, and
version compatibility.
"""

import pytest
import asyncio
from typing import Dict, Any
from httpx import AsyncClient

pytestmark = pytest.mark.workflow


@pytest.fixture
async def service_client(workflow_context):
    """Get HTTP client for {self.service_name}"""
    return workflow_context.get_client("{self.service_name}", "v2")


@pytest.fixture
async def v1_client(workflow_context):
    """Get HTTP client for {self.service_name} v1"""
    return workflow_context.get_client("{self.service_name}", "v1")


'''
    
    def _generate_test_class(self) -> str:
        """Generate test class with workflow methods"""
        content = f'''@pytest.mark.asyncio
class Test{self._to_class_name(self.service_name)}Workflows:
    """
    Workflow tests for {self.service_name}
    
    Tests both v1 (legacy) and v2 (refactored) implementations.
    """
    
    # Test data
    SAMPLE_DATA = {{
        "title": "Test Resource",
        "description": "This is test data for workflow testing"
    }}
    
'''
        
        # Generate test methods for each workflow
        for workflow in self.workflows:
            content += self._generate_workflow_test(workflow)
        
        return content
    
    def _generate_workflow_test(self, workflow: Dict) -> str:
        """Generate individual workflow test method"""
        method_name = workflow["name"]
        description = workflow["description"]
        workflow_type = workflow["type"]
        
        # Determine priority marker
        if workflow_type == "single_service":
            marker = "@pytest.mark.critical"
        elif workflow_type == "integration":
            marker = "@pytest.mark.integration"
        else:
            marker = "@pytest.mark.compatibility"
        
        content = f'''    {marker}
    async def test_{method_name}(self, workflow_context):
        """
        {description}
        
        Type: {workflow_type}
        Steps:
'''
        
        for i, step in enumerate(workflow["steps"], 1):
            content += f'        {i}. {step}\n'
        
        content += '        """\n'
        content += self._generate_workflow_implementation(workflow)
        content += '\n\n'
        
        return content
    
    def _generate_workflow_implementation(self, workflow: Dict) -> str:
        """Generate workflow test implementation"""
        workflow_type = workflow["type"]
        
        if workflow_type == "single_service":
            return self._generate_single_service_impl()
        elif workflow_type == "integration":
            return self._generate_integration_impl(workflow)
        elif workflow_type == "compatibility":
            return self._generate_compatibility_impl()
        else:
            return "        # TODO: Implement workflow test\n        pass"
    
    def _generate_single_service_impl(self) -> str:
        """Generate single-service workflow implementation"""
        return '''        # Step 1: Create resource
        client = workflow_context.get_client("{service}")
        create_response = await client.post(
            "/resources",
            json=self.SAMPLE_DATA
        )
        assert create_response.status_code == 201
        
        resource_id = create_response.json()["data"]["id"]
        
        # Register cleanup
        workflow_context.register_cleanup(
            lambda: client.delete(f"/resources/{{resource_id}}")
        )
        
        # Step 2: Retrieve resource
        get_response = await client.get(f"/resources/{{resource_id}}")
        assert get_response.status_code == 200
        
        # Step 3: Verify data
        resource_data = get_response.json()["data"]
        assert resource_data["title"] == self.SAMPLE_DATA["title"]
'''.format(service="{self.service_name}")
    
    def _generate_integration_impl(self, workflow: Dict) -> str:
        """Generate integration workflow implementation"""
        services = workflow.get("services", [])
        service_a = services[0] if len(services) > 0 else "service_a"
        service_b = services[1] if len(services) > 1 else "service_b"
        
        return f'''        # Step 1: Create in {service_a}
        client_a = workflow_context.get_client("{service_a}", "v2")
        create_response = await client_a.post("/resources", json=self.SAMPLE_DATA)
        resource_id = create_response.json()["data"]["id"]
        
        # Step 2: Trigger processing in {service_b}
        client_b = workflow_context.get_client("{service_b}", "v2")
        process_response = await client_b.post(
            "/process",
            json={{"resource_id": resource_id}}
        )
        assert process_response.status_code == 200
        
        # Step 3: Wait for completion
        job_id = process_response.json()["data"]["id"]
        await self._wait_for_job_completion(client_b, job_id)
        
        # Step 4: Verify results
        result_response = await client_b.get(f"/jobs/{{job_id}}/result")
        assert result_response.status_code == 200
        assert result_response.json()["data"]["status"] == "completed"
'''
    
    def _generate_compatibility_impl(self) -> str:
        """Generate compatibility workflow implementation"""
        return '''        # Step 1: Create via v1
        v1_client = workflow_context.get_client("{service}", "v1")
        v1_response = await v1_client.post("/resources", json=self.SAMPLE_DATA)
        resource_id = v1_response.json()["id"]
        
        # Step 2: Process via v2
        v2_client = workflow_context.get_client("{service}", "v2")
        v2_response = await v2_client.post(
            "/process",
            json={{"resource_id": resource_id}}
        )
        assert v2_response.status_code == 200
        
        # Step 3: Retrieve via v1
        retrieve_response = await v1_client.get(f"/resources/{{resource_id}}")
        assert retrieve_response.status_code == 200
        
        # Step 4: Verify v1 can see v2 changes
        data = retrieve_response.json()
        assert "processed" in data
        assert data["processed"] is True
        
        # Step 5: Verify deprecation headers
        assert "X-API-Deprecation" in retrieve_response.headers
'''.format(service="{self.service_name}")
    
    def _generate_helper_methods(self) -> str:
        """Generate helper methods"""
        return '''    # Helper methods
    
    async def _wait_for_job_completion(
        self,
        client: AsyncClient,
        job_id: str,
        timeout: int = 30
    ):
        """Wait for job to complete"""
        for _ in range(timeout):
            response = await client.get(f"/jobs/{job_id}")
            status = response.json()["data"]["status"]
            
            if status == "completed":
                return
            elif status == "failed":
                raise AssertionError("Job failed")
            
            await asyncio.sleep(1)
        
        raise AssertionError(f"Job did not complete within {timeout} seconds")
    
    async def _cleanup_resource(self, client: AsyncClient, resource_id: str):
        """Clean up test resource"""
        try:
            await client.delete(f"/resources/{resource_id}")
        except Exception as e:
            print(f"Warning: Could not clean up resource {resource_id}: {e}")
'''
    
    def _to_class_name(self, service_name: str) -> str:
        """Convert service name to class name"""
        # doc_store -> DocStore
        # analysis-service -> AnalysisService
        parts = service_name.replace("-", "_").split("_")
        return "".join(part.capitalize() for part in parts)
    
    def save_test_file(self, content: str) -> Path:
        """Save test file"""
        # Create tests/workflows directory if it doesn't exist
        workflows_dir = project_root / "tests" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test file
        test_file = workflows_dir / f"test_{self.service_name}_workflows.py"
        
        with open(test_file, 'w') as f:
            f.write(content)
        
        print(f"✅ Generated workflow tests: {test_file}")
        return test_file
    
    def generate_conftest_if_needed(self):
        """Generate conftest.py if it doesn't exist"""
        workflows_dir = project_root / "tests" / "workflows"
        conftest_file = workflows_dir / "conftest.py"
        
        if conftest_file.exists():
            print("   ℹ️  conftest.py already exists")
            return
        
        conftest_content = '''"""
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
'''
        
        with open(conftest_file, 'w') as f:
            f.write(conftest_content)
        
        print(f"✅ Generated conftest.py: {conftest_file}")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python generate_workflow_tests.py <service-name>")
        print("\nExamples:")
        print("  python generate_workflow_tests.py doc_store")
        print("  python generate_workflow_tests.py analysis-service")
        sys.exit(1)
    
    service_name = sys.argv[1]
    
    print(f"🔧 Generating workflow tests for: {service_name}")
    print("=" * 60)
    
    generator = WorkflowTestGenerator(service_name)
    
    # Analyze service
    generator.analyze_service()
    
    # Generate test file
    content = generator.generate_test_file()
    test_file = generator.save_test_file(content)
    
    # Generate conftest if needed
    generator.generate_conftest_if_needed()
    
    print("\n" + "=" * 60)
    print("Next steps:")
    print(f"1. Review generated tests: {test_file}")
    print("2. Customize workflows for your service")
    print("3. Run tests: pytest tests/workflows/ -v")
    print("=" * 60)


if __name__ == "__main__":
    main()

