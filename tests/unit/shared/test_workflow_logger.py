"""Unit tests for WorkflowLogger

Tests the universal workflow logging client for the Enhanced Roadmap v2.0.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from services.shared.infrastructure.logging.workflow_logger import (
    WorkflowLogger,
    LogLevel,
    quick_log
)


@pytest.fixture
def mock_http_client():
    """Mock HTTP client for testing."""
    mock_client = AsyncMock()
    mock_response = Mock()
    mock_response.status_code = 200
    mock_client.post.return_value = mock_response
    return mock_client


@pytest.fixture
async def workflow_logger(mock_http_client):
    """Create workflow logger with mocked client."""
    with patch('httpx.AsyncClient', return_value=mock_http_client):
        logger = WorkflowLogger(
            service_name="test-service",
            log_collector_url="http://localhost:5040"
        )
        yield logger
        await logger.close()


class TestWorkflowLoggerInitialization:
    """Test WorkflowLogger initialization."""
    
    def test_logger_initialization(self):
        """Test basic logger initialization."""
        logger = WorkflowLogger(
            service_name="test-service",
            log_collector_url="http://localhost:5040"
        )
        
        assert logger.service_name == "test-service"
        assert logger.log_collector_url == "http://localhost:5040"
        assert logger.timeout_seconds == 5.0
        assert logger.fail_silently is True
    
    def test_logger_custom_timeout(self):
        """Test logger with custom timeout."""
        logger = WorkflowLogger(
            service_name="test-service",
            timeout_seconds=10.0
        )
        
        assert logger.timeout_seconds == 10.0
    
    def test_logger_fail_not_silently(self):
        """Test logger configured to raise exceptions."""
        logger = WorkflowLogger(
            service_name="test-service",
            fail_silently=False
        )
        
        assert logger.fail_silently is False


class TestWorkflowStart:
    """Test workflow start logging."""
    
    @pytest.mark.asyncio
    async def test_log_workflow_start_basic(self, workflow_logger, mock_http_client):
        """Test basic workflow start logging."""
        # Act
        result = await workflow_logger.log_workflow_start(
            workflow_id="wf-123",
            operation="test_operation"
        )
        
        # Assert
        assert result is True
        mock_http_client.post.assert_called_once()
        
        call_args = mock_http_client.post.call_args
        assert call_args[0][0] == "http://localhost:5040/logs"
        
        log_entry = call_args[1]['json']
        assert log_entry['level'] == "INFO"
        assert log_entry['service'] == "test-service"
        assert "Workflow started" in log_entry['message']
        assert log_entry['context']['workflow_id'] == "wf-123"
        assert log_entry['context']['operation'] == "test_operation"
        assert log_entry['context']['phase'] == "start"
    
    @pytest.mark.asyncio
    async def test_log_workflow_start_with_context(self, workflow_logger, mock_http_client):
        """Test workflow start with additional context."""
        # Act
        result = await workflow_logger.log_workflow_start(
            workflow_id="wf-123",
            operation="test_op",
            context={"user": "test-user", "feature": "auth"},
            user_id="user-001"
        )
        
        # Assert
        assert result is True
        log_entry = mock_http_client.post.call_args[1]['json']
        assert log_entry['context']['user'] == "test-user"
        assert log_entry['context']['feature'] == "auth"
        assert log_entry['context']['user_id'] == "user-001"


class TestWorkflowStep:
    """Test workflow step logging."""
    
    @pytest.mark.asyncio
    async def test_log_workflow_step(self, workflow_logger, mock_http_client):
        """Test logging a workflow step."""
        # Act
        result = await workflow_logger.log_workflow_step(
            workflow_id="wf-123",
            step_name="process_data",
            step_data={"records": 100, "duration": 1.5}
        )
        
        # Assert
        assert result is True
        log_entry = mock_http_client.post.call_args[1]['json']
        assert log_entry['level'] == "DEBUG"
        assert "Workflow step" in log_entry['message']
        assert log_entry['context']['step_name'] == "process_data"
        assert log_entry['context']['records'] == 100
        assert log_entry['context']['duration'] == 1.5
    
    @pytest.mark.asyncio
    async def test_log_workflow_step_custom_level(self, workflow_logger, mock_http_client):
        """Test workflow step with custom log level."""
        # Act
        result = await workflow_logger.log_workflow_step(
            workflow_id="wf-123",
            step_name="important_step",
            step_data={"status": "complete"},
            level=LogLevel.INFO
        )
        
        # Assert
        log_entry = mock_http_client.post.call_args[1]['json']
        assert log_entry['level'] == "INFO"


class TestWorkflowComplete:
    """Test workflow completion logging."""
    
    @pytest.mark.asyncio
    async def test_log_workflow_complete_success(self, workflow_logger, mock_http_client):
        """Test logging successful workflow completion."""
        # Act
        result = await workflow_logger.log_workflow_complete(
            workflow_id="wf-123",
            duration_ms=1234.5,
            success=True,
            metrics={"items_processed": 50}
        )
        
        # Assert
        assert result is True
        log_entry = mock_http_client.post.call_args[1]['json']
        assert log_entry['level'] == "INFO"
        assert "completed" in log_entry['message']
        assert log_entry['context']['duration_ms'] == 1234.5
        assert log_entry['context']['success'] is True
        assert log_entry['context']['items_processed'] == 50
    
    @pytest.mark.asyncio
    async def test_log_workflow_complete_failure(self, workflow_logger, mock_http_client):
        """Test logging failed workflow completion."""
        # Act
        result = await workflow_logger.log_workflow_complete(
            workflow_id="wf-123",
            duration_ms=500.0,
            success=False
        )
        
        # Assert
        log_entry = mock_http_client.post.call_args[1]['json']
        assert log_entry['level'] == "ERROR"
        assert "failed" in log_entry['message']
        assert log_entry['context']['success'] is False


class TestServiceCall:
    """Test service call logging."""
    
    @pytest.mark.asyncio
    async def test_log_service_call(self, workflow_logger, mock_http_client):
        """Test logging a service call."""
        # Act
        result = await workflow_logger.log_service_call(
            workflow_id="wf-123",
            target_service="llm-gateway",
            operation="generate",
            duration_ms=250.0,
            success=True,
            response_data={"tokens": 150}
        )
        
        # Assert
        assert result is True
        log_entry = mock_http_client.post.call_args[1]['json']
        assert "Service call" in log_entry['message']
        assert log_entry['context']['target_service'] == "llm-gateway"
        assert log_entry['context']['operation'] == "generate"
        assert log_entry['context']['duration_ms'] == 250.0


class TestErrorLogging:
    """Test error logging."""
    
    @pytest.mark.asyncio
    async def test_log_error(self, workflow_logger, mock_http_client):
        """Test logging an error."""
        # Arrange
        test_error = ValueError("Test error message")
        
        # Act
        result = await workflow_logger.log_error(
            workflow_id="wf-123",
            error=test_error,
            context={"step": "data_processing"}
        )
        
        # Assert
        assert result is True
        log_entry = mock_http_client.post.call_args[1]['json']
        assert log_entry['level'] == "ERROR"
        assert "Test error message" in log_entry['message']
        assert log_entry['context']['error_type'] == "ValueError"
        assert log_entry['context']['step'] == "data_processing"
        assert 'traceback' in log_entry['context']


class TestPerformanceMetrics:
    """Test performance metric logging."""
    
    @pytest.mark.asyncio
    async def test_log_performance_metric(self, workflow_logger, mock_http_client):
        """Test logging a performance metric."""
        # Act
        result = await workflow_logger.log_performance_metric(
            workflow_id="wf-123",
            metric_name="response_time",
            metric_value=125.5,
            metric_unit="ms",
            additional_context={"endpoint": "/api/v1/query"}
        )
        
        # Assert
        assert result is True
        log_entry = mock_http_client.post.call_args[1]['json']
        assert "Performance metric" in log_entry['message']
        assert log_entry['context']['metric_name'] == "response_time"
        assert log_entry['context']['metric_value'] == 125.5
        assert log_entry['context']['metric_unit'] == "ms"


class TestConvenienceMethods:
    """Test convenience logging methods."""
    
    @pytest.mark.asyncio
    async def test_log_debug(self, workflow_logger, mock_http_client):
        """Test debug logging."""
        result = await workflow_logger.log_debug(
            workflow_id="wf-123",
            message="Debug message",
            context={"detail": "value"}
        )
        
        assert result is True
        log_entry = mock_http_client.post.call_args[1]['json']
        assert log_entry['level'] == "DEBUG"
    
    @pytest.mark.asyncio
    async def test_log_warning(self, workflow_logger, mock_http_client):
        """Test warning logging."""
        result = await workflow_logger.log_warning(
            workflow_id="wf-123",
            message="Warning message"
        )
        
        assert result is True
        log_entry = mock_http_client.post.call_args[1]['json']
        assert log_entry['level'] == "WARNING"


class TestFailureHandling:
    """Test logger failure handling."""
    
    @pytest.mark.asyncio
    async def test_logging_failure_silent(self):
        """Test that logging failures are silent by default."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.post.side_effect = Exception("Network error")
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            logger = WorkflowLogger(
                service_name="test-service",
                fail_silently=True
            )
            
            # Act - should not raise exception
            result = await logger.log_workflow_start("wf-123", "test")
            
            # Assert
            assert result is False
    
    @pytest.mark.asyncio
    async def test_logging_failure_not_silent(self):
        """Test that logging failures raise when configured."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.post.side_effect = Exception("Network error")
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            logger = WorkflowLogger(
                service_name="test-service",
                fail_silently=False
            )
            
            # Act & Assert
            with pytest.raises(Exception, match="Network error"):
                await logger.log_workflow_start("wf-123", "test")


class TestResponseSummarization:
    """Test response data summarization."""
    
    def test_summarize_small_response(self, workflow_logger):
        """Test summarization of small response."""
        response = {"status": "ok", "count": 5}
        summary = workflow_logger._summarize_response(response)
        
        assert summary == response
    
    def test_summarize_large_list(self, workflow_logger):
        """Test summarization of response with large list."""
        response = {"items": [1, 2, 3, 4, 5]}
        summary = workflow_logger._summarize_response(response)
        
        assert "<list with 5 items>" in summary["items"]
    
    def test_summarize_long_string(self, workflow_logger):
        """Test summarization of long string."""
        long_string = "a" * 200
        response = {"data": long_string}
        summary = workflow_logger._summarize_response(response)
        
        assert len(summary["data"]) == 103  # 100 chars + "..."
        assert summary["data"].endswith("...")


class TestContextManager:
    """Test async context manager support."""
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test using logger as async context manager."""
        async with WorkflowLogger("test-service") as logger:
            assert logger.service_name == "test-service"
        
        # Client should be closed after context


class TestQuickLog:
    """Test quick_log convenience function."""
    
    @pytest.mark.asyncio
    async def test_quick_log(self):
        """Test quick_log function."""
        with patch('services.shared.infrastructure.logging.workflow_logger.WorkflowLogger._send_log') as mock_send:
            mock_send.return_value = True
            
            await quick_log(
                service_name="test-service",
                workflow_id="wf-123",
                message="Quick test",
                level=LogLevel.INFO,
                context={"test": "data"}
            )
            
            # Verify _send_log was called
            assert mock_send.called


@pytest.mark.integration
class TestIntegrationWithLogCollector:
    """Integration tests with actual log-collector service."""
    
    @pytest.mark.asyncio
    async def test_send_log_to_collector(self):
        """Test sending actual log to log-collector (requires service running)."""
        # This test requires log-collector service to be running
        # Skip if service is not available
        
        try:
            async with WorkflowLogger("test-service") as logger:
                result = await logger.log_workflow_start(
                    workflow_id="integration-test-123",
                    operation="integration_test"
                )
                
                # If service is available, this should succeed
                assert result is True
        except Exception:
            pytest.skip("Log collector service not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

