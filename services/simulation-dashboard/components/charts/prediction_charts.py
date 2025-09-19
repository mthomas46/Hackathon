"""Prediction Charts Components.

This module provides chart components for displaying ML predictions,
forecasts, and predictive analytics visualizations.
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
    st.warning("⚠️ Plotly not available. Chart components will be limited.")


def render_prediction_chart(
    predictions: Dict[str, Any],
    chart_type: str = "line",
    title: str = "Prediction Results",
    width: Optional[int] = None,
    height: Optional[int] = 400
) -> None:
    """Render prediction chart for ML model results.

    Args:
        predictions: Dictionary containing prediction data
        chart_type: Type of chart ('line', 'scatter', 'area')
        title: Chart title
        width: Chart width
        height: Chart height
    """
    if not PLOTLY_AVAILABLE:
        st.error("❌ Plotly is required for chart components")
        return

    try:
        st.markdown(f"### {title}")

        if not predictions or 'data' not in predictions:
            st.info("No prediction data available")
            return

        data = predictions['data']

        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)

            # Ensure we have the required columns
            if 'timestamp' not in df.columns or 'predicted_value' not in df.columns:
                st.error("❌ Prediction data missing required columns (timestamp, predicted_value)")
                return

            # Convert timestamp if needed
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Create the chart
            if chart_type == "line":
                fig = px.line(
                    df,
                    x='timestamp',
                    y='predicted_value',
                    title=title,
                    labels={'predicted_value': 'Predicted Value', 'timestamp': 'Time'}
                )
            elif chart_type == "scatter":
                fig = px.scatter(
                    df,
                    x='timestamp',
                    y='predicted_value',
                    title=title,
                    labels={'predicted_value': 'Predicted Value', 'timestamp': 'Time'}
                )
            elif chart_type == "area":
                fig = px.area(
                    df,
                    x='timestamp',
                    y='predicted_value',
                    title=title,
                    labels={'predicted_value': 'Predicted Value', 'timestamp': 'Time'}
                )
            else:
                # Default to line chart
                fig = px.line(
                    df,
                    x='timestamp',
                    y='predicted_value',
                    title=title,
                    labels={'predicted_value': 'Predicted Value', 'timestamp': 'Time'}
                )

            # Update layout
            fig.update_layout(
                width=width,
                height=height,
                xaxis_title="Time",
                yaxis_title="Predicted Value",
                showlegend=True
            )

            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("No prediction data to display")

    except Exception as e:
        st.error(f"❌ Error rendering prediction chart: {str(e)}")
        st.info("Please check that the prediction data format is correct")


def render_forecast_comparison_chart(
    historical_data: List[Dict[str, Any]],
    forecast_data: List[Dict[str, Any]],
    title: str = "Historical vs Forecast Comparison",
    width: Optional[int] = None,
    height: Optional[int] = 400
) -> None:
    """Render comparison chart between historical and forecast data.

    Args:
        historical_data: Historical data points
        forecast_data: Forecast data points
        title: Chart title
        width: Chart width
        height: Chart height
    """
    if not PLOTLY_AVAILABLE:
        st.error("❌ Plotly is required for chart components")
        return

    try:
        st.markdown(f"### {title}")

        # Convert to DataFrames
        if historical_data:
            hist_df = pd.DataFrame(historical_data)
            if 'timestamp' in hist_df.columns:
                hist_df['timestamp'] = pd.to_datetime(hist_df['timestamp'])

        if forecast_data:
            forecast_df = pd.DataFrame(forecast_data)
            if 'timestamp' in forecast_df.columns:
                forecast_df['timestamp'] = pd.to_datetime(forecast_df['timestamp'])

        # Create subplots
        fig = make_subplots(specs=[[{"secondary_y": False}]])

        # Add historical data
        if historical_data and not hist_df.empty:
            fig.add_trace(
                go.Scatter(
                    x=hist_df['timestamp'],
                    y=hist_df.get('actual_value', hist_df.get('value', [])),
                    name='Historical',
                    line=dict(color='blue')
                )
            )

        # Add forecast data
        if forecast_data and not forecast_df.empty:
            fig.add_trace(
                go.Scatter(
                    x=forecast_df['timestamp'],
                    y=forecast_df.get('predicted_value', forecast_df.get('value', [])),
                    name='Forecast',
                    line=dict(color='red', dash='dash')
                )
            )

        # Update layout
        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title="Value",
            width=width,
            height=height
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error rendering forecast comparison chart: {str(e)}")


def render_prediction_confidence_chart(
    predictions: Dict[str, Any],
    confidence_intervals: Optional[Dict[str, Any]] = None,
    title: str = "Prediction with Confidence Intervals",
    width: Optional[int] = None,
    height: Optional[int] = 400
) -> None:
    """Render prediction chart with confidence intervals.

    Args:
        predictions: Prediction data
        confidence_intervals: Confidence interval data
        title: Chart title
        width: Chart width
        height: Chart height
    """
    if not PLOTLY_AVAILABLE:
        st.error("❌ Plotly is required for chart components")
        return

    try:
        st.markdown(f"### {title}")

        if not predictions or 'data' not in predictions:
            st.info("No prediction data available")
            return

        data = predictions['data']
        df = pd.DataFrame(data)

        if 'timestamp' not in df.columns or 'predicted_value' not in df.columns:
            st.error("❌ Prediction data missing required columns")
            return

        df['timestamp'] = pd.to_datetime(df['timestamp'])

        fig = go.Figure()

        # Add prediction line
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['predicted_value'],
            mode='lines',
            name='Prediction',
            line=dict(color='blue', width=2)
        ))

        # Add confidence intervals if available
        if confidence_intervals and 'upper' in df.columns and 'lower' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['upper'],
                mode='lines',
                name='Upper Confidence',
                line=dict(color='lightblue', width=1, dash='dot')
            ))

            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['lower'],
                mode='lines',
                name='Lower Confidence',
                line=dict(color='lightblue', width=1, dash='dot'),
                fill='tonexty',
                fillcolor='rgba(173, 216, 230, 0.3)'
            ))

        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title="Predicted Value",
            width=width,
            height=height
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error rendering confidence chart: {str(e)}")


def render_model_performance_chart(
    performance_data: Dict[str, Any],
    title: str = "Model Performance Metrics",
    width: Optional[int] = None,
    height: Optional[int] = 400
) -> None:
    """Render model performance metrics chart.

    Args:
        performance_data: Model performance metrics
        title: Chart title
        width: Chart width
        height: Chart height
    """
    if not PLOTLY_AVAILABLE:
        st.error("❌ Plotly is required for chart components")
        return

    try:
        st.markdown(f"### {title}")

        if not performance_data:
            st.info("No performance data available")
            return

        # Extract metrics
        metrics = []
        values = []

        for key, value in performance_data.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                metrics.append(key.replace('_', ' ').title())
                values.append(value)

        if not metrics:
            st.info("No numerical performance metrics found")
            return

        # Create bar chart
        fig = px.bar(
            x=metrics,
            y=values,
            title=title,
            labels={'x': 'Metric', 'y': 'Value'}
        )

        fig.update_layout(
            width=width,
            height=height,
            xaxis_title="Performance Metric",
            yaxis_title="Value"
        )

        st.plotly_chart(fig, use_container_width=True)

        # Display metrics as a table as well
        metrics_df = pd.DataFrame({
            'Metric': metrics,
            'Value': values
        })
        st.dataframe(metrics_df, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error rendering performance chart: {str(e)}")
