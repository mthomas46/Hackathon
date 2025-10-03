"""
Context Manager - Phase 3 Day 1
Manages workflow results and context storage.
"""

import uuid
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

from ..entities.memory_context import (
    MemoryContext,
    WorkflowResult,
    ArtifactLink,
    WorkflowType
)


class ContextManager:
    """
    Enhanced context management for Phase 3.
    
    Responsibilities:
    - Store workflow execution results
    - Manage context lifecycle (TTL, versioning)
    - Aggregate results from multiple workflows
    - Synthesize unified context views
    
    Part of Enhanced Roadmap v2.0 Phase 3 implementation.
    """
    
    def __init__(
        self,
        redis_client: Optional[Any] = None,
        redis_url: str = "redis://localhost:6379"
    ):
        """
        Initialize Context Manager.
        
        Args:
            redis_client: Redis client for persistence
            redis_url: Redis URL if client not provided
        """
        self.redis_client = redis_client
        self.redis_url = redis_url
        self._local_cache: Dict[str, MemoryContext] = {}  # Fallback cache
    
    async def _get_redis_client(self) -> Optional[Any]:
        """Get or create Redis client."""
        if self.redis_client:
            return self.redis_client
        
        if aioredis:
            try:
                self.redis_client = await aioredis.from_url(
                    self.redis_url,
                    decode_responses=False
                )
                return self.redis_client
            except Exception:
                return None
        return None
    
    async def create_context(
        self,
        workflow_id: str,
        workflow_type: WorkflowType,
        context_data: Optional[Dict[str, Any]] = None,
        parent_workflow_id: Optional[str] = None,
        ttl_seconds: int = 86400
    ) -> MemoryContext:
        """
        Create a new memory context.
        
        Args:
            workflow_id: Unique workflow identifier
            workflow_type: Type of workflow
            context_data: Initial context data
            parent_workflow_id: Parent workflow if this is a child
            ttl_seconds: Time-to-live in seconds
            
        Returns:
            MemoryContext instance
        """
        context_id = f"ctx_{str(uuid.uuid4())[:8]}"
        
        context = MemoryContext(
            context_id=context_id,
            workflow_id=workflow_id,
            parent_workflow_id=parent_workflow_id,
            workflow_type=workflow_type,
            context_data=context_data or {},
            ttl_seconds=ttl_seconds
        )
        
        # Save to Redis
        await self._save_context(context)
        
        return context
    
    async def store_workflow_result(
        self,
        workflow_id: str,
        workflow_type: WorkflowType,
        result_data: Dict[str, Any],
        artifacts: Optional[List[ArtifactLink]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        duration_ms: float = 0.0,
        services_called: Optional[List[str]] = None,
        parent_workflow_id: Optional[str] = None
    ) -> WorkflowResult:
        """
        Store a complete workflow result.
        
        Args:
            workflow_id: Workflow identifier
            workflow_type: Type of workflow
            result_data: Result data dictionary
            artifacts: List of artifact links
            success: Whether workflow succeeded
            error_message: Error message if failed
            duration_ms: Execution duration in milliseconds
            services_called: List of services called
            parent_workflow_id: Parent workflow if child
            
        Returns:
            WorkflowResult instance
        """
        result_id = f"result_{workflow_id}_{str(uuid.uuid4())[:8]}"
        
        result = WorkflowResult(
            result_id=result_id,
            workflow_id=workflow_id,
            workflow_type=workflow_type,
            result_data=result_data,
            success=success,
            error_message=error_message,
            artifacts=artifacts or [],
            duration_ms=duration_ms,
            services_called=services_called or []
        )
        
        # Get or create context
        context = await self.get_context(workflow_id)
        
        if context is None:
            # Create new context
            context = await self.create_context(
                workflow_id=workflow_id,
                workflow_type=workflow_type,
                parent_workflow_id=parent_workflow_id
            )
        
        # Add result to context
        context.add_workflow_result(result)
        
        # Save updated context
        await self._save_context(context)
        
        return result
    
    async def get_context(
        self,
        workflow_id: str
    ) -> Optional[MemoryContext]:
        """
        Retrieve a memory context by workflow ID.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            MemoryContext if found, None otherwise
        """
        redis = await self._get_redis_client()
        
        if redis:
            try:
                key = f"context:{workflow_id}"
                data = await redis.get(key)
                
                if data:
                    context_dict = json.loads(data.decode("utf-8") if isinstance(data, bytes) else data)
                    context = MemoryContext.from_dict(context_dict)
                    
                    # Check if expired
                    if context.is_expired():
                        await self.delete_context(workflow_id)
                        return None
                    
                    return context
            except Exception:
                pass
        
        # Fallback to local cache
        return self._local_cache.get(workflow_id)
    
    async def get_workflow_history(
        self,
        workflow_type: WorkflowType,
        limit: int = 10,
        parent_workflow_id: Optional[str] = None
    ) -> List[WorkflowResult]:
        """
        Get historical workflow executions.
        
        Args:
            workflow_type: Type of workflow to retrieve
            limit: Maximum number of results
            parent_workflow_id: Filter by parent workflow
            
        Returns:
            List of WorkflowResult instances
        """
        redis = await self._get_redis_client()
        results = []
        
        if redis:
            try:
                # Scan for matching contexts
                pattern = "context:*"
                cursor = 0
                
                while True:
                    cursor, keys = await redis.scan(cursor, match=pattern, count=100)
                    
                    for key in keys:
                        data = await redis.get(key)
                        if data:
                            try:
                                context_dict = json.loads(data.decode("utf-8") if isinstance(data, bytes) else data)
                                context = MemoryContext.from_dict(context_dict)
                                
                                # Filter by workflow type and parent
                                if context.workflow_type == workflow_type:
                                    if parent_workflow_id is None or context.parent_workflow_id == parent_workflow_id:
                                        results.extend(context.get_successful_workflows())
                            except Exception:
                                continue
                    
                    if cursor == 0:
                        break
                
                # Sort by completed_at descending
                results.sort(key=lambda r: r.completed_at, reverse=True)
                return results[:limit]
                
            except Exception:
                pass
        
        # Fallback to local cache
        for context in self._local_cache.values():
            if context.workflow_type == workflow_type:
                if parent_workflow_id is None or context.parent_workflow_id == parent_workflow_id:
                    results.extend(context.get_successful_workflows())
        
        results.sort(key=lambda r: r.completed_at, reverse=True)
        return results[:limit]
    
    async def aggregate_workflow_results(
        self,
        parent_workflow_id: str
    ) -> Dict[str, Any]:
        """
        Aggregate all child workflow results for a parent workflow.
        
        Args:
            parent_workflow_id: Parent workflow identifier
            
        Returns:
            Aggregated results dictionary
        """
        redis = await self._get_redis_client()
        child_contexts: List[MemoryContext] = []
        
        if redis:
            try:
                pattern = "context:*"
                cursor = 0
                
                while True:
                    cursor, keys = await redis.scan(cursor, match=pattern, count=100)
                    
                    for key in keys:
                        data = await redis.get(key)
                        if data:
                            try:
                                context_dict = json.loads(data.decode("utf-8") if isinstance(data, bytes) else data)
                                context = MemoryContext.from_dict(context_dict)
                                
                                if context.parent_workflow_id == parent_workflow_id:
                                    child_contexts.append(context)
                            except Exception:
                                continue
                    
                    if cursor == 0:
                        break
            except Exception:
                pass
        
        # Fallback to local cache
        if not child_contexts:
            child_contexts = [
                ctx for ctx in self._local_cache.values()
                if ctx.parent_workflow_id == parent_workflow_id
            ]
        
        # Aggregate results
        aggregated = {
            "parent_workflow_id": parent_workflow_id,
            "total_child_workflows": len(child_contexts),
            "successful_workflows": sum(ctx.successful_workflows for ctx in child_contexts),
            "failed_workflows": sum(ctx.failed_workflows for ctx in child_contexts),
            "total_artifacts": sum(len(ctx.get_all_artifacts()) for ctx in child_contexts),
            "workflow_results": {},
            "all_artifacts": []
        }
        
        # Collect all workflow results
        for context in child_contexts:
            for workflow_id, result in context.workflow_results.items():
                aggregated["workflow_results"][workflow_id] = result.to_dict()
                aggregated["all_artifacts"].extend([a.to_dict() for a in result.artifacts])
        
        return aggregated
    
    async def synthesize_context(
        self,
        workflow_id: str
    ) -> Dict[str, Any]:
        """
        Synthesize a unified context view from a workflow and its children.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Synthesized context dictionary
        """
        context = await self.get_context(workflow_id)
        
        if context is None:
            return {}
        
        # Get aggregated child results
        child_results = await self.aggregate_workflow_results(workflow_id)
        
        # Synthesize unified view
        synthesized = {
            "context_id": context.context_id,
            "workflow_id": context.workflow_id,
            "workflow_type": context.workflow_type.value,
            "created_at": context.created_at.isoformat(),
            "age_seconds": context.age_seconds,
            "success_rate": context.success_rate,
            "total_workflows": context.total_workflows + child_results.get("total_child_workflows", 0),
            "successful_workflows": context.successful_workflows + child_results.get("successful_workflows", 0),
            "failed_workflows": context.failed_workflows + child_results.get("failed_workflows", 0),
            "context_data": context.context_data,
            "linked_documents": context.linked_documents,
            "linked_prompts": context.linked_prompts,
            "linked_users": context.linked_users,
            "total_artifacts": len(context.get_all_artifacts()) + child_results.get("total_artifacts", 0),
            "child_workflows": child_results.get("workflow_results", {})
        }
        
        return synthesized
    
    async def delete_context(
        self,
        workflow_id: str
    ) -> bool:
        """
        Delete a context.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            True if deleted, False otherwise
        """
        redis = await self._get_redis_client()
        
        if redis:
            try:
                key = f"context:{workflow_id}"
                await redis.delete(key)
                return True
            except Exception:
                pass
        
        # Fallback to local cache
        if workflow_id in self._local_cache:
            del self._local_cache[workflow_id]
            return True
        
        return False
    
    async def _save_context(
        self,
        context: MemoryContext
    ) -> bool:
        """Save context to Redis or local cache."""
        redis = await self._get_redis_client()
        
        if redis:
            try:
                key = f"context:{context.workflow_id}"
                value = json.dumps(context.to_dict())
                
                # Set with TTL
                if context.ttl_seconds:
                    await redis.setex(key, context.ttl_seconds, value)
                else:
                    await redis.set(key, value)
                
                return True
            except Exception:
                pass
        
        # Fallback to local cache
        self._local_cache[context.workflow_id] = context
        return True

