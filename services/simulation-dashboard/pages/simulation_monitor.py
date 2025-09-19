"""Simulation Monitor Page - Real-time Dashboard for Simulation Execution.

This module provides a comprehensive real-time dashboard for monitoring simulation execution,
including progress visualization, workflow tracking, document generation monitoring,
and live event streaming.
"""

import streamlit as st
from typing import Dict, Any, Optional, List, Callable
import pandas as pd
from datetime import datetime, timedelta
import time
import asyncio
import json
from dataclasses import dataclass
import plotly.graph_objects as go
import plotly.express as px

# Import simulation client
from services.clients.simulation_client import SimulationClient
from infrastructure.config.config import get_config

# Import real-time components
from components.realtime.live_metrics import render_live_metrics
from components.realtime.event_stream import render_event_stream
from components.realtime.progress_indicators import render_progress_indicator
from components.realtime.status_dashboard import render_status_dashboard
from components.realtime.workflow_visualizer import RealTimeWorkflowVisualizer, create_workflow_visualizer
from components.realtime.event_timeline import RealTimeEventTimeline, create_event_timeline

# Import chart components
from components.charts.timeline_charts import render_timeline_chart
from components.charts.performance_charts import render_performance_chart
from components.charts.anomaly_charts import render_anomaly_chart


@dataclass
class SimulationProgress:
    """Data class for simulation progress information."""
    simulation_id: str
    status: str
    progress_percentage: float
    current_phase: str
    documents_generated: int
    workflows_executed: int
    start_time: Optional[datetime]
    estimated_completion: Optional[datetime]
    active_tasks: List[str]
    completed_tasks: List[str]
    failed_tasks: List[str]


class SimulationMonitor:
    """Main simulation monitoring dashboard."""

    def __init__(self):
        """Initialize the simulation monitor."""
        self.client = SimulationClient()
        self.config = get_config()
        self.last_update = datetime.now()
        self.update_interval = 5  # seconds

        # Initialize real-time components
        self.workflow_visualizer = create_workflow_visualizer()
        self.event_timeline = create_event_timeline()

        # Sample data for demonstration
        self._initialize_sample_data()

    def render_monitor_page(self):
        """Render the main simulation monitor page."""
        st.markdown("## 📊 Simulation Monitor Dashboard")
        st.markdown("Real-time monitoring and visualization of simulation execution progress.")

        # Initialize session state
        if 'selected_simulation' not in st.session_state:
            st.session_state.selected_simulation = None
        if 'simulation_progress' not in st.session_state:
            st.session_state.simulation_progress = None
        if 'monitor_active' not in st.session_state:
            st.session_state.monitor_active = False

        # Simulation selection
        self.render_simulation_selector()

        # Main monitoring dashboard
        if st.session_state.selected_simulation:
            self.render_monitoring_dashboard()
        else:
            self.render_welcome_screen()

    def render_simulation_selector(self):
        """Render simulation selection interface."""
        st.markdown("### 🎯 Select Simulation to Monitor")

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            # Get list of simulations
            try:
                simulations_response = self.client.list_simulations()
                if simulations_response.get('success'):
                    simulations = simulations_response.get('data', {}).get('items', [])

                    if simulations:
                        simulation_options = ["Select a simulation..."] + [
                            f"{sim['id'][:8]} - {sim.get('name', 'Unknown')}"
                            for sim in simulations
                        ]
                        selected_option = st.selectbox(
                            "Available Simulations",
                            options=simulation_options,
                            key="simulation_selector"
                        )

                        if selected_option != "Select a simulation...":
                            selected_sim_id = selected_option.split(" - ")[0]
                            st.session_state.selected_simulation = selected_sim_id
                    else:
                        st.info("No simulations found. Create a simulation to begin monitoring.")
                else:
                    st.error("Failed to load simulations list.")
            except Exception as e:
                st.error(f"Error connecting to simulation service: {e}")

        with col2:
            if st.button("🔄 Refresh", key="refresh_simulations"):
                st.rerun()

        with col3:
            auto_refresh = st.checkbox("Auto-refresh", value=True, key="auto_refresh_monitor")

    def render_welcome_screen(self):
        """Render welcome screen when no simulation is selected."""
        st.markdown("### 🚀 Welcome to Simulation Monitor")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            **Real-time Monitoring Features:**

            ✅ **Live Progress Tracking** - Monitor simulation execution in real-time
            📊 **Workflow Visualization** - See workflows complete as they happen
            📄 **Document Generation** - Track document creation and quality
            📈 **Performance Metrics** - Real-time performance and resource usage
            📅 **Event Timeline** - Interactive timeline of all simulation events
            🔧 **System Health** - Monitor ecosystem service health
            """)

        with col2:
            st.markdown("""
            **How to Use:**

            1. **Select a Simulation** from the dropdown above
            2. **Start Monitoring** to begin real-time tracking
            3. **Watch Progress** as workflows execute and documents generate
            4. **View Analytics** for detailed performance insights
            5. **Export Reports** when simulation completes

            **Real-time Updates:**
            - Progress bars update automatically
            - New events appear instantly
            - Metrics refresh every 5 seconds
            - WebSocket connection for live data
            """)

        # Quick stats
        try:
            health_response = self.client.get_health()
            if health_response.get('success'):
                st.success("✅ Simulation service is healthy and ready for monitoring")
            else:
                st.warning("⚠️ Simulation service health check failed")
        except:
            st.error("❌ Unable to connect to simulation service")

    def render_monitoring_dashboard(self):
        """Render the main monitoring dashboard."""
        simulation_id = st.session_state.selected_simulation

        # Control panel
        self.render_monitor_controls(simulation_id)

        # Main dashboard layout
        if st.session_state.monitor_active:
            self.render_active_monitoring(simulation_id)
        else:
            self.render_simulation_overview(simulation_id)

    def render_monitor_controls(self, simulation_id: str):
        """Render monitoring control panel."""
        st.markdown("### 🎮 Monitor Controls")

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            if st.button("▶️ Start Monitoring", key="start_monitoring"):
                self.start_monitoring(simulation_id)
                st.rerun()

        with col2:
            if st.button("⏸️ Pause Monitoring", key="pause_monitoring"):
                self.pause_monitoring(simulation_id)

        with col3:
            if st.button("🔄 Refresh Data", key="refresh_monitoring"):
                self.refresh_monitoring_data(simulation_id)
                st.rerun()

        with col4:
            if st.button("📊 View Reports", key="view_reports"):
                st.info("Report generation would be triggered here")

        with col5:
            if st.button("🛑 Stop Simulation", key="stop_simulation"):
                self.stop_simulation(simulation_id)

        # Status indicator
        if st.session_state.monitor_active:
            st.success("🔴 **MONITORING ACTIVE** - Real-time updates enabled")
        else:
            st.info("⚪ **MONITORING INACTIVE** - Click 'Start Monitoring' to begin")

    def render_simulation_overview(self, simulation_id: str):
        """Render simulation overview when not actively monitoring."""
        st.markdown("### 📋 Simulation Overview")

        try:
            # Get simulation status
            status_response = self.client.get_simulation_status(simulation_id)
            if status_response.get('success'):
                sim_data = status_response.get('data', {})

                # Overview cards
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    status = sim_data.get('status', 'unknown')
                    status_color = self.get_status_color(status)
                    st.metric("Status", status.title(), delta=None)
                    st.markdown(f"<span style='color:{status_color}'>●</span> {status.title()}", unsafe_allow_html=True)

                with col2:
                    progress = sim_data.get('progress_percentage', 0)
                    st.metric("Progress", ".1f", progress)

                with col3:
                    docs = sim_data.get('documents_generated', 0)
                    st.metric("Documents", docs)

                with col4:
                    workflows = sim_data.get('workflows_executed', 0)
                    st.metric("Workflows", workflows)

                # Detailed information
                with st.expander("📋 Detailed Information", expanded=True):
                    self.render_simulation_details(sim_data)

            else:
                st.error("Failed to load simulation data")

        except Exception as e:
            st.error(f"Error loading simulation: {e}")

    def render_active_monitoring(self, simulation_id: str):
        """Render active monitoring dashboard with real-time updates."""
        # Create tabs for different monitoring views
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Live Progress",
            "🔄 Workflow Monitor",
            "📄 Document Tracker",
            "📈 Performance"
        ])

        with tab1:
            self.render_live_progress_tab(simulation_id)

        with tab2:
            self.render_workflow_monitor_tab(simulation_id)

        with tab3:
            self.render_document_tracker_tab(simulation_id)

        with tab4:
            self.render_performance_tab(simulation_id)

    def render_live_progress_tab(self, simulation_id: str):
        """Render live progress monitoring tab."""
        st.markdown("### 📊 Live Simulation Progress")

        # Get current simulation data
        progress_data = self.get_simulation_progress_data(simulation_id)

        if progress_data:
            # Overall progress indicator
            with st.container():
                col1, col2 = st.columns([3, 1])

                with col1:
                    # Create progress visualization
                    fig = go.Figure()

                    # Overall progress
                    fig.add_trace(go.Indicator(
                        mode="gauge+number+delta",
                        value=progress_data.progress_percentage,
                        title={'text': "Overall Progress"},
                        gauge={
                            'axis': {'range': [None, 100]},
                            'bar': {'color': "darkblue"},
                            'steps': [
                                {'range': [0, 50], 'color': "lightgray"},
                                {'range': [50, 80], 'color': "gray"},
                                {'range': [80, 100], 'color': "darkgray"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 90
                            }
                        }
                    ))

                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    st.metric("Status", progress_data.status.title())
                    st.metric("Current Phase", progress_data.current_phase or "N/A")
                    st.metric("Active Tasks", len(progress_data.active_tasks))
                    st.metric("Completed Tasks", len(progress_data.completed_tasks))

            # Phase timeline visualization
            st.markdown("#### 📅 Phase Timeline")
            self.render_phase_timeline(progress_data)

            # Real-time metrics
            st.markdown("#### 📈 Real-time Metrics")
            self.render_realtime_metrics(progress_data)

        else:
            st.warning("Unable to load progress data")

    def render_workflow_monitor_tab(self, simulation_id: str):
        """Render workflow monitoring tab with active workflow visualization."""
        st.markdown("### 🔄 Workflow Monitor")
        st.markdown("**Active Visual Element**: Watch workflows complete in real-time")

        # Add some sample workflow data for demonstration
        self._add_sample_workflows()

        # Render the real-time workflow visualizer
        self.workflow_visualizer.render_workflow_visualizer(
            title="🔄 Real-Time Workflow Monitor",
            height=600
        )

        # Additional workflow controls
        st.markdown("---")
        with st.expander("Workflow Controls", expanded=False):
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("🔄 Refresh Workflows", key="refresh_workflows"):
                    self._refresh_workflow_data()
                    st.rerun()

            with col2:
                if st.button("🧹 Clear Completed", key="clear_completed_workflows"):
                    self.workflow_visualizer.clear_completed_workflows()
                    st.success("✅ Cleared completed workflows")
                    st.rerun()

            with col3:
                if st.button("📊 Export Workflow Data", key="export_workflow_data"):
                    export_data = self.workflow_visualizer.export_workflow_data('json')
                    st.download_button(
                        label="Download Workflow Data",
                        data=export_data,
                        file_name=f"workflow_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        key="download_workflow_data"
                    )

    def render_document_tracker_tab(self, simulation_id: str):
        """Render document tracking tab."""
        st.markdown("### 📄 Document Generation Tracker")
        st.markdown("**Active Visual Element**: Monitor document generation progress")

        # Get document data
        document_data = self.get_document_progress_data(simulation_id)

        if document_data:
            # Document generation progress
            st.markdown("#### 📝 Document Generation Progress")

            docs_generated = document_data.get('generated_documents', [])
            docs_queued = document_data.get('queued_documents', [])

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Generated", len(docs_generated))

            with col2:
                st.metric("Queued", len(docs_queued))

            with col3:
                total = len(docs_generated) + len(docs_queued)
                completion_rate = (len(docs_generated) / total * 100) if total > 0 else 0
                st.metric("Completion Rate", ".1f")

            # Active document generation visualization
            if docs_queued:
                st.markdown("#### 🚀 Currently Generating")

                for doc in docs_queued[:3]:  # Show top 3
                    self.render_active_document_card(doc)

            # Document quality metrics
            if docs_generated:
                st.markdown("#### 📊 Document Quality Metrics")

                quality_data = []
                for doc in docs_generated[-10:]:  # Last 10 documents
                    quality_data.append({
                        'Document': doc['title'][:30] + "..." if len(doc['title']) > 30 else doc['title'],
                        'Quality_Score': doc.get('quality_score', 0),
                        'Word_Count': doc.get('word_count', 0),
                        'Generation_Time': doc.get('generation_time', 0)
                    })

                if quality_data:
                    df = pd.DataFrame(quality_data)

                    # Quality score chart
                    fig = px.bar(
                        df,
                        x='Document',
                        y='Quality_Score',
                        title="Document Quality Scores",
                        color='Quality_Score',
                        color_continuous_scale='RdYlGn'
                    )
                    fig.update_xaxes(tickangle=45)
                    st.plotly_chart(fig, use_container_width=True)

            # Event Timeline Integration
            st.markdown("#### 📅 Document Generation Events")
            st.markdown("*Real-time event timeline showing document generation activities*")

            # Render event timeline with document-related events
            self.event_timeline.render_timeline(
                title="📅 Document Events Timeline",
                height=400
            )

        else:
            st.warning("Unable to load document data")

    def render_performance_tab(self, simulation_id: str):
        """Render performance monitoring tab."""
        st.markdown("### 📈 Performance Monitor")

        # Get performance data
        performance_data = self.get_performance_data(simulation_id)

        if performance_data:
            # Performance metrics overview
            metrics = performance_data.get('metrics', {})

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                cpu = metrics.get('cpu_usage', 0)
                st.metric("CPU Usage", ".1f", cpu)

            with col2:
                memory = metrics.get('memory_usage', 0)
                st.metric("Memory Usage", ".1f", memory)

            with col3:
                response_time = metrics.get('response_time', 0)
                st.metric("Response Time", ".0f", response_time)

            with col4:
                throughput = metrics.get('throughput', 0)
                st.metric("Throughput", ".0f", throughput)

            # Performance trends
            st.markdown("#### 📊 Performance Trends")

            # Create sample trend data (in real implementation, this would come from monitoring)
            trend_data = []
            base_time = datetime.now() - timedelta(minutes=30)

            for i in range(30):
                trend_data.append({
                    'timestamp': base_time + timedelta(minutes=i),
                    'cpu_usage': 60 + np.random.normal(0, 5),
                    'memory_usage': 70 + np.random.normal(0, 3),
                    'response_time': 150 + np.random.normal(0, 20)
                })

            df = pd.DataFrame(trend_data)

            # CPU and Memory usage over time
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['cpu_usage'],
                mode='lines',
                name='CPU Usage (%)',
                line=dict(color='red')
            ))

            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['memory_usage'],
                mode='lines',
                name='Memory Usage (%)',
                line=dict(color='blue')
            ))

            fig.update_layout(
                title="Resource Usage Trends",
                xaxis_title="Time",
                yaxis_title="Usage (%)"
            )

            st.plotly_chart(fig, use_container_width=True)

            # Response time trend
            fig2 = px.line(
                df,
                x='timestamp',
                y='response_time',
                title="Response Time Trend",
                labels={'response_time': 'Response Time (ms)', 'timestamp': 'Time'}
            )
            st.plotly_chart(fig2, use_container_width=True)

        else:
            st.warning("Unable to load performance data")

    def render_phase_timeline(self, progress_data: SimulationProgress):
        """Render phase timeline visualization."""
        # Create sample phase data (in real implementation, this would come from the simulation)
        phases = [
            {'name': 'Planning', 'status': 'completed', 'duration': 7, 'start_date': progress_data.start_time},
            {'name': 'Design', 'status': 'completed', 'duration': 10, 'start_date': progress_data.start_time + timedelta(days=7) if progress_data.start_time else None},
            {'name': 'Development', 'status': 'in_progress', 'duration': 21, 'start_date': progress_data.start_time + timedelta(days=17) if progress_data.start_time else None},
            {'name': 'Testing', 'status': 'pending', 'duration': 7, 'start_date': None},
            {'name': 'Deployment', 'status': 'pending', 'duration': 3, 'start_date': None}
        ]

        # Create timeline data for visualization
        timeline_data = []
        for phase in phases:
            if phase['start_date']:
                end_date = phase['start_date'] + timedelta(days=phase['duration'])
                timeline_data.append({
                    'Phase': phase['name'],
                    'Start': phase['start_date'],
                    'End': end_date,
                    'Status': phase['status']
                })

        if timeline_data:
            df = pd.DataFrame(timeline_data)

            fig = px.timeline(
                df,
                x_start="Start",
                x_end="End",
                y="Phase",
                color="Status",
                color_discrete_map={
                    'completed': 'green',
                    'in_progress': 'blue',
                    'pending': 'gray'
                },
                title="Project Phase Timeline"
            )
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)

    def render_realtime_metrics(self, progress_data: SimulationProgress):
        """Render real-time metrics display."""
        # Create sample metrics data
        metrics_data = [
            {
                'name': 'Documents Generated',
                'value': progress_data.documents_generated,
                'unit': 'docs',
                'category': 'Productivity',
                'status': 'normal',
                'threshold': 100
            },
            {
                'name': 'Workflows Executed',
                'value': progress_data.workflows_executed,
                'unit': 'workflows',
                'category': 'Productivity',
                'status': 'normal',
                'threshold': 50
            },
            {
                'name': 'Active Tasks',
                'value': len(progress_data.active_tasks),
                'unit': 'tasks',
                'category': 'Activity',
                'status': 'normal',
                'threshold': 20
            },
            {
                'name': 'Completed Tasks',
                'value': len(progress_data.completed_tasks),
                'unit': 'tasks',
                'category': 'Activity',
                'status': 'normal',
                'threshold': 100
            }
        ]

        # Display metrics using the live metrics component
        render_live_metrics(metrics_data, update_interval=10)

    def render_active_workflow_card(self, workflow: Dict[str, Any]):
        """Render an active workflow card with progress."""
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.markdown(f"**⚙️ {workflow.get('name', 'Unknown Workflow')}**")
                progress = workflow.get('progress', 0)
                st.progress(progress / 100, text=".1f")

            with col2:
                status = workflow.get('status', 'running')
                if status == 'running':
                    st.markdown("🔄 Running")
                elif status == 'completed':
                    st.markdown("✅ Completed")
                else:
                    st.markdown("⏸️ Paused")

            with col3:
                elapsed = workflow.get('elapsed_time', 0)
                st.markdown(f"⏱️ {elapsed:.0f}s")

    def render_active_document_card(self, document: Dict[str, Any]):
        """Render an active document generation card."""
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.markdown(f"**📄 {document.get('title', 'Unknown Document')}**")
                progress = document.get('progress', 0)
                st.progress(progress / 100, text=".1f")

            with col2:
                doc_type = document.get('type', 'unknown')
                st.markdown(f"📋 {doc_type.title()}")

            with col3:
                eta = document.get('estimated_completion', 'N/A')
                st.markdown(f"⏱️ {eta}")

    def render_simulation_details(self, sim_data: Dict[str, Any]):
        """Render detailed simulation information."""
        st.markdown("**Simulation Details:**")
        st.json(sim_data)

    def start_monitoring(self, simulation_id: str):
        """Start monitoring for a simulation."""
        try:
            # Start UI monitoring on the simulation service
            response = self.client.start_ui_monitoring(simulation_id)
            if response.get('success'):
                st.session_state.monitor_active = True
                st.success("✅ Monitoring started successfully")
            else:
                st.error("Failed to start monitoring")
        except Exception as e:
            st.error(f"Error starting monitoring: {e}")

    def pause_monitoring(self, simulation_id: str):
        """Pause monitoring for a simulation."""
        st.session_state.monitor_active = False
        st.info("⏸️ Monitoring paused")

    def refresh_monitoring_data(self, simulation_id: str):
        """Refresh monitoring data."""
        # Force refresh of simulation data
        st.session_state.simulation_progress = None

    def stop_simulation(self, simulation_id: str):
        """Stop a simulation."""
        try:
            response = self.client.stop_ui_monitoring(simulation_id, success=False)
            if response.get('success'):
                st.session_state.monitor_active = False
                st.warning("🛑 Simulation stopped")
            else:
                st.error("Failed to stop simulation")
        except Exception as e:
            st.error(f"Error stopping simulation: {e}")

    def get_simulation_progress_data(self, simulation_id: str) -> Optional[SimulationProgress]:
        """Get simulation progress data."""
        try:
            response = self.client.get_simulation_status(simulation_id)
            if response.get('success'):
                data = response.get('data', {})

                return SimulationProgress(
                    simulation_id=simulation_id,
                    status=data.get('status', 'unknown'),
                    progress_percentage=data.get('progress_percentage', 0),
                    current_phase=data.get('current_phase', ''),
                    documents_generated=data.get('documents_generated', 0),
                    workflows_executed=data.get('workflows_executed', 0),
                    start_time=datetime.fromisoformat(data['start_time']) if data.get('start_time') else None,
                    estimated_completion=datetime.fromisoformat(data['estimated_completion']) if data.get('estimated_completion') else None,
                    active_tasks=data.get('active_tasks', []),
                    completed_tasks=data.get('completed_tasks', []),
                    failed_tasks=data.get('failed_tasks', [])
                )
        except Exception as e:
            st.error(f"Error getting progress data: {e}")

        return None

    def get_workflow_progress_data(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow progress data."""
        # This would typically fetch from the simulation service
        # For now, return mock data
        return {
            'total_workflows': 8,
            'active_workflows': [
                {'name': 'Document Generation', 'progress': 75, 'status': 'running', 'elapsed_time': 45.2},
                {'name': 'Quality Analysis', 'progress': 30, 'status': 'running', 'elapsed_time': 12.8}
            ],
            'completed_workflows': [
                {'name': 'Planning Phase', 'start_time': datetime.now() - timedelta(minutes=30), 'end_time': datetime.now() - timedelta(minutes=25), 'duration': 5.0, 'status': 'completed'},
                {'name': 'Design Phase', 'start_time': datetime.now() - timedelta(minutes=25), 'end_time': datetime.now() - timedelta(minutes=20), 'duration': 5.0, 'status': 'completed'},
                {'name': 'Development Setup', 'start_time': datetime.now() - timedelta(minutes=20), 'end_time': datetime.now() - timedelta(minutes=18), 'duration': 2.0, 'status': 'completed'}
            ]
        }

    def get_document_progress_data(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        """Get document progress data."""
        # This would typically fetch from the simulation service
        return {
            'generated_documents': [
                {'title': 'Project Requirements Document', 'type': 'requirements', 'quality_score': 0.88, 'word_count': 2450, 'generation_time': 45.2},
                {'title': 'System Architecture Overview', 'type': 'architecture', 'quality_score': 0.92, 'word_count': 1890, 'generation_time': 38.7},
                {'title': 'API Documentation', 'type': 'api_docs', 'quality_score': 0.85, 'word_count': 3200, 'generation_time': 52.1}
            ],
            'queued_documents': [
                {'title': 'Test Plan Document', 'type': 'testing', 'progress': 60, 'estimated_completion': '2 min'},
                {'title': 'Deployment Guide', 'type': 'deployment', 'progress': 25, 'estimated_completion': '5 min'}
            ]
        }

    def get_performance_data(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        """Get performance data."""
        # This would typically fetch from the simulation service
        return {
            'metrics': {
                'cpu_usage': 67.3,
                'memory_usage': 72.1,
                'response_time': 145.8,
                'throughput': 1250.5,
                'error_rate': 0.02,
                'disk_usage': 45.6
            },
            'trends': {
                'cpu_trend': -2.1,
                'memory_trend': 1.8,
                'response_time_trend': -5.3
            }
        }

    def get_status_color(self, status: str) -> str:
        """Get color for status display."""
        colors = {
            'running': '#28a745',
            'completed': '#007bff',
            'failed': '#dc3545',
            'pending': '#ffc107',
            'paused': '#6c757d'
        }
        return colors.get(status.lower(), '#6c757d')

    def _initialize_sample_data(self):
        """Initialize sample data for demonstration."""
        # Add sample workflows
        self._add_sample_workflows()

        # Add sample events
        self._add_sample_events()

    def _add_sample_workflows(self):
        """Add sample workflow data for demonstration."""
        base_time = datetime.now() - timedelta(minutes=15)

        # Sample active workflows
        active_workflows = [
            {
                'workflow_id': 'wf_doc_gen_001',
                'name': 'Document Generation Pipeline',
                'status': 'running',
                'progress': 75,
                'start_time': base_time + timedelta(minutes=2),
                'estimated_duration': 180.0,
                'current_step': 'Generating API documentation',
                'steps': [
                    {'name': 'Initialize pipeline', 'status': 'completed'},
                    {'name': 'Load templates', 'status': 'completed'},
                    {'name': 'Generate requirements doc', 'status': 'completed'},
                    {'name': 'Generate API documentation', 'status': 'running'},
                    {'name': 'Generate testing docs', 'status': 'pending'},
                    {'name': 'Finalize documents', 'status': 'pending'}
                ]
            },
            {
                'workflow_id': 'wf_analysis_002',
                'name': 'Quality Analysis Workflow',
                'status': 'running',
                'progress': 45,
                'start_time': base_time + timedelta(minutes=8),
                'estimated_duration': 120.0,
                'current_step': 'Analyzing document consistency',
                'steps': [
                    {'name': 'Load documents', 'status': 'completed'},
                    {'name': 'Parse content', 'status': 'completed'},
                    {'name': 'Analyze consistency', 'status': 'running'},
                    {'name': 'Generate insights', 'status': 'pending'},
                    {'name': 'Create report', 'status': 'pending'}
                ]
            }
        ]

        # Sample completed workflows
        completed_workflows = [
            {
                'workflow_id': 'wf_setup_003',
                'name': 'Simulation Setup Workflow',
                'status': 'completed',
                'progress': 100,
                'start_time': base_time - timedelta(minutes=10),
                'end_time': base_time - timedelta(minutes=5),
                'actual_duration': 300.0,
                'steps': [
                    {'name': 'Validate configuration', 'status': 'completed'},
                    {'name': 'Initialize services', 'status': 'completed'},
                    {'name': 'Setup monitoring', 'status': 'completed'},
                    {'name': 'Start simulation', 'status': 'completed'}
                ]
            },
            {
                'workflow_id': 'wf_validation_004',
                'name': 'Configuration Validation',
                'status': 'completed',
                'progress': 100,
                'start_time': base_time - timedelta(minutes=8),
                'end_time': base_time - timedelta(minutes=6),
                'actual_duration': 120.0,
                'steps': [
                    {'name': 'Load configuration', 'status': 'completed'},
                    {'name': 'Validate schema', 'status': 'completed'},
                    {'name': 'Check dependencies', 'status': 'completed'},
                    {'name': 'Generate validation report', 'status': 'completed'}
                ]
            }
        ]

        # Update workflow visualizer with sample data
        for wf in active_workflows + completed_workflows:
            self.workflow_visualizer.update_workflow_state(wf)

    def _add_sample_events(self):
        """Add sample events for demonstration."""
        base_time = datetime.now() - timedelta(minutes=30)

        sample_events = [
            {
                'event_id': 'evt_sim_start_001',
                'timestamp': base_time + timedelta(minutes=2),
                'event_type': 'simulation_started',
                'title': 'Simulation Started',
                'description': 'Project simulation execution has begun',
                'severity': 'info',
                'source': 'simulation_engine',
                'simulation_id': 'sim_demo_001',
                'data': {'project_type': 'web_application', 'team_size': 5}
            },
            {
                'event_id': 'evt_doc_gen_002',
                'timestamp': base_time + timedelta(minutes=5),
                'event_type': 'document_generated',
                'title': 'Requirements Document Generated',
                'description': 'Successfully generated project requirements document',
                'severity': 'info',
                'source': 'document_service',
                'simulation_id': 'sim_demo_001',
                'data': {'document_type': 'requirements', 'word_count': 2450}
            },
            {
                'event_id': 'evt_workflow_start_003',
                'timestamp': base_time + timedelta(minutes=8),
                'event_type': 'workflow_executed',
                'title': 'Quality Analysis Started',
                'description': 'Quality analysis workflow has begun execution',
                'severity': 'info',
                'source': 'workflow_orchestrator',
                'simulation_id': 'sim_demo_001',
                'workflow_id': 'wf_analysis_002'
            },
            {
                'event_id': 'evt_phase_complete_004',
                'timestamp': base_time + timedelta(minutes=12),
                'event_type': 'phase_completed',
                'title': 'Planning Phase Completed',
                'description': 'Planning phase has been completed successfully',
                'severity': 'info',
                'source': 'simulation_engine',
                'simulation_id': 'sim_demo_001',
                'data': {'phase_name': 'planning', 'duration_days': 7}
            },
            {
                'event_id': 'evt_performance_warn_005',
                'timestamp': base_time + timedelta(minutes=15),
                'event_type': 'performance_warning',
                'title': 'High Memory Usage Detected',
                'description': 'Memory usage has exceeded 85% threshold',
                'severity': 'warning',
                'source': 'monitoring',
                'simulation_id': 'sim_demo_001',
                'data': {'memory_usage': 87.5, 'threshold': 85}
            }
        ]

        # Add events to timeline
        for event in sample_events:
            self.event_timeline.add_event(event)

    def _refresh_workflow_data(self):
        """Refresh workflow data from simulation service."""
        # In a real implementation, this would fetch updated data
        # For now, we'll simulate some updates
        self._add_sample_workflows()


def render_simulation_monitor_page():
    """Render the simulation monitor page."""
    monitor = SimulationMonitor()
    monitor.render_monitor_page()
