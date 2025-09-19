"""Events Timeline Page.

This module provides the event timeline and replay visualization interface,
allowing users to explore simulation events chronologically and replay event sequences.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json

from services.clients.simulation_client import SimulationClient
from infrastructure.config.config import get_config


def render_events_page():
    """Render the events timeline and replay page."""
    st.markdown("## 📅 Event Timeline & Replay")
    st.markdown("Explore simulation events chronologically and replay event sequences for analysis.")

    # Initialize session state
    initialize_events_state()

    # Create tabs for different event views
    tab1, tab2, tab3 = st.tabs([
        "📊 Event Timeline",
        "🎬 Event Replay",
        "📈 Event Analytics"
    ])

    with tab1:
        render_event_timeline()

    with tab2:
        render_event_replay()

    with tab3:
        render_event_analytics()


def initialize_events_state():
    """Initialize session state for events page."""
    if 'selected_simulation_events' not in st.session_state:
        st.session_state.selected_simulation_events = None

    if 'event_filters' not in st.session_state:
        st.session_state.event_filters = {
            'event_types': [],
            'start_date': None,
            'end_date': None,
            'tags': []
        }

    if 'replay_config' not in st.session_state:
        st.session_state.replay_config = {
            'speed_multiplier': 1.0,
            'include_system_events': False,
            'max_events': 100,
            'is_replaying': False
        }


def render_event_timeline():
    """Render the interactive event timeline visualization."""
    st.markdown("### 📊 Event Timeline")

    # Simulation selection
    col1, col2 = st.columns([2, 1])

    with col1:
        simulations = get_available_simulations()

        if simulations:
            simulation_options = ["Select a simulation..."] + [
                f"{sim.get('id', 'Unknown')} - {sim.get('name', 'Unnamed')}"
                for sim in simulations
            ]

            selected_sim_option = st.selectbox(
                "Select Simulation for Timeline",
                options=simulation_options,
                key="timeline_simulation_selector"
            )

            if selected_sim_option and selected_sim_option != "Select a simulation...":
                sim_id = selected_sim_option.split(" - ")[0]
                st.session_state.selected_simulation_events = sim_id
        else:
            st.warning("No simulations available for timeline view.")
            return

    with col2:
        if st.button("🔄 Refresh Events", key="refresh_events"):
            load_simulation_events()

    # Load events if simulation selected
    if st.session_state.selected_simulation_events:
        events = load_simulation_events()

        if not events:
            st.info("No events found for this simulation.")
            return

        # Filters
        st.markdown("---")
        render_event_filters(events)

        # Filtered events
        filtered_events = apply_event_filters(events)

        # Timeline visualization
        if filtered_events:
            render_timeline_visualization(filtered_events)
        else:
            st.info("No events match the current filters.")

        # Event details table
        st.markdown("---")
        render_event_details_table(filtered_events)


def render_event_replay():
    """Render the event replay interface."""
    st.markdown("### 🎬 Event Replay")

    if not st.session_state.selected_simulation_events:
        st.info("Please select a simulation from the Timeline tab first.")
        return

    # Replay controls
    st.markdown("#### 🎛️ Replay Controls")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        speed_multiplier = st.slider(
            "Playback Speed",
            min_value=0.1,
            max_value=5.0,
            value=st.session_state.replay_config['speed_multiplier'],
            step=0.1,
            help="Speed multiplier for event replay"
        )
        st.session_state.replay_config['speed_multiplier'] = speed_multiplier

    with col2:
        include_system = st.checkbox(
            "Include System Events",
            value=st.session_state.replay_config['include_system_events'],
            help="Include system-level events in replay"
        )
        st.session_state.replay_config['include_system_events'] = include_system

    with col3:
        max_events = st.slider(
            "Max Events",
            min_value=10,
            max_value=500,
            value=st.session_state.replay_config['max_events'],
            step=10,
            help="Maximum number of events to replay"
        )
        st.session_state.replay_config['max_events'] = max_events

    with col4:
        if st.button("▶️ Start Replay", type="primary", key="start_replay"):
            start_event_replay()

        if st.button("⏹️ Stop Replay", key="stop_replay"):
            stop_event_replay()

    # Replay status
    if st.session_state.replay_config['is_replaying']:
        st.success("🎬 Replay in progress...")
        render_replay_progress()
    else:
        st.info("Ready to start replay. Configure settings above and click Start Replay.")

    # Replay visualization area
    st.markdown("---")
    st.markdown("#### 📺 Replay Visualization")

    replay_placeholder = st.empty()

    # Event sequence display
    if st.session_state.replay_config['is_replaying']:
        display_replay_sequence(replay_placeholder)


def render_event_analytics():
    """Render event analytics and insights."""
    st.markdown("### 📈 Event Analytics")

    if not st.session_state.selected_simulation_events:
        st.info("Please select a simulation from the Timeline tab first.")
        return

    events = load_simulation_events()

    if not events:
        st.info("No events available for analytics.")
        return

    # Event type distribution
    render_event_type_distribution(events)

    # Event frequency over time
    render_event_frequency_chart(events)

    # Event correlation analysis
    render_event_correlations(events)

    # Event insights and recommendations
    render_event_insights(events)


def render_event_filters(events: List[Dict[str, Any]]):
    """Render event filtering controls."""
    st.markdown("#### 🔍 Event Filters")

    col1, col2, col3 = st.columns(3)

    # Event type filter
    with col1:
        available_event_types = list(set(event.get('event_type', 'Unknown') for event in events))
        selected_event_types = st.multiselect(
            "Event Types",
            options=available_event_types,
            default=st.session_state.event_filters['event_types'] or available_event_types[:5],
            help="Filter events by type"
        )
        st.session_state.event_filters['event_types'] = selected_event_types

    # Time range filter
    with col2:
        # Get date range from events
        if events:
            timestamps = [event.get('timestamp', '') for event in events if event.get('timestamp')]
            if timestamps:
                dates = [datetime.fromisoformat(ts.replace('Z', '+00:00')) for ts in timestamps if ts]
                if dates:
                    min_date = min(dates).date()
                    max_date = max(dates).date()

                    date_range = st.date_input(
                        "Date Range",
                        value=(min_date, max_date),
                        min_value=min_date,
                        max_value=max_date,
                        help="Filter events by date range"
                    )

                    if len(date_range) == 2:
                        st.session_state.event_filters['start_date'] = date_range[0]
                        st.session_state.event_filters['end_date'] = date_range[1]

    # Tags filter
    with col3:
        available_tags = []
        for event in events:
            available_tags.extend(event.get('tags', []))
        available_tags = list(set(available_tags))

        if available_tags:
            selected_tags = st.multiselect(
                "Tags",
                options=available_tags,
                default=st.session_state.event_filters['tags'],
                help="Filter events by tags"
            )
            st.session_state.event_filters['tags'] = selected_tags


def apply_event_filters(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply current filters to events list."""
    filtered_events = events

    # Event type filter
    if st.session_state.event_filters['event_types']:
        filtered_events = [
            event for event in filtered_events
            if event.get('event_type') in st.session_state.event_filters['event_types']
        ]

    # Date range filter
    if st.session_state.event_filters['start_date'] and st.session_state.event_filters['end_date']:
        start_date = st.session_state.event_filters['start_date']
        end_date = st.session_state.event_filters['end_date']

        filtered_events = [
            event for event in filtered_events
            if event.get('timestamp') and
               start_date <= datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00')).date() <= end_date
        ]

    # Tags filter
    if st.session_state.event_filters['tags']:
        filtered_events = [
            event for event in filtered_events
            if any(tag in event.get('tags', []) for tag in st.session_state.event_filters['tags'])
        ]

    return filtered_events


def render_timeline_visualization(events: List[Dict[str, Any]]):
    """Render the interactive timeline visualization."""
    st.markdown("#### 📈 Timeline Visualization")

    if not events:
        st.info("No events to visualize.")
        return

    # Prepare data for timeline
    timeline_data = []
    for event in events:
        timestamp = event.get('timestamp', '')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                timeline_data.append({
                    'timestamp': dt,
                    'event_type': event.get('event_type', 'Unknown'),
                    'description': get_event_description(event),
                    'simulation_id': event.get('simulation_id', 'Unknown'),
                    'correlation_id': event.get('correlation_id', 'Unknown')
                })
            except:
                continue

    if timeline_data:
        df = pd.DataFrame(timeline_data)

        # Create timeline scatter plot
        fig = px.scatter(
            df,
            x='timestamp',
            y='event_type',
            color='event_type',
            title='Event Timeline',
            hover_data=['description', 'simulation_id', 'correlation_id']
        )

        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Event Type",
            height=500
        )

        fig.update_xaxes(tickformat="%H:%M:%S")
        fig.update_traces(marker=dict(size=8))

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Unable to create timeline visualization from event data.")


def render_event_details_table(events: List[Dict[str, Any]]):
    """Render detailed event information table."""
    st.markdown("#### 📋 Event Details")

    if not events:
        st.info("No events to display.")
        return

    # Prepare data for table
    table_data = []
    for event in events:
        timestamp = event.get('timestamp', '')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                formatted_time = timestamp
        else:
            formatted_time = "Unknown"

        table_data.append({
            'Time': formatted_time,
            'Event Type': event.get('event_type', 'Unknown'),
            'Description': get_event_description(event),
            'Simulation': event.get('simulation_id', 'Unknown'),
            'Correlation ID': event.get('correlation_id', 'Unknown')[:8] + "..."
        })

    if table_data:
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)

        # Export option
        if st.button("📥 Export Events to CSV"):
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"simulation_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="export_events_csv"
            )


def render_event_type_distribution(events: List[Dict[str, Any]]):
    """Render event type distribution chart."""
    st.markdown("#### 📊 Event Type Distribution")

    # Count events by type
    event_counts = {}
    for event in events:
        event_type = event.get('event_type', 'Unknown')
        event_counts[event_type] = event_counts.get(event_type, 0) + 1

    if event_counts:
        # Create pie chart
        labels = list(event_counts.keys())
        values = list(event_counts.values())

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            title="Event Types Distribution",
            marker_colors=px.colors.qualitative.Set3
        )])

        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

        # Summary table
        summary_data = {
            'Event Type': labels,
            'Count': values,
            'Percentage': [".1f" for v in values]
        }

        st.table(pd.DataFrame(summary_data))


def render_event_frequency_chart(events: List[Dict[str, Any]]):
    """Render event frequency over time chart."""
    st.markdown("#### 📈 Event Frequency Over Time")

    if not events:
        st.info("No events to analyze.")
        return

    # Group events by time intervals
    time_intervals = {}
    for event in events:
        timestamp = event.get('timestamp', '')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                # Group by minute intervals
                interval = dt.replace(second=0, microsecond=0)
                time_intervals[interval] = time_intervals.get(interval, 0) + 1
            except:
                continue

    if time_intervals:
        # Create line chart
        sorted_intervals = sorted(time_intervals.items())
        times = [interval.strftime("%H:%M") for interval, _ in sorted_intervals]
        counts = [count for _, count in sorted_intervals]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=times,
            y=counts,
            mode='lines+markers',
            name='Event Frequency',
            line=dict(color='blue', width=2),
            marker=dict(size=6)
        ))

        fig.update_layout(
            title="Event Frequency Over Time",
            xaxis_title="Time",
            yaxis_title="Number of Events",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)


def render_event_correlations(events: List[Dict[str, Any]]):
    """Render event correlation analysis."""
    st.markdown("#### 🔗 Event Correlations")

    if len(events) < 2:
        st.info("Need at least 2 events for correlation analysis.")
        return

    # Analyze event sequences
    event_sequence = [event.get('event_type', 'Unknown') for event in events]

    # Find common patterns
    patterns = {}
    for i in range(len(event_sequence) - 1):
        pattern = f"{event_sequence[i]} → {event_sequence[i + 1]}"
        patterns[pattern] = patterns.get(pattern, 0) + 1

    # Display top patterns
    if patterns:
        sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)
        top_patterns = sorted_patterns[:10]

        st.markdown("**Top Event Transitions:**")
        for pattern, count in top_patterns:
            st.write(f"• {pattern}: {count} times")


def render_event_insights(events: List[Dict[str, Any]]):
    """Render event insights and recommendations."""
    st.markdown("#### 💡 Event Insights & Recommendations")

    insights = generate_event_insights(events)

    for insight in insights:
        if insight['type'] == 'success':
            st.success(f"✅ {insight['message']}")
        elif insight['type'] == 'warning':
            st.warning(f"⚠️ {insight['message']}")
        elif insight['type'] == 'info':
            st.info(f"ℹ️ {insight['message']}")


def load_simulation_events() -> List[Dict[str, Any]]:
    """Load events for the selected simulation."""
    if not st.session_state.selected_simulation_events:
        return []

    # Mock event data - in real implementation, this would call the simulation service
    mock_events = generate_mock_events(st.session_state.selected_simulation_events)

    # Store in session state
    st.session_state.simulation_events = mock_events

    return mock_events


def generate_mock_events(simulation_id: str) -> List[Dict[str, Any]]:
    """Generate mock events for demonstration."""
    base_time = datetime.now() - timedelta(hours=2)

    event_types = [
        "SimulationStarted", "ProjectCreated", "DocumentGenerated", "WorkflowExecuted",
        "PhaseStarted", "MilestoneAchieved", "DocumentGenerated", "WorkflowExecuted",
        "PhaseCompleted", "SimulationCompleted"
    ]

    events = []
    for i, event_type in enumerate(event_types):
        event_time = base_time + timedelta(minutes=i * 5)

        events.append({
            'event_id': f"evt_{i+1}_{simulation_id}",
            'event_type': event_type,
            'timestamp': event_time.isoformat(),
            'simulation_id': simulation_id,
            'correlation_id': f"corr_{i+1}",
            'tags': ['simulation', 'development'],
            'data': {
                'description': get_event_description({'event_type': event_type}),
                'sequence_number': i + 1
            }
        })

    return events


def get_event_description(event: Dict[str, Any]) -> str:
    """Get human-readable description for an event."""
    event_type = event.get('event_type', 'Unknown')

    descriptions = {
        "SimulationStarted": "Simulation execution began",
        "SimulationCompleted": "Simulation finished successfully",
        "SimulationFailed": "Simulation encountered an error",
        "ProjectCreated": "New project was created",
        "ProjectStatusChanged": "Project status was updated",
        "DocumentGenerated": "New document was generated",
        "WorkflowExecuted": "Workflow completed execution",
        "PhaseStarted": "Project phase began",
        "PhaseCompleted": "Project phase finished",
        "MilestoneAchieved": "Project milestone was reached",
        "TeamMemberAdded": "Team member was added to project",
        "DocumentAnalysisCompleted": "Document analysis finished"
    }

    return descriptions.get(event_type, f"Event: {event_type}")


def start_event_replay():
    """Start event replay sequence."""
    st.session_state.replay_config['is_replaying'] = True
    st.session_state.replay_config['replay_start_time'] = datetime.now()
    st.rerun()


def stop_event_replay():
    """Stop event replay sequence."""
    st.session_state.replay_config['is_replaying'] = False
    st.rerun()


def render_replay_progress():
    """Render replay progress indicator."""
    start_time = st.session_state.replay_config.get('replay_start_time')
    if start_time:
        elapsed = (datetime.now() - start_time).total_seconds()
        progress = min(elapsed / 30, 1.0)  # Assume 30 second replay
        st.progress(progress, text=".1f")


def display_replay_sequence(placeholder):
    """Display event replay sequence."""
    events = load_simulation_events()
    config = st.session_state.replay_config

    if not events:
        placeholder.info("No events to replay.")
        return

    max_events = min(len(events), config['max_events'])
    speed_multiplier = config['speed_multiplier']

    for i in range(max_events):
        if not st.session_state.replay_config['is_replaying']:
            break

        event = events[i]

        # Display current event
        placeholder.markdown(f"""
        ### 🎬 Replaying Event {i + 1}/{max_events}
        **{event['event_type']}** - {get_event_description(event)}

        *Time: {event['timestamp']}*
        """)

        # Wait based on speed multiplier
        import time
        time.sleep(1.0 / speed_multiplier)

        # Update placeholder
        placeholder.empty()

    # Replay finished
    if st.session_state.replay_config['is_replaying']:
        st.session_state.replay_config['is_replaying'] = False
        placeholder.success("🎬 Event replay completed!")
        st.rerun()


def generate_event_insights(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate insights from event analysis."""
    insights = []

    if not events:
        return insights

    # Analyze event patterns
    event_types = [e.get('event_type', 'Unknown') for e in events]
    total_events = len(events)

    # Success pattern analysis
    if "SimulationCompleted" in event_types:
        insights.append({
            'type': 'success',
            'message': 'Simulation completed successfully with comprehensive event tracking'
        })

    # Frequency analysis
    document_events = sum(1 for e in event_types if 'Document' in e)
    if document_events > total_events * 0.3:
        insights.append({
            'type': 'info',
            'message': 'High document generation activity indicates productive simulation'
        })

    # Error analysis
    error_events = sum(1 for e in event_types if 'Failed' in e)
    if error_events > 0:
        insights.append({
            'type': 'warning',
            'message': f'Detected {error_events} error events - review simulation configuration'
        })

    # Timeline analysis
    if len(events) > 1:
        timestamps = []
        for event in events:
            ts = event.get('timestamp', '')
            if ts:
                try:
                    timestamps.append(datetime.fromisoformat(ts.replace('Z', '+00:00')))
                except:
                    continue

        if len(timestamps) > 1:
            duration = (max(timestamps) - min(timestamps)).total_seconds()
            insights.append({
                'type': 'info',
                'message': '.1f'
            })

    return insights


def get_available_simulations() -> List[Dict[str, Any]]:
    """Get list of available simulations."""
    # Mock data - in real implementation, this would call the simulation service
    return [
        {
            'id': 'sim_001',
            'name': 'E-commerce Platform Development',
            'status': 'completed'
        },
        {
            'id': 'sim_002',
            'name': 'Mobile App Development',
            'status': 'running'
        },
        {
            'id': 'sim_003',
            'name': 'API Service Implementation',
            'status': 'completed'
        }
    ]
