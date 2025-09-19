"""Timeline Charts Components.

This module provides chart components for displaying project timelines,
Gantt charts, and scheduling visualizations.
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

try:
    import plotly.express as px
    import plotly.figure_factory as ff
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    st.warning("⚠️ Plotly not available. Timeline chart components will be limited.")


def render_timeline_chart(
    phases: List[Dict[str, Any]],
    title: str = "Project Timeline",
    width: Optional[int] = None,
    height: Optional[int] = 500
) -> None:
    """Render project timeline chart.

    Args:
        phases: List of project phases with timing information
        title: Chart title
        width: Chart width
        height: Chart height
    """
    if not PLOTLY_AVAILABLE:
        st.error("❌ Plotly is required for timeline components")
        return

    try:
        st.markdown(f"### {title}")

        if not phases:
            st.info("No timeline data available")
            return

        # Prepare data for Gantt chart
        df = []

        for phase in phases:
            start_date = datetime.now()  # Default to now, should be calculated from project start
            duration_days = phase.get('duration_days', 7)

            # Calculate start and end dates based on dependencies and durations
            start_date = calculate_phase_start_date(phase, phases, start_date)
            end_date = start_date + timedelta(days=duration_days)

            df.append({
                'Task': phase.get('name', 'Unnamed Phase'),
                'Start': start_date,
                'Finish': end_date,
                'Resource': phase.get('status', 'Planned'),
                'Description': phase.get('description', ''),
                'Duration': duration_days
            })

        if not df:
            st.info("No valid timeline data to display")
            return

        # Create Gantt chart
        fig = ff.create_gantt(
            df,
            colors=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
            index_col='Resource',
            show_colorbar=True,
            group_tasks=True
        )

        fig.update_layout(
            title=title,
            width=width,
            height=height,
            xaxis_title="Timeline",
            yaxis_title="Project Phases"
        )

        st.plotly_chart(fig, use_container_width=True)

        # Display timeline summary
        render_timeline_summary(phases)

    except Exception as e:
        st.error(f"❌ Error rendering timeline chart: {str(e)}")


def render_milestone_chart(
    milestones: List[Dict[str, Any]],
    title: str = "Project Milestones",
    width: Optional[int] = None,
    height: Optional[int] = 400
) -> None:
    """Render project milestones chart.

    Args:
        milestones: List of project milestones
        title: Chart title
        width: Chart width
        height: Chart height
    """
    if not PLOTLY_AVAILABLE:
        st.error("❌ Plotly is required for chart components")
        return

    try:
        st.markdown(f"### {title}")

        if not milestones:
            st.info("No milestone data available")
            return

        # Prepare milestone data
        milestone_names = []
        milestone_dates = []
        milestone_status = []

        for milestone in milestones:
            milestone_names.append(milestone.get('name', 'Unnamed Milestone'))
            milestone_dates.append(pd.to_datetime(milestone.get('due_date', datetime.now())))
            milestone_status.append(milestone.get('status', 'Planned'))

        # Create scatter plot for milestones
        fig = go.Figure()

        # Add milestone points
        for i, (name, date, status) in enumerate(zip(milestone_names, milestone_dates, milestone_status)):
            color = get_status_color(status)

            fig.add_trace(go.Scatter(
                x=[date],
                y=[i],
                mode='markers+text',
                name=name,
                text=[name],
                textposition="middle right",
                marker=dict(
                    size=12,
                    color=color,
                    symbol='diamond'
                ),
                showlegend=False
            ))

        # Add vertical line for current date
        current_date = datetime.now()
        fig.add_vline(
            x=current_date,
            line_width=2,
            line_dash="dash",
            line_color="red",
            annotation_text="Today"
        )

        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="",
            width=width,
            height=height,
            yaxis=dict(
                tickmode='array',
                tickvals=list(range(len(milestone_names))),
                ticktext=milestone_names
            )
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error rendering milestone chart: {str(e)}")


def render_dependency_chart(
    phases: List[Dict[str, Any]],
    title: str = "Phase Dependencies",
    width: Optional[int] = None,
    height: Optional[int] = 500
) -> None:
    """Render phase dependency visualization.

    Args:
        phases: List of project phases with dependencies
        title: Chart title
        width: Chart width
        height: Chart height
    """
    if not PLOTLY_AVAILABLE:
        st.error("❌ Plotly is required for chart components")
        return

    try:
        st.markdown(f"### {title}")

        if not phases:
            st.info("No dependency data available")
            return

        # Create nodes and links for dependency graph
        nodes = []
        links = []

        # Create node mapping
        node_map = {}
        for i, phase in enumerate(phases):
            node_id = f"phase_{i}"
            node_map[phase.get('id', f"phase_{i}")] = node_id
            nodes.append({
                'id': node_id,
                'label': phase.get('name', 'Unnamed'),
                'color': get_phase_status_color(phase.get('status', 'planned'))
            })

        # Create links for dependencies
        for phase in phases:
            phase_id = phase.get('id', 'unknown')
            dependencies = phase.get('dependencies', [])

            for dep in dependencies:
                if dep in node_map and phase_id in node_map:
                    links.append({
                        'source': node_map[dep],
                        'target': node_map[phase_id],
                        'value': 1
                    })

        if not nodes:
            st.info("No valid dependency data to display")
            return

        # Create Sankey diagram for dependencies
        if links:
            # Prepare data for Sankey
            source_indices = []
            target_indices = []
            values = []

            node_labels = [node['label'] for node in nodes]

            for link in links:
                source_idx = node_labels.index(next((n['label'] for n in nodes if n['id'] == link['source']), 'Unknown'))
                target_idx = node_labels.index(next((n['label'] for n in nodes if n['id'] == link['target']), 'Unknown'))

                source_indices.append(source_idx)
                target_indices.append(target_idx)
                values.append(link['value'])

            fig = go.Figure(data=[go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=node_labels,
                    color=[node['color'] for node in nodes]
                ),
                link=dict(
                    source=source_indices,
                    target=target_indices,
                    value=values
                )
            )])

            fig.update_layout(
                title=title,
                width=width,
                height=height
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No dependencies found to visualize")

    except Exception as e:
        st.error(f"❌ Error rendering dependency chart: {str(e)}")


def render_resource_allocation_chart(
    resources: Dict[str, Any],
    time_periods: List[str],
    title: str = "Resource Allocation Over Time",
    width: Optional[int] = None,
    height: Optional[int] = 400
) -> None:
    """Render resource allocation timeline chart.

    Args:
        resources: Resource allocation data
        time_periods: Time periods for allocation
        title: Chart title
        width: Chart width
        height: Chart height
    """
    if not PLOTLY_AVAILABLE:
        st.error("❌ Plotly is required for chart components")
        return

    try:
        st.markdown(f"### {title}")

        if not resources or not time_periods:
            st.info("No resource allocation data available")
            return

        # Prepare data for stacked area chart
        data = []
        resource_names = []

        for resource_name, allocation in resources.items():
            if isinstance(allocation, list) and len(allocation) == len(time_periods):
                data.append(allocation)
                resource_names.append(resource_name)

        if not data:
            st.info("No valid resource allocation data to display")
            return

        # Create stacked area chart
        fig = go.Figure()

        for i, (resource_name, allocation) in enumerate(zip(resource_names, data)):
            fig.add_trace(go.Scatter(
                x=time_periods,
                y=allocation,
                mode='lines',
                name=resource_name,
                stackgroup='one',
                groupnorm='percent'  # Show as percentage
            ))

        fig.update_layout(
            title=title,
            xaxis_title="Time Period",
            yaxis_title="Resource Allocation (%)",
            width=width,
            height=height,
            showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error rendering resource allocation chart: {str(e)}")


def render_timeline_summary(phases: List[Dict[str, Any]]) -> None:
    """Render timeline summary metrics."""
    try:
        if not phases:
            return

        # Calculate summary metrics
        total_duration = sum(phase.get('duration_days', 0) for phase in phases)
        completed_phases = sum(1 for phase in phases if phase.get('status') == 'completed')
        in_progress_phases = sum(1 for phase in phases if phase.get('status') == 'in_progress')
        planned_phases = sum(1 for phase in phases if phase.get('status') in ['planned', None])

        # Display metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Duration", f"{total_duration} days")

        with col2:
            completion_rate = (completed_phases / len(phases)) * 100 if phases else 0
            st.metric("Completion Rate", ".1f", completion_rate)

        with col3:
            st.metric("Completed", completed_phases)

        with col4:
            st.metric("In Progress", in_progress_phases)

        # Phase status breakdown
        status_counts = {
            'Completed': completed_phases,
            'In Progress': in_progress_phases,
            'Planned': planned_phases
        }

        # Create status pie chart
        fig = px.pie(
            values=list(status_counts.values()),
            names=list(status_counts.keys()),
            title="Phase Status Distribution"
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error rendering timeline summary: {str(e)}")


# Helper functions

def calculate_phase_start_date(
    phase: Dict[str, Any],
    all_phases: List[Dict[str, Any]],
    project_start: datetime
) -> datetime:
    """Calculate the start date for a phase based on dependencies."""
    dependencies = phase.get('dependencies', [])

    if not dependencies:
        return project_start

    # Find the latest end date among dependencies
    latest_end_date = project_start

    for dep_id in dependencies:
        dep_phase = next((p for p in all_phases if p.get('id') == dep_id), None)
        if dep_phase:
            dep_duration = dep_phase.get('duration_days', 7)
            dep_end_date = project_start + timedelta(days=dep_duration)
            latest_end_date = max(latest_end_date, dep_end_date)

    return latest_end_date


def get_status_color(status: str) -> str:
    """Get color for milestone status."""
    color_map = {
        'completed': 'green',
        'in_progress': 'blue',
        'planned': 'gray',
        'overdue': 'red',
        'at_risk': 'orange'
    }
    return color_map.get(status.lower(), 'gray')


def get_phase_status_color(status: str) -> str:
    """Get color for phase status."""
    color_map = {
        'completed': '#2ca02c',
        'in_progress': '#1f77b4',
        'planned': '#7f7f7f',
        'on_hold': '#ff7f0e',
        'cancelled': '#d62728'
    }
    return color_map.get(status.lower(), '#7f7f7f')
