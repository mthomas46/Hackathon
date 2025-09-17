"""Prompt handlers for Prompt Store service.

Handles the complex logic for prompt CRUD endpoints.
"""
from typing import Optional, List, Tuple, Dict, Any

from .shared_utils import (
    get_prompt_store_client,
    handle_prompt_error,
    create_prompt_success_response,
    build_prompt_context,
    validate_prompt_data
)
from services.shared.core.constants_new import ErrorCodes


class PromptHandlers:
    """Handles prompt CRUD operations."""

    @staticmethod
    async def handle_create_prompt(prompt_data) -> Dict[str, Any]:
        """Create a new prompt."""
        try:
            db = get_prompt_store_client()

            # Check if prompt already exists
            existing = db.get_prompt_by_name(prompt_data.category, prompt_data.name)
            if existing:
                return handle_prompt_error(
                    Exception(f"Prompt '{prompt_data.name}' already exists in category '{prompt_data.category}'"),
                    ErrorCodes.VALIDATION_ERROR,
                    category=prompt_data.category,
                    name=prompt_data.name
                )

            # Validate prompt data
            validated_data = validate_prompt_data(prompt_data.dict())

            from ..models import Prompt
            prompt = Prompt(
                name=validated_data['name'],
                category=validated_data['category'],
                description=validated_data.get('description', ""),
                content=validated_data['content'],
                variables=validated_data['variables'],
                tags=validated_data['tags'],
                created_by="api_user"
            )

            created = db.create_prompt(prompt)
            context = {"prompt_id": created.id, "category": created.category}
            return create_prompt_success_response("created", {"prompt_id": created.id}, **context)

        except Exception as e:
            context = {"category": getattr(prompt_data, 'category', None)}
            return handle_prompt_error("create", e, **context)

    @staticmethod
    async def handle_list_prompts(category: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """List prompts."""
        try:
            db = get_prompt_store_client()
            filters = {"category": category} if category else {}
            prompts, total = db.list_prompts(filters, limit)

            result = {
                "prompts": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "category": p.category,
                        "description": p.description,
                        "tags": p.tags,
                        "version": p.version
                    } for p in prompts
                ],
                "total": total
            }

            context = build_prompt_context("list", category=category, limit=limit, total=total)
            return create_prompt_success_response("retrieved", result, **context)

        except Exception as e:
            context = build_prompt_context("list", category=category)
            return handle_prompt_error("retrieve", e, **context)

    @staticmethod
    async def handle_get_prompt_by_name(category: str, name: str, **variables) -> Dict[str, Any]:
        """Get prompt by category/name and fill variables."""
        try:
            db = get_prompt_store_client()
            prompt = db.get_prompt_by_name(category, name)

            if not prompt:
                return handle_prompt_error(
                    "find",
                    Exception(f"Prompt '{name}' not found in category '{category}'"),
                    ErrorCodes.PROMPT_NOT_FOUND,
                    category=category,
                    name=name
                )

            # Fill template variables
            content = prompt.content
            for var_name, var_value in variables.items():
                content = content.replace(f"{{{var_name}}}", str(var_value))

            result = {
                "prompt": content,
                "id": prompt.id,
                "name": prompt.name,
                "version": prompt.version
            }

            context = build_prompt_context("retrieve", prompt_id=prompt.id, category=category, variables_count=len(variables))
            return create_prompt_success_response("retrieved", result, **context)

        except Exception as e:
            context = build_prompt_context("retrieve", category=category, name=name)
            return handle_prompt_error("retrieve", e, **context)

    @staticmethod
    async def handle_update_prompt(prompt_id: str, updates) -> Dict[str, Any]:
        """Update a prompt."""
        try:
            db = get_prompt_store_client()
            update_dict = updates.dict(exclude_unset=True)
            updated = db.update_prompt(prompt_id, update_dict, "api_user")

            if not updated:
                return handle_prompt_error(
                    "find",
                    Exception(f"Prompt '{prompt_id}' not found for update"),
                    ErrorCodes.PROMPT_NOT_FOUND,
                    prompt_id=prompt_id
                )

            context = build_prompt_context("update", prompt_id=prompt_id)
            return create_prompt_success_response("updated", {"prompt_id": prompt_id}, **context)

        except Exception as e:
            context = build_prompt_context("update", prompt_id=prompt_id)
            return handle_prompt_error("update", e, **context)

    @staticmethod
    async def handle_delete_prompt(prompt_id: str) -> Dict[str, Any]:
        """Delete a prompt."""
        try:
            db = get_prompt_store_client()
            if db.delete_prompt(prompt_id, "api_user"):
                context = build_prompt_context("delete", prompt_id=prompt_id)
                return create_prompt_success_response("deleted", {"prompt_id": prompt_id}, **context)

            return handle_prompt_error(
                "find",
                Exception(f"Prompt '{prompt_id}' not found for deletion"),
                ErrorCodes.PROMPT_NOT_FOUND,
                prompt_id=prompt_id
            )

        except Exception as e:
            context = build_prompt_context("delete", prompt_id=prompt_id)
            return handle_prompt_error("delete", e, **context)

    @staticmethod
    async def handle_migrate_from_yaml() -> Dict[str, Any]:
        """Migrate prompts from YAML config."""
        try:
            db = get_prompt_store_client()
            yaml_path = "services/shared/prompts.yaml"
            count = db.migrate_from_yaml(yaml_path)

            result = {"migrated": count, "status": "completed"}
            context = {"migrated_count": count}
            # Filter out keys that might conflict with function parameters
            filtered_context = {k: v for k, v in context.items() if k not in ['operation', 'operation_name']}
            return create_prompt_success_response("migrated", result, **filtered_context)

        except Exception as e:
            context = {}
            return handle_prompt_error("migrate", e, **context)


# Create singleton instance
prompt_handlers = PromptHandlers()
