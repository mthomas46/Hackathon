"""Create Session use case."""

import logging
from typing import Dict, Any, Optional

from ...domain.services.cli_session_service import CLISessionService
from ...domain.entities.cli_session import CLISession


logger = logging.getLogger(__name__)


class CreateSessionUseCase:
    """Use case for creating CLI sessions."""

    def __init__(self, session_service: CLISessionService):
        """Initialize the use case."""
        self.session_service = session_service

    async def execute(
        self,
        user_id: Optional[str] = None,
        interactive_mode: bool = False,
        working_directory: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None
    ) -> CLISession:
        """Create a new CLI session."""
        session = self.session_service.create_session(
            user_id=user_id,
            interactive_mode=interactive_mode,
            working_directory=working_directory,
            environment=environment or {}
        )

        # Validate session
        if not self.session_service.validate_session(session):
            logger.warning(f"Created invalid session: {session.validation_errors}")
        else:
            logger.info(f"Created valid session {session.id} for user {user_id}")

        return session

    async def execute_interactive(
        self,
        user_id: Optional[str] = None,
        working_directory: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None
    ) -> CLISession:
        """Create an interactive CLI session."""
        return await self.execute(
            user_id=user_id,
            interactive_mode=True,
            working_directory=working_directory,
            environment=environment
        )

    async def execute_batch(
        self,
        session_specs: list,
        default_user_id: Optional[str] = None
    ) -> list:
        """Create multiple sessions in batch."""
        sessions = []

        for spec in session_specs:
            if isinstance(spec, dict):
                session = await self.execute(
                    user_id=spec.get('user_id', default_user_id),
                    interactive_mode=spec.get('interactive_mode', False),
                    working_directory=spec.get('working_directory'),
                    environment=spec.get('environment', {})
                )
            else:
                # Simple user ID specification
                session = await self.execute(user_id=spec or default_user_id)

            sessions.append(session)

        logger.info(f"Created batch of {len(sessions)} sessions")
        return sessions

