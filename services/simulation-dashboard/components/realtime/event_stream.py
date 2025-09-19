"""Event Stream Component.

This module provides real-time event streaming and display capabilities,
with filtering, search, and live updates.
"""

import streamlit as st
from typing import Dict, Any, Optional, List, Callable
import pandas as pd
from datetime import datetime, timedelta
import time
import json


def render_event_stream(
    events_data: List[Dict[str, Any]],
    title: str = "📡 Live Event Stream",
    enable_filtering: bool = True,
    enable_search: bool = True,
    max_display_events: int = 100,
    auto_scroll: bool = True,
    on_event_click: Optional[Callable] = None
) -> Dict[str, Any]:
    """Render a live event stream with real-time updates.

    Args:
        events_data: Initial events data
        title: Stream title
        enable_filtering: Whether to enable event filtering
        enable_search: Whether to enable search
        max_display_events: Maximum events to display
        auto_scroll: Whether to auto-scroll to new events
        on_event_click: Callback for event clicks

    Returns:
        Dictionary with current events and stream status
    """
    st.markdown(f"### {title}")

    # Initialize session state for event stream
    if 'event_stream_data' not in st.session_state:
        st.session_state.event_stream_data = events_data.copy() if events_data else []
    if 'event_filters' not in st.session_state:
        st.session_state.event_filters = {
            'severity': [],
            'event_type': [],
            'source': [],
            'time_range': '1h'
        }
    if 'event_search' not in st.session_state:
        st.session_state.event_search = ""
    if 'stream_paused' not in st.session_state:
        st.session_state.stream_paused = False

    # Control panel
    display_stream_controls()

    # Filters and search
    if enable_filtering or enable_search:
        display_stream_filters(enable_filtering, enable_search)

    # Update event stream
    update_event_stream()

    # Display events
    filtered_events = get_filtered_events()
    display_event_stream(filtered_events, max_display_events, auto_scroll, on_event_click)

    # Stream statistics
    display_stream_statistics(filtered_events)

    return {
        'current_events': st.session_state.get('event_stream_data', []),
        'filtered_events': filtered_events,
        'stream_status': 'active' if not st.session_state.get('stream_paused', False) else 'paused',
        'filters': st.session_state.get('event_filters', {})
    }


def display_stream_controls():
    """Display stream control panel."""
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 2, 1])

    with col1:
        if st.button("🔄 Refresh", key="refresh_stream"):
            update_event_stream()
            st.rerun()

    with col2:
        pause_label = "⏸️ Pause" if not st.session_state.get('stream_paused', False) else "▶️ Resume"
        if st.button(pause_label, key="toggle_pause"):
            st.session_state.stream_paused = not st.session_state.get('stream_paused', False)
            st.rerun()

    with col3:
        if st.button("🗑️ Clear", key="clear_stream"):
            st.session_state.event_stream_data = []
            st.success("✅ Event stream cleared")
            st.rerun()

    with col4:
        auto_scroll = st.checkbox("Auto-scroll", value=True, key="auto_scroll")

    with col5:
        export_events = st.button("📥 Export", key="export_events")
        if export_events:
            events_df = pd.DataFrame(st.session_state.get('event_stream_data', []))
            if not events_df.empty:
                csv_data = events_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name="events.csv",
                    mime='text/csv',
                    key="download_events_csv"
                )


def display_stream_filters(enable_filtering: bool, enable_search: bool):
    """Display filtering and search options."""
    with st.expander("🔍 Filters & Search", expanded=False):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if enable_filtering:
                severity_options = ['critical', 'high', 'medium', 'low', 'info']
                selected_severity = st.multiselect(
                    "Severity",
                    options=severity_options,
                    default=st.session_state.event_filters.get('severity', []),
                    key="severity_filter"
                )
                st.session_state.event_filters['severity'] = selected_severity

        with col2:
            if enable_filtering:
                # Get unique event types from current data
                all_events = st.session_state.get('event_stream_data', [])
                event_types = list(set([e.get('event_type', 'unknown') for e in all_events]))
                selected_types = st.multiselect(
                    "Event Type",
                    options=event_types,
                    default=st.session_state.event_filters.get('event_type', []),
                    key="event_type_filter"
                )
                st.session_state.event_filters['event_type'] = selected_types

        with col3:
            if enable_filtering:
                time_ranges = ['5m', '15m', '1h', '6h', '24h', 'all']
                selected_time = st.selectbox(
                    "Time Range",
                    options=time_ranges,
                    index=time_ranges.index(st.session_state.event_filters.get('time_range', '1h')),
                    key="time_filter"
                )
                st.session_state.event_filters['time_range'] = selected_time

        with col4:
            if enable_search:
                search_term = st.text_input(
                    "Search Events",
                    value=st.session_state.get('event_search', ''),
                    placeholder="Search by message, source...",
                    key="event_search_input"
                )
                st.session_state.event_search = search_term


def update_event_stream():
    """Update the event stream with new events."""
    if st.session_state.get('stream_paused', False):
        return

    current_events = st.session_state.get('event_stream_data', [])

    # Add new simulated events
    new_events = generate_new_events(3)  # Generate 3 new events
    current_events.extend(new_events)

    # Keep only recent events (last 1000)
    if len(current_events) > 1000:
        current_events = current_events[-1000:]

    st.session_state.event_stream_data = current_events


def generate_new_events(count: int = 1) -> List[Dict[str, Any]]:
    """Generate new events for the stream."""
    import numpy as np

    events = []
    event_types = [
        'simulation_start', 'simulation_complete', 'error_occurred',
        'performance_warning', 'resource_allocated', 'user_action',
        'system_status', 'data_processed', 'alert_triggered'
    ]

    severities = ['info', 'low', 'medium', 'high', 'critical']
    sources = ['simulation_engine', 'monitoring_system', 'user_interface', 'database', 'api_gateway']

    messages = [
        "Simulation execution started",
        "Data processing completed successfully",
        "Performance threshold exceeded",
        "Resource allocation updated",
        "User authentication successful",
        "System health check passed",
        "Error detected in processing pipeline",
        "Configuration update applied",
        "Backup operation completed"
    ]

    for _ in range(count):
        event = {
            'id': f"evt_{int(time.time() * 1000000)}",
            'timestamp': datetime.now(),
            'event_type': np.random.choice(event_types),
            'severity': np.random.choice(severities, p=[0.4, 0.3, 0.2, 0.08, 0.02]),
            'source': np.random.choice(sources),
            'message': np.random.choice(messages),
            'details': {
                'user_id': np.random.randint(1000, 9999),
                'session_id': f"sess_{np.random.randint(100, 999)}",
                'request_id': f"req_{np.random.randint(10000, 99999)}"
            }
        }
        events.append(event)

    return events


def get_filtered_events() -> List[Dict[str, Any]]:
    """Get events filtered by current criteria."""
    all_events = st.session_state.get('event_stream_data', [])
    filters = st.session_state.get('event_filters', {})
    search_term = st.session_state.get('event_search', '')

    filtered_events = all_events.copy()

    # Apply time filter
    time_range = filters.get('time_range', '1h')
    if time_range != 'all':
        time_map = {'5m': 5, '15m': 15, '1h': 60, '6h': 360, '24h': 1440}
        minutes_back = time_map.get(time_range, 60)
        cutoff_time = datetime.now() - timedelta(minutes=minutes_back)
        filtered_events = [e for e in filtered_events if e['timestamp'] > cutoff_time]

    # Apply severity filter
    severity_filter = filters.get('severity', [])
    if severity_filter:
        filtered_events = [e for e in filtered_events if e['severity'] in severity_filter]

    # Apply event type filter
    event_type_filter = filters.get('event_type', [])
    if event_type_filter:
        filtered_events = [e for e in filtered_events if e['event_type'] in event_type_filter]

    # Apply search filter
    if search_term:
        search_lower = search_term.lower()
        filtered_events = [
            e for e in filtered_events
            if search_lower in e['message'].lower() or
               search_lower in e['source'].lower() or
               search_lower in e['event_type'].lower()
        ]

    return filtered_events


def display_event_stream(
    events: List[Dict[str, Any]],
    max_display: int,
    auto_scroll: bool,
    on_event_click: Optional[Callable]
):
    """Display the event stream."""
    if not events:
        st.info("No events to display. Events will appear here as they occur.")
        return

    # Display events in reverse chronological order (newest first)
    display_events = events[-max_display:] if len(events) > max_display else events
    display_events.reverse()

    st.markdown("#### 📋 Event Stream")

    # Create a scrollable container
    event_container = st.container()

    with event_container:
        for event in display_events:
            display_single_event(event, on_event_click)

    # Auto-scroll to bottom for new events
    if auto_scroll and display_events:
        # Use a small invisible element at the bottom to scroll to
        st.markdown('<div id="scroll-to-bottom"></div>', unsafe_allow_html=True)
        st.markdown("""
        <script>
            var element = document.getElementById('scroll-to-bottom');
            if (element) {
                element.scrollIntoView({behavior: 'smooth'});
            }
        </script>
        """, unsafe_allow_html=True)


def display_single_event(event: Dict[str, Any], on_event_click: Optional[Callable]):
    """Display a single event in the stream."""
    severity = event.get('severity', 'info')
    timestamp = event.get('timestamp', datetime.now())
    event_type = event.get('event_type', 'unknown')
    source = event.get('source', 'unknown')
    message = event.get('message', 'No message')

    # Severity-based styling
    if severity == 'critical':
        icon = "🚨"
        bg_color = "#ffcccc"
        border_color = "#cc0000"
    elif severity == 'high':
        icon = "🔴"
        bg_color = "#ffe6e6"
        border_color = "#ff4444"
    elif severity == 'medium':
        icon = "🟡"
        bg_color = "#fff9e6"
        border_color = "#ffaa00"
    elif severity == 'low':
        icon = "🟢"
        bg_color = "#e6ffe6"
        border_color = "#44aa44"
    else:  # info
        icon = "ℹ️"
        bg_color = "#e6f3ff"
        border_color = "#0066cc"

    # Create event display
    time_str = timestamp.strftime("%H:%M:%S")

    # Clickable event
    event_clicked = st.button(
        f"{icon} {time_str} | {event_type.upper()} | {source} | {message}",
        key=f"event_{event['id']}",
        help=f"Click to view event details | Severity: {severity}"
    )

    if event_clicked:
        display_event_details(event)
        if on_event_click:
            on_event_click(event)


def display_event_details(event: Dict[str, Any]):
    """Display detailed information for an event."""
    st.markdown("---")
    st.markdown("#### 🔍 Event Details")

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Event ID:** {event['id']}")
        st.write(f"**Timestamp:** {event['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        st.write(f"**Event Type:** {event['event_type']}")
        st.write(f"**Severity:** {event['severity'].title()}")

    with col2:
        st.write(f"**Source:** {event['source']}")
        st.write(f"**Message:** {event['message']}")

    # Additional details
    if 'details' in event and event['details']:
        st.markdown("**Additional Details:**")
        st.json(event['details'])


def display_stream_statistics(events: List[Dict[str, Any]]):
    """Display stream statistics."""
    if not events:
        return

    st.markdown("#### 📊 Stream Statistics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_events = len(st.session_state.get('event_stream_data', []))
        st.metric("Total Events", total_events)

    with col2:
        recent_count = len([e for e in events if e['timestamp'] > datetime.now() - timedelta(minutes=5)])
        st.metric("Last 5 min", recent_count)

    with col3:
        critical_count = len([e for e in events if e['severity'] == 'critical'])
        st.metric("Critical", critical_count)

    with col4:
        error_count = len([e for e in events if 'error' in e['event_type'].lower()])
        st.metric("Errors", error_count)

    # Event type breakdown
    if events:
        event_types = {}
        for event in events[-50:]:  # Last 50 events
            event_type = event.get('event_type', 'unknown')
            event_types[event_type] = event_types.get(event_type, 0) + 1

        st.markdown("**Recent Event Types:**")
        for event_type, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True):
            st.write(f"- {event_type}: {count}")


# WebSocket simulation for real-time event streaming
class EventStreamWebSocketSimulator:
    """Simulate WebSocket connections for real-time event streaming."""

    def __init__(self):
        self.connected = False
        self.event_queue = []

    def connect(self):
        """Simulate WebSocket connection."""
        self.connected = True

    def disconnect(self):
        """Disconnect WebSocket."""
        self.connected = False

    def send_event(self, event: Dict[str, Any]):
        """Add event to the stream."""
        self.event_queue.append(event)

    def get_events(self) -> List[Dict[str, Any]]:
        """Get pending events."""
        events = self.event_queue.copy()
        self.event_queue.clear()
        return events


# Global event stream simulator
event_stream_ws = EventStreamWebSocketSimulator()
