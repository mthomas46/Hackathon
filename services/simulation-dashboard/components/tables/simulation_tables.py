"""Simulation Table Components.

This module provides table components for displaying and managing simulation data,
including status tracking, filtering, sorting, and bulk operations.
"""

import streamlit as st
from typing import Dict, Any, Optional, List, Callable
import pandas as pd
from datetime import datetime, timedelta
import numpy as np


def render_simulation_table(
    simulations_data: List[Dict[str, Any]],
    title: str = "📊 Simulation Management",
    show_controls: bool = True,
    enable_selection: bool = True,
    enable_filtering: bool = True,
    enable_sorting: bool = True,
    on_status_change: Optional[Callable] = None,
    on_delete: Optional[Callable] = None,
    on_view_details: Optional[Callable] = None
) -> Dict[str, Any]:
    """Render a comprehensive simulation management table.

    Args:
        simulations_data: List of simulation data dictionaries
        title: Table title
        show_controls: Whether to show action controls
        enable_selection: Whether to enable row selection
        enable_filtering: Whether to enable filtering
        enable_sorting: Whether to enable sorting
        on_status_change: Callback for status changes
        on_delete: Callback for deletion
        on_view_details: Callback for viewing details

    Returns:
        Dictionary with table state and selected items
    """
    st.markdown(f"### {title}")

    if not simulations_data:
        st.info("No simulations found. Create your first simulation to get started!")
        return {'selected_simulations': [], 'table_state': {}}

    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(simulations_data)

    # Ensure required columns exist
    required_columns = ['id', 'name', 'status', 'created_at', 'progress', 'duration']
    for col in required_columns:
        if col not in df.columns:
            df[col] = 'N/A' if col in ['name', 'status'] else 0 if col in ['progress', 'duration'] else datetime.now()

    # Add derived columns
    df['created_date'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
    df['status_icon'] = df['status'].apply(get_status_icon)
    df['progress_display'] = df['progress'].apply(lambda x: ".1f")
    df['duration_display'] = df['duration'].apply(format_duration)

    # Filters
    if enable_filtering:
        st.markdown("#### 🔍 Filters")
        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

        with filter_col1:
            status_filter = st.multiselect(
                "Status",
                options=['pending', 'running', 'completed', 'failed', 'paused', 'cancelled'],
                default=[],
                key="simulation_status_filter"
            )

        with filter_col2:
            name_search = st.text_input(
                "Search by Name",
                placeholder="Enter simulation name...",
                key="simulation_name_search"
            )

        with filter_col3:
            date_from = st.date_input(
                "Created From",
                value=datetime.now() - timedelta(days=30),
                key="simulation_date_from"
            )

        with filter_col4:
            date_to = st.date_input(
                "Created To",
                value=datetime.now(),
                key="simulation_date_to"
            )

        # Apply filters
        filtered_df = df.copy()

        if status_filter:
            filtered_df = filtered_df[filtered_df['status'].isin(status_filter)]

        if name_search:
            filtered_df = filtered_df[
                filtered_df['name'].str.contains(name_search, case=False, na=False)
            ]

        if date_from and date_to:
            filtered_df = filtered_df[
                (pd.to_datetime(filtered_df['created_at']).dt.date >= date_from) &
                (pd.to_datetime(filtered_df['created_at']).dt.date <= date_to)
            ]
    else:
        filtered_df = df

    # Sorting
    if enable_sorting:
        sort_col1, sort_col2 = st.columns([3, 1])

        with sort_col1:
            sort_by = st.selectbox(
                "Sort by",
                options=['created_at', 'name', 'status', 'progress', 'duration'],
                format_func=lambda x: x.replace('_', ' ').title(),
                key="simulation_sort_by"
            )

        with sort_col2:
            sort_order = st.selectbox(
                "Order",
                options=['descending', 'ascending'],
                key="simulation_sort_order"
            )

        ascending = sort_order == 'ascending'
        filtered_df = filtered_df.sort_values(sort_by, ascending=ascending)

    # Selection
    selected_simulations = []
    if enable_selection:
        st.markdown("#### ✅ Selection")

        select_col1, select_col2, select_col3 = st.columns([1, 2, 2])

        with select_col1:
            select_all = st.checkbox("Select All", key="simulation_select_all")

        with select_col2:
            if st.button("🗑️ Delete Selected", key="simulation_delete_selected", type="secondary"):
                if selected_simulations and on_delete:
                    on_delete(selected_simulations)

        with select_col3:
            if st.button("⏸️ Pause Selected", key="simulation_pause_selected"):
                if selected_simulations and on_status_change:
                    for sim_id in selected_simulations:
                        on_status_change(sim_id, 'paused')

    # Display table
    st.markdown(f"#### 📋 Simulations ({len(filtered_df)} total)")

    # Create display DataFrame
    display_columns = ['status_icon', 'name', 'created_date', 'progress_display', 'duration_display', 'status']
    display_df = filtered_df[display_columns].copy()
    display_df.columns = ['Status', 'Name', 'Created', 'Progress', 'Duration', 'State']

    # Render table with selection
    if enable_selection:
        # Add selection column
        selection_data = []
        for idx, row in filtered_df.iterrows():
            sim_id = row['id']
            is_selected = select_all or st.checkbox(
                f"Select {row['name']}",
                key=f"select_sim_{sim_id}",
                value=select_all
            )
            if is_selected:
                selected_simulations.append(sim_id)

            selection_data.append({
                'Select': "✅" if is_selected else "⬜",
                'Status': row['status_icon'],
                'Name': row['name'],
                'Created': row['created_date'],
                'Progress': row['progress_display'],
                'Duration': row['duration_display'],
                'State': row['status']
            })

        selection_df = pd.DataFrame(selection_data)
        st.dataframe(
            selection_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        # Simple table without selection
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

    # Individual row actions
    if show_controls and not filtered_df.empty:
        st.markdown("#### 🎮 Individual Actions")

        # Group actions by status for better organization
        status_groups = filtered_df.groupby('status')

        for status, group in status_groups:
            if len(group) > 0:
                with st.expander(f"{get_status_icon(status)} {status.title()} Simulations ({len(group)})", expanded=False):
                    for _, row in group.iterrows():
                        render_simulation_row_actions(
                            row, on_status_change, on_delete, on_view_details
                        )

    # Table statistics
    st.markdown("#### 📊 Table Statistics")

    col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)

    with col_stats1:
        st.metric("Total Simulations", len(df))

    with col_stats2:
        running_count = len(df[df['status'] == 'running'])
        st.metric("Running", running_count)

    with col_stats3:
        completed_count = len(df[df['status'] == 'completed'])
        st.metric("Completed", completed_count)

    with col_stats4:
        failed_count = len(df[df['status'] == 'failed'])
        st.metric("Failed", failed_count)

    return {
        'selected_simulations': selected_simulations,
        'table_state': {
            'total_count': len(df),
            'filtered_count': len(filtered_df),
            'status_counts': df['status'].value_counts().to_dict(),
            'sort_by': sort_by if enable_sorting else None,
            'sort_order': sort_order if enable_sorting else None,
            'filters': {
                'status': status_filter if enable_filtering else [],
                'name_search': name_search if enable_filtering else '',
                'date_from': date_from if enable_filtering else None,
                'date_to': date_to if enable_filtering else None
            }
        }
    }


def render_simulation_row_actions(
    simulation_row: pd.Series,
    on_status_change: Optional[Callable],
    on_delete: Optional[Callable],
    on_view_details: Optional[Callable]
):
    """Render action buttons for a single simulation row."""
    sim_id = simulation_row['id']
    sim_name = simulation_row['name']
    sim_status = simulation_row['status']

    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])

    with col1:
        st.write(f"**{sim_name}** ({sim_id})")

    with col2:
        if on_view_details:
            if st.button("👁️ View", key=f"view_{sim_id}"):
                on_view_details(sim_id)

    with col3:
        # Status-specific actions
        if sim_status == 'running':
            if on_status_change:
                if st.button("⏸️ Pause", key=f"pause_{sim_id}"):
                    on_status_change(sim_id, 'paused')
        elif sim_status == 'paused':
            if on_status_change:
                if st.button("▶️ Resume", key=f"resume_{sim_id}"):
                    on_status_change(sim_id, 'running')
        elif sim_status in ['pending', 'completed']:
            if on_status_change:
                if st.button("▶️ Start", key=f"start_{sim_id}"):
                    on_status_change(sim_id, 'running')

    with col4:
        if sim_status in ['running', 'paused']:
            if on_status_change:
                if st.button("⏹️ Stop", key=f"stop_{sim_id}", type="secondary"):
                    on_status_change(sim_id, 'cancelled')

    with col5:
        if on_delete:
            if st.button("🗑️ Delete", key=f"delete_{sim_id}", type="secondary"):
                if st.checkbox("Confirm", key=f"confirm_delete_{sim_id}"):
                    on_delete([sim_id])


def get_status_icon(status: str) -> str:
    """Get status icon for display."""
    icons = {
        'pending': '⏳',
        'running': '🔄',
        'completed': '✅',
        'failed': '❌',
        'paused': '⏸️',
        'cancelled': '🚫'
    }
    return icons.get(status, '❓')


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable format."""
    if pd.isna(seconds) or seconds == 0:
        return "0s"

    if seconds < 60:
        return ".1f"
    elif seconds < 3600:
        minutes = seconds / 60
        return ".1f"
    elif seconds < 86400:
        hours = seconds / 3600
        return ".1f"
    else:
        days = seconds / 86400
        return ".1f"


def render_simulation_summary_table(
    simulations_data: List[Dict[str, Any]],
    group_by: str = 'status',
    title: str = "📈 Simulation Summary"
) -> Dict[str, Any]:
    """Render a summary table grouped by specified criteria.

    Args:
        simulations_data: List of simulation data
        group_by: Column to group by ('status', 'created_date', etc.)
        title: Table title

    Returns:
        Summary statistics
    """
    st.markdown(f"### {title}")

    if not simulations_data:
        st.info("No simulation data available for summary.")
        return {}

    df = pd.DataFrame(simulations_data)

    # Group and aggregate
    if group_by == 'status':
        summary = df.groupby('status').agg({
            'id': 'count',
            'progress': 'mean',
            'duration': 'mean'
        }).round(2)

        summary.columns = ['Count', 'Avg Progress', 'Avg Duration']
        summary['Avg Duration'] = summary['Avg Duration'].apply(format_duration)

    elif group_by == 'created_date':
        df['date'] = pd.to_datetime(df['created_at']).dt.date
        summary = df.groupby('date').agg({
            'id': 'count',
            'progress': 'mean',
            'duration': 'mean'
        }).round(2)

        summary.columns = ['Count', 'Avg Progress', 'Avg Duration']
        summary['Avg Duration'] = summary['Avg Duration'].apply(format_duration)

    else:
        # Default summary
        summary = df.agg({
            'id': 'count',
            'progress': 'mean',
            'duration': 'mean'
        }).round(2).to_frame().T
        summary.columns = ['Total Count', 'Avg Progress', 'Avg Duration']
        summary['Avg Duration'] = summary['Avg Duration'].apply(format_duration)

    # Display summary table
    st.dataframe(summary, use_container_width=True)

    return summary.to_dict()


# Sample data generator for testing
def generate_sample_simulation_data(count: int = 10) -> List[Dict[str, Any]]:
    """Generate sample simulation data for testing."""
    statuses = ['pending', 'running', 'completed', 'failed', 'paused', 'cancelled']
    names = [
        'E-commerce Platform', 'Mobile App', 'API Service', 'Data Pipeline',
        'ML Model Training', 'Web Application', 'Microservices', 'Analytics Dashboard'
    ]

    simulations = []
    base_time = datetime.now() - timedelta(days=30)

    for i in range(count):
        created_at = base_time + timedelta(days=np.random.randint(0, 30))
        status = np.random.choice(statuses, p=[0.1, 0.3, 0.4, 0.1, 0.05, 0.05])

        simulation = {
            'id': f"sim_{i+1:03d}",
            'name': np.random.choice(names),
            'status': status,
            'created_at': created_at,
            'progress': np.random.uniform(0, 100) if status in ['running', 'completed'] else 0,
            'duration': np.random.uniform(0, 3600) if status == 'completed' else np.random.uniform(0, 1800),
            'description': f"Sample simulation {i+1}"
        }
        simulations.append(simulation)

    return simulations
