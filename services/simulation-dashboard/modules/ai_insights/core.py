"""Core AI Insights Data Processing and Analysis.

This module provides core data processing, statistical analysis,
and foundational functions for AI-powered insights.
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

import numpy as np
import pandas as pd


def generate_sample_data() -> list:
    """Generate sample simulation data for analysis."""
    data = []
    base_time = datetime.now() - timedelta(days=30)
    
    for i in range(720):  # 30 days * 24 hours
        timestamp = base_time + timedelta(hours=i)
        # Generate realistic simulation metrics
        cpu_usage = 45 + 25 * np.sin(i * 0.1) + np.random.normal(0, 5)
        memory_usage = 60 + 20 * np.cos(i * 0.15) + np.random.normal(0, 3)
        response_time = 150 + 50 * np.sin(i * 0.05) + np.random.normal(0, 10)
        
        # Add occasional anomalies
        if random.random() < 0.05:  # 5% chance of anomaly
            cpu_usage *= random.uniform(1.5, 2.0)
            memory_usage *= random.uniform(1.3, 1.8)
            response_time *= random.uniform(1.2, 2.5)
        
        data.append({
            'timestamp': timestamp,
            'cpu_usage': max(0, min(100, cpu_usage)),
            'memory_usage': max(0, min(100, memory_usage)),
            'response_time': max(0, response_time),
            'requests_per_second': 100 + 50 * np.sin(i * 0.08) + np.random.normal(0, 10),
            'error_rate': max(0, 0.01 + 0.05 * np.sin(i * 0.12) + np.random.normal(0, 0.005))
        })
    
    return data


def display_basic_statistics(data: list):
    """Display basic statistical analysis of the data."""
    if not data:
        st.warning("No data available for statistical analysis.")
        return
    
    df = pd.DataFrame(data)
    
    st.markdown("#### 📊 Basic Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Records", len(df))
        st.metric("Date Range", f"{df['timestamp'].min().date()} to {df['timestamp'].max().date()}")
    
    with col2:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        st.metric("Metrics Tracked", len(numeric_cols))
        st.metric("Avg CPU Usage", ".1f")
    
    with col3:
        st.metric("Avg Memory Usage", ".1f")
        st.metric("Avg Response Time", ".1f")


def detect_basic_anomalies(data: list, threshold: float) -> dict:
    """Detect basic anomalies using statistical methods."""
    if not data:
        return {"anomalies": [], "count": 0, "percentage": 0}
    
    df = pd.DataFrame(data)
    anomalies = []
    
    # Calculate rolling statistics for each metric
    for col in ['cpu_usage', 'memory_usage', 'response_time']:
        if col in df.columns:
            rolling_mean = df[col].rolling(window=24, center=True).mean()
            rolling_std = df[col].rolling(window=24, center=True).std()
            
            # Detect anomalies using z-score
            z_scores = np.abs((df[col] - rolling_mean) / rolling_std)
            anomaly_mask = z_scores > threshold
            
            for idx in df[anomaly_mask].index:
                anomalies.append({
                    'timestamp': df.loc[idx, 'timestamp'],
                    'metric': col,
                    'value': df.loc[idx, col],
                    'expected': rolling_mean.loc[idx],
                    'deviation': abs(df.loc[idx, col] - rolling_mean.loc[idx]),
                    'severity': 'high' if z_scores.loc[idx] > threshold * 2 else 'medium'
                })
    
    return {
        "anomalies": anomalies,
        "count": len(anomalies),
        "percentage": len(anomalies) / len(data) * 100 if data else 0
    }


def display_anomaly_results(results: dict):
    """Display anomaly detection results."""
    anomalies = results.get("anomalies", [])
    count = results.get("count", 0)
    percentage = results.get("percentage", 0)
    
    st.markdown("#### 🚨 Anomaly Detection Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Anomalies", count)
    
    with col2:
        st.metric("Anomaly Rate", ".2f")
    
    with col3:
        severity = "High" if percentage > 10 else "Medium" if percentage > 5 else "Low"
        st.metric("Risk Level", severity)
    
    if anomalies:
        st.markdown("##### Recent Anomalies")
        
        # Group by metric
        by_metric = {}
        for anomaly in anomalies[-10:]:  # Show last 10
            metric = anomaly['metric']
            if metric not in by_metric:
                by_metric[metric] = []
            by_metric[metric].append(anomaly)
        
        for metric, metric_anomalies in by_metric.items():
            with st.expander(f"{metric.replace('_', ' ').title()} Anomalies ({len(metric_anomalies)})"):
                for anomaly in metric_anomalies:
                    st.write(f"• {anomaly['timestamp'].strftime('%Y-%m-%d %H:%M')} - "
                           f"Value: {anomaly['value']:.1f} (Expected: {anomaly['expected']:.1f}) - "
                           f"Severity: {anomaly['severity']}")


def generate_time_series_data() -> list:
    """Generate time series data for trend analysis."""
    data = []
    base_time = datetime.now() - timedelta(days=90)  # 90 days of data
    
    for i in range(2160):  # 90 days * 24 hours
        timestamp = base_time + timedelta(hours=i)
        
        # Generate trending data with seasonality
        trend = i * 0.01  # Slight upward trend
        seasonal = 10 * np.sin(2 * np.pi * i / 24)  # Daily seasonality
        weekly = 5 * np.sin(2 * np.pi * i / (24 * 7))  # Weekly seasonality
        noise = np.random.normal(0, 2)
        
        performance_score = 70 + trend + seasonal + weekly + noise
        
        data.append({
            'timestamp': timestamp,
            'performance_score': max(0, min(100, performance_score)),
            'efficiency_rating': max(0, min(100, performance_score + np.random.normal(0, 3))),
            'resource_utilization': max(0, min(100, 80 + seasonal + noise))
        })
    
    return data


def analyze_basic_trends(data: list) -> dict:
    """Analyze basic trends in time series data."""
    if not data:
        return {"trends": {}, "insights": []}
    
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    
    trends = {}
    insights = []
    
    # Analyze each numeric column
    for col in df.select_dtypes(include=[np.number]).columns:
        # Calculate trend using linear regression
        x = np.arange(len(df))
        y = df[col].values
        
        # Simple linear regression
        slope = np.polyfit(x, y, 1)[0]
        trend_direction = "increasing" if slope > 0.01 else "decreasing" if slope < -0.01 else "stable"
        trend_strength = abs(slope) * len(df)  # Scale by data length
        
        trends[col] = {
            'direction': trend_direction,
            'strength': trend_strength,
            'slope': slope,
            'start_value': y[0],
            'end_value': y[-1],
            'change': y[-1] - y[0]
        }
        
        # Generate insights
        if trend_direction == "increasing":
            insights.append(f"{col.replace('_', ' ').title()} shows positive growth trend (+{trends[col]['change']:.1f})")
        elif trend_direction == "decreasing":
            insights.append(f"{col.replace('_', ' ').title()} shows declining trend ({trends[col]['change']:.1f})")
        else:
            insights.append(f"{col.replace('_', ' ').title()} remains stable")
    
    return {"trends": trends, "insights": insights}


def display_trend_analysis(analysis: dict):
    """Display trend analysis results."""
    trends = analysis.get("trends", {})
    insights = analysis.get("insights", [])
    
    st.markdown("#### 📈 Trend Analysis")
    
    if insights:
        st.markdown("##### Key Insights")
        for insight in insights:
            st.info(f"💡 {insight}")
    
    if trends:
        st.markdown("##### Detailed Trends")
        
        trend_data = []
        for metric, trend_info in trends.items():
            trend_data.append({
                'Metric': metric.replace('_', ' ').title(),
                'Direction': trend_info['direction'].title(),
                'Change': ".2f",
                'Strength': ".3f"
            })
        
        st.dataframe(pd.DataFrame(trend_data))
