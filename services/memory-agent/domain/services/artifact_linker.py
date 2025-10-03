"""
Artifact Linker - Phase 3 Day 2
Links workflow artifacts to external services (Doc Store, Prompt Store, User Store).
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    import httpx
except ImportError:
    httpx = None

from ..entities.memory_context import (
    ArtifactLink,
    MemoryContext
)


class ArtifactLinker:
    """
    Links artifacts across services for Phase 3.
    
    Responsibilities:
    - Link documents from Doc Store
    - Link prompts from Prompt Store
    - Link users from User Store
    - Manage cross-references between artifacts
    - Validate artifact existence
    
    Part of Enhanced Roadmap v2.0 Phase 3 implementation.
    """
    
    def __init__(
        self,
        doc_store_url: str = "http://doc-store:5140",
        prompt_store_url: str = "http://prompt-store:5110",
        user_store_url: str = "http://user-store:5130",
        timeout: float = 10.0
    ):
        """
        Initialize Artifact Linker.
        
        Args:
            doc_store_url: URL for Doc Store service
            prompt_store_url: URL for Prompt Store service
            user_store_url: URL for User Store service
            timeout: HTTP request timeout in seconds
        """
        self.doc_store_url = doc_store_url
        self.prompt_store_url = prompt_store_url
        self.user_store_url = user_store_url
        self.timeout = timeout
    
    async def link_document(
        self,
        context: MemoryContext,
        document_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        validate: bool = False
    ) -> ArtifactLink:
        """
        Link a Doc Store document to a context.
        
        Args:
            context: MemoryContext to link to
            document_id: Document ID in Doc Store
            metadata: Additional metadata for the link
            validate: Whether to validate document exists
            
        Returns:
            ArtifactLink instance
        """
        # Validate document exists if requested
        if validate and httpx:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(
                        f"{self.doc_store_url}/api/v1/documents/{document_id}"
                    )
                    if response.status_code != 200:
                        raise ValueError(f"Document {document_id} not found in Doc Store")
            except Exception as e:
                # Log but don't fail - validation is optional
                pass
        
        # Create artifact link
        artifact_url = f"{self.doc_store_url}/api/v1/documents/{document_id}"
        
        artifact = ArtifactLink(
            artifact_id=document_id,
            artifact_type="document",
            source_service="doc-store",
            artifact_url=artifact_url,
            metadata=metadata or {}
        )
        
        # Add to context
        context.add_artifact_link(artifact)
        context.link_document(document_id)
        
        return artifact
    
    async def link_prompt(
        self,
        context: MemoryContext,
        prompt_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        validate: bool = False
    ) -> ArtifactLink:
        """
        Link a Prompt Store prompt to a context.
        
        Args:
            context: MemoryContext to link to
            prompt_id: Prompt ID in Prompt Store
            metadata: Additional metadata for the link
            validate: Whether to validate prompt exists
            
        Returns:
            ArtifactLink instance
        """
        # Validate prompt exists if requested
        if validate and httpx:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(
                        f"{self.prompt_store_url}/api/v1/prompts/{prompt_id}"
                    )
                    if response.status_code != 200:
                        raise ValueError(f"Prompt {prompt_id} not found in Prompt Store")
            except Exception:
                pass
        
        # Create artifact link
        artifact_url = f"{self.prompt_store_url}/api/v1/prompts/{prompt_id}"
        
        artifact = ArtifactLink(
            artifact_id=prompt_id,
            artifact_type="prompt",
            source_service="prompt-store",
            artifact_url=artifact_url,
            metadata=metadata or {}
        )
        
        # Add to context
        context.add_artifact_link(artifact)
        context.link_prompt(prompt_id)
        
        return artifact
    
    async def link_user(
        self,
        context: MemoryContext,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        validate: bool = False
    ) -> ArtifactLink:
        """
        Link a User Store user to a context.
        
        Args:
            context: MemoryContext to link to
            user_id: User ID in User Store
            metadata: Additional metadata for the link
            validate: Whether to validate user exists
            
        Returns:
            ArtifactLink instance
        """
        # Validate user exists if requested
        if validate and httpx:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(
                        f"{self.user_store_url}/api/v1/users/{user_id}"
                    )
                    if response.status_code != 200:
                        raise ValueError(f"User {user_id} not found in User Store")
            except Exception:
                pass
        
        # Create artifact link
        artifact_url = f"{self.user_store_url}/api/v1/users/{user_id}"
        
        artifact = ArtifactLink(
            artifact_id=user_id,
            artifact_type="user",
            source_service="user-store",
            artifact_url=artifact_url,
            metadata=metadata or {}
        )
        
        # Add to context
        context.add_artifact_link(artifact)
        context.link_user(user_id)
        
        return artifact
    
    async def link_custom_artifact(
        self,
        context: MemoryContext,
        artifact_id: str,
        artifact_type: str,
        source_service: str,
        artifact_url: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ArtifactLink:
        """
        Link a custom artifact to a context.
        
        Args:
            context: MemoryContext to link to
            artifact_id: Artifact identifier
            artifact_type: Type of artifact (e.g., "code", "report", "diagram")
            source_service: Source service name
            artifact_url: Full URL to artifact
            metadata: Additional metadata for the link
            
        Returns:
            ArtifactLink instance
        """
        artifact = ArtifactLink(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            source_service=source_service,
            artifact_url=artifact_url,
            metadata=metadata or {}
        )
        
        # Add to context
        context.add_artifact_link(artifact)
        
        return artifact
    
    async def get_all_artifacts(
        self,
        context: MemoryContext
    ) -> List[ArtifactLink]:
        """
        Get all artifacts linked to a context.
        
        Args:
            context: MemoryContext to retrieve artifacts from
            
        Returns:
            List of ArtifactLink instances
        """
        return context.get_all_artifacts()
    
    async def get_artifacts_by_type(
        self,
        context: MemoryContext,
        artifact_type: str
    ) -> List[ArtifactLink]:
        """
        Get artifacts of a specific type.
        
        Args:
            context: MemoryContext to retrieve artifacts from
            artifact_type: Type of artifact to filter by
            
        Returns:
            List of matching ArtifactLink instances
        """
        all_artifacts = context.get_all_artifacts()
        return [a for a in all_artifacts if a.artifact_type == artifact_type]
    
    async def get_artifacts_by_service(
        self,
        context: MemoryContext,
        source_service: str
    ) -> List[ArtifactLink]:
        """
        Get artifacts from a specific service.
        
        Args:
            context: MemoryContext to retrieve artifacts from
            source_service: Source service to filter by
            
        Returns:
            List of matching ArtifactLink instances
        """
        all_artifacts = context.get_all_artifacts()
        return [a for a in all_artifacts if a.source_service == source_service]
    
    async def remove_artifact_link(
        self,
        context: MemoryContext,
        artifact_id: str
    ) -> bool:
        """
        Remove an artifact link from a context.
        
        Args:
            context: MemoryContext to remove from
            artifact_id: Artifact ID to remove
            
        Returns:
            True if removed, False if not found
        """
        # Remove from linked_artifacts
        original_count = len(context.linked_artifacts)
        context.linked_artifacts = [
            a for a in context.linked_artifacts
            if a.artifact_id != artifact_id
        ]
        
        # Remove from specific lists
        if artifact_id in context.linked_documents:
            context.linked_documents.remove(artifact_id)
        if artifact_id in context.linked_prompts:
            context.linked_prompts.remove(artifact_id)
        if artifact_id in context.linked_users:
            context.linked_users.remove(artifact_id)
        
        # Update version if something was removed
        if len(context.linked_artifacts) < original_count:
            context.updated_at = datetime.utcnow()
            context.version += 1
            return True
        
        return False
    
    async def get_cross_references(
        self,
        context: MemoryContext
    ) -> Dict[str, List[str]]:
        """
        Get cross-references between different artifact types.
        
        Args:
            context: MemoryContext to analyze
            
        Returns:
            Dictionary mapping artifact types to lists of IDs
        """
        cross_refs = {
            "documents": context.linked_documents,
            "prompts": context.linked_prompts,
            "users": context.linked_users,
            "all_artifacts": [a.artifact_id for a in context.linked_artifacts]
        }
        
        # Group artifacts by type
        artifacts_by_type: Dict[str, List[str]] = {}
        for artifact in context.linked_artifacts:
            if artifact.artifact_type not in artifacts_by_type:
                artifacts_by_type[artifact.artifact_type] = []
            artifacts_by_type[artifact.artifact_type].append(artifact.artifact_id)
        
        cross_refs["by_type"] = artifacts_by_type
        
        # Group artifacts by service
        artifacts_by_service: Dict[str, List[str]] = {}
        for artifact in context.linked_artifacts:
            if artifact.source_service not in artifacts_by_service:
                artifacts_by_service[artifact.source_service] = []
            artifacts_by_service[artifact.source_service].append(artifact.artifact_id)
        
        cross_refs["by_service"] = artifacts_by_service
        
        return cross_refs
    
    async def validate_all_artifacts(
        self,
        context: MemoryContext
    ) -> Dict[str, Any]:
        """
        Validate all artifacts linked to a context.
        
        Args:
            context: MemoryContext to validate
            
        Returns:
            Validation report dictionary
        """
        if not httpx:
            return {
                "validated": False,
                "reason": "httpx not available",
                "total_artifacts": len(context.get_all_artifacts())
            }
        
        report = {
            "validated": True,
            "total_artifacts": len(context.get_all_artifacts()),
            "valid_artifacts": 0,
            "invalid_artifacts": 0,
            "errors": []
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for artifact in context.get_all_artifacts():
                try:
                    response = await client.get(artifact.artifact_url)
                    if response.status_code == 200:
                        report["valid_artifacts"] += 1
                    else:
                        report["invalid_artifacts"] += 1
                        report["errors"].append({
                            "artifact_id": artifact.artifact_id,
                            "status_code": response.status_code
                        })
                except Exception as e:
                    report["invalid_artifacts"] += 1
                    report["errors"].append({
                        "artifact_id": artifact.artifact_id,
                        "error": str(e)
                    })
        
        return report
    
    async def fetch_artifact_metadata(
        self,
        artifact: ArtifactLink
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch metadata for an artifact from its source service.
        
        Args:
            artifact: ArtifactLink to fetch metadata for
            
        Returns:
            Metadata dictionary if successful, None otherwise
        """
        if not httpx:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(artifact.artifact_url)
                
                if response.status_code == 200:
                    return response.json()
        except Exception:
            pass
        
        return None
    
    async def bulk_link_documents(
        self,
        context: MemoryContext,
        document_ids: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[ArtifactLink]:
        """
        Link multiple documents at once.
        
        Args:
            context: MemoryContext to link to
            document_ids: List of document IDs
            metadata: Metadata to apply to all links
            
        Returns:
            List of created ArtifactLink instances
        """
        artifacts = []
        
        for doc_id in document_ids:
            artifact = await self.link_document(
                context=context,
                document_id=doc_id,
                metadata=metadata,
                validate=False  # Skip validation for bulk operations
            )
            artifacts.append(artifact)
        
        return artifacts
    
    async def bulk_link_prompts(
        self,
        context: MemoryContext,
        prompt_ids: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[ArtifactLink]:
        """
        Link multiple prompts at once.
        
        Args:
            context: MemoryContext to link to
            prompt_ids: List of prompt IDs
            metadata: Metadata to apply to all links
            
        Returns:
            List of created ArtifactLink instances
        """
        artifacts = []
        
        for prompt_id in prompt_ids:
            artifact = await self.link_prompt(
                context=context,
                prompt_id=prompt_id,
                metadata=metadata,
                validate=False  # Skip validation for bulk operations
            )
            artifacts.append(artifact)
        
        return artifacts
    
    async def bulk_link_users(
        self,
        context: MemoryContext,
        user_ids: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[ArtifactLink]:
        """
        Link multiple users at once.
        
        Args:
            context: MemoryContext to link to
            user_ids: List of user IDs
            metadata: Metadata to apply to all links
            
        Returns:
            List of created ArtifactLink instances
        """
        artifacts = []
        
        for user_id in user_ids:
            artifact = await self.link_user(
                context=context,
                user_id=user_id,
                metadata=metadata,
                validate=False  # Skip validation for bulk operations
            )
            artifacts.append(artifact)
        
        return artifacts

