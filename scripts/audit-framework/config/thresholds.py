"""
Audit Framework Thresholds Configuration
Centralized threshold management for configurable audit criteria
"""

from typing import Dict, Any
from .profiles import AuditProfile


def get_default_thresholds() -> Dict[str, Any]:
    """Get default threshold configuration for audit framework"""
    return {
        # Core scoring thresholds
        'min_passing_score': 70.0,
        'excellent_score': 90.0,
        'critical_score': 50.0,

        # Dimension-specific thresholds
        'dimensions': {
            'architecture': {
                'min_score': 60.0,
                'target_score': 80.0,
                'ddd_compliance_required': 70.0,
                'rest_compliance_required': 75.0,
                'layer_separation_required': 70.0,
                'routes_score_required': 8.0
            },
            'code_quality': {
                'min_score': 65.0,
                'target_score': 85.0,
                'complexity_max': 10,
                'test_coverage_required': 70.0,
                'linting_score_required': 7.0
            },
            'performance': {
                'min_score': 70.0,
                'target_score': 85.0,
                'memory_threshold_mb': 500,
                'cpu_threshold_percent': 80,
                'response_time_max_ms': 1000
            },
            'maintainability': {
                'min_score': 65.0,
                'target_score': 80.0,
                'docstring_coverage_required': 80.0,
                'max_file_size_lines': 1000,
                'dead_code_tolerance_percent': 5.0
            }
        },

        # Critical issue thresholds
        'critical_issues': {
            'max_critical_issues': 2,
            'max_high_priority_issues': 5,
            'max_medium_priority_issues': 10
        },

        # File and module limits
        'file_limits': {
            'max_lines_per_file': 1000,
            'max_functions_per_file': 20,
            'max_classes_per_file': 10,
            'max_imports_per_file': 20
        },

        # Complexity thresholds
        'complexity': {
            'max_cyclomatic_complexity': 10,
            'max_function_complexity': 15,
            'max_class_complexity': 50,
            'high_complexity_threshold': 20
        },

        # Testing requirements
        'testing': {
            'min_test_coverage': 70.0,
            'min_test_files_ratio': 0.5,
            'max_test_file_size': 500,
            'test_naming_required': True
        },

        # Documentation requirements
        'documentation': {
            'min_docstring_coverage': 80.0,
            'require_module_docstrings': True,
            'require_function_docstrings': True,
            'require_class_docstrings': True
        },

        # Security thresholds
        'security': {
            'max_hardcoded_secrets': 0,
            'max_vulnerabilities': 0,
            'require_input_validation': True,
            'require_secure_defaults': True
        },

        # Performance thresholds
        'performance': {
            'max_memory_usage_mb': 500,
            'max_cpu_usage_percent': 80,
            'max_response_time_ms': 1000,
            'require_resource_limits': True
        },

        # Maintainability thresholds
        'maintainability': {
            'max_duplicate_lines_percent': 10.0,
            'max_dead_code_percent': 5.0,
            'require_dependency_injection': False,  # Optional for now
            'max_coupling_score': 20
        },

        # Architecture thresholds
        'architecture': {
            'require_ddd_layers': True,
            'require_clean_architecture': False,
            'max_architecture_violations': 5,
            'require_routes_directory': True,
            'require_domain_separation': True
        },

        # CI/CD specific thresholds
        'ci_cd': {
            'max_audit_time_seconds': 300,
            'fail_on_critical_issues': True,
            'require_minimum_score': 60.0,
            'generate_actionable_report': True
        }
    }


def get_thresholds_for_profile(profile: AuditProfile) -> Dict[str, Any]:
    """Get thresholds adjusted for a specific audit profile"""
    base_thresholds = get_default_thresholds()

    # Adjust thresholds based on profile intensity
    if profile.intensity.name == 'RELAXED':
        # Relax thresholds for development
        base_thresholds['dimensions']['architecture']['min_score'] = 50.0
        base_thresholds['dimensions']['code_quality']['min_score'] = 55.0
        base_thresholds['dimensions']['maintainability']['min_score'] = 55.0
        base_thresholds['complexity']['max_cyclomatic_complexity'] = 15
        base_thresholds['testing']['min_test_coverage'] = 50.0
        base_thresholds['documentation']['min_docstring_coverage'] = 60.0
        base_thresholds['file_limits']['max_lines_per_file'] = 1500

    elif profile.intensity.name == 'STRICT':
        # Stricter thresholds for maximum quality
        base_thresholds['dimensions']['architecture']['min_score'] = 75.0
        base_thresholds['dimensions']['code_quality']['min_score'] = 80.0
        base_thresholds['dimensions']['maintainability']['min_score'] = 75.0
        base_thresholds['complexity']['max_cyclomatic_complexity'] = 8
        base_thresholds['testing']['min_test_coverage'] = 85.0
        base_thresholds['documentation']['min_docstring_coverage'] = 90.0
        base_thresholds['file_limits']['max_lines_per_file'] = 800
        base_thresholds['critical_issues']['max_critical_issues'] = 1

    elif profile.intensity.name == 'CI_FAST':
        # Fast CI checks - focus on critical issues only
        base_thresholds['ci_cd']['max_audit_time_seconds'] = 60
        base_thresholds['critical_issues']['max_critical_issues'] = 0
        base_thresholds['dimensions']['architecture']['min_score'] = 40.0
        base_thresholds['dimensions']['code_quality']['min_score'] = 50.0

    # Apply profile-specific overrides
    if profile.custom_thresholds:
        _apply_custom_thresholds(base_thresholds, profile.custom_thresholds)

    return base_thresholds


def _apply_custom_thresholds(base_thresholds: Dict[str, Any], custom: Dict[str, Any]) -> None:
    """Apply custom threshold overrides"""
    def deep_update(base: Dict[str, Any], updates: Dict[str, Any]) -> None:
        for key, value in updates.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                deep_update(base[key], value)
            else:
                base[key] = value

    deep_update(base_thresholds, custom)


def validate_thresholds(thresholds: Dict[str, Any]) -> bool:
    """Validate that thresholds configuration is valid"""
    try:
        # Check required top-level keys
        required_keys = ['dimensions', 'critical_issues', 'file_limits', 'complexity', 'testing']
        for key in required_keys:
            if key not in thresholds:
                return False

        # Check dimension weights sum to 100
        dimensions = thresholds.get('dimensions', {})
        for dim_name, dim_config in dimensions.items():
            if 'min_score' not in dim_config:
                return False
            if not (0 <= dim_config['min_score'] <= 100):
                return False

        # Check complexity thresholds are reasonable
        complexity = thresholds.get('complexity', {})
        if complexity.get('max_cyclomatic_complexity', 0) <= 0:
            return False

        return True

    except Exception:
        return False


class ThresholdConfig:
    """Configuration class for audit thresholds"""

    def __init__(self, thresholds: Dict[str, Any] = None):
        self._thresholds = thresholds or get_default_thresholds()
        if not validate_thresholds(self._thresholds):
            raise ValueError("Invalid threshold configuration")

    def get(self, key_path: str, default=None):
        """Get a threshold value using dot notation (e.g., 'dimensions.architecture.min_score')"""
        keys = key_path.split('.')
        value = self._thresholds

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any) -> None:
        """Set a threshold value using dot notation"""
        keys = key_path.split('.')
        config = self._thresholds

        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        # Set the value
        config[keys[-1]] = value

        # Re-validate after change
        if not validate_thresholds(self._thresholds):
            raise ValueError(f"Setting {key_path} to {value} creates invalid configuration")

    def to_dict(self) -> Dict[str, Any]:
        """Export thresholds as dictionary"""
        return self._thresholds.copy()

    def validate(self) -> bool:
        """Validate current configuration"""
        return validate_thresholds(self._thresholds)
