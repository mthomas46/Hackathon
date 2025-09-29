"""Predictive ingestion model for data ingestion optimization."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from .types import DataSource, IngestionPriority


@dataclass
class PredictiveIngestionModel:
    """Predictive model for data ingestion optimization."""

    model_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    data_source: DataSource = DataSource.GITHUB
    prediction_type: str = "usage_pattern"

    # Model parameters
    usage_patterns: Dict[str, Any] = field(default_factory=dict)
    temporal_patterns: Dict[str, Any] = field(default_factory=dict)
    content_patterns: Dict[str, Any] = field(default_factory=dict)

    # Prediction results
    predicted_priority: IngestionPriority = IngestionPriority.MEDIUM
    predicted_frequency: str = "daily"
    predicted_volume: int = 0
    confidence_score: float = 0.0

    # Metadata
    trained_at: datetime = field(default_factory=datetime.now)
    last_prediction: Optional[datetime] = None
    prediction_accuracy: float = 0.0

    def predict_ingestion_parameters(
        self, current_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Predict optimal ingestion parameters based on current data."""
        # Simple prediction logic - in production would use ML models
        predictions = {
            "priority": self._predict_priority(current_data),
            "frequency": self._predict_frequency(current_data),
            "volume": self._predict_volume(current_data),
            "confidence": self.confidence_score,
        }

        self.last_prediction = datetime.now()
        return predictions

    def _predict_priority(self, data: Dict[str, Any]) -> IngestionPriority:
        """Predict ingestion priority."""
        # Check for high-priority indicators
        if data.get("contains_security_issues", False):
            return IngestionPriority.CRITICAL
        elif data.get("is_frequently_accessed", False):
            return IngestionPriority.HIGH
        elif data.get("has_recent_changes", False):
            return IngestionPriority.MEDIUM
        else:
            return IngestionPriority.LOW

    def _predict_frequency(self, data: Dict[str, Any]) -> str:
        """Predict ingestion frequency."""
        change_frequency = data.get("change_frequency", "low")

        if change_frequency == "high":
            return "hourly"
        elif change_frequency == "medium":
            return "daily"
        else:
            return "weekly"

    def _predict_volume(self, data: Dict[str, Any]) -> int:
        """Predict data volume for ingestion."""
        base_volume = data.get("current_size", 1000)

        # Adjust based on patterns
        if self.usage_patterns.get("high_usage_period"):
            base_volume *= 1.5
        if self.content_patterns.get("large_files"):
            base_volume *= 2.0

        return int(base_volume)

    def update_model_accuracy(self, actual_outcome: Dict[str, Any], predicted_outcome: Dict[str, Any]) -> None:
        """Update model accuracy based on actual vs predicted outcomes."""
        # Simple accuracy calculation
        matches = 0
        total_predictions = 0

        for key in ["priority", "frequency", "volume"]:
            if key in actual_outcome and key in predicted_outcome:
                total_predictions += 1
                if actual_outcome[key] == predicted_outcome[key]:
                    matches += 1

        if total_predictions > 0:
            self.prediction_accuracy = matches / total_predictions

    def retrain_model(self, historical_data: List[Dict[str, Any]]) -> None:
        """Retrain the predictive model with historical data."""
        # Analyze patterns from historical data
        self.usage_patterns = self._analyze_usage_patterns(historical_data)
        self.temporal_patterns = self._analyze_temporal_patterns(historical_data)
        self.content_patterns = self._analyze_content_patterns(historical_data)

        # Update confidence based on data quality
        data_quality = len(historical_data) / 100.0  # Simple quality metric
        self.confidence_score = min(data_quality, 1.0)

        self.trained_at = datetime.now()

    def _analyze_usage_patterns(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze usage patterns from historical data."""
        patterns = {
            "peak_hours": [],
            "high_usage_periods": [],
            "access_frequency": {}
        }

        # Simple pattern analysis - would be more sophisticated in production
        for item in data:
            timestamp = item.get("timestamp")
            if timestamp:
                hour = timestamp.hour
                if hour in [9, 10, 11, 14, 15, 16]:  # Business hours
                    patterns["peak_hours"].append(hour)

        if len(patterns["peak_hours"]) > len(data) * 0.3:
            patterns["high_usage_period"] = True

        return patterns

    def _analyze_temporal_patterns(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze temporal patterns from historical data."""
        patterns = {
            "daily_cycles": {},
            "weekly_cycles": {},
            "seasonal_patterns": {}
        }

        # Analyze daily patterns
        for item in data:
            timestamp = item.get("timestamp")
            if timestamp:
                hour = timestamp.hour
                patterns["daily_cycles"][hour] = patterns["daily_cycles"].get(hour, 0) + 1

        return patterns

    def _analyze_content_patterns(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze content patterns from historical data."""
        patterns = {
            "file_types": {},
            "size_distribution": {},
            "content_categories": {},
            "large_files": False
        }

        total_size = 0
        large_files_count = 0

        for item in data:
            file_size = item.get("size", 0)
            total_size += file_size

            if file_size > 1000000:  # 1MB
                large_files_count += 1

            file_type = item.get("file_type", "unknown")
            patterns["file_types"][file_type] = patterns["file_types"].get(file_type, 0) + 1

        if large_files_count > len(data) * 0.1:  # More than 10% are large files
            patterns["large_files"] = True

        return patterns

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "model_id": self.model_id,
            "data_source": self.data_source.value,
            "prediction_type": self.prediction_type,
            "usage_patterns": self.usage_patterns,
            "temporal_patterns": self.temporal_patterns,
            "content_patterns": self.content_patterns,
            "predicted_priority": self.predicted_priority.value,
            "predicted_frequency": self.predicted_frequency,
            "predicted_volume": self.predicted_volume,
            "confidence_score": self.confidence_score,
            "trained_at": self.trained_at.isoformat(),
            "last_prediction": self.last_prediction.isoformat() if self.last_prediction else None,
            "prediction_accuracy": self.prediction_accuracy
        }
