"""Real-time Event Timeline - Live Event Visualization Component.

This module provides a comprehensive real-time event timeline visualization
that displays simulation events as they occur, with filtering, search,
and interactive exploration capabilities.

Key Features:
- Real-time event streaming and display
- Interactive timeline with zoom and pan
- Event filtering by type, severity, and time range
- Event search and highlighting
- Event details drill-down
- Performance metrics and event statistics
- Export capabilities for event analysis
"""

import streamlit as st
from typing import Dict, Any, List, Optional, Callable, Tuple
import pandas as pd
from datetime import datetime, timedelta
import time
import asyncio
from dataclasses import dataclass, field
import plotly.graph_objects as go
import plotly.express as px
from collections import deque
import json
import re


@dataclass
class TimelineEvent:
    """Represents a single event in the timeline."""
    event_id: str
    timestamp: datetime
    event_type: str
    title: str
    description: str
    severity: str = "info"  # info, warning, error, critical
    source: str = "system"
    simulation_id: Optional[str] = None
    workflow_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    duration_ms: Optional[float] = None


@dataclass
class TimelineFilter:
    """Filter configuration for timeline events."""
    event_types: List[str] = field(default_factory=list)
    severities: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    simulation_ids: List[str] = field(default_factory=list)
    time_range_hours: int = 24
    search_query: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class TimelineConfig:
    """Configuration for the event timeline."""
    max_events: int = 1000
    update_interval_seconds: float = 2.0
    show_event_details: bool = True
    enable_search: bool = True
    enable_filters: bool = True
    enable_export: bool = True
    height_pixels: int = 500
    color_scheme: str = "default"


class RealTimeEventTimeline:
    """Real-time event timeline visualizer with interactive features."""

    def __init__(self, config: Optional[TimelineConfig] = None):
        """Initialize the event timeline."""
        self.config = config or TimelineConfig()
        self.events: deque[TimelineEvent] = deque(maxlen=self.config.max_events)
        self.filters = TimelineFilter()
        self.selected_event: Optional[TimelineEvent] = None
        self.last_update_time = datetime.now()

        # Event type color mapping
        self.event_colors = {
            'simulation_started': '#28a745',
            'simulation_completed': '#007bff',
            'simulation_failed': '#dc3545',
            'workflow_executed': '#17a2b8',
            'document_generated': '#ffc107',
            'phase_completed': '#6f42c1',
            'error_occurred': '#fd7e14',
            'performance_warning': '#e83e8c',
            'system_info': '#6c757d'
        }

    def add_event(self, event_data: Dict[str, Any]) -> None:
        """Add a new event to the timeline."""
        try:
            # Parse timestamp
            timestamp = event_data.get('timestamp')
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            elif not isinstance(timestamp, datetime):
                timestamp = datetime.now()

            # Create timeline event
            event = TimelineEvent(
                event_id=event_data.get('event_id', f"evt_{int(time.time())}_{len(self.events)}"),
                timestamp=timestamp,
                event_type=event_data.get('event_type', 'unknown'),
                title=event_data.get('title', event_data.get('event_type', 'Unknown Event')),
                description=event_data.get('description', event_data.get('message', '')),
                severity=event_data.get('severity', 'info'),
                source=event_data.get('source', 'system'),
                simulation_id=event_data.get('simulation_id'),
                workflow_id=event_data.get('workflow_id'),
                data=event_data.get('data', {}),
                tags=event_data.get('tags', []),
                duration_ms=event_data.get('duration_ms')
            )

            self.events.append(event)
            self.last_update_time = datetime.now()

        except Exception as e:
            print(f"Error adding event to timeline: {e}")

    def render_timeline(self,
                       title: str = "📅 Real-Time Event Timeline",
                       height: Optional[int] = None) -> None:
        """Render the main event timeline component."""
        st.markdown(f"### {title}")
        st.markdown("*Live event streaming with interactive timeline visualization*")

        height = height or self.config.height_pixels

        # Filters and controls
        if self.config.enable_filters:
            self._render_timeline_filters()

        # Main timeline visualization
        self._render_timeline_visualization(height)

        # Event details panel
        if self.config.show_event_details and self.selected_event:
            self._render_event_details_panel()

        # Statistics and summary
        self._render_timeline_statistics()

        # Export options
        if self.config.enable_export:
            self._render_export_options()

    def _render_timeline_filters(self) -> None:
        """Render timeline filtering controls."""
        with st.expander("🔍 Filters & Search", expanded=False):
            col1, col2, col3 = st.columns(3)

            with col1:
                # Event type filter
                available_types = list(set(event.event_type for event in self.events))
                if available_types:
                    self.filters.event_types = st.multiselect(
                        "Event Types",
                        options=sorted(available_types),
                        default=self.filters.event_types,
                        key="timeline_event_types"
                    )

            with col2:
                # Severity filter
                available_severities = list(set(event.severity for event in self.events))
                if available_severities:
                    self.filters.severities = st.multiselect(
                        "Severity",
                        options=sorted(available_severities),
                        default=self.filters.severities,
                        key="timeline_severity"
                    )

            with col3:
                # Time range
                self.filters.time_range_hours = st.selectbox(
                    "Time Range",
                    options=[1, 6, 12, 24, 48, 72],
                    index=3,  # Default to 24 hours
                    format_func=lambda x: f"{x} hours",
                    key="timeline_time_range"
                )

            # Search query
            if self.config.enable_search:
                self.filters.search_query = st.text_input(
                    "Search Events",
                    value=self.filters.search_query,
                    placeholder="Search in event titles and descriptions...",
                    key="timeline_search"
                )

            # Clear filters button
            if st.button("Clear All Filters", key="clear_timeline_filters"):
                self.filters = TimelineFilter()
                st.rerun()

    def _render_timeline_visualization(self, height: int) -> None:
        """Render the main timeline visualization."""
        # Get filtered events
        filtered_events = self._get_filtered_events()

        if not filtered_events:
            st.info("No events match the current filters")
            return

        # Convert to DataFrame for visualization
        events_df = pd.DataFrame([
            {
                'timestamp': event.timestamp,
                'event_type': event.event_type,
                'title': event.title,
                'severity': event.severity,
                'source': event.source,
                'simulation_id': event.simulation_id,
                'event_id': event.event_id
            }
            for event in filtered_events
        ])

        # Create timeline scatter plot
        fig = go.Figure()

        # Group events by type for better visualization
        for event_type in events_df['event_type'].unique():
            type_events = events_df[events_df['event_type'] == event_type]

            # Create y-position based on event type (for separation)
            y_position = hash(event_type) % 10  # Simple hash for y-position

            fig.add_trace(go.Scatter(
                x=type_events['timestamp'],
                y=[y_position] * len(type_events),
                mode='markers+text',
                name=event_type.replace('_', ' ').title(),
                text=type_events['title'],
                textposition="top center",
                marker=dict(
                    size=self._get_marker_size(type_events['severity']),
                    color=self._get_event_color(event_type),
                    symbol='circle'
                ),
                hovertemplate=
                '<b>%{text}</b><br>' +
                'Time: %{x}<br>' +
                'Type: ' + event_type + '<br>' +
                'Severity: %{customdata}<br>' +
                '<extra></extra>',
                customdata=type_events['severity']
            ))

        # Update layout
        fig.update_layout(
            title="Event Timeline",
            xaxis_title="Time",
            yaxis_title="",
            yaxis=dict(showticklabels=False),  # Hide y-axis labels
            height=height,
            showlegend=True,
            hovermode='closest'
        )

        # Add click handler for event selection
        fig.update_traces(marker=dict(size=12))

        # Render the plot
        st.plotly_chart(fig, use_container_width=True, key="event_timeline_plot")

        # Event list below the timeline
        self._render_event_list(filtered_events)

    def _render_event_list(self, events: List[TimelineEvent]) -> None:
        """Render a list of events below the timeline."""
        st.markdown("#### 📋 Recent Events")

        # Display events in reverse chronological order (newest first)
        for event in events[-20:]:  # Show last 20 events
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 3, 1, 1])

                with col1:
                    # Event icon and title
                    icon = self._get_event_icon(event.event_type)
                    st.markdown(f"{icon} **{event.title}**")

                with col2:
                    # Description and metadata
                    st.markdown(f"*{event.description[:100]}...*" if len(event.description) > 100 else f"*{event.description}*")
                    if event.simulation_id:
                        st.caption(f"Sim: {event.simulation_id[:8]}")

                with col3:
                    # Timestamp
                    st.caption(event.timestamp.strftime("%H:%M:%S"))

                with col4:
                    # Severity badge
                    severity_color = self._get_severity_color(event.severity)
                    st.markdown(f"<span style='color:{severity_color}'>●</span> {event.severity.title()}",
                               unsafe_allow_html=True)

                # Click to select event
                if st.button(f"View Details #{event.event_id[:8]}",
                           key=f"select_event_{event.event_id}",
                           help="Click to view detailed event information"):
                    self.selected_event = event
                    st.rerun()

                st.markdown("---")

    def _render_event_details_panel(self) -> None:
        """Render detailed information for the selected event."""
        if not self.selected_event:
            return

        st.markdown("#### 📋 Event Details")

        with st.expander(f"Event: {self.selected_event.title}", expanded=True):
            # Basic information
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Event ID:** {self.selected_event.event_id}")
                st.markdown(f"**Type:** {self.selected_event.event_type}")
                st.markdown(f"**Source:** {self.selected_event.source}")

            with col2:
                st.markdown(f"**Timestamp:** {self.selected_event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                st.markdown(f"**Severity:** {self.selected_event.severity.title()}")
                if self.selected_event.duration_ms:
                    st.markdown(f"**Duration:** {self.selected_event.duration_ms:.2f}ms")

            # Simulation and workflow context
            if self.selected_event.simulation_id or self.selected_event.workflow_id:
                st.markdown("**Context:**")
                if self.selected_event.simulation_id:
                    st.markdown(f"- Simulation: `{self.selected_event.simulation_id}`")
                if self.selected_event.workflow_id:
                    st.markdown(f"- Workflow: `{self.selected_event.workflow_id}`")

            # Event description
            st.markdown(f"**Description:** {self.selected_event.description}")

            # Event data (if available)
            if self.selected_event.data:
                st.markdown("**Event Data:**")
                st.json(self.selected_event.data)

            # Tags
            if self.selected_event.tags:
                st.markdown(f"**Tags:** {', '.join(self.selected_event.tags)}")

    def _render_timeline_statistics(self) -> None:
        """Render timeline statistics and summary."""
        st.markdown("#### 📊 Timeline Statistics")

        if not self.events:
            st.info("No events to analyze")
            return

        # Calculate statistics
        total_events = len(self.events)
        time_range = datetime.now() - self.events[0].timestamp if self.events else timedelta(0)

        # Event type distribution
        event_types = {}
        severities = {}
        sources = {}

        for event in self.events:
            event_types[event.event_type] = event_types.get(event.event_type, 0) + 1
            severities[event.severity] = severities.get(event.severity, 0) + 1
            sources[event.source] = sources.get(event.source, 0) + 1

        # Display metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Events", total_events)

        with col2:
            events_per_hour = total_events / max(1, time_range.total_seconds() / 3600)
            st.metric("Events/Hour", ".1f")

        with col3:
            error_count = severities.get('error', 0) + severities.get('critical', 0)
            st.metric("Errors", error_count)

        with col4:
            unique_types = len(event_types)
            st.metric("Event Types", unique_types)

        # Event type breakdown
        if len(event_types) > 1:
            with st.expander("Event Type Distribution", expanded=False):
                type_df = pd.DataFrame(
                    list(event_types.items()),
                    columns=['Event Type', 'Count']
                ).sort_values('Count', ascending=False)

                fig = px.pie(
                    type_df,
                    values='Count',
                    names='Event Type',
                    title="Event Types Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)

    def _render_export_options(self) -> None:
        """Render export options for timeline data."""
        with st.expander("💾 Export Options", expanded=False):
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("📄 Export as JSON", key="export_timeline_json"):
                    export_data = self.export_timeline_data('json')
                    st.download_button(
                        label="Download JSON",
                        data=export_data,
                        file_name=f"timeline_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        key="download_timeline_json"
                    )

            with col2:
                if st.button("📊 Export as CSV", key="export_timeline_csv"):
                    export_data = self.export_timeline_data('csv')
                    st.download_button(
                        label="Download CSV",
                        data=export_data,
                        file_name=f"timeline_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        key="download_timeline_csv"
                    )

            with col3:
                if st.button("🗂️ Export Summary", key="export_timeline_summary"):
                    summary_data = self.export_timeline_summary()
                    st.download_button(
                        label="Download Summary",
                        data=summary_data,
                        file_name=f"timeline_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        key="download_timeline_summary"
                    )

    def _get_filtered_events(self) -> List[TimelineEvent]:
        """Get events filtered according to current filter settings."""
        filtered_events = list(self.events)

        # Time range filter
        if self.filters.time_range_hours > 0:
            cutoff_time = datetime.now() - timedelta(hours=self.filters.time_range_hours)
            filtered_events = [e for e in filtered_events if e.timestamp >= cutoff_time]

        # Event type filter
        if self.filters.event_types:
            filtered_events = [e for e in filtered_events if e.event_type in self.filters.event_types]

        # Severity filter
        if self.filters.severities:
            filtered_events = [e for e in filtered_events if e.severity in self.filters.severities]

        # Source filter
        if self.filters.sources:
            filtered_events = [e for e in filtered_events if e.source in self.filters.sources]

        # Simulation ID filter
        if self.filters.simulation_ids:
            filtered_events = [e for e in filtered_events if e.simulation_id in self.filters.simulation_ids]

        # Search query filter
        if self.filters.search_query:
            query = self.filters.search_query.lower()
            filtered_events = [
                e for e in filtered_events
                if query in e.title.lower() or
                   query in e.description.lower() or
                   any(query in tag.lower() for tag in e.tags)
            ]

        return filtered_events

    def _get_event_color(self, event_type: str) -> str:
        """Get color for event type."""
        return self.event_colors.get(event_type, '#6c757d')

    def _get_marker_size(self, severity: pd.Series) -> List[int]:
        """Get marker size based on severity."""
        size_map = {'info': 8, 'warning': 10, 'error': 12, 'critical': 14}
        return [size_map.get(s, 8) for s in severity]

    def _get_event_icon(self, event_type: str) -> str:
        """Get icon for event type."""
        icons = {
            'simulation_started': '🚀',
            'simulation_completed': '✅',
            'simulation_failed': '❌',
            'workflow_executed': '⚙️',
            'document_generated': '📄',
            'phase_completed': '🎯',
            'error_occurred': '🔥',
            'performance_warning': '⚠️',
            'system_info': 'ℹ️'
        }
        return icons.get(event_type, '📌')

    def _get_severity_color(self, severity: str) -> str:
        """Get color for severity level."""
        colors = {
            'info': '#17a2b8',
            'warning': '#ffc107',
            'error': '#fd7e14',
            'critical': '#dc3545'
        }
        return colors.get(severity.lower(), '#6c757d')

    def export_timeline_data(self, format: str = 'json') -> str:
        """Export timeline data in specified format."""
        events_data = [
            {
                'event_id': event.event_id,
                'timestamp': event.timestamp.isoformat(),
                'event_type': event.event_type,
                'title': event.title,
                'description': event.description,
                'severity': event.severity,
                'source': event.source,
                'simulation_id': event.simulation_id,
                'workflow_id': event.workflow_id,
                'data': event.data,
                'tags': event.tags,
                'duration_ms': event.duration_ms
            }
            for event in self.events
        ]

        if format == 'json':
            return json.dumps({
                'export_timestamp': datetime.now().isoformat(),
                'total_events': len(events_data),
                'events': events_data
            }, indent=2)

        elif format == 'csv':
            if events_data:
                df = pd.DataFrame(events_data)
                return df.to_csv(index=False)
            return ""

        return ""

    def export_timeline_summary(self) -> str:
        """Export timeline summary statistics."""
        if not self.events:
            return json.dumps({'message': 'No events to summarize'})

        # Calculate summary statistics
        summary = {
            'export_timestamp': datetime.now().isoformat(),
            'total_events': len(self.events),
            'time_range': {
                'start': self.events[0].timestamp.isoformat(),
                'end': self.events[-1].timestamp.isoformat()
            },
            'event_types': {},
            'severities': {},
            'sources': {},
            'hourly_distribution': {}
        }

        for event in self.events:
            # Count by type
            summary['event_types'][event.event_type] = summary['event_types'].get(event.event_type, 0) + 1
            summary['severities'][event.severity] = summary['severities'].get(event.severity, 0) + 1
            summary['sources'][event.source] = summary['sources'].get(event.source, 0) + 1

            # Hourly distribution
            hour = event.timestamp.strftime('%Y-%m-%d %H:00')
            summary['hourly_distribution'][hour] = summary['hourly_distribution'].get(hour, 0) + 1

        return json.dumps(summary, indent=2)

    def clear_events(self) -> None:
        """Clear all events from the timeline."""
        self.events.clear()
        self.selected_event = None

    def search_events(self, query: str) -> List[TimelineEvent]:
        """Search events by query string."""
        if not query:
            return list(self.events)

        query_lower = query.lower()
        return [
            event for event in self.events
            if (query_lower in event.title.lower() or
                query_lower in event.description.lower() or
                any(query_lower in tag.lower() for tag in event.tags) or
                query_lower in event.event_type.lower())
        ]

    def get_event_statistics(self) -> Dict[str, Any]:
        """Get comprehensive event statistics."""
        if not self.events:
            return {'total_events': 0}

        stats = {
            'total_events': len(self.events),
            'time_span_hours': (self.events[-1].timestamp - self.events[0].timestamp).total_seconds() / 3600,
            'events_per_hour': len(self.events) / max(1, (self.events[-1].timestamp - self.events[0].timestamp).total_seconds() / 3600),
            'event_types_count': len(set(e.event_type for e in self.events)),
            'severities_count': len(set(e.severity for e in self.events)),
            'sources_count': len(set(e.source for e in self.events))
        }

        # Most common event types
        event_types = {}
        for event in self.events:
            event_types[event.event_type] = event_types.get(event.event_type, 0) + 1

        stats['most_common_event_types'] = sorted(
            event_types.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return stats


# Convenience functions for easy integration
def create_event_timeline(config: Optional[TimelineConfig] = None) -> RealTimeEventTimeline:
    """Create a new event timeline instance."""
    return RealTimeEventTimeline(config)


def render_realtime_event_timeline(simulation_id: Optional[str] = None,
                                  title: str = "📅 Real-Time Event Timeline") -> None:
    """Render a real-time event timeline component."""
    timeline = RealTimeEventTimeline()
    timeline.render_timeline(title=title)


def add_sample_events_to_timeline(timeline: RealTimeEventTimeline, count: int = 20) -> None:
    """Add sample events to timeline for demonstration."""
    base_time = datetime.now() - timedelta(minutes=30)

    event_types = [
        'simulation_started', 'workflow_executed', 'document_generated',
        'phase_completed', 'error_occurred', 'performance_warning'
    ]

    severities = ['info', 'warning', 'error', 'critical']
    sources = ['simulation_engine', 'workflow_orchestrator', 'document_service', 'monitoring']

    for i in range(count):
        event_data = {
            'event_id': f'sample_event_{i}',
            'timestamp': base_time + timedelta(minutes=i*2),
            'event_type': event_types[i % len(event_types)],
            'title': f'Sample Event {i+1}',
            'description': f'This is a sample event number {i+1} for demonstration purposes.',
            'severity': severities[i % len(severities)],
            'source': sources[i % len(sources)],
            'simulation_id': f'sim_{i % 3 + 1}',
            'data': {'sample_data': f'value_{i}'},
            'tags': ['sample', f'type_{i % 3}']
        }
        timeline.add_event(event_data)

