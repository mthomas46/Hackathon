"""
Domain Value Objects for Audit Framework

Immutable value objects that represent concepts in the auditing domain
with their own validation rules and behavior.
"""

from .audit_profile import AuditProfile
from .thresholds import ThresholdConfig

__all__ = ['AuditProfile', 'ThresholdConfig']
