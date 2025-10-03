"""
Context Search - Phase 3 Day 4
Smart search and retrieval of memory contexts.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from ..entities.memory_context import (
    MemoryContext,
    WorkflowType
)


class ContextSearch:
    """
    Smart context search and retrieval for Phase 3.
    
    Responsibilities:
    - Search contexts by various criteria
    - Filter contexts by attributes
    - Find similar contexts
    - Retrieve context history
    
    Part of Enhanced Roadmap v2.0 Phase 3 implementation.
    """
    
    def __init__(self):
        """Initialize Context Search."""
        pass
    
    async def search_by_workflow_type(
        self,
        contexts: List[MemoryContext],
        workflow_type: WorkflowType,
        limit: int = 10
    ) -> List[MemoryContext]:
        """
        Search contexts by workflow type.
        
        Args:
            contexts: List of contexts to search
            workflow_type: Workflow type to filter by
            limit: Maximum number of results
            
        Returns:
            List of matching contexts
        """
        matching = [
            ctx for ctx in contexts
            if ctx.workflow_type == workflow_type
        ]
        
        # Sort by created_at descending (most recent first)
        matching.sort(key=lambda x: x.created_at, reverse=True)
        
        return matching[:limit]
    
    async def search_by_date_range(
        self,
        contexts: List[MemoryContext],
        start_date: datetime,
        end_date: datetime,
        limit: int = 10
    ) -> List[MemoryContext]:
        """
        Search contexts within a date range.
        
        Args:
            contexts: List of contexts to search
            start_date: Start of date range
            end_date: End of date range
            limit: Maximum number of results
            
        Returns:
            List of matching contexts
        """
        matching = [
            ctx for ctx in contexts
            if start_date <= ctx.created_at <= end_date
        ]
        
        matching.sort(key=lambda x: x.created_at, reverse=True)
        
        return matching[:limit]
    
    async def search_by_success_rate(
        self,
        contexts: List[MemoryContext],
        min_success_rate: float = 0.0,
        max_success_rate: float = 1.0,
        limit: int = 10
    ) -> List[MemoryContext]:
        """
        Search contexts by success rate.
        
        Args:
            contexts: List of contexts to search
            min_success_rate: Minimum success rate (0.0-1.0)
            max_success_rate: Maximum success rate (0.0-1.0)
            limit: Maximum number of results
            
        Returns:
            List of matching contexts
        """
        matching = [
            ctx for ctx in contexts
            if min_success_rate <= ctx.success_rate <= max_success_rate
        ]
        
        # Sort by success rate descending
        matching.sort(key=lambda x: x.success_rate, reverse=True)
        
        return matching[:limit]
    
    async def search_by_artifacts(
        self,
        contexts: List[MemoryContext],
        has_documents: bool = False,
        has_prompts: bool = False,
        has_users: bool = False,
        min_artifacts: int = 0,
        limit: int = 10
    ) -> List[MemoryContext]:
        """
        Search contexts by artifact presence.
        
        Args:
            contexts: List of contexts to search
            has_documents: Filter for contexts with documents
            has_prompts: Filter for contexts with prompts
            has_users: Filter for contexts with users
            min_artifacts: Minimum total artifacts
            limit: Maximum number of results
            
        Returns:
            List of matching contexts
        """
        matching = []
        
        for ctx in contexts:
            # Check artifact requirements
            if has_documents and len(ctx.linked_documents) == 0:
                continue
            if has_prompts and len(ctx.linked_prompts) == 0:
                continue
            if has_users and len(ctx.linked_users) == 0:
                continue
            if len(ctx.get_all_artifacts()) < min_artifacts:
                continue
            
            matching.append(ctx)
        
        # Sort by total artifacts descending
        matching.sort(key=lambda x: len(x.get_all_artifacts()), reverse=True)
        
        return matching[:limit]
    
    async def find_similar_contexts(
        self,
        target_context: MemoryContext,
        candidate_contexts: List[MemoryContext],
        similarity_threshold: float = 0.7,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find contexts similar to the target context.
        
        Args:
            target_context: Context to find similar ones for
            candidate_contexts: List of candidate contexts
            similarity_threshold: Minimum similarity score (0.0-1.0)
            limit: Maximum number of results
            
        Returns:
            List of dictionaries with context and similarity score
        """
        similar = []
        
        for candidate in candidate_contexts:
            if candidate.context_id == target_context.context_id:
                continue  # Skip self
            
            similarity = self._calculate_similarity(target_context, candidate)
            
            if similarity >= similarity_threshold:
                similar.append({
                    "context": candidate,
                    "similarity_score": similarity,
                    "matching_criteria": self._get_matching_criteria(target_context, candidate)
                })
        
        # Sort by similarity descending
        similar.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return similar[:limit]
    
    async def search_recent(
        self,
        contexts: List[MemoryContext],
        hours: int = 24,
        limit: int = 10
    ) -> List[MemoryContext]:
        """
        Search for recent contexts.
        
        Args:
            contexts: List of contexts to search
            hours: Number of hours to look back
            limit: Maximum number of results
            
        Returns:
            List of recent contexts
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        matching = [
            ctx for ctx in contexts
            if ctx.created_at >= cutoff_time
        ]
        
        matching.sort(key=lambda x: x.created_at, reverse=True)
        
        return matching[:limit]
    
    async def search_by_parent(
        self,
        contexts: List[MemoryContext],
        parent_workflow_id: str,
        limit: int = 10
    ) -> List[MemoryContext]:
        """
        Search for child contexts of a parent workflow.
        
        Args:
            contexts: List of contexts to search
            parent_workflow_id: Parent workflow ID
            limit: Maximum number of results
            
        Returns:
            List of child contexts
        """
        matching = [
            ctx for ctx in contexts
            if ctx.parent_workflow_id == parent_workflow_id
        ]
        
        matching.sort(key=lambda x: x.created_at)
        
        return matching[:limit]
    
    def _calculate_similarity(
        self,
        context1: MemoryContext,
        context2: MemoryContext
    ) -> float:
        """
        Calculate similarity score between two contexts.
        
        Uses multiple factors:
        - Workflow type match
        - Artifact overlap
        - Success rate similarity
        - Temporal proximity
        """
        score = 0.0
        weights = {
            "workflow_type": 0.3,
            "artifacts": 0.3,
            "success_rate": 0.2,
            "temporal": 0.2
        }
        
        # Workflow type match
        if context1.workflow_type == context2.workflow_type:
            score += weights["workflow_type"]
        
        # Artifact overlap
        artifacts1 = set(context1.linked_documents + context1.linked_prompts + context1.linked_users)
        artifacts2 = set(context2.linked_documents + context2.linked_prompts + context2.linked_users)
        
        if artifacts1 and artifacts2:
            overlap = len(artifacts1 & artifacts2)
            total = len(artifacts1 | artifacts2)
            if total > 0:
                score += weights["artifacts"] * (overlap / total)
        
        # Success rate similarity
        success_diff = abs(context1.success_rate - context2.success_rate)
        score += weights["success_rate"] * (1.0 - success_diff)
        
        # Temporal proximity (closer in time = more similar)
        time_diff_days = abs((context1.created_at - context2.created_at).total_seconds()) / 86400
        temporal_score = max(0.0, 1.0 - (time_diff_days / 30))  # 30 days = 0 similarity
        score += weights["temporal"] * temporal_score
        
        return min(score, 1.0)
    
    def _get_matching_criteria(
        self,
        context1: MemoryContext,
        context2: MemoryContext
    ) -> List[str]:
        """Get list of matching criteria between contexts."""
        criteria = []
        
        if context1.workflow_type == context2.workflow_type:
            criteria.append("Same workflow type")
        
        artifacts1 = set(context1.linked_documents + context1.linked_prompts + context1.linked_users)
        artifacts2 = set(context2.linked_documents + context2.linked_prompts + context2.linked_users)
        overlap = len(artifacts1 & artifacts2)
        
        if overlap > 0:
            criteria.append(f"{overlap} shared artifacts")
        
        success_diff = abs(context1.success_rate - context2.success_rate)
        if success_diff < 0.1:
            criteria.append("Similar success rate")
        
        time_diff_hours = abs((context1.created_at - context2.created_at).total_seconds()) / 3600
        if time_diff_hours < 24:
            criteria.append("Created within 24 hours")
        elif time_diff_hours < 168:  # 1 week
            criteria.append("Created within 1 week")
        
        return criteria

