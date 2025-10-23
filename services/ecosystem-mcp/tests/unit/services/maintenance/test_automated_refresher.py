"""
Unit tests for AutomatedRefresher service.
Tests automated documentation refresh functionality.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from src.services.maintenance.automated_refresher import AutomatedRefresher, RefreshStrategy, RefreshTrigger

@pytest.mark.unit
class TestRefresherInstantiation:
    def test_create_refresher(self):
        refresher = AutomatedRefresher()
        assert refresher is not None
    
    def test_refresher_has_methods(self):
        refresher = AutomatedRefresher()
        assert hasattr(refresher, 'refresh_documentation')

@pytest.mark.unit
class TestRefreshStrategies:
    async def test_smart_refresh_strategy(self):
        refresher = AutomatedRefresher()
        with patch.object(refresher, '_identify_smart_targets', new_callable=AsyncMock) as mock_targets:
            mock_targets.return_value = []
            with patch.object(refresher, '_execute_refresh', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {"refreshed": 0, "failed": 0, "details": [], "started_at": datetime.utcnow().isoformat()}
                result = await refresher.refresh_documentation(service_name="test", strategy=RefreshStrategy.SMART)
                assert result is not None
                assert "service_name" in result
                assert result["status"] == "skipped"

    async def test_incremental_refresh_strategy(self):
        refresher = AutomatedRefresher()
        with patch.object(refresher, '_identify_incremental_targets', new_callable=AsyncMock) as mock_targets:
            mock_targets.return_value = []
            result = await refresher.refresh_documentation(service_name="test", strategy=RefreshStrategy.INCREMENTAL)
            assert result is not None
            assert isinstance(result, dict)

    async def test_full_refresh_strategy(self):
        refresher = AutomatedRefresher()
        with patch.object(refresher, '_identify_full_targets', new_callable=AsyncMock) as mock_targets:
            mock_targets.return_value = []
            result = await refresher.refresh_documentation(service_name="test", strategy=RefreshStrategy.FULL)
            assert result is not None
            assert isinstance(result, dict)

@pytest.mark.unit
class TestRefreshTriggers:
    async def test_manual_trigger(self):
        refresher = AutomatedRefresher()
        with patch.object(refresher, '_identify_smart_targets', new_callable=AsyncMock) as mock_targets:
            mock_targets.return_value = []
            result = await refresher.refresh_documentation(service_name="test", trigger=RefreshTrigger.MANUAL)
            assert result is not None
            assert result["trigger"] == RefreshTrigger.MANUAL

    async def test_scheduled_trigger(self):
        refresher = AutomatedRefresher()
        with patch.object(refresher, '_identify_smart_targets', new_callable=AsyncMock) as mock_targets:
            mock_targets.return_value = []
            result = await refresher.refresh_documentation(service_name="test", trigger=RefreshTrigger.SCHEDULED)
            assert result is not None
            assert result["trigger"] == RefreshTrigger.SCHEDULED

@pytest.mark.unit
class TestRefreshExecution:
    async def test_execute_with_targets(self):
        refresher = AutomatedRefresher()
        targets = [{"id": uuid4(), "path": "/docs/test.md"}]
        with patch.object(refresher, '_identify_smart_targets', new_callable=AsyncMock) as mock_targets:
            mock_targets.return_value = targets
            with patch.object(refresher, '_execute_refresh', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {
                    "refreshed": 1,
                    "failed": 0,
                    "details": [],
                    "started_at": datetime.utcnow().isoformat()
                }
                result = await refresher.refresh_documentation(service_name="test")
                assert result["status"] == "completed"
                assert result["documents_refreshed"] == 1

    async def test_execute_with_force(self):
        refresher = AutomatedRefresher()
        with patch.object(refresher, '_identify_smart_targets', new_callable=AsyncMock) as mock_targets:
            mock_targets.return_value = []
            with patch.object(refresher, '_execute_refresh', new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = {
                    "refreshed": 0,
                    "failed": 0,
                    "details": [],
                    "started_at": datetime.utcnow().isoformat()
                }
                result = await refresher.refresh_documentation(service_name="test", force=True)
                assert result["status"] == "completed"

@pytest.mark.unit
class TestRefreshErrorHandling:
    async def test_handle_refresh_error(self):
        refresher = AutomatedRefresher()
        with patch.object(refresher, '_identify_smart_targets', new_callable=AsyncMock) as mock_targets:
            mock_targets.side_effect = Exception("Refresh error")
            with pytest.raises(Exception):
                await refresher.refresh_documentation(service_name="test")

    async def test_skip_when_no_targets(self):
        refresher = AutomatedRefresher()
        with patch.object(refresher, '_identify_smart_targets', new_callable=AsyncMock) as mock_targets:
            mock_targets.return_value = []
            result = await refresher.refresh_documentation(service_name="test", force=False)
            assert result["status"] == "skipped"
            assert result["documents_refreshed"] == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "unit"])
