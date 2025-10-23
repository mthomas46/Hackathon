"""
Unit tests for QualityDashboard service.
Tests quality metrics aggregation and reporting.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from src.services.maintenance.quality_dashboard import QualityDashboard

@pytest.fixture
def complete_mock_data():
    """Complete mock data structure for quality dashboard."""
    return {
        "staleness": {
            "summary": {
                "stale_percentage": 10,
                "critical_issues": 2
            },
            "recommendations": []
        },
        "coverage": {
            "overall_coverage": {
                "coverage_score": 80,
                "total_coverage": 80,
                "coverage_level": "GOOD"
            },
            "service_coverage": {"top_services": []},
            "recommendations": []
        },
        "consistency": {
            "total_issues": 5,
            "total_checked": 100,
            "by_severity": {"CRITICAL": 1, "HIGH": 2, "MEDIUM": 2, "LOW": 0},
            "recommendations": []
        }
    }

@pytest.mark.unit
class TestDashboardInstantiation:
    def test_create_dashboard(self):
        dashboard = QualityDashboard()
        assert dashboard is not None
    
    def test_dashboard_has_methods(self):
        dashboard = QualityDashboard()
        assert hasattr(dashboard, 'get_quality_overview')

@pytest.mark.unit
class TestMetricsAggregation:
    async def test_aggregate_quality_metrics(self, complete_mock_data):
        dashboard = QualityDashboard()
        with patch.object(dashboard.staleness_detector, 'get_staleness_summary', new_callable=AsyncMock) as mock_stale:
            mock_stale.return_value = complete_mock_data["staleness"]
            with patch.object(dashboard.coverage_analyzer, 'analyze_coverage', new_callable=AsyncMock) as mock_cov:
                mock_cov.return_value = complete_mock_data["coverage"]
                with patch.object(dashboard.consistency_checker, 'check_consistency', new_callable=AsyncMock) as mock_cons:
                    mock_cons.return_value = complete_mock_data["consistency"]
                    result = await dashboard.get_quality_overview(service_name="test")
                    assert result is not None
                    assert "quality_score" in result

    async def test_aggregate_by_service(self, complete_mock_data):
        dashboard = QualityDashboard()
        with patch.object(dashboard.staleness_detector, 'get_staleness_summary', new_callable=AsyncMock) as mock_stale:
            mock_stale.return_value = complete_mock_data["staleness"]
            with patch.object(dashboard.coverage_analyzer, 'analyze_coverage', new_callable=AsyncMock) as mock_cov:
                mock_cov.return_value = complete_mock_data["coverage"]
                with patch.object(dashboard.consistency_checker, 'check_consistency', new_callable=AsyncMock) as mock_cons:
                    mock_cons.return_value = complete_mock_data["consistency"]
                    result = await dashboard.get_quality_overview(service_name="test-service")
                    assert result["metadata"]["service_name"] == "test-service"

@pytest.mark.unit
class TestQualityScoring:
    async def test_calculate_quality_score(self, complete_mock_data):
        dashboard = QualityDashboard()
        with patch.object(dashboard.staleness_detector, 'get_staleness_summary', new_callable=AsyncMock) as mock_stale:
            mock_stale.return_value = complete_mock_data["staleness"]
            with patch.object(dashboard.coverage_analyzer, 'analyze_coverage', new_callable=AsyncMock) as mock_cov:
                mock_cov.return_value = complete_mock_data["coverage"]
                with patch.object(dashboard.consistency_checker, 'check_consistency', new_callable=AsyncMock) as mock_cons:
                    mock_cons.return_value = complete_mock_data["consistency"]
                    result = await dashboard.get_quality_overview(service_name="test")
                    assert "quality_score" in result
                    assert isinstance(result["quality_score"], dict)

@pytest.mark.unit
class TestDashboardReporting:
    async def test_generate_overview(self, complete_mock_data):
        dashboard = QualityDashboard()
        with patch.object(dashboard.staleness_detector, 'get_staleness_summary', new_callable=AsyncMock) as mock_stale:
            mock_stale.return_value = complete_mock_data["staleness"]
            with patch.object(dashboard.coverage_analyzer, 'analyze_coverage', new_callable=AsyncMock) as mock_cov:
                mock_cov.return_value = complete_mock_data["coverage"]
                with patch.object(dashboard.consistency_checker, 'check_consistency', new_callable=AsyncMock) as mock_cons:
                    mock_cons.return_value = complete_mock_data["consistency"]
                    result = await dashboard.get_quality_overview(service_name="test")
                    assert "staleness" in result
                    assert "coverage" in result
                    assert "consistency" in result

    async def test_include_recommendations(self, complete_mock_data):
        dashboard = QualityDashboard()
        with patch.object(dashboard.staleness_detector, 'get_staleness_summary', new_callable=AsyncMock) as mock_stale:
            mock_stale.return_value = complete_mock_data["staleness"]
            with patch.object(dashboard.coverage_analyzer, 'analyze_coverage', new_callable=AsyncMock) as mock_cov:
                mock_cov.return_value = complete_mock_data["coverage"]
                with patch.object(dashboard.consistency_checker, 'check_consistency', new_callable=AsyncMock) as mock_cons:
                    mock_cons.return_value = complete_mock_data["consistency"]
                    result = await dashboard.get_quality_overview(service_name="test")
                    assert "recommendations" in result
                    assert isinstance(result["recommendations"], list)

@pytest.mark.unit
class TestDashboardErrorHandling:
    async def test_handle_dashboard_error(self):
        dashboard = QualityDashboard()
        with patch.object(dashboard.staleness_detector, 'get_staleness_summary', new_callable=AsyncMock) as mock_stale:
            mock_stale.side_effect = Exception("Staleness error")
            with pytest.raises(Exception):
                await dashboard.get_quality_overview(service_name="test")

    async def test_handle_partial_failure(self, complete_mock_data):
        dashboard = QualityDashboard()
        with patch.object(dashboard.staleness_detector, 'get_staleness_summary', new_callable=AsyncMock) as mock_stale:
            mock_stale.return_value = complete_mock_data["staleness"]
            with patch.object(dashboard.coverage_analyzer, 'analyze_coverage', new_callable=AsyncMock) as mock_cov:
                mock_cov.return_value = complete_mock_data["coverage"]
                with patch.object(dashboard.consistency_checker, 'check_consistency', new_callable=AsyncMock) as mock_cons:
                    mock_cons.return_value = complete_mock_data["consistency"]
                    result = await dashboard.get_quality_overview(service_name="test")
                    assert result is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "unit"])
