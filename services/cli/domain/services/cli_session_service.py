"""CLI Session domain service."""

import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from ..entities.cli_session import CLISession, SessionStatus
from ..entities.cli_command import CLICommand


logger = logging.getLogger(__name__)


class CLISessionService:
    """Domain service for CLI session operations."""

    def __init__(self):
        """Initialize the CLI session service."""
        pass

    def create_session(
        self,
        user_id: Optional[str] = None,
        interactive_mode: bool = False,
        working_directory: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None
    ) -> CLISession:
        """Create a new CLI session."""
        session_id = str(uuid.uuid4())

        session = CLISession(
            id=session_id,
            user_id=user_id,
            interactive_mode=interactive_mode,
            working_directory=working_directory or "/",
            environment=environment or {}
        )

        logger.info(f"Created new CLI session: {session_id} for user: {user_id}")
        return session

    def validate_session(self, session: CLISession) -> bool:
        """Validate a CLI session."""
        is_valid = session.is_valid

        if not is_valid:
            logger.warning(f"Session validation failed: {session.validation_errors}")

        return is_valid

    def update_session_activity(self, session: CLISession) -> None:
        """Update session last activity timestamp."""
        session.update_activity()
        logger.debug(f"Updated activity for session {session.id}")

    def add_command_to_session(self, session: CLISession, command: CLICommand) -> None:
        """Add a command to the session history."""
        session.add_command(command)
        logger.debug(f"Added command {command.id} to session {session.id}")

    def terminate_session(self, session: CLISession) -> None:
        """Terminate a CLI session."""
        if session.is_active:
            session.terminate()
            logger.info(f"Terminated session {session.id}")
        else:
            logger.warning(f"Cannot terminate session {session.id}: already terminated")

    def get_session_info(self, session: CLISession) -> Dict[str, Any]:
        """Get detailed information about a session."""
        return {
            'session_id': session.id,
            'user_id': session.user_id,
            'status': session.status.value,
            'is_active': session.is_active,
            'started_at': session.started_at.isoformat(),
            'last_activity_at': session.last_activity_at.isoformat(),
            'ended_at': session.ended_at.isoformat() if session.ended_at else None,
            'duration_seconds': session.get_session_duration(),
            'working_directory': session.working_directory,
            'interactive_mode': session.interactive_mode,
            'command_count': session.command_count,
            'successful_command_count': session.successful_command_count,
            'active_commands': len(session.get_active_commands())
        }

    def find_inactive_sessions(self, inactivity_threshold_minutes: int = 30) -> List[CLISession]:
        """Find sessions that have been inactive for longer than threshold."""
        # This would typically query a repository
        # For now, return empty list as we don't have persistence yet
        threshold = timedelta(minutes=inactivity_threshold_minutes)
        logger.info(f"Looking for sessions inactive for more than {inactivity_threshold_minutes} minutes")
        return []

    def cleanup_expired_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up sessions older than max age."""
        # This would typically clean up from repository
        # For now, just log
        logger.info(f"Cleaning up sessions older than {max_age_hours} hours")
        return 0

    def get_session_statistics(self, sessions: List[CLISession]) -> Dict[str, Any]:
        """Get statistics about sessions."""
        total_sessions = len(sessions)
        if total_sessions == 0:
            return {
                'total_sessions': 0,
                'active_sessions': 0,
                'inactive_sessions': 0,
                'terminated_sessions': 0,
                'average_session_duration': 0.0,
                'total_commands_executed': 0
            }

        active = len([s for s in sessions if s.status == SessionStatus.ACTIVE])
        inactive = len([s for s in sessions if s.status == SessionStatus.INACTIVE])
        terminated = len([s for s in sessions if s.status == SessionStatus.TERMINATED])

        durations = [s.get_session_duration() for s in sessions if s.get_session_duration() is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0.0

        total_commands = sum(s.command_count for s in sessions)

        return {
            'total_sessions': total_sessions,
            'active_sessions': active,
            'inactive_sessions': inactive,
            'terminated_sessions': terminated,
            'average_session_duration': avg_duration,
            'total_commands_executed': total_commands
        }

    def export_session_history(self, session: CLISession, format: str = "json") -> str:
        """Export session command history."""
        if format == "json":
            commands_data = [cmd.to_dict() for cmd in session.command_history]
            return json.dumps({
                'session_id': session.id,
                'exported_at': datetime.now().isoformat(),
                'command_count': len(commands_data),
                'commands': commands_data
            }, indent=2)
        else:
            # Plain text format
            lines = [f"Session {session.id} Command History"]
            lines.append(f"Started: {session.started_at.isoformat()}")
            lines.append(f"Commands: {len(session.command_history)}")
            lines.append("")

            for cmd in session.command_history:
                status = "✓" if cmd.is_successful else "✗"
                duration = f" ({cmd.execution_time_seconds:.2f}s)" if cmd.execution_time_seconds else ""
                lines.append(f"{status} {cmd.name} - {cmd.status.value}{duration}")

            return "\n".join(lines)
