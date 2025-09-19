"""Anomaly Detection Charts Components.

This module provides chart components for displaying anomaly detection results,
outlier analysis, and pattern recognition visualizations.
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    st.warning("⚠️ Plotly not available. Anomaly chart components will be limited.")


def render_anomaly_chart(
    anomaly_data: Dict[str, Any],
    title: str = "Anomaly Detection Results",
    width: Optional[int] = None,
    height: Optional[int] = 400
) -> None:
    """Render anomaly detection results chart.

    Args:
        anomaly_data: Anomaly detection data with timestamps, values, and anomaly scores
        title: Chart title
        width: Chart width
        height: Chart height
    """
    if not PLOTLY_AVAILABLE:
        st.error("❌ Plotly is required for anomaly chart components")
        return

    try:
        st.markdown(f"### {title}")

        if not anomaly_data or 'data' not in anomaly_data:
            st.info("No anomaly data available")
            return

        data = anomaly_data['data']

        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)

            # Ensure required columns exist
            if 'timestamp' not in df.columns or 'value' not in df.columns:
                st.error("❌ Anomaly data missing required columns (timestamp, value)")
                return

            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Check for anomaly indicators
            anomaly_col = None
            for col in ['is_anomaly', 'anomaly', 'outlier', 'anomaly_score']:
                if col in df.columns:
                    anomaly_col = col
                    break

            # Create the main chart
            fig = go.Figure()

            # Add the main data line
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['value'],
                mode='lines',
                name='Normal Data',
                line=dict(color='blue', width=2)
            ))

            # Highlight anomalies if available
            if anomaly_col:
                if anomaly_col == 'anomaly_score':
                    # For anomaly scores, show as a separate trace
                    fig.add_trace(go.Scatter(
                        x=df['timestamp'],
                        y=df['anomaly_score'],
                        mode='lines',
                        name='Anomaly Score',
                        line=dict(color='orange', width=1),
                        yaxis='y2'
                    ))
                else:
                    # For boolean anomaly indicators, highlight anomalous points
                    anomaly_df = df[df[anomaly_col] == True]
                    if not anomaly_df.empty:
                        fig.add_trace(go.Scatter(
                            x=anomaly_df['timestamp'],
                            y=anomaly_df['value'],
                            mode='markers',
                            name='Anomalies',
                            marker=dict(
                                size=8,
                                color='red',
                                symbol='x'
                            )
                        ))

            # Update layout
            fig.update_layout(
                title=title,
                width=width,
                height=height,
                xaxis_title="Time",
                yaxis_title="Value",
                yaxis2=dict(
                    title="Anomaly Score",
                    overlaying="y",
                    side="right"
                ) if anomaly_col == 'anomaly_score' else None
            )

            st.plotly_chart(fig, use_container_width=True)

            # Display anomaly summary
            render_anomaly_summary(df, anomaly_col)

        else:
            st.info("No anomaly data to display")

    except Exception as e:
        st.error(f"❌ Error rendering anomaly chart: {str(e)}")


def render_anomaly_summary(df: pd.DataFrame, anomaly_col: Optional[str]) -> None:
    """Render anomaly detection summary."""
    try:
        if df.empty:
            return

        st.markdown("#### 📊 Anomaly Detection Summary")

        if anomaly_col:
            if anomaly_col == 'anomaly_score':
                # For anomaly scores, show distribution
                scores = df['anomaly_score'].dropna()
                if not scores.empty:
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        avg_score = scores.mean()
                        st.metric("Average Score", ".3f", avg_score)

                    with col2:
                        max_score = scores.max()
                        st.metric("Peak Score", ".3f", max_score)

                    with col3:
                        threshold = scores.quantile(0.95)  # 95th percentile as threshold
                        st.metric("Threshold (95%)", ".3f", threshold)

                    # Show score distribution
                    st.markdown("##### Anomaly Score Distribution")
                    fig = px.histogram(
                        scores,
                        title="Anomaly Score Distribution",
                        labels={'value': 'Anomaly Score', 'count': 'Frequency'},
                        nbins=30
                    )
                    st.plotly_chart(fig, use_container_width=True)

            else:
                # For boolean indicators, show counts
                total_points = len(df)
                anomaly_points = df[anomaly_col].sum() if df[anomaly_col].dtype == bool else 0
                normal_points = total_points - anomaly_points

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Total Data Points", total_points)

                with col2:
                    st.metric("Anomalies Detected", anomaly_points)

                with col3:
                    anomaly_rate = (anomaly_points / total_points) * 100 if total_points > 0 else 0
                    st.metric("Anomaly Rate", ".2f", anomaly_rate)

                # Create pie chart for anomaly distribution
                fig = px.pie(
                    values=[normal_points, anomaly_points],
                    names=['Normal', 'Anomalies'],
                    title="Data Point Classification",
                    color=['Normal', 'Anomalies'],
                    color_discrete_map={'Normal': 'blue', 'Anomalies': 'red'}
                )
                st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("No anomaly indicators available for summary")

    except Exception as e:
        st.error(f"❌ Error rendering anomaly summary: {str(e)}")


def render_pattern_recognition_chart(
    pattern_data: Dict[str, Any],
    title: str = "Pattern Recognition Results",
    width: Optional[int] = None,
    height: Optional[int] = 400
) -> None:
    """Render pattern recognition results chart.

    Args:
        pattern_data: Pattern recognition data with clusters or patterns
        title: Chart title
        width: Chart width
        height: Chart height
    """
    if not PLOTLY_AVAILABLE:
        st.error("❌ Plotly is required for chart components")
        return

    try:
        st.markdown(f"### {title}")

        if not pattern_data or 'data' not in pattern_data:
            st.info("No pattern data available")
            return

        data = pattern_data['data']

        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)

            if 'timestamp' not in df.columns:
                st.error("❌ Pattern data missing timestamp column")
                return

            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Check for cluster or pattern indicators
            cluster_col = None
            for col in ['cluster', 'pattern', 'segment', 'group']:
                if col in df.columns:
                    cluster_col = col
                    break

            # Create pattern visualization
            if cluster_col and len(df[cluster_col].unique()) <= 10:  # Reasonable number of clusters
                # Create scatter plot with clusters
                fig = px.scatter(
                    df,
                    x='timestamp',
                    y=df.select_dtypes(include=[np.number]).columns[0] if len(df.select_dtypes(include=[np.number]).columns) > 0 else 'value',
                    color=cluster_col,
                    title=title,
                    labels={'color': 'Pattern/Cluster'}
                )
            else:
                # Create line plot with patterns highlighted
                fig = go.Figure()

                # Add main data line
                value_col = df.select_dtypes(include=[np.number]).columns[0] if len(df.select_dtypes(include=[np.number]).columns) > 0 else None
                if value_col:
                    fig.add_trace(go.Scatter(
                        x=df['timestamp'],
                        y=df[value_col],
                        mode='lines',
                        name='Data Pattern',
                        line=dict(color='blue', width=2)
                    ))

                # Add pattern markers if available
                if cluster_col:
                    for pattern in df[cluster_col].unique():
                        pattern_df = df[df[cluster_col] == pattern]
                        if not pattern_df.empty and value_col:
                            fig.add_trace(go.Scatter(
                                x=pattern_df['timestamp'],
                                y=pattern_df[value_col],
                                mode='markers',
                                name=f'Pattern {pattern}',
                                marker=dict(size=6)
                            ))

            fig.update_layout(
                title=title,
                width=width,
                height=height,
                xaxis_title="Time",
                yaxis_title="Value"
            )

            st.plotly_chart(fig, use_container_width=True)

            # Display pattern summary
            render_pattern_summary(df, cluster_col)

        else:
            st.info("No pattern data to display")

    except Exception as e:
        st.error(f"❌ Error rendering pattern recognition chart: {str(e)}")


def render_pattern_summary(df: pd.DataFrame, cluster_col: Optional[str]) -> None:
    """Render pattern recognition summary."""
    try:
        if df.empty:
            return

        st.markdown("#### 📊 Pattern Recognition Summary")

        if cluster_col:
            # Show cluster/pattern distribution
            cluster_counts = df[cluster_col].value_counts().reset_index()
            cluster_counts.columns = ['Pattern', 'Count']

            col1, col2, col3 = st.columns(3)

            with col1:
                total_patterns = len(cluster_counts)
                st.metric("Patterns Identified", total_patterns)

            with col2:
                most_common = cluster_counts.iloc[0]['Pattern'] if not cluster_counts.empty else 'None'
                st.metric("Most Common", str(most_common))

            with col3:
                avg_pattern_size = cluster_counts['Count'].mean()
                st.metric("Avg Pattern Size", ".1f", avg_pattern_size)

            # Show pattern distribution chart
            fig = px.bar(
                cluster_counts,
                x='Pattern',
                y='Count',
                title="Pattern Distribution",
                labels={'Pattern': 'Pattern Type', 'Count': 'Occurrences'}
            )
            st.plotly_chart(fig, use_container_width=True)

            # Display pattern details table
            st.markdown("##### Pattern Details")
            st.dataframe(cluster_counts, use_container_width=True)

        else:
            # Show general statistics
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                col1, col2, col3 = st.columns(3)

                with col1:
                    total_points = len(df)
                    st.metric("Total Data Points", total_points)

                with col2:
                    avg_value = df[numeric_cols[0]].mean()
                    st.metric("Average Value", ".2f", avg_value)

                with col3:
                    std_value = df[numeric_cols[0]].std()
                    st.metric("Value Variability", ".2f", std_value)

    except Exception as e:
        st.error(f"❌ Error rendering pattern summary: {str(e)}")


def render_outlier_analysis_chart(
    outlier_data: Dict[str, Any],
    title: str = "Outlier Analysis",
    width: Optional[int] = None,
    height: Optional[int] = 400
) -> None:
    """Render outlier analysis chart.

    Args:
        outlier_data: Outlier analysis data
        title: Chart title
        width: Chart width
        height: Chart height
    """
    if not PLOTLY_AVAILABLE:
        st.error("❌ Plotly is required for chart components")
        return

    try:
        st.markdown(f"### {title}")

        if not outlier_data or 'data' not in outlier_data:
            st.info("No outlier data available")
            return

        data = outlier_data['data']

        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)

            if 'timestamp' not in df.columns:
                st.error("❌ Outlier data missing timestamp column")
                return

            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Get value column
            value_col = None
            for col in ['value', 'metric', 'measurement']:
                if col in df.columns:
                    value_col = col
                    break

            if not value_col:
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                value_col = numeric_cols[0] if numeric_cols else None

            if not value_col:
                st.info("No numeric data found for outlier analysis")
                return

            # Create box plot for outlier visualization
            fig = go.Figure()

            # Add main data as scatter plot
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df[value_col],
                mode='markers',
                name='Data Points',
                marker=dict(
                    size=4,
                    color='blue',
                    opacity=0.6
                )
            ))

            # Identify and highlight outliers using IQR method
            values = df[value_col].dropna()
            if len(values) > 0:
                Q1 = values.quantile(0.25)
                Q3 = values.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                outliers = df[(df[value_col] < lower_bound) | (df[value_col] > upper_bound)]

                if not outliers.empty:
                    fig.add_trace(go.Scatter(
                        x=outliers['timestamp'],
                        y=outliers[value_col],
                        mode='markers',
                        name='Outliers',
                        marker=dict(
                            size=8,
                            color='red',
                            symbol='x'
                        )
                    ))

                # Add IQR bounds
                fig.add_hline(
                    y=lower_bound,
                    line_dash="dash",
                    line_color="orange",
                    annotation_text="Lower Bound"
                )
                fig.add_hline(
                    y=upper_bound,
                    line_dash="dash",
                    line_color="orange",
                    annotation_text="Upper Bound"
                )

            fig.update_layout(
                title=title,
                width=width,
                height=height,
                xaxis_title="Time",
                yaxis_title="Value"
            )

            st.plotly_chart(fig, use_container_width=True)

            # Display outlier statistics
            render_outlier_summary(df, value_col, lower_bound if 'lower_bound' in locals() else None, upper_bound if 'upper_bound' in locals() else None)

        else:
            st.info("No outlier data to display")

    except Exception as e:
        st.error(f"❌ Error rendering outlier analysis chart: {str(e)}")


def render_outlier_summary(df: pd.DataFrame, value_col: str, lower_bound: Optional[float], upper_bound: Optional[float]) -> None:
    """Render outlier analysis summary."""
    try:
        if df.empty or not value_col or value_col not in df.columns:
            return

        st.markdown("#### 📊 Outlier Analysis Summary")

        values = df[value_col].dropna()

        if values.empty:
            return

        # Calculate outlier statistics
        if lower_bound is not None and upper_bound is not None:
            outliers = df[(df[value_col] < lower_bound) | (df[value_col] > upper_bound)]
            outlier_count = len(outliers)
            total_count = len(df)
            outlier_percentage = (outlier_count / total_count) * 100 if total_count > 0 else 0
        else:
            outlier_count = 0
            outlier_percentage = 0

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Data Points", len(df))

        with col2:
            st.metric("Outliers Detected", outlier_count)

        with col3:
            st.metric("Outlier Percentage", ".2f", outlier_percentage)

        with col4:
            if outlier_count > 0:
                avg_outlier_value = outliers[value_col].mean()
                st.metric("Avg Outlier Value", ".2f", avg_outlier_value)
            else:
                st.metric("No Outliers Found", "✓")

        # Show distribution with outliers highlighted
        if outlier_count > 0:
            st.markdown("##### Outlier Distribution")

            fig = px.histogram(
                values,
                title="Value Distribution with Outlier Bounds",
                labels={'value': 'Value', 'count': 'Frequency'},
                nbins=30
            )

            # Add outlier bounds
            if lower_bound is not None:
                fig.add_vline(x=lower_bound, line_dash="dash", line_color="red", annotation_text="Lower Bound")
            if upper_bound is not None:
                fig.add_vline(x=upper_bound, line_dash="dash", line_color="red", annotation_text="Upper Bound")

            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error rendering outlier summary: {str(e)}")


def render_anomaly_timeline_chart(
    anomaly_timeline: Dict[str, Any],
    title: str = "Anomaly Timeline",
    width: Optional[int] = None,
    height: Optional[int] = 400
) -> None:
    """Render anomaly timeline chart showing anomaly patterns over time.

    Args:
        anomaly_timeline: Anomaly timeline data
        title: Chart title
        width: Chart width
        height: Chart height
    """
    if not PLOTLY_AVAILABLE:
        st.error("❌ Plotly is required for chart components")
        return

    try:
        st.markdown(f"### {title}")

        if not anomaly_timeline or 'data' not in anomaly_timeline:
            st.info("No anomaly timeline data available")
            return

        data = anomaly_timeline['data']

        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)

            if 'timestamp' not in df.columns:
                st.error("❌ Timeline data missing timestamp column")
                return

            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Aggregate anomalies by time period
            df['date'] = df['timestamp'].dt.date
            daily_anomalies = df.groupby('date').size().reset_index(name='anomaly_count')

            # Create timeline chart
            fig = px.bar(
                daily_anomalies,
                x='date',
                y='anomaly_count',
                title=title,
                labels={'date': 'Date', 'anomaly_count': 'Number of Anomalies'}
            )

            # Add trend line
            if len(daily_anomalies) > 1:
                daily_anomalies['rolling_avg'] = daily_anomalies['anomaly_count'].rolling(window=7).mean()
                fig.add_trace(go.Scatter(
                    x=daily_anomalies['date'],
                    y=daily_anomalies['rolling_avg'],
                    mode='lines',
                    name='7-Day Rolling Average',
                    line=dict(color='red', width=2)
                ))

            fig.update_layout(
                width=width,
                height=height,
                xaxis_title="Date",
                yaxis_title="Anomaly Count"
            )

            st.plotly_chart(fig, use_container_width=True)

            # Display timeline insights
            render_timeline_insights(daily_anomalies)

        else:
            st.info("No timeline data to display")

    except Exception as e:
        st.error(f"❌ Error rendering anomaly timeline chart: {str(e)}")


def render_timeline_insights(df: pd.DataFrame) -> None:
    """Render timeline insights and patterns."""
    try:
        if df.empty:
            return

        st.markdown("#### 📊 Timeline Insights")

        col1, col2, col3 = st.columns(3)

        with col1:
            total_anomalies = df['anomaly_count'].sum()
            st.metric("Total Anomalies", total_anomalies)

        with col2:
            avg_daily = df['anomaly_count'].mean()
            st.metric("Daily Average", ".1f", avg_daily)

        with col3:
            peak_day = df.loc[df['anomaly_count'].idxmax()]
            st.metric("Peak Day", f"{peak_day['anomaly_count']} anomalies")

        # Show anomaly patterns
        st.markdown("##### Anomaly Patterns")

        # Find days with high anomaly counts
        threshold = df['anomaly_count'].quantile(0.95)  # Top 5% of days
        high_anomaly_days = df[df['anomaly_count'] >= threshold]

        if not high_anomaly_days.empty:
            st.markdown("**High Anomaly Days:**")
            for _, row in high_anomaly_days.iterrows():
                st.write(f"• {row['date']}: {row['anomaly_count']} anomalies")
        else:
            st.info("No unusually high anomaly days detected")

    except Exception as e:
        st.error(f"❌ Error rendering timeline insights: {str(e)}")
