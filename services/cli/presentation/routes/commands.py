"""Commands API routes."""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from ...application.use_cases.execute_command_use_case import ExecuteCommandUseCase
from ...domain.entities.cli_command import CommandType
from ...domain.entities.command_result import CommandResult


router = APIRouter(prefix="/commands", tags=["Commands"])


class ExecuteCommandRequest(BaseModel):
    """Request model for command execution."""
    name: str
    args: Optional[List[str]] = []
    kwargs: Optional[Dict[str, Any]] = {}
    command_type: Optional[str] = "single_command"
    user_id: Optional[str] = None


class BatchExecuteRequest(BaseModel):
    """Request model for batch command execution."""
    commands: List[Dict[str, Any]]
    user_id: Optional[str] = None


@router.post("/execute", summary="Execute a CLI command")
async def execute_command(
    request: ExecuteCommandRequest,
    background_tasks: BackgroundTasks,
    use_case: ExecuteCommandUseCase = None  # Would be injected
) -> Dict[str, Any]:
    """
    Execute a CLI command.

    This endpoint allows execution of CLI commands through the REST API.
    Commands can be executed synchronously or asynchronously based on their nature.
    """
    try:
        # Map string command type to enum
        command_type_map = {
            "single_command": CommandType.SINGLE_COMMAND,
            "batch": CommandType.BATCH,
            "workflow": CommandType.WORKFLOW
        }
        cmd_type = command_type_map.get(request.command_type, CommandType.SINGLE_COMMAND)

        # Execute command (would use actual use case)
        # For now, simulate response
        result = {
            "command_id": f"cmd_{request.name}",
            "status": "completed",
            "result_type": "success",
            "message": f"Command '{request.name}' executed successfully",
            "data": {},
            "execution_duration_seconds": 0.5
        }

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Command execution failed: {str(e)}")


@router.post("/execute-batch", summary="Execute multiple commands in batch")
async def execute_batch_commands(
    request: BatchExecuteRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Execute multiple commands in batch.

    This endpoint allows execution of multiple CLI commands as a batch operation.
    Results are returned for each command in the batch.
    """
    try:
        results = []
        for i, cmd_spec in enumerate(request.commands):
            # Simulate batch execution
            result = {
                "command_id": f"batch_cmd_{i}",
                "name": cmd_spec.get("name", "unknown"),
                "status": "completed",
                "result_type": "success",
                "message": f"Batch command {i} executed successfully"
            }
            results.append(result)

        return {
            "batch_id": f"batch_{len(request.commands)}",
            "total_commands": len(request.commands),
            "results": results,
            "summary": {
                "successful": len(results),
                "failed": 0
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch execution failed: {str(e)}")


@router.post("/cancel/{command_id}", summary="Cancel a running command")
async def cancel_command(command_id: str) -> Dict[str, Any]:
    """
    Cancel a running command.

    This endpoint allows cancellation of commands that are currently executing.
    """
    try:
        # Simulate cancellation
        return {
            "command_id": command_id,
            "cancelled": True,
            "message": "Command cancelled successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Command cancellation failed: {str(e)}")


@router.get("/status/{command_id}", summary="Get command execution status")
async def get_command_status(command_id: str) -> Dict[str, Any]:
    """
    Get the status of a command execution.

    Returns detailed information about a command's execution state.
    """
    try:
        # Simulate status response
        return {
            "command_id": command_id,
            "name": "example_command",
            "status": "completed",
            "is_running": False,
            "is_completed": True,
            "is_successful": True,
            "started_at": "2024-01-15T10:30:00Z",
            "completed_at": "2024-01-15T10:30:05Z",
            "execution_time_seconds": 5.0,
            "exit_code": 0
        }

    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Command {command_id} not found")


@router.get("/long-running", summary="Get long-running commands")
async def get_long_running_commands(
    threshold_seconds: int = Query(300, description="Threshold in seconds for long-running commands")
) -> Dict[str, Any]:
    """
    Get commands that have been running longer than the specified threshold.

    Useful for monitoring and potentially cancelling long-running operations.
    """
    try:
        # Simulate response
        return {
            "threshold_seconds": threshold_seconds,
            "long_running_commands": [],
            "total_found": 0
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get long-running commands: {str(e)}")


@router.get("/statistics", summary="Get command execution statistics")
async def get_command_statistics() -> Dict[str, Any]:
    """
    Get statistics about command executions.

    Provides insights into command usage patterns and performance.
    """
    try:
        # Simulate statistics response
        return {
            "total_commands": 150,
            "successful_commands": 142,
            "failed_commands": 8,
            "running_commands": 0,
            "success_rate": 94.67,
            "average_execution_time": 2.3,
            "most_used_commands": [
                {"name": "health", "count": 45},
                {"name": "list-prompts", "count": 32},
                {"name": "get-prompt", "count": 28}
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get command statistics: {str(e)}")

