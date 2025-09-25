"""
AuditServiceCommand - Command Object

Represents the user's intention to audit a specific service.
Following CQRS command pattern for clear intent expression.
"""

from dataclasses import dataclass
from typing import Optional

from domain.value_objects.audit_profile import AuditProfile


@dataclass
class AuditServiceCommand:
    """Command to audit a specific service.

    This command represents the user's intention to perform
    a complete audit of a service using specified parameters.
    """

    service_name: str
    service_path: Optional[str] = None
    profile_name: str = "standard"
    enable_detailed_analysis: bool = True
    timeout_seconds: Optional[int] = None

    def __post_init__(self):
        """Validate command parameters."""
        if not self.service_name:
            raise ValueError("Service name is required")

        if len(self.service_name.strip()) == 0:
            raise ValueError("Service name cannot be empty")

        # Validate profile name
        valid_profiles = ["relaxed", "standard", "strict", "ci_fast", "ci_comprehensive"]
        if self.profile_name not in valid_profiles:
            raise ValueError(f"Invalid profile name. Must be one of: {', '.join(valid_profiles)}")

        if self.timeout_seconds is not None and self.timeout_seconds <= 0:
            raise ValueError("Timeout must be a positive number")

    def to_audit_profile(self) -> AuditProfile:
        """Convert command to audit profile.

        Returns:
            AuditProfile instance based on command parameters
        """
        from ...domain.value_objects.audit_profile import AuditIntensity

        # Map profile name to intensity
        intensity_map = {
            "relaxed": AuditIntensity.RELAXED,
            "standard": AuditIntensity.STANDARD,
            "strict": AuditIntensity.STRICT,
            "ci_fast": AuditIntensity.CI_FAST,
            "ci_comprehensive": AuditIntensity.STRICT,  # Comprehensive uses strict settings
        }

        intensity = intensity_map.get(self.profile_name, AuditIntensity.STANDARD)

        # Create profile with command parameters
        return AuditProfile(
            name=self.profile_name,
            intensity=intensity,
            description=f"Audit profile for {self.service_name}",
            enable_detailed_analysis=self.enable_detailed_analysis,
        )

    def should_enable_third_party_tools(self) -> bool:
        """Determine if third-party tools should be enabled."""
        # Disable for fast profiles to improve performance
        return self.profile_name not in ["ci_fast"]

    def get_timeout_seconds(self) -> int:
        """Get timeout for this command."""
        return self.timeout_seconds or 300  # Default 5 minutes
