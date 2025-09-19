"""Distribution Charts Components.

This module provides chart components for displaying data distributions,
histograms, box plots, and statistical visualizations.
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots

try:
    import plotly.express as px
    import plotly.figure_factory as ff
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    st.warning("⚠️ Plotly not available. Distribution chart components will be limited.")


def render_distribution_chart(
    distribution_data: Dict[str, Any],
    chart_type: str = "histogram",
    title: str = "Data Distribution",
    width: Optional[int] = None,
    height: Optional[int] = 400
) -> None:
    """Render data distribution chart.

    Args:
        distribution_data: Distribution data to visualize
        chart_type: Type of distribution chart ('histogram', 'box', 'violin', 'kde')
        title: Chart title
        width: Chart width
        height: Chart height
    """
    if not PLOTLY_AVAILABLE:
        st.error("❌ Plotly is required for distribution chart components")
        return

    try:
        st.markdown(f"### {title}")

        if not distribution_data or 'data' not in distribution_data:
            st.info("No distribution data available")
            return

        data = distribution_data['data']

        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)

            # Find numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

            if not numeric_cols:
                st.info("No numeric data found for distribution analysis")
                return

            # Use first numeric column for single distribution
            value_col = numeric_cols[0]

            # Create the appropriate chart type
            if chart_type == "histogram":
                fig = px.histogram(
                    df,
                    x=value_col,
                    title=title,
                    labels={value_col: value_col.replace('_', ' ').title()},
                    nbins=30
                )
            elif chart_type == "box":
                fig = px.box(
                    df,
                    y=value_col,
                    title=title,
                    labels={value_col: value_col.replace('_', ' ').title()}
                )
            elif chart_type == "violin":
                fig = px.violin(
                    df,
                    y=value_col,
                    title=title,
                    labels={value_col: value_col.replace('_', ' ').title()},
                    box=True,
                    points="all"
                )
            elif chart_type == "kde":
                # Create KDE plot approximation using histogram
                fig = ff.create_distplot(
                    [df[value_col].dropna()],
                    [value_col.replace('_', ' ').title()],
                    show_hist=True,
                    show_rug=False
                )
                fig.update_layout(title=title)
            else:
                # Default to histogram
                fig = px.histogram(
                    df,
                    x=value_col,
                    title=title,
                    labels={value_col: value_col.replace('_', ' ').title()},
                    nbins=30
                )

            fig.update_layout(
                width=width,
                height=height,
                xaxis_title=value_col.replace('_', ' ').title(),
                yaxis_title="Frequency" if chart_type == "histogram" else "Value"
            )

            st.plotly_chart(fig, use_container_width=True)

            # Display distribution statistics
            render_distribution_stats(df[value_col])

        else:
            st.info("No distribution data to display")

    except Exception as e:
        st.error(f"❌ Error rendering distribution chart: {str(e)}")


def render_distribution_stats(series: pd.Series) -> None:
    """Render distribution statistics."""
    try:
        if series.empty:
            return

        values = series.dropna()

        if values.empty:
            return

        st.markdown("#### 📊 Distribution Statistics")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            mean_val = values.mean()
            st.metric("Mean", ".2f", mean_val)

        with col2:
            median_val = values.median()
            st.metric("Median", ".2f", median_val)

        with col3:
            std_val = values.std()
            st.metric("Std Dev", ".2f", std_val)

        with col4:
            skew_val = values.skew()
            st.metric("Skewness", ".2f", skew_val)

        # Additional statistics
        col5, col6, col7, col8 = st.columns(4)

        with col5:
            min_val = values.min()
            st.metric("Minimum", ".2f", min_val)

        with col6:
            max_val = values.max()
            st.metric("Maximum", ".2f", max_val)

        with col7:
            q25 = values.quantile(0.25)
            st.metric("25th Percentile", ".2f", q25)

        with col8:
            q75 = values.quantile(0.75)
            st.metric("75th Percentile", ".2f", q75)

        # Distribution shape analysis
        st.markdown("#### 📈 Distribution Analysis")

        # Check for normality using simple heuristics
        if abs(skew_val) < 0.5 and abs(values.kurtosis()) < 0.5:
            st.success("✅ Approximately normal distribution")
        elif skew_val > 1:
            st.warning("⚠️ Right-skewed distribution (long right tail)")
        elif skew_val < -1:
            st.warning("⚠️ Left-skewed distribution (long left tail)")
        else:
            st.info("ℹ️ Moderately skewed distribution")

        # Range analysis
        data_range = max_val - min_val
        st.info(f"**Data Range:** {data_range:.2f} (from {min_val:.2f} to {max_val:.2f})")

    except Exception as e:
        st.error(f"❌ Error rendering distribution statistics: {str(e)}")


def render_multi_distribution_chart(
    multi_data: Dict[str, Any],
    title: str = "Multiple Distributions Comparison",
    width: Optional[int] = None,
    height: Optional[int] = 400
) -> None:
    """Render comparison of multiple distributions.

    Args:
        multi_data: Multiple distribution data
        title: Chart title
        width: Chart width
        height: Chart height
    """
    if not PLOTLY_AVAILABLE:
        st.error("❌ Plotly is required for chart components")
        return

    try:
        st.markdown(f"### {title}")

        if not multi_data or 'distributions' not in multi_data:
            st.info("No multi-distribution data available")
            return

        distributions = multi_data['distributions']

        if not distributions:
            st.info("No distributions to compare")
            return

        # Create subplots for multiple distributions
        num_distributions = len(distributions)
        rows = (num_distributions + 2) // 3  # 3 columns max
        cols = min(3, num_distributions)

        fig = make_subplots(
            rows=rows,
            cols=cols,
            subplot_titles=[dist.get('name', f'Distribution {i+1}') for i, dist in enumerate(distributions)]
        )

        for i, dist in enumerate(distributions):
            row = (i // 3) + 1
            col = (i % 3) + 1

            if 'data' in dist and isinstance(dist['data'], list):
                values = pd.Series(dist['data'])

                # Create histogram for this distribution
                hist_data = np.histogram(values.dropna(), bins=20)
                fig.add_trace(
                    go.Bar(
                        x=hist_data[1][:-1],
                        y=hist_data[0],
                        name=dist.get('name', f'Distribution {i+1}'),
                        showlegend=False
                    ),
                    row=row,
                    col=col
                )

        fig.update_layout(
            title=title,
            width=width,
            height=height,
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

        # Display comparative statistics
        render_comparative_stats(distributions)

    except Exception as e:
        st.error(f"❌ Error rendering multi-distribution chart: {str(e)}")


def render_comparative_stats(distributions: List[Dict[str, Any]]) -> None:
    """Render comparative statistics for multiple distributions."""
    try:
        if not distributions:
            return

        st.markdown("#### 📊 Comparative Statistics")

        # Create comparison table
        comparison_data = []

        for dist in distributions:
            if 'data' in dist and isinstance(dist['data'], list):
                values = pd.Series(dist['data'])
                name = dist.get('name', 'Unnamed')

                stats = {
                    'Distribution': name,
                    'Count': len(values),
                    'Mean': ".2f",
                    'Std Dev': ".2f",
                    'Min': ".2f",
                    'Max': ".2f"
                }
                comparison_data.append(stats)

        if comparison_data:
            comparison_df = pd.DataFrame(comparison_data)
            st.dataframe(comparison_df, use_container_width=True)

            # Add insights
            means = [stats['Mean'] for stats in comparison_data]
            if len(means) > 1:
                max_mean_idx = means.index(max(means))
                min_mean_idx = means.index(min(means))

                if max_mean_idx != min_mean_idx:
                    st.info(f"📈 **{comparison_data[max_mean_idx]['Distribution']}** has the highest average value")
                    st.info(f"📉 **{comparison_data[min_mean_idx]['Distribution']}** has the lowest average value")

    except Exception as e:
        st.error(f"❌ Error rendering comparative statistics: {str(e)}")


def render_probability_distribution_chart(
    prob_data: Dict[str, Any],
    title: str = "Probability Distribution",
    width: Optional[int] = None,
    height: Optional[int] = 400
) -> None:
    """Render probability distribution chart.

    Args:
        prob_data: Probability distribution data
        title: Chart title
        width: Chart width
        height: Chart height
    """
    if not PLOTLY_AVAILABLE:
        st.error("❌ Plotly is required for chart components")
        return

    try:
        st.markdown(f"### {title}")

        if not prob_data or 'distribution' not in prob_data:
            st.info("No probability distribution data available")
            return

        distribution = prob_data['distribution']

        if isinstance(distribution, dict) and 'x' in distribution and 'y' in distribution:
            x_values = distribution['x']
            y_values = distribution['y']

            # Create probability distribution plot
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=x_values,
                y=y_values,
                mode='lines',
                name='Probability Density',
                fill='tozeroy',
                line=dict(color='blue')
            ))

            # Add mean line if available
            if 'mean' in prob_data:
                mean_val = prob_data['mean']
                fig.add_vline(
                    x=mean_val,
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Mean: {mean_val:.2f}"
                )

            # Add standard deviation lines if available
            if 'std' in prob_data and 'mean' in prob_data:
                mean_val = prob_data['mean']
                std_val = prob_data['std']

                fig.add_vline(
                    x=mean_val - std_val,
                    line_dash="dot",
                    line_color="orange",
                    annotation_text="-1σ"
                )
                fig.add_vline(
                    x=mean_val + std_val,
                    line_dash="dot",
                    line_color="orange",
                    annotation_text="+1σ"
                )

            fig.update_layout(
                title=title,
                width=width,
                height=height,
                xaxis_title="Value",
                yaxis_title="Probability Density"
            )

            st.plotly_chart(fig, use_container_width=True)

            # Display distribution parameters
            render_distribution_parameters(prob_data)

        else:
            st.info("No probability distribution data to display")

    except Exception as e:
        st.error(f"❌ Error rendering probability distribution chart: {str(e)}")


def render_distribution_parameters(prob_data: Dict[str, Any]) -> None:
    """Render distribution parameters."""
    try:
        if not prob_data:
            return

        st.markdown("#### 📊 Distribution Parameters")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if 'mean' in prob_data:
                st.metric("Mean", ".2f", prob_data['mean'])

        with col2:
            if 'median' in prob_data:
                st.metric("Median", ".2f", prob_data['median'])

        with col3:
            if 'std' in prob_data:
                st.metric("Std Deviation", ".2f", prob_data['std'])

        with col4:
            if 'variance' in prob_data:
                st.metric("Variance", ".2f", prob_data['variance'])

        # Additional parameters
        if 'skewness' in prob_data or 'kurtosis' in prob_data:
            col5, col6 = st.columns(2)

            with col5:
                if 'skewness' in prob_data:
                    st.metric("Skewness", ".2f", prob_data['skewness'])

            with col6:
                if 'kurtosis' in prob_data:
                    st.metric("Kurtosis", ".2f", prob_data['kurtosis'])

        # Distribution type
        if 'distribution_type' in prob_data:
            dist_type = prob_data['distribution_type']
            st.info(f"**Distribution Type:** {dist_type}")

            # Add interpretation based on distribution type
            if dist_type.lower() == 'normal':
                st.success("✅ Normal distribution - data follows expected pattern")
            elif 'skew' in dist_type.lower():
                st.warning("⚠️ Skewed distribution - data shows asymmetry")
            elif 'heavy' in dist_type.lower():
                st.warning("⚠️ Heavy-tailed distribution - extreme values are common")

    except Exception as e:
        st.error(f"❌ Error rendering distribution parameters: {str(e)}")


def render_cumulative_distribution_chart(
    cdf_data: Dict[str, Any],
    title: str = "Cumulative Distribution Function",
    width: Optional[int] = None,
    height: Optional[int] = 400
) -> None:
    """Render cumulative distribution function chart.

    Args:
        cdf_data: CDF data
        title: Chart title
        width: Chart width
        height: Chart height
    """
    if not PLOTLY_AVAILABLE:
        st.error("❌ Plotly is required for chart components")
        return

    try:
        st.markdown(f"### {title}")

        if not cdf_data or 'data' not in cdf_data:
            st.info("No CDF data available")
            return

        data = cdf_data['data']

        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)

            # Find value and cumulative probability columns
            value_col = None
            prob_col = None

            for col in df.columns:
                if 'value' in col.lower():
                    value_col = col
                elif 'prob' in col.lower() or 'cumulative' in col.lower() or 'cdf' in col.lower():
                    prob_col = col

            if not value_col or not prob_col:
                # Try to use first two numeric columns
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                if len(numeric_cols) >= 2:
                    value_col = numeric_cols[0]
                    prob_col = numeric_cols[1]

            if not value_col or not prob_col:
                st.info("CDF data missing required value and probability columns")
                return

            # Sort by value for proper CDF
            df_sorted = df.sort_values(value_col)

            # Create CDF plot
            fig = px.line(
                df_sorted,
                x=value_col,
                y=prob_col,
                title=title,
                labels={
                    value_col: value_col.replace('_', ' ').title(),
                    prob_col: 'Cumulative Probability'
                }
            )

            # Add reference lines
            fig.add_hline(y=0.5, line_dash="dash", line_color="red", annotation_text="Median (50%)")
            fig.add_hline(y=0.95, line_dash="dot", line_color="orange", annotation_text="95th Percentile")

            fig.update_layout(
                width=width,
                height=height,
                xaxis_title=value_col.replace('_', ' ').title(),
                yaxis_title="Cumulative Probability",
                yaxis=dict(range=[0, 1])
            )

            st.plotly_chart(fig, use_container_width=True)

            # Display CDF insights
            render_cdf_insights(df_sorted, value_col, prob_col)

        else:
            st.info("No CDF data to display")

    except Exception as e:
        st.error(f"❌ Error rendering cumulative distribution chart: {str(e)}")


def render_cdf_insights(df: pd.DataFrame, value_col: str, prob_col: str) -> None:
    """Render CDF insights and percentiles."""
    try:
        if df.empty or value_col not in df.columns or prob_col not in df.columns:
            return

        st.markdown("#### 📊 CDF Insights")

        # Calculate key percentiles
        percentiles = [0.25, 0.5, 0.75, 0.9, 0.95, 0.99]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Key Percentiles:**")
            for p in percentiles[:3]:
                value = df[value_col].quantile(p)
                st.write(".1f")

        with col2:
            st.markdown("**More Percentiles:**")
            for p in percentiles[3:]:
                value = df[value_col].quantile(p)
                st.write(".1f")

        with col3:
            # Distribution spread
            q25 = df[value_col].quantile(0.25)
            q75 = df[value_col].quantile(0.75)
            iqr = q75 - q25

            st.metric("Interquartile Range", ".2f", iqr)
            st.metric("Median", ".2f", df[value_col].quantile(0.5))

            # Check for outliers
            q95 = df[value_col].quantile(0.95)
            max_val = df[value_col].max()
            outlier_ratio = (max_val - q95) / iqr if iqr > 0 else 0

            if outlier_ratio > 3:
                st.warning("⚠️ Potential outliers detected (extreme values)")
            else:
                st.success("✅ No significant outliers detected")

    except Exception as e:
        st.error(f"❌ Error rendering CDF insights: {str(e)}")
