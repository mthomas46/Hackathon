"""Unit Tests for Simulation Engine in Project Simulation Service.

This module tests simulation engine capabilities including:
- Scenario execution and state management
- Performance modeling and predictive analytics
- Real-time simulation monitoring and control
- AI-powered optimization and recommendations

Tests cover the complete simulation engine infrastructure within the Project Simulation service.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from core.simulation_engine import SimulationEngine


class TestScenarioExecution:
    """Test Scenario Execution functionality."""

    @pytest.fixture
    def simulation_engine(self):
        """Create simulation engine instance."""
        return SimulationEngine()

    def test_scenario_initialization(self, simulation_engine):
        """Test scenario initialization and configuration."""
        scenario_config = {
            "scenario_id": "load_test_simulation",
            "name": "High Load Performance Test",
            "description": "Simulate high concurrent user load on API endpoints",
            "duration_seconds": 300,
            "parameters": {
                "concurrent_users": 1000,
                "ramp_up_seconds": 60,
                "target_endpoints": ["/api/documents", "/api/search"],
                "request_patterns": {
                    "read_operations": 70,
                    "write_operations": 20,
                    "search_operations": 10
                }
            },
            "success_criteria": {
                "avg_response_time_ms": 500,
                "error_rate_percent": 1.0,
                "throughput_requests_per_second": 200
            },
            "monitoring_config": {
                "metrics_collection_interval": 5,
                "alert_thresholds": {
                    "response_time_p95": 1000,
                    "error_rate": 0.05
                }
            }
        }

        init_result = simulation_engine.initialize_scenario(scenario_config)

        assert init_result["success"] is True
        assert "scenario_instance" in init_result
        assert "execution_plan" in init_result
        assert "resource_requirements" in init_result

        scenario_instance = init_result["scenario_instance"]
        assert scenario_instance["status"] == "initialized"
        assert scenario_instance["scenario_id"] == "load_test_simulation"
        assert "start_time" in scenario_instance
        assert "estimated_completion" in scenario_instance

        execution_plan = init_result["execution_plan"]
        assert "phases" in execution_plan
        assert "timeline" in execution_plan
        assert len(execution_plan["phases"]) > 0

    def test_simulation_state_management(self, simulation_engine):
        """Test simulation state management during execution."""
        scenario_id = "test_scenario_001"

        # Initialize scenario
        init_result = simulation_engine.initialize_scenario({
            "scenario_id": scenario_id,
            "duration_seconds": 60,
            "parameters": {"test_param": "value"}
        })
        assert init_result["success"] is True

        # Start execution
        start_result = simulation_engine.start_scenario(scenario_id)
        assert start_result["success"] is True
        assert start_result["status"] == "running"

        # Check state during execution
        state_result = simulation_engine.get_scenario_state(scenario_id)
        assert state_result["status"] == "running"
        assert "progress_percentage" in state_result
        assert "current_phase" in state_result
        assert "metrics" in state_result

        # Pause execution
        pause_result = simulation_engine.pause_scenario(scenario_id)
        assert pause_result["success"] is True
        assert pause_result["status"] == "paused"

        # Verify paused state
        paused_state = simulation_engine.get_scenario_state(scenario_id)
        assert paused_state["status"] == "paused"

        # Resume execution
        resume_result = simulation_engine.resume_scenario(scenario_id)
        assert resume_result["success"] is True
        assert resume_result["status"] == "running"

        # Stop execution
        stop_result = simulation_engine.stop_scenario(scenario_id)
        assert stop_result["success"] is True
        assert stop_result["status"] == "stopped"

    def test_scenario_parameter_validation(self, simulation_engine):
        """Test scenario parameter validation and constraints."""
        # Valid scenario
        valid_scenario = {
            "scenario_id": "valid_scenario",
            "parameters": {
                "concurrent_users": 100,
                "duration_seconds": 300,
                "target_endpoints": ["/api/test"],
                "success_criteria": {
                    "avg_response_time_ms": 500,
                    "error_rate_percent": 1.0
                }
            }
        }

        validation_result = simulation_engine.validate_scenario_parameters(valid_scenario)
        assert validation_result["is_valid"] is True
        assert len(validation_result["errors"]) == 0
        assert len(validation_result["warnings"]) == 0

        # Invalid scenarios
        invalid_scenarios = [
            {
                "scenario_id": "invalid_users",
                "parameters": {
                    "concurrent_users": -1,  # Invalid negative value
                    "duration_seconds": 300
                }
            },
            {
                "scenario_id": "invalid_duration",
                "parameters": {
                    "concurrent_users": 100,
                    "duration_seconds": 0  # Invalid zero duration
                }
            },
            {
                "scenario_id": "missing_criteria",
                "parameters": {
                    "concurrent_users": 100,
                    "duration_seconds": 300
                    # Missing success_criteria
                }
            }
        ]

        for invalid_scenario in invalid_scenarios:
            validation_result = simulation_engine.validate_scenario_parameters(invalid_scenario)
            assert validation_result["is_valid"] is False
            assert len(validation_result["errors"]) > 0

    def test_scenario_execution_monitoring(self, simulation_engine):
        """Test scenario execution monitoring and metrics collection."""
        scenario_id = "monitored_scenario"

        # Initialize and start scenario
        init_result = simulation_engine.initialize_scenario({
            "scenario_id": scenario_id,
            "duration_seconds": 120,
            "monitoring_config": {
                "metrics_collection_interval": 5,
                "collect_system_metrics": True,
                "collect_performance_metrics": True
            }
        })
        assert init_result["success"] is True

        start_result = simulation_engine.start_scenario(scenario_id)
        assert start_result["success"] is True

        # Collect monitoring data
        monitoring_data = simulation_engine.collect_monitoring_data(scenario_id)
        assert monitoring_data["success"] is True
        assert "metrics" in monitoring_data
        assert "system_resources" in monitoring_data
        assert "performance_indicators" in monitoring_data

        metrics = monitoring_data["metrics"]
        assert "timestamp" in metrics
        assert "scenario_progress" in metrics
        assert "active_users" in metrics

        system_resources = monitoring_data["system_resources"]
        assert "cpu_usage_percent" in system_resources
        assert "memory_usage_mb" in system_resources
        assert "disk_io" in system_resources

        performance_indicators = monitoring_data["performance_indicators"]
        assert "response_time_p50" in performance_indicators
        assert "throughput_rps" in performance_indicators
        assert "error_rate_percent" in performance_indicators

    def test_scenario_failure_handling(self, simulation_engine):
        """Test scenario failure handling and recovery."""
        scenario_id = "failure_test_scenario"

        # Initialize scenario
        init_result = simulation_engine.initialize_scenario({
            "scenario_id": scenario_id,
            "parameters": {"simulate_failures": True}
        })
        assert init_result["success"] is True

        # Simulate various failure conditions
        failure_scenarios = [
            {
                "failure_type": "resource_exhaustion",
                "failure_details": {"resource": "memory", "limit_exceeded": True},
                "expected_recovery": "scale_resources"
            },
            {
                "failure_type": "external_service_down",
                "failure_details": {"service": "database", "error": "connection_timeout"},
                "expected_recovery": "failover_to_backup"
            },
            {
                "failure_type": "data_corruption",
                "failure_details": {"component": "metrics_collector", "data_integrity": False},
                "expected_recovery": "rollback_and_retry"
            }
        ]

        for failure_scenario in failure_scenarios:
            # Inject failure
            failure_result = simulation_engine.inject_failure(scenario_id, failure_scenario)
            assert failure_result["failure_injected"] is True

            # Check failure detection
            detection_result = simulation_engine.detect_scenario_failure(scenario_id)
            assert detection_result["failure_detected"] is True
            assert detection_result["failure_type"] == failure_scenario["failure_type"]

            # Execute recovery
            recovery_result = simulation_engine.execute_failure_recovery(scenario_id, detection_result)
            assert recovery_result["recovery_attempted"] is True
            assert recovery_result["recovery_strategy"] == failure_scenario["expected_recovery"]

            # Verify recovery success
            verification_result = simulation_engine.verify_recovery_success(scenario_id)
            assert verification_result["recovery_successful"] is True


class TestPerformanceModeling:
    """Test Performance Modeling functionality."""

    @pytest.fixture
    def simulation_engine(self):
        """Create simulation engine instance."""
        return SimulationEngine()

    def test_performance_baseline_establishment(self, simulation_engine):
        """Test performance baseline establishment."""
        baseline_config = {
            "system_under_test": "api_endpoints",
            "baseline_scenarios": [
                {
                    "scenario": "light_load",
                    "concurrent_users": 10,
                    "duration_seconds": 60,
                    "target_throughput_rps": 50
                },
                {
                    "scenario": "medium_load",
                    "concurrent_users": 50,
                    "duration_seconds": 120,
                    "target_throughput_rps": 200
                },
                {
                    "scenario": "heavy_load",
                    "concurrent_users": 200,
                    "duration_seconds": 300,
                    "target_throughput_rps": 500
                }
            ],
            "performance_indicators": [
                "response_time_p50",
                "response_time_p95",
                "throughput_rps",
                "error_rate_percent",
                "cpu_usage_percent",
                "memory_usage_mb"
            ]
        }

        baseline_result = simulation_engine.establish_performance_baseline(baseline_config)

        assert baseline_result["success"] is True
        assert "baseline_metrics" in baseline_result
        assert "performance_curves" in baseline_result
        assert "bottleneck_identification" in baseline_result

        baseline_metrics = baseline_result["baseline_metrics"]
        assert len(baseline_metrics) == len(baseline_config["baseline_scenarios"])

        for scenario_metrics in baseline_metrics:
            assert "scenario" in scenario_metrics
            assert "metrics" in scenario_metrics
            assert "stability_score" in scenario_metrics

        performance_curves = baseline_result["performance_curves"]
        assert "throughput_curve" in performance_curves
        assert "latency_curve" in performance_curves
        assert "resource_usage_curves" in performance_curves

    def test_predictive_performance_modeling(self, simulation_engine):
        """Test predictive performance modeling and forecasting."""
        historical_data = {
            "time_series_data": [
                {
                    "timestamp": datetime.now() - timedelta(days=30),
                    "metrics": {
                        "concurrent_users": 50,
                        "response_time_p50": 245,
                        "throughput_rps": 180,
                        "error_rate_percent": 0.8,
                        "cpu_usage_percent": 45,
                        "memory_usage_mb": 512
                    }
                },
                {
                    "timestamp": datetime.now() - timedelta(days=20),
                    "metrics": {
                        "concurrent_users": 75,
                        "response_time_p50": 312,
                        "throughput_rps": 220,
                        "error_rate_percent": 1.2,
                        "cpu_usage_percent": 62,
                        "memory_usage_mb": 678
                    }
                },
                {
                    "timestamp": datetime.now() - timedelta(days=10),
                    "metrics": {
                        "concurrent_users": 100,
                        "response_time_p50": 387,
                        "throughput_rps": 195,
                        "error_rate_percent": 2.1,
                        "cpu_usage_percent": 78,
                        "memory_usage_mb": 823
                    }
                }
            ],
            "trend_analysis": {
                "performance_trends": {
                    "response_time_growth_rate": 0.15,  # 15% increase per period
                    "throughput_decline_rate": 0.08,    # 8% decline per period
                    "resource_usage_growth_rate": 0.22   # 22% increase per period
                }
            }
        }

        prediction_config = {
            "forecast_periods": 5,
            "prediction_models": ["linear_regression", "time_series_arima", "machine_learning"],
            "confidence_intervals": [0.80, 0.95],
            "what_if_scenarios": [
                {
                    "scenario": "infrastructure_upgrade",
                    "changes": {"cpu_cores": 2, "memory_gb": 4},
                    "expected_impact": {"performance_improvement": 0.25}
                },
                {
                    "scenario": "load_balancer_optimization",
                    "changes": {"load_distribution_algorithm": "least_connections"},
                    "expected_impact": {"throughput_improvement": 0.35}
                }
            ]
        }

        prediction_result = simulation_engine.predict_performance_trends(historical_data, prediction_config)

        assert prediction_result["success"] is True
        assert "predictions" in prediction_result
        assert "model_accuracy" in prediction_result
        assert "what_if_analysis" in prediction_result

        predictions = prediction_result["predictions"]
        assert len(predictions) == prediction_config["forecast_periods"]

        for period_prediction in predictions:
            assert "period" in period_prediction
            assert "predicted_metrics" in period_prediction
            assert "confidence_intervals" in period_prediction

        model_accuracy = prediction_result["model_accuracy"]
        for model in prediction_config["prediction_models"]:
            assert model in model_accuracy
            assert "accuracy_score" in model_accuracy[model]
            assert "mean_absolute_error" in model_accuracy[model]

        what_if_analysis = prediction_result["what_if_analysis"]
        assert len(what_if_analysis) == len(prediction_config["what_if_scenarios"])

        for scenario_analysis in what_if_analysis:
            assert "scenario" in scenario_analysis
            assert "predicted_impact" in scenario_analysis
            assert "confidence_level" in scenario_analysis

    def test_capacity_planning_and_scaling(self, simulation_engine):
        """Test capacity planning and scaling recommendations."""
        current_capacity = {
            "infrastructure": {
                "servers": 3,
                "cpu_cores_per_server": 8,
                "memory_gb_per_server": 16,
                "network_bandwidth_gbps": 10
            },
            "application": {
                "max_concurrent_users": 500,
                "current_user_load": 320,
                "peak_hour_multiplier": 1.8
            },
            "performance_baselines": {
                "response_time_p95_target": 500,
                "error_rate_target": 0.01,
                "throughput_target_rps": 300
            }
        }

        growth_projections = {
            "user_growth_scenarios": [
                {
                    "scenario": "conservative_growth",
                    "monthly_growth_rate": 0.05,  # 5% monthly growth
                    "time_horizon_months": 12
                },
                {
                    "scenario": "aggressive_growth",
                    "monthly_growth_rate": 0.15,  # 15% monthly growth
                    "time_horizon_months": 12
                }
            ],
            "feature_expansion": [
                {
                    "feature": "real_time_analytics",
                    "resource_impact": {"cpu_multiplier": 1.3, "memory_multiplier": 1.5},
                    "timeline_months": 6
                },
                {
                    "feature": "advanced_ml_models",
                    "resource_impact": {"cpu_multiplier": 2.0, "memory_multiplier": 2.2},
                    "timeline_months": 9
                }
            ]
        }

        capacity_result = simulation_engine.plan_capacity_scaling(current_capacity, growth_projections)

        assert capacity_result["success"] is True
        assert "capacity_analysis" in capacity_result
        assert "scaling_recommendations" in capacity_result
        assert "cost_projections" in capacity_result

        capacity_analysis = capacity_result["capacity_analysis"]
        assert "current_utilization" in capacity_analysis
        assert "bottlenecks_identified" in capacity_analysis
        assert "growth_projections_analysis" in capacity_analysis

        scaling_recommendations = capacity_result["scaling_recommendations"]
        assert len(scaling_recommendations) >= len(growth_projections["user_growth_scenarios"])

        for recommendation in scaling_recommendations:
            assert "scenario" in recommendation
            assert "recommended_capacity" in recommendation
            assert "timeline" in recommendation
            assert "scaling_strategy" in recommendation

        cost_projections = capacity_result["cost_projections"]
        assert "infrastructure_costs" in cost_projections
        assert "operational_costs" in cost_projections
        assert "return_on_investment" in cost_projections


class TestRealTimeMonitoring:
    """Test Real-Time Monitoring functionality."""

    @pytest.fixture
    def simulation_engine(self):
        """Create simulation engine instance."""
        return SimulationEngine()

    def test_real_time_metrics_collection(self, simulation_engine):
        """Test real-time metrics collection during simulation."""
        scenario_id = "realtime_monitoring_test"

        # Initialize scenario with real-time monitoring
        init_config = {
            "scenario_id": scenario_id,
            "real_time_monitoring": {
                "enabled": True,
                "collection_interval_seconds": 1,
                "streaming_metrics": [
                    "response_time_p50",
                    "throughput_rps",
                    "error_rate_percent",
                    "active_connections",
                    "queue_depth"
                ],
                "alerting_enabled": True,
                "alert_thresholds": {
                    "response_time_p95": 1000,
                    "error_rate_percent": 5.0,
                    "queue_depth": 100
                }
            }
        }

        init_result = simulation_engine.initialize_scenario(init_config)
        assert init_result["success"] is True

        # Start scenario
        start_result = simulation_engine.start_scenario(scenario_id)
        assert start_result["success"] is True

        # Collect real-time metrics
        realtime_metrics = simulation_engine.collect_realtime_metrics(scenario_id)
        assert realtime_metrics["success"] is True
        assert "metrics_stream" in realtime_metrics
        assert "timestamp" in realtime_metrics

        metrics_stream = realtime_metrics["metrics_stream"]
        for metric_name in init_config["real_time_monitoring"]["streaming_metrics"]:
            assert metric_name in metrics_stream

        # Test alerting
        alert_conditions = [
            {"metric": "response_time_p95", "value": 1200, "threshold": 1000},  # Above threshold
            {"metric": "error_rate_percent", "value": 2.0, "threshold": 5.0},   # Below threshold
            {"metric": "queue_depth", "value": 150, "threshold": 100}          # Above threshold
        ]

        for condition in alert_conditions:
            alert_result = simulation_engine.evaluate_metric_alert(scenario_id, condition)

            if condition["value"] > condition["threshold"]:
                assert alert_result["alert_triggered"] is True
                assert "alert_details" in alert_result
                assert alert_result["alert_details"]["severity"] in ["warning", "error", "critical"]
            else:
                assert alert_result["alert_triggered"] is False

    def test_simulation_control_and_adaptation(self, simulation_engine):
        """Test simulation control and adaptive adjustments."""
        scenario_id = "adaptive_simulation"

        # Initialize scenario with adaptive controls
        init_config = {
            "scenario_id": scenario_id,
            "adaptive_controls": {
                "enabled": True,
                "control_parameters": [
                    "concurrent_users",
                    "request_rate",
                    "think_time_seconds"
                ],
                "adaptation_rules": [
                    {
                        "condition": "response_time_p95 > 800",
                        "action": "reduce_concurrent_users",
                        "adjustment_factor": 0.8
                    },
                    {
                        "condition": "error_rate_percent > 3.0",
                        "action": "increase_think_time",
                        "adjustment_factor": 1.5
                    },
                    {
                        "condition": "throughput_rps < 50",
                        "action": "increase_request_rate",
                        "adjustment_factor": 1.2
                    }
                ],
                "adaptation_interval_seconds": 30,
                "max_adjustments_per_hour": 6
            }
        }

        init_result = simulation_engine.initialize_scenario(init_config)
        assert init_result["success"] is True

        start_result = simulation_engine.start_scenario(scenario_id)
        assert start_result["success"] is True

        # Simulate performance degradation
        degradation_event = {
            "metric": "response_time_p95",
            "value": 950,  # Above 800ms threshold
            "timestamp": datetime.now()
        }

        adaptation_result = simulation_engine.evaluate_adaptation_rules(scenario_id, degradation_event)
        assert adaptation_result["adaptation_triggered"] is True
        assert "adaptation_action" in adaptation_result

        adaptation_action = adaptation_result["adaptation_action"]
        assert adaptation_action["parameter"] == "concurrent_users"
        assert adaptation_action["adjustment_type"] == "reduction"
        assert 0.7 <= adaptation_action["adjustment_factor"] <= 0.9  # Around 0.8

        # Apply adaptation
        apply_result = simulation_engine.apply_adaptation(scenario_id, adaptation_action)
        assert apply_result["adaptation_applied"] is True
        assert "new_parameter_value" in apply_result

    def test_simulation_visualization_and_reporting(self, simulation_engine):
        """Test simulation visualization and real-time reporting."""
        scenario_id = "visualization_test"

        # Initialize scenario with visualization config
        init_config = {
            "scenario_id": scenario_id,
            "visualization_config": {
                "real_time_charts": True,
                "dashboard_components": [
                    "response_time_chart",
                    "throughput_gauge",
                    "error_rate_indicator",
                    "resource_usage_graph"
                ],
                "reporting_intervals": {
                    "summary_report": 60,      # Every minute
                    "detailed_report": 300,    # Every 5 minutes
                    "final_report": "on_completion"
                },
                "export_formats": ["json", "csv", "pdf", "html"]
            }
        }

        init_result = simulation_engine.initialize_scenario(init_config)
        assert init_result["success"] is True

        start_result = simulation_engine.start_scenario(scenario_id)
        assert start_result["success"] is True

        # Generate real-time visualization data
        viz_data = simulation_engine.generate_visualization_data(scenario_id)
        assert viz_data["success"] is True
        assert "charts_data" in viz_data
        assert "dashboard_state" in viz_data

        charts_data = viz_data["charts_data"]
        for component in init_config["visualization_config"]["dashboard_components"]:
            assert component in charts_data
            assert "data" in charts_data[component]
            assert "metadata" in charts_data[component]

        # Generate summary report
        summary_report = simulation_engine.generate_simulation_report(scenario_id, "summary")
        assert summary_report["success"] is True
        assert "report_type" in summary_report
        assert "generated_at" in summary_report
        assert "summary_data" in summary_report

        summary_data = summary_report["summary_data"]
        assert "execution_summary" in summary_data
        assert "performance_summary" in summary_data
        assert "key_findings" in summary_data

        # Test report export
        for export_format in init_config["visualization_config"]["export_formats"]:
            export_result = simulation_engine.export_simulation_report(scenario_id, export_format)
            assert export_result["success"] is True
            assert "export_path" in export_result
            assert "file_size_bytes" in export_result
            assert export_result["format"] == export_format


class TestAIPoweredOptimization:
    """Test AI-Powered Optimization functionality."""

    @pytest.fixture
    def simulation_engine(self):
        """Create simulation engine instance."""
        return SimulationEngine()

    def test_scenario_optimization_with_ai(self, simulation_engine):
        """Test AI-powered scenario optimization."""
        scenario_config = {
            "scenario_id": "ai_optimized_scenario",
            "base_config": {
                "concurrent_users": 100,
                "duration_seconds": 300,
                "target_endpoints": ["/api/search", "/api/documents"]
            },
            "optimization_goals": {
                "primary_goal": "maximize_throughput",
                "secondary_goals": ["minimize_response_time", "minimize_error_rate"],
                "constraints": {
                    "max_response_time_p95": 800,
                    "max_error_rate_percent": 2.0,
                    "resource_budget": {"cpu_percent": 80, "memory_mb": 1024}
                }
            },
            "ai_optimization_config": {
                "enabled": True,
                "optimization_algorithm": "reinforcement_learning",
                "exploration_rate": 0.1,
                "learning_iterations": 10,
                "parameter_ranges": {
                    "concurrent_users": [50, 200],
                    "think_time_seconds": [1, 10],
                    "request_distribution": ["uniform", "poisson", "exponential"]
                }
            }
        }

        optimization_result = simulation_engine.optimize_scenario_with_ai(scenario_config)

        assert optimization_result["success"] is True
        assert "optimized_config" in optimization_result
        assert "optimization_analysis" in optimization_result
        assert "performance_projections" in optimization_result

        optimized_config = optimization_result["optimized_config"]
        assert "ai_optimized_parameters" in optimized_config
        assert "expected_improvements" in optimized_config

        ai_params = optimized_config["ai_optimized_parameters"]
        assert "concurrent_users" in ai_params
        assert "think_time_seconds" in ai_params
        assert "request_distribution" in ai_params

        analysis = optimization_result["optimization_analysis"]
        assert "optimization_iterations" in analysis
        assert "best_configuration_found" in analysis
        assert "parameter_importance" in analysis

        projections = optimization_result["performance_projections"]
        assert "optimized_throughput_rps" in projections
        assert "optimized_response_time_p50" in projections
        assert "improvement_percentages" in projections

    def test_anomaly_detection_and_alerting(self, simulation_engine):
        """Test AI-powered anomaly detection and intelligent alerting."""
        monitoring_data = {
            "scenario_id": "anomaly_detection_test",
            "metrics_stream": [
                {
                    "timestamp": datetime.now() - timedelta(minutes=10),
                    "response_time_p50": 245,
                    "throughput_rps": 180,
                    "error_rate_percent": 0.8
                },
                {
                    "timestamp": datetime.now() - timedelta(minutes=9),
                    "response_time_p50": 267,
                    "throughput_rps": 175,
                    "error_rate_percent": 0.9
                },
                {
                    "timestamp": datetime.now() - timedelta(minutes=8),
                    "response_time_p50": 289,
                    "throughput_rps": 168,
                    "error_rate_percent": 1.1
                },
                {
                    "timestamp": datetime.now() - timedelta(minutes=7),
                    "response_time_p50": 1450,  # Anomalous spike
                    "throughput_rps": 45,       # Anomalous drop
                    "error_rate_percent": 15.2  # Anomalous spike
                },
                {
                    "timestamp": datetime.now() - timedelta(minutes=6),
                    "response_time_p50": 267,
                    "throughput_rps": 172,
                    "error_rate_percent": 0.9
                }
            ],
            "baseline_statistics": {
                "response_time_p50": {"mean": 250, "std": 30},
                "throughput_rps": {"mean": 175, "std": 15},
                "error_rate_percent": {"mean": 1.0, "std": 0.3}
            }
        }

        anomaly_result = simulation_engine.detect_anomalies_with_ai(monitoring_data)

        assert anomaly_result["success"] is True
        assert "anomalies_detected" in anomaly_result
        assert "anomaly_analysis" in anomaly_result
        assert "alert_recommendations" in anomaly_result

        anomalies = anomaly_result["anomalies_detected"]
        assert len(anomalies) >= 1  # Should detect the spike/drop at minute 7

        # Verify anomaly detection for the spike
        spike_anomalies = [a for a in anomalies if a["timestamp"] == datetime.now() - timedelta(minutes=7)]
        assert len(spike_anomalies) >= 2  # Response time and throughput anomalies

        for anomaly in spike_anomalies:
            assert "metric" in anomaly
            assert "severity" in anomaly
            assert "confidence" in anomaly
            assert anomaly["confidence"] > 0.8  # High confidence detection

        analysis = anomaly_result["anomaly_analysis"]
        assert "anomaly_patterns" in analysis
        assert "root_cause_hypotheses" in analysis

        alerts = anomaly_result["alert_recommendations"]
        assert len(alerts) > 0

        # Should recommend alerts for critical anomalies
        critical_alerts = [a for a in alerts if a["severity"] == "critical"]
        assert len(critical_alerts) >= 1

    def test_predictive_failure_prevention(self, simulation_engine):
        """Test predictive failure prevention using AI."""
        predictive_data = {
            "scenario_id": "predictive_maintenance_test",
            "historical_failures": [
                {
                    "timestamp": datetime.now() - timedelta(days=30),
                    "failure_type": "memory_exhaustion",
                    "leading_indicators": {
                        "memory_usage_mb": 1800,
                        "memory_growth_rate": 15.5,
                        "gc_pause_time_ms": 250
                    },
                    "time_to_failure_minutes": 45
                },
                {
                    "timestamp": datetime.now() - timedelta(days=15),
                    "failure_type": "database_connection_pool_exhausted",
                    "leading_indicators": {
                        "active_connections": 95,
                        "connection_wait_time_ms": 1200,
                        "failed_connection_attempts": 25
                    },
                    "time_to_failure_minutes": 30
                }
            ],
            "current_metrics": {
                "memory_usage_mb": 1650,
                "memory_growth_rate": 12.3,
                "gc_pause_time_ms": 180,
                "active_connections": 85,
                "connection_wait_time_ms": 800,
                "failed_connection_attempts": 5
            },
            "prediction_horizon_minutes": 120
        }

        prediction_result = simulation_engine.predict_failures_with_ai(predictive_data)

        assert prediction_result["success"] is True
        assert "failure_predictions" in prediction_result
        assert "preventive_actions" in prediction_result
        assert "risk_assessment" in prediction_result

        predictions = prediction_result["failure_predictions"]
        assert len(predictions) >= 1

        # Should predict potential memory issues
        memory_predictions = [p for p in predictions if "memory" in p["failure_type"].lower()]
        assert len(memory_predictions) >= 1

        for prediction in memory_predictions:
            assert "failure_type" in prediction
            assert "probability" in prediction
            assert "predicted_time_to_failure_minutes" in prediction
            assert "confidence_level" in prediction

        preventive_actions = prediction_result["preventive_actions"]
        assert len(preventive_actions) >= 1

        for action in preventive_actions:
            assert "action_type" in action
            assert "target_failure_type" in action
            assert "expected_effectiveness" in action
            assert "implementation_complexity" in action

        risk_assessment = prediction_result["risk_assessment"]
        assert "overall_risk_score" in risk_assessment
        assert "risk_trend" in risk_assessment
        assert "critical_time_windows" in risk_assessment

    def test_simulation_scenario_recommendation(self, simulation_engine):
        """Test AI-powered simulation scenario recommendations."""
        context_data = {
            "system_context": {
                "architecture": "microservices",
                "technologies": ["kubernetes", "docker", "postgresql", "redis"],
                "current_load": {"avg_rps": 150, "peak_rps": 300},
                "known_issues": ["intermittent_db_timeouts", "memory_leaks_in_worker_processes"]
            },
            "business_context": {
                "upcoming_events": [
                    {
                        "event": "product_launch",
                        "expected_traffic_increase": 3.0,
                        "timeline_days": 30
                    },
                    {
                        "event": "holiday_season",
                        "expected_traffic_increase": 2.5,
                        "timeline_days": 60
                    }
                ],
                "performance_requirements": {
                    "max_response_time_ms": 500,
                    "availability_target": 0.999,
                    "error_budget_percent": 0.1
                }
            },
            "historical_data": {
                "past_incidents": [
                    {
                        "incident": "database_overload",
                        "trigger": "traffic_spike",
                        "impact": "30_minute_outage",
                        "frequency": "monthly"
                    },
                    {
                        "incident": "memory_exhaustion",
                        "trigger": "memory_leak_under_load",
                        "impact": "service_restart_required",
                        "frequency": "weekly"
                    }
                ]
            }
        }

        recommendation_result = simulation_engine.recommend_simulation_scenarios(context_data)

        assert recommendation_result["success"] is True
        assert "recommended_scenarios" in recommendation_result
        assert "scenario_prioritization" in recommendation_result
        assert "expected_business_value" in recommendation_result

        recommended_scenarios = recommendation_result["recommended_scenarios"]
        assert len(recommended_scenarios) >= 3  # Should recommend multiple scenarios

        for scenario in recommended_scenarios:
            assert "scenario_type" in scenario
            assert "description" in scenario
            assert "relevance_score" in scenario
            assert "expected_insights" in scenario
            assert "resource_requirements" in scenario

        prioritization = recommendation_result["scenario_prioritization"]
        assert "priority_order" in prioritization
        assert "rationale" in prioritization

        business_value = recommendation_result["expected_business_value"]
        assert "risk_mitigation_value" in business_value
        assert "performance_optimization_value" in business_value
        assert "confidence_level" in business_value
