"""Unit tests for audit system functionality."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

from pages.audit import (
    get_audit_events, get_filtered_audit_events, render_audit_filters,
    export_audit_events, generate_audit_report, get_compliance_data
)


@pytest.mark.unit
class TestAuditEvents:
    """Test cases for audit event handling."""

    def test_get_audit_events_returns_list(self):
        """Test that get_audit_events returns proper list structure."""
        events = get_audit_events()

        assert isinstance(events, list)
        assert len(events) > 0

        # Check event structure
        event = events[0]
        required_keys = ["id", "event_type", "timestamp", "user", "severity"]

        for key in required_keys:
            assert key in event, f"Missing required key: {key}"

    def test_get_audit_events_structure(self):
        """Test audit event data structure."""
        events = get_audit_events()

        for event in events[:5]:  # Test first 5 events
            # Required fields
            assert "id" in event
            assert "event_type" in event
            assert "timestamp" in event
            assert "user" in event
            assert "severity" in event

            # Optional fields
            assert "description" in event
            assert "ip_address" in event

            # Data types
            assert isinstance(event["id"], str)
            assert isinstance(event["event_type"], str)
            assert isinstance(event["timestamp"], str)
            assert isinstance(event["user"], str)
            assert isinstance(event["severity"], str)

    def test_audit_events_timestamp_format(self):
        """Test that audit events have properly formatted timestamps."""
        events = get_audit_events()

        for event in events[:3]:
            timestamp = event["timestamp"]

            # Should be ISO format string
            try:
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                pytest.fail(f"Invalid timestamp format: {timestamp}")

    def test_audit_events_severity_levels(self):
        """Test that audit events have valid severity levels."""
        events = get_audit_events()
        valid_severities = ["low", "medium", "high", "critical"]

        for event in events[:10]:
            severity = event.get("severity", "").lower()
            assert severity in valid_severities, f"Invalid severity: {severity}"


@pytest.mark.unit
class TestAuditFiltering:
    """Test cases for audit event filtering."""

    def test_get_filtered_audit_events_no_filters(self):
        """Test filtering with no active filters."""
        with patch('pages.audit.st') as mock_st:
            mock_st.session_state = {'audit_filters': {}}

            filtered_events = get_filtered_audit_events()
            all_events = get_audit_events()

            # Should return all events when no filters
            assert len(filtered_events) == len(all_events)

    def test_get_filtered_audit_events_by_event_type(self):
        """Test filtering by event type."""
        with patch('pages.audit.st') as mock_st:
            mock_st.session_state = {
                'audit_filters': {
                    'event_types': ['simulation_started']
                }
            }

            filtered_events = get_filtered_audit_events()

            # All filtered events should match the type
            for event in filtered_events:
                assert event['event_type'] == 'simulation_started'

    def test_get_filtered_audit_events_by_user(self):
        """Test filtering by user."""
        with patch('pages.audit.st') as mock_st:
            mock_st.session_state = {
                'audit_filters': {
                    'users': ['admin']
                }
            }

            filtered_events = get_filtered_audit_events()

            # All filtered events should be from the specified user
            for event in filtered_events:
                assert event['user'] == 'admin'

    def test_get_filtered_audit_events_by_severity(self):
        """Test filtering by severity level."""
        with patch('pages.audit.st') as mock_st:
            mock_st.session_state = {
                'audit_filters': {
                    'severities': ['high', 'critical']
                }
            }

            filtered_events = get_filtered_audit_events()

            # All filtered events should have matching severity
            for event in filtered_events:
                assert event['severity'] in ['high', 'critical']

    def test_get_filtered_audit_events_date_range(self):
        """Test filtering by date range."""
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now() + timedelta(days=1)

        with patch('pages.audit.st') as mock_st:
            mock_st.session_state = {
                'audit_filters': {
                    'date_range': (start_date.date(), end_date.date())
                }
            }

            filtered_events = get_filtered_audit_events()

            # Should not raise exceptions and return events
            assert isinstance(filtered_events, list)

    @patch('pages.audit.st')
    def test_render_audit_filters_components(self, mock_st):
        """Test that audit filter rendering calls correct components."""
        mock_st.markdown = Mock()
        mock_st.expander = Mock(return_value=Mock())
        mock_st.multiselect = Mock(return_value=[])
        mock_st.date_input = Mock(return_value=datetime.now().date())
        mock_st.button = Mock(return_value=False)

        render_audit_filters()

        mock_st.expander.assert_called_once()
        assert mock_st.multiselect.call_count >= 3  # event_types, users, severities
        assert mock_st.date_input.call_count >= 2  # start_date, end_date


@pytest.mark.unit
class TestAuditExport:
    """Test cases for audit event export functionality."""

    @patch('pages.audit.st')
    def test_export_audit_events_csv(self, mock_st):
        """Test CSV export functionality."""
        mock_st.download_button = Mock()
        mock_st.success = Mock()

        test_events = [
            {
                "id": "audit_1",
                "event_type": "simulation_started",
                "timestamp": "2024-01-15T10:00:00Z",
                "user": "admin",
                "severity": "low"
            }
        ]

        export_audit_events(test_events, "csv")

        mock_st.download_button.assert_called_once()
        mock_st.success.assert_called_once_with("✅ Audit events exported as CSV!")

    @patch('pages.audit.st')
    def test_export_audit_events_json(self, mock_st):
        """Test JSON export functionality."""
        mock_st.download_button = Mock()
        mock_st.success = Mock()

        test_events = [
            {
                "id": "audit_1",
                "event_type": "simulation_started",
                "timestamp": "2024-01-15T10:00:00Z",
                "user": "admin",
                "severity": "low"
            }
        ]

        export_audit_events(test_events, "json")

        mock_st.download_button.assert_called_once()
        mock_st.success.assert_called_once_with("✅ Audit events exported as JSON!")

    @patch('pages.audit.st')
    def test_export_audit_events_error_handling(self, mock_st):
        """Test error handling in export functionality."""
        mock_st.error = Mock()

        # Pass invalid data that would cause export to fail
        export_audit_events(None, "csv")

        mock_st.error.assert_called_once()


@pytest.mark.unit
class TestAuditReporting:
    """Test cases for audit report generation."""

    @patch('pages.audit.st')
    def test_generate_audit_report_success(self, mock_st):
        """Test successful audit report generation."""
        mock_st.success = Mock()
        mock_st.code = Mock()

        test_events = [
            {
                "id": "audit_1",
                "event_type": "simulation_started",
                "timestamp": "2024-01-15T10:00:00Z",
                "user": "admin",
                "severity": "low"
            }
        ]

        generate_audit_report(test_events)

        mock_st.success.assert_called_once()
        mock_st.code.assert_called_once()

    @patch('pages.audit.st')
    def test_generate_audit_report_empty_events(self, mock_st):
        """Test audit report generation with empty events."""
        mock_st.success = Mock()
        mock_st.code = Mock()

        generate_audit_report([])

        mock_st.success.assert_called_once()
        mock_st.code.assert_called_once()


@pytest.mark.unit
class TestComplianceData:
    """Test cases for compliance data handling."""

    def test_get_compliance_data_structure(self):
        """Test compliance data structure."""
        compliance_data = get_compliance_data()

        required_keys = ['overall_score', 'policies_enforced', 'violations', 'last_audit', 'categories']

        for key in required_keys:
            assert key in compliance_data

        # Check score is reasonable
        assert 0 <= compliance_data['overall_score'] <= 100

        # Check categories structure
        categories = compliance_data['categories']
        assert isinstance(categories, dict)
        assert len(categories) > 0

    def test_compliance_categories_structure(self):
        """Test compliance categories data structure."""
        compliance_data = get_compliance_data()
        categories = compliance_data['categories']

        for category_name, category_data in categories.items():
            assert 'score' in category_data
            assert 'violations' in category_data
            assert isinstance(category_data['score'], (int, float))
            assert isinstance(category_data['violations'], int)


@pytest.mark.unit
class TestAuditPageRendering:
    """Test cases for audit page rendering."""

    @patch('pages.audit.st')
    def test_render_audit_log_basic_structure(self, mock_st):
        """Test basic audit log rendering structure."""
        mock_st.markdown = Mock()
        mock_st.columns = Mock(return_value=[Mock(), Mock(), Mock(), Mock()])
        mock_st.metric = Mock()
        mock_st.tabs = Mock(return_value=[Mock(), Mock(), Mock(), Mock()])
        mock_st.expander = Mock(return_value=Mock())

        from pages.audit import render_audit_log
        render_audit_log()

        # Verify basic structure components
        assert mock_st.markdown.call_count >= 2
        mock_st.columns.assert_called()
        mock_st.metric.assert_called()
        mock_st.tabs.assert_called()

    @patch('pages.audit.st')
    def test_render_event_analysis_structure(self, mock_st):
        """Test event analysis rendering structure."""
        mock_st.markdown = Mock()
        mock_st.columns = Mock(return_value=[Mock(), Mock(), Mock(), Mock()])
        mock_st.metric = Mock()

        from pages.audit import render_event_analysis
        render_event_analysis()

        # Verify analysis components
        assert mock_st.markdown.call_count >= 3
        mock_st.columns.assert_called()
        mock_st.metric.assert_called()

    @patch('pages.audit.st')
    def test_render_compliance_reports_structure(self, mock_st):
        """Test compliance reports rendering structure."""
        mock_st.markdown = Mock()
        mock_st.columns = Mock(return_value=[Mock(), Mock(), Mock(), Mock()])
        mock_st.metric = Mock()
        mock_st.selectbox = Mock(return_value="GDPR Compliance Report")

        from pages.audit import render_compliance_reports
        render_compliance_reports()

        # Verify compliance components
        assert mock_st.markdown.call_count >= 2
        mock_st.columns.assert_called()
        mock_st.metric.assert_called()

    @patch('pages.audit.st')
    def test_render_audit_configuration_structure(self, mock_st):
        """Test audit configuration rendering structure."""
        mock_st.markdown = Mock()
        mock_st.expander = Mock(return_value=Mock())
        mock_st.checkbox = Mock(return_value=True)
        mock_st.slider = Mock(return_value=90)
        mock_st.button = Mock(return_value=False)

        from pages.audit import render_audit_configuration
        render_audit_configuration()

        # Verify configuration components
        assert mock_st.markdown.call_count >= 2
        assert mock_st.expander.call_count >= 3  # Multiple expandable sections
        mock_st.checkbox.assert_called()
        mock_st.slider.assert_called()


@pytest.mark.unit
class TestAuditUtilityFunctions:
    """Test cases for audit utility functions."""

    def test_get_earliest_event_date_with_events(self):
        """Test getting earliest event date from events."""
        from pages.audit import get_earliest_event_date

        events = [
            {"timestamp": "2024-01-15T10:00:00Z"},
            {"timestamp": "2024-01-14T08:00:00Z"},
            {"timestamp": "2024-01-16T12:00:00Z"}
        ]

        earliest_date = get_earliest_event_date(events)
        assert earliest_date == datetime(2024, 1, 14).date()

    def test_get_earliest_event_date_empty_events(self):
        """Test getting earliest event date with empty events."""
        from pages.audit import get_earliest_event_date

        earliest_date = get_earliest_event_date([])
        assert earliest_date == datetime.now().date()

    def test_get_earliest_event_date_invalid_timestamps(self):
        """Test handling of invalid timestamps."""
        from pages.audit import get_earliest_event_date

        events = [
            {"timestamp": "invalid"},
            {"timestamp": "2024-01-15T10:00:00Z"}
        ]

        earliest_date = get_earliest_event_date(events)
        assert earliest_date == datetime(2024, 1, 15).date()


@pytest.mark.unit
class TestAuditEventAnalysis:
    """Test cases for audit event analysis functions."""

    def test_event_type_distribution_calculation(self):
        """Test event type distribution calculation."""
        from pages.audit import get_audit_events

        events = get_audit_events()

        # Calculate distribution manually
        event_counts = {}
        for event in events:
            event_type = event.get('event_type', 'Unknown')
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        # Verify we have some distribution
        assert len(event_counts) > 0
        assert sum(event_counts.values()) == len(events)

    def test_user_activity_analysis(self):
        """Test user activity analysis."""
        from pages.audit import get_audit_events

        events = get_audit_events()

        # Calculate user activity manually
        user_activity = {}
        for event in events:
            user = event.get('user', 'unknown')
            user_activity[user] = user_activity.get(user, 0) + 1

        # Verify we have user activity data
        assert len(user_activity) > 0
        assert all(count > 0 for count in user_activity.values())


if __name__ == "__main__":
    pytest.main([__file__])
