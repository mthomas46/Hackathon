"""
Template Manager Service

Handles loading, validation, rendering, and tracking of documentation templates.
Integrates with existing infrastructure for adaptive documentation generation.
"""

import logging
from typing import Dict, List, Optional, Any
from uuid import UUID
import json
from datetime import datetime
from jinja2 import Template as Jinja2Template, Environment, BaseLoader, TemplateError

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...storage.database import get_database
from ...storage.models_templates import (
    DocumentationTemplateModel,
    TemplateExecutionHistoryModel
)

logger = logging.getLogger(__name__)


class TemplateValidationError(Exception):
    """Raised when template structure validation fails."""
    pass


class TemplateManager:
    """
    Manages documentation templates.
    
    Responsibilities:
    - Load templates from database or YAML files
    - Validate template structure
    - Render templates with context
    - Track template usage and quality
    - Provide template recommendations
    """
    
    def __init__(self):
        """Initialize template manager."""
        self.jinja_env = Environment(
            loader=BaseLoader(),
            autoescape=False  # We control the input
        )
        self.cache: Dict[str, Dict[str, Any]] = {}
        logger.info("TemplateManager initialized")
    
    async def load_template(
        self,
        template_name: str,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Load template from database.
        
        Args:
            template_name: Template name or ID
            category: Optional category filter
        
        Returns:
            Template structure dict
            
        Raises:
            ValueError: If template not found
        """
        # Check cache first
        cache_key = f"{template_name}_{category}"
        if cache_key in self.cache:
            logger.debug(f"Template '{template_name}' loaded from cache")
            return self.cache[cache_key]
        
        async with get_database().session() as session:
            query = select(DocumentationTemplateModel).filter(
                DocumentationTemplateModel.name == template_name,
                DocumentationTemplateModel.is_active == True
            )
            
            if category:
                query = query.filter(DocumentationTemplateModel.category == category)
            
            result = await session.execute(query)
            template_model = result.scalar_one_or_none()
            
            if not template_model:
                raise ValueError(f"Template not found: {template_name}")
            
            template_dict = {
                "id": str(template_model.id),
                "name": template_model.name,
                "category": template_model.category,
                "version": template_model.version,
                "structure": template_model.structure,
                "render_options": template_model.render_options or {},
                "target_framework": template_model.target_framework,
                "target_audience": template_model.target_audience,
            }
            
            # Cache it
            self.cache[cache_key] = template_dict
            
            logger.info(f"Template '{template_name}' loaded from database")
            return template_dict
    
    async def create_template(
        self,
        name: str,
        category: str,
        structure: Dict[str, Any],
        created_by: str,
        description: Optional[str] = None,
        target_framework: Optional[str] = None,
        target_audience: Optional[str] = None,
        render_options: Optional[Dict[str, Any]] = None,
        is_system_template: bool = False,
        is_public: bool = False
    ) -> UUID:
        """
        Create new template.
        
        Args:
            name: Template name (must be unique)
            category: Template category
            structure: Template structure (will be validated)
            created_by: Username or system identifier
            description: Template description
            target_framework: Target framework (e.g., 'scala_play', 'java_spring')
            target_audience: Target audience (e.g., 'developers', 'operators')
            render_options: Rendering options
            is_system_template: Whether this is a system template
            is_public: Whether template is publicly accessible
        
        Returns:
            Template ID
            
        Raises:
            TemplateValidationError: If structure validation fails
        """
        # Validate structure
        self._validate_template_structure(structure)
        
        async with get_database().session() as session:
            template = DocumentationTemplateModel(
                name=name,
                category=category,
                structure=structure,
                created_by=created_by,
                description=description,
                target_framework=target_framework,
                target_audience=target_audience,
                render_options=render_options,
                is_system_template=is_system_template,
                is_public=is_public
            )
            
            session.add(template)
            await session.commit()
            await session.refresh(template)
            
            logger.info(f"✅ Template '{name}' created (ID: {template.id})")
            return template.id
    
    def _validate_template_structure(self, structure: Dict[str, Any]) -> None:
        """
        Validate template structure.
        
        Checks:
        - Required fields present
        - Section order is sequential
        - Prompt templates are valid
        - Validation rules are valid
        
        Raises:
            TemplateValidationError: If validation fails
        """
        if "sections" not in structure:
            raise TemplateValidationError("Template must have 'sections' field")
        
        sections = structure["sections"]
        if not isinstance(sections, list) or len(sections) == 0:
            raise TemplateValidationError("Template must have at least one section")
        
        seen_orders = set()
        for section in sections:
            # Check required fields
            required_fields = ["name", "order", "required"]
            for field in required_fields:
                if field not in section:
                    raise TemplateValidationError(
                        f"Section missing required field: {field}"
                    )
            
            # Check order uniqueness
            order = section["order"]
            if order in seen_orders:
                raise TemplateValidationError(f"Duplicate section order: {order}")
            seen_orders.add(order)
            
            # Validate prompt template if present
            if "prompt_template" in section:
                prompt = section["prompt_template"]
                if prompt.count("{") != prompt.count("}"):
                    raise TemplateValidationError(
                        f"Unbalanced braces in prompt for section: {section['name']}"
                    )
        
        logger.debug(f"Template structure validated: {len(sections)} sections")
    
    async def render_section(
        self,
        template: Dict[str, Any],
        section_name: str,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Render a section using template structure.
        
        Args:
            template: Template dict
            section_name: Section to render
            content: Generated content
            context: Optional context variables for metadata
        
        Returns:
            Formatted section markdown
            
        Raises:
            ValueError: If section not found in template
        """
        context = context or {}
        
        # Find section in template
        section = next(
            (s for s in template["structure"]["sections"] if s["name"] == section_name),
            None
        )
        
        if not section:
            raise ValueError(f"Section not found in template: {section_name}")
        
        # Get formatting options
        formatting = template["structure"].get("formatting", {})
        header_style = formatting.get("header_style", "atx")
        
        # Build section header
        header_level = 2  # Assuming top-level sections are ##
        if header_style == "atx":
            header = f"{'#' * header_level} {section_name}"
        else:
            header = f"{section_name}\n{'=' * len(section_name)}"
        
        # Build subsections
        rendered = f"{header}\n\n"
        
        if "subsections" in section:
            for subsection in section["subsections"]:
                rendered += f"{'#' * (header_level + 1)} {subsection}\n\n"
        
        # Add content
        rendered += content
        
        # Add validation markers if in verbose mode
        if context.get("transparency_mode") == "verbose":
            validation = section.get("validation", {})
            rendered += f"\n\n<!-- Template: {template['name']}, Section: {section_name}, Validation: {validation} -->\n"
        
        return rendered
    
    async def validate_generated_content(
        self,
        template: Dict[str, Any],
        section_name: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Validate generated content against template rules.
        
        Args:
            template: Template dict
            section_name: Section name
            content: Generated content
        
        Returns:
            Validation result with errors/warnings
        """
        section = next(
            (s for s in template["structure"]["sections"] if s["name"] == section_name),
            None
        )
        
        if not section:
            return {"valid": True, "errors": [], "warnings": []}
        
        validation = section.get("validation", {})
        errors = []
        warnings = []
        
        # Check word count
        word_count = len(content.split())
        
        if "min_words" in validation:
            if word_count < validation["min_words"]:
                errors.append(
                    f"Content too short: {word_count} words (min: {validation['min_words']})"
                )
        
        if "max_words" in validation:
            if word_count > validation["max_words"]:
                warnings.append(
                    f"Content too long: {word_count} words (max: {validation['max_words']})"
                )
        
        # Check for code examples
        if validation.get("must_include_code_example", False):
            if "```" not in content:
                errors.append("Section must include code example")
        
        # Check for specific keywords
        if "must_include" in validation:
            for keyword in validation["must_include"]:
                if keyword.lower() not in content.lower():
                    warnings.append(f"Section should mention: {keyword}")
        
        adherence_score = 1.0 if len(errors) == 0 else max(0.0, 1.0 - (len(errors) * 0.2))
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "word_count": word_count,
            "adherence_score": adherence_score
        }
    
    async def track_template_usage(
        self,
        template_id: UUID,
        run_id: UUID,
        artifact_id: Optional[UUID],
        section_name: str,
        validation_result: Dict[str, Any]
    ) -> None:
        """
        Track template usage for analytics.
        
        Args:
            template_id: Template ID
            run_id: Documentation run ID
            artifact_id: Artifact ID (if created)
            section_name: Section name
            validation_result: Validation result
        """
        async with get_database().session() as session:
            # Update usage count
            template = await session.get(DocumentationTemplateModel, template_id)
            if template:
                template.usage_count += 1
                template.last_used_at = datetime.utcnow()
            
            # Create execution history
            execution = TemplateExecutionHistoryModel(
                template_id=template_id,
                run_id=run_id,
                artifact_id=artifact_id,
                section_name=section_name,
                adherence_score=validation_result.get("adherence_score"),
                validation_errors=validation_result.get("errors", []),
                rendering_errors=[]
            )
            
            session.add(execution)
            await session.commit()
            
            logger.debug(
                f"Template usage tracked: {template_id} - {section_name} "
                f"(adherence: {validation_result.get('adherence_score', 'N/A')})"
            )
    
    async def get_recommended_template(
        self,
        category: str,
        framework: Optional[str] = None,
        audience: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get recommended template based on criteria.
        
        Args:
            category: Template category
            framework: Target framework (optional)
            audience: Target audience (optional)
        
        Returns:
            Best matching template
            
        Raises:
            ValueError: If no template found
        """
        async with get_database().session() as session:
            query = select(DocumentationTemplateModel).filter(
                DocumentationTemplateModel.category == category,
                DocumentationTemplateModel.is_active == True
            )
            
            # Prioritize templates matching framework and audience
            if framework:
                query = query.filter(
                    (DocumentationTemplateModel.target_framework == framework) |
                    (DocumentationTemplateModel.target_framework == None)
                )
            
            if audience:
                query = query.filter(
                    (DocumentationTemplateModel.target_audience == audience) |
                    (DocumentationTemplateModel.target_audience == None)
                )
            
            # Order by usage count (popular templates first)
            query = query.order_by(DocumentationTemplateModel.usage_count.desc())
            
            result = await session.execute(query)
            template_model = result.scalar_one_or_none()
            
            if not template_model:
                raise ValueError(f"No template found for category: {category}")
            
            return await self.load_template(template_model.name, category)
    
    async def list_templates(
        self,
        category: Optional[str] = None,
        framework: Optional[str] = None,
        user_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List available templates.
        
        Args:
            category: Filter by category
            framework: Filter by framework
            user_only: Only user-supplied templates
        
        Returns:
            List of template summaries
        """
        async with get_database().session() as session:
            query = select(DocumentationTemplateModel).filter(
                DocumentationTemplateModel.is_active == True
            )
            
            if category:
                query = query.filter(DocumentationTemplateModel.category == category)
            
            if framework:
                query = query.filter(DocumentationTemplateModel.target_framework == framework)
            
            if user_only:
                query = query.filter(DocumentationTemplateModel.is_system_template == False)
            
            result = await session.execute(query)
            templates = result.scalars().all()
            
            return [
                {
                    "id": str(t.id),
                    "name": t.name,
                    "category": t.category,
                    "version": t.version,
                    "description": t.description,
                    "target_framework": t.target_framework,
                    "target_audience": t.target_audience,
                    "usage_count": t.usage_count,
                    "is_system_template": t.is_system_template
                }
                for t in templates
            ]
    
    async def update_template(
        self,
        template_id: UUID,
        **updates
    ) -> None:
        """
        Update template fields.
        
        Args:
            template_id: Template ID
            **updates: Fields to update
        """
        async with get_database().session() as session:
            template = await session.get(DocumentationTemplateModel, template_id)
            
            if not template:
                raise ValueError(f"Template not found: {template_id}")
            
            # Update allowed fields
            allowed_fields = [
                'description', 'structure', 'render_options', 
                'target_framework', 'target_audience', 'is_active', 'is_public'
            ]
            
            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(template, field, value)
            
            template.updated_at = datetime.utcnow()
            
            await session.commit()
            
            # Clear cache
            self.cache.clear()
            
            logger.info(f"Template '{template.name}' updated")
    
    async def delete_template(self, template_id: UUID) -> None:
        """
        Delete template (soft delete by setting is_active=False).
        
        Args:
            template_id: Template ID
        """
        async with get_database().session() as session:
            template = await session.get(DocumentationTemplateModel, template_id)
            
            if not template:
                raise ValueError(f"Template not found: {template_id}")
            
            template.is_active = False
            template.updated_at = datetime.utcnow()
            
            await session.commit()
            
            # Clear cache
            self.cache.clear()
            
            logger.info(f"Template '{template.name}' deleted (soft)")


# Singleton instance
_template_manager: Optional[TemplateManager] = None


def get_template_manager() -> TemplateManager:
    """Get or create singleton template manager."""
    global _template_manager
    if _template_manager is None:
        _template_manager = TemplateManager()
    return _template_manager

