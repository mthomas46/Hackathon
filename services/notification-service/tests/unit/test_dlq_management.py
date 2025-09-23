"""Unit Tests for Dead Letter Queue Management in Notification Service.

This module tests dead letter queue capabilities including:
- DLQ entry management and lifecycle
- Retry scheduling and execution
- Failure analysis and reporting
- Capacity management and monitoring

Tests cover the complete dead letter queue infrastructure within the Notification Service.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from modules.dlq_manager import DLQManager


class TestDLQEntryManagement:
    """Test DLQ Entry Management functionality."""

    @pytest.fixture
    def dlq_manager(self):
        """Create DLQ manager instance."""
        return DLQManager()

    def test_dlq_entry_creation(self, dlq_manager):
        """Test DLQ entry creation and validation."""
        dlq_entry_data = {
            "original_event_id": str(uuid.uuid4()),
            "event_type": "service_failure",
            "severity": "high",
            "failure_reason": "delivery_timeout",
            "failure_details": {
                "error_code": "SMTP_TIMEOUT",
                "error_message": "Connection to SMTP server timed out after 30 seconds",
                "smtp_server": "smtp.company.com",
                "port": 587,
                "timeout_seconds": 30
            },
            "original_payload": {
                "title": "Service Failure Alert",
                "description": "Critical service is down",
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
                }
            ],
            "metadata": {
                "correlation_id": str(uuid.uuid4()),
                "request_id": str(uuid.uuid4()),
                "event_timestamp": datetime.now() - timedelta(minutes=20)
            }
        }

        entry_creation = dlq_manager.create_dlq_entry(dlq_entry_data)

        assert entry_creation["creation_success"] is True
        assert "dlq_entry" in entry_creation
        assert "validation_results" in entry_creation

        dlq_entry = entry_creation["dlq_entry"]
        assert "dlq_id" in dlq_entry
        assert dlq_entry["processing_status"] == "awaiting_retry"
        assert "created_at" in dlq_entry
        assert "expires_at" in dlq_entry

        # Should set TTL (default 7 days)
        expected_expiry = dlq_entry["created_at"] + timedelta(days=7)
        assert dlq_entry["expires_at"] == expected_expiry

        validation = entry_creation["validation_results"]
        assert validation["entry_valid"] is True
        assert len(validation["validation_errors"]) == 0

    def test_dlq_entry_lifecycle(self, dlq_manager):
        """Test DLQ entry lifecycle management."""
        # Create an entry
        entry_data = {
            "original_event_id": str(uuid.uuid4()),
            "event_type": "performance_alert",
            "failure_reason": "rate_limit_exceeded",
            "original_payload": {"alert": "High CPU usage"},
            "delivery_attempts": []
        }

        creation_result = dlq_manager.create_dlq_entry(entry_data)
        dlq_id = creation_result["dlq_entry"]["dlq_id"]

        # Test status transitions
        status_transitions = [
            ("processing", "Processing entry"),
            ("retry_scheduled", "Retry scheduled"),
            ("retry_completed", "Retry completed successfully"),
            ("max_retries_exceeded", "Maximum retries exceeded"),
            ("manually_resolved", "Manually resolved by administrator")
        ]

        for new_status, reason in status_transitions:
            status_update = dlq_manager.update_dlq_entry_status(dlq_id, new_status, reason)

            assert status_update["update_success"] is True
            assert "status_transition" in status_update

            transition = status_update["status_transition"]
            assert transition["from_status"] != transition["to_status"]
            assert transition["to_status"] == new_status
            assert transition["reason"] == reason

            # Verify current status
            current_entry = dlq_manager.get_dlq_entry(dlq_id)
            assert current_entry["processing_status"] == new_status

    def test_dlq_capacity_management(self, dlq_manager):
        """Test DLQ capacity management and overflow handling."""
        capacity_config = {
            "max_entries": 1000,
            "max_entry_size_bytes": 102400,  # 100KB
            "retention_days": 7,
            "overflow_policy": "lru_eviction",  # Least Recently Used
            "priority_levels": ["critical", "high", "medium", "low"]
        }

        # Test capacity validation
        capacity_validation = dlq_manager.validate_dlq_capacity(capacity_config)
        assert capacity_validation["validation_success"] is True

        # Simulate adding entries up to capacity
        entries_added = 0
        for i in range(1050):  # Over capacity
            entry_data = {
                "original_event_id": str(uuid.uuid4()),
                "event_type": "test_event",
                "failure_reason": "test_failure",
                "original_payload": {"test_data": f"entry_{i}"},
                "priority": "medium" if i % 3 == 0 else "low",
                "size_bytes": 51200  # 50KB
            }

            add_result = dlq_manager.add_entry_with_capacity_check(entry_data, capacity_config)

            if i < capacity_config["max_entries"]:
                assert add_result["entry_added"] is True
                entries_added += 1
            else:
                # Should trigger overflow handling
                assert add_result["entry_added"] is False
                assert "overflow_handling" in add_result

                overflow = add_result["overflow_handling"]
                assert overflow["policy_applied"] == "lru_eviction"
                assert "evicted_entries" in overflow

        # Verify final capacity
        final_capacity = dlq_manager.get_dlq_capacity_status()
        assert final_capacity["current_entries"] == capacity_config["max_entries"]
        assert final_capacity["capacity_utilization"] == 1.0  # 100%

    def test_dlq_entry_expiration(self, dlq_manager):
        """Test DLQ entry expiration and cleanup."""
        # Create entries with different TTL values
        test_entries = [
            {
                "original_event_id": str(uuid.uuid4()),
                "event_type": "temp_failure",
                "failure_reason": "connection_timeout",
                "ttl_seconds": 3600,  # 1 hour
                "created_at": datetime.now() - timedelta(seconds=7200)  # 2 hours ago - expired
            },
            {
                "original_event_id": str(uuid.uuid4()),
                "event_type": "perm_failure",
                "failure_reason": "invalid_recipient",
                "ttl_seconds": 604800,  # 7 days
                "created_at": datetime.now() - timedelta(days=1)  # 1 day ago - still valid
            },
            {
                "original_event_id": str(uuid.uuid4()),
                "event_type": "short_lived",
                "failure_reason": "rate_limit",
                "ttl_seconds": 300,  # 5 minutes
                "created_at": datetime.now() - timedelta(seconds=600)  # 10 minutes ago - expired
            }
        ]

        for entry_data in test_entries:
            dlq_manager.create_dlq_entry(entry_data)

        # Run expiration check
        expiration_check = dlq_manager.check_entry_expirations()

        assert expiration_check["check_completed"] is True
        assert "expired_entries" in expiration_check
        assert "active_entries" in expiration_check

        expired_entries = expiration_check["expired_entries"]
        active_entries = expiration_check["active_entries"]

        # Should identify expired entries (first and third)
        assert len(expired_entries) == 2
        expired_types = [entry["event_type"] for entry in expired_entries]
        assert "temp_failure" in expired_types
        assert "short_lived" in expired_types

        # Should keep active entry
        assert len(active_entries) == 1
        assert active_entries[0]["event_type"] == "perm_failure"

        # Run cleanup
        cleanup_result = dlq_manager.cleanup_expired_entries()

        assert cleanup_result["cleanup_success"] is True
        assert "entries_removed" in cleanup_result
        assert cleanup_result["entries_removed"] == 2

        # Verify cleanup
        final_status = dlq_manager.get_dlq_stats()
        assert final_status["total_entries"] == 1


class TestRetryScheduling:
    """Test Retry Scheduling functionality."""

    @pytest.fixture
    def dlq_manager(self):
        """Create DLQ manager instance."""
        return DLQManager()

    def test_retry_policy_application(self, dlq_manager):
        """Test retry policy application to DLQ entries."""
        retry_policies = {
            "aggressive_retry": {
                "max_attempts": 10,
                "base_delay_seconds": 60,
                "backoff_multiplier": 1.5,
                "max_delay_seconds": 3600,
                "retryable_errors": ["connection_timeout", "rate_limit", "temporary_failure"]
            },
            "conservative_retry": {
                "max_attempts": 3,
                "base_delay_seconds": 300,
                "backoff_multiplier": 2.0,
                "max_delay_seconds": 7200,
                "retryable_errors": ["connection_timeout"]
            },
            "no_retry": {
                "max_attempts": 0,
                "retryable_errors": []
            }
        }

        test_entries = [
            {
                "dlq_id": str(uuid.uuid4()),
                "failure_reason": "connection_timeout",
                "retry_attempts": 2,
                "expected_policy": "aggressive_retry",
                "expected_retryable": True
            },
            {
                "dlq_id": str(uuid.uuid4()),
                "failure_reason": "invalid_recipient",
                "retry_attempts": 1,
                "expected_policy": None,
                "expected_retryable": False
            },
            {
                "dlq_id": str(uuid.uuid4()),
                "failure_reason": "rate_limit",
                "retry_attempts": 0,
                "expected_policy": "aggressive_retry",
                "expected_retryable": True
            }
        ]

        for entry in test_entries:
            policy_application = dlq_manager.apply_retry_policy(entry, retry_policies)

            assert policy_application["policy_application_success"] is True
            assert "retry_eligibility" in policy_application
            assert "applied_policy" in policy_application

            eligibility = policy_application["retry_eligibility"]
            assert eligibility["retryable"] == entry["expected_retryable"]

            applied_policy = policy_application["applied_policy"]
            if entry["expected_policy"]:
                assert applied_policy["policy_name"] == entry["expected_policy"]
                assert "next_retry_time" in applied_policy

                # Verify retry scheduling
                next_retry = applied_policy["next_retry_time"]
                assert next_retry > datetime.now()
            else:
                assert applied_policy is None

    def test_retry_execution_coordination(self, dlq_manager):
        """Test retry execution coordination and batching."""
        retry_batch = {
            "batch_id": str(uuid.uuid4()),
            "scheduled_entries": [
                {
                    "dlq_id": str(uuid.uuid4()),
                    "next_retry_time": datetime.now() + timedelta(minutes=5),
                    "retry_policy": "exponential_backoff",
                    "attempt_number": 2,
                    "priority": "high"
                },
                {
                    "dlq_id": str(uuid.uuid4()),
                    "next_retry_time": datetime.now() + timedelta(minutes=10),
                    "retry_policy": "linear_backoff",
                    "attempt_number": 1,
                    "priority": "medium"
                },
                {
                    "dlq_id": str(uuid.uuid4()),
                    "next_retry_time": datetime.now() + timedelta(minutes=15),
                    "retry_policy": "fixed_delay",
                    "attempt_number": 3,
                    "priority": "low"
                }
            ],
            "execution_constraints": {
                "max_concurrent_retries": 5,
                "max_retries_per_minute": 10,
                "respect_entry_priority": True,
                "allow_parallel_execution": True
            }
        }

        coordination_result = dlq_manager.coordinate_retry_execution(retry_batch)

        assert coordination_result["coordination_success"] is True
        assert "execution_plan" in coordination_result
        assert "resource_allocation" in coordination_result
        assert "timing_schedule" in coordination_result

        execution_plan = coordination_result["execution_plan"]
        assert "execution_groups" in execution_plan
        assert "priority_ordering" in execution_plan

        # Should respect priority ordering
        priority_ordering = execution_plan["priority_ordering"]
        assert priority_ordering[0] == "high"
        assert priority_ordering[1] == "medium"
        assert priority_ordering[2] == "low"

        timing_schedule = coordination_result["timing_schedule"]
        assert "scheduled_execution_times" in timing_schedule
        assert "estimated_completion_time" in timing_schedule

        resource_allocation = coordination_result["resource_allocation"]
        assert "concurrent_slots_allocated" in resource_allocation
        assert resource_allocation["concurrent_slots_allocated"] <= retry_batch["execution_constraints"]["max_concurrent_retries"]

    def test_retry_success_tracking(self, dlq_manager):
        """Test retry success tracking and success rate analysis."""
        retry_tracking_data = {
            "dlq_id": str(uuid.uuid4()),
            "retry_history": [
                {
                    "attempt_number": 1,
                    "timestamp": datetime.now() - timedelta(hours=2),
                    "result": "failed",
                    "error": "connection_timeout",
                    "retry_delay_seconds": 60
                },
                {
                    "attempt_number": 2,
                    "timestamp": datetime.now() - timedelta(hours=1),
                    "result": "failed",
                    "error": "rate_limit_exceeded",
                    "retry_delay_seconds": 120
                },
                {
                    "attempt_number": 3,
                    "timestamp": datetime.now() - timedelta(minutes=30),
                    "result": "successful",
                    "delivery_time_ms": 245,
                    "channel": "email",
                    "target": "platform@company.com"
                }
            ],
            "success_criteria": {
                "min_success_rate": 0.3,
                "max_retry_attempts": 5,
                "success_streak_required": 1
            }
        }

        success_analysis = dlq_manager.analyze_retry_success(retry_tracking_data)

        assert success_analysis["analysis_success"] is True
        assert "success_metrics" in success_analysis
        assert "retry_effectiveness" in success_analysis
        assert "recommendations" in success_analysis

        success_metrics = success_analysis["success_metrics"]
        assert "overall_success_rate" in success_metrics
        assert "attempts_to_success" in success_metrics
        assert "average_delivery_time_ms" in success_metrics

        # Should calculate 33.3% success rate (1 out of 3 attempts successful)
        expected_success_rate = 1.0 / 3
        assert abs(success_metrics["overall_success_rate"] - expected_success_rate) < 0.01

        retry_effectiveness = success_analysis["retry_effectiveness"]
        assert "retry_strategy_effectiveness" in retry_effectiveness
        assert "optimal_retry_count" in retry_effectiveness

        recommendations = success_analysis["recommendations"]
        assert len(recommendations) > 0

        # Should recommend continuing retries since eventually successful
        continue_retry_rec = next((rec for rec in recommendations if "continue" in rec["recommendation_type"].lower()), None)
        assert continue_retry_rec is not None

    def test_retry_failure_pattern_analysis(self, dlq_manager):
        """Test retry failure pattern analysis and adaptation."""
        failure_pattern_data = {
            "failure_patterns": [
                {
                    "pattern": "connection_timeout_cluster",
                    "affected_entries": 15,
                    "time_window_hours": 24,
                    "common_characteristics": {
                        "target_domain": "smtp.company.com",
                        "time_of_day": "business_hours",
                        "frequency": "intermittent"
                    },
                    "retry_success_rate": 0.2
                },
                {
                    "pattern": "rate_limit_cascade",
                    "affected_entries": 8,
                    "time_window_hours": 12,
                    "common_characteristics": {
                        "channel": "slack",
                        "error_code": "429",
                        "frequency": "bursty"
                    },
                    "retry_success_rate": 0.75
                },
                {
                    "pattern": "permanent_recipient_failures",
                    "affected_entries": 25,
                    "time_window_hours": 168,  # 1 week
                    "common_characteristics": {
                        "error_type": "invalid_recipient",
                        "channel": "email",
                        "frequency": "consistent"
                    },
                    "retry_success_rate": 0.0
                }
            ],
            "pattern_analysis_config": {
                "min_pattern_size": 5,
                "similarity_threshold": 0.8,
                "analysis_time_window_days": 7
            }
        }

        pattern_analysis = dlq_manager.analyze_retry_failure_patterns(failure_pattern_data)

        assert pattern_analysis["analysis_success"] is True
        assert "identified_patterns" in pattern_analysis
        assert "pattern_characteristics" in pattern_analysis
        assert "adaptive_strategies" in pattern_analysis

        identified_patterns = pattern_analysis["identified_patterns"]
        assert len(identified_patterns) == len(failure_pattern_data["failure_patterns"])

        for pattern in identified_patterns:
            assert "pattern_id" in pattern
            assert "severity_score" in pattern
            assert "recommended_action" in pattern

        # Should identify permanent failures as highest severity
        permanent_pattern = next(p for p in identified_patterns if "permanent" in p["pattern_id"])
        assert permanent_pattern["severity_score"] >= 0.8

        adaptive_strategies = pattern_analysis["adaptive_strategies"]
        assert len(adaptive_strategies) > 0

        # Should recommend different strategies for different patterns
        strategies_by_type = {}
        for strategy in adaptive_strategies:
            pattern_type = strategy["target_pattern"]
            strategies_by_type[pattern_type] = strategy["recommended_strategy"]

        # Permanent failures should stop retries
        assert strategies_by_type.get("permanent_recipient_failures") == "stop_retries"

        # Rate limit should use exponential backoff
        assert "backoff" in strategies_by_type.get("rate_limit_cascade", "").lower()


class TestDLQMonitoringAndReporting:
    """Test DLQ Monitoring and Reporting functionality."""

    @pytest.fixture
    def dlq_manager(self):
        """Create DLQ manager instance."""
        return DLQManager()

    def test_dlq_health_monitoring(self, dlq_manager):
        """Test DLQ health monitoring and alerting."""
        health_monitoring_data = {
            "current_state": {
                "total_entries": 450,
                "capacity_limit": 1000,
                "utilization_percentage": 45.0,
                "entries_by_status": {
                    "awaiting_retry": 320,
                    "retry_scheduled": 85,
                    "processing": 25,
                    "max_retries_exceeded": 20
                },
                "entries_by_age": {
                    "less_than_1_hour": 50,
                    "1_to_24_hours": 200,
                    "1_to_7_days": 180,
                    "older_than_7_days": 20
                }
            },
            "performance_metrics": {
                "average_processing_time_seconds": 2.3,
                "retry_success_rate": 0.65,
                "entries_processed_per_hour": 120,
                "error_rate": 0.05
            },
            "health_thresholds": {
                "max_utilization_percentage": 80.0,
                "min_retry_success_rate": 0.5,
                "max_error_rate": 0.1,
                "max_old_entries_percentage": 10.0
            }
        }

        health_monitoring = dlq_manager.monitor_dlq_health(health_monitoring_data)

        assert health_monitoring["monitoring_success"] is True
        assert "health_assessment" in health_monitoring
        assert "alerts_generated" in health_monitoring
        assert "health_score" in health_monitoring

        health_assessment = health_monitoring["health_assessment"]
        assert health_assessment["overall_health"] == "healthy"  # Within thresholds

        health_score = health_monitoring["health_score"]
        assert 0.0 <= health_score <= 1.0
        assert health_score >= 0.7  # Good health score

        alerts = health_monitoring["alerts_generated"]
        # Should have minimal alerts since within thresholds
        assert len(alerts) <= 1  # Maybe one informational alert

    def test_dlq_performance_analytics(self, dlq_manager):
        """Test DLQ performance analytics and optimization."""
        performance_analytics_data = {
            "time_window": {
                "start": datetime.now() - timedelta(days=7),
                "end": datetime.now()
            },
            "performance_metrics": {
                "entries_processed": 15420,
                "average_processing_time_seconds": 2.1,
                "retry_success_rate": 0.68,
                "error_rate": 0.04,
                "throughput_entries_per_hour": 220
            },
            "bottleneck_analysis": {
                "slowest_processing_stage": "retry_execution",
                "bottleneck_duration_seconds": 1.8,
                "queue_wait_time_seconds": 0.3,
                "resource_contention": "cpu_bound"
            },
            "efficiency_metrics": {
                "resource_utilization": 0.75,
                "memory_usage_mb": 450,
                "cpu_usage_percentage": 65,
                "i/o_operations_per_second": 150
            },
            "optimization_opportunities": [
                {
                    "opportunity": "parallel_processing",
                    "potential_improvement": 0.35,
                    "implementation_complexity": "medium"
                },
                {
                    "opportunity": "caching_optimization",
                    "potential_improvement": 0.20,
                    "implementation_complexity": "low"
                },
                {
                    "opportunity": "algorithm_optimization",
                    "potential_improvement": 0.15,
                    "implementation_complexity": "high"
                }
            ]
        }

        performance_analytics = dlq_manager.analyze_dlq_performance(performance_analytics_data)

        assert performance_analytics["analysis_success"] is True
        assert "performance_insights" in performance_analytics
        assert "bottleneck_resolution" in performance_analytics
        assert "optimization_recommendations" in performance_analytics

        performance_insights = performance_analytics["performance_insights"]
        assert "efficiency_score" in performance_insights
        assert "throughput_analysis" in performance_insights
        assert "resource_utilization_analysis" in performance_insights

        bottleneck_resolution = performance_analytics["bottleneck_resolution"]
        assert "identified_bottlenecks" in bottleneck_resolution
        assert "resolution_strategies" in bottleneck_resolution

        # Should identify retry_execution as bottleneck
        bottlenecks = bottleneck_resolution["identified_bottlenecks"]
        retry_bottleneck = next((b for b in bottlenecks if "retry" in b["component"].lower()), None)
        assert retry_bottleneck is not None

        optimization_recs = performance_analytics["optimization_recommendations"]
        assert len(optimization_recs) >= len(performance_analytics_data["optimization_opportunities"])

        # Should prioritize parallel_processing as highest impact
        parallel_rec = next((rec for rec in optimization_recs if rec["opportunity"] == "parallel_processing"), None)
        assert parallel_rec is not None
        assert parallel_rec["priority"] == "high"

    def test_dlq_capacity_planning(self, dlq_manager):
        """Test DLQ capacity planning and scaling recommendations."""
        capacity_planning_data = {
            "current_capacity": {
                "max_entries": 1000,
                "storage_size_gb": 10,
                "retention_days": 7,
                "processing_threads": 5
            },
            "usage_patterns": {
                "average_entries_per_day": 450,
                "peak_entries_per_hour": 120,
                "growth_rate_percentage": 15,  # 15% monthly growth
                "seasonal_peaks": {
                    "month": 1.8,  # 80% increase in busy month
                    "hour": 2.2    # 120% increase during peak hours
                }
            },
            "performance_requirements": {
                "max_processing_delay_seconds": 300,
                "min_success_rate": 0.8,
                "max_resource_utilization": 0.8
            },
            "scaling_options": {
                "vertical_scaling": {
                    "cpu_cores": [4, 8, 16],
                    "memory_gb": [8, 16, 32],
                    "cost_multiplier": [1.0, 1.5, 2.2]
                },
                "horizontal_scaling": {
                    "instances": [1, 2, 3, 4],
                    "load_balancer_required": True,
                    "cost_multiplier": [1.0, 1.8, 2.5, 3.1]
                },
                "storage_scaling": {
                    "size_gb": [10, 20, 50, 100],
                    "performance_impact": [1.0, 1.1, 1.3, 1.6],
                    "cost_multiplier": [1.0, 1.6, 3.0, 5.5]
                }
            }
        }

        capacity_planning = dlq_manager.plan_dlq_capacity(capacity_planning_data)

        assert capacity_planning["planning_success"] is True
        assert "capacity_analysis" in capacity_planning
        assert "scaling_recommendations" in capacity_planning
        assert "cost_benefit_analysis" in capacity_planning

        capacity_analysis = capacity_planning["capacity_analysis"]
        assert "current_capacity_sufficiency" in capacity_analysis
        assert "projected_capacity_needs" in capacity_analysis
        assert "bottleneck_predictions" in capacity_analysis

        scaling_recommendations = capacity_planning["scaling_recommendations"]
        assert len(scaling_recommendations) > 0

        for recommendation in scaling_recommendations:
            assert "scaling_type" in recommendation
            assert "recommended_configuration" in recommendation
            assert "expected_capacity_improvement" in recommendation
            assert "timeline_months" in recommendation

        cost_benefit_analysis = capacity_planning["cost_benefit_analysis"]
        assert "cost_comparison" in cost_benefit_analysis
        assert "benefit_analysis" in cost_benefit_analysis
        assert "recommended_option" in cost_benefit_analysis

    def test_dlq_compliance_reporting(self, dlq_manager):
        """Test DLQ compliance reporting and audit trails."""
        compliance_reporting_data = {
            "reporting_period": {
                "start": datetime.now() - timedelta(days=30),
                "end": datetime.now()
            },
            "compliance_frameworks": [
                {
                    "framework": "GDPR",
                    "requirements": {
                        "data_retention_days": 2555,  # 7 years
                        "audit_trail_required": True,
                        "data_minimization": True,
                        "consent_management": True
                    }
                },
                {
                    "framework": "SOX",
                    "requirements": {
                        "audit_trail_required": True,
                        "change_tracking": True,
                        "access_logging": True,
                        "data_integrity": True
                    }
                },
                {
                    "framework": "PCI_DSS",
                    "requirements": {
                        "data_encryption": True,
                        "access_controls": True,
                        "audit_trail_required": True,
                        "vulnerability_scanning": True
                    }
                }
            ],
            "dlq_operations_log": [
                {
                    "timestamp": datetime.now() - timedelta(days=15),
                    "operation": "entry_created",
                    "entry_id": str(uuid.uuid4()),
                    "user": "system",
                    "data_classification": "internal"
                },
                {
                    "timestamp": datetime.now() - timedelta(days=10),
                    "operation": "retry_attempted",
                    "entry_id": str(uuid.uuid4()),
                    "user": "system",
                    "sensitive_data_accessed": False
                },
                {
                    "timestamp": datetime.now() - timedelta(days=5),
                    "operation": "entry_deleted",
                    "entry_id": str(uuid.uuid4()),
                    "user": "admin_user",
                    "reason": "data_retention_policy",
                    "data_permanently_removed": True
                }
            ],
            "data_handling_stats": {
                "total_entries_processed": 12543,
                "entries_with_pii": 234,
                "encryption_applied": True,
                "access_audit_events": 892,
                "data_retention_compliant": True
            }
        }

        compliance_reporting = dlq_manager.generate_compliance_report(compliance_reporting_data)

        assert compliance_reporting["reporting_success"] is True
        assert "compliance_assessment" in compliance_reporting
        assert "audit_trail_analysis" in compliance_reporting
        assert "recommendations" in compliance_reporting

        compliance_assessment = compliance_reporting["compliance_assessment"]

        # Should assess compliance for each framework
        for framework in compliance_reporting_data["compliance_frameworks"]:
            framework_name = framework["framework"]
            assert framework_name in compliance_assessment
            framework_assessment = compliance_assessment[framework_name]
            assert "compliant" in framework_assessment
            assert "compliance_score" in framework_assessment
            assert "violations" in framework_assessment

        audit_trail_analysis = compliance_reporting["audit_trail_analysis"]
        assert "audit_completeness" in audit_trail_analysis
        assert "access_pattern_analysis" in audit_trail_analysis
        assert "data_handling_compliance" in audit_trail_analysis

        # Should verify audit trail completeness
        assert audit_trail_analysis["audit_completeness"] >= 0.95

        recommendations = compliance_reporting["recommendations"]
        assert len(recommendations) > 0

        # Should include data handling recommendations
        data_rec = next((rec for rec in recommendations if "data" in rec["category"].lower()), None)
        assert data_rec is not None

    def test_dlq_disaster_recovery(self, dlq_manager):
        """Test DLQ disaster recovery and data integrity."""
        disaster_recovery_data = {
            "disaster_scenario": "complete_system_failure",
            "recovery_objectives": {
                "rto_hours": 4,  # Recovery Time Objective
                "rpo_minutes": 15,  # Recovery Point Objective
                "data_integrity_required": True,
                "audit_trail_preservation": True
            },
            "system_state_before_failure": {
                "total_entries": 750,
                "entries_by_status": {
                    "awaiting_retry": 520,
                    "retry_scheduled": 180,
                    "processing": 50
                },
                "last_backup_timestamp": datetime.now() - timedelta(hours=2),
                "data_integrity_hash": "abc123def456"
            },
            "failure_impact": {
                "data_loss_percentage": 0.05,  # 5% data loss
                "corruption_detected": False,
                "audit_trail_intact": True,
                "recovery_time_actual_hours": 3.5
            },
            "recovery_procedures": [
                {
                    "procedure": "backup_restoration",
                    "estimated_duration_hours": 2,
                    "success_probability": 0.95,
                    "data_loss_expected": 0.03
                },
                {
                    "procedure": "incremental_sync",
                    "estimated_duration_hours": 1.5,
                    "success_probability": 0.88,
                    "data_loss_expected": 0.02
                },
                {
                    "procedure": "manual_reconstruction",
                    "estimated_duration_hours": 6,
                    "success_probability": 0.99,
                    "data_loss_expected": 0.01
                }
            ]
        }

        disaster_recovery = dlq_manager.execute_disaster_recovery(disaster_recovery_data)

        assert disaster_recovery["recovery_success"] is True
        assert "recovery_assessment" in disaster_recovery
        assert "data_integrity_verification" in disaster_recovery
        assert "recovery_procedure_executed" in disaster_recovery

        recovery_assessment = disaster_recovery["recovery_assessment"]
        assert "rto_achieved" in recovery_assessment
        assert "rpo_achieved" in recovery_assessment
        assert "overall_recovery_success" in recovery_assessment

        # Should achieve recovery objectives
        assert recovery_assessment["rto_achieved"] is True  # 3.5 hours < 4 hours
        assert recovery_assessment["rpo_achieved"] is True  # 15 minutes RPO met

        data_integrity = disaster_recovery["data_integrity_verification"]
        assert "data_integrity_maintained" in data_integrity
        assert "audit_trail_preserved" in data_integrity
        assert data_integrity["data_integrity_maintained"] is True

        recovery_procedure = disaster_recovery["recovery_procedure_executed"]
        assert "procedure_selected" in recovery_procedure
        assert "execution_success" in recovery_procedure
        assert recovery_procedure["execution_success"] is True

        # Should select the most effective procedure (manual_reconstruction has lowest data loss)
        assert recovery_procedure["procedure_selected"] == "manual_reconstruction"
