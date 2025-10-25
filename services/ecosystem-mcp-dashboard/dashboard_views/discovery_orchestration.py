"""
Discovery & Orchestration Dashboard

Repository scanning, processing plan management, and orchestration monitoring.
Enables parallel processing and execution monitoring.
"""

import streamlit as st
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Optional

from utils.api_tracker import make_api_request


def show(api_base_url: str):
    """Display Discovery & Orchestration dashboard."""
    st.title("🎯 Discovery & Orchestration")
    st.markdown("Repository scanning, processing plans, and parallel execution monitoring")
    
    # Top-level tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔍 Discovery Scanner",
        "📋 Processing Plans",
        "▶️ Execution Monitor",
        "⚠️ Alerts",
        "📊 Metrics"
    ])
    
    with tab1:
        show_discovery_scanner(api_base_url)
    
    with tab2:
        show_processing_plans(api_base_url)
    
    with tab3:
        show_execution_monitor(api_base_url)
    
    with tab4:
        show_alerts_dashboard(api_base_url)
    
    with tab5:
        show_orchestration_metrics(api_base_url)


def show_discovery_scanner(api_base_url: str):
    """Show repository discovery scanner interface."""
    st.subheader("🔍 Repository Discovery Scanner")
    st.markdown("Scan repositories to discover files and create processing plans")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        repo_path = st.text_input(
            "Repository Path",
            value="/Users/mykalthomas/Documents/work/Hackathon",
            help="Path to the repository to scan"
        )
    
    with col2:
        scan_depth = st.selectbox(
            "Scan Depth",
            ["Shallow", "Medium", "Deep"],
            index=1,
            help="How deep to scan the repository"
        )
    
    # Scan options
    st.markdown("### 🔧 Scan Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        include_docs = st.checkbox("Include Documentation", value=True)
    with col2:
        include_code = st.checkbox("Include Code", value=True)
    with col3:
        include_configs = st.checkbox("Include Configs", value=True)
    
    # File type filters
    file_patterns = st.multiselect(
        "File Patterns (optional)",
        ["*.md", "*.py", "*.js", "*.ts", "*.yaml", "*.json", "*.txt"],
        default=["*.md", "*.py"]
    )
    
    if st.button("🚀 Start Discovery Scan", type="primary"):
        with st.spinner("Scanning repository..."):
            scan_data = {
                "repo_path": repo_path,
                "scan_depth": scan_depth.lower(),
                "options": {
                    "include_docs": include_docs,
                    "include_code": include_code,
                    "include_configs": include_configs
                }
            }
            
            if file_patterns:
                scan_data["file_patterns"] = file_patterns
            
            result = make_api_request(
                api_base_url,
                "/api/v1/discovery/scan",
                method="POST",
                json_data=scan_data,
                timeout=60.0
            )
            
            if result:
                st.success(f"✅ Scan completed!")
                
                # Display scan results
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Files Found", result.get("file_count", 0))
                with col2:
                    st.metric("Services Detected", result.get("service_count", 0))
                with col3:
                    st.metric("Total Size", f"{result.get('total_size_mb', 0):.1f} MB")
                with col4:
                    plan_id = result.get("plan_id", "N/A")
                    st.metric("Plan ID", "Created" if plan_id != "N/A" else "N/A")
                
                # File breakdown
                if "files_by_type" in result:
                    st.markdown("### 📁 Files by Type")
                    
                    file_types = result["files_by_type"]
                    df = pd.DataFrame([
                        {"Type": file_type, "Count": count}
                        for file_type, count in file_types.items()
                    ])
                    
                    fig = px.pie(df, names="Type", values="Count", title="File Distribution")
                    st.plotly_chart(fig, use_container_width=True)
                
                # Services detected
                if "services" in result and result["services"]:
                    st.markdown("### 🏗️ Services Detected")
                    
                    for service in result["services"][:10]:
                        with st.expander(f"📦 {service.get('name', 'Unknown')}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"**Path:** {service.get('path', 'N/A')}")
                                st.markdown(f"**Files:** {service.get('file_count', 0)}")
                            with col2:
                                st.markdown(f"**Type:** {service.get('type', 'N/A')}")
                                st.markdown(f"**Size:** {service.get('size_mb', 0):.1f} MB")
                
                # Show plan if created
                if plan_id and plan_id != "N/A":
                    st.markdown("### 📋 Processing Plan Created")
                    st.info(f"**Plan ID:** `{plan_id}`")
                    
                    if st.button("📋 View Plan Details"):
                        st.session_state.selected_plan_id = plan_id
                        st.rerun()


def show_processing_plans(api_base_url: str):
    """Show processing plans management interface."""
    st.subheader("📋 Processing Plans")
    st.markdown("Manage and view processing plans created from discovery scans")
    
    # Fetch all plans
    plans_result = make_api_request(
        api_base_url,
        "/api/v1/discovery/plans",
        method="GET",
        timeout=10.0,
        show_error=False
    )
    
    if plans_result and "plans" in plans_result:
        plans = plans_result["plans"]
        
        if not plans:
            st.info("📭 No processing plans found. Run a discovery scan to create one.")
        else:
            st.success(f"📋 Found {len(plans)} processing plan(s)")
            
            # Plans table
            plans_data = []
            for plan in plans:
                plans_data.append({
                    "Plan ID": plan.get("plan_id", "Unknown")[:8] + "...",
                    "Created": plan.get("created_at", "Unknown"),
                    "Files": plan.get("file_count", 0),
                    "Services": plan.get("service_count", 0),
                    "Status": plan.get("status", "Unknown")
                })
            
            df = pd.DataFrame(plans_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Plan selector
            st.markdown("### 🔍 Plan Details")
            
            plan_ids = [p.get("plan_id", "Unknown") for p in plans]
            selected_plan = st.selectbox(
                "Select Plan",
                plan_ids,
                format_func=lambda x: f"{x[:16]}..." if len(x) > 16 else x
            )
            
            if selected_plan:
                show_plan_details(api_base_url, selected_plan)
    else:
        st.info("📭 No processing plans available or unable to fetch plans.")


def show_plan_details(api_base_url: str, plan_id: str):
    """Show detailed information about a processing plan."""
    result = make_api_request(
        api_base_url,
        f"/api/v1/discovery/plans/{plan_id}",
        method="GET",
        timeout=10.0
    )
    
    if result:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Status", result.get("status", "Unknown"))
        with col2:
            st.metric("Total Files", result.get("file_count", 0))
        with col3:
            st.metric("Services", result.get("service_count", 0))
        with col4:
            st.metric("Est. Duration", f"{result.get('estimated_duration_min', 0)} min")
        
        # Execution actions
        st.markdown("### ⚡ Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("▶️ Execute Plan", type="primary", use_container_width=True):
                execute_result = make_api_request(
                    api_base_url,
                    f"/api/v1/orchestration/execute/{plan_id}",
                    method="POST",
                    timeout=10.0
                )
                if execute_result:
                    st.success("✅ Execution started!")
                    st.rerun()
        
        with col2:
            if st.button("⏸️ Pause", use_container_width=True):
                pause_result = make_api_request(
                    api_base_url,
                    f"/api/v1/orchestration/pause/{plan_id}",
                    method="POST"
                )
                if pause_result:
                    st.success("⏸️ Execution paused")
                    st.rerun()
        
        with col3:
            if st.button("❌ Cancel", use_container_width=True):
                cancel_result = make_api_request(
                    api_base_url,
                    f"/api/v1/orchestration/cancel/{plan_id}",
                    method="POST"
                )
                if cancel_result:
                    st.warning("❌ Execution cancelled")
                    st.rerun()
        
        # Plan details
        if "details" in result:
            st.markdown("### 📊 Plan Details")
            st.json(result["details"])


def show_execution_monitor(api_base_url: str):
    """Show execution monitoring interface."""
    st.subheader("▶️ Execution Monitor")
    st.markdown("Monitor active and completed plan executions in real-time")
    
    # Auto-refresh toggle
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("**Active Executions**")
    
    with col2:
        auto_refresh = st.toggle("Auto-refresh", value=True)
    
    with col3:
        if auto_refresh:
            import time
            st.info(f"⏱️ Refresh: 5s")
            time.sleep(5)
            st.rerun()
    
    # Get orchestration status for active plans
    # For now, let's show a way to monitor a specific plan
    plan_id_input = st.text_input(
        "Plan ID to Monitor",
        placeholder="Enter plan ID from Processing Plans tab",
        help="Monitor execution progress for a specific plan",
        key="monitor_plan_id"
    )
    
    if plan_id_input:
        st.markdown("---")
        
        # Always show current status when plan ID is entered
        with st.spinner(f"🔍 Checking status for plan {plan_id_input[:16]}..."):
            st.write(f"**Debug:** Fetching status from `/api/v1/orchestration/status/{plan_id_input}`")
            
            status_result = make_api_request(
                api_base_url,
                f"/api/v1/orchestration/status/{plan_id_input}",
                method="GET",
                timeout=10.0,
                show_error=False  # Don't show error popup, we'll handle it
            )
        
        if status_result and status_result.get("success") != False:
            st.success("✅ Found active execution!")
            
            st.markdown("### 📊 Execution Status")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                status = status_result.get("status", "Unknown")
                st.metric("Status", status)
            with col2:
                progress = status_result.get("progress_percent", 0)
                st.metric("Progress", f"{progress:.1f}%")
            with col3:
                st.metric("Completed", status_result.get("completed_tasks", 0))
            with col4:
                st.metric("Remaining", status_result.get("remaining_tasks", 0))
            
            # Progress bar
            st.progress(progress / 100.0)
            
            # Get detailed progress
            with st.spinner("📊 Fetching detailed progress..."):
                st.write(f"**Debug:** Fetching progress from `/api/v1/orchestration/progress/{plan_id_input}`")
                
                progress_result = make_api_request(
                    api_base_url,
                    f"/api/v1/orchestration/progress/{plan_id_input}",
                    method="GET",
                    timeout=10.0,
                    show_error=False
                )
            
            if progress_result and progress_result.get("success") != False:
                st.markdown("### 📈 Detailed Progress")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    files_processed = progress_result.get("files_processed", 0)
                    total_files = progress_result.get("total_files", 0)
                    st.metric("Files Processed", f"{files_processed}/{total_files}")
                
                with col2:
                    files_failed = progress_result.get("files_failed", 0)
                    st.metric("Files Failed", files_failed)
                
                with col3:
                    eta = progress_result.get("eta_seconds")
                    if eta:
                        eta_min = int(eta / 60)
                        st.metric("ETA", f"{eta_min} min")
                    else:
                        st.metric("ETA", "Calculating...")
            else:
                st.warning("⚠️ No detailed progress data available yet. Progress tracking may not be initialized.")
                st.write("**Note:** Progress tracking is created when execution starts processing files.")
        else:
            st.warning(f"⚠️ No active execution found for plan {plan_id_input[:16]}...")
            
            # Check if plan exists
            with st.expander("🔍 Troubleshooting"):
                st.markdown("**Checking plan status...**")
                
                # Try to get plan details
                plan_result = make_api_request(
                    api_base_url,
                    f"/api/v1/discovery/plan/{plan_id_input}",
                    method="GET",
                    timeout=10.0,
                    show_error=False
                )
                
                if plan_result:
                    st.info(f"✅ Plan exists with status: **{plan_result.get('status', 'Unknown')}**")
                    
                    if st.button("▶️ Start Execution", key=f"start_exec_{plan_id_input}"):
                        with st.spinner("🚀 Starting execution..."):
                            exec_result = make_api_request(
                                api_base_url,
                                f"/api/v1/orchestration/execute/{plan_id_input}",
                                method="POST",
                                timeout=10.0
                            )
                            
                            if exec_result and exec_result.get("success"):
                                st.success("✅ Execution started! Refreshing in 2 seconds...")
                                import time
                                time.sleep(2)
                                st.rerun()
                else:
                    st.error(f"❌ Plan {plan_id_input[:16]}... not found in database")
        
        # Control buttons
        st.markdown("### ⚙️ Execution Controls")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("⏸️ Pause Execution", use_container_width=True):
                with st.spinner("⏸️ Pausing..."):
                    pause_result = make_api_request(
                        api_base_url,
                        f"/api/v1/orchestration/pause/{plan_id_input}",
                        method="POST"
                    )
                    if pause_result:
                        st.success("⏸️ Execution paused")
                        st.rerun()
        
        with col2:
            if st.button("▶️ Resume Execution", use_container_width=True):
                with st.spinner("▶️ Resuming..."):
                    resume_result = make_api_request(
                        api_base_url,
                        f"/api/v1/orchestration/resume/{plan_id_input}",
                        method="POST"
                    )
                    if resume_result:
                        st.success("▶️ Execution resumed")
                        st.rerun()
        
        with col3:
            if st.button("❌ Cancel Execution", use_container_width=True):
                with st.spinner("❌ Cancelling..."):
                    cancel_result = make_api_request(
                        api_base_url,
                        f"/api/v1/orchestration/cancel/{plan_id_input}",
                        method="POST"
                    )
                    if cancel_result:
                        st.warning("❌ Execution cancelled")
                        st.rerun()
                    
                    # Progress bar
                    st.progress(progress / 100.0)
                    
                    # Detailed status
                    if "details" in status_result:
                        with st.expander("🔍 Detailed Status"):
                            st.json(status_result["details"])
        
        with col2:
            if st.button("📈 View Progress", type="secondary"):
                progress_result = make_api_request(
                    api_base_url,
                    f"/api/v1/orchestration/progress/{plan_id_input}",
                    method="GET",
                    timeout=10.0
                )
                
                if progress_result:
                    st.markdown("### 📈 Progress Details")
                    
                    # Timeline
                    if "timeline" in progress_result:
                        st.markdown("**Execution Timeline:**")
                        for event in progress_result["timeline"][-10:]:
                            st.markdown(f"- `{event.get('timestamp', '')}`: {event.get('message', '')}")
                    
                    # Current task
                    if "current_task" in progress_result:
                        st.info(f"**Current Task:** {progress_result['current_task']}")
        
        # Monitor dashboard
        if st.button("👁️ Monitor Dashboard"):
            monitor_result = make_api_request(
                api_base_url,
                f"/api/v1/orchestration/monitor/{plan_id_input}",
                method="GET",
                timeout=10.0
            )
            
            if monitor_result:
                st.markdown("### 👁️ Monitoring Dashboard")
                
                # Worker status
                if "workers" in monitor_result:
                    st.markdown("**Worker Status:**")
                    
                    workers_data = []
                    for worker in monitor_result["workers"]:
                        workers_data.append({
                            "Worker": worker.get("id", "Unknown"),
                            "Status": worker.get("status", "Unknown"),
                            "Tasks": worker.get("tasks_completed", 0),
                            "Current": worker.get("current_task", "Idle")
                        })
                    
                    df = pd.DataFrame(workers_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Resource usage
                if "resources" in monitor_result:
                    col1, col2, col3 = st.columns(3)
                    
                    resources = monitor_result["resources"]
                    with col1:
                        st.metric("CPU", f"{resources.get('cpu_percent', 0):.1f}%")
                    with col2:
                        st.metric("Memory", f"{resources.get('memory_mb', 0):.0f} MB")
                    with col3:
                        st.metric("Queue", resources.get('queue_size', 0))


def show_alerts_dashboard(api_base_url: str):
    """Show orchestration alerts."""
    st.subheader("⚠️ Orchestration Alerts")
    st.markdown("View system alerts and warnings from orchestration")
    
    result = make_api_request(
        api_base_url,
        "/api/v1/orchestration/alerts",
        method="GET",
        timeout=10.0,
        show_error=False
    )
    
    if result and "alerts" in result:
        alerts = result["alerts"]
        
        if not alerts:
            st.success("✅ No active alerts")
        else:
            st.warning(f"⚠️ {len(alerts)} active alert(s)")
            
            # Group by severity
            critical = [a for a in alerts if a.get("severity") == "CRITICAL"]
            warning = [a for a in alerts if a.get("severity") == "WARNING"]
            info = [a for a in alerts if a.get("severity") == "INFO"]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Critical", len(critical), delta=None if len(critical) == 0 else str(len(critical)), delta_color="inverse")
            with col2:
                st.metric("Warning", len(warning))
            with col3:
                st.metric("Info", len(info))
            
            # Display alerts
            st.markdown("### 🔔 Active Alerts")
            
            for alert in alerts[:20]:
                severity = alert.get("severity", "INFO")
                icon = {"CRITICAL": "🔴", "WARNING": "🟡", "INFO": "🔵"}.get(severity, "⚪")
                
                with st.expander(f"{icon} {alert.get('title', 'Alert')} - {alert.get('timestamp', '')}"):
                    st.markdown(f"**Severity:** {severity}")
                    st.markdown(f"**Message:** {alert.get('message', 'N/A')}")
                    
                    if "plan_id" in alert:
                        st.markdown(f"**Plan ID:** `{alert['plan_id']}`")
                    
                    if "recommendation" in alert:
                        st.info(f"💡 **Recommendation:** {alert['recommendation']}")
    else:
        st.info("📭 No alerts available")


def show_orchestration_metrics(api_base_url: str):
    """Show orchestration metrics and statistics."""
    st.subheader("📊 Orchestration Metrics")
    st.markdown("System-wide orchestration performance and statistics")
    
    result = make_api_request(
        api_base_url,
        "/api/v1/orchestration/metrics",
        method="GET",
        timeout=10.0,
        show_error=False
    )
    
    if result:
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Executions", result.get("total_executions", 0))
        with col2:
            st.metric("Active", result.get("active_executions", 0))
        with col3:
            st.metric("Completed", result.get("completed_executions", 0))
        with col4:
            st.metric("Failed", result.get("failed_executions", 0))
        
        # Success rate
        total = result.get("total_executions", 0)
        completed = result.get("completed_executions", 0)
        if total > 0:
            success_rate = (completed / total) * 100
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        # Performance metrics
        if "performance" in result:
            st.markdown("### ⚡ Performance")
            
            perf = result["performance"]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Avg Duration", f"{perf.get('avg_duration_min', 0):.1f} min")
            with col2:
                st.metric("Throughput", f"{perf.get('tasks_per_minute', 0):.1f} tasks/min")
            with col3:
                st.metric("Avg Parallelism", f"{perf.get('avg_parallelism', 0):.1f}")
        
        # Timeline chart
        if "execution_history" in result:
            st.markdown("### 📈 Execution History")
            
            history = result["execution_history"]
            df = pd.DataFrame(history)
            
            if not df.empty:
                fig = px.line(df, x="date", y="count", title="Executions Over Time")
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📭 Metrics not available")

