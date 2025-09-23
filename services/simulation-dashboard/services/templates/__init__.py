"""Template Service Module.

This module provides predefined project templates for quick simulation setup,
including e-commerce, mobile apps, APIs, microservices, data pipelines, and ML projects.
"""

from .project_templates import ProjectTemplates
from .template_manager import TemplateManager

__all__ = ["TemplateManager", "ProjectTemplates"]
