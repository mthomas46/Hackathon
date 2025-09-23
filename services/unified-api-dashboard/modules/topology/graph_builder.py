"""
Dependency Graph Builder

Advanced dependency graph construction and manipulation utilities
for service topology analysis and visualization.
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict, deque
import networkx as nx
from dataclasses import dataclass

from .analyzer import TopologyAnalysis, ServiceNode, ServiceRelationship


@dataclass
class GraphMetrics:
    """Comprehensive graph metrics."""
    nodes: int
    edges: int
    density: float
    average_degree: float
    clustering_coefficient: float
    diameter: Optional[int]
    radius: Optional[int]
    connected_components: int
    strongly_connected_components: int
    centrality_measures: Dict[str, Dict[str, float]]


@dataclass
class DependencyChain:
    """Represents a chain of service dependencies."""
    services: List[str]
    relationship_types: List[str]
    total_strength: float
    is_circular: bool
    depth: int


class DependencyGraphBuilder:
    """
    Advanced dependency graph builder and analyzer.

    Constructs and analyzes service dependency graphs with support for
    complex relationship types, circular dependency detection, and
    performance optimization.
    """

    def __init__(self):
        self.graph_cache = {}

    def build_dependency_graph(
        self,
        nodes: Dict[str, ServiceNode],
        relationships: List[ServiceRelationship],
        graph_type: str = "directed"
    ) -> nx.DiGraph:
        """
        Build a NetworkX graph from service nodes and relationships.

        Args:
            nodes: Service nodes
            relationships: Service relationships
            graph_type: Type of graph to build

        Returns:
            NetworkX graph object
        """
        if graph_type == "directed":
            graph = nx.DiGraph()
        elif graph_type == "undirected":
            graph = nx.Graph()
        else:
            graph = nx.MultiDiGraph()

        # Add nodes with attributes
        for node_name, node in nodes.items():
            graph.add_node(node_name, **{
                "service_type": node.service_type.value,
                "health_status": node.health_status,
                "api_count": node.api_count,
                "metadata": node.metadata
            })

        # Add edges with attributes
        for relationship in relationships:
            edge_attrs = {
                "relationship_type": relationship.relationship_type.value,
                "strength": relationship.strength,
                "bidirectional": relationship.bidirectional,
                "metadata": relationship.metadata
            }

            graph.add_edge(
                relationship.source_service,
                relationship.target_service,
                **edge_attrs
            )

            # Add reverse edge for bidirectional relationships
            if relationship.bidirectional:
                graph.add_edge(
                    relationship.target_service,
                    relationship.source_service,
                    **edge_attrs
                )

        return graph

    def analyze_graph_structure(self, graph: nx.DiGraph) -> GraphMetrics:
        """
        Perform comprehensive graph structure analysis.

        Args:
            graph: NetworkX graph to analyze

        Returns:
            Comprehensive graph metrics
        """
        metrics = GraphMetrics(
            nodes=graph.number_of_nodes(),
            edges=graph.number_of_edges(),
            density=nx.density(graph),
            average_degree=sum(dict(graph.degree()).values()) / graph.number_of_nodes() if graph.number_of_nodes() > 0 else 0,
            clustering_coefficient=nx.average_clustering(graph),
            diameter=None,
            radius=None,
            connected_components=nx.number_weakly_connected_components(graph),
            strongly_connected_components=nx.number_strongly_connected_components(graph),
            centrality_measures={}
        )

        # Calculate diameter and radius for connected graphs
        if nx.is_weakly_connected(graph):
            try:
                metrics.diameter = nx.diameter(graph)
                metrics.radius = nx.radius(graph)
            except:
                pass  # Some graphs don't have these properties

        # Calculate centrality measures
        try:
            metrics.centrality_measures = {
                "degree": dict(nx.degree_centrality(graph)),
                "betweenness": dict(nx.betweenness_centrality(graph)),
                "closeness": dict(nx.closeness_centrality(graph)),
                "eigenvector": dict(nx.eigenvector_centrality(graph, max_iter=1000))
            }
        except:
            # Fallback centrality measures
            metrics.centrality_measures = {
                "degree": dict(nx.degree_centrality(graph))
            }

        return metrics

    def find_dependency_chains(
        self,
        graph: nx.DiGraph,
        start_service: str,
        max_depth: int = 10,
        include_circular: bool = False
    ) -> List[DependencyChain]:
        """
        Find all dependency chains starting from a service.

        Args:
            graph: Dependency graph
            start_service: Service to start analysis from
            max_depth: Maximum chain depth
            include_circular: Whether to include circular dependencies

        Returns:
            List of dependency chains
        """
        chains = []
        visited = set()
        current_chain = []

        def dfs(current_service: str, depth: int):
            if depth > max_depth or current_service in current_chain:
                # Check for circular dependency
                if current_service in current_chain:
                    chain_start = current_chain.index(current_service)
                    circular_chain = current_chain[chain_start:] + [current_service]
                    if include_circular:
                        chains.append(DependencyChain(
                            services=circular_chain,
                            relationship_types=["circular"] * (len(circular_chain) - 1),
                            total_strength=0.0,
                            is_circular=True,
                            depth=len(circular_chain)
                        ))
                return

            current_chain.append(current_service)
            visited.add(current_service)

            # Explore neighbors
            for neighbor in graph.successors(current_service):
                if neighbor not in visited:
                    dfs(neighbor, depth + 1)

            current_chain.pop()

        if start_service in graph:
            dfs(start_service, 0)

        # Convert to DependencyChain objects
        dependency_chains = []
        for chain_services in chains:
            if isinstance(chain_services, DependencyChain):
                dependency_chains.append(chain_services)
            else:
                # Build relationship types and strength
                relationship_types = []
                total_strength = 0.0

                for i in range(len(chain_services) - 1):
                    source = chain_services[i]
                    target = chain_services[i + 1]

                    edge_data = graph.get_edge_data(source, target)
                    if edge_data:
                        rel_type = edge_data.get("relationship_type", "unknown")
                        strength = edge_data.get("strength", 1.0)
                        relationship_types.append(rel_type)
                        total_strength += strength
                    else:
                        relationship_types.append("unknown")
                        total_strength += 1.0

                dependency_chains.append(DependencyChain(
                    services=chain_services,
                    relationship_types=relationship_types,
                    total_strength=total_strength,
                    is_circular=False,
                    depth=len(chain_services)
                ))

        return dependency_chains

    def identify_critical_paths(
        self,
        graph: nx.DiGraph,
        importance_threshold: float = 0.7
    ) -> List[List[str]]:
        """
        Identify critical paths in the dependency graph.

        Args:
            graph: Dependency graph
            importance_threshold: Threshold for considering paths critical

        Returns:
            List of critical service paths
        """
        critical_paths = []

        # Find all pairs shortest paths for important services
        important_services = self._identify_important_services(graph, importance_threshold)

        for source in important_services:
            for target in important_services:
                if source != target:
                    try:
                        # Find all simple paths
                        paths = list(nx.all_simple_paths(graph, source, target, cutoff=10))

                        # Score paths by importance
                        for path in paths:
                            if len(path) > 2:  # Only multi-hop paths
                                path_score = self._calculate_path_importance(graph, path)
                                if path_score >= importance_threshold:
                                    critical_paths.append((path, path_score))

                    except nx.NetworkXNoPath:
                        continue

        # Sort by importance score and return top paths
        critical_paths.sort(key=lambda x: x[1], reverse=True)
        return [path for path, score in critical_paths[:20]]  # Top 20 critical paths

    def detect_circular_dependencies(self, graph: nx.DiGraph) -> List[List[str]]:
        """
        Detect circular dependencies in the graph.

        Args:
            graph: Dependency graph

        Returns:
            List of circular dependency chains
        """
        circular_deps = []

        try:
            # Find all simple cycles
            cycles = list(nx.simple_cycles(graph))

            # Filter and sort cycles
            for cycle in cycles:
                if len(cycle) > 2:  # Only meaningful cycles
                    # Remove duplicate cycles (same cycle starting from different points)
                    normalized_cycle = tuple(sorted(cycle))
                    if normalized_cycle not in [tuple(sorted(c)) for c in circular_deps]:
                        circular_deps.append(cycle)

        except:
            # Fallback: manual cycle detection
            circular_deps = self._manual_cycle_detection(graph)

        return circular_deps

    def optimize_graph_layout(
        self,
        graph: nx.DiGraph,
        layout_algorithm: str = "spring",
        **kwargs
    ) -> Dict[str, Tuple[float, float]]:
        """
        Calculate optimal graph layout for visualization.

        Args:
            graph: Graph to layout
            layout_algorithm: Layout algorithm to use
            **kwargs: Additional layout parameters

        Returns:
            Node positions as (x, y) coordinates
        """
        if layout_algorithm == "spring":
            pos = nx.spring_layout(graph, **kwargs)
        elif layout_algorithm == "circular":
            pos = nx.circular_layout(graph, **kwargs)
        elif layout_algorithm == "random":
            pos = nx.random_layout(graph, **kwargs)
        elif layout_algorithm == "shell":
            pos = nx.shell_layout(graph, **kwargs)
        elif layout_algorithm == "spectral":
            pos = nx.spectral_layout(graph, **kwargs)
        else:
            pos = nx.spring_layout(graph, **kwargs)

        # Normalize coordinates to 0-1000 range
        if pos:
            x_coords = [coord[0] for coord in pos.values()]
            y_coords = [coord[1] for coord in pos.values()]

            if x_coords and y_coords:
                x_min, x_max = min(x_coords), max(x_coords)
                y_min, y_max = min(y_coords), max(y_coords)

                x_range = x_max - x_min if x_max != x_min else 1
                y_range = y_max - y_min if y_max != y_min else 1

                normalized_pos = {}
                for node, (x, y) in pos.items():
                    normalized_x = ((x - x_min) / x_range) * 800 + 100
                    normalized_y = ((y - y_min) / y_range) * 600 + 100
                    normalized_pos[node] = (normalized_x, normalized_y)

                return normalized_pos

        return {}

    def calculate_service_impact(
        self,
        graph: nx.DiGraph,
        service_name: str
    ) -> Dict[str, Any]:
        """
        Calculate the impact of a service failure on the ecosystem.

        Args:
            graph: Dependency graph
            service_name: Service to analyze

        Returns:
            Impact analysis metrics
        """
        if service_name not in graph:
            return {"error": "Service not found in graph"}

        impact = {
            "service": service_name,
            "direct_dependents": list(graph.successors(service_name)),
            "direct_dependencies": list(graph.predecessors(service_name)),
            "impact_score": 0.0,
            "affected_services": set(),
            "critical_paths_affected": 0
        }

        # Calculate cascading impact
        visited = set()
        queue = deque([service_name])
        visited.add(service_name)

        while queue:
            current = queue.popleft()
            dependents = list(graph.successors(current))

            for dependent in dependents:
                if dependent not in visited:
                    visited.add(dependent)
                    queue.append(dependent)
                    impact["affected_services"].add(dependent)

        impact["affected_services"] = list(impact["affected_services"])
        impact["total_affected"] = len(impact["affected_services"])

        # Calculate impact score based on affected services and their importance
        impact_score = len(impact["affected_services"])
        centrality = nx.degree_centrality(graph)
        for affected in impact["affected_services"]:
            impact_score += centrality.get(affected, 0) * 10

        impact["impact_score"] = impact_score

        return impact

    def _identify_important_services(
        self,
        graph: nx.DiGraph,
        threshold: float
    ) -> List[str]:
        """Identify important services based on centrality measures."""
        degree_centrality = nx.degree_centrality(graph)

        # Services with high centrality are important
        important = [
            service for service, centrality in degree_centrality.items()
            if centrality >= threshold
        ]

        # Always include services with high degree
        degree_threshold = max(1, int(graph.number_of_nodes() * 0.1))
        high_degree_services = [
            service for service, degree in graph.degree()
            if degree >= degree_threshold
        ]

        # Combine and deduplicate
        important_services = list(set(important + high_degree_services))

        return important_services[:20]  # Limit to top 20

    def _calculate_path_importance(self, graph: nx.DiGraph, path: List[str]) -> float:
        """Calculate importance score for a path."""
        if len(path) < 2:
            return 0.0

        score = 0.0

        # Length factor
        score += len(path) * 0.1

        # Node centrality factor
        degree_centrality = nx.degree_centrality(graph)
        for service in path:
            score += degree_centrality.get(service, 0) * 2

        # Edge strength factor
        for i in range(len(path) - 1):
            source = path[i]
            target = path[i + 1]
            edge_data = graph.get_edge_data(source, target, {})
            strength = edge_data.get("strength", 1.0)
            score += strength

        return score

    def _manual_cycle_detection(self, graph: nx.DiGraph) -> List[List[str]]:
        """Manual cycle detection using DFS."""
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.successors(node):
                if neighbor not in visited:
                    if dfs(neighbor, path.copy()):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                    return True

            rec_stack.remove(node)
            return False

        for node in graph.nodes():
            if node not in visited:
                dfs(node, [])

        return cycles

    def cache_graph(self, key: str, graph: nx.DiGraph):
        """Cache a graph for later reuse."""
        self.graph_cache[key] = graph

    def get_cached_graph(self, key: str) -> Optional[nx.DiGraph]:
        """Retrieve a cached graph."""
        return self.graph_cache.get(key)

    def clear_cache(self):
        """Clear the graph cache."""
        self.graph_cache.clear()
