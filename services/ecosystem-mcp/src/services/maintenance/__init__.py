"""
Documentation Maintenance Services (Phase 2.2 & 2.3)

Services for maintaining documentation quality:
- Staleness Detection: Find outdated docs
- Coverage Analysis: Track documentation coverage
- Consistency Checker: Find conflicting information
- Automated Refresher: Auto-update docs
- Quality Dashboard: Real-time quality metrics
- Dependency Tracker: Track cross-references
- Version Comparator: Compare document versions
- Search Service: Advanced search and discovery
"""

from .staleness_detector import StalenessDetector
from .coverage_analyzer import CoverageAnalyzer
from .consistency_checker import ConsistencyChecker
from .automated_refresher import AutomatedRefresher
from .quality_dashboard import QualityDashboard
from .dependency_tracker import DependencyTracker
from .version_comparator import VersionComparator

__all__ = [
    "StalenessDetector",
    "CoverageAnalyzer",
    "ConsistencyChecker",
    "AutomatedRefresher",
    "QualityDashboard",
    "DependencyTracker",
    "VersionComparator",
]

