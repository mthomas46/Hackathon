"""Execution Status Value Object."""

from enum import Enum


class ExecutionStatus(Enum):
    """Status of an MCP orchestration execution."""
    
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
