"""
Domain Entities for Audit Framework

Core business entities that represent the fundamental concepts
of the auditing domain with business logic and invariants.
"""

from .service_info import ServiceInfo
from .analysis_result import AnalysisResult

__all__ = ['ServiceInfo', 'AnalysisResult']
