"""
Collaborative Planning API Routes
==================================

REST API endpoints for managing collaborative planning sessions.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..domain.collaboration import (
    CollaborationManager,
    PlanningSession,
    Participant,
    Change,
    ParticipantRole,
    ChangeType,
    SessionStatus,
    ConflictResolution
)

router = APIRouter()

# Initialize collaboration manager (would be injected via dependency injection in production)
collaboration_manager = CollaborationManager()


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateSessionRequest(BaseModel):
    """Request to create a planning session."""
    roadmap_id: str
    title: str
    description: str = ""
    owner_id: str
    owner_name: str
    owner_email: str


class AddParticipantRequest(BaseModel):
    """Request to add a participant."""
    user_id: str
    name: str
    email: str
    role: str = Field(default="editor", description="editor, reviewer, or viewer")


class ApplyChangeRequest(BaseModel):
    """Request to apply a change."""
    change_type: str
    user_id: str
    user_name: str
    description: str
    data: Dict[str, Any] = Field(default_factory=dict)


class SyncRequest(BaseModel):
    """Request to sync changes."""
    client_version: int


class UpdateStatusRequest(BaseModel):
    """Request to update participant status."""
    is_online: bool


class SessionResponse(BaseModel):
    """Session response model."""
    id: str
    roadmap_id: str
    title: str
    description: str
    status: str
    current_version: int
    participants: List[Dict[str, Any]]
    created_at: str
    updated_at: str


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(request: CreateSessionRequest):
    """
    Create a new collaborative planning session.
    
    Args:
        request: Session creation request
        
    Returns:
        Created session details
    """
    owner = Participant(
        user_id=request.owner_id,
        name=request.owner_name,
        email=request.owner_email,
        role=ParticipantRole.OWNER
    )
    
    session = await collaboration_manager.create_planning_session(
        roadmap_id=request.roadmap_id,
        title=request.title,
        description=request.description,
        owner=owner
    )
    
    return SessionResponse(**session.to_dict())


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get a planning session by ID."""
    session = await collaboration_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse(**session.to_dict())


@router.get("/users/{user_id}/sessions", response_model=List[SessionResponse])
async def get_user_sessions(user_id: str):
    """Get all sessions for a user."""
    sessions = await collaboration_manager.get_user_sessions(user_id)
    return [SessionResponse(**s.to_dict()) for s in sessions]


@router.post("/sessions/{session_id}/participants", status_code=status.HTTP_200_OK)
async def add_participant(session_id: str, request: AddParticipantRequest):
    """Add a participant to a session."""
    # Parse role
    role_map = {
        "owner": ParticipantRole.OWNER,
        "editor": ParticipantRole.EDITOR,
        "reviewer": ParticipantRole.REVIEWER,
        "viewer": ParticipantRole.VIEWER
    }
    role = role_map.get(request.role.lower(), ParticipantRole.VIEWER)
    
    participant = Participant(
        user_id=request.user_id,
        name=request.name,
        email=request.email,
        role=role
    )
    
    success = await collaboration_manager.add_participant(session_id, participant)
    if not success:
        raise HTTPException(status_code=400, detail="Could not add participant")
    
    return {"success": True, "message": f"Participant {request.name} added"}


@router.delete("/sessions/{session_id}/participants/{user_id}", status_code=status.HTTP_200_OK)
async def remove_participant(session_id: str, user_id: str):
    """Remove a participant from a session."""
    success = await collaboration_manager.remove_participant(session_id, user_id)
    if not success:
        raise HTTPException(status_code=400, detail="Could not remove participant")
    
    return {"success": True, "message": "Participant removed"}


@router.post("/sessions/{session_id}/changes", status_code=status.HTTP_200_OK)
async def apply_change(session_id: str, request: ApplyChangeRequest):
    """Apply a change to a planning session."""
    # Parse change type
    change_type_map = {
        "feature_added": ChangeType.FEATURE_ADDED,
        "feature_updated": ChangeType.FEATURE_UPDATED,
        "feature_removed": ChangeType.FEATURE_REMOVED,
        "dependency_added": ChangeType.DEPENDENCY_ADDED,
        "dependency_removed": ChangeType.DEPENDENCY_REMOVED,
        "milestone_updated": ChangeType.MILESTONE_UPDATED,
        "timeline_adjusted": ChangeType.TIMELINE_ADJUSTED,
        "comment_added": ChangeType.COMMENT_ADDED
    }
    change_type = change_type_map.get(request.change_type.lower(), ChangeType.FEATURE_UPDATED)
    
    change = Change(
        change_type=change_type,
        user_id=request.user_id,
        user_name=request.user_name,
        description=request.description,
        data=request.data
    )
    
    result = await collaboration_manager.apply_change(session_id, change)
    if not result['success']:
        raise HTTPException(status_code=400, detail=result.get('error', 'Could not apply change'))
    
    return result


@router.post("/sessions/{session_id}/sync", status_code=status.HTTP_200_OK)
async def sync_changes(session_id: str, request: SyncRequest):
    """Synchronize changes since a specific version."""
    result = await collaboration_manager.sync_changes(session_id, request.client_version)
    if not result['success']:
        raise HTTPException(status_code=404, detail=result.get('error', 'Session not found'))
    
    return result


@router.post("/sessions/{session_id}/participants/{user_id}/status", status_code=status.HTTP_200_OK)
async def update_participant_status(
    session_id: str,
    user_id: str,
    request: UpdateStatusRequest
):
    """Update participant online status."""
    success = await collaboration_manager.update_participant_status(
        session_id,
        user_id,
        request.is_online
    )
    if not success:
        raise HTTPException(status_code=404, detail="Session or participant not found")
    
    return {"success": True, "is_online": request.is_online}


@router.post("/sessions/{session_id}/complete", status_code=status.HTTP_200_OK)
async def complete_session(session_id: str, completed_by: str):
    """Mark a session as completed."""
    success = await collaboration_manager.complete_session(session_id, completed_by)
    if not success:
        raise HTTPException(status_code=400, detail="Could not complete session")
    
    return {"success": True, "message": "Session completed"}


@router.get("/sessions/{session_id}/statistics", status_code=status.HTTP_200_OK)
async def get_session_statistics(session_id: str):
    """Get session statistics."""
    stats = await collaboration_manager.get_session_statistics(session_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return stats


@router.get("/sessions/{session_id}/conflicts", status_code=status.HTTP_200_OK)
async def detect_conflicts(
    session_id: str,
    since_version: int,
    change_data: Dict[str, Any]
):
    """Detect conflicts for a proposed change."""
    # Create proposed change from request data
    proposed_change = Change(
        change_type=ChangeType.FEATURE_UPDATED,
        user_id=change_data.get('user_id', 'unknown'),
        user_name=change_data.get('user_name', 'Unknown'),
        description=change_data.get('description', ''),
        data=change_data.get('data', {})
    )
    
    conflicts = await collaboration_manager.detect_conflicts(
        session_id,
        proposed_change,
        since_version
    )
    
    return {
        "has_conflicts": len(conflicts) > 0,
        "conflicts": conflicts
    }

