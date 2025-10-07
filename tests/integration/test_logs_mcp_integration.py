"""Integration tests for Logs MCP system."""

import sys
from pathlib import Path

# Add services directory to path
services_path = Path(__file__).parent.parent.parent / "services"
sys.path.insert(0, str(services_path))

import pytest
from datetime import datetime, timedelta
from mcp_logs.src.log_processor import LogProcessor, LogEntry, LogLevel
from mcp_logs.src.pattern_detector import PatternDetector, PatternType
from mcp_logs.src.anomaly_detector import AnomalyDetector, AnomalyType
from mcp_logs.src.root_cause_analyzer import RootCauseAnalyzer
from mcp_logs.src.predictive_maintenance import PredictiveMaintenance


class TestLogsMCPIntegration:
    """Integration tests for complete Logs MCP workflow."""
    
    @pytest.fixture
    def processor(self):
        """Create log processor."""
        return LogProcessor()
    
    @pytest.fixture
    def pattern_detector(self):
        """Create pattern detector."""
        return PatternDetector()
    
    @pytest.fixture
    def anomaly_detector(self):
        """Create anomaly detector."""
        return AnomalyDetector()
    
    @pytest.fixture
    def root_cause_analyzer(self):
        """Create root cause analyzer."""
        return RootCauseAnalyzer()
    
    @pytest.fixture
    def predictive_maintenance(self):
        """Create predictive maintenance."""
        return PredictiveMaintenance()
    
    @pytest.fixture
    def sample_logs(self):
        """Create sample log entries for testing."""
        base_time = datetime.now()
        
        return [
            LogEntry(
                timestamp=base_time,
                level=LogLevel.INFO,
                service="api-gateway",
                source="app.log",
                message="Request received"
            ),
            LogEntry(
                timestamp=base_time + timedelta(seconds=1),
                level=LogLevel.ERROR,
                service="api-gateway",
                source="app.log",
                message="Database connection failed"
            ),
            LogEntry(
                timestamp=base_time + timedelta(seconds=2),
                level=LogLevel.ERROR,
                service="user-service",
                source="app.log",
                message="Database connection failed"
            ),
            LogEntry(
                timestamp=base_time + timedelta(seconds=3),
                level=LogLevel.ERROR,
                service="api-gateway",
                source="app.log",
                message="Database connection failed"
            ),
            LogEntry(
                timestamp=base_time + timedelta(seconds=5),
                level=LogLevel.WARNING,
                service="api-gateway",
                source="app.log",
                message="Slow query detected",
                metadata={"duration_ms": 1500}
            ),
        ]
    
    def test_complete_log_analysis_workflow(
        self,
        processor,
        pattern_detector,
        anomaly_detector,
        sample_logs
    ):
        """Test complete log analysis workflow."""
        # Step 1: Process logs
        filtered = processor.filter_logs(sample_logs, level=LogLevel.ERROR)
        assert len(filtered) == 3
        
        # Step 2: Detect patterns
        result = pattern_detector.detect_patterns(sample_logs)
        assert result.patterns_found > 0
        
        # Check for repeated error pattern
        repeated_errors = [
            p for p in result.patterns
            if p.type == PatternType.REPEATED_ERROR
        ]
        assert len(repeated_errors) > 0
        assert repeated_errors[0].occurrences >= 2
        
        # Step 3: Detect anomalies
        baseline = {"error_rate": 0.1, "std_dev": 0.05}
        current_error_rate = len(filtered) / len(sample_logs)
        
        anomaly = anomaly_detector.detect_anomaly(
            "error_rate",
            current_error_rate,
            baseline
        )
        
        assert anomaly is not None
        assert isinstance(anomaly.score, float)
    
    @pytest.mark.asyncio
    async def test_incident_investigation_workflow(
        self,
        root_cause_analyzer,
        sample_logs
    ):
        """Test complete incident investigation workflow."""
        # Analyze incident
        analysis = await root_cause_analyzer.analyze_incident(
            "INC-001",
            sample_logs
        )
        
        # Verify analysis components
        assert analysis.incident_id == "INC-001"
        assert analysis.timeline is not None
        assert len(analysis.timeline.events) == len(sample_logs)
        
        # Check for root cause
        if analysis.root_cause:
            assert analysis.root_cause.confidence > 0
            assert analysis.root_cause.category in [
                "database", "network", "performance", "resource", "unknown"
            ]
        
        # Check contributing factors
        assert isinstance(analysis.contributing_factors, list)
        
        # Check recommendations
        assert isinstance(analysis.recommendations, list)
    
    def test_predictive_maintenance_workflow(self, predictive_maintenance):
        """Test predictive maintenance workflow."""
        # Simulate increasing error rate
        base_time = datetime.now()
        timestamps = [base_time + timedelta(hours=i) for i in range(24)]
        values = [0.1 + (i * 0.02) for i in range(24)]  # Increasing trend
        
        # Predict failure
        prediction = predictive_maintenance.predict_failure(
            "api-gateway",
            "error_rate",
            timestamps,
            values
        )
        
        assert prediction.service == "api-gateway"
        assert prediction.metric == "error_rate"
        assert prediction.likely_failure is True
        assert prediction.confidence > 0
        assert prediction.estimated_time_to_failure is not None
        
        # Get recommended actions
        actions = predictive_maintenance.recommend_actions(prediction)
        assert len(actions) > 0
        assert all(action.priority in ["low", "medium", "high", "critical"] for action in actions)
    
    def test_cascading_failure_detection(
        self,
        processor,
        pattern_detector
    ):
        """Test detection of cascading failures across services."""
        base_time = datetime.now()
        
        # Create cascading failure scenario
        cascading_logs = [
            LogEntry(base_time, LogLevel.ERROR, "database", "app.log", "Connection timeout"),
            LogEntry(base_time + timedelta(seconds=2), LogLevel.ERROR, "api-gateway", "app.log", "Database unavailable"),
            LogEntry(base_time + timedelta(seconds=3), LogLevel.ERROR, "user-service", "app.log", "API call failed"),
        ]
        
        # Detect patterns
        result = pattern_detector.detect_patterns(cascading_logs)
        
        # Check for cascading failure pattern
        cascading = [
            p for p in result.patterns
            if p.type == PatternType.CASCADING_FAILURE
        ]
        
        assert len(cascading) > 0
        assert len(cascading[0].affected_services) >= 2
        assert cascading[0].severity == "critical"
    
    def test_memory_leak_detection(self, anomaly_detector):
        """Test memory leak detection."""
        base_time = datetime.now()
        
        # Simulate gradual memory increase
        timestamps = [base_time + timedelta(hours=i) for i in range(12)]
        memory_values = [50.0 + (i * 5) for i in range(12)]  # Gradual increase
        
        # Detect trend anomaly
        result = anomaly_detector.detect_trend_anomaly(
            "memory_usage",
            timestamps,
            memory_values
        )
        
        assert result.is_anomaly is True
        assert result.type == AnomalyType.MEMORY_LEAK
        assert result.severity in ["high", "critical"]
        assert "leak" in result.description.lower()
    
    def test_error_spike_detection(self, pattern_detector):
        """Test error spike detection."""
        base_time = datetime.now()
        minute = base_time.replace(second=0, microsecond=0)
        
        # Create error spike (10 errors in 1 minute)
        spike_logs = [
            LogEntry(
                minute + timedelta(seconds=i * 5),
                LogLevel.ERROR,
                "api-gateway",
                "app.log",
                f"Error {i}"
            )
            for i in range(10)
        ]
        
        # Detect patterns
        result = pattern_detector.detect_patterns(spike_logs)
        
        # Check for error spike
        spikes = [p for p in result.patterns if p.type == PatternType.ERROR_SPIKE]
        assert len(spikes) > 0
        assert spikes[0].severity == "high"
        assert spikes[0].occurrences >= 5
    
    @pytest.mark.asyncio
    async def test_correlation_analysis(self, root_cause_analyzer):
        """Test event correlation analysis."""
        base_time = datetime.now()
        
        # Create correlated events
        logs = [
            LogEntry(base_time, LogLevel.ERROR, "database", "app.log", "Query timeout"),
            LogEntry(base_time + timedelta(seconds=5), LogLevel.ERROR, "api-gateway", "app.log", "Query timeout"),
        ]
        
        # Identify correlations
        correlations = await root_cause_analyzer.identify_correlations(logs)
        
        assert len(correlations) > 0
        assert correlations[0].score > 0
        assert correlations[0].reason != ""
    
    def test_trend_analysis_stable_metrics(self, predictive_maintenance):
        """Test trend analysis with stable metrics."""
        base_time = datetime.now()
        
        # Stable metrics
        timestamps = [base_time + timedelta(hours=i) for i in range(10)]
        values = [0.5] * 10  # Flat line
        
        # Analyze trend
        trend = predictive_maintenance.analyze_trend(
            "cpu_usage",
            timestamps,
            values
        )
        
        assert trend.direction == "stable"
        assert abs(trend.slope) < 0.1
    
    def test_aggregation_and_filtering(self, processor):
        """Test log aggregation and filtering."""
        base_time = datetime.now()
        
        logs = [
            LogEntry(base_time, LogLevel.INFO, "service-a", "app.log", "Info message"),
            LogEntry(base_time + timedelta(seconds=1), LogLevel.ERROR, "service-a", "app.log", "Error 1"),
            LogEntry(base_time + timedelta(seconds=2), LogLevel.ERROR, "service-b", "app.log", "Error 2"),
            LogEntry(base_time + timedelta(seconds=3), LogLevel.WARNING, "service-a", "app.log", "Warning"),
        ]
        
        # Aggregate by service
        aggregated = processor.aggregate_logs(logs, by="service")
        
        assert "service-a" in aggregated
        assert "service-b" in aggregated
        assert aggregated["service-a"] == 3
        assert aggregated["service-b"] == 1
        
        # Filter by level
        errors_only = processor.filter_logs(logs, level=LogLevel.ERROR)
        assert len(errors_only) == 2
        assert all(log.level == LogLevel.ERROR for log in errors_only)
    
    def test_latency_spike_detection(self, anomaly_detector):
        """Test latency spike detection."""
        # Normal latency
        baseline = {"p95": 100.0, "p99": 200.0}
        
        # Spike scenario
        current = {"p95": 250.0, "p99": 450.0}  # 150% increase
        
        result = anomaly_detector.detect_latency_anomaly(current, baseline)
        
        assert result.is_anomaly is True
        assert result.type == AnomalyType.LATENCY_SPIKE
        assert result.severity in ["high", "critical"]
    
    @pytest.mark.asyncio
    async def test_end_to_end_incident_response(
        self,
        processor,
        pattern_detector,
        anomaly_detector,
        root_cause_analyzer,
        predictive_maintenance
    ):
        """Test complete end-to-end incident response workflow."""
        base_time = datetime.now()
        
        # Simulate incident logs
        incident_logs = []
        
        # Phase 1: Warning signs
        for i in range(5):
            incident_logs.append(LogEntry(
                base_time + timedelta(minutes=i),
                LogLevel.WARNING,
                "api-gateway",
                "app.log",
                "High memory usage",
                metadata={"memory_pct": 70 + i * 5}
            ))
        
        # Phase 2: Errors start
        for i in range(10):
            incident_logs.append(LogEntry(
                base_time + timedelta(minutes=5 + i),
                LogLevel.ERROR,
                "api-gateway",
                "app.log",
                "Out of memory error"
            ))
        
        # Phase 3: Cascading to other services
        incident_logs.append(LogEntry(
            base_time + timedelta(minutes=15),
            LogLevel.ERROR,
            "user-service",
            "app.log",
            "API gateway unavailable"
        ))
        
        # Step 1: Process and filter
        error_logs = processor.filter_logs(incident_logs, level=LogLevel.ERROR)
        assert len(error_logs) > 0
        
        # Step 2: Detect patterns
        patterns = pattern_detector.detect_patterns(incident_logs)
        assert patterns.patterns_found > 0
        
        # Step 3: Analyze root cause
        analysis = await root_cause_analyzer.analyze_incident(
            "INC-MEMORY-001",
            incident_logs
        )
        
        assert analysis.root_cause is not None
        assert len(analysis.recommendations) > 0
        
        # Step 4: Predictive maintenance
        timestamps = [log.timestamp for log in incident_logs[:10]]
        memory_values = [70 + i * 5 for i in range(10)]
        
        prediction = predictive_maintenance.predict_failure(
            "api-gateway",
            "memory_usage",
            timestamps,
            memory_values
        )
        
        assert prediction.likely_failure is True
        
        # Step 5: Get remediation actions
        actions = predictive_maintenance.recommend_actions(prediction)
        assert len(actions) > 0
        
        # Verify complete workflow
        assert patterns.patterns_found > 0
        assert analysis.incident_id == "INC-MEMORY-001"
        assert len(actions) > 0


class TestLogsMCPPerformance:
    """Performance tests for Logs MCP system."""
    
    def test_large_log_processing(self):
        """Test processing large number of logs."""
        processor = LogProcessor()
        base_time = datetime.now()
        
        # Generate 10,000 logs
        large_log_set = [
            LogEntry(
                base_time + timedelta(seconds=i),
                LogLevel.INFO if i % 10 != 0 else LogLevel.ERROR,
                f"service-{i % 10}",
                "app.log",
                f"Message {i}"
            )
            for i in range(10000)
        ]
        
        # Test filtering performance
        import time
        start = time.time()
        filtered = processor.filter_logs(large_log_set, level=LogLevel.ERROR)
        duration = time.time() - start
        
        assert len(filtered) == 1000  # 10% are errors
        assert duration < 1.0  # Should complete in under 1 second
    
    def test_pattern_detection_performance(self):
        """Test pattern detection performance."""
        detector = PatternDetector()
        base_time = datetime.now()
        
        # Generate 5,000 logs with patterns
        logs = [
            LogEntry(
                base_time + timedelta(seconds=i),
                LogLevel.ERROR if i % 5 == 0 else LogLevel.INFO,
                f"service-{i % 3}",
                "app.log",
                "Database connection failed" if i % 5 == 0 else "Normal operation"
            )
            for i in range(5000)
        ]
        
        # Test detection performance
        import time
        start = time.time()
        result = detector.detect_patterns(logs)
        duration = time.time() - start
        
        assert result.patterns_found > 0
        assert duration < 2.0  # Should complete in under 2 seconds

