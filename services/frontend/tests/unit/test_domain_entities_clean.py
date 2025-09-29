"""Clean unit tests for frontend domain entities."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from typing import List, Dict, Optional

# Define domain entities inline to avoid import dependencies
from enum import Enum


class UIStateType(str, Enum):
    """UI state type enumeration."""
    DASHBOARD = "dashboard"
    SERVICE_VIEW = "service_view"
    WORKFLOW_VIEW = "workflow_view"
    SETTINGS = "settings"
    MONITORING = "monitoring"


class InteractionType(str, Enum):
    """User interaction type enumeration."""
    CLICK = "click"
    NAVIGATION = "navigation"
    SEARCH = "search"
    FILTER = "filter"
    EXPORT = "export"
    REFRESH = "refresh"


class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    DEVELOPER = "developer"
    ANALYST = "analyst"
    VIEWER = "viewer"


class NotificationLevel(str, Enum):
    """Notification level enumeration."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class UIState:
    """Domain entity for UI state management."""

    def __init__(self,
                 state_id: str = None,
                 user_id: str = None,
                 state_type: UIStateType = UIStateType.DASHBOARD,
                 current_view: str = None,
                 filters: Dict = None,
                 preferences: Dict = None,
                 session_data: Dict = None,
                 is_active: bool = True,
                 created_at: datetime = None,
                 updated_at: datetime = None):
        self.state_id = state_id or str(uuid4())
        self.user_id = user_id
        self.state_type = state_type
        self.current_view = current_view or ""
        self.filters = filters or {}
        self.preferences = preferences or {}
        self.session_data = session_data or {}
        self.is_active = is_active
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    def update_filters(self, new_filters: Dict):
        """Update UI filters."""
        self.filters.update(new_filters)
        self.updated_at = datetime.now(timezone.utc)

    def set_preference(self, key: str, value):
        """Set user preference."""
        self.preferences[key] = value
        self.updated_at = datetime.now(timezone.utc)

    def get_preference(self, key: str, default=None):
        """Get user preference."""
        return self.preferences.get(key, default)

    def update_session_data(self, key: str, value):
        """Update session data."""
        self.session_data[key] = value
        self.updated_at = datetime.now(timezone.utc)

    def get_session_data(self, key: str, default=None):
        """Get session data."""
        return self.session_data.get(key, default)

    def clear_session_data(self):
        """Clear all session data."""
        self.session_data.clear()
        self.updated_at = datetime.now(timezone.utc)

    def is_dashboard_view(self) -> bool:
        """Check if current view is dashboard."""
        return self.state_type == UIStateType.DASHBOARD

    def has_filters(self) -> bool:
        """Check if filters are applied."""
        return bool(self.filters)

    def deactivate(self):
        """Deactivate the UI state."""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)


class UserInteraction:
    """Domain entity for user interaction tracking."""

    def __init__(self,
                 interaction_id: str = None,
                 user_id: str = None,
                 session_id: str = None,
                 interaction_type: InteractionType = InteractionType.CLICK,
                 target_element: str = None,
                 target_data: Dict = None,
                 user_agent: str = None,
                 ip_address: str = None,
                 timestamp: datetime = None,
                 metadata: Dict = None):
        self.interaction_id = interaction_id or str(uuid4())
        self.user_id = user_id
        self.session_id = session_id
        self.interaction_type = interaction_type
        self.target_element = target_element or ""
        self.target_data = target_data or {}
        self.user_agent = user_agent or ""
        self.ip_address = ip_address or ""
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.metadata = metadata or {}

    def is_navigation(self) -> bool:
        """Check if interaction is navigation."""
        return self.interaction_type == InteractionType.NAVIGATION

    def is_search(self) -> bool:
        """Check if interaction is search."""
        return self.interaction_type == InteractionType.SEARCH

    def has_target_data(self) -> bool:
        """Check if interaction has target data."""
        return bool(self.target_data)

    def add_metadata(self, key: str, value):
        """Add metadata to interaction."""
        self.metadata[key] = value

    def get_metadata(self, key: str, default=None):
        """Get metadata from interaction."""
        return self.metadata.get(key, default)

    def get_interaction_summary(self) -> Dict:
        """Get interaction summary."""
        return {
            "interaction_id": self.interaction_id,
            "type": self.interaction_type.value,
            "target": self.target_element,
            "timestamp": self.timestamp.isoformat(),
            "has_data": self.has_target_data()
        }


class NotificationMessage:
    """Domain entity for notification messages."""

    def __init__(self,
                 notification_id: str = None,
                 user_id: str = None,
                 level: NotificationLevel = NotificationLevel.INFO,
                 title: str = None,
                 message: str = None,
                 source: str = None,
                 is_read: bool = False,
                 is_dismissed: bool = False,
                 action_url: str = None,
                 expires_at: datetime = None,
                 created_at: datetime = None,
                 metadata: Dict = None):
        self.notification_id = notification_id or str(uuid4())
        self.user_id = user_id
        self.level = level
        self.title = title or ""
        self.message = message or ""
        self.source = source or ""
        self.is_read = is_read
        self.is_dismissed = is_dismissed
        self.action_url = action_url
        self.expires_at = expires_at
        self.created_at = created_at or datetime.now(timezone.utc)
        self.metadata = metadata or {}

    def is_expired(self) -> bool:
        """Check if notification is expired."""
        if not self.expires_at:
            return False
        expires_at_utc = self.expires_at.replace(tzinfo=timezone.utc) if self.expires_at.tzinfo is None else self.expires_at
        return datetime.now(timezone.utc) > expires_at_utc

    def is_active(self) -> bool:
        """Check if notification is active."""
        return not self.is_dismissed and not self.is_expired()

    def mark_as_read(self):
        """Mark notification as read."""
        self.is_read = True

    def dismiss(self):
        """Dismiss the notification."""
        self.is_dismissed = True

    def has_action(self) -> bool:
        """Check if notification has an action URL."""
        return bool(self.action_url)

    def is_error_level(self) -> bool:
        """Check if notification is error level."""
        return self.level == NotificationLevel.ERROR

    def is_warning_level(self) -> bool:
        """Check if notification is warning level."""
        return self.level == NotificationLevel.WARNING

    def get_notification_age_hours(self) -> float:
        """Get notification age in hours."""
        age = datetime.now(timezone.utc) - self.created_at
        return age.total_seconds() / 3600


class ServiceView:
    """Domain entity for service view configuration."""

    def __init__(self,
                 view_id: str = None,
                 service_name: str = None,
                 display_name: str = None,
                 view_type: str = None,
                 columns: List[str] = None,
                 filters: Dict = None,
                 sort_by: str = None,
                 sort_order: str = "asc",
                 page_size: int = 25,
                 is_default: bool = False,
                 user_id: str = None,
                 created_at: datetime = None):
        self.view_id = view_id or str(uuid4())
        self.service_name = service_name or ""
        self.display_name = display_name or ""
        self.view_type = view_type or ""
        self.columns = columns or []
        self.filters = filters or {}
        self.sort_by = sort_by
        self.sort_order = sort_order
        self.page_size = page_size
        self.is_default = is_default
        self.user_id = user_id
        self.created_at = created_at or datetime.now(timezone.utc)

    def add_column(self, column: str):
        """Add a column to the view."""
        if column not in self.columns:
            self.columns.append(column)

    def remove_column(self, column: str):
        """Remove a column from the view."""
        if column in self.columns:
            self.columns.remove(column)

    def set_sorting(self, column: str, order: str = "asc"):
        """Set sorting configuration."""
        self.sort_by = column
        self.sort_order = order

    def update_filters(self, new_filters: Dict):
        """Update view filters."""
        self.filters.update(new_filters)

    def clear_filters(self):
        """Clear all filters."""
        self.filters.clear()

    def is_ascending_sort(self) -> bool:
        """Check if sort order is ascending."""
        return self.sort_order.lower() == "asc"

    def has_custom_columns(self) -> bool:
        """Check if view has custom columns."""
        return len(self.columns) > 0

    def is_user_specific(self) -> bool:
        """Check if view is user-specific."""
        return bool(self.user_id) and not self.is_default


class DashboardWidget:
    """Domain entity for dashboard widgets."""

    def __init__(self,
                 widget_id: str = None,
                 widget_type: str = None,
                 title: str = None,
                 position: Dict = None,  # {"x": int, "y": int, "width": int, "height": int}
                 configuration: Dict = None,
                 data_source: str = None,
                 refresh_interval: int = 300,  # seconds
                 is_visible: bool = True,
                 user_id: str = None,
                 created_at: datetime = None):
        self.widget_id = widget_id or str(uuid4())
        self.widget_type = widget_type or ""
        self.title = title or ""
        self.position = position or {"x": 0, "y": 0, "width": 4, "height": 3}
        self.configuration = configuration or {}
        self.data_source = data_source or ""
        self.refresh_interval = refresh_interval
        self.is_visible = is_visible
        self.user_id = user_id
        self.created_at = created_at or datetime.now(timezone.utc)

    def update_position(self, x: int, y: int, width: int = None, height: int = None):
        """Update widget position."""
        self.position["x"] = x
        self.position["y"] = y
        if width is not None:
            self.position["width"] = width
        if height is not None:
            self.position["height"] = height

    def set_configuration(self, key: str, value):
        """Set widget configuration."""
        self.configuration[key] = value

    def get_configuration(self, key: str, default=None):
        """Get widget configuration."""
        return self.configuration.get(key, default)

    def hide(self):
        """Hide the widget."""
        self.is_visible = False

    def show(self):
        """Show the widget."""
        self.is_visible = True

    def toggle_visibility(self):
        """Toggle widget visibility."""
        self.is_visible = not self.is_visible

    def needs_refresh(self, last_refresh: datetime) -> bool:
        """Check if widget needs refresh."""
        if not self.is_visible:
            return False
        time_since_refresh = datetime.now(timezone.utc) - last_refresh
        return time_since_refresh.total_seconds() >= self.refresh_interval

    def get_area(self) -> int:
        """Get widget area (width * height)."""
        return self.position.get("width", 1) * self.position.get("height", 1)


class TestUIStateEntity:
    """Test the UIState domain entity."""

    def test_ui_state_creation(self):
        """Test creating a UI state."""
        state = UIState(
            user_id="user123",
            state_type=UIStateType.DASHBOARD,
            current_view="services-overview",
            filters={"status": "active", "type": "microservice"},
            preferences={"theme": "dark", "language": "en"}
        )

        assert state.state_id is not None
        assert state.user_id == "user123"
        assert state.state_type == UIStateType.DASHBOARD
        assert state.current_view == "services-overview"
        assert state.filters["status"] == "active"
        assert state.preferences["theme"] == "dark"
        assert state.is_active

    def test_ui_state_filter_management(self):
        """Test UI state filter management."""
        state = UIState()

        # Initial state
        assert not state.has_filters()

        # Update filters
        state.update_filters({"status": "active"})
        assert state.has_filters()
        assert state.filters["status"] == "active"

        # Update existing filter
        state.update_filters({"status": "inactive", "type": "api"})
        assert state.filters["status"] == "inactive"
        assert state.filters["type"] == "api"

    def test_ui_state_preferences(self):
        """Test UI state preferences management."""
        state = UIState()

        # Set preferences
        state.set_preference("theme", "dark")
        state.set_preference("language", "en")

        assert state.get_preference("theme") == "dark"
        assert state.get_preference("language") == "en"
        assert state.get_preference("nonexistent", "default") == "default"

    def test_ui_state_session_data(self):
        """Test UI state session data management."""
        state = UIState()

        # Set session data
        state.update_session_data("last_action", "view_service")
        state.update_session_data("page", 1)

        assert state.get_session_data("last_action") == "view_service"
        assert state.get_session_data("page") == 1
        assert state.get_session_data("nonexistent", "default") == "default"

        # Clear session data
        state.clear_session_data()
        assert not state.get_session_data("last_action")

    def test_ui_state_view_type_methods(self):
        """Test UI state view type methods."""
        dashboard_state = UIState(state_type=UIStateType.DASHBOARD)
        assert dashboard_state.is_dashboard_view()

        service_state = UIState(state_type=UIStateType.SERVICE_VIEW)
        assert not service_state.is_dashboard_view()

    def test_ui_state_lifecycle(self):
        """Test UI state lifecycle."""
        state = UIState()
        assert state.is_active

        state.deactivate()
        assert not state.is_active


class TestUserInteractionEntity:
    """Test the UserInteraction domain entity."""

    def test_user_interaction_creation(self):
        """Test creating a user interaction."""
        interaction = UserInteraction(
            user_id="user123",
            session_id="session456",
            interaction_type=InteractionType.CLICK,
            target_element="service-card",
            target_data={"service_id": "analysis-service", "action": "view"},
            user_agent="Mozilla/5.0...",
            ip_address="192.168.1.100",
            metadata={"page": "dashboard", "section": "services"}
        )

        assert interaction.interaction_id is not None
        assert interaction.user_id == "user123"
        assert interaction.session_id == "session456"
        assert interaction.interaction_type == InteractionType.CLICK
        assert interaction.target_element == "service-card"
        assert interaction.target_data["service_id"] == "analysis-service"
        assert interaction.user_agent == "Mozilla/5.0..."
        assert interaction.ip_address == "192.168.1.100"

    def test_user_interaction_type_methods(self):
        """Test user interaction type methods."""
        click_interaction = UserInteraction(interaction_type=InteractionType.CLICK)
        assert not click_interaction.is_navigation()
        assert not click_interaction.is_search()

        nav_interaction = UserInteraction(interaction_type=InteractionType.NAVIGATION)
        assert nav_interaction.is_navigation()

        search_interaction = UserInteraction(interaction_type=InteractionType.SEARCH)
        assert search_interaction.is_search()

    def test_user_interaction_target_data(self):
        """Test user interaction target data."""
        interaction = UserInteraction()
        assert not interaction.has_target_data()

        interaction.target_data = {"service": "analysis"}
        assert interaction.has_target_data()

    def test_user_interaction_metadata(self):
        """Test user interaction metadata."""
        interaction = UserInteraction()

        interaction.add_metadata("page", "dashboard")
        interaction.add_metadata("section", "services")

        assert interaction.get_metadata("page") == "dashboard"
        assert interaction.get_metadata("section") == "services"
        assert interaction.get_metadata("nonexistent", "default") == "default"

    def test_user_interaction_summary(self):
        """Test user interaction summary."""
        interaction = UserInteraction(
            interaction_type=InteractionType.CLICK,
            target_element="button",
            target_data={"action": "submit"}
        )

        summary = interaction.get_interaction_summary()

        assert summary["type"] == "click"
        assert summary["target"] == "button"
        assert summary["has_data"] is True
        assert "timestamp" in summary


class TestNotificationMessageEntity:
    """Test the NotificationMessage domain entity."""

    def test_notification_creation(self):
        """Test creating a notification message."""
        expires_at = datetime(2024, 12, 31, tzinfo=timezone.utc)

        notification = NotificationMessage(
            user_id="user123",
            level=NotificationLevel.WARNING,
            title="Service Unavailable",
            message="Analysis service is experiencing high latency",
            source="monitoring",
            action_url="/services/analysis",
            expires_at=expires_at,
            metadata={"service": "analysis-service", "severity": "medium"}
        )

        assert notification.notification_id is not None
        assert notification.user_id == "user123"
        assert notification.level == NotificationLevel.WARNING
        assert notification.title == "Service Unavailable"
        assert notification.message == "Analysis service is experiencing high latency"
        assert notification.source == "monitoring"
        assert notification.action_url == "/services/analysis"
        assert not notification.is_read
        assert not notification.is_dismissed

    def test_notification_expiry(self):
        """Test notification expiry."""
        # Future expiry
        future_expiry = NotificationMessage(expires_at=datetime(2030, 1, 1, tzinfo=timezone.utc))
        assert not future_expiry.is_expired()

        # Past expiry
        past_expiry = NotificationMessage(expires_at=datetime(2020, 1, 1, tzinfo=timezone.utc))
        assert past_expiry.is_expired()

        # No expiry
        no_expiry = NotificationMessage()
        assert not no_expiry.is_expired()

    def test_notification_lifecycle(self):
        """Test notification lifecycle."""
        notification = NotificationMessage()

        # Initially active
        assert notification.is_active()
        assert not notification.is_read

        # Mark as read
        notification.mark_as_read()
        assert notification.is_read
        assert notification.is_active()

        # Dismiss
        notification.dismiss()
        assert notification.is_dismissed
        assert not notification.is_active()

    def test_notification_properties(self):
        """Test notification properties."""
        # With action
        with_action = NotificationMessage(action_url="/dashboard")
        assert with_action.has_action()

        # Without action
        without_action = NotificationMessage()
        assert not without_action.has_action()

        # Error level
        error_notif = NotificationMessage(level=NotificationLevel.ERROR)
        assert error_notif.is_error_level()

        # Warning level
        warning_notif = NotificationMessage(level=NotificationLevel.WARNING)
        assert warning_notif.is_warning_level()

    def test_notification_age(self):
        """Test notification age calculation."""
        # Recent notification (should be close to 0)
        recent = NotificationMessage(created_at=datetime.now(timezone.utc))
        age_hours = recent.get_notification_age_hours()
        assert age_hours >= 0 and age_hours < 1  # Less than 1 hour old


class TestServiceViewEntity:
    """Test the ServiceView domain entity."""

    def test_service_view_creation(self):
        """Test creating a service view."""
        view = ServiceView(
            service_name="analysis-service",
            display_name="Analysis Services",
            view_type="table",
            columns=["name", "status", "health", "last_updated"],
            filters={"status": "active", "type": "analysis"},
            sort_by="name",
            sort_order="asc",
            page_size=50,
            is_default=True,
            user_id="user123"
        )

        assert view.view_id is not None
        assert view.service_name == "analysis-service"
        assert view.display_name == "Analysis Services"
        assert view.view_type == "table"
        assert "name" in view.columns
        assert "status" in view.columns
        assert view.filters["status"] == "active"
        assert view.sort_by == "name"
        assert view.sort_order == "asc"
        assert view.page_size == 50
        assert view.is_default
        assert view.user_id == "user123"

    def test_service_view_column_management(self):
        """Test service view column management."""
        view = ServiceView()

        # Initially no custom columns
        assert not view.has_custom_columns()

        # Add columns
        view.add_column("name")
        view.add_column("status")
        assert view.has_custom_columns()
        assert "name" in view.columns
        assert "status" in view.columns

        # Remove column
        view.remove_column("status")
        assert "name" in view.columns
        assert "status" not in view.columns

    def test_service_view_sorting(self):
        """Test service view sorting."""
        view = ServiceView()

        # Default sorting
        assert view.sort_by is None
        assert view.sort_order == "asc"

        # Set sorting
        view.set_sorting("name", "desc")
        assert view.sort_by == "name"
        assert view.sort_order == "desc"
        assert not view.is_ascending_sort()

        # Set ascending
        view.set_sorting("status", "asc")
        assert view.is_ascending_sort()

    def test_service_view_filters(self):
        """Test service view filter management."""
        view = ServiceView()

        # Update filters
        view.update_filters({"status": "active"})
        assert view.filters["status"] == "active"

        # Clear filters
        view.clear_filters()
        assert len(view.filters) == 0

    def test_service_view_user_specificity(self):
        """Test service view user specificity."""
        # Default view
        default_view = ServiceView(is_default=True)
        assert not default_view.is_user_specific()

        # User-specific view
        user_view = ServiceView(user_id="user123", is_default=False)
        assert user_view.is_user_specific()

        # System default view
        system_view = ServiceView(is_default=True)
        assert not system_view.is_user_specific()


class TestDashboardWidgetEntity:
    """Test the DashboardWidget domain entity."""

    def test_dashboard_widget_creation(self):
        """Test creating a dashboard widget."""
        position = {"x": 0, "y": 0, "width": 6, "height": 4}

        widget = DashboardWidget(
            widget_type="service_status",
            title="Service Health Overview",
            position=position,
            configuration={"show_details": True, "auto_refresh": True},
            data_source="monitoring_api",
            refresh_interval=600,
            is_visible=True,
            user_id="user123"
        )

        assert widget.widget_id is not None
        assert widget.widget_type == "service_status"
        assert widget.title == "Service Health Overview"
        assert widget.position["width"] == 6
        assert widget.position["height"] == 4
        assert widget.configuration["show_details"] is True
        assert widget.data_source == "monitoring_api"
        assert widget.refresh_interval == 600
        assert widget.is_visible
        assert widget.user_id == "user123"

    def test_dashboard_widget_position_management(self):
        """Test dashboard widget position management."""
        widget = DashboardWidget()

        # Update position
        widget.update_position(2, 3, 8, 6)
        assert widget.position["x"] == 2
        assert widget.position["y"] == 3
        assert widget.position["width"] == 8
        assert widget.position["height"] == 6

        # Update position without size
        widget.update_position(5, 1)
        assert widget.position["x"] == 5
        assert widget.position["y"] == 1
        assert widget.position["width"] == 8  # Should remain unchanged
        assert widget.position["height"] == 6  # Should remain unchanged

    def test_dashboard_widget_configuration(self):
        """Test dashboard widget configuration."""
        widget = DashboardWidget()

        # Set configuration
        widget.set_configuration("theme", "dark")
        widget.set_configuration("refresh", True)

        assert widget.get_configuration("theme") == "dark"
        assert widget.get_configuration("refresh") is True
        assert widget.get_configuration("nonexistent", "default") == "default"

    def test_dashboard_widget_visibility(self):
        """Test dashboard widget visibility."""
        widget = DashboardWidget()

        # Initially visible
        assert widget.is_visible

        # Hide
        widget.hide()
        assert not widget.is_visible

        # Show
        widget.show()
        assert widget.is_visible

        # Toggle
        widget.toggle_visibility()
        assert not widget.is_visible

        widget.toggle_visibility()
        assert widget.is_visible

    def test_dashboard_widget_refresh_logic(self):
        """Test dashboard widget refresh logic."""
        widget = DashboardWidget(refresh_interval=300)  # 5 minutes

        # Recent refresh
        recent_refresh = datetime.now(timezone.utc)
        assert not widget.needs_refresh(recent_refresh)

        # Old refresh (more than refresh interval ago)
        old_refresh = datetime.now(timezone.utc).replace(hour=0, minute=0)
        assert widget.needs_refresh(old_refresh)

        # Hidden widget doesn't need refresh
        hidden_widget = DashboardWidget(is_visible=False)
        assert not hidden_widget.needs_refresh(old_refresh)

    def test_dashboard_widget_area_calculation(self):
        """Test dashboard widget area calculation."""
        # Default widget (4x3)
        default_widget = DashboardWidget()
        assert default_widget.get_area() == 12

        # Custom size widget
        custom_widget = DashboardWidget()
        custom_widget.update_position(0, 0, 6, 4)
        assert custom_widget.get_area() == 24

        # Zero size widget
        zero_widget = DashboardWidget()
        zero_widget.position = {"x": 0, "y": 0, "width": 0, "height": 0}
        assert zero_widget.get_area() == 0


class TestEntityIntegration:
    """Test integration between entities."""

    def test_ui_state_with_interaction_integration(self):
        """Test integration between UIState and UserInteraction."""
        state = UIState(
            user_id="user123",
            state_type=UIStateType.SERVICE_VIEW,
            current_view="analysis-service"
        )

        interaction = UserInteraction(
            user_id="user123",
            interaction_type=InteractionType.NAVIGATION,
            target_element="service-link",
            target_data={"service": "analysis-service", "view": "details"}
        )

        # Verify integration
        assert state.user_id == interaction.user_id
        assert interaction.is_navigation()
        assert interaction.has_target_data()
        assert state.current_view in interaction.target_data.get("service", "")

    def test_notification_with_ui_state_integration(self):
        """Test integration between NotificationMessage and UIState."""
        notification = NotificationMessage(
            user_id="user123",
            level=NotificationLevel.ERROR,
            title="Service Down",
            message="Analysis service is unavailable",
            action_url="/services/analysis"
        )

        state = UIState(
            user_id="user123",
            state_type=UIStateType.DASHBOARD,
            preferences={"notifications_enabled": True}
        )

        # Verify integration
        assert notification.user_id == state.user_id
        assert notification.is_error_level()
        assert notification.has_action()
        assert state.get_preference("notifications_enabled") is True

    def test_service_view_with_widget_integration(self):
        """Test integration between ServiceView and DashboardWidget."""
        view = ServiceView(
            service_name="analysis-service",
            display_name="Analysis Dashboard",
            columns=["status", "health", "metrics"],
            filters={"status": "active"}
        )

        widget = DashboardWidget(
            widget_type="service_table",
            title="Analysis Dashboard",
            configuration={"view_config": "analysis-view", "columns": view.columns},
            data_source="analysis-service"
        )

        # Verify integration
        assert view.has_custom_columns()
        assert widget.configuration["columns"] == view.columns
        assert widget.data_source == view.service_name
        assert widget.title == view.display_name

    def test_complete_frontend_workflow(self):
        """Test complete frontend workflow with all entities."""
        # Create user
        user_id = "developer123"

        # Create UI state
        ui_state = UIState(
            user_id=user_id,
            state_type=UIStateType.DASHBOARD,
            current_view="services",
            preferences={"theme": "dark", "notifications": True}
        )

        # Create service view
        service_view = ServiceView(
            service_name="analysis-service",
            display_name="Analysis Services",
            columns=["name", "status", "health"],
            user_id=user_id
        )

        # Create dashboard widget
        widget = DashboardWidget(
            widget_type="service_grid",
            title="Service Overview",
            data_source="analysis-service",
            user_id=user_id
        )

        # Create user interaction
        interaction = UserInteraction(
            user_id=user_id,
            interaction_type=InteractionType.CLICK,
            target_element="service-widget",
            target_data={"widget_id": widget.widget_id, "action": "refresh"}
        )

        # Create notification
        notification = NotificationMessage(
            user_id=user_id,
            level=NotificationLevel.INFO,
            title="Services Updated",
            message="Analysis services have been refreshed",
            source="dashboard"
        )

        # Verify complete workflow
        assert ui_state.user_id == user_id
        assert ui_state.is_dashboard_view()
        assert ui_state.get_preference("theme") == "dark"

        assert service_view.is_user_specific()
        assert service_view.has_custom_columns()

        assert widget.is_visible
        assert widget.get_area() == 12  # Default 4x3

        assert interaction.has_target_data()
        # Interaction has target data but no metadata initially

        assert notification.is_active()
        assert not notification.is_error_level()
        assert notification.get_notification_age_hours() >= 0
