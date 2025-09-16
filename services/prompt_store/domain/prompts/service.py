"""Prompt service implementation.

Handles business logic for prompts following domain-driven design.
"""

import asyncio
from typing import List, Optional, Dict, Any, Tuple
from services.prompt_store.core.service import BaseService
from services.prompt_store.core.entities import Prompt
from services.prompt_store.domain.prompts.repository import PromptRepository
from services.prompt_store.infrastructure.cache import prompt_store_cache
from services.prompt_store.infrastructure.utils import (
    generate_prompt_hash,
    validate_template_variables,
    calculate_prompt_complexity,
    sanitize_prompt_content,
    detect_prompt_drift,
    generate_prompt_suggestions
)
from services.shared.utilities import generate_id, utc_now


class PromptService(BaseService[Prompt]):
    """Service for prompt business logic."""

    def __init__(self):
        super().__init__(PromptRepository())

    def create_entity(self, data: Dict[str, Any], entity_id: Optional[str] = None) -> Prompt:
        """Create a new prompt with validation and business rules."""
        # Validate required fields
        required_fields = ["name", "category", "content"]
        missing = [field for field in required_fields if field not in data]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        # Sanitize and validate content
        content = sanitize_prompt_content(data["content"])
        if not content:
            raise ValueError("Prompt content cannot be empty")

        # Validate template variables if it's a template
        variables = data.get("variables", [])
        if data.get("is_template", False):
            validation = validate_template_variables(content, variables)
            if not validation["valid"]:
                raise ValueError(f"Template validation failed: {', '.join(validation['errors'])}")

        # Check for duplicate prompt by content hash
        content_hash = generate_prompt_hash(content, variables)
        existing = self._find_by_content_hash(content_hash)
        if existing:
            raise ValueError(f"Similar prompt already exists: {existing.name} in {existing.category}")

        # Check for duplicate name in category
        category = data["category"]
        name = data["name"]
        existing_by_name = self.repository.get_by_name(category, name)
        if existing_by_name:
            raise ValueError(f"Prompt '{name}' already exists in category '{category}'")

        # Calculate complexity score
        complexity = calculate_prompt_complexity(content, variables)

        # Create prompt entity
        prompt = Prompt(
            id=entity_id or generate_id(),
            name=name,
            category=category,
            description=data.get("description", ""),
            content=content,
            variables=variables,
            tags=data.get("tags", []),
            is_template=data.get("is_template", False),
            created_by=data.get("created_by", "api_user"),
            performance_score=complexity  # Initial score based on complexity
        )

        # Save to database
        saved_prompt = self.repository.save(prompt)

        # Cache the prompt
        asyncio.create_task(self._cache_prompt(saved_prompt))

        return saved_prompt

    def get_prompt_by_name(self, category: str, name: str) -> Optional[Prompt]:
        """Get prompt by category and name with caching."""
        cache_key = f"prompt:{category}:{name}"

        # Try cache first
        cached = asyncio.run(prompt_store_cache.get(cache_key))
        if cached:
            return cached

        # Get from database
        prompt = self.repository.get_by_name(category, name)
        if prompt:
            # Cache for future use
            asyncio.create_task(prompt_store_cache.set(cache_key, prompt, ttl=3600))

        return prompt

    def fill_template(self, prompt: Prompt, variables: Dict[str, Any]) -> str:
        """Fill template variables in prompt content."""
        if not prompt.is_template:
            return prompt.content

        # Validate that all required variables are provided
        required_vars = set(prompt.variables)
        provided_vars = set(variables.keys())
        missing = required_vars - provided_vars
        if missing:
            raise ValueError(f"Missing required variables: {', '.join(missing)}")

        # Fill template
        from services.prompt_store.infrastructure.utils import format_prompt_template
        filled_content = format_prompt_template(prompt.content, variables)

        # Increment usage count
        asyncio.create_task(self._increment_usage_async(prompt.id))

        return filled_content

    def search_prompts(self, query: str, category: Optional[str] = None,
                      tags: Optional[List[str]] = None, limit: int = 50) -> List[Prompt]:
        """Search prompts with enhanced filtering."""
        return self.repository.search_prompts(query, category, tags, limit)

    def get_prompts_by_category(self, category: str, limit: int = 50, offset: int = 0) -> List[Prompt]:
        """Get prompts by category."""
        return self.repository.get_by_category(category, limit, offset)

    def get_prompts_by_tags(self, tags: List[str], limit: int = 50) -> List[Prompt]:
        """Get prompts by tags."""
        return self.repository.get_by_tags(tags, limit)

    def fork_prompt(self, prompt_id: str, new_name: str, created_by: str,
                   changes: Optional[Dict[str, Any]] = None) -> Prompt:
        """Fork a prompt to create a new version."""
        original = self.get_entity(prompt_id)
        if not original:
            raise ValueError(f"Prompt {prompt_id} not found")

        # Create fork data
        fork_data = {
            "name": new_name,
            "category": original.category,
            "description": f"Forked from {original.name}",
            "content": original.content,
            "variables": original.variables.copy(),
            "tags": original.tags.copy(),
            "is_template": original.is_template,
            "created_by": created_by,
            "parent_id": prompt_id
        }

        # Apply changes if provided
        if changes:
            fork_data.update(changes)

        return self.create_entity(fork_data)

    def update_prompt_content(self, prompt_id: str, content: str, variables: Optional[List[str]] = None,
                             change_summary: str = "", updated_by: str = "api_user") -> Prompt:
        """Update prompt content with versioning."""
        prompt = self.get_entity(prompt_id)
        if not prompt:
            raise ValueError(f"Prompt {prompt_id} not found")

        # Create version record
        self._create_version_record(prompt, change_summary, updated_by)

        # Update content
        updates = {"content": sanitize_prompt_content(content)}
        if variables is not None:
            updates["variables"] = variables

        # Recalculate complexity
        complexity = calculate_prompt_complexity(content, variables or prompt.variables)
        updates["performance_score"] = complexity

        updated_prompt = self.update_entity(prompt_id, updates)

        # Invalidate cache
        asyncio.create_task(self._invalidate_prompt_cache(prompt.category, prompt.name))

        return updated_prompt

    def detect_drift(self, prompt_id: str) -> Dict[str, Any]:
        """Detect prompt drift over time."""
        # Get prompt versions history
        versions = self._get_prompt_versions(prompt_id)
        if not versions:
            return {"drift_detected": False, "drift_score": 0.0, "significant_changes": []}

        current_prompt = self.get_entity(prompt_id)
        if not current_prompt:
            raise ValueError(f"Prompt {prompt_id} not found")

        historical_versions = [{"content": v.content, "version": v.version, "created_at": v.created_at.isoformat()}
                              for v in versions]

        return detect_prompt_drift(current_prompt.content, historical_versions)

    def get_suggestions(self, prompt_id: str) -> List[str]:
        """Get improvement suggestions for a prompt."""
        prompt = self.get_entity(prompt_id)
        if not prompt:
            raise ValueError(f"Prompt {prompt_id} not found")

        # Get similar prompts in the same category
        similar_prompts = self.get_prompts_by_category(prompt.category, limit=10)

        return generate_prompt_suggestions(prompt.category, [p.to_dict() for p in similar_prompts])

    def bulk_update_tags(self, prompt_ids: List[str], tags_to_add: Optional[List[str]] = None,
                        tags_to_remove: Optional[List[str]] = None) -> int:
        """Bulk update tags on multiple prompts."""
        updated_count = 0

        for prompt_id in prompt_ids:
            prompt = self.get_entity(prompt_id)
            if not prompt:
                continue

            current_tags = set(prompt.tags)
            if tags_to_add:
                current_tags.update(tags_to_add)
            if tags_to_remove:
                current_tags -= set(tags_to_remove)

            self.update_entity(prompt_id, {"tags": list(current_tags)})
            updated_count += 1

        return updated_count

    def _find_by_content_hash(self, content_hash: str) -> Optional[Prompt]:
        """Find prompt by content hash (simplified implementation)."""
        # This would require a content_hash field in the database
        # For now, return None (no duplicate checking)
        return None

    def _create_version_record(self, prompt: Prompt, change_summary: str, created_by: str) -> None:
        """Create a version record for prompt changes."""
        from services.prompt_store.core.entities import PromptVersion
        from services.prompt_store.domain.prompts.versioning_repository import PromptVersioningRepository

        version_repo = PromptVersioningRepository()
        version = PromptVersion(
            prompt_id=prompt.id,
            version=prompt.version,
            content=prompt.content,
            variables=prompt.variables,
            change_summary=change_summary,
            created_by=created_by
        )
        version_repo.save(version)

    def _get_prompt_versions(self, prompt_id: str) -> List[Any]:
        """Get version history for a prompt."""
        from services.prompt_store.domain.prompts.versioning_repository import PromptVersioningRepository

        version_repo = PromptVersioningRepository()
        return version_repo.get_versions_for_prompt(prompt_id)

    async def _cache_prompt(self, prompt: Prompt) -> None:
        """Cache prompt asynchronously."""
        cache_key = f"prompt:{prompt.category}:{prompt.name}"
        await prompt_store_cache.set(cache_key, prompt, ttl=3600)

    async def _invalidate_prompt_cache(self, category: str, name: str) -> None:
        """Invalidate prompt cache."""
        cache_key = f"prompt:{category}:{name}"
        await prompt_store_cache.delete(cache_key)

    async def _increment_usage_async(self, prompt_id: str) -> None:
        """Increment usage count asynchronously."""
        self.repository.increment_usage_count(prompt_id)
