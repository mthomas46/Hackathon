"""
Adaptive Documentation Services

Provides discovery, prompt tracking, citation management, and transparency
logging for adaptive documentation generation.
"""

from .discovery_service import DiscoveryService, get_discovery_service
from .prompt_tracker import PromptTracker, get_prompt_tracker
from .citation_manager import CitationManager, get_citation_manager
from .transparency_logger import TransparencyLogger, get_transparency_logger
from .runtime_framework_detector import RuntimeFrameworkDetector, get_runtime_detector

__all__ = [
    "DiscoveryService",
    "get_discovery_service",
    "PromptTracker",
    "get_prompt_tracker",
    "CitationManager",
    "get_citation_manager",
    "TransparencyLogger",
    "get_transparency_logger",
    "RuntimeFrameworkDetector",
    "get_runtime_detector",
]

