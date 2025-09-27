"""Unit tests for simulation-dashboard domain entities."""

import pytest
from datetime import datetime, timezone, timedelta

from services.simulation_dashboard.domain.entities.simulation import Simulation, SimulationStatus, SimulationType
from services.simulation_dashboard.domain.entities.ai_insight import AIInsight, InsightType, InsightSeverity
from services.simulation_dashboard.domain.entities.analytics_result import AnalyticsResult, AnalyticsType
from services.simulation_dashboard.domain.entities.audit_log import AuditLog, AuditAction
from services.simulation_dashboard.domain.entities.configuration import Configuration


class TestSimulation:
    """Test cases for Simulation entity."""

    def test_simulation_creation(self):
        """Test basic Simulation creation."""
        sim = Simulation(
            id="sim-123",
            name="Test Simulation",
            simulation_type=SimulationType.PROJECT_SIMULATION
        )

        assert sim.id == "sim-123"
        assert sim.name == "Test Simulation"
        assert sim.simulation_type == SimulationType.PROJECT_SIMULATION
        assert sim.status == SimulationStatus.CREATED
        assert sim.progress_percentage == 0.0

    def test_simulation_validation(self):
        """Test Simulation validation rules."""
        # Valid simulation
        valid_sim = Simulation(
            id="valid-sim",
            name="Valid Simulation",
            simulation_type=SimulationType.RISK_ANALYSIS
        )
        assert valid_sim.id == "valid-sim"

        # Empty ID should raise error
        with pytest.raises(ValueError):
            Simulation(
                id="",
                name="Invalid Simulation",
                simulation_type=SimulationType.PROJECT_SIMULATION
            )

        # Empty name should raise error
        with pytest.raises(ValueError):
            Simulation(
                id="invalid-sim",
                name="",
                simulation_type=SimulationType.PROJECT_SIMULATION
            )

    def test_simulation_state_transitions(self):
        """Test simulation state transitions."""
        sim = Simulation(
            id="state-test",
            name="State Test Simulation",
            simulation_type=SimulationType.PROJECT_SIMULATION
        )

        # Initial state
        assert sim.status == SimulationStatus.CREATED
        assert not sim.is_running()
        assert not sim.is_completed()

        # Start simulation
        sim.start_simulation()
        assert sim.status == SimulationStatus.RUNNING
        assert sim.is_running()

        # Update progress
        sim.update_progress(50.0, "Halfway complete")
        assert sim.progress_percentage == 50.0

        # Complete simulation
        results = {"outcome": "success", "metrics": {"efficiency": 0.85}}
        sim.complete_simulation(results)
        assert sim.status == SimulationStatus.COMPLETED
        assert sim.is_completed()
        assert sim.results == results

    def test_simulation_failure_handling(self):
        """Test simulation failure handling."""
        sim = Simulation(
            id="failure-test",
            name="Failure Test",
            simulation_type=SimulationType.PROJECT_SIMULATION
        )

        sim.start_simulation()
        sim.fail_simulation("Database connection timeout")

        assert sim.status == SimulationStatus.FAILED
        assert sim.error_message == "Database connection timeout"
        assert not sim.is_running()
        assert not sim.is_completed()

    def test_simulation_duration_calculation(self):
        """Test simulation duration calculation."""
        sim = Simulation(
            id="duration-test",
            name="Duration Test",
            simulation_type=SimulationType.PROJECT_SIMULATION
        )

        # Not started simulation
        assert sim.get_duration_seconds() is None

        # Started but not completed
        sim.start_simulation()
        duration = sim.get_duration_seconds()
        assert duration is not None
        assert duration >= 0

    def test_simulation_serialization(self):
        """Test simulation serialization."""
        sim = Simulation(
            id="serialize-test",
            name="Serialization Test",
            simulation_type=SimulationType.RISK_ANALYSIS,
            description="Test simulation for serialization",
            tags=["test", "serialization"]
        )

        data = sim.to_dict()
        assert data["id"] == "serialize-test"
        assert data["name"] == "Serialization Test"
        assert data["simulation_type"] == "risk_analysis"
        assert data["description"] == "Test simulation for serialization"
        assert "test" in data["tags"]


class TestAIInsight:
    """Test cases for AIInsight entity."""

    def test_ai_insight_creation(self):
        """Test basic AIInsight creation."""
        insight = AIInsight(
            id="insight-123",
            title="Performance Optimization Opportunity",
            description="Analysis shows 15% performance improvement possible",
            insight_type=InsightType.PRESCRIPTIVE,
            severity=InsightSeverity.HIGH,
            confidence_score=0.89
        )

        assert insight.id == "insight-123"
        assert insight.title == "Performance Optimization Opportunity"
        assert insight.confidence_score == 0.89
        assert insight.is_high_confidence()

    def test_ai_insight_validation(self):
        """Test AIInsight validation rules."""
        # Valid insight
        valid_insight = AIInsight(
            id="valid-insight",
            title="Valid Insight",
            description="Valid description",
            insight_type=InsightType.DIAGNOSTIC,
            severity=InsightSeverity.MEDIUM,
            confidence_score=0.75
        )
        assert valid_insight.id == "valid-insight"

        # Empty title should raise error
        with pytest.raises(ValueError):
            AIInsight(
                id="invalid-insight",
                title="",
                description="Description",
                insight_type=InsightType.DESCRIPTIVE,
                severity=InsightSeverity.LOW,
                confidence_score=0.5
            )

        # Invalid confidence score
        with pytest.raises(ValueError):
            AIInsight(
                id="invalid-confidence",
                title="Invalid Confidence",
                description="Description",
                insight_type=InsightType.PREDICTIVE,
                severity=InsightSeverity.HIGH,
                confidence_score=1.5  # Invalid: > 1.0
            )

    def test_ai_insight_action_tracking(self):
        """Test AI insight action tracking."""
        insight = AIInsight(
            id="action-test",
            title="Action Test Insight",
            description="Test action tracking",
            insight_type=InsightType.PRESCRIPTIVE,
            severity=InsightSeverity.MEDIUM,
            confidence_score=0.8,
            is_actionable=True
        )

        assert not insight.action_taken
        assert insight.is_actionable

        insight.mark_action_taken()

        assert insight.action_taken
        assert insight.action_timestamp is not None

    def test_ai_insight_priority_calculation(self):
        """Test AI insight priority calculation."""
        # High severity, high confidence
        high_priority = AIInsight(
            id="high-pri",
            title="High Priority",
            description="Critical issue",
            insight_type=InsightType.ANOMALY,
            severity=InsightSeverity.CRITICAL,
            confidence_score=0.95
        )

        # Low severity, low confidence
        low_priority = AIInsight(
            id="low-pri",
            title="Low Priority",
            description="Minor observation",
            insight_type=InsightType.DESCRIPTIVE,
            severity=InsightSeverity.LOW,
            confidence_score=0.3
        )

        assert high_priority.get_priority_score() > low_priority.get_priority_score()

    def test_ai_insight_recommendations(self):
        """Test AI insight recommendations management."""
        insight = AIInsight(
            id="rec-test",
            title="Recommendation Test",
            description="Test recommendations",
            insight_type=InsightType.PRESCRIPTIVE,
            severity=InsightSeverity.MEDIUM,
            confidence_score=0.7
        )

        # Add recommendations
        insight.add_recommendation("Increase cache size")
        insight.add_recommendation("Optimize database queries")

        assert len(insight.recommendations) == 2
        assert "Increase cache size" in insight.recommendations

        # Remove recommendation
        insight.remove_recommendation("Increase cache size")
        assert len(insight.recommendations) == 1
        assert "Increase cache size" not in insight.recommendations


class TestAnalyticsResult:
    """Test cases for AnalyticsResult entity."""

    def test_analytics_result_creation(self):
        """Test basic AnalyticsResult creation."""
        result = AnalyticsResult(
            id="analytics-123",
            analytics_type=AnalyticsType.PREDICTIVE,
            simulation_id="sim-456",
            results={"prediction": "positive", "confidence": 0.85}
        )

        assert result.id == "analytics-123"
        assert result.analytics_type == AnalyticsType.PREDICTIVE
        assert result.simulation_id == "sim-456"
        assert result.status == "completed"

    def test_analytics_result_visualizations(self):
        """Test analytics result visualization management."""
        result = AnalyticsResult(
            id="viz-test",
            analytics_type=AnalyticsType.DIAGNOSTIC,
            results={"diagnosis": "bottleneck_found"}
        )

        # Add visualization
        result.add_visualization(
            "chart",
            {"type": "bar", "data": [1, 2, 3, 4]}
        )

        assert len(result.visualizations) == 1
        assert result.visualizations[0]["type"] == "chart"
        assert result.visualizations[0]["data"]["type"] == "bar"

    def test_analytics_result_updates(self):
        """Test analytics result updates."""
        result = AnalyticsResult(
            id="update-test",
            analytics_type=AnalyticsType.CAUSAL,
            results={"initial": "data"}
        )

        # Update results
        result.update_results({"additional": "insights", "correlation": 0.95})

        assert result.results["initial"] == "data"
        assert result.results["additional"] == "insights"
        assert result.results["correlation"] == 0.95


class TestAuditLog:
    """Test cases for AuditLog entity."""

    def test_audit_log_creation(self):
        """Test basic AuditLog creation."""
        log = AuditLog(
            id="audit-123",
            user_id="user-456",
            action=AuditAction.UPDATE,
            resource_type="simulation",
            resource_id="sim-789",
            details={"field": "status", "old_value": "running", "new_value": "completed"}
        )

        assert log.id == "audit-123"
        assert log.user_id == "user-456"
        assert log.action == AuditAction.UPDATE
        assert log.resource_type == "simulation"
        assert log.resource_id == "sim-789"
        assert log.details["field"] == "status"

    def test_audit_log_validation(self):
        """Test AuditLog validation rules."""
        # Valid log
        valid_log = AuditLog(
            id="valid-audit",
            user_id="user-123",
            action=AuditAction.CREATE,
            resource_type="simulation",
            resource_id="sim-456"
        )
        assert valid_log.id == "valid-audit"

        # Empty user_id should raise error
        with pytest.raises(ValueError):
            AuditLog(
                id="invalid-audit",
                user_id="",
                action=AuditAction.VIEW,
                resource_type="simulation",
                resource_id="sim-123"
            )


class TestConfiguration:
    """Test cases for Configuration entity."""

    def test_configuration_creation(self):
        """Test basic Configuration creation."""
        config = Configuration(
            id="config-123",
            name="Database Configuration",
            category="database",
            settings={"host": "localhost", "port": 5432, "pool_size": 10}
        )

        assert config.id == "config-123"
        assert config.name == "Database Configuration"
        assert config.category == "database"
        assert config.is_active is True

    def test_configuration_validation(self):
        """Test Configuration validation rules."""
        # Valid configuration
        valid_config = Configuration(
            id="valid-config",
            name="Valid Config",
            category="test"
        )
        assert valid_config.id == "valid-config"

        # Empty name should raise error
        with pytest.raises(ValueError):
            Configuration(
                id="invalid-config",
                name="",
                category="test"
            )

    def test_configuration_settings_management(self):
        """Test configuration settings management."""
        config = Configuration(
            id="settings-test",
            name="Settings Test",
            category="test"
        )

        # Set and get settings
        config.set_setting("timeout", 30)
        config.set_setting("retries", 3)

        assert config.get_setting("timeout") == 30
        assert config.get_setting("retries") == 3
        assert config.get_setting("nonexistent", "default") == "default"

    def test_configuration_serialization(self):
        """Test configuration serialization."""
        config = Configuration(
            id="serialize-config",
            name="Serialization Test",
            category="test",
            settings={"key": "value", "number": 42}
        )

        data = config.to_dict()
        assert data["id"] == "serialize-config"
        assert data["name"] == "Serialization Test"
        assert data["category"] == "test"
        assert data["settings"]["key"] == "value"
        assert data["settings"]["number"] == 42


class TestEntityIntegration:
    """Integration tests for domain entities working together."""

    def test_simulation_and_insight_integration(self):
        """Test Simulation and AIInsight working together."""
        # Create simulation
        sim = Simulation(
            id="integration-sim",
            name="Integration Test Simulation",
            simulation_type=SimulationType.PROJECT_SIMULATION
        )

        # Create insight related to simulation
        insight = AIInsight(
            id="integration-insight",
            title="Simulation Optimization",
            description="Found optimization opportunity",
            insight_type=InsightType.PRESCRIPTIVE,
            severity=InsightSeverity.MEDIUM,
            confidence_score=0.82,
            simulation_id=sim.id
        )

        # Verify relationship
        assert insight.simulation_id == sim.id
        assert sim.id == insight.simulation_id

        # Test insight priority for simulation context
        assert insight.is_high_confidence()
        assert insight.requires_attention()

    def test_audit_log_tracking(self):
        """Test audit logging across entities."""
        # Create simulation
        sim = Simulation(
            id="audit-sim",
            name="Audit Test Simulation",
            simulation_type=SimulationType.RISK_ANALYSIS
        )

        # Create audit log for simulation creation
        audit_log = AuditLog(
            id="audit-log-1",
            user_id="user-123",
            action=AuditAction.CREATE,
            resource_type="simulation",
            resource_id=sim.id,
            details={"simulation_type": sim.simulation_type.value}
        )

        # Verify audit relationship
        assert audit_log.resource_type == "simulation"
        assert audit_log.resource_id == sim.id
        assert audit_log.action == AuditAction.CREATE
