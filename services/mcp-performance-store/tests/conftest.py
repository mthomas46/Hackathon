"""Pytest configuration and fixtures for MCP Performance Store tests."""

import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator
import uuid

from services.mcp_performance_store.domain.entities.orchestration_execution import (
    OrchestrationExecution,
)
from services.mcp_performance_store.domain.entities.pattern_performance import (
    PatternPerformance,
)
from services.mcp_performance_store.domain.value_objects.execution_status import (
    ExecutionStatus,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_orchestration_execution() -> OrchestrationExecution:
    """Create a sample orchestration execution for testing."""
    return OrchestrationExecution(
        execution_id=str(uuid.uuid4()),
        orchestration_id=str(uuid.uuid4()),
        mcp_id="mcp-test-001",
        status=ExecutionStatus.SUCCESS,
        started_at=datetime.now() - timedelta(seconds=5),
        completed_at=datetime.now(),
        duration_ms=5000,
        input_prompt="Test prompt for orchestration",
        output_response="Test response from orchestration",
        metadata={"test": True, "environment": "test"},
    )


@pytest.fixture
def sample_pattern_performance() -> PatternPerformance:
    """Create a sample pattern performance for testing."""
    return PatternPerformance(
        performance_id=str(uuid.uuid4()),
        execution_id=str(uuid.uuid4()),
        pattern_name="ChainOfThought",
        started_at=datetime.now() - timedelta(seconds=2),
        completed_at=datetime.now(),
        duration_ms=2000,
        status=ExecutionStatus.SUCCESS,
        input_tokens=100,
        output_tokens=150,
        error_message=None,
        metadata={"model": "gpt-4", "temperature": 0.7},
    )


@pytest.fixture
def multiple_executions() -> list[OrchestrationExecution]:
    """Create multiple orchestration executions for testing."""
    executions = []
    base_time = datetime.now() - timedelta(hours=1)
    
    for i in range(10):
        status = ExecutionStatus.SUCCESS if i % 3 != 0 else ExecutionStatus.FAILED
        execution = OrchestrationExecution(
            execution_id=str(uuid.uuid4()),
            orchestration_id=f"orch-{i:03d}",
            mcp_id=f"mcp-{i % 3}",
            status=status,
            started_at=base_time + timedelta(minutes=i * 5),
            completed_at=base_time + timedelta(minutes=i * 5, seconds=10),
            duration_ms=10000 + (i * 100),
            input_prompt=f"Test prompt {i}",
            output_response=f"Test response {i}",
            metadata={"index": i},
        )
        executions.append(execution)
    
    return executions


@pytest.fixture
def multiple_pattern_performances() -> list[PatternPerformance]:
    """Create multiple pattern performances for testing."""
    patterns = ["RAG", "ChainOfThought", "MultiAgent", "Summarizer"]
    performances = []
    base_time = datetime.now() - timedelta(hours=1)
    
    for i in range(20):
        pattern_name = patterns[i % len(patterns)]
        status = ExecutionStatus.SUCCESS if i % 4 != 0 else ExecutionStatus.FAILED
        
        performance = PatternPerformance(
            performance_id=str(uuid.uuid4()),
            execution_id=str(uuid.uuid4()),
            pattern_name=pattern_name,
            started_at=base_time + timedelta(minutes=i * 2),
            completed_at=base_time + timedelta(minutes=i * 2, seconds=5),
            duration_ms=5000 + (i * 50),
            status=status,
            input_tokens=50 + (i * 10),
            output_tokens=75 + (i * 15),
            error_message="Test error" if status == ExecutionStatus.FAILED else None,
            metadata={"iteration": i},
        )
        performances.append(performance)
    
    return performances
