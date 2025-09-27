"""Architecture Digitizer infrastructure layer package.

This package contains infrastructure concerns for the Architecture
Digitizer service, including event handling, external service
integrations, and system-level operations.
"""

from .events import register_lifecycle_events

__all__ = ["register_lifecycle_events"]
