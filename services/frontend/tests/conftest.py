"""Pytest configuration and shared fixtures for Frontend Service tests.

This module provides comprehensive test fixtures for enterprise-grade testing
of real-time features, dashboard components, WebSocket connections, and UI
interactions within the Frontend service.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime, timedelta
import json

from modules.realtime_interface import RealtimeInterface
from modules.log_cache import LogCache
from modules.summarizer_cache import SummarizerCache


# =============================================================================
# SHARED TEST FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def request_id():
    """Generate a unique request ID for each test."""
    return str(uuid.uuid4())


@pytest.fixture(scope="function")
def correlation_id():
    """Generate a unique correlation ID for each test."""
    return str(uuid.uuid4())


@pytest.fixture(scope="function")
def test_timestamp():
    """Provide a consistent timestamp for testing."""
    return datetime(2024, 1, 1, 12, 0, 0)


# =============================================================================
# DOMAIN ENTITY FIXTURES
# =============================================================================

@pytest.fixture
def sample_websocket_message():
    """Sample WebSocket message."""
    return {
        "type": "service_status_update",
        "data": {
            "service": "interpreter",
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "response_time_ms": 245,
                "requests_per_minute": 12,
                "error_rate": 0.01
            }
        },
        "correlation_id": str(uuid.uuid4()),
        "sequence_number": 42
    }


@pytest.fixture
def sample_dashboard_data():
    """Sample dashboard data."""
    return {
        "services_overview": {
            "total_services": 12,
            "healthy_services": 10,
            "degraded_services": 1,
            "down_services": 1,
            "overall_health_score": 91.7
        },
        "recent_activity": [
            {
                "timestamp": datetime.now() - timedelta(minutes=5),
                "event_type": "service_restart",
                "service": "orchestrator",
                "details": "Automatic restart due to health check failure"
            },
            {
                "timestamp": datetime.now() - timedelta(minutes=3),
                "event_type": "workflow_completed",
                "service": "interpreter",
                "details": "Document analysis workflow finished successfully"
            }
        ],
        "performance_metrics": {
            "avg_response_time": 234,
            "total_requests": 15420,
            "error_rate": 0.008,
            "uptime_percentage": 99.7
        },
        "alerts": [
            {
                "level": "warning",
                "service": "memory_agent",
                "message": "High memory usage detected",
                "timestamp": datetime.now() - timedelta(minutes=2)
            }
        ]
    }


@pytest.fixture
def sample_log_entry():
    """Sample log entry."""
    return {
        "timestamp": datetime.now(),
        "level": "INFO",
        "service": "interpreter",
        "message": "Document analysis completed successfully",
        "correlation_id": str(uuid.uuid4()),
        "metadata": {
            "user_id": "user123",
            "document_id": "doc456",
            "processing_time_ms": 1250,
            "tokens_used": 450
        },
        "stack_trace": None,
        "request_id": str(uuid.uuid4())
    }


@pytest.fixture
def sample_realtime_update():
    """Sample real-time update."""
    return {
        "update_id": str(uuid.uuid4()),
        "timestamp": datetime.now(),
        "update_type": "service_metrics",
        "data": {
            "service": "orchestrator",
            "metric_type": "throughput",
            "value": 45.2,
            "unit": "requests_per_minute",
            "trend": "increasing",
            "change_percentage": 12.5
        },
        "priority": "normal",
        "expires_at": datetime.now() + timedelta(minutes=5)
    }


@pytest.fixture
def sample_user_session():
    """Sample user session data."""
    return {
        "session_id": str(uuid.uuid4()),
        "user_id": "user123",
        "start_time": datetime.now() - timedelta(hours=2),
        "last_activity": datetime.now() - timedelta(minutes=5),
        "current_page": "dashboard",
        "preferences": {
            "theme": "dark",
            "refresh_interval": 30,
            "notifications_enabled": True,
            "auto_refresh": True
        },
        "active_connections": {
            "websocket": True,
            "api_polling": False
        },
        "permissions": {
            "admin_access": False,
            "service_management": True,
            "log_viewing": True,
            "workflow_execution": True
        }
    }


@pytest.fixture
def sample_ui_component_state():
    """Sample UI component state."""
    return {
        "component_id": "services_overview_table",
        "component_type": "data_table",
        "state": {
            "sort_column": "name",
            "sort_direction": "asc",
            "filters": {
                "status": ["healthy", "degraded"],
                "category": ["core", "ai_services"]
            },
            "page": 1,
            "page_size": 25,
            "selected_rows": ["interpreter", "orchestrator"],
            "expanded_rows": ["interpreter"]
        },
        "last_updated": datetime.now(),
        "data_version": "v1.2.3",
        "user_customizations": {
            "column_order": ["name", "status", "uptime", "response_time"],
            "hidden_columns": ["last_restart"],
            "column_widths": {"name": 200, "status": 100}
        }
    }


# =============================================================================
# MOCK FIXTURES
# =============================================================================

@pytest.fixture
def mock_websocket_connection():
    """Mock WebSocket connection."""
    mock_ws = AsyncMock()
    mock_ws.send_json = AsyncMock(return_value=None)
    mock_ws.receive_json = AsyncMock(return_value={
        "type": "subscribe",
        "channels": ["service_status", "logs"]
    })
    mock_ws.close = AsyncMock(return_value=None)
    mock_ws.closed = False
    return mock_ws


@pytest.fixture
def mock_websocket_manager():
    """Mock WebSocket manager."""
    mock_manager = AsyncMock()
    mock_manager.connect = AsyncMock(return_value="ws_connection_123")
    mock_manager.disconnect = AsyncMock(return_value=True)
    mock_manager.send_to_client = AsyncMock(return_value=True)
    mock_manager.broadcast = AsyncMock(return_value=True)
    mock_manager.get_active_connections = AsyncMock(return_value=15)
    mock_manager.get_connection_info = AsyncMock(return_value={
        "connection_id": "ws_conn_123",
        "user_id": "user123",
        "connected_at": datetime.now(),
        "last_activity": datetime.now(),
        "subscribed_channels": ["service_status", "logs", "metrics"]
    })
    return mock_manager


@pytest.fixture
def mock_realtime_interface(mock_websocket_manager):
    """Mock real-time interface."""
    mock_realtime = AsyncMock()
    mock_realtime.initialize = AsyncMock(return_value=True)
    mock_realtime.subscribe_to_updates = AsyncMock(return_value=str(uuid.uuid4()))
    mock_realtime.unsubscribe_from_updates = AsyncMock(return_value=True)
    mock_realtime.publish_update = AsyncMock(return_value=True)
    mock_realtime.get_active_subscriptions = AsyncMock(return_value=[
        {"subscription_id": str(uuid.uuid4()), "channels": ["service_status"]},
        {"subscription_id": str(uuid.uuid4()), "channels": ["logs", "metrics"]}
    ])
    mock_realtime.get_subscription_stats = AsyncMock(return_value={
        "total_subscriptions": 8,
        "active_channels": ["service_status", "logs", "metrics", "alerts"],
        "avg_messages_per_minute": 45,
        "peak_connections": 23
    })
    return mock_realtime


@pytest.fixture
def mock_log_cache():
    """Mock log cache."""
    mock_cache = AsyncMock()
    mock_cache.store_log = AsyncMock(return_value=True)
    mock_cache.retrieve_logs = AsyncMock(return_value=[
        {
            "timestamp": datetime.now(),
            "level": "INFO",
            "service": "interpreter",
            "message": "Processing completed"
        }
    ])
    mock_cache.search_logs = AsyncMock(return_value={
        "total_matches": 25,
        "results": [],
        "search_time_ms": 45
    })
    mock_cache.get_cache_stats = AsyncMock(return_value={
        "total_entries": 15420,
        "cache_hit_rate": 0.87,
        "memory_usage_mb": 45.2,
        "avg_entry_size_bytes": 1024
    })
    mock_cache.clear_cache = AsyncMock(return_value=True)
    return mock_cache


@pytest.fixture
def mock_summarizer_cache():
    """Mock summarizer cache."""
    mock_cache = AsyncMock()
    mock_cache.get_summary = AsyncMock(return_value={
        "summary": "Services are operating normally with 91.7% overall health score",
        "generated_at": datetime.now(),
        "valid_for_minutes": 15,
        "data_points_used": 12
    })
    mock_cache.store_summary = AsyncMock(return_value=True)
    mock_cache.invalidate_summaries = AsyncMock(return_value=5)  # Number invalidated
    mock_cache.get_cache_performance = AsyncMock(return_value={
        "hit_rate": 0.92,
        "avg_response_time_ms": 15,
        "cache_size_mb": 12.5,
        "summaries_served": 1540
    })
    return mock_cache


@pytest.fixture
def mock_service_monitor():
    """Mock service monitor."""
    mock_monitor = AsyncMock()
    mock_monitor.get_service_status = AsyncMock(return_value={
        "status": "healthy",
        "response_time_ms": 145,
        "last_check": datetime.now(),
        "uptime_percentage": 99.5
    })
    mock_monitor.get_service_metrics = AsyncMock(return_value={
        "requests_per_minute": 23.4,
        "error_rate": 0.005,
        "avg_response_time": 234,
        "active_connections": 12
    })
    mock_monitor.check_service_health = AsyncMock(return_value={
        "healthy": True,
        "checks_passed": 8,
        "checks_failed": 0,
        "response_time_ms": 145
    })
    mock_monitor.get_service_logs = AsyncMock(return_value=[
        {"timestamp": datetime.now(), "level": "INFO", "message": "Service running normally"}
    ])
    return mock_monitor


@pytest.fixture
def mock_ui_handler():
    """Mock UI handler."""
    mock_handler = AsyncMock()
    mock_handler.handle_request = AsyncMock(return_value={
        "status": "success",
        "data": {"result": "handled successfully"},
        "processing_time_ms": 45
    })
    mock_handler.validate_request = AsyncMock(return_value=True)
    mock_handler.format_response = AsyncMock(return_value="<div>Formatted response</div>")
    mock_handler.get_handler_stats = AsyncMock(return_value={
        "requests_handled": 1540,
        "avg_processing_time_ms": 42,
        "error_rate": 0.008,
        "cache_hit_rate": 0.76
    })
    return mock_handler


@pytest.fixture
def mock_api_client():
    """Mock API client for backend communication."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value={
        "status_code": 200,
        "data": {"services": ["interpreter", "orchestrator"]},
        "response_time_ms": 145
    })
    mock_client.post = AsyncMock(return_value={
        "status_code": 201,
        "data": {"workflow_id": str(uuid.uuid4())},
        "response_time_ms": 234
    })
    mock_client.put = AsyncMock(return_value={
        "status_code": 200,
        "data": {"updated": True},
        "response_time_ms": 156
    })
    mock_client.delete = AsyncMock(return_value={
        "status_code": 204,
        "data": None,
        "response_time_ms": 98
    })
    mock_client.get_connection_stats = AsyncMock(return_value={
        "total_requests": 15420,
        "avg_response_time_ms": 145,
        "error_rate": 0.008,
        "active_connections": 5
    })
    return mock_client


@pytest.fixture
def mock_data_browser():
    """Mock data browser for service data exploration."""
    mock_browser = AsyncMock()
    mock_browser.get_service_data = AsyncMock(return_value={
        "service": "interpreter",
        "data": {
            "active_workflows": 3,
            "queued_requests": 12,
            "completed_today": 245
        },
        "last_updated": datetime.now()
    })
    mock_browser.search_service_data = AsyncMock(return_value={
        "query": "error logs",
        "total_results": 15,
        "results": [],
        "search_time_ms": 67
    })
    mock_browser.get_data_schema = AsyncMock(return_value={
        "service": "interpreter",
        "schema": {
            "workflows": {
                "id": "string",
                "status": "enum[pending,running,completed,failed]",
                "created_at": "datetime"
            }
        }
    })
    mock_browser.export_data = AsyncMock(return_value={
        "export_id": str(uuid.uuid4()),
        "format": "json",
        "file_size_bytes": 15432,
        "download_url": "http://localhost/export/123"
    })
    return mock_browser


@pytest.fixture
def mock_analysis_monitor():
    """Mock analysis monitor for performance tracking."""
    mock_monitor = AsyncMock()
    mock_monitor.get_performance_metrics = AsyncMock(return_value={
        "period": "last_hour",
        "metrics": {
            "avg_response_time": 234,
            "throughput_rpm": 45,
            "error_rate": 0.008,
            "cache_hit_rate": 0.87
        },
        "trends": {
            "response_time_trend": "stable",
            "throughput_trend": "increasing",
            "error_rate_trend": "decreasing"
        }
    })
    mock_monitor.generate_performance_report = AsyncMock(return_value={
        "report_id": str(uuid.uuid4()),
        "title": "Performance Analysis Report",
        "period": "2024-01-01 to 2024-01-07",
        "summary": "Overall performance is stable with improving trends",
        "recommendations": ["Consider increasing cache size", "Optimize database queries"]
    })
    mock_monitor.detect_performance_anomalies = AsyncMock(return_value=[
        {
            "anomaly_type": "response_time_spike",
            "severity": "medium",
            "timestamp": datetime.now(),
            "description": "Response time increased by 45% for 5 minutes"
        }
    ])
    return mock_monitor


# =============================================================================
# INTEGRATION TEST FIXTURES
# =============================================================================

@pytest.fixture
def integration_config():
    """Configuration for integration tests."""
    return {
        "websocket_url": "ws://localhost:8080/ws",
        "api_base_url": "http://localhost:8080/api",
        "realtime_update_interval": 5,
        "max_websocket_connections": 100,
        "cache_ttl_seconds": 300,
        "test_timeout": 30,
        "cleanup_after_tests": True,
        "test_data": {
            "websocket_messages": 100,
            "api_requests": 200,
            "log_entries": 500,
            "user_sessions": 10
        }
    }


@pytest.fixture
def mock_external_services():
    """Mock external services for integration testing."""
    return {
        "interpreter": AsyncMock(),
        "orchestrator": AsyncMock(),
        "doc_store": AsyncMock(),
        "prompt_store": AsyncMock(),
        "memory_agent": AsyncMock(),
        "log_collector": AsyncMock(),
        "notification_service": AsyncMock(),
        "websocket_server": AsyncMock(),
        "cache_service": AsyncMock()
    }


# =============================================================================
# PERFORMANCE TEST FIXTURES
# =============================================================================

@pytest.fixture
def performance_test_data():
    """Test data for performance benchmarking."""
    return {
        "websocket_messages": [
            {
                "type": "service_status_update",
                "data": {"service": f"service_{i}", "status": "healthy", "response_time": 100 + i},
                "expected_delivery_time_ms": 50
            }
            for i in range(1000)
        ],
        "dashboard_loads": [
            {
                "dashboard_type": "services_overview",
                "data_points": 50 + (i * 10),
                "expected_render_time_ms": 200 + (i * 5)
            }
            for i in range(50)
        ],
        "api_requests": [
            {
                "endpoint": f"/api/services/{i}",
                "method": "GET",
                "expected_response_time_ms": 150,
                "payload_size_bytes": 1024 + (i * 100)
            }
            for i in range(500)
        ],
        "concurrent_users": [
            {
                "user_count": 10 + (i * 5),
                "actions_per_user": 20,
                "test_duration_seconds": 300,
                "expected_avg_response_time_ms": 200 + (i * 10)
            }
            for i in range(10)
        ],
        "realtime_scenarios": [
            {
                "scenario": "high_frequency_updates",
                "updates_per_second": 10 + i,
                "duration_seconds": 60,
                "expected_dropped_messages": 0
            }
            for i in range(20)
        ]
    }


@pytest.fixture
def load_test_scenario():
    """Load testing scenario configuration."""
    return {
        "duration_seconds": 300,
        "concurrent_users": 200,
        "ramp_up_seconds": 60,
        "scenarios": {
            "dashboard_interaction": {
                "weight": 40,
                "steps": ["load_dashboard", "interact_with_widgets", "refresh_data", "navigate_pages"]
            },
            "realtime_monitoring": {
                "weight": 30,
                "steps": ["establish_websocket", "subscribe_channels", "receive_updates", "handle_alerts"]
            },
            "api_operations": {
                "weight": 20,
                "steps": ["api_request", "process_response", "update_ui", "cache_data"]
            },
            "log_monitoring": {
                "weight": 10,
                "steps": ["view_logs", "filter_logs", "search_logs", "export_logs"]
            }
        },
        "thresholds": {
            "avg_page_load_time_ms": 500,
            "websocket_message_delivery_time_ms": 100,
            "api_response_time_ms": 300,
            "ui_interaction_response_time_ms": 100,
            "memory_usage_mb": 256,
            "error_rate_percent": 1.0
        }
    }


# =============================================================================
# CHAOS ENGINEERING FIXTURES
# =============================================================================

@pytest.fixture
def chaos_experiment_config():
    """Configuration for chaos engineering experiments."""
    return {
        "experiment_name": "frontend_service_resilience_test",
        "duration_minutes": 15,
        "failure_scenarios": [
            {
                "type": "websocket_connection_loss",
                "target": "websocket_server",
                "duration_seconds": 120,
                "impact": "high",
                "reconnection_test": True
            },
            {
                "type": "api_service_degradation",
                "target": "backend_api",
                "latency_increase_ms": 3000,
                "duration_seconds": 180,
                "impact": "medium"
            },
            {
                "type": "cache_failure",
                "target": "frontend_cache",
                "duration_seconds": 90,
                "impact": "medium",
                "fallback_test": True
            },
            {
                "type": "high_memory_pressure",
                "target": "browser_memory",
                "memory_limit_mb": 100,
                "duration_seconds": 300,
                "impact": "high"
            },
            {
                "type": "network_intermittency",
                "target": "client_network",
                "packet_loss_percentage": 5,
                "duration_seconds": 240,
                "impact": "medium",
                "recovery_test": True
            }
        ],
        "monitoring": {
            "metrics": ["websocket_reconnection_time", "ui_error_rate", "api_timeout_rate", "memory_usage", "page_load_time"],
            "alerts": ["websocket_disconnection_rate > 10%", "ui_error_rate > 5%", "memory_usage > 90%", "page_load_time > 3000ms"],
            "recovery_time_sla": 300
        },
        "data_integrity_checks": [
            "ui_state_preservation",
            "websocket_message_ordering",
            "cache_data_consistency",
            "session_data_integrity"
        ]
    }


@pytest.fixture
def mock_failure_injector():
    """Mock failure injector for chaos testing."""
    mock_injector = MagicMock()
    mock_injector.inject_websocket_failure = MagicMock(return_value=True)
    mock_injector.inject_api_degradation = MagicMock(return_value=True)
    mock_injector.inject_cache_failure = MagicMock(return_value=True)
    mock_injector.inject_memory_pressure = MagicMock(return_value=True)
    mock_injector.inject_network_issues = MagicMock(return_value=True)
    mock_injector.restore_normal_operation = MagicMock(return_value=True)
    mock_injector.get_system_health = MagicMock(return_value={
        "status": "degraded",
        "active_failures": ["websocket_down", "api_slow", "memory_high"],
        "recovery_eta_seconds": 120,
        "ui_error_rate": 0.03,
        "websocket_reconnection_rate": 0.85
    })
    return mock_injector
