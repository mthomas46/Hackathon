"""Entity type value object."""

from enum import Enum
from typing import Optional, List


class EntityType(Enum):
    """Enumeration of code entity types."""

    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    VARIABLE = "variable"
    CONSTANT = "constant"
    INTERFACE = "interface"
    ENUM = "enum"
    MODULE = "module"
    PACKAGE = "package"

    @classmethod
    def from_string(cls, value: str) -> Optional['EntityType']:
        """Create entity type from string value."""
        try:
            return cls(value.lower())
        except ValueError:
            return None

    def get_display_name(self) -> str:
        """Get human-readable display name."""
        display_names = {
            "function": "Function",
            "class": "Class",
            "method": "Method",
            "variable": "Variable",
            "constant": "Constant",
            "interface": "Interface",
            "enum": "Enumeration",
            "module": "Module",
            "package": "Package",
        }
        return display_names.get(self.value, self.value.title())

    def is_executable(self) -> bool:
        """Check if this entity type represents executable code."""
        return self in [self.FUNCTION, self.METHOD]

    def is_data_container(self) -> bool:
        """Check if this entity type represents a data container."""
        return self in [self.CLASS, self.INTERFACE, self.ENUM]

    def is_definition(self) -> bool:
        """Check if this entity type represents a definition/declaration."""
        return self in [self.VARIABLE, self.CONSTANT]

    def can_have_complexity(self) -> bool:
        """Check if this entity type can have complexity metrics."""
        return self.is_executable() or self == self.CLASS

    def can_have_dependencies(self) -> bool:
        """Check if this entity type can have dependencies."""
        return self in [self.FUNCTION, self.METHOD, self.CLASS, self.MODULE]

    def supports_inheritance(self) -> bool:
        """Check if this entity type supports inheritance."""
        return self in [self.CLASS, self.INTERFACE]

    def get_typical_complexity_range(self) -> tuple[int, int]:
        """Get typical complexity range for this entity type."""
        complexity_ranges = {
            self.FUNCTION: (1, 15),
            self.METHOD: (1, 12),
            self.CLASS: (1, 50),
            self.VARIABLE: (1, 1),     # Variables have minimal complexity
            self.CONSTANT: (1, 1),     # Constants have minimal complexity
            self.INTERFACE: (1, 5),    # Interfaces are typically simple
            self.ENUM: (1, 3),         # Enums are typically simple
            self.MODULE: (1, 30),      # Modules can be complex
            self.PACKAGE: (1, 10),     # Packages are organizational
        }
        return complexity_ranges.get(self, (1, 10))

    def get_recommended_max_complexity(self) -> int:
        """Get recommended maximum complexity for this entity type."""
        max_complexities = {
            self.FUNCTION: 10,
            self.METHOD: 8,
            self.CLASS: 30,
            self.VARIABLE: 1,
            self.CONSTANT: 1,
            self.INTERFACE: 5,
            self.ENUM: 3,
            self.MODULE: 20,
            self.PACKAGE: 10,
        }
        return max_complexities.get(self, 10)

    @classmethod
    def get_executable_types(cls) -> List['EntityType']:
        """Get all executable entity types."""
        return [entity_type for entity_type in cls if entity_type.is_executable()]

    @classmethod
    def get_complexity_supported_types(cls) -> List['EntityType']:
        """Get all entity types that support complexity metrics."""
        return [entity_type for entity_type in cls if entity_type.can_have_complexity()]
