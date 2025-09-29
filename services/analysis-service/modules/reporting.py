"""Reporting functionality for the Analysis Service.

This module provides a unified reporting interface that leverages the optimized
analysis functions from analysis_logic.py to eliminate code duplication.
"""

from typing import List, Dict, Any
from services.shared.core.models.models import Finding

# Import the optimized functions from analysis_logic to avoid duplication
from .analysis_logic import generate_summary_report as _generate_summary_report
from .analysis_logic import generate_trends_report as _generate_trends_report

# Import shared utilities for consistency across analysis modules
from .shared_utils import (
    build_analysis_context,
    create_analysis_success_response
)


def generate_summary_report(findings: List[Finding]) -> Dict[str, Any]:
    """Generate summary report of findings using optimized analysis logic.

    This function serves as a unified interface that delegates to the
    optimized implementation in analysis_logic.py, ensuring consistency
    and eliminating code duplication across modules.
    """
    context = build_analysis_context("summary_report", total_findings=len(findings))
    result = _generate_summary_report(findings)
    return create_analysis_success_response("summary report generation", result, **context)


def generate_trends_report(findings: List[Finding], time_window: str = "7d") -> Dict[str, Any]:
    """Generate trends report showing patterns over time using optimized analysis logic.

    This function serves as a unified interface that delegates to the
    optimized implementation in analysis_logic.py, ensuring consistency
    and eliminating code duplication across modules.
    """
    context = build_analysis_context("trends_report", total_findings=len(findings), time_window=time_window)
    result = _generate_trends_report(findings, time_window)
    return create_analysis_success_response("trends report generation", result, **context)


