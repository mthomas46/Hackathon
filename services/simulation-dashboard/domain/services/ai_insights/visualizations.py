"""AI Insights Visualization Functions.

This module provides visualization functions for AI-powered insights,
charts, graphs, and interactive displays.
"""

from typing import Any, Dict, List

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def display_patterns(patterns: List[Dict[str, Any]]):
    """Display discovered patterns in an organized format."""
    if not patterns:
        st.info("No significant patterns detected in the data.")
        return
    
    st.markdown("#### 🔍 Discovered Patterns")
    
    # Group patterns by type
    by_type = {}
    for pattern in patterns:
        ptype = pattern.get('type', 'unknown')
        if ptype not in by_type:
            by_type[ptype] = []
        by_type[ptype].append(pattern)
    
    for pattern_type, type_patterns in by_type.items():
        with st.expander(f"{pattern_type.title()} Patterns ({len(type_patterns)})", expanded=True):
            for pattern in type_patterns:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**{pattern.get('description', 'Unknown pattern')}**")
                    if 'metrics' in pattern:
                        st.write(f"📊 Metrics: {', '.join(pattern['metrics'])}")
                
                with col2:
                    impact = pattern.get('impact', 'medium')
                    color = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(impact, '🟡')
                    st.metric("Impact", impact.title(), delta_color="off")
                    st.write(f"{color} {impact.title()}")


def display_recommendations(recommendations: List[Dict[str, Any]]):
    """Display intelligent recommendations."""
    if not recommendations:
        st.info("No recommendations available at this time.")
        return
    
    st.markdown("#### 💡 Intelligent Recommendations")
    
    # Group by priority
    by_priority = {'high': [], 'medium': [], 'low': []}
    for rec in recommendations:
        priority = rec.get('priority', 'medium')
        by_priority[priority].append(rec)
    
    for priority in ['high', 'medium', 'low']:
        if by_priority[priority]:
            priority_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(priority, '🟡')
            with st.expander(f"{priority_icon} {priority.title()} Priority ({len(by_priority[priority])})", 
                           expanded=(priority == 'high')):
                for rec in by_priority[priority]:
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{rec.get('title', 'Unknown')}**")
                        st.write(rec.get('description', ''))
                    
                    with col2:
                        effort = rec.get('effort', 'medium')
                        st.metric("Effort", effort.title())
                    
                    with col3:
                        impact = rec.get('impact', 'medium')
                        st.metric("Impact", impact.title())


def display_anomalies(anomalies: List[Dict[str, Any]]):
    """Display detected anomalies."""
    if not anomalies:
        st.success("✅ No anomalies detected in the analyzed period.")
        return
    
    st.markdown("#### 🚨 Detected Anomalies")
    
    # Summary statistics
    severity_counts = {'high': 0, 'medium': 0, 'low': 0}
    for anomaly in anomalies:
        severity = anomaly.get('severity', 'medium')
        severity_counts[severity] += 1
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Anomalies", len(anomalies))
    with col2:
        st.metric("High Severity", severity_counts['high'])
    with col3:
        st.metric("Medium Severity", severity_counts['medium'])
    with col4:
        st.metric("Low Severity", severity_counts['low'])
    
    # Show recent anomalies
    recent_anomalies = anomalies[-10:]  # Last 10
    
    st.markdown("##### Recent Anomalies")
    
    for anomaly in recent_anomalies:
        severity_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(anomaly.get('severity', 'medium'), '🟡')
        
        with st.expander(f"{severity_icon} {anomaly.get('metric', 'Unknown').replace('_', ' ').title()} "
                        f"at {anomaly.get('timestamp', 'Unknown')}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Actual Value", ".1f")
                st.metric("Expected Value", ".1f")
            
            with col2:
                st.metric("Deviation", ".1f")
                st.metric("Severity", anomaly.get('severity', 'medium').title())


def display_predictions(category: str, predictions_data: Dict[str, Any]):
    """Display prediction results."""
    st.markdown(f"#### 🔮 {category.title()} Predictions")
    
    next_hour = predictions_data.get('next_hour', {})
    next_24h = predictions_data.get('next_24h', {})
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Predicted CPU", ".1f", 
                 delta="%.1f" % (next_hour.get('cpu_usage', 0) - 70))
    
    with col2:
        st.metric("Predicted Memory", ".1f",
                 delta="%.1f" % (next_hour.get('memory_usage', 0) - 75))
    
    with col3:
        st.metric("Predicted Response Time", ".1f",
                 delta="%.1f" % (next_hour.get('response_time', 0) - 150))
    
    st.markdown("##### 24-Hour Forecast")
    trend = next_24h.get('trend', 'unknown')
    trend_icon = {'increasing': '📈', 'decreasing': '📉', 'stable': '📊'}.get(trend, '📊')
    
    st.info(f"{trend_icon} **Trend:** {trend.title()} | "
            f"**Peak Usage:** {next_24h.get('peak_usage', 0):.1f}% | "
            f"**Recommended Capacity:** {next_24h.get('recommended_capacity', 0):.1f}%")
    
    insights = predictions_data.get('insights', [])
    if insights:
        st.markdown("##### Key Insights")
        for insight in insights:
            st.write(f"💡 {insight}")


def display_optimization_plan(plan: Dict[str, Any]):
    """Display optimization plan and recommendations."""
    st.markdown("#### 🚀 Optimization Plan")
    
    # Implementation overview
    col1, col2, col3 = st.columns(3)
    
    benefits = plan.get('estimated_benefits', {})
    
    with col1:
        st.metric("Performance Gain", ".1f")
    
    with col2:
        st.metric("Cost Reduction", ".1f")
    
    with col3:
        st.metric("Reliability Improvement", ".1f")
    
    st.markdown(f"**Implementation Effort:** {plan.get('implementation_effort', 'medium').title()}")
    st.markdown(f"**Timeline:** {plan.get('timeline', 'Unknown')}")
    
    # Action items
    for action_type in ['immediate_actions', 'short_term', 'long_term']:
        actions = plan.get(action_type, [])
        if actions:
            title = action_type.replace('_', ' ').title()
            with st.expander(f"📋 {title} ({len(actions)})", expanded=(action_type == 'immediate_actions')):
                for action in actions:
                    st.write(f"• {action}")


def render_pattern_visualization(patterns: List[Dict[str, Any]]):
    """Render pattern visualization charts."""
    if not patterns:
        return
    
    st.markdown("##### Pattern Visualizations")
    
    # Create a summary chart of pattern types
    pattern_types = {}
    for pattern in patterns:
        ptype = pattern.get('type', 'unknown')
        pattern_types[ptype] = pattern_types.get(ptype, 0) + 1
    
    if pattern_types:
        fig = px.bar(
            x=list(pattern_types.keys()),
            y=list(pattern_types.values()),
            title="Pattern Types Distribution",
            labels={'x': 'Pattern Type', 'y': 'Count'}
        )
        st.plotly_chart(fig, use_container_width=True)


def render_anomaly_visualization(anomalies: List[Dict[str, Any]]):
    """Render anomaly visualization charts."""
    if not anomalies:
        return
    
    st.markdown("##### Anomaly Visualizations")
    
    # Convert to DataFrame for plotting
    df = pd.DataFrame(anomalies)
    
    if not df.empty and 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Severity distribution
        severity_counts = df['severity'].value_counts()
        fig = px.pie(
            values=severity_counts.values,
            names=severity_counts.index,
            title="Anomaly Severity Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Timeline of anomalies
        if len(df) > 1:
            df_sorted = df.sort_values('timestamp')
            fig2 = px.scatter(
                df_sorted,
                x='timestamp',
                y='value',
                color='severity',
                size='deviation',
                title="Anomaly Timeline"
            )
            st.plotly_chart(fig2, use_container_width=True)


def render_predictive_visualization(category: str, predictions_data: Dict[str, Any]):
    """Render predictive analytics visualizations."""
    st.markdown(f"##### {category.title()} Predictive Visualizations")
    
    # Create sample prediction data for visualization
    hours = list(range(25))  # Next 24 hours + current
    predicted_cpu = [70 + np.random.normal(0, 5) for _ in hours]
    predicted_memory = [75 + np.random.normal(0, 3) for _ in hours]
    
    # Create subplot
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('CPU Usage Prediction', 'Memory Usage Prediction'),
        shared_xaxes=True
    )
    
    # CPU prediction
    fig.add_trace(
        go.Scatter(x=hours, y=predicted_cpu, mode='lines+markers', name='Predicted CPU'),
        row=1, col=1
    )
    
    # Memory prediction
    fig.add_trace(
        go.Scatter(x=hours, y=predicted_memory, mode='lines+markers', name='Predicted Memory'),
        row=2, col=1
    )
    
    fig.update_layout(height=600, title_text="24-Hour Resource Prediction")
    st.plotly_chart(fig, use_container_width=True)


def render_recommendation_impact_analysis(recommendations: List[Dict[str, Any]]):
    """Render recommendation impact analysis visualization."""
    if not recommendations:
        return
    
    st.markdown("##### Recommendation Impact Analysis")
    
    # Create impact vs effort matrix
    impact_levels = {'high': 3, 'medium': 2, 'low': 1}
    effort_levels = {'high': 3, 'medium': 2, 'low': 1}
    
    impact_scores = []
    effort_scores = []
    titles = []
    
    for rec in recommendations:
        impact_scores.append(impact_levels.get(rec.get('impact', 'medium'), 2))
        effort_scores.append(effort_levels.get(rec.get('effort', 'medium'), 2))
        titles.append(rec.get('title', 'Unknown'))
    
    # Create scatter plot
    fig = px.scatter(
        x=effort_scores,
        y=impact_scores,
        text=titles,
        title="Impact vs Effort Analysis",
        labels={'x': 'Effort Level', 'y': 'Impact Level'}
    )
    
    fig.update_traces(textposition='top center')
    fig.update_xaxes(tickvals=[1, 2, 3], ticktext=['Low', 'Medium', 'High'])
    fig.update_yaxes(tickvals=[1, 2, 3], ticktext=['Low', 'Medium', 'High'])
    
    st.plotly_chart(fig, use_container_width=True)
