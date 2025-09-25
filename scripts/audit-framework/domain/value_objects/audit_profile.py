"""
AuditProfile Value Object

Immutable value object representing audit configuration profiles
with validation and business rules.
"""

from dataclasses import dataclass, field
from typing import Dict, Any
from enum import Enum


class AuditIntensity(Enum):
    """Audit intensity levels defining analysis depth and strictness."""
    RELAXED = "relaxed"     # Basic checks, minimal penalties
    STANDARD = "standard"   # Balanced analysis and penalties
    STRICT = "strict"       # Maximum scrutiny and penalties
    CI_FAST = "ci_fast"     # Fast CI checks, focus on critical issues


@dataclass(frozen=True)
class AuditProfile:
    """Immutable value object representing an audit configuration profile.

    Audit profiles define the analysis depth, scoring weights, and thresholds
    used during service auditing with business rules for validation.
    """

    name: str
    intensity: AuditIntensity
    description: str

    # Core scoring weights (must sum to 100)
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
        'max_file_size_kb': 1000,
        'duplicate_line_threshold': 50,
        'enable_linting': True,
        'enable_complexity_analysis': True
    })

    performance: Dict[str, Any] = field(default_factory=lambda: {
        'memory_threshold_mb': 512,
        'cpu_threshold_percent': 80,
        'io_threshold_iops': 1000,
        'enable_resource_monitoring': True,
        'enable_caching_analysis': True
    })

    maintainability: Dict[str, Any] = field(default_factory=lambda: {
        'min_docstring_coverage': 80,
        'organization_weight': 0.25,
        'error_handling_weight': 0.15,
        'scalability_weight': 0.15,
        'devops_weight': 0.10,
        'architecture_weight': 0.10
    })

    def __post_init__(self):
        """Apply business rules and validations."""
        self._validate_weights()
        self._validate_intensity_settings()

    def _validate_weights(self) -> None:
        """Validate that dimension weights sum to 100."""
        total_weight = sum(self.dimension_weights.values())
        if abs(total_weight - 100.0) > 0.01:  # Allow small floating point differences
            raise ValueError(f"Dimension weights must sum to 100, got {total_weight}")

        # Validate individual weights are reasonable
        for dimension, weight in self.dimension_weights.items():
            if not (0 <= weight <= 100):
                raise ValueError(f"Dimension weight for {dimension} must be between 0 and 100")

    def _validate_intensity_settings(self) -> None:
        """Apply intensity-specific validations and defaults."""
        if self.intensity == AuditIntensity.CI_FAST:
            # CI_FAST should be fast, so disable heavy analysis
            if self.enable_third_party_tools:
                object.__setattr__(self, 'enable_third_party_tools', False)
            if self.enable_system_metrics:
                object.__setattr__(self, 'enable_system_metrics', False)

        elif self.intensity == AuditIntensity.STRICT:
            # STRICT should be thorough, so enable everything
            if not self.enable_detailed_analysis:
                object.__setattr__(self, 'enable_detailed_analysis', True)
            if not self.enable_system_metrics:
                object.__setattr__(self, 'enable_system_metrics', True)
            if not self.enable_third_party_tools:
                object.__setattr__(self, 'enable_third_party_tools', True)

    def get_dimension_weight(self, dimension: str) -> float:
        """Get weight for a specific dimension."""
        return self.dimension_weights.get(dimension, 0.0)

    def is_fast_mode(self) -> bool:
        """Check if this profile is optimized for speed."""
        return self.intensity == AuditIntensity.CI_FAST

    def is_strict_mode(self) -> bool:
        """Check if this profile applies maximum scrutiny."""
        return self.intensity == AuditIntensity.STRICT

    def get_setting(self, category: str, key: str, default: Any = None) -> Any:
        """Get a setting value from category configuration."""
        category_config = getattr(self, category, {})
        return category_config.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "intensity": self.intensity.value,
            "description": self.description,
            "dimension_weights": self.dimension_weights,
            "critical_issue_threshold": self.critical_issue_threshold,
            "max_penalty_per_category": self.max_penalty_per_category,
            "enable_detailed_analysis": self.enable_detailed_analysis,
            "enable_system_metrics": self.enable_system_metrics,
            "enable_third_party_tools": self.enable_third_party_tools,
            "architecture": self.architecture,
            "code_quality": self.code_quality,
            "performance": self.performance,
            "maintainability": self.maintainability,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditProfile':
        """Create AuditProfile from dictionary."""
        # Handle intensity enum conversion
        intensity = AuditIntensity(data["intensity"])

        return cls(
            name=data["name"],
            intensity=intensity,
            description=data["description"],
            dimension_weights=data.get("dimension_weights", {}),
            critical_issue_threshold=data.get("critical_issue_threshold", 2),
            max_penalty_per_category=data.get("max_penalty_per_category", 5.0),
            enable_detailed_analysis=data.get("enable_detailed_analysis", True),
            enable_system_metrics=data.get("enable_system_metrics", True),
            enable_third_party_tools=data.get("enable_third_party_tools", True),
            architecture=data.get("architecture", {}),
            code_quality=data.get("code_quality", {}),
            performance=data.get("performance", {}),
            maintainability=data.get("maintainability", {}),
        )
