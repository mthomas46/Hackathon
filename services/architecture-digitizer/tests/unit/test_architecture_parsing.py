"""Unit Tests for Architecture Parsing in Architecture Digitizer Service.

This module tests architecture parsing capabilities including:
- Diagram format parsing and validation
- Component extraction and classification
- Relationship identification and mapping
- Metadata extraction and enrichment
- Format conversion and normalization

Tests cover the complete architecture parsing infrastructure within the Architecture Digitizer service.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock
from typing import Dict, Any, List

from main import ArchitectureRequest, ArchitectureResponse


class TestArchitectureParsing:
    """Test Architecture Parsing functionality."""

    @pytest.fixture
    def architecture_parser(self):
        """Create architecture parser instance with test configuration."""
        from main import ArchitectureParser
        return ArchitectureParser()

    @pytest.fixture
    def diagram_normalizer(self):
        """Create diagram normalizer instance with test configuration."""
        from main import DiagramNormalizer
        return DiagramNormalizer()

    @pytest.fixture
    def sample_miro_diagram(self):
        """Sample Miro diagram data for testing."""
        return {
            "board_id": "board123",
            "widgets": [
                {
                    "id": "widget1",
                    "type": "sticker",
                    "metadata": {
                        "text": "Web Server\nNode.js Application"
                    },
                    "bounds": {"x": 100, "y": 100, "width": 150, "height": 100}
                },
                {
                    "id": "widget2",
                    "type": "sticker",
                    "metadata": {
                        "text": "Database\nPostgreSQL"
                    },
                    "bounds": {"x": 300, "y": 100, "width": 150, "height": 100}
                },
                {
                    "id": "widget3",
                    "type": "line",
                    "metadata": {
                        "startWidget": {"id": "widget1"},
                        "endWidget": {"id": "widget2"},
                        "style": {"strokeStyle": "normal"}
                    }
                },
                {
                    "id": "widget4",
                    "type": "sticker",
                    "metadata": {
                        "text": "API Gateway\nREST API"
                    },
                    "bounds": {"x": 200, "y": 50, "width": 150, "height": 80}
                },
                {
                    "id": "widget5",
                    "type": "line",
                    "metadata": {
                        "startWidget": {"id": "widget4"},
                        "endWidget": {"id": "widget1"},
                        "style": {"strokeStyle": "dashed"}
                    }
                }
            ],
            "metadata": {
                "name": "E-commerce Architecture",
                "description": "Microservices architecture for e-commerce platform",
                "tags": ["microservices", "ecommerce", "web"]
            }
        }

    @pytest.fixture
    def sample_lucidchart_diagram(self):
        """Sample Lucidchart diagram data for testing."""
        return {
            "document_id": "doc456",
            "pages": [
                {
                    "id": "page1",
                    "name": "System Architecture",
                    "shapes": [
                        {
                            "id": "shape1",
                            "type": "rectangle",
                            "text": "Frontend\nReact SPA",
                            "properties": {
                                "fillColor": "#E3F2FD",
                                "strokeColor": "#1976D2"
                            },
                            "position": {"x": 150, "y": 50, "width": 200, "height": 100}
                        },
                        {
                            "id": "shape2",
                            "type": "cylinder",
                            "text": "Backend API\nExpress.js",
                            "properties": {
                                "fillColor": "#F3E5F5",
                                "strokeColor": "#7B1FA2"
                            },
                            "position": {"x": 150, "y": 200, "width": 200, "height": 120}
                        },
                        {
                            "id": "shape3",
                            "type": "hexagon",
                            "text": "Database\nMongoDB",
                            "properties": {
                                "fillColor": "#E8F5E8",
                                "strokeColor": "#388E3C"
                            },
                            "position": {"x": 450, "y": 200, "width": 180, "height": 100}
                        }
                    ],
                    "lines": [
                        {
                            "id": "line1",
                            "startShape": {"id": "shape1"},
                            "endShape": {"id": "shape2"},
                            "properties": {
                                "strokeStyle": "solid",
                                "strokeColor": "#666666"
                            }
                        },
                        {
                            "id": "line2",
                            "startShape": {"id": "shape2"},
                            "endShape": {"id": "shape3"},
                            "properties": {
                                "strokeStyle": "solid",
                                "strokeColor": "#666666"
                            }
                        }
                    ]
                }
            ],
            "metadata": {
                "title": "Web Application Architecture",
                "author": "Architecture Team",
                "version": "2.1",
                "lastModified": "2024-01-15T10:30:00Z"
            }
        }

    @pytest.fixture
    def complex_enterprise_diagram(self):
        """Complex enterprise architecture diagram for testing."""
        return {
            "system": "enterprise",
            "components": [
                {
                    "id": "web_tier",
                    "name": "Web Tier",
                    "type": "load_balancer",
                    "technology": "NGINX",
                    "replicas": 3,
                    "position": {"x": 100, "y": 50}
                },
                {
                    "id": "api_gateway",
                    "name": "API Gateway",
                    "type": "api_gateway",
                    "technology": "Kong",
                    "position": {"x": 100, "y": 150}
                },
                {
                    "id": "user_service",
                    "name": "User Service",
                    "type": "microservice",
                    "technology": "Node.js",
                    "database": "PostgreSQL",
                    "position": {"x": 300, "y": 100}
                },
                {
                    "id": "order_service",
                    "name": "Order Service",
                    "type": "microservice",
                    "technology": "Java Spring Boot",
                    "database": "MySQL",
                    "position": {"x": 300, "y": 200}
                },
                {
                    "id": "payment_service",
                    "name": "Payment Service",
                    "type": "microservice",
                    "technology": "Python FastAPI",
                    "external_apis": ["Stripe", "PayPal"],
                    "position": {"x": 500, "y": 100}
                },
                {
                    "id": "notification_service",
                    "name": "Notification Service",
                    "type": "microservice",
                    "technology": "Go",
                    "message_queue": "RabbitMQ",
                    "position": {"x": 500, "y": 200}
                },
                {
                    "id": "cache",
                    "name": "Redis Cache",
                    "type": "cache",
                    "technology": "Redis",
                    "cluster": True,
                    "position": {"x": 700, "y": 50}
                },
                {
                    "id": "user_db",
                    "name": "User Database",
                    "type": "database",
                    "technology": "PostgreSQL",
                    "replicas": 2,
                    "position": {"x": 700, "y": 150}
                },
                {
                    "id": "order_db",
                    "name": "Order Database",
                    "type": "database",
                    "technology": "MySQL",
                    "sharding": True,
                    "position": {"x": 700, "y": 250}
                }
            ],
            "connections": [
                {"from": "web_tier", "to": "api_gateway", "type": "http", "protocol": "HTTPS"},
                {"from": "api_gateway", "to": "user_service", "type": "http", "protocol": "HTTP"},
                {"from": "api_gateway", "to": "order_service", "type": "http", "protocol": "HTTP"},
                {"from": "user_service", "to": "user_db", "type": "database", "protocol": "PostgreSQL"},
                {"from": "order_service", "to": "order_db", "type": "database", "protocol": "MySQL"},
                {"from": "order_service", "to": "payment_service", "type": "http", "protocol": "HTTPS"},
                {"from": "payment_service", "to": "notification_service", "type": "message_queue", "protocol": "AMQP"},
                {"from": "user_service", "to": "cache", "type": "cache", "protocol": "Redis"},
                {"from": "order_service", "to": "cache", "type": "cache", "protocol": "Redis"}
            ],
            "metadata": {
                "system_name": "E-Commerce Platform",
                "architecture_style": "Microservices",
                "technologies": ["Node.js", "Java", "Python", "Go", "PostgreSQL", "MySQL", "Redis", "RabbitMQ"],
                "compliance_requirements": ["PCI_DSS", "GDPR"],
                "scalability_requirements": ["horizontal_scaling", "database_sharding"],
                "security_layers": ["api_gateway", "encryption_at_rest", "ssl_tls"]
            }
        }

    def test_miro_diagram_parsing(self, architecture_parser, sample_miro_diagram):
        """Test Miro diagram parsing capabilities."""
        result = architecture_parser.parse_miro_diagram(sample_miro_diagram)

        assert result.success is True
        assert "components" in result.parsed_data
        assert "connections" in result.parsed_data
        assert "metadata" in result.parsed_data

        # Verify component extraction
        components = result.parsed_data["components"]
        assert len(components) >= 3  # Web Server, Database, API Gateway

        # Check component properties
        web_server = next(c for c in components if "Web Server" in c["name"])
        assert web_server["type"] == "service"
        assert web_server["technology"] == "Node.js"

        database = next(c for c in components if "Database" in c["name"])
        assert database["type"] == "storage"
        assert database["technology"] == "PostgreSQL"

        # Verify connections
        connections = result.parsed_data["connections"]
        assert len(connections) >= 2

        # Check connection types
        solid_connections = [c for c in connections if c["style"] == "solid"]
        dashed_connections = [c for c in connections if c["style"] == "dashed"]

        assert len(solid_connections) >= 1
        assert len(dashed_connections) >= 1

    def test_lucidchart_diagram_parsing(self, architecture_parser, sample_lucidchart_diagram):
        """Test Lucidchart diagram parsing capabilities."""
        result = architecture_parser.parse_lucidchart_diagram(sample_lucidchart_diagram)

        assert result.success is True
        assert "components" in result.parsed_data
        assert "connections" in result.parsed_data

        # Verify component extraction
        components = result.parsed_data["components"]
        assert len(components) == 3

        # Check component types
        frontend = next(c for c in components if "Frontend" in c["name"])
        assert frontend["type"] == "frontend"
        assert frontend["technology"] == "React"

        backend = next(c for c in components if "Backend" in c["name"])
        assert backend["type"] == "backend"
        assert backend["technology"] == "Express.js"

        database = next(c for c in components if "Database" in c["name"])
        assert database["type"] == "database"
        assert database["technology"] == "MongoDB"

        # Verify connections
        connections = result.parsed_data["connections"]
        assert len(connections) == 2

        # Check connection properties
        for conn in connections:
            assert "from" in conn
            assert "to" in conn
            assert conn["type"] == "http"

    def test_enterprise_diagram_normalization(self, diagram_normalizer, complex_enterprise_diagram):
        """Test enterprise diagram normalization."""
        result = diagram_normalizer.normalize_enterprise_diagram(complex_enterprise_diagram)

        assert result.success is True
        assert "normalized_components" in result.normalized_data
        assert "normalized_connections" in result.normalized_data
        assert "architecture_patterns" in result.normalized_data

        # Verify component normalization
        components = result.normalized_data["normalized_components"]
        assert len(components) == 9

        # Check component categorization
        microservices = [c for c in components if c["category"] == "microservice"]
        infrastructure = [c for c in components if c["category"] == "infrastructure"]
        databases = [c for c in components if c["category"] == "database"]

        assert len(microservices) == 4  # user, order, payment, notification services
        assert len(infrastructure) >= 2  # web tier, api gateway
        assert len(databases) == 2  # user_db, order_db

        # Verify connection normalization
        connections = result.normalized_data["normalized_connections"]
        assert len(connections) == 9

        # Check connection types
        http_connections = [c for c in connections if c["protocol"] == "HTTP" or c["protocol"] == "HTTPS"]
        db_connections = [c for c in connections if "database" in c["type"].lower()]
        cache_connections = [c for c in connections if "cache" in c["type"].lower()]

        assert len(http_connections) >= 3
        assert len(db_connections) == 2
        assert len(cache_connections) == 2

        # Verify architecture patterns detection
        patterns = result.normalized_data["architecture_patterns"]
        assert "microservices" in patterns
        assert "api_gateway" in patterns
        assert "database_per_service" in patterns
        assert "caching_layer" in patterns

    def test_component_classification_engine(self, architecture_parser):
        """Test component classification and categorization."""
        # Test various component types
        test_components = [
            {"name": "Web Server", "description": "Handles HTTP requests"},
            {"name": "PostgreSQL Database", "description": "Primary data storage"},
            {"name": "Redis Cache", "description": "In-memory caching"},
            {"name": "API Gateway", "description": "Request routing and authentication"},
            {"name": "Message Queue", "description": "Async communication"},
            {"name": "Load Balancer", "description": "Traffic distribution"},
            {"name": "CDN", "description": "Content delivery network"},
            {"name": "Monitoring Service", "description": "System observability"}
        ]

        for component in test_components:
            classification = architecture_parser.classify_component(component)

            assert "type" in classification
            assert "category" in classification
            assert "confidence" in classification
            assert 0.0 <= classification["confidence"] <= 1.0

            # Verify classification accuracy
            name_lower = component["name"].lower()

            if "database" in name_lower or "postgres" in name_lower or "mysql" in name_lower:
                assert classification["category"] == "database"
            elif "cache" in name_lower or "redis" in name_lower:
                assert classification["category"] == "cache"
            elif "api" in name_lower and "gateway" in name_lower:
                assert classification["category"] == "api_gateway"
            elif "web" in name_lower or "server" in name_lower:
                assert classification["category"] in ["web_server", "application"]

    def test_relationship_extraction_engine(self, architecture_parser, sample_miro_diagram):
        """Test relationship and connection extraction."""
        relationships = architecture_parser.extract_relationships(sample_miro_diagram)

        assert len(relationships) >= 2

        for rel in relationships:
            assert "from" in rel
            assert "to" in rel
            assert "type" in rel
            assert "strength" in rel

            # Verify relationship strength calculation
            assert 0.0 <= rel["strength"] <= 1.0

            # Verify relationship type classification
            assert rel["type"] in ["depends_on", "communicates_with", "stores_in", "caches_in"]

    def test_metadata_enrichment_engine(self, architecture_parser, complex_enterprise_diagram):
        """Test metadata extraction and enrichment."""
        enriched_metadata = architecture_parser.enrich_metadata(complex_enterprise_diagram)

        assert "enriched_properties" in enriched_metadata
        assert "inferred_technologies" in enriched_metadata
        assert "architecture_characteristics" in enriched_metadata

        # Verify technology inference
        technologies = enriched_metadata["inferred_technologies"]
        expected_tech = ["Node.js", "Java", "Python", "Go", "PostgreSQL", "MySQL", "Redis", "RabbitMQ", "NGINX", "Kong"]
        for tech in expected_tech:
            assert tech in technologies

        # Verify architecture characteristics
        characteristics = enriched_metadata["architecture_characteristics"]
        assert characteristics["style"] == "microservices"
        assert characteristics["scalability_approach"] == "horizontal_scaling"
        assert len(characteristics["communication_patterns"]) >= 3  # HTTP, Database, Message Queue

    def test_format_conversion_engine(self, diagram_normalizer):
        """Test diagram format conversion capabilities."""
        # Test Miro to internal format conversion
        miro_data = {
            "widgets": [
                {"id": "w1", "type": "sticker", "metadata": {"text": "Service A"}},
                {"id": "w2", "type": "line", "metadata": {"startWidget": {"id": "w1"}, "endWidget": {"id": "w2"}}}
            ]
        }

        internal_format = diagram_normalizer.convert_miro_to_internal(miro_data)

        assert "components" in internal_format
        assert "connections" in internal_format
        assert len(internal_format["components"]) == 1
        assert len(internal_format["connections"]) == 1

        # Test Lucidchart to internal format conversion
        lucid_data = {
            "shapes": [
                {"id": "s1", "type": "rectangle", "text": "Component B"}
            ],
            "lines": []
        }

        internal_format = diagram_normalizer.convert_lucidchart_to_internal(lucid_data)

        assert "components" in internal_format
        assert len(internal_format["components"]) == 1
        assert internal_format["components"][0]["name"] == "Component B"

    def test_validation_and_error_handling(self, architecture_parser):
        """Test validation and error handling for malformed diagrams."""
        # Test empty diagram
        empty_diagram = {}
        result = architecture_parser.parse_diagram(empty_diagram, "miro")
        assert result.success is False
        assert "empty" in str(result.error).lower()

        # Test malformed Miro diagram
        malformed_miro = {"widgets": "not_a_list"}
        result = architecture_parser.parse_diagram(malformed_miro, "miro")
        assert result.success is False

        # Test unsupported format
        unsupported_diagram = {"data": "some_data"}
        result = architecture_parser.parse_diagram(unsupported_diagram, "unsupported_format")
        assert result.success is False
        assert "unsupported" in str(result.error).lower()

        # Test missing required fields
        incomplete_diagram = {"widgets": [{"id": "w1"}]}  # Missing type and metadata
        result = architecture_parser.parse_diagram(incomplete_diagram, "miro")
        # Should handle gracefully, not crash
        assert result is not None

    def test_performance_and_scalability(self, architecture_parser, complex_enterprise_diagram):
        """Test parsing performance and scalability."""
        import time

        # Test parsing performance
        start_time = time.time()
        result = architecture_parser.parse_diagram(complex_enterprise_diagram, "enterprise")
        end_time = time.time()

        parsing_time = end_time - start_time
        assert parsing_time < 2.0  # Should complete within 2 seconds

        # Test memory efficiency (no memory leaks)
        initial_memory = architecture_parser._get_memory_usage() if hasattr(architecture_parser, '_get_memory_usage') else 0

        # Parse multiple times
        for _ in range(10):
            architecture_parser.parse_diagram(complex_enterprise_diagram, "enterprise")

        final_memory = architecture_parser._get_memory_usage() if hasattr(architecture_parser, '_get_memory_usage') else 0

        # Memory usage should not grow significantly
        if initial_memory > 0 and final_memory > 0:
            memory_growth = (final_memory - initial_memory) / initial_memory
            assert memory_growth < 0.5  # Less than 50% growth

    @pytest.mark.parametrize("diagram_type,input_data,expected_components", [
        ("miro", {"widgets": [{"type": "sticker", "metadata": {"text": "Test"}}]}, 1),
        ("lucidchart", {"shapes": [{"text": "Component"}, {"text": "Another"}]}, 2),
        ("enterprise", {"components": [{"name": "Service"}, {"name": "DB"}]}, 2),
    ])
    def test_diagram_type_support(self, architecture_parser, diagram_type, input_data, expected_components):
        """Test support for different diagram types with parametrized tests."""
        result = architecture_parser.parse_diagram(input_data, diagram_type)

        # Should handle each type appropriately
        assert result is not None

        if result.success:
            components = result.parsed_data.get("components", [])
            assert len(components) >= expected_components

    def test_architecture_pattern_detection(self, architecture_parser, complex_enterprise_diagram):
        """Test architecture pattern detection and analysis."""
        patterns = architecture_parser.detect_architecture_patterns(complex_enterprise_diagram)

        assert "detected_patterns" in patterns
        assert "confidence_scores" in patterns
        assert "recommendations" in patterns

        detected = patterns["detected_patterns"]

        # Should detect microservices patterns
        assert any("microservice" in p.lower() for p in detected)

        # Should detect database patterns
        assert any("database" in p.lower() for p in detected)

        # Should detect caching patterns
        assert any("cach" in p.lower() for p in detected)

        # Should detect API gateway pattern
        assert any("gateway" in p.lower() for p in detected)

        # Verify confidence scores
        confidence = patterns["confidence_scores"]
        for pattern, score in confidence.items():
            assert 0.0 <= score <= 1.0

    def test_technology_inference_engine(self, architecture_parser):
        """Test technology stack inference from component descriptions."""
        test_descriptions = [
            "Node.js web application server",
            "PostgreSQL database cluster",
            "Redis caching layer",
            "RabbitMQ message broker",
            "NGINX load balancer",
            "Docker containerized deployment"
        ]

        inferred_technologies = []

        for desc in test_descriptions:
            technologies = architecture_parser.infer_technologies(desc)
            inferred_technologies.extend(technologies)

        # Should infer major technologies
        assert "Node.js" in inferred_technologies
        assert "PostgreSQL" in inferred_technologies
        assert "Redis" in inferred_technologies
        assert "RabbitMQ" in inferred_technologies
        assert "NGINX" in inferred_technologies
        assert "Docker" in inferred_technologies

    def test_diagram_export_and_serialization(self, diagram_normalizer, complex_enterprise_diagram):
        """Test diagram export and serialization capabilities."""
        # Normalize diagram first
        normalized = diagram_normalizer.normalize_enterprise_diagram(complex_enterprise_diagram)

        # Test JSON export
        json_export = diagram_normalizer.export_as_json(normalized.normalized_data)
        assert isinstance(json_export, str)

        # Verify JSON is valid and contains expected data
        parsed_json = json.loads(json_export)
        assert "normalized_components" in parsed_json
        assert "normalized_connections" in parsed_json

        # Test YAML export (if supported)
        try:
            yaml_export = diagram_normalizer.export_as_yaml(normalized.normalized_data)
            assert isinstance(yaml_export, str)
        except ImportError:
            # YAML not available, skip test
            pass

        # Test PlantUML export
        plantuml_export = diagram_normalizer.export_as_plantuml(normalized.normalized_data)
        assert isinstance(plantuml_export, str)
        assert "@startuml" in plantuml_export
        assert "@enduml" in plantuml_export

        # Test Draw.io export
        drawio_export = diagram_normalizer.export_as_drawio(normalized.normalized_data)
        assert isinstance(drawio_export, str)
        assert "<mxfile>" in drawio_export or "draw.io" in drawio_export.lower()
