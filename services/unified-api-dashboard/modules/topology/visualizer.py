"""
Topology Visualizer

Generates visualization data for service topology graphs, including
interactive diagrams, charts, and dashboard widgets.
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import networkx as nx
import colorsys

from .analyzer import TopologyAnalysis, ServiceNode, ServiceRelationship, ServiceType, RelationshipType


class LayoutAlgorithm(Enum):
    """Graph layout algorithms for visualization."""
    FORCE_DIRECTED = "force_directed"
    HIERARCHICAL = "hierarchical"
    CIRCULAR = "circular"
    GRID = "grid"


class VisualizationFormat(Enum):
    """Output formats for topology visualization."""
    CYTOSCAPE = "cytoscape"  # For web-based interactive graphs
    D3 = "d3"  # D3.js compatible format
    GRAPHVIZ = "graphviz"  # DOT format for Graphviz
    JSON = "json"  # Generic JSON format


@dataclass
class NodeStyle:
    """Visual styling for service nodes."""
    color: str
    shape: str
    size: int
    border_color: str
    border_width: int
    label_color: str = "#000000"
    font_size: int = 12


@dataclass
class EdgeStyle:
    """Visual styling for relationships."""
    color: str
    width: int
    style: str = "solid"  # solid, dashed, dotted
    arrow: bool = True
    label: Optional[str] = None


@dataclass
class VisualizationData:
    """Complete visualization data package."""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    layout: Dict[str, Any]
    styles: Dict[str, Any]
    metadata: Dict[str, Any]
    format: VisualizationFormat


class TopologyVisualizer:
    """
    Advanced topology visualization engine.

    Generates interactive visualizations for service topology graphs
    with multiple output formats and customization options.
    """

    def __init__(self):
        # Color schemes for different service types
        self.service_colors = {
            ServiceType.API_SERVICE: "#4CAF50",      # Green
            ServiceType.DATA_SERVICE: "#2196F3",     # Blue
            ServiceType.INFRASTRUCTURE: "#FF9800",   # Orange
            ServiceType.EXTERNAL_SERVICE: "#9C27B0", # Purple
            ServiceType.MONITORING: "#00BCD4",      # Cyan
            ServiceType.SECURITY: "#F44336"         # Red
        }

        # Relationship colors
        self.relationship_colors = {
            RelationshipType.DIRECT_API_CALL: "#4CAF50",
            RelationshipType.SHARED_DATABASE: "#2196F3",
            RelationshipType.MESSAGE_QUEUE: "#FF9800",
            RelationshipType.EVENT_STREAMING: "#9C27B0",
            RelationshipType.SHARED_CACHE: "#00BCD4",
            RelationshipType.CONFIG_DEPENDENCY: "#F44336",
            RelationshipType.CIRCUIT_BREAKER: "#607D8B",
            RelationshipType.LOAD_BALANCER: "#795548"
        }

    def generate_visualization(
        self,
        analysis: TopologyAnalysis,
        format: VisualizationFormat = VisualizationFormat.CYTOSCAPE,
        layout: LayoutAlgorithm = LayoutAlgorithm.FORCE_DIRECTED,
        include_styles: bool = True,
        include_metrics: bool = True
    ) -> VisualizationData:
        """
        Generate visualization data from topology analysis.

        Args:
            analysis: Topology analysis results
            format: Output format for visualization
            layout: Layout algorithm to use
            include_styles: Whether to include styling information
            include_metrics: Whether to include topology metrics

        Returns:
            Complete visualization data package
        """
        # Generate layout coordinates
        layout_coords = self._calculate_layout(analysis.graph, layout)

        # Convert nodes
        nodes = self._convert_nodes(analysis.nodes, layout_coords, format)

        # Convert edges
        edges = self._convert_edges(analysis.relationships, format)

        # Generate styles
        styles = {}
        if include_styles:
            styles = self._generate_styles(analysis.nodes, analysis.relationships)

        # Generate layout information
        layout_info = self._generate_layout_info(layout, layout_coords)

        # Prepare metadata
        metadata = {
            "total_nodes": len(analysis.nodes),
            "total_edges": len(analysis.relationships),
            "layout_algorithm": layout.value,
            "format": format.value
        }

        if include_metrics:
            metadata.update(analysis.metrics)

        return VisualizationData(
            nodes=nodes,
            edges=edges,
            layout=layout_info,
            styles=styles,
            metadata=metadata,
            format=format
        )

    def generate_cluster_visualization(
        self,
        analysis: TopologyAnalysis,
        format: VisualizationFormat = VisualizationFormat.CYTOSCAPE
    ) -> List[VisualizationData]:
        """
        Generate separate visualizations for each service cluster.

        Args:
            analysis: Topology analysis results

        Returns:
            List of visualization data for each cluster
        """
        visualizations = []

        for cluster in analysis.clusters:
            # Create subgraph for this cluster
            subgraph = analysis.graph.subgraph(cluster["services"])

            # Create cluster-specific analysis
            cluster_nodes = {name: analysis.nodes[name] for name in cluster["services"]}
            cluster_relationships = [
                rel for rel in analysis.relationships
                if rel.source_service in cluster["services"] and rel.target_service in cluster["services"]
            ]

            cluster_analysis = TopologyAnalysis(
                nodes=cluster_nodes,
                relationships=cluster_relationships,
                graph=subgraph,
                metrics=cluster,
                clusters=[],
                critical_paths=[],
                bottlenecks=[]
            )

            # Generate visualization for this cluster
            viz = self.generate_visualization(
                cluster_analysis,
                format=format,
                layout=LayoutAlgorithm.FORCE_DIRECTED
            )

            # Add cluster metadata
            viz.metadata.update({
                "cluster_id": cluster["id"],
                "cluster_name": cluster["name"],
                "cluster_type": cluster["type"],
                "cluster_size": cluster["size"]
            })

            visualizations.append(viz)

        return visualizations

    def generate_critical_path_visualization(
        self,
        analysis: TopologyAnalysis,
        path_index: int = 0,
        format: VisualizationFormat = VisualizationFormat.CYTOSCAPE
    ) -> Optional[VisualizationData]:
        """
        Generate visualization highlighting a specific critical path.

        Args:
            analysis: Topology analysis results
            path_index: Index of critical path to highlight

        Returns:
            Visualization data with highlighted critical path
        """
        if not analysis.critical_paths or path_index >= len(analysis.critical_paths):
            return None

        critical_path = analysis.critical_paths[path_index]

        # Create subgraph containing only the critical path
        path_subgraph = analysis.graph.subgraph(critical_path)

        # Create path-specific analysis
        path_nodes = {name: analysis.nodes[name] for name in critical_path}
        path_relationships = []

        for i in range(len(critical_path) - 1):
            source = critical_path[i]
            target = critical_path[i + 1]

            # Find the relationship between these services
            for rel in analysis.relationships:
                if rel.source_service == source and rel.target_service == target:
                    path_relationships.append(rel)
                    break

        path_analysis = TopologyAnalysis(
            nodes=path_nodes,
            relationships=path_relationships,
            graph=path_subgraph,
            metrics={"path_length": len(critical_path), "is_critical_path": True},
            clusters=[],
            critical_paths=[critical_path],
            bottlenecks=[]
        )

        # Generate visualization
        viz = self.generate_visualization(
            path_analysis,
            format=format,
            layout=LayoutAlgorithm.HIERARCHICAL
        )

        # Mark path nodes and edges as highlighted
        for node in viz.nodes:
            node["data"]["highlighted"] = True
            node["data"]["critical_path"] = True

        for edge in viz.edges:
            edge["data"]["highlighted"] = True
            edge["data"]["critical_path"] = True

        viz.metadata.update({
            "critical_path_index": path_index,
            "path_services": critical_path,
            "path_highlighted": True
        })

        return viz

    def _calculate_layout(self, graph: nx.DiGraph, algorithm: LayoutAlgorithm) -> Dict[str, Tuple[float, float]]:
        """Calculate node positions using the specified layout algorithm."""
        if algorithm == LayoutAlgorithm.FORCE_DIRECTED:
            # Use spring layout (force-directed)
            pos = nx.spring_layout(graph, k=2, iterations=50, seed=42)
        elif algorithm == LayoutAlgorithm.HIERARCHICAL:
            # Use hierarchical layout (layered)
            pos = nx.multipartite_layout(graph)
        elif algorithm == LayoutAlgorithm.CIRCULAR:
            # Use circular layout
            pos = nx.circular_layout(graph)
        elif algorithm == LayoutAlgorithm.GRID:
            # Use grid layout
            pos = nx.grid_layout(graph)
        else:
            # Default to spring layout
            pos = nx.spring_layout(graph)

        # Convert to dictionary with normalized coordinates (0-1000 range)
        coords = {}
        if pos:
            x_coords = [coord[0] for coord in pos.values()]
            y_coords = [coord[1] for coord in pos.values()]

            if x_coords and y_coords:
                x_min, x_max = min(x_coords), max(x_coords)
                y_min, y_max = min(y_coords), max(y_coords)

                x_range = x_max - x_min if x_max != x_min else 1
                y_range = y_max - y_min if y_max != y_min else 1

                for node, (x, y) in pos.items():
                    normalized_x = ((x - x_min) / x_range) * 800 + 100  # 100-900 range
                    normalized_y = ((y - y_min) / y_range) * 600 + 100  # 100-700 range
                    coords[node] = (normalized_x, normalized_y)

        return coords

    def _convert_nodes(
        self,
        nodes: Dict[str, ServiceNode],
        layout_coords: Dict[str, Tuple[float, float]],
        format: VisualizationFormat
    ) -> List[Dict[str, Any]]:
        """Convert service nodes to visualization format."""
        converted_nodes = []

        for node_name, node in nodes.items():
            # Get position
            x, y = layout_coords.get(node_name, (0, 0))

            # Get styling
            style = self._get_node_style(node)

            if format == VisualizationFormat.CYTOSCAPE:
                cytoscape_node = {
                    "data": {
                        "id": node_name,
                        "label": node.service_name,
                        "service_type": node.service_type.value,
                        "health_status": node.health_status,
                        "api_count": node.api_count,
                        "dependency_count": len(node.dependencies),
                        "dependent_count": len(node.dependents),
                        "metadata": node.metadata
                    },
                    "position": {
                        "x": x,
                        "y": y
                    },
                    "style": asdict(style)
                }
                converted_nodes.append(cytoscape_node)

            elif format == VisualizationFormat.D3:
                d3_node = {
                    "id": node_name,
                    "name": node.service_name,
                    "group": node.service_type.value,
                    "x": x,
                    "y": y,
                    "health": node.health_status,
                    "api_count": node.api_count,
                    **asdict(style)
                }
                converted_nodes.append(d3_node)

            elif format == VisualizationFormat.JSON:
                json_node = {
                    "id": node_name,
                    "name": node.service_name,
                    "type": node.service_type.value,
                    "health": node.health_status,
                    "position": {"x": x, "y": y},
                    "metrics": {
                        "api_count": node.api_count,
                        "dependencies": len(node.dependencies),
                        "dependents": len(node.dependents)
                    },
                    "style": asdict(style),
                    "metadata": node.metadata
                }
                converted_nodes.append(json_node)

        return converted_nodes

    def _convert_edges(
        self,
        relationships: List[ServiceRelationship],
        format: VisualizationFormat
    ) -> List[Dict[str, Any]]:
        """Convert relationships to visualization format."""
        converted_edges = []

        for i, rel in enumerate(relationships):
            # Get styling
            style = self._get_edge_style(rel)

            if format == VisualizationFormat.CYTOSCAPE:
                cytoscape_edge = {
                    "data": {
                        "id": f"edge_{i}",
                        "source": rel.source_service,
                        "target": rel.target_service,
                        "relationship_type": rel.relationship_type.value,
                        "strength": rel.strength,
                        "bidirectional": rel.bidirectional,
                        "metadata": rel.metadata
                    },
                    "style": asdict(style)
                }
                converted_edges.append(cytoscape_edge)

            elif format == VisualizationFormat.D3:
                d3_edge = {
                    "source": rel.source_service,
                    "target": rel.target_service,
                    "type": rel.relationship_type.value,
                    "strength": rel.strength,
                    **asdict(style)
                }
                converted_edges.append(d3_edge)

            elif format == VisualizationFormat.JSON:
                json_edge = {
                    "id": f"edge_{i}",
                    "source": rel.source_service,
                    "target": rel.target_service,
                    "type": rel.relationship_type.value,
                    "strength": rel.strength,
                    "bidirectional": rel.bidirectional,
                    "style": asdict(style),
                    "metadata": rel.metadata
                }
                converted_edges.append(json_edge)

        return converted_edges

    def _get_node_style(self, node: ServiceNode) -> NodeStyle:
        """Get visual styling for a service node."""
        base_color = self.service_colors.get(node.service_type, "#9E9E9E")

        # Adjust color based on health status
        if node.health_status == "unhealthy":
            color = "#F44336"  # Red
        elif node.health_status == "degraded":
            color = "#FF9800"  # Orange
        else:
            color = base_color

        # Size based on API count and dependencies
        size = 30 + min(node.api_count * 2, 20) + min(len(node.dependencies) * 3, 15)

        return NodeStyle(
            color=color,
            shape="ellipse",
            size=size,
            border_color="#333333",
            border_width=2,
            label_color="#000000",
            font_size=10
        )

    def _get_edge_style(self, relationship: ServiceRelationship) -> EdgeStyle:
        """Get visual styling for a relationship edge."""
        color = self.relationship_colors.get(relationship.relationship_type, "#9E9E9E")

        # Width based on relationship strength
        width = max(1, int(relationship.strength * 5))

        # Style based on relationship type
        if relationship.relationship_type == RelationshipType.SHARED_DATABASE:
            style = "dashed"
        elif relationship.relationship_type == RelationshipType.CONFIG_DEPENDENCY:
            style = "dotted"
        else:
            style = "solid"

        return EdgeStyle(
            color=color,
            width=width,
            style=style,
            arrow=True,
            label=relationship.relationship_type.value.replace("_", " ").title()
        )

    def _generate_styles(
        self,
        nodes: Dict[str, ServiceNode],
        relationships: List[ServiceRelationship]
    ) -> Dict[str, Any]:
        """Generate comprehensive styling information."""
        return {
            "node_styles": {
                service_type.value: asdict(self._get_node_style(
                    ServiceNode("", "", service_type, health_status="healthy")
                ))
                for service_type in ServiceType
            },
            "edge_styles": {
                rel_type.value: asdict(self._get_edge_style(
                    ServiceRelationship("", "", rel_type)
                ))
                for rel_type in RelationshipType
            },
            "color_schemes": {
                "service_types": {st.value: color for st, color in self.service_colors.items()},
                "relationship_types": {rt.value: color for rt, color in self.relationship_colors.items()},
                "health_status": {
                    "healthy": "#4CAF50",
                    "degraded": "#FF9800",
                    "unhealthy": "#F44336",
                    "unknown": "#9E9E9E"
                }
            }
        }

    def _generate_layout_info(
        self,
        algorithm: LayoutAlgorithm,
        coords: Dict[str, Tuple[float, float]]
    ) -> Dict[str, Any]:
        """Generate layout configuration information."""
        return {
            "algorithm": algorithm.value,
            "bounding_box": self._calculate_bounding_box(coords),
            "node_positions": coords,
            "viewport": {
                "width": 1000,
                "height": 800,
                "padding": 50
            }
        }

    def _calculate_bounding_box(self, coords: Dict[str, Tuple[float, float]]) -> Dict[str, float]:
        """Calculate bounding box for all node positions."""
        if not coords:
            return {"x_min": 0, "y_min": 0, "x_max": 1000, "y_max": 800}

        x_coords = [pos[0] for pos in coords.values()]
        y_coords = [pos[1] for pos in coords.values()]

        return {
            "x_min": min(x_coords),
            "y_min": min(y_coords),
            "x_max": max(x_coords),
            "y_max": max(y_coords)
        }

    def export_visualization(
        self,
        visualization: VisualizationData,
        filename: str,
        include_metadata: bool = True
    ) -> str:
        """
        Export visualization data to a file.

        Args:
            visualization: Visualization data to export
            filename: Output filename
            include_metadata: Whether to include metadata

        Returns:
            Path to exported file
        """
        export_data = {
            "nodes": visualization.nodes,
            "edges": visualization.edges,
            "layout": visualization.layout,
            "styles": visualization.styles
        }

        if include_metadata:
            export_data["metadata"] = visualization.metadata

        # Ensure directory exists
        import os
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else ".", exist_ok=True)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, default=str)

        return filename
