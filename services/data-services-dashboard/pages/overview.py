"""Overview Page - Main dashboard overview for the Data Services Dashboard.

This module provides the main overview dashboard with service health, key metrics,
and navigation to different data services.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List

import httpx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


async def check_service_health(service_name: str, url: str) -> Dict[str, Any]:
    """Check the health of a specific service."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                return {
                    "name": service_name,
                    "status": "healthy",
                    "response_time": response.elapsed.total_seconds(),
                    "data": data,
                }
            else:
                return {"name": service_name, "status": "unhealthy", "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"name": service_name, "status": "unhealthy", "error": str(e)}


def render_overview_page():
    """Render the main overview dashboard page."""
    st.markdown("## 📊 Dashboard Overview")
    st.markdown(
        "Welcome to the Data Services Dashboard. Monitor and manage your Memory Agent, Prompt Store, and Document Store services."
    )

    # Service Health Overview
    st.markdown("### 🔧 Service Health Status")

    # Check service health
    services = [
        ("Memory Agent", "http://localhost:5040/health"),
        ("Prompt Store", "http://localhost:8080/health"),
        ("Document Store", "http://localhost:8081/health"),
    ]

    # Run health checks asynchronously
    health_results = asyncio.run(check_all_services(services))

    # Display health status
    render_health_status_grid(health_results)

    # Key Metrics
    st.markdown("---")
    st.markdown("### 📈 Key Metrics")

    render_key_metrics(health_results)

    # Quick Actions
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")

    render_quick_actions()

    # Recent Activity
    st.markdown("---")
    st.markdown("### 📋 Recent Activity")

    render_recent_activity()


async def check_all_services(services: List[tuple]) -> List[Dict[str, Any]]:
    """Check health of all services concurrently."""
    tasks = [check_service_health(name, url) for name, url in services]
    return await asyncio.gather(*tasks)


def render_health_status_grid(health_results: List[Dict[str, Any]]):
    """Render the service health status grid."""
    cols = st.columns(len(health_results))

    for col, result in zip(cols, health_results):
        with col:
            service_name = result["name"]
            status = result["status"]

            if status == "healthy":
                st.success(f"🟢 {service_name}")
                if "response_time" in result:
                    st.caption(".2f")
            else:
                st.error(f"🔴 {service_name}")
                if "error" in result:
                    st.caption(f"Error: {result['error']}")


def render_key_metrics(health_results: List[Dict[str, Any]]):
    """Render key performance metrics."""
    # Calculate metrics
    healthy_services = sum(1 for r in health_results if r["status"] == "healthy")
    total_services = len(health_results)
    avg_response_time = sum(r.get("response_time", 0) for r in health_results) / len(health_results)

    # Create metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        health_percentage = (healthy_services / total_services) * 100
        st.metric(
            label="Service Health",
            value=".1f",
            delta="+5.2%" if healthy_services == total_services else "-20.0%",
            help="Percentage of services that are healthy",
        )

    with col2:
        st.metric(
            label="Active Services",
            value=f"{healthy_services}/{total_services}",
            delta="+1" if healthy_services > 0 else "0",
            help="Number of active vs total services",
        )

    with col3:
        st.metric(
            label="Avg Response Time", value=".2f", delta="-0.05s", help="Average response time across all services"
        )

    with col4:
        total_items = 1250  # Mock data - would come from actual service APIs
        st.metric(
            label="Total Data Items", value=f"{total_items:,}", delta="+125", help="Total items across all services"
        )


def render_quick_actions():
    """Render quick action buttons."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🧠 Browse Memory", key="quick_memory", use_container_width=True):
            st.session_state.current_page = "memory_browser"
            st.rerun()

    with col2:
        if st.button("📝 Manage Prompts", key="quick_prompts", use_container_width=True):
            st.session_state.current_page = "prompt_browser"
            st.rerun()

    with col3:
        if st.button("📄 Browse Documents", key="quick_documents", use_container_width=True):
            st.session_state.current_page = "document_browser"
            st.rerun()

    with col4:
        if st.button("🔍 Advanced Search", key="quick_search", use_container_width=True):
            st.session_state.current_page = "search"
            st.rerun()


def render_recent_activity():
    """Render recent activity feed."""
    # Mock activity data - would come from actual service logs
    activities = [
        {"time": "2 minutes ago", "action": "New prompt created", "service": "Prompt Store", "user": "system"},
        {"time": "5 minutes ago", "action": "Document uploaded", "service": "Document Store", "user": "admin"},
        {"time": "8 minutes ago", "action": "Memory item added", "service": "Memory Agent", "user": "system"},
        {"time": "12 minutes ago", "action": "Prompt forked", "service": "Prompt Store", "user": "developer"},
        {"time": "15 minutes ago", "action": "Document tagged", "service": "Document Store", "user": "analyst"},
    ]

    for activity in activities:
        col1, col2 = st.columns([1, 4])

        with col1:
            # Service icon
            service_icons = {"Memory Agent": "🧠", "Prompt Store": "📝", "Document Store": "📄"}
            st.markdown(f"{service_icons.get(activity['service'], '📊')}")

        with col2:
            st.markdown(f"**{activity['action']}** - {activity['service']}")
            st.caption(f"{activity['time']} by {activity['user']}")

        st.markdown("---")
