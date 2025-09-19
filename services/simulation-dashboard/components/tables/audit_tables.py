"""Audit Table Components.

This module provides table components for displaying audit trails,
compliance logs, and security event tracking.
"""

import streamlit as st
from typing import Dict, Any, Optional, List, Callable
import pandas as pd
from datetime import datetime, timedelta
import numpy as np


def render_audit_table(
    audit_data: List[Dict[str, Any]],
    title: str = "🔍 Audit Trail",
    enable_filtering: bool = True,
    enable_search: bool = True,
    enable_export: bool = True,
    on_investigate: Optional[Callable] = None,
    on_export: Optional[Callable] = None
) -> Dict[str, Any]:
    """Render a comprehensive audit trail table.

    Args:
        audit_data: List of audit event dictionaries
        title: Table title
        enable_filtering: Whether to enable filtering
        enable_search: Whether to enable search
        enable_export: Whether to enable export
        on_investigate: Callback for investigating events
        on_export: Callback for export actions

    Returns:
        Dictionary with table state and audit metrics
    """
    st.markdown(f"### {title}")

    if not audit_data:
        st.info("No audit events found. Audit logging will appear here as events occur.")
        return {'audit_metrics': {}, 'filtered_events': []}

    # Convert to DataFrame
    df = pd.DataFrame(audit_data)

    # Ensure required columns exist
    required_columns = ['id', 'timestamp', 'event_type', 'user', 'action', 'resource', 'severity', 'status']
    for col in required_columns:
        if col not in df.columns:
            df[col] = 'N/A' if col in ['user', 'action', 'resource'] else 'info' if col == 'severity' else 'success' if col == 'status' else datetime.now()

    # Add derived columns
    df['timestamp_display'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    df['severity_icon'] = df['severity'].apply(get_severity_icon)
    df['status_icon'] = df['status'].apply(get_status_icon)

    # Filters and search
    if enable_filtering or enable_search:
        st.markdown("#### 🔍 Filters & Search")

        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

        with filter_col1:
            severity_filter = st.multiselect(
                "Severity",
                options=['critical', 'high', 'medium', 'low', 'info'],
                default=[],
                key="audit_severity_filter"
            )

        with filter_col2:
            event_type_filter = st.multiselect(
                "Event Type",
                options=df['event_type'].unique().tolist(),
                default=[],
                key="audit_event_filter"
            )

        with filter_col3:
            date_from = st.date_input(
                "From Date",
                value=datetime.now() - timedelta(days=7),
                key="audit_date_from"
            )

        with filter_col4:
            date_to = st.date_input(
                "To Date",
                value=datetime.now(),
                key="audit_date_to"
            )

        # Search
        if enable_search:
            search_term = st.text_input(
                "Search Events",
                placeholder="Search by user, action, or resource...",
                key="audit_search"
            )

    # Apply filters
    filtered_df = df.copy()

    if enable_filtering:
        if severity_filter:
            filtered_df = filtered_df[filtered_df['severity'].isin(severity_filter)]

        if event_type_filter:
            filtered_df = filtered_df[filtered_df['event_type'].isin(event_type_filter)]

        if date_from and date_to:
            filtered_df = filtered_df[
                (pd.to_datetime(filtered_df['timestamp']).dt.date >= date_from) &
                (pd.to_datetime(filtered_df['timestamp']).dt.date <= date_to)
            ]

    if enable_search and 'search_term' in locals() and search_term:
        search_cols = ['user', 'action', 'resource']
        search_condition = filtered_df[search_cols].apply(
            lambda x: x.astype(str).str.contains(search_term, case=False, na=False)
        ).any(axis=1)
        filtered_df = filtered_df[search_condition]

    # Sort by timestamp (most recent first)
    filtered_df = filtered_df.sort_values('timestamp', ascending=False)

    # Audit metrics
    st.markdown("#### 📊 Audit Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_events = len(filtered_df)
        st.metric("Total Events", total_events)

    with col2:
        critical_count = len(filtered_df[filtered_df['severity'] == 'critical'])
        st.metric("Critical", critical_count)

    with col3:
        failed_count = len(filtered_df[filtered_df['status'] == 'failed'])
        st.metric("Failed", failed_count)

    with col4:
        recent_count = len(filtered_df[
            pd.to_datetime(filtered_df['timestamp']) > (datetime.now() - timedelta(hours=24))
        ])
        st.metric("Last 24h", recent_count)

    # Event type breakdown
    st.markdown("#### 📈 Event Breakdown")

    event_types = filtered_df['event_type'].value_counts()
    severity_levels = filtered_df['severity'].value_counts()

    col_break1, col_break2 = st.columns(2)

    with col_break1:
        st.write("**Event Types:**")
        for event_type, count in event_types.head(5).items():
            st.write(f"- {event_type}: {count}")

    with col_break2:
        st.write("**Severity Levels:**")
        for severity, count in severity_levels.items():
            icon = get_severity_icon(severity)
            st.write(f"- {icon} {severity.title()}: {count}")

    # Main audit table
    st.markdown(f"#### 📋 Audit Events ({len(filtered_df)} total)")

    # Display columns
    display_columns = [
        'severity_icon', 'timestamp_display', 'event_type', 'user',
        'action', 'resource', 'status_icon'
    ]
    display_names = [
        'Severity', 'Timestamp', 'Event Type', 'User',
        'Action', 'Resource', 'Status'
    ]

    display_df = filtered_df[display_columns].copy()
    display_df.columns = display_names

    # Display table
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=400
    )

    # Individual event details
    if not filtered_df.empty:
        st.markdown("#### 🔍 Event Details")

        # Show details for high-severity events first
        high_priority_events = filtered_df[
            (filtered_df['severity'].isin(['critical', 'high'])) |
            (filtered_df['status'] == 'failed')
        ]

        if len(high_priority_events) > 0:
            with st.expander("🚨 High Priority Events", expanded=True):
                for _, row in high_priority_events.head(5).iterrows():
                    render_audit_event_details(row, on_investigate)

        # Show recent events
        recent_events = filtered_df.head(10)
        with st.expander("🕒 Recent Events", expanded=False):
            for _, row in recent_events.iterrows():
                render_audit_event_details(row, on_investigate)

    # Export functionality
    if enable_export:
        st.markdown("#### 💾 Export")

        col_export1, col_export2, col_export3 = st.columns([1, 2, 2])

        with col_export1:
            export_format = st.selectbox(
                "Format",
                options=['CSV', 'JSON', 'PDF'],
                key="audit_export_format"
            )

        with col_export2:
            if st.button("📥 Export Filtered", key="export_filtered"):
                export_audit_data(filtered_df, export_format, "filtered_audit")
                st.success("✅ Export completed!")

        with col_export3:
            if st.button("📥 Export All", key="export_all"):
                export_audit_data(df, export_format, "full_audit")
                st.success("✅ Export completed!")

    return {
        'audit_metrics': {
            'total_events': len(df),
            'filtered_events': len(filtered_df),
            'critical_events': critical_count,
            'failed_events': failed_count,
            'recent_events': recent_count
        },
        'filtered_events': filtered_df.to_dict('records'),
        'event_breakdown': {
            'event_types': event_types.to_dict(),
            'severity_levels': severity_levels.to_dict()
        }
    }


def render_audit_event_details(event_row: pd.Series, on_investigate: Optional[Callable]):
    """Render detailed view of an audit event."""
    event_id = event_row['id']
    severity = event_row['severity']
    timestamp = event_row['timestamp_display']
    event_type = event_row['event_type']
    user = event_row['user']
    action = event_row['action']
    resource = event_row['resource']
    status = event_row['status']

    severity_icon = get_severity_icon(severity)
    status_icon = get_status_icon(status)

    with st.expander(f"{severity_icon} {event_type} - {action} ({timestamp})", expanded=False):
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            st.write(f"**User:** {user}")
            st.write(f"**Action:** {action}")
            st.write(f"**Resource:** {resource}")

        with col2:
            st.write(f"**Severity:** {severity_icon} {severity.title()}")
            st.write(f"**Status:** {status_icon} {status.title()}")
            st.write(f"**Event ID:** {event_id}")

        with col3:
            if on_investigate:
                if st.button("🔍 Investigate", key=f"investigate_{event_id}"):
                    on_investigate(event_id)

            # Additional details if available
            if 'details' in event_row and event_row['details']:
                if st.button("📋 More Details", key=f"details_{event_id}"):
                    st.json(event_row['details'])

        # Show additional fields if they exist
        additional_fields = ['ip_address', 'user_agent', 'session_id', 'error_message']
        additional_data = {}

        for field in additional_fields:
            if field in event_row.index and pd.notna(event_row[field]):
                additional_data[field.replace('_', ' ').title()] = event_row[field]

        if additional_data:
            st.markdown("**Additional Information:**")
            for key, value in additional_data.items():
                st.write(f"- **{key}:** {value}")


def get_severity_icon(severity: str) -> str:
    """Get severity icon for display."""
    icons = {
        'critical': '🚨',
        'high': '🔴',
        'medium': '🟡',
        'low': '🟢',
        'info': 'ℹ️'
    }
    return icons.get(severity, '❓')


def get_status_icon(status: str) -> str:
    """Get status icon for display."""
    icons = {
        'success': '✅',
        'failed': '❌',
        'warning': '⚠️',
        'pending': '⏳',
        'unknown': '❓'
    }
    return icons.get(status, '❓')


def export_audit_data(df: pd.DataFrame, format_type: str, filename_prefix: str):
    """Export audit data in specified format."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{filename_prefix}_{timestamp}"

    if format_type == 'CSV':
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=f"{filename}.csv",
            mime='text/csv'
        )
    elif format_type == 'JSON':
        json_data = df.to_json(orient='records', indent=2)
        st.download_button(
            label="Download JSON",
            data=json_data,
            file_name=f"{filename}.json",
            mime='application/json'
        )
    elif format_type == 'PDF':
        # PDF export would require additional libraries like reportlab
        st.info("PDF export requires additional dependencies. Use CSV or JSON for now.")


def render_audit_compliance_report(audit_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Render audit compliance report with key metrics."""

    if not audit_data:
        st.warning("No audit data available for compliance reporting.")
        return {}

    df = pd.DataFrame(audit_data)

    st.markdown("### 📊 Audit Compliance Report")

    # Compliance metrics
    total_events = len(df)
    failed_events = len(df[df['status'] == 'failed'])
    critical_events = len(df[df['severity'] == 'critical'])

    success_rate = ((total_events - failed_events) / total_events) * 100 if total_events > 0 else 100
    compliance_score = 100 - (critical_events / total_events * 50) - (failed_events / total_events * 30)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Success Rate", ".1f", success_rate)

    with col2:
        st.metric("Compliance Score", ".1f", max(0, compliance_score))

    with col3:
        st.metric("Failed Events", failed_events)

    with col4:
        st.metric("Critical Events", critical_events)

    # Compliance status
    if compliance_score >= 90:
        st.success("✅ Excellent compliance - system operating normally")
    elif compliance_score >= 75:
        st.warning("⚠️ Good compliance - minor issues detected")
    elif compliance_score >= 60:
        st.error("🚨 Poor compliance - attention required")
    else:
        st.error("🚨 Critical compliance issues - immediate action needed")

    # Recent compliance trends
    st.markdown("#### 📈 Recent Trends")

    # Group by day for trend analysis
    df['date'] = pd.to_datetime(df['timestamp']).dt.date
    daily_stats = df.groupby('date').agg({
        'id': 'count',
        'status': lambda x: (x == 'failed').sum(),
        'severity': lambda x: (x == 'critical').sum()
    }).rename(columns={'id': 'total', 'status': 'failed', 'severity': 'critical'})

    if len(daily_stats) > 1:
        daily_stats['success_rate'] = ((daily_stats['total'] - daily_stats['failed']) / daily_stats['total']) * 100

        # Simple trend analysis
        recent_success = daily_stats['success_rate'].tail(7).mean()
        previous_success = daily_stats['success_rate'].head(-7).mean() if len(daily_stats) > 7 else recent_success

        trend = recent_success - previous_success

        if trend > 5:
            st.success(f"📈 Improving trend (+{trend:.1f}% success rate)")
        elif trend < -5:
            st.error(f"📉 Declining trend ({trend:.1f}% success rate)")
        else:
            st.info("📊 Stable compliance performance"
    return {
        'compliance_score': compliance_score,
        'success_rate': success_rate,
        'failed_events': failed_events,
        'critical_events': critical_events,
        'trend': trend if 'trend' in locals() else 0
    }


# Sample data generator for testing
def generate_sample_audit_data(count: int = 50) -> List[Dict[str, Any]]:
    """Generate sample audit data for testing."""
    event_types = ['login', 'logout', 'create', 'update', 'delete', 'access', 'error', 'security']
    severities = ['critical', 'high', 'medium', 'low', 'info']
    statuses = ['success', 'failed', 'warning', 'pending']
    users = ['alice', 'bob', 'charlie', 'diana', 'eve', 'frank', 'grace', 'henry']
    actions = ['create_simulation', 'update_config', 'delete_resource', 'access_dashboard', 'export_data']
    resources = ['simulation_001', 'config_file', 'user_database', 'dashboard', 'report_001']

    audit_events = []
    base_time = datetime.now() - timedelta(days=7)

    for i in range(count):
        timestamp = base_time + timedelta(
            days=np.random.randint(0, 7),
            hours=np.random.randint(0, 24),
            minutes=np.random.randint(0, 60)
        )

        severity = np.random.choice(severities, p=[0.05, 0.1, 0.3, 0.3, 0.25])
        status = np.random.choice(statuses, p=[0.7, 0.15, 0.1, 0.05])

        # Make critical events more likely to fail
        if severity == 'critical':
            status = np.random.choice(['failed', 'success'], p=[0.7, 0.3])

        event = {
            'id': f"audit_{i+1:05d}",
            'timestamp': timestamp,
            'event_type': np.random.choice(event_types),
            'user': np.random.choice(users),
            'action': np.random.choice(actions),
            'resource': np.random.choice(resources),
            'severity': severity,
            'status': status,
            'ip_address': f"192.168.1.{np.random.randint(1, 255)}",
            'user_agent': "Mozilla/5.0 (compatible; AuditBot/1.0)",
            'session_id': f"sess_{np.random.randint(1000, 9999)}"
        }
        audit_events.append(event)

    return audit_events
