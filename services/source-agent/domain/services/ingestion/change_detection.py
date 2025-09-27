"""Change detection engine for real-time data source monitoring."""

import hashlib
import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .types import DataSource


@dataclass
class ChangeDetectionEngine:
    """Real-time change detection for data sources."""

    source_checksums: Dict[str, str] = field(default_factory=dict)
    change_patterns: Dict[str, List[Dict[str, Any]]] = field(default_factory=lambda: defaultdict(list))
    detection_rules: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def add_detection_rule(
        self, rule_name: str, source_type: DataSource, conditions: Dict[str, Any]
    ):
        """Add a change detection rule."""
        self.detection_rules[rule_name] = {
            "source_type": source_type,
            "conditions": conditions,
            "created_at": datetime.now(),
            "trigger_count": 0,
        }

    async def detect_changes(
        self, source_id: str, current_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect changes in data source."""
        # Calculate current checksum
        current_checksum = self._calculate_checksum(current_data)

        # Get previous checksum
        previous_checksum = self.source_checksums.get(source_id)

        changes_detected = []
        change_confidence = 0.0

        if previous_checksum != current_checksum:
            # Changes detected
            changes_detected = self._analyze_changes(
                source_id, previous_checksum, current_data
            )

            if changes_detected:
                change_confidence = self._calculate_change_confidence(changes_detected)

                # Update patterns
                self._update_change_patterns(source_id, changes_detected)

        # Update checksum
        self.source_checksums[source_id] = current_checksum

        return {
            "changes_detected": changes_detected,
            "change_confidence": change_confidence,
            "requires_ingestion": change_confidence > 0.5,
            "change_summary": self._summarize_changes(changes_detected),
        }

    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate checksum for data."""
        # Create a normalized string representation
        normalized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(normalized.encode()).hexdigest()

    def _analyze_changes(
        self,
        source_id: str,
        previous_checksum: Optional[str],
        current_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Analyze what changes occurred."""
        changes = []

        # If no previous checksum, consider it a new source
        if not previous_checksum:
            changes.append(
                {
                    "change_type": "new_source",
                    "description": f"New source detected: {source_id}",
                    "severity": "info",
                    "timestamp": datetime.now(),
                    "data_size": len(str(current_data)),
                }
            )
            return changes

        # Analyze different types of changes
        # This is a simplified version - in production would compare with cached previous data

        # Check for size changes (simple heuristic)
        data_size = len(str(current_data))
        if data_size > 1000:  # Arbitrary threshold
            changes.append({
                "change_type": "content_update",
                "description": "Significant content changes detected",
                "severity": "medium",
                "timestamp": datetime.now(),
                "data_size": data_size,
            })

        # Check for structural changes
        if isinstance(current_data, dict):
            if len(current_data) > 10:  # Many fields
                changes.append({
                    "change_type": "structure_update",
                    "description": "Data structure changes detected",
                    "severity": "low",
                    "timestamp": datetime.now(),
                    "field_count": len(current_data),
                })

        return changes

    def _calculate_change_confidence(self, changes: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for detected changes."""
        if not changes:
            return 0.0

        # Base confidence on number and severity of changes
        severity_weights = {
            "low": 0.3,
            "medium": 0.6,
            "high": 0.9,
            "critical": 1.0
        }

        total_confidence = 0.0
        for change in changes:
            severity = change.get("severity", "low")
            weight = severity_weights.get(severity, 0.3)
            total_confidence += weight

        # Normalize by number of changes (more changes = higher confidence)
        avg_confidence = total_confidence / len(changes)

        # Cap at 1.0
        return min(avg_confidence, 1.0)

    def _update_change_patterns(self, source_id: str, changes: List[Dict[str, Any]]):
        """Update change patterns for predictive analysis."""
        pattern_entry = {
            "timestamp": datetime.now(),
            "changes": changes,
            "change_count": len(changes),
            "source_id": source_id,
        }

        self.change_patterns[source_id].append(pattern_entry)

        # Keep only recent patterns (last 100)
        if len(self.change_patterns[source_id]) > 100:
            self.change_patterns[source_id] = self.change_patterns[source_id][-100:]

    def _summarize_changes(self, changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize detected changes."""
        summary = {
            "total_changes": len(changes),
            "change_types": {},
            "severity_breakdown": {},
            "most_common_type": None,
            "highest_severity": "none",
        }

        severity_levels = ["low", "medium", "high", "critical"]

        for change in changes:
            # Count change types
            change_type = change.get("change_type", "unknown")
            summary["change_types"][change_type] = summary["change_types"].get(change_type, 0) + 1

            # Count severities
            severity = change.get("severity", "unknown")
            summary["severity_breakdown"][severity] = summary["severity_breakdown"].get(severity, 0) + 1

            # Track highest severity
            if severity in severity_levels:
                if summary["highest_severity"] == "none" or severity_levels.index(severity) > severity_levels.index(summary["highest_severity"]):
                    summary["highest_severity"] = severity

        # Find most common change type
        if summary["change_types"]:
            summary["most_common_type"] = max(summary["change_types"], key=summary["change_types"].get)

        return summary

    def get_change_patterns(self, source_id: str, days: int = 7) -> Dict[str, Any]:
        """Get change patterns for a source over recent days."""
        cutoff_time = datetime.now() - timedelta(days=days)

        recent_patterns = [
            pattern for pattern in self.change_patterns.get(source_id, [])
            if pattern["timestamp"] > cutoff_time
        ]

        if not recent_patterns:
            return {"pattern": "no_recent_changes"}

        # Analyze patterns
        total_changes = sum(p["change_count"] for p in recent_patterns)
        avg_changes_per_check = total_changes / len(recent_patterns)

        change_frequency = "low"
        if avg_changes_per_check > 5:
            change_frequency = "high"
        elif avg_changes_per_check > 2:
            change_frequency = "medium"

        return {
            "total_checks": len(recent_patterns),
            "total_changes": total_changes,
            "average_changes_per_check": avg_changes_per_check,
            "change_frequency": change_frequency,
            "pattern_period_days": days,
        }

    def predict_next_change(self, source_id: str) -> Dict[str, Any]:
        """Predict when the next change might occur."""
        patterns = self.change_patterns.get(source_id, [])

        if len(patterns) < 3:
            return {"prediction": "insufficient_data"}

        # Simple prediction based on recent patterns
        recent_patterns = patterns[-10:]  # Last 10 checks
        intervals = []

        for i in range(1, len(recent_patterns)):
            interval = recent_patterns[i]["timestamp"] - recent_patterns[i-1]["timestamp"]
            intervals.append(interval.total_seconds())

        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            last_change = recent_patterns[-1]["timestamp"]
            predicted_next = last_change + timedelta(seconds=avg_interval)

            return {
                "prediction": "available",
                "predicted_next_change": predicted_next,
                "confidence": min(len(recent_patterns) / 10.0, 1.0),  # Higher confidence with more data
                "average_interval_hours": avg_interval / 3600,
            }

        return {"prediction": "no_pattern_detected"}

    def get_detection_statistics(self) -> Dict[str, Any]:
        """Get statistics about change detection performance."""
        total_sources = len(self.source_checksums)
        total_patterns = sum(len(patterns) for patterns in self.change_patterns.values())

        return {
            "total_sources_monitored": total_sources,
            "total_change_patterns": total_patterns,
            "average_patterns_per_source": total_patterns / total_sources if total_sources > 0 else 0,
            "detection_rules_count": len(self.detection_rules),
        }
