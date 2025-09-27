"""Execute Command use case."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ...domain.services.cli_command_service import CLICommandService
from ...domain.services.cli_session_service import CLISessionService
from ...domain.entities.cli_command import CLICommand, CommandType
from ...domain.entities.cli_session import CLISession
from ...domain.entities.command_result import CommandResult


logger = logging.getLogger(__name__)


class ExecuteCommandUseCase:
    """Use case for executing CLI commands."""

    def __init__(
        self,
        command_service: CLICommandService,
        session_service: CLISessionService
    ):
        """Initialize the use case."""
        self.command_service = command_service
        self.session_service = session_service

    async def execute(
        self,
        command_name: str,
        args: Optional[list] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        session: Optional[CLISession] = None,
        command_type: CommandType = CommandType.SINGLE_COMMAND,
        user_id: Optional[str] = None
    ) -> CommandResult:
        """Execute a CLI command."""
        # Generate command ID
        command_id = f"cmd_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(command_name) % 1000}"

        # Create command
        command = self.command_service.create_command(
            command_id=command_id,
            name=command_name,
            args=args or [],
            kwargs=kwargs or {},
            command_type=command_type,
            user_id=user_id,
            session_id=session.id if session else None
        )

        # Validate command
        if not self.command_service.validate_command(command):
            result = CommandResult(command_id=command_id)
            result.set_error(f"Invalid command: {', '.join(command.validation_errors)}")
            return result

        # Add to session if provided
        if session:
            self.session_service.add_command_to_session(session, command)
            self.session_service.update_session_activity(session)

        # Execute command
        result = self.command_service.execute_command(command)

        logger.info(f"Executed command '{command_name}' with result: {result.result_type.value}")

        return result

    async def execute_batch(
        self,
        commands: list,
        session: Optional[CLISession] = None,
        user_id: Optional[str] = None
    ) -> list:
        """Execute multiple commands in batch."""
        results = []

        for cmd_spec in commands:
            if isinstance(cmd_spec, dict):
                result = await self.execute(
                    command_name=cmd_spec.get('name', ''),
                    args=cmd_spec.get('args', []),
                    kwargs=cmd_spec.get('kwargs', {}),
                    session=session,
                    user_id=user_id,
                    command_type=CommandType.BATCH
                )
            elif isinstance(cmd_spec, str):
                result = await self.execute(
                    command_name=cmd_spec,
                    session=session,
                    user_id=user_id,
                    command_type=CommandType.BATCH
                )
            else:
                # Invalid command specification
                result = CommandResult(command_id=f"invalid_{len(results)}")
                result.set_error("Invalid command specification")

            results.append(result)

        logger.info(f"Executed batch of {len(commands)} commands")
        return results

    async def cancel_command(
        self,
        command: CLICommand,
        reason: str = "Cancelled by user"
    ) -> bool:
        """Cancel a running command."""
        try:
            self.command_service.cancel_command(command, reason)
            logger.info(f"Cancelled command {command.id}: {reason}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel command {command.id}: {str(e)}")
            return False

