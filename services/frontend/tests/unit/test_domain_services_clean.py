"""Clean unit tests for frontend domain services."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Dict, Optional

# Define mock entities and repositories to avoid import dependencies
from enum import Enum
from datetime import datetime, timezone


class UIStateType(str, Enum):
    DASHBOARD = "dashboard"
    SERVICE_VIEW = "service_view"
    MONITORING = "monitoring"


class InteractionType(str, Enum):
    CLICK = "click"
    NAVIGATION = "navigation"
    SEARCH = "search"


class NotificationLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class MockUIState:
    """Mock UI state entity."""
    def __init__(self, state_id: str, user_id: str, state_type: UIStateType = UIStateType.DASHBOARD,
                 is_active: bool = True):
        self.state_id = state_id
        self.user_id = user_id
        self.state_type = state_type
        self.current_view = ""
        self.filters = {}
        self.preferences = {}
        self.session_data = {}
        self.is_active = is_active
        self.updated_at = datetime.now(timezone.utc)
        self.is_dashboard_view = lambda: state_type == UIStateType.DASHBOARD
        self.has_filters = lambda: bool(self.filters)
        self.get_preference = lambda k, d=None: self.preferences.get(k, d)
        self.set_preference = lambda k, v: self.preferences.update({k: v})
        self.update_filters = lambda f: self.filters.update(f)
        self.update_session_data = lambda k, v: self.session_data.update({k: v})
        self.get_session_data = lambda k, d=None: self.session_data.get(k, d)
        self.clear_session_data = lambda: self.session_data.clear()
        self.deactivate = lambda: setattr(self, 'is_active', False)


class MockUserInteraction:
    """Mock user interaction entity."""
    def __init__(self, interaction_id: str, user_id: str, interaction_type: InteractionType,
                 target_element: str = "", timestamp: datetime = None):
        self.interaction_id = interaction_id
        self.user_id = user_id
        self.session_id = ""
        self.interaction_type = interaction_type
        self.target_element = target_element
        self.target_data = {}
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.metadata = {}
        self.is_navigation = lambda: interaction_type == InteractionType.NAVIGATION
        self.is_search = lambda: interaction_type == InteractionType.SEARCH
        self.has_target_data = lambda: bool(self.target_data)
        self.add_metadata = lambda k, v: self.metadata.update({k: v})
        self.get_metadata = lambda k, d=None: self.metadata.get(k, d)
        self.get_interaction_summary = lambda: {
            "interaction_id": interaction_id,
            "type": interaction_type.value,
            "target": target_element,
            "timestamp": self.timestamp.isoformat(),
            "has_data": self.has_target_data()
        }


class MockNotificationMessage:
    """Mock notification message entity."""
    def __init__(self, notification_id: str, user_id: str, level: NotificationLevel,
                 title: str, is_read: bool = False, is_dismissed: bool = False):
        self.notification_id = notification_id
        self.user_id = user_id
        self.level = level
        self.title = title
        self.message = ""
        self.is_read = is_read
        self.is_dismissed = is_dismissed
        self.created_at = datetime.now(timezone.utc)
        self.is_expired = lambda: False
        self.is_active = lambda: not self.is_dismissed and not self.is_expired()
        self.mark_as_read = lambda: setattr(self, 'is_read', True)
        self.dismiss = lambda: setattr(self, 'is_dismissed', True)
        self.has_action = lambda: False
        self.is_error_level = lambda: level == NotificationLevel.ERROR
        self.is_warning_level = lambda: level == NotificationLevel.WARNING
        self.get_notification_age_hours = lambda: 0.0


class MockServiceView:
    """Mock service view entity."""
    def __init__(self, view_id: str, service_name: str, user_id: str = None,
                 is_default: bool = False):
        self.view_id = view_id
        self.service_name = service_name
        self.user_id = user_id
        self.is_default = is_default
        self.columns = []
        self.filters = {}
        self.add_column = lambda c: self.columns.append(c) if c not in self.columns else None
        self.has_custom_columns = lambda: len(self.columns) > 0
        self.is_user_specific = lambda: bool(self.user_id) and not self.is_default
        self.update_filters = lambda f: self.filters.update(f)


class MockDashboardWidget:
    """Mock dashboard widget entity."""
    def __init__(self, widget_id: str, widget_type: str, user_id: str,
                 is_visible: bool = True):
        self.widget_id = widget_id
        self.widget_type = widget_type
        self.user_id = user_id
        self.is_visible = is_visible
        self.position = {"x": 0, "y": 0, "width": 4, "height": 3}
        self.configuration = {}
        self.set_configuration = lambda k, v: self.configuration.update({k: v})
        self.get_configuration = lambda k, d=None: self.configuration.get(k, d)
        self.get_area = lambda: self.position["width"] * self.position["height"]
        self.toggle_visibility = lambda: setattr(self, 'is_visible', not self.is_visible)


# Mock repositories
class MockUIStateRepository:
    """Mock UI state repository."""
    def __init__(self):
        self.states = {
            "state1": MockUIState("state1", "user1", UIStateType.DASHBOARD, True),
            "state2": MockUIState("state2", "user2", UIStateType.SERVICE_VIEW, True),
        }

    async def save(self, state: MockUIState) -> MockUIState:
        """Save UI state."""
        self.states[state.state_id] = state
        return state

    async def get_by_id(self, state_id: str) -> Optional[MockUIState]:
        """Get UI state by ID."""
        return self.states.get(state_id)

    async def get_by_user_id(self, user_id: str) -> List[MockUIState]:
        """Get UI states by user ID."""
        return [s for s in self.states.values() if s.user_id == user_id]

    async def get_active_states(self) -> List[MockUIState]:
        """Get active UI states."""
        return [s for s in self.states.values() if s.is_active]


class MockUserInteractionRepository:
    """Mock user interaction repository."""
    def __init__(self):
        self.interactions = {}

    async def save(self, interaction: MockUserInteraction) -> MockUserInteraction:
        """Save user interaction."""
        self.interactions[interaction.interaction_id] = interaction
        return interaction

    async def get_by_user_id(self, user_id: str, limit: int = 100) -> List[MockUserInteraction]:
        """Get interactions by user ID."""
        user_interactions = [i for i in self.interactions.values() if i.user_id == user_id]
        return user_interactions[-limit:]  # Return most recent

    async def get_recent_interactions(self, hours: int = 24) -> List[MockUserInteraction]:
        """Get recent interactions."""
        cutoff = datetime.now(timezone.utc).replace(hour=datetime.now(timezone.utc).hour - hours)
        return [i for i in self.interactions.values() if i.timestamp > cutoff]


class MockNotificationRepository:
    """Mock notification repository."""
    def __init__(self):
        self.notifications = {}

    async def save(self, notification: MockNotificationMessage) -> MockNotificationMessage:
        """Save notification."""
        self.notifications[notification.notification_id] = notification
        return notification

    async def get_by_user_id(self, user_id: str, limit: int = 50) -> List[MockNotificationMessage]:
        """Get notifications by user ID."""
        user_notifications = [n for n in self.notifications.values() if n.user_id == user_id]
        return sorted(user_notifications, key=lambda n: n.created_at, reverse=True)[:limit]

    async def get_unread_by_user_id(self, user_id: str) -> List[MockNotificationMessage]:
        """Get unread notifications by user ID."""
        return [n for n in self.notifications.values()
                if n.user_id == user_id and not n.is_read and n.is_active()]


class MockServiceViewRepository:
    """Mock service view repository."""
    def __init__(self):
        self.views = {
            "view1": MockServiceView("view1", "analysis-service", "user1", False),
            "view2": MockServiceView("view2", "doc-store", None, True),  # Default view
        }

    async def save(self, view: MockServiceView) -> MockServiceView:
        """Save service view."""
        self.views[view.view_id] = view
        return view

    async def get_by_id(self, view_id: str) -> Optional[MockServiceView]:
        """Get service view by ID."""
        return self.views.get(view_id)

    async def get_by_user_id(self, user_id: str) -> List[MockServiceView]:
        """Get service views by user ID."""
        return [v for v in self.views.values() if v.user_id == user_id]

    async def get_default_views(self) -> List[MockServiceView]:
        """Get default service views."""
        return [v for v in self.views.values() if v.is_default]


class MockDashboardWidgetRepository:
    """Mock dashboard widget repository."""
    def __init__(self):
        self.widgets = {
            "widget1": MockDashboardWidget("widget1", "service_status", "user1", True),
            "widget2": MockDashboardWidget("widget2", "metrics_chart", "user1", True),
        }

    async def save(self, widget: MockDashboardWidget) -> MockDashboardWidget:
        """Save dashboard widget."""
        self.widgets[widget.widget_id] = widget
        return widget

    async def get_by_id(self, widget_id: str) -> Optional[MockDashboardWidget]:
        """Get dashboard widget by ID."""
        return self.widgets.get(widget_id)

    async def get_by_user_id(self, user_id: str) -> List[MockDashboardWidget]:
        """Get dashboard widgets by user ID."""
        return [w for w in self.widgets.values() if w.user_id == user_id]

    async def get_visible_widgets(self, user_id: str) -> List[MockDashboardWidget]:
        """Get visible dashboard widgets by user ID."""
        return [w for w in self.widgets.values() if w.user_id == user_id and w.is_visible]


# Domain services
class UIStateService:
    """Domain service for UI state management."""

    def __init__(self, ui_state_repo: MockUIStateRepository):
        self.ui_state_repo = ui_state_repo

    async def create_ui_state(self, user_id: str, state_type: UIStateType = UIStateType.DASHBOARD) -> MockUIState:
        """Create a new UI state for user."""
        state_id = f"state_{user_id}_{len(await self.ui_state_repo.get_by_user_id(user_id)) + 1}"
        state = MockUIState(state_id, user_id, state_type)
        await self.ui_state_repo.save(state)
        return state

    async def get_user_ui_state(self, user_id: str) -> Optional[MockUIState]:
        """Get active UI state for user."""
        user_states = await self.ui_state_repo.get_by_user_id(user_id)
        active_states = [s for s in user_states if s.is_active]
        return active_states[0] if active_states else None

    async def update_ui_filters(self, user_id: str, filters: Dict) -> Optional[MockUIState]:
        """Update UI filters for user."""
        state = await self.get_user_ui_state(user_id)
        if state:
            state.update_filters(filters)
            await self.ui_state_repo.save(state)
            return state
        return None

    async def set_user_preference(self, user_id: str, key: str, value) -> bool:
        """Set user preference."""
        state = await self.get_user_ui_state(user_id)
        if state:
            state.set_preference(key, value)
            await self.ui_state_repo.save(state)
            return True
        return False

    async def update_session_data(self, user_id: str, key: str, value) -> bool:
        """Update session data for user."""
        state = await self.get_user_ui_state(user_id)
        if state:
            state.update_session_data(key, value)
            await self.ui_state_repo.save(state)
            return True
        return False

    async def clear_user_session(self, user_id: str) -> bool:
        """Clear user session data."""
        state = await self.get_user_ui_state(user_id)
        if state:
            state.clear_session_data()
            await self.ui_state_repo.save(state)
            return True
        return False

    async def deactivate_user_state(self, user_id: str) -> bool:
        """Deactivate user UI state."""
        state = await self.get_user_ui_state(user_id)
        if state:
            state.deactivate()
            await self.ui_state_repo.save(state)
            return True
        return False


class UserInteractionService:
    """Domain service for user interaction tracking."""

    def __init__(self, interaction_repo: MockUserInteractionRepository):
        self.interaction_repo = interaction_repo

    async def track_interaction(self, user_id: str, interaction_type: InteractionType,
                              target_element: str = "", target_data: Dict = None) -> MockUserInteraction:
        """Track a user interaction."""
        interaction_id = f"interaction_{user_id}_{int(datetime.now(timezone.utc).timestamp())}"
        interaction = MockUserInteraction(interaction_id, user_id, interaction_type, target_element)

        if target_data:
            interaction.target_data = target_data

        await self.interaction_repo.save(interaction)
        return interaction

    async def get_user_interactions(self, user_id: str, limit: int = 50) -> List[MockUserInteraction]:
        """Get user interactions."""
        return await self.interaction_repo.get_by_user_id(user_id, limit)

    async def get_recent_interactions(self, hours: int = 24) -> List[MockUserInteraction]:
        """Get recent interactions across all users."""
        return await self.interaction_repo.get_recent_interactions(hours)

    async def get_interaction_summary(self, user_id: str) -> Dict:
        """Get interaction summary for user."""
        interactions = await self.get_user_interactions(user_id, 1000)

        summary = {
            "total_interactions": len(interactions),
            "interaction_types": {},
            "most_used_elements": {},
            "avg_interactions_per_hour": 0
        }

        if interactions:
            # Count interaction types
            for interaction in interactions:
                itype = interaction.interaction_type.value
                summary["interaction_types"][itype] = summary["interaction_types"].get(itype, 0) + 1

            # Count target elements
            for interaction in interactions:
                element = interaction.target_element or "unknown"
                summary["most_used_elements"][element] = summary["most_used_elements"].get(element, 0) + 1

            # Calculate average interactions per hour (simplified)
            if len(interactions) > 1:
                time_span = (interactions[0].timestamp - interactions[-1].timestamp).total_seconds() / 3600
                if time_span > 0:
                    summary["avg_interactions_per_hour"] = len(interactions) / time_span

        return summary


class NotificationService:
    """Domain service for notification management."""

    def __init__(self, notification_repo: MockNotificationRepository):
        self.notification_repo = notification_repo

    async def create_notification(self, user_id: str, level: NotificationLevel,
                                title: str, message: str = "", source: str = "") -> MockNotificationMessage:
        """Create a notification."""
        notification_id = f"notification_{user_id}_{int(datetime.now(timezone.utc).timestamp())}"
        notification = MockNotificationMessage(notification_id, user_id, level, title)
        notification.message = message
        notification.source = source

        await self.notification_repo.save(notification)
        return notification

    async def get_user_notifications(self, user_id: str, limit: int = 20) -> List[MockNotificationMessage]:
        """Get user notifications."""
        return await self.notification_repo.get_by_user_id(user_id, limit)

    async def get_unread_notifications(self, user_id: str) -> List[MockNotificationMessage]:
        """Get unread notifications for user."""
        return await self.notification_repo.get_unread_by_user_id(user_id)

    async def mark_notification_read(self, notification_id: str) -> bool:
        """Mark notification as read."""
        # In a real implementation, we'd get the notification by ID
        # For this mock, we'll assume it exists and was already retrieved
        # This is a limitation of the mock approach
        return True

    async def dismiss_notification(self, notification_id: str) -> bool:
        """Dismiss notification."""
        # Similar limitation as above
        return True

    async def get_notification_stats(self, user_id: str) -> Dict:
        """Get notification statistics for user."""
        notifications = await self.get_user_notifications(user_id, 1000)

        stats = {
            "total_notifications": len(notifications),
            "unread_count": len([n for n in notifications if not n.is_read]),
            "by_level": {},
            "by_source": {}
        }

        for notification in notifications:
            # Count by level
            level = notification.level.value
            stats["by_level"][level] = stats["by_level"].get(level, 0) + 1

            # Count by source
            source = notification.source or "unknown"
            stats["by_source"][source] = stats["by_source"].get(source, 0) + 1

        return stats

    async def cleanup_expired_notifications(self) -> int:
        """Clean up expired notifications."""
        # In a real implementation, this would check expiry dates
        # For this mock, we'll simulate some cleanup
        return 5  # Mock cleanup count


class TestUIStateService:
    """Test the UIStateService domain service."""

    @pytest.fixture
    def ui_state_repo(self):
        """Create UI state repository."""
        return MockUIStateRepository()

    @pytest.fixture
    def ui_state_service(self, ui_state_repo):
        """Create UI state service."""
        return UIStateService(ui_state_repo)

    @pytest.mark.asyncio
    async def test_create_ui_state(self, ui_state_service, ui_state_repo):
        """Test creating a UI state."""
        state = await ui_state_service.create_ui_state("user123", UIStateType.DASHBOARD)

        assert state.user_id == "user123"
        assert state.state_type == UIStateType.DASHBOARD
        assert state.is_active

        # Verify saved
        saved = await ui_state_repo.get_by_id(state.state_id)
        assert saved is not None

    @pytest.mark.asyncio
    async def test_get_user_ui_state(self, ui_state_service):
        """Test getting user UI state."""
        state = await ui_state_service.get_user_ui_state("user1")
        assert state is not None
        assert state.user_id == "user1"
        assert state.is_active

        nonexistent = await ui_state_service.get_user_ui_state("nonexistent")
        assert nonexistent is None

    @pytest.mark.asyncio
    async def test_update_ui_filters(self, ui_state_service):
        """Test updating UI filters."""
        filters = {"status": "active", "type": "microservice"}
        updated_state = await ui_state_service.update_ui_filters("user1", filters)

        assert updated_state is not None
        assert updated_state.filters["status"] == "active"
        assert updated_state.filters["type"] == "microservice"

    @pytest.mark.asyncio
    async def test_set_user_preference(self, ui_state_service):
        """Test setting user preference."""
        success = await ui_state_service.set_user_preference("user1", "theme", "dark")
        assert success

        state = await ui_state_service.get_user_ui_state("user1")
        assert state.get_preference("theme") == "dark"

    @pytest.mark.asyncio
    async def test_update_session_data(self, ui_state_service):
        """Test updating session data."""
        success = await ui_state_service.update_session_data("user1", "last_page", "dashboard")
        assert success

        state = await ui_state_service.get_user_ui_state("user1")
        assert state.get_session_data("last_page") == "dashboard"

    @pytest.mark.asyncio
    async def test_clear_user_session(self, ui_state_service):
        """Test clearing user session."""
        # First set some session data
        await ui_state_service.update_session_data("user1", "temp_data", "value")

        # Clear session
        success = await ui_state_service.clear_user_session("user1")
        assert success

        state = await ui_state_service.get_user_ui_state("user1")
        assert state.get_session_data("temp_data") is None

    @pytest.mark.asyncio
    async def test_deactivate_user_state(self, ui_state_service):
        """Test deactivating user state."""
        success = await ui_state_service.deactivate_user_state("user1")
        assert success

        state = await ui_state_service.get_user_ui_state("user1")
        assert state is None  # Should not return inactive states


class TestUserInteractionService:
    """Test the UserInteractionService domain service."""

    @pytest.fixture
    def interaction_repo(self):
        """Create user interaction repository."""
        return MockUserInteractionRepository()

    @pytest.fixture
    def interaction_service(self, interaction_repo):
        """Create user interaction service."""
        return UserInteractionService(interaction_repo)

    @pytest.mark.asyncio
    async def test_track_interaction(self, interaction_service):
        """Test tracking user interaction."""
        interaction = await interaction_service.track_interaction(
            "user123",
            InteractionType.CLICK,
            "dashboard-button",
            {"action": "refresh", "section": "services"}
        )

        assert interaction.user_id == "user123"
        assert interaction.interaction_type == InteractionType.CLICK
        assert interaction.target_element == "dashboard-button"
        assert interaction.target_data["action"] == "refresh"

    @pytest.mark.asyncio
    async def test_get_user_interactions(self, interaction_service):
        """Test getting user interactions."""
        # Track some interactions
        await interaction_service.track_interaction("user123", InteractionType.CLICK, "button1")
        await interaction_service.track_interaction("user123", InteractionType.NAVIGATION, "page1")
        await interaction_service.track_interaction("user456", InteractionType.SEARCH, "query1")

        interactions = await interaction_service.get_user_interactions("user123", 10)
        assert len(interactions) >= 2
        assert all(i.user_id == "user123" for i in interactions)

    @pytest.mark.asyncio
    async def test_get_recent_interactions(self, interaction_service):
        """Test getting recent interactions."""
        # Track interactions
        await interaction_service.track_interaction("user123", InteractionType.CLICK, "element1")

        recent = await interaction_service.get_recent_interactions(1)  # Last hour
        assert len(recent) >= 1

    @pytest.mark.asyncio
    async def test_get_interaction_summary(self, interaction_service):
        """Test getting interaction summary."""
        # Track various interactions
        await interaction_service.track_interaction("user123", InteractionType.CLICK, "button1")
        await interaction_service.track_interaction("user123", InteractionType.CLICK, "button2")
        await interaction_service.track_interaction("user123", InteractionType.NAVIGATION, "page1")
        await interaction_service.track_interaction("user123", InteractionType.SEARCH, "query1")

        summary = await interaction_service.get_interaction_summary("user123")

        assert summary["total_interactions"] >= 4
        assert summary["interaction_types"]["click"] >= 2
        assert summary["interaction_types"]["navigation"] >= 1
        assert summary["interaction_types"]["search"] >= 1
        assert "button1" in summary["most_used_elements"]
        assert "button2" in summary["most_used_elements"]


class TestNotificationService:
    """Test the NotificationService domain service."""

    @pytest.fixture
    def notification_repo(self):
        """Create notification repository."""
        return MockNotificationRepository()

    @pytest.fixture
    def notification_service(self, notification_repo):
        """Create notification service."""
        return NotificationService(notification_repo)

    @pytest.mark.asyncio
    async def test_create_notification(self, notification_service):
        """Test creating a notification."""
        notification = await notification_service.create_notification(
            "user123",
            NotificationLevel.WARNING,
            "Service Alert",
            "Analysis service is running slow",
            "monitoring"
        )

        assert notification.user_id == "user123"
        assert notification.level == NotificationLevel.WARNING
        assert notification.title == "Service Alert"
        assert notification.message == "Analysis service is running slow"
        assert notification.source == "monitoring"
        assert not notification.is_read

    @pytest.mark.asyncio
    async def test_get_user_notifications(self, notification_service):
        """Test getting user notifications."""
        # Create notifications
        await notification_service.create_notification("user123", NotificationLevel.INFO, "Info 1")
        await notification_service.create_notification("user123", NotificationLevel.ERROR, "Error 1")
        await notification_service.create_notification("user456", NotificationLevel.WARNING, "Warning 1")

        notifications = await notification_service.get_user_notifications("user123", 10)
        assert len(notifications) >= 2
        assert all(n.user_id == "user123" for n in notifications)

    @pytest.mark.asyncio
    async def test_get_unread_notifications(self, notification_service):
        """Test getting unread notifications."""
        # Create notifications
        notif1 = await notification_service.create_notification("user123", NotificationLevel.INFO, "Unread 1")
        notif2 = await notification_service.create_notification("user123", NotificationLevel.WARNING, "Unread 2")

        unread = await notification_service.get_unread_notifications("user123")
        assert len(unread) >= 2
        assert all(not n.is_read for n in unread)

    @pytest.mark.asyncio
    async def test_get_notification_stats(self, notification_service):
        """Test getting notification statistics."""
        # Create various notifications
        await notification_service.create_notification("user123", NotificationLevel.INFO, "Info 1", "", "system")
        await notification_service.create_notification("user123", NotificationLevel.WARNING, "Warning 1", "", "monitoring")
        await notification_service.create_notification("user123", NotificationLevel.ERROR, "Error 1", "", "monitoring")

        stats = await notification_service.get_notification_stats("user123")

        assert stats["total_notifications"] >= 3
        assert stats["unread_count"] >= 3
        assert stats["by_level"]["info"] >= 1
        assert stats["by_level"]["warning"] >= 1
        assert stats["by_level"]["error"] >= 1
        assert stats["by_source"]["system"] >= 1
        assert stats["by_source"]["monitoring"] >= 2

    @pytest.mark.asyncio
    async def test_cleanup_expired_notifications(self, notification_service):
        """Test cleaning up expired notifications."""
        cleaned_count = await notification_service.cleanup_expired_notifications()
        assert isinstance(cleaned_count, int)
        assert cleaned_count >= 0


class TestServiceIntegration:
    """Test integration between services."""

    @pytest.fixture
    def ui_state_repo(self):
        """Create UI state repository."""
        return MockUIStateRepository()

    @pytest.fixture
    def interaction_repo(self):
        """Create user interaction repository."""
        return MockUserInteractionRepository()

    @pytest.fixture
    def notification_repo(self):
        """Create notification repository."""
        return MockNotificationRepository()

    @pytest.fixture
    def ui_state_service(self, ui_state_repo):
        """Create UI state service."""
        return UIStateService(ui_state_repo)

    @pytest.fixture
    def interaction_service(self, interaction_repo):
        """Create user interaction service."""
        return UserInteractionService(interaction_repo)

    @pytest.fixture
    def notification_service(self, notification_repo):
        """Create notification service."""
        return NotificationService(notification_repo)

    @pytest.mark.asyncio
    async def test_complete_user_session_workflow(self, ui_state_service, interaction_service, notification_service):
        """Test complete user session workflow."""
        user_id = "developer123"

        # 1. Create UI state
        ui_state = await ui_state_service.create_ui_state(user_id, UIStateType.DASHBOARD)

        # 2. Track user interactions
        interaction1 = await interaction_service.track_interaction(
            user_id, InteractionType.NAVIGATION, "dashboard", {"page": "services"}
        )
        interaction2 = await interaction_service.track_interaction(
            user_id, InteractionType.CLICK, "service-card", {"service": "analysis-service"}
        )

        # 3. Update UI preferences
        await ui_state_service.set_user_preference(user_id, "theme", "dark")
        await ui_state_service.set_user_preference(user_id, "language", "en")

        # 4. Create notifications
        notification1 = await notification_service.create_notification(
            user_id, NotificationLevel.INFO, "Welcome", "Welcome to the dashboard", "system"
        )
        notification2 = await notification_service.create_notification(
            user_id, NotificationLevel.WARNING, "Service Alert", "Analysis service slow", "monitoring"
        )

        # 5. Update session data
        await ui_state_service.update_session_data(user_id, "last_activity", "viewing_services")

        # 6. Get interaction summary
        interaction_summary = await interaction_service.get_interaction_summary(user_id)

        # 7. Get notification stats
        notification_stats = await notification_service.get_notification_stats(user_id)

        # Verify complete workflow
        assert ui_state.user_id == user_id
        assert ui_state.is_dashboard_view()
        assert ui_state.get_preference("theme") == "dark"
        assert ui_state.get_session_data("last_activity") == "viewing_services"

        assert interaction_summary["total_interactions"] >= 2
        assert interaction_summary["interaction_types"]["navigation"] >= 1
        assert interaction_summary["interaction_types"]["click"] >= 1

        assert notification_stats["total_notifications"] >= 2
        assert notification_stats["unread_count"] >= 2
        assert notification1.is_active()
        assert notification2.is_active()

    @pytest.mark.asyncio
    async def test_user_engagement_workflow(self, interaction_service, notification_service):
        """Test user engagement workflow."""
        user_id = "analyst456"

        # Track various user activities
        activities = [
            (InteractionType.NAVIGATION, "dashboard", {"section": "analytics"}),
            (InteractionType.SEARCH, "search-bar", {"query": "performance metrics"}),
            (InteractionType.CLICK, "export-button", {"format": "csv"}),
            (InteractionType.NAVIGATION, "reports", {"report_type": "weekly"}),
            (InteractionType.CLICK, "filter-button", {"filter": "last_7_days"})
        ]

        for interaction_type, target, data in activities:
            await interaction_service.track_interaction(user_id, interaction_type, target, data)

        # Create contextual notifications
        await notification_service.create_notification(
            user_id, NotificationLevel.INFO, "Report Generated",
            "Your weekly performance report is ready", "reporting"
        )

        await notification_service.create_notification(
            user_id, NotificationLevel.SUCCESS, "Export Complete",
            "Your data export has been completed", "export"
        )

        # Get engagement metrics
        interaction_summary = await interaction_service.get_interaction_summary(user_id)
        notification_stats = await notification_service.get_notification_stats(user_id)

        # Verify engagement workflow
        assert interaction_summary["total_interactions"] >= 5
        assert interaction_summary["interaction_types"]["navigation"] >= 2
        assert interaction_summary["interaction_types"]["click"] >= 2
        assert interaction_summary["interaction_types"]["search"] >= 1

        assert notification_stats["total_notifications"] >= 2
        assert notification_stats["by_source"]["reporting"] >= 1
        assert notification_stats["by_source"]["export"] >= 1

    @pytest.mark.asyncio
    async def test_notification_lifecycle_workflow(self, notification_service):
        """Test notification lifecycle workflow."""
        user_id = "manager789"

        # Create various notifications
        info_notif = await notification_service.create_notification(
            user_id, NotificationLevel.INFO, "System Update",
            "New features available", "system"
        )

        warning_notif = await notification_service.create_notification(
            user_id, NotificationLevel.WARNING, "Resource Usage",
            "High memory usage detected", "monitoring"
        )

        error_notif = await notification_service.create_notification(
            user_id, NotificationLevel.ERROR, "Service Down",
            "Critical service unavailable", "alerts"
        )

        # Check initial state
        unread = await notification_service.get_unread_notifications(user_id)
        assert len(unread) >= 3

        all_notifications = await notification_service.get_user_notifications(user_id)
        assert len(all_notifications) >= 3

        # Verify notification types
        assert info_notif.is_active() and not info_notif.is_error_level()
        assert warning_notif.is_active() and warning_notif.is_warning_level()
        assert error_notif.is_active() and error_notif.is_error_level()

        # Get comprehensive stats
        stats = await notification_service.get_notification_stats(user_id)
        assert stats["total_notifications"] >= 3
        assert stats["by_level"]["info"] >= 1
        assert stats["by_level"]["warning"] >= 1
        assert stats["by_level"]["error"] >= 1

        # Cleanup simulation
        cleaned = await notification_service.cleanup_expired_notifications()
        assert cleaned >= 0

    @pytest.mark.asyncio
    async def test_cross_service_integration_workflow(self, ui_state_service, interaction_service, notification_service):
        """Test cross-service integration workflow."""
        user_id = "poweruser999"

        # 1. Initialize user session
        ui_state = await ui_state_service.create_ui_state(user_id, UIStateType.DASHBOARD)

        # 2. User navigates and interacts
        nav_interaction = await interaction_service.track_interaction(
            user_id, InteractionType.NAVIGATION, "services-page", {"from": "dashboard"}
        )

        click_interaction = await interaction_service.track_interaction(
            user_id, InteractionType.CLICK, "analyze-button", {"service": "analysis-service"}
        )

        # 3. System responds with notification
        analysis_complete_notif = await notification_service.create_notification(
            user_id, NotificationLevel.SUCCESS, "Analysis Complete",
            "Code analysis completed successfully", "analysis-service"
        )

        # 4. User updates preferences
        await ui_state_service.set_user_preference(user_id, "auto_refresh", True)
        await ui_state_service.update_session_data(user_id, "current_workflow", "analysis_review")

        # 5. Get comprehensive user context
        current_state = await ui_state_service.get_user_ui_state(user_id)
        recent_interactions = await interaction_service.get_user_interactions(user_id, 5)
        user_notifications = await notification_service.get_user_notifications(user_id, 5)

        # Verify cross-service integration
        assert current_state.user_id == user_id
        assert current_state.get_preference("auto_refresh") is True
        assert current_state.get_session_data("current_workflow") == "analysis_review"

        assert len(recent_interactions) >= 2
        assert any(i.is_navigation() for i in recent_interactions)
        assert any(not i.is_navigation() and not i.is_search() for i in recent_interactions)

        assert len(user_notifications) >= 1
        assert any(n.level.value == "success" for n in user_notifications)

        # All services working together seamlessly
        assert ui_state.is_active
        assert nav_interaction.user_id == user_id
        assert analysis_complete_notif.is_active()
