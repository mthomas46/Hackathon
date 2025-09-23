"""
Topology Analyzer

Advanced service topology analysis engine that maps API relationships,
builds dependency graphs, and analyzes service interaction patterns.
"""

import asyncio
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
import networkx as nx
import json

from ..discovery.client import DiscoveryClient
from ..api.catalog import APICatalogManager
from ..monitoring.health import HealthMonitor


class RelationshipType(Enum):
    """Types of relationships between services."""
    DIRECT_API_CALL = "direct_api_call"
    SHARED_DATABASE = "shared_database"
    MESSAGE_QUEUE = "message_queue"
    EVENT_STREAMING = "event_streaming"
    SHARED_CACHE = "shared_cache"
    CONFIG_DEPENDENCY = "config_dependency"
    CIRCUIT_BREAKER = "circuit_breaker"
    LOAD_BALANCER = "load_balancer"


class ServiceType(Enum):
    """Types of services in the ecosystem."""
    API_SERVICE = "api_service"
    DATA_SERVICE = "data_service"
    INFRASTRUCTURE = "infrastructure"
    EXTERNAL_SERVICE = "external_service"
    MONITORING = "monitoring"
    SECURITY = "security"


@dataclass
class ServiceNode:
    """Represents a service node in the topology graph."""
    service_id: str
    service_name: str
    service_type: ServiceType
    base_url: Optional[str] = None
    health_status: str = "unknown"
    api_count: int = 0
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceRelationship:
    """Represents a relationship between two services."""
    source_service: str
    target_service: str
    relationship_type: RelationshipType
    strength: float = 1.0  # 0.0 to 1.0
    bidirectional: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TopologyAnalysis:
    """Complete topology analysis result."""
    nodes: Dict[str, ServiceNode]
    relationships: List[ServiceRelationship]
    graph: nx.DiGraph
    metrics: Dict[str, Any]
    clusters: List[Dict[str, Any]]
    critical_paths: List[List[str]]
    bottlenecks: List[Dict[str, Any]]


class TopologyAnalyzer:
    """
    Enterprise-grade service topology analyzer.

    Analyzes API relationships, builds dependency graphs, and provides
    comprehensive insights into service architecture and interactions.
    """

    def __init__(
        self,
        discovery_client: DiscoveryClient,
        catalog_manager: APICatalogManager,
        health_monitor: HealthMonitor
    ):
        self.discovery_client = discovery_client
        self.catalog_manager = catalog_manager
        self.health_monitor = health_monitor

        # Service type classification patterns
        self.service_type_patterns = {
            ServiceType.API_SERVICE: [
                'orchestrator', 'interpreter', 'doc-store', 'prompt-store',
                'cli', 'frontend', 'discovery-agent', 'project-simulation',
                'data-services-dashboard', 'notification-service', 'mock-data-generator'
            ],
            ServiceType.DATA_SERVICE: [
                'doc-store', 'prompt-store', 'source-agent', 'architecture-digitizer'
            ],
            ServiceType.INFRASTRUCTURE: [
                'github-mcp', 'bedrock-proxy', 'code-analyzer', 'secure-analyzer'
            ],
            ServiceType.MONITORING: [
                'unified-api-dashboard', 'health-monitor'
            ],
            ServiceType.SECURITY: [
                'secure-analyzer', 'auth-service'
            ]
        }

    async def analyze_topology(
        self,
        include_external_services: bool = True,
        max_depth: int = 5
    ) -> TopologyAnalysis:
        """
        Perform comprehensive topology analysis of the service ecosystem.

        Args:
            include_external_services: Whether to include external service dependencies
            max_depth: Maximum depth for relationship analysis

        Returns:
            Complete topology analysis
        """
        # Get all services
        services = await self.discovery_client.get_all_services()

        # Build service nodes
        nodes = await self._build_service_nodes(services)

        # Analyze relationships
        relationships = await self._analyze_relationships(nodes, max_depth)

        # Build graph
        graph = self._build_dependency_graph(nodes, relationships)

        # Calculate metrics
        metrics = self._calculate_topology_metrics(graph, nodes, relationships)

        # Identify clusters
        clusters = self._identify_service_clusters(graph, nodes)

        # Find critical paths
        critical_paths = self._find_critical_paths(graph, nodes)

        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(graph, nodes, relationships)

        return TopologyAnalysis(
            nodes=nodes,
            relationships=relationships,
            graph=graph,
            metrics=metrics,
            clusters=clusters,
            critical_paths=critical_paths,
            bottlenecks=bottlenecks
        )

    async def _build_service_nodes(self, services: Dict[str, Any]) -> Dict[str, ServiceNode]:
        """Build service nodes from discovered services."""
        nodes = {}

        for service_name, service_info in services.items():
            # Determine service type
            service_type = self._classify_service_type(service_name)

            # Get API count
            api_count = 0
            if "openapi_spec" in service_info:
                spec = service_info["openapi_spec"]
                if "paths" in spec:
                    api_count = len(spec["paths"])

            # Get health status
            health_status = "unknown"
            try:
                health_data = await self.health_monitor.get_service_health(service_name)
                if health_data and health_data.get("status") == "healthy":
                    health_status = "healthy"
                elif health_data and health_data.get("status") == "degraded":
                    health_status = "degraded"
                else:
                    health_status = "unhealthy"
            except Exception:
                pass

            node = ServiceNode(
                service_id=service_name,
                service_name=service_name,
                service_type=service_type,
                base_url=service_info.get("base_url"),
                health_status=health_status,
                api_count=api_count,
                metadata={
                    "description": service_info.get("description", ""),
                    "version": service_info.get("version", "unknown"),
                    "tags": service_info.get("tags", [])
                }
            )

            nodes[service_name] = node

        return nodes

    async def _analyze_relationships(
        self,
        nodes: Dict[str, ServiceNode],
        max_depth: int
    ) -> List[ServiceRelationship]:
        """Analyze relationships between services."""
        relationships = []

        # Analyze API call relationships from OpenAPI specs
        for service_name, node in nodes.items():
            service_info = await self.catalog_manager.get_service_details(service_name)
            if not service_info or "openapi_spec" not in service_info:
                continue

            spec = service_info["openapi_spec"]
            service_relationships = await self._analyze_service_relationships(
                service_name, spec, nodes, max_depth
            )
            relationships.extend(service_relationships)

        # Analyze configuration-based relationships
        config_relationships = await self._analyze_config_relationships(nodes)
        relationships.extend(config_relationships)

        # Analyze health monitoring relationships
        health_relationships = await self._analyze_health_relationships(nodes)
        relationships.extend(health_relationships)

        return relationships

    async def _analyze_service_relationships(
        self,
        service_name: str,
        spec: Dict[str, Any],
        nodes: Dict[str, ServiceNode],
        max_depth: int
    ) -> List[ServiceRelationship]:
        """Analyze relationships from OpenAPI specification."""
        relationships = []

        if "paths" not in spec:
            return relationships

        # Extract server URLs and external references
        servers = spec.get("servers", [])
        external_services = set()

        for server in servers:
            url = server.get("url", "")
            # Check if URL references other services in our ecosystem
            for node_name in nodes.keys():
                if node_name.lower() in url.lower():
                    relationships.append(ServiceRelationship(
                        source_service=service_name,
                        target_service=node_name,
                        relationship_type=RelationshipType.DIRECT_API_CALL,
                        strength=0.8,
                        metadata={"server_url": url}
                    ))

        # Analyze operation descriptions for service references
        for path, methods in spec["paths"].items():
            for method, operation in methods.items():
                if not isinstance(operation, dict):
                    continue

                description = operation.get("description", "").lower()
                summary = operation.get("summary", "").lower()

                # Look for service references in descriptions
                for node_name in nodes.keys():
                    if node_name in description or node_name in summary:
                        if node_name != service_name:  # Avoid self-references
                            relationships.append(ServiceRelationship(
                                source_service=service_name,
                                target_service=node_name,
                                relationship_type=RelationshipType.DIRECT_API_CALL,
                                strength=0.6,
                                metadata={
                                    "path": path,
                                    "method": method,
                                    "context": "description_reference"
                                }
                            ))

        return relationships

    async def _analyze_config_relationships(self, nodes: Dict[str, ServiceNode]) -> List[ServiceRelationship]:
        """Analyze configuration-based service relationships."""
        relationships = []

        # Common configuration patterns that indicate dependencies
        config_patterns = {
            "database": RelationshipType.SHARED_DATABASE,
            "redis": RelationshipType.SHARED_CACHE,
            "kafka": RelationshipType.MESSAGE_QUEUE,
            "rabbitmq": RelationshipType.MESSAGE_QUEUE,
            "elasticsearch": RelationshipType.SHARED_DATABASE,
            "mongodb": RelationshipType.SHARED_DATABASE,
            "postgres": RelationshipType.SHARED_DATABASE
        }

        # This would analyze actual configuration files or environment variables
        # For now, create some example relationships based on service types

        # Data services likely share databases
        data_services = [name for name, node in nodes.items()
                        if node.service_type == ServiceType.DATA_SERVICE]

        for i, service1 in enumerate(data_services):
            for service2 in data_services[i+1:]:
                relationships.append(ServiceRelationship(
                    source_service=service1,
                    target_service=service2,
                    relationship_type=RelationshipType.SHARED_DATABASE,
                    strength=0.4,
                    bidirectional=True,
                    metadata={"inferred": True, "reason": "data_services_share_storage"}
                ))

        # API services often depend on data services
        api_services = [name for name, node in nodes.items()
                       if node.service_type == ServiceType.API_SERVICE]
        infra_services = [name for name, node in nodes.items()
                         if node.service_type == ServiceType.INFRASTRUCTURE]

        for api_service in api_services:
            for data_service in data_services:
                relationships.append(ServiceRelationship(
                    source_service=api_service,
                    target_service=data_service,
                    relationship_type=RelationshipType.DIRECT_API_CALL,
                    strength=0.7,
                    metadata={"inferred": True, "reason": "api_calls_data_service"}
                ))

        return relationships

    async def _analyze_health_relationships(self, nodes: Dict[str, ServiceNode]) -> List[ServiceRelationship]:
        """Analyze health monitoring relationships."""
        relationships = []

        # Monitoring services have relationships with all other services
        monitoring_services = [name for name, node in nodes.items()
                              if node.service_type == ServiceType.MONITORING]

        for monitor_service in monitoring_services:
            for service_name in nodes.keys():
                if service_name != monitor_service:
                    relationships.append(ServiceRelationship(
                        source_service=monitor_service,
                        target_service=service_name,
                        relationship_type=RelationshipType.CONFIG_DEPENDENCY,
                        strength=0.3,
                        metadata={"monitoring": True}
                    ))

        return relationships

    def _build_dependency_graph(
        self,
        nodes: Dict[str, ServiceNode],
        relationships: List[ServiceRelationship]
    ) -> nx.DiGraph:
        """Build NetworkX directed graph from nodes and relationships."""
        graph = nx.DiGraph()

        # Add nodes
        for node_name, node in nodes.items():
            graph.add_node(node_name, **{
                "service_type": node.service_type.value,
                "health_status": node.health_status,
                "api_count": node.api_count,
                **node.metadata
            })

        # Add edges
        for relationship in relationships:
            graph.add_edge(
                relationship.source_service,
                relationship.target_service,
                relationship_type=relationship.relationship_type.value,
                strength=relationship.strength,
                bidirectional=relationship.bidirectional,
                **relationship.metadata
            )

            # Update node dependencies
            if relationship.source_service in nodes:
                nodes[relationship.source_service].dependencies.add(relationship.target_service)
            if relationship.target_service in nodes:
                nodes[relationship.target_service].dependents.add(relationship.source_service)

        return graph

    def _calculate_topology_metrics(
        self,
        graph: nx.DiGraph,
        nodes: Dict[str, ServiceNode],
        relationships: List[ServiceRelationship]
    ) -> Dict[str, Any]:
        """Calculate comprehensive topology metrics."""
        metrics = {}

        # Basic graph metrics
        metrics["total_services"] = len(nodes)
        metrics["total_relationships"] = len(relationships)
        metrics["graph_density"] = nx.density(graph)

        # Service type distribution
        type_counts = defaultdict(int)
        for node in nodes.values():
            type_counts[node.service_type.value] += 1
        metrics["service_type_distribution"] = dict(type_counts)

        # Health status distribution
        health_counts = defaultdict(int)
        for node in nodes.values():
            health_counts[node.health_status] += 1
        metrics["health_distribution"] = dict(health_counts)

        # Connectivity metrics
        if len(graph) > 0:
            metrics["average_degree"] = sum(dict(graph.degree()).values()) / len(graph)
            metrics["strongly_connected_components"] = nx.number_strongly_connected_components(graph)
            metrics["weakly_connected_components"] = nx.number_weakly_connected_components(graph)

            # Centrality measures
            try:
                degree_centrality = nx.degree_centrality(graph)
                metrics["most_connected_service"] = max(degree_centrality.items(), key=lambda x: x[1])
            except:
                metrics["most_connected_service"] = None

        # Relationship type distribution
        relationship_counts = defaultdict(int)
        for rel in relationships:
            relationship_counts[rel.relationship_type.value] += 1
        metrics["relationship_type_distribution"] = dict(relationship_counts)

        return metrics

    def _identify_service_clusters(
        self,
        graph: nx.DiGraph,
        nodes: Dict[str, ServiceNode]
    ) -> List[Dict[str, Any]]:
        """Identify service clusters and communities."""
        clusters = []

        # Use connected components as basic clusters
        for i, component in enumerate(nx.weakly_connected_components(graph)):
            component_nodes = list(component)

            # Calculate cluster metrics
            subgraph = graph.subgraph(component_nodes)
            cluster_type = self._determine_cluster_type(component_nodes, nodes)

            cluster_info = {
                "id": f"cluster_{i}",
                "name": f"{cluster_type.title()} Services",
                "services": component_nodes,
                "size": len(component_nodes),
                "density": nx.density(subgraph),
                "type": cluster_type,
                "central_services": self._find_central_services(subgraph, component_nodes)
            }

            clusters.append(cluster_info)

        return clusters

    def _find_critical_paths(
        self,
        graph: nx.DiGraph,
        nodes: Dict[str, ServiceNode]
    ) -> List[List[str]]:
        """Find critical paths in the service topology."""
        critical_paths = []

        # Find all simple paths between important services
        important_services = [
            name for name, node in nodes.items()
            if node.service_type in [ServiceType.API_SERVICE, ServiceType.INFRASTRUCTURE]
        ]

        for i, source in enumerate(important_services):
            for target in important_services[i+1:]:
                try:
                    # Find shortest path
                    path = nx.shortest_path(graph, source, target)
                    if len(path) > 2:  # Only paths with intermediate services
                        critical_paths.append(path)
                except nx.NetworkXNoPath:
                    continue

        # Sort by path length (longer paths are more critical)
        critical_paths.sort(key=len, reverse=True)
        return critical_paths[:10]  # Return top 10 critical paths

    def _identify_bottlenecks(
        self,
        graph: nx.DiGraph,
        nodes: Dict[str, ServiceNode],
        relationships: List[ServiceRelationship]
    ) -> List[Dict[str, Any]]:
        """Identify potential bottlenecks in the service topology."""
        bottlenecks = []

        # Calculate betweenness centrality (services that many paths go through)
        try:
            betweenness = nx.betweenness_centrality(graph)

            for service, centrality in betweenness.items():
                if centrality > 0.1:  # Threshold for bottleneck detection
                    node = nodes[service]
                    bottlenecks.append({
                        "service": service,
                        "bottleneck_score": centrality,
                        "service_type": node.service_type.value,
                        "health_status": node.health_status,
                        "dependency_count": len(node.dependencies),
                        "dependent_count": len(node.dependents),
                        "risk_level": "high" if centrality > 0.3 else "medium"
                    })
        except:
            pass

        # Sort by bottleneck score
        bottlenecks.sort(key=lambda x: x["bottleneck_score"], reverse=True)
        return bottlenecks[:10]  # Return top 10 bottlenecks

    def _classify_service_type(self, service_name: str) -> ServiceType:
        """Classify service type based on name patterns."""
        service_lower = service_name.lower()

        for service_type, patterns in self.service_type_patterns.items():
            if any(pattern in service_lower for pattern in patterns):
                return service_type

        # Default classification
        if "dashboard" in service_lower or "ui" in service_lower:
            return ServiceType.MONITORING
        elif "proxy" in service_lower or "gateway" in service_lower:
            return ServiceType.INFRASTRUCTURE
        else:
            return ServiceType.API_SERVICE

    def _determine_cluster_type(self, services: List[str], nodes: Dict[str, ServiceNode]) -> str:
        """Determine the type of a service cluster."""
        service_types = [nodes[s].service_type.value for s in services]
        most_common = max(set(service_types), key=service_types.count)

        type_mapping = {
            "api_service": "API",
            "data_service": "Data",
            "infrastructure": "Infrastructure",
            "monitoring": "Monitoring",
            "security": "Security"
        }

        return type_mapping.get(most_common, "Mixed")

    def _find_central_services(self, subgraph: nx.DiGraph, services: List[str]) -> List[str]:
        """Find central services within a cluster."""
        try:
            degree_centrality = nx.degree_centrality(subgraph)
            sorted_services = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)
            return [service for service, _ in sorted_services[:3]]  # Top 3 central services
        except:
            return services[:3] if len(services) >= 3 else services
