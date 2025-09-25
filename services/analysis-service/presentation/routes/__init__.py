"""
Routes package for Analysis Service
Organized by domain/feature for DDD+REST compliance
"""

from . import analysis, documents, workflows, reports, health

__all__ = ['analysis', 'documents', 'workflows', 'reports', 'health']
