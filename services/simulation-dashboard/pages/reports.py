"""Reports Page.

This module provides the reporting and analytics page with interactive
report generation and visualization capabilities.
"""

import streamlit as st
from typing import Dict, Any, List
from datetime import datetime


def render_reports_page():
    """Render the comprehensive reports and analytics page."""
    st.markdown("## 📋 Reports & Analytics")
    st.markdown("Generate comprehensive reports and view interactive analytics for your simulations.")

    # Create tabs for different report sections
    tab1, tab2, tab3 = st.tabs([
        "📊 Report Generation",
        "📈 Analytics Dashboard",
        "📋 Report History"
    ])

    with tab1:
        render_report_generation()

    with tab2:
        render_analytics_dashboard()

    with tab3:
        render_report_history()


def render_report_generation():
    """Render the report generation interface."""
    st.markdown("### 📊 Generate New Report")

    # Simulation selection
    simulations = get_available_simulations()

    if simulations:
        simulation_options = ["Select a simulation..."] + [
            f"{sim.get('id', 'Unknown')} - {sim.get('name', 'Unnamed')}"
            for sim in simulations
        ]

        selected_sim_option = st.selectbox(
            "Select Simulation",
            options=simulation_options,
            key="simulation_selector"
        )

        if selected_sim_option and selected_sim_option != "Select a simulation...":
            sim_id = selected_sim_option.split(" - ")[0]

            # Report type selection
            st.markdown("---")

            report_types = {
                "executive_summary": "Executive Summary",
                "technical_report": "Technical Report",
                "workflow_analysis": "Workflow Analysis",
                "quality_report": "Quality Assessment",
                "performance_report": "Performance Report",
                "financial_report": "Financial Impact",
                "comprehensive_analysis": "Comprehensive Analysis"
            }

            selected_report_types = st.multiselect(
                "Select Report Types",
                options=list(report_types.keys()),
                format_func=lambda x: report_types[x],
                default=["executive_summary"],
                help="Choose one or more report types to generate"
            )

            # Generate button
            if st.button("🚀 Generate Reports", type="primary", use_container_width=True):
                if selected_report_types:
                    generate_reports(sim_id, selected_report_types)
                else:
                    st.error("Please select at least one report type.")
    else:
        st.warning("No simulations available for reporting.")


def render_analytics_dashboard():
    """Render the analytics dashboard with interactive visualizations."""
    st.markdown("### 📈 Analytics Dashboard")

    # Get analytics data
    analytics_data = get_analytics_data()

    if not analytics_data:
        st.info("No analytics data available. Generate some reports first to see analytics.")
        return

    # Key metrics overview
    st.markdown("#### 📊 Key Performance Indicators")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_reports = len(analytics_data.get('reports', []))
        st.metric("Total Reports", total_reports)

    with col2:
        avg_quality = analytics_data.get('average_quality_score', 0) * 100
        st.metric("Avg Quality Score", ".1f")

    with col3:
        total_simulations = len(set(r.get('simulation_id', '') for r in analytics_data.get('reports', [])))
        st.metric("Simulations Analyzed", total_simulations)

    with col4:
        avg_execution_time = analytics_data.get('average_execution_time', 0)
        st.metric("Avg Execution Time", ".1f")

    # Interactive charts section
    st.markdown("---")
    st.markdown("#### 📈 Interactive Visualizations")

    st.info("Interactive charts and visualizations would be implemented here using Plotly and other visualization libraries.")


def render_report_history():
    """Render the report history and management interface."""
    st.markdown("### 📋 Report History")

    # Get report history from session state
    if 'report_history' not in st.session_state:
        st.session_state.report_history = []

    report_history = st.session_state.report_history

    if not report_history:
        st.info("No reports have been generated yet.")
        st.markdown("**💡 Tip:** Generate your first report using the Report Generation tab!")
        return

    # Display reports
    st.markdown(f"**Total Reports:** {len(report_history)}")

    for report in report_history[-10:]:  # Show last 10 reports
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])

            with col1:
                st.markdown(f"**{report.get('report_type', 'Unknown').replace('_', ' ').title()}**")
                st.caption(f"Simulation: {report.get('simulation_id', 'Unknown')}")

            with col2:
                st.caption(f"Generated: {report.get('generated_at', 'Unknown')[:19]}")

            with col3:
                if st.button("👁️ View", key=f"view_{report.get('simulation_id')}_{report.get('report_type')}"):
                    view_report_details(report)

            st.markdown("---")


# Helper functions

def get_available_simulations() -> List[Dict[str, Any]]:
    """Get list of available simulations for reporting."""
    # Mock data - in real implementation, this would call the simulation service
    return [
        {
            'id': 'sim_001',
            'name': 'E-commerce Platform Development',
            'status': 'completed',
            'created_at': '2024-01-15T10:00:00Z'
        },
        {
            'id': 'sim_002',
            'name': 'Mobile App Development',
            'status': 'completed',
            'created_at': '2024-01-14T15:30:00Z'
        },
        {
            'id': 'sim_003',
            'name': 'API Service Implementation',
            'status': 'running',
            'created_at': '2024-01-15T08:45:00Z'
        }
    ]


def generate_reports(simulation_id: str, report_types: List[str]):
    """Generate reports for the selected simulation."""
    try:
        with st.spinner("Generating reports... This may take a few moments."):
            import time

            for report_type in report_types:
                # Simulate report generation time
                time.sleep(0.5)

                # Mock successful report generation
                report_data = {
                    'simulation_id': simulation_id,
                    'report_type': report_type,
                    'generated_at': datetime.now().isoformat(),
                    'status': 'completed',
                    'quality_score': 0.85,
                    'execution_time_seconds': 120.5,
                    'documents_generated': 12,
                    'workflows_executed': 8,
                    'consistency_score': 0.78,
                    'success_rate': 0.95
                }

                # Add to history
                if 'report_history' not in st.session_state:
                    st.session_state.report_history = []

                st.session_state.report_history.append(report_data)

        # Success message
        st.success(f"✅ Successfully generated {len(report_types)} reports!")

        # Display generated reports
        with st.expander("📋 Generated Reports", expanded=True):
            for report_type in report_types:
                st.write(f"• {report_type.replace('_', ' ').title()} - Generated at {datetime.now().isoformat()[:19]}")

    except Exception as e:
        st.error(f"❌ Failed to generate reports: {str(e)}")


def get_analytics_data() -> Dict[str, Any]:
    """Get analytics data from generated reports."""
    reports = st.session_state.get('report_history', [])

    if not reports:
        return {}

    # Calculate analytics
    analytics = {
        'reports': reports,
        'total_reports': len(reports),
        'average_quality_score': 0.0,
        'average_execution_time': 0.0,
        'report_types_count': {},
        'simulations_analyzed': set()
    }

    quality_scores = []
    execution_times = []

    for report in reports:
        # Quality scores
        if 'quality_score' in report:
            quality_scores.append(report['quality_score'])

        # Execution times
        if 'execution_time_seconds' in report:
            execution_times.append(report['execution_time_seconds'])

        # Report types
        report_type = report.get('report_type', 'unknown')
        analytics['report_types_count'][report_type] = analytics['report_types_count'].get(report_type, 0) + 1

        # Simulations
        analytics['simulations_analyzed'].add(report.get('simulation_id', 'unknown'))

    # Calculate averages
    if quality_scores:
        analytics['average_quality_score'] = sum(quality_scores) / len(quality_scores)

    if execution_times:
        analytics['average_execution_time'] = sum(execution_times) / len(execution_times)

    analytics['simulations_analyzed'] = len(analytics['simulations_analyzed'])

    return analytics


def view_report_details(report: Dict[str, Any]):
    """Display detailed view of a report."""
    st.markdown("### 📄 Report Details")

    # Basic information
    st.write(f"**Simulation ID:** {report.get('simulation_id', 'Unknown')}")
    st.write(f"**Report Type:** {report.get('report_type', 'Unknown').replace('_', ' ').title()}")
    st.write(f"**Generated:** {report.get('generated_at', 'Unknown')}")
    st.write(f"**Status:** {report.get('status', 'Unknown').title()}")

    # Report metrics
    if 'quality_score' in report:
        st.metric("Quality Score", ".1%")

    if 'execution_time_seconds' in report:
        st.metric("Execution Time", ".1f")

    if 'documents_generated' in report:
        st.metric("Documents Generated", report['documents_generated'])