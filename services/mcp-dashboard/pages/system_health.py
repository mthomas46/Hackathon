"""System Health - Monitor service health and system status."""

import streamlit as st
import pandas as pd


def render():
    """Render the system health page."""
    
    st.title("💚 System Health")
    st.markdown("Monitor service status and system metrics")
    
    # Overall health
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Overall Status", "Healthy", delta="✓")
    
    with col2:
        st.metric("Services Online", "9/11", delta="-2")
    
    with col3:
        st.metric("Uptime", "99.8%", delta="+0.1%")
    
    with col4:
        st.metric("Alerts", "2", delta="+1")
    
    # Service status
    st.markdown("---")
    st.subheader("📡 Service Status")
    
    services = [
        {"name": "MCP Provisioner", "port": 5001, "status": "🟢 Healthy", "uptime": "15d", "response": "45ms"},
        {"name": "MCP Composer", "port": 5002, "status": "🟢 Healthy", "uptime": "15d", "response": "32ms"},
        {"name": "MCP Orchestrator", "port": 5003, "status": "🟢 Healthy", "uptime": "15d", "response": "78ms"},
        {"name": "MCP Interpreter", "port": 5004, "status": "🟢 Healthy", "uptime": "15d", "response": "23ms"},
        {"name": "MCP Registry", "port": 5005, "status": "🔴 Offline", "uptime": "-", "response": "-"},
        {"name": "API Gateway", "port": 5006, "status": "🟢 Healthy", "uptime": "15d", "response": "12ms"},
        {"name": "Training Coordinator", "port": 5007, "status": "🟡 Degraded", "uptime": "15d", "response": "234ms"},
        {"name": "MCP Performance Store", "port": 5649, "status": "🟢 Healthy", "uptime": "2d", "response": "28ms"},
        {"name": "MCP Store", "port": 5648, "status": "🟢 Healthy", "uptime": "2d", "response": "35ms"},
        {"name": "Log Collector", "port": 5008, "status": "🟢 Healthy", "uptime": "15d", "response": "18ms"},
        {"name": "Redis", "port": 6379, "status": "🟢 Healthy", "uptime": "15d", "response": "2ms"},
    ]
    
    # Create dataframe
    df = pd.DataFrame(services)
    
    # Display as table
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # System metrics
    st.markdown("---")
    st.subheader("💻 System Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### CPU Usage")
        st.metric("Average", "34%", delta="-2%")
        st.progress(34)
        
    with col2:
        st.markdown("#### Memory Usage")
        st.metric("Average", "52%", delta="+3%")
        st.progress(52)
    
    with col3:
        st.markdown("#### Disk Usage")
        st.metric("Average", "41%", delta="+5%")
        st.progress(41)
    
    # Active alerts
    st.markdown("---")
    st.subheader("⚠️ Active Alerts")
    
    alerts = [
        {
            "severity": "🟡 Warning",
            "service": "Training Coordinator",
            "message": "High response time (>200ms) for 10+ minutes",
            "time": "5 minutes ago"
        },
        {
            "severity": "🔴 Critical",
            "service": "MCP Registry",
            "message": "Service offline - health check failing",
            "time": "12 minutes ago"
        }
    ]
    
    for alert in alerts:
        with st.expander(f"{alert['severity']} {alert['service']} - {alert['time']}", expanded=True):
            st.markdown(f"**Message:** {alert['message']}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔍 Investigate", key=f"inv_{alert['service']}"):
                    st.info("Opening detailed logs...")
            with col2:
                if st.button("✓ Acknowledge", key=f"ack_{alert['service']}"):
                    st.success("Alert acknowledged")
