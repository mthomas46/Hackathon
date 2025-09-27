"""Domain entities for CLI service."""

from .cli_command import CLICommand
from .cli_session import CLISession
from .command_result import CommandResult

__all__ = [
    'CLICommand',
    'CLISession',
    'CommandResult'
]

