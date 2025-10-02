"""AI-Powered Insights Page.

This module provides the main AI insights page that integrates
core analysis, ML models, and visualizations.
"""

import streamlit as st

# Import AI insights modules
from modules.ai_insights.core import (
    generate_sample_data,
    display_basic_statistics,
    detect_basic_anomalies,
    display_anomaly_results,
    generate_time_series_data,
    analyze_basic_trends,
    display_trend_analysis,
)

from modules.ai_insights.models import (
    discover_patterns,
    generate_intelligent_recommendations,
    train_anomaly_detection_model,
    detect_anomalies,
    train_predictive_model,
    generate_predictions,
    generate_optimization_plan,
)

from modules.ai_insights.visualizations import (
    display_patterns,
    display_recommendations,
    display_anomalies,
    display_predictions,
    display_optimization_plan,
    render_pattern_visualization,
    render_anomaly_visualization,
    render_predictive_visualization,
    render_recommendation_impact_analysis,
)


def render_ai_insights_page():
    """Render the main AI insights page."""
    st.markdown("## 🧠 AI-Powered Insights")
    st.markdown(
        "Leverage machine learning and advanced analytics to gain deep insights "
        "into your simulation performance, predict issues, and receive intelligent recommendations."
    )

    # Initialize AI insights state
    initialize_ai_insights_state()

    # Main tabs for different AI capabilities
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Pattern Recognition",
        "💡 Intelligent Recommendations", 
        "🚨 Anomaly Detection",
        "🔮 Predictive Optimization"
    ])

    with tab1:
        render_pattern_recognition()

    with tab2:
        render_intelligent_recommendations()

    with tab3:
        render_ai_anomaly_detection()

    with tab4:
        render_predictive_optimization()


def initialize_ai_insights_state():
    """Initialize session state for AI insights."""
    if "ai_insights_data" not in st.session_state:
        st.session_state.ai_insights_data = generate_sample_data()
    
    if "ai_models_trained" not in st.session_state:
        st.session_state.ai_models_trained = {}


def render_pattern_recognition():
    """Render pattern recognition section."""
    st.markdown("### 🔍 Pattern Recognition")
    st.markdown("Discover hidden patterns and correlations in your simulation data.")

    # Data selection
    data_source = st.selectbox(
        "Data Source",
        ["Simulation Metrics", "Performance Logs", "Custom Dataset"],
        key="pattern_data_source"
    )

    if st.button("🔍 Discover Patterns", key="discover_patterns"):
        with st.spinner("Analyzing data patterns..."):
            patterns = discover_patterns(st.session_state.ai_insights_data)
            
            if patterns:
                display_patterns(patterns)
                render_pattern_visualization(patterns)
            else:
                st.info("No significant patterns detected. Try with more data or different parameters.")


def render_intelligent_recommendations():
    """Render intelligent recommendations section."""
    st.markdown("### 💡 Intelligent Recommendations")
    st.markdown("Get AI-powered recommendations to optimize your simulation performance.")

    # Category selection
    category = st.selectbox(
        "Focus Area",
        ["performance", "reliability", "cost", "scalability"],
        format_func=lambda x: x.title(),
        key="recommendation_category"
    )

    if st.button("🧠 Generate Recommendations", key="generate_recommendations"):
        with st.spinner("Analyzing and generating recommendations..."):
            recommendations = generate_intelligent_recommendations(category)
            
            if recommendations:
                display_recommendations(recommendations)
                render_recommendation_impact_analysis(recommendations)
            else:
                st.info("Unable to generate recommendations. Please check your data.")


def render_ai_anomaly_detection():
    """Render AI-powered anomaly detection."""
    st.markdown("### 🚨 AI Anomaly Detection")
    st.markdown("Use machine learning to automatically detect anomalies in your simulation data.")

    col1, col2 = st.columns(2)
    
    with col1:
        target_metric = st.selectbox(
            "Target Metric",
            ["cpu_usage", "memory_usage", "response_time", "error_rate"],
            format_func=lambda x: x.replace('_', ' ').title(),
            key="anomaly_target"
        )
    
    with col2:
        sensitivity = st.slider(
            "Detection Sensitivity",
            min_value=0.1,
            max_value=1.0,
            value=0.3,
            step=0.1,
            key="anomaly_sensitivity"
        )

    if st.button("🔍 Detect Anomalies", key="detect_anomalies"):
        with st.spinner("Training anomaly detection model..."):
            # Train model (mock for now)
            model_result = train_anomaly_detection_model(
                st.session_state.ai_insights_data, 
                contamination=sensitivity
            )
            
            if model_result.get("available", False):
                st.success("✅ Anomaly detection model trained successfully!")
                
                # Detect anomalies
                anomalies = detect_anomalies(target_metric)
                
                if anomalies:
                    display_anomalies(anomalies)
                    render_anomaly_visualization(anomalies)
                else:
                    st.success("✅ No anomalies detected in the analyzed data.")
            else:
                st.warning(f"⚠️ {model_result.get('message', 'Model training failed')}")
                
                # Fallback to basic analysis
                st.markdown("##### Basic Statistical Analysis")
                data = st.session_state.ai_insights_data
                results = detect_basic_anomalies(data, threshold=3.0)
                display_anomaly_results(results)


def render_predictive_optimization():
    """Render predictive optimization section."""
    st.markdown("### 🔮 Predictive Optimization")
    st.markdown("Predict future performance and get optimization recommendations.")

    # Category selection
    category = st.selectbox(
        "Prediction Category",
        ["performance", "resource_usage", "scaling_needs"],
        format_func=lambda x: x.replace('_', ' ').title(),
        key="prediction_category"
    )

    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔮 Generate Predictions", key="generate_predictions"):
            with st.spinner("Training predictive model..."):
                # Train model
                trained = train_predictive_model(category)
                
                if trained:
                    st.success("✅ Predictive model trained successfully!")
                    
                    # Generate predictions
                    predictions = generate_predictions(category)
                    display_predictions(category, predictions)
                    render_predictive_visualization(category, predictions)
                    
                    # Generate optimization plan
                    plan = generate_optimization_plan(category)
                    display_optimization_plan(plan)
                    
                else:
                    st.warning("⚠️ Model training failed. Using basic analysis.")
                    
                    # Fallback to basic trend analysis
                    st.markdown("##### Basic Trend Analysis")
                    data = generate_time_series_data()
                    analysis = analyze_basic_trends(data)
                    display_trend_analysis(analysis)

    with col2:
        if st.button("📊 Basic Statistics", key="show_basic_stats"):
            data = st.session_state.ai_insights_data
            display_basic_statistics(data)


# Limited functionality versions for when ML libraries are not available
def render_pattern_recognition_limited():
    """Render pattern recognition with limited functionality."""
    st.markdown("### 🔍 Pattern Recognition (Limited)")
    st.markdown("*Note: Advanced ML libraries not available. Using basic analysis.*")
    
    if st.button("🔍 Analyze Basic Patterns", key="basic_patterns"):
        data = generate_time_series_data()
        analysis = analyze_basic_trends(data)
        display_trend_analysis(analysis)


def render_anomaly_detection_limited():
    """Render anomaly detection with limited functionality."""
    st.markdown("### 🚨 Anomaly Detection (Limited)")
    st.markdown("*Note: Advanced ML libraries not available. Using statistical methods.*")
    
    data = st.session_state.ai_insights_data
    threshold = st.slider("Anomaly Threshold (σ)", 2.0, 5.0, 3.0, key="basic_threshold")
    
    if st.button("🔍 Detect Anomalies", key="basic_anomalies"):
        results = detect_basic_anomalies(data, threshold=threshold)
        display_anomaly_results(results)


def render_predictive_optimization_limited():
    """Render predictive optimization with limited functionality."""
    st.markdown("### 🔮 Predictive Optimization (Limited)")
    st.markdown("*Note: Advanced ML libraries not available. Using trend analysis.*")
    
    if st.button("📈 Analyze Trends", key="basic_trends"):
        data = generate_time_series_data()
        analysis = analyze_basic_trends(data)
        display_trend_analysis(analysis)
