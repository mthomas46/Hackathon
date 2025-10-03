"""
Unit tests for Artifact Linker - Phase 3 Day 2
Tests for artifact linking functionality across services.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.memory_agent.domain.entities.memory_context import (
    MemoryContext,
    ArtifactLink,
    WorkflowType
)
from services.memory_agent.domain.services.artifact_linker import ArtifactLinker


@pytest.fixture
def artifact_linker():
    """Create ArtifactLinker instance for testing."""
    return ArtifactLinker(
        doc_store_url="http://test-doc-store:5140",
        prompt_store_url="http://test-prompt-store:5110",
        user_store_url="http://test-user-store:5130"
    )


@pytest.fixture
def sample_context():
    """Create sample memory context."""
    return MemoryContext(
        context_id="ctx_test_001",
        workflow_id="wf_test_001",
        parent_workflow_id=None,
        workflow_type=WorkflowType.ORCHESTRATION
    )


class TestArtifactLinker:
    """Test Artifact Linker service."""
    
    @pytest.mark.asyncio
    async def test_link_document(self, artifact_linker, sample_context):
        """Test linking a document from Doc Store."""
        document_id = "doc_12345"
        metadata = {"title": "Feature Breakdown", "type": "analysis"}
        
        artifact = await artifact_linker.link_document(
            context=sample_context,
            document_id=document_id,
            metadata=metadata,
            validate=False
        )
        
        # Verify artifact was created
        assert artifact.artifact_id == document_id
        assert artifact.artifact_type == "document"
        assert artifact.source_service == "doc-store"
        assert "test-doc-store:5140" in artifact.artifact_url
        assert artifact.metadata["title"] == "Feature Breakdown"
        
        # Verify it was added to context
        assert document_id in sample_context.linked_documents
        assert len(sample_context.linked_artifacts) == 1
    
    @pytest.mark.asyncio
    async def test_link_prompt(self, artifact_linker, sample_context):
        """Test linking a prompt from Prompt Store."""
        prompt_id = "prompt_67890"
        metadata = {"category": "decomposition", "version": "v2"}
        
        artifact = await artifact_linker.link_prompt(
            context=sample_context,
            prompt_id=prompt_id,
            metadata=metadata,
            validate=False
        )
        
        # Verify artifact was created
        assert artifact.artifact_id == prompt_id
        assert artifact.artifact_type == "prompt"
        assert artifact.source_service == "prompt-store"
        assert "test-prompt-store:5110" in artifact.artifact_url
        assert artifact.metadata["category"] == "decomposition"
        
        # Verify it was added to context
        assert prompt_id in sample_context.linked_prompts
        assert len(sample_context.linked_artifacts) == 1
    
    @pytest.mark.asyncio
    async def test_link_user(self, artifact_linker, sample_context):
        """Test linking a user from User Store."""
        user_id = "user_alice_001"
        metadata = {"role": "tech_lead", "team": "backend"}
        
        artifact = await artifact_linker.link_user(
            context=sample_context,
            user_id=user_id,
            metadata=metadata,
            validate=False
        )
        
        # Verify artifact was created
        assert artifact.artifact_id == user_id
        assert artifact.artifact_type == "user"
        assert artifact.source_service == "user-store"
        assert "test-user-store:5130" in artifact.artifact_url
        assert artifact.metadata["role"] == "tech_lead"
        
        # Verify it was added to context
        assert user_id in sample_context.linked_users
        assert len(sample_context.linked_artifacts) == 1
    
    @pytest.mark.asyncio
    async def test_link_custom_artifact(self, artifact_linker, sample_context):
        """Test linking a custom artifact."""
        artifact_id = "code_snippet_001"
        artifact_type = "code"
        source_service = "github"
        artifact_url = "https://github.com/org/repo/blob/main/file.py"
        metadata = {"language": "python", "lines": 150}
        
        artifact = await artifact_linker.link_custom_artifact(
            context=sample_context,
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            source_service=source_service,
            artifact_url=artifact_url,
            metadata=metadata
        )
        
        # Verify artifact was created
        assert artifact.artifact_id == artifact_id
        assert artifact.artifact_type == "code"
        assert artifact.source_service == "github"
        assert artifact.artifact_url == artifact_url
        assert artifact.metadata["language"] == "python"
        
        # Verify it was added to context
        assert len(sample_context.linked_artifacts) == 1
    
    @pytest.mark.asyncio
    async def test_get_all_artifacts(self, artifact_linker, sample_context):
        """Test retrieving all artifacts."""
        # Link multiple artifacts
        await artifact_linker.link_document(sample_context, "doc_1", validate=False)
        await artifact_linker.link_prompt(sample_context, "prompt_1", validate=False)
        await artifact_linker.link_user(sample_context, "user_1", validate=False)
        
        # Get all artifacts
        artifacts = await artifact_linker.get_all_artifacts(sample_context)
        
        assert len(artifacts) == 3
        artifact_types = [a.artifact_type for a in artifacts]
        assert "document" in artifact_types
        assert "prompt" in artifact_types
        assert "user" in artifact_types
    
    @pytest.mark.asyncio
    async def test_get_artifacts_by_type(self, artifact_linker, sample_context):
        """Test filtering artifacts by type."""
        # Link multiple artifacts
        await artifact_linker.link_document(sample_context, "doc_1", validate=False)
        await artifact_linker.link_document(sample_context, "doc_2", validate=False)
        await artifact_linker.link_prompt(sample_context, "prompt_1", validate=False)
        
        # Get documents only
        documents = await artifact_linker.get_artifacts_by_type(
            sample_context, "document"
        )
        
        assert len(documents) == 2
        assert all(a.artifact_type == "document" for a in documents)
    
    @pytest.mark.asyncio
    async def test_get_artifacts_by_service(self, artifact_linker, sample_context):
        """Test filtering artifacts by service."""
        # Link artifacts from different services
        await artifact_linker.link_document(sample_context, "doc_1", validate=False)
        await artifact_linker.link_prompt(sample_context, "prompt_1", validate=False)
        await artifact_linker.link_prompt(sample_context, "prompt_2", validate=False)
        
        # Get prompt-store artifacts only
        prompt_store_artifacts = await artifact_linker.get_artifacts_by_service(
            sample_context, "prompt-store"
        )
        
        assert len(prompt_store_artifacts) == 2
        assert all(a.source_service == "prompt-store" for a in prompt_store_artifacts)
    
    @pytest.mark.asyncio
    async def test_remove_artifact_link(self, artifact_linker, sample_context):
        """Test removing an artifact link."""
        document_id = "doc_to_remove"
        
        # Link document
        await artifact_linker.link_document(
            sample_context, document_id, validate=False
        )
        
        assert document_id in sample_context.linked_documents
        assert len(sample_context.linked_artifacts) == 1
        
        # Remove it
        removed = await artifact_linker.remove_artifact_link(
            sample_context, document_id
        )
        
        assert removed is True
        assert document_id not in sample_context.linked_documents
        assert len(sample_context.linked_artifacts) == 0
    
    @pytest.mark.asyncio
    async def test_get_cross_references(self, artifact_linker, sample_context):
        """Test getting cross-references between artifacts."""
        # Link various artifacts
        await artifact_linker.link_document(sample_context, "doc_1", validate=False)
        await artifact_linker.link_document(sample_context, "doc_2", validate=False)
        await artifact_linker.link_prompt(sample_context, "prompt_1", validate=False)
        await artifact_linker.link_user(sample_context, "user_1", validate=False)
        await artifact_linker.link_custom_artifact(
            sample_context,
            artifact_id="report_1",
            artifact_type="report",
            source_service="analysis-service",
            artifact_url="http://analysis:8004/reports/report_1"
        )
        
        # Get cross-references
        cross_refs = await artifact_linker.get_cross_references(sample_context)
        
        # Verify structure
        assert "documents" in cross_refs
        assert "prompts" in cross_refs
        assert "users" in cross_refs
        assert "all_artifacts" in cross_refs
        assert "by_type" in cross_refs
        assert "by_service" in cross_refs
        
        # Verify counts
        assert len(cross_refs["documents"]) == 2
        assert len(cross_refs["prompts"]) == 1
        assert len(cross_refs["users"]) == 1
        assert len(cross_refs["all_artifacts"]) == 5
        
        # Verify groupings
        assert "document" in cross_refs["by_type"]
        assert "report" in cross_refs["by_type"]
        assert "doc-store" in cross_refs["by_service"]
        assert "analysis-service" in cross_refs["by_service"]
    
    @pytest.mark.asyncio
    async def test_bulk_link_documents(self, artifact_linker, sample_context):
        """Test bulk linking of documents."""
        document_ids = ["doc_1", "doc_2", "doc_3", "doc_4", "doc_5"]
        metadata = {"batch": "import_001"}
        
        artifacts = await artifact_linker.bulk_link_documents(
            context=sample_context,
            document_ids=document_ids,
            metadata=metadata
        )
        
        assert len(artifacts) == 5
        assert len(sample_context.linked_documents) == 5
        assert all(a.metadata["batch"] == "import_001" for a in artifacts)
    
    @pytest.mark.asyncio
    async def test_bulk_link_prompts(self, artifact_linker, sample_context):
        """Test bulk linking of prompts."""
        prompt_ids = ["prompt_1", "prompt_2", "prompt_3"]
        metadata = {"category": "workflow_templates"}
        
        artifacts = await artifact_linker.bulk_link_prompts(
            context=sample_context,
            prompt_ids=prompt_ids,
            metadata=metadata
        )
        
        assert len(artifacts) == 3
        assert len(sample_context.linked_prompts) == 3
        assert all(a.metadata["category"] == "workflow_templates" for a in artifacts)
    
    @pytest.mark.asyncio
    async def test_bulk_link_users(self, artifact_linker, sample_context):
        """Test bulk linking of users."""
        user_ids = ["user_alice", "user_bob"]
        metadata = {"team": "backend"}
        
        artifacts = await artifact_linker.bulk_link_users(
            context=sample_context,
            user_ids=user_ids,
            metadata=metadata
        )
        
        assert len(artifacts) == 2
        assert len(sample_context.linked_users) == 2
        assert all(a.metadata["team"] == "backend" for a in artifacts)
    
    @pytest.mark.asyncio
    async def test_validate_all_artifacts_without_httpx(self, artifact_linker, sample_context):
        """Test validation when httpx is not available."""
        await artifact_linker.link_document(sample_context, "doc_1", validate=False)
        
        with patch('services.memory_agent.domain.services.artifact_linker.httpx', None):
            report = await artifact_linker.validate_all_artifacts(sample_context)
            
            assert report["validated"] is False
            assert report["reason"] == "httpx not available"
            assert report["total_artifacts"] == 1
    
    @pytest.mark.asyncio
    async def test_context_versioning_on_link(self, artifact_linker, sample_context):
        """Test that linking increments context version."""
        initial_version = sample_context.version
        
        await artifact_linker.link_document(sample_context, "doc_1", validate=False)
        
        # Version should increment twice: once for artifact link, once for document list
        assert sample_context.version > initial_version
    
    @pytest.mark.asyncio
    async def test_duplicate_prevention(self, artifact_linker, sample_context):
        """Test that duplicate document IDs are prevented."""
        document_id = "doc_duplicate"
        
        # Link same document twice
        await artifact_linker.link_document(sample_context, document_id, validate=False)
        await artifact_linker.link_document(sample_context, document_id, validate=False)
        
        # Should only appear once in linked_documents
        assert sample_context.linked_documents.count(document_id) == 1
        
        # But might have multiple artifact links (different timestamps)
        doc_artifacts = await artifact_linker.get_artifacts_by_type(
            sample_context, "document"
        )
        # Could be 1 or 2 depending on implementation
        assert len(doc_artifacts) >= 1
    
    @pytest.mark.asyncio
    async def test_remove_nonexistent_artifact(self, artifact_linker, sample_context):
        """Test removing an artifact that doesn't exist."""
        removed = await artifact_linker.remove_artifact_link(
            sample_context, "nonexistent_id"
        )
        
        assert removed is False
    
    @pytest.mark.asyncio
    async def test_artifact_metadata_preserved(self, artifact_linker, sample_context):
        """Test that artifact metadata is preserved."""
        metadata = {
            "title": "Important Document",
            "author": "Alice",
            "created": "2025-01-01",
            "tags": ["urgent", "feature"]
        }
        
        artifact = await artifact_linker.link_document(
            context=sample_context,
            document_id="doc_metadata_test",
            metadata=metadata,
            validate=False
        )
        
        # Verify all metadata fields are preserved
        assert artifact.metadata["title"] == "Important Document"
        assert artifact.metadata["author"] == "Alice"
        assert artifact.metadata["tags"] == ["urgent", "feature"]
        
        # Retrieve and verify
        artifacts = await artifact_linker.get_all_artifacts(sample_context)
        retrieved_artifact = artifacts[0]
        assert retrieved_artifact.metadata == metadata
    
    @pytest.mark.asyncio
    async def test_multiple_artifact_types_in_context(self, artifact_linker, sample_context):
        """Test context with multiple artifact types."""
        # Link various types
        await artifact_linker.link_document(sample_context, "doc_1", validate=False)
        await artifact_linker.link_prompt(sample_context, "prompt_1", validate=False)
        await artifact_linker.link_user(sample_context, "user_1", validate=False)
        await artifact_linker.link_custom_artifact(
            sample_context,
            "code_1",
            "code",
            "github",
            "https://github.com/test"
        )
        
        # Verify all types present
        cross_refs = await artifact_linker.get_cross_references(sample_context)
        
        assert len(cross_refs["by_type"]) == 4
        assert "document" in cross_refs["by_type"]
        assert "prompt" in cross_refs["by_type"]
        assert "user" in cross_refs["by_type"]
        assert "code" in cross_refs["by_type"]
    
    @pytest.mark.asyncio
    async def test_empty_context_operations(self, artifact_linker, sample_context):
        """Test operations on empty context."""
        # Get artifacts from empty context
        artifacts = await artifact_linker.get_all_artifacts(sample_context)
        assert len(artifacts) == 0
        
        # Get cross-references from empty context
        cross_refs = await artifact_linker.get_cross_references(sample_context)
        assert len(cross_refs["documents"]) == 0
        assert len(cross_refs["prompts"]) == 0
        assert len(cross_refs["users"]) == 0
        
        # Try to remove from empty context
        removed = await artifact_linker.remove_artifact_link(sample_context, "any_id")
        assert removed is False


class TestArtifactLinkerIntegration:
    """Integration tests for Artifact Linker with other components."""
    
    @pytest.mark.asyncio
    async def test_artifact_linking_workflow(self, artifact_linker):
        """Test complete artifact linking workflow."""
        # Create context
        context = MemoryContext(
            context_id="ctx_workflow",
            workflow_id="wf_workflow",
            parent_workflow_id=None,
            workflow_type=WorkflowType.WORKFLOW_A
        )
        
        # Step 1: Link documents from decomposition
        await artifact_linker.link_document(
            context, "breakdown_doc_001",
            metadata={"stage": "decomposition"},
            validate=False
        )
        
        # Step 2: Link prompts used
        await artifact_linker.bulk_link_prompts(
            context,
            ["prompt_decomp_001", "prompt_decomp_002"],
            metadata={"workflow": "decomposition"}
        )
        
        # Step 3: Link team members
        await artifact_linker.bulk_link_users(
            context,
            ["user_alice", "user_bob"],
            metadata={"assigned": True}
        )
        
        # Verify complete workflow
        all_artifacts = await artifact_linker.get_all_artifacts(context)
        assert len(all_artifacts) == 5  # 1 doc + 2 prompts + 2 users
        
        # Verify cross-references
        cross_refs = await artifact_linker.get_cross_references(context)
        assert len(cross_refs["documents"]) == 1
        assert len(cross_refs["prompts"]) == 2
        assert len(cross_refs["users"]) == 2

