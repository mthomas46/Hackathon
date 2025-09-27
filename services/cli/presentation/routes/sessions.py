"""Sessions API routes."""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from ...application.use_cases.create_session_use_case import CreateSessionUseCase
from ...application.use_cases.manage_session_use_case import ManageSessionUseCase


router = APIRouter(prefix="/sessions", tags=["Sessions"])


class CreateSessionRequest(BaseModel):
    """Request model for session creation."""
    user_id: Optional[str] = None
    interactive_mode: bool = False
    working_directory: Optional[str] = None
    environment: Optional[Dict[str, str]] = {}


@router.post("/", summary="Create a new CLI session")
async def create_session(
    request: CreateSessionRequest
) -> Dict[str, Any]:
    """
    Create a new CLI session.

    Sessions track command execution history and provide context for CLI operations.
    """
    try:
        # Simulate session creation
        session = {
            "id": f"session_{request.user_id or 'anonymous'}",
            "user_id": request.user_id,
            "status": "active",
            "interactive_mode": request.interactive_mode,
            "working_directory": request.working_directory or "/",
            "started_at": "2024-01-15T10:30:00Z",
            "command_count": 0
        }

        return session

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session creation failed: {str(e)}")


@router.post("/interactive", summary="Create an interactive CLI session")
async def create_interactive_session(
    user_id: Optional[str] = None,
    working_directory: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create an interactive CLI session.

    Interactive sessions are designed for multi-command workflows and user interaction.
    """
    try:
        # Simulate interactive session creation
        session = {
            "id": f"interactive_session_{user_id or 'anonymous'}",
            "user_id": user_id,
            "status": "active",
            "interactive_mode": True,
            "working_directory": working_directory or "/",
            "started_at": "2024-01-15T10:30:00Z",
            "command_count": 0
        }

        return session

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Interactive session creation failed: {str(e)}")


@router.delete("/{session_id}", summary="Terminate a CLI session")
async def terminate_session(session_id: str) -> Dict[str, Any]:
    """
    Terminate a CLI session.

    This will end the session and clean up associated resources.
    """
    try:
        # Simulate session termination
        return {
            "session_id": session_id,
            "terminated": True,
            "message": "Session terminated successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session termination failed: {str(e)}")


@router.get("/{session_id}", summary="Get session information")
async def get_session_info(session_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a CLI session.
    """
    try:
        # Simulate session info response
        return {
            "session_id": session_id,
            "user_id": "user123",
            "status": "active",
            "is_active": True,
            "started_at": "2024-01-15T10:30:00Z",
            "last_activity_at": "2024-01-15T10:45:00Z",
            "duration_seconds": 900.0,
            "working_directory": "/home/user",
            "interactive_mode": False,
            "command_count": 15,
            "successful_command_count": 14,
            "active_commands": 0
        }

    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")


@router.get("/{session_id}/history", summary="Get session command history")
async def get_session_history(
    session_id: str,
    limit: int = Query(50, description="Maximum number of commands to return"),
    format: str = Query("json", description="Response format (json or text)")
) -> Any:
    """
    Get the command execution history for a session.
    """
    try:
        if format == "text":
            # Return plain text history
            history = f"""Session {session_id} Command History
Started: 2024-01-15T10:30:00Z
Commands: 15

✓ health - completed (2.3s)
✓ list-prompts - completed (1.8s)
✓ get-prompt api --category general - completed (3.1s)
✗ invalid-command - failed (0.5s)
✓ health - completed (2.1s)
"""
            return history
        else:
            # Return JSON history
            commands = [
                {
                    "id": "cmd_001",
                    "name": "health",
                    "status": "completed",
                    "is_successful": True,
                    "execution_time_seconds": 2.3,
                    "executed_at": "2024-01-15T10:31:00Z"
                },
                {
                    "id": "cmd_002",
                    "name": "list-prompts",
                    "status": "completed",
                    "is_successful": True,
                    "execution_time_seconds": 1.8,
                    "executed_at": "2024-01-15T10:32:00Z"
                }
            ]

            return {
                "session_id": session_id,
                "exported_at": "2024-01-15T10:45:00Z",
                "command_count": len(commands),
                "commands": commands
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session history: {str(e)}")


@router.get("/inactive/cleanup", summary="Clean up inactive sessions")
async def cleanup_inactive_sessions(
    threshold_minutes: int = Query(30, description="Inactivity threshold in minutes")
) -> Dict[str, Any]:
    """
    Clean up sessions that have been inactive for longer than the threshold.

    This helps maintain system resources by removing stale sessions.
    """
    try:
        # Simulate cleanup response
        return {
            "inactive_sessions_found": 3,
            "sessions_terminated": 3,
            "threshold_minutes": threshold_minutes,
            "message": "Inactive sessions cleaned up successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@router.get("/statistics", summary="Get session statistics")
async def get_session_statistics() -> Dict[str, Any]:
    """
    Get statistics about CLI sessions.

    Provides insights into session usage patterns and system load.
    """
    try:
        # Simulate statistics response
        return {
            "total_sessions": 25,
            "active_sessions": 18,
            "inactive_sessions": 5,
            "terminated_sessions": 2,
            "average_session_duration": 1800.5,  # 30 minutes
            "total_commands_executed": 450,
            "average_commands_per_session": 18.0,
            "peak_concurrent_sessions": 8
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session statistics: {str(e)}")


@router.post("/{session_id}/activity", summary="Update session activity")
async def update_session_activity(session_id: str) -> Dict[str, Any]:
    """
    Update the last activity timestamp for a session.

    This prevents the session from being marked as inactive.
    """
    try:
        # Simulate activity update
        return {
            "session_id": session_id,
            "activity_updated": True,
            "last_activity_at": "2024-01-15T10:45:30Z",
            "message": "Session activity updated"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Activity update failed: {str(e)}")

