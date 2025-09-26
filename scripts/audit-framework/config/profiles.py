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

    # Core scoring weights (must sum to 100)
    dimension_weights: Dict[str, float] = field(default_factory=lambda: {
        'architecture': 25,
        'code_quality': 20,
        'performance': 15,
        'maintainability': 15,
        'documentation_quality': 13,
        'dry_principles': 7,
        'kiss_principles': 5
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
        'ddd_compliance_weight': 0.23,
        'ddd_migration_status_weight': 0.08,
        'rest_compliance_weight': 0.18,
        'layer_separation_weight': 0.09,
        'empty_directories_weight': 0.04,
        'requirements_file_weight': 0.04,
        'docker_infrastructure_weight': 0.04,
        'ddd_patterns_weight': 0.02,
        'rest_best_practices_weight': 0.02,
        'enable_routes_validation': True,
        'enable_endpoint_detection': True,
        'max_files_to_analyze': 50,
        'enable_ddd_patterns_analysis': True,
        'enable_rest_best_practices_analysis': True
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
            dimension_weights={
                'architecture': 20,
                'code_quality': 20,
                'performance': 15,
                'maintainability': 15,
                'documentation_quality': 10,
                'dry_principles': 10,
                'kiss_principles': 10
            },
            max_penalty_per_category=3.0,
            enable_detailed_analysis=False,
            architecture={
                'ddd_compliance_weight': 0.15,
                'rest_compliance_weight': 0.15,
                'layer_separation_weight': 0.10,
                'dry_principles_weight': 0.20,
                'kiss_principles_weight': 0.15,
                'documentation_quality_weight': 0.20,
                'enable_dry_analysis': False,
                'enable_kiss_analysis': False,
                'enable_documentation_analysis': False,
                'max_files_to_analyze': 20
            },
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
            description="Balanced analysis with standard thresholds",
            dimension_weights={
                'architecture': 25,
                'code_quality': 20,
                'performance': 15,
                'maintainability': 15,
                'documentation_quality': 13,
                'dry_principles': 7,
                'kiss_principles': 5
            }
        )

        # Strict profile for maximum quality enforcement
        self._profiles['strict'] = AuditProfile(
            name="strict",
            intensity=AuditIntensity.STRICT,
            description="MAXIMUM QUALITY ENFORCEMENT - Zero tolerance for code quality issues, enforces DRY/KISS/documentation compliance",
            dimension_weights={
                'architecture': 15,           # Reduced to emphasize quality issues
                'code_quality': 12,           # Core quality metrics
                'performance': 10,            # Performance still important
                'maintainability': 8,         # Organization matters
                'documentation_quality': 25,  # EXTREMELY weighted documentation (was 18)
                'dry_principles': 20,         # MAJOR emphasis on DRY (was 15)
                'kiss_principles': 10         # Strong KISS enforcement
            },
            critical_issue_threshold=0,       # ZERO tolerance for critical issues
            max_penalty_per_category=10.0,    # Severe penalties
            architecture={
                'ddd_compliance_weight': 0.18,
                'rest_compliance_weight': 0.14,
                'layer_separation_weight': 0.06,
                'dry_principles_weight': 0.22,    # HEAVILY weighted DRY
                'kiss_principles_weight': 0.15,   # Strongly weighted KISS
                'ddd_patterns_weight': 0.05,
                'rest_best_practices_weight': 0.05,
                'documentation_quality_weight': 0.22,  # HEAVILY weighted docs
                'enable_dry_analysis': True,
                'enable_kiss_analysis': True,
                'enable_ddd_patterns_analysis': True,
                'enable_rest_best_practices_analysis': True,
                'enable_documentation_analysis': True,
                'max_files_to_analyze': 100  # Maximum analysis depth
            },
            code_quality={
                'complexity_threshold': 6,         # EXTREMELY strict (was 8)
                'max_line_length': 88,             # Very strict (was 100)
                'test_coverage_required': 90.0,    # Very high requirement (was 85)
                'enable_duplication_check': True
            },
            maintainability={
                'docstring_coverage_required': 95.0,  # Extremely strict (was 90)
                'max_file_size_lines': 600,           # Very strict (was 800)
                'enable_dead_code_detection': True,
                'enable_dependency_analysis': True
            }
        )

        # CI Fast profile for quick CI/CD checks
        self._profiles['ci_fast'] = AuditProfile(
            name="ci_fast",
            intensity=AuditIntensity.CI_FAST,
            description="Fast CI checks focusing on critical issues only",
            dimension_weights={
                'architecture': 30,
                'code_quality': 25,
                'performance': 20,
                'maintainability': 25,
                'documentation_quality': 0,  # Skip documentation for speed
                'dry_principles': 0,         # Skip DRY analysis for speed
                'kiss_principles': 0         # Skip KISS analysis for speed
            },
            enable_detailed_analysis=False,
            enable_system_metrics=False,
            enable_third_party_tools=False,
            ci_mode=True,
            architecture={
                'enable_dry_analysis': False,
                'enable_kiss_analysis': False,
                'enable_ddd_patterns_analysis': False,
                'enable_rest_best_practices_analysis': False,
                'enable_documentation_analysis': False,
                'max_files_to_analyze': 20
            }
        )

        # STRICT DDD profile for maximum DDD compliance enforcement
        self._profiles['strict_ddd'] = AuditProfile(
            name="strict_ddd",
            intensity=AuditIntensity.STRICT,
            description="STRICT DDD ENFORCEMENT - Zero tolerance for architecture violations, includes DRY/KISS/documentation checks",
            critical_issue_threshold=0,  # Zero tolerance
            max_penalty_per_category=10.0,
            dimension_weights={
                'architecture': 30,      # Core DDD architecture
                'code_quality': 15,
                'performance': 10,
                'maintainability': 15,
                'documentation_quality': 10,  # Documentation matters for DDD
                'dry_principles': 10,         # DRY is critical for DDD
                'kiss_principles': 10         # KISS is critical for DDD
            },
            code_quality={
                'complexity_threshold': 8,
                'max_line_length': 100,
                'test_coverage_required': 90.0,  # STRICT requirement
                'enable_linting': True,
                'enable_duplication_check': True
            },
            maintainability={
                'docstring_coverage_required': 95.0,  # STRICT requirement
                'max_file_size_lines': 600,  # STRICT limit
                'enable_dead_code_detection': True,
                'enable_dependency_analysis': True
            },
            architecture={
                'ddd_compliance_weight': 0.35,     # High DDD weight
                'rest_compliance_weight': 0.20,
                'layer_separation_weight': 0.15,
                'dry_principles_weight': 0.15,
                'kiss_principles_weight': 0.15,
                'ddd_patterns_weight': 0.05,
                'rest_best_practices_weight': 0.03,
                'documentation_quality_weight': 0.12,
                'enable_dry_analysis': True,
                'enable_kiss_analysis': True,
                'enable_ddd_patterns_analysis': True,
                'enable_rest_best_practices_analysis': True,
                'enable_documentation_analysis': True,
                'enable_routes_validation': True,
                'enable_endpoint_detection': True,
                'max_files_to_analyze': 100  # Analyze more files for DDD compliance
            },
            custom_thresholds={
                'architecture': {
                    'require_ddd_layers': True,
                    'require_clean_architecture': True,
                    'require_strict_layer_separation': True,
                    'forbid_modules_directory_business_logic': True,
                    'require_ddd_directory_migration': True,
                    'max_legacy_module_files': 0,
                    'enforce_domain_layer_completeness': True,
                    'enforce_application_layer_patterns': True,
                    'forbid_presentation_business_logic': True,
                    'require_infrastructure_abstractions': True,
                    'max_architecture_violations': 0,
                    'require_dry_compliance': True,      # New: Enforce DRY
                    'require_kiss_compliance': True,     # New: Enforce KISS
                    'require_documentation_compliance': True  # New: Enforce docs
                }
            }
        )

        # CI Comprehensive profile for full CI analysis
        self._profiles['ci_comprehensive'] = AuditProfile(
            name="ci_comprehensive",
            intensity=AuditIntensity.STRICT,
            description="Comprehensive CI analysis with full scrutiny including all new checks",
            dimension_weights={
                'architecture': 25,
                'code_quality': 20,
                'performance': 15,
                'maintainability': 15,
                'documentation_quality': 13,
                'dry_principles': 7,
                'kiss_principles': 5
            },
            ci_mode=True,
            fail_on_critical_issues=True,
            output_format="json",
            architecture={
                'enable_dry_analysis': True,
                'enable_kiss_analysis': True,
                'enable_ddd_patterns_analysis': True,
                'enable_rest_best_practices_analysis': True,
                'enable_documentation_analysis': True,
                'max_files_to_analyze': 50
            }
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
