# ============================================================================
# ARCHITECTURE ANALYZER MODULE
# ============================================================================
"""
Architecture diagram analysis module for the analysis-service.

Provides specialized analysis capabilities for architectural diagrams,
including consistency checks, completeness validation, and best practice
recommendations based on normalized architecture data.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class AnalysisType(Enum):
    """Types of architecture analysis available."""
    CONSISTENCY = "consistency"
    COMPLETENESS = "completeness"
    BEST_PRACTICES = "best_practices"
    COMBINED = "combined"


class IssueSeverity(Enum):
    """Severity levels for architecture issues."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ArchitectureIssue:
    """Represents an issue found in architecture analysis."""
    issue_type: str
    severity: IssueSeverity
    component_id: Optional[str]
    message: str
    recommendation: str
    metadata: Optional[Dict[str, Any]] = None


class ArchitectureAnalyzer:
    """Analyzer for architectural diagrams and system designs."""

    def __init__(self):
        self.analyzers = {
            AnalysisType.CONSISTENCY: self._analyze_consistency,
            AnalysisType.COMPLETENESS: self._analyze_completeness,
            AnalysisType.BEST_PRACTICES: self._analyze_best_practices,
        }

    async def analyze_architecture(
        self,
        components: List[Dict[str, Any]],
        connections: List[Dict[str, Any]],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze architectural components and connections.

        Args:
            components: List of architecture components
            connections: List of connections between components
            options: Analysis options (analysis_type, etc.)

        Returns:
            Analysis results with issues and recommendations
        """
        options = options or {}
        analysis_type = AnalysisType(options.get("analysis_type", "combined"))

        if analysis_type == AnalysisType.COMBINED:
            # Run all analyses
            results = {}
            all_issues = []

            for analyzer_type, analyzer_func in self.analyzers.items():
                analysis_result = await analyzer_func(components, connections, options)
                results[analyzer_type.value] = analysis_result
                all_issues.extend(analysis_result.get("issues", []))

            # Combine results
            return {
                "success": True,
                "analysis_type": "combined",
                "component_count": len(components),
                "connection_count": len(connections),
                "issues": all_issues,
                "issue_count": len(all_issues),
                "severity_counts": self._count_severities(all_issues),
                "results": results
            }
        else:
            # Run specific analysis
            analyzer_func = self.analyzers.get(analysis_type)
            if not analyzer_func:
                raise ValueError(f"Unsupported analysis type: {analysis_type}")

            result = await analyzer_func(components, connections, options)
            return {
                "success": True,
                "analysis_type": analysis_type.value,
                "component_count": len(components),
                "connection_count": len(connections),
                **result
            }

    async def _analyze_consistency(
        self,
        components: List[Dict[str, Any]],
        connections: List[Dict[str, Any]],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze consistency of the architecture."""
        issues = []

        # Check for orphaned connections (connections to non-existent components)
        component_ids = {comp.get("id") for comp in components}

        for conn in connections:
            from_id = conn.get("from_id")
            to_id = conn.get("to_id")

            if from_id not in component_ids:
                issues.append(ArchitectureIssue(
                    issue_type="orphaned_connection",
                    severity=IssueSeverity.CRITICAL,
                    component_id=None,
                    message=f"Connection references non-existent source component: {from_id}",
                    recommendation="Remove or correct the connection",
                    metadata={"connection": conn}
                ))

            if to_id not in component_ids:
                issues.append(ArchitectureIssue(
                    issue_type="orphaned_connection",
                    severity=IssueSeverity.CRITICAL,
                    component_id=None,
                    message=f"Connection references non-existent target component: {to_id}",
                    recommendation="Remove or correct the connection",
                    metadata={"connection": conn}
                ))

        # Check for duplicate component IDs
        seen_ids = set()
        for comp in components:
            comp_id = comp.get("id")
            if comp_id in seen_ids:
                issues.append(ArchitectureIssue(
                    issue_type="duplicate_component",
                    severity=IssueSeverity.HIGH,
                    component_id=comp_id,
                    message=f"Duplicate component ID found: {comp_id}",
                    recommendation="Ensure all component IDs are unique",
                    metadata={"component": comp}
                ))
            seen_ids.add(comp_id)

        return {
            "issues": issues,
            "issue_count": len(issues),
            "severity_counts": self._count_severities(issues)
        }

    async def _analyze_completeness(
        self,
        components: List[Dict[str, Any]],
        connections: List[Dict[str, Any]],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze completeness of the architecture."""
        issues = []

        # Check for components without descriptions
        for comp in components:
            if not comp.get("description") or comp.get("description").strip() == "":
                issues.append(ArchitectureIssue(
                    issue_type="missing_description",
                    severity=IssueSeverity.MEDIUM,
                    component_id=comp.get("id"),
                    message=f"Component '{comp.get('name', comp.get('id'))}' has no description",
                    recommendation="Add a clear description of the component's purpose and functionality",
                    metadata={"component": comp}
                ))

        # Check for components without types
        for comp in components:
            if not comp.get("type"):
                issues.append(ArchitectureIssue(
                    issue_type="missing_type",
                    severity=IssueSeverity.MEDIUM,
                    component_id=comp.get("id"),
                    message=f"Component '{comp.get('name', comp.get('id'))}' has no type specified",
                    recommendation="Specify the component type (service, database, API, etc.)",
                    metadata={"component": comp}
                ))

        # Check for isolated components (no connections)
        connected_component_ids = set()
        for conn in connections:
            connected_component_ids.add(conn.get("from_id"))
            connected_component_ids.add(conn.get("to_id"))

        for comp in components:
            comp_id = comp.get("id")
            if comp_id not in connected_component_ids:
                issues.append(ArchitectureIssue(
                    issue_type="isolated_component",
                    severity=IssueSeverity.LOW,
                    component_id=comp_id,
                    message=f"Component '{comp.get('name', comp_id)}' has no connections",
                    recommendation="Consider if this component should be connected to others or if it can be removed",
                    metadata={"component": comp}
                ))

        return {
            "issues": issues,
            "issue_count": len(issues),
            "severity_counts": self._count_severities(issues)
        }

    async def _analyze_best_practices(
        self,
        components: List[Dict[str, Any]],
        connections: List[Dict[str, Any]],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze architecture against best practices."""
        issues = []

        # Check for circular dependencies (simplified check)
        # This is a basic implementation - more sophisticated analysis would be needed
        component_map = {comp.get("id"): comp for comp in components}
        connection_map = {}

        for conn in connections:
            from_id = conn.get("from_id")
            if from_id not in connection_map:
                connection_map[from_id] = []
            connection_map[from_id].append(conn.get("to_id"))

        # Simple cycle detection (basic implementation)
        visited = set()
        rec_stack = set()

        def has_cycle(node_id):
            visited.add(node_id)
            rec_stack.add(node_id)

            for neighbor in connection_map.get(node_id, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node_id)
            return False

        for comp_id in component_map.keys():
            if comp_id not in visited:
                if has_cycle(comp_id):
                    issues.append(ArchitectureIssue(
                        issue_type="circular_dependency",
                        severity=IssueSeverity.HIGH,
                        component_id=None,
                        message="Potential circular dependency detected in architecture",
                        recommendation="Review component dependencies to eliminate circular references",
                        metadata={"starting_component": comp_id}
                    ))
                    break  # Only report once

        # Check for components with too many connections (high coupling)
        max_connections = options.get("max_connections_per_component", 10)
        for comp_id, targets in connection_map.items():
            if len(targets) > max_connections:
                comp = component_map.get(comp_id, {})
                issues.append(ArchitectureIssue(
                    issue_type="high_coupling",
                    severity=IssueSeverity.MEDIUM,
                    component_id=comp_id,
                    message=f"Component '{comp.get('name', comp_id)}' has {len(targets)} connections (threshold: {max_connections})",
                    recommendation="Consider breaking down this component or introducing intermediaries",
                    metadata={"component": comp, "connection_count": len(targets)}
                ))

        return {
            "issues": issues,
            "issue_count": len(issues),
            "severity_counts": self._count_severities(issues)
        }

    def _count_severities(self, issues: List[ArchitectureIssue]) -> Dict[str, int]:
        """Count issues by severity level."""
        counts = {severity.value: 0 for severity in IssueSeverity}
        for issue in issues:
            counts[issue.severity.value] += 1
        return counts
