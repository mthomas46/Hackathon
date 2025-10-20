"""
Discovery Module

Provides repository scanning, file classification, and processing plan generation.
"""

from .repository_scanner import RepositoryScanner, RepositoryInventory, FileInfo
from .file_classifier import FileClassifier, ClassifiedFile, ImportanceLevel
from .processing_planner import ProcessingPlanner, ProcessingPlan, SubJobPlan
from .discovery_engine import DiscoveryEngine, get_discovery_engine

__all__ = [
    "RepositoryScanner",
    "RepositoryInventory",
    "FileInfo",
    "FileClassifier",
    "ClassifiedFile",
    "ImportanceLevel",
    "ProcessingPlanner",
    "ProcessingPlan",
    "SubJobPlan",
    "DiscoveryEngine",
    "get_discovery_engine",
]

