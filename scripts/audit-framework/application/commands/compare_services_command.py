"""
CompareServicesCommand - Command Object

Represents the user's intention to compare multiple services.
Following CQRS command pattern for clear intent expression.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CompareServicesCommand:
    """Command to compare multiple services.

    This command represents the user's intention to perform
    a comparative analysis of multiple services.
    """

    service_names: List[str]
    profile_name: str = "standard"
    include_trends: bool = False
    output_format: str = "rich"

    def __post_init__(self):
        """Validate command parameters."""
        if not self.service_names:
            raise ValueError("At least one service name is required")

        if len(self.service_names) < 2:
            raise ValueError("At least two services are required for comparison")

        if len(self.service_names) > 10:
            raise ValueError("Cannot compare more than 10 services at once")

        # Validate profile name
        valid_profiles = ["relaxed", "standard", "strict", "ci_fast", "ci_comprehensive"]
        if self.profile_name not in valid_profiles:
            raise ValueError(f"Invalid profile name. Must be one of: {', '.join(valid_profiles)}")

        # Validate output format
        valid_formats = ["rich", "json", "markdown", "table"]
        if self.output_format not in valid_formats:
            raise ValueError(f"Invalid output format. Must be one of: {', '.join(valid_formats)}")

        # Remove duplicates while preserving order
        seen = set()
        unique_names = []
        for name in self.service_names:
            if name not in seen:
                unique_names.append(name)
                seen.add(name)
        self.service_names = unique_names

    def get_service_count(self) -> int:
        """Get the number of services to compare."""
        return len(self.service_names)

    def should_include_trends(self) -> bool:
        """Check if trend analysis should be included."""
        return self.include_trends and len(self.service_names) <= 5  # Trends only for smaller comparisons
