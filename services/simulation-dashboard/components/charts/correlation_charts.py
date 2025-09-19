"""Correlation Charts Components.

This module provides chart components for displaying correlation analysis,
relationship visualization, and dependency mapping.
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import plotly.graph_objects as go
from plotly.subplots import make_subplots

try:
    import plotly.express as px
    import plotly.figure_factory as ff
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    st.warning("⚠️ Plotly not available. Correlation chart components will be limited.")


def render_correlation_chart(
    correlation_data: Dict[str, Any],
    title: str = "Correlation Analysis",
    width: Optional[int] = None,
    height: Optional[int] = 500
) -> None:
    """Render correlation matrix heatmap.

    Args:
        correlation_data: Correlation matrix data
        title: Chart title
        width: Chart width
        height: Chart height
    """
    if not PLOTLY_AVAILABLE:
        st.error("❌ Plotly is required for correlation chart components")
        return

    try:
        st.markdown(f"### {title}")

        if not correlation_data or 'matrix' not in correlation_data:
            st.info("No correlation data available")
            return

        matrix = correlation_data['matrix']
        variables = correlation_data.get('variables', [])

        if isinstance(matrix, list) and len(matrix) > 0:
            # Convert to numpy array for processing
            corr_matrix = np.array(matrix)

            if len(variables) != len(corr_matrix):
                # Generate variable names if not provided
                variables = [f'Var_{i+1}' for i in range(len(corr_matrix))]

            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=corr_matrix,
                x=variables,
                y=variables,
                colorscale='RdBu',
                zmin=-1,
                zmax=1,
                text=np.round(corr_matrix, 2),
                texttemplate='%{text}',
                textfont={"size": 10},
                hoverongaps=False
            ))

            fig.update_layout(
                title=title,
                width=width,
                height=height,
                xaxis_title="Variables",
                yaxis_title="Variables"
            )

            st.plotly_chart(fig, use_container_width=True)

            # Display correlation insights
            render_correlation_insights(corr_matrix, variables)

        else:
            st.info("No correlation matrix to display")

    except Exception as e:
        st.error(f"❌ Error rendering correlation chart: {str(e)}")


def render_correlation_insights(corr_matrix: np.ndarray, variables: List[str]) -> None:
    """Render correlation analysis insights."""
    try:
        if corr_matrix is None or len(variables) == 0:
            return

        st.markdown("#### 📊 Correlation Insights")

        # Find strongest correlations
        strong_positive = []
        strong_negative = []

        for i in range(len(variables)):
            for j in range(i+1, len(variables)):
                corr_value = corr_matrix[i, j]
                if abs(corr_value) > 0.7:  # Strong correlation threshold
                    if corr_value > 0:
                        strong_positive.append((variables[i], variables[j], corr_value))
                    else:
                        strong_negative.append((variables[i], variables[j], corr_value))

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Strong Positive Correlations:**")
            if strong_positive:
                for var1, var2, corr in strong_positive[:5]:  # Top 5
                    st.write(".3f")
            else:
                st.write("None found")

        with col2:
            st.markdown("**Strong Negative Correlations:**")
            if strong_negative:
                for var1, var2, corr in strong_negative[:5]:  # Top 5
                    st.write(".3f")
            else:
                st.write("None found")

    except Exception as e:
        st.error(f"❌ Error rendering correlation insights: {str(e)}")


def render_scatter_correlation_chart(
    scatter_data: Dict[str, Any],
    title: str = "Scatter Plot Correlation",
    width: Optional[int] = None,
    height: Optional[int] = 400
) -> None:
    """Render scatter plot showing correlation between two variables.

    Args:
        scatter_data: Scatter plot data with x and y variables
        title: Chart title
        width: Chart width
        height: Chart height
    """
    if not PLOTLY_AVAILABLE:
        st.error("❌ Plotly is required for chart components")
        return

    try:
        st.markdown(f"### {title}")

        if not scatter_data or 'data' not in scatter_data:
            st.info("No scatter data available")
            return

        data = scatter_data['data']

        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)

            # Find numeric columns for correlation
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

            if len(numeric_cols) < 2:
                st.info("Need at least 2 numeric columns for scatter correlation")
                return

            # Use first two numeric columns
            x_col = numeric_cols[0]
            y_col = numeric_cols[1]

            # Calculate correlation coefficient
            correlation = df[x_col].corr(df[y_col])

            # Create scatter plot
            fig = px.scatter(
                df,
                x=x_col,
                y=y_col,
                title=f"{title} (r = {correlation:.3f})",
                trendline="ols"  # Add trend line
            )

            fig.update_layout(
                width=width,
                height=height,
                xaxis_title=x_col.replace('_', ' ').title(),
                yaxis_title=y_col.replace('_', ' ').title()
            )

            st.plotly_chart(fig, use_container_width=True)

            # Display correlation strength
            render_correlation_strength(correlation)

        else:
            st.info("No scatter data to display")

    except Exception as e:
        st.error(f"❌ Error rendering scatter correlation chart: {str(e)}")


def render_correlation_strength(correlation: float) -> None:
    """Render correlation strength interpretation."""
    try:
        abs_corr = abs(correlation)

        if abs_corr >= 0.9:
            strength = "Very Strong"
            color = "🟢"
        elif abs_corr >= 0.7:
            strength = "Strong"
            color = "🟢"
        elif abs_corr >= 0.5:
            strength = "Moderate"
            color = "🟡"
        elif abs_corr >= 0.3:
            strength = "Weak"
            color = "🟡"
        else:
            strength = "Very Weak"
            color = "🔴"

        direction = "Positive" if correlation > 0 else "Negative" if correlation < 0 else "No"

        st.markdown(f"#### 📊 Correlation Strength: {color} {strength} {direction}")
        st.write(f"**Coefficient:** {correlation:.3f}")

        # Interpretation
        if abs_corr >= 0.7:
            st.success("✅ Strong correlation detected - variables are closely related")
        elif abs_corr >= 0.5:
            st.info("ℹ️ Moderate correlation - some relationship exists")
        else:
            st.warning("⚠️ Weak correlation - variables are largely independent")

    except Exception as e:
        st.error(f"❌ Error rendering correlation strength: {str(e)}")


def render_network_correlation_chart(
    network_data: Dict[str, Any],
    title: str = "Correlation Network",
    width: Optional[int] = None,
    height: Optional[int] = 500
) -> None:
    """Render network visualization of correlations.

    Args:
        network_data: Network data with nodes and edges
        title: Chart title
        width: Chart width
        height: Chart height
    """
    if not PLOTLY_AVAILABLE:
        st.error("❌ Plotly is required for chart components")
        return

    try:
        st.markdown(f"### {title}")

        if not network_data or 'nodes' not in network_data or 'edges' not in network_data:
            st.info("No network data available")
            return

        nodes = network_data['nodes']
        edges = network_data['edges']

        if not nodes or not edges:
            st.info("Network data is empty")
            return

        # Create network visualization using scatter plot with lines
        fig = go.Figure()

        # Add edges
        for edge in edges:
            source_node = next((n for n in nodes if n.get('id') == edge.get('source')), None)
            target_node = next((n for n in nodes if n.get('id') == edge.get('target')), None)

            if source_node and target_node:
                fig.add_trace(go.Scatter(
                    x=[source_node.get('x', 0), target_node.get('x', 0)],
                    y=[source_node.get('y', 0), target_node.get('y', 0)],
                    mode='lines',
                    line=dict(width=edge.get('weight', 1) * 2, color='gray'),
                    showlegend=False
                ))

        # Add nodes
        node_x = [n.get('x', 0) for n in nodes]
        node_y = [n.get('y', 0) for n in nodes]
        node_text = [n.get('label', n.get('id', '')) for n in nodes]
        node_size = [n.get('size', 10) for n in nodes]

        fig.add_trace(go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text',
            text=node_text,
            textposition="top center",
            marker=dict(
                size=node_size,
                color='blue',
                opacity=0.8
            ),
            showlegend=False
        ))

        fig.update_layout(
            title=title,
            width=width,
            height=height,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error rendering network correlation chart: {str(e)}")
