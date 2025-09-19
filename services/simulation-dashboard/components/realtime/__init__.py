"""Real-time Components Module.

This module provides real-time components for the simulation dashboard,
including live metrics, event streams, progress indicators, and status dashboards.
"""

from .live_metrics import render_live_metrics
from .event_stream import render_event_stream
from .progress_indicators import render_progress_indicator
from .status_dashboard import render_status_dashboard

__all__ = [
    'render_live_metrics',
    'render_event_stream',
    'render_progress_indicator',
    'render_status_dashboard'
]
