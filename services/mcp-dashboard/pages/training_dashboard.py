"""Training Dashboard - Monitor training jobs and pipelines."""

import streamlit as st
import pandas as pd


def render():
    """Render the training dashboard page."""
    
    st.title("🎓 Training Dashboard")
    st.markdown("Monitor MCP training jobs and data pipelines")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["⏳ Active Jobs", "✅ Completed", "📊 Statistics"])
    
    with tab1:
        render_active_jobs()
    
    with tab2:
        render_completed_jobs()
    
    with tab3:
        render_statistics()


def render_active_jobs():
    """Render active training jobs."""
    
    st.subheader("Active Training Jobs")
    
    jobs = [
        {
            "id": "job-001",
            "mcp": "customer-support",
            "source": "GitHub + Confluence",
            "progress": 67,
            "eta": "12 min",
            "documents": "12,450 / 18,500"
        },
        {
            "id": "job-002",
            "mcp": "product-docs",
            "source": "Documentation Site",
            "progress": 34,
            "eta": "25 min",
            "documents": "3,200 / 9,400"
        }
    ]
    
    for job in jobs:
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"### 🔄 {job['mcp']}")
                st.caption(f"Job ID: {job['id']} | Source: {job['source']}")
                st.progress(job['progress'] / 100)
                st.caption(f"{job['progress']}% complete • {job['documents']} documents • ETA: {job['eta']}")
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("⏸️ Pause", key=f"pause_{job['id']}", use_container_width=True):
                    st.info("Job paused")
                if st.button("🗑️ Cancel", key=f"cancel_{job['id']}", use_container_width=True):
                    st.warning("Job cancelled")
            
            st.markdown("---")
    
    if not jobs:
        st.info("No active training jobs")


def render_completed_jobs():
    """Render completed training jobs."""
    
    st.subheader("Recently Completed Jobs")
    
    completed = pd.DataFrame({
        "Job ID": ["job-003", "job-004", "job-005"],
        "MCP": ["code-analysis", "sales-insights", "customer-support"],
        "Duration": ["18 min", "32 min", "45 min"],
        "Documents": ["15.2K", "8.7K", "23.5K"],
        "Completed": ["2 hours ago", "5 hours ago", "1 day ago"],
        "Status": ["✅ Success", "✅ Success", "✅ Success"]
    })
    
    st.dataframe(completed, use_container_width=True, hide_index=True)


def render_statistics():
    """Render training statistics."""
    
    st.subheader("Training Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Jobs", "127", delta="+5 this week")
    
    with col2:
        st.metric("Success Rate", "98.4%", delta="+0.3%")
    
    with col3:
        st.metric("Avg Duration", "28 min", delta="-3 min")
    
    with col4:
        st.metric("Total Documents", "456K", delta="+42K")
    
    st.markdown("---")
    
    # Job distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Jobs by Source")
        source_data = pd.DataFrame({
            "Source": ["GitHub", "Confluence", "Documentation", "Upload"],
            "Count": [45, 32, 28, 22]
        })
        st.bar_chart(source_data.set_index("Source"))
    
    with col2:
        st.subheader("Processing Time Distribution")
        time_data = pd.DataFrame({
            "Duration": ["<10 min", "10-30 min", "30-60 min", ">60 min"],
            "Count": [18, 65, 34, 10]
        })
        st.bar_chart(time_data.set_index("Duration"))
