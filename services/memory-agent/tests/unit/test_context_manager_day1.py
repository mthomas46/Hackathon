"""
Unit tests for Context Manager - Phase 3 Day 1
Tests for enhanced context storage functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from services.memory_agent.domain.entities.memory_context import (
    MemoryContext,
    WorkflowResult,
    ArtifactLink,
    WorkflowType
)
from services.memory_agent.domain.services.context_manager import ContextManager


@pytest.fixture
def context_manager():
    """Create ContextManager instance for testing."""
    return ContextManager(redis_client=None)  # Use local cache for tests


@pytest.fixture
def sample_workflow_result():
    """Create sample workflow result."""
    return WorkflowResult(
        result_id="result_test_001",
        workflow_id="wf_test_001",
        workflow_type=WorkflowType.WORKFLOW_A,
        result_data={"status": "success", "features": 5},
        success=True,
        duration_ms=1500.0,
        services_called=["llm-gateway", "prompt-store"]
    )


@pytest.fixture
def sample_artifact_link():
    """Create sample artifact link."""
    return ArtifactLink(
        artifact_id="doc_12345",
        artifact_type="document",
        source_service="doc-store",
        artifact_url="http://doc-store:5140/documents/doc_12345",
        metadata={"title": "Feature Breakdown"}
    )


class TestMemoryContext:
    """Test Memory Context dataclass."""
    
    def test_memory_context_creation(self):
        """Test creating a basic memory context."""
        context = MemoryContext(
            context_id="ctx_001",
            workflow_id="wf_001",
            parent_workflow_id=None,
            workflow_type=WorkflowType.ORCHESTRATION
        )
        
        assert context.context_id == "ctx_001"
        assert context.workflow_id == "wf_001"
        assert context.workflow_type == WorkflowType.ORCHESTRATION
        assert context.version == 1
        assert context.ttl_seconds == 86400  # 24 hours default
        assert context.expires_at is not None
    
    def test_memory_context_ttl_initialization(self):
        """Test TTL is correctly initialized."""
        now = datetime.utcnow()
        context = MemoryContext(
            context_id="ctx_002",
            workflow_id="wf_002",
            parent_workflow_id=None,
            workflow_type=WorkflowType.WORKFLOW_A,
            ttl_seconds=3600  # 1 hour
        )
        
        expected_expiry = now + timedelta(seconds=3600)
        assert context.expires_at is not None
        # Check within 10 seconds tolerance
        assert abs((context.expires_at - expected_expiry).total_seconds()) < 10
    
    def test_add_workflow_result(self, sample_workflow_result):
        """Test adding workflow result to context."""
        context = MemoryContext(
            context_id="ctx_003",
            workflow_id="wf_003",
            parent_workflow_id=None,
            workflow_type=WorkflowType.ORCHESTRATION
        )
        
        initial_version = context.version
        context.add_workflow_result(sample_workflow_result)
        
        assert len(context.workflow_results) == 1
        assert "wf_test_001" in context.workflow_results
        assert context.version == initial_version + 1
    
    def test_link_document(self):
        """Test linking a document."""
        context = MemoryContext(
            context_id="ctx_004",
            workflow_id="wf_004",
            parent_workflow_id=None,
            workflow_type=WorkflowType.WORKFLOW_B
        )
        
        context.link_document("doc_123")
        assert "doc_123" in context.linked_documents
        
        # Test duplicate prevention
        context.link_document("doc_123")
        assert context.linked_documents.count("doc_123") == 1
    
    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        context = MemoryContext(
            context_id="ctx_005",
            workflow_id="wf_005",
            parent_workflow_id=None,
            workflow_type=WorkflowType.ORCHESTRATION
        )
        
        # Add successful workflows
        for i in range(3):
            result = WorkflowResult(
                result_id=f"result_{i}",
                workflow_id=f"wf_{i}",
                workflow_type=WorkflowType.WORKFLOW_A,
                result_data={},
                success=True
            )
            context.add_workflow_result(result)
        
        # Add failed workflow
        failed_result = WorkflowResult(
            result_id="result_failed",
            workflow_id="wf_failed",
            workflow_type=WorkflowType.WORKFLOW_B,
            result_data={},
            success=False,
            error_message="Test error"
        )
        context.add_workflow_result(failed_result)
        
        assert context.total_workflows == 4
        assert context.successful_workflows == 3
        assert context.failed_workflows == 1
        assert context.success_rate == 0.75  # 3/4
    
    def test_is_expired(self):
        """Test expiration checking."""
        # Create expired context
        past_time = datetime.utcnow() - timedelta(hours=25)
        context = MemoryContext(
            context_id="ctx_006",
            workflow_id="wf_006",
            parent_workflow_id=None,
            workflow_type=WorkflowType.WORKFLOW_C,
            ttl_seconds=86400
        )
        context.created_at = past_time
        context.expires_at = past_time + timedelta(seconds=86400)
        
        assert context.is_expired()
    
    def test_extend_ttl(self):
        """Test extending TTL."""
        context = MemoryContext(
            context_id="ctx_007",
            workflow_id="wf_007",
            parent_workflow_id=None,
            workflow_type=WorkflowType.WORKFLOW_D,
            ttl_seconds=3600
        )
        
        original_expiry = context.expires_at
        context.extend_ttl(3600)  # Add 1 hour
        
        expected_expiry = original_expiry + timedelta(seconds=3600)
        assert abs((context.expires_at - expected_expiry).total_seconds()) < 1
    
    def test_to_dict_and_from_dict(self, sample_workflow_result, sample_artifact_link):
        """Test serialization and deserialization."""
        context = MemoryContext(
            context_id="ctx_008",
            workflow_id="wf_008",
            parent_workflow_id="parent_wf",
            workflow_type=WorkflowType.ORCHESTRATION,
            context_data={"key": "value"},
            metadata={"meta": "data"}
        )
        
        context.add_workflow_result(sample_workflow_result)
        context.add_artifact_link(sample_artifact_link)
        context.link_document("doc_456")
        context.link_prompt("prompt_789")
        context.link_user("user_012")
        
        # Convert to dict
        context_dict = context.to_dict()
        
        assert context_dict["context_id"] == "ctx_008"
        assert context_dict["workflow_id"] == "wf_008"
        assert context_dict["parent_workflow_id"] == "parent_wf"
        assert len(context_dict["workflow_results"]) == 1
        assert len(context_dict["linked_artifacts"]) == 1
        assert "doc_456" in context_dict["linked_documents"]
        
        # Convert back from dict
        reconstructed = MemoryContext.from_dict(context_dict)
        
        assert reconstructed.context_id == context.context_id
        assert reconstructed.workflow_id == context.workflow_id
        assert reconstructed.workflow_type == context.workflow_type
        assert len(reconstructed.workflow_results) == 1
        assert len(reconstructed.linked_artifacts) == 1


class TestContextManager:
    """Test Context Manager service."""
    
    @pytest.mark.asyncio
    async def test_create_context(self, context_manager):
        """Test creating a new context."""
        context = await context_manager.create_context(
            workflow_id="wf_new_001",
            workflow_type=WorkflowType.ORCHESTRATION,
            context_data={"initial": "data"},
            ttl_seconds=7200
        )
        
        assert context.workflow_id == "wf_new_001"
        assert context.workflow_type == WorkflowType.ORCHESTRATION
        assert context.context_data["initial"] == "data"
        assert context.ttl_seconds == 7200
    
    @pytest.mark.asyncio
    async def test_store_workflow_result(self, context_manager):
        """Test storing a workflow result."""
        result = await context_manager.store_workflow_result(
            workflow_id="wf_store_001",
            workflow_type=WorkflowType.WORKFLOW_A,
            result_data={"features": 10, "tasks": 25},
            success=True,
            duration_ms=2500.0,
            services_called=["llm-gateway", "prompt-store", "analysis-service"]
        )
        
        assert result.workflow_id == "wf_store_001"
        assert result.success is True
        assert result.duration_ms == 2500.0
        assert len(result.services_called) == 3
        
        # Verify it was stored
        context = await context_manager.get_context("wf_store_001")
        assert context is not None
        assert len(context.workflow_results) == 1
    
    @pytest.mark.asyncio
    async def test_get_context(self, context_manager):
        """Test retrieving a context."""
        # Create context first
        await context_manager.create_context(
            workflow_id="wf_get_001",
            workflow_type=WorkflowType.WORKFLOW_B
        )
        
        # Retrieve it
        context = await context_manager.get_context("wf_get_001")
        
        assert context is not None
        assert context.workflow_id == "wf_get_001"
    
    @pytest.mark.asyncio
    async def test_get_workflow_history(self, context_manager):
        """Test getting workflow history."""
        # Create multiple workflows of same type
        for i in range(5):
            await context_manager.store_workflow_result(
                workflow_id=f"wf_history_{i}",
                workflow_type=WorkflowType.WORKFLOW_A,
                result_data={"iteration": i},
                success=True
            )
        
        # Get history
        history = await context_manager.get_workflow_history(
            workflow_type=WorkflowType.WORKFLOW_A,
            limit=3
        )
        
        assert len(history) > 0
        assert len(history) <= 3
        assert all(isinstance(r, WorkflowResult) for r in history)
    
    @pytest.mark.asyncio
    async def test_aggregate_workflow_results(self, context_manager):
        """Test aggregating child workflow results."""
        parent_id = "parent_wf_001"
        
        # Create parent context
        await context_manager.create_context(
            workflow_id=parent_id,
            workflow_type=WorkflowType.ORCHESTRATION
        )
        
        # Create child workflows
        for i in range(4):
            await context_manager.store_workflow_result(
                workflow_id=f"child_wf_{i}",
                workflow_type=WorkflowType.WORKFLOW_A if i < 2 else WorkflowType.WORKFLOW_B,
                parent_workflow_id=parent_id,
                result_data={"child": i},
                success=(i < 3)  # One failure
            )
        
        # Aggregate
        aggregated = await context_manager.aggregate_workflow_results(parent_id)
        
        assert aggregated["parent_workflow_id"] == parent_id
        assert aggregated["total_child_workflows"] == 4
        assert aggregated["successful_workflows"] == 3
        assert aggregated["failed_workflows"] == 1
    
    @pytest.mark.asyncio
    async def test_synthesize_context(self, context_manager):
        """Test synthesizing unified context view."""
        workflow_id = "wf_synthesize_001"
        
        # Create main workflow
        await context_manager.store_workflow_result(
            workflow_id=workflow_id,
            workflow_type=WorkflowType.ORCHESTRATION,
            result_data={"main": "result"},
            success=True
        )
        
        # Add child workflows
        for i in range(2):
            await context_manager.store_workflow_result(
                workflow_id=f"child_synth_{i}",
                workflow_type=WorkflowType.WORKFLOW_A,
                parent_workflow_id=workflow_id,
                result_data={"child": i},
                success=True
            )
        
        # Synthesize
        synthesized = await context_manager.synthesize_context(workflow_id)
        
        assert synthesized["workflow_id"] == workflow_id
        assert "total_workflows" in synthesized
        assert "successful_workflows" in synthesized
        assert "failed_workflows" in synthesized
        assert "child_workflows" in synthesized
    
    @pytest.mark.asyncio
    async def test_delete_context(self, context_manager):
        """Test deleting a context."""
        workflow_id = "wf_delete_001"
        
        # Create context
        await context_manager.create_context(
            workflow_id=workflow_id,
            workflow_type=WorkflowType.WORKFLOW_C
        )
        
        # Verify it exists
        context = await context_manager.get_context(workflow_id)
        assert context is not None
        
        # Delete it
        deleted = await context_manager.delete_context(workflow_id)
        assert deleted is True
        
        # Verify it's gone
        context_after = await context_manager.get_context(workflow_id)
        assert context_after is None


class TestArtifactLink:
    """Test Artifact Link dataclass."""
    
    def test_artifact_link_creation(self):
        """Test creating an artifact link."""
        artifact = ArtifactLink(
            artifact_id="art_001",
            artifact_type="document",
            source_service="doc-store",
            artifact_url="http://doc-store:5140/documents/art_001"
        )
        
        assert artifact.artifact_id == "art_001"
        assert artifact.artifact_type == "document"
        assert artifact.source_service == "doc-store"
    
    def test_artifact_link_serialization(self):
        """Test artifact link to/from dict."""
        artifact = ArtifactLink(
            artifact_id="art_002",
            artifact_type="prompt",
            source_service="prompt-store",
            artifact_url="http://prompt-store:5110/prompts/art_002",
            metadata={"category": "decomposition"}
        )
        
        # To dict
        artifact_dict = artifact.to_dict()
        assert artifact_dict["artifact_id"] == "art_002"
        assert artifact_dict["metadata"]["category"] == "decomposition"
        
        # From dict
        reconstructed = ArtifactLink.from_dict(artifact_dict)
        assert reconstructed.artifact_id == artifact.artifact_id
        assert reconstructed.artifact_type == artifact.artifact_type


class TestWorkflowResult:
    """Test Workflow Result dataclass."""
    
    def test_workflow_result_creation(self):
        """Test creating a workflow result."""
        result = WorkflowResult(
            result_id="res_001",
            workflow_id="wf_001",
            workflow_type=WorkflowType.WORKFLOW_D,
            result_data={"team_size": 5, "capacity": 100},
            success=True,
            duration_ms=3000.0
        )
        
        assert result.result_id == "res_001"
        assert result.workflow_id == "wf_001"
        assert result.workflow_type == WorkflowType.WORKFLOW_D
        assert result.success is True
    
    def test_add_artifact_to_result(self, sample_artifact_link):
        """Test adding artifacts to a result."""
        result = WorkflowResult(
            result_id="res_002",
            workflow_id="wf_002",
            workflow_type=WorkflowType.WORKFLOW_A,
            result_data={},
            success=True
        )
        
        result.add_artifact(sample_artifact_link)
        assert len(result.artifacts) == 1
        assert result.artifacts[0].artifact_id == "doc_12345"
    
    def test_workflow_result_serialization(self):
        """Test workflow result to/from dict."""
        result = WorkflowResult(
            result_id="res_003",
            workflow_id="wf_003",
            workflow_type=WorkflowType.WORKFLOW_B,
            result_data={"sources": 50, "relevance": 0.85},
            success=True,
            duration_ms=4500.0,
            services_called=["source-agent", "doc-store", "memory-agent"]
        )
        
        # To dict
        result_dict = result.to_dict()
        assert result_dict["result_id"] == "res_003"
        assert result_dict["workflow_type"] == "workflow_b"
        assert len(result_dict["services_called"]) == 3
        
        # From dict
        reconstructed = WorkflowResult.from_dict(result_dict)
        assert reconstructed.result_id == result.result_id
        assert reconstructed.workflow_type == result.workflow_type
        assert reconstructed.success == result.success

