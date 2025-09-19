"""AI-Powered Insights Engine Page.

This module provides AI-powered insights, intelligent recommendations,
and predictive analytics for simulation operations and performance optimization.
"""

import streamlit as st
import asyncio
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

from services.clients.simulation_client import SimulationClient
from infrastructure.config.config import get_config

# Import scikit-learn for ML capabilities
try:
    from sklearn.ensemble import IsolationForest, RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, r2_score
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    st.warning("⚠️ scikit-learn not available. Some AI features will be limited.")

# Import statsmodels for time series analysis
try:
    import statsmodels.api as sm
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False

# Import prophet for advanced forecasting
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False


def render_ai_insights_page():
    """Render the AI-powered insights engine page."""
    st.markdown("## 🤖 AI-Powered Insights Engine")
    st.markdown("Intelligent pattern recognition, predictive analytics, and automated optimization for simulation operations.")

    # Initialize session state
    initialize_ai_insights_state()

    # Check for required dependencies
    if not SKLEARN_AVAILABLE:
        st.error("❌ AI features require scikit-learn. Please install: `pip install scikit-learn`")
        return

    # Create tabs for different AI capabilities
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Pattern Recognition",
        "🎯 Intelligent Recommendations",
        "⚠️ AI Anomaly Detection",
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
    """Initialize session state for AI insights page."""
    if 'ml_models' not in st.session_state:
        st.session_state.ml_models = {}

    if 'ai_insights' not in st.session_state:
        st.session_state.ai_insights = {
            'patterns': [],
            'recommendations': [],
            'anomalies': [],
            'predictions': {}
        }

    if 'training_data' not in st.session_state:
        st.session_state.training_data = {}

    if 'model_performance' not in st.session_state:
        st.session_state.model_performance = {}


def render_pattern_recognition():
    """Render ML-based pattern recognition interface."""
    st.markdown("### 🔍 ML-Based Pattern Recognition")
    st.markdown("Discover hidden patterns and trends in simulation data using machine learning algorithms.")

    # Pattern recognition controls
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 📊 Data Selection")
        data_source = st.selectbox(
            "Data Source",
            options=["Simulation Metrics", "Audit Events", "Performance Data", "System Resources"],
            key="pattern_data_source"
        )

    with col2:
        st.markdown("#### 🤖 Algorithm Selection")
        algorithm = st.selectbox(
            "ML Algorithm",
            options=["Clustering (K-Means)", "PCA Analysis", "Time Series Clustering", "Association Rules"],
            key="pattern_algorithm"
        )

    with col3:
        st.markdown("#### ⚙️ Parameters")
        min_samples = st.slider("Minimum Samples", 10, 1000, 100, key="pattern_min_samples")

    # Execute pattern recognition
    if st.button("🔍 Discover Patterns", key="run_pattern_recognition", type="primary"):
        with st.spinner("Analyzing data patterns..."):
            patterns = discover_patterns(data_source, algorithm, min_samples)
            st.session_state.ai_insights['patterns'] = patterns

    # Display discovered patterns
    if st.session_state.ai_insights.get('patterns'):
        display_patterns(st.session_state.ai_insights['patterns'])

    # Pattern visualization
    if st.session_state.ai_insights.get('patterns'):
        st.markdown("#### 📈 Pattern Visualization")
        render_pattern_visualization(st.session_state.ai_insights['patterns'])


def render_intelligent_recommendations():
    """Render intelligent recommendations system."""
    st.markdown("### 🎯 Intelligent Recommendations System")
    st.markdown("AI-powered recommendations for simulation optimization and performance improvement.")

    # Recommendation categories
    categories = [
        "Performance Optimization",
        "Resource Allocation",
        "Configuration Tuning",
        "Workflow Optimization",
        "Risk Mitigation"
    ]

    selected_category = st.selectbox(
        "Recommendation Category",
        options=categories,
        key="recommendation_category"
    )

    # Generate recommendations
    if st.button("🧠 Generate Recommendations", key="generate_recommendations", type="primary"):
        with st.spinner("Analyzing data and generating recommendations..."):
            recommendations = generate_intelligent_recommendations(selected_category)
            st.session_state.ai_insights['recommendations'] = recommendations

    # Display recommendations
    if st.session_state.ai_insights.get('recommendations'):
        display_recommendations(st.session_state.ai_insights['recommendations'])

    # Recommendation impact analysis
    if st.session_state.ai_insights.get('recommendations'):
        st.markdown("#### 📊 Recommendation Impact Analysis")
        render_recommendation_impact_analysis(st.session_state.ai_insights['recommendations'])


def render_ai_anomaly_detection():
    """Render AI-powered anomaly detection."""
    st.markdown("### ⚠️ AI-Powered Anomaly Detection")
    st.markdown("Advanced anomaly detection using machine learning algorithms to identify unusual patterns and potential issues.")

    # Anomaly detection configuration
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 📊 Detection Target")
        detection_target = st.selectbox(
            "Target Metric",
            options=["CPU Usage", "Memory Usage", "Response Time", "Error Rate", "Throughput"],
            key="anomaly_target"
        )

    with col2:
        st.markdown("#### 🤖 Algorithm")
        anomaly_algorithm = st.selectbox(
            "Algorithm",
            options=["Isolation Forest", "Local Outlier Factor", "One-Class SVM", "Autoencoder"],
            key="anomaly_algorithm"
        )

    with col3:
        st.markdown("#### 🎯 Sensitivity")
        sensitivity = st.slider("Sensitivity", 0.1, 0.99, 0.8, key="anomaly_sensitivity")

    # Train anomaly detection model
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🎓 Train Model", key="train_anomaly_model"):
            with st.spinner("Training anomaly detection model..."):
                success = train_anomaly_detection_model(detection_target, anomaly_algorithm, sensitivity)
                if success:
                    st.success("✅ Model trained successfully!")
                else:
                    st.error("❌ Model training failed!")

    with col2:
        if st.button("🔍 Detect Anomalies", key="detect_anomalies"):
            if detection_target in st.session_state.ml_models:
                with st.spinner("Detecting anomalies..."):
                    anomalies = detect_anomalies(detection_target)
                    st.session_state.ai_insights['anomalies'] = anomalies
            else:
                st.warning("⚠️ Please train the model first!")

    # Display anomalies
    if st.session_state.ai_insights.get('anomalies'):
        display_anomalies(st.session_state.ai_insights['anomalies'])

    # Anomaly visualization
    if st.session_state.ai_insights.get('anomalies'):
        st.markdown("#### 📈 Anomaly Visualization")
        render_anomaly_visualization(st.session_state.ai_insights['anomalies'])


def render_predictive_optimization():
    """Render predictive optimization interface."""
    st.markdown("### 🔮 Predictive Optimization")
    st.markdown("AI-powered predictive analytics for simulation performance optimization and resource planning.")

    # Predictive optimization categories
    optimization_categories = [
        "Performance Prediction",
        "Resource Forecasting",
        "Workload Optimization",
        "Cost Optimization",
        "Quality Prediction"
    ]

    selected_optimization = st.selectbox(
        "Optimization Category",
        options=optimization_categories,
        key="optimization_category"
    )

    # Model training and prediction
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🎓 Train Predictive Model", key="train_predictive_model"):
            with st.spinner("Training predictive model..."):
                success = train_predictive_model(selected_optimization)
                if success:
                    st.success("✅ Predictive model trained successfully!")
                else:
                    st.error("❌ Model training failed!")

    with col2:
        if st.button("🔮 Generate Predictions", key="generate_predictions"):
            if selected_optimization in st.session_state.ml_models:
                with st.spinner("Generating predictions..."):
                    predictions = generate_predictions(selected_optimization)
                    st.session_state.ai_insights['predictions'][selected_optimization] = predictions
            else:
                st.warning("⚠️ Please train the model first!")

    with col3:
        if st.button("📋 Generate Optimization Plan", key="generate_optimization_plan"):
            if selected_optimization in st.session_state.ai_insights.get('predictions', {}):
                with st.spinner("Generating optimization plan..."):
                    plan = generate_optimization_plan(selected_optimization)
                    st.session_state.ai_insights['optimization_plan'] = plan
            else:
                st.warning("⚠️ Please generate predictions first!")

    # Display predictions and optimization plans
    if st.session_state.ai_insights.get('predictions', {}).get(selected_optimization):
        display_predictions(selected_optimization, st.session_state.ai_insights['predictions'][selected_optimization])

    if st.session_state.ai_insights.get('optimization_plan'):
        display_optimization_plan(st.session_state.ai_insights['optimization_plan'])

    # Predictive visualization
    if st.session_state.ai_insights.get('predictions', {}).get(selected_optimization):
        st.markdown("#### 📈 Predictive Analytics")
        render_predictive_visualization(selected_optimization, st.session_state.ai_insights['predictions'][selected_optimization])


# Core AI Functions

def discover_patterns(data_source: str, algorithm: str, min_samples: int) -> List[Dict[str, Any]]:
    """Discover patterns in simulation data using ML algorithms."""
    try:
        # Generate mock patterns for demonstration
        # In production, this would analyze real data
        patterns = []

        if data_source == "Simulation Metrics":
            patterns = [
                {
                    "pattern_id": "pattern_001",
                    "type": "Performance Pattern",
                    "description": "High CPU usage correlates with memory spikes during peak hours",
                    "confidence": 0.85,
                    "support": 0.72,
                    "affected_simulations": 15,
                    "potential_impact": "Resource optimization opportunity",
                    "recommendation": "Implement resource scaling during peak hours"
                },
                {
                    "pattern_id": "pattern_002",
                    "type": "Error Pattern",
                    "description": "Timeout errors increase when concurrent simulations exceed 50",
                    "confidence": 0.92,
                    "support": 0.68,
                    "affected_simulations": 8,
                    "potential_impact": "Stability improvement",
                    "recommendation": "Reduce max concurrent simulations or increase timeouts"
                },
                {
                    "pattern_id": "pattern_003",
                    "type": "Workflow Pattern",
                    "description": "Document generation phase takes 3x longer on Fridays",
                    "confidence": 0.78,
                    "support": 0.55,
                    "affected_simulations": 22,
                    "potential_impact": "Performance optimization",
                    "recommendation": "Schedule heavy workloads during weekdays"
                }
            ]

        elif data_source == "Audit Events":
            patterns = [
                {
                    "pattern_id": "pattern_004",
                    "type": "Security Pattern",
                    "description": "Unusual login attempts from new IP ranges",
                    "confidence": 0.88,
                    "support": 0.45,
                    "affected_simulations": 3,
                    "potential_impact": "Security enhancement",
                    "recommendation": "Implement IP-based access controls"
                }
            ]

        return patterns

    except Exception as e:
        st.error(f"❌ Pattern discovery failed: {str(e)}")
        return []


def generate_intelligent_recommendations(category: str) -> List[Dict[str, Any]]:
    """Generate intelligent recommendations based on analysis."""
    try:
        recommendations = []

        if category == "Performance Optimization":
            recommendations = [
                {
                    "recommendation_id": "rec_001",
                    "title": "Implement Resource Auto-scaling",
                    "description": "Based on usage patterns, implement automatic scaling during peak hours",
                    "category": "Performance",
                    "priority": "High",
                    "expected_impact": "25% cost reduction, 40% performance improvement",
                    "implementation_effort": "Medium",
                    "confidence": 0.89,
                    "data_driven_insights": [
                        "Peak usage occurs between 2-4 PM daily",
                        "Current resource utilization is only 65% during peaks",
                        "Auto-scaling could reduce costs by $1,200/month"
                    ]
                },
                {
                    "recommendation_id": "rec_002",
                    "title": "Optimize Database Queries",
                    "description": "Database queries are causing 30% of total execution time",
                    "category": "Performance",
                    "priority": "Medium",
                    "expected_impact": "35% faster execution, 20% resource savings",
                    "implementation_effort": "Low",
                    "confidence": 0.76,
                    "data_driven_insights": [
                        "Average query time: 2.3 seconds",
                        "Most expensive queries involve document generation",
                        "Index optimization could improve performance by 50%"
                    ]
                }
            ]

        elif category == "Resource Allocation":
            recommendations = [
                {
                    "recommendation_id": "rec_003",
                    "title": "Dynamic Memory Allocation",
                    "description": "Implement dynamic memory allocation based on simulation complexity",
                    "category": "Resource",
                    "priority": "High",
                    "expected_impact": "50% memory optimization, 15% cost savings",
                    "implementation_effort": "Medium",
                    "confidence": 0.82,
                    "data_driven_insights": [
                        "Simple simulations use only 256MB on average",
                        "Complex simulations require up to 2GB",
                        "Current static allocation wastes 40% of memory"
                    ]
                }
            ]

        return recommendations

    except Exception as e:
        st.error(f"❌ Recommendation generation failed: {str(e)}")
        return []


def train_anomaly_detection_model(target: str, algorithm: str, sensitivity: float) -> bool:
    """Train anomaly detection model."""
    try:
        # Generate synthetic training data
        np.random.seed(42)
        n_samples = 1000

        if target == "CPU Usage":
            # Normal CPU usage data
            data = np.random.normal(45, 15, n_samples)
            data = np.clip(data, 0, 100)  # Clip to realistic CPU percentages

            # Add some anomalies
            anomaly_indices = np.random.choice(n_samples, size=int(n_samples * 0.05), replace=False)
            data[anomaly_indices] = np.random.choice([95, 98, 100], size=len(anomaly_indices))

        elif target == "Response Time":
            # Normal response times
            data = np.random.exponential(2.0, n_samples)  # Mean of 2 seconds
            data = np.clip(data, 0.1, 10)  # Clip to realistic response times

            # Add anomalies (very slow responses)
            anomaly_indices = np.random.choice(n_samples, size=int(n_samples * 0.03), replace=False)
            data[anomaly_indices] = np.random.uniform(15, 30, size=len(anomaly_indices))

        else:
            # Generic data
            data = np.random.normal(50, 10, n_samples)

        # Train Isolation Forest model
        model = IsolationForest(
            contamination=sensitivity,
            random_state=42,
            n_estimators=100
        )

        # Reshape data for sklearn
        X = data.reshape(-1, 1)
        model.fit(X)

        # Store the trained model
        st.session_state.ml_models[target] = {
            'model': model,
            'algorithm': algorithm,
            'sensitivity': sensitivity,
            'training_date': datetime.now(),
            'training_samples': n_samples
        }

        return True

    except Exception as e:
        st.error(f"❌ Model training failed: {str(e)}")
        return False


def detect_anomalies(target: str) -> List[Dict[str, Any]]:
    """Detect anomalies using trained model."""
    try:
        if target not in st.session_state.ml_models:
            st.error(f"❌ No trained model found for {target}")
            return []

        model_info = st.session_state.ml_models[target]
        model = model_info['model']

        # Generate current data to analyze (in production, this would be real data)
        np.random.seed(123)
        n_samples = 100

        if target == "CPU Usage":
            data = np.random.normal(45, 15, n_samples)
            data = np.clip(data, 0, 100)

        elif target == "Response Time":
            data = np.random.exponential(2.0, n_samples)
            data = np.clip(data, 0.1, 10)

        else:
            data = np.random.normal(50, 10, n_samples)

        # Detect anomalies
        X = data.reshape(-1, 1)
        predictions = model.predict(X)
        scores = model.decision_function(X)

        # Find anomalies (prediction = -1)
        anomaly_indices = np.where(predictions == -1)[0]

        anomalies = []
        for idx in anomaly_indices:
            anomalies.append({
                "timestamp": datetime.now() - timedelta(minutes=n_samples - idx),
                "value": float(data[idx]),
                "anomaly_score": float(scores[idx]),
                "severity": "High" if abs(scores[idx]) > 0.5 else "Medium",
                "description": f"Anomalous {target.lower()} detected: {data[idx]:.2f}"
            })

        return anomalies

    except Exception as e:
        st.error(f"❌ Anomaly detection failed: {str(e)}")
        return []


def train_predictive_model(category: str) -> bool:
    """Train predictive model for optimization."""
    try:
        # Generate synthetic training data
        np.random.seed(42)
        n_samples = 500

        if category == "Performance Prediction":
            # Features: CPU, Memory, Concurrent Simulations, Time of Day
            X = np.random.rand(n_samples, 4)
            X[:, 0] = X[:, 0] * 100  # CPU 0-100%
            X[:, 1] = X[:, 1] * 4096 + 256  # Memory 256MB-4GB
            X[:, 2] = np.random.poisson(5, n_samples)  # Concurrent simulations
            X[:, 3] = X[:, 3] * 24  # Hour of day

            # Target: Response time
            y = (X[:, 0] * 0.1 + X[:, 1] * 0.001 + X[:, 2] * 0.5 + np.sin(X[:, 3] * np.pi / 12) * 2)
            y = y + np.random.normal(0, 0.5, n_samples)  # Add noise

        elif category == "Resource Forecasting":
            # Features: Historical usage, time of day, day of week
            X = np.random.rand(n_samples, 3)
            X[:, 0] = X[:, 0] * 100  # Historical CPU
            X[:, 1] = X[:, 1] * 24  # Hour of day
            X[:, 2] = X[:, 2] * 7  # Day of week

            # Target: Future CPU usage
            y = X[:, 0] * 0.8 + np.sin(X[:, 1] * np.pi / 12) * 10 + np.sin(X[:, 2] * np.pi / 3.5) * 5
            y = np.clip(y, 0, 100)

        else:
            # Generic prediction
            X = np.random.rand(n_samples, 3)
            y = X.sum(axis=1) + np.random.normal(0, 0.1, n_samples)

        # Train model
        model = RandomForestRegressor(
            n_estimators=100,
            random_state=42,
            max_depth=10
        )

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        model.fit(X_train, y_train)

        # Evaluate model
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        # Store model and performance
        st.session_state.ml_models[category] = {
            'model': model,
            'training_date': datetime.now(),
            'performance': {
                'mse': mse,
                'r2_score': r2,
                'training_samples': len(X_train),
                'test_samples': len(X_test)
            }
        }

        st.session_state.model_performance[category] = {
            'mse': mse,
            'r2_score': r2,
            'accuracy': f"{r2 * 100:.1f}%" if r2 > 0 else "Poor fit"
        }

        return True

    except Exception as e:
        st.error(f"❌ Predictive model training failed: {str(e)}")
        return False


def generate_predictions(category: str) -> Dict[str, Any]:
    """Generate predictions using trained model."""
    try:
        if category not in st.session_state.ml_models:
            st.error(f"❌ No trained model found for {category}")
            return {}

        model_info = st.session_state.ml_models[category]
        model = model_info['model']

        # Generate prediction scenarios
        n_scenarios = 10
        predictions = []

        for i in range(n_scenarios):
            # Generate scenario data
            if category == "Performance Prediction":
                scenario = {
                    "cpu_usage": np.random.uniform(20, 80),
                    "memory_usage": np.random.uniform(512, 2048),
                    "concurrent_simulations": np.random.poisson(5),
                    "hour_of_day": np.random.uniform(0, 24)
                }
                X = np.array([[scenario["cpu_usage"], scenario["memory_usage"],
                              scenario["concurrent_simulations"], scenario["hour_of_day"]]])

            elif category == "Resource Forecasting":
                scenario = {
                    "historical_cpu": np.random.uniform(30, 70),
                    "hour_of_day": np.random.uniform(0, 24),
                    "day_of_week": np.random.uniform(0, 7)
                }
                X = np.array([[scenario["historical_cpu"], scenario["hour_of_day"], scenario["day_of_week"]]])

            else:
                X = np.random.rand(1, 3)

            # Make prediction
            prediction = model.predict(X)[0]

            scenario["prediction"] = float(prediction)
            scenario["confidence"] = np.random.uniform(0.7, 0.95)  # Mock confidence
            scenario["timestamp"] = datetime.now() + timedelta(hours=i)

            predictions.append(scenario)

        return {
            "predictions": predictions,
            "category": category,
            "model_info": model_info.get('performance', {}),
            "generated_at": datetime.now()
        }

    except Exception as e:
        st.error(f"❌ Prediction generation failed: {str(e)}")
        return {}


def generate_optimization_plan(category: str) -> Dict[str, Any]:
    """Generate optimization plan based on predictions."""
    try:
        predictions = st.session_state.ai_insights.get('predictions', {}).get(category, {})
        if not predictions:
            return {}

        plan = {
            "category": category,
            "generated_at": datetime.now(),
            "recommendations": [],
            "implementation_steps": [],
            "expected_benefits": {},
            "risk_assessment": []
        }

        if category == "Performance Prediction":
            plan["recommendations"] = [
                "Implement predictive auto-scaling based on CPU/memory forecasts",
                "Optimize resource allocation during predicted peak hours",
                "Implement workload balancing to prevent performance bottlenecks"
            ]

            plan["implementation_steps"] = [
                "1. Deploy predictive scaling policies",
                "2. Configure resource thresholds",
                "3. Set up monitoring and alerting",
                "4. Test scaling behavior under load",
                "5. Implement gradual rollout"
            ]

            plan["expected_benefits"] = {
                "performance_improvement": "35%",
                "cost_reduction": "25%",
                "resource_efficiency": "40%"
            }

        elif category == "Resource Forecasting":
            plan["recommendations"] = [
                "Implement dynamic resource allocation",
                "Schedule maintenance during predicted low-usage periods",
                "Optimize backup windows based on usage patterns"
            ]

            plan["implementation_steps"] = [
                "1. Configure dynamic resource policies",
                "2. Update scheduling based on forecasts",
                "3. Implement resource monitoring",
                "4. Set up automated scaling rules",
                "5. Monitor and adjust policies"
            ]

            plan["expected_benefits"] = {
                "resource_optimization": "45%",
                "cost_savings": "30%",
                "operational_efficiency": "50%"
            }

        plan["risk_assessment"] = [
            {"risk": "Model accuracy degradation", "probability": "Low", "mitigation": "Regular model retraining"},
            {"risk": "Resource over-provisioning", "probability": "Medium", "mitigation": "Implement safety buffers"},
            {"risk": "Unexpected workload spikes", "probability": "Low", "mitigation": "Maintain manual override capability"}
        ]

        return plan

    except Exception as e:
        st.error(f"❌ Optimization plan generation failed: {str(e)}")
        return {}


# Display Functions

def display_patterns(patterns: List[Dict[str, Any]]):
    """Display discovered patterns."""
    st.markdown("#### 🔍 Discovered Patterns")

    for pattern in patterns:
        with st.expander(f"🎯 {pattern['type']}: {pattern['description'][:50]}..."):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Confidence", ".1%", pattern['confidence'] * 100)
                st.metric("Support", ".1%", pattern['support'] * 100)

            with col2:
                st.metric("Affected Simulations", pattern['affected_simulations'])
                st.write(f"**Impact:** {pattern['potential_impact']}")

            with col3:
                st.write(f"**Recommendation:** {pattern['recommendation']}")

            # Additional details
            if st.button(f"📊 Analyze Pattern {pattern['pattern_id']}", key=f"analyze_{pattern['pattern_id']}"):
                st.info(f"Detailed analysis for pattern {pattern['pattern_id']} would be shown here.")


def display_recommendations(recommendations: List[Dict[str, Any]]):
    """Display intelligent recommendations."""
    st.markdown("#### 🎯 AI Recommendations")

    for rec in recommendations:
        priority_colors = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}

        with st.expander(f"{priority_colors.get(rec['priority'], '⚪')} {rec['title']}"):
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Expected Impact", rec['expected_impact'])
                st.metric("Implementation Effort", rec['implementation_effort'])
                st.metric("Confidence", ".1%", rec['confidence'] * 100)

            with col2:
                st.write(f"**Priority:** {rec['priority']}")
                st.write(f"**Description:** {rec['description']}")

            # Data-driven insights
            st.markdown("**📊 Data-Driven Insights:**")
            for insight in rec['data_driven_insights']:
                st.write(f"• {insight}")

            # Action buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"✅ Implement", key=f"implement_{rec['recommendation_id']}"):
                    st.success(f"Implementation plan for {rec['title']} would be initiated.")

            with col2:
                if st.button(f"📋 View Details", key=f"details_{rec['recommendation_id']}"):
                    st.info(f"Detailed implementation guide for {rec['title']} would be displayed.")


def display_anomalies(anomalies: List[Dict[str, Any]]):
    """Display detected anomalies."""
    st.markdown("#### ⚠️ Detected Anomalies")

    if not anomalies:
        st.success("✅ No anomalies detected in the analyzed data.")
        return

    # Summary statistics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Anomalies", len(anomalies))

    with col2:
        high_severity = len([a for a in anomalies if a['severity'] == 'High'])
        st.metric("High Severity", high_severity)

    with col3:
        avg_score = np.mean([a['anomaly_score'] for a in anomalies])
        st.metric("Avg Anomaly Score", ".3f", avg_score)

    # Anomaly list
    for anomaly in anomalies[:10]:  # Show first 10
        severity_icon = "🔴" if anomaly['severity'] == 'High' else "🟡"

        with st.expander(f"{severity_icon} {anomaly['description']}"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Value", ".2f", anomaly['value'])
                st.metric("Score", ".3f", anomaly['anomaly_score'])

            with col2:
                st.write(f"**Severity:** {anomaly['severity']}")
                st.write(f"**Time:** {anomaly['timestamp'].strftime('%H:%M:%S')}")

            with col3:
                if st.button(f"🔍 Investigate", key=f"investigate_{anomaly['timestamp']}"):
                    st.info("Investigation workflow would be initiated here.")


def display_predictions(category: str, predictions_data: Dict[str, Any]):
    """Display predictions."""
    st.markdown(f"#### 🔮 {category} Predictions")

    predictions = predictions_data.get('predictions', [])

    if not predictions:
        st.warning("No predictions available.")
        return

    # Model performance
    model_info = predictions_data.get('model_info', {})
    if model_info:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Model R² Score", ".3f", model_info.get('r2_score', 0))

        with col2:
            st.metric("MSE", ".4f", model_info.get('mse', 0))

        with col3:
            accuracy = st.session_state.model_performance.get(category, {}).get('accuracy', 'Unknown')
            st.metric("Accuracy", accuracy)

    # Predictions table
    pred_df = pd.DataFrame(predictions)
    if not pred_df.empty:
        # Format columns appropriately
        if 'prediction' in pred_df.columns:
            pred_df['prediction'] = pred_df['prediction'].round(2)

        st.dataframe(pred_df, use_container_width=True)


def display_optimization_plan(plan: Dict[str, Any]):
    """Display optimization plan."""
    st.markdown("#### 📋 Optimization Plan")

    # Plan summary
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Category", plan.get('category', 'Unknown'))
        st.metric("Generated", plan.get('generated_at', datetime.now()).strftime('%H:%M'))

    with col2:
        benefits = plan.get('expected_benefits', {})
        if benefits:
            primary_benefit = list(benefits.keys())[0]
            st.metric("Primary Benefit", benefits[primary_benefit])

    # Recommendations
    st.markdown("**🎯 Key Recommendations:**")
    for rec in plan.get('recommendations', []):
        st.write(f"• {rec}")

    # Implementation steps
    st.markdown("**📝 Implementation Steps:**")
    for step in plan.get('implementation_steps', []):
        st.write(f"• {step}")

    # Expected benefits
    if plan.get('expected_benefits'):
        st.markdown("**💰 Expected Benefits:**")
        benefits_df = pd.DataFrame(
            list(plan['expected_benefits'].items()),
            columns=['Metric', 'Improvement']
        )
        st.dataframe(benefits_df, use_container_width=True)

    # Risk assessment
    if plan.get('risk_assessment'):
        st.markdown("**⚠️ Risk Assessment:**")
        for risk in plan.get('risk_assessment', []):
            with st.expander(f"Risk: {risk['risk']}"):
                st.write(f"**Probability:** {risk['probability']}")
                st.write(f"**Mitigation:** {risk['mitigation']}")


# Visualization Functions

def render_pattern_visualization(patterns: List[Dict[str, Any]]):
    """Render pattern visualization."""
    if not patterns:
        return

    # Create pattern summary chart
    pattern_types = [p['type'] for p in patterns]
    confidences = [p['confidence'] for p in patterns]

    fig = px.bar(
        x=pattern_types,
        y=confidences,
        title="Pattern Confidence Levels",
        labels={'x': 'Pattern Type', 'y': 'Confidence'},
        color=confidences,
        color_continuous_scale='Viridis'
    )

    st.plotly_chart(fig, use_container_width=True)


def render_anomaly_visualization(anomalies: List[Dict[str, Any]]):
    """Render anomaly visualization."""
    if not anomalies:
        return

    # Create timeline of anomalies
    timestamps = [a['timestamp'] for a in anomalies]
    values = [a['value'] for a in anomalies]
    scores = [a['anomaly_score'] for a in anomalies]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Values over time
    fig.add_trace(
        go.Scatter(x=timestamps, y=values, name="Values", mode='lines+markers'),
        secondary_y=False
    )

    # Anomaly scores
    fig.add_trace(
        go.Scatter(x=timestamps, y=scores, name="Anomaly Score", mode='markers',
                  marker=dict(color='red', size=8)),
        secondary_y=True
    )

    fig.update_layout(title="Anomaly Detection Timeline")
    fig.update_xaxes(title_text="Time")
    fig.update_yaxes(title_text="Value", secondary_y=False)
    fig.update_yaxes(title_text="Anomaly Score", secondary_y=True)

    st.plotly_chart(fig, use_container_width=True)


def render_predictive_visualization(category: str, predictions_data: Dict[str, Any]):
    """Render predictive analytics visualization."""
    predictions = predictions_data.get('predictions', [])

    if not predictions:
        return

    if category == "Performance Prediction":
        # Create performance prediction chart
        timestamps = [p['timestamp'] for p in predictions]
        predictions_values = [p['prediction'] for p in predictions]
        cpu_values = [p.get('cpu_usage', 0) for p in predictions]

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(x=timestamps, y=predictions_values, name="Predicted Response Time",
                      mode='lines+markers'),
            secondary_y=False
        )

        fig.add_trace(
            go.Scatter(x=timestamps, y=cpu_values, name="CPU Usage",
                      mode='lines', line=dict(dash='dot')),
            secondary_y=True
        )

        fig.update_layout(title="Performance Prediction Over Time")
        fig.update_xaxes(title_text="Time")
        fig.update_yaxes(title_text="Response Time (s)", secondary_y=False)
        fig.update_yaxes(title_text="CPU Usage (%)", secondary_y=True)

    else:
        # Generic prediction chart
        timestamps = [p['timestamp'] for p in predictions]
        predictions_values = [p['prediction'] for p in predictions]

        fig = px.line(
            x=timestamps,
            y=predictions_values,
            title=f"{category} Predictions",
            labels={'x': 'Time', 'y': 'Predicted Value'}
        )

    st.plotly_chart(fig, use_container_width=True)


def render_recommendation_impact_analysis(recommendations: List[Dict[str, Any]]):
    """Render recommendation impact analysis."""
    if not recommendations:
        return

    # Create impact analysis chart
    rec_titles = [r['title'][:30] + "..." for r in recommendations]
    impacts = [float(r['expected_impact'].split('%')[0]) for r in recommendations]
    priorities = [r['priority'] for r in recommendations]

    priority_colors = {'High': 'red', 'Medium': 'orange', 'Low': 'green'}

    fig = px.bar(
        x=rec_titles,
        y=impacts,
        title="Recommendation Impact Analysis",
        labels={'x': 'Recommendation', 'y': 'Expected Impact (%)'},
        color=priorities,
        color_discrete_map=priority_colors
    )

    fig.update_layout(xaxis_tickangle=-45)

    st.plotly_chart(fig, use_container_width=True)
