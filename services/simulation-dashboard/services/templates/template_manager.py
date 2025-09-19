"""Template Manager.

This module provides functionality for managing project templates,
including loading, applying, customizing, and sharing templates.
"""

import json
import os
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime
import uuid

from infrastructure.logging.logger import get_dashboard_logger

logger = get_dashboard_logger("template_manager")


class TemplateManager:
    """Manager for project templates."""

    def __init__(self, templates_dir: Optional[str] = None):
        """Initialize template manager."""
        if templates_dir is None:
            # Default to templates directory relative to this file
            templates_dir = Path(__file__).parent / "data"

        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(exist_ok=True)
        self.templates_cache: Dict[str, Dict[str, Any]] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Load all available templates."""
        try:
            # Load built-in templates
            from .project_templates import BUILT_IN_TEMPLATES

            for template_id, template in BUILT_IN_TEMPLATES.items():
                self.templates_cache[template_id] = template
                logger.info(f"Loaded built-in template: {template_id}")

            # Load custom templates from files
            for template_file in self.templates_dir.glob("*.json"):
                try:
                    with open(template_file, 'r') as f:
                        custom_template = json.load(f)
                        template_id = custom_template.get('id', template_file.stem)
                        self.templates_cache[template_id] = custom_template
                        logger.info(f"Loaded custom template: {template_id}")
                except Exception as e:
                    logger.error(f"Failed to load template {template_file}: {e}")

        except Exception as e:
            logger.error(f"Error loading templates: {e}")

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a template by ID."""
        return self.templates_cache.get(template_id)

    def get_all_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get all available templates."""
        return self.templates_cache.copy()

    def get_templates_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get templates by category."""
        return [
            template for template in self.templates_cache.values()
            if template.get('category', '').lower() == category.lower()
        ]

    def get_template_categories(self) -> List[str]:
        """Get all available template categories."""
        categories = set()
        for template in self.templates_cache.values():
            category = template.get('category', 'General')
            categories.add(category)
        return sorted(list(categories))

    def apply_template(
        self,
        template_id: str,
        customizations: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Apply a template with customizations."""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Deep copy the template
        import copy
        applied_config = copy.deepcopy(template.get('configuration', {}))

        # Apply customizations
        if customizations:
            self._apply_customizations(applied_config, customizations)

        # Generate unique IDs and timestamps
        applied_config['id'] = str(uuid.uuid4())
        applied_config['created_from_template'] = template_id
        applied_config['applied_at'] = datetime.now().isoformat()

        logger.info(f"Applied template {template_id} with customizations")
        return applied_config

    def _apply_customizations(
        self,
        config: Dict[str, Any],
        customizations: Dict[str, Any]
    ) -> None:
        """Apply customizations to configuration."""
        def update_nested_dict(d: Dict[str, Any], updates: Dict[str, Any]) -> None:
            for key, value in updates.items():
                if isinstance(value, dict) and key in d and isinstance(d[key], dict):
                    update_nested_dict(d[key], value)
                else:
                    d[key] = value

        update_nested_dict(config, customizations)

    def create_custom_template(
        self,
        base_template_id: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a custom template."""
        template_id = f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        template = {
            'id': template_id,
            'name': metadata.get('name', f'Custom Template {template_id}'),
            'description': metadata.get('description', 'Custom project template'),
            'category': metadata.get('category', 'Custom'),
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
            'tags': metadata.get('tags', []),
            'configuration': configuration or {}
        }

        # If based on existing template, inherit its configuration
        if base_template_id:
            base_template = self.get_template(base_template_id)
            if base_template:
                template['configuration'] = base_template.get('configuration', {}).copy()
                template['based_on'] = base_template_id

        # Save to file
        template_file = self.templates_dir / f"{template_id}.json"
        try:
            with open(template_file, 'w') as f:
                json.dump(template, f, indent=2, default=str)
            self.templates_cache[template_id] = template
            logger.info(f"Created custom template: {template_id}")
        except Exception as e:
            logger.error(f"Failed to save custom template: {e}")
            raise

        return template_id

    def delete_template(self, template_id: str) -> bool:
        """Delete a custom template."""
        if template_id not in self.templates_cache:
            return False

        template = self.templates_cache[template_id]
        if template.get('built_in', False):
            raise ValueError("Cannot delete built-in templates")

        # Remove from cache
        del self.templates_cache[template_id]

        # Remove file if it exists
        template_file = self.templates_dir / f"{template_id}.json"
        if template_file.exists():
            try:
                template_file.unlink()
            except Exception as e:
                logger.error(f"Failed to delete template file: {e}")

        logger.info(f"Deleted template: {template_id}")
        return True

    def export_template(self, template_id: str, filepath: str) -> bool:
        """Export a template to a file."""
        template = self.get_template(template_id)
        if not template:
            return False

        try:
            with open(filepath, 'w') as f:
                json.dump(template, f, indent=2, default=str)
            logger.info(f"Exported template {template_id} to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to export template: {e}")
            return False

    def import_template(self, filepath: str) -> Optional[str]:
        """Import a template from a file."""
        try:
            with open(filepath, 'r') as f:
                template = json.load(f)

            template_id = template.get('id', f"imported_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            template['imported_at'] = datetime.now().isoformat()

            # Save to templates directory
            import_filepath = self.templates_dir / f"{template_id}.json"
            with open(import_filepath, 'w') as f:
                json.dump(template, f, indent=2, default=str)

            self.templates_cache[template_id] = template
            logger.info(f"Imported template: {template_id}")
            return template_id

        except Exception as e:
            logger.error(f"Failed to import template: {e}")
            return None

    def search_templates(
        self,
        query: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search templates by query, category, and tags."""
        results = []

        for template in self.templates_cache.values():
            # Text search in name and description
            search_text = f"{template.get('name', '')} {template.get('description', '')}".lower()
            if query.lower() not in search_text:
                continue

            # Category filter
            if category and template.get('category', '').lower() != category.lower():
                continue

            # Tags filter
            if tags:
                template_tags = set(template.get('tags', []))
                search_tags = set(tags)
                if not search_tags.issubset(template_tags):
                    continue

            results.append(template)

        return results

    def get_template_stats(self) -> Dict[str, Any]:
        """Get template usage statistics."""
        stats = {
            'total_templates': len(self.templates_cache),
            'categories': {},
            'built_in_count': 0,
            'custom_count': 0,
            'total_tags': set()
        }

        for template in self.templates_cache.values():
            # Category stats
            category = template.get('category', 'General')
            stats['categories'][category] = stats['categories'].get(category, 0) + 1

            # Built-in vs custom
            if template.get('built_in', False):
                stats['built_in_count'] += 1
            else:
                stats['custom_count'] += 1

            # Tags
            tags = template.get('tags', [])
            stats['total_tags'].update(tags)

        stats['total_tags'] = len(stats['total_tags'])
        return stats
