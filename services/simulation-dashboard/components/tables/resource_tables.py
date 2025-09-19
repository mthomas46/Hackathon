"""Resource Table Components.

This module provides table components for displaying and managing resource allocation,
usage tracking, and capacity planning.
"""

import streamlit as st
from typing import Dict, Any, Optional, List, Callable
import pandas as pd
from datetime import datetime, timedelta
import numpy as np


def render_resource_table(
    resources_data: List[Dict[str, Any]],
    title: str = "📊 Resource Allocation",
    show_capacity: bool = True,
    enable_monitoring: bool = True,
    on_allocation_change: Optional[Callable] = None,
    on_capacity_adjust: Optional[Callable] = None
) -> Dict[str, Any]:
    """Render a comprehensive resource allocation table.

    Args:
        resources_data: List of resource data dictionaries
        title: Table title
        show_capacity: Whether to show capacity information
        enable_monitoring: Whether to enable real-time monitoring
        on_allocation_change: Callback for allocation changes
        on_capacity_adjust: Callback for capacity adjustments

    Returns:
        Dictionary with table state and resource metrics
    """
    st.markdown(f"### {title}")

    if not resources_data:
        st.info("No resource data available. Configure resources to get started!")
        return {'resource_metrics': {}, 'allocation_summary': {}}

    # Convert to DataFrame
    df = pd.DataFrame(resources_data)

    # Ensure required columns exist
    required_columns = ['id', 'name', 'type', 'allocated', 'capacity', 'utilization', 'status']
    for col in required_columns:
        if col not in df.columns:
            df[col] = 'N/A' if col in ['name', 'type', 'status'] else 0

    # Calculate derived metrics
    df['utilization_display'] = df['utilization'].apply(lambda x: ".1f")
    df['available'] = df['capacity'] - df['allocated']
    df['available_display'] = df['available'].apply(lambda x: max(0, x))
    df['status_icon'] = df['status'].apply(get_resource_status_icon)

    # Resource type filter
    resource_types = df['type'].unique().tolist()
    selected_types = st.multiselect(
        "Filter by Resource Type",
        options=resource_types,
        default=resource_types,
        key="resource_type_filter"
    )

    filtered_df = df[df['type'].isin(selected_types)] if selected_types else df

    # Resource status overview
    st.markdown("#### 📊 Resource Overview")

    status_counts = filtered_df['status'].value_counts()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_resources = len(filtered_df)
        st.metric("Total Resources", total_resources)

    with col2:
        healthy_count = status_counts.get('healthy', 0)
        st.metric("Healthy", healthy_count)

    with col3:
        warning_count = status_counts.get('warning', 0)
        st.metric("Warning", warning_count)

    with col4:
        critical_count = status_counts.get('critical', 0)
        st.metric("Critical", critical_count)

    # Resource utilization summary
    st.markdown("#### 📈 Utilization Summary")

    utilization_stats = {
        'Average Utilization': filtered_df['utilization'].mean(),
        'Peak Utilization': filtered_df['utilization'].max(),
        'Low Utilization (<30%)': len(filtered_df[filtered_df['utilization'] < 30]),
        'High Utilization (>80%)': len(filtered_df[filtered_df['utilization'] > 80])
    }

    col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)

    with col_stats1:
        st.metric("Avg Utilization", ".1f", utilization_stats['Average Utilization'])

    with col_stats2:
        st.metric("Peak Utilization", ".1f", utilization_stats['Peak Utilization'])

    with col_stats3:
        st.metric("Under-utilized", utilization_stats['Low Utilization (<30%)'])

    with col_stats4:
        st.metric("Over-utilized", utilization_stats['High Utilization (>80%)'])

    # Main resource table
    st.markdown("#### 📋 Resource Details")

    # Display columns
    display_columns = [
        'status_icon', 'name', 'type', 'allocated', 'capacity',
        'available_display', 'utilization_display', 'status'
    ]
    display_names = [
        'Status', 'Name', 'Type', 'Allocated', 'Capacity',
        'Available', 'Utilization', 'State'
    ]

    display_df = filtered_df[display_columns].copy()
    display_df.columns = display_names

    # Color-code utilization
    def color_utilization(val):
        if isinstance(val, str) and '%' in val:
            util_val = float(val.strip('%'))
            if util_val > 80:
                return 'background-color: #ffcccc'  # Light red
            elif util_val > 60:
                return 'background-color: #fff3cd'  # Light yellow
            else:
                return 'background-color: #d4edda'  # Light green
        return ''

    # Display table
    st.dataframe(
        display_df.style.applymap(color_utilization, subset=['Utilization']),
        use_container_width=True,
        hide_index=True
    )

    # Individual resource actions
    if not filtered_df.empty:
        st.markdown("#### 🎮 Resource Actions")

        # Group by status for better organization
        critical_resources = filtered_df[filtered_df['status'] == 'critical']
        warning_resources = filtered_df[filtered_df['status'] == 'warning']

        if len(critical_resources) > 0:
            with st.expander("🚨 Critical Resources", expanded=True):
                for _, row in critical_resources.iterrows():
                    render_resource_actions(row, on_allocation_change, on_capacity_adjust)

        if len(warning_resources) > 0:
            with st.expander("⚠️ Warning Resources", expanded=False):
                for _, row in warning_resources.iterrows():
                    render_resource_actions(row, on_allocation_change, on_capacity_adjust)

        # Healthy resources
        healthy_resources = filtered_df[filtered_df['status'] == 'healthy']
        if len(healthy_resources) > 0:
            with st.expander("✅ Healthy Resources", expanded=False):
                for _, row in healthy_resources.iterrows():
                    render_resource_actions(row, on_allocation_change, on_capacity_adjust)

    # Capacity planning
    if show_capacity:
        st.markdown("#### 📅 Capacity Planning")

        # Forecast future utilization
        forecast_days = st.slider("Forecast Period (days)", 7, 90, 30, key="capacity_forecast_days")

        forecast_data = forecast_resource_utilization(filtered_df, forecast_days)

        if forecast_data:
            st.markdown("**Projected Utilization Trends:**")
            for resource_type, forecast in forecast_data.items():
                st.write(f"- **{resource_type}**: {forecast['current']:.1f}% → {forecast['projected']:.1f}% (in {forecast_days} days)")

                if forecast['projected'] > 90:
                    st.warning(f"⚠️ {resource_type} projected to exceed 90% utilization!")
                elif forecast['projected'] < 30:
                    st.info(f"💡 {resource_type} has low projected utilization - consider consolidation.")

    # Resource allocation recommendations
    st.markdown("#### 💡 Recommendations")

    recommendations = generate_resource_recommendations(filtered_df)

    for rec in recommendations:
        if rec['priority'] == 'high':
            st.error(f"🔴 {rec['message']}")
        elif rec['priority'] == 'medium':
            st.warning(f"🟡 {rec['message']}")
        else:
            st.info(f"💡 {rec['message']}")

    return {
        'resource_metrics': {
            'total_resources': len(filtered_df),
            'healthy_count': healthy_count,
            'warning_count': warning_count,
            'critical_count': critical_count,
            'average_utilization': utilization_stats['Average Utilization'],
            'peak_utilization': utilization_stats['Peak Utilization']
        },
        'allocation_summary': {
            'total_allocated': filtered_df['allocated'].sum(),
            'total_capacity': filtered_df['capacity'].sum(),
            'total_available': filtered_df['available'].sum(),
            'overall_utilization': (filtered_df['allocated'].sum() / filtered_df['capacity'].sum()) * 100 if filtered_df['capacity'].sum() > 0 else 0
        },
        'filtered_resources': filtered_df.to_dict('records')
    }


def render_resource_actions(
    resource_row: pd.Series,
    on_allocation_change: Optional[Callable],
    on_capacity_adjust: Optional[Callable]
):
    """Render action buttons for a single resource."""
    resource_id = resource_row['id']
    resource_name = resource_row['name']
    resource_status = resource_row['status']
    current_allocation = resource_row['allocated']
    capacity = resource_row['capacity']
    utilization = resource_row['utilization']

    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])

    with col1:
        st.write(f"**{resource_name}**")
        st.write(f"Utilization: {utilization:.1f}% | Available: {capacity - current_allocation}")

    with col2:
        # Allocation adjustment
        if on_allocation_change:
            if st.button("⚖️ Adjust", key=f"adjust_{resource_id}"):
                st.session_state[f"adjusting_{resource_id}"] = True

            if st.session_state.get(f"adjusting_{resource_id}", False):
                new_allocation = st.number_input(
                    "New Allocation",
                    min_value=0,
                    max_value=int(capacity),
                    value=int(current_allocation),
                    key=f"new_allocation_{resource_id}"
                )

                if st.button("✅ Apply", key=f"apply_adjust_{resource_id}"):
                    on_allocation_change(resource_id, new_allocation)
                    st.session_state[f"adjusting_{resource_id}"] = False
                    st.rerun()

                if st.button("❌ Cancel", key=f"cancel_adjust_{resource_id}"):
                    st.session_state[f"adjusting_{resource_id}"] = False
                    st.rerun()

    with col3:
        # Capacity adjustment
        if on_capacity_adjust:
            if st.button("🔧 Capacity", key=f"capacity_{resource_id}"):
                st.session_state[f"adjusting_capacity_{resource_id}"] = True

            if st.session_state.get(f"adjusting_capacity_{resource_id}", False):
                new_capacity = st.number_input(
                    "New Capacity",
                    min_value=int(current_allocation),
                    value=int(capacity),
                    key=f"new_capacity_{resource_id}"
                )

                if st.button("✅ Update", key=f"apply_capacity_{resource_id}"):
                    on_capacity_adjust(resource_id, new_capacity)
                    st.session_state[f"adjusting_capacity_{resource_id}"] = False
                    st.rerun()

                if st.button("❌ Cancel", key=f"cancel_capacity_{resource_id}"):
                    st.session_state[f"adjusting_capacity_{resource_id}"] = False
                    st.rerun()

    with col4:
        # Quick actions based on status
        if utilization > 80:
            if st.button("🛑 Throttle", key=f"throttle_{resource_id}", type="secondary"):
                st.info(f"Throttling resource {resource_name}...")
        elif utilization < 30:
            if st.button("⚡ Scale Down", key=f"scale_down_{resource_id}"):
                st.info(f"Scaling down resource {resource_name}...")

    with col5:
        # Monitoring toggle
        monitoring_enabled = st.checkbox(
            "Monitor",
            value=True,
            key=f"monitor_{resource_id}",
            help="Enable real-time monitoring for this resource"
        )


def get_resource_status_icon(status: str) -> str:
    """Get status icon for resource display."""
    icons = {
        'healthy': '✅',
        'warning': '⚠️',
        'critical': '🚨',
        'unknown': '❓',
        'maintenance': '🔧'
    }
    return icons.get(status, '❓')


def forecast_resource_utilization(df: pd.DataFrame, days: int) -> Dict[str, Dict[str, float]]:
    """Forecast future resource utilization."""
    forecast_data = {}

    for resource_type in df['type'].unique():
        type_data = df[df['type'] == resource_type]

        if len(type_data) > 0:
            current_avg = type_data['utilization'].mean()

            # Simple forecasting based on current trends
            # In a real implementation, this would use more sophisticated forecasting
            growth_rate = np.random.uniform(-0.02, 0.05)  # Random growth between -2% and +5%
            projected = min(100, current_avg * (1 + growth_rate * (days / 30)))

            forecast_data[resource_type] = {
                'current': current_avg,
                'projected': projected,
                'growth_rate': growth_rate * 100
            }

    return forecast_data


def generate_resource_recommendations(df: pd.DataFrame) -> List[Dict[str, str]]:
    """Generate resource management recommendations."""
    recommendations = []

    # Check for over-utilized resources
    over_utilized = df[df['utilization'] > 80]
    if len(over_utilized) > 0:
        recommendations.append({
            'message': f"{len(over_utilized)} resources are over-utilized (>80%). Consider scaling up capacity.",
            'priority': 'high'
        })

    # Check for under-utilized resources
    under_utilized = df[df['utilization'] < 30]
    if len(under_utilized) > 0:
        recommendations.append({
            'message': f"{len(under_utilized)} resources are under-utilized (<30%). Consider consolidation or scaling down.",
            'priority': 'medium'
        })

    # Check for critical resources
    critical_count = len(df[df['status'] == 'critical'])
    if critical_count > 0:
        recommendations.append({
            'message': f"{critical_count} resources are in critical status. Immediate attention required.",
            'priority': 'high'
        })

    # Check for capacity bottlenecks
    low_capacity = df[df['available'] < (df['capacity'] * 0.1)]  # Less than 10% available
    if len(low_capacity) > 0:
        recommendations.append({
            'message': f"{len(low_capacity)} resources are running low on capacity. Plan for expansion.",
            'priority': 'medium'
        })

    # General recommendations
    total_utilization = df['utilization'].mean()
    if total_utilization > 70:
        recommendations.append({
            'message': "Overall resource utilization is high. Consider capacity planning.",
            'priority': 'medium'
        })
    elif total_utilization < 40:
        recommendations.append({
            'message': "Overall resource utilization is low. Look for optimization opportunities.",
            'priority': 'low'
        })

    return recommendations


# Sample data generator for testing
def generate_sample_resource_data(count: int = 8) -> List[Dict[str, Any]]:
    """Generate sample resource data for testing."""
    resource_types = ['CPU', 'Memory', 'Storage', 'Network', 'GPU', 'Database']
    statuses = ['healthy', 'warning', 'critical']

    resources = []

    for i in range(count):
        capacity = np.random.uniform(100, 1000)
        utilization = np.random.uniform(10, 95)
        allocated = capacity * (utilization / 100)

        # Determine status based on utilization
        if utilization > 85:
            status = 'critical'
        elif utilization > 70:
            status = 'warning'
        else:
            status = 'healthy'

        resource = {
            'id': f"res_{i+1:03d}",
            'name': f"{np.random.choice(resource_types)}-{i+1}",
            'type': np.random.choice(resource_types),
            'allocated': round(allocated, 1),
            'capacity': round(capacity, 1),
            'utilization': round(utilization, 1),
            'status': status,
            'description': f"Sample resource {i+1}",
            'last_updated': datetime.now() - timedelta(minutes=np.random.randint(0, 60))
        }
        resources.append(resource)

    return resources
