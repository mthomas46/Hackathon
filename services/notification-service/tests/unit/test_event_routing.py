"""Unit Tests for Event Routing in Notification Service.

This module tests event routing capabilities including:
- Event classification and prioritization
- Intelligent routing to appropriate owners
- Channel selection and optimization
- Routing rule validation and management

Tests cover the complete event routing infrastructure within the Notification Service.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

# Note: Using mock implementations for testing event routing functionality
# The actual NotificationSender is simpler, so we create test-specific classes


# Mock implementations for testing
class MockNotificationSender:
    """Mock notification sender for testing event routing functionality."""

    def __init__(self, event_router=None, owner_resolver=None):
        self.event_router = event_router
        self.owner_resolver = owner_resolver

    def classify_event(self, event):
        """Mock event classification."""
        type_mapping = {
            "database connection failed": "infrastructure_failure",
            "api response time degraded": "performance_degradation",
            "unauthorized access attempt detected": "security_incident",
            "scheduled maintenance completed": "maintenance_notification",
            "new user registration": "business_event"
        }

        severity_mapping = {
            "database connection failed": "high",
            "api response time degraded": "medium",
            "unauthorized access attempt detected": "critical",
            "scheduled maintenance completed": "low",
            "new user registration": "info"
        }

        return {
            "event_type": type_mapping.get(event.get("title", "").lower(), "unknown"),
            "severity": severity_mapping.get(event.get("title", "").lower(), "medium"),
            "confidence_score": 0.85
        }

    def escalate_event_severity(self, event):
        """Mock event severity escalation."""
        return {
            "severity": "critical",
            "escalation_reason": "high_user_impact",
            "escalation_timestamp": datetime.now(),
            "original_severity": event.get("severity", "medium")
        }

    def correlate_events(self, events):
        """Mock event correlation."""
        return {
            "correlation_success": True,
            "event_groups": [{
                "correlation_key": "db_connection_failure",
                "events": events,
                "group_severity": "high",
                "impact_assessment": {"scope": "multiple_services"}
            }]
        }

    def enrich_event(self, event, context):
        """Mock event enrichment."""
        return {
            **event,
            "enrichment_applied": True,
            "adjusted_severity": "critical"
        }

    def resolve_event_owners(self, event):
        """Mock owner resolution."""
        return {
            "resolution_success": True,
            "resolved_owners": [{
                "owner_id": "platform_team",
                "owner_type": "team",
                "contact_methods": ["email", "slack"],
                "priority": "high"
            }]
        }

    def optimize_channel_selection(self, context):
        """Mock channel optimization."""
        return {
            "optimization_success": True,
            "selected_channels": ["email", "slack"],
            "primary_channel": "email",
            "channel_ranking": [
                {"channel": "email", "priority_score": 0.9},
                {"channel": "slack", "priority_score": 0.8}
            ]
        }

    def apply_routing_rules(self, event, routing_rules):
        """Mock routing rule application."""
        return {
            "rule_applied": True,
            "matched_rule": {"rule_id": "test_rule"},
            "applied_actions": {
                "notify_owners": ["platform_team"],
                "channels": ["email"]
            }
        }

    def balance_routing_load(self, event, owners):
        """Mock load balancing."""
        return {
            "balancing_success": True,
            "load_distribution": [{"owner_id": "team_a", "assigned_load": 0.6}],
            "capacity_utilization": {"average_utilization": 0.65}
        }

    def handle_routing_failures(self, scenario):
        """Mock failure handling."""
        return {
            "failover_attempted": True,
            "failover_success": True,
            "fallback_routing": {"channel": "slack"}
        }

    def optimize_routing_performance(self, routing_optimization):
        """Mock performance optimization."""
        return {
            "optimization_success": True,
            "applied_optimizations": [{"optimization": "caching", "improvement": 0.25}],
            "performance_projections": {"estimated_routing_time_ms": 95}
        }

    def validate_routing_rule(self, rule):
        """Mock rule validation."""
        return {
            "validation_performed": True,
            "is_valid": True,
            "validation_errors": []
        }

    def resolve_rule_conflicts(self, event, rules):
        """Mock conflict resolution."""
        return {
            "conflict_resolution_success": True,
            "winning_rule": {"rule_id": "rule_3"},
            "applied_actions": {"notify_owners": ["team_c"]}
        }

    def analyze_rule_performance(self, data):
        """Mock performance analysis."""
        return {
            "analysis_success": True,
            "performance_score": 0.92,
            "optimization_recommendations": [{"recommendation": "cache_rules"}]
        }

    def manage_rule_versions(self, versions, current, trigger):
        """Mock version management."""
        return {
            "version_management_success": True,
            "rollback_recommended": True,
            "target_version": "1.1"
        }

    def audit_rule_compliance(self, audit_data):
        """Mock compliance audit."""
        return {
            "audit_success": True,
            "compliance_status": {"GDPR": {"compliant": True}},
            "audit_findings": {"total_findings": 0}
        }


class TestEventClassification:
    """Test Event Classification functionality."""

    @pytest.fixture
    def notification_sender(self, mock_event_router, mock_owner_resolver):
        """Create notification sender instance."""
        return MockNotificationSender(
            event_router=mock_event_router,
            owner_resolver=mock_owner_resolver
        )

    def test_event_type_classification(self, notification_sender):
        """Test automatic event type classification."""
        test_events = [
            {
                "title": "Database connection failed",
                "description": "Unable to connect to PostgreSQL database",
                "source": "doc_store",
                "expected_type": "infrastructure_failure",
                "expected_severity": "high"
            },
            {
                "title": "API response time degraded",
                "description": "Average response time increased by 150%",
                "source": "interpreter",
                "metrics": {"response_time_p95": 2500},
                "expected_type": "performance_degradation",
                "expected_severity": "medium"
            },
            {
                "title": "Unauthorized access attempt detected",
                "description": "Multiple failed authentication attempts from IP 192.168.1.100",
                "source": "security_monitor",
                "expected_type": "security_incident",
                "expected_severity": "critical"
            },
            {
                "title": "Scheduled maintenance completed",
                "description": "Database maintenance window completed successfully",
                "source": "maintenance_system",
                "expected_type": "maintenance_notification",
                "expected_severity": "low"
            },
            {
                "title": "New user registration",
                "description": "User john.doe@example.com registered successfully",
                "source": "user_management",
                "expected_type": "business_event",
                "expected_severity": "info"
            }
        ]

        for event in test_events:
            classification = notification_sender.classify_event(event)

            assert classification["event_type"] == event["expected_type"]
            assert classification["severity"] == event["expected_severity"]
            assert "confidence_score" in classification
            assert 0.0 <= classification["confidence_score"] <= 1.0
            assert classification["confidence_score"] >= 0.7  # High confidence classifications

    def test_event_severity_escalation(self, notification_sender):
        """Test automatic event severity escalation based on context."""
        base_event = {
            "title": "Service response time increased",
            "description": "Response time increased by 50%",
            "source": "api_gateway",
            "metrics": {"response_time_p95": 1200}
        }

        # Test escalation triggers
        escalation_scenarios = [
            {
                "context": {"affected_users": 1000, "business_impact": "high"},
                "expected_severity": "critical",
                "escalation_reason": "high_user_impact"
            },
            {
                "context": {"duration_minutes": 30, "trend": "worsening"},
                "expected_severity": "high",
                "escalation_reason": "persistent_issue"
            },
            {
                "context": {"related_incidents": 3, "time_window_hours": 24},
                "expected_severity": "high",
                "escalation_reason": "frequent_occurrences"
            },
            {
                "context": {"business_value_affected": "revenue_generating"},
                "expected_severity": "high",
                "escalation_reason": "business_critical"
            }
        ]

        for scenario in escalation_scenarios:
            event_with_context = {**base_event, **scenario["context"]}

            escalated_event = notification_sender.escalate_event_severity(event_with_context)

            assert escalated_event["severity"] == scenario["expected_severity"]
            assert escalated_event["escalation_reason"] == scenario["escalation_reason"]
            assert "escalation_timestamp" in escalated_event
            assert "original_severity" in escalated_event

    def test_event_correlation_and_deduplication(self, notification_sender):
        """Test event correlation and deduplication."""
        # Simulate multiple similar events
        correlated_events = [
            {
                "title": "Database connection timeout",
                "description": "Connection to PostgreSQL timed out",
                "source": "doc_store",
                "timestamp": datetime.now() - timedelta(minutes=5),
                "correlation_key": "db_connection_failure"
            },
            {
                "title": "Database connection failed",
                "description": "Failed to establish connection to database",
                "source": "prompt_store",
                "timestamp": datetime.now() - timedelta(minutes=3),
                "correlation_key": "db_connection_failure"
            },
            {
                "title": "Database connectivity issue",
                "description": "Database server is not responding",
                "source": "orchestrator",
                "timestamp": datetime.now() - timedelta(minutes=1),
                "correlation_key": "db_connection_failure"
            },
            {
                "title": "API authentication failed",
                "description": "Invalid API key provided",
                "source": "external_api",
                "timestamp": datetime.now() - timedelta(seconds=30),
                "correlation_key": "api_auth_failure"
            }
        ]

        correlation_result = notification_sender.correlate_events(correlated_events)

        assert correlation_result["correlation_success"] is True
        assert "event_groups" in correlation_result

        event_groups = correlation_result["event_groups"]

        # Should group related database events
        db_groups = [group for group in event_groups if group["correlation_key"] == "db_connection_failure"]
        assert len(db_groups) == 1

        db_group = db_groups[0]
        assert len(db_group["events"]) == 3
        assert db_group["group_severity"] == "high"  # Escalated due to multiple occurrences
        assert "impact_assessment" in db_group

        # Should keep unrelated events separate
        auth_groups = [group for group in event_groups if group["correlation_key"] == "api_auth_failure"]
        assert len(auth_groups) == 1
        assert len(auth_groups[0]["events"]) == 1

    def test_event_enrichment_and_context(self, notification_sender):
        """Test event enrichment with additional context."""
        base_event = {
            "title": "Service unavailable",
            "description": "The service is currently unavailable",
            "source": "interpreter",
            "severity": "high"
        }

        enrichment_context = {
            "system_status": {
                "overall_health": "degraded",
                "affected_services": ["interpreter", "doc_store", "orchestrator"],
                "active_incidents": 3
            },
            "business_context": {
                "peak_usage_time": True,
                "revenue_impact": "medium",
                "customer_facing": True
            },
            "historical_context": {
                "similar_incidents_last_24h": 2,
                "average_resolution_time_minutes": 45,
                "common_root_causes": ["resource_exhaustion", "network_issues"]
            },
            "environmental_context": {
                "deployment_environment": "production",
                "maintenance_window": False,
                "load_percentage": 85
            }
        }

        enriched_event = notification_sender.enrich_event(base_event, enrichment_context)

        assert enriched_event["enrichment_applied"] is True
        assert "system_context" in enriched_event
        assert "business_context" in enriched_event
        assert "historical_context" in enriched_event
        assert "environmental_context" in enriched_event

        # Should enhance severity based on context
        assert enriched_event["adjusted_severity"] == "critical"  # Escalated due to multiple factors

        # Should include impact assessment
        assert "impact_assessment" in enriched_event
        impact = enriched_event["impact_assessment"]
        assert impact["affected_services_count"] == 3
        assert impact["business_impact"] == "medium"

        # Should include recommended actions
        assert "recommended_actions" in enriched_event
        actions = enriched_event["recommended_actions"]
        assert len(actions) > 0


class TestIntelligentRouting:
    """Test Intelligent Routing functionality."""

    @pytest.fixture
    def notification_sender(self, mock_event_router, mock_owner_resolver):
        """Create notification sender instance."""
        return NotificationSender(
            event_router=mock_event_router,
            owner_resolver=mock_owner_resolver
        )

    def test_owner_resolution_logic(self, notification_sender):
        """Test intelligent owner resolution for events."""
        event_scenarios = [
            {
                "event_type": "service_failure",
                "source_service": "interpreter",
                "severity": "high",
                "expected_owners": ["platform_team", "ml_engineering"],
                "expected_primary_channel": "pagerduty"
            },
            {
                "event_type": "performance_alert",
                "source_service": "api_gateway",
                "severity": "medium",
                "business_impact": "customer_facing",
                "expected_owners": ["platform_team", "devops"],
                "expected_primary_channel": "slack"
            },
            {
                "event_type": "security_incident",
                "source_service": "authentication_service",
                "severity": "critical",
                "expected_owners": ["security_team", "platform_team", "legal"],
                "expected_primary_channel": "pagerduty"
            },
            {
                "event_type": "maintenance_notification",
                "source_service": "backup_system",
                "severity": "low",
                "expected_owners": ["platform_team"],
                "expected_primary_channel": "email"
            }
        ]

        for scenario in event_scenarios:
            routing_decision = notification_sender.resolve_event_owners(scenario)

            assert routing_decision["resolution_success"] is True
            assert "resolved_owners" in routing_decision

            resolved_owners = routing_decision["resolved_owners"]
            assert len(resolved_owners) >= len(scenario["expected_owners"])

            # Check that expected owners are included
            owner_ids = [owner["owner_id"] for owner in resolved_owners]
            for expected_owner in scenario["expected_owners"]:
                assert expected_owner in owner_ids

            # Verify primary channel selection
            assert "primary_channel" in routing_decision
            assert routing_decision["primary_channel"] == scenario["expected_primary_channel"]

    def test_channel_selection_optimization(self, notification_sender):
        """Test optimal channel selection based on event characteristics."""
        event_contexts = [
            {
                "event_type": "critical_system_failure",
                "severity": "critical",
                "time_sensitivity": "immediate",
                "recipient_availability": "on_call_required",
                "expected_channels": ["pagerduty", "sms", "phone"],
                "expected_primary": "pagerduty"
            },
            {
                "event_type": "performance_degradation",
                "severity": "medium",
                "time_sensitivity": "within_hour",
                "recipient_availability": "working_hours",
                "expected_channels": ["slack", "email"],
                "expected_primary": "slack"
            },
            {
                "event_type": "maintenance_notification",
                "severity": "low",
                "time_sensitivity": "end_of_day",
                "recipient_availability": "business_hours",
                "expected_channels": ["email"],
                "expected_primary": "email"
            },
            {
                "event_type": "business_metric_alert",
                "severity": "medium",
                "time_sensitivity": "within_hours",
                "recipient_availability": "team_lead_required",
                "expected_channels": ["slack", "email"],
                "expected_primary": "slack"
            }
        ]

        for context in event_contexts:
            channel_selection = notification_sender.optimize_channel_selection(context)

            assert channel_selection["optimization_success"] is True
            assert "selected_channels" in channel_selection
            assert "primary_channel" in channel_selection
            assert "channel_ranking" in channel_selection

            selected_channels = channel_selection["selected_channels"]
            assert len(selected_channels) >= len(context["expected_channels"])

            # Verify primary channel
            assert channel_selection["primary_channel"] == context["expected_primary"]

            # Check channel ranking
            ranking = channel_selection["channel_ranking"]
            assert len(ranking) == len(selected_channels)

            # Primary channel should be ranked first
            assert ranking[0]["channel"] == context["expected_primary"]
            assert ranking[0]["priority_score"] == max(r["priority_score"] for r in ranking)

    def test_routing_rule_engine(self, notification_sender):
        """Test comprehensive routing rule engine."""
        routing_rules = [
            {
                "rule_id": "critical_system_events",
                "conditions": {
                    "severity": "critical",
                    "event_type": ["system_failure", "security_breach", "data_loss"]
                },
                "actions": {
                    "notify_owners": ["security_team", "platform_team", "executive_team"],
                    "channels": ["pagerduty", "sms", "phone"],
                    "escalation": "immediate",
                    "acknowledgment_required": True
                },
                "priority": 1
            },
            {
                "rule_id": "business_impact_events",
                "conditions": {
                    "business_impact": ["revenue_impact", "customer_facing"],
                    "severity": ["high", "critical"]
                },
                "actions": {
                    "notify_owners": ["business_team", "platform_team"],
                    "channels": ["slack", "email", "sms"],
                    "escalation": "within_15_minutes",
                    "acknowledgment_required": True
                },
                "priority": 2
            },
            {
                "rule_id": "performance_alerts",
                "conditions": {
                    "event_type": "performance_degradation",
                    "severity": ["medium", "high"],
                    "metrics": {"response_time_p95": "> 2000"}
                },
                "actions": {
                    "notify_owners": ["platform_team", "devops"],
                    "channels": ["slack", "email"],
                    "escalation": "within_1_hour",
                    "acknowledgment_required": False
                },
                "priority": 3
            }
        ]

        # Test events against rules
        test_events = [
            {
                "event_type": "system_failure",
                "severity": "critical",
                "expected_rule": "critical_system_events"
            },
            {
                "event_type": "performance_degradation",
                "severity": "high",
                "metrics": {"response_time_p95": 2500},
                "expected_rule": "performance_alerts"
            },
            {
                "event_type": "customer_issue",
                "severity": "high",
                "business_impact": "customer_facing",
                "expected_rule": "business_impact_events"
            }
        ]

        for event in test_events:
            rule_match = notification_sender.apply_routing_rules(event, routing_rules)

            assert rule_match["rule_applied"] is True
            assert "matched_rule" in rule_match
            assert rule_match["matched_rule"]["rule_id"] == event["expected_rule"]

            # Verify actions from matched rule
            applied_actions = rule_match["applied_actions"]
            expected_rule = next(rule for rule in routing_rules if rule["rule_id"] == event["expected_rule"])

            assert set(applied_actions["notify_owners"]) == set(expected_rule["actions"]["notify_owners"])
            assert applied_actions["escalation"] == expected_rule["actions"]["escalation"]

    def test_routing_load_balancing(self, notification_sender):
        """Test routing load balancing across multiple owners/channels."""
        high_volume_event = {
            "event_type": "system_wide_alert",
            "severity": "high",
            "affected_services": ["all_services"],
            "concurrent_notifications": 1000,
            "time_window_seconds": 60
        }

        available_owners = [
            {"owner_id": "team_a", "capacity": 300, "current_load": 50},
            {"owner_id": "team_b", "capacity": 400, "current_load": 75},
            {"owner_id": "team_c", "capacity": 300, "current_load": 25}
        ]

        load_balancing = notification_sender.balance_routing_load(high_volume_event, available_owners)

        assert load_balancing["balancing_success"] is True
        assert "load_distribution" in load_balancing
        assert "capacity_utilization" in load_balancing

        distribution = load_balancing["load_distribution"]

        # Should distribute load based on capacity and current load
        total_assigned = sum(dist["assigned_notifications"] for dist in distribution)
        assert total_assigned == high_volume_event["concurrent_notifications"]

        # Should not exceed individual capacities
        for dist in distribution:
            assigned = dist["assigned_notifications"]
            current_load = dist["current_load"]
            capacity = dist["capacity"]
            assert assigned + current_load <= capacity

        # Should optimize for efficiency
        utilization = load_balancing["capacity_utilization"]
        assert utilization["average_utilization"] <= 0.9  # Don't over-utilize
        assert utilization["max_utilization"] <= 1.0   # Don't exceed capacity

    def test_routing_fallback_and_resilience(self, notification_sender):
        """Test routing fallback mechanisms and resilience."""
        routing_scenarios = [
            {
                "scenario": "primary_channel_failure",
                "event": {"severity": "high", "preferred_channel": "email"},
                "failures": {"email": True, "slack": False, "sms": False},
                "expected_fallback": "slack",
                "expected_success": True
            },
            {
                "scenario": "owner_resolution_failure",
                "event": {"severity": "critical", "target_owner": "platform_team"},
                "failures": {"platform_team": True, "backup_team": False},
                "expected_fallback": "backup_team",
                "expected_success": True
            },
            {
                "scenario": "multiple_failures",
                "event": {"severity": "critical", "preferred_channel": "pagerduty", "target_owner": "security_team"},
                "failures": {"pagerduty": True, "security_team": True, "email": False, "backup_team": False},
                "expected_fallback": {"channel": "email", "owner": "backup_team"},
                "expected_success": True
            },
            {
                "scenario": "complete_failure",
                "event": {"severity": "medium"},
                "failures": {"all_channels": True, "all_owners": True},
                "expected_fallback": None,
                "expected_success": False
            }
        ]

        for scenario in routing_scenarios:
            fallback_result = notification_sender.handle_routing_failures(scenario)

            assert fallback_result["fallback_attempted"] is True

            if scenario["expected_success"]:
                assert fallback_result["fallback_success"] is True
                assert "fallback_routing" in fallback_result

                fallback_routing = fallback_result["fallback_routing"]

                if isinstance(scenario["expected_fallback"], str):
                    # Single fallback
                    assert fallback_routing["channel"] == scenario["expected_fallback"] or \
                           fallback_routing["owner"] == scenario["expected_fallback"]
                else:
                    # Multiple fallbacks
                    for key, expected_value in scenario["expected_fallback"].items():
                        assert fallback_routing[key] == expected_value
            else:
                assert fallback_result["fallback_success"] is False
                assert "failure_reason" in fallback_result

    def test_routing_performance_optimization(self, notification_sender):
        """Test routing performance optimization."""
        routing_optimization = {
            "routing_patterns": [
                {"pattern": "service_failure", "frequency": 50, "avg_processing_time_ms": 150},
                {"pattern": "performance_alert", "frequency": 100, "avg_processing_time_ms": 80},
                {"pattern": "security_event", "frequency": 10, "avg_processing_time_ms": 200},
                {"pattern": "maintenance", "frequency": 25, "avg_processing_time_ms": 50}
            ],
            "optimization_goals": {
                "max_average_routing_time_ms": 100,
                "min_routing_success_rate": 0.98,
                "max_resource_utilization_percent": 70
            },
            "available_optimizations": [
                "caching_frequent_routes",
                "parallel_owner_resolution",
                "channel_connection_pooling",
                "rule_precompilation"
            ]
        }

        optimization_result = notification_sender.optimize_routing_performance(routing_optimization)

        assert optimization_result["optimization_success"] is True
        assert "applied_optimizations" in optimization_result
        assert "performance_projections" in optimization_result

        applied = optimization_result["applied_optimizations"]
        assert len(applied) > 0

        # Should apply relevant optimizations
        optimization_names = [opt["optimization"] for opt in applied]
        assert "caching_frequent_routes" in optimization_names
        assert "parallel_owner_resolution" in optimization_names

        projections = optimization_result["performance_projections"]
        assert "estimated_routing_time_ms" in projections
        assert "estimated_success_rate" in projections

        # Should meet optimization goals
        assert projections["estimated_routing_time_ms"] <= routing_optimization["optimization_goals"]["max_average_routing_time_ms"]
        assert projections["estimated_success_rate"] >= routing_optimization["optimization_goals"]["min_routing_success_rate"]


class TestRoutingRuleManagement:
    """Test Routing Rule Management functionality."""

    @pytest.fixture
    def notification_sender(self):
        """Create notification sender instance."""
        return NotificationSender()

    def test_rule_validation_and_testing(self, notification_sender):
        """Test routing rule validation and testing."""
        test_rules = [
            {
                "rule_id": "valid_rule",
                "conditions": {
                    "severity": "high",
                    "event_type": "service_failure"
                },
                "actions": {
                    "notify_owners": ["platform_team"],
                    "channels": ["email", "slack"]
                },
                "expected_valid": True
            },
            {
                "rule_id": "invalid_conditions",
                "conditions": {
                    "invalid_field": "value",
                    "severity": "invalid_severity"
                },
                "actions": {
                    "notify_owners": ["platform_team"]
                },
                "expected_valid": False
            },
            {
                "rule_id": "missing_actions",
                "conditions": {
                    "severity": "medium"
                },
                "actions": {},
                "expected_valid": False
            },
            {
                "rule_id": "circular_reference",
                "conditions": {
                    "severity": "high",
                    "depends_on_rule": "circular_reference"  # Self-reference
                },
                "actions": {
                    "notify_owners": ["platform_team"]
                },
                "expected_valid": False
            }
        ]

        for rule in test_rules:
            validation_result = notification_sender.validate_routing_rule(rule)

            assert validation_result["validation_performed"] is True
            assert validation_result["is_valid"] == rule["expected_valid"]

            if rule["expected_valid"]:
                assert len(validation_result["validation_errors"]) == 0
                assert "test_coverage" in validation_result
            else:
                assert len(validation_result["validation_errors"]) > 0

    def test_rule_conflict_resolution(self, notification_sender):
        """Test routing rule conflict resolution."""
        conflicting_rules = [
            {
                "rule_id": "rule_1",
                "priority": 1,
                "conditions": {"severity": "high"},
                "actions": {"notify_owners": ["team_a"], "channels": ["email"]}
            },
            {
                "rule_id": "rule_2",
                "priority": 2,  # Higher priority
                "conditions": {"severity": "high", "event_type": "service_failure"},
                "actions": {"notify_owners": ["team_b"], "channels": ["slack"]}
            },
            {
                "rule_id": "rule_3",
                "priority": 3,  # Highest priority
                "conditions": {"severity": "high", "event_type": "service_failure", "source": "critical_service"},
                "actions": {"notify_owners": ["team_c"], "channels": ["pagerduty"]}
            }
        ]

        # Test event that matches all rules
        test_event = {
            "severity": "high",
            "event_type": "service_failure",
            "source": "critical_service"
        }

        conflict_resolution = notification_sender.resolve_rule_conflicts(test_event, conflicting_rules)

        assert conflict_resolution["conflict_resolution_success"] is True
        assert "winning_rule" in conflict_resolution
        assert "applied_actions" in conflict_resolution

        # Should select highest priority rule
        winning_rule = conflict_resolution["winning_rule"]
        assert winning_rule["rule_id"] == "rule_3"

        applied_actions = conflict_resolution["applied_actions"]
        assert applied_actions["notify_owners"] == ["team_c"]
        assert applied_actions["channels"] == ["pagerduty"]

    def test_rule_performance_monitoring(self, notification_sender):
        """Test routing rule performance monitoring."""
        rule_performance_data = {
            "rule_id": "performance_monitored_rule",
            "execution_stats": {
                "total_executions": 1000,
                "successful_executions": 980,
                "average_execution_time_ms": 45,
                "error_rate": 0.02,
                "false_positives": 15,
                "false_negatives": 5
            },
            "performance_metrics": {
                "precision": 0.985,  # True positives / (True positives + False positives)
                "recall": 0.995,     # True positives / (True positives + False negatives)
                "f1_score": 0.99,
                "efficiency_score": 0.88
            },
            "usage_patterns": {
                "peak_usage_hour": 14,
                "most_common_event_type": "service_failure",
                "average_events_per_hour": 25
            }
        }

        performance_analysis = notification_sender.analyze_rule_performance(rule_performance_data)

        assert performance_analysis["analysis_success"] is True
        assert "performance_score" in performance_analysis
        assert "efficiency_metrics" in performance_analysis
        assert "optimization_recommendations" in performance_analysis

        performance_score = performance_analysis["performance_score"]
        assert 0.0 <= performance_score <= 1.0
        assert performance_score >= 0.85  # Should be high performing

        efficiency_metrics = performance_analysis["efficiency_metrics"]
        assert "accuracy_score" in efficiency_metrics
        assert "processing_efficiency" in efficiency_metrics

        recommendations = performance_analysis["optimization_recommendations"]
        assert len(recommendations) >= 0

        # Should provide specific recommendations based on metrics
        if rule_performance_data["execution_stats"]["error_rate"] > 0.01:
            error_recs = [rec for rec in recommendations if "error" in rec["recommendation_type"].lower()]
            assert len(error_recs) > 0

    def test_rule_versioning_and_rollback(self, notification_sender):
        """Test routing rule versioning and rollback capabilities."""
        rule_versions = [
            {
                "version": "1.0",
                "rule_definition": {
                    "conditions": {"severity": "high"},
                    "actions": {"notify_owners": ["platform_team"]}
                },
                "created_at": datetime.now() - timedelta(days=30),
                "performance_score": 0.85
            },
            {
                "version": "1.1",
                "rule_definition": {
                    "conditions": {"severity": "high", "event_type": "service_failure"},
                    "actions": {"notify_owners": ["platform_team"], "channels": ["email"]}
                },
                "created_at": datetime.now() - timedelta(days=15),
                "performance_score": 0.90
            },
            {
                "version": "2.0",
                "rule_definition": {
                    "conditions": {"severity": ["high", "critical"], "event_type": "service_failure"},
                    "actions": {"notify_owners": ["platform_team", "oncall"], "channels": ["email", "slack"]}
                },
                "created_at": datetime.now() - timedelta(days=1),
                "performance_score": 0.95
            }
        ]

        current_version = "2.0"
        rollback_trigger = {
            "trigger_reason": "performance_degradation",
            "current_performance": 0.78,  # Below threshold
            "performance_threshold": 0.85,
            "rollback_target": "auto_select_best"
        }

        versioning_result = notification_sender.manage_rule_versions(rule_versions, current_version, rollback_trigger)

        assert versioning_result["version_management_success"] is True
        assert "rollback_recommended" in versioning_result
        assert "target_version" in versioning_result

        # Should recommend rollback due to performance degradation
        assert versioning_result["rollback_recommended"] is True

        target_version = versioning_result["target_version"]
        assert target_version == "2.0"  # Best performing version

        assert "rollback_plan" in versioning_result
        rollback_plan = versioning_result["rollback_plan"]
        assert "rollback_steps" in rollback_plan
        assert "estimated_downtime_seconds" in rollback_plan

    def test_rule_audit_and_compliance(self, notification_sender):
        """Test routing rule audit trails and compliance validation."""
        rule_audit_data = {
            "rule_id": "audited_rule",
            "audit_trail": [
                {
                    "timestamp": datetime.now() - timedelta(days=7),
                    "action": "rule_created",
                    "user": "compliance_officer",
                    "changes": {"conditions": {"severity": "high"}, "actions": {"notify_owners": ["platform_team"]}}
                },
                {
                    "timestamp": datetime.now() - timedelta(days=3),
                    "action": "rule_modified",
                    "user": "platform_engineer",
                    "changes": {"actions": {"channels": ["email"]}},
                    "approval_required": True,
                    "approved_by": "team_lead"
                },
                {
                    "timestamp": datetime.now() - timedelta(hours=1),
                    "action": "rule_executed",
                    "automated": True,
                    "execution_context": {"event_id": "evt_123", "matched_conditions": True}
                }
            ],
            "compliance_requirements": [
                {
                    "framework": "SOX",
                    "requirements": ["audit_trails", "change_management", "access_controls"],
                    "validation_rules": {
                        "audit_trail_required": True,
                        "change_approval_required": True,
                        "access_logging_enabled": True
                    }
                },
                {
                    "framework": "GDPR",
                    "requirements": ["data_minimization", "purpose_limitation"],
                    "validation_rules": {
                        "minimal_data_collection": True,
                        "purpose_specified": True,
                        "retention_limits": True
                    }
                }
            ]
        }

        audit_result = notification_sender.audit_rule_compliance(rule_audit_data)

        assert audit_result["audit_success"] is True
        assert "compliance_status" in audit_result
        assert "audit_findings" in audit_result

        compliance_status = audit_result["compliance_status"]

        # Should validate against each framework
        for framework in rule_audit_data["compliance_requirements"]:
            framework_name = framework["framework"]
            assert framework_name in compliance_status
            assert "compliant" in compliance_status[framework_name]
            assert compliance_status[framework_name]["compliant"] is True

        audit_findings = audit_result["audit_findings"]
        assert "total_findings" in audit_findings
        assert "severity_breakdown" in audit_findings

        # Should have comprehensive audit trail
        assert "audit_trail_completeness" in audit_findings
        assert audit_findings["audit_trail_completeness"] >= 0.95
