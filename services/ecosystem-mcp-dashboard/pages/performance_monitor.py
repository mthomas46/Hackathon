"""
Performance Monitoring Dashboard (Option C, Phase 3, Day 7)

Real-time performance monitoring with:
- Live metrics visualization
- Bottleneck detection
- Health score tracking
- Operation statistics
- Optimization recommendations
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time

# from dashboard_views.api_client import get_api_client  # Module not available


def show(api_base_url: str):
    """Entry point for dashboard integration."""
    render_performance_monitor()


def render_performance_monitor():
    """Render performance monitoring page."""
    st.title("📊 Performance Monitor")
    st.markdown("Real-time performance monitoring and bottleneck detection")
    
    # Get API client
    api_client = get_api_client()
    
    # Auto-refresh toggle
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        auto_refresh = st.checkbox("🔄 Auto-refresh", value=True, key="perf_auto_refresh")
    with col2:
        refresh_interval = st.selectbox(
            "Interval",
            options=[5, 10, 30, 60],
            index=1,
            format_func=lambda x: f"{x}s",
            key="perf_refresh_interval"
        )
    with col3:
        if st.button("🔄 Refresh Now", key="perf_refresh_now"):
            st.rerun()
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Overview",
        "🔍 Bottlenecks",
        "📊 Operation Stats",
        "💡 Recommendations"
    ])
    
    # Tab 1: Overview
    with tab1:
        render_overview_tab(api_client)
    
    # Tab 2: Bottlenecks
    with tab2:
        render_bottlenecks_tab(api_client)
    
    # Tab 3: Operation Stats
    with tab3:
        render_operation_stats_tab(api_client)
    
    # Tab 4: Recommendations
    with tab4:
        render_recommendations_tab(api_client)
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()


def render_overview_tab(api_client):
    """Render overview tab."""
    st.subheader("📈 Performance Overview")
    
    try:
        # Get performance summary
        response = api_client.get("/performance/summary")
        
        if response.status_code != 200:
            st.error(f"❌ Failed to fetch performance data (HTTP {response.status_code})")
            return
        
        summary = response.json()
        
        # Health Score
        health_score = summary.get("health_score", 0)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Health score with color
            if health_score >= 80:
                color = "🟢"
                status = "Healthy"
            elif health_score >= 50:
                color = "🟡"
                status = "Degraded"
            else:
                color = "🔴"
                status = "Critical"
            
            st.metric(
                "Health Score",
                f"{color} {health_score:.0f}/100",
                delta=status,
                delta_color="off"
            )
        
        with col2:
            st.metric(
                "Total Metrics",
                f"{summary.get('total_metrics', 0):,}"
            )
        
        with col3:
            bottleneck_count = len(summary.get("bottlenecks", []))
            st.metric(
                "Bottlenecks",
                bottleneck_count,
                delta="Issues detected" if bottleneck_count > 0 else "None",
                delta_color="inverse"
            )
        
        with col4:
            operations_count = len(summary.get("operations", {}))
            st.metric(
                "Monitored Operations",
                operations_count
            )
        
        st.divider()
        
        # Operation Performance Chart
        st.subheader("⚡ Operation Performance")
        
        operations = summary.get("operations", {})
        
        if operations:
            # Create DataFrame
            op_data = []
            for op_name, op_stats in operations.items():
                op_data.append({
                    "Operation": op_name.replace("_", " ").title(),
                    "Avg (ms)": op_stats.get("avg", 0),
                    "P95 (ms)": op_stats.get("p95", 0),
                    "P99 (ms)": op_stats.get("p99", 0),
                    "Count": op_stats.get("count", 0)
                })
            
            df = pd.DataFrame(op_data)
            
            # Bar chart
            fig = px.bar(
                df,
                x="Operation",
                y=["Avg (ms)", "P95 (ms)", "P99 (ms)"],
                title="Operation Duration (ms)",
                barmode="group",
                color_discrete_sequence=["#1f77b4", "#ff7f0e", "#d62728"]
            )
            
            fig.update_layout(
                xaxis_title="Operation Type",
                yaxis_title="Duration (ms)",
                legend_title="Metric",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Data table
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("ℹ️ No operation data available yet. Operations will appear as they are monitored.")
    
    except Exception as e:
        st.error(f"❌ Error loading performance overview: {str(e)}")


def render_bottlenecks_tab(api_client):
    """Render bottlenecks tab."""
    st.subheader("🔍 Performance Bottlenecks")
    
    try:
        # Get bottlenecks
        response = api_client.get("/performance/bottlenecks")
        
        if response.status_code != 200:
            st.error(f"❌ Failed to fetch bottlenecks (HTTP {response.status_code})")
            return
        
        bottlenecks = response.json()
        
        if not bottlenecks:
            st.success("✅ No bottlenecks detected! System is performing well.")
            return
        
        # Display bottlenecks
        for bottleneck in bottlenecks:
            severity = bottleneck.get("severity", "unknown")
            
            # Severity icon and color
            if severity == "critical":
                icon = "🔴"
                color = "red"
            elif severity == "high":
                icon = "🟠"
                color = "orange"
            elif severity == "medium":
                icon = "🟡"
                color = "yellow"
            else:
                icon = "🔵"
                color = "blue"
            
            with st.expander(
                f"{icon} {bottleneck.get('operation_type', 'Unknown').replace('_', ' ').title()} "
                f"(Impact: {bottleneck.get('impact_score', 0):.0f}/100)",
                expanded=(severity in ["critical", "high"])
            ):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Description:**")
                    st.write(bottleneck.get("description", "No description"))
                    
                    st.markdown(f"**Recommendation:**")
                    st.info(bottleneck.get("recommendation", "No recommendation"))
                
                with col2:
                    st.metric(
                        "Avg Duration",
                        f"{bottleneck.get('avg_duration_ms', 0):.0f} ms"
                    )
                    st.metric(
                        "Impact Score",
                        f"{bottleneck.get('impact_score', 0):.0f}/100"
                    )
                    st.metric(
                        "Severity",
                        severity.upper()
                    )
        
        # Summary chart
        st.divider()
        st.subheader("📊 Bottleneck Summary")
        
        # Create DataFrame
        df = pd.DataFrame(bottlenecks)
        
        if not df.empty:
            # Impact score chart
            fig = px.bar(
                df,
                x="operation_type",
                y="impact_score",
                color="severity",
                title="Bottleneck Impact by Operation",
                color_discrete_map={
                    "critical": "#d62728",
                    "high": "#ff7f0e",
                    "medium": "#ffdd57",
                    "low": "#1f77b4"
                }
            )
            
            fig.update_layout(
                xaxis_title="Operation Type",
                yaxis_title="Impact Score",
                height=300
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"❌ Error loading bottlenecks: {str(e)}")


def render_operation_stats_tab(api_client):
    """Render operation statistics tab."""
    st.subheader("📊 Operation Statistics")
    
    # Get available operations
    try:
        response = api_client.get("/performance/operations")
        
        if response.status_code != 200:
            st.error(f"❌ Failed to fetch operations (HTTP {response.status_code})")
            return
        
        data = response.json()
        operation_types = data.get("operation_types", [])
        
        # Operation selector
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            selected_op = st.selectbox(
                "Operation Type",
                options=operation_types,
                format_func=lambda x: x.replace("_", " ").title(),
                key="perf_op_selector"
            )
        
        with col2:
            metric_type = st.selectbox(
                "Metric Type",
                options=["duration", "throughput", "count"],
                key="perf_metric_selector"
            )
        
        with col3:
            time_window = st.selectbox(
                "Time Window",
                options=[15, 60, 240, None],
                format_func=lambda x: f"{x} min" if x else "All time",
                key="perf_time_window"
            )
        
        # Get stats
        params = {
            "metric_type": metric_type
        }
        if time_window:
            params["time_window_minutes"] = time_window
        
        response = api_client.get(
            f"/performance/stats/{selected_op}",
            params=params
        )
        
        if response.status_code != 200:
            st.warning(f"ℹ️ No data available for {selected_op}")
            return
        
        stats = response.json()
        
        if not stats:
            st.info(f"ℹ️ No statistics available for {selected_op} yet.")
            return
        
        # Display stats
        st.divider()
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Count", f"{stats.get('count', 0):,}")
        
        with col2:
            st.metric("Avg", f"{stats.get('avg', 0):.1f}")
        
        with col3:
            st.metric("Median", f"{stats.get('median', 0):.1f}")
        
        with col4:
            st.metric("P95", f"{stats.get('p95', 0):.1f}")
        
        with col5:
            st.metric("P99", f"{stats.get('p99', 0):.1f}")
        
        # Box plot
        st.subheader("📈 Distribution")
        
        fig = go.Figure()
        
        fig.add_trace(go.Box(
            y=[
                stats.get('min', 0),
                stats.get('avg', 0),
                stats.get('median', 0),
                stats.get('p95', 0),
                stats.get('p99', 0),
                stats.get('max', 0)
            ],
            name=selected_op.replace("_", " ").title(),
            boxmean='sd'
        ))
        
        fig.update_layout(
            title=f"{selected_op.replace('_', ' ').title()} - {metric_type.title()}",
            yaxis_title=f"{metric_type.title()} Value",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"❌ Error loading operation stats: {str(e)}")


def render_recommendations_tab(api_client):
    """Render recommendations tab."""
    st.subheader("💡 Optimization Recommendations")
    
    try:
        # Get bottlenecks for recommendations
        response = api_client.get("/performance/bottlenecks")
        
        if response.status_code != 200:
            st.error(f"❌ Failed to fetch recommendations (HTTP {response.status_code})")
            return
        
        bottlenecks = response.json()
        
        if not bottlenecks:
            st.success("✅ No optimization recommendations at this time. System is performing well!")
            return
        
        # Group by severity
        critical = [b for b in bottlenecks if b.get("severity") == "critical"]
        high = [b for b in bottlenecks if b.get("severity") == "high"]
        medium = [b for b in bottlenecks if b.get("severity") == "medium"]
        
        # Critical recommendations
        if critical:
            st.error("🔴 **Critical Issues (Immediate Action Required)**")
            for b in critical:
                st.markdown(f"**{b.get('operation_type', 'Unknown').replace('_', ' ').title()}**")
                st.markdown(f"- {b.get('recommendation', 'No recommendation')}")
                st.markdown("")
        
        # High priority recommendations
        if high:
            st.warning("🟠 **High Priority Optimizations**")
            for b in high:
                st.markdown(f"**{b.get('operation_type', 'Unknown').replace('_', ' ').title()}**")
                st.markdown(f"- {b.get('recommendation', 'No recommendation')}")
                st.markdown("")
        
        # Medium priority recommendations
        if medium:
            st.info("🟡 **Medium Priority Improvements**")
            for b in medium:
                st.markdown(f"**{b.get('operation_type', 'Unknown').replace('_', ' ').title()}**")
                st.markdown(f"- {b.get('recommendation', 'No recommendation')}")
                st.markdown("")
        
        # General recommendations
        st.divider()
        st.subheader("📚 General Best Practices")
        
        st.markdown("""
        **Ingestion Optimization:**
        - Enable sub-job orchestration for large repositories
        - Use incremental documentation for updates
        - Increase batch sizes for embedding generation
        
        **Embedding Performance:**
        - Use FastEmbed service for 5-10× speedup
        - Batch embeddings (50-100 per batch)
        - Enable Redis embedding cache
        
        **RAG Query Optimization:**
        - Cache frequent queries
        - Optimize context size
        - Use hierarchical contexts for filtering
        
        **Database Performance:**
        - Add indexes on frequently queried columns
        - Use connection pooling
        - Review slow query logs
        
        **Caching Strategy:**
        - Enable L1 (memory) + L2 (Redis) caching
        - Set appropriate TTLs
        - Monitor cache hit rates
        """)
    
    except Exception as e:
        st.error(f"❌ Error loading recommendations: {str(e)}")


# Main entry point
if __name__ == "__main__":
    render_performance_monitor()
else:
    render_performance_monitor()

