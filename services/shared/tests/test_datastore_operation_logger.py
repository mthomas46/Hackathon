"""Unit tests for DataStore Operation Logger Middleware.

Tests the middleware that logs all database operations to log-collector.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request
from starlette.responses import Response

# Import the middleware
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infrastructure.logging.datastore_operation_logger import (
    DataStoreOperationMiddleware,
    add_datastore_logging
)


class TestDataStoreOperationMiddleware:
    """Unit tests for DataStoreOperationMiddleware class."""
    
    @pytest.fixture
    def app(self):
        """Create a test FastAPI app."""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}
        
        @app.post("/documents")
        async def create_document():
            return {"id": "doc-123", "status": "created"}
        
        @app.get("/health")
        async def health():
            return {"status": "healthy"}
        
        return app
    
    @pytest.fixture
    def middleware(self, app):
        """Create middleware instance."""
        return DataStoreOperationMiddleware(
            app,
            service_name="test-service",
            log_collector_url="http://localhost:8104",
            timeout_seconds=1.0
        )
    
    def test_middleware_initialization(self, middleware):
        """Test middleware initializes with correct config."""
        assert middleware.service_name == "test-service"
        assert middleware.log_collector_url == "http://localhost:8104"
        assert middleware.timeout_seconds == 1.0
        assert "/documents" in str(middleware.log_paths)
    
    def test_determine_operation_type_create(self, middleware):
        """Test operation type detection for CREATE operations."""
        op_type = middleware._determine_operation_type("POST", "/documents")
        assert op_type == "create"
    
    def test_determine_operation_type_read(self, middleware):
        """Test operation type detection for READ operations."""
        op_type = middleware._determine_operation_type("GET", "/documents/123")
        assert op_type == "read"
    
    def test_determine_operation_type_list(self, middleware):
        """Test operation type detection for LIST operations."""
        op_type = middleware._determine_operation_type("GET", "/documents/")
        assert op_type == "list"
    
    def test_determine_operation_type_search(self, middleware):
        """Test operation type detection for SEARCH operations."""
        op_type = middleware._determine_operation_type("GET", "/documents/search")
        assert op_type == "search"
    
    def test_determine_operation_type_update(self, middleware):
        """Test operation type detection for UPDATE operations."""
        op_type = middleware._determine_operation_type("PUT", "/documents/123")
        assert op_type == "update"
    
    def test_determine_operation_type_delete(self, middleware):
        """Test operation type detection for DELETE operations."""
        op_type = middleware._determine_operation_type("DELETE", "/documents/123")
        assert op_type == "delete"
    
    def test_determine_operation_type_bulk(self, middleware):
        """Test operation type detection for BULK operations."""
        op_type = middleware._determine_operation_type("POST", "/documents/bulk")
        assert op_type == "bulk_create"
    
    @patch('infrastructure.logging.datastore_operation_logger.httpx.Client')
    def test_send_log_success(self, mock_client, middleware):
        """Test successful log sending."""
        mock_post = Mock()
        mock_client.return_value.post = mock_post
        
        middleware._send_log(
            level="INFO",
            message="Test log",
            context={"test": "data"}
        )
        
        # Verify httpx client was called with correct data
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:8104/logs"
        
        log_data = call_args[1]['json']
        assert log_data['service'] == "test-service"
        assert log_data['level'] == "INFO"
        assert log_data['message'] == "Test log"
        assert log_data['context']['test'] == "data"
        assert 'timestamp' in log_data
    
    @patch('infrastructure.logging.datastore_operation_logger.httpx.Client')
    def test_send_log_failure_graceful(self, mock_client, middleware):
        """Test that log sending failures don't crash the middleware."""
        mock_client.return_value.post.side_effect = Exception("Network error")
        
        # Should not raise exception
        try:
            middleware._send_log(
                level="INFO",
                message="Test log",
                context={}
            )
        except Exception:
            pytest.fail("Middleware should handle logging failures gracefully")
    
    @pytest.mark.asyncio
    async def test_middleware_skips_health_check(self, app):
        """Test that middleware skips health check endpoints."""
        logged_operations = []
        
        # Mock the _send_log method to track calls
        with patch.object(
            DataStoreOperationMiddleware,
            '_send_log',
            side_effect=lambda *args, **kwargs: logged_operations.append(args[1])
        ):
            add_datastore_logging(app, "test-service")
            client = TestClient(app)
            
            response = client.get("/health")
            assert response.status_code == 200
            
            # Health check should not be logged
            assert len(logged_operations) == 0
    
    @pytest.mark.asyncio
    async def test_middleware_logs_document_operations(self, app):
        """Test that middleware logs document operations."""
        logged_operations = []
        
        def capture_log(level, message, context):
            logged_operations.append({
                'level': level,
                'message': message,
                'context': context
            })
        
        with patch.object(
            DataStoreOperationMiddleware,
            '_send_log',
            side_effect=capture_log
        ):
            add_datastore_logging(app, "test-service")
            client = TestClient(app)
            
            response = client.post("/documents")
            assert response.status_code == 200
            
            # Should have logged start and complete
            assert len(logged_operations) >= 2
            
            # Check start log
            start_log = logged_operations[0]
            assert "started" in start_log['message'].lower()
            assert start_log['context']['method'] == "POST"
            assert start_log['context']['path'] == "/documents"
            assert start_log['context']['operation_type'] == "create"
            
            # Check complete log
            complete_log = logged_operations[1]
            assert "completed" in complete_log['message'].lower()
            assert complete_log['context']['status_code'] == 200
            assert 'duration_ms' in complete_log['context']
            assert complete_log['context']['success'] is True


class TestAddDatastoreLogging:
    """Tests for the add_datastore_logging helper function."""
    
    def test_add_datastore_logging_basic(self):
        """Test basic middleware addition."""
        app = FastAPI()
        
        add_datastore_logging(
            app,
            service_name="test-service",
            log_collector_url="http://localhost:8104"
        )
        
        # Check that middleware was added
        assert len(app.user_middleware) > 0
    
    def test_add_datastore_logging_custom_config(self):
        """Test middleware with custom configuration."""
        app = FastAPI()
        
        add_datastore_logging(
            app,
            service_name="custom-service",
            log_collector_url="http://custom:9999",
            timeout_seconds=2.5,
            log_paths=["/api/"]
        )
        
        # Middleware should be added
        assert len(app.user_middleware) > 0


class TestWorkflowIdTracking:
    """Tests for X-Workflow-ID header tracking."""
    
    @pytest.mark.asyncio
    async def test_workflow_id_captured(self):
        """Test that workflow ID from header is captured in logs."""
        app = FastAPI()
        
        @app.get("/documents")
        async def get_docs():
            return {"docs": []}
        
        logged_operations = []
        
        def capture_log(level, message, context):
            logged_operations.append(context)
        
        with patch.object(
            DataStoreOperationMiddleware,
            '_send_log',
            side_effect=capture_log
        ):
            add_datastore_logging(app, "test-service")
            client = TestClient(app)
            
            # Send request with workflow ID
            response = client.get(
                "/documents",
                headers={"X-Workflow-ID": "workflow-abc-123"}
            )
            
            assert response.status_code == 200
            assert len(logged_operations) >= 2
            
            # Check that workflow ID was captured
            for log_context in logged_operations:
                assert log_context['workflow_id'] == "workflow-abc-123"
    
    @pytest.mark.asyncio
    async def test_workflow_id_default(self):
        """Test default workflow ID when header not present."""
        app = FastAPI()
        
        @app.get("/documents")
        async def get_docs():
            return {"docs": []}
        
        logged_operations = []
        
        def capture_log(level, message, context):
            logged_operations.append(context)
        
        with patch.object(
            DataStoreOperationMiddleware,
            '_send_log',
            side_effect=capture_log
        ):
            add_datastore_logging(app, "test-service")
            client = TestClient(app)
            
            response = client.get("/documents")
            
            assert response.status_code == 200
            
            # Should have default workflow_id
            for log_context in logged_operations:
                assert log_context['workflow_id'] == "unknown"


class TestErrorLogging:
    """Tests for error logging capabilities."""
    
    @pytest.mark.asyncio
    async def test_error_logged_on_exception(self):
        """Test that exceptions are properly logged."""
        app = FastAPI()
        
        @app.get("/documents")
        async def failing_endpoint():
            raise ValueError("Test error")
        
        logged_operations = []
        
        def capture_log(level, message, context):
            logged_operations.append({
                'level': level,
                'message': message,
                'context': context
            })
        
        with patch.object(
            DataStoreOperationMiddleware,
            '_send_log',
            side_effect=capture_log
        ):
            add_datastore_logging(app, "test-service")
            client = TestClient(app)
            
            try:
                client.get("/documents")
            except Exception:
                pass  # Expected
            
            # Should have logged error
            error_logs = [log for log in logged_operations if log['level'] == "ERROR"]
            assert len(error_logs) > 0
            
            error_log = error_logs[0]
            assert "failed" in error_log['message'].lower()
            assert 'error' in error_log['context']
            assert 'error_type' in error_log['context']
            assert error_log['context']['error_type'] == "ValueError"


class TestPerformanceTracking:
    """Tests for duration and performance tracking."""
    
    @pytest.mark.asyncio
    async def test_duration_tracking(self):
        """Test that operation duration is tracked."""
        app = FastAPI()
        
        @app.get("/documents")
        async def slow_endpoint():
            await asyncio.sleep(0.1)  # 100ms delay
            return {"docs": []}
        
        logged_operations = []
        
        def capture_log(level, message, context):
            logged_operations.append(context)
        
        with patch.object(
            DataStoreOperationMiddleware,
            '_send_log',
            side_effect=capture_log
        ):
            add_datastore_logging(app, "test-service")
            client = TestClient(app)
            
            response = client.get("/documents")
            assert response.status_code == 200
            
            # Find the complete log
            complete_logs = [log for log in logged_operations if log.get('phase') == 'complete']
            assert len(complete_logs) > 0
            
            complete_log = complete_logs[0]
            assert 'duration_ms' in complete_log
            # Should be at least 100ms
            assert complete_log['duration_ms'] >= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

