"""Collaboration domain for multi-user planning sessions."""

from .entities import (
    PlanningSession,
    Participant,
    Change,
    ConflictResolution,
    SessionStatus,
    ParticipantRole,
    ChangeType
)
from .services import CollaborationManager

__all__ = [
    'PlanningSession',
    'Participant',
    'Change',
    'ConflictResolution',
    'SessionStatus',
    'ParticipantRole',
    'ChangeType',
    'CollaborationManager'
]

