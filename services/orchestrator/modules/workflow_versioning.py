#!/usr/bin/env python3
"""
Workflow Versioning and Templating System

This module provides comprehensive workflow versioning, templating,
and collaboration capabilities including:
- Version control for workflows
- Template management and inheritance
- Collaborative editing
- Workflow composition and reuse
- Change tracking and audit trails
"""

import asyncio
import json
import uuid
import hashlib
from typing import Dict, Any, List, Optional, Callable, Type, Union, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import difflib
import copy

from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget
from services.shared.intelligent_caching import get_service_cache


class WorkflowVersionStatus(Enum):
    """Workflow version statuses."""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ChangeType(Enum):
    """Types of changes to workflows."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"
    CLONED = "cloned"
    MERGED = "merged"
    REVERTED = "reverted"


@dataclass
class WorkflowVersion:
    """Workflow version representation."""
    version_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str
    version_number: str  # Semantic versioning (e.g., "1.2.3")
    content: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: WorkflowVersionStatus = WorkflowVersionStatus.DRAFT
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    change_log: List[Dict[str, Any]] = field(default_factory=list)
    parent_version_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert version to dictionary."""
        return {
            "version_id": self.version_id,
            "workflow_id": self.workflow_id,
            "version_number": self.version_number,
            "content": self.content,
            "metadata": self.metadata,
            "status": self.status.value,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "change_log": self.change_log,
            "parent_version_id": self.parent_version_id,
            "tags": self.tags
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowVersion':
        """Create version from dictionary."""
        return cls(
            version_id=data["version_id"],
            workflow_id=data["workflow_id"],
            version_number=data["version_number"],
            content=data["content"],
            metadata=data["metadata"],
            status=WorkflowVersionStatus(data["status"]),
            created_by=data["created_by"],
            created_at=datetime.fromisoformat(data["created_at"]),
            approved_by=data.get("approved_by"),
            approved_at=datetime.fromisoformat(data["approved_at"]) if data.get("approved_at") else None,
            published_at=datetime.fromisoformat(data["published_at"]) if data.get("published_at") else None,
            change_log=data["change_log"],
            parent_version_id=data.get("parent_version_id"),
            tags=data["tags"]
        )


@dataclass
class WorkflowTemplate:
    """Reusable workflow template."""
    template_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    category: str
    content: Dict[str, Any]
    parameters: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    usage_count: int = 0
    rating: float = 0.0
    reviews: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary."""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "content": self.content,
            "parameters": self.parameters,
            "variables": self.variables,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "tags": self.tags,
            "usage_count": self.usage_count,
            "rating": self.rating,
            "reviews": self.reviews
        }


@dataclass
class WorkflowComposition:
    """Workflow composition from multiple templates."""
    composition_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    templates: List[Dict[str, Any]] = field(default_factory=list)  # Template references with overrides
    composition_logic: Dict[str, Any] = field(default_factory=dict)  # How templates are combined
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    resolved_workflow: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert composition to dictionary."""
        return {
            "composition_id": self.composition_id,
            "name": self.name,
            "description": self.description,
            "templates": self.templates,
            "composition_logic": self.composition_logic,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "resolved_workflow": self.resolved_workflow
        }


class WorkflowVersionControl:
    """Version control system for workflows."""

    def __init__(self):
        self.versions: Dict[str, Dict[str, WorkflowVersion]] = defaultdict(dict)  # workflow_id -> version_id -> version
        self.workflows: Dict[str, Dict[str, Any]] = {}  # workflow_id -> workflow metadata
        self.version_history: Dict[str, List[str]] = defaultdict(list)  # workflow_id -> list of version_ids
        self.branches: Dict[str, Dict[str, str]] = {}  # branch_name -> workflow_id -> current_version_id
        self.cache = get_service_cache(ServiceNames.ORCHESTRATOR)

    async def create_workflow(self, workflow_id: str, initial_content: Dict[str, Any],
                            created_by: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new workflow with initial version."""
        if workflow_id in self.workflows:
            raise ValueError(f"Workflow {workflow_id} already exists")

        # Create initial version
        initial_version = WorkflowVersion(
            workflow_id=workflow_id,
            version_number="1.0.0",
            content=initial_content,
            created_by=created_by,
            metadata=metadata or {},
            change_log=[{
                "change_type": ChangeType.CREATED.value,
                "description": "Initial workflow creation",
                "timestamp": datetime.now().isoformat(),
                "user": created_by
            }]
        )

        # Store version
        self.versions[workflow_id][initial_version.version_id] = initial_version
        self.version_history[workflow_id].append(initial_version.version_id)

        # Store workflow metadata
        self.workflows[workflow_id] = {
            "workflow_id": workflow_id,
            "current_version": initial_version.version_id,
            "created_by": created_by,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "status": "active",
            "metadata": metadata or {}
        }

        # Cache workflow
        await self.cache.set(f"workflow_{workflow_id}", self.workflows[workflow_id], ttl_seconds=3600)

        fire_and_forget("info", f"Created workflow {workflow_id} with initial version {initial_version.version_number}", ServiceNames.ORCHESTRATOR)
        return initial_version.version_id

    async def create_version(self, workflow_id: str, new_content: Dict[str, Any],
                           change_description: str, created_by: str,
                           version_increment: str = "patch") -> str:
        """Create a new version of a workflow."""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        current_version_id = self.workflows[workflow_id]["current_version"]
        current_version = self.versions[workflow_id][current_version_id]

        # Calculate new version number
        new_version_number = self._increment_version(current_version.version_number, version_increment)

        # Create new version
        new_version = WorkflowVersion(
            workflow_id=workflow_id,
            version_number=new_version_number,
            content=new_content,
            created_by=created_by,
            parent_version_id=current_version.version_id,
            change_log=[{
                "change_type": ChangeType.MODIFIED.value,
                "description": change_description,
                "timestamp": datetime.now().isoformat(),
                "user": created_by,
                "version_increment": version_increment
            }]
        )

        # Calculate diff with previous version
        diff = self._calculate_version_diff(current_version.content, new_content)
        new_version.metadata["diff"] = diff

        # Store new version
        self.versions[workflow_id][new_version.version_id] = new_version
        self.version_history[workflow_id].append(new_version.version_id)

        # Update workflow metadata
        self.workflows[workflow_id]["current_version"] = new_version.version_id
        self.workflows[workflow_id]["updated_at"] = datetime.now()

        # Cache updated workflow
        await self.cache.set(f"workflow_{workflow_id}", self.workflows[workflow_id], ttl_seconds=3600)

        fire_and_forget("info", f"Created version {new_version_number} for workflow {workflow_id}", ServiceNames.ORCHESTRATOR)
        return new_version.version_id

    def _increment_version(self, current_version: str, increment_type: str) -> str:
        """Increment semantic version number."""
        parts = current_version.split('.')
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {current_version}")

        major, minor, patch = map(int, parts)

        if increment_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif increment_type == "minor":
            minor += 1
            patch = 0
        elif increment_type == "patch":
            patch += 1
        else:
            raise ValueError(f"Invalid increment type: {increment_type}")

        return f"{major}.{minor}.{patch}"

    def _calculate_version_diff(self, old_content: Dict[str, Any], new_content: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate diff between workflow versions."""
        old_json = json.dumps(old_content, sort_keys=True, indent=2)
        new_json = json.dumps(new_content, sort_keys=True, indent=2)

        diff = {
            "old_size": len(old_json),
            "new_size": len(new_json),
            "size_change": len(new_json) - len(old_json),
            "changes": []
        }

        # Simple diff calculation
        old_lines = old_json.split('\n')
        new_lines = new_json.split('\n')

        for line in difflib.unified_diff(old_lines, new_lines, lineterm='', fromfile='old', tofile='new'):
            if line.startswith('@@') or line.startswith('+++') or line.startswith('---'):
                continue
            if line.startswith('+'):
                diff["changes"].append({"type": "addition", "content": line[1:]})
            elif line.startswith('-'):
                diff["changes"].append({"type": "deletion", "content": line[1:]})

        return diff

    async def approve_version(self, workflow_id: str, version_id: str, approved_by: str) -> bool:
        """Approve a workflow version."""
        if workflow_id not in self.versions or version_id not in self.versions[workflow_id]:
            return False

        version = self.versions[workflow_id][version_id]
        version.status = WorkflowVersionStatus.APPROVED
        version.approved_by = approved_by
        version.approved_at = datetime.now()

        fire_and_forget("info", f"Version {version.version_number} of workflow {workflow_id} approved by {approved_by}", ServiceNames.ORCHESTRATOR)
        return True

    async def publish_version(self, workflow_id: str, version_id: str) -> bool:
        """Publish a workflow version."""
        if workflow_id not in self.versions or version_id not in self.versions[workflow_id]:
            return False

        version = self.versions[workflow_id][version_id]
        if version.status != WorkflowVersionStatus.APPROVED:
            return False

        version.status = WorkflowVersionStatus.PUBLISHED
        version.published_at = datetime.now()

        # Update workflow to point to published version
        self.workflows[workflow_id]["published_version"] = version_id

        fire_and_forget("info", f"Version {version.version_number} of workflow {workflow_id} published", ServiceNames.ORCHESTRATOR)
        return True

    async def revert_to_version(self, workflow_id: str, version_id: str, reverted_by: str) -> Optional[str]:
        """Revert workflow to a previous version."""
        if workflow_id not in self.versions or version_id not in self.versions[workflow_id]:
            return None

        target_version = self.versions[workflow_id][version_id]

        # Create new version with reverted content
        new_version_id = await self.create_version(
            workflow_id=workflow_id,
            new_content=target_version.content,
            change_description=f"Reverted to version {target_version.version_number}",
            created_by=reverted_by,
            version_increment="patch"
        )

        # Update change log
        new_version = self.versions[workflow_id][new_version_id]
        new_version.change_log[0]["change_type"] = ChangeType.REVERTED.value

        fire_and_forget("info", f"Workflow {workflow_id} reverted to version {target_version.version_number}", ServiceNames.ORCHESTRATOR)
        return new_version_id

    def get_workflow_versions(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get all versions of a workflow."""
        if workflow_id not in self.versions:
            return []

        return [version.to_dict() for version in self.versions[workflow_id].values()]

    def get_version_history(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get version history for a workflow."""
        if workflow_id not in self.version_history:
            return []

        history = []
        for version_id in self.version_history[workflow_id]:
            version = self.versions[workflow_id][version_id]
            history.append({
                "version_id": version.version_id,
                "version_number": version.version_number,
                "status": version.status.value,
                "created_at": version.created_at.isoformat(),
                "created_by": version.created_by,
                "change_log": version.change_log
            })

        return history

    async def compare_versions(self, workflow_id: str, version_id_1: str, version_id_2: str) -> Dict[str, Any]:
        """Compare two workflow versions."""
        if workflow_id not in self.versions:
            return {"error": "Workflow not found"}

        if version_id_1 not in self.versions[workflow_id] or version_id_2 not in self.versions[workflow_id]:
            return {"error": "One or both versions not found"}

        version_1 = self.versions[workflow_id][version_id_1]
        version_2 = self.versions[workflow_id][version_id_2]

        comparison = {
            "workflow_id": workflow_id,
            "version_1": {
                "version_id": version_id_1,
                "version_number": version_1.version_number,
                "created_at": version_1.created_at.isoformat()
            },
            "version_2": {
                "version_id": version_id_2,
                "version_number": version_2.version_number,
                "created_at": version_2.created_at.isoformat()
            },
            "diff": self._calculate_version_diff(version_1.content, version_2.content),
            "comparison_timestamp": datetime.now().isoformat()
        }

        return comparison


class WorkflowTemplating:
    """Workflow template management system."""

    def __init__(self):
        self.templates: Dict[str, WorkflowTemplate] = {}
        self.template_categories: Dict[str, List[str]] = defaultdict(list)  # category -> template_ids
        self.user_templates: Dict[str, List[str]] = defaultdict(list)  # user_id -> template_ids
        self.cache = get_service_cache(ServiceNames.ORCHESTRATOR)

    async def create_template(self, name: str, description: str, category: str,
                            content: Dict[str, Any], created_by: str,
                            parameters: Optional[Dict[str, Any]] = None,
                            variables: Optional[Dict[str, Any]] = None,
                            tags: Optional[List[str]] = None) -> str:
        """Create a new workflow template."""
        template = WorkflowTemplate(
            name=name,
            description=description,
            category=category,
            content=content,
            parameters=parameters or {},
            variables=variables or {},
            created_by=created_by,
            tags=tags or []
        )

        self.templates[template.template_id] = template
        self.template_categories[category].append(template.template_id)
        self.user_templates[created_by].append(template.template_id)

        # Cache template
        await self.cache.set(f"template_{template.template_id}", template.to_dict(), ttl_seconds=3600)

        fire_and_forget("info", f"Created template '{name}' in category '{category}'", ServiceNames.ORCHESTRATOR)
        return template.template_id

    async def instantiate_template(self, template_id: str, parameter_values: Dict[str, Any],
                                 instantiated_by: str) -> Optional[Dict[str, Any]]:
        """Instantiate a workflow from a template."""
        if template_id not in self.templates:
            return None

        template = self.templates[template_id]

        # Deep copy template content
        workflow_content = copy.deepcopy(template.content)

        # Apply parameter values
        self._apply_parameters(workflow_content, template.parameters, parameter_values)

        # Apply variables
        if template.variables:
            self._apply_variables(workflow_content, template.variables)

        # Update template usage
        template.usage_count += 1
        template.updated_at = datetime.now()

        # Cache updated template
        await self.cache.set(f"template_{template_id}", template.to_dict(), ttl_seconds=3600)

        fire_and_forget("info", f"Template '{template.name}' instantiated by {instantiated_by}", ServiceNames.ORCHESTRATOR)

        return {
            "workflow_content": workflow_content,
            "template_id": template_id,
            "template_name": template.name,
            "instantiated_by": instantiated_by,
            "instantiated_at": datetime.now().isoformat(),
            "parameters_used": parameter_values
        }

    def _apply_parameters(self, content: Dict[str, Any], parameters: Dict[str, Any],
                         values: Dict[str, Any]):
        """Apply parameter values to workflow content."""
        def replace_placeholders(obj):
            if isinstance(obj, str):
                for param_name, param_config in parameters.items():
                    placeholder = f"{{{{ {param_name} }}}}"
                    if placeholder in obj and param_name in values:
                        obj = obj.replace(placeholder, str(values[param_name]))
                return obj
            elif isinstance(obj, dict):
                return {k: replace_placeholders(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_placeholders(item) for item in obj]
            else:
                return obj

        # Apply replacements to entire content structure
        for key, value in content.items():
            content[key] = replace_placeholders(value)

    def _apply_variables(self, content: Dict[str, Any], variables: Dict[str, Any]):
        """Apply variables to workflow content."""
        # Similar to parameters but for predefined variables
        self._apply_parameters(content, variables, variables)

    async def update_template_rating(self, template_id: str, user_id: str, rating: float,
                                   review: Optional[str] = None) -> bool:
        """Update template rating and add review."""
        if template_id not in self.templates:
            return False

        template = self.templates[template_id]

        # Remove existing review by this user
        template.reviews = [r for r in template.reviews if r.get("user_id") != user_id]

        # Add new review
        if review or rating > 0:
            review_data = {
                "user_id": user_id,
                "rating": rating,
                "review": review,
                "timestamp": datetime.now().isoformat()
            }
            template.reviews.append(review_data)

        # Recalculate average rating
        if template.reviews:
            template.rating = sum(r["rating"] for r in template.reviews) / len(template.reviews)

        template.updated_at = datetime.now()

        # Cache updated template
        await self.cache.set(f"template_{template_id}", template.to_dict(), ttl_seconds=3600)

        return True

    def get_templates_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get templates by category."""
        template_ids = self.template_categories.get(category, [])
        return [self.templates[tid].to_dict() for tid in template_ids if tid in self.templates]

    def get_popular_templates(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular templates."""
        sorted_templates = sorted(
            self.templates.values(),
            key=lambda t: (t.usage_count, t.rating),
            reverse=True
        )
        return [t.to_dict() for t in sorted_templates[:limit]]

    def search_templates(self, query: str, category: Optional[str] = None,
                        tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search templates by query, category, and tags."""
        results = []

        for template in self.templates.values():
            # Filter by category
            if category and template.category != category:
                continue

            # Filter by tags
            if tags and not any(tag in template.tags for tag in tags):
                continue

            # Search in name, description, and tags
            search_text = f"{template.name} {template.description} {' '.join(template.tags)}".lower()
            if query.lower() in search_text:
                results.append(template.to_dict())

        return results


class WorkflowCompositionEngine:
    """Workflow composition and reuse engine."""

    def __init__(self):
        self.compositions: Dict[str, WorkflowComposition] = {}
        self.composition_cache: Dict[str, Dict[str, Any]] = {}
        self.cache = get_service_cache(ServiceNames.ORCHESTRATOR)

    async def create_composition(self, name: str, description: str,
                               templates: List[Dict[str, Any]],
                               composition_logic: Dict[str, Any],
                               created_by: str) -> str:
        """Create a workflow composition from multiple templates."""
        composition = WorkflowComposition(
            name=name,
            description=description,
            templates=templates,
            composition_logic=composition_logic,
            created_by=created_by
        )

        self.compositions[composition.composition_id] = composition

        # Cache composition
        await self.cache.set(f"composition_{composition.composition_id}", composition.to_dict(), ttl_seconds=3600)

        fire_and_forget("info", f"Created workflow composition '{name}' with {len(templates)} templates", ServiceNames.ORCHESTRATOR)
        return composition.composition_id

    async def resolve_composition(self, composition_id: str,
                                parameter_values: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Resolve a composition into a complete workflow."""
        if composition_id not in self.compositions:
            return None

        composition = self.compositions[composition_id]

        # Check cache first
        cache_key = f"resolved_{composition_id}_{hash(json.dumps(parameter_values or {}, sort_keys=True))}"
        cached_workflow = await self.cache.get(cache_key)
        if cached_workflow:
            return cached_workflow

        # Resolve templates
        resolved_workflow = await self._resolve_templates(
            composition.templates,
            composition.composition_logic,
            parameter_values or {}
        )

        composition.resolved_workflow = resolved_workflow

        # Cache resolved workflow
        await self.cache.set(cache_key, resolved_workflow, ttl_seconds=1800)  # 30 minutes

        return resolved_workflow

    async def _resolve_templates(self, templates: List[Dict[str, Any]],
                               composition_logic: Dict[str, Any],
                               parameter_values: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve templates into a complete workflow."""
        resolved_steps = []
        step_counter = 0

        for template_ref in templates:
            template_id = template_ref.get("template_id")
            overrides = template_ref.get("overrides", {})

            # In practice, this would fetch template from template store
            # For now, create a mock resolved template
            template_steps = self._generate_template_steps(template_id, step_counter, overrides)
            resolved_steps.extend(template_steps)
            step_counter += len(template_steps)

        # Apply composition logic
        if composition_logic.get("parallel_execution"):
            # Group steps for parallel execution
            resolved_workflow = self._apply_parallel_logic(resolved_steps, composition_logic)
        elif composition_logic.get("conditional_execution"):
            # Apply conditional logic
            resolved_workflow = self._apply_conditional_logic(resolved_steps, composition_logic)
        else:
            # Sequential execution
            resolved_workflow = {
                "type": "sequential",
                "steps": resolved_steps
            }

        return resolved_workflow

    def _generate_template_steps(self, template_id: str, start_step: int,
                               overrides: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate steps from a template (mock implementation)."""
        # In practice, this would fetch actual template content
        return [
            {
                "step_id": f"step_{start_step + i}",
                "name": f"Template {template_id} Step {i}",
                "type": "service_call",
                "service": "mock_service",
                "operation": "mock_operation",
                "parameters": overrides
            }
            for i in range(3)  # Mock 3 steps per template
        ]

    def _apply_parallel_logic(self, steps: List[Dict[str, Any]], logic: Dict[str, Any]) -> Dict[str, Any]:
        """Apply parallel execution logic."""
        # Group steps into parallel batches
        batch_size = logic.get("batch_size", 2)
        batches = [steps[i:i + batch_size] for i in range(0, len(steps), batch_size)]

        return {
            "type": "parallel",
            "batches": batches,
            "batch_size": batch_size
        }

    def _apply_conditional_logic(self, steps: List[Dict[str, Any]], logic: Dict[str, Any]) -> Dict[str, Any]:
        """Apply conditional execution logic."""
        conditions = logic.get("conditions", [])

        return {
            "type": "conditional",
            "steps": steps,
            "conditions": conditions
        }


# Global instances
workflow_version_control = WorkflowVersionControl()
workflow_templating = WorkflowTemplating()
workflow_composition = WorkflowCompositionEngine()


async def initialize_workflow_versioning():
    """Initialize workflow versioning and templating."""
    # Create sample templates
    await workflow_templating.create_template(
        name="Document Analysis Pipeline",
        description="Complete document analysis workflow",
        category="analysis",
        content={
            "type": "sequential",
            "steps": [
                {"name": "Extract Text", "service": "source_agent"},
                {"name": "Analyze Content", "service": "analysis_service"},
                {"name": "Generate Summary", "service": "summarizer_hub"}
            ]
        },
        created_by="system",
        parameters={
            "document_url": {"type": "string", "required": True},
            "analysis_type": {"type": "string", "default": "comprehensive"}
        },
        tags=["analysis", "documents", "ai"]
    )

    fire_and_forget("info", "Workflow versioning and templating initialized", ServiceNames.ORCHESTRATOR)
