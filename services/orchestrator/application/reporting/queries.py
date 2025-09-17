"""Reporting Application Queries"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class GetReportQuery:
    """Query to get a report."""
    report_id: str


@dataclass
class ListReportsQuery:
    """Query to list reports."""
    report_type_filter: Optional[str] = None
    limit: int = 50
    offset: int = 0
