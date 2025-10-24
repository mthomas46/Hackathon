"""
Unit tests for Structured Logger (Week 2, Day 7).

Tests:
- JSON logging
- Correlation ID management
- Request tracing
- Structured fields
- Decorators
"""

import pytest
import json
import uuid
import logging
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.utils.structured_logger import (
    StructuredLogger,
    get_structured_logger,
    set_request_id,
    get_request_id,
    set_job_id,
    get_job_id,
    set_user_id,
    get_user_id,
    clear_correlation_ids,
    with_request_id,
    log_function_call
)


@pytest.fixture
def mock_logger(monkeypatch):
    """Create a mock logger for testing."""
    mock = MagicMock(spec=logging.Logger)
    mock.name = "test_logger"
    
    def get_logger(name=None):
        if name:
            mock.name = name
        return mock
    
    monkeypatch.setattr(logging, 'getLogger', get_logger)
    return mock


@pytest.mark.unit
class TestStructuredLogger:
    """Test StructuredLogger class."""
    
    def test_initialization(self, mock_logger):
        """Test logger initialization."""
        logger = StructuredLogger("test", request_id="req-123")
        
        assert logger.request_id == "req-123"
        assert logger.job_id is None
        assert logger.user_id is None
        assert logger.logger.name == "test"
    
    def test_auto_generate_request_id(self, mock_logger):
        """Test automatic request ID generation."""
        clear_correlation_ids()
        logger = StructuredLogger("test")
        
        assert logger.request_id is not None
        assert isinstance(logger.request_id, str)
        assert len(logger.request_id) > 0
    
    def test_build_log_entry(self, mock_logger):
        """Test building structured log entry."""
        logger = StructuredLogger("test", request_id="req-123", job_id="job-456")
        
        entry = logger._build_log_entry(
            "INFO",
            "test_event",
            custom_field="custom_value"
        )
        
        assert entry["level"] == "INFO"
        assert entry["event"] == "test_event"
        assert entry["request_id"] == "req-123"
        assert entry["job_id"] == "job-456"
        assert entry["custom_field"] == "custom_value"
        assert "timestamp" in entry
        assert "logger" in entry
    
    def test_info_logging(self, mock_logger):
        """Test info level logging."""
        logger = StructuredLogger("test", request_id="req-123")
        logger.info("test_event", key="value")
        
        # Verify logger.info was called
        mock_logger.info.assert_called_once()
        
        # Parse the JSON message
        call_args = mock_logger.info.call_args[0][0]
        log_entry = json.loads(call_args)
        
        assert log_entry["level"] == "INFO"
        assert log_entry["event"] == "test_event"
        assert log_entry["key"] == "value"
        assert log_entry["request_id"] == "req-123"
    
    def test_error_logging(self, mock_logger):
        """Test error level logging."""
        logger = StructuredLogger("test", request_id="req-123")
        logger.error("error_event", error_type="ValueError", error_message="Test error")
        
        mock_logger.error.assert_called_once()
        
        call_args = mock_logger.error.call_args[0][0]
        log_entry = json.loads(call_args)
        
        assert log_entry["level"] == "ERROR"
        assert log_entry["event"] == "error_event"
        assert log_entry["error_type"] == "ValueError"
        assert log_entry["error_message"] == "Test error"
    
    def test_log_request(self, mock_logger):
        """Test HTTP request logging."""
        logger = StructuredLogger("test", request_id="req-123")
        logger.log_request(
            method="GET",
            path="/api/test",
            status_code=200,
            duration_ms=45.2
        )
        
        mock_logger.info.assert_called_once()
        
        call_args = mock_logger.info.call_args[0][0]
        log_entry = json.loads(call_args)
        
        assert log_entry["event"] == "http_request"
        assert log_entry["method"] == "GET"
        assert log_entry["path"] == "/api/test"
        assert log_entry["status_code"] == 200
        assert log_entry["duration_ms"] == 45.2
    
    def test_log_job_event(self, mock_logger):
        """Test job event logging."""
        logger = StructuredLogger("test", request_id="req-123", job_id="job-456")
        logger.log_job_event(
            event="job_progress",
            status="processing",
            progress=0.5
        )
        
        mock_logger.info.assert_called_once()
        
        call_args = mock_logger.info.call_args[0][0]
        log_entry = json.loads(call_args)
        
        assert log_entry["event"] == "job_progress"
        assert log_entry["status"] == "processing"
        assert log_entry["progress"] == 0.5
        assert log_entry["job_id"] == "job-456"
    
    def test_log_error_with_trace(self, mock_logger):
        """Test error logging with stack trace."""
        logger = StructuredLogger("test", request_id="req-123")
        
        try:
            raise ValueError("Test error")
        except ValueError as e:
            logger.log_error_with_trace("error_occurred", e)
        
        mock_logger.error.assert_called_once()
        
        call_args = mock_logger.error.call_args[0][0]
        log_entry = json.loads(call_args)
        
        assert log_entry["event"] == "error_occurred"
        assert log_entry["error_type"] == "ValueError"
        assert log_entry["error_message"] == "Test error"
        assert "stack_trace" in log_entry
        assert "ValueError: Test error" in log_entry["stack_trace"]


@pytest.mark.unit
class TestCorrelationIDs:
    """Test correlation ID management."""
    
    def test_set_and_get_request_id(self):
        """Test request ID management."""
        clear_correlation_ids()
        
        set_request_id("req-789")
        assert get_request_id() == "req-789"
    
    def test_set_and_get_job_id(self):
        """Test job ID management."""
        clear_correlation_ids()
        
        set_job_id("job-101")
        assert get_job_id() == "job-101"
    
    def test_set_and_get_user_id(self):
        """Test user ID management."""
        clear_correlation_ids()
        
        set_user_id("user-202")
        assert get_user_id() == "user-202"
    
    def test_clear_all_ids(self):
        """Test clearing all correlation IDs."""
        set_request_id("req-789")
        set_job_id("job-101")
        set_user_id("user-202")
        
        clear_correlation_ids()
        
        assert get_request_id() is None
        assert get_job_id() is None
        assert get_user_id() is None
    
    def test_multiple_loggers_share_context(self, mock_logger):
        """Test that multiple loggers share correlation ID context."""
        clear_correlation_ids()
        set_request_id("shared-req-id")
        
        logger1 = StructuredLogger("test1")
        logger2 = StructuredLogger("test2")
        
        assert logger1.request_id == "shared-req-id"
        assert logger2.request_id == "shared-req-id"


@pytest.mark.unit
class TestDecorators:
    """Test logging decorators."""
    
    @pytest.mark.asyncio
    async def test_with_request_id_async(self):
        """Test request ID decorator with async function."""
        clear_correlation_ids()
        
        @with_request_id
        async def async_func():
            return get_request_id()
        
        result = await async_func()
        
        assert result is not None
        assert isinstance(result, str)
    
    def test_with_request_id_sync(self):
        """Test request ID decorator with sync function."""
        clear_correlation_ids()
        
        @with_request_id
        def sync_func():
            return get_request_id()
        
        result = sync_func()
        
        assert result is not None
        assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_log_function_call_async(self, mock_logger):
        """Test function call logging with async function."""
        @log_function_call("test_operation")
        async def async_func():
            return "result"
        
        result = await async_func()
        
        assert result == "result"
        # Should have logged start and complete
        assert mock_logger.debug.call_count >= 2
    
    def test_log_function_call_sync(self, mock_logger):
        """Test function call logging with sync function."""
        @log_function_call("test_operation")
        def sync_func():
            return "result"
        
        result = sync_func()
        
        assert result == "result"
        # Should have logged start and complete
        assert mock_logger.debug.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_log_function_call_with_error_async(self, mock_logger):
        """Test function call logging with error in async function."""
        @log_function_call("failing_operation")
        async def failing_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            await failing_func()
        
        # Should have logged error
        assert mock_logger.error.call_count >= 1
    
    def test_log_function_call_with_error_sync(self, mock_logger):
        """Test function call logging with error in sync function."""
        @log_function_call("failing_operation")
        def failing_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            failing_func()
        
        # Should have logged error
        assert mock_logger.error.call_count >= 1


@pytest.mark.unit
class TestLoggerFactory:
    """Test logger factory function."""
    
    def test_get_structured_logger(self, mock_logger):
        """Test factory function."""
        logger = get_structured_logger(
            "test",
            request_id="req-999",
            job_id="job-888"
        )
        
        assert isinstance(logger, StructuredLogger)
        assert logger.request_id == "req-999"
        assert logger.job_id == "job-888"
    
    def test_get_structured_logger_minimal(self, mock_logger):
        """Test factory function with minimal args."""
        clear_correlation_ids()
        logger = get_structured_logger("test")
        
        assert isinstance(logger, StructuredLogger)
        assert logger.request_id is not None


@pytest.mark.unit
class TestJSONSerialization:
    """Test JSON serialization of log entries."""
    
    def test_complex_objects(self, mock_logger):
        """Test logging with complex objects."""
        logger = StructuredLogger("test", request_id="req-123")
        
        logger.info(
            "complex_event",
            data={
                "nested": {"key": "value"},
                "list": [1, 2, 3],
                "number": 42,
                "boolean": True,
                "null": None
            }
        )
        
        mock_logger.info.assert_called_once()
        
        call_args = mock_logger.info.call_args[0][0]
        log_entry = json.loads(call_args)  # Should not raise
        
        assert log_entry["data"]["nested"]["key"] == "value"
        assert log_entry["data"]["list"] == [1, 2, 3]
        assert log_entry["data"]["number"] == 42
        assert log_entry["data"]["boolean"] is True
        assert log_entry["data"]["null"] is None
    
    def test_timestamp_format(self, mock_logger):
        """Test timestamp format."""
        logger = StructuredLogger("test", request_id="req-123")
        
        logger.info("test_event")
        
        call_args = mock_logger.info.call_args[0][0]
        log_entry = json.loads(call_args)
        
        # Verify ISO format with Z suffix
        timestamp = log_entry["timestamp"]
        assert timestamp.endswith("Z")
        
        # Should be parseable
        datetime.fromisoformat(timestamp.rstrip("Z"))


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

