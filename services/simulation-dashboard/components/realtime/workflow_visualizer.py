"""Real-time Workflow Visualizer - Live Workflow Execution Display.

This module provides a comprehensive real-time visualization component
for monitoring workflow execution, showing active workflows, completion progress,
and performance metrics as workflows execute.

Key Features:
- Real-time workflow progress tracking
- Active workflow visualization with progress bars
- Workflow completion animations
- Performance metrics and timing
- Interactive workflow drill-down
- Multi-workflow concurrent monitoring
"""

import streamlit as st
from typing import Dict, Any, List, Optional, Callable
import pandas as pd
from datetime import datetime, timedelta
import time
import asyncio
import random
from dataclasses import dataclass, field
import plotly.graph_objects as go
import plotly.express as px
from collections import deque


@dataclass
class WorkflowState:
    """Represents the state of a single workflow."""
    workflow_id: str
    name: str
    status: str = "pending"  # pending, running, completed, failed
    progress: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    steps: List[Dict[str, Any]] = field(default_factory=list)
    current_step: Optional[str] = None
    estimated_duration: Optional[float] = None
    actual_duration: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowVisualizerConfig:
    """Configuration for the workflow visualizer."""
    max_concurrent_workflows: int = 10
    update_interval_seconds: float = 1.0
    show_progress_bars: bool = True
    show_timing_info: bool = True
    show_step_details: bool = True
    enable_animations: bool = True
    color_scheme: str = "default"
    height_pixels: int = 600


class RealTimeWorkflowVisualizer:
    """Real-time workflow execution visualizer with live updates."""

    def __init__(self, config: Optional[WorkflowVisualizerConfig] = None):
        """Initialize the workflow visualizer."""
        self.config = config or WorkflowVisualizerConfig()
        self.workflows: Dict[str, WorkflowState] = {}
        self.workflow_history: deque = deque(maxlen=100)  # Keep last 100 workflows
        self.active_workflows: List[str] = []
        self.completed_workflows: List[str] = []
        self.failed_workflows: List[str] = []

        # Animation state
        self.animation_frames: Dict[str, List[Dict[str, Any]]] = {}
        self.last_update_time = datetime.now()

    def update_workflow_state(self, workflow_data: Dict[str, Any]) -> None:
        """Update the state of a workflow from incoming data."""
        workflow_id = workflow_data.get('workflow_id', workflow_data.get('id'))

        if not workflow_id:
            return

        # Get or create workflow state
        if workflow_id not in self.workflows:
            self.workflows[workflow_id] = WorkflowState(
                workflow_id=workflow_id,
                name=workflow_data.get('name', f'Workflow {workflow_id[:8]}')
            )

        workflow = self.workflows[workflow_id]

        # Update workflow state
        workflow.status = workflow_data.get('status', workflow.status)
        workflow.progress = workflow_data.get('progress', workflow.progress)
        workflow.current_step = workflow_data.get('current_step', workflow.current_step)

        # Handle timing
        if workflow_data.get('event_type') == 'workflow_started' and not workflow.start_time:
            workflow.start_time = datetime.now()
            if workflow_id not in self.active_workflows:
                self.active_workflows.append(workflow_id)

        elif workflow_data.get('event_type') in ['workflow_completed', 'workflow_failed']:
            if not workflow.end_time:
                workflow.end_time = datetime.now()
                workflow.actual_duration = (workflow.end_time - workflow.start_time).total_seconds() if workflow.start_time else 0

                # Move from active to completed/failed
                if workflow_id in self.active_workflows:
                    self.active_workflows.remove(workflow_id)

                if workflow_data.get('event_type') == 'workflow_completed':
                    self.completed_workflows.append(workflow_id)
                else:
                    self.failed_workflows.append(workflow_id)
                    workflow.error_message = workflow_data.get('error_message')

        # Update steps if provided
        if 'steps' in workflow_data:
            workflow.steps = workflow_data['steps']

        # Update metadata
        if 'metadata' in workflow_data:
            workflow.metadata.update(workflow_data['metadata'])

        self.last_update_time = datetime.now()

    def render_workflow_visualizer(self,
                                 title: str = "🔄 Real-Time Workflow Monitor",
                                 height: Optional[int] = None) -> None:
        """Render the main workflow visualizer component."""
        st.markdown(f"### {title}")
        st.markdown("*Watch workflows execute in real-time with live progress updates*")

        height = height or self.config.height_pixels

        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs([
            "📊 Active Workflows",
            "✅ Completed Workflows",
            "📈 Performance Analytics"
        ])

        with tab1:
            self._render_active_workflows_tab()

        with tab2:
            self._render_completed_workflows_tab()

        with tab3:
            self._render_performance_analytics_tab()

        # Real-time update indicator
        self._render_update_indicator()

    def _render_active_workflows_tab(self) -> None:
        """Render the active workflows tab."""
        if not self.active_workflows:
            st.success("🎉 No active workflows at the moment")
            st.markdown("""
            **Waiting for workflows to start...**

            When workflows begin execution, they will appear here with:
            - Live progress bars
            - Current step information
            - Estimated completion time
            - Performance metrics
            """)
            return

        st.markdown(f"#### 🚀 Active Workflows ({len(self.active_workflows)})")

        # Sort active workflows by start time (most recent first)
        sorted_workflows = sorted(
            [self.workflows[wid] for wid in self.active_workflows],
            key=lambda w: w.start_time or datetime.min,
            reverse=True
        )

        for workflow in sorted_workflows[:self.config.max_concurrent_workflows]:
            self._render_single_workflow_card(workflow)

        if len(self.active_workflows) > self.config.max_concurrent_workflows:
            st.info(f"... and {len(self.active_workflows) - self.config.max_concurrent_workflows} more workflows")

    def _render_single_workflow_card(self, workflow: WorkflowState) -> None:
        """Render a single workflow card with progress visualization."""
        with st.container():
            # Header with workflow info
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.markdown(f"**⚙️ {workflow.name}**")
                if workflow.current_step:
                    st.markdown(f"*{workflow.current_step}*")

            with col2:
                status_color = self._get_status_color(workflow.status)
                st.markdown(f"<span style='color:{status_color}'>●</span> {workflow.status.title()}",
                           unsafe_allow_html=True)

            with col3:
                elapsed = self._calculate_elapsed_time(workflow)
                st.markdown(f"⏱️ {elapsed}")

            # Progress bar with animation
            if self.config.show_progress_bars:
                progress_bar = st.progress(workflow.progress / 100, text=".1f")

                # Add animated progress effect for running workflows
                if workflow.status == 'running' and self.config.enable_animations:
                    self._add_progress_animation(progress_bar, workflow.workflow_id)

            # Timing information
            if self.config.show_timing_info and workflow.start_time:
                col1, col2, col3 = st.columns(3)

                with col1:
                    elapsed_time = (datetime.now() - workflow.start_time).total_seconds()
                    st.metric("Elapsed", ".0f", "seconds")

                with col2:
                    if workflow.estimated_duration:
                        remaining = max(0, workflow.estimated_duration - elapsed_time)
                        st.metric("Remaining", ".0f", "seconds")
                    else:
                        st.metric("Remaining", "Unknown")

                with col3:
                    if workflow.estimated_duration:
                        eta = workflow.start_time + timedelta(seconds=workflow.estimated_duration)
                        st.metric("ETA", eta.strftime("%H:%M:%S"))
                    else:
                        st.metric("ETA", "Unknown")

            # Step details
            if self.config.show_step_details and workflow.steps:
                self._render_workflow_steps(workflow)

            st.markdown("---")

    def _render_workflow_steps(self, workflow: WorkflowState) -> None:
        """Render detailed workflow steps."""
        with st.expander(f"📋 Steps ({len(workflow.steps)})", expanded=False):
            for i, step in enumerate(workflow.steps):
                step_status = step.get('status', 'pending')
                step_name = step.get('name', f'Step {i+1}')

                # Step status indicator
                if step_status == 'completed':
                    st.markdown(f"✅ {step_name}")
                elif step_status == 'running':
                    st.markdown(f"🔄 {step_name} *(in progress)*")
                elif step_status == 'failed':
                    st.markdown(f"❌ {step_name} *(failed)*")
                else:
                    st.markdown(f"⏳ {step_name} *(pending)*")

                # Step timing
                if step.get('start_time') and step.get('end_time'):
                    duration = (step['end_time'] - step['start_time']).total_seconds()
                    st.markdown(f"   ⏱️ {duration:.1f}s")

    def _render_completed_workflows_tab(self) -> None:
        """Render the completed workflows tab."""
        st.markdown("#### ✅ Completed Workflows")

        if not self.completed_workflows:
            st.info("No completed workflows yet")
            return

        # Recent completions (last 10)
        recent_completions = self.completed_workflows[-10:]

        for workflow_id in reversed(recent_completions):
            if workflow_id in self.workflows:
                workflow = self.workflows[workflow_id]
                self._render_completed_workflow_summary(workflow)

    def _render_completed_workflow_summary(self, workflow: WorkflowState) -> None:
        """Render a summary of a completed workflow."""
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            with col1:
                st.markdown(f"**✅ {workflow.name}**")
                if workflow.actual_duration:
                    st.markdown(".1f")

            with col2:
                if workflow.end_time:
                    st.markdown(workflow.end_time.strftime("%H:%M:%S"))

            with col3:
                st.metric("Steps", len(workflow.steps))

            with col4:
                success_rate = self._calculate_workflow_success_rate(workflow)
                st.metric("Success", ".1f")

            st.markdown("---")

    def _render_performance_analytics_tab(self) -> None:
        """Render the performance analytics tab."""
        st.markdown("#### 📈 Workflow Performance Analytics")

        if not self.workflows:
            st.info("No workflow data available for analytics")
            return

        # Performance metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_workflows = len(self.workflows)
            st.metric("Total Workflows", total_workflows)

        with col2:
            completed_count = len(self.completed_workflows)
            completion_rate = (completed_count / total_workflows * 100) if total_workflows > 0 else 0
            st.metric("Completion Rate", ".1f")

        with col3:
            avg_duration = self._calculate_average_duration()
            st.metric("Avg Duration", ".1f")

        with col4:
            success_rate = self._calculate_overall_success_rate()
            st.metric("Success Rate", ".1f")

        # Performance trends chart
        st.markdown("##### 📊 Performance Trends")

        # Create sample performance data (would come from actual workflow data)
        performance_data = []
        base_time = datetime.now() - timedelta(hours=2)

        for i in range(24):  # Last 24 data points
            performance_data.append({
                'time': base_time + timedelta(minutes=i*5),
                'duration': 120 + random.uniform(-20, 30),
                'success_rate': 85 + random.uniform(-10, 10),
                'throughput': 5 + random.uniform(-1, 2)
            })

        df = pd.DataFrame(performance_data)

        # Duration trend
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df['time'],
            y=df['duration'],
            mode='lines+markers',
            name='Avg Duration (s)',
            line=dict(color='blue')
        ))

        fig.add_trace(go.Scatter(
            x=df['time'],
            y=df['success_rate'],
            mode='lines+markers',
            name='Success Rate (%)',
            line=dict(color='green'),
            yaxis='y2'
        ))

        fig.update_layout(
            title="Workflow Performance Trends",
            xaxis_title="Time",
            yaxis_title="Duration (seconds)",
            yaxis2=dict(
                title="Success Rate (%)",
                overlaying='y',
                side='right'
            ),
            showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)

    def _render_update_indicator(self) -> None:
        """Render the real-time update indicator."""
        time_since_update = (datetime.now() - self.last_update_time).total_seconds()

        if time_since_update < 5:
            st.success("🔴 **LIVE** - Real-time updates active")
        elif time_since_update < 30:
            st.warning("🟡 **STALE** - Updates may be delayed")
        else:
            st.error("🔴 **OFFLINE** - No recent updates")

        st.caption(f"Last update: {self.last_update_time.strftime('%H:%M:%S')}")

    def _add_progress_animation(self, progress_bar, workflow_id: str) -> None:
        """Add animated progress effect for running workflows."""
        if workflow_id not in self.animation_frames:
            self.animation_frames[workflow_id] = []

        # Add subtle animation by slightly varying the progress
        # This creates a "pulsing" effect for active workflows
        pass  # Animation logic would go here

    def _calculate_elapsed_time(self, workflow: WorkflowState) -> str:
        """Calculate and format elapsed time for a workflow."""
        if not workflow.start_time:
            return "00:00"

        elapsed = datetime.now() - workflow.start_time
        minutes = int(elapsed.total_seconds() // 60)
        seconds = int(elapsed.total_seconds() % 60)

        return "02d"

    def _calculate_workflow_success_rate(self, workflow: WorkflowState) -> float:
        """Calculate success rate for a workflow based on completed steps."""
        if not workflow.steps:
            return 100.0 if workflow.status == 'completed' else 0.0

        completed_steps = sum(1 for step in workflow.steps if step.get('status') == 'completed')
        return (completed_steps / len(workflow.steps)) * 100

    def _calculate_average_duration(self) -> float:
        """Calculate average duration of completed workflows."""
        completed_workflows = [
            self.workflows[wid] for wid in self.completed_workflows
            if wid in self.workflows and self.workflows[wid].actual_duration
        ]

        if not completed_workflows:
            return 0.0

        return sum(w.actual_duration for w in completed_workflows) / len(completed_workflows)

    def _calculate_overall_success_rate(self) -> float:
        """Calculate overall success rate across all workflows."""
        total_workflows = len(self.workflows)
        if total_workflows == 0:
            return 0.0

        successful_workflows = len(self.completed_workflows)
        return (successful_workflows / total_workflows) * 100

    def _get_status_color(self, status: str) -> str:
        """Get color code for workflow status."""
        colors = {
            'running': '#28a745',
            'completed': '#007bff',
            'failed': '#dc3545',
            'pending': '#ffc107',
            'paused': '#6c757d'
        }
        return colors.get(status.lower(), '#6c757d')

    def add_workflow_event_handler(self, event_type: str, handler: Callable) -> None:
        """Add an event handler for workflow events."""
        # This would integrate with the WebSocket event system
        pass

    def export_workflow_data(self, format: str = 'json') -> str:
        """Export workflow data for external analysis."""
        export_data = {
            'workflows': {
                wid: {
                    'name': w.name,
                    'status': w.status,
                    'progress': w.progress,
                    'start_time': w.start_time.isoformat() if w.start_time else None,
                    'end_time': w.end_time.isoformat() if w.end_time else None,
                    'duration': w.actual_duration,
                    'steps': w.steps
                }
                for wid, w in self.workflows.items()
            },
            'export_timestamp': datetime.now().isoformat(),
            'total_workflows': len(self.workflows),
            'active_workflows': len(self.active_workflows),
            'completed_workflows': len(self.completed_workflows)
        }

        if format == 'json':
            import json
            return json.dumps(export_data, indent=2, default=str)
        else:
            return str(export_data)

    def clear_completed_workflows(self) -> None:
        """Clear completed workflows from the visualizer."""
        for workflow_id in self.completed_workflows[:]:
            if workflow_id in self.workflows:
                del self.workflows[workflow_id]
            self.completed_workflows.remove(workflow_id)

    def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get comprehensive workflow statistics."""
        return {
            'total_workflows': len(self.workflows),
            'active_workflows': len(self.active_workflows),
            'completed_workflows': len(self.completed_workflows),
            'failed_workflows': len(self.failed_workflows),
            'average_duration': self._calculate_average_duration(),
            'overall_success_rate': self._calculate_overall_success_rate(),
            'completion_rate': len(self.completed_workflows) / len(self.workflows) if self.workflows else 0
        }


# Convenience function for easy integration
def create_workflow_visualizer(config: Optional[WorkflowVisualizerConfig] = None) -> RealTimeWorkflowVisualizer:
    """Create a new workflow visualizer instance."""
    return RealTimeWorkflowVisualizer(config)


def render_realtime_workflow_monitor(simulation_id: Optional[str] = None,
                                   title: str = "🔄 Real-Time Workflow Monitor") -> None:
    """Render a real-time workflow monitor component."""
    visualizer = RealTimeWorkflowVisualizer()
    visualizer.render_workflow_visualizer(title=title)
