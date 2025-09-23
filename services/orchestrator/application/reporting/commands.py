"""Reporting Application Commands"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class GenerateReportCommand:
    """Command to generate a report."""

    report_type: str
    parameters: Dict[str, Any]
