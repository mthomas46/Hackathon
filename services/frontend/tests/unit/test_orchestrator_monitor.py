"""Tests for Orchestrator Monitor"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from services.frontend.modules.orchestrator_monitor import OrchestratorMonitor


class TestOrchestratorMonitor:
    """Test cases for OrchestratorMonitor."""

    @pytest.fixture
    def monitor(self):
        """Create OrchestratorMonitor instance."""
        return OrchestratorMonitor()

    def test_init(self, monitor):
        """Test monitor initialization."""
        assert monitor._pubsub_activity == {
            "ingestion_requested": [],
            "findings_created": [],
            "other_events": [],
        }
        assert monitor._config_cache == {}
        assert monitor._activity_cache == {}
        assert monitor._cache_ttl == 30

    def test_is_cache_fresh_no_cache(self, monitor):
        """Test cache freshness check when no cache exists."""
        assert not monitor.is_cache_fresh("test_key")

    def test_is_cache_fresh_expired(self, monitor):
        """Test cache freshness check when cache is expired."""
        old_time = datetime.utcnow() - timedelta(seconds=31)
        monitor._activity_cache["test_key_updated"] = old_time

        assert not monitor.is_cache_fresh("test_key")

    def test_is_cache_fresh_valid(self, monitor):
        """Test cache freshness check when cache is still valid."""
        recent_time = datetime.utcnow() - timedelta(seconds=15)
        monitor._activity_cache["test_key_updated"] = recent_time

        assert monitor.is_cache_fresh("test_key")

    @pytest.mark.asyncio
    async def test_get_orchestrator_config_cached(self, monitor):
        """Test getting cached orchestrator config."""
        monitor._config_cache = {"test": "cached_data"}
        monitor._activity_cache["config_updated"] = datetime.utcnow()

        with patch.object(monitor, 'is_cache_fresh', return_value=True):
            result = await monitor.get_orchestrator_config()

            assert result == {"test": "cached_data"}

    @pytest.mark.asyncio
    async def test_get_orchestrator_config_force_refresh(self, monitor):
        """Test forcing refresh of orchestrator config."""
        monitor._config_cache = {"test": "old_data"}

        with patch('services.frontend.modules.orchestrator_monitor.get_frontend_clients') as mock_clients, \
             patch('services.frontend.modules.orchestrator_monitor.get_orchestrator_url') as mock_url, \
             patch.object(monitor, 'is_cache_fresh', return_value=True):

            mock_client_instance = AsyncMock()
            mock_clients.return_value = mock_client_instance
            mock_url.return_value = "http://test-orchestrator"
            mock_client_instance.get_json.return_value = {"new": "config"}

            result = await monitor.get_orchestrator_config(force_refresh=True)

            assert result == {"new": "config"}
            mock_client_instance.get_json.assert_called()

    @pytest.mark.asyncio
    async def test_get_orchestrator_config_error(self, monitor):
        """Test orchestrator config retrieval with error."""
        with patch('services.frontend.modules.orchestrator_monitor.get_frontend_clients') as mock_clients, \
             patch('services.frontend.modules.orchestrator_monitor.get_orchestrator_url') as mock_url:

            mock_clients.side_effect = Exception("Connection failed")

            result = await monitor.get_orchestrator_config()

            assert result == {}  # Should return empty dict on error

    @pytest.mark.asyncio
    async def test_get_pubsub_activity_cached(self, monitor):
        """Test getting cached pubsub activity."""
        cached_activity = {"test": "activity"}
        monitor._activity_cache["pubsub"] = cached_activity
        monitor._activity_cache["pubsub_updated"] = datetime.utcnow()

        with patch.object(monitor, 'is_cache_fresh', return_value=True):
            result = await monitor.get_pubsub_activity()

            assert result == cached_activity

    @pytest.mark.asyncio
    async def test_get_pubsub_activity_fetch(self, monitor):
        """Test fetching fresh pubsub activity."""
        with patch('services.frontend.modules.orchestrator_monitor.get_frontend_clients') as mock_clients, \
             patch('services.frontend.modules.orchestrator_monitor.get_orchestrator_url') as mock_url:

            mock_client_instance = AsyncMock()
            mock_clients.return_value = mock_client_instance
            mock_url.return_value = "http://test-orchestrator"

            # Mock Redis activity response
            mock_client_instance.get_json.return_value = {
                "pubsub_activity": {
                    "ingestion_requested": ["event1"],
                    "findings_created": ["event2"],
                    "other_events": ["event3"]
                }
            }

            result = await monitor.get_pubsub_activity()

            assert "ingestion_requested" in result
            assert "findings_created" in result
            assert "other_events" in result
            mock_client_instance.get_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_pubsub_activity_error(self, monitor):
        """Test pubsub activity retrieval with error."""
        with patch('services.frontend.modules.orchestrator_monitor.get_frontend_clients') as mock_clients:
            mock_clients.side_effect = Exception("Connection failed")

            result = await monitor.get_pubsub_activity()

            assert result == {
                "ingestion_requested": [],
                "findings_created": [],
                "other_events": [],
                "error": "Connection failed"
            }

    def test_get_recent_events_empty(self, monitor):
        """Test getting recent events when no activity."""
        result = monitor.get_recent_events()

        assert result == []

    def test_get_recent_events_with_data(self, monitor):
        """Test getting recent events with activity data."""
        # Add some test activity
        monitor._pubsub_activity["ingestion_requested"] = [
            {"timestamp": "2024-01-01T10:00:00Z", "event": "test1"}
        ]
        monitor._pubsub_activity["findings_created"] = [
            {"timestamp": "2024-01-01T11:00:00Z", "event": "test2"}
        ]

        result = monitor.get_recent_events(limit=5)

        assert len(result) == 2
        # Should be sorted by timestamp (most recent first)
        assert result[0]["event"] == "test2"
        assert result[1]["event"] == "test1"

    def test_get_recent_events_with_limit(self, monitor):
        """Test getting recent events with limit."""
        # Add many events
        events = [{"timestamp": f"2024-01-01T{i:02d}:00:00Z", "event": f"test{i}"} for i in range(10)]
        monitor._pubsub_activity["ingestion_requested"] = events

        result = monitor.get_recent_events(limit=3)

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_get_service_health_overview(self, monitor):
        """Test getting service health overview."""
        with patch('services.frontend.modules.orchestrator_monitor.get_frontend_clients') as mock_clients, \
             patch('services.frontend.modules.orchestrator_monitor.get_orchestrator_url') as mock_url:

            mock_client_instance = AsyncMock()
            mock_clients.return_value = mock_client_instance
            mock_url.return_value = "http://test-orchestrator"

            mock_client_instance.get_json.return_value = {
                "services": [
                    {"name": "service1", "status": "healthy"},
                    {"name": "service2", "status": "unhealthy"}
                ]
            }

            result = await monitor.get_service_health_overview()

            assert "services" in result
            assert len(result["services"]) == 2
            mock_client_instance.get_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_service_health_overview_error(self, monitor):
        """Test service health overview with error."""
        with patch('services.frontend.modules.orchestrator_monitor.get_frontend_clients') as mock_clients:
            mock_clients.side_effect = Exception("Connection failed")

            result = await monitor.get_service_health_overview()

            assert result == {"error": "Connection failed"}

    def test_clear_cache(self, monitor):
        """Test cache clearing."""
        monitor._config_cache = {"test": "data"}
        monitor._activity_cache = {"test": "activity"}
        monitor._pubsub_activity = {"test": ["event"]}

        monitor.clear_cache()

        assert monitor._config_cache == {}
        assert monitor._activity_cache == {}
        assert monitor._pubsub_activity == {
            "ingestion_requested": [],
            "findings_created": [],
            "other_events": [],
        }
