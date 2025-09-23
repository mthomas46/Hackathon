"""Unit Tests for A/B Testing in Prompt Store Service.

This module tests A/B testing capabilities including:
- Test creation and configuration
- Variant management and distribution
- Result collection and statistical analysis
- Winner determination and statistical significance
- Test lifecycle management and automation
- Performance impact assessment

Tests cover the complete A/B testing system for prompt optimization.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from statistics import mean, stdev

from core.entities import ABTest, ABTestResult
from core.models import ABTestVariant
from domain.ab_testing.handlers import ABTestCommandHandler
from domain.ab_testing.repository import ABTestRepository
from domain.ab_testing.service import ABTestService


class TestABTestCreation:
    """Test A/B Test Creation functionality."""

    @pytest.fixture
    def ab_test_handler(self, mock_repository, mock_event_bus):
        """Create A/B test command handler instance."""
        return ABTestCommandHandler(mock_repository, mock_event_bus)

    def test_basic_ab_test_creation(self, ab_test_handler, sample_ab_test):
        """Test basic A/B test creation with minimal configuration."""
        create_command = {
            "name": "Simple Prompt Test",
            "prompt_id": str(uuid.uuid4()),
            "variants": [
                {"name": "Control", "content": "Analyze this: {content}"},
                {"name": "Variant A", "content": "Please analyze this content: {content}"}
            ],
            "created_by": "test@example.com"
        }

        result = ab_test_handler.handle_create_ab_test(create_command)

        assert result["success"] is True
        assert "test_id" in result
        assert result["test"]["status"] == "created"
        assert len(result["test"]["variants"]) == 2

    def test_ab_test_creation_with_full_configuration(self, ab_test_handler):
        """Test A/B test creation with comprehensive configuration."""
        create_command = {
            "name": "Advanced Prompt Optimization Test",
            "description": "Testing different prompt structures for code analysis",
            "prompt_id": str(uuid.uuid4()),
            "variants": [
                {
                    "name": "Control",
                    "content": "Analyze this code: {code_content}",
                    "weight": 30,
                    "metadata": {"structure": "basic", "complexity": "simple"}
                },
                {
                    "name": "Structured Analysis",
                    "content": """Analyze this code comprehensively:

Code: {code_content}

Provide:
1. Code quality assessment
2. Potential improvements
3. Best practices evaluation""",
                    "weight": 35,
                    "metadata": {"structure": "structured", "complexity": "detailed"}
                },
                {
                    "name": "Expert Analysis",
                    "content": """You are a senior software engineer. Perform a detailed code review:

{code_content}

Evaluate:
- Code correctness and efficiency
- Design patterns and architecture
- Security considerations
- Performance optimization opportunities
- Code maintainability and readability""",
                    "weight": 35,
                    "metadata": {"structure": "expert", "complexity": "comprehensive"}
                }
            ],
            "target_sample_size": 1000,
            "metrics": ["response_quality", "response_time", "user_satisfaction", "cost_efficiency"],
            "significance_threshold": 0.05,
            "early_stopping_enabled": True,
            "max_duration_days": 14,
            "created_by": "data.scientist@example.com"
        }

        result = ab_test_handler.handle_create_ab_test(create_command)

        assert result["success"] is True
        test = result["test"]

        assert test["name"] == create_command["name"]
        assert len(test["variants"]) == 3
        assert test["target_sample_size"] == 1000
        assert set(test["metrics"]) == set(create_command["metrics"])
        assert test["significance_threshold"] == 0.05

        # Verify variant weights sum to 100
        total_weight = sum(variant["weight"] for variant in test["variants"])
        assert total_weight == 100

    def test_ab_test_validation(self, ab_test_handler):
        """Test A/B test creation validation."""
        invalid_commands = [
            # Missing name
            {"prompt_id": str(uuid.uuid4()), "variants": [], "created_by": "user@example.com"},
            # No variants
            {"name": "Test", "prompt_id": str(uuid.uuid4()), "variants": [], "created_by": "user@example.com"},
            # Only one variant
            {"name": "Test", "prompt_id": str(uuid.uuid4()),
             "variants": [{"name": "Only One", "content": "Content"}],
             "created_by": "user@example.com"},
            # Variant weights don't sum to 100
            {"name": "Test", "prompt_id": str(uuid.uuid4()),
             "variants": [
                 {"name": "A", "content": "Content A", "weight": 50},
                 {"name": "B", "content": "Content B", "weight": 30}
             ],
             "created_by": "user@example.com"},
            # Invalid metric
            {"name": "Test", "prompt_id": str(uuid.uuid4()),
             "variants": [
                 {"name": "A", "content": "Content A", "weight": 50},
                 {"name": "B", "content": "Content B", "weight": 50}
             ],
             "metrics": ["invalid_metric"],
             "created_by": "user@example.com"}
        ]

        for invalid_command in invalid_commands:
            result = ab_test_handler.handle_create_ab_test(invalid_command)
            assert result["success"] is False
            assert "validation_errors" in result

    def test_ab_test_variant_distribution(self, ab_test_handler):
        """Test variant distribution logic."""
        variants = [
            {"name": "Control", "weight": 25},
            {"name": "Variant A", "weight": 25},
            {"name": "Variant B", "weight": 25},
            {"name": "Variant C", "weight": 25}
        ]

        distribution_result = ab_test_handler.calculate_variant_distribution(variants)

        assert distribution_result["success"] is True
        distribution = distribution_result["distribution"]

        # Each variant should have equal probability (25%)
        for variant in variants:
            assert distribution[variant["name"]] == 0.25

        # Total probability should sum to 1.0
        total_probability = sum(distribution.values())
        assert abs(total_probability - 1.0) < 0.001

    def test_ab_test_start_and_stop(self, ab_test_handler, sample_ab_test):
        """Test A/B test lifecycle management."""
        test_id = sample_ab_test.id

        # Start test
        start_result = ab_test_handler.handle_start_ab_test(test_id, "admin@example.com")
        assert start_result["success"] is True
        assert start_result["test"]["status"] == "running"
        assert start_result["test"]["started_at"] is not None

        # Stop test
        stop_result = ab_test_handler.handle_stop_ab_test(test_id, "admin@example.com", "Manual stop")
        assert stop_result["success"] is True
        assert stop_result["test"]["status"] == "stopped"
        assert stop_result["test"]["ended_at"] is not None
        assert stop_result["test"]["stop_reason"] == "Manual stop"


class TestVariantManagement:
    """Test Variant Management functionality."""

    @pytest.fixture
    def variant_manager(self, mock_repository):
        """Create variant manager instance."""
        return ABTestService(repository=mock_repository)

    def test_variant_selection_algorithm(self, variant_manager):
        """Test variant selection algorithm."""
        test_variants = [
            {"id": "var_1", "name": "Control", "weight": 50},
            {"id": "var_2", "name": "Variant A", "weight": 30},
            {"id": "var_3", "name": "Variant B", "weight": 20}
        ]

        # Test selection over multiple calls
        selections = []
        for _ in range(200):
            selection = variant_manager.select_variant_for_request(test_variants)
            selections.append(selection["selected_variant"]["id"])

        # Count selections
        selection_counts = {}
        for variant_id in selections:
            selection_counts[variant_id] = selection_counts.get(variant_id, 0) + 1

        # Verify distribution is roughly correct (within 10% tolerance)
        total_selections = len(selections)
        for variant in test_variants:
            expected_count = int((variant["weight"] / 100) * total_selections)
            actual_count = selection_counts.get(variant["id"], 0)
            tolerance = expected_count * 0.1  # 10% tolerance

            assert abs(actual_count - expected_count) <= tolerance

    def test_dynamic_variant_adjustment(self, variant_manager):
        """Test dynamic variant adjustment based on performance."""
        initial_variants = [
            {"id": "var_1", "name": "Control", "weight": 50, "performance_score": 0.7},
            {"id": "var_2", "name": "Variant A", "weight": 30, "performance_score": 0.8},
            {"id": "var_3", "name": "Variant B", "weight": 20, "performance_score": 0.6}
        ]

        adjustment_result = variant_manager.adjust_variant_weights_dynamically(initial_variants)

        assert adjustment_result["success"] is True
        adjusted_variants = adjustment_result["adjusted_variants"]

        # Better performing variant should get higher weight
        variant_a_adjusted = next(v for v in adjusted_variants if v["id"] == "var_2")
        control_adjusted = next(v for v in adjusted_variants if v["id"] == "var_1")

        assert variant_a_adjusted["weight"] > control_adjusted["weight"]

        # Total weight should still sum to 100
        total_weight = sum(v["weight"] for v in adjusted_variants)
        assert total_weight == 100

    def test_variant_performance_tracking(self, variant_manager):
        """Test variant performance tracking."""
        variant_id = str(uuid.uuid4())
        test_results = [
            {"metric": "response_quality", "value": 0.85, "timestamp": datetime.now()},
            {"metric": "response_time", "value": 2450, "timestamp": datetime.now()},
            {"metric": "user_satisfaction", "value": 0.92, "timestamp": datetime.now()},
            {"metric": "response_quality", "value": 0.88, "timestamp": datetime.now()},
            {"metric": "response_time", "value": 2200, "timestamp": datetime.now()}
        ]

        for result in test_results:
            variant_manager.record_variant_result(variant_id, result["metric"], result["value"], result["timestamp"])

        performance_result = variant_manager.get_variant_performance(variant_id)

        assert performance_result["success"] is True
        performance = performance_result["performance"]

        # Should have metrics aggregated
        assert "response_quality" in performance
        assert "response_time" in performance
        assert "user_satisfaction" in performance

        # Response quality should be averaged
        quality_values = [r["value"] for r in test_results if r["metric"] == "response_quality"]
        expected_avg_quality = mean(quality_values)
        assert abs(performance["response_quality"]["average"] - expected_avg_quality) < 0.001

        # Should include sample counts
        assert performance["response_quality"]["sample_count"] == 2
        assert performance["response_time"]["sample_count"] == 2
        assert performance["user_satisfaction"]["sample_count"] == 1

    def test_variant_comparison_analytics(self, variant_manager):
        """Test variant comparison and analytics."""
        variants_performance = {
            "control": {
                "response_quality": {"average": 0.75, "sample_count": 100},
                "response_time": {"average": 2500, "sample_count": 100},
                "cost_efficiency": {"average": 0.85, "sample_count": 100}
            },
            "variant_a": {
                "response_quality": {"average": 0.82, "sample_count": 100},
                "response_time": {"average": 2200, "sample_count": 100},
                "cost_efficiency": {"average": 0.88, "sample_count": 100}
            },
            "variant_b": {
                "response_quality": {"average": 0.78, "sample_count": 100},
                "response_time": {"average": 2400, "sample_count": 100},
                "cost_efficiency": {"average": 0.82, "sample_count": 100}
            }
        }

        comparison_result = variant_manager.compare_variant_performance(variants_performance)

        assert comparison_result["success"] is True
        comparison = comparison_result["comparison"]

        # Should identify best performing variant
        assert "best_performing_variant" in comparison
        assert comparison["best_performing_variant"] == "variant_a"

        # Should calculate improvement percentages
        assert "performance_improvements" in comparison
        improvements = comparison["performance_improvements"]

        # Variant A should show improvements over control
        assert improvements["variant_a"]["response_quality"] > 0
        assert improvements["variant_a"]["response_time"] < 0  # Negative = improvement
        assert improvements["variant_a"]["cost_efficiency"] > 0

    def test_variant_traffic_allocation(self, variant_manager):
        """Test variant traffic allocation and ramp-up."""
        variant_config = {
            "variant_a": {"initial_weight": 10, "target_weight": 50, "ramp_up_days": 7},
            "variant_b": {"initial_weight": 5, "target_weight": 25, "ramp_up_days": 7},
            "control": {"initial_weight": 85, "target_weight": 25, "ramp_up_days": 7}
        }

        # Test allocation at different time points
        test_scenarios = [
            (0, {"variant_a": 10, "variant_b": 5, "control": 85}),  # Day 0
            (3.5, {"variant_a": 30, "variant_b": 15, "control": 55}),  # Midway
            (7, {"variant_a": 50, "variant_b": 25, "control": 25}),  # Final
            (10, {"variant_a": 50, "variant_b": 25, "control": 25})  # Beyond ramp-up
        ]

        for days_elapsed, expected_weights in test_scenarios:
            allocation_result = variant_manager.calculate_traffic_allocation(
                variant_config, days_elapsed
            )

            assert allocation_result["success"] is True
            allocated_weights = allocation_result["allocated_weights"]

            for variant, expected_weight in expected_weights.items():
                assert abs(allocated_weights[variant] - expected_weight) < 1  # Allow 1% tolerance


class TestResultCollectionAndAnalysis:
    """Test Result Collection and Statistical Analysis functionality."""

    @pytest.fixture
    def result_analyzer(self, mock_repository):
        """Create result analyzer instance."""
        return ABTestService(repository=mock_repository)

    def test_statistical_significance_calculation(self, result_analyzer):
        """Test statistical significance calculation."""
        # Sample data: control vs variant performance
        control_data = [0.75, 0.78, 0.72, 0.79, 0.76, 0.74, 0.77, 0.73, 0.75, 0.78]  # 10 samples
        variant_data = [0.82, 0.85, 0.79, 0.87, 0.83, 0.81, 0.84, 0.80, 0.82, 0.86]  # 10 samples

        significance_result = result_analyzer.calculate_statistical_significance(
            control_data, variant_data, alpha=0.05
        )

        assert significance_result["success"] is True
        stats = significance_result["statistics"]

        # Variant should perform better
        assert stats["variant_mean"] > stats["control_mean"]
        assert stats["improvement_percentage"] > 0

        # Should be statistically significant
        assert stats["statistically_significant"] is True
        assert stats["p_value"] < 0.05

        # Should include confidence interval
        assert "confidence_interval" in stats
        assert len(stats["confidence_interval"]) == 2

    def test_ab_test_result_aggregation(self, result_analyzer):
        """Test A/B test result aggregation from multiple sessions."""
        test_results = [
            {"variant_id": "control", "metric": "response_quality", "value": 0.75, "session_id": "s1"},
            {"variant_id": "control", "metric": "response_quality", "value": 0.78, "session_id": "s1"},
            {"variant_id": "variant_a", "metric": "response_quality", "value": 0.82, "session_id": "s2"},
            {"variant_id": "variant_a", "metric": "response_quality", "value": 0.85, "session_id": "s2"},
            {"variant_id": "control", "metric": "response_time", "value": 2500, "session_id": "s1"},
            {"variant_id": "variant_a", "metric": "response_time", "value": 2200, "session_id": "s2"}
        ]

        aggregation_result = result_analyzer.aggregate_test_results(test_results)

        assert aggregation_result["success"] is True
        aggregated = aggregation_result["aggregated_results"]

        # Should have data for both variants and metrics
        assert "control" in aggregated
        assert "variant_a" in aggregated

        control_data = aggregated["control"]
        variant_a_data = aggregated["variant_a"]

        # Control should have response_quality and response_time
        assert "response_quality" in control_data
        assert "response_time" in control_data

        # Variant A should have both metrics
        assert "response_quality" in variant_a_data
        assert "response_time" in variant_a_data

        # Response quality averages should be correct
        assert abs(control_data["response_quality"]["average"] - 0.765) < 0.001
        assert abs(variant_a_data["response_quality"]["average"] - 0.835) < 0.001

        # Sample counts should be correct
        assert control_data["response_quality"]["sample_count"] == 2
        assert variant_a_data["response_quality"]["sample_count"] == 2

    def test_winner_determination_logic(self, result_analyzer):
        """Test winner determination logic with multiple criteria."""
        test_scenarios = [
            {
                "name": "clear_winner",
                "variants": {
                    "control": {"quality": 0.75, "time": 2500, "cost": 0.85},
                    "variant_a": {"quality": 0.85, "time": 2000, "cost": 0.90},
                    "variant_b": {"quality": 0.78, "time": 2200, "cost": 0.82}
                },
                "weights": {"quality": 0.5, "time": 0.3, "cost": 0.2},
                "expected_winner": "variant_a"
            },
            {
                "name": "trade_off_decision",
                "variants": {
                    "control": {"quality": 0.80, "time": 1800, "cost": 0.75},
                    "variant_a": {"quality": 0.78, "time": 1500, "cost": 0.85}  # Faster but more expensive
                },
                "weights": {"quality": 0.4, "time": 0.3, "cost": 0.3},
                "expected_winner": "control"  # Better overall balance
            }
        ]

        for scenario in test_scenarios:
            winner_result = result_analyzer.determine_test_winner(
                scenario["variants"], scenario["weights"]
            )

            assert winner_result["success"] is True
            assert winner_result["winner"] == scenario["expected_winner"]

            # Should include detailed scoring
            assert "variant_scores" in winner_result
            assert "winning_criteria" in winner_result

    def test_confidence_interval_calculation(self, result_analyzer):
        """Test confidence interval calculation for test results."""
        sample_data = [0.75, 0.78, 0.72, 0.79, 0.76, 0.74, 0.77, 0.73, 0.75, 0.78]

        ci_result = result_analyzer.calculate_confidence_interval(sample_data, confidence_level=0.95)

        assert ci_result["success"] is True
        confidence_interval = ci_result["confidence_interval"]

        assert len(confidence_interval) == 2
        assert confidence_interval[0] < confidence_interval[1]  # Lower < Upper

        # Mean should be within confidence interval
        sample_mean = mean(sample_data)
        assert confidence_interval[0] <= sample_mean <= confidence_interval[1]

        # Should include metadata
        assert "margin_of_error" in ci_result
        assert "sample_size" in ci_result
        assert ci_result["sample_size"] == len(sample_data)

    def test_ab_test_power_analysis(self, result_analyzer):
        """Test A/B test power analysis for sample size determination."""
        test_parameters = {
            "baseline_conversion": 0.20,  # 20% baseline
            "minimum_detectable_effect": 0.03,  # 3 percentage point improvement
            "desired_power": 0.80,  # 80% power
            "significance_level": 0.05  # 5% alpha
        }

        power_result = result_analyzer.calculate_required_sample_size(test_parameters)

        assert power_result["success"] is True
        assert "required_sample_size_per_variant" in power_result
        assert "total_required_sample_size" in power_result

        # Required sample size should be reasonable
        required_size = power_result["required_sample_size_per_variant"]
        assert required_size > 100  # Should need meaningful sample
        assert required_size < 10000  # Shouldn't be impossibly large

        # Total should be 2x individual (for two variants)
        assert power_result["total_required_sample_size"] == required_size * 2

    def test_result_anomaly_detection(self, result_analyzer):
        """Test detection of anomalous results in A/B testing."""
        # Normal data with one clear outlier
        normal_data = [0.75, 0.76, 0.74, 0.77, 0.75, 0.78, 0.73, 0.76, 0.74, 0.75]
        anomalous_data = normal_data + [0.95]  # Clear outlier

        anomaly_result_normal = result_analyzer.detect_result_anomalies(normal_data)
        anomaly_result_anomalous = result_analyzer.detect_result_anomalies(anomalous_data)

        # Normal data should have no anomalies
        assert anomaly_result_normal["anomalies_detected"] is False
        assert len(anomaly_result_normal["anomalous_values"]) == 0

        # Anomalous data should detect the outlier
        assert anomaly_result_anomalous["anomalies_detected"] is True
        assert len(anomaly_result_anomalous["anomalous_values"]) >= 1
        assert 0.95 in anomaly_result_anomalous["anomalous_values"]

        # Should provide anomaly statistics
        assert "anomaly_score" in anomaly_result_anomalous
        assert "z_score" in anomaly_result_anomalous

    def test_ab_test_early_stopping(self, result_analyzer):
        """Test early stopping logic for A/B tests."""
        early_stopping_scenarios = [
            {
                "name": "significant_result_early",
                "data_points": 50,
                "effect_size": 0.20,  # Large effect
                "current_p_value": 0.001,  # Highly significant
                "should_stop": True
            },
            {
                "name": "no_effect_continue",
                "data_points": 100,
                "effect_size": 0.01,  # Small effect
                "current_p_value": 0.85,  # Not significant
                "should_stop": False
            },
            {
                "name": "moderate_effect_continue",
                "data_points": 75,
                "effect_size": 0.08,  # Moderate effect
                "current_p_value": 0.15,  # Borderline
                "should_stop": False
            }
        ]

        for scenario in early_stopping_scenarios:
            stopping_result = result_analyzer.evaluate_early_stopping(
                scenario["data_points"], scenario["effect_size"],
                scenario["current_p_value"], alpha=0.05
            )

            assert stopping_result["success"] is True
            assert stopping_result["should_stop"] == scenario["should_stop"]

            # Should include stopping criteria evaluation
            assert "stopping_criteria" in stopping_result
            criteria = stopping_result["stopping_criteria"]

            if scenario["should_stop"]:
                assert criteria["statistical_significance"] is True
            else:
                assert criteria["statistical_significance"] is False


class TestABTestLifecycle:
    """Test A/B Test Lifecycle Management functionality."""

    @pytest.fixture
    def lifecycle_manager(self, mock_repository, mock_event_bus):
        """Create lifecycle manager instance."""
        return ABTestCommandHandler(mock_repository, mock_event_bus)

    def test_ab_test_state_transitions(self, lifecycle_manager):
        """Test A/B test state transition validation."""
        test_id = str(uuid.uuid4())

        # Valid transitions
        valid_transitions = [
            ("created", "configured"),
            ("configured", "running"),
            ("running", "paused"),
            ("paused", "running"),
            ("running", "completed"),
            ("running", "stopped"),
            ("completed", "archived"),
            ("stopped", "archived")
        ]

        for from_state, to_state in valid_transitions:
            transition_result = lifecycle_manager.validate_state_transition(test_id, from_state, to_state)
            assert transition_result["valid"] is True

        # Invalid transitions
        invalid_transitions = [
            ("created", "completed"),  # Cannot skip states
            ("completed", "running"),  # Cannot restart completed test
            ("archived", "running"),   # Cannot unarchive
            ("stopped", "completed")   # Cannot complete stopped test
        ]

        for from_state, to_state in invalid_transitions:
            transition_result = lifecycle_manager.validate_state_transition(test_id, from_state, to_state)
            assert transition_result["valid"] is False
            assert "reason" in transition_result

    def test_ab_test_automation_rules(self, lifecycle_manager):
        """Test A/B test automation rules and triggers."""
        automation_config = {
            "early_stopping": {
                "enabled": True,
                "significance_threshold": 0.01,
                "minimum_samples": 100,
                "maximum_duration_days": 14
            },
            "winner_declaration": {
                "auto_declare": True,
                "confidence_threshold": 0.95,
                "minimum_improvement": 0.05
            },
            "traffic_adjustment": {
                "enabled": True,
                "adjustment_interval_hours": 24,
                "max_single_adjustment": 10  # percentage points
            }
        }

        test_state = {
            "status": "running",
            "current_sample_size": 150,
            "running_days": 5,
            "best_variant_confidence": 0.98,
            "best_variant_improvement": 0.08
        }

        automation_result = lifecycle_manager.evaluate_automation_rules(automation_config, test_state)

        assert automation_result["success"] is True
        actions = automation_result["recommended_actions"]

        # Should recommend winner declaration (high confidence, good improvement)
        winner_actions = [a for a in actions if a["action_type"] == "declare_winner"]
        assert len(winner_actions) > 0

        # Should not recommend early stopping (still within duration limits)
        stop_actions = [a for a in actions if a["action_type"] == "early_stop"]
        assert len(stop_actions) == 0

    def test_ab_test_performance_impact_assessment(self, lifecycle_manager):
        """Test A/B test performance impact assessment."""
        test_metrics = {
            "baseline_metrics": {
                "response_time_p95": 2000,
                "error_rate": 0.02,
                "cost_per_request": 0.025
            },
            "test_impact": {
                "additional_response_time": 150,  # ms
                "additional_error_rate": 0.005,
                "additional_cost_per_request": 0.003
            },
            "test_traffic_percentage": 15  # 15% of traffic
        }

        impact_result = lifecycle_manager.assess_performance_impact(test_metrics)

        assert impact_result["success"] is True
        impact = impact_result["performance_impact"]

        # Should calculate overall impact
        assert "overall_response_time_impact" in impact
        assert "overall_error_rate_impact" in impact
        assert "overall_cost_impact" in impact

        # Response time impact should be proportional to traffic
        expected_response_impact = (test_metrics["test_impact"]["additional_response_time"] *
                                  test_metrics["test_traffic_percentage"] / 100)
        assert abs(impact["overall_response_time_impact"] - expected_response_impact) < 1

    def test_ab_test_resource_cleanup(self, lifecycle_manager):
        """Test A/B test resource cleanup after completion."""
        completed_test = {
            "id": str(uuid.uuid4()),
            "status": "completed",
            "winner_variant": "variant_a",
            "resources": {
                "database_records": 1000,
                "cache_entries": 50,
                "log_files": 5,
                "temporary_storage_gb": 2.5
            },
            "retention_policy": {
                "keep_raw_data_days": 30,
                "keep_aggregated_data_days": 365,
                "archive_logs": True
            }
        }

        cleanup_result = lifecycle_manager.perform_test_cleanup(completed_test)

        assert cleanup_result["success"] is True
        cleanup_actions = cleanup_result["cleanup_actions"]

        # Should include data retention actions
        retention_actions = [a for a in cleanup_actions if "retention" in a["action_type"]]
        assert len(retention_actions) > 0

        # Should include archival actions
        archival_actions = [a for a in cleanup_actions if "archive" in a["action_type"]]
        assert len(archival_actions) > 0

        # Should calculate storage reclamation
        assert "storage_reclaimed_gb" in cleanup_result
        assert cleanup_result["storage_reclaimed_gb"] > 0

    def test_ab_test_audit_trail(self, lifecycle_manager):
        """Test comprehensive A/B test audit trail."""
        test_id = str(uuid.uuid4())

        # Simulate test lifecycle events
        events = [
            {"event": "created", "actor": "user@example.com", "timestamp": datetime.now() - timedelta(days=7)},
            {"event": "configured", "actor": "admin@example.com", "timestamp": datetime.now() - timedelta(days=7)},
            {"event": "started", "actor": "system", "timestamp": datetime.now() - timedelta(days=6)},
            {"event": "traffic_adjusted", "actor": "system", "details": {"old_weight": 20, "new_weight": 30}, "timestamp": datetime.now() - timedelta(days=4)},
            {"event": "early_stopping_evaluated", "actor": "system", "details": {"should_stop": False}, "timestamp": datetime.now() - timedelta(days=2)},
            {"event": "completed", "actor": "system", "details": {"winner": "variant_a"}, "timestamp": datetime.now()}
        ]

        for event in events:
            lifecycle_manager.record_test_event(test_id, event["event"], event["actor"],
                                             event.get("details"), event["timestamp"])

        audit_result = lifecycle_manager.get_test_audit_trail(test_id)

        assert audit_result["success"] is True
        audit_trail = audit_result["audit_trail"]

        assert len(audit_trail) == len(events)

        # Should be chronologically ordered
        for i in range(len(audit_trail) - 1):
            assert audit_trail[i]["timestamp"] <= audit_trail[i + 1]["timestamp"]

        # Should include all event types
        event_types = {event["event"] for event in audit_trail}
        expected_types = {"created", "configured", "started", "traffic_adjusted", "early_stopping_evaluated", "completed"}
        assert event_types == expected_types

        # Should include event details where provided
        traffic_adjustment = next(e for e in audit_trail if e["event"] == "traffic_adjusted")
        assert "old_weight" in traffic_adjustment["details"]
        assert "new_weight" in traffic_adjustment["details"]
