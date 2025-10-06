"""Redis implementation of Workflow Repository."""

import json
import logging
from typing import List, Optional

import redis.asyncio as redis

from services.mcp_orchestrator.domain.entities.workflow import Workflow
from services.mcp_orchestrator.domain.repositories.workflow_repository import WorkflowRepository
from services.mcp_orchestrator.domain.value_objects.workflow_state import WorkflowState
from services.mcp_orchestrator.infrastructure.config.settings import Settings

logger = logging.getLogger(__name__)


class RedisWorkflowRepository(WorkflowRepository):
    """
    Redis implementation of the Workflow Repository.
    
    Uses Redis hashes for storing workflows and Redis sets for indexing.
    """
    
    def __init__(self, redis_client: redis.Redis, settings: Settings):
        """
        Initialize the repository.
        
        Args:
            redis_client: Async Redis client
            settings: Application settings
        """
        self.redis = redis_client
        self.settings = settings
        self.KEY_PREFIX = settings.redis_key_prefix
    
    def _workflow_key(self, workflow_id: str) -> str:
        """Generate Redis key for workflow."""
        return f"{self.KEY_PREFIX}workflow:{workflow_id}"
    
    def _user_index_key(self, user_id: str) -> str:
        """Generate Redis key for user's workflows index."""
        return f"{self.KEY_PREFIX}index:user:{user_id}"
    
    def _state_index_key(self, state: WorkflowState) -> str:
        """Generate Redis key for state index."""
        return f"{self.KEY_PREFIX}index:state:{state.value}"
    
    def _all_workflows_key(self) -> str:
        """Generate Redis key for all workflows set."""
        return f"{self.KEY_PREFIX}all_workflows"
    
    async def save(self, workflow: Workflow) -> None:
        """Save a workflow."""
        try:
            workflow_key = self._workflow_key(workflow.id)
            workflow_data = json.dumps(workflow.to_dict())
            
            # Save workflow
            await self.redis.set(workflow_key, workflow_data)
            
            # Update indices
            pipeline = self.redis.pipeline()
            pipeline.sadd(self._all_workflows_key(), workflow.id)
            
            if workflow.user_id:
                pipeline.sadd(self._user_index_key(workflow.user_id), workflow.id)
            
            pipeline.sadd(self._state_index_key(workflow.state), workflow.id)
            
            await pipeline.execute()
            
            logger.debug(f"Saved workflow {workflow.id} (state: {workflow.state.value})")
            
        except redis.RedisError as e:
            logger.error(f"Redis error saving workflow {workflow.id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error saving workflow {workflow.id}: {e}", exc_info=True)
            raise
    
    async def find_by_id(self, workflow_id: str) -> Optional[Workflow]:
        """Find a workflow by ID."""
        try:
            workflow_key = self._workflow_key(workflow_id)
            data = await self.redis.get(workflow_key)
            
            if not data:
                return None
            
            workflow_dict = json.loads(data)
            
            # Reconstruct workflow from dict
            # Note: This is simplified; full implementation would properly
            # reconstruct all nested entities (ExecutionPlan, Steps, etc.)
            return self._workflow_from_dict(workflow_dict)
            
        except redis.RedisError as e:
            logger.error(f"Redis error finding workflow {workflow_id}: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for workflow {workflow_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error finding workflow {workflow_id}: {e}", exc_info=True)
            raise
    
    async def find_by_user_id(
        self,
        user_id: str,
        limit: Optional[int] = None
    ) -> List[Workflow]:
        """Find workflows by user ID."""
        try:
            user_index_key = self._user_index_key(user_id)
            workflow_ids = await self.redis.smembers(user_index_key)
            
            workflows = []
            for i, workflow_id_bytes in enumerate(workflow_ids):
                if limit and i >= limit:
                    break
                
                workflow_id = workflow_id_bytes.decode()
                workflow = await self.find_by_id(workflow_id)
                
                if workflow:
                    workflows.append(workflow)
            
            return workflows
            
        except redis.RedisError as e:
            logger.error(f"Redis error finding workflows for user {user_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error finding workflows for user {user_id}: {e}", exc_info=True)
            raise
    
    async def find_by_state(
        self,
        state: WorkflowState,
        limit: Optional[int] = None
    ) -> List[Workflow]:
        """Find workflows by state."""
        try:
            state_index_key = self._state_index_key(state)
            workflow_ids = await self.redis.smembers(state_index_key)
            
            workflows = []
            for i, workflow_id_bytes in enumerate(workflow_ids):
                if limit and i >= limit:
                    break
                
                workflow_id = workflow_id_bytes.decode()
                workflow = await self.find_by_id(workflow_id)
                
                if workflow:
                    workflows.append(workflow)
            
            return workflows
            
        except redis.RedisError as e:
            logger.error(f"Redis error finding workflows by state {state.value}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error finding workflows by state {state.value}: {e}", exc_info=True)
            raise
    
    async def find_active_workflows(self, limit: Optional[int] = None) -> List[Workflow]:
        """Find all active workflows."""
        try:
            active_workflows = []
            
            # Get workflows from all active states
            active_states = [
                WorkflowState.PENDING,
                WorkflowState.PLANNING,
                WorkflowState.READY,
                WorkflowState.EXECUTING,
                WorkflowState.AGGREGATING,
                WorkflowState.REFINING,
            ]
            
            for state in active_states:
                state_workflows = await self.find_by_state(state, limit=limit)
                active_workflows.extend(state_workflows)
                
                if limit and len(active_workflows) >= limit:
                    active_workflows = active_workflows[:limit]
                    break
            
            return active_workflows
            
        except Exception as e:
            logger.error(f"Error finding active workflows: {e}", exc_info=True)
            raise
    
    async def delete(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        try:
            # Get workflow first to clean up indices
            workflow = await self.find_by_id(workflow_id)
            if not workflow:
                return False
            
            # Delete workflow
            workflow_key = self._workflow_key(workflow_id)
            
            pipeline = self.redis.pipeline()
            pipeline.delete(workflow_key)
            pipeline.srem(self._all_workflows_key(), workflow_id)
            
            if workflow.user_id:
                pipeline.srem(self._user_index_key(workflow.user_id), workflow_id)
            
            pipeline.srem(self._state_index_key(workflow.state), workflow_id)
            
            await pipeline.execute()
            
            logger.debug(f"Deleted workflow {workflow_id}")
            return True
            
        except redis.RedisError as e:
            logger.error(f"Redis error deleting workflow {workflow_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error deleting workflow {workflow_id}: {e}", exc_info=True)
            raise
    
    async def count_by_state(self, state: WorkflowState) -> int:
        """Count workflows by state."""
        try:
            state_index_key = self._state_index_key(state)
            count = await self.redis.scard(state_index_key)
            return count
            
        except redis.RedisError as e:
            logger.error(f"Redis error counting workflows by state {state.value}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error counting workflows by state {state.value}: {e}", exc_info=True)
            raise
    
    def _workflow_from_dict(self, data: dict) -> Workflow:
        """
        Reconstruct Workflow from dictionary.
        
        Note: Simplified implementation. Full version would
        reconstruct all nested entities properly.
        """
        from datetime import datetime
        from services.mcp_orchestrator.domain.value_objects.llm_pattern import LLMPattern
        
        workflow = Workflow(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            original_query=data["original_query"],
            parsed_query_id=data["parsed_query_id"],
            query_intent=data["query_intent"],
            query_complexity=data["query_complexity"],
            state=WorkflowState(data["state"]),
            progress=data["progress"],
            applied_patterns=[LLMPattern(p) for p in data.get("applied_patterns", [])],
            final_result=data.get("final_result"),
            confidence_score=data.get("confidence_score", 0.0),
            error_message=data.get("error_message"),
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            duration_ms=data.get("duration_ms", 0.0),
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            metadata=data.get("metadata", {}),
        )
        
        # Note: execution_plan would be reconstructed here in full implementation
        # For now, leaving it as None (can be added later)
        
        return workflow

