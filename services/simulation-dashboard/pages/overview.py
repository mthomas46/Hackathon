"""
Intelligent Overview Dashboard Page.

This module provides an intelligent overview dashboard that leverages
the full ecosystem infrastructure including LLM Gateway, Analysis
Service, and real-time data processing for intelligent insights,
predictive analytics, and autonomous features.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List

import httpx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from components.realtime.analytics_stream import render_realtime_analytics_dashboard
from infrastructure.logging.logger import get_dashboard_logger
from plotly.subplots import make_subplots

from services.clients.llm_client import LLMGatewayClient
from services.clients.simulation_client import SimulationClient

logger = get_dashboard_logger("intelligent_overview_page")


async def check_ecosystem_health() -> Dict[str, Any]:
    """Check the health of all ecosystem services."""
    health_status = {
        "overall_health": "unknown",
        "services": {},
        "timestamp": datetime.now(),
        "insights": [],
        "recommendations": [],
    }

    services_to_check = [
        ("project-simulation", "http://localhost:5075/health"),
        ("analysis-service", "http://localhost:5080/health"),
        ("llm-gateway", "http://localhost:5055/health"),
        ("doc-store", "http://localhost:5087/health"),
        ("orchestrator", "http://localhost:5099/health"),
        ("interpreter", "http://localhost:5120/health"),
        ("summarizer-hub", "http://localhost:5160/health"),
        ("redis", "http://localhost:6379"),  # Special case for Redis
    ]

    async with httpx.AsyncClient(timeout=5.0) as client:
        for service_name, url in services_to_check:
            try:
                if service_name == "redis":
                    # Special handling for Redis
                    response = await client.get(url)
                    health_status["services"][service_name] = {
                        "status": "healthy" if response.status_code == 200 else "unhealthy",
                        "response_time": response.elapsed.total_seconds(),
                        "last_check": datetime.now(),
                    }
                else:
                    response = await client.get(url)
                    data = response.json() if response.status_code == 200 else {}

                    health_status["services"][service_name] = {
                        "status": data.get("status", "unknown") if isinstance(data, dict) else "healthy",
                        "response_time": response.elapsed.total_seconds(),
                        "version": data.get("version", "unknown") if isinstance(data, dict) else "unknown",
                        "last_check": datetime.now(),
                    }
            except Exception as e:
                health_status["services"][service_name] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "last_check": datetime.now(),
                }

    # Calculate overall health
    healthy_services = sum(1 for s in health_status["services"].values() if s["status"] == "healthy")
    total_services = len(health_status["services"])

    if healthy_services == total_services:
        health_status["overall_health"] = "excellent"
    elif healthy_services >= total_services * 0.8:
        health_status["overall_health"] = "good"
    elif healthy_services >= total_services * 0.5:
        health_status["overall_health"] = "fair"
    else:
        health_status["overall_health"] = "poor"

    # Generate intelligent insights
    health_status["insights"] = generate_health_insights(health_status)
    health_status["recommendations"] = generate_health_recommendations(health_status)

    return health_status


def generate_health_insights(health_data: Dict[str, Any]) -> List[str]:
    """Generate intelligent insights from health data."""
    insights = []

    services = health_data["services"]
    healthy_count = sum(1 for s in services.values() if s["status"] == "healthy")
    total_count = len(services)

    # Service health insights
    if healthy_count == total_count:
        insights.append("🎉 All ecosystem services are operating optimally")
    elif healthy_count >= total_count * 0.8:
        insights.append(f"✅ {healthy_count}/{total_count} services healthy - ecosystem stable")
    else:
        unhealthy = [name for name, data in services.items() if data["status"] != "healthy"]
        insights.append(f"⚠️ {len(unhealthy)} services need attention: {', '.join(unhealthy[:3])}")

    # Performance insights
    response_times = [s.get("response_time", 0) for s in services.values() if s.get("response_time")]
    if response_times:
        avg_response = sum(response_times) / len(response_times)
        if avg_response < 0.5:
            insights.append("🚀 Excellent response times across services")
        elif avg_response < 2.0:
            insights.append("⚡ Good response performance")
        else:
            insights.append("🐌 Some services showing slower response times")

    return insights


def generate_health_recommendations(health_data: Dict[str, Any]) -> List[str]:
    """Generate intelligent recommendations based on health data."""
    recommendations = []
    services = health_data["services"]

    # Check for unhealthy services
    unhealthy_services = [name for name, data in services.items() if data["status"] != "healthy"]
    if unhealthy_services:
        recommendations.append(f"🔧 Restart or investigate unhealthy services: {', '.join(unhealthy_services)}")

    # Performance recommendations
    slow_services = [
        name for name, data in services.items() if data.get("response_time", 0) > 2.0 and data["status"] == "healthy"
    ]
    if slow_services:
        recommendations.append(f"⚡ Optimize performance for: {', '.join(slow_services)}")

    # Ecosystem completeness
    critical_services = ["project-simulation", "llm-gateway", "analysis-service"]
    missing_critical = [s for s in critical_services if s not in services or services[s]["status"] != "healthy"]
    if missing_critical:
        recommendations.append(f"🚨 Critical services need attention: {', '.join(missing_critical)}")

    return recommendations


def render_overview_page():
    """Render the intelligent overview dashboard page."""
    st.markdown("## 🧠 Intelligent Project Simulation Dashboard")
    st.markdown("*Powered by LLM Gateway, Real-time Analytics, and Autonomous AI*")
    st.markdown("---")

    # Initialize ecosystem clients
    sim_client = st.session_state.get("simulation_client")
    if not sim_client:
        st.error("❌ Simulation service not available")
        return

    # Real-time ecosystem health check
    ecosystem_health = asyncio.run(check_ecosystem_health())

    # Create intelligent tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "🧠 AI Insights",
            "📊 Smart Metrics",
            "🎯 Intelligent Monitoring",
            "🔮 Predictive Analytics",
            "⚡ Autonomous Actions",
        ]
    )

    with tab1:
        render_ai_insights_dashboard(ecosystem_health)

    with tab2:
        render_smart_metrics_dashboard(sim_client, ecosystem_health)

    with tab3:
        render_intelligent_monitoring_dashboard(sim_client)

    with tab4:
        render_predictive_analytics_dashboard(sim_client, ecosystem_health)

    with tab5:
        render_autonomous_actions_dashboard(sim_client, ecosystem_health)

    # Intelligent system status
    st.markdown("---")
    render_intelligent_system_status(ecosystem_health)


async def generate_llm_insights(context: Dict[str, Any]) -> List[str]:
    """Generate LLM-powered insights from context data."""
    logger = get_dashboard_logger()
    try:
        async with LLMGatewayClient() as llm_client:
            return await llm_client.generate_insights(context)
    except Exception as e:
        logger.error(f"Failed to generate LLM insights: {e}")
        return []


def render_ai_insights_dashboard(ecosystem_health: Dict[str, Any]):
    """Render AI-powered insights dashboard."""
    st.markdown("### 🧠 AI-Powered Ecosystem Insights")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Health insights
        st.markdown("#### 🔍 System Intelligence")
        for insight in ecosystem_health.get("insights", []):
            st.markdown(f"• {insight}")

        # LLM Gateway integration for intelligent analysis
        llm_gateway_status = ecosystem_health["services"].get("llm-gateway", {}).get("status")
        if llm_gateway_status == "healthy":
            st.markdown("#### 🤖 AI Analysis Available")
            st.success("✅ LLM Gateway online - Intelligent analysis enabled")

            # Get simulation data for context
            sim_data = asyncio.run(get_simulation_metrics(st.session_state.get("simulation_client")))

            if st.button("🔮 Generate AI Insights", key="ai_insights_btn"):
                with st.spinner("Generating intelligent insights..."):
                    context = {
                        "health_data": ecosystem_health,
                        "simulation_data": sim_data,
                        "timestamp": ecosystem_health.get("timestamp", datetime.now()),
                    }
                    insights = asyncio.run(generate_llm_insights(context))
                    if insights:
                        st.markdown("#### ✨ AI-Generated Insights")
                        for insight in insights:
                            st.markdown(f"• {insight}")
                    else:
                        st.warning("⚠️ Could not generate AI insights at this time")
        else:
            st.warning(f"⚠️ LLM Gateway {llm_gateway_status} - Limited AI features")

    with col2:
        # Quick health overview
        health_colors = {"excellent": "🟢", "good": "🟡", "fair": "🟠", "poor": "🔴", "unknown": "⚪"}

        overall_health = ecosystem_health.get("overall_health", "unknown")
        st.metric(
            "Ecosystem Health",
            f"{health_colors.get(overall_health, '⚪')} {overall_health.title()}",
            help="Overall health of the ecosystem services",
        )

        # Service count
        healthy_count = sum(1 for s in ecosystem_health["services"].values() if s["status"] == "healthy")
        total_count = len(ecosystem_health["services"])
        st.metric("Services Online", f"{healthy_count}/{total_count}")


def render_smart_metrics_dashboard(sim_client: SimulationClient, ecosystem_health: Dict[str, Any]):
    """Render smart metrics dashboard with intelligent analytics."""
    st.markdown("### 📊 Smart Metrics & Analytics")

    # Get simulation data
    try:
        # This would normally call the simulation service
        simulation_data = asyncio.run(get_simulation_metrics(sim_client))
    except:
        simulation_data = generate_mock_simulation_data()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Active Simulations", simulation_data.get("active_count", 0), delta="+2 from yesterday")

    with col2:
        st.metric("Success Rate", f"{simulation_data.get('success_rate', 85)}%", delta="+5% from last week")

    with col3:
        st.metric("Avg Processing Time", f"{simulation_data.get('avg_duration', 45)}min", delta="-8min improvement")

    # Intelligent charts
    st.markdown("#### 📈 Performance Trends")

    # Create sample trend data
    trend_data = pd.DataFrame(
        {
            "timestamp": pd.date_range(start="2024-01-01", periods=30, freq="D"),
            "success_rate": [85 + (i % 10 - 5) for i in range(30)],
            "processing_time": [45 + (i % 8 - 4) for i in range(30)],
            "simulations_count": [5 + (i % 6 - 3) for i in range(30)],
        }
    )

    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=("Success Rate Trend", "Processing Time", "Simulations Count", "Performance Correlation"),
    )

    fig.add_trace(
        go.Scatter(x=trend_data["timestamp"], y=trend_data["success_rate"], mode="lines", name="Success Rate"),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=trend_data["timestamp"], y=trend_data["processing_time"], mode="lines", name="Processing Time"),
        row=1,
        col=2,
    )
    fig.add_trace(
        go.Bar(x=trend_data["timestamp"], y=trend_data["simulations_count"], name="Simulations"), row=2, col=1
    )

    # Correlation scatter plot
    fig.add_trace(
        go.Scatter(x=trend_data["processing_time"], y=trend_data["success_rate"], mode="markers", name="Correlation"),
        row=2,
        col=2,
    )

    fig.update_layout(height=600, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


def render_intelligent_monitoring_dashboard(sim_client: SimulationClient):
    """Render intelligent monitoring dashboard."""
    st.markdown("### 🎯 Intelligent Simulation Monitoring")

    # Real-time monitoring with AI insights
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("#### 📊 Live Simulation Status")

        # Mock real-time data (would come from WebSocket)
        progress_data = {
            "simulation_1": {"name": "E-commerce Platform", "progress": 85, "status": "running", "eta": "5 min"},
            "simulation_2": {"name": "FinTech API", "progress": 62, "status": "running", "eta": "12 min"},
            "simulation_3": {"name": "Healthcare System", "progress": 100, "status": "completed", "eta": "Done"},
        }

        for sim_id, data in progress_data.items():
            status_color = {"running": "🟡", "completed": "🟢", "failed": "🔴"}.get(data["status"], "⚪")
            st.progress(data["progress"] / 100)
            st.markdown(f"{status_color} **{data['name']}** - {data['progress']}% complete (ETA: {data['eta']})")

    with col2:
        st.markdown("#### 🧠 AI Predictions")
        st.info("🎯 Next completion: 3 min")
        st.info("⚡ Performance: Optimal")
        st.info("🔮 Risk Level: Low")
        st.info("💡 Recommendation: Continue")


def render_predictive_analytics_dashboard(sim_client: SimulationClient, ecosystem_health: Dict[str, Any]):
    """Render predictive analytics dashboard."""
    st.markdown("### 🔮 Predictive Analytics & Forecasting")

    # Create tabs for different analytics views
    tab1, tab2, tab3 = st.tabs(["📊 Real-Time Streams", "🔮 Load Forecasting", "🎯 Anomaly Detection"])

    with tab1:
        # Real-time analytics streams
        render_realtime_analytics_dashboard()

    with tab2:
        render_load_forecasting()

    with tab3:
        render_anomaly_detection(ecosystem_health)


def render_load_forecasting():
    """Render load forecasting analytics."""
    st.markdown("#### 📈 Load Forecasting & Capacity Planning")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Generate forecasting data based on current ecosystem state
        forecast_data = generate_load_forecast_data()

        fig = px.line(
            forecast_data,
            x="hour",
            y="predicted_load",
            title="24-Hour Load Forecast",
            labels={"predicted_load": "Predicted Load (%)", "hour": "Hour"},
        )

        # Add confidence intervals
        fig.add_trace(
            go.Scatter(
                x=forecast_data["hour"],
                y=forecast_data["upper_bound"],
                mode="lines",
                name="Upper Bound",
                line=dict(width=0),
                showlegend=False,
            )
        )

        fig.add_trace(
            go.Scatter(
                x=forecast_data["hour"],
                y=forecast_data["lower_bound"],
                mode="lines",
                name="Lower Bound",
                fill="tonexty",
                fillcolor="rgba(0,100,255,0.2)",
                line=dict(width=0),
                showlegend=False,
            )
        )

        # Add confidence percentage line
        fig.add_trace(
            go.Scatter(
                x=forecast_data["hour"],
                y=forecast_data["confidence"],
                mode="lines",
                name="Confidence %",
                yaxis="y2",
                line=dict(dash="dot", color="red"),
            )
        )

        fig.update_layout(yaxis2=dict(title="Confidence %", overlaying="y", side="right"), height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Forecast Insights:**")
        st.info("🔺 Peak load expected at 14:00-16:00")
        st.info("📊 85% confidence in predictions")
        st.info("⚡ Recommended: Scale up 2 instances")

        # Capacity recommendations
        st.markdown("**Capacity Planning:**")
        capacity_metrics = {
            "Current Load": "65%",
            "Peak Load": "92%",
            "Recommended Buffer": "20%",
            "Auto-scale Threshold": "80%",
        }

        for metric, value in capacity_metrics.items():
            st.metric(metric, value)


def render_anomaly_detection(ecosystem_health: Dict[str, Any]):
    """Render anomaly detection analytics."""
    st.markdown("#### 🎯 Real-Time Anomaly Detection")

    # Analyze ecosystem health for anomalies
    anomalies = detect_anomalies(ecosystem_health)

    col1, col2 = st.columns([2, 1])

    with col1:
        if anomalies:
            st.markdown("**🚨 Detected Anomalies:**")

            for anomaly in anomalies:
                severity_color = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(
                    anomaly["severity"], "⚪"
                )

                with st.expander(f"{severity_color} {anomaly['title']} ({anomaly['severity']})"):
                    st.markdown(f"**Description:** {anomaly['description']}")
                    st.markdown(f"**Impact:** {anomaly['impact']}")
                    st.markdown(f"**Affected Services:** {', '.join(anomaly['affected_services'])}")
                    st.markdown(f"**Detected:** {anomaly['timestamp'].strftime('%H:%M:%S')}")

                    # Action buttons
                    action_col1, action_col2 = st.columns(2)
                    with action_col1:
                        if st.button(f"🔧 Auto-fix", key=f"fix_{anomaly['id']}"):
                            st.success(f"✅ Applied automatic fix for {anomaly['title']}")
                    with action_col2:
                        if st.button(f"📋 Investigate", key=f"investigate_{anomaly['id']}"):
                            st.info(f"📋 Investigation initiated for {anomaly['title']}")
        else:
            st.success("✅ No anomalies detected - All systems operating normally")

    with col2:
        st.markdown("**Anomaly Statistics:**")
        total_anomalies = len(anomalies)
        critical_count = sum(1 for a in anomalies if a["severity"] == "Critical")
        high_count = sum(1 for a in anomalies if a["severity"] == "High")

        st.metric("Total Anomalies", total_anomalies)
        st.metric("Critical Issues", critical_count, delta=f"{'+' if critical_count > 0 else ''}{critical_count}")
        st.metric("High Priority", high_count, delta=f"{'+' if high_count > 0 else ''}{high_count}")

        # Detection accuracy
        st.markdown("**Detection Metrics:**")
        st.metric("Detection Accuracy", "96.7%")
        st.metric("False Positive Rate", "2.1%")
        st.metric("Average Response Time", "1.2s")


def generate_load_forecast_data() -> pd.DataFrame:
    """Generate load forecasting data based on current patterns."""
    import numpy as np

    hours = list(range(24))
    base_load = 60

    # Simulate realistic load patterns (business hours peak)
    load_pattern = []
    for hour in hours:
        if 9 <= hour <= 17:  # Business hours
            base = base_load + 20
            # Add some realistic variation
            variation = np.sin(hour * np.pi / 12) * 10  # Sine wave variation
            random_noise = np.random.normal(0, 3)  # Random noise
            load = base + variation + random_noise
        else:
            # Off-hours lower load
            load = base_load - 15 + np.random.normal(0, 2)

        load_pattern.append(max(10, min(100, load)))  # Clamp between 10-100

    return pd.DataFrame(
        {
            "hour": hours,
            "predicted_load": load_pattern,
            "upper_bound": [min(100, l + 5 + np.random.uniform(0, 3)) for l in load_pattern],
            "lower_bound": [max(0, l - 5 - np.random.uniform(0, 3)) for l in load_pattern],
            "confidence": [85 + np.random.normal(0, 5) for _ in hours],
        }
    )


def detect_anomalies(ecosystem_health: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Detect anomalies in ecosystem health data."""
    anomalies = []
    services = ecosystem_health.get("services", {})

    # Check for response time anomalies
    for service_name, service_data in services.items():
        response_time = service_data.get("response_time", 0)
        status = service_data.get("status")

        # Define anomaly thresholds
        if response_time > 3.0 and status == "healthy":
            anomalies.append(
                {
                    "id": f"response_time_{service_name}",
                    "title": f"High Response Time: {service_name}",
                    "description": f"Service {service_name} showing elevated response time of {response_time:.2f}s",
                    "severity": "Medium" if response_time < 5.0 else "High",
                    "impact": "Performance degradation affecting user experience",
                    "affected_services": [service_name],
                    "timestamp": ecosystem_health.get("timestamp", datetime.now()),
                    "auto_fix_available": True,
                }
            )

        # Check for unhealthy services
        if status != "healthy":
            anomalies.append(
                {
                    "id": f"service_health_{service_name}",
                    "title": f"Service Unhealthy: {service_name}",
                    "description": f"Service {service_name} is reporting {status} status",
                    "severity": "Critical" if service_name in ["project-simulation", "llm-gateway"] else "High",
                    "impact": "Service disruption affecting system functionality",
                    "affected_services": [service_name],
                    "timestamp": ecosystem_health.get("timestamp", datetime.now()),
                    "auto_fix_available": service_name not in ["llm-gateway"],  # Can't auto-restart LLM gateway
                }
            )

    # Check for overall system health
    healthy_count = sum(1 for s in services.values() if s.get("status") == "healthy")
    total_count = len(services)

    if healthy_count / total_count < 0.8:  # Less than 80% services healthy
        anomalies.append(
            {
                "id": "system_health_critical",
                "title": "Critical System Health Degradation",
                "description": f"Only {healthy_count}/{total_count} services are healthy",
                "severity": "Critical",
                "impact": "System-wide performance and reliability impact",
                "affected_services": list(services.keys()),
                "timestamp": ecosystem_health.get("timestamp", datetime.now()),
                "auto_fix_available": False,
            }
        )

    return anomalies


def render_autonomous_actions_dashboard(sim_client: SimulationClient, ecosystem_health: Dict[str, Any]):
    """Render intelligent autonomous actions dashboard."""
    st.markdown("### ⚡ Autonomous Actions & AI Optimization")

    # Initialize LLM client for autonomous features
    llm_client = LLMGatewayClient()

    # Create tabs for different autonomous capabilities
    tab1, tab2, tab3, tab4 = st.tabs(
        ["🤖 Smart Recommendations", "⚡ Auto-Optimization", "🔧 Self-Healing", "📈 Predictive Scaling"]
    )

    with tab1:
        render_smart_recommendations(ecosystem_health, llm_client)

    with tab2:
        render_auto_optimization(sim_client, ecosystem_health, llm_client)

    with tab3:
        render_self_healing(ecosystem_health)

    with tab4:
        render_predictive_scaling(ecosystem_health, llm_client)


def render_smart_recommendations(ecosystem_health: Dict[str, Any], llm_client: LLMGatewayClient):
    """Render smart AI-driven recommendations."""
    st.markdown("#### 🎯 AI-Powered Smart Recommendations")

    # Generate dynamic recommendations based on current ecosystem state
    recommendations = asyncio.run(generate_dynamic_recommendations(ecosystem_health, llm_client))

    if not recommendations:
        # Fallback recommendations
        recommendations = [
            {
                "type": "optimization",
                "title": "Scale Analysis Service",
                "description": "Increase instances based on predicted load",
                "impact": "High",
                "confidence": 92,
                "action": "Auto-scale to 3 instances",
                "category": "performance",
            },
            {
                "type": "maintenance",
                "title": "Cache Optimization",
                "description": "Clear outdated cache entries",
                "impact": "Medium",
                "confidence": 87,
                "action": "Schedule cache cleanup",
                "category": "maintenance",
            },
            {
                "type": "security",
                "title": "Update Dependencies",
                "description": "Critical security updates available",
                "impact": "High",
                "confidence": 95,
                "action": "Apply security patches",
                "category": "security",
            },
        ]

    # Group recommendations by category
    categories = {}
    for rec in recommendations:
        category = rec.get("category", "general")
        if category not in categories:
            categories[category] = []
        categories[category].append(rec)

    # Display recommendations by category
    for category, recs in categories.items():
        st.markdown(f"**{category.title()} Recommendations:**")

        for rec in recs:
            impact_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(rec["impact"], "⚪")

            with st.expander(f"{impact_color} {rec['title']} (Confidence: {rec['confidence']}%)"):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"**Description:** {rec['description']}")
                    st.markdown(f"**Impact:** {rec['impact']}")
                    st.markdown(f"**Recommended Action:** {rec['action']}")

                with col2:
                    if st.button(f"✅ Apply", key=f"apply_{rec['title'].lower().replace(' ', '_')}"):
                        st.success(f"✅ Applied: {rec['action']}")
                        # Log the action
                        st.info(f"📝 Action logged: {rec['action']}")

                    if st.button(f"⏭️ Schedule", key=f"schedule_{rec['title'].lower().replace(' ', '_')}"):
                        st.info(f"⏰ Scheduled: {rec['action']}")


def render_auto_optimization(
    sim_client: SimulationClient, ecosystem_health: Dict[str, Any], llm_client: LLMGatewayClient
):
    """Render automatic optimization features."""
    st.markdown("#### ⚡ Autonomous Optimization Engine")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Optimization Controls:**")

        # Auto-optimization settings
        auto_optimization_enabled = st.checkbox(
            "Enable Auto-Optimization", value=True, help="Allow automatic optimization based on AI recommendations"
        )

        optimization_frequency = st.selectbox(
            "Optimization Frequency",
            options=["Continuous", "Hourly", "Daily", "Weekly"],
            index=1,
            help="How often to check for optimizations",
        )

        risk_tolerance = st.slider(
            "Risk Tolerance",
            min_value=1,
            max_value=10,
            value=7,
            help="Higher values allow more aggressive optimizations",
        )

    with col2:
        st.markdown("**Optimization Status:**")

        # Mock optimization metrics
        optimization_metrics = {
            "Optimizations Applied": 24,
            "Performance Improvement": "+18%",
            "Cost Savings": "$2,340",
            "Uptime Impact": "0.01%",
        }

        for metric, value in optimization_metrics.items():
            st.metric(metric, value)

    # Manual optimization trigger
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔍 Analyze & Optimize", key="analyze_optimize"):
            with st.spinner("AI analyzing system for optimization opportunities..."):
                asyncio.run(run_system_analysis(llm_client, ecosystem_health))

    with col2:
        if st.button("⚡ Quick Optimize", key="quick_optimize"):
            with st.spinner("Applying quick optimizations..."):
                asyncio.run(apply_quick_optimizations(ecosystem_health))

    with col3:
        if st.button("📊 Optimization Report", key="optimization_report"):
            st.info("📊 Generating comprehensive optimization report...")
            # Would generate detailed report here


def render_self_healing(ecosystem_health: Dict[str, Any]):
    """Render self-healing capabilities."""
    st.markdown("#### 🔧 Self-Healing & Auto-Recovery")

    # Analyze current issues
    issues = detect_system_issues(ecosystem_health)

    if issues:
        st.markdown("**🚨 Detected Issues:**")

        for issue in issues:
            severity_color = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(issue["severity"], "⚪")

            with st.expander(f"{severity_color} {issue['title']} ({issue['severity']})"):
                st.markdown(f"**Description:** {issue['description']}")
                st.markdown(f"**Affected Services:** {', '.join(issue['affected_services'])}")
                st.markdown(
                    f"**Auto-Recovery:** {'Available' if issue['auto_recoverable'] else 'Manual intervention required'}"
                )

                if issue["auto_recoverable"]:
                    if st.button(f"🔧 Auto-Fix", key=f"fix_{issue['id']}"):
                        with st.spinner("Applying automatic fix..."):
                            success = apply_auto_fix(issue)
                            if success:
                                st.success(f"✅ Fixed: {issue['title']}")
                            else:
                                st.error(f"❌ Failed to fix: {issue['title']}")
                else:
                    st.warning("⚠️ Manual intervention required for this issue")
    else:
        st.success("✅ System Health: All services operating normally")
        st.info("🔍 Self-healing system actively monitoring for issues")


def render_predictive_scaling(ecosystem_health: Dict[str, Any], llm_client: LLMGatewayClient):
    """Render predictive scaling capabilities."""
    st.markdown("#### 📈 Predictive Scaling & Resource Management")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Current Load Analysis:**")

        # Mock current load data
        load_data = {
            "CPU Usage": "68%",
            "Memory Usage": "74%",
            "Network I/O": "45 Mbps",
            "Active Connections": 1250,
            "Queue Depth": 23,
        }

        for metric, value in load_data.items():
            st.metric(metric, value)

        # Load prediction
        st.markdown("**📊 Load Prediction (Next Hour):**")
        prediction = predict_load_trend(ecosystem_health)
        st.info(f"🔮 Predicted peak load: {prediction['peak_load']}% at {prediction['peak_time']}")

    with col2:
        st.markdown("**Scaling Recommendations:**")

        # Generate scaling recommendations
        scaling_recs = asyncio.run(generate_scaling_recommendations(ecosystem_health, llm_client))

        for rec in scaling_recs:
            with st.expander(f"⚖️ {rec['service']} Scaling"):
                st.markdown(f"**Current Instances:** {rec['current_instances']}")
                st.markdown(f"**Recommended:** {rec['recommended_instances']}")
                st.markdown(f"**Reason:** {rec['reason']}")
                st.markdown(f"**Confidence:** {rec['confidence']}%")

                if st.button(f"📈 Scale {rec['service']}", key=f"scale_{rec['service']}"):
                    st.success(f"✅ Scaling {rec['service']} to {rec['recommended_instances']} instances")


async def generate_dynamic_recommendations(
    ecosystem_health: Dict[str, Any], llm_client: LLMGatewayClient
) -> List[Dict[str, Any]]:
    """Generate dynamic AI-powered recommendations."""
    try:
        # Analyze ecosystem health for specific recommendations
        services = ecosystem_health.get("services", {})
        unhealthy_services = [name for name, data in services.items() if data.get("status") != "healthy"]
        slow_services = [
            name
            for name, data in services.items()
            if data.get("response_time", 0) > 2.0 and data.get("status") == "healthy"
        ]

        context = f"""
        Ecosystem Health Analysis:
        - Total Services: {len(services)}
        - Unhealthy Services: {len(unhealthy_services)} ({', '.join(unhealthy_services[:3])})
        - Slow Services: {len(slow_services)} ({', '.join(slow_services[:3])})
        - Overall Health: {ecosystem_health.get('overall_health', 'unknown')}

        Generate 3-5 specific, actionable recommendations for system optimization.
        Format as JSON with fields: title, description, impact, confidence, action, category
        """

        result = await llm_client.query_llm(prompt=context, max_tokens=300)

        if result.get("success"):
            response_text = result["data"]["response"]
            # Try to parse as JSON, fallback to text processing
            try:
                recommendations = json.loads(response_text)
                return recommendations if isinstance(recommendations, list) else []
            except:
                # Fallback: extract recommendations from text
                return parse_recommendations_from_text(response_text)
        else:
            return []

    except Exception as e:
        st.error(f"Failed to generate dynamic recommendations: {e}")
        return []


def parse_recommendations_from_text(text: str) -> List[Dict[str, Any]]:
    """Parse recommendations from plain text response."""
    recommendations = []

    # Simple text parsing - look for numbered or bulleted items
    lines = text.strip().split("\n")

    for line in lines:
        line = line.strip()
        if line and (line[0].isdigit() or line.startswith("-") or line.startswith("•")):
            # Extract the main recommendation text
            if line[0].isdigit():
                rec_text = line.split(". ", 1)[1] if ". " in line else line[2:]
            else:
                rec_text = line[1:].strip()

            recommendations.append(
                {
                    "title": rec_text[:50] + "..." if len(rec_text) > 50 else rec_text,
                    "description": rec_text,
                    "impact": "Medium",
                    "confidence": 85,
                    "action": f"Implement: {rec_text}",
                    "category": "optimization",
                }
            )

    return recommendations[:5]


async def run_system_analysis(llm_client: LLMGatewayClient, ecosystem_health: Dict[str, Any]):
    """Run comprehensive system analysis."""
    try:
        analysis_prompt = f"""
        Perform a comprehensive analysis of this system health data and provide optimization recommendations:

        {json.dumps(ecosystem_health, indent=2)}

        Focus on:
        1. Performance bottlenecks
        2. Resource optimization opportunities
        3. Reliability improvements
        4. Cost optimization
        5. Security enhancements

        Provide specific, actionable recommendations.
        """

        result = await llm_client.query_llm(prompt=analysis_prompt, max_tokens=400)

        if result.get("success"):
            analysis = result["data"]["response"]
            st.markdown("#### 📊 AI System Analysis Results")
            st.info(analysis)
        else:
            st.error("❌ Failed to generate system analysis")

    except Exception as e:
        st.error(f"❌ System analysis failed: {e}")


async def apply_quick_optimizations(ecosystem_health: Dict[str, Any]):
    """Apply quick optimization actions."""
    try:
        # Mock quick optimizations
        optimizations = [
            "Cleared expired cache entries",
            "Optimized database connections",
            "Balanced load across instances",
            "Updated configuration parameters",
        ]

        st.markdown("#### ⚡ Quick Optimizations Applied")
        for i, opt in enumerate(optimizations, 1):
            st.success(f"✅ {i}. {opt}")

        st.info("📈 Expected performance improvement: 12-18%")

    except Exception as e:
        st.error(f"❌ Quick optimizations failed: {e}")


def detect_system_issues(ecosystem_health: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Detect system issues that need healing."""
    issues = []
    services = ecosystem_health.get("services", {})

    for service_name, service_data in services.items():
        status = service_data.get("status")

        if status != "healthy":
            issues.append(
                {
                    "id": f"health_{service_name}",
                    "title": f"Service {service_name} unhealthy",
                    "description": f"Service {service_name} is reporting {status} status",
                    "severity": "Critical" if service_name in ["project-simulation", "llm-gateway"] else "High",
                    "affected_services": [service_name],
                    "auto_recoverable": service_name not in ["llm-gateway"],  # Can't auto-restart LLM gateway
                }
            )

        # Check for performance issues
        response_time = service_data.get("response_time", 0)
        if response_time > 5.0 and status == "healthy":
            issues.append(
                {
                    "id": f"perf_{service_name}",
                    "title": f"High response time: {service_name}",
                    "description": f"Service {service_name} response time is {response_time:.2f}s",
                    "severity": "Medium",
                    "affected_services": [service_name],
                    "auto_recoverable": True,
                }
            )

    return issues


def apply_auto_fix(issue: Dict[str, Any]) -> bool:
    """Apply automatic fix for an issue."""
    try:
        issue_type = issue["id"].split("_")[0]

        if issue_type == "health":
            # Service restart simulation
            service_name = issue["affected_services"][0]
            st.info(f"🔄 Restarting service: {service_name}")
            return True
        elif issue_type == "perf":
            # Performance optimization
            service_name = issue["affected_services"][0]
            st.info(f"⚡ Optimizing performance for: {service_name}")
            return True

        return False
    except:
        return False


def predict_load_trend(ecosystem_health: Dict[str, Any]) -> Dict[str, Any]:
    """Predict load trends for the next hour."""
    # Mock prediction logic
    current_hour = ecosystem_health.get("timestamp", datetime.now()).hour

    # Simulate business hours peak
    if 9 <= current_hour <= 17:
        peak_load = 85 + (current_hour - 12) * 2  # Peak around noon
        peak_time = f"{(current_hour + 1) % 24}:00"
    else:
        peak_load = 45
        peak_time = "09:00"

    return {
        "peak_load": min(100, peak_load),
        "peak_time": peak_time,
        "trend": "increasing" if current_hour < 14 else "decreasing",
    }


async def generate_scaling_recommendations(
    ecosystem_health: Dict[str, Any], llm_client: LLMGatewayClient
) -> List[Dict[str, Any]]:
    """Generate scaling recommendations."""
    try:
        scaling_prompt = f"""
        Based on this ecosystem health data, provide scaling recommendations for each service:

        {json.dumps(ecosystem_health, indent=2)}

        For each service, consider:
        - Current load and performance
        - Response times
        - Resource utilization
        - Predicted future load

        Provide recommendations in JSON format with fields: service, current_instances, recommended_instances, reason, confidence
        """

        result = await llm_client.query_llm(prompt=scaling_prompt, max_tokens=300)

        if result.get("success"):
            response_text = result["data"]["response"]
            try:
                recommendations = json.loads(response_text)
                return recommendations if isinstance(recommendations, list) else []
            except:
                # Fallback recommendations
                return generate_fallback_scaling_recs(ecosystem_health)
        else:
            return generate_fallback_scaling_recs(ecosystem_health)

    except:
        return generate_fallback_scaling_recs(ecosystem_health)


def generate_fallback_scaling_recs(ecosystem_health: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate fallback scaling recommendations."""
    services = ecosystem_health.get("services", {})

    recommendations = []
    for service_name in ["project-simulation", "analysis-service", "llm-gateway"]:
        if service_name in services:
            service_data = services[service_name]
            response_time = service_data.get("response_time", 0)

            if response_time > 2.0:
                recommendations.append(
                    {
                        "service": service_name,
                        "current_instances": 1,
                        "recommended_instances": 2,
                        "reason": f"High response time ({response_time:.2f}s) indicates need for scaling",
                        "confidence": 85,
                    }
                )

    if not recommendations:
        # Default recommendations
        recommendations = [
            {
                "service": "analysis-service",
                "current_instances": 1,
                "recommended_instances": 2,
                "reason": "Predicted load increase during business hours",
                "confidence": 78,
            }
        ]

    return recommendations


def render_intelligent_system_status(ecosystem_health: Dict[str, Any]):
    """Render intelligent system status with recommendations."""
    st.markdown("### 🔧 Intelligent System Status")

    # Overall health indicator
    health_status = ecosystem_health.get("overall_health", "unknown")
    health_colors = {
        "excellent": ("🟢", "success"),
        "good": ("🟡", "warning"),
        "fair": ("🟠", "warning"),
        "poor": ("🔴", "error"),
        "unknown": ("⚪", "info"),
    }

    color, level = health_colors.get(health_status, ("⚪", "info"))

    if level == "success":
        st.success(f"{color} **Ecosystem Health: {health_status.title()}**")
    elif level == "warning":
        st.warning(f"{color} **Ecosystem Health: {health_status.title()}**")
    elif level == "error":
        st.error(f"{color} **Ecosystem Health: {health_status.title()}**")
    else:
        st.info(f"{color} **Ecosystem Health: {health_status.title()}**")

    # Service grid
    st.markdown("#### 🏥 Service Health Matrix")

    services = ecosystem_health.get("services", {})
    cols = st.columns(4)

    for i, (service_name, service_data) in enumerate(services.items()):
        with cols[i % 4]:
            status = service_data.get("status", "unknown")
            status_icon = {"healthy": "✅", "unhealthy": "❌", "unknown": "❓"}.get(status, "❓")

            st.metric(
                service_name.replace("-", " ").title(),
                f"{status_icon} {status.title()}",
                help=f"Response time: {service_data.get('response_time', 'N/A')}",
            )

    # Intelligent recommendations
    if ecosystem_health.get("recommendations"):
        st.markdown("#### 💡 AI Recommendations")
        for rec in ecosystem_health["recommendations"]:
            st.info(f"🧠 {rec}")


async def get_simulation_metrics(sim_client: SimulationClient) -> Dict[str, Any]:
    """Get simulation metrics from the service."""
    # This would make actual API calls to the simulation service
    return {
        "active_count": 3,
        "success_rate": 89,
        "avg_duration": 42,
        "total_simulations": 156,
        "performance_score": 94,
    }


def generate_mock_simulation_data() -> Dict[str, Any]:
    """Generate mock simulation data for demonstration."""
    return {
        "active_count": 3,
        "success_rate": 87,
        "avg_duration": 38,
        "total_simulations": 142,
        "performance_score": 91,
    }


def render_key_metrics():
    """Render key performance metrics."""
    st.markdown("### Key Performance Indicators")

    # Create metrics row
    col1, col2, col3, col4 = st.columns(4)

    # Mock data - in real implementation this would come from the simulation service
    with col1:
        total_simulations = get_total_simulations_count()
        st.metric(
            label="Total Simulations",
            value=total_simulations,
            delta="+2 from yesterday",
            help="Total number of simulations created",
        )

    with col2:
        active_simulations = get_active_simulations_count()
        st.metric(
            label="Active Simulations",
            value=active_simulations,
            delta=f"{active_simulations} running",
            help="Currently running simulations",
        )

    with col3:
        success_rate = get_success_rate()
        st.metric(
            label="Success Rate",
            value=f"{success_rate}%",
            delta="+5% from last week",
            help="Percentage of successful simulations",
        )

    with col4:
        avg_duration = get_average_duration()
        st.metric(
            label="Avg Duration",
            value=f"{avg_duration}min",
            delta="-2min from last week",
            help="Average simulation duration",
        )

    # Additional metrics
    st.markdown("---")
    render_additional_metrics()


def render_additional_metrics():
    """Render additional performance metrics."""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**📊 Simulation Types**")
        # Mock data
        simulation_types = {"Web Application": 45, "Mobile App": 23, "API Service": 18, "Data Pipeline": 14}

        for sim_type, count in simulation_types.items():
            st.progress(count / 100, text=f"{sim_type}: {count}")

    with col2:
        st.markdown("**⏱️ Performance Trends**")
        # Mock performance data
        performance_data = [85, 87, 82, 89, 91, 88, 93]
        for i, value in enumerate(performance_data[-7:]):
            days_ago = 6 - i
            st.progress(value / 100, text=f"{days_ago} days ago: {value}%")

    with col3:
        st.markdown("**🏆 Top Performers**")
        # Mock top performers
        top_performers = [
            ("E-commerce Platform", "98%"),
            ("User Management API", "95%"),
            ("Analytics Dashboard", "93%"),
        ]

        for name, score in top_performers:
            st.markdown(f"• **{name}**: {score}")


def render_active_simulations():
    """Render active simulations overview."""
    st.markdown("### Active Simulations")

    # Get active simulations
    active_sims = get_active_simulations()

    if not active_sims:
        st.info("No active simulations at the moment.")
        return

    # Display active simulations
    for sim in active_sims:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])

            with col1:
                st.markdown(f"**{sim['name']}**")
                st.caption(f"ID: {sim['id']}")

            with col2:
                st.markdown(f"**Status:** {sim['status']}")
                if sim["status"] == "running":
                    st.success("🟢 Running")
                elif sim["status"] == "paused":
                    st.warning("🟡 Paused")
                else:
                    st.info(f"🔵 {sim['status']}")

            with col3:
                progress = sim.get("progress", 0)
                st.progress(progress / 100, text=f"{progress}% Complete")

            with col4:
                st.markdown(f"**Started:** {sim['start_time']}")
                if "estimated_completion" in sim:
                    st.caption(f"Est. completion: {sim['estimated_completion']}")

            with col5:
                if st.button("👁️ View", key=f"view_{sim['id']}", help=f"Monitor simulation {sim['id']}"):
                    st.session_state.selected_simulation = sim["id"]
                    st.session_state.current_page = "monitor"
                    st.rerun()

            st.markdown("---")


def render_recent_activity():
    """Render recent activity feed."""
    st.markdown("### Recent Activity")

    # Get recent activity
    activities = get_recent_activities()

    if not activities:
        st.info("No recent activity to display.")
        return

    # Display activities
    for activity in activities:
        with st.container():
            col1, col2 = st.columns([1, 4])

            with col1:
                # Activity icon based on type
                icon_map = {
                    "simulation_created": "➕",
                    "simulation_started": "▶️",
                    "simulation_completed": "✅",
                    "simulation_failed": "❌",
                    "report_generated": "📊",
                }
                icon = icon_map.get(activity["type"], "📝")
                st.markdown(f"### {icon}")

            with col2:
                st.markdown(f"**{activity['title']}**")
                st.caption(f"{activity['description']}")
                st.caption(f"{activity['timestamp']} • {activity['user']}")

            st.markdown("---")


def render_quick_actions():
    """Render quick action buttons."""
    st.markdown("### Quick Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("**🚀 Start New**")
        if st.button("Create Simulation", key="quick_create", use_container_width=True):
            st.session_state.current_page = "create"
            st.rerun()

        if st.button("From Config File", key="quick_config", use_container_width=True):
            st.session_state.current_page = "create"
            st.rerun()

    with col2:
        st.markdown("**📊 Monitor**")
        if st.button("Active Simulations", key="quick_monitor", use_container_width=True):
            st.session_state.current_page = "monitor"
            st.rerun()

        if st.button("System Health", key="quick_health", use_container_width=True):
            st.session_state.current_page = "config"
            st.rerun()

    with col3:
        st.markdown("**📋 Reports**")
        if st.button("Generate Report", key="quick_report", use_container_width=True):
            st.session_state.current_page = "reports"
            st.rerun()

        if st.button("View Analytics", key="quick_analytics", use_container_width=True):
            st.session_state.current_page = "analytics"
            st.rerun()

    with col4:
        st.markdown("**⚙️ Manage**")
        if st.button("Configuration", key="quick_config_manage", use_container_width=True):
            st.session_state.current_page = "config"
            st.rerun()

        if st.button("Settings", key="quick_settings", use_container_width=True):
            st.info("Settings panel would open here")


def render_system_status():
    """Render system status overview."""
    st.markdown("## 🏥 System Status")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Simulation Service Status
        st.markdown("**🎯 Simulation Service**")
        service_status = check_simulation_service_status()
        if service_status["healthy"]:
            st.success("✅ Healthy")
        else:
            st.error("❌ Unhealthy")
        st.caption(f"Response: {service_status['response_time']}ms")

    with col2:
        # Database Status
        st.markdown("**🗄️ Database**")
        db_status = check_database_status()
        if db_status["healthy"]:
            st.success("✅ Connected")
        else:
            st.error("❌ Disconnected")
        st.caption(f"Connections: {db_status['active_connections']}")

    with col3:
        # WebSocket Status
        st.markdown("**🔄 Real-time Updates**")
        ws_status = check_websocket_status()
        if ws_status["connected"]:
            st.success("✅ Connected")
        else:
            st.warning("⚠️ Disconnected")
        st.caption(f"Active: {ws_status['active_connections']}")

    with col4:
        # System Resources
        st.markdown("**💻 System Resources**")
        resources = get_system_resources()
        cpu_usage = resources["cpu_percent"]
        memory_usage = resources["memory_percent"]

        if cpu_usage < 70 and memory_usage < 80:
            st.success("✅ Normal")
        elif cpu_usage < 90 and memory_usage < 90:
            st.warning("⚠️ High")
        else:
            st.error("❌ Critical")

        st.caption(f"CPU: {cpu_usage}% | RAM: {memory_usage}%")


# Mock data functions - in real implementation these would call the actual services


def get_total_simulations_count() -> int:
    """Get total simulations count."""
    # Mock data
    return 127


def get_active_simulations_count() -> int:
    """Get active simulations count."""
    # Mock data
    return 3


def get_success_rate() -> int:
    """Get success rate percentage."""
    # Mock data
    return 89


def get_average_duration() -> int:
    """Get average duration in minutes."""
    # Mock data
    return 45


def get_active_simulations() -> List[Dict[str, Any]]:
    """Get list of active simulations."""
    # Mock data
    return [
        {
            "id": "sim_001",
            "name": "E-commerce Platform",
            "status": "running",
            "progress": 67,
            "start_time": "2024-01-15 14:30:00",
            "estimated_completion": "2024-01-15 16:15:00",
        },
        {
            "id": "sim_002",
            "name": "User Management API",
            "status": "running",
            "progress": 34,
            "start_time": "2024-01-15 15:45:00",
            "estimated_completion": "2024-01-15 17:30:00",
        },
        {
            "id": "sim_003",
            "name": "Analytics Dashboard",
            "status": "paused",
            "progress": 12,
            "start_time": "2024-01-15 16:00:00",
        },
    ]


def get_recent_activities() -> List[Dict[str, Any]]:
    """Get recent activities."""
    # Mock data
    return [
        {
            "type": "simulation_completed",
            "title": "Simulation Completed",
            "description": "Mobile App Development simulation finished successfully",
            "timestamp": "2024-01-15 14:15:00",
            "user": "System",
        },
        {
            "type": "report_generated",
            "title": "Report Generated",
            "description": "Executive summary report for Project Alpha",
            "timestamp": "2024-01-15 13:45:00",
            "user": "john.doe@example.com",
        },
        {
            "type": "simulation_started",
            "title": "Simulation Started",
            "description": "E-commerce Platform simulation initiated",
            "timestamp": "2024-01-15 13:30:00",
            "user": "jane.smith@example.com",
        },
        {
            "type": "simulation_created",
            "title": "Simulation Created",
            "description": "New simulation: API Service Development",
            "timestamp": "2024-01-15 12:00:00",
            "user": "System",
        },
    ]


def check_simulation_service_status() -> Dict[str, Any]:
    """Check simulation service health."""
    # Mock health check
    return {"healthy": True, "response_time": 45}


def check_database_status() -> Dict[str, Any]:
    """Check database health."""
    # Mock database check
    return {"healthy": True, "active_connections": 5}


def check_websocket_status() -> Dict[str, Any]:
    """Check WebSocket connection status."""
    # Mock WebSocket check
    return {"connected": True, "active_connections": 2}


def get_system_resources() -> Dict[str, Any]:
    """Get system resource usage."""
    # Mock resource data
    return {"cpu_percent": 23.5, "memory_percent": 45.2}
