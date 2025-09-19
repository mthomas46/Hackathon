"""Audit Trail System Page.

This module provides comprehensive auditing capabilities for simulation operations,
including event tracking, compliance reporting, and audit trail management.
"""

import streamlit as st
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from services.clients.simulation_client import SimulationClient
from infrastructure.config.config import get_config


def render_audit_page():
    """Render the comprehensive audit trail system page."""
    st.markdown("## 🔍 Audit Trail System")
    st.markdown("Comprehensive auditing, compliance tracking, and security monitoring for simulation operations.")

    # Initialize session state
    initialize_audit_state()

    # Create tabs for different audit aspects
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Audit Log",
        "🔍 Event Analysis",
        "📊 Compliance Reports",
        "⚙️ Audit Configuration"
    ])

    with tab1:
        render_audit_log()

    with tab2:
        render_event_analysis()

    with tab3:
        render_compliance_reports()

    with tab4:
        render_audit_configuration()


def initialize_audit_state():
    """Initialize session state for audit page."""
    if 'audit_filters' not in st.session_state:
        st.session_state.audit_filters = {
            'event_types': [],
            'users': [],
            'simulations': [],
            'date_range': None,
            'severity_levels': [],
            'compliance_categories': []
        }

    if 'audit_events' not in st.session_state:
        st.session_state.audit_events = []

    if 'audit_configuration' not in st.session_state:
        st.session_state.audit_configuration = {
            'retention_days': 90,
            'enable_compliance_mode': True,
            'audit_critical_operations': True,
            'log_system_events': True,
            'alert_on_suspicious_activity': True
        }


def render_audit_log():
    """Render the audit log viewer with advanced filtering."""
    st.markdown("### 📋 Audit Log Viewer")
    st.markdown("Comprehensive view of all simulation operations and system events.")

    # Quick stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_events = len(get_audit_events())
        st.metric("Total Events", total_events)

    with col2:
        today_events = len([e for e in get_audit_events()
                           if e.get('timestamp', '').startswith(datetime.now().strftime("%Y-%m-%d"))])
        st.metric("Today's Events", today_events)

    with col3:
        critical_events = len([e for e in get_audit_events()
                              if e.get('severity') == 'critical'])
        st.metric("Critical Events", critical_events)

    with col4:
        compliance_events = len([e for e in get_audit_events()
                                if e.get('compliance_category')])
        st.metric("Compliance Events", compliance_events)

    # Advanced filters
    st.markdown("#### 🔍 Advanced Filters")

    with st.expander("Filter Options", expanded=False):
        render_audit_filters()

    # Audit log display
    st.markdown("#### 📝 Audit Events")

    filtered_events = get_filtered_audit_events()
    render_audit_events_table(filtered_events)

    # Export options
    st.markdown("#### 📤 Export Options")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📄 Export as CSV", key="export_audit_csv"):
            export_audit_events(filtered_events, "csv")

    with col2:
        if st.button("📊 Export as JSON", key="export_audit_json"):
            export_audit_events(filtered_events, "json")

    with col3:
        if st.button("📋 Generate Report", key="generate_audit_report"):
            generate_audit_report(filtered_events)


def render_event_analysis():
    """Render event analysis and insights."""
    st.markdown("### 🔍 Event Analysis")
    st.markdown("Advanced analysis of audit events with patterns and insights.")

    events = get_filtered_audit_events()

    if not events:
        st.info("No audit events available for analysis.")
        return

    # Analysis overview
    st.markdown("#### 📊 Event Analysis Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        event_types = len(set(e.get('event_type', 'Unknown') for e in events))
        st.metric("Event Types", event_types)

    with col2:
        users = len(set(e.get('user', 'system') for e in events))
        st.metric("Active Users", users)

    with col3:
        avg_events_per_day = len(events) / max(1, (datetime.now() - get_earliest_event_date(events)).days)
        st.metric("Avg Events/Day", ".1f")

    with col4:
        suspicious_events = len([e for e in events if e.get('severity') in ['high', 'critical']])
        st.metric("Suspicious Events", suspicious_events)

    # Event type distribution
    st.markdown("#### 📈 Event Type Distribution")
    render_event_type_chart(events)

    # Timeline analysis
    st.markdown("#### ⏰ Event Timeline")
    render_event_timeline_chart(events)

    # User activity analysis
    st.markdown("#### 👥 User Activity Analysis")
    render_user_activity_chart(events)

    # Pattern detection
    st.markdown("#### 🔍 Pattern Detection")
    render_pattern_analysis(events)

    # Anomaly detection
    st.markdown("#### ⚠️ Anomaly Detection")
    render_anomaly_detection(events)


def render_compliance_reports():
    """Render compliance reporting and tracking."""
    st.markdown("### 📊 Compliance Reports")
    st.markdown("Generate and view compliance reports for regulatory requirements.")

    # Compliance overview
    st.markdown("#### 📋 Compliance Overview")

    compliance_data = get_compliance_data()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        compliance_score = compliance_data.get('overall_score', 0)
        st.metric("Compliance Score", ".1f")

    with col2:
        policies_enforced = compliance_data.get('policies_enforced', 0)
        st.metric("Policies Enforced", policies_enforced)

    with col3:
        violations = compliance_data.get('violations', 0)
        st.metric("Policy Violations", violations)

    with col4:
        last_audit = compliance_data.get('last_audit', 'Never')
        st.metric("Last Audit", last_audit)

    # Compliance categories
    st.markdown("#### 🏷️ Compliance Categories")
    render_compliance_categories(compliance_data)

    # Regulatory reports
    st.markdown("#### 📄 Regulatory Reports")

    report_types = [
        "GDPR Compliance Report",
        "SOX Compliance Report",
        "PCI DSS Compliance Report",
        "ISO 27001 Compliance Report",
        "HIPAA Compliance Report",
        "Custom Compliance Report"
    ]

    selected_report = st.selectbox(
        "Select Report Type",
        options=report_types,
        key="compliance_report_type"
    )

    if st.button("📋 Generate Compliance Report", key="generate_compliance_report"):
        generate_compliance_report(selected_report)

    # Audit trail verification
    st.markdown("#### 🔒 Audit Trail Integrity")
    render_audit_integrity_check()


def render_audit_configuration():
    """Render audit configuration and settings."""
    st.markdown("### ⚙️ Audit Configuration")
    st.markdown("Configure audit policies, retention settings, and monitoring rules.")

    # Audit policies
    st.markdown("#### 📋 Audit Policies")

    with st.expander("Audit Policy Settings", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Event Logging**")
            enable_detailed_logging = st.checkbox(
                "Enable Detailed Event Logging",
                value=st.session_state.audit_configuration.get('enable_detailed_logging', True),
                key="enable_detailed_logging"
            )

            audit_admin_actions = st.checkbox(
                "Audit Administrative Actions",
                value=st.session_state.audit_configuration.get('audit_admin_actions', True),
                key="audit_admin_actions"
            )

            log_failed_authentications = st.checkbox(
                "Log Failed Authentication Attempts",
                value=st.session_state.audit_configuration.get('log_failed_authentications', True),
                key="log_failed_authentications"
            )

        with col2:
            st.markdown("**Data Retention**")
            retention_days = st.slider(
                "Audit Log Retention (days)",
                min_value=30,
                max_value=365,
                value=st.session_state.audit_configuration.get('retention_days', 90),
                key="retention_days"
            )

            compress_old_logs = st.checkbox(
                "Compress Old Audit Logs",
                value=st.session_state.audit_configuration.get('compress_old_logs', True),
                key="compress_old_logs"
            )

    # Alert configuration
    st.markdown("#### 🚨 Alert Configuration")

    with st.expander("Alert Settings", expanded=False):
        alert_on_critical_events = st.checkbox(
            "Alert on Critical Events",
            value=st.session_state.audit_configuration.get('alert_on_critical_events', True),
            key="alert_on_critical_events"
        )

        alert_on_policy_violations = st.checkbox(
            "Alert on Policy Violations",
            value=st.session_state.audit_configuration.get('alert_on_policy_violations', True),
            key="alert_on_policy_violations"
        )

        alert_threshold = st.slider(
            "Alert Threshold (events per hour)",
            min_value=1,
            max_value=100,
            value=st.session_state.audit_configuration.get('alert_threshold', 10),
            key="alert_threshold"
        )

    # Compliance settings
    st.markdown("#### 🏛️ Compliance Settings")

    with st.expander("Compliance Configuration", expanded=False):
        enable_compliance_mode = st.checkbox(
            "Enable Compliance Mode",
            value=st.session_state.audit_configuration.get('enable_compliance_mode', True),
            key="enable_compliance_mode"
        )

        require_audit_approval = st.checkbox(
            "Require Audit Approval for Critical Operations",
            value=st.session_state.audit_configuration.get('require_audit_approval', False),
            key="require_audit_approval"
        )

        encryption_enabled = st.checkbox(
            "Enable Audit Log Encryption",
            value=st.session_state.audit_configuration.get('encryption_enabled', True),
            key="encryption_enabled"
        )

    # Save configuration
    if st.button("💾 Save Audit Configuration", key="save_audit_config", type="primary"):
        save_audit_configuration()


# Helper functions

def get_audit_events() -> List[Dict[str, Any]]:
    """Get audit events from the system."""
    # Mock audit events - in real implementation, this would fetch from audit service
    base_time = datetime.now() - timedelta(days=7)

    audit_events = []
    event_types = [
        "simulation_created", "simulation_started", "simulation_completed",
        "user_login", "user_logout", "permission_changed",
        "data_exported", "configuration_changed", "security_alert",
        "compliance_check", "audit_review"
    ]

    severities = ["low", "medium", "high", "critical"]
    users = ["admin", "user1", "user2", "system", "auditor"]

    for i in range(100):  # Generate 100 mock events
        event_time = base_time + timedelta(minutes=i * 15)

        audit_events.append({
            "id": f"audit_{i+1}",
            "event_type": event_types[i % len(event_types)],
            "timestamp": event_time.isoformat(),
            "user": users[i % len(users)],
            "simulation_id": f"sim_{(i % 10) + 1}",
            "severity": severities[i % len(severities)],
            "description": f"Event {i+1} description",
            "ip_address": f"192.168.1.{(i % 255) + 1}",
            "user_agent": "Mozilla/5.0 (compatible)",
            "compliance_category": "GDPR" if i % 5 == 0 else None,
            "metadata": {
                "session_id": f"session_{i % 10}",
                "operation_id": f"op_{i+1}"
            }
        })

    return audit_events


def render_audit_filters():
    """Render advanced audit filters."""
    col1, col2, col3 = st.columns(3)

    with col1:
        event_types = st.multiselect(
            "Event Types",
            options=["simulation_created", "simulation_started", "user_login", "security_alert", "all"],
            default=st.session_state.audit_filters.get('event_types', []),
            key="audit_event_types"
        )

    with col2:
        users = st.multiselect(
            "Users",
            options=["admin", "user1", "user2", "system", "all"],
            default=st.session_state.audit_filters.get('users', []),
            key="audit_users"
        )

    with col3:
        severities = st.multiselect(
            "Severity Levels",
            options=["low", "medium", "high", "critical"],
            default=st.session_state.audit_filters.get('severity_levels', []),
            key="audit_severities"
        )

    # Date range filter
    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=7),
            key="audit_start_date"
        )

    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now(),
            key="audit_end_date"
        )

    # Apply filters
    if st.button("🔍 Apply Filters", key="apply_audit_filters"):
        st.session_state.audit_filters.update({
            'event_types': event_types,
            'users': users,
            'severities': severities,
            'date_range': (start_date, end_date)
        })
        st.success("Filters applied successfully!")
        st.rerun()


def get_filtered_audit_events() -> List[Dict[str, Any]]:
    """Get audit events filtered by current criteria."""
    events = get_audit_events()
    filters = st.session_state.audit_filters

    filtered_events = events

    # Filter by event types
    if filters.get('event_types') and 'all' not in filters['event_types']:
        filtered_events = [e for e in filtered_events if e.get('event_type') in filters['event_types']]

    # Filter by users
    if filters.get('users') and 'all' not in filters['users']:
        filtered_events = [e for e in filtered_events if e.get('user') in filters['users']]

    # Filter by severity
    if filters.get('severities'):
        filtered_events = [e for e in filtered_events if e.get('severity') in filters['severities']]

    # Filter by date range
    if filters.get('date_range'):
        start_date, end_date = filters['date_range']
        filtered_events = [e for e in filtered_events
                          if start_date <= datetime.fromisoformat(e['timestamp'][:10]).date() <= end_date]

    return filtered_events


def render_audit_events_table(events: List[Dict[str, Any]]):
    """Render audit events in a table format."""
    if not events:
        st.info("No audit events match the current filters.")
        return

    # Create table data
    table_data = []
    for event in events[-50:]:  # Show last 50 events
        table_data.append({
            "Time": event['timestamp'][:19],
            "Event Type": event['event_type'].replace('_', ' ').title(),
            "User": event['user'],
            "Severity": event['severity'].title(),
            "Description": event['description'][:50] + "..." if len(event['description']) > 50 else event['description']
        })

    # Display as dataframe
    import pandas as pd
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True)

    # Pagination info
    total_events = len(events)
    st.caption(f"Showing {min(50, len(table_data))} of {total_events} events")


def render_event_type_chart(events: List[Dict[str, Any]]):
    """Render event type distribution chart."""
    event_counts = {}
    for event in events:
        event_type = event.get('event_type', 'Unknown')
        event_counts[event_type] = event_counts.get(event_type, 0) + 1

    if event_counts:
        fig = px.pie(
            values=list(event_counts.values()),
            names=list(event_counts.keys()),
            title="Event Type Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)


def render_event_timeline_chart(events: List[Dict[str, Any]]):
    """Render event timeline chart."""
    timeline_data = []
    for event in events[-100:]:  # Last 100 events
        try:
            timestamp = datetime.fromisoformat(event['timestamp'])
            timeline_data.append({
                'time': timestamp,
                'event_type': event['event_type'],
                'severity': event['severity']
            })
        except:
            continue

    if timeline_data:
        import pandas as pd
        df = pd.DataFrame(timeline_data)

        fig = px.scatter(
            df,
            x='time',
            y='event_type',
            color='severity',
            title="Event Timeline",
            color_discrete_map={
                'low': 'green',
                'medium': 'yellow',
                'high': 'orange',
                'critical': 'red'
            }
        )
        st.plotly_chart(fig, use_container_width=True)


def render_user_activity_chart(events: List[Dict[str, Any]]):
    """Render user activity analysis chart."""
    user_activity = {}
    for event in events:
        user = event.get('user', 'unknown')
        user_activity[user] = user_activity.get(user, 0) + 1

    if user_activity:
        fig = px.bar(
            x=list(user_activity.keys()),
            y=list(user_activity.values()),
            title="User Activity Summary",
            labels={'x': 'User', 'y': 'Number of Events'}
        )
        st.plotly_chart(fig, use_container_width=True)


def render_pattern_analysis(events: List[Dict[str, Any]]):
    """Render pattern analysis for audit events."""
    # Simple pattern detection
    patterns = []

    # Look for repeated events from same user
    user_events = {}
    for event in events:
        user = event.get('user', 'unknown')
        event_type = event.get('event_type', 'unknown')
        key = f"{user}_{event_type}"
        user_events[key] = user_events.get(key, 0) + 1

    # Find patterns with high frequency
    for key, count in user_events.items():
        if count > 5:  # More than 5 events of same type from same user
            user, event_type = key.split('_', 1)
            patterns.append({
                'pattern': f"High frequency: {user} - {event_type}",
                'count': count,
                'severity': 'medium'
            })

    if patterns:
        st.markdown("**Detected Patterns:**")
        for pattern in patterns:
            severity_icon = {'low': '🟢', 'medium': '🟡', 'high': '🔴'}.get(pattern['severity'], '⚪')
            st.write(f"{severity_icon} {pattern['pattern']} ({pattern['count']} occurrences)")
    else:
        st.info("No significant patterns detected.")


def render_anomaly_detection(events: List[Dict[str, Any]]):
    """Render anomaly detection analysis."""
    # Simple anomaly detection
    anomalies = []

    # Check for events outside normal hours (assuming 9-5 business hours)
    for event in events:
        try:
            timestamp = datetime.fromisoformat(event['timestamp'])
            hour = timestamp.hour
            if hour < 9 or hour > 17:  # Outside business hours
                anomalies.append({
                    'type': 'Out of hours activity',
                    'event': event,
                    'reason': f"Event at {hour}:00 (outside 9-17 business hours)"
                })
        except:
            continue

    # Check for rapid successive events (potential automation or attack)
    events_by_minute = {}
    for event in events:
        try:
            timestamp = datetime.fromisoformat(event['timestamp'])
            minute_key = timestamp.strftime("%Y-%m-%d %H:%M")
            events_by_minute[minute_key] = events_by_minute.get(minute_key, 0) + 1
        except:
            continue

    for minute_key, count in events_by_minute.items():
        if count > 10:  # More than 10 events per minute
            anomalies.append({
                'type': 'High frequency activity',
                'event': minute_key,
                'reason': f"{count} events in one minute"
            })

    if anomalies:
        st.markdown("**Detected Anomalies:**")
        for anomaly in anomalies[:10]:  # Show first 10
            st.warning(f"⚠️ {anomaly['type']}: {anomaly['reason']}")
    else:
        st.success("✅ No anomalies detected in the audit trail.")


def get_compliance_data() -> Dict[str, Any]:
    """Get compliance data and metrics."""
    # Mock compliance data
    return {
        'overall_score': 94.2,
        'policies_enforced': 15,
        'violations': 2,
        'last_audit': '2024-01-16',
        'categories': {
            'GDPR': {'score': 96.5, 'violations': 0},
            'SOX': {'score': 92.1, 'violations': 1},
            'ISO27001': {'score': 95.8, 'violations': 0},
            'PCI DSS': {'score': 93.7, 'violations': 1}
        }
    }


def render_compliance_categories(compliance_data: Dict[str, Any]):
    """Render compliance categories overview."""
    categories = compliance_data.get('categories', {})

    if categories:
        for category, data in categories.items():
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.write(f"**{category}**")

            with col2:
                score = data.get('score', 0)
                st.metric("Score", ".1f")

            with col3:
                violations = data.get('violations', 0)
                if violations == 0:
                    st.success("✅ Compliant")
                else:
                    st.error(f"❌ {violations} violations")


def generate_compliance_report(report_type: str):
    """Generate a compliance report."""
    # Mock report generation
    st.success(f"✅ {report_type} generated successfully!")

    # Mock report content
    report_content = f"""
    # {report_type}

    ## Executive Summary
    This compliance report was generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.

    ## Key Findings
    - Overall compliance score: 94.2%
    - Total policies enforced: 15
    - Policy violations: 2
    - Last audit: 2024-01-16

    ## Recommendations
    1. Address identified policy violations
    2. Implement additional monitoring controls
    3. Regular compliance audits
    4. Staff training on compliance requirements
    """

    st.code(report_content, language="markdown")

    # Download button
    st.download_button(
        label="📥 Download Full Report",
        data=report_content,
        file_name=f"{report_type.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown",
        key="download_compliance_report"
    )


def render_audit_integrity_check():
    """Render audit trail integrity verification."""
    st.markdown("#### 🔍 Integrity Check Results")

    # Mock integrity check results
    integrity_results = {
        'log_integrity': 'verified',
        'tamper_detection': 'no_tampering_detected',
        'chain_verification': 'intact',
        'encryption_status': 'encrypted',
        'backup_status': 'current'
    }

    for check, status in integrity_results.items():
        col1, col2 = st.columns([3, 1])

        with col1:
            st.write(f"**{check.replace('_', ' ').title()}**")

        with col2:
            if status in ['verified', 'no_tampering_detected', 'intact', 'encrypted', 'current']:
                st.success("✅")
            else:
                st.error("❌")


def export_audit_events(events: List[Dict[str, Any]], format: str):
    """Export audit events in specified format."""
    try:
        if format == "csv":
            # Convert to CSV
            import pandas as pd
            df = pd.DataFrame(events)
            csv_data = df.to_csv(index=False)

            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"audit_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_audit_csv"
            )

        elif format == "json":
            # Convert to JSON
            json_data = json.dumps(events, indent=2, default=str)

            st.download_button(
                label="📥 Download JSON",
                data=json_data,
                file_name=f"audit_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                key="download_audit_json"
            )

        st.success(f"✅ Audit events exported as {format.upper()}!")

    except Exception as e:
        st.error(f"❌ Failed to export audit events: {str(e)}")


def generate_audit_report(events: List[Dict[str, Any]]):
    """Generate a comprehensive audit report."""
    try:
        # Mock report generation
        report_summary = f"""
        # Audit Report Summary

        Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        Total Events: {len(events)}
        Date Range: {get_earliest_event_date(events)} to {datetime.now().date()}

        ## Event Statistics
        - Total Events: {len(events)}
        - Unique Users: {len(set(e.get('user', 'unknown') for e in events))}
        - Event Types: {len(set(e.get('event_type', 'unknown') for e in events))}
        - Critical Events: {len([e for e in events if e.get('severity') == 'critical'])}

        ## Key Findings
        1. System activity is within normal parameters
        2. No security violations detected
        3. All compliance requirements met
        4. Audit trail integrity verified
        """

        st.success("✅ Audit report generated successfully!")
        st.code(report_summary, language="markdown")

    except Exception as e:
        st.error(f"❌ Failed to generate audit report: {str(e)}")


def get_earliest_event_date(events: List[Dict[str, Any]]) -> datetime.date:
    """Get the earliest event date from audit events."""
    if not events:
        return datetime.now().date()

    earliest = datetime.now()
    for event in events:
        try:
            event_date = datetime.fromisoformat(event.get('timestamp', '')[:19])
            if event_date < earliest:
                earliest = event_date
        except:
            continue

    return earliest.date()


def save_audit_configuration():
    """Save audit configuration settings."""
    try:
        # Update session state with new configuration
        st.session_state.audit_configuration.update({
            'retention_days': st.session_state.get('retention_days', 90),
            'enable_compliance_mode': st.session_state.get('enable_compliance_mode', True),
            'alert_on_critical_events': st.session_state.get('alert_on_critical_events', True),
            'alert_on_policy_violations': st.session_state.get('alert_on_policy_violations', True),
            'alert_threshold': st.session_state.get('alert_threshold', 10),
            'require_audit_approval': st.session_state.get('require_audit_approval', False),
            'encryption_enabled': st.session_state.get('encryption_enabled', True)
        })

        st.success("✅ Audit configuration saved successfully!")

    except Exception as e:
        st.error(f"❌ Failed to save audit configuration: {str(e)}")
