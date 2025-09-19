"""Template Service Module.

This module provides predefined project templates for quick simulation setup,
including e-commerce, mobile apps, APIs, microservices, data pipelines, and ML projects.
"""

from .template_manager import TemplateManager
from .project_templates import ProjectTemplates

__all__ = ['TemplateManager', 'ProjectTemplates']
