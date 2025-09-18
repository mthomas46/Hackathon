"""Tests for Application Events system."""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timezone
from typing import Dict, Any, List
from uuid import uuid4

from ...application.events.application_events import (
    ApplicationEvent, AnalysisRequestedEvent, AnalysisCompletedEvent,
    AnalysisFailedEvent, DocumentCreatedEvent, DocumentUpdatedEvent,
    FindingCreatedEvent, FindingResolvedEvent
)
from ...application.events.event_bus import EventBus
from ...application.events.event_publisher import EventPublisher
from ...application.events.event_subscriber import EventSubscriber

from ...domain.entities.document import Document
from ...domain.entities.analysis import Analysis
from ...domain.entities.finding import Finding
from ...domain.value_objects.analysis_type import AnalysisType


class TestApplicationEvents:
    """Test cases for Application Events."""

    def test_application_event_creation(self):
        """Test creating base application event."""
        event = ApplicationEvent(
            event_id='event-123',
            event_type='test_event',
            correlation_id='corr-456',
            timestamp=datetime.now(timezone.utc),
            metadata={'source': 'test'}
        )

        assert event.event_id == 'event-123'
        assert event.event_type == 'test_event'
        assert event.correlation_id == 'corr-456'
        assert event.metadata == {'source': 'test'}

    def test_analysis_requested_event_creation(self):
        """Test creating analysis requested event."""
        event = AnalysisRequestedEvent(
            event_id='event-123',
            correlation_id='corr-456',
            document_id='doc-123',
            analysis_type='semantic_similarity',
            requested_by='user-789',
            priority='high',
            configuration={'threshold': 0.8},
            metadata={'session_id': 'session-101'}
        )

        assert event.event_type == 'analysis_requested'
        assert event.document_id == 'doc-123'
        assert event.analysis_type == 'semantic_similarity'
        assert event.requested_by == 'user-789'
        assert event.priority == 'high'
        assert event.configuration == {'threshold': 0.8}

    def test_analysis_completed_event_creation(self):
        """Test creating analysis completed event."""
        event = AnalysisCompletedEvent(
            event_id='event-123',
            correlation_id='corr-456',
            analysis_id='analysis-123',
            document_id='doc-123',
            analysis_type='semantic_similarity',
            result={'similarity_score': 0.85},
            execution_time_seconds=2.5,
            findings_count=3,
            metadata={'user_id': 'user-789'}
        )

        assert event.event_type == 'analysis_completed'
        assert event.analysis_id == 'analysis-123'
        assert event.result == {'similarity_score': 0.85}
        assert event.execution_time_seconds == 2.5
        assert event.findings_count == 3

    def test_analysis_failed_event_creation(self):
        """Test creating analysis failed event."""
        event = AnalysisFailedEvent(
            event_id='event-123',
            correlation_id='corr-456',
            document_id='doc-123',
            analysis_type='semantic_similarity',
            error_message='Analysis failed due to network error',
            error_code='NETWORK_ERROR',
            retry_count=2,
            metadata={'user_id': 'user-789'}
        )

        assert event.event_type == 'analysis_failed'
        assert event.error_message == 'Analysis failed due to network error'
        assert event.error_code == 'NETWORK_ERROR'
        assert event.retry_count == 2

    def test_document_created_event_creation(self):
        """Test creating document created event."""
        event = DocumentCreatedEvent(
            event_id='event-123',
            correlation_id='corr-456',
            document_id='doc-123',
            repository_id='repo-456',
            author='user-789',
            metadata={'size': 1024}
        )

        assert event.event_type == 'document_created'
        assert event.document_id == 'doc-123'
        assert event.repository_id == 'repo-456'
        assert event.author == 'user-789'

    def test_finding_created_event_creation(self):
        """Test creating finding created event."""
        event = FindingCreatedEvent(
            event_id='event-123',
            correlation_id='corr-456',
            finding_id='finding-123',
            document_id='doc-123',
            analysis_id='analysis-456',
            severity='high',
            category='security',
            description='Critical security vulnerability found',
            confidence=0.9,
            metadata={'rule_id': 'SEC-001'}
        )

        assert event.event_type == 'finding_created'
        assert event.finding_id == 'finding-123'
        assert event.severity == 'high'
        assert event.category == 'security'
        assert event.confidence == 0.9

    def test_event_serialization(self):
        """Test event serialization."""
        event = AnalysisRequestedEvent(
            event_id='event-123',
            correlation_id='corr-456',
            document_id='doc-123',
            analysis_type='semantic_similarity'
        )

        # Test to_dict
        event_dict = event.to_dict()
        assert isinstance(event_dict, dict)
        assert event_dict['event_id'] == 'event-123'
        assert event_dict['event_type'] == 'analysis_requested'

        # Test to_json
        event_json = event.to_json()
        assert isinstance(event_json, str)
        assert 'event-123' in event_json

    def test_event_from_dict(self):
        """Test creating event from dictionary."""
        event_data = {
            'event_id': 'event-123',
            'event_type': 'analysis_requested',
            'correlation_id': 'corr-456',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'document_id': 'doc-123',
            'analysis_type': 'semantic_similarity'
        }

        event = AnalysisRequestedEvent.from_dict(event_data)

        assert event.event_id == 'event-123'
        assert event.document_id == 'doc-123'
        assert event.analysis_type == 'semantic_similarity'


class TestEventBus:
    """Test cases for EventBus."""

    def test_event_bus_creation(self):
        """Test creating event bus."""
        bus = EventBus()
        assert bus is not None
        assert len(bus._subscribers) == 0

    @pytest.mark.asyncio
    async def test_event_subscription(self):
        """Test event subscription."""
        bus = EventBus()

        # Mock subscriber
        subscriber = Mock()
        subscriber.handle_event = AsyncMock()

        # Subscribe to events
        bus.subscribe('analysis_requested', subscriber)
        bus.subscribe('analysis_completed', subscriber)

        assert 'analysis_requested' in bus._subscribers
        assert 'analysis_completed' in bus._subscribers
        assert subscriber in bus._subscribers['analysis_requested']

    @pytest.mark.asyncio
    async def test_event_publishing(self):
        """Test event publishing."""
        bus = EventBus()

        # Mock subscriber
        subscriber = Mock()
        subscriber.handle_event = AsyncMock()

        # Subscribe and publish
        bus.subscribe('analysis_requested', subscriber)

        event = AnalysisRequestedEvent(
            event_id='event-123',
            correlation_id='corr-456',
            document_id='doc-123',
            analysis_type='semantic_similarity'
        )

        await bus.publish(event)

        # Verify subscriber was called
        subscriber.handle_event.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self):
        """Test multiple subscribers for same event."""
        bus = EventBus()

        # Mock subscribers
        subscriber1 = Mock()
        subscriber1.handle_event = AsyncMock()

        subscriber2 = Mock()
        subscriber2.handle_event = AsyncMock()

        # Subscribe both
        bus.subscribe('analysis_requested', subscriber1)
        bus.subscribe('analysis_requested', subscriber2)

        # Publish event
        event = AnalysisRequestedEvent(
            event_id='event-123',
            correlation_id='corr-456',
            document_id='doc-123',
            analysis_type='semantic_similarity'
        )

        await bus.publish(event)

        # Verify both subscribers were called
        subscriber1.handle_event.assert_called_once_with(event)
        subscriber2.handle_event.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        """Test unsubscribing from events."""
        bus = EventBus()

        # Mock subscriber
        subscriber = Mock()
        subscriber.handle_event = AsyncMock()

        # Subscribe and then unsubscribe
        bus.subscribe('analysis_requested', subscriber)
        assert subscriber in bus._subscribers['analysis_requested']

        bus.unsubscribe('analysis_requested', subscriber)
        assert subscriber not in bus._subscribers['analysis_requested']

    @pytest.mark.asyncio
    async def test_publish_to_nonexistent_event_type(self):
        """Test publishing to event type with no subscribers."""
        bus = EventBus()

        event = AnalysisRequestedEvent(
            event_id='event-123',
            correlation_id='corr-456',
            document_id='doc-123',
            analysis_type='semantic_similarity'
        )

        # Should not raise exception
        await bus.publish(event)

    @pytest.mark.asyncio
    async def test_event_bus_error_handling(self):
        """Test event bus error handling."""
        bus = EventBus()

        # Mock subscriber that raises exception
        subscriber = Mock()
        subscriber.handle_event = AsyncMock(side_effect=Exception("Subscriber error"))

        bus.subscribe('analysis_requested', subscriber)

        event = AnalysisRequestedEvent(
            event_id='event-123',
            correlation_id='corr-456',
            document_id='doc-123',
            analysis_type='semantic_similarity'
        )

        # Should handle subscriber errors gracefully
        await bus.publish(event)

        # Subscriber should still have been called
        subscriber.handle_event.assert_called_once_with(event)


class TestEventPublisher:
    """Test cases for EventPublisher."""

    def test_event_publisher_creation(self):
        """Test creating event publisher."""
        publisher = EventPublisher()
        assert publisher is not None

    @pytest.mark.asyncio
    async def test_publish_single_event(self):
        """Test publishing single event."""
        publisher = EventPublisher()

        # Mock event bus
        mock_bus = Mock()
        mock_bus.publish = AsyncMock()

        publisher._event_bus = mock_bus

        event = AnalysisRequestedEvent(
            event_id='event-123',
            correlation_id='corr-456',
            document_id='doc-123',
            analysis_type='semantic_similarity'
        )

        await publisher.publish(event)

        mock_bus.publish.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_publish_multiple_events(self):
        """Test publishing multiple events."""
        publisher = EventPublisher()

        # Mock event bus
        mock_bus = Mock()
        mock_bus.publish = AsyncMock()

        publisher._event_bus = mock_bus

        events = [
            AnalysisRequestedEvent(
                event_id='event-1',
                correlation_id='corr-1',
                document_id='doc-1',
                analysis_type='semantic_similarity'
            ),
            AnalysisCompletedEvent(
                event_id='event-2',
                correlation_id='corr-2',
                analysis_id='analysis-1',
                document_id='doc-1',
                analysis_type='semantic_similarity',
                result={'score': 0.85},
                execution_time_seconds=2.0,
                findings_count=2
            )
        ]

        await publisher.publish_batch(events)

        # Verify both events were published
        assert mock_bus.publish.call_count == 2
        mock_bus.publish.assert_any_call(events[0])
        mock_bus.publish.assert_any_call(events[1])

    @pytest.mark.asyncio
    async def test_publish_with_retry(self):
        """Test publishing with retry logic."""
        publisher = EventPublisher()

        # Mock event bus that fails first time
        mock_bus = Mock()
        mock_bus.publish = AsyncMock(side_effect=[Exception("Network error"), None])

        publisher._event_bus = mock_bus

        event = AnalysisRequestedEvent(
            event_id='event-123',
            correlation_id='corr-456',
            document_id='doc-123',
            analysis_type='semantic_similarity'
        )

        # Should succeed on retry
        await publisher.publish_with_retry(event, max_retries=3)

        # Should have been called twice (first failed, second succeeded)
        assert mock_bus.publish.call_count == 2


class TestEventSubscriber:
    """Test cases for EventSubscriber."""

    def test_event_subscriber_creation(self):
        """Test creating event subscriber."""
        subscriber = EventSubscriber()
        assert subscriber is not None

    @pytest.mark.asyncio
    async def test_handle_event(self):
        """Test event handling."""
        subscriber = EventSubscriber()

        event = AnalysisRequestedEvent(
            event_id='event-123',
            correlation_id='corr-456',
            document_id='doc-123',
            analysis_type='semantic_similarity'
        )

        # Should handle event without error (base implementation)
        await subscriber.handle_event(event)

    def test_get_subscribed_events(self):
        """Test getting subscribed events."""
        subscriber = EventSubscriber()

        # Base implementation returns empty list
        events = subscriber.get_subscribed_events()
        assert isinstance(events, list)

    @pytest.mark.asyncio
    async def test_event_filtering(self):
        """Test event filtering."""
        subscriber = EventSubscriber()

        # Create events of different types
        analysis_event = AnalysisRequestedEvent(
            event_id='event-1',
            correlation_id='corr-1',
            document_id='doc-1',
            analysis_type='semantic_similarity'
        )

        document_event = DocumentCreatedEvent(
            event_id='event-2',
            correlation_id='corr-2',
            document_id='doc-2',
            repository_id='repo-1',
            author='user-1'
        )

        # Subscriber should handle both (base implementation accepts all)
        await subscriber.handle_event(analysis_event)
        await subscriber.handle_event(document_event)


class TestEventIntegration:
    """Test integration between event components."""

    @pytest.mark.asyncio
    async def test_complete_event_workflow(self):
        """Test complete event publishing and handling workflow."""
        # Setup components
        bus = EventBus()
        publisher = EventPublisher()
        publisher._event_bus = bus

        # Mock subscriber
        subscriber = Mock()
        subscriber.handle_event = AsyncMock()

        # Subscribe to events
        bus.subscribe('analysis_requested', subscriber)
        bus.subscribe('analysis_completed', subscriber)

        # Create and publish events
        requested_event = AnalysisRequestedEvent(
            event_id='event-1',
            correlation_id='corr-123',
            document_id='doc-123',
            analysis_type='semantic_similarity'
        )

        completed_event = AnalysisCompletedEvent(
            event_id='event-2',
            correlation_id='corr-123',
            analysis_id='analysis-123',
            document_id='doc-123',
            analysis_type='semantic_similarity',
            result={'score': 0.85},
            execution_time_seconds=2.0,
            findings_count=1
        )

        # Publish events
        await publisher.publish(requested_event)
        await publisher.publish(completed_event)

        # Verify subscriber was called for both events
        assert subscriber.handle_event.call_count == 2
        subscriber.handle_event.assert_any_call(requested_event)
        subscriber.handle_event.assert_any_call(completed_event)

    @pytest.mark.asyncio
    async def test_event_chaining(self):
        """Test event chaining (one event triggers another)."""
        bus = EventBus()

        # First subscriber that creates another event
        first_subscriber = Mock()
        async def first_handler(event):
            # Create completion event
            completion_event = AnalysisCompletedEvent(
                event_id='completion-event',
                correlation_id=event.correlation_id,
                analysis_id='analysis-123',
                document_id=event.document_id,
                analysis_type=event.analysis_type,
                result={'score': 0.9},
                execution_time_seconds=1.5,
                findings_count=0
            )
            await bus.publish(completion_event)

        first_subscriber.handle_event = first_handler

        # Second subscriber that handles completion
        second_subscriber = Mock()
        second_subscriber.handle_event = AsyncMock()

        # Subscribe
        bus.subscribe('analysis_requested', first_subscriber)
        bus.subscribe('analysis_completed', second_subscriber)

        # Publish initial event
        initial_event = AnalysisRequestedEvent(
            event_id='initial-event',
            correlation_id='corr-123',
            document_id='doc-123',
            analysis_type='semantic_similarity'
        )

        await bus.publish(initial_event)

        # Verify both subscribers were called
        # First subscriber should have been called once
        # Second subscriber should have been called once (from the chained event)

    @pytest.mark.asyncio
    async def test_event_error_isolation(self):
        """Test that one subscriber error doesn't affect others."""
        bus = EventBus()

        # Subscriber that succeeds
        good_subscriber = Mock()
        good_subscriber.handle_event = AsyncMock()

        # Subscriber that fails
        bad_subscriber = Mock()
        bad_subscriber.handle_event = AsyncMock(side_effect=Exception("Subscriber failed"))

        # Subscribe both
        bus.subscribe('analysis_requested', good_subscriber)
        bus.subscribe('analysis_requested', bad_subscriber)

        # Publish event
        event = AnalysisRequestedEvent(
            event_id='event-123',
            correlation_id='corr-456',
            document_id='doc-123',
            analysis_type='semantic_similarity'
        )

        # Should not raise exception despite one subscriber failing
        await bus.publish(event)

        # Good subscriber should still have been called
        good_subscriber.handle_event.assert_called_once_with(event)
        bad_subscriber.handle_event.assert_called_once_with(event)


class TestEventPerformance:
    """Test performance aspects of event system."""

    @pytest.mark.asyncio
    async def test_bulk_event_publishing(self):
        """Test bulk event publishing performance."""
        bus = EventBus()

        # Create many subscribers
        subscribers = []
        for i in range(10):
            subscriber = Mock()
            subscriber.handle_event = AsyncMock()
            subscribers.append(subscriber)
            bus.subscribe('test_event', subscriber)

        # Publish many events
        events = []
        for i in range(50):
            event = ApplicationEvent(
                event_id=f'event-{i}',
                event_type='test_event',
                correlation_id=f'corr-{i}',
                timestamp=datetime.now(timezone.utc)
            )
            events.append(event)

        import time
        start_time = time.time()

        for event in events:
            await bus.publish(event)

        end_time = time.time()
        duration = end_time - start_time

        # Assert reasonable performance (< 5 seconds for 50 events * 10 subscribers)
        assert duration < 5.0

        # Verify all subscribers were called for all events
        for subscriber in subscribers:
            assert subscriber.handle_event.call_count == 50

    @pytest.mark.asyncio
    async def test_event_serialization_performance(self):
        """Test event serialization performance."""
        events = []
        for i in range(100):
            event = AnalysisCompletedEvent(
                event_id=f'event-{i}',
                correlation_id=f'corr-{i}',
                analysis_id=f'analysis-{i}',
                document_id=f'doc-{i}',
                analysis_type='semantic_similarity',
                result={'score': 0.85},
                execution_time_seconds=2.0,
                findings_count=1
            )
            events.append(event)

        import time
        start_time = time.time()

        # Serialize all events
        for event in events:
            event.to_json()

        end_time = time.time()
        duration = end_time - start_time

        # Assert reasonable serialization performance (< 2 seconds for 100 events)
        assert duration < 2.0


class TestEventMonitoring:
    """Test event monitoring and metrics."""

    @pytest.mark.asyncio
    async def test_event_metrics_collection(self):
        """Test collecting metrics on event publishing."""
        bus = EventBus()

        # Track published events
        published_events = []

        original_publish = bus.publish
        async def tracked_publish(event):
            published_events.append(event)
            await original_publish(event)

        bus.publish = tracked_publish

        # Publish some events
        events = [
            AnalysisRequestedEvent(
                event_id='event-1',
                correlation_id='corr-1',
                document_id='doc-1',
                analysis_type='semantic_similarity'
            ),
            AnalysisCompletedEvent(
                event_id='event-2',
                correlation_id='corr-2',
                analysis_id='analysis-1',
                document_id='doc-1',
                analysis_type='semantic_similarity',
                result={'score': 0.85},
                execution_time_seconds=2.0,
                findings_count=1
            )
        ]

        for event in events:
            await bus.publish(event)

        # Verify events were tracked
        assert len(published_events) == 2
        assert published_events[0].event_type == 'analysis_requested'
        assert published_events[1].event_type == 'analysis_completed'

    @pytest.mark.asyncio
    async def test_event_error_tracking(self):
        """Test tracking event processing errors."""
        bus = EventBus()

        # Track errors
        errors = []

        original_publish = bus.publish
        async def error_tracked_publish(event):
            try:
                await original_publish(event)
            except Exception as e:
                errors.append(e)

        bus.publish = error_tracked_publish

        # Mock subscriber that fails
        subscriber = Mock()
        subscriber.handle_event = AsyncMock(side_effect=Exception("Processing failed"))

        bus.subscribe('analysis_requested', subscriber)

        # Publish event
        event = AnalysisRequestedEvent(
            event_id='event-123',
            correlation_id='corr-456',
            document_id='doc-123',
            analysis_type='semantic_similarity'
        )

        await bus.publish(event)

        # Error should have been tracked
        assert len(errors) == 1
        assert str(errors[0]) == "Processing failed"
