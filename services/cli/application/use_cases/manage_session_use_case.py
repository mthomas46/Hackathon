"""Manage Session use case."""

import logging
from typing import Dict, Any, List

from ...domain.services.cli_session_service import CLISessionService
from ...domain.entities.cli_session import CLISession, SessionStatus


logger = logging.getLogger(__name__)


class ManageSessionUseCase:
    """Use case for managing CLI sessions."""

    def __init__(self, session_service: CLISessionService):
        """Initialize the use case."""
        self.session_service = session_service

    async def terminate_session(self, session: CLISession) -> bool:
        """Terminate a CLI session."""
        try:
            self.session_service.terminate_session(session)
            logger.info(f"Terminated session {session.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to terminate session {session.id}: {str(e)}")
            return False

    async def get_session_info(self, session: CLISession) -> Dict[str, Any]:
        """Get detailed information about a session."""
        return self.session_service.get_session_info(session)

    async def update_session_activity(self, session: CLISession) -> None:
        """Update session activity timestamp."""
        self.session_service.update_session_activity(session)

    async def export_session_history(
        self,
        session: CLISession,
        format: str = "json"
    ) -> str:
        """Export session command history."""
        return self.session_service.export_session_history(session, format)

    async def cleanup_inactive_sessions(
        self,
        sessions: List[CLISession],
        inactivity_threshold_minutes: int = 30
    ) -> Dict[str, Any]:
        """Clean up inactive sessions."""
        inactive_sessions = self.session_service.find_inactive_sessions(inactivity_threshold_minutes)
        terminated_count = 0

        for session in inactive_sessions:
            if await self.terminate_session(session):
                terminated_count += 1

        return {
            'inactive_sessions_found': len(inactive_sessions),
            'sessions_terminated': terminated_count,
            'threshold_minutes': inactivity_threshold_minutes
        }

    async def cleanup_expired_sessions(
        self,
        max_age_hours: int = 24
    ) -> Dict[str, Any]:
        """Clean up expired sessions."""
        cleaned_count = self.session_service.cleanup_expired_sessions(max_age_hours)

        return {
            'sessions_cleaned': cleaned_count,
            'max_age_hours': max_age_hours
        }

    async def get_session_statistics(
        self,
        sessions: List[CLISession]
    ) -> Dict[str, Any]:
        """Get statistics about sessions."""
        return self.session_service.get_session_statistics(sessions)

