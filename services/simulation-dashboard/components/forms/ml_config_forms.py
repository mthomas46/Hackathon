"""ML Configuration Form Components.

This module provides form components for configuring machine learning models,
training parameters, and prediction settings.
"""

import streamlit as st
from typing import Dict, Any, Optional, List
from infrastructure.dependencies import dependency_manager


def render_ml_config_form(
    config_key: str = "ml_config",
    title: str = "🤖 Machine Learning Configuration",
    default_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Render ML configuration form for model training and prediction settings.

    Args:
        config_key: Key for storing configuration in session state
        title: Form title
        default_config: Default configuration values

    Returns:
        Dictionary containing the ML configuration
    """
    st.markdown(f"### {title}")

    # Initialize configuration in session state
    if config_key not in st.session_state:
        st.session_state[config_key] = default_config or get_default_ml_config()

    config = st.session_state[config_key]

    # Check ML library availability
    sklearn_available = dependency_manager.check_dependency('scikit_learn')
    statsmodels_available = dependency_manager.check_dependency('statsmodels')
    prophet_available = dependency_manager.check_dependency('prophet')
    xgboost_available = dependency_manager.check_dependency('xgboost')
    lightgbm_available = dependency_manager.check_dependency('lightgbm')

    # Display dependency status
    if not sklearn_available:
        st.warning("⚠️ scikit-learn not available. Limited ML configuration options.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🎯 Model Selection")

        # Algorithm selection based on available libraries
        available_algorithms = ["Linear Regression", "Decision Tree"]

        if sklearn_available:
            available_algorithms.extend([
                "Random Forest", "Gradient Boosting", "Support Vector Machine",
                "K-Nearest Neighbors", "Neural Network"
            ])

        if xgboost_available:
            available_algorithms.append("XGBoost")

        if lightgbm_available:
            available_algorithms.append("LightGBM")

        if statsmodels_available:
            available_algorithms.extend(["ARIMA", "SARIMA"])

        if prophet_available:
            available_algorithms.append("Facebook Prophet")

        selected_algorithm = st.selectbox(
            "Algorithm",
            options=available_algorithms,
            index=available_algorithms.index(config.get('algorithm', 'Random Forest')) if config.get('algorithm') in available_algorithms else 0,
            key=f"{config_key}_algorithm"
        )
        config['algorithm'] = selected_algorithm

        # Problem type
        problem_type = st.selectbox(
            "Problem Type",
            options=["Regression", "Classification", "Time Series", "Clustering"],
            index=["Regression", "Classification", "Time Series", "Clustering"].index(config.get('problem_type', 'Regression')),
            key=f"{config_key}_problem_type"
        )
        config['problem_type'] = problem_type

    with col2:
        st.markdown("#### ⚙️ Training Parameters")

        # Common parameters
        test_size = st.slider(
            "Test Size (%)",
            min_value=10,
            max_value=50,
            value=config.get('test_size', 20),
            key=f"{config_key}_test_size"
        )
        config['test_size'] = test_size

        random_state = st.number_input(
            "Random State",
            min_value=0,
            max_value=9999,
            value=config.get('random_state', 42),
            key=f"{config_key}_random_state"
        )
        config['random_state'] = random_state

        # Algorithm-specific parameters
        if selected_algorithm in ["Random Forest", "Gradient Boosting", "XGBoost", "LightGBM"]:
            n_estimators = st.slider(
                "Number of Estimators",
                min_value=10,
                max_value=1000,
                value=config.get('n_estimators', 100),
                key=f"{config_key}_n_estimators"
            )
            config['n_estimators'] = n_estimators

            max_depth = st.slider(
                "Max Depth",
                min_value=3,
                max_value=20,
                value=config.get('max_depth', 10),
                key=f"{config_key}_max_depth"
            )
            config['max_depth'] = max_depth

        elif selected_algorithm == "Support Vector Machine":
            c_param = st.slider(
                "C Parameter",
                min_value=0.1,
                max_value=10.0,
                value=config.get('c_param', 1.0),
                key=f"{config_key}_c_param"
            )
            config['c_param'] = c_param

            kernel = st.selectbox(
                "Kernel",
                options=["linear", "poly", "rbf", "sigmoid"],
                index=["linear", "poly", "rbf", "sigmoid"].index(config.get('kernel', 'rbf')),
                key=f"{config_key}_kernel"
            )
            config['kernel'] = kernel

        elif selected_algorithm in ["ARIMA", "SARIMA"]:
            p_param = st.slider(
                "AR Order (p)",
                min_value=0,
                max_value=5,
                value=config.get('p_param', 1),
                key=f"{config_key}_p_param"
            )
            config['p_param'] = p_param

            d_param = st.slider(
                "Differencing (d)",
                min_value=0,
                max_value=2,
                value=config.get('d_param', 1),
                key=f"{config_key}_d_param"
            )
            config['d_param'] = d_param

            q_param = st.slider(
                "MA Order (q)",
                min_value=0,
                max_value=5,
                value=config.get('q_param', 1),
                key=f"{config_key}_q_param"
            )
            config['q_param'] = q_param

    # Advanced options
    st.markdown("#### 🔧 Advanced Options")

    col3, col4 = st.columns(2)

    with col3:
        enable_cross_validation = st.checkbox(
            "Enable Cross-Validation",
            value=config.get('enable_cross_validation', True),
            key=f"{config_key}_cross_validation"
        )
        config['enable_cross_validation'] = enable_cross_validation

        if enable_cross_validation:
            cv_folds = st.slider(
                "CV Folds",
                min_value=3,
                max_value=10,
                value=config.get('cv_folds', 5),
                key=f"{config_key}_cv_folds"
            )
            config['cv_folds'] = cv_folds

        enable_feature_selection = st.checkbox(
            "Enable Feature Selection",
            value=config.get('enable_feature_selection', False),
            key=f"{config_key}_feature_selection"
        )
        config['enable_feature_selection'] = enable_feature_selection

    with col4:
        enable_early_stopping = st.checkbox(
            "Enable Early Stopping",
            value=config.get('enable_early_stopping', False),
            key=f"{config_key}_early_stopping"
        )
        config['enable_early_stopping'] = enable_early_stopping

        enable_grid_search = st.checkbox(
            "Enable Grid Search",
            value=config.get('enable_grid_search', False),
            key=f"{config_key}_grid_search"
        )
        config['enable_grid_search'] = enable_grid_search

        save_model = st.checkbox(
            "Save Trained Model",
            value=config.get('save_model', True),
            key=f"{config_key}_save_model"
        )
        config['save_model'] = save_model

    # Performance metrics
    st.markdown("#### 📊 Performance Metrics")

    available_metrics = ["Mean Absolute Error", "Mean Squared Error", "Root Mean Squared Error", "R² Score"]

    if problem_type == "Classification":
        available_metrics.extend(["Accuracy", "Precision", "Recall", "F1 Score"])

    selected_metrics = st.multiselect(
        "Evaluation Metrics",
        options=available_metrics,
        default=config.get('evaluation_metrics', ["Mean Absolute Error", "R² Score"]),
        key=f"{config_key}_metrics"
    )
    config['evaluation_metrics'] = selected_metrics

    # Configuration summary
    st.markdown("---")
    st.markdown("#### 📋 Configuration Summary")

    summary_col1, summary_col2 = st.columns(2)

    with summary_col1:
        st.write(f"**Algorithm:** {config['algorithm']}")
        st.write(f"**Problem Type:** {config['problem_type']}")
        st.write(f"**Test Size:** {config['test_size']}%")

    with summary_col2:
        st.write(f"**Cross-Validation:** {'Enabled' if config.get('enable_cross_validation', False) else 'Disabled'}")
        st.write(f"**Feature Selection:** {'Enabled' if config.get('enable_feature_selection', False) else 'Disabled'}")
        st.write(f"**Metrics:** {len(config.get('evaluation_metrics', []))}")

    # Save configuration
    if st.button("💾 Save Configuration", key=f"{config_key}_save"):
        st.success("✅ ML configuration saved successfully!")
        st.session_state[config_key] = config

    return config


def render_model_training_form(
    training_key: str = "training_config",
    title: str = "🎓 Model Training Configuration"
) -> Dict[str, Any]:
    """Render model training configuration form.

    Args:
        training_key: Key for storing training configuration
        title: Form title

    Returns:
        Dictionary containing training configuration
    """
    st.markdown(f"### {title}")

    if training_key not in st.session_state:
        st.session_state[training_key] = get_default_training_config()

    training_config = st.session_state[training_key]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📊 Data Configuration")

        data_source = st.selectbox(
            "Data Source",
            options=["Upload File", "Database Connection", "API Endpoint", "Sample Data"],
            index=["Upload File", "Database Connection", "API Endpoint", "Sample Data"].index(training_config.get('data_source', 'Sample Data')),
            key=f"{training_key}_data_source"
        )
        training_config['data_source'] = data_source

        if data_source == "Upload File":
            uploaded_file = st.file_uploader(
                "Upload training data (CSV)",
                type=['csv'],
                key=f"{training_key}_upload"
            )
            if uploaded_file:
                training_config['uploaded_file'] = uploaded_file

        target_column = st.text_input(
            "Target Column",
            value=training_config.get('target_column', ''),
            placeholder="e.g., price, category, sales",
            key=f"{training_key}_target"
        )
        training_config['target_column'] = target_column

    with col2:
        st.markdown("#### ⏱️ Training Settings")

        max_training_time = st.slider(
            "Max Training Time (minutes)",
            min_value=1,
            max_value=120,
            value=training_config.get('max_training_time', 30),
            key=f"{training_key}_max_time"
        )
        training_config['max_training_time'] = max_training_time

        enable_monitoring = st.checkbox(
            "Enable Training Monitoring",
            value=training_config.get('enable_monitoring', True),
            key=f"{training_key}_monitoring"
        )
        training_config['enable_monitoring'] = enable_monitoring

        save_checkpoints = st.checkbox(
            "Save Model Checkpoints",
            value=training_config.get('save_checkpoints', False),
            key=f"{training_key}_checkpoints"
        )
        training_config['save_checkpoints'] = save_checkpoints

    # Feature engineering options
    st.markdown("#### 🔧 Feature Engineering")

    col3, col4 = st.columns(2)

    with col3:
        enable_scaling = st.checkbox(
            "Enable Feature Scaling",
            value=training_config.get('enable_scaling', True),
            key=f"{training_key}_scaling"
        )
        training_config['enable_scaling'] = enable_scaling

        handle_missing = st.checkbox(
            "Handle Missing Values",
            value=training_config.get('handle_missing', True),
            key=f"{training_key}_missing"
        )
        training_config['handle_missing'] = handle_missing

    with col4:
        encode_categorical = st.checkbox(
            "Encode Categorical Features",
            value=training_config.get('encode_categorical', True),
            key=f"{training_key}_categorical"
        )
        training_config['encode_categorical'] = encode_categorical

        remove_outliers = st.checkbox(
            "Remove Outliers",
            value=training_config.get('remove_outliers', False),
            key=f"{training_key}_outliers"
        )
        training_config['remove_outliers'] = remove_outliers

    # Start training button
    st.markdown("---")

    col_start, col_status = st.columns([1, 2])

    with col_start:
        if st.button("🚀 Start Training", key=f"{training_key}_start", type="primary"):
            # Here you would typically start the training process
            st.success("🎯 Training started! Monitor progress below.")
            training_config['training_status'] = 'running'
            training_config['start_time'] = str(pd.Timestamp.now())

    with col_status:
        status = training_config.get('training_status', 'idle')
        if status == 'running':
            st.info("🔄 Training in progress...")
        elif status == 'completed':
            st.success("✅ Training completed!")
        elif status == 'failed':
            st.error("❌ Training failed!")
        else:
            st.write("⏸️ Ready to start training")

    return training_config


def get_default_ml_config() -> Dict[str, Any]:
    """Get default ML configuration."""
    return {
        'algorithm': 'Random Forest',
        'problem_type': 'Regression',
        'test_size': 20,
        'random_state': 42,
        'n_estimators': 100,
        'max_depth': 10,
        'enable_cross_validation': True,
        'cv_folds': 5,
        'enable_feature_selection': False,
        'enable_early_stopping': False,
        'enable_grid_search': False,
        'save_model': True,
        'evaluation_metrics': ['Mean Absolute Error', 'R² Score']
    }


def get_default_training_config() -> Dict[str, Any]:
    """Get default training configuration."""
    return {
        'data_source': 'Sample Data',
        'target_column': '',
        'max_training_time': 30,
        'enable_monitoring': True,
        'save_checkpoints': False,
        'enable_scaling': True,
        'handle_missing': True,
        'encode_categorical': True,
        'remove_outliers': False,
        'training_status': 'idle'
    }
