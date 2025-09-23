"""End-to-End Integration Tests for Notification Service Workflows.

This module tests complete notification workflows from event ingestion through
delivery confirmation, including failure scenarios and recovery mechanisms.

Integration tests cover the full notification pipeline within the LLM Documentation Ecosystem.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from modules.notification_sender import NotificationSender
from modules.dlq_manager import DLQManager
from modules.owner_resolver import OwnerResolver


class TestCompleteNotificationWorkflow:
    """Test Complete Notification Workflow functionality."""

    @pytest.fixture
    def notification_service_components(self, mock_channel_providers, mock_template_engine):
        """Create complete notification service component set."""
        event_router = AsyncMock()
        event_router.route_event.return_value = {
            "routing_decision": "deliver",
            "target_owners": ["platform_team"],
            "channels": ["email", "slack"],
            "priority": "high"
        }

        owner_resolver = OwnerResolver()
        dlq_manager = DLQManager()

        notification_sender = NotificationSender(
            event_router=event_router,
            owner_resolver=owner_resolver,
            dlq_manager=dlq_manager,
            channel_providers=mock_channel_providers,
            template_engine=mock_template_engine
        )

        return {
            "notification_sender": notification_sender,
            "owner_resolver": owner_resolver,
            "dlq_manager": dlq_manager,
            "event_router": event_router
        }

    def test_successful_notification_delivery_workflow(self, notification_service_components):
        """Test successful end-to-end notification delivery workflow."""
        components = notification_service_components

        # Step 1: Event Ingestion
        notification_event = {
            "event_id": str(uuid.uuid4()),
            "event_type": "service_failure",
            "severity": "high",
            "source_service": "interpreter",
            "timestamp": datetime.now(),
            "title": "Document Interpreter Service Failure",
            "description": "The document interpreter service has become unresponsive",
            "details": {
                "error_code": "CONNECTION_TIMEOUT",
                "affected_components": ["api_endpoints", "document_processing"],
                "impact_assessment": "high"
            }
        }

        # Step 2: Event Classification and Enrichment
        enriched_event = components["notification_sender"].enrich_event(notification_event, {
            "system_status": {"overall_health": "degraded"},
            "business_context": {"customer_facing": True}
        })

        assert enriched_event["enrichment_applied"] is True
        assert enriched_event["adjusted_severity"] == "critical"  # Escalated

        # Step 3: Owner Resolution
        routing_decision = components["event_router"].route_event.return_value
        assert routing_decision["routing_decision"] == "deliver"

        # Step 4: Template Rendering
        template_rendering = components["notification_sender"].render_notification_template({
            "template_id": "service_failure_template",
            "template_content": "🚨 {{title}} - {{description}}",
            "variables": {
                "title": enriched_event["title"],
                "description": enriched_event["description"]
            }
        })

        assert template_rendering["rendering_success"] is True

        # Step 5: Multi-Channel Delivery
        delivery_result = components["notification_sender"].send_notification({
            "event_id": notification_event["event_id"],
            "rendered_content": template_rendering["rendered_content"],
            "routing_decision": routing_decision,
            "priority": "high"
        })

        assert delivery_result["delivery_success"] is True
        assert "delivery_confirmations" in delivery_result

        confirmations = delivery_result["delivery_confirmations"]
        assert len(confirmations) == 2  # email and slack

        for confirmation in confirmations:
            assert confirmation["status"] == "delivered"
            assert "delivery_time_ms" in confirmation

    def test_notification_workflow_with_failover(self, notification_service_components):
        """Test notification workflow with channel failover."""
        components = notification_service_components

        # Configure primary channel to fail
        components["notification_sender"].channel_providers["email"].send = AsyncMock(
            side_effect=Exception("SMTP server down")
        )
        components["notification_sender"].channel_providers["slack"].send = AsyncMock(
            return_value={"status": "delivered", "message_id": "slack_123"}
        )

        notification_event = {
            "event_id": str(uuid.uuid4()),
            "event_type": "performance_alert",
            "severity": "medium",
            "source_service": "api_gateway"
        }

        # Execute workflow with failover
        workflow_result = components["notification_sender"].send_notification_with_failover({
            "event": notification_event,
            "primary_channels": ["email"],
            "backup_channels": ["slack"],
            "max_retry_attempts": 1
        })

        assert workflow_result["workflow_success"] is True
        assert "failover_executed" in workflow_result
        assert workflow_result["failover_executed"] is True

        delivery_details = workflow_result["delivery_details"]
        assert delivery_details["final_channel"] == "slack"
        assert delivery_details["attempts_made"] == 2  # primary + backup
        assert delivery_details["final_status"] == "delivered"

    def test_notification_workflow_with_dlq_recovery(self, notification_service_components):
        """Test notification workflow with DLQ recovery."""
        components = notification_service_components

        # Configure all channels to fail initially
        for provider in components["notification_sender"].channel_providers.values():
            provider.send = AsyncMock(side_effect=Exception("Channel unavailable"))

        notification_event = {
            "event_id": str(uuid.uuid4()),
            "event_type": "security_incident",
            "severity": "critical",
            "source_service": "authentication"
        }

        # Step 1: Initial delivery attempt (should fail)
        initial_delivery = components["notification_sender"].send_notification({
            "event_id": notification_event["event_id"],
            "channels": ["email", "slack", "sms"],
            "content": {"alert": "Security incident detected"}
        })

        assert initial_delivery["delivery_success"] is False
        assert "failed_deliveries" in initial_delivery

        # Step 2: DLQ entry creation
        dlq_creation = components["dlq_manager"].create_dlq_entry({
            "original_event_id": notification_event["event_id"],
            "event_type": notification_event["event_type"],
            "failure_reason": "all_channels_failed",
            "original_payload": notification_event,
            "delivery_attempts": initial_delivery["failed_deliveries"]
        })

        assert dlq_creation["creation_success"] is True
        dlq_id = dlq_creation["dlq_entry"]["dlq_id"]

        # Step 3: Simulate channel recovery
        components["notification_sender"].channel_providers["email"].send = AsyncMock(
            return_value={"status": "delivered", "message_id": "email_123"}
        )

        # Step 4: DLQ retry execution
        retry_result = components["dlq_manager"].execute_dlq_retry(dlq_id, {
            "retry_channels": ["email"],
            "max_retry_attempts": 3,
            "retry_policy": "exponential_backoff"
        })

        assert retry_result["retry_success"] is True
        assert "final_delivery_status" in retry_result
        assert retry_result["final_delivery_status"] == "delivered"

        # Step 5: DLQ entry cleanup
        cleanup_result = components["dlq_manager"].cleanup_resolved_dlq_entry(dlq_id)
        assert cleanup_result["cleanup_success"] is True

    def test_high_volume_notification_processing(self, notification_service_components):
        """Test high-volume notification processing workflow."""
        components = notification_service_components

        # Generate high volume of notifications
        notification_batch = []
        for i in range(100):
            notification_batch.append({
                "event_id": str(uuid.uuid4()),
                "event_type": "metric_alert" if i % 2 == 0 else "service_health",
                "severity": "low" if i % 10 == 0 else "medium",
                "source_service": f"service_{i % 5}",
                "timestamp": datetime.now() - timedelta(seconds=i*10),
                "title": f"Alert {i}",
                "description": f"Test alert number {i}"
            })

        # Process batch with optimization
        batch_processing = components["notification_sender"].process_notification_batch({
            "notifications": notification_batch,
            "batch_config": {
                "max_concurrent_deliveries": 10,
                "batch_timeout_seconds": 300,
                "channel_prioritization": True,
                "priority_queueing": True
            }
        })

        assert batch_processing["batch_processing_success"] is True
        assert "processing_stats" in batch_processing
        assert "delivery_results" in batch_processing

        processing_stats = batch_processing["processing_stats"]
        assert processing_stats["total_notifications"] == 100
        assert "processing_time_seconds" in processing_stats
        assert "throughput_per_second" in processing_stats
        assert processing_stats["processing_time_seconds"] < 300  # Within timeout

        delivery_results = batch_processing["delivery_results"]
        assert len(delivery_results) == 100

        # Verify priority handling (low severity alerts should be processed)
        low_severity_results = [r for r in delivery_results if r["original_severity"] == "low"]
        medium_severity_results = [r for r in delivery_results if r["original_severity"] == "medium"]

        # All should be delivered
        assert all(r["status"] == "delivered" for r in delivery_results)

    def test_notification_workflow_with_escalation(self, notification_service_components):
        """Test notification workflow with escalation policies."""
        components = notification_service_components

        critical_event = {
            "event_id": str(uuid.uuid4()),
            "event_type": "data_breach",
            "severity": "critical",
            "source_service": "security_monitor",
            "timestamp": datetime.now(),
            "title": "Potential Data Breach Detected",
            "description": "Unauthorized access patterns detected in production database"
        }

        # Configure escalation policy
        escalation_config = {
            "escalation_required": True,
            "escalation_policy": {
                "immediate_acknowledgment_required": True,
                "maximum_response_time_minutes": 15,
                "escalation_levels": [
                    {
                        "delay_minutes": 0,
                        "contacts": ["security_team", "oncall_engineer"],
                        "channels": ["pagerduty", "sms", "phone"]
                    },
                    {
                        "delay_minutes": 5,
                        "contacts": ["security_lead", "platform_team"],
                        "channels": ["pagerduty", "email", "slack"]
                    },
                    {
                        "delay_minutes": 10,
                        "contacts": ["vp_security", "executive_team"],
                        "channels": ["pagerduty", "phone", "email"]
                    }
                ]
            }
        }

        # Execute escalation workflow
        escalation_result = components["notification_sender"].execute_escalation_workflow(
            critical_event, escalation_config
        )

        assert escalation_result["escalation_success"] is True
        assert "escalation_levels_executed" in escalation_result
        assert "acknowledgment_received" in escalation_result

        escalation_levels = escalation_result["escalation_levels_executed"]
        assert len(escalation_levels) >= 1

        # Should have immediate escalation for critical event
        immediate_level = next((level for level in escalation_levels if level["level"] == 1), None)
        assert immediate_level is not None
        assert immediate_level["executed_immediately"] is True

        acknowledgment = escalation_result["acknowledgment_received"]
        assert acknowledgment["acknowledged"] is True
        assert "acknowledgment_time_seconds" in acknowledgment
        assert acknowledgment["acknowledgment_time_seconds"] <= 900  # Within 15 minutes

    def test_notification_workflow_error_recovery(self, notification_service_components):
        """Test notification workflow error recovery and resilience."""
        components = notification_service_components

        # Simulate various failure scenarios
        failure_scenarios = [
            {
                "scenario": "template_rendering_failure",
                "event": {"event_type": "service_failure", "severity": "high"},
                "failure_point": "template_engine",
                "expected_recovery": "fallback_template"
            },
            {
                "scenario": "owner_resolution_failure",
                "event": {"event_type": "performance_alert", "severity": "medium"},
                "failure_point": "owner_resolver",
                "expected_recovery": "default_owner_fallback"
            },
            {
                "scenario": "routing_engine_failure",
                "event": {"event_type": "maintenance_notification", "severity": "low"},
                "failure_point": "event_router",
                "expected_recovery": "default_routing_rules"
            }
        ]

        for scenario in failure_scenarios:
            # Inject failure
            if scenario["failure_point"] == "template_engine":
                components["notification_sender"].template_engine.render_template = AsyncMock(
                    side_effect=Exception("Template rendering failed")
                )
            elif scenario["failure_point"] == "owner_resolver":
                components["owner_resolver"].resolve_owners = AsyncMock(
                    side_effect=Exception("Owner resolution failed")
                )
            elif scenario["failure_point"] == "event_router":
                components["event_router"].route_event = AsyncMock(
                    side_effect=Exception("Routing engine failed")
                )

            # Execute workflow with error recovery
            recovery_result = components["notification_sender"].execute_notification_workflow_with_recovery(
                scenario["event"]
            )

            assert recovery_result["workflow_completed"] is True
            assert "error_recovery_applied" in recovery_result
            assert recovery_result["error_recovery_applied"] is True

            recovery_details = recovery_result["recovery_details"]
            assert recovery_details["recovery_strategy"] == scenario["expected_recovery"]
            assert "fallback_applied" in recovery_details
            assert recovery_details["fallback_applied"] is True

            # Verify final delivery
            assert "final_delivery_status" in recovery_result
            assert recovery_result["final_delivery_status"] == "delivered"


class TestNotificationServiceIntegration:
    """Test Notification Service Integration functionality."""

    @pytest.fixture
    def integrated_notification_service(self, mock_channel_providers, mock_template_engine):
        """Create fully integrated notification service."""
        return NotificationSender(
            channel_providers=mock_channel_providers,
            template_engine=mock_template_engine,
            enable_integrations=True
        )

    def test_cross_service_notification_coordination(self, integrated_notification_service):
        """Test cross-service notification coordination."""
        # Simulate notifications from multiple services in the ecosystem
        ecosystem_events = [
            {
                "source_service": "interpreter",
                "event_type": "document_processing_failure",
                "severity": "high",
                "affected_users": 150,
                "business_impact": "customer_facing"
            },
            {
                "source_service": "doc_store",
                "event_type": "database_performance_degraded",
                "severity": "medium",
                "affected_users": 50,
                "business_impact": "internal"
            },
            {
                "source_service": "orchestrator",
                "event_type": "workflow_execution_timeout",
                "severity": "high",
                "affected_users": 25,
                "business_impact": "operational"
            },
            {
                "source_service": "llm_gateway",
                "event_type": "api_rate_limit_exceeded",
                "severity": "medium",
                "affected_users": 10,
                "business_impact": "development"
            }
        ]

        coordination_result = integrated_notification_service.coordinate_ecosystem_notifications(
            ecosystem_events
        )

        assert coordination_result["coordination_success"] is True
        assert "coordinated_notifications" in coordination_result
        assert "impact_assessment" in coordination_result

        coordinated_notifications = coordination_result["coordinated_notifications"]
        assert len(coordinated_notifications) == len(ecosystem_events)

        impact_assessment = coordination_result["impact_assessment"]
        assert "overall_ecosystem_impact" in impact_assessment
        assert "service_correlation" in impact_assessment
        assert "notification_prioritization" in impact_assessment

        # Should correlate related events
        correlation = impact_assessment["service_correlation"]
        assert correlation["correlated_events_found"] > 0

        # Should prioritize based on impact
        prioritization = impact_assessment["notification_prioritization"]
        high_impact_notifications = [n for n in prioritization if n["priority"] == "high"]
        assert len(high_impact_notifications) >= 2  # interpreter and orchestrator events

    def test_notification_service_health_monitoring(self, integrated_notification_service):
        """Test notification service health monitoring integration."""
        health_monitoring_data = {
            "service_components": {
                "event_router": {"status": "healthy", "response_time_ms": 45},
                "owner_resolver": {"status": "healthy", "response_time_ms": 32},
                "template_engine": {"status": "degraded", "response_time_ms": 120},
                "channel_providers": {
                    "email": {"status": "healthy", "connectivity": True},
                    "slack": {"status": "healthy", "connectivity": True},
                    "sms": {"status": "degraded", "connectivity": False}
                },
                "dlq_manager": {"status": "healthy", "queue_size": 25}
            },
            "performance_metrics": {
                "average_delivery_time_ms": 245,
                "delivery_success_rate": 0.967,
                "queue_processing_rate": 150,  # notifications per minute
                "error_rate": 0.033
            },
            "external_dependencies": {
                "smtp_server": {"status": "healthy", "latency_ms": 89},
                "slack_api": {"status": "healthy", "latency_ms": 156},
                "sms_gateway": {"status": "degraded", "latency_ms": 500},
                "pagerduty_api": {"status": "healthy", "latency_ms": 234}
            }
        }

        health_monitoring = integrated_notification_service.monitor_service_health(health_monitoring_data)

        assert health_monitoring["monitoring_success"] is True
        assert "overall_health_status" in health_monitoring
        assert "component_health_details" in health_monitoring
        assert "performance_assessment" in health_monitoring

        overall_health = health_monitoring["overall_health_status"]
        assert overall_health["status"] == "degraded"  # Due to template engine and SMS issues

        component_details = health_monitoring["component_health_details"]
        assert len(component_details) == len(health_monitoring_data["service_components"])

        # Should identify degraded components
        degraded_components = [comp for comp in component_details if comp["status"] == "degraded"]
        assert len(degraded_components) >= 2  # template_engine and SMS

        performance_assessment = health_monitoring["performance_assessment"]
        assert "performance_score" in performance_assessment
        assert "bottlenecks_identified" in performance_assessment
        assert performance_assessment["performance_score"] >= 0.8  # Still good despite issues

    def test_notification_service_load_balancing(self, integrated_notification_service):
        """Test notification service load balancing across instances."""
        load_balancing_scenario = {
            "service_instances": [
                {
                    "instance_id": "notification-01",
                    "current_load": 0.7,  # 70% capacity
                    "capacity_notifications_per_minute": 200,
                    "active_channels": ["email", "slack"],
                    "health_status": "healthy"
                },
                {
                    "instance_id": "notification-02",
                    "current_load": 0.3,  # 30% capacity
                    "capacity_notifications_per_minute": 200,
                    "active_channels": ["email", "slack", "sms"],
                    "health_status": "healthy"
                },
                {
                    "instance_id": "notification-03",
                    "current_load": 0.9,  # 90% capacity
                    "capacity_notifications_per_minute": 200,
                    "active_channels": ["email"],
                    "health_status": "healthy"
                }
            ],
            "incoming_notifications": [
                {"event_type": "service_failure", "channels": ["email", "slack"], "priority": "high"},
                {"event_type": "performance_alert", "channels": ["slack"], "priority": "medium"},
                {"event_type": "maintenance", "channels": ["email"], "priority": "low"},
                {"event_type": "security_event", "channels": ["email", "sms"], "priority": "critical"}
            ]
        }

        load_balancing = integrated_notification_service.balance_service_load(load_balancing_scenario)

        assert load_balancing["balancing_success"] is True
        assert "load_distribution" in load_balancing
        assert "instance_utilization" in load_balancing
        assert "routing_decisions" in load_balancing

        load_distribution = load_balancing["load_distribution"]
        assert len(load_distribution) == len(load_balancing_scenario["service_instances"])

        instance_utilization = load_balancing["instance_utilization"]
        assert "before_balancing" in instance_utilization
        assert "after_balancing" in instance_utilization

        # Should distribute load more evenly
        before_loads = [inst["current_load"] for inst in load_balancing_scenario["service_instances"]]
        after_loads = [dist["final_load"] for dist in load_distribution]

        before_variance = max(before_loads) - min(before_loads)
        after_variance = max(after_loads) - min(after_loads)

        assert after_variance <= before_variance  # More balanced

        routing_decisions = load_balancing["routing_decisions"]
        assert len(routing_decisions) == len(load_balancing_scenario["incoming_notifications"])

        # Critical notifications should go to least loaded instance with required channels
        critical_decision = next(dec for dec in routing_decisions if dec["notification_priority"] == "critical")
        assert critical_decision["assigned_instance"] == "notification-02"  # Has SMS capability and lower load

    def test_notification_service_auto_scaling(self, integrated_notification_service):
        """Test notification service auto-scaling based on load."""
        scaling_scenario = {
            "current_load_metrics": {
                "total_notifications_per_minute": 450,
                "average_delivery_time_ms": 350,
                "queue_depth": 120,
                "error_rate": 0.05,
                "channel_utilization": {
                    "email": 0.85,
                    "slack": 0.75,
                    "sms": 0.60
                }
            },
            "scaling_configuration": {
                "min_instances": 2,
                "max_instances": 10,
                "scale_up_threshold_notifications_per_minute": 300,
                "scale_down_threshold_notifications_per_minute": 100,
                "cooldown_period_minutes": 5,
                "instance_capacity_notifications_per_minute": 200
            },
            "infrastructure_limits": {
                "available_instances": 8,
                "cost_budget_per_hour": 50,
                "resource_limits": {
                    "cpu_cores_available": 32,
                    "memory_gb_available": 128
                }
            },
            "scaling_history": [
                {"timestamp": datetime.now() - timedelta(minutes=30), "instances": 3, "load": 0.6},
                {"timestamp": datetime.now() - timedelta(minutes=15), "instances": 4, "load": 0.75},
                {"timestamp": datetime.now() - timedelta(minutes=5), "instances": 4, "load": 0.85}
            ]
        }

        auto_scaling = integrated_notification_service.execute_auto_scaling(scaling_scenario)

        assert auto_scaling["scaling_success"] is True
        assert "scaling_decision" in auto_scaling
        assert "capacity_projections" in auto_scaling
        assert "cost_impact" in auto_scaling

        scaling_decision = auto_scaling["scaling_decision"]
        assert "scale_direction" in scaling_decision
        assert "target_instance_count" in scaling_decision
        assert "scaling_reason" in scaling_decision

        # Should recommend scaling up due to high load (450 > 300 threshold)
        assert scaling_decision["scale_direction"] == "up"
        assert scaling_decision["target_instance_count"] > 4  # Current is 4

        capacity_projections = auto_scaling["capacity_projections"]
        assert "projected_capacity_notifications_per_minute" in capacity_projections
        assert "estimated_delivery_time_ms" in capacity_projections

        # Projected capacity should handle current load
        assert capacity_projections["projected_capacity_notifications_per_minute"] >= 450

        cost_impact = auto_scaling["cost_impact"]
        assert "estimated_hourly_cost" in cost_impact
        assert "cost_efficiency_score" in cost_impact
        assert cost_impact["estimated_hourly_cost"] <= scaling_scenario["infrastructure_limits"]["cost_budget_per_hour"]


class TestNotificationServiceChaosEngineering:
    """Test Notification Service Chaos Engineering functionality."""

    @pytest.fixture
    def chaos_notification_service(self, mock_channel_providers):
        """Create notification service for chaos testing."""
        return NotificationSender(
            channel_providers=mock_channel_providers,
            enable_chaos_testing=True
        )

    def test_channel_failure_chaos_scenario(self, chaos_notification_service):
        """Test chaos scenario with channel failures."""
        chaos_experiment = {
            "experiment_name": "channel_failure_chaos",
            "duration_minutes": 10,
            "failure_injection": {
                "email_channel": {
                    "failure_mode": "complete_outage",
                    "duration_seconds": 300,
                    "failure_rate": 1.0
                },
                "slack_channel": {
                    "failure_mode": "intermittent",
                    "duration_seconds": 600,
                    "failure_rate": 0.3
                }
            },
            "notification_load": {
                "rate_per_second": 5,
                "total_notifications": 3000,
                "event_types": ["service_failure", "performance_alert", "maintenance"]
            },
            "monitoring": {
                "metrics": ["delivery_success_rate", "average_delivery_time", "dlq_queue_size"],
                "alerts": ["delivery_success_rate < 80%", "dlq_queue_size > 100"]
            }
        }

        chaos_result = chaos_notification_service.execute_chaos_experiment(chaos_experiment)

        assert chaos_result["experiment_completed"] is True
        assert "chaos_impact_assessment" in chaos_result
        assert "system_resilience_measures" in chaos_result
        assert "failure_recovery_analysis" in chaos_result

        impact_assessment = chaos_result["chaos_impact_assessment"]
        assert "delivery_success_rate_during_chaos" in impact_assessment
        assert "dlq_growth_rate" in impact_assessment
        assert "channel_failover_effectiveness" in impact_assessment

        # Should show impact of email channel failure
        assert impact_assessment["delivery_success_rate_during_chaos"] < 1.0

        resilience_measures = chaos_result["system_resilience_measures"]
        assert "automatic_failover_activated" in resilience_measures
        assert "load_balancing_adjusted" in resilience_measures
        assert resilience_measures["automatic_failover_activated"] is True

        recovery_analysis = chaos_result["failure_recovery_analysis"]
        assert "recovery_time_seconds" in recovery_analysis
        assert "data_loss_during_failure" in recovery_analysis
        assert recovery_analysis["data_loss_during_failure"] == 0  # Should preserve all notifications

    def test_dlq_overflow_chaos_scenario(self, chaos_notification_service):
        """Test chaos scenario with DLQ overflow."""
        chaos_experiment = {
            "experiment_name": "dlq_overflow_chaos",
            "duration_minutes": 15,
            "failure_injection": {
                "all_channels": {
                    "failure_mode": "complete_outage",
                    "duration_seconds": 600,
                    "failure_rate": 1.0
                },
                "dlq_capacity": {
                    "overflow_mode": "reject_new_entries",
                    "capacity_limit": 100,
                    "overflow_behavior": "drop_oldest"
                }
            },
            "notification_load": {
                "rate_per_second": 10,
                "total_notifications": 9000,
                "event_types": ["critical_failure"] * 9000  # All critical to force DLQ
            },
            "dlq_configuration": {
                "max_entries": 100,
                "retention_hours": 24,
                "overflow_policy": "lru_eviction"
            }
        }

        chaos_result = chaos_notification_service.execute_dlq_overflow_chaos(chaos_experiment)

        assert chaos_result["experiment_completed"] is True
        assert "dlq_overflow_impact" in chaos_result
        assert "capacity_management_effectiveness" in chaos_result
        assert "data_loss_analysis" in chaos_result

        overflow_impact = chaos_result["dlq_overflow_impact"]
        assert "entries_dropped" in overflow_impact
        assert "overflow_events_detected" in overflow_impact
        assert overflow_impact["overflow_events_detected"] > 0

        capacity_management = chaos_result["capacity_management_effectiveness"]
        assert "eviction_policy_executed" in capacity_management
        assert "capacity_utilization_max" in capacity_management
        assert capacity_management["capacity_utilization_max"] == 1.0

        data_loss_analysis = chaos_result["data_loss_analysis"]
        assert "notifications_lost" in data_loss_analysis
        assert "data_loss_percentage" in data_loss_analysis
        assert "recovery_options_evaluated" in data_loss_analysis

        # Should have lost some notifications due to capacity limits
        assert data_loss_analysis["notifications_lost"] > 0
        assert data_loss_analysis["data_loss_percentage"] <= 0.5  # Should not lose more than 50%

    def test_owner_resolution_failure_chaos_scenario(self, chaos_notification_service):
        """Test chaos scenario with owner resolution failures."""
        chaos_experiment = {
            "experiment_name": "owner_resolution_chaos",
            "duration_minutes": 8,
            "failure_injection": {
                "owner_resolver": {
                    "failure_mode": "service_unavailable",
                    "duration_seconds": 240,
                    "failure_rate": 1.0
                },
                "fallback_owner_resolution": {
                    "enabled": True,
                    "default_owners": ["platform_team", "oncall_engineer"],
                    "fallback_effectiveness": 0.9
                }
            },
            "notification_load": {
                "rate_per_second": 3,
                "total_notifications": 1440,
                "event_types": ["service_failure", "performance_alert", "security_event"]
            },
            "owner_resolution_config": {
                "resolution_timeout_seconds": 30,
                "fallback_enabled": True,
                "default_owner_groups": ["platform_team", "security_team", "devops"]
            }
        }

        chaos_result = chaos_notification_service.execute_owner_resolution_chaos(chaos_experiment)

        assert chaos_result["experiment_completed"] is True
        assert "owner_resolution_impact" in chaos_result
        assert "fallback_mechanism_effectiveness" in chaos_result
        assert "notification_routing_during_failure" in chaos_result

        resolution_impact = chaos_result["owner_resolution_impact"]
        assert "resolution_failure_rate" in resolution_impact
        assert "undelivered_notifications" in resolution_impact
        assert resolution_impact["resolution_failure_rate"] == 1.0  # Complete failure injected

        fallback_effectiveness = chaos_result["fallback_mechanism_effectiveness"]
        assert "fallback_activated" in fallback_effectiveness
        assert "fallback_success_rate" in fallback_effectiveness
        assert fallback_effectiveness["fallback_activated"] is True
        assert fallback_effectiveness["fallback_success_rate"] >= 0.8

        routing_during_failure = chaos_result["notification_routing_during_failure"]
        assert "default_routing_applied" in routing_during_failure
        assert "routing_success_rate" in routing_during_failure
        assert routing_during_failure["routing_success_rate"] >= 0.7  # Despite owner resolution failure

    def test_template_engine_failure_chaos_scenario(self, chaos_notification_service):
        """Test chaos scenario with template engine failures."""
        chaos_experiment = {
            "experiment_name": "template_engine_chaos",
            "duration_minutes": 12,
            "failure_injection": {
                "template_engine": {
                    "failure_mode": "rendering_errors",
                    "duration_seconds": 360,
                    "failure_rate": 0.4  # 40% of templates fail
                },
                "fallback_templates": {
                    "enabled": True,
                    "simple_templates": {
                        "service_failure": "🚨 Service {{service_name}} failed",
                        "performance_alert": "⚠️ Performance issue in {{service_name}}",
                        "security_event": "🔒 Security event in {{service_name}}"
                    }
                }
            },
            "notification_load": {
                "rate_per_second": 4,
                "total_notifications": 2880,
                "template_complexity": "mixed"  # Some simple, some complex
            },
            "template_configuration": {
                "template_timeout_seconds": 10,
                "fallback_enabled": True,
                "template_validation_enabled": True
            }
        }

        chaos_result = chaos_notification_service.execute_template_engine_chaos(chaos_experiment)

        assert chaos_result["experiment_completed"] is True
        assert "template_failure_impact" in chaos_result
        assert "fallback_template_effectiveness" in chaos_result
        assert "content_quality_during_failure" in chaos_result

        template_failure_impact = chaos_result["template_failure_impact"]
        assert "template_rendering_failure_rate" in template_failure_impact
        assert "notifications_with_fallback_content" in template_failure_impact
        assert template_failure_impact["template_rendering_failure_rate"] >= 0.3  # At least injected rate

        fallback_effectiveness = chaos_result["fallback_template_effectiveness"]
        assert "fallback_templates_used" in fallback_effectiveness
        assert "fallback_rendering_success_rate" in fallback_effectiveness
        assert fallback_effectiveness["fallback_templates_used"] > 0
        assert fallback_effectiveness["fallback_rendering_success_rate"] >= 0.9

        content_quality = chaos_result["content_quality_during_failure"]
        assert "content_completeness_score" in content_quality
        assert "information_preservation_rate" in content_quality
        assert content_quality["information_preservation_rate"] >= 0.7  # Should preserve most critical info
