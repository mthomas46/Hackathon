"""Evergreen Documentation Management UI."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd

# Page config
st.set_page_config(
    page_title="Evergreen Documentation",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Evergreen Documentation System")
st.markdown("**Bi-directional sync, self-healing, and auto-archiving for documentation**")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Health Dashboard",
    "🔄 Sync Management",
    "🏥 Self-Healing",
    "📈 Analytics"
])

# Tab 1: Health Dashboard
with tab1:
    st.subheader("Documentation Health Overview")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Documents", "247", delta="12 this week")
    
    with col2:
        st.metric("Avg Health Score", "87.3%", delta="2.1%")
    
    with col3:
        st.metric("Stale Documents", "15", delta="-3", delta_color="inverse")
    
    with col4:
        st.metric("Auto-Healed", "8", delta="5")
    
    st.divider()
    
    # Health distribution
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("### 📊 Health Score Distribution")
        
        health_ranges = ["90-100 (Excellent)", "70-89 (Good)", "50-69 (Fair)", "0-49 (Poor)"]
        counts = [180, 45, 15, 7]
        colors = ["#00CC96", "#636EFA", "#FFA15A", "#EF553B"]
        
        fig = go.Figure(data=[go.Bar(
            x=health_ranges,
            y=counts,
            marker_color=colors
        )])
        fig.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col_chart2:
        st.markdown("### ⏰ Document Age Distribution")
        
        age_ranges = ["<30 days", "30-90 days", "90-180 days", ">180 days"]
        counts = [120, 85, 30, 12]
        
        fig = go.Figure(data=[go.Pie(
            labels=age_ranges,
            values=counts,
            hole=.3
        )])
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Documents needing attention
    st.markdown("### ⚠️ Documents Needing Attention")
    
    issues_data = [
        {"Document": "API Authentication Guide", "Health": 45, "Issues": "Stale (120 days), 5 broken links", "Action": "Auto-archive"},
        {"Document": "Deployment Manual", "Health": 62, "Issues": "Stale (95 days)", "Action": "Update needed"},
        {"Document": "Database Schema", "Health": 58, "Issues": "3 empty sections", "Action": "Manual review"},
        {"Document": "Security Policy", "Health": 71, "Issues": "Outdated references (2021)", "Action": "Update"},
    ]
    
    df_issues = pd.DataFrame(issues_data)
    
    for _, row in df_issues.iterrows():
        col1, col2, col3, col4 = st.columns([3, 1, 2, 1])
        
        with col1:
            st.text(row["Document"])
        
        with col2:
            health_color = "🟢" if row["Health"] >= 70 else "🟡" if row["Health"] >= 50 else "🔴"
            st.text(f"{health_color} {row['Health']}%")
        
        with col3:
            st.caption(row["Issues"])
        
        with col4:
            st.button("Fix", key=f"fix_{row['Document']}")

# Tab 2: Sync Management
with tab2:
    st.subheader("Bi-directional Sync Management")
    
    # Sync status
    col_sync1, col_sync2, col_sync3 = st.columns(3)
    
    with col_sync1:
        st.metric("Last Sync", "5 min ago")
    
    with col_sync2:
        st.metric("Sync Success Rate", "98.7%")
    
    with col_sync3:
        st.metric("Conflicts Resolved", "3")
    
    st.divider()
    
    # Sync controls
    col_ctrl1, col_ctrl2 = st.columns([2, 1])
    
    with col_ctrl1:
        st.markdown("### 🔄 Manual Sync")
        
        sync_direction = st.selectbox(
            "Sync Direction",
            ["MCP → Confluence", "Confluence → MCP", "Bi-directional"]
        )
        
        space_key = st.text_input("Confluence Space Key", value="DOCS")
        
        conflict_resolution = st.selectbox(
            "Conflict Resolution",
            ["Last Modified Wins", "MCP Wins", "Confluence Wins", "Manual Review"]
        )
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🚀 Start Sync", use_container_width=True, type="primary"):
                with st.spinner("Syncing..."):
                    st.success("✅ Sync completed successfully!")
        
        with col_btn2:
            if st.button("📅 Schedule Sync", use_container_width=True):
                st.info("Sync scheduled for every 30 minutes")
    
    with col_ctrl2:
        st.markdown("### 📋 Sync Schedule")
        
        schedules = [
            {"Space": "DOCS", "Interval": "30 min", "Status": "✅ Active"},
            {"Space": "ENG", "Interval": "1 hour", "Status": "✅ Active"},
            {"Space": "PROD", "Interval": "2 hours", "Status": "⏸️ Paused"},
        ]
        
        for sched in schedules:
            st.text(f"{sched['Status']} {sched['Space']} - {sched['Interval']}")
    
    st.divider()
    
    # Recent sync history
    st.markdown("### 📜 Recent Sync Operations")
    
    sync_history = [
        {"Time": "2 min ago", "Direction": "MCP→Confluence", "Docs": "5", "Conflicts": "0", "Status": "✅"},
        {"Time": "32 min ago", "Direction": "Bi-directional", "Docs": "12", "Conflicts": "1", "Status": "✅"},
        {"Time": "1 hour ago", "Direction": "Confluence→MCP", "Docs": "3", "Conflicts": "0", "Status": "✅"},
    ]
    
    df_sync = pd.DataFrame(sync_history)
    st.dataframe(df_sync, use_container_width=True, hide_index=True)

# Tab 3: Self-Healing
with tab3:
    st.subheader("Self-Healing Documentation")
    
    # Healing stats
    col_heal1, col_heal2, col_heal3, col_heal4 = st.columns(4)
    
    with col_heal1:
        st.metric("Auto-Healed (Today)", "8")
    
    with col_heal2:
        st.metric("Pending Actions", "3")
    
    with col_heal3:
        st.metric("Success Rate", "94.5%")
    
    with col_heal4:
        st.metric("Time Saved", "2.5 hrs")
    
    st.divider()
    
    # Healing rules
    st.markdown("### ⚙️ Healing Rules")
    
    rules = [
        {"Rule": "Auto-archive Stale", "Trigger": ">90 days", "Action": "Archive", "Auto": True, "Count": "15"},
        {"Rule": "Notify Broken Links", "Trigger": ">3 links", "Action": "Notify", "Auto": True, "Count": "8"},
        {"Rule": "Update from Source", "Trigger": "Source changed", "Action": "Update", "Auto": True, "Count": "12"},
        {"Rule": "Recreate Deleted", "Trigger": "Unexpected delete", "Action": "Recreate", "Auto": False, "Count": "2"},
    ]
    
    for rule in rules:
        with st.expander(f"**{rule['Rule']}** ({rule['Count']} triggered)"):
            col_r1, col_r2, col_r3, col_r4 = st.columns(4)
            
            with col_r1:
                st.text(f"Trigger: {rule['Trigger']}")
            
            with col_r2:
                st.text(f"Action: {rule['Action']}")
            
            with col_r3:
                auto_status = "✅ Auto" if rule['Auto'] else "👤 Manual"
                st.text(auto_status)
            
            with col_r4:
                st.button("Configure", key=f"config_{rule['Rule']}")
    
    st.divider()
    
    # Recent healing operations
    st.markdown("### 🔧 Recent Healing Operations")
    
    healing_ops = [
        {"Time": "5 min ago", "Document": "Old API Guide", "Action": "Auto-archived", "Status": "✅"},
        {"Time": "1 hour ago", "Document": "Setup Guide", "Action": "Fixed broken links", "Status": "✅"},
        {"Time": "3 hours ago", "Document": "FAQ", "Action": "Updated from source", "Status": "✅"},
    ]
    
    df_healing = pd.DataFrame(healing_ops)
    st.dataframe(df_healing, use_container_width=True, hide_index=True)

# Tab 4: Analytics
with tab4:
    st.subheader("Documentation Analytics")
    
    # Time series
    st.markdown("### 📈 Health Score Trend (30 Days)")
    
    days = [(datetime.now() - timedelta(days=29-i)).strftime('%m/%d') for i in range(30)]
    scores = [82, 83, 85, 84, 86, 87, 85, 86, 88, 87, 89, 88, 90, 89, 88, 
              87, 88, 89, 87, 86, 88, 89, 87, 88, 89, 86, 87, 88, 87, 87]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=days,
        y=scores,
        mode='lines+markers',
        fill='tozeroy',
        line=dict(color='#00CC96', width=2)
    ))
    fig.update_layout(
        height=300,
        xaxis_title="Date",
        yaxis_title="Avg Health Score",
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Issue breakdown
    col_analytics1, col_analytics2 = st.columns(2)
    
    with col_analytics1:
        st.markdown("### 🚨 Issue Types")
        
        issues = ["Stale Content", "Broken Links", "Empty Sections", "Outdated Refs"]
        counts = [15, 12, 8, 5]
        
        fig = go.Figure(data=[go.Bar(x=issues, y=counts)])
        fig.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col_analytics2:
        st.markdown("### 🔧 Healing Actions")
        
        actions = ["Auto-archived", "Updated", "Notified", "Fixed Links"]
        counts = [15, 12, 8, 6]
        
        fig = go.Figure(data=[go.Pie(labels=actions, values=counts, hole=.3)])
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

# Footer
st.divider()
st.caption("💡 Tip: Enable auto-healing rules to maintain documentation health automatically")

