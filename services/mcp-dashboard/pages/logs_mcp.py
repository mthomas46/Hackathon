"""Logs MCP Dashboard - Intelligent Observability System."""

import sys
from pathlib import Path

# Add services to path
services_path = Path(__file__).parent.parent.parent / "services"
sys.path.insert(0, str(services_path))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import List, Dict
import pandas as pd

from mcp_logs.src.log_processor import LogProcessor, LogEntry, LogLevel
from mcp_logs.src.pattern_detector import PatternDetector, PatternType
from mcp_logs.src.anomaly_detector import AnomalyDetector, AnomalyType
from mcp_logs.src.root_cause_analyzer import RootCauseAnalyzer
from mcp_logs.src.predictive_maintenance import PredictiveMaintenance


# Page config
st.set_page_config(
    page_title="Logs MCP - Intelligent Observability",
    page_icon="🔍",
    layout="wide"
)

# Initialize services
if "log_processor" not in st.session_state:
    st.session_state.log_processor = LogProcessor()
    st.session_state.pattern_detector = PatternDetector()
    st.session_state.anomaly_detector = AnomalyDetector()
    st.session_state.root_cause_analyzer = RootCauseAnalyzer()
    st.session_state.predictive_maintenance = PredictiveMaintenance()

# Initialize sample logs if not present
if "sample_logs" not in st.session_state:
    # Generate sample logs for demo
    base_time = datetime.now() - timedelta(hours=1)
    st.session_state.sample_logs = []
    
    # Normal operations
    for i in range(100):
        st.session_state.sample_logs.append(LogEntry(
            timestamp=base_time + timedelta(minutes=i),
            level=LogLevel.INFO if i % 15 != 0 else LogLevel.WARNING,
            service=f"service-{i % 5}",
            source="app.log",
            message=f"Request processed successfully" if i % 15 != 0 else f"High latency detected"
        ))
    
    # Add some errors
    error_time = base_time + timedelta(minutes=45)
    for i in range(10):
        st.session_state.sample_logs.append(LogEntry(
            timestamp=error_time + timedelta(seconds=i * 30),
            level=LogLevel.ERROR,
            service=f"service-{i % 3}",
            source="app.log",
            message="Database connection failed"
        ))


# Header
st.title("🔍 Logs MCP - Intelligent Observability")
st.markdown("Transform observability data into strategic intelligence")

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋 Log Viewer",
    "🔍 Pattern Detection",
    "⚠️ Anomaly Detection",
    "🎯 Root Cause Analysis",
    "🔮 Predictive Maintenance",
    "📊 Analytics"
])

# Tab 1: Log Viewer
with tab1:
    st.header("📋 Log Viewer & Filtering")
    
    col1, col2 = st.columns(2)
    
    with col1:
        level_filter = st.multiselect(
            "Filter by Level",
            options=[level.value for level in LogLevel],
            default=[]
        )
    
    with col2:
        services = list(set(log.service for log in st.session_state.sample_logs))
        service_filter = st.multiselect(
            "Filter by Service",
            options=services,
            default=[]
        )
    
    # Apply filters
    filtered_logs = st.session_state.sample_logs.copy()
    
    if level_filter:
        filtered_logs = [log for log in filtered_logs if log.level.value in level_filter]
    
    if service_filter:
        filtered_logs = [log for log in filtered_logs if log.service in service_filter]
    
    # Display stats
    st.subheader("📊 Log Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Logs", len(filtered_logs))
    
    with col2:
        error_count = len([log for log in filtered_logs if log.level == LogLevel.ERROR])
        st.metric("Errors", error_count, delta=-error_count if error_count > 0 else 0)
    
    with col3:
        warning_count = len([log for log in filtered_logs if log.level == LogLevel.WARNING])
        st.metric("Warnings", warning_count)
    
    with col4:
        unique_services = len(set(log.service for log in filtered_logs))
        st.metric("Services", unique_services)
    
    # Log level distribution
    st.subheader("📈 Log Level Distribution")
    
    level_counts = {}
    for log in filtered_logs:
        level_counts[log.level.value] = level_counts.get(log.level.value, 0) + 1
    
    fig = px.bar(
        x=list(level_counts.keys()),
        y=list(level_counts.values()),
        labels={'x': 'Log Level', 'y': 'Count'},
        title="Logs by Level"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Recent logs table
    st.subheader("📝 Recent Logs")
    
    df = pd.DataFrame([
        {
            "Timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "Level": log.level.value,
            "Service": log.service,
            "Message": log.message[:80]
        }
        for log in filtered_logs[-50:]
    ])
    
    st.dataframe(df, use_container_width=True, height=400)


# Tab 2: Pattern Detection
with tab2:
    st.header("🔍 Pattern Detection")
    st.markdown("Automatically detect patterns in logs: repeated errors, spikes, cascading failures")
    
    if st.button("🔍 Detect Patterns", key="detect_patterns"):
        with st.spinner("Analyzing patterns..."):
            result = st.session_state.pattern_detector.detect_patterns(st.session_state.sample_logs)
            st.session_state.detection_result = result
    
    if "detection_result" in st.session_state:
        result = st.session_state.detection_result
        
        # Overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Patterns Found", result.patterns_found)
        
        with col2:
            st.metric("Logs Analyzed", result.analyzed_entries)
        
        with col3:
            if result.time_range:
                duration = (result.time_range[1] - result.time_range[0]).total_seconds() / 60
                st.metric("Time Range (min)", f"{duration:.1f}")
        
        # Pattern details
        st.subheader("🔍 Detected Patterns")
        
        if result.patterns:
            for i, pattern in enumerate(result.patterns):
                with st.expander(f"Pattern {i+1}: {pattern.type.value} - {pattern.severity.upper()}", expanded=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Description:** {pattern.description}")
                        st.write(f"**Occurrences:** {pattern.occurrences}")
                        st.write(f"**Severity:** {pattern.severity}")
                    
                    with col2:
                        st.write(f"**First Seen:** {pattern.first_seen.strftime('%Y-%m-%d %H:%M:%S')}")
                        st.write(f"**Last Seen:** {pattern.last_seen.strftime('%Y-%m-%d %H:%M:%S')}")
                        st.write(f"**Affected Services:** {', '.join(pattern.affected_services)}")
            
            # Pattern type distribution
            st.subheader("📊 Pattern Distribution")
            
            pattern_types = {}
            for pattern in result.patterns:
                pattern_types[pattern.type.value] = pattern_types.get(pattern.type.value, 0) + 1
            
            fig = px.pie(
                values=list(pattern_types.values()),
                names=list(pattern_types.keys()),
                title="Patterns by Type"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("✅ No concerning patterns detected. System is healthy!")


# Tab 3: Anomaly Detection
with tab3:
    st.header("⚠️ Anomaly Detection")
    st.markdown("Detect anomalies using statistical analysis and ML-based methods")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔢 Error Rate Anomaly")
        
        # Calculate current error rate
        error_logs = [log for log in st.session_state.sample_logs if log.level == LogLevel.ERROR]
        current_error_rate = len(error_logs) / len(st.session_state.sample_logs)
        
        # Define baseline
        baseline = {"error_rate": 0.05, "std_dev": 0.02}
        
        # Detect anomaly
        anomaly = st.session_state.anomaly_detector.detect_anomaly(
            "error_rate",
            current_error_rate,
            baseline
        )
        
        st.metric("Current Error Rate", f"{current_error_rate*100:.2f}%")
        st.metric("Baseline Rate", f"{baseline['error_rate']*100:.2f}%")
        st.metric("Anomaly Score", f"{anomaly.score:.3f}")
        
        if anomaly.is_anomaly:
            st.error(f"⚠️ **ANOMALY DETECTED**")
            st.write(f"**Severity:** {anomaly.severity}")
            st.write(f"**Description:** {anomaly.description}")
        else:
            st.success("✅ No anomaly detected")
    
    with col2:
        st.subheader("📈 Trend Analysis")
        
        # Simulate trend data
        timestamps = [datetime.now() - timedelta(hours=23-i) for i in range(24)]
        memory_values = [50 + i * 1.5 for i in range(24)]  # Gradual increase
        
        # Analyze trend
        trend = st.session_state.predictive_maintenance.analyze_trend(
            "memory_usage",
            timestamps,
            memory_values
        )
        
        st.metric("Trend Direction", trend.direction.upper())
        st.metric("Slope", f"{trend.slope:.4f}")
        st.metric("Confidence", f"{trend.confidence*100:.1f}%")
        
        # Plot trend
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[t.strftime('%H:%M') for t in timestamps],
            y=memory_values,
            mode='lines+markers',
            name='Memory Usage %'
        ))
        fig.update_layout(
            title="Memory Usage Trend (24h)",
            xaxis_title="Time",
            yaxis_title="Memory %"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Latency anomaly detection
    st.subheader("⚡ Latency Spike Detection")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Baseline Latency**")
        st.json({"p95": 100.0, "p99": 200.0})
    
    with col2:
        st.write("**Current Latency**")
        current_latency = {"p95": 150.0, "p99": 300.0}
        st.json(current_latency)
    
    baseline_latency = {"p95": 100.0, "p99": 200.0}
    latency_anomaly = st.session_state.anomaly_detector.detect_latency_anomaly(
        current_latency,
        baseline_latency
    )
    
    if latency_anomaly.is_anomaly:
        st.warning(f"⚠️ Latency spike detected: {latency_anomaly.description}")
    else:
        st.success("✅ Latency is normal")


# Tab 4: Root Cause Analysis
with tab4:
    st.header("🎯 Root Cause Analysis")
    st.markdown("Automated incident investigation with timeline and recommendations")
    
    incident_id = st.text_input("Incident ID", value="INC-001")
    
    if st.button("🔍 Analyze Incident", key="analyze_incident"):
        with st.spinner("Analyzing incident..."):
            # Get error logs for analysis
            error_logs = [log for log in st.session_state.sample_logs if log.level == LogLevel.ERROR]
            
            import asyncio
            
            # Run async analysis
            analysis = asyncio.run(
                st.session_state.root_cause_analyzer.analyze_incident(
                    incident_id,
                    error_logs
                )
            )
            st.session_state.rca_analysis = analysis
    
    if "rca_analysis" in st.session_state:
        analysis = st.session_state.rca_analysis
        
        # Overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Incident ID", analysis.incident_id)
        
        with col2:
            if analysis.root_cause:
                st.metric("Confidence", f"{analysis.root_cause.confidence*100:.0f}%")
        
        with col3:
            if analysis.timeline:
                st.metric("Duration (sec)", f"{analysis.timeline.duration_seconds:.0f}")
        
        # Root cause
        if analysis.root_cause:
            st.subheader("🎯 Root Cause")
            
            with st.container():
                st.write(f"**Category:** {analysis.root_cause.category.upper()}")
                st.write(f"**Description:** {analysis.root_cause.description}")
                st.write(f"**Confidence:** {analysis.root_cause.confidence*100:.0f}%")
                
                st.write("**Evidence:**")
                for evidence in analysis.root_cause.evidence[:5]:
                    st.write(f"- {evidence}")
        
        # Contributing factors
        if analysis.contributing_factors:
            st.subheader("📌 Contributing Factors")
            
            for factor in analysis.contributing_factors:
                st.write(f"- {factor}")
        
        # Timeline
        if analysis.timeline:
            st.subheader("⏱️ Incident Timeline")
            
            df = pd.DataFrame(analysis.timeline.events)
            st.dataframe(df, use_container_width=True, height=300)
        
        # Recommendations
        if analysis.recommendations:
            st.subheader("💡 Recommendations")
            
            for i, rec in enumerate(analysis.recommendations):
                st.write(f"{i+1}. {rec}")


# Tab 5: Predictive Maintenance
with tab5:
    st.header("🔮 Predictive Maintenance")
    st.markdown("Predict failures before they happen and recommend preventive actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        service_name = st.selectbox(
            "Select Service",
            options=["api-gateway", "user-service", "database", "cache"]
        )
    
    with col2:
        metric_name = st.selectbox(
            "Select Metric",
            options=["error_rate", "memory_usage", "cpu_usage", "latency"]
        )
    
    if st.button("🔮 Predict Failure", key="predict_failure"):
        with st.spinner("Analyzing trends..."):
            # Generate sample time series data
            timestamps = [datetime.now() - timedelta(hours=23-i) for i in range(24)]
            
            # Generate increasing trend for demo
            if metric_name == "error_rate":
                values = [0.01 + (i * 0.003) for i in range(24)]
            elif metric_name == "memory_usage":
                values = [60 + (i * 1.2) for i in range(24)]
            else:
                values = [30 + (i * 0.8) for i in range(24)]
            
            # Predict failure
            prediction = st.session_state.predictive_maintenance.predict_failure(
                service_name,
                metric_name,
                timestamps,
                values
            )
            
            st.session_state.prediction = prediction
            st.session_state.prediction_values = values
            st.session_state.prediction_timestamps = timestamps
    
    if "prediction" in st.session_state:
        prediction = st.session_state.prediction
        
        # Prediction result
        if prediction.likely_failure:
            st.error(f"⚠️ **FAILURE PREDICTED**")
        else:
            st.success(f"✅ **NO FAILURE EXPECTED**")
        
        # Metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Confidence", f"{prediction.confidence*100:.0f}%")
        
        with col2:
            if prediction.estimated_time_to_failure:
                hours = prediction.estimated_time_to_failure.total_seconds() / 3600
                st.metric("Time to Failure", f"{hours:.1f}h")
            else:
                st.metric("Time to Failure", "N/A")
        
        with col3:
            st.metric("Service", prediction.service)
        
        st.write(f"**Reason:** {prediction.reason}")
        
        # Plot trend
        st.subheader("📈 Trend Analysis")
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[t.strftime('%H:%M') for t in st.session_state.prediction_timestamps],
            y=st.session_state.prediction_values,
            mode='lines+markers',
            name=prediction.metric
        ))
        
        if prediction.likely_failure:
            # Add warning threshold
            fig.add_hline(
                y=max(st.session_state.prediction_values) * 0.9,
                line_dash="dash",
                line_color="red",
                annotation_text="Warning Threshold"
            )
        
        fig.update_layout(
            title=f"{prediction.metric} - 24h Trend",
            xaxis_title="Time",
            yaxis_title=prediction.metric
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Recommended actions
        if prediction.likely_failure:
            st.subheader("🛠️ Recommended Actions")
            
            actions = st.session_state.predictive_maintenance.recommend_actions(prediction)
            
            for i, action in enumerate(actions):
                with st.expander(f"Action {i+1}: {action.description} - {action.priority.upper()}", expanded=True):
                    st.write(f"**Priority:** {action.priority}")
                    st.write(f"**Impact:** {action.estimated_impact}")
                    st.write("**Steps:**")
                    for step in action.steps:
                        st.write(f"- {step}")


# Tab 6: Analytics
with tab6:
    st.header("📊 System Analytics")
    
    # Service health overview
    st.subheader("🏥 Service Health Overview")
    
    services = list(set(log.service for log in st.session_state.sample_logs))
    service_health = []
    
    for service in services:
        service_logs = [log for log in st.session_state.sample_logs if log.service == service]
        error_count = len([log for log in service_logs if log.level == LogLevel.ERROR])
        error_rate = error_count / len(service_logs) if service_logs else 0
        
        health_status = "🟢 Healthy" if error_rate < 0.05 else "🟡 Warning" if error_rate < 0.10 else "🔴 Critical"
        
        service_health.append({
            "Service": service,
            "Total Logs": len(service_logs),
            "Errors": error_count,
            "Error Rate": f"{error_rate*100:.2f}%",
            "Status": health_status
        })
    
    df = pd.DataFrame(service_health)
    st.dataframe(df, use_container_width=True)
    
    # Logs over time
    st.subheader("📈 Logs Over Time")
    
    # Group logs by 5-minute intervals
    from collections import defaultdict
    
    time_buckets = defaultdict(lambda: {"info": 0, "warning": 0, "error": 0})
    
    for log in st.session_state.sample_logs:
        bucket = log.timestamp.replace(second=0, microsecond=0)
        minute = bucket.minute - (bucket.minute % 5)
        bucket = bucket.replace(minute=minute)
        
        if log.level == LogLevel.INFO:
            time_buckets[bucket]["info"] += 1
        elif log.level == LogLevel.WARNING:
            time_buckets[bucket]["warning"] += 1
        elif log.level == LogLevel.ERROR:
            time_buckets[bucket]["error"] += 1
    
    sorted_times = sorted(time_buckets.keys())
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=[t.strftime('%H:%M') for t in sorted_times],
        y=[time_buckets[t]["info"] for t in sorted_times],
        mode='lines',
        name='INFO',
        fill='tonexty'
    ))
    
    fig.add_trace(go.Scatter(
        x=[t.strftime('%H:%M') for t in sorted_times],
        y=[time_buckets[t]["warning"] for t in sorted_times],
        mode='lines',
        name='WARNING',
        fill='tonexty'
    ))
    
    fig.add_trace(go.Scatter(
        x=[t.strftime('%H:%M') for t in sorted_times],
        y=[time_buckets[t]["error"] for t in sorted_times],
        mode='lines',
        name='ERROR',
        fill='tonexty'
    ))
    
    fig.update_layout(
        title="Log Activity Over Time (5min intervals)",
        xaxis_title="Time",
        yaxis_title="Log Count"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Service comparison
    st.subheader("⚖️ Service Comparison")
    
    service_data = []
    for service in services:
        service_logs = [log for log in st.session_state.sample_logs if log.service == service]
        service_data.append({
            "Service": service,
            "Total": len(service_logs),
            "INFO": len([l for l in service_logs if l.level == LogLevel.INFO]),
            "WARNING": len([l for l in service_logs if l.level == LogLevel.WARNING]),
            "ERROR": len([l for l in service_logs if l.level == LogLevel.ERROR])
        })
    
    df = pd.DataFrame(service_data)
    
    fig = px.bar(
        df,
        x="Service",
        y=["INFO", "WARNING", "ERROR"],
        title="Logs by Service and Level",
        barmode="group"
    )
    st.plotly_chart(fig, use_container_width=True)


# Footer
st.markdown("---")
st.markdown("**Logs MCP** - Intelligent Observability System | Transform logs into strategic intelligence")

