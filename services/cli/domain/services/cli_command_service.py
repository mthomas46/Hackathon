"""CLI Command domain service."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..entities.cli_command import CLICommand, CommandStatus, CommandType
from ..entities.command_result import CommandResult, ResultType


logger = logging.getLogger(__name__)


class CLICommandService:
    """Domain service for CLI command operations."""

    def __init__(self):
        """Initialize the CLI command service."""
        pass

    def create_command(
        self,
        command_id: str,
        name: str,
        args: Optional[List[str]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        command_type: CommandType = CommandType.SINGLE_COMMAND,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> CLICommand:
        """Create a new CLI command."""
        command = CLICommand(
            id=command_id,
            name=name,
            args=args or [],
            kwargs=kwargs or {},
            command_type=command_type,
            user_id=user_id,
            session_id=session_id
        )

        if command.is_valid:
            logger.info(f"Created valid command: {command.name} ({command.id})")
        else:
            logger.warning(f"Created invalid command: {command.name} - {command.validation_errors}")

        return command

    def validate_command(self, command: CLICommand) -> bool:
        """Validate a CLI command."""
        is_valid = command.is_valid

        if not is_valid:
            logger.warning(f"Command validation failed: {command.validation_errors}")

        return is_valid

    def execute_command(self, command: CLICommand) -> CommandResult:
        """Execute a CLI command and return result."""
        result = CommandResult(command_id=command.id)

        try:
            # Mark command as started
            command.start_execution()

            # Here would be the actual command execution logic
            # For now, we'll simulate execution
            execution_start = datetime.now()

            # Simulate command execution (replace with actual logic)
            success = self._execute_command_logic(command)

            execution_duration = (datetime.now() - execution_start).total_seconds()

            if success:
                command.complete_execution(exit_code=0, stdout="Command executed successfully")
                result.set_success(
                    data={"execution_duration": execution_duration},
                    message="Command completed successfully"
                )
            else:
                command.fail_execution("Command execution failed")
                result.set_error("Command execution failed")

            result.execution_duration_seconds = execution_duration

        except Exception as e:
            logger.error(f"Error executing command {command.id}: {str(e)}")
            command.fail_execution(str(e))
            result.set_error(f"Command execution error: {str(e)}")

        return result

    def _execute_command_logic(self, command: CLICommand) -> bool:
        """Execute the actual command logic (placeholder)."""
        # This would contain the actual command execution logic
        # For now, return success for demonstration
        logger.info(f"Executing command: {command.name} with args: {command.args}")
        return True

    def cancel_command(self, command: CLICommand, reason: str = "Cancelled by user") -> None:
        """Cancel a running command."""
        if command.is_running:
            command.cancel_execution()
            logger.info(f"Cancelled command {command.id}: {reason}")
        else:
            logger.warning(f"Cannot cancel command {command.id}: not running")

    def get_command_status(self, command: CLICommand) -> Dict[str, Any]:
        """Get detailed status of a command."""
        return {
            'command_id': command.id,
            'name': command.name,
            'status': command.status.value,
            'is_running': command.is_running,
            'is_completed': command.is_completed,
            'is_successful': command.is_successful,
            'started_at': command.started_at.isoformat() if command.started_at else None,
            'completed_at': command.completed_at.isoformat() if command.completed_at else None,
            'execution_time_seconds': command.execution_time_seconds,
            'exit_code': command.exit_code,
            'error_message': command.error_message
        }

    def find_long_running_commands(self, threshold_seconds: int = 300) -> List[CLICommand]:
        """Find commands that have been running longer than threshold."""
        # This would typically query a repository
        # For now, return empty list as we don't have persistence yet
        logger.info(f"Looking for commands running longer than {threshold_seconds} seconds")
        return []

    def get_command_statistics(self, commands: List[CLICommand]) -> Dict[str, Any]:
        """Get statistics about commands."""
        total_commands = len(commands)
        if total_commands == 0:
            return {
                'total_commands': 0,
                'successful_commands': 0,
                'failed_commands': 0,
                'running_commands': 0,
                'success_rate': 0.0,
                'average_execution_time': 0.0
            }

        successful = len([c for c in commands if c.is_successful])
        failed = len([c for c in commands if c.status == CommandStatus.FAILED])
        running = len([c for c in commands if c.is_running])

        execution_times = [c.execution_time_seconds for c in commands if c.execution_time_seconds is not None]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0.0

        return {
            'total_commands': total_commands,
            'successful_commands': successful,
            'failed_commands': failed,
            'running_commands': running,
            'success_rate': (successful / total_commands) * 100,
            'average_execution_time': avg_execution_time
        }

