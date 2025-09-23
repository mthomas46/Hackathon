"""Notifications domain tests.

Comprehensive tests for notification events, webhooks, and delivery mechanisms.
"""
import pytest
from unittest.mock import patch, AsyncMock, Mock
from tests.unit.doc_store.conftest import BaseTestCase


@pytest.mark.unit
@pytest.mark.domain
class TestNotificationsRepository(BaseTestCase):
    """Test NotificationsRepository functionality."""

    @pytest.fixture
    def repository(self):
        """Create notifications repository instance."""
        from services.doc_store.domain.notifications.repository import NotificationsRepository
        return NotificationsRepository()

    def test_get_webhooks_for_event(self, repository):
        """Test getting webhooks that should receive an event."""
        mock_webhooks = [
            {
                'id': 'webhook1',
                'name': 'Test Webhook',
                'url': 'https://example.com/hook',
                'events': '["document.created", "document.updated"]',
                'is_active': 1,
                'secret': 'secret123',
                'created_at': '2024-01-01T00:00:00'
            }
        ]

        with patch('services.doc_store.domain.notifications.repository.execute_query', return_value=mock_webhooks):
            webhooks = repository.get_webhooks_for_event('document.created')

            assert len(webhooks) == 1
            assert webhooks[0].id == 'webhook1'
            assert webhooks[0].name == 'Test Webhook'

    def test_get_event_history_with_filters(self, repository):
        """Test getting event history with filters."""
        mock_events = [
            {
                'id': 'event1',
                'event_type': 'document.created',
                'entity_type': 'document',
                'entity_id': 'doc1',
                'user_id': 'user1',
                'metadata': '{"size": 1000}',
                'created_at': '2024-01-01T00:00:00'
            }
        ]

        with patch('services.doc_store.domain.notifications.repository.execute_query', return_value=mock_events):
            events = repository.get_event_history(
                event_type='document.created',
                limit=10
            )

            assert len(events) == 1
            assert events[0].event_type == 'document.created'
            assert events[0].entity_id == 'doc1'

    def test_get_notification_stats_comprehensive(self, repository):
        """Test comprehensive notification statistics."""
        with patch('services.doc_store.domain.notifications.repository.execute_query') as mock_execute:
            mock_execute.side_effect = [
                [{'event_type': 'document.created', 'count': 50}, {'event_type': 'document.updated', 'count': 30}],
                [{'status': 'delivered', 'count': 70}, {'status': 'failed', 'count': 10}]
            ]

            stats = repository.get_notification_stats(days_back=7)

            assert stats['period_days'] == 7
            assert stats['events_by_type']['document.created'] == 50
            assert stats['deliveries_by_status']['delivered'] == 70
            assert stats['total_events'] == 80  # 50 + 30
            assert stats['total_deliveries'] == 80  # 70 + 10


@pytest.mark.unit
@pytest.mark.domain
class TestNotificationsService(BaseTestCase):
    """Test NotificationsService functionality."""

    @pytest.fixture
    def service(self):
        """Create notifications service instance."""
        from services.doc_store.domain.notifications.service import NotificationsService
        return NotificationsService()

    @pytest.fixture
    def mock_repository(self, service):
        """Mock the repository for isolated testing."""
        with patch.object(service, 'repository') as mock_repo:
            yield mock_repo

    def test_emit_event_success(self, service, mock_repository):
        """Test successful event emission."""
        with patch.object(service, '_trigger_webhooks') as mock_trigger:
            result = service.emit_event('document.created', 'document', 'doc1', user_id='user1')

            # Service creates entity with auto-generated UUID
            assert result is not None
            assert hasattr(result, 'id')
            assert result.event_type == 'document.created'
            assert result.entity_type == 'document'
            assert result.entity_id == 'doc1'
            assert result.user_id == 'user1'
            mock_repository.save.assert_called_once()
            mock_trigger.assert_called_once()

    def test_get_event_history_formatted(self, service, mock_repository):
        """Test event history formatting."""
        mock_events = [Mock(to_dict=lambda: {'id': 'event1', 'event_type': 'created'})]
        mock_repository.get_event_history.return_value = mock_events

        result = service.get_event_history(limit=20)

        assert result['total'] == 1
        assert len(result['events']) == 1
        assert result['limit'] == 20

    def test_get_notification_stats_delegation(self, service, mock_repository):
        """Test notification stats delegation."""
        mock_stats = {'total_events': 100, 'total_deliveries': 95}
        mock_repository.get_notification_stats.return_value = mock_stats

        result = service.get_notification_stats(days_back=30)

        assert result == mock_stats
        mock_repository.get_notification_stats.assert_called_once_with(30)


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.domain
class TestNotificationsHandlers(BaseTestCase):
    """Test NotificationsHandlers functionality."""

    @pytest.fixture
    def handlers(self):
        """Create notifications handlers instance."""
        from services.doc_store.domain.notifications.handlers import NotificationsHandlers
        return NotificationsHandlers()

    @pytest.fixture
    def mock_service(self, handlers):
        """Mock the service for isolated testing."""
        with patch.object(handlers, 'service') as mock_svc:
            yield mock_svc

    async def test_handle_emit_event_success(self, handlers, mock_service):
        """Test successful event emission via handler."""
        mock_event = Mock()
        mock_event.to_dict.return_value = {
            'id': 'event123',
            'event_type': 'document.created',
            'entity_id': 'doc1'
        }
        mock_service.emit_event.return_value = mock_event

        result = await handlers.handle_emit_event('document.created', 'document', 'doc1')

        self.assert_success_response(result)
        assert result['data']['event_type'] == 'document.created'

    async def test_handle_get_event_history_success(self, handlers, mock_service):
        """Test successful event history retrieval."""
        mock_result = {
            'events': [{'id': 'event1'}],
            'total': 1,
            'limit': 50
        }
        mock_service.get_event_history.return_value = mock_result

        result = await handlers.handle_get_event_history(limit=50)

        self.assert_success_response(result)
        assert result['data']['total'] == 1

    async def test_handle_get_notification_stats_success(self, handlers, mock_service):
        """Test successful notification stats retrieval."""
        mock_stats = {
            'total_events': 100,
            'total_deliveries': 95,
            'period_days': 7
        }
        mock_service.get_notification_stats.return_value = mock_stats

        result = await handlers.handle_get_notification_stats(days_back=7)

        self.assert_success_response(result)
        assert result['data']['total_events'] == 100
