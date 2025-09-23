"""Unit Tests for Notification Delivery in Notification Service.

This module tests notification delivery capabilities including:
- Multi-channel delivery (email, Slack, SMS, PagerDuty)
- Delivery tracking and confirmation
- Retry logic and failure handling
- Template rendering and personalization

Tests cover the complete notification delivery infrastructure within the Notification Service.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from modules.notification_sender import NotificationSender


class TestMultiChannelDelivery:
    """Test Multi-Channel Delivery functionality."""

    @pytest.fixture
    def notification_sender(self, mock_channel_providers):
        """Create notification sender instance."""
        return NotificationSender(channel_providers=mock_channel_providers)

    def test_channel_availability_detection(self, notification_sender):
        """Test automatic channel availability detection."""
        channel_status_checks = [
            {
                "channel": "email",
                "endpoints": ["smtp.company.com:587", "smtp.backup.com:587"],
                "expected_available": True,
                "expected_primary": "smtp.company.com:587"
            },
            {
                "channel": "slack",
                "endpoints": ["https://slack.com/api", "https://hooks.slack.com"],
                "expected_available": True,
                "expected_primary": "https://hooks.slack.com"
            },
            {
                "channel": "sms",
                "endpoints": ["twilio_api", "aws_sns"],
                "expected_available": True,
                "expected_primary": "twilio_api"
            },
            {
                "channel": "pagerduty",
                "endpoints": ["https://api.pagerduty.com"],
                "expected_available": True,
                "expected_primary": "https://api.pagerduty.com"
            },
            {
                "channel": "webhook",
                "endpoints": ["https://webhook.company.com/alerts"],
                "expected_available": False,  # Simulated failure
                "expected_primary": None
            }
        ]

        for check in channel_status_checks:
            availability_result = notification_sender.check_channel_availability(check["channel"])

            assert availability_result["check_performed"] is True
            assert availability_result["channel_available"] == check["expected_available"]

            if check["expected_available"]:
                assert "available_endpoints" in availability_result
                assert len(availability_result["available_endpoints"]) > 0
                assert "primary_endpoint" in availability_result
                assert availability_result["primary_endpoint"] == check["expected_primary"]
            else:
                assert len(availability_result.get("available_endpoints", [])) == 0

    def test_delivery_routing_optimization(self, notification_sender):
        """Test delivery routing optimization across channels."""
        delivery_scenarios = [
            {
                "event_type": "critical_system_failure",
                "severity": "critical",
                "time_sensitivity": "immediate",
                "recipient_count": 5,
                "expected_channels": ["pagerduty", "sms", "slack"],
                "expected_strategy": "parallel_broadcast"
            },
            {
                "event_type": "performance_alert",
                "severity": "medium",
                "time_sensitivity": "within_hour",
                "recipient_count": 15,
                "expected_channels": ["slack", "email"],
                "expected_strategy": "staggered_delivery"
            },
            {
                "event_type": "maintenance_notification",
                "severity": "low",
                "time_sensitivity": "end_of_day",
                "recipient_count": 50,
                "expected_channels": ["email"],
                "expected_strategy": "batched_delivery"
            },
            {
                "event_type": "business_metric_update",
                "severity": "info",
                "time_sensitivity": "daily_digest",
                "recipient_count": 200,
                "expected_channels": ["email"],
                "expected_strategy": "digest_batch"
            }
        ]

        for scenario in delivery_scenarios:
            routing_optimization = notification_sender.optimize_delivery_routing(scenario)

            assert routing_optimization["optimization_success"] is True
            assert "delivery_strategy" in routing_optimization
            assert "channel_selection" in routing_optimization
            assert "routing_efficiency" in routing_optimization

            assert routing_optimization["delivery_strategy"] == scenario["expected_strategy"]

            channel_selection = routing_optimization["channel_selection"]
            assert len(channel_selection) >= len(scenario["expected_channels"])

            selected_channel_names = [ch["channel"] for ch in channel_selection]
            for expected_channel in scenario["expected_channels"]:
                assert expected_channel in selected_channel_names

            efficiency = routing_optimization["routing_efficiency"]
            assert "estimated_delivery_time_seconds" in efficiency
            assert "success_rate_projection" in efficiency
            assert "resource_utilization" in efficiency

    def test_channel_failover_mechanisms(self, notification_sender):
        """Test channel failover mechanisms."""
        failover_scenarios = [
            {
                "primary_channel": "email",
                "backup_channels": ["slack", "sms"],
                "failure_type": "smtp_server_down",
                "expected_failover": "slack",
                "expected_success": True
            },
            {
                "primary_channel": "slack",
                "backup_channels": ["email", "pagerduty"],
                "failure_type": "api_rate_limit",
                "expected_failover": "email",
                "expected_success": True
            },
            {
                "primary_channel": "sms",
                "backup_channels": ["email"],
                "failure_type": "carrier_outage",
                "expected_failover": "email",
                "expected_success": True
            },
            {
                "primary_channel": "pagerduty",
                "backup_channels": ["email", "sms"],
                "failure_type": "service_degradation",
                "expected_failover": ["email", "sms"],
                "expected_success": True
            },
            {
                "primary_channel": "webhook",
                "backup_channels": ["email"],
                "failure_type": "endpoint_unreachable",
                "expected_failover": None,
                "expected_success": False
            }
        ]

        for scenario in failover_scenarios:
            failover_result = notification_sender.handle_channel_failover(scenario)

            assert failover_result["failover_attempted"] is True

            if scenario["expected_success"]:
                assert failover_result["failover_success"] is True
                assert "failover_channel" in failover_result

                if isinstance(scenario["expected_failover"], str):
                    assert failover_result["failover_channel"] == scenario["expected_failover"]
                else:
                    # Multiple fallbacks
                    assert failover_result["failover_channel"] in scenario["expected_failover"]
            else:
                assert failover_result["failover_success"] is False
                assert "failure_reason" in failover_result

    def test_delivery_batch_processing(self, notification_sender):
        """Test delivery batch processing for efficiency."""
        batch_notifications = [
            {
                "id": f"notif_{i}",
                "channel": "email" if i % 3 == 0 else "slack" if i % 3 == 1 else "sms",
                "recipient": f"user{i}@company.com" if i % 3 == 0 else f"@user{i}" if i % 3 == 1 else f"+1-555-01{i:02d}",
                "content": f"Test notification {i}",
                "priority": "high" if i % 10 == 0 else "medium" if i % 5 == 0 else "low"
            }
            for i in range(50)
        ]

        batch_config = {
            "max_batch_size": 10,
            "batch_timeout_seconds": 30,
            "channel_prioritization": True,
            "priority_queueing": True,
            "parallel_processing": True
        }

        batch_result = notification_sender.process_delivery_batch(batch_notifications, batch_config)

        assert batch_result["batch_processing_success"] is True
        assert "batch_groups" in batch_result
        assert "processing_stats" in batch_result
        assert "delivery_results" in batch_result

        batch_groups = batch_result["batch_groups"]

        # Should group by channel
        assert "email" in batch_groups
        assert "slack" in batch_groups
        assert "sms" in batch_groups

        # Should respect batch size limits
        for channel, groups in batch_groups.items():
            for group in groups:
                assert len(group["notifications"]) <= batch_config["max_batch_size"]

        processing_stats = batch_result["processing_stats"]
        assert "total_batches" in processing_stats
        assert "average_batch_size" in processing_stats
        assert "processing_time_seconds" in processing_stats

        delivery_results = batch_result["delivery_results"]
        assert len(delivery_results) == len(batch_notifications)

        # Should prioritize high priority notifications
        high_priority_results = [r for r in delivery_results if r["priority"] == "high"]
        if high_priority_results:
            # High priority should be processed first (lower processing order)
            assert all(r["processing_order"] < 20 for r in high_priority_results)


class TestTemplateRendering:
    """Test Template Rendering functionality."""

    @pytest.fixture
    def notification_sender(self, mock_template_engine):
        """Create notification sender instance."""
        return NotificationSender(template_engine=mock_template_engine)

    def test_template_variable_substitution(self, notification_sender):
        """Test template variable substitution."""
        template_data = {
            "template_id": "service_alert_template",
            "template_content": """
            🚨 SERVICE ALERT 🚨

            Service: {{service_name}}
            Status: {{status|upper}}
            Severity: {{severity|title}}
            Timestamp: {{timestamp|strftime('%Y-%m-%d %H:%M:%S UTC')}}

            Description: {{description}}

            {% if affected_components %}
            Affected Components:
            {% for component in affected_components %}
            - {{component}}
            {% endfor %}
            {% endif %}

            Event ID: {{event_id}}
            """,
            "variables": {
                "service_name": "interpreter",
                "status": "degraded",
                "severity": "high",
                "timestamp": datetime(2024, 1, 1, 14, 30, 0),
                "description": "Document processing queue is backing up",
                "affected_components": ["document_processor", "queue_manager"],
                "event_id": "evt_123456"
            }
        }

        rendering_result = notification_sender.render_notification_template(template_data)

        assert rendering_result["rendering_success"] is True
        assert "rendered_content" in rendering_result
        assert "rendering_metadata" in rendering_result

        rendered_content = rendering_result["rendered_content"]
        assert "🚨 SERVICE ALERT 🚨" in rendered_content
        assert "Service: interpreter" in rendered_content
        assert "Status: DEGRADED" in rendered_content
        assert "Severity: High" in rendered_content
        assert "2024-01-01 14:30:00 UTC" in rendered_content
        assert "Document processing queue is backing up" in rendered_content
        assert "document_processor" in rendered_content
        assert "queue_manager" in rendered_content
        assert "Event ID: evt_123456" in rendered_content

        metadata = rendering_result["rendering_metadata"]
        assert "render_time_ms" in metadata
        assert "variable_substitutions" in metadata
        assert metadata["variable_substitutions"] == len(template_data["variables"])

    def test_template_conditionals_and_loops(self, notification_sender):
        """Test template conditionals and loops."""
        complex_template = {
            "template_content": """
            {% if severity == 'critical' %}
            🚨 CRITICAL ALERT 🚨
            {% elif severity == 'high' %}
            ⚠️ HIGH PRIORITY ALERT ⚠️
            {% else %}
            ℹ️ INFORMATION NOTICE ℹ️
            {% endif %}

            {% if metrics %}
            Current Metrics:
            {% for metric, value in metrics.items() %}
            - {{metric|title}}: {{value}}
            {% endfor %}
            {% endif %}

            {% if recommendations %}
            Recommendations:
            {% for recommendation in recommendations %}
            {{loop.index}}. {{recommendation}}
            {% endfor %}
            {% endif %}
            """,
            "variables": {
                "severity": "high",
                "metrics": {
                    "response_time_p95": "1250ms",
                    "error_rate": "2.3%",
                    "throughput": "450 rpm"
                },
                "recommendations": [
                    "Increase server capacity",
                    "Optimize database queries",
                    "Implement caching layer"
                ]
            }
        }

        rendering_result = notification_sender.render_notification_template(complex_template)

        assert rendering_result["rendering_success"] is True

        rendered_content = rendering_result["rendered_content"]
        assert "⚠️ HIGH PRIORITY ALERT ⚠️" in rendered_content
        assert "🚨 CRITICAL ALERT 🚨" not in rendered_content

        assert "Current Metrics:" in rendered_content
        assert "Response Time P95: 1250ms" in rendered_content
        assert "Error Rate: 2.3%" in rendered_content
        assert "Throughput: 450 rpm" in rendered_content

        assert "Recommendations:" in rendered_content
        assert "1. Increase server capacity" in rendered_content
        assert "2. Optimize database queries" in rendered_content
        assert "3. Implement caching layer" in rendered_content

    def test_template_error_handling(self, notification_sender):
        """Test template error handling and validation."""
        error_scenarios = [
            {
                "template_content": "Hello {{undefined_variable}}",
                "variables": {},
                "expected_error": "undefined_variable"
            },
            {
                "template_content": "Count: {{count + 1}}",  # Invalid expression
                "variables": {"count": 5},
                "expected_error": "template_syntax"
            },
            {
                "template_content": "{% for item in undefined_list %}Item{% endfor %}",
                "variables": {},
                "expected_error": "undefined_variable"
            },
            {
                "template_content": "Valid template with {{valid_var}}",
                "variables": {"valid_var": "value"},
                "expected_error": None
            }
        ]

        for scenario in error_scenarios:
            rendering_result = notification_sender.render_notification_template(scenario)

            if scenario["expected_error"]:
                assert rendering_result["rendering_success"] is False
                assert "rendering_error" in rendering_result
                assert scenario["expected_error"] in rendering_result["rendering_error"]
            else:
                assert rendering_result["rendering_success"] is True
                assert "rendered_content" in rendering_result

    def test_template_performance_optimization(self, notification_sender):
        """Test template performance optimization."""
        performance_test = {
            "template_content": """
            {% for i in range(100) %}
            Item {{i}}: {{data[i]}}
            {% endfor %}
            """,
            "variables": {"data": [f"value_{i}" for i in range(100)]},
            "optimization_settings": {
                "enable_caching": True,
                "precompile_template": True,
                "optimize_loops": True,
                "memory_limits": {"max_template_size_kb": 50}
            }
        }

        optimization_result = notification_sender.optimize_template_performance(performance_test)

        assert optimization_result["optimization_success"] is True
        assert "performance_metrics" in optimization_result
        assert "optimization_applied" in optimization_result

        metrics = optimization_result["performance_metrics"]
        assert "render_time_ms" in metrics
        assert "memory_usage_kb" in metrics
        assert "optimization_speedup" in metrics

        applied = optimization_result["optimization_applied"]
        assert applied["enable_caching"] is True
        assert applied["precompile_template"] is True

        # Should show performance improvement
        assert metrics["optimization_speedup"] > 1.0


class TestDeliveryTracking:
    """Test Delivery Tracking functionality."""

    @pytest.fixture
    def notification_sender(self, mock_delivery_tracker):
        """Create notification sender instance."""
        return NotificationSender(delivery_tracker=mock_delivery_tracker)

    def test_delivery_attempt_tracking(self, notification_sender):
        """Test delivery attempt tracking and logging."""
        delivery_attempt = {
            "attempt_id": str(uuid.uuid4()),
            "notification_id": str(uuid.uuid4()),
            "channel": "email",
            "target": "platform@company.com",
            "content": {
                "subject": "Service Alert",
                "body": "Service is experiencing issues"
            },
            "metadata": {
                "priority": "high",
                "event_id": str(uuid.uuid4()),
                "correlation_id": str(uuid.uuid4())
            }
        }

        tracking_result = notification_sender.track_delivery_attempt(delivery_attempt)

        assert tracking_result["tracking_success"] is True
        assert "tracking_id" in tracking_result
        assert "initial_status" in tracking_result

        # Should generate tracking ID if not provided
        assert tracking_result["tracking_id"] is not None

        initial_status = tracking_result["initial_status"]
        assert initial_status["status"] == "attempting"
        assert "timestamp" in initial_status
        assert initial_status["channel"] == delivery_attempt["channel"]

    def test_delivery_status_updates(self, notification_sender):
        """Test delivery status updates and transitions."""
        delivery_id = str(uuid.uuid4())

        status_updates = [
            {
                "status": "sent",
                "timestamp": datetime.now(),
                "channel_response": {"message_id": "msg_123", "queued": True},
                "delivery_metadata": {"smtp_server": "smtp.company.com", "response_time_ms": 245}
            },
            {
                "status": "delivered",
                "timestamp": datetime.now() + timedelta(seconds=2),
                "channel_response": {"delivered": True, "delivery_time_ms": 2340},
                "delivery_metadata": {"confirmation_received": True}
            }
        ]

        for update in status_updates:
            update_result = notification_sender.update_delivery_status(delivery_id, update)

            assert update_result["update_success"] is True
            assert "status_transition" in update_result
            assert "updated_record" in update_result

            transition = update_result["status_transition"]
            assert "from_status" in transition
            assert "to_status" in transition
            assert transition["to_status"] == update["status"]

            updated_record = update_result["updated_record"]
            assert updated_record["status"] == update["status"]
            assert updated_record["last_updated"] >= update["timestamp"]

    def test_delivery_failure_analysis(self, notification_sender):
        """Test delivery failure analysis and diagnostics."""
        failure_scenarios = [
            {
                "failure_type": "smtp_connection_timeout",
                "error_details": {
                    "error_code": "ETIMEDOUT",
                    "error_message": "Connection timed out",
                    "smtp_server": "smtp.company.com",
                    "port": 587,
                    "timeout_seconds": 30
                },
                "expected_root_cause": "network_connectivity",
                "expected_solution": "retry_with_backoff"
            },
            {
                "failure_type": "invalid_recipient",
                "error_details": {
                    "error_code": "550",
                    "error_message": "Mailbox does not exist",
                    "recipient": "invalid@company.com"
                },
                "expected_root_cause": "recipient_validation",
                "expected_solution": "remove_invalid_recipient"
            },
            {
                "failure_type": "rate_limit_exceeded",
                "error_details": {
                    "error_code": "429",
                    "error_message": "Too many requests",
                    "retry_after_seconds": 300,
                    "channel": "slack"
                },
                "expected_root_cause": "rate_limiting",
                "expected_solution": "exponential_backoff"
            },
            {
                "failure_type": "authentication_failure",
                "error_details": {
                    "error_code": "401",
                    "error_message": "Invalid credentials",
                    "channel": "pagerduty"
                },
                "expected_root_cause": "authentication_issue",
                "expected_solution": "refresh_credentials"
            }
        ]

        for scenario in failure_scenarios:
            analysis_result = notification_sender.analyze_delivery_failure(scenario)

            assert analysis_result["analysis_success"] is True
            assert "root_cause_analysis" in analysis_result
            assert "recommended_actions" in analysis_result
            assert "failure_classification" in analysis_result

            root_cause = analysis_result["root_cause_analysis"]
            assert root_cause["identified_root_cause"] == scenario["expected_root_cause"]
            assert "confidence_score" in root_cause
            assert root_cause["confidence_score"] >= 0.7

            recommended_actions = analysis_result["recommended_actions"]
            assert len(recommended_actions) > 0

            # Should include expected solution
            action_types = [action["action_type"] for action in recommended_actions]
            assert scenario["expected_solution"] in action_types

            classification = analysis_result["failure_classification"]
            assert "failure_category" in classification
            assert "severity" in classification
            assert "retry_eligible" in classification

    def test_delivery_performance_metrics(self, notification_sender):
        """Test delivery performance metrics calculation."""
        performance_data = {
            "time_window": {
                "start": datetime.now() - timedelta(hours=24),
                "end": datetime.now()
            },
            "delivery_stats": {
                "total_attempts": 15420,
                "successful_deliveries": 14850,
                "failed_deliveries": 570,
                "average_delivery_time_ms": 234,
                "median_delivery_time_ms": 198,
                "p95_delivery_time_ms": 850,
                "p99_delivery_time_ms": 1450
            },
            "channel_breakdown": {
                "email": {
                    "attempts": 8921,
                    "success_rate": 0.981,
                    "avg_delivery_time_ms": 245
                },
                "slack": {
                    "attempts": 4123,
                    "success_rate": 0.945,
                    "avg_delivery_time_ms": 156
                },
                "sms": {
                    "attempts": 1234,
                    "success_rate": 0.923,
                    "avg_delivery_time_ms": 189
                },
                "pagerduty": {
                    "attempts": 1142,
                    "success_rate": 0.997,
                    "avg_delivery_time_ms": 234
                }
            },
            "failure_analysis": {
                "top_failure_reasons": [
                    {"reason": "rate_limit", "count": 234, "percentage": 41.1},
                    {"reason": "invalid_recipient", "count": 156, "percentage": 27.4},
                    {"reason": "network_timeout", "count": 98, "percentage": 17.2},
                    {"reason": "authentication_failure", "count": 82, "percentage": 14.4}
                ]
            }
        }

        metrics_result = notification_sender.calculate_delivery_performance_metrics(performance_data)

        assert metrics_result["calculation_success"] is True
        assert "overall_metrics" in metrics_result
        assert "channel_performance" in metrics_result
        assert "performance_trends" in metrics_result
        assert "efficiency_analysis" in metrics_result

        overall_metrics = metrics_result["overall_metrics"]
        assert "delivery_success_rate" in overall_metrics
        assert "average_delivery_time_ms" in overall_metrics
        assert "throughput_deliveries_per_hour" in overall_metrics

        # Should calculate correct success rate
        expected_success_rate = performance_data["delivery_stats"]["successful_deliveries"] / performance_data["delivery_stats"]["total_attempts"]
        assert abs(overall_metrics["delivery_success_rate"] - expected_success_rate) < 0.001

        channel_performance = metrics_result["channel_performance"]
        assert len(channel_performance) == len(performance_data["channel_breakdown"])

        for channel_name, channel_data in performance_data["channel_breakdown"].items():
            assert channel_name in channel_performance
            channel_metrics = channel_performance[channel_name]
            assert channel_metrics["success_rate"] == channel_data["success_rate"]
            assert channel_metrics["avg_delivery_time_ms"] == channel_data["avg_delivery_time_ms"]

        efficiency_analysis = metrics_result["efficiency_analysis"]
        assert "bottlenecks_identified" in efficiency_analysis
        assert "optimization_opportunities" in efficiency_analysis

        # Should identify email as having the slowest delivery time
        bottlenecks = efficiency_analysis["bottlenecks_identified"]
        assert len(bottlenecks) > 0


class TestRetryLogicAndFailureHandling:
    """Test Retry Logic and Failure Handling functionality."""

    @pytest.fixture
    def notification_sender(self):
        """Create notification sender instance."""
        return NotificationSender()

    def test_retry_policy_configuration(self, notification_sender):
        """Test retry policy configuration and validation."""
        retry_policies = [
            {
                "policy_name": "immediate_retry",
                "max_attempts": 3,
                "base_delay_seconds": 1,
                "backoff_multiplier": 1.0,  # No backoff
                "max_delay_seconds": 10,
                "retryable_errors": ["connection_timeout", "temporary_failure"],
                "expected_valid": True
            },
            {
                "policy_name": "exponential_backoff",
                "max_attempts": 5,
                "base_delay_seconds": 2,
                "backoff_multiplier": 2.0,
                "max_delay_seconds": 300,
                "retryable_errors": ["rate_limit", "service_unavailable"],
                "expected_valid": True
            },
            {
                "policy_name": "invalid_policy",
                "max_attempts": 0,  # Invalid
                "base_delay_seconds": 1,
                "backoff_multiplier": 2.0,
                "max_delay_seconds": 300,
                "retryable_errors": ["rate_limit"],
                "expected_valid": False
            },
            {
                "policy_name": "immediate_only",
                "max_attempts": 1,  # No retries
                "base_delay_seconds": 0,
                "backoff_multiplier": 1.0,
                "max_delay_seconds": 0,
                "retryable_errors": [],
                "expected_valid": True
            }
        ]

        for policy in retry_policies:
            validation_result = notification_sender.validate_retry_policy(policy)

            assert validation_result["validation_performed"] is True
            assert validation_result["is_valid"] == policy["expected_valid"]

            if policy["expected_valid"]:
                assert len(validation_result["validation_errors"]) == 0
                assert "policy_characteristics" in validation_result

                characteristics = validation_result["policy_characteristics"]
                assert "estimated_max_duration_seconds" in characteristics
                assert "aggressiveness_level" in characteristics
            else:
                assert len(validation_result["validation_errors"]) > 0

    def test_retry_execution_logic(self, notification_sender):
        """Test retry execution logic and timing."""
        retry_scenario = {
            "delivery_id": str(uuid.uuid4()),
            "retry_policy": {
                "max_attempts": 3,
                "base_delay_seconds": 2,
                "backoff_multiplier": 2.0,
                "max_delay_seconds": 60,
                "retryable_errors": ["connection_timeout", "rate_limit"]
            },
            "failure_history": [
                {
                    "attempt": 1,
                    "timestamp": datetime.now() - timedelta(minutes=5),
                    "error": "connection_timeout",
                    "retry_eligible": True
                },
                {
                    "attempt": 2,
                    "timestamp": datetime.now() - timedelta(minutes=2),
                    "error": "rate_limit",
                    "retry_eligible": True
                }
            ],
            "current_attempt": 2
        }

        retry_execution = notification_sender.execute_retry_logic(retry_scenario)

        assert retry_execution["retry_logic_executed"] is True
        assert "retry_decision" in retry_execution
        assert "next_attempt_schedule" in retry_execution

        retry_decision = retry_execution["retry_decision"]
        assert retry_decision["should_retry"] is True  # Still within max_attempts
        assert retry_decision["remaining_attempts"] == 1  # 3 max - 2 current = 1 remaining

        next_schedule = retry_execution["next_attempt_schedule"]
        assert "scheduled_time" in next_schedule
        assert "delay_seconds" in next_schedule

        # Should use exponential backoff: 2 * (2^1) = 4 seconds delay for attempt 2
        expected_delay = 2 * (2 ** (retry_scenario["current_attempt"] - 1))
        assert next_schedule["delay_seconds"] == expected_delay

        # Should schedule next attempt
        expected_next_time = retry_scenario["failure_history"][-1]["timestamp"] + timedelta(seconds=expected_delay)
        assert abs((next_schedule["scheduled_time"] - expected_next_time).total_seconds()) < 1

    def test_failure_pattern_recognition(self, notification_sender):
        """Test failure pattern recognition and adaptive retry strategies."""
        failure_patterns = [
            {
                "pattern_type": "intermittent_network_failures",
                "failure_sequence": ["connection_timeout", "success", "connection_timeout", "success"],
                "frequency": 0.5,  # 50% failure rate
                "expected_adaptation": "increase_timeout"
            },
            {
                "pattern_type": "rate_limit_cascading",
                "failure_sequence": ["rate_limit", "rate_limit", "rate_limit"],
                "frequency": 1.0,  # 100% failure rate
                "expected_adaptation": "exponential_backoff_increase"
            },
            {
                "pattern_type": "authentication_token_expiry",
                "failure_sequence": ["auth_failure", "auth_failure", "success"],
                "frequency": 0.67,  # 2 out of 3 failures
                "expected_adaptation": "token_refresh_retry"
            },
            {
                "pattern_type": "permanent_recipient_failure",
                "failure_sequence": ["invalid_recipient", "invalid_recipient", "invalid_recipient"],
                "frequency": 1.0,
                "expected_adaptation": "stop_retries"
            }
        ]

        for pattern in failure_patterns:
            pattern_recognition = notification_sender.recognize_failure_patterns(pattern)

            assert pattern_recognition["pattern_recognized"] is True
            assert "identified_pattern" in pattern_recognition
            assert "confidence_score" in pattern_recognition

            identified_pattern = pattern_recognition["identified_pattern"]
            assert identified_pattern["type"] == pattern["pattern_type"]
            assert identified_pattern["frequency"] == pattern["frequency"]

            assert "adaptive_strategy" in pattern_recognition
            adaptive_strategy = pattern_recognition["adaptive_strategy"]
            assert adaptive_strategy["recommended_action"] == pattern["expected_adaptation"]

            confidence = pattern_recognition["confidence_score"]
            assert 0.0 <= confidence <= 1.0
            assert confidence >= 0.7  # High confidence pattern recognition

    def test_circuit_breaker_pattern(self, notification_sender):
        """Test circuit breaker pattern implementation."""
        circuit_breaker_config = {
            "service_endpoint": "smtp.company.com:587",
            "failure_threshold": 5,
            "recovery_timeout_seconds": 300,
            "success_threshold": 3,
            "monitoring_window_seconds": 60
        }

        # Simulate circuit breaker states
        circuit_states = [
            {
                "state": "closed",
                "recent_failures": 2,
                "recent_successes": 8,
                "last_failure_time": datetime.now() - timedelta(minutes=30),
                "expected_allow_request": True
            },
            {
                "state": "open",
                "recent_failures": 6,
                "recent_successes": 1,
                "last_failure_time": datetime.now() - timedelta(minutes=2),
                "expected_allow_request": False
            },
            {
                "state": "half_open",
                "recent_failures": 5,
                "recent_successes": 2,
                "last_failure_time": datetime.now() - timedelta(minutes=10),
                "expected_allow_request": True  # Allow limited requests in half-open
            }
        ]

        for state_info in circuit_states:
            circuit_decision = notification_sender.evaluate_circuit_breaker(
                circuit_breaker_config,
                state_info
            )

            assert circuit_decision["evaluation_success"] is True
            assert "circuit_state" in circuit_decision
            assert "allow_request" in circuit_decision

            assert circuit_decision["circuit_state"] == state_info["state"]
            assert circuit_decision["allow_request"] == state_info["expected_allow_request"]

            if state_info["state"] == "open":
                assert "time_to_half_open" in circuit_decision
                expected_half_open_time = state_info["last_failure_time"] + timedelta(seconds=circuit_breaker_config["recovery_timeout_seconds"])
                assert circuit_decision["time_to_half_open"] == expected_half_open_time

    def test_dead_letter_queue_integration(self, notification_sender):
        """Test dead letter queue integration for permanent failures."""
        dlq_scenarios = [
            {
                "delivery_id": str(uuid.uuid4()),
                "failure_reason": "invalid_recipient",
                "retry_attempts": 3,
                "max_retries": 3,
                "error_pattern": "permanent_failure",
                "expected_dlq_action": "move_to_dlq"
            },
            {
                "delivery_id": str(uuid.uuid4()),
                "failure_reason": "connection_timeout",
                "retry_attempts": 2,
                "max_retries": 5,
                "error_pattern": "temporary_failure",
                "expected_dlq_action": "schedule_retry"
            },
            {
                "delivery_id": str(uuid.uuid4()),
                "failure_reason": "rate_limit",
                "retry_attempts": 5,
                "max_retries": 5,
                "error_pattern": "throttling_failure",
                "expected_dlq_action": "move_to_dlq_with_delay"
            }
        ]

        for scenario in dlq_scenarios:
            dlq_decision = notification_sender.evaluate_dlq_eligibility(scenario)

            assert dlq_decision["evaluation_success"] is True
            assert "dlq_action" in dlq_decision
            assert "action_reason" in dlq_decision

            assert dlq_decision["dlq_action"] == scenario["expected_dlq_action"]

            if scenario["expected_dlq_action"] == "move_to_dlq":
                assert "dlq_entry_prepared" in dlq_decision
                assert dlq_decision["dlq_entry_prepared"] is True

            elif scenario["expected_dlq_action"] == "schedule_retry":
                assert "retry_schedule" in dlq_decision
                retry_schedule = dlq_decision["retry_schedule"]
                assert "next_retry_time" in retry_schedule
                assert "retry_strategy" in retry_schedule

            elif scenario["expected_dlq_action"] == "move_to_dlq_with_delay":
                assert "dlq_entry_prepared" in dlq_decision
                assert "delayed_processing" in dlq_decision
                assert dlq_decision["delayed_processing"] is True
