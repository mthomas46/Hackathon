"""
Audit Framework Profiles
Configurable profiles for different audit scenarios and intensity levels
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum


class AuditIntensity(Enum):
    """Audit intensity levels"""
    RELAXED = "relaxed"      # Development-friendly, fewer penalties
    STANDARD = "standard"   # Balanced analysis and penalties
    STRICT = "strict"       # Maximum scrutiny and penalties
    CI_FAST = "ci_fast"     # Fast CI checks, focus on critical issues


@dataclass
class AuditProfile:
    """Configurable audit profile with tunable parameters"""

    name: str
    intensity: AuditIntensity
    description: str

    # Core scoring weights
    dimension_weights: Dict[str, float] = field(default_factory=lambda: {
        'architecture': 30,
        'code_quality': 25,
        'performance': 20,
        'maintainability': 25
    })

    # Thresholds and penalties
    critical_issue_threshold: int = 2
    max_penalty_per_category: float = 5.0

    # Analysis depth controls
    enable_detailed_analysis: bool = True
    enable_system_metrics: bool = True
    enable_third_party_tools: bool = True

    # Module-specific settings
    architecture: Dict[str, Any] = field(default_factory=lambda: {
        'ddd_compliance_weight': 0.4,
        'rest_compliance_weight': 0.35,
        'layer_separation_weight': 0.25,
        'enable_routes_validation': True,
        'enable_endpoint_detection': True,
        'max_files_to_analyze': 50
    })

    code_quality: Dict[str, Any] = field(default_factory=lambda: {
        'complexity_threshold': 10,
        'max_line_length': 120,
        'enable_linting': True,
        'enable_duplication_check': True,
        'test_coverage_required': 70.0
    })

    performance: Dict[str, Any] = field(default_factory=lambda: {
        'memory_threshold_mb': 500,
        'cpu_threshold_percent': 80,
        'enable_resource_monitoring': True,
        'timeout_seconds': 30
    })

    maintainability: Dict[str, Any] = field(default_factory=lambda: {
        'docstring_coverage_required': 80.0,
        'max_file_size_lines': 1000,
        'enable_dead_code_detection': True,
        'enable_dependency_analysis': True
    })

    # CI/CD specific settings
    ci_mode: bool = False
    fail_on_critical_issues: bool = True
    generate_recommendations: bool = True
    output_format: str = "rich"  # rich, json, markdown

    # Custom overrides
    custom_thresholds: Dict[str, Any] = field(default_factory=dict)
    disabled_checks: list = field(default_factory=list)


class ProfileManager:
    """Manages audit profiles and provides easy access"""

    def __init__(self):
        self._profiles = {}
        self._load_default_profiles()

    def _load_default_profiles(self):
        """Load built-in audit profiles"""

        # Relaxed profile for development
        self._profiles['relaxed'] = AuditProfile(
            name="relaxed",
            intensity=AuditIntensity.RELAXED,
            description="Development-friendly profile with relaxed thresholds",
            max_penalty_per_category=3.0,
            enable_detailed_analysis=False,
            code_quality={
                'complexity_threshold': 15,
                'max_line_length': 140,
                'test_coverage_required': 50.0
            },
            maintainability={
                'docstring_coverage_required': 60.0,
                'max_file_size_lines': 1500,
            }
        )

        # Standard profile for regular analysis
        self._profiles['standard'] = AuditProfile(
            name="standard",
            intensity=AuditIntensity.STANDARD,
            description="Balanced analysis with standard thresholds"
        )

        # Strict profile for maximum quality enforcement
        self._profiles['strict'] = AuditProfile(
            name="strict",
            intensity=AuditIntensity.STRICT,
            description="Maximum scrutiny with strict quality requirements",
            critical_issue_threshold=1,
            max_penalty_per_category=7.0,
            code_quality={
                'complexity_threshold': 8,
                'max_line_length': 100,
                'test_coverage_required': 85.0
            },
            maintainability={
                'docstring_coverage_required': 90.0,
                'max_file_size_lines': 800,
            }
        )

        # CI Fast profile for quick CI/CD checks
        self._profiles['ci_fast'] = AuditProfile(
            name="ci_fast",
            intensity=AuditIntensity.CI_FAST,
            description="Fast CI checks focusing on critical issues only",
            enable_detailed_analysis=False,
            enable_system_metrics=False,
            enable_third_party_tools=False,
            ci_mode=True,
            architecture={
                'max_files_to_analyze': 20
            }
        )

        # CI Comprehensive profile for full CI analysis
        self._profiles['ci_comprehensive'] = AuditProfile(
            name="ci_comprehensive",
            intensity=AuditIntensity.STRICT,
            description="Comprehensive CI analysis with full scrutiny",
            ci_mode=True,
            fail_on_critical_issues=True,
            output_format="json"
        )

    def get_profile(self, name: str) -> AuditProfile:
        """Get a profile by name"""
        if name not in self._profiles:
            raise ValueError(f"Profile '{name}' not found. Available: {list(self._profiles.keys())}")
        return self._profiles[name]

    def list_profiles(self) -> Dict[str, str]:
        """List all available profiles with descriptions"""
        return {name: profile.description for name, profile in self._profiles.items()}

    def create_custom_profile(self, base_profile: str, overrides: Dict[str, Any]) -> AuditProfile:
        """Create a custom profile based on an existing one"""
        base = self.get_profile(base_profile)

        # Create a copy with overrides
        custom_data = base.__dict__.copy()
        custom_data.update(overrides)
        custom_data['name'] = f"custom_{base_profile}"

        return AuditProfile(**custom_data)

    def validate_profile(self, profile: AuditProfile) -> bool:
        """Validate that a profile has valid configuration"""
        # Check dimension weights sum to 100
        total_weight = sum(profile.dimension_weights.values())
        if not (99.5 <= total_weight <= 100.5):  # Allow small floating point variance
            return False

        # Check intensity is valid
        if profile.intensity not in AuditIntensity:
            return False

        return True


# Global profile manager instance
profile_manager = ProfileManager()
