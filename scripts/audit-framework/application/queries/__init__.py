"""
Queries for Audit Framework

Query objects that represent read operations.
Following CQRS pattern for clear read intent expression.
"""

from .get_audit_history_query import GetAuditHistoryQuery
from .get_audit_trends_query import GetAuditTrendsQuery

__all__ = ['GetAuditHistoryQuery', 'GetAuditTrendsQuery']
