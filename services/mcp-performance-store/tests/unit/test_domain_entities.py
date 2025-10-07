"""Unit tests for domain entities."""

import pytest
from datetime import datetime, timedelta
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


# ============================================================================
# OrchestrationExecution Tests
# ============================================================================


def test_orchestration_execution_creation(sample_orchestration_execution):
    """Test creating an orchestration execution."""
    exec = sample_orchestration_execution
    
    assert exec.execution_id is not None
    assert exec.orchestration_id is not None
    assert exec.mcp_id == "mcp-test-001"
    assert exec.status == ExecutionStatus.SUCCESS
    assert exec.started_at is not None
    assert exec.completed_at is not None
    assert exec.duration_ms == 5000
    assert exec.input_prompt == "Test prompt for orchestration"
    assert exec.output_response == "Test response from orchestration"
    assert exec.metadata["test"] is True


def test_orchestration_execution_validation():
    """Test orchestration execution validation."""
    # Test missing required fields
    with pytest.raises(TypeError):
        OrchestrationExecution()
    
    # Test invalid duration
    with pytest.raises(ValueError, match="Duration must be positive"):
        OrchestrationExecution(
            execution_id=str(uuid.uuid4()),
            orchestration_id=str(uuid.uuid4()),
            mcp_id="test",
            status=ExecutionStatus.SUCCESS,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            duration_ms=-100,
        )


def test_orchestration_execution_status_transitions():
    """Test status transitions."""
    exec = OrchestrationExecution(
        execution_id=str(uuid.uuid4()),
        orchestration_id=str(uuid.uuid4()),
        mcp_id="test",
        status=ExecutionStatus.RUNNING,
        started_at=datetime.now(),
    )
    
    assert exec.status == ExecutionStatus.RUNNING
    assert exec.completed_at is None
    
    # Complete the execution
    exec.complete(ExecutionStatus.SUCCESS, duration_ms=1000)
    assert exec.status == ExecutionStatus.SUCCESS
    assert exec.completed_at is not None
    assert exec.duration_ms == 1000


def test_orchestration_execution_with_error():
    """Test execution with error."""
    exec = OrchestrationExecution(
        execution_id=str(uuid.uuid4()),
        orchestration_id=str(uuid.uuid4()),
        mcp_id="test",
        status=ExecutionStatus.FAILED,
        started_at=datetime.now(),
        completed_at=datetime.now(),
        duration_ms=500,
        error_message="Test error occurred",
    )
    
    assert exec.status == ExecutionStatus.FAILED
    assert exec.error_message == "Test error occurred"


# ============================================================================
# PatternPerformance Tests
# ============================================================================


def test_pattern_performance_creation(sample_pattern_performance):
    """Test creating a pattern performance."""
    perf = sample_pattern_performance
    
    assert perf.performance_id is not None
    assert perf.execution_id is not None
    assert perf.pattern_name == "ChainOfThought"
    assert perf.started_at is not None
    assert perf.completed_at is not None
    assert perf.duration_ms == 2000
    assert perf.status == ExecutionStatus.SUCCESS
    assert perf.input_tokens == 100
    assert perf.output_tokens == 150
    assert perf.error_message is None


def test_pattern_performance_validation():
    """Test pattern performance validation."""
    # Test missing required fields
    with pytest.raises(TypeError):
        PatternPerformance()
    
    # Test invalid pattern name
    with pytest.raises(ValueError, match="Pattern name cannot be empty"):
        PatternPerformance(
            performance_id=str(uuid.uuid4()),
            execution_id=str(uuid.uuid4()),
            pattern_name="",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            duration_ms=1000,
            status=ExecutionStatus.SUCCESS,
        )
    
    # Test invalid tokens
    with pytest.raises(ValueError, match="Token counts must be non-negative"):
        PatternPerformance(
            performance_id=str(uuid.uuid4()),
            execution_id=str(uuid.uuid4()),
            pattern_name="TestPattern",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            duration_ms=1000,
            status=ExecutionStatus.SUCCESS,
            input_tokens=-10,
        )


def test_pattern_performance_token_calculation(sample_pattern_performance):
    """Test token calculation."""
    perf = sample_pattern_performance
    
    assert perf.total_tokens == 250  # 100 + 150
    assert perf.input_tokens == 100
    assert perf.output_tokens == 150


def test_pattern_performance_with_error():
    """Test pattern performance with error."""
    perf = PatternPerformance(
        performance_id=str(uuid.uuid4()),
        execution_id=str(uuid.uuid4()),
        pattern_name="FailedPattern",
        started_at=datetime.now(),
        completed_at=datetime.now(),
        duration_ms=500,
        status=ExecutionStatus.FAILED,
        error_message="Pattern execution failed",
    )
    
    assert perf.status == ExecutionStatus.FAILED
    assert perf.error_message == "Pattern execution failed"


def test_pattern_performance_metrics():
    """Test performance metrics calculation."""
    perf = PatternPerformance(
        performance_id=str(uuid.uuid4()),
        execution_id=str(uuid.uuid4()),
        pattern_name="MetricsPattern",
        started_at=datetime.now(),
        completed_at=datetime.now(),
        duration_ms=3000,
        status=ExecutionStatus.SUCCESS,
        input_tokens=200,
        output_tokens=300,
    )
    
    # Tokens per second
    tokens_per_second = (perf.input_tokens + perf.output_tokens) / (perf.duration_ms / 1000)
    assert tokens_per_second == pytest.approx(166.67, rel=0.01)


# ============================================================================
# ExecutionStatus Tests
# ============================================================================


def test_execution_status_enum():
    """Test execution status enum values."""
    assert ExecutionStatus.PENDING.value == "pending"
    assert ExecutionStatus.RUNNING.value == "running"
    assert ExecutionStatus.SUCCESS.value == "success"
    assert ExecutionStatus.FAILED.value == "failed"
    assert ExecutionStatus.TIMEOUT.value == "timeout"
    assert ExecutionStatus.CANCELLED.value == "cancelled"


def test_execution_status_is_terminal():
    """Test terminal status checking."""
    assert ExecutionStatus.SUCCESS.is_terminal()
    assert ExecutionStatus.FAILED.is_terminal()
    assert ExecutionStatus.TIMEOUT.is_terminal()
    assert ExecutionStatus.CANCELLED.is_terminal()
    assert not ExecutionStatus.PENDING.is_terminal()
    assert not ExecutionStatus.RUNNING.is_terminal()


def test_execution_status_is_successful():
    """Test success status checking."""
    assert ExecutionStatus.SUCCESS.is_successful()
    assert not ExecutionStatus.FAILED.is_successful()
    assert not ExecutionStatus.TIMEOUT.is_successful()
    assert not ExecutionStatus.CANCELLED.is_successful()
    assert not ExecutionStatus.PENDING.is_successful()
    assert not ExecutionStatus.RUNNING.is_successful()
