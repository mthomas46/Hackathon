"""
Dependency Resolution Engine
============================

Graph-based dependency management with topological sorting,
circular dependency detection, and critical path analysis.

REFACTORED: Simplified cycle detection to avoid hanging issues.
"""

from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque

from ..entities.feature import Feature
from ..entities.task import Task


class DependencyType(Enum):
    """Type of dependency relationship."""
    FINISH_TO_START = "finish_to_start"
    START_TO_START = "start_to_start"
    FINISH_TO_FINISH = "finish_to_finish"
    START_TO_FINISH = "start_to_finish"


@dataclass
class DependencyEdge:
    """Edge in dependency graph."""
    from_id: str
    to_id: str
    dependency_type: DependencyType = DependencyType.FINISH_TO_START
    lag_days: int = 0


@dataclass
class DependencyNode:
    """Node in dependency graph."""
    id: str
    title: str
    estimated_effort: float
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    level: int = 0


@dataclass
class DependencyGraph:
    """Dependency graph structure."""
    nodes: Dict[str, DependencyNode] = field(default_factory=dict)
    edges: List[DependencyEdge] = field(default_factory=list)
    
    def add_node(self, node: DependencyNode) -> None:
        """Add node to graph."""
        self.nodes[node.id] = node
    
    def add_edge(self, edge: DependencyEdge) -> None:
        """Add edge to graph."""
        self.edges.append(edge)
        
        # Update node connections
        if edge.from_id in self.nodes and edge.to_id in self.nodes:
            if edge.to_id not in self.nodes[edge.from_id].dependents:
                self.nodes[edge.from_id].dependents.append(edge.to_id)
            if edge.from_id not in self.nodes[edge.to_id].dependencies:
                self.nodes[edge.to_id].dependencies.append(edge.from_id)
    
    def get_node(self, node_id: str) -> Optional[DependencyNode]:
        """Get node by ID."""
        return self.nodes.get(node_id)
    
    def get_dependencies(self, node_id: str) -> List[str]:
        """Get all dependencies for a node."""
        node = self.get_node(node_id)
        return node.dependencies.copy() if node else []
    
    def get_dependents(self, node_id: str) -> List[str]:
        """Get all dependents for a node."""
        node = self.get_node(node_id)
        return node.dependents.copy() if node else []
    
    def node_count(self) -> int:
        """Get total number of nodes."""
        return len(self.nodes)
    
    def edge_count(self) -> int:
        """Get total number of edges."""
        return len(self.edges)


@dataclass
class DependencyAnalysisResult:
    """Result of dependency analysis."""
    graph: DependencyGraph
    sorted_order: List[str]
    circular_dependencies: List[List[str]]
    critical_path: List[str]
    critical_path_duration: float
    parallel_tracks: List[List[str]]
    bottlenecks: List[DependencyNode]
    independent_nodes: List[str]
    is_valid: bool
    warnings: List[str] = field(default_factory=list)
    
    def has_cycles(self) -> bool:
        """Check if there are circular dependencies."""
        return len(self.circular_dependencies) > 0


class DependencyResolver:
    """
    Dependency resolution and analysis engine.
    
    Features:
    - Topological sorting (Kahn's algorithm)
    - Cycle detection (simple and efficient)
    - Critical path analysis
    - Parallel track identification
    - Bottleneck detection
    """
    
    def __init__(self):
        """Initialize dependency resolver."""
        pass
    
    def analyze_dependencies(
        self,
        features: List[Feature],
        tasks: Optional[List[Task]] = None
    ) -> DependencyAnalysisResult:
        """
        Analyze dependencies between features and tasks.
        
        Args:
            features: List of features with dependencies
            tasks: Optional list of tasks with dependencies
            
        Returns:
            DependencyAnalysisResult with analysis results
        """
        # Build dependency graph
        graph = self._build_graph(features, tasks)
        
        # Detect circular dependencies FIRST (before topological sort)
        circular_deps = self._detect_cycles_simple(graph)
        
        # Perform topological sort (will be empty if cycles exist)
        sorted_order = self._topological_sort(graph) if not circular_deps else []
        
        # Calculate critical path
        critical_path, critical_duration = self._calculate_critical_path(graph, sorted_order)
        
        # Identify parallel tracks
        parallel_tracks = self._identify_parallel_tracks(graph, sorted_order)
        
        # Find bottlenecks
        bottlenecks = self._find_bottlenecks(graph)
        
        # Find independent nodes
        independent_nodes = self._find_independent_nodes(graph)
        
        # Generate warnings
        warnings = self._generate_warnings(graph, circular_deps, bottlenecks)
        
        return DependencyAnalysisResult(
            graph=graph,
            sorted_order=sorted_order,
            circular_dependencies=circular_deps,
            critical_path=critical_path,
            critical_path_duration=critical_duration,
            parallel_tracks=parallel_tracks,
            bottlenecks=bottlenecks,
            independent_nodes=independent_nodes,
            is_valid=len(circular_deps) == 0,
            warnings=warnings
        )
    
    def _build_graph(
        self,
        features: List[Feature],
        tasks: Optional[List[Task]]
    ) -> DependencyGraph:
        """Build dependency graph from features and tasks."""
        graph = DependencyGraph()
        
        # Add features as nodes
        for feature in features:
            node = DependencyNode(
                id=feature.id,
                title=feature.title,
                estimated_effort=feature.estimated_effort if feature.estimated_effort else 0.0,
                dependencies=feature.dependencies.copy() if feature.dependencies else []
            )
            graph.add_node(node)
        
        # Add tasks as nodes if provided
        if tasks:
            for task in tasks:
                node = DependencyNode(
                    id=task.id,
                    title=task.title,
                    estimated_effort=task.estimated_hours / 8.0 if task.estimated_hours else 0.0,
                    dependencies=task.dependencies.copy() if task.dependencies else []
                )
                graph.add_node(node)
        
        # Create edges from dependencies
        for node in graph.nodes.values():
            for dep_id in node.dependencies:
                if dep_id in graph.nodes:
                    edge = DependencyEdge(from_id=dep_id, to_id=node.id)
                    graph.add_edge(edge)
        
        return graph
    
    def _detect_cycles_simple(self, graph: DependencyGraph) -> List[List[str]]:
        """
        Detect cycles using a simple iterative approach.
        
        This uses Kahn's algorithm logic: if we can't process all nodes,
        the remaining nodes form cycles.
        
        Returns list of cycles (simplified - returns nodes involved in cycles).
        """
        if not graph.nodes:
            return []
        
        # Build in-degree map
        in_degree = {node_id: 0 for node_id in graph.nodes}
        
        # Count incoming edges for each node
        for node_id, node in graph.nodes.items():
            for dep_id in node.dependencies:
                if dep_id in graph.nodes:
                    in_degree[node_id] += 1
        
        # Start with nodes that have no dependencies
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        processed = []
        
        # Process nodes in order
        while queue:
            current = queue.popleft()
            processed.append(current)
            
            # For each dependent of current node
            node = graph.get_node(current)
            if node:
                for dependent_id in node.dependents:
                    if dependent_id in in_degree:
                        in_degree[dependent_id] -= 1
                        if in_degree[dependent_id] == 0:
                            queue.append(dependent_id)
        
        # If we didn't process all nodes, remaining ones are in cycles
        if len(processed) < len(graph.nodes):
            cycle_nodes = [nid for nid in graph.nodes if nid not in processed]
            return [cycle_nodes]
        
        return []
    
    def _topological_sort(self, graph: DependencyGraph) -> List[str]:
        """
        Perform topological sort using Kahn's algorithm.
        
        Returns sorted list of node IDs.
        """
        if not graph.nodes:
            return []
        
        # Build in-degree map
        in_degree = {node_id: 0 for node_id in graph.nodes}
        
        for node_id, node in graph.nodes.items():
            for dep_id in node.dependencies:
                if dep_id in graph.nodes:
                    in_degree[node_id] += 1
        
        # Start with nodes that have no dependencies
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        sorted_order = []
        
        while queue:
            current = queue.popleft()
            sorted_order.append(current)
            
            # Update dependents
            node = graph.get_node(current)
            if node:
                for dependent_id in node.dependents:
                    if dependent_id in in_degree:
                        in_degree[dependent_id] -= 1
                        if in_degree[dependent_id] == 0:
                            queue.append(dependent_id)
        
        return sorted_order
    
    def _calculate_critical_path(
        self,
        graph: DependencyGraph,
        sorted_order: List[str]
    ) -> Tuple[List[str], float]:
        """
        Calculate critical path using longest path algorithm.
        
        Returns tuple of (critical_path, duration).
        """
        if not sorted_order:
            return [], 0.0
        
        # Calculate earliest start times
        earliest_start = {node_id: 0.0 for node_id in graph.nodes}
        
        for node_id in sorted_order:
            node = graph.get_node(node_id)
            if not node:
                continue
            
            # Calculate earliest start based on dependencies
            for dep_id in node.dependencies:
                if dep_id in graph.nodes:
                    dep_node = graph.get_node(dep_id)
                    if dep_node:
                        finish_time = earliest_start[dep_id] + dep_node.estimated_effort
                        earliest_start[node_id] = max(earliest_start[node_id], finish_time)
        
        # Find node with latest finish time
        latest_finish = 0.0
        end_node = None
        
        for node_id in sorted_order:
            node = graph.get_node(node_id)
            if node:
                finish = earliest_start[node_id] + node.estimated_effort
                if finish > latest_finish:
                    latest_finish = finish
                    end_node = node_id
        
        # Trace back critical path
        if not end_node:
            return [], 0.0
        
        critical_path = self._trace_critical_path(graph, end_node, earliest_start)
        
        return critical_path, latest_finish
    
    def _trace_critical_path(
        self,
        graph: DependencyGraph,
        end_node: str,
        earliest_start: Dict[str, float]
    ) -> List[str]:
        """Trace critical path backwards from end node."""
        path = [end_node]
        current = end_node
        
        while True:
            node = graph.get_node(current)
            if not node or not node.dependencies:
                break
            
            # Find predecessor on critical path
            current_start = earliest_start[current]
            critical_pred = None
            
            for dep_id in node.dependencies:
                if dep_id not in graph.nodes:
                    continue
                dep_node = graph.get_node(dep_id)
                if not dep_node:
                    continue
                
                # Check if this dependency is on critical path
                if earliest_start[dep_id] + dep_node.estimated_effort == current_start:
                    critical_pred = dep_id
                    break
            
            if not critical_pred:
                break
            
            path.insert(0, critical_pred)
            current = critical_pred
        
        return path
    
    def _identify_parallel_tracks(
        self,
        graph: DependencyGraph,
        sorted_order: List[str]
    ) -> List[List[str]]:
        """Identify independent parallel tracks of work."""
        if not sorted_order:
            return []
        
        # Find root nodes (no dependencies)
        roots = [nid for nid in graph.nodes if not graph.get_node(nid).dependencies]
        
        # Trace each root to find its track
        tracks = []
        visited = set()
        
        for root in roots:
            if root in visited:
                continue
            
            track = self._trace_dependency_tree(graph, root, visited)
            if track:
                tracks.append(track)
        
        return tracks
    
    def _trace_dependency_tree(
        self,
        graph: DependencyGraph,
        root: str,
        visited: Set[str]
    ) -> List[str]:
        """Trace all nodes reachable from root."""
        track = []
        queue = deque([root])
        
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            
            visited.add(current)
            track.append(current)
            
            node = graph.get_node(current)
            if node:
                for dependent in node.dependents:
                    if dependent not in visited:
                        queue.append(dependent)
        
        return track
    
    def _find_bottlenecks(self, graph: DependencyGraph) -> List[DependencyNode]:
        """Find nodes that are dependencies for many other nodes."""
        bottleneck_threshold = 2  # Node with 2+ dependents is a bottleneck
        
        bottlenecks = []
        for node in graph.nodes.values():
            if len(node.dependents) >= bottleneck_threshold:
                bottlenecks.append(node)
        
        # Sort by number of dependents (descending)
        bottlenecks.sort(key=lambda n: len(n.dependents), reverse=True)
        
        return bottlenecks
    
    def _find_independent_nodes(self, graph: DependencyGraph) -> List[str]:
        """Find nodes with no dependencies."""
        return [
            node.id for node in graph.nodes.values()
            if not node.dependencies
        ]
    
    def _generate_warnings(
        self,
        graph: DependencyGraph,
        circular_deps: List[List[str]],
        bottlenecks: List[DependencyNode]
    ) -> List[str]:
        """Generate warnings based on analysis."""
        warnings = []
        
        if circular_deps:
            warnings.append(
                f"Found {len(circular_deps)} circular dependency cycle(s). "
                "These must be resolved before scheduling."
            )
            for i, cycle in enumerate(circular_deps, 1):
                warnings.append(f"Cycle {i}: {', '.join(cycle[:5])}")
        
        if bottlenecks:
            top_bottlenecks = bottlenecks[:3]
            warnings.append(
                f"Found {len(bottlenecks)} bottleneck(s). "
                f"Top: {', '.join([b.title for b in top_bottlenecks])}"
            )
        
        if not graph.nodes:
            warnings.append("No dependencies to analyze")
        
        return warnings
    
    def validate_dependency(
        self,
        from_feature: Feature,
        to_feature: Feature,
        all_features: List[Feature]
    ) -> Tuple[bool, str]:
        """
        Validate if adding a dependency would create a cycle.
        
        Args:
            from_feature: The feature that will be depended upon
            to_feature: The feature that will depend on from_feature
            all_features: All features in the project
        
        Returns tuple of (is_valid, message).
        """
        # Check if features exist
        feature_ids = {f.id for f in all_features}
        if from_feature.id not in feature_ids or to_feature.id not in feature_ids:
            return False, "One or both features do not exist"
        
        # Temporarily add the dependency and check for cycles
        temp_features = []
        for f in all_features:
            if f.id == to_feature.id:
                # Add the new dependency
                new_deps = f.dependencies.copy() if f.dependencies else []
                if from_feature.id not in new_deps:
                    new_deps.append(from_feature.id)
                temp_f = Feature(f.id, f.title, f.description, dependencies=new_deps)
                temp_features.append(temp_f)
            else:
                temp_features.append(f)
        
        # Analyze with new dependency
        result = self.analyze_dependencies(temp_features)
        
        if result.has_cycles():
            return False, "Adding this dependency would create a circular dependency"
        
        return True, "Dependency is valid"
    
    def suggest_dependency_order(self, features: List[Feature]) -> List[str]:
        """
        Suggest optimal order for implementing features based on dependencies.
        
        Returns list of feature IDs in suggested order, or empty list if cycles exist.
        """
        result = self.analyze_dependencies(features)
        
        if result.has_cycles():
            return []  # Cannot suggest order with cycles
        
        return result.sorted_order
