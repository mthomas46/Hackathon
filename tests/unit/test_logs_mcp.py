"""
Unit tests for Logs MCP System.

Tests intelligent log analysis, pattern detection, predictive maintenance,
and automated root cause analysis.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add services directory to path
services_path = Path(__file__).parent.parent.parent / "services"
sys.path.insert(0, str(services_path))

from mcp_logs.src.log_processor import (
    LogProcessor,
    LogEntry,
    LogLevel,
    LogSource,
    ParseResult
)
from mcp_logs.src.pattern_detector import (
    PatternDetector,
    Pattern,
    PatternType,
    DetectionResult
)
from mcp_logs.src.anomaly_detector import (
    AnomalyDetector,
    Anomaly,
    AnomalyType,
    AnomalyScore
)
from mcp_logs.src.root_cause_analyzer import (
    RootCauseAnalyzer,
    RootCause,
    IncidentTimeline,
    CorrelationScore
)
from mcp_logs.src.predictive_maintenance import (
    PredictiveMaintenance,
    Prediction,
    MaintenanceAction,
    TrendAnalysis
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_log_entries():
    """Create sample log entries."""
    base_time = datetime.now()
    
    return [
        LogEntry(
            timestamp=base_time,
            level=LogLevel.INFO,
            message="Service started successfully",
            source=LogSource.APPLICATION,
            service="api-gateway",
            metadata={"version": "1.0.0"}
        ),
        LogEntry(
            timestamp=base_time + timedelta(seconds=10),
            level=LogLevel.ERROR,
            message="Database connection failed: timeout",
            source=LogSource.DATABASE,
            service="user-service",
            metadata={"error_code": "DB_TIMEOUT"}
        ),
        LogEntry(
            timestamp=base_time + timedelta(seconds=15),
            level=LogLevel.WARNING,
            message="High memory usage detected: 85%",
            source=LogSource.INFRASTRUCTURE,
            service="worker-01",
            metadata={"memory_percent": 85}
        ),
        LogEntry(
            timestamp=base_time + timedelta(seconds=20),
            level=LogLevel.ERROR,
            message="Database connection failed: timeout",
            source=LogSource.DATABASE,
            service="order-service",
            metadata={"error_code": "DB_TIMEOUT"}
        ),
    ]


@pytest.fixture
def log_processor():
    """Create log processor instance."""
    return LogProcessor()


@pytest.fixture
def pattern_detector():
    """Create pattern detector instance."""
    return PatternDetector()


@pytest.fixture
def anomaly_detector():
    """Create anomaly detector instance."""
    return AnomalyDetector()


@pytest.fixture
def root_cause_analyzer():
    """Create root cause analyzer instance."""
    return RootCauseAnalyzer()


@pytest.fixture
def predictive_maintenance():
    """Create predictive maintenance instance."""
    return PredictiveMaintenance()


# ============================================================================
# Log Processor Tests
# ============================================================================

class TestLogProcessor:
    """Test log processing functionality."""
    
    def test_parse_log_entry(self, log_processor):
        """Test parsing a single log entry."""
        raw_log = '2025-10-07 10:00:00 ERROR [user-service] Database connection failed'
        
        result = log_processor.parse_log(raw_log)
        
        assert result.success
        assert result.entry.level == LogLevel.ERROR
        assert result.entry.service == "user-service"
        assert "Database connection failed" in result.entry.message
    
    def test_parse_json_log(self, log_processor):
        """Test parsing JSON formatted logs."""
        json_log = '{"timestamp": "2025-10-07T10:00:00", "level": "ERROR", "service": "api", "message": "Failed"}'
        
        result = log_processor.parse_log(json_log, format="json")
        
        assert result.success
        assert result.entry.level == LogLevel.ERROR
        assert result.entry.service == "api"
    
    def test_parse_multiple_formats(self, log_processor):
        """Test parsing logs in multiple formats."""
        formats = [
            ("plain", "ERROR: Database connection failed"),
            ("json", '{"level": "ERROR", "message": "Failed"}'),
            ("syslog", "<34>Oct 7 10:00:00 host app: ERROR message"),
        ]
        
        for fmt, log in formats:
            result = log_processor.parse_log(log, format=fmt)
            assert result.success
    
    def test_filter_by_level(self, log_processor, sample_log_entries):
        """Test filtering logs by level."""
        filtered = log_processor.filter_by_level(
            sample_log_entries,
            LogLevel.ERROR
        )
        
        assert len(filtered) == 2
        assert all(entry.level == LogLevel.ERROR for entry in filtered)
    
    def test_filter_by_service(self, log_processor, sample_log_entries):
        """Test filtering logs by service."""
        filtered = log_processor.filter_by_service(
            sample_log_entries,
            "user-service"
        )
        
        assert len(filtered) == 1
        assert filtered[0].service == "user-service"
    
    def test_filter_by_time_range(self, log_processor, sample_log_entries):
        """Test filtering logs by time range."""
        start = sample_log_entries[0].timestamp
        end = sample_log_entries[2].timestamp
        
        filtered = log_processor.filter_by_time_range(
            sample_log_entries,
            start,
            end
        )
        
        assert len(filtered) == 3
    
    def test_aggregate_by_service(self, log_processor, sample_log_entries):
        """Test aggregating logs by service."""
        aggregated = log_processor.aggregate_by_service(sample_log_entries)
        
        assert "user-service" in aggregated
        assert "order-service" in aggregated
        assert aggregated["user-service"] == 1
        assert aggregated["order-service"] == 1


# ============================================================================
# Pattern Detector Tests
# ============================================================================

class TestPatternDetector:
    """Test pattern detection functionality."""
    
    def test_detect_repeated_errors(self, pattern_detector, sample_log_entries):
        """Test detecting repeated error patterns."""
        result = pattern_detector.detect_patterns(sample_log_entries)
        
        assert result.patterns_found > 0
        
        # Should detect "Database connection failed" pattern
        db_patterns = [p for p in result.patterns if "Database" in p.description]
        assert len(db_patterns) > 0
    
    def test_detect_error_spike(self, pattern_detector):
        """Test detecting error spikes."""
        # Create logs with error spike
        base_time = datetime.now()
        logs = []
        
        # Normal period
        for i in range(10):
            logs.append(LogEntry(
                timestamp=base_time + timedelta(minutes=i),
                level=LogLevel.INFO,
                message=f"Request {i}",
                source=LogSource.APPLICATION,
                service="api"
            ))
        
        # Spike period
        for i in range(20):
            logs.append(LogEntry(
                timestamp=base_time + timedelta(minutes=10+i),
                level=LogLevel.ERROR,
                message=f"Error {i}",
                source=LogSource.APPLICATION,
                service="api"
            ))
        
        result = pattern_detector.detect_patterns(logs)
        
        # Should detect spike
        spike_patterns = [p for p in result.patterns if p.type == PatternType.ERROR_SPIKE]
        assert len(spike_patterns) > 0
    
    def test_detect_cascading_failures(self, pattern_detector):
        """Test detecting cascading failures."""
        base_time = datetime.now()
        logs = [
            LogEntry(
                timestamp=base_time,
                level=LogLevel.ERROR,
                message="Database connection failed",
                source=LogSource.DATABASE,
                service="db"
            ),
            LogEntry(
                timestamp=base_time + timedelta(seconds=1),
                level=LogLevel.ERROR,
                message="User service unavailable",
                source=LogSource.APPLICATION,
                service="user-service"
            ),
            LogEntry(
                timestamp=base_time + timedelta(seconds=2),
                level=LogLevel.ERROR,
                message="Order service unavailable",
                source=LogSource.APPLICATION,
                service="order-service"
            ),
        ]
        
        result = pattern_detector.detect_patterns(logs)
        
        cascading = [p for p in result.patterns if p.type == PatternType.CASCADING_FAILURE]
        assert len(cascading) > 0
    
    def test_detect_slow_queries(self, pattern_detector):
        """Test detecting slow query patterns."""
        base_time = datetime.now()
        logs = []
        
        for i in range(5):
            logs.append(LogEntry(
                timestamp=base_time + timedelta(seconds=i),
                level=LogLevel.WARNING,
                message=f"Slow query detected: {2000 + i*100}ms",
                source=LogSource.DATABASE,
                service="db",
                metadata={"duration_ms": 2000 + i*100}
            ))
        
        result = pattern_detector.detect_patterns(logs)
        
        slow_query_patterns = [p for p in result.patterns if "slow query" in p.description.lower()]
        assert len(slow_query_patterns) > 0


# ============================================================================
# Anomaly Detector Tests
# ============================================================================

class TestAnomalyDetector:
    """Test anomaly detection functionality."""
    
    def test_detect_anomalous_error_rate(self, anomaly_detector):
        """Test detecting anomalous error rates."""
        # Historical baseline: 1% error rate
        baseline = {
            "error_rate": 0.01,
            "std_dev": 0.002
        }
        
        # Current: 10% error rate (anomalous)
        current_metrics = {
            "error_rate": 0.10,
            "total_requests": 1000,
            "error_count": 100
        }
        
        result = anomaly_detector.detect_anomaly(
            metric_name="error_rate",
            current_value=current_metrics["error_rate"],
            baseline=baseline
        )
        
        assert result.is_anomaly
        assert result.severity == "high"
        assert result.score > 0.8
    
    def test_detect_memory_leak(self, anomaly_detector):
        """Test detecting memory leak patterns."""
        # Gradually increasing memory usage
        timestamps = []
        memory_values = []
        base_time = datetime.now()
        
        for i in range(60):
            timestamps.append(base_time + timedelta(minutes=i))
            memory_values.append(50 + i * 0.5)  # Gradual increase
        
        result = anomaly_detector.detect_trend_anomaly(
            metric_name="memory_usage",
            timestamps=timestamps,
            values=memory_values
        )
        
        assert result.is_anomaly
        assert result.type == AnomalyType.MEMORY_LEAK
    
    def test_detect_latency_spike(self, anomaly_detector):
        """Test detecting latency spikes."""
        baseline = {
            "p50": 100,
            "p95": 200,
            "p99": 300
        }
        
        current = {
            "p50": 150,
            "p95": 500,  # Spike
            "p99": 800   # Spike
        }
        
        result = anomaly_detector.detect_latency_anomaly(
            current=current,
            baseline=baseline
        )
        
        assert result.is_anomaly
        assert "latency" in result.description.lower()
    
    def test_no_anomaly_when_normal(self, anomaly_detector):
        """Test that no anomaly is detected for normal values."""
        baseline = {
            "error_rate": 0.01,
            "std_dev": 0.002
        }
        
        # Normal value within 2 standard deviations
        result = anomaly_detector.detect_anomaly(
            metric_name="error_rate",
            current_value=0.012,
            baseline=baseline
        )
        
        assert not result.is_anomaly


# ============================================================================
# Root Cause Analyzer Tests
# ============================================================================

class TestRootCauseAnalyzer:
    """Test root cause analysis functionality."""
    
    @pytest.mark.asyncio
    async def test_analyze_incident(self, root_cause_analyzer, sample_log_entries):
        """Test analyzing an incident."""
        incident_id = "INC-001"
        
        result = await root_cause_analyzer.analyze_incident(
            incident_id=incident_id,
            logs=sample_log_entries
        )
        
        assert result.incident_id == incident_id
        assert result.root_cause is not None
        assert len(result.contributing_factors) > 0
    
    @pytest.mark.asyncio
    async def test_build_timeline(self, root_cause_analyzer, sample_log_entries):
        """Test building incident timeline."""
        timeline = await root_cause_analyzer.build_timeline(sample_log_entries)
        
        assert len(timeline.events) == len(sample_log_entries)
        assert timeline.start_time == sample_log_entries[0].timestamp
        assert timeline.end_time == sample_log_entries[-1].timestamp
    
    @pytest.mark.asyncio
    async def test_identify_correlations(self, root_cause_analyzer):
        """Test identifying correlations between events."""
        base_time = datetime.now()
        logs = [
            LogEntry(
                timestamp=base_time,
                level=LogLevel.ERROR,
                message="Database connection lost",
                source=LogSource.DATABASE,
                service="db"
            ),
            LogEntry(
                timestamp=base_time + timedelta(seconds=1),
                level=LogLevel.ERROR,
                message="Service unavailable",
                source=LogSource.APPLICATION,
                service="api"
            ),
        ]
        
        correlations = await root_cause_analyzer.identify_correlations(logs)
        
        assert len(correlations) > 0
        assert any(c.score > 0.7 for c in correlations)
    
    @pytest.mark.asyncio
    async def test_suggest_remediation(self, root_cause_analyzer):
        """Test suggesting remediation actions."""
        root_cause = RootCause(
            description="Database connection timeout",
            confidence=0.9,
            category="database"
        )
        
        actions = await root_cause_analyzer.suggest_remediation(root_cause)
        
        assert len(actions) > 0
        assert any("database" in a.description.lower() for a in actions)


# ============================================================================
# Predictive Maintenance Tests
# ============================================================================

class TestPredictiveMaintenance:
    """Test predictive maintenance functionality."""
    
    def test_predict_failure(self, predictive_maintenance):
        """Test predicting service failure."""
        # Historical metrics showing degradation
        timestamps = []
        error_rates = []
        base_time = datetime.now()
        
        for i in range(7):
            timestamps.append(base_time - timedelta(days=7-i))
            error_rates.append(0.01 + i * 0.005)  # Increasing trend
        
        prediction = predictive_maintenance.predict_failure(
            service="api-gateway",
            metric="error_rate",
            timestamps=timestamps,
            values=error_rates
        )
        
        assert prediction.likely_failure
        assert prediction.confidence > 0.6
        assert prediction.estimated_time_to_failure is not None
    
    def test_analyze_trends(self, predictive_maintenance):
        """Test analyzing metric trends."""
        # Create trend data
        timestamps = [datetime.now() - timedelta(days=i) for i in range(7, 0, -1)]
        values = [100 + i * 10 for i in range(7)]  # Increasing trend
        
        trend = predictive_maintenance.analyze_trend(
            metric_name="response_time",
            timestamps=timestamps,
            values=values
        )
        
        assert trend.direction == "increasing"
        assert trend.slope > 0
    
    def test_recommend_maintenance(self, predictive_maintenance):
        """Test recommending maintenance actions."""
        prediction = Prediction(
            service="api-gateway",
            metric="memory_usage",
            likely_failure=True,
            confidence=0.85,
            estimated_time_to_failure=timedelta(hours=2),
            reason="Memory leak detected"
        )
        
        actions = predictive_maintenance.recommend_actions(prediction)
        
        assert len(actions) > 0
        assert any("memory" in a.description.lower() for a in actions)
        assert any(a.priority == "high" for a in actions)
    
    def test_no_prediction_when_stable(self, predictive_maintenance):
        """Test that no failure is predicted for stable metrics."""
        # Stable metrics
        timestamps = [datetime.now() - timedelta(days=i) for i in range(7, 0, -1)]
        values = [0.01] * 7  # Flat, stable
        
        prediction = predictive_maintenance.predict_failure(
            service="api-gateway",
            metric="error_rate",
            timestamps=timestamps,
            values=values
        )
        
        assert not prediction.likely_failure


# ============================================================================
# Integration Tests
# ============================================================================

class TestLogsIntegration:
    """Test integration between components."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_analysis(
        self,
        log_processor,
        pattern_detector,
        anomaly_detector,
        root_cause_analyzer
    ):
        """Test end-to-end log analysis workflow."""
        # 1. Parse logs
        raw_logs = [
            '2025-10-07 10:00:00 ERROR [db] Connection timeout',
            '2025-10-07 10:00:01 ERROR [api] Service unavailable',
            '2025-10-07 10:00:02 ERROR [api] Service unavailable',
        ]
        
        parsed_logs = []
        for raw in raw_logs:
            result = log_processor.parse_log(raw)
            if result.success:
                parsed_logs.append(result.entry)
        
        assert len(parsed_logs) == 3
        
        # 2. Detect patterns
        patterns = pattern_detector.detect_patterns(parsed_logs)
        assert patterns.patterns_found > 0
        
        # 3. Detect anomalies
        anomaly = anomaly_detector.detect_anomaly(
            metric_name="error_rate",
            current_value=1.0,  # 100% errors
            baseline={"error_rate": 0.01, "std_dev": 0.002}
        )
        assert anomaly.is_anomaly
        
        # 4. Analyze root cause
        analysis = await root_cause_analyzer.analyze_incident(
            incident_id="TEST-001",
            logs=parsed_logs
        )
        assert analysis.root_cause is not None

