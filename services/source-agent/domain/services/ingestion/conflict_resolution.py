"""Conflict resolution engine for multi-source data ingestion."""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .types import ConflictResolutionStrategy


@dataclass
class ConflictResolutionEngine:
    """Advanced conflict resolution for multi-source data ingestion."""

    resolution_rules: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    conflict_history: List[Dict[str, Any]] = field(default_factory=list)

    def add_resolution_rule(
        self,
        rule_name: str,
        conditions: Dict[str, Any],
        strategy: ConflictResolutionStrategy,
    ):
        """Add a conflict resolution rule."""
        self.resolution_rules[rule_name] = {
            "conditions": conditions,
            "strategy": strategy,
            "created_at": datetime.now(),
            "usage_count": 0,
            "success_rate": 0.0,
        }

    async def resolve_conflict(
        self, conflicting_records: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve conflicts between multiple data records."""
        start_time = time.time()

        # Analyze conflict
        conflict_analysis = self._analyze_conflict(conflicting_records)

        # Select resolution strategy
        strategy = self._select_resolution_strategy(conflict_analysis, context)

        # Apply resolution
        resolved_record = await self._apply_resolution_strategy(
            conflicting_records, strategy, context
        )

        # Record resolution
        resolution_record = {
            "conflict_id": str(uuid.uuid4()),
            "conflicting_records": len(conflicting_records),
            "strategy_used": strategy.value,
            "resolution_time": time.time() - start_time,
            "resolved_at": datetime.now(),
            "conflict_analysis": conflict_analysis,
        }

        self.conflict_history.append(resolution_record)

        # Update rule statistics
        rule_name = self._find_matching_rule(conflict_analysis)
        if rule_name:
            rule = self.resolution_rules[rule_name]
            rule["usage_count"] += 1
            # Update success rate based on resolution quality

        return {
            "resolved_record": resolved_record,
            "strategy_used": strategy.value,
            "confidence": self._calculate_resolution_confidence(
                conflicting_records, resolved_record
            ),
            "analysis": conflict_analysis,
        }

    def _analyze_conflict(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the nature of the conflict."""
        analysis = {
            "conflict_type": "unknown",
            "differing_fields": [],
            "record_count": len(records),
            "sources_involved": set(),
            "temporal_span": 0,
            "data_types": set(),
        }

        if len(records) < 2:
            analysis["conflict_type"] = "no_conflict"
            return analysis

        # Find differing fields
        first_record = records[0]
        for field in first_record.keys():
            values = [r.get(field) for r in records]
            if len(set(str(v) for v in values)) > 1:  # Different values
                analysis["differing_fields"].append(field)

        # Analyze sources
        for record in records:
            source = record.get("source", record.get("data_source", "unknown"))
            analysis["sources_involved"].add(source)

        # Analyze timestamps
        timestamps = []
        for record in records:
            ts = record.get("timestamp") or record.get("updated_at") or record.get("created_at")
            if ts:
                if isinstance(ts, str):
                    try:
                        ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    except:
                        continue
                timestamps.append(ts)

        if len(timestamps) >= 2:
            analysis["temporal_span"] = max(timestamps) - min(timestamps)

        # Determine conflict type
        if len(analysis["differing_fields"]) == 0:
            analysis["conflict_type"] = "duplicate"
        elif "version" in analysis["differing_fields"] or "updated_at" in analysis["differing_fields"]:
            analysis["conflict_type"] = "version_conflict"
        elif "status" in analysis["differing_fields"]:
            analysis["conflict_type"] = "status_conflict"
        else:
            analysis["conflict_type"] = "content_conflict"

        return analysis

    def _select_resolution_strategy(
        self, analysis: Dict[str, Any], context: Dict[str, Any]
    ) -> ConflictResolutionStrategy:
        """Select the appropriate resolution strategy."""
        # Check for matching rules
        rule_name = self._find_matching_rule(analysis)
        if rule_name:
            return self.resolution_rules[rule_name]["strategy"]

        # Default strategy selection based on conflict type
        conflict_type = analysis.get("conflict_type", "unknown")

        if conflict_type == "version_conflict":
            return ConflictResolutionStrategy.LATEST_WINS
        elif conflict_type == "status_conflict":
            return ConflictResolutionStrategy.SOURCE_PRIORITY
        elif conflict_type == "duplicate":
            return ConflictResolutionStrategy.MERGE
        else:
            return ConflictResolutionStrategy.LATEST_WINS

    async def _apply_resolution_strategy(
        self,
        records: List[Dict[str, Any]],
        strategy: ConflictResolutionStrategy,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply the selected resolution strategy."""
        if strategy == ConflictResolutionStrategy.LATEST_WINS:
            return self._resolve_latest_wins(records)
        elif strategy == ConflictResolutionStrategy.OLDEST_WINS:
            return self._resolve_oldest_wins(records)
        elif strategy == ConflictResolutionStrategy.MERGE:
            return await self._resolve_merge(records, context)
        elif strategy == ConflictResolutionStrategy.SOURCE_PRIORITY:
            return self._resolve_source_priority(records, context)
        else:  # MANUAL
            return self._resolve_manual(records, context)

    def _resolve_latest_wins(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Resolve by selecting the most recent record."""
        # Sort by timestamp (most recent first)
        sorted_records = sorted(
            records,
            key=lambda r: r.get("updated_at") or r.get("timestamp") or r.get("created_at", ""),
            reverse=True
        )
        return sorted_records[0].copy()

    def _resolve_oldest_wins(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Resolve by selecting the oldest record."""
        # Sort by timestamp (oldest first)
        sorted_records = sorted(
            records,
            key=lambda r: r.get("updated_at") or r.get("timestamp") or r.get("created_at", "")
        )
        return sorted_records[0].copy()

    async def _resolve_merge(
        self, records: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve by merging conflicting records."""
        merged = {}

        # Start with the most complete record
        base_record = max(records, key=lambda r: len(r))

        # Merge all records
        for record in records:
            for key, value in record.items():
                if key not in merged:
                    merged[key] = value
                elif isinstance(merged[key], list) and isinstance(value, list):
                    # Merge lists
                    merged[key] = list(set(merged[key] + value))
                elif isinstance(merged[key], dict) and isinstance(value, dict):
                    # Merge dicts
                    merged[key] = {**merged[key], **value}
                # For conflicting scalar values, keep the base record's value

        # Add merge metadata
        merged["_merge_info"] = {
            "merged_records": len(records),
            "merged_at": datetime.now().isoformat(),
            "strategy": "merge"
        }

        return merged

    def _resolve_source_priority(
        self, records: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve based on source priority."""
        source_priority = context.get("source_priority", {})

        # Sort records by source priority
        def get_priority(record):
            source = record.get("source") or record.get("data_source", "unknown")
            return source_priority.get(source, 0)

        sorted_records = sorted(records, key=get_priority, reverse=True)
        return sorted_records[0].copy()

    def _resolve_manual(
        self, records: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Manual resolution - flag for human intervention."""
        return {
            "resolution_status": "manual_intervention_required",
            "conflicting_records": records,
            "flagged_at": datetime.now().isoformat(),
            "reason": "Manual resolution strategy selected"
        }

    def _find_matching_rule(self, analysis: Dict[str, Any]) -> Optional[str]:
        """Find a matching resolution rule."""
        for rule_name, rule in self.resolution_rules.items():
            conditions = rule["conditions"]

            # Check if conditions match analysis
            matches = True
            for key, value in conditions.items():
                if analysis.get(key) != value:
                    matches = False
                    break

            if matches:
                return rule_name

        return None

    def _calculate_resolution_confidence(
        self, original_records: List[Dict[str, Any]], resolved_record: Dict[str, Any]
    ) -> float:
        """Calculate confidence in the resolution."""
        if not original_records:
            return 0.0

        # Simple confidence based on data completeness
        total_fields = len(set().union(*[set(r.keys()) for r in original_records]))
        resolved_fields = len(resolved_record.keys())

        field_coverage = resolved_fields / total_fields if total_fields > 0 else 0

        # Adjust based on resolution strategy success history
        strategy_adjustment = 0.1  # Would be calculated from historical success rates

        return min(field_coverage + strategy_adjustment, 1.0)

    def get_resolution_statistics(self) -> Dict[str, Any]:
        """Get statistics about conflict resolution performance."""
        total_conflicts = len(self.conflict_history)

        if total_conflicts == 0:
            return {"total_conflicts": 0}

        strategy_counts = {}
        avg_resolution_time = 0

        for conflict in self.conflict_history:
            strategy = conflict.get("strategy_used", "unknown")
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
            avg_resolution_time += conflict.get("resolution_time", 0)

        avg_resolution_time /= total_conflicts

        return {
            "total_conflicts": total_conflicts,
            "strategy_distribution": strategy_counts,
            "average_resolution_time": avg_resolution_time,
            "most_used_strategy": max(strategy_counts, key=strategy_counts.get) if strategy_counts else None
        }
