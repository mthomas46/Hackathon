"""Pytest configuration and shared fixtures for Notification Service tests.

This module provides comprehensive test fixtures for enterprise-grade testing
of event routing, dead letter queue management, notification delivery, and
owner resolution within the Notification Service.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime, timedelta
import json

from modules.notification_sender import NotificationSender
from modules.dlq_manager import DLQManager
from modules.owner_resolver import OwnerResolver


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
def sample_notification_event():
    """Sample notification event."""
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "service_failure",
        "severity": "high",
        "source_service": "interpreter",
        "timestamp": datetime.now(),
        "title": "Document Interpreter Service Down",
        "description": "The document interpreter service has become unresponsive",
        "details": {
            "error_code": "CONNECTION_TIMEOUT",
            "last_seen": datetime.now() - timedelta(minutes=5),
            "affected_components": ["document_processing", "api_endpoints"],
            "impact_assessment": "high"
        },
        "metadata": {
            "correlation_id": str(uuid.uuid4()),
            "request_id": str(uuid.uuid4()),
            "user_context": {"user_id": "user_001", "session_id": "sess_123"}
        },
        "routing_rules": {
            "priority_channels": ["email", "slack"],
            "target_owners": ["platform_team", "oncall_engineer"],
            "escalation_policy": "immediate"
        }
    }


@pytest.fixture
def sample_notification_template():
    """Sample notification template."""
    return {
        "template_id": "service_failure_template",
        "template_name": "Service Failure Alert",
        "template_type": "alert",
        "description": "Template for service failure notifications",
        "channels": ["email", "slack", "sms"],
        "subject_template": "🚨 ALERT: {{service_name}} Service Failure - {{severity|upper}} Priority",
        "body_templates": {
            "email": {
                "html": """
                <div style="background-color: #ffebee; border-left: 4px solid #f44336; padding: 16px; margin: 16px 0;">
                    <h2 style="color: #d32f2f; margin-top: 0;">Service Failure Alert</h2>
                    <p><strong>Service:</strong> {{source_service}}</p>
                    <p><strong>Status:</strong> {{severity|upper}} Priority</p>
                    <p><strong>Description:</strong> {{description}}</p>
                    <p><strong>Timestamp:</strong> {{timestamp|strftime('%Y-%m-%d %H:%M:%S UTC')}}</p>
                    <p><strong>Error Details:</strong> {{details.error_code}}</p>
                    <div style="background-color: #fff3e0; padding: 12px; margin: 12px 0; border-radius: 4px;">
                        <h4>Impact Assessment: {{details.impact_assessment|upper}}</h4>
                        <ul>
                        {% for component in details.affected_components %}
                            <li>{{ component }}</li>
                        {% endfor %}
                        </ul>
                    </div>
                    <p style="color: #666; font-size: 12px;">
                        This alert was generated automatically by the Notification Service.<br>
                        Event ID: {{event_id}}
                    </p>
                </div>
                """,
                "text": """
                🚨 SERVICE FAILURE ALERT 🚨

                Service: {{source_service}}
                Status: {{severity|upper}} Priority
                Description: {{description}}
                Timestamp: {{timestamp|strftime('%Y-%m-%d %H:%M:%S UTC')}}
                Error Details: {{details.error_code}}

                Impact Assessment: {{details.impact_assessment|upper}}
                Affected Components:
                {% for component in details.affected_components %}
                - {{ component }}
                {% endfor %}

                Event ID: {{event_id}}
                """
            },
            "slack": {
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "🚨 Service Failure Alert"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*Service:*\n{{source_service}}"},
                            {"type": "mrkdwn", "text": f"*Priority:*\n{{severity|upper}}"},
                            {"type": "mrkdwn", "text": f"*Time:*\n{{timestamp|strftime('%H:%M:%S UTC')}}"}
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Description:* {{description}}"
                        }
                    }
                ]
            },
            "sms": {
                "text": "ALERT: {{source_service}} {{severity|upper}} failure. {{description}}. Event: {{event_id}}"
            }
        },
        "variables": [
            {"name": "source_service", "type": "string", "required": True},
            {"name": "severity", "type": "enum", "values": ["low", "medium", "high", "critical"], "required": True},
            {"name": "description", "type": "string", "required": True},
            {"name": "timestamp", "type": "datetime", "required": True},
            {"name": "event_id", "type": "string", "required": True},
            {"name": "details", "type": "object", "required": False}
        ],
        "metadata": {
            "created_by": "platform_team",
            "created_at": datetime.now() - timedelta(days=30),
            "last_modified": datetime.now() - timedelta(days=5),
            "usage_count": 145,
            "success_rate": 0.98
        }
    }


@pytest.fixture
def sample_owner_configuration():
    """Sample owner configuration for notification routing."""
    return {
        "owner_id": "platform_team",
        "owner_name": "Platform Engineering Team",
        "owner_type": "team",
        "contact_methods": {
            "email": {
                "addresses": ["platform@company.com", "alerts@company.com"],
                "preferred": True
            },
            "slack": {
                "channels": ["#platform-alerts", "#oncall"],
                "users": ["@platform-lead", "@oncall-engineer"],
                "preferred": True
            },
            "sms": {
                "numbers": ["+1-555-0101", "+1-555-0102"],
                "preferred": False
            },
            "pagerduty": {
                "integration_key": "pd_integration_key_123",
                "preferred": True
            }
        },
        "notification_preferences": {
            "quiet_hours": {
                "enabled": True,
                "timezone": "America/New_York",
                "start_time": "22:00",
                "end_time": "08:00",
                "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
            },
            "escalation_policy": {
                "immediate_acknowledgment_required": True,
                "maximum_response_time_minutes": 15,
                "escalation_levels": [
                    {"delay_minutes": 0, "contacts": ["primary_oncall"]},
                    {"delay_minutes": 5, "contacts": ["secondary_oncall", "team_lead"]},
                    {"delay_minutes": 10, "contacts": ["engineering_manager", "vp_engineering"]}
                ]
            },
            "severity_filtering": {
                "minimum_severity": "medium",
                "bypass_filter_events": ["security_breach", "data_loss"]
            }
        },
        "responsibilities": [
            "interpreter",
            "doc_store",
            "prompt_store",
            "orchestrator"
        ],
        "metadata": {
            "created_at": datetime.now() - timedelta(days=90),
            "last_updated": datetime.now() - timedelta(days=7),
            "active": True,
            "timezone": "America/New_York"
        }
    }


@pytest.fixture
def sample_dlq_entry():
    """Sample dead letter queue entry."""
    return {
        "dlq_id": str(uuid.uuid4()),
        "original_event_id": str(uuid.uuid4()),
        "event_type": "service_failure",
        "severity": "high",
        "source_service": "interpreter",
        "failure_reason": "delivery_timeout",
        "failure_details": {
            "error_code": "SMTP_CONNECTION_TIMEOUT",
            "error_message": "Connection to SMTP server timed out after 30 seconds",
            "retry_count": 3,
            "last_attempt": datetime.now() - timedelta(minutes=5),
            "next_retry_scheduled": datetime.now() + timedelta(hours=1)
        },
        "original_payload": {
            "title": "Document Interpreter Service Down",
            "description": "The document interpreter service has become unresponsive",
            "target_owners": ["platform_team"],
            "channels": ["email", "slack"]
        },
        "delivery_attempts": [
            {
                "attempt_id": str(uuid.uuid4()),
                "timestamp": datetime.now() - timedelta(minutes=15),
                "channel": "email",
                "target": "platform@company.com",
                "status": "failed",
                "error": "connection_timeout"
            },
            {
                "attempt_id": str(uuid.uuid4()),
                "timestamp": datetime.now() - timedelta(minutes=10),
                "channel": "email",
                "target": "alerts@company.com",
                "status": "failed",
                "error": "connection_timeout"
            },
            {
                "attempt_id": str(uuid.uuid4()),
                "timestamp": datetime.now() - timedelta(minutes=5),
                "channel": "slack",
                "target": "#platform-alerts",
                "status": "failed",
                "error": "rate_limit_exceeded"
            }
        ],
        "metadata": {
            "created_at": datetime.now() - timedelta(minutes=15),
            "last_updated": datetime.now() - timedelta(minutes=5),
            "ttl_seconds": 604800,  # 7 days
            "expires_at": datetime.now() + timedelta(days=7),
            "requeue_attempts": 2,
            "max_requeue_attempts": 5
        },
        "processing_status": "awaiting_retry"
    }


@pytest.fixture
def sample_delivery_attempt():
    """Sample notification delivery attempt."""
    return {
        "attempt_id": str(uuid.uuid4()),
        "event_id": str(uuid.uuid4()),
        "channel": "email",
        "target": "platform@company.com",
        "status": "pending",
        "scheduled_time": datetime.now(),
        "template_id": "service_failure_template",
        "rendered_content": {
            "subject": "🚨 ALERT: interpreter Service Failure - HIGH Priority",
            "body_html": "<div>Rendered HTML content...</div>",
            "body_text": "Rendered text content..."
        },
        "delivery_metadata": {
            "smtp_server": "smtp.company.com",
            "port": 587,
            "encryption": "tls",
            "authentication": True,
            "timeout_seconds": 30
        },
        "retry_policy": {
            "max_attempts": 3,
            "base_delay_seconds": 60,
            "backoff_multiplier": 2,
            "max_delay_seconds": 3600
        },
        "attempt_history": [],
        "metadata": {
            "created_at": datetime.now(),
            "priority": "high",
            "correlation_id": str(uuid.uuid4()),
            "owner_id": "platform_team"
        }
    }


# =============================================================================
# MOCK FIXTURES
# =============================================================================

@pytest.fixture
def mock_notification_sender():
    """Mock notification sender."""
    mock_sender = AsyncMock()
    mock_sender.send_notification = AsyncMock(return_value={
        "delivery_id": str(uuid.uuid4()),
        "status": "delivered",
        "channel": "email",
        "target": "platform@company.com",
        "delivered_at": datetime.now(),
        "response_time_ms": 245
    })
    mock_sender.validate_channel_config = AsyncMock(return_value={
        "channel": "email",
        "valid": True,
        "configuration_status": "ready",
        "connectivity_test_passed": True
    })
    mock_sender.get_delivery_status = AsyncMock(return_value={
        "delivery_id": "del_123",
        "status": "delivered",
        "delivered_at": datetime.now(),
        "confirmation_received": True
    })
    return mock_sender


@pytest.fixture
def mock_dlq_manager():
    """Mock DLQ manager."""
    mock_dlq = AsyncMock()
    mock_dlq.add_to_dlq = AsyncMock(return_value={
        "dlq_id": str(uuid.uuid4()),
        "status": "queued",
        "estimated_retry_time": datetime.now() + timedelta(hours=1)
    })
    mock_dlq.get_dlq_entries = AsyncMock(return_value=[
        {
            "dlq_id": str(uuid.uuid4()),
            "event_type": "service_failure",
            "failure_reason": "delivery_timeout",
            "created_at": datetime.now() - timedelta(hours=2)
        }
    ])
    mock_dlq.requeue_dlq_entry = AsyncMock(return_value={
        "dlq_id": "dlq_123",
        "requeue_status": "scheduled",
        "next_attempt": datetime.now() + timedelta(hours=1)
    })
    mock_dlq.get_dlq_stats = AsyncMock(return_value={
        "total_entries": 45,
        "entries_by_status": {"awaiting_retry": 30, "max_retries_exceeded": 15},
        "entries_by_failure_reason": {"delivery_timeout": 25, "channel_error": 12, "invalid_target": 8},
        "avg_time_in_dlq_hours": 24.5
    })
    return mock_dlq


@pytest.fixture
def mock_owner_resolver():
    """Mock owner resolver."""
    mock_resolver = AsyncMock()
    mock_resolver.resolve_owners = AsyncMock(return_value=[
        {
            "owner_id": "platform_team",
            "owner_type": "team",
            "contact_methods": ["email", "slack"],
            "priority": "high"
        }
    ])
    mock_resolver.validate_owner_config = AsyncMock(return_value={
        "owner_id": "platform_team",
        "valid": True,
        "contact_methods_verified": ["email", "slack"],
        "issues": []
    })
    mock_resolver.get_owner_preferences = AsyncMock(return_value={
        "quiet_hours_enabled": True,
        "timezone": "America/New_York",
        "severity_filter": "medium"
    })
    return mock_resolver


@pytest.fixture
def mock_channel_providers():
    """Mock channel providers for different notification channels."""
    return {
        "email": AsyncMock(),
        "slack": AsyncMock(),
        "sms": AsyncMock(),
        "pagerduty": AsyncMock()
    }


@pytest.fixture
def mock_template_engine():
    """Mock template engine for notification rendering."""
    mock_engine = AsyncMock()
    mock_engine.render_template = AsyncMock(return_value={
        "rendered_content": {
            "subject": "🚨 ALERT: Service Failure",
            "body_html": "<div>Rendered HTML content</div>",
            "body_text": "Rendered text content"
        },
        "render_time_ms": 45,
        "validation_passed": True
    })
    mock_engine.validate_template = AsyncMock(return_value={
        "template_id": "service_failure_template",
        "valid": True,
        "syntax_check_passed": True,
        "variable_validation_passed": True,
        "issues": []
    })
    mock_engine.get_template_variables = AsyncMock(return_value=[
        {"name": "service_name", "type": "string", "required": True},
        {"name": "severity", "type": "enum", "values": ["low", "medium", "high", "critical"], "required": True}
    ])
    return mock_engine


@pytest.fixture
def mock_event_router():
    """Mock event router for notification routing logic."""
    mock_router = AsyncMock()
    mock_router.route_event = AsyncMock(return_value={
        "routing_decision": "deliver",
        "target_owners": ["platform_team", "oncall_engineer"],
        "channels": ["email", "slack", "pagerduty"],
        "priority": "high",
        "escalation_required": True
    })
    mock_router.validate_routing_rules = AsyncMock(return_value={
        "rules_valid": True,
        "routing_coverage": 0.95,
        "potential_gaps": []
    })
    mock_router.get_routing_stats = AsyncMock(return_value={
        "total_events_routed": 15420,
        "routing_efficiency": 0.98,
        "average_routing_time_ms": 12,
        "routing_rules_active": 25
    })
    return mock_router


@pytest.fixture
def mock_delivery_tracker():
    """Mock delivery tracker for notification delivery monitoring."""
    mock_tracker = AsyncMock()
    mock_tracker.track_delivery_attempt = AsyncMock(return_value={
        "tracking_id": str(uuid.uuid4()),
        "delivery_status": "delivered",
        "confirmation_received": True,
        "delivery_time_ms": 245
    })
    mock_tracker.get_delivery_history = AsyncMock(return_value=[
        {
            "delivery_id": str(uuid.uuid4()),
            "channel": "email",
            "status": "delivered",
            "timestamp": datetime.now() - timedelta(minutes=5)
        }
    ])
    mock_tracker.get_delivery_metrics = AsyncMock(return_value={
        "total_deliveries": 12543,
        "delivery_success_rate": 0.967,
        "average_delivery_time_ms": 234,
        "deliveries_by_channel": {
            "email": {"count": 8921, "success_rate": 0.981},
            "slack": {"count": 2654, "success_rate": 0.945},
            "sms": {"count": 654, "success_rate": 0.923},
            "pagerduty": {"count": 314, "success_rate": 0.997}
        }
    })
    return mock_tracker


# =============================================================================
# INTEGRATION TEST FIXTURES
# =============================================================================

@pytest.fixture
def integration_test_config():
    """Configuration for integration tests."""
    return {
        "test_services": ["notification_service", "interpreter", "orchestrator"],
        "notification_channels": ["email", "slack", "sms"],
        "test_events": [
            {"type": "service_failure", "severity": "high", "count": 10},
            {"type": "performance_alert", "severity": "medium", "count": 15},
            {"type": "security_event", "severity": "critical", "count": 5}
        ],
        "test_duration_seconds": 300,
        "expected_delivery_rate": 0.95,
        "max_delivery_delay_seconds": 60
    }


@pytest.fixture
def mock_external_services():
    """Mock external services for integration testing."""
    return {
        "smtp_server": AsyncMock(),
        "slack_api": AsyncMock(),
        "twilio_api": AsyncMock(),
        "pagerduty_api": AsyncMock(),
        "service_registry": AsyncMock()
    }


# =============================================================================
# PERFORMANCE TEST FIXTURES
# =============================================================================

@pytest.fixture
def performance_test_scenarios():
    """Performance testing scenarios for notification operations."""
    return {
        "high_volume_notifications": {
            "name": "High Volume Notification Storm",
            "description": "Simulate high volume of notifications during system-wide incident",
            "event_rate_per_second": 50,
            "duration_seconds": 300,
            "event_types": ["service_failure", "performance_alert", "security_event"],
            "expected_delivery_success_rate": 0.90,
            "max_average_delivery_time_ms": 5000
        },
        "mixed_priority_delivery": {
            "name": "Mixed Priority Delivery Test",
            "description": "Test delivery prioritization with mixed high/medium/low priority notifications",
            "total_notifications": 1000,
            "priority_distribution": {"high": 0.1, "medium": 0.3, "low": 0.6},
            "expected_high_priority_delivery_rate": 0.98,
            "expected_medium_priority_delivery_rate": 0.95,
            "expected_low_priority_delivery_rate": 0.85
        },
        "channel_failure_resilience": {
            "name": "Channel Failure Resilience Test",
            "description": "Test system resilience when notification channels fail",
            "primary_channel_failure_rate": 0.5,
            "secondary_channel_available": True,
            "total_notifications": 500,
            "expected_overall_delivery_rate": 0.85
        },
        "owner_resolution_performance": {
            "name": "Owner Resolution Performance",
            "description": "Test performance of owner resolution for large numbers of events",
            "concurrent_events": 100,
            "unique_owners": 20,
            "expected_resolution_time_ms": 100,
            "expected_resolution_success_rate": 0.99
        }
    }


@pytest.fixture
def load_test_configuration():
    """Load testing configuration for notification service."""
    return {
        "duration_minutes": 15,
        "concurrent_events_per_second": 100,
        "total_events": 90000,
        "event_distribution": {
            "service_failures": 0.3,
            "performance_alerts": 0.4,
            "security_events": 0.2,
            "maintenance_notifications": 0.1
        },
        "channel_distribution": {
            "email": 0.6,
            "slack": 0.3,
            "sms": 0.05,
            "pagerduty": 0.05
        },
        "thresholds": {
            "min_delivery_success_rate": 0.85,
            "max_average_delivery_time_ms": 3000,
            "max_dlq_queue_size": 1000,
            "max_memory_usage_mb": 1024,
            "max_cpu_usage_percent": 75
        }
    }


# =============================================================================
# CHAOS ENGINEERING FIXTURES
# =============================================================================

@pytest.fixture
def chaos_experiment_config():
    """Configuration for chaos engineering experiments."""
    return {
        "experiment_name": "notification_service_resilience_test",
        "duration_minutes": 20,
        "failure_scenarios": [
            {
                "type": "channel_failure",
                "target": "email_channel",
                "description": "Simulate email service unavailability",
                "duration_seconds": 180,
                "impact": "medium",
                "fallback_test": True
            },
            {
                "type": "owner_resolution_failure",
                "target": "owner_resolver",
                "description": "Simulate owner resolution service failures",
                "duration_seconds": 120,
                "impact": "high",
                "degradation_test": True
            },
            {
                "type": "high_delivery_backlog",
                "target": "delivery_queue",
                "description": "Create excessive delivery backlog",
                "backlog_size": 10000,
                "duration_seconds": 300,
                "impact": "high",
                "queue_management_test": True
            },
            {
                "type": "template_rendering_failure",
                "target": "template_engine",
                "description": "Simulate template rendering failures",
                "failure_rate": 0.3,
                "duration_seconds": 240,
                "impact": "medium",
                "error_handling_test": True
            },
            {
                "type": "dlq_overflow",
                "target": "dead_letter_queue",
                "description": "Simulate DLQ capacity limits being reached",
                "queue_capacity": 1000,
                "overflow_rate": 2.0,
                "duration_seconds": 360,
                "impact": "high",
                "capacity_management_test": True
            }
        ],
        "monitoring": {
            "metrics": [
                "delivery_success_rate",
                "average_delivery_time",
                "dlq_queue_size",
                "error_rate",
                "channel_availability"
            ],
            "alerts": [
                "delivery_success_rate < 80%",
                "average_delivery_time > 10000ms",
                "dlq_queue_size > 500",
                "error_rate > 20%"
            ],
            "recovery_sla_seconds": 300
        },
        "data_integrity_checks": [
            "notification_event_integrity",
            "delivery_attempt_tracking",
            "dlq_entry_consistency",
            "owner_resolution_accuracy"
        ]
    }


@pytest.fixture
def mock_failure_injector():
    """Mock failure injector for chaos testing."""
    mock_injector = MagicMock()
    mock_injector.inject_channel_failure = MagicMock(return_value=True)
    mock_injector.inject_owner_resolution_failure = MagicMock(return_value=True)
    mock_injector.inject_delivery_backlog = MagicMock(return_value=True)
    mock_injector.inject_template_failure = MagicMock(return_value=True)
    mock_injector.inject_dlq_overflow = MagicMock(return_value=True)
    mock_injector.restore_normal_operation = MagicMock(return_value=True)
    mock_injector.get_system_health = MagicMock(return_value={
        "status": "degraded",
        "active_failures": ["email_down", "owner_resolution_slow", "high_backlog"],
        "recovery_eta_seconds": 180,
        "delivery_success_rate": 0.72,
        "average_delivery_time_ms": 4500,
        "dlq_queue_size": 750
    })
    return mock_injector
