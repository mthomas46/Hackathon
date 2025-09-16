"""Lifecycle management service.

Contains business logic for prompt lifecycle transitions, validation, and workflow management.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from services.prompt_store.domain.lifecycle.repository import LifecycleRepository
from services.prompt_store.domain.prompts.service import PromptService
from services.prompt_store.infrastructure.cache import prompt_store_cache
from services.shared.utilities import generate_id, utc_now


class LifecycleService:
    """Service for managing prompt lifecycle operations."""

    def __init__(self):
        self.lifecycle_repo = LifecycleRepository()
        self.prompt_service = PromptService()

    async def update_lifecycle_status(self, prompt_id: str, new_status: str,
                                     reason: str = "", user_id: str = "system") -> Dict[str, Any]:
        """Update the lifecycle status of a prompt with validation and side effects."""

        # Validate the transition
        current_prompt = self.lifecycle_repo.get_entity(prompt_id)
        if not current_prompt:
            raise ValueError(f"Prompt {prompt_id} not found")

        if not self.lifecycle_repo.validate_transition(current_prompt.lifecycle_status, new_status):
            raise ValueError(
                f"Invalid lifecycle transition from '{current_prompt.lifecycle_status}' to '{new_status}'"
            )

        # Perform the transition
        success = self.lifecycle_repo.update_lifecycle_status(
            prompt_id, new_status, reason, user_id
        )

        if success:
            # Invalidate cache for this prompt
            await prompt_store_cache.delete(f"prompt:{prompt_id}")
            await prompt_store_cache.delete(f"prompt_versions:{prompt_id}")

            # Trigger any side effects based on the transition
            await self._handle_transition_side_effects(current_prompt, new_status, user_id)

            return {
                "prompt_id": prompt_id,
                "previous_status": current_prompt.lifecycle_status,
                "new_status": new_status,
                "transition_timestamp": utc_now().isoformat(),
                "reason": reason,
                "updated_by": user_id
            }
        else:
            raise Exception("Failed to update lifecycle status")

    async def get_prompts_by_status(self, status: str, limit: int = 50,
                                   offset: int = 0) -> Dict[str, Any]:
        """Get prompts by lifecycle status with caching."""

        cache_key = f"lifecycle_status:{status}:{limit}:{offset}"
        cached_result = await prompt_store_cache.get(cache_key)
        if cached_result:
            return cached_result

        prompts = self.lifecycle_repo.get_prompts_by_status(status, limit, offset)

        result = {
            "status": status,
            "prompts": [prompt.to_dict() for prompt in prompts],
            "count": len(prompts),
            "limit": limit,
            "offset": offset
        }

        await prompt_store_cache.set(cache_key, result, ttl=300)  # Cache for 5 minutes
        return result

    def get_lifecycle_history(self, prompt_id: str) -> Dict[str, Any]:
        """Get the complete lifecycle history for a prompt."""

        prompt = self.lifecycle_repo.get_entity(prompt_id)
        if not prompt:
            raise ValueError(f"Prompt {prompt_id} not found")

        history = self.lifecycle_repo.get_lifecycle_history(prompt_id)

        return {
            "prompt_id": prompt_id,
            "current_status": prompt.lifecycle_status,
            "lifecycle_history": history,
            "history_count": len(history)
        }

    def get_status_counts(self) -> Dict[str, Any]:
        """Get counts of prompts in each lifecycle status."""

        counts = self.lifecycle_repo.get_status_counts()

        return {
            "status_counts": counts,
            "total_prompts": sum(counts.values()),
            "last_updated": utc_now().isoformat()
        }

    def get_transition_rules(self) -> Dict[str, Any]:
        """Get all valid lifecycle transition rules."""

        rules = self.lifecycle_repo.get_transition_rules()

        return {
            "valid_statuses": list(self.lifecycle_repo.VALID_STATUSES),
            "transition_rules": rules,
            "description": "Valid transitions between lifecycle statuses"
        }

    def validate_transition(self, prompt_id: str, new_status: str) -> Dict[str, Any]:
        """Validate if a transition is allowed for a specific prompt."""

        prompt = self.lifecycle_repo.get_entity(prompt_id)
        if not prompt:
            return {
                "valid": False,
                "reason": f"Prompt {prompt_id} not found"
            }

        is_valid = self.lifecycle_repo.validate_transition(prompt.lifecycle_status, new_status)

        return {
            "valid": is_valid,
            "current_status": prompt.lifecycle_status,
            "requested_status": new_status,
            "reason": None if is_valid else
                    f"Invalid transition from '{prompt.lifecycle_status}' to '{new_status}'"
        }

    async def bulk_lifecycle_update(self, prompt_ids: List[str], new_status: str,
                                   reason: str = "", user_id: str = "system") -> Dict[str, Any]:
        """Perform bulk lifecycle status updates."""

        results = []
        successful = 0
        failed = 0

        for prompt_id in prompt_ids:
            try:
                result = await self.update_lifecycle_status(
                    prompt_id, new_status, reason, user_id
                )
                results.append({"prompt_id": prompt_id, "success": True, "result": result})
                successful += 1
            except Exception as e:
                results.append({"prompt_id": prompt_id, "success": False, "error": str(e)})
                failed += 1

        return {
            "operation": "bulk_lifecycle_update",
            "total_requested": len(prompt_ids),
            "successful": successful,
            "failed": failed,
            "new_status": new_status,
            "results": results,
            "timestamp": utc_now().isoformat()
        }

    async def _handle_transition_side_effects(self, prompt: Any, new_status: str,
                                            user_id: str) -> None:
        """Handle side effects of lifecycle transitions."""

        # When archiving a prompt, clean up any active sessions or references
        if new_status == "archived":
            await self._cleanup_archived_prompt(prompt.id)

        # When publishing a prompt, validate it meets publishing criteria
        elif new_status == "published":
            await self._validate_publish_criteria(prompt)

        # When deprecating, notify dependent systems
        elif new_status == "deprecated":
            await self._notify_deprecation(prompt, user_id)

    async def _cleanup_archived_prompt(self, prompt_id: str) -> None:
        """Clean up resources when a prompt is archived."""
        # This could involve:
        # - Cleaning up cache entries
        # - Removing from active search indexes
        # - Notifying dependent services

        # For now, just clean cache
        await prompt_store_cache.delete(f"prompt:{prompt_id}")
        await prompt_store_cache.delete(f"prompt_versions:{prompt_id}")
        await prompt_store_cache.delete_pattern(f"lifecycle_status:*:*")  # Clear status caches

    async def _validate_publish_criteria(self, prompt: Any) -> None:
        """Validate that a prompt meets criteria for publishing."""
        # This could involve:
        # - Content validation
        # - Security checks
        # - Completeness checks

        # For now, basic validation
        if not prompt.content or len(prompt.content.strip()) < 10:
            raise ValueError("Prompt content is too short for publishing")

        if not prompt.name or len(prompt.name.strip()) < 3:
            raise ValueError("Prompt name is too short for publishing")

    async def _notify_deprecation(self, prompt: Any, user_id: str) -> None:
        """Notify relevant systems about prompt deprecation."""
        # This could involve:
        # - Sending notifications to prompt users
        # - Updating dependent workflows
        # - Logging deprecation events

        # For now, just log the deprecation
        # In a real system, this would trigger webhook notifications
        pass
