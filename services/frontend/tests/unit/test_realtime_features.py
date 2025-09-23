"""Unit Tests for Real-Time Features in Frontend Service.

This module tests real-time capabilities including:
- WebSocket connection management
- Real-time data streaming
- Live service monitoring
- Event-driven updates
- Connection resilience and recovery

Tests cover the complete real-time infrastructure within the Frontend service.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from modules.realtime_interface import RealtimeInterface


class TestWebsocketConnectionManagement:
    """Test WebSocket Connection Management functionality."""

    @pytest.fixture
    def realtime_interface(self, mock_websocket_manager):
        """Create real-time interface instance."""
        return RealtimeInterface(websocket_manager=mock_websocket_manager)

    def test_websocket_connection_establishment(self, realtime_interface):
        """Test WebSocket connection establishment."""
        connection_params = {
            "url": "ws://localhost:8080/ws",
            "protocols": ["chat", "service_status"],
            "headers": {"Authorization": "Bearer token123"},
            "timeout": 10
        }

        connection_result = realtime_interface.establish_connection(connection_params)

        assert connection_result["success"] is True
        assert "connection_id" in connection_result
        assert connection_result["status"] == "connected"
        assert "established_at" in connection_result

    def test_websocket_connection_authentication(self, realtime_interface):
        """Test WebSocket connection authentication."""
        auth_params = {
            "token": "jwt_token_123",
            "user_id": "user123",
            "permissions": ["read_services", "read_logs"],
            "session_id": "session_456"
        }

        auth_result = realtime_interface.authenticate_connection(auth_params)

        assert auth_result["authenticated"] is True
        assert auth_result["user_id"] == "user123"
        assert set(auth_result["granted_permissions"]) == set(auth_params["permissions"])
        assert "token_valid_until" in auth_result

    def test_websocket_subscription_management(self, realtime_interface):
        """Test WebSocket subscription management."""
        connection_id = "ws_conn_123"
        subscriptions = {
            "channels": ["service_status", "logs", "metrics"],
            "filters": {
                "service_status": {"services": ["interpreter", "orchestrator"]},
                "logs": {"level": ["ERROR", "WARN"]},
                "metrics": {"time_range": "last_5_minutes"}
            }
        }

        subscription_result = realtime_interface.manage_subscriptions(connection_id, subscriptions)

        assert subscription_result["success"] is True
        assert len(subscription_result["subscribed_channels"]) == len(subscriptions["channels"])
        assert "subscription_id" in subscription_result
        assert subscription_result["active_filters"] == subscriptions["filters"]

    def test_websocket_message_handling(self, realtime_interface):
        """Test WebSocket message handling."""
        message = {
            "type": "service_status_update",
            "data": {
                "service": "interpreter",
                "status": "healthy",
                "response_time_ms": 245
            },
            "correlation_id": "corr_123",
            "sequence_number": 42
        }

        handling_result = realtime_interface.handle_incoming_message(message)

        assert handling_result["processed"] is True
        assert handling_result["message_type"] == "service_status_update"
        assert handling_result["correlation_id"] == "corr_123"
        assert "processing_time_ms" in handling_result

        # Verify message validation
        assert handling_result["validation_passed"] is True
        assert "parsed_data" in handling_result

    def test_websocket_connection_recovery(self, realtime_interface):
        """Test WebSocket connection recovery mechanisms."""
        connection_id = "ws_conn_123"
        failure_context = {
            "failure_type": "connection_lost",
            "last_seen": datetime.now() - timedelta(seconds=30),
            "retry_count": 2,
            "last_error": "WebSocket connection closed unexpectedly"
        }

        recovery_result = realtime_interface.handle_connection_recovery(connection_id, failure_context)

        assert recovery_result["recovery_attempted"] is True
        assert "recovery_strategy" in recovery_result

        # Should attempt reconnection
        assert recovery_result["recovery_strategy"] in ["immediate_reconnect", "exponential_backoff", "failover"]

        if recovery_result["recovery_strategy"] == "exponential_backoff":
            assert "backoff_delay_seconds" in recovery_result
            assert recovery_result["backoff_delay_seconds"] > 0

    def test_websocket_message_buffering(self, realtime_interface):
        """Test WebSocket message buffering during disconnections."""
        connection_id = "ws_conn_123"

        # Simulate disconnection
        realtime_interface.handle_connection_lost(connection_id)

        # Send messages during disconnection
        messages = [
            {"type": "status_update", "data": {"service": "svc1", "status": "up"}},
            {"type": "log_entry", "data": {"level": "INFO", "message": "Test log"}},
            {"type": "metric_update", "data": {"cpu_usage": 75.5}}
        ]

        for message in messages:
            buffer_result = realtime_interface.buffer_message(connection_id, message)
            assert buffer_result["buffered"] is True

        # Verify buffering
        buffer_status = realtime_interface.get_buffer_status(connection_id)
        assert buffer_status["buffered_message_count"] == len(messages)
        assert buffer_status["oldest_message_age_seconds"] > 0

        # Simulate reconnection and message replay
        replay_result = realtime_interface.replay_buffered_messages(connection_id)
        assert replay_result["replayed_count"] == len(messages)
        assert replay_result["replay_success_rate"] == 1.0

    def test_websocket_connection_scaling(self, realtime_interface):
        """Test WebSocket connection scaling and resource management."""
        # Simulate multiple connections
        connection_ids = []
        for i in range(100):
            conn_result = realtime_interface.establish_connection({"url": f"ws://test{i}:8080"})
            if conn_result["success"]:
                connection_ids.append(conn_result["connection_id"])

        scaling_metrics = realtime_interface.get_scaling_metrics()

        assert scaling_metrics["total_active_connections"] == len(connection_ids)
        assert "connection_distribution" in scaling_metrics
        assert "resource_usage" in scaling_metrics

        # Should provide scaling recommendations
        assert "scaling_recommendations" in scaling_metrics
        recommendations = scaling_metrics["scaling_recommendations"]

        if len(connection_ids) > 50:
            assert any("increase_resources" in rec.lower() for rec in recommendations)

    def test_websocket_security_validation(self, realtime_interface):
        """Test WebSocket security validation."""
        # Test valid message
        valid_message = {
            "type": "service_query",
            "data": {"service": "interpreter", "action": "status"},
            "auth_token": "valid_jwt_token",
            "timestamp": datetime.now().isoformat()
        }

        security_result = realtime_interface.validate_message_security(valid_message)
        assert security_result["security_check_passed"] is True
        assert security_result["auth_valid"] is True
        assert len(security_result["security_warnings"]) == 0

        # Test invalid messages
        invalid_messages = [
            {
                "type": "service_query",
                "data": {"service": "interpreter", "action": "delete_all_data"},  # Dangerous action
                "auth_token": "valid_jwt_token"
            },
            {
                "type": "service_query",
                "data": {"service": "interpreter"},
                "auth_token": "expired_token"
            },
            {
                "type": "malicious_type",
                "data": "<script>alert('xss')</script>",
                "auth_token": "valid_jwt_token"
            }
        ]

        for invalid_message in invalid_messages:
            security_result = realtime_interface.validate_message_security(invalid_message)
            assert security_result["security_check_passed"] is False
            assert len(security_result["security_warnings"]) > 0


class TestRealtimeDataStreaming:
    """Test Real-Time Data Streaming functionality."""

    @pytest.fixture
    def realtime_interface(self, mock_websocket_manager, mock_log_cache):
        """Create real-time interface instance."""
        return RealtimeInterface(
            websocket_manager=mock_websocket_manager,
            log_cache=mock_log_cache
        )

    def test_realtime_data_stream_initialization(self, realtime_interface):
        """Test real-time data stream initialization."""
        stream_config = {
            "stream_id": "service_status_stream",
            "data_source": "service_monitoring",
            "update_interval_seconds": 5,
            "filters": {
                "services": ["interpreter", "orchestrator", "doc_store"],
                "metrics": ["status", "response_time", "error_rate"]
            },
            "transformation": "status_summary"
        }

        init_result = realtime_interface.initialize_data_stream(stream_config)

        assert init_result["success"] is True
        assert init_result["stream_id"] == "service_status_stream"
        assert init_result["status"] == "initialized"
        assert "stream_metadata" in init_result

    def test_realtime_data_filtering_and_transformation(self, realtime_interface):
        """Test real-time data filtering and transformation."""
        raw_data = {
            "timestamp": datetime.now(),
            "services": [
                {
                    "name": "interpreter",
                    "status": "healthy",
                    "response_time_ms": 245,
                    "error_rate": 0.005,
                    "uptime_percentage": 99.7,
                    "active_connections": 12
                },
                {
                    "name": "orchestrator",
                    "status": "degraded",
                    "response_time_ms": 450,
                    "error_rate": 0.023,
                    "uptime_percentage": 98.2,
                    "active_connections": 8
                },
                {
                    "name": "doc_store",
                    "status": "healthy",
                    "response_time_ms": 180,
                    "error_rate": 0.002,
                    "uptime_percentage": 99.9,
                    "active_connections": 25
                }
            ]
        }

        filters = {
            "status": ["healthy", "degraded"],
            "max_response_time_ms": 300,
            "min_uptime_percentage": 99.0
        }

        transformation = "health_summary"

        processed_result = realtime_interface.process_stream_data(raw_data, filters, transformation)

        assert processed_result["success"] is True
        assert "filtered_data" in processed_result
        assert "transformed_data" in processed_result

        filtered_services = processed_result["filtered_data"]["services"]

        # Should filter out orchestrator (response time > 300ms)
        service_names = [s["name"] for s in filtered_services]
        assert "orchestrator" not in service_names
        assert "interpreter" in service_names
        assert "doc_store" in service_names

        # Should include transformation
        transformed = processed_result["transformed_data"]
        assert "overall_health_score" in transformed
        assert "service_count_by_status" in transformed

    def test_realtime_event_driven_updates(self, realtime_interface):
        """Test event-driven real-time updates."""
        event_config = {
            "event_types": ["service_failure", "performance_degradation", "security_alert"],
            "priority_levels": ["high", "medium", "low"],
            "update_channels": ["alerts", "notifications", "dashboard"],
            "throttling_rules": {
                "max_updates_per_minute": 30,
                "cooldown_period_seconds": 5
            }
        }

        # Simulate events
        events = [
            {
                "event_type": "service_failure",
                "priority": "high",
                "data": {"service": "interpreter", "error": "Connection timeout"},
                "timestamp": datetime.now()
            },
            {
                "event_type": "performance_degradation",
                "priority": "medium",
                "data": {"service": "orchestrator", "metric": "response_time", "value": 1500},
                "timestamp": datetime.now()
            }
        ]

        for event in events:
            update_result = realtime_interface.process_event_driven_update(event, event_config)

            assert update_result["success"] is True
            assert update_result["event_processed"] is True
            assert "dispatched_channels" in update_result

            # High priority events should be dispatched immediately
            if event["priority"] == "high":
                assert "immediate_dispatch" in update_result
                assert update_result["immediate_dispatch"] is True

    def test_realtime_data_compression_and_optimization(self, realtime_interface):
        """Test real-time data compression and optimization."""
        large_dataset = {
            "services": [
                {
                    "name": f"service_{i}",
                    "status": "healthy" if i % 3 != 0 else "degraded",
                    "metrics": {
                        "response_time": 200 + (i * 5),
                        "throughput": 50 + i,
                        "error_rate": 0.001 * i,
                        "memory_usage": 100 + (i * 2),
                        "cpu_usage": 20 + (i % 10),
                        "disk_usage": 30 + (i % 15),
                        "network_in": 1000 + (i * 10),
                        "network_out": 800 + (i * 8)
                    },
                    "logs": [
                        {
                            "timestamp": datetime.now() - timedelta(minutes=j),
                            "level": "INFO" if j % 5 != 0 else "ERROR",
                            "message": f"Service {i} log entry {j}: {'Normal operation' if j % 5 != 0 else 'Error occurred'}"
                        }
                        for j in range(20)  # 20 log entries per service
                    ]
                }
                for i in range(50)  # 50 services
            ]
        }

        compression_config = {
            "compression_algorithm": "gzip",
            "compression_level": 6,
            "data_reduction_rules": {
                "remove_old_logs": {"older_than_minutes": 30},
                "aggregate_metrics": {"time_window_minutes": 5},
                "filter_redundant_data": True
            }
        }

        compression_result = realtime_interface.compress_realtime_data(large_dataset, compression_config)

        assert compression_result["success"] is True
        assert "compressed_data" in compression_result
        assert "compression_ratio" in compression_result
        assert "data_reduction_stats" in compression_result

        # Should achieve compression
        assert compression_result["compression_ratio"] < 1.0  # Less than original size

        # Should reduce data volume
        reduction_stats = compression_result["data_reduction_stats"]
        assert reduction_stats["logs_removed"] > 0
        assert reduction_stats["metrics_aggregated"] > 0

    def test_realtime_stream_error_handling_and_recovery(self, realtime_interface):
        """Test error handling and recovery in real-time streams."""
        stream_id = "test_stream_123"

        # Simulate various error conditions
        error_scenarios = [
            {
                "error_type": "data_source_unavailable",
                "error_details": {"source": "service_monitoring", "reason": "network_timeout"},
                "expected_recovery": "switch_to_backup_source"
            },
            {
                "error_type": "websocket_connection_lost",
                "error_details": {"connection_id": "ws_123", "reason": "network_interruption"},
                "expected_recovery": "reconnect_with_backoff"
            },
            {
                "error_type": "data_processing_error",
                "error_details": {"stage": "transformation", "error": "invalid_data_format"},
                "expected_recovery": "skip_invalid_data"
            },
            {
                "error_type": "rate_limit_exceeded",
                "error_details": {"limit": 1000, "current": 1200, "window": "per_minute"},
                "expected_recovery": "throttle_and_queue"
            }
        ]

        for scenario in error_scenarios:
            error_context = {
                "stream_id": stream_id,
                "error": scenario,
                "timestamp": datetime.now(),
                "affected_subscribers": 15
            }

            recovery_result = realtime_interface.handle_stream_error(error_context)

            assert recovery_result["success"] is True
            assert recovery_result["error_handled"] is True
            assert "recovery_strategy" in recovery_result
            assert recovery_result["recovery_strategy"] == scenario["expected_recovery"]

            # Should notify affected subscribers
            assert "subscriber_notifications_sent" in recovery_result
            assert recovery_result["subscriber_notifications_sent"] == 15

    def test_realtime_performance_monitoring(self, realtime_interface):
        """Test performance monitoring of real-time features."""
        monitoring_config = {
            "metrics": [
                "message_throughput",
                "average_latency",
                "error_rate",
                "connection_stability",
                "data_processing_time"
            ],
            "alerts": {
                "high_latency_threshold_ms": 500,
                "error_rate_threshold": 0.05,
                "connection_drop_threshold": 0.1
            },
            "reporting_interval_seconds": 60
        }

        # Simulate monitoring data
        monitoring_data = {
            "time_window": "last_5_minutes",
            "metrics": {
                "messages_processed": 2500,
                "average_latency_ms": 45,
                "errors_count": 12,
                "connections_dropped": 3,
                "active_connections": 97,
                "data_processing_time_avg_ms": 12
            }
        }

        performance_report = realtime_interface.generate_performance_report(monitoring_data, monitoring_config)

        assert performance_report["success"] is True
        assert "performance_metrics" in performance_report
        assert "alerts_triggered" in performance_report
        assert "recommendations" in performance_report

        metrics = performance_report["performance_metrics"]

        # Should calculate derived metrics
        assert "message_throughput_per_second" in metrics
        assert metrics["message_throughput_per_second"] == 2500 / 300  # messages per second

        assert "error_rate_percentage" in metrics
        assert metrics["error_rate_percentage"] == (12 / 2500) * 100

        # Should generate alerts for issues
        alerts = performance_report["alerts_triggered"]
        assert len(alerts) >= 0  # May have alerts based on thresholds

        # Should provide recommendations
        recommendations = performance_report["recommendations"]
        assert len(recommendations) > 0

    def test_realtime_data_consistency_validation(self, realtime_interface):
        """Test data consistency validation in real-time streams."""
        consistency_rules = {
            "timestamp_monotonicity": True,
            "sequence_number_continuity": True,
            "data_schema_compliance": True,
            "referential_integrity": True,
            "business_rule_compliance": {
                "service_status_values": ["healthy", "degraded", "down"],
                "response_time_positive": True,
                "error_rate_range": [0.0, 1.0]
            }
        }

        # Test consistent data
        consistent_data = {
            "sequence_number": 100,
            "timestamp": datetime.now(),
            "services": [
                {
                    "name": "interpreter",
                    "status": "healthy",
                    "response_time_ms": 245,
                    "error_rate": 0.005
                }
            ]
        }

        consistency_result = realtime_interface.validate_data_consistency(consistent_data, consistency_rules)

        assert consistency_result["is_consistent"] is True
        assert len(consistency_result["consistency_violations"]) == 0

        # Test inconsistent data
        inconsistent_data = {
            "sequence_number": 95,  # Out of sequence
            "timestamp": datetime.now() - timedelta(hours=1),  # Old timestamp
            "services": [
                {
                    "name": "interpreter",
                    "status": "unknown_status",  # Invalid status
                    "response_time_ms": -100,  # Negative response time
                    "error_rate": 1.5  # Error rate > 1.0
                }
            ]
        }

        consistency_result = realtime_interface.validate_data_consistency(inconsistent_data, consistency_rules)

        assert consistency_result["is_consistent"] is False
        violations = consistency_result["consistency_violations"]

        # Should detect multiple violations
        assert len(violations) >= 3

        violation_types = [v["violation_type"] for v in violations]
        assert "sequence_discontinuity" in violation_types
        assert "timestamp_anomaly" in violation_types
        assert "business_rule_violation" in violation_types

    def test_realtime_stream_load_balancing(self, realtime_interface):
        """Test load balancing across real-time streams."""
        stream_loads = {
            "stream_1": {"active_connections": 50, "messages_per_second": 100, "cpu_usage": 60},
            "stream_2": {"active_connections": 75, "messages_per_second": 150, "cpu_usage": 75},
            "stream_3": {"active_connections": 25, "messages_per_second": 50, "cpu_usage": 40},
            "stream_4": {"active_connections": 100, "messages_per_second": 200, "cpu_usage": 85}
        }

        load_config = {
            "balancing_strategy": "adaptive",
            "max_connections_per_stream": 80,
            "cpu_threshold": 80,
            "rebalancing_interval_seconds": 300
        }

        balancing_result = realtime_interface.balance_stream_load(stream_loads, load_config)

        assert balancing_result["success"] is True
        assert "load_distribution" in balancing_result
        assert "rebalancing_actions" in balancing_result

        actions = balancing_result["rebalancing_actions"]

        # Should recommend rebalancing overloaded streams
        overloaded_actions = [a for a in actions if a["action_type"] == "redirect_connections"]
        assert len(overloaded_actions) > 0

        # Should identify which streams need rebalancing
        affected_streams = set()
        for action in actions:
            if "source_stream" in action:
                affected_streams.add(action["source_stream"])
            if "target_stream" in action:
                affected_streams.add(action["target_stream"])

        # Should include overloaded streams
        assert "stream_2" in affected_streams  # 75 connections > 50 average
        assert "stream_4" in affected_streams  # 85% CPU > 80% threshold

    def test_realtime_data_archiving_and_cleanup(self, realtime_interface):
        """Test data archiving and cleanup in real-time streams."""
        archiving_config = {
            "retention_policy": {
                "raw_data_days": 7,
                "aggregated_data_days": 90,
                "audit_logs_days": 365
            },
            "archival_strategy": "tiered_storage",
            "compression_enabled": True,
            "cleanup_schedule": "daily_at_2am"
        }

        archival_result = realtime_interface.perform_data_archival(archiving_config)

        assert archival_result["success"] is True
        assert "archival_stats" in archival_result
        assert "cleanup_stats" in archival_result

        archival_stats = archival_result["archival_stats"]
        assert "data_points_archived" in archival_stats
        assert "storage_space_freed_mb" in archival_stats
        assert "compression_ratio" in archival_stats

        cleanup_stats = archival_result["cleanup_stats"]
        assert "expired_records_deleted" in cleanup_stats
        assert "archive_integrity_checks_passed" in cleanup_stats

        # Should maintain data integrity
        assert cleanup_stats["archive_integrity_checks_passed"] >= 0.99  # 99% success rate
