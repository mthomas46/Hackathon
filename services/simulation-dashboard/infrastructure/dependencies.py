"""Dependency Management and Graceful Degradation.

This module provides comprehensive dependency checking and graceful degradation
for optional libraries, ensuring the dashboard works even when some advanced
features are not available.
"""

import importlib
import sys
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from infrastructure.logging.logger import get_dashboard_logger

logger = get_dashboard_logger("dependencies")


class DependencyStatus(Enum):
    """Status of a dependency."""
    AVAILABLE = "available"
    MISSING = "missing"
    OPTIONAL = "optional"
    REQUIRED = "required"


@dataclass
class DependencyInfo:
    """Information about a dependency."""
    name: str
    package_name: str
    version_required: Optional[str] = None
    status: DependencyStatus = DependencyStatus.MISSING
    import_name: Optional[str] = None
    description: str = ""
    features_affected: List[str] = None
    fallback_message: str = ""
    install_command: str = ""

    def __post_init__(self):
        if self.features_affected is None:
            self.features_affected = []
        if not self.import_name:
            self.import_name = self.name


class DependencyManager:
    """Manager for handling optional dependencies and graceful degradation."""

    def __init__(self):
        self.dependencies: Dict[str, DependencyInfo] = {}
        self._checked_dependencies: Dict[str, bool] = {}
        self._feature_availability: Dict[str, bool] = {}

    def register_dependency(self, dependency: DependencyInfo) -> None:
        """Register a dependency for monitoring."""
        self.dependencies[dependency.name] = dependency
        logger.debug(f"Registered dependency: {dependency.name}")

    def check_dependency(self, name: str) -> bool:
        """Check if a dependency is available."""
        if name not in self.dependencies:
            logger.warning(f"Dependency {name} not registered")
            return False

        if name in self._checked_dependencies:
            return self._checked_dependencies[name]

        dependency = self.dependencies[name]

        try:
            # Try to import the dependency
            importlib.import_module(dependency.import_name)
            dependency.status = DependencyStatus.AVAILABLE
            self._checked_dependencies[name] = True
            logger.info(f"✅ Dependency {name} is available")
            return True

        except ImportError as e:
            dependency.status = DependencyStatus.MISSING
            self._checked_dependencies[name] = False

            # Log appropriate message based on status
            if dependency.status == DependencyStatus.REQUIRED:
                logger.error(f"❌ Required dependency {name} is missing: {dependency.fallback_message}")
                logger.error(f"   Install with: {dependency.install_command}")
            else:
                logger.warning(f"⚠️ Optional dependency {name} is not available: {dependency.fallback_message}")
                logger.info(f"   Some features will be limited. Install with: {dependency.install_command}")

            return False

        except Exception as e:
            logger.error(f"❌ Error checking dependency {name}: {str(e)}")
            dependency.status = DependencyStatus.MISSING
            self._checked_dependencies[name] = False
            return False

    def check_all_dependencies(self) -> Dict[str, bool]:
        """Check all registered dependencies."""
        results = {}
        for name in self.dependencies.keys():
            results[name] = self.check_dependency(name)
        return results

    def is_feature_available(self, feature_name: str) -> bool:
        """Check if a feature is available based on its dependencies."""
        if feature_name in self._feature_availability:
            return self._feature_availability[feature_name]

        # Find dependencies required for this feature
        required_deps = []
        for dep in self.dependencies.values():
            if feature_name in dep.features_affected:
                required_deps.append(dep.name)

        if not required_deps:
            # Feature doesn't have specific dependencies, assume available
            self._feature_availability[feature_name] = True
            return True

        # Check if all required dependencies are available
        all_available = all(self.check_dependency(dep) for dep in required_deps)
        self._feature_availability[feature_name] = all_available

        if not all_available:
            logger.warning(f"⚠️ Feature '{feature_name}' is disabled due to missing dependencies: {required_deps}")

        return all_available

    def get_dependency_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all dependencies."""
        status = {}
        for name, dep in self.dependencies.items():
            status[name] = {
                'name': dep.name,
                'status': dep.status.value,
                'description': dep.description,
                'features_affected': dep.features_affected,
                'available': self.check_dependency(name),
                'install_command': dep.install_command,
                'fallback_message': dep.fallback_message
            }
        return status

    def get_missing_dependencies(self) -> List[Dict[str, Any]]:
        """Get list of missing dependencies."""
        missing = []
        for name, dep in self.dependencies.items():
            if not self.check_dependency(name):
                missing.append({
                    'name': dep.name,
                    'package_name': dep.package_name,
                    'description': dep.description,
                    'install_command': dep.install_command,
                    'features_affected': dep.features_affected
                })
        return missing

    def get_feature_status(self) -> Dict[str, bool]:
        """Get availability status of all features."""
        # Define all known features
        all_features = [
            'ai_insights', 'pattern_recognition', 'anomaly_detection',
            'predictive_analytics', 'time_series_forecasting', 'ml_model_training',
            'advanced_visualizations', 'real_time_monitoring', 'autonomous_systems',
            'advanced_reporting', 'causal_analysis', 'correlation_analysis'
        ]

        feature_status = {}
        for feature in all_features:
            feature_status[feature] = self.is_feature_available(feature)

        return feature_status


# Global dependency manager instance
dependency_manager = DependencyManager()

# Register all known dependencies
def initialize_dependencies():
    """Initialize all known dependencies."""

    # Core ML Libraries
    dependency_manager.register_dependency(DependencyInfo(
        name="scikit_learn",
        package_name="scikit-learn",
        import_name="sklearn",
        version_required=">=1.3.0",
        status=DependencyStatus.REQUIRED,
        description="Machine learning algorithms for pattern recognition and predictive modeling",
        features_affected=["ai_insights", "pattern_recognition", "anomaly_detection", "ml_model_training"],
        fallback_message="AI insights and ML-based features will be limited",
        install_command="pip install scikit-learn>=1.3.0"
    ))

    dependency_manager.register_dependency(DependencyInfo(
        name="statsmodels",
        package_name="statsmodels",
        import_name="statsmodels",
        version_required=">=0.14.0",
        status=DependencyStatus.OPTIONAL,
        description="Statistical models and time series analysis",
        features_affected=["time_series_forecasting", "causal_analysis", "predictive_analytics"],
        fallback_message="Advanced time series analysis will be limited",
        install_command="pip install statsmodels>=0.14.0"
    ))

    dependency_manager.register_dependency(DependencyInfo(
        name="prophet",
        package_name="prophet",
        import_name="prophet",
        version_required=">=1.1.0",
        status=DependencyStatus.OPTIONAL,
        description="Facebook Prophet for advanced time series forecasting",
        features_affected=["time_series_forecasting", "predictive_analytics"],
        fallback_message="Prophet-based forecasting will not be available",
        install_command="pip install prophet>=1.1.0"
    ))

    dependency_manager.register_dependency(DependencyInfo(
        name="xgboost",
        package_name="xgboost",
        import_name="xgboost",
        version_required=">=1.7.0",
        status=DependencyStatus.OPTIONAL,
        description="Gradient boosting framework for advanced ML models",
        features_affected=["ml_model_training", "predictive_analytics"],
        fallback_message="XGBoost models will not be available",
        install_command="pip install xgboost>=1.7.0"
    ))

    dependency_manager.register_dependency(DependencyInfo(
        name="lightgbm",
        package_name="lightgbm",
        import_name="lightgbm",
        version_required=">=4.0.0",
        status=DependencyStatus.OPTIONAL,
        description="LightGBM for fast gradient boosting",
        features_affected=["ml_model_training", "predictive_analytics"],
        fallback_message="LightGBM models will not be available",
        install_command="pip install lightgbm>=4.0.0"
    ))

    dependency_manager.register_dependency(DependencyInfo(
        name="tensorflow",
        package_name="tensorflow",
        import_name="tensorflow",
        version_required=">=2.13.0",
        status=DependencyStatus.OPTIONAL,
        description="TensorFlow for deep learning and neural networks",
        features_affected=["ml_model_training", "pattern_recognition"],
        fallback_message="Deep learning features will not be available",
        install_command="pip install tensorflow>=2.13.0"
    ))

    dependency_manager.register_dependency(DependencyInfo(
        name="torch",
        package_name="torch",
        import_name="torch",
        version_required=">=2.0.0",
        status=DependencyStatus.OPTIONAL,
        description="PyTorch for deep learning and neural networks",
        features_affected=["ml_model_training", "pattern_recognition"],
        fallback_message="PyTorch-based features will not be available",
        install_command="pip install torch>=2.0.0"
    ))

    # Visualization Libraries
    dependency_manager.register_dependency(DependencyInfo(
        name="plotly",
        package_name="plotly",
        import_name="plotly",
        version_required=">=5.17.0",
        status=DependencyStatus.REQUIRED,
        description="Interactive plotting library for advanced visualizations",
        features_affected=["advanced_visualizations", "real_time_monitoring"],
        fallback_message="Advanced charts and visualizations will be limited",
        install_command="pip install plotly>=5.17.0"
    ))

    dependency_manager.register_dependency(DependencyInfo(
        name="bokeh",
        package_name="bokeh",
        import_name="bokeh",
        version_required=">=3.2.0",
        status=DependencyStatus.OPTIONAL,
        description="Interactive visualizations and dashboards",
        features_affected=["advanced_visualizations"],
        fallback_message="Some advanced visualization features will be limited",
        install_command="pip install bokeh>=3.2.0"
    ))

    dependency_manager.register_dependency(DependencyInfo(
        name="altair",
        package_name="altair",
        import_name="altair",
        version_required=">=5.1.0",
        status=DependencyStatus.OPTIONAL,
        description="Declarative statistical visualization library",
        features_affected=["advanced_visualizations", "correlation_analysis"],
        fallback_message="Altair-based visualizations will not be available",
        install_command="pip install altair>=5.1.0"
    ))

    # Additional Analytics Libraries
    dependency_manager.register_dependency(DependencyInfo(
        name="pandas_ta",
        package_name="pandas-ta",
        import_name="pandas_ta",
        version_required=">=0.3.14b",
        status=DependencyStatus.OPTIONAL,
        description="Technical analysis library for financial data",
        features_affected=["pattern_recognition", "anomaly_detection"],
        fallback_message="Technical analysis features will be limited",
        install_command="pip install pandas-ta>=0.3.14b"
    ))

    dependency_manager.register_dependency(DependencyInfo(
        name="ta_lib",
        package_name="TA-Lib",
        import_name="talib",
        version_required=">=0.4.25",
        status=DependencyStatus.OPTIONAL,
        description="Technical analysis library",
        features_affected=["pattern_recognition", "predictive_analytics"],
        fallback_message="TA-Lib indicators will not be available",
        install_command="pip install TA-Lib>=0.4.25"
    ))

    # WebSocket and Real-time Libraries
    dependency_manager.register_dependency(DependencyInfo(
        name="websockets",
        package_name="websockets",
        import_name="websockets",
        version_required=">=12.0",
        status=DependencyStatus.REQUIRED,
        description="WebSocket library for real-time communication",
        features_affected=["real_time_monitoring", "autonomous_systems"],
        fallback_message="Real-time features will be disabled",
        install_command="pip install websockets>=12.0"
    ))

    logger.info("✅ Dependency management system initialized")


# Utility functions for safe imports
def safe_import(module_name: str, fallback=None):
    """Safely import a module with fallback."""
    try:
        return importlib.import_module(module_name)
    except ImportError:
        logger.warning(f"⚠️ Failed to import {module_name}, using fallback")
        return fallback


def check_ml_availability() -> Dict[str, bool]:
    """Check availability of ML libraries."""
    ml_libs = ['scikit_learn', 'statsmodels', 'prophet', 'xgboost', 'lightgbm', 'tensorflow', 'torch']
    return {lib: dependency_manager.check_dependency(lib) for lib in ml_libs}


def check_visualization_availability() -> Dict[str, bool]:
    """Check availability of visualization libraries."""
    viz_libs = ['plotly', 'bokeh', 'altair']
    return {lib: dependency_manager.check_dependency(lib) for lib in viz_libs}


def get_system_status() -> Dict[str, Any]:
    """Get overall system status including dependency information."""
    return {
        'dependencies': dependency_manager.get_dependency_status(),
        'features': dependency_manager.get_feature_status(),
        'missing_dependencies': dependency_manager.get_missing_dependencies(),
        'ml_availability': check_ml_availability(),
        'visualization_availability': check_visualization_availability()
    }


# Initialize dependencies on module import
try:
    initialize_dependencies()
except Exception as e:
    logger.error(f"❌ Failed to initialize dependency management: {str(e)}")
