"""
Collaboration Manager Service
==============================

Domain service for managing collaborative planning sessions.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict

from .entities import (
    PlanningSession,
    Participant,
    Change,
    ConflictResolution,
    SessionStatus,
    ParticipantRole,
    ChangeType
)


class CollaborationManager:
    """
    Manages collaborative planning sessions.
    
    Features:
    - Multi-user planning sessions
    - Real-time change synchronization
    - Conflict detection and resolution
    - Participant management
    - Change tracking and versioning
    """
    
    def __init__(self):
        """Initialize collaboration manager."""
        # In-memory storage (would be replaced with Redis/database in production)
        self._sessions: Dict[str, PlanningSession] = {}
        self._user_sessions: Dict[str, List[str]] = defaultdict(list)
    
    async def create_planning_session(
        self,
        roadmap_id: str,
        title: str,
        description: str,
        owner: Participant
    ) -> PlanningSession:
        """
        Create a new collaborative planning session.
        
        Args:
            roadmap_id: ID of the roadmap being planned
            title: Session title
            description: Session description
            owner: Session owner/creator
            
        Returns:
            Created planning session
        """
        session = PlanningSession(
            roadmap_id=roadmap_id,
            title=title,
            description=description,
            created_by=owner.user_id,
            status=SessionStatus.ACTIVE
        )
        
        # Add owner as first participant
        owner.role = ParticipantRole.OWNER
        session.add_participant(owner)
        
        # Store session
        self._sessions[session.id] = session
        self._user_sessions[owner.user_id].append(session.id)
        
        return session
    
    async def add_participant(
        self,
        session_id: str,
        participant: Participant
    ) -> bool:
        """
        Add a participant to a planning session.
        
        Args:
            session_id: Session ID
            participant: Participant to add
            
        Returns:
            True if added successfully
        """
        session = self._sessions.get(session_id)
        if not session or not session.is_active():
            return False
        
        session.add_participant(participant)
        self._user_sessions[participant.user_id].append(session_id)
        
        # Record join event
        change = Change(
            change_type=ChangeType.COMMENT_ADDED,
            user_id="system",
            user_name="System",
            description=f"{participant.name} joined the session",
            data={'participant_id': participant.user_id}
        )
        session.add_change(change)
        
        return True
    
    async def remove_participant(
        self,
        session_id: str,
        user_id: str
    ) -> bool:
        """Remove a participant from a session."""
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        participant = session.get_participant(user_id)
        if not participant:
            return False
        
        # Don't allow removing the owner
        if participant.role == ParticipantRole.OWNER:
            return False
        
        session.remove_participant(user_id)
        self._user_sessions[user_id].remove(session_id)
        
        # Record leave event
        change = Change(
            change_type=ChangeType.COMMENT_ADDED,
            user_id="system",
            user_name="System",
            description=f"{participant.name} left the session",
            data={'participant_id': user_id}
        )
        session.add_change(change)
        
        return True
    
    async def apply_change(
        self,
        session_id: str,
        change: Change
    ) -> Dict[str, Any]:
        """
        Apply a change to a planning session.
        
        Args:
            session_id: Session ID
            change: Change to apply
            
        Returns:
            Result dictionary with success status and conflicts
        """
        session = self._sessions.get(session_id)
        if not session or not session.is_active():
            return {
                'success': False,
                'error': 'Session not found or not active'
            }
        
        # Check if user can edit
        if not session.can_user_edit(change.user_id):
            return {
                'success': False,
                'error': 'User does not have edit permissions'
            }
        
        # Update change version
        change.version = session.current_version + 1
        
        # Add change to session
        session.add_change(change)
        
        return {
            'success': True,
            'version': change.version,
            'change_id': change.id
        }
    
    async def sync_changes(
        self,
        session_id: str,
        client_version: int
    ) -> Dict[str, Any]:
        """
        Synchronize changes since a specific version.
        
        Args:
            session_id: Session ID
            client_version: Client's current version
            
        Returns:
            Dictionary with new changes and current version
        """
        session = self._sessions.get(session_id)
        if not session:
            return {
                'success': False,
                'error': 'Session not found'
            }
        
        # Get changes since client version
        new_changes = session.get_changes_since(client_version)
        
        # Update sync timestamp
        session.last_sync_at = datetime.now()
        
        return {
            'success': True,
            'current_version': session.current_version,
            'changes': [c.to_dict() for c in new_changes],
            'online_participants': [
                {
                    'user_id': p.user_id,
                    'name': p.name,
                    'role': p.role.value
                }
                for p in session.get_online_participants()
            ]
        }
    
    async def detect_conflicts(
        self,
        session_id: str,
        proposed_change: Change,
        since_version: int
    ) -> List[Dict[str, Any]]:
        """
        Detect conflicts between a proposed change and recent changes.
        
        Args:
            session_id: Session ID
            proposed_change: Change being proposed
            since_version: Version to check conflicts from
            
        Returns:
            List of conflicts found
        """
        session = self._sessions.get(session_id)
        if not session:
            return []
        
        conflicts = []
        recent_changes = session.get_changes_since(since_version)
        
        # Check for conflicts based on change type
        for change in recent_changes:
            if self._changes_conflict(proposed_change, change):
                conflicts.append({
                    'conflict_type': 'concurrent_modification',
                    'conflicting_change': change.to_dict(),
                    'affected_entity': proposed_change.data.get('entity_id'),
                    'description': f"Concurrent modification by {change.user_name}"
                })
        
        return conflicts
    
    def _changes_conflict(self, change1: Change, change2: Change) -> bool:
        """Check if two changes conflict."""
        # Same entity modified
        if change1.data.get('entity_id') == change2.data.get('entity_id'):
            # Same field modified
            if change1.data.get('field') == change2.data.get('field'):
                return True
        
        # Dependency conflicts
        if change1.change_type == ChangeType.DEPENDENCY_REMOVED:
            if change2.change_type == ChangeType.DEPENDENCY_ADDED:
                if change1.data.get('dependency_id') == change2.data.get('dependency_id'):
                    return True
        
        return False
    
    async def resolve_conflict(
        self,
        session_id: str,
        resolution: ConflictResolution
    ) -> bool:
        """
        Resolve a conflict in a planning session.
        
        Args:
            session_id: Session ID
            resolution: Conflict resolution details
            
        Returns:
            True if resolved successfully
        """
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        # Record resolution
        change = Change(
            change_type=ChangeType.COMMENT_ADDED,
            user_id=resolution.resolved_by,
            user_name="User",
            description=f"Resolved conflict: {resolution.conflict_id}",
            data={
                'resolution_type': resolution.resolution_type,
                'resolution_data': resolution.resolution_data
            }
        )
        session.add_change(change)
        
        return True
    
    async def update_participant_status(
        self,
        session_id: str,
        user_id: str,
        is_online: bool
    ) -> bool:
        """Update participant online status."""
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        participant = session.get_participant(user_id)
        if not participant:
            return False
        
        participant.is_online = is_online
        participant.update_activity()
        
        return True
    
    async def get_session(self, session_id: str) -> Optional[PlanningSession]:
        """Get a planning session by ID."""
        return self._sessions.get(session_id)
    
    async def get_user_sessions(self, user_id: str) -> List[PlanningSession]:
        """Get all sessions for a user."""
        session_ids = self._user_sessions.get(user_id, [])
        return [self._sessions[sid] for sid in session_ids if sid in self._sessions]
    
    async def complete_session(
        self,
        session_id: str,
        completed_by: str
    ) -> bool:
        """Mark a session as completed."""
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        # Only owner can complete
        owner = session.get_owner()
        if not owner or owner.user_id != completed_by:
            return False
        
        session.update_status(SessionStatus.COMPLETED)
        
        # Record completion
        change = Change(
            change_type=ChangeType.COMMENT_ADDED,
            user_id=completed_by,
            user_name=owner.name,
            description="Session completed",
            data={'final_version': session.current_version}
        )
        session.add_change(change)
        
        return True
    
    async def get_session_statistics(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """Get statistics for a planning session."""
        session = self._sessions.get(session_id)
        if not session:
            return {}
        
        # Calculate statistics
        change_types = defaultdict(int)
        for change in session.changes:
            change_types[change.change_type.value] += 1
        
        participant_contributions = defaultdict(int)
        for change in session.changes:
            if change.user_id != "system":
                participant_contributions[change.user_id] += 1
        
        duration = (datetime.now() - session.created_at).total_seconds() / 3600
        
        return {
            'session_id': session.id,
            'duration_hours': round(duration, 2),
            'total_changes': len(session.changes),
            'participant_count': len(session.participants),
            'online_count': len(session.get_online_participants()),
            'current_version': session.current_version,
            'change_types': dict(change_types),
            'participant_contributions': dict(participant_contributions),
            'status': session.status.value
        }

