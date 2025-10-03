"""
Collaboration Entities for Planning Sessions
=============================================

Domain entities for multi-user collaborative planning.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
import uuid


class SessionStatus(Enum):
    """Collaboration session status."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ParticipantRole(Enum):
    """Participant role in collaboration session."""
    OWNER = "owner"
    EDITOR = "editor"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


class ChangeType(Enum):
    """Type of change made to roadmap."""
    FEATURE_ADDED = "feature_added"
    FEATURE_UPDATED = "feature_updated"
    FEATURE_REMOVED = "feature_removed"
    DEPENDENCY_ADDED = "dependency_added"
    DEPENDENCY_REMOVED = "dependency_removed"
    MILESTONE_UPDATED = "milestone_updated"
    TIMELINE_ADJUSTED = "timeline_adjusted"
    COMMENT_ADDED = "comment_added"


@dataclass
class Participant:
    """Participant in a collaborative planning session."""
    user_id: str
    name: str
    email: str
    role: ParticipantRole
    joined_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    is_online: bool = True
    
    def update_activity(self):
        """Update last active timestamp."""
        self.last_active = datetime.now()
    
    def can_edit(self) -> bool:
        """Check if participant can edit."""
        return self.role in [ParticipantRole.OWNER, ParticipantRole.EDITOR]
    
    def can_approve(self) -> bool:
        """Check if participant can approve changes."""
        return self.role in [ParticipantRole.OWNER, ParticipantRole.REVIEWER]


@dataclass
class Change:
    """A change made to the roadmap."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    change_type: ChangeType = ChangeType.FEATURE_UPDATED
    user_id: str = ""
    user_name: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    version: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'change_type': self.change_type.value,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'description': self.description,
            'version': self.version
        }


@dataclass
class ConflictResolution:
    """Resolution for a conflict between changes."""
    conflict_id: str
    resolution_type: str  # "accept_local", "accept_remote", "merge", "manual"
    resolved_by: str
    resolved_at: datetime = field(default_factory=datetime.now)
    resolution_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlanningSession:
    """
    Collaborative planning session entity.
    
    Represents a multi-user planning session where participants can
    collaboratively create and modify roadmaps.
    """
    
    # Required fields
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    roadmap_id: str = ""
    title: str = "Untitled Planning Session"
    description: str = ""
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    # Session state
    status: SessionStatus = SessionStatus.ACTIVE
    participants: List[Participant] = field(default_factory=list)
    changes: List[Change] = field(default_factory=list)
    current_version: int = 1
    
    # Metadata
    updated_at: datetime = field(default_factory=datetime.now)
    last_sync_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_participant(self, participant: Participant):
        """Add a participant to the session."""
        if not any(p.user_id == participant.user_id for p in self.participants):
            self.participants.append(participant)
            self.updated_at = datetime.now()
    
    def remove_participant(self, user_id: str):
        """Remove a participant from the session."""
        self.participants = [p for p in self.participants if p.user_id != user_id]
        self.updated_at = datetime.now()
    
    def get_participant(self, user_id: str) -> Optional[Participant]:
        """Get participant by user ID."""
        return next((p for p in self.participants if p.user_id == user_id), None)
    
    def add_change(self, change: Change):
        """Add a change to the session."""
        self.changes.append(change)
        self.current_version += 1
        self.updated_at = datetime.now()
    
    def get_changes_since(self, version: int) -> List[Change]:
        """Get all changes since a specific version."""
        return [c for c in self.changes if c.version > version]
    
    def get_online_participants(self) -> List[Participant]:
        """Get list of currently online participants."""
        return [p for p in self.participants if p.is_online]
    
    def update_status(self, new_status: SessionStatus):
        """Update session status."""
        self.status = new_status
        self.updated_at = datetime.now()
    
    def is_active(self) -> bool:
        """Check if session is active."""
        return self.status == SessionStatus.ACTIVE
    
    def get_owner(self) -> Optional[Participant]:
        """Get session owner."""
        return next((p for p in self.participants if p.role == ParticipantRole.OWNER), None)
    
    def can_user_edit(self, user_id: str) -> bool:
        """Check if user can edit."""
        participant = self.get_participant(user_id)
        return participant.can_edit() if participant else False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'roadmap_id': self.roadmap_id,
            'title': self.title,
            'description': self.description,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'status': self.status.value,
            'participants': [
                {
                    'user_id': p.user_id,
                    'name': p.name,
                    'email': p.email,
                    'role': p.role.value,
                    'is_online': p.is_online,
                    'last_active': p.last_active.isoformat()
                }
                for p in self.participants
            ],
            'current_version': self.current_version,
            'updated_at': self.updated_at.isoformat(),
            'last_sync_at': self.last_sync_at.isoformat() if self.last_sync_at else None,
            'metadata': self.metadata
        }

