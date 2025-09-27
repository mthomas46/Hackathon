"""Configuration domain entity."""

from typing import Dict, Any
from dataclasses import dataclass, field

from services.shared.domain import BaseEntity


@dataclass
class Configuration(BaseEntity):
    """Domain entity representing system configuration."""

    id: str
    name: str
    category: str
    settings: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    version: str = "1.0.0"

    def __post_init__(self):
        """Post initialization validation."""
        if not self.id:
            raise ValueError("Configuration ID cannot be empty")
        if not self.name:
            raise ValueError("Configuration name cannot be empty")

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting."""
        return self.settings.get(key, default)

    def set_setting(self, key: str, value: Any) -> None:
        """Set a configuration setting."""
        self.settings[key] = value
        self.updated_at = None  # Will be set by base entity

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "settings": self.settings,
            "is_active": self.is_active,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
