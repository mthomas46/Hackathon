"""Analytics Result domain entity."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from services.shared.domain import BaseEntity


class AnalyticsType(Enum):
    """Analytics type enumeration."""
    DESCRIPTIVE = "descriptive"
    DIAGNOSTIC = "diagnostic"
    PREDICTIVE = "predictive"
    PRESCRIPTIVE = "prescriptive"
    CAUSAL = "causal"


@dataclass
class AnalyticsResult(BaseEntity):
    """Domain entity representing analytics results."""

    id: str
    analytics_type: AnalyticsType = AnalyticsType.DESCRIPTIVE
    simulation_id: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    visualizations: List[Dict[str, Any]] = field(default_factory=list)
    insights_generated: int = 0
    processing_time_seconds: float = 0.0
    status: str = "completed"
    error_message: Optional[str] = None

    def __post_init__(self):
        """Post initialization validation."""
        if not self.id:
            raise ValueError("Analytics Result ID cannot be empty")

    def add_visualization(self, viz_type: str, data: Dict[str, Any]) -> None:
        """Add a visualization."""
        self.visualizations.append({
            "type": viz_type,
            "data": data,
            "created_at": datetime.utcnow().isoformat()
        })
        self.updated_at = datetime.utcnow()

    def update_results(self, new_results: Dict[str, Any]) -> None:
        """Update analytics results."""
        self.results.update(new_results)
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert analytics result to dictionary."""
        return {
            "id": self.id,
            "analytics_type": self.analytics_type.value,
            "simulation_id": self.simulation_id,
            "parameters": self.parameters,
            "results": self.results,
            "visualizations": self.visualizations,
            "insights_generated": self.insights_generated,
            "processing_time_seconds": self.processing_time_seconds,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
