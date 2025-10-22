"""
Timeline Analysis Dashboard

Comprehensive dashboard for Timeline Analysis features:
- Timeline management and visualization
- Temporal RAG queries
- Quality monitoring
- Gap and drift detection
- Real-time analytics
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any


def show(api_base_url: str):
    """Show the Timeline Analysis dashboard."""
    st.title("📊 Timeline Analysis Dashboard")
    st.markdown("---")
    
    # Store API URL in session state for helper functions
    if 'api_base_url' not in st.session_state:
        st.session_state.api_base_url = api_base_url
    
    # Create tabs for different features
    tabs = st.tabs([
        "🗓️ Timelines",
        "⏰ Temporal Queries",
        "📊 Quality Dashboard",
        "🔍 Gap Analysis",
        "🔄 Drift Detection",
        "📤 Export"
    ])
    
    with tabs[0]:
        render_timelines_tab()
    
    with tabs[1]:
        render_temporal_rag_tab()
    
    with tabs[2]:
        render_quality_tab()
    
    with tabs[3]:
        render_gap_analysis_tab()
    
    with tabs[4]:
        render_drift_detection_tab()
    
    with tabs[5]:
        render_export_tab()


# =============================================================================
# Timeline Management Tab
# =============================================================================

def render_timelines_tab():
    """Render timeline management interface."""
    st.header("Timeline Management")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📋 Existing Timelines")
        
        # Fetch timelines
        timelines = fetch_timelines()
        
        if timelines:
            for timeline in timelines[:10]:  # Show first 10
                with st.expander(f"📅 {timeline['name']} ({timeline['service_name']})"):
                    display_timeline_details(timeline)
        else:
            st.info("No timelines found. Create one to get started!")
    
    with col2:
        st.subheader("➕ Create Timeline")
        
        with st.form("create_timeline_form"):
            name = st.text_input("Timeline Name*", placeholder="Q1 2025 Documentation")
            service_name = st.text_input("Service Name*", placeholder="ecosystem-mcp")
            repo_path = st.text_input("Repository Path*", placeholder="/path/to/repo")
            
            col_dates1, col_dates2 = st.columns(2)
            with col_dates1:
                start_date = st.date_input("Start Date", value=datetime(2025, 1, 1))
            with col_dates2:
                end_date = st.date_input("End Date", value=datetime(2025, 12, 31))
            
            period_strategy = st.selectbox(
                "Period Strategy",
                ["monthly", "quarterly", "adaptive"],
                help="How to divide the timeline into periods"
            )
            
            description = st.text_area("Description (optional)")
            
            submitted = st.form_submit_button("🚀 Create Timeline", use_container_width=True)
            
            if submitted:
                if not all([name, service_name, repo_path]):
                    st.error("Please fill in all required fields!")
                else:
                    create_timeline(name, service_name, repo_path, start_date, end_date, period_strategy, description)


def fetch_timelines(service_name: Optional[str] = None) -> List[Dict]:
    """Fetch timelines from API."""
    try:
        api_base_url = st.session_state.get('api_base_url', 'http://localhost:8000')
        params = {}
        if service_name:
            params['service_name'] = service_name
        
        response = requests.get(f"{api_base_url}/api/v1/timelines", params=params, timeout=10)
        
        if response.status_code == 200:
            return response.json().get('timelines', [])
        return []
    except Exception as e:
        st.error(f"Error fetching timelines: {e}")
        return []


def display_timeline_details(timeline: Dict):
    """Display detailed timeline information."""
    # Timeline info
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Confidence", timeline.get('confidence_level', 'N/A'))
    with col2:
        st.metric("Periods", timeline.get('period_count', 0))
    with col3:
        st.metric("Documents", timeline.get('document_count', 0))
    
    # Timeline visualization
    if timeline.get('periods'):
        render_timeline_chart(timeline)
    
    # Actions
    col_act1, col_act2, col_act3 = st.columns(3)
    
    with col_act1:
        if st.button("📊 View Details", key=f"view_{timeline['id']}"):
            view_timeline_details(timeline['id'])
    
    with col_act2:
        if st.button("🔄 Refresh", key=f"refresh_{timeline['id']}"):
            refresh_timeline(timeline['id'])
    
    with col_act3:
        if st.button("📤 Export", key=f"export_{timeline['id']}"):
            export_timeline(timeline['id'])


def render_timeline_chart(timeline: Dict):
    """Render timeline visualization."""
    periods = timeline.get('periods', [])
    
    if not periods:
        return
    
    # Create Gantt-style chart
    fig = go.Figure()
    
    for i, period in enumerate(periods):
        fig.add_trace(go.Bar(
            name=period['name'],
            x=[period['document_count']],
            y=[period['name']],
            orientation='h',
            marker=dict(
                color=period['document_count'],
                colorscale='Viridis',
                showscale=False
            ),
            text=f"{period['document_count']} docs",
            textposition='auto',
        ))
    
    fig.update_layout(
        title="Documents per Period",
        xaxis_title="Document Count",
        yaxis_title="Period",
        height=200,
        showlegend=False,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def create_timeline(name, service_name, repo_path, start_date, end_date, period_strategy, description):
    """Create a new timeline."""
    try:
        api_base_url = st.session_state.get('api_base_url', 'http://localhost:8000')
        payload = {
            "name": name,
            "service_name": service_name,
            "repo_path": repo_path,
            "start_date": start_date.isoformat() + "T00:00:00Z",
            "end_date": end_date.isoformat() + "T23:59:59Z",
            "period_strategy": period_strategy,
            "description": description or ""
        }
        
        response = requests.post(f"{api_base_url}/api/v1/timelines", json=payload, timeout=30)
        
        if response.status_code == 201:
            st.success(f"✅ Timeline '{name}' created successfully!")
            st.rerun()
        else:
            st.error(f"Failed to create timeline: {response.text}")
    except Exception as e:
        st.error(f"Error creating timeline: {e}")


# =============================================================================
# Temporal RAG Tab
# =============================================================================

def render_temporal_rag_tab():
    """Render temporal RAG query interface."""
    st.header("⏰ Temporal RAG Queries")
    st.markdown("Query documentation as it existed at any point in time.")
    
    # Query type selector
    query_type = st.radio(
        "Query Type",
        ["Time-Travel Query", "Evolution Tracking", "Period Comparison"],
        horizontal=True
    )
    
    if query_type == "Time-Travel Query":
        render_time_travel_query()
    elif query_type == "Evolution Tracking":
        render_evolution_query()
    else:
        render_comparison_query()


def render_time_travel_query():
    """Render time-travel query interface."""
    st.subheader("🕐 Time-Travel Query")
    st.caption("Ask questions about documentation as it existed at a specific date")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        question = st.text_area(
            "Your Question",
            placeholder="What did the API documentation say about authentication?",
            height=100
        )
    
    with col2:
        as_of_date = st.date_input(
            "As of Date",
            value=datetime.now() - timedelta(days=30)
        )
        
        service_name = st.text_input(
            "Service (optional)",
            placeholder="ecosystem-mcp"
        )
        
        limit = st.slider("Max Results", 1, 20, 10)
    
    if st.button("🔍 Query", use_container_width=True, type="primary"):
        if question:
            execute_time_travel_query(question, as_of_date, service_name, limit)
        else:
            st.warning("Please enter a question!")


def execute_time_travel_query(question, as_of_date, service_name, limit):
    """Execute time-travel query."""
    with st.spinner("Querying temporal database..."):
        try:
            api_base_url = st.session_state.get('api_base_url', 'http://localhost:8000')
            payload = {
                "question": question,
                "as_of_date": as_of_date.isoformat() + "T00:00:00Z",
                "limit": limit
            }
            
            if service_name:
                payload["service_name"] = service_name
            
            response = requests.post(
                f"{api_base_url}/api/v1/rag/temporal/query",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                display_temporal_query_result(result)
            else:
                st.error(f"Query failed: {response.text}")
        except Exception as e:
            st.error(f"Error executing query: {e}")


def display_temporal_query_result(result: Dict):
    """Display temporal query results."""
    st.success("✅ Query completed!")
    
    # Show temporal context
    if result.get('temporal_context'):
        context = result['temporal_context']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Timeline", context.get('timeline_name', 'N/A'))
        with col2:
            st.metric("Period", context.get('period_name', 'N/A'))
        with col3:
            st.metric("Confidence", context.get('confidence_level', 'N/A'))
        
        if context.get('period_range'):
            st.info(f"📅 Period: {context['period_range']['start']} to {context['period_range']['end']}")
    
    # Display results
    st.subheader("📄 Results")
    
    results = result.get('results', [])
    
    if results:
        for i, doc in enumerate(results, 1):
            with st.expander(f"Result {i}: {doc.get('file_path', 'Unknown')} (Score: {doc.get('score', 0):.2f})"):
                st.markdown(doc.get('content', 'No content available'))
                
                if doc.get('metadata'):
                    st.caption(f"📝 {doc['metadata']}")
    else:
        st.warning("No results found for this query.")


def render_evolution_query():
    """Render evolution tracking interface."""
    st.subheader("📈 Evolution Tracking")
    st.caption("Track how a topic evolved over time")
    
    topic = st.text_input("Topic to Track", placeholder="API authentication approach")
    
    # Timeline selector would go here
    st.info("💡 Timeline selector coming soon - for now, evolution queries work with default timelines")
    
    if st.button("📈 Track Evolution", use_container_width=True, type="primary"):
        if topic:
            st.info("Evolution tracking feature ready - API endpoint available at /api/v1/rag/temporal/evolution")
        else:
            st.warning("Please enter a topic!")


def render_comparison_query():
    """Render comparison query interface."""
    st.subheader("⚖️ Period Comparison")
    st.caption("Compare information between two time periods")
    
    question = st.text_area("What to Compare", placeholder="API authentication methods")
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=90))
    with col2:
        end_date = st.date_input("End Date", value=datetime.now())
    
    if st.button("⚖️ Compare", use_container_width=True, type="primary"):
        if question:
            st.info("Comparison feature ready - API endpoint available at /api/v1/rag/temporal/comparison")
        else:
            st.warning("Please enter a comparison query!")


# =============================================================================
# Quality Dashboard Tab
# =============================================================================

def render_quality_tab():
    """Render quality monitoring dashboard."""
    st.header("📊 Quality Dashboard")
    
    # Service selector
    service_name = st.text_input("Service Name", value="ecosystem-mcp")
    
    if st.button("📊 Analyze Quality", type="primary"):
        analyze_quality(service_name)


def analyze_quality(service_name: str):
    """Analyze and display quality metrics."""
    with st.spinner("Analyzing documentation quality..."):
        try:
            api_base_url = st.session_state.get('api_base_url', 'http://localhost:8000')
            response = requests.get(
                f"{api_base_url}/api/v1/maintenance/quality/overview",
                params={"service_name": service_name},
                timeout=30
            )
            
            if response.status_code == 200:
                quality_data = response.json()
                display_quality_dashboard(quality_data)
            else:
                st.error(f"Failed to fetch quality data: {response.text}")
        except Exception as e:
            st.error(f"Error analyzing quality: {e}")


def display_quality_dashboard(data: Dict):
    """Display quality dashboard."""
    score_data = data.get('quality_score', {})
    
    # Overall score
    st.markdown("### Overall Quality Score")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        score = score_data.get('overall', 0)
        grade = score_data.get('grade', 'F')
        st.metric("Quality Score", f"{score:.1f}/100", delta=grade)
    
    components = score_data.get('components', {})
    with col2:
        freshness = components.get('freshness', {})
        st.metric("Freshness", f"{freshness.get('score', 0):.1f}", delta=f"{freshness.get('weight', 0)*100:.0f}%")
    
    with col3:
        coverage = components.get('coverage', {})
        st.metric("Coverage", f"{coverage.get('score', 0):.1f}", delta=f"{coverage.get('weight', 0)*100:.0f}%")
    
    with col4:
        consistency = components.get('consistency', {})
        st.metric("Consistency", f"{consistency.get('score', 0):.1f}", delta=f"{consistency.get('weight', 0)*100:.0f}%")
    
    # Quality gauge
    render_quality_gauge(score)
    
    # Top issues
    if data.get('top_issues'):
        st.markdown("### 🚨 Top Issues")
        for issue in data['top_issues'][:5]:
            severity_emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(issue['severity'], "⚪")
            st.warning(f"{severity_emoji} **{issue['title']}**: {issue['description']}")
    
    # Recommendations
    if data.get('recommendations'):
        st.markdown("### 💡 Recommendations")
        for rec in data['recommendations']:
            st.info(f"**{rec['priority']}**: {rec['title']}")


def render_quality_gauge(score: float):
    """Render quality score gauge."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Quality Score"},
        delta={'reference': 80, 'increasing': {'color': "green"}},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 60], 'color': "lightgray"},
                {'range': [60, 80], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# Gap Analysis Tab
# =============================================================================

def render_gap_analysis_tab():
    """Render gap analysis interface."""
    st.header("🔍 Gap Analysis")
    st.caption("Identify missing documentation and coverage gaps")
    
    service_name = st.text_input("Service Name", value="ecosystem-mcp", key="gap_service")
    include_root_cause = st.checkbox("Include Root Cause Analysis", value=True)
    
    if st.button("🔍 Analyze Gaps", type="primary", use_container_width=True):
        analyze_gaps(service_name, include_root_cause)


def analyze_gaps(service_name: str, include_root_cause: bool):
    """Analyze and display gaps."""
    with st.spinner("Analyzing documentation gaps..."):
        try:
            api_base_url = st.session_state.get('api_base_url', 'http://localhost:8000')
            response = requests.get(
                f"{api_base_url}/api/v1/analysis/gaps/analyze",
                params={
                    "service_name": service_name,
                    "include_root_cause": include_root_cause
                },
                timeout=30
            )
            
            if response.status_code == 200:
                gap_data = response.json()
                display_gap_analysis(gap_data)
            else:
                st.error(f"Failed to analyze gaps: {response.text}")
        except Exception as e:
            st.error(f"Error analyzing gaps: {e}")


def display_gap_analysis(data: Dict):
    """Display gap analysis results."""
    st.success(f"✅ Found {data.get('total_gaps', 0)} gaps")
    
    # Gap summary
    col1, col2, col3, col4 = st.columns(4)
    
    by_severity = data.get('by_severity', {})
    with col1:
        st.metric("Critical", by_severity.get('CRITICAL', 0), delta="🔴")
    with col2:
        st.metric("High", by_severity.get('HIGH', 0), delta="🟠")
    with col3:
        st.metric("Medium", by_severity.get('MEDIUM', 0), delta="🟡")
    with col4:
        st.metric("Low", by_severity.get('LOW', 0), delta="🟢")
    
    # Gap chart
    render_gap_chart(by_severity)
    
    # Detailed gaps
    st.markdown("### Detected Gaps")
    
    gaps = data.get('gaps', {})
    for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
        severity_gaps = gaps.get(severity, [])
        if severity_gaps:
            with st.expander(f"{severity} Gaps ({len(severity_gaps)})"):
                for gap in severity_gaps:
                    st.markdown(f"**{gap['gap_type']}**: {gap['description']}")
                    st.caption(f"Affected: {gap['affected_area']} | Root Cause: {gap['root_cause']}")
                    st.info(f"💡 {gap['recommendation']}")
                    st.markdown("---")


def render_gap_chart(by_severity: Dict):
    """Render gap distribution chart."""
    fig = go.Figure(data=[
        go.Bar(
            x=list(by_severity.keys()),
            y=list(by_severity.values()),
            marker_color=['red', 'orange', 'yellow', 'green']
        )
    ])
    
    fig.update_layout(
        title="Gaps by Severity",
        xaxis_title="Severity",
        yaxis_title="Count",
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# Drift Detection Tab
# =============================================================================

def render_drift_detection_tab():
    """Render drift detection interface."""
    st.header("🔄 Drift Detection")
    st.caption("Detect when code and documentation have drifted apart")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        service_name = st.text_input("Service Name", value="ecosystem-mcp", key="drift_service")
    
    with col2:
        detection_mode = st.selectbox(
            "Detection Mode",
            ["hybrid", "git_only", "content_only"],
            help="Hybrid uses both git and content analysis"
        )
    
    if st.button("🔄 Detect Drift", type="primary", use_container_width=True):
        detect_drift(service_name, detection_mode)


def detect_drift(service_name: str, detection_mode: str):
    """Detect and display drift."""
    with st.spinner("Detecting code-documentation drift..."):
        try:
            api_base_url = st.session_state.get('api_base_url', 'http://localhost:8000')
            response = requests.get(
                f"{api_base_url}/api/v1/analysis/drift/detect",
                params={
                    "service_name": service_name,
                    "detection_mode": detection_mode
                },
                timeout=30
            )
            
            if response.status_code == 200:
                drift_data = response.json()
                display_drift_analysis(drift_data)
            else:
                st.error(f"Failed to detect drift: {response.text}")
        except Exception as e:
            st.error(f"Error detecting drift: {e}")


def display_drift_analysis(data: Dict):
    """Display drift analysis results."""
    st.success(f"✅ Detected {data.get('total_drifts', 0)} drifts")
    
    # Drift summary
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Drifts", data.get('total_drifts', 0))
    
    by_severity = data.get('by_severity', {})
    with col2:
        st.metric("Critical", by_severity.get('CRITICAL', 0), delta="🔴")
    with col3:
        st.metric("High", by_severity.get('HIGH', 0), delta="🟠")
    with col4:
        st.metric("Medium", by_severity.get('MEDIUM', 0), delta="🟡")
    with col5:
        st.metric("Low", by_severity.get('LOW', 0), delta="🟢")
    
    # Confidence indicator
    confidence = data.get('confidence_level', 'UNKNOWN')
    st.info(f"🎯 Detection Confidence: **{confidence}** | Mode: {data.get('detection_mode', 'hybrid')}")
    
    # Drift details
    st.markdown("### Detected Drifts")
    
    drifts = data.get('drifts', {})
    for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
        severity_drifts = drifts.get(severity, [])
        if severity_drifts:
            with st.expander(f"{severity} Drifts ({len(severity_drifts)})"):
                for drift in severity_drifts:
                    st.markdown(f"**{drift['file_path']}**")
                    st.caption(f"{drift['description']} (Drift: {drift['drift_days']} days)")
                    st.info(f"💡 {drift['recommendation']}")
                    st.markdown("---")


# =============================================================================
# Export Tab
# =============================================================================

def render_export_tab():
    """Render export interface."""
    st.header("📤 Export Documentation")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        service_name = st.text_input("Service Name", value="ecosystem-mcp", key="export_service")
        
        export_format = st.selectbox(
            "Export Format",
            ["markdown", "html", "json", "pdf", "docx"],
            help="Choose the export format"
        )
        
        output_path = st.text_input("Output Path (optional)", placeholder="./docs")
    
    with col2:
        include_metadata = st.checkbox("Include Metadata", value=True)
        
        st.markdown("### Quick Export")
        
        if st.button("🌐 Export to GitHub Pages", use_container_width=True):
            export_github_pages(service_name)
    
    if st.button("📤 Export", type="primary", use_container_width=True):
        export_documentation(service_name, export_format, output_path, include_metadata)


def export_documentation(service_name, export_format, output_path, include_metadata):
    """Export documentation."""
    with st.spinner(f"Exporting as {export_format}..."):
        try:
            api_base_url = st.session_state.get('api_base_url', 'http://localhost:8000')
            payload = {
                "export_format": export_format,
                "service_name": service_name,
                "include_metadata": include_metadata
            }
            
            if output_path:
                payload["output_path"] = output_path
            
            response = requests.post(
                f"{api_base_url}/api/v1/analysis/export",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                st.success(f"✅ Exported {result.get('documents_exported', 0)} documents!")
                
                if result.get('output_files'):
                    st.markdown("### Generated Files")
                    for file in result['output_files'][:10]:
                        st.code(file['path'])
            else:
                st.error(f"Export failed: {response.text}")
        except Exception as e:
            st.error(f"Error exporting: {e}")


def export_github_pages(service_name):
    """Export for GitHub Pages."""
    with st.spinner("Exporting for GitHub Pages..."):
        try:
            api_base_url = st.session_state.get('api_base_url', 'http://localhost:8000')
            response = requests.post(
                f"{api_base_url}/api/v1/analysis/export/github-pages/{service_name}",
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                st.success("✅ GitHub Pages export complete!")
                
                if result.get('github_pages_config'):
                    config = result['github_pages_config']
                    st.markdown("### 📝 Setup Instructions")
                    for instruction in config.get('instructions', []):
                        st.info(instruction)
            else:
                st.error(f"Export failed: {response.text}")
        except Exception as e:
            st.error(f"Error exporting: {e}")


# =============================================================================
# Helper Functions
# =============================================================================

def view_timeline_details(timeline_id: str):
    """View detailed timeline information."""
    st.info(f"Viewing timeline {timeline_id} - Full details view coming soon!")


def refresh_timeline(timeline_id: str):
    """Refresh timeline data."""
    st.info(f"Refreshing timeline {timeline_id}...")


def export_timeline(timeline_id: str):
    """Export timeline data."""
    st.info(f"Exporting timeline {timeline_id}...")

