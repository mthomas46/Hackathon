"""
Infrastructure Layer for Audit Framework

Contains external service integrations, file system operations,
and other infrastructure concerns that the application depends on.
"""

from .external_services import ThirdPartyToolService
from .file_system import FileSystemService, ServiceDiscoveryService

__all__ = [
    'ThirdPartyToolService',
    'FileSystemService',
    'ServiceDiscoveryService'
]
