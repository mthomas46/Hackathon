# 🔄 Workflow Testing Strategy - Realistic End-to-End Scenarios

**Version**: 1.0.0  
**Created**: October 8, 2025  
**Status**: Active

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Workflow Types](#workflow-types)
3. [Testing Approach](#testing-approach)
4. [Workflow Templates](#workflow-templates)
5. [Implementation Guide](#implementation-guide)
6. [Examples](#examples)

---

## 🎯 Overview

### Purpose

Workflow testing ensures that services work correctly not just in isolation, but in realistic end-to-end scenarios that mirror actual production usage. This is critical during refactoring to ensure:

- **No regressions** in service interactions
- **Backward compatibility** between API versions
- **Cross-version compatibility** (v1 client → v2 service or vice versa)
- **Data integrity** across service boundaries
- **Performance** under realistic load

### Key Principles

1. **Realistic Scenarios**: Test actual user workflows, not just happy paths
2. **Cross-Service**: Test service-to-service interactions
3. **Version Compatibility**: Test v1 and v2 interactions
4. **Data Validation**: Verify data consistency across services
5. **Error Handling**: Test failure scenarios and recovery

---

## 🔄 Workflow Types

### Type 1: Single-Service Workflows

**Purpose**: Verify refactored service works correctly

**Pattern**: User → Service (v2) → Database

**Example**: Create, Read, Update, Delete operations

```python
async def test_document_crud_workflow():
    # Create
    doc = await create_document()
    # Read
    retrieved = await get_document(doc.id)
    # Update
    updated = await update_document(doc.id, new_data)
    # Delete
    await delete_document(doc.id)
```

### Type 2: Service-to-Service Workflows

**Purpose**: Verify service interactions

**Pattern**: Service A → Service B → Service C

**Example**: Document creation triggers analysis

```python
async def test_document_analysis_workflow():
    # Create document (doc-store)
    doc = await doc_store.create_document()
    
    # Trigger analysis (analysis-service)
    analysis = await analysis_service.analyze(doc.id)
    
    # Verify analysis stored (doc-store)
    doc_with_analysis = await doc_store.get_document(doc.id)
    assert doc_with_analysis.analysis_results
```

### Type 3: Cross-Version Workflows

**Purpose**: Verify v1 and v2 compatibility

**Pattern**: v1 Service → v2 Service → v1 Service

**Example**: v1 client uses v2 backend

```python
async def test_cross_version_workflow():
    # Create via v1 API
    doc_id = await v1_client.post("/documents", data)
    
    # Analyze via v2 API
    analysis = await v2_client.post("/api/v2/analyze", {"targets": [doc_id]})
    
    # Retrieve via v1 API (should include analysis)
    doc = await v1_client.get(f"/documents/{doc_id}")
    assert "analysis" in doc
```

### Type 4: Complex Multi-Service Workflows

**Purpose**: Verify complete user journeys

**Pattern**: Multiple services, multiple steps

**Example**: Complete document lifecycle

```python
async def test_document_lifecycle_workflow():
    # 1. User uploads document (source-agent)
    upload = await source_agent.upload_from_github(repo, file)
    
    # 2. Document stored (doc-store)
    doc_id = upload.document_id
    
    # 3. Analysis triggered (analysis-service)
    analysis = await analysis_service.analyze(doc_id)
    
    # 4. Findings generated (analysis-service)
    findings = await analysis_service.get_findings(analysis.id)
    
    # 5. Notifications sent (notification-service)
    await notification_service.notify_owners(findings)
    
    # 6. Prompt optimization (prompt-store)
    await prompt_store.optimize_based_on_findings(findings)
```

### Type 5: Failure Recovery Workflows

**Purpose**: Verify error handling and recovery

**Pattern**: Trigger failures, verify recovery

**Example**: Service unavailable scenario

```python
async def test_service_failure_recovery():
    # Create document
    doc = await doc_store.create_document()
    
    # Simulate analysis-service failure
    with analysis_service_down():
        # Should fail gracefully
        result = await trigger_analysis(doc.id)
        assert result.status == "pending"
        assert result.retry_count == 0
    
    # Service comes back
    # Should auto-retry and succeed
    await wait_for_retry()
    analysis = await get_analysis_status(doc.id)
    assert analysis.status == "completed"
```

---

## 🧪 Testing Approach

### Test Organization

```
tests/
├── workflows/                          # Workflow tests
│   ├── __init__.py
│   ├── conftest.py                    # Shared fixtures
│   ├── test_document_workflows.py     # Document-related workflows
│   ├── test_analysis_workflows.py     # Analysis workflows
│   ├── test_cross_service_workflows.py # Multi-service
│   └── test_version_compatibility.py   # v1/v2 compatibility
├── integration/                        # Service integration
└── e2e/                               # End-to-end
```

### Test Structure

Each workflow test follows this pattern:

```python
@pytest.mark.workflow
@pytest.mark.asyncio
class TestDocumentAnalysisWorkflow:
    """
    Workflow: Document Creation → Analysis → Results Retrieval
    Services: doc-store (v2), analysis-service (v2)
    User Story: As a developer, I want to analyze a document
    """
    
    async def test_happy_path(self, workflow_context):
        """Test successful workflow"""
        # Given: A document exists
        doc = await self.create_test_document(workflow_context)
        
        # When: Analysis is triggered
        analysis = await self.trigger_analysis(doc.id, workflow_context)
        
        # Then: Analysis completes successfully
        result = await self.wait_for_completion(analysis.id, workflow_context)
        assert result.status == "completed"
        
        # And: Results are retrievable
        findings = await self.get_findings(analysis.id, workflow_context)
        assert len(findings) > 0
        
        # And: Document is updated with analysis metadata
        updated_doc = await self.get_document(doc.id, workflow_context)
        assert updated_doc.last_analyzed_at is not None
    
    async def test_error_handling(self, workflow_context):
        """Test workflow error handling"""
        pass
    
    async def test_concurrent_workflows(self, workflow_context):
        """Test multiple concurrent workflows"""
        pass
```

### Workflow Context

**Shared context for workflow tests:**

```python
# tests/workflows/conftest.py

import pytest
from typing import Dict, Any
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
        # Create HTTP clients for each service
        self.clients["doc_store"] = AsyncClient(base_url="http://doc_store:5087")
        self.clients["analysis"] = AsyncClient(base_url="http://analysis:5020")
        self.clients["notification"] = AsyncClient(base_url="http://notification:5130")
        
        # Start with clean state
        await self.cleanup_test_data()
    
    async def teardown(self):
        """Clean up after tests"""
        # Run cleanup tasks
        for task in self.cleanup_tasks:
            await task()
        
        # Close clients
        for client in self.clients.values():
            await client.aclose()
    
    def get_client(self, service: str, version: str = "v2") -> AsyncClient:
        """Get HTTP client for service"""
        client = self.clients[service]
        if version == "v2":
            client.base_url = f"{client.base_url}/api/v2"
        return client
    
    def register_cleanup(self, task: Callable):
        """Register cleanup task to run after test"""
        self.cleanup_tasks.append(task)
```

---

## 📝 Workflow Templates

### Template 1: Create → Process → Retrieve

**Use Case**: Most common pattern (CRUD with processing)

```python
async def test_create_process_retrieve_workflow():
    """
    Steps:
    1. Create resource
    2. Trigger processing
    3. Wait for completion
    4. Retrieve results
    5. Verify data integrity
    """
    # Create
    resource = await create_resource()
    assert resource.id
    
    # Process
    job = await trigger_processing(resource.id)
    assert job.status == "pending"
    
    # Wait
    result = await wait_for_completion(job.id, timeout=30)
    assert result.status == "completed"
    
    # Retrieve
    processed = await get_resource(resource.id)
    assert processed.processed_at is not None
    
    # Verify
    assert processed.data == expected_data
```

### Template 2: Multi-Service Chain

**Use Case**: Data flows through multiple services

```python
async def test_multi_service_chain():
    """
    Flow: Service A → Service B → Service C → Service A
    
    Steps:
    1. Service A creates data
    2. Service B processes data
    3. Service C enriches data
    4. Service A stores final result
    """
    # Service A: Create
    data_id = await service_a.create(initial_data)
    
    # Service B: Process
    processed = await service_b.process(data_id)
    assert processed.status == "success"
    
    # Service C: Enrich
    enriched = await service_c.enrich(data_id)
    assert enriched.metadata is not None
    
    # Service A: Retrieve final
    final = await service_a.get(data_id)
    assert final.processed_by == ["service_b", "service_c"]
```

### Template 3: Event-Driven Workflow

**Use Case**: Services communicate via events

```python
async def test_event_driven_workflow():
    """
    Flow: Event → Handler → Result
    
    Steps:
    1. Publish event
    2. Wait for handlers
    3. Verify results
    """
    # Subscribe to result event
    result_received = asyncio.Event()
    
    async def result_handler(event):
        result_received.set()
    
    await subscribe("workflow.completed", result_handler)
    
    # Trigger workflow by publishing event
    await publish("workflow.started", {"data": "test"})
    
    # Wait for completion event
    await asyncio.wait_for(result_received.wait(), timeout=30)
    
    # Verify result
    result = await get_workflow_result()
    assert result.success
```

### Template 4: Backward Compatibility

**Use Case**: v1 and v2 API compatibility

```python
async def test_version_compatibility():
    """
    Test v1 client with v2 backend
    
    Steps:
    1. Create via v1
    2. Process via v2
    3. Retrieve via v1
    4. Verify compatibility
    """
    # Create via v1 API
    v1_response = await v1_client.post("/documents", v1_data)
    doc_id = v1_response["id"]
    
    # Process via v2 API
    v2_response = await v2_client.post(
        "/api/v2/analyze",
        {"targets": [doc_id]}
    )
    assert v2_response["data"]["status"] == "completed"
    
    # Retrieve via v1 API
    doc = await v1_client.get(f"/documents/{doc_id}")
    
    # Verify data is accessible via v1
    assert "analysis" in doc
    assert doc["analysis"]["status"] == "completed"
```

### Template 5: Failure and Recovery

**Use Case**: Testing resilience

```python
async def test_failure_recovery_workflow():
    """
    Test workflow handles failures gracefully
    
    Steps:
    1. Start workflow
    2. Inject failure
    3. Verify error handling
    4. Trigger recovery
    5. Verify completion
    """
    # Start workflow
    workflow_id = await start_workflow()
    
    # Inject failure
    await inject_failure("service_b")
    
    # Wait for error detection
    status = await wait_for_status(workflow_id, "error")
    assert status.error_count == 1
    assert status.retry_scheduled
    
    # Remove failure
    await remove_failure("service_b")
    
    # Wait for recovery
    final_status = await wait_for_status(workflow_id, "completed")
    assert final_status.retry_count == 1
    assert final_status.success
```

---

## 💻 Implementation Guide

### Step 1: Identify Key Workflows

**For each service, identify:**

1. **Primary Workflows**: Most common user actions
2. **Critical Workflows**: Business-critical operations
3. **Integration Points**: Where service interacts with others
4. **Edge Cases**: Unusual but important scenarios

**Example for `doc-store`:**

```
Primary Workflows:
1. Upload document → Store → Retrieve
2. Update document → Version → Retrieve history
3. Delete document → Cleanup → Verify deletion

Critical Workflows:
1. Bulk upload → Process → Index → Search
2. Document → Trigger analysis → Store results
3. Document → Generate embeddings → Enable semantic search

Integration Points:
- source-agent → doc-store (ingestion)
- doc-store → analysis-service (analysis)
- doc-store → prompt-store (prompt optimization)
- doc-store → search-service (indexing)

Edge Cases:
- Very large documents
- Concurrent updates
- Document with special characters
- Document deletion with active analysis
```

### Step 2: Create Workflow Test File

```python
# tests/workflows/test_doc_store_workflows.py

import pytest
from typing import Dict, Any
from .conftest import WorkflowContext

@pytest.mark.workflow
@pytest.mark.asyncio
class TestDocStoreWorkflows:
    """
    Workflow tests for doc-store service
    
    Tests both v1 (legacy) and v2 (refactored) implementations
    """
    
    # Test data
    SAMPLE_DOCUMENT = {
        "title": "Test Document",
        "content": "This is test content for workflow testing.",
        "metadata": {
            "author": "Test User",
            "tags": ["test", "workflow"]
        }
    }
    
    @pytest.mark.critical
    async def test_document_upload_and_retrieval(self, workflow_context: WorkflowContext):
        """
        Workflow: Upload → Store → Retrieve
        Services: doc-store v2
        Priority: Critical
        """
        # Step 1: Upload document
        client = workflow_context.get_client("doc_store", "v2")
        upload_response = await client.post(
            "/documents",
            json=self.SAMPLE_DOCUMENT
        )
        assert upload_response.status_code == 201
        
        doc_data = upload_response.json()["data"]
        doc_id = doc_data["id"]
        
        # Register cleanup
        workflow_context.register_cleanup(
            lambda: client.delete(f"/documents/{doc_id}")
        )
        
        # Step 2: Verify immediate retrieval
        get_response = await client.get(f"/documents/{doc_id}")
        assert get_response.status_code == 200
        
        retrieved = get_response.json()["data"]
        assert retrieved["title"] == self.SAMPLE_DOCUMENT["title"]
        assert retrieved["content"] == self.SAMPLE_DOCUMENT["content"]
        
        # Step 3: Verify searchability
        search_response = await client.get(
            "/documents",
            params={"search": "test content"}
        )
        assert search_response.status_code == 200
        
        search_results = search_response.json()["data"]
        assert any(doc["id"] == doc_id for doc in search_results)
    
    @pytest.mark.integration
    async def test_document_to_analysis_workflow(self, workflow_context: WorkflowContext):
        """
        Workflow: Create Doc → Trigger Analysis → Retrieve Results
        Services: doc-store v2, analysis-service v2
        Priority: High
        """
        # Step 1: Create document
        doc_client = workflow_context.get_client("doc_store", "v2")
        doc_response = await doc_client.post("/documents", json=self.SAMPLE_DOCUMENT)
        doc_id = doc_response.json()["data"]["id"]
        
        # Register cleanup
        workflow_context.register_cleanup(
            lambda: doc_client.delete(f"/documents/{doc_id}")
        )
        
        # Step 2: Trigger analysis
        analysis_client = workflow_context.get_client("analysis", "v2")
        analysis_response = await analysis_client.post(
            "/analyze",
            json={
                "targets": [doc_id],
                "analysis_types": ["quality", "semantic"]
            }
        )
        assert analysis_response.status_code == 200
        
        analysis_data = analysis_response.json()["data"]
        analysis_id = analysis_data["id"]
        
        # Step 3: Wait for completion
        import asyncio
        max_wait = 30  # seconds
        wait_interval = 1
        
        for _ in range(max_wait // wait_interval):
            status_response = await analysis_client.get(f"/analyses/{analysis_id}")
            status = status_response.json()["data"]["status"]
            
            if status == "completed":
                break
            elif status == "failed":
                pytest.fail("Analysis failed")
            
            await asyncio.sleep(wait_interval)
        else:
            pytest.fail(f"Analysis did not complete within {max_wait} seconds")
        
        # Step 4: Verify results
        results_response = await analysis_client.get(f"/analyses/{analysis_id}/results")
        assert results_response.status_code == 200
        
        results = results_response.json()["data"]
        assert "quality" in results
        assert "semantic" in results
        
        # Step 5: Verify document updated
        doc_response = await doc_client.get(f"/documents/{doc_id}")
        doc_data = doc_response.json()["data"]
        assert doc_data["analyzed_at"] is not None
        assert "quality_score" in doc_data
    
    @pytest.mark.compatibility
    async def test_v1_to_v2_compatibility(self, workflow_context: WorkflowContext):
        """
        Workflow: v1 Create → v2 Process → v1 Retrieve
        Services: doc-store (v1 and v2)
        Priority: High
        """
        # Step 1: Create via v1
        v1_client = workflow_context.get_client("doc_store", "v1")
        create_response = await v1_client.post(
            "/documents",  # v1 endpoint
            json={
                "title": self.SAMPLE_DOCUMENT["title"],
                "content": self.SAMPLE_DOCUMENT["content"]
            }
        )
        assert create_response.status_code == 201
        doc_id = create_response.json()["id"]
        
        # Register cleanup
        workflow_context.register_cleanup(
            lambda: v1_client.delete(f"/documents/{doc_id}")
        )
        
        # Step 2: Update via v2
        v2_client = workflow_context.get_client("doc_store", "v2")
        update_response = await v2_client.patch(
            f"/documents/{doc_id}",
            json={"metadata": {"updated_via": "v2"}}
        )
        assert update_response.status_code == 200
        
        # Step 3: Retrieve via v1
        v1_response = await v1_client.get(f"/documents/{doc_id}")
        assert v1_response.status_code == 200
        
        # Verify v1 can see v2 changes
        doc_data = v1_response.json()
        assert doc_data["metadata"]["updated_via"] == "v2"
        
        # Verify deprecation headers on v1
        assert "X-API-Deprecation" in v1_response.headers
```

### Step 3: Create Workflow Runner Script

```python
# scripts/refactoring/run_workflow_tests.py

#!/usr/bin/env python3
"""
Run workflow tests for a service

Usage:
    python scripts/refactoring/run_workflow_tests.py <service-name>
    
Example:
    python scripts/refactoring/run_workflow_tests.py doc_store
"""

import sys
import subprocess
from pathlib import Path

def run_workflow_tests(service_name: str, version: str = "both"):
    """Run workflow tests for a service"""
    
    print(f"🔄 Running workflow tests for: {service_name}")
    print(f"   Version: {version}")
    print("=" * 60)
    
    # Build pytest command
    cmd = [
        "pytest",
        f"tests/workflows/test_{service_name}_workflows.py",
        "-v",
        "-m", "workflow",
        "--tb=short",
        "--color=yes"
    ]
    
    if version == "v2":
        cmd.extend(["-k", "not v1"])
    elif version == "v1":
        cmd.extend(["-k", "v1 or compatibility"])
    
    # Run tests
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n✅ All workflow tests passed!")
    else:
        print("\n❌ Some workflow tests failed")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_workflow_tests.py <service-name> [version]")
        sys.exit(1)
    
    service = sys.argv[1]
    version = sys.argv[2] if len(sys.argv) > 2 else "both"
    
    run_workflow_tests(service, version)
```

---

## 📚 Examples

### Example 1: Document Lifecycle

**Complete document lifecycle workflow:**

```python
@pytest.mark.workflow
@pytest.mark.asyncio
async def test_complete_document_lifecycle(workflow_context):
    """
    Full document lifecycle:
    1. Upload from GitHub (source-agent)
    2. Store (doc-store)
    3. Analyze (analysis-service)
    4. Generate findings (analysis-service)
    5. Send notifications (notification-service)
    6. Archive (doc-store)
    """
    # 1. Upload
    source = workflow_context.get_client("source_agent", "v2")
    upload = await source.post("/github/import", json={
        "repo": "test/repo",
        "file": "README.md"
    })
    doc_id = upload.json()["data"]["document_id"]
    
    # 2. Verify stored
    docs = workflow_context.get_client("doc_store", "v2")
    doc = await docs.get(f"/documents/{doc_id}")
    assert doc.status_code == 200
    
    # 3. Analyze
    analysis = workflow_context.get_client("analysis", "v2")
    job = await analysis.post("/analyze", json={"targets": [doc_id]})
    analysis_id = job.json()["data"]["id"]
    
    # Wait for completion
    await wait_for_completion(analysis, analysis_id)
    
    # 4. Get findings
    findings = await analysis.get(f"/analyses/{analysis_id}/findings")
    assert findings.status_code == 200
    assert len(findings.json()["data"]) > 0
    
    # 5. Verify notification sent
    notifications = workflow_context.get_client("notification", "v2")
    sent = await notifications.get("/notifications", params={"document_id": doc_id})
    assert sent.status_code == 200
    assert len(sent.json()["data"]) > 0
    
    # 6. Archive
    archive = await docs.post(f"/documents/{doc_id}/archive")
    assert archive.status_code == 200
```

### Example 2: Performance Workflow

**Test workflow under load:**

```python
@pytest.mark.workflow
@pytest.mark.performance
@pytest.mark.asyncio
async def test_concurrent_document_workflows(workflow_context):
    """
    Test multiple concurrent workflows
    
    Simulates realistic load with multiple users
    """
    import asyncio
    
    async def run_single_workflow(workflow_id: int):
        """Single workflow instance"""
        client = workflow_context.get_client("doc_store", "v2")
        
        # Create
        doc = await client.post("/documents", json={
            "title": f"Concurrent Test {workflow_id}",
            "content": f"Content for workflow {workflow_id}"
        })
        doc_id = doc.json()["data"]["id"]
        
        # Process
        await asyncio.sleep(0.1)  # Simulate processing
        
        # Retrieve
        retrieved = await client.get(f"/documents/{doc_id}")
        assert retrieved.status_code == 200
        
        return doc_id
    
    # Run 50 concurrent workflows
    tasks = [run_single_workflow(i) for i in range(50)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Verify all succeeded
    failures = [r for r in results if isinstance(r, Exception)]
    assert len(failures) == 0, f"{len(failures)} workflows failed"
```

---

## ✅ Checklist

### For Each Service

**Before Refactoring**:
- [ ] Identify key workflows
- [ ] Document current behavior
- [ ] Create baseline workflow tests for v1

**During Refactoring**:
- [ ] Create v2 workflow tests
- [ ] Create cross-version compatibility tests
- [ ] Test incrementally as features complete

**After Refactoring**:
- [ ] Verify all workflows pass for v2
- [ ] Verify v1 compatibility workflows pass
- [ ] Run performance workflow tests
- [ ] Document any workflow changes

---

**Document Control**  
**Version**: 1.0.0  
**Last Updated**: October 8, 2025  
**Owner**: Hackathon Team

