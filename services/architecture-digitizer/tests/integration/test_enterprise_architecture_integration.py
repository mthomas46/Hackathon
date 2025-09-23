"""Integration Tests for Enterprise Architecture Integration in Architecture Digitizer Service.

This module tests enterprise architecture integration capabilities including:
- End-to-end architecture digitization workflows
- Multi-format diagram processing and conversion
- Enterprise architecture documentation generation
- Architecture analysis and pattern recognition
- Compliance and governance validation
- Architecture visualization and reporting

Integration tests cover complete enterprise architecture workflows and documentation generation scenarios.
"""

import pytest
import asyncio
import time
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List
import uuid

from main import ArchitectureRequest, ArchitectureResponse


class TestEnterpriseArchitectureIntegration:
    """Integration tests for enterprise architecture workflows."""

    @pytest.fixture
    def integration_app(self):
        """Create a complete Architecture Digitizer application for integration testing."""
        from main import app
        return app

    @pytest.fixture
    def enterprise_architecture_diagrams(self):
        """Enterprise architecture diagrams for comprehensive testing."""
        return {
            "system_overview": {
                "format": "miro",
                "data": {
                    "board_id": "enterprise_overview_001",
                    "widgets": [
                        {
                            "id": "widget1",
                            "type": "sticker",
                            "metadata": {"text": "Customer Portal\nReact SPA"},
                            "bounds": {"x": 100, "y": 50, "width": 150, "height": 100}
                        },
                        {
                            "id": "widget2",
                            "type": "sticker",
                            "metadata": {"text": "API Gateway\nKong"},
                            "bounds": {"x": 300, "y": 50, "width": 150, "height": 100}
                        },
                        {
                            "id": "widget3",
                            "type": "sticker",
                            "metadata": {"text": "User Management\nMicroservice"},
                            "bounds": {"x": 500, "y": 50, "width": 150, "height": 100}
                        },
                        {
                            "id": "widget4",
                            "type": "sticker",
                            "metadata": {"text": "Product Catalog\nMicroservice"},
                            "bounds": {"x": 300, "y": 200, "width": 150, "height": 100}
                        },
                        {
                            "id": "widget5",
                            "type": "sticker",
                            "metadata": {"text": "Order Processing\nMicroservice"},
                            "bounds": {"x": 500, "y": 200, "width": 150, "height": 100}
                        },
                        {
                            "id": "widget6",
                            "type": "sticker",
                            "metadata": {"text": "PostgreSQL\nPrimary DB"},
                            "bounds": {"x": 100, "y": 350, "width": 150, "height": 100}
                        },
                        {
                            "id": "widget7",
                            "type": "sticker",
                            "metadata": {"text": "MongoDB\nProduct Data"},
                            "bounds": {"x": 300, "y": 350, "width": 150, "height": 100}
                        },
                        {
                            "id": "widget8",
                            "type": "sticker",
                            "metadata": {"text": "Redis Cache\nSession Store"},
                            "bounds": {"x": 500, "y": 350, "width": 150, "height": 100}
                        },
                        # Connections
                        {
                            "id": "line1",
                            "type": "line",
                            "metadata": {"startWidget": {"id": "widget1"}, "endWidget": {"id": "widget2"}}
                        },
                        {
                            "id": "line2",
                            "type": "line",
                            "metadata": {"startWidget": {"id": "widget2"}, "endWidget": {"id": "widget3"}}
                        },
                        {
                            "id": "line3",
                            "type": "line",
                            "metadata": {"startWidget": {"id": "widget2"}, "endWidget": {"id": "widget4"}}
                        },
                        {
                            "id": "line4",
                            "type": "line",
                            "metadata": {"startWidget": {"id": "widget4"}, "endWidget": {"id": "widget5"}}
                        },
                        {
                            "id": "line5",
                            "type": "line",
                            "metadata": {"startWidget": {"id": "widget3"}, "endWidget": {"id": "widget6"}}
                        },
                        {
                            "id": "line6",
                            "type": "line",
                            "metadata": {"startWidget": {"id": "widget4"}, "endWidget": {"id": "widget7"}}
                        },
                        {
                            "id": "line7",
                            "type": "line",
                            "metadata": {"startWidget": {"id": "widget3"}, "endWidget": {"id": "widget8"}}
                        }
                    ],
                    "metadata": {
                        "name": "E-Commerce Platform Architecture",
                        "description": "Complete microservices architecture for e-commerce platform",
                        "tags": ["ecommerce", "microservices", "cloud-native"],
                        "version": "2.1",
                        "author": "Enterprise Architecture Team"
                    }
                }
            },
            "infrastructure_diagram": {
                "format": "lucidchart",
                "data": {
                    "document_id": "infra_789",
                    "pages": [{
                        "id": "page1",
                        "name": "Infrastructure Architecture",
                        "shapes": [
                            {
                                "id": "vpc",
                                "type": "rectangle",
                                "text": "VPC\n10.0.0.0/16",
                                "properties": {"fillColor": "#E3F2FD"}
                            },
                            {
                                "id": "subnet_public",
                                "type": "rectangle",
                                "text": "Public Subnet\n10.0.1.0/24",
                                "properties": {"fillColor": "#F3E5F5"}
                            },
                            {
                                "id": "subnet_private",
                                "type": "rectangle",
                                "text": "Private Subnet\n10.0.2.0/24",
                                "properties": {"fillColor": "#E8F5E8"}
                            },
                            {
                                "id": "alb",
                                "type": "rectangle",
                                "text": "Application Load Balancer",
                                "properties": {"fillColor": "#FFF3E0"}
                            },
                            {
                                "id": "ecs_cluster",
                                "type": "circle",
                                "text": "ECS Cluster\nFargate",
                                "properties": {"fillColor": "#FCE4EC"}
                            },
                            {
                                "id": "rds",
                                "type": "cylinder",
                                "text": "RDS Aurora\nPostgreSQL",
                                "properties": {"fillColor": "#F3E5F5"}
                            },
                            {
                                "id": "elasticache",
                                "type": "hexagon",
                                "text": "ElastiCache\nRedis Cluster",
                                "properties": {"fillColor": "#E8F5E8"}
                            }
                        ],
                        "lines": [
                            {"startShape": {"id": "subnet_public"}, "endShape": {"id": "alb"}},
                            {"startShape": {"id": "alb"}, "endShape": {"id": "ecs_cluster"}},
                            {"startShape": {"id": "ecs_cluster"}, "endShape": {"id": "rds"}},
                            {"startShape": {"id": "ecs_cluster"}, "endShape": {"id": "elasticache"}},
                            {"startShape": {"id": "vpc"}, "endShape": {"id": "subnet_public"}},
                            {"startShape": {"id": "vpc"}, "endShape": {"id": "subnet_private"}}
                        ]
                    }],
                    "metadata": {
                        "title": "AWS Infrastructure Architecture",
                        "author": "DevOps Team",
                        "version": "1.8",
                        "lastModified": "2024-01-15T14:30:00Z",
                        "compliance": ["SOC2", "PCI_DSS"]
                    }
                }
            },
            "security_architecture": {
                "format": "enterprise",
                "data": {
                    "system": "security",
                    "components": [
                        {
                            "id": "waf",
                            "name": "Web Application Firewall",
                            "type": "security",
                            "technology": "AWS WAF",
                            "position": {"x": 100, "y": 50}
                        },
                        {
                            "id": "api_gateway",
                            "name": "API Gateway with Security",
                            "type": "api_gateway",
                            "technology": "Kong Gateway",
                            "security_features": ["JWT", "Rate Limiting", "CORS"],
                            "position": {"x": 300, "y": 50}
                        },
                        {
                            "id": "auth_service",
                            "name": "Authentication Service",
                            "type": "security_service",
                            "technology": "Keycloak",
                            "protocols": ["OAuth2", "OpenID Connect"],
                            "position": {"x": 500, "y": 50}
                        },
                        {
                            "id": "encryption_service",
                            "name": "Data Encryption Service",
                            "type": "security_service",
                            "technology": "AWS KMS",
                            "encryption_types": ["AES256", "RSA"],
                            "position": {"x": 100, "y": 200}
                        },
                        {
                            "id": "audit_service",
                            "name": "Audit & Compliance Service",
                            "type": "monitoring",
                            "technology": "Custom Service",
                            "compliance_standards": ["GDPR", "HIPAA", "PCI_DSS"],
                            "position": {"x": 300, "y": 200}
                        },
                        {
                            "id": "threat_detection",
                            "name": "Threat Detection System",
                            "type": "security_service",
                            "technology": "AWS GuardDuty",
                            "detection_types": ["Anomaly", "Malware", "Unauthorized Access"],
                            "position": {"x": 500, "y": 200}
                        }
                    ],
                    "connections": [
                        {"from": "waf", "to": "api_gateway", "type": "security_filter", "protocol": "HTTPS"},
                        {"from": "api_gateway", "to": "auth_service", "type": "authentication", "protocol": "JWT"},
                        {"from": "encryption_service", "to": "api_gateway", "type": "encryption", "protocol": "TLS"},
                        {"from": "audit_service", "to": "api_gateway", "type": "monitoring", "protocol": "HTTP"},
                        {"from": "threat_detection", "to": "waf", "type": "threat_intelligence", "protocol": "API"}
                    ],
                    "metadata": {
                        "system_name": "Enterprise Security Architecture",
                        "architecture_style": "Defense in Depth",
                        "security_layers": ["Perimeter", "Network", "Application", "Data"],
                        "compliance_requirements": ["GDPR", "HIPAA", "PCI_DSS", "SOC2"],
                        "threat_model": "STRIDE",
                        "risk_assessment": "High Security Required"
                    }
                }
            }
        }

    @pytest.fixture
    def enterprise_architecture_requirements(self):
        """Enterprise architecture requirements and standards."""
        return {
            "compliance_standards": ["GDPR", "HIPAA", "PCI_DSS", "SOC2"],
            "architecture_patterns": ["microservices", "event_driven", "api_first"],
            "technology_standards": ["cloud_native", "containerized", "serverless_ready"],
            "security_requirements": ["defense_in_depth", "zero_trust", "encryption_at_rest"],
            "scalability_requirements": ["horizontal_scaling", "auto_scaling", "global_distribution"],
            "monitoring_requirements": ["observability", "distributed_tracing", "log_aggregation"],
            "documentation_standards": ["architecture_decision_records", "api_documentation", "runbooks"]
        }

    @pytest.mark.asyncio
    async def test_end_to_end_architecture_digitization_workflow(self, integration_app, enterprise_architecture_diagrams):
        """Test complete enterprise architecture digitization workflow."""
        # Setup comprehensive architecture digitization workflow
        with patch("main.ArchitectureParser") as mock_parser_class, \
             patch("main.DiagramNormalizer") as mock_normalizer_class, \
             patch("main.ArchitectureAnalyzer") as mock_analyzer_class:

            # Mock components
            mock_parser = MagicMock()
            mock_normalizer = MagicMock()
            mock_analyzer = MagicMock()

            mock_parser_class.return_value = mock_parser
            mock_normalizer_class.return_value = mock_normalizer
            mock_analyzer_class.return_value = mock_analyzer

            # Configure parser responses for different diagram types
            def parser_side_effect(diagram_data, format_type):
                if format_type == "miro":
                    return ArchitectureResponse(
                        success=True,
                        parsed_data={
                            "components": [
                                {"id": "comp1", "name": "Customer Portal", "type": "frontend"},
                                {"id": "comp2", "name": "API Gateway", "type": "api_gateway"},
                                {"id": "comp3", "name": "User Management", "type": "microservice"},
                                {"id": "comp4", "name": "Product Catalog", "type": "microservice"},
                                {"id": "comp5", "name": "Order Processing", "type": "microservice"},
                                {"id": "comp6", "name": "PostgreSQL", "type": "database"},
                                {"id": "comp7", "name": "MongoDB", "type": "database"},
                                {"id": "comp8", "name": "Redis Cache", "type": "cache"}
                            ],
                            "connections": [
                                {"from": "comp1", "to": "comp2", "type": "http"},
                                {"from": "comp2", "to": "comp3", "type": "http"},
                                {"from": "comp2", "to": "comp4", "type": "http"},
                                {"from": "comp4", "to": "comp5", "type": "message_queue"},
                                {"from": "comp3", "to": "comp6", "type": "database"},
                                {"from": "comp4", "to": "comp7", "type": "database"},
                                {"from": "comp3", "to": "comp8", "type": "cache"}
                            ],
                            "metadata": {"source": "miro", "pattern": "microservices"}
                        }
                    )
                elif format_type == "lucidchart":
                    return ArchitectureResponse(
                        success=True,
                        parsed_data={
                            "components": [
                                {"id": "infra1", "name": "VPC", "type": "network"},
                                {"id": "infra2", "name": "Public Subnet", "type": "network"},
                                {"id": "infra3", "name": "ALB", "type": "load_balancer"},
                                {"id": "infra4", "name": "ECS Cluster", "type": "compute"},
                                {"id": "infra5", "name": "RDS Aurora", "type": "database"},
                                {"id": "infra6", "name": "ElastiCache", "type": "cache"}
                            ],
                            "connections": [
                                {"from": "infra2", "to": "infra3", "type": "network"},
                                {"from": "infra3", "to": "infra4", "type": "network"},
                                {"from": "infra4", "to": "infra5", "type": "network"},
                                {"from": "infra4", "to": "infra6", "type": "network"}
                            ],
                            "metadata": {"source": "lucidchart", "pattern": "cloud_infrastructure"}
                        }
                    )
                else:  # enterprise format
                    return ArchitectureResponse(
                        success=True,
                        parsed_data={
                            "components": diagram_data.get("components", []),
                            "connections": diagram_data.get("connections", []),
                            "metadata": {"source": "enterprise", "pattern": "security_architecture"}
                        }
                    )

            mock_parser.parse_diagram.side_effect = parser_side_effect

            # Configure normalizer responses
            def normalizer_side_effect(diagram_data):
                return ArchitectureResponse(
                    success=True,
                    normalized_data={
                        "normalized_components": [
                            {**comp, "category": "infrastructure" if "subnet" in comp.get("name", "").lower() or "vpc" in comp.get("name", "").lower() else "application",
                             "normalized_name": comp["name"].replace(" ", "_").lower()}
                            for comp in diagram_data.get("components", [])
                        ],
                        "normalized_connections": [
                            {**conn, "normalized_type": conn["type"].replace("_", "-")}
                            for conn in diagram_data.get("connections", [])
                        ],
                        "architecture_patterns": ["microservices", "cloud_native", "event_driven"]
                    }
                )

            mock_normalizer.normalize_enterprise_diagram.side_effect = normalizer_side_effect

            # Configure analyzer responses
            mock_analyzer.analyze_patterns.return_value = {
                "patterns": ["microservices", "api_gateway", "database_per_service"],
                "confidence_scores": {"microservices": 0.95, "api_gateway": 0.88, "database_per_service": 0.82},
                "recommendations": ["Consider implementing service mesh", "Add circuit breakers", "Implement distributed tracing"]
            }

            mock_analyzer.assess_compliance.return_value = {
                "compliant": True,
                "standards_checked": ["GDPR", "HIPAA", "PCI_DSS"],
                "violations": [],
                "recommendations": ["Regular security audits", "Implement data encryption at rest"]
            }

            # Execute enterprise architecture digitization workflow
            digitization_results = {}

            for diagram_name, diagram_config in enterprise_architecture_diagrams.items():
                print(f"🔍 Digitizing {diagram_name} architecture...")

                # Parse diagram
                parse_result = mock_parser.parse_diagram(diagram_config["data"], diagram_config["format"])

                # Normalize architecture
                normalize_result = mock_normalizer.normalize_enterprise_diagram(parse_result.parsed_data)

                # Analyze patterns and compliance
                pattern_analysis = mock_analyzer.analyze_patterns(normalize_result.normalized_data)
                compliance_assessment = mock_analyzer.assess_compliance(normalize_result.normalized_data)

                digitization_results[diagram_name] = {
                    "parsed": parse_result,
                    "normalized": normalize_result,
                    "patterns": pattern_analysis,
                    "compliance": compliance_assessment
                }

            # Verify comprehensive enterprise architecture digitization
            assert len(digitization_results) == 3

            # Verify system overview digitization
            system_result = digitization_results["system_overview"]
            assert system_result["parsed"].success is True
            assert len(system_result["parsed"].parsed_data["components"]) >= 8
            assert len(system_result["parsed"].parsed_data["connections"]) >= 7

            # Verify infrastructure digitization
            infra_result = digitization_results["infrastructure_diagram"]
            assert infra_result["parsed"].success is True
            assert any("VPC" in comp["name"] for comp in infra_result["parsed"].parsed_data["components"])
            assert any("ECS" in comp["name"] for comp in infra_result["parsed"].parsed_data["components"])

            # Verify security architecture digitization
            security_result = digitization_results["security_architecture"]
            assert security_result["parsed"].success is True
            assert any("WAF" in comp["name"] for comp in security_result["parsed"].parsed_data["components"])
            assert any("API Gateway" in comp["name"] for comp in security_result["parsed"].parsed_data["components"])

            # Verify normalization across all diagrams
            for result in digitization_results.values():
                normalized = result["normalized"]
                assert normalized.success is True
                assert "normalized_components" in normalized.normalized_data
                assert "normalized_connections" in normalized.normalized_data
                assert "architecture_patterns" in normalized.normalized_data

            # Verify pattern analysis
            for result in digitization_results.values():
                patterns = result["patterns"]
                assert "patterns" in patterns
                assert "confidence_scores" in patterns
                assert len(patterns["patterns"]) > 0

            # Verify compliance assessment
            for result in digitization_results.values():
                compliance = result["compliance"]
                assert "compliant" in compliance
                assert "standards_checked" in compliance
                assert compliance["compliant"] is True  # Should pass compliance checks

    @pytest.mark.asyncio
    async def test_multi_format_architecture_processing_pipeline(self, integration_app, enterprise_architecture_diagrams):
        """Test multi-format architecture processing and conversion pipeline."""
        # Setup multi-format processing pipeline
        with patch("main.ArchitectureParser") as mock_parser_class, \
             patch("main.DiagramNormalizer") as mock_normalizer_class, \
             patch("main.FormatConverter") as mock_converter_class:

            mock_parser = MagicMock()
            mock_normalizer = MagicMock()
            mock_converter = MagicMock()

            mock_parser_class.return_value = mock_parser
            mock_normalizer_class.return_value = mock_normalizer
            mock_converter_class.return_value = mock_converter

            # Configure format conversion capabilities
            conversion_formats = ["plantuml", "drawio", "json", "yaml", "markdown"]

            def convert_side_effect(data, from_format, to_format):
                if to_format == "plantuml":
                    return f"""@startuml
{chr(10).join([f"component {comp['name'].replace(' ', '_')}" for comp in data.get('normalized_components', [])])}
@enduml"""
                elif to_format == "drawio":
                    return f"""<mxfile>
<diagram>
{chr(10).join([f'<mxCell value="{comp["name"]}" />' for comp in data.get('normalized_components', [])])}
</diagram>
</mxfile>"""
                elif to_format == "json":
                    return json.dumps(data, indent=2)
                elif to_format == "yaml":
                    return "yaml_content_placeholder"  # Simplified for testing
                elif to_format == "markdown":
                    components_md = chr(10).join([f"- {comp['name']}" for comp in data.get('normalized_components', [])])
                    return f"""# Architecture Documentation

## Components
{components_md}

## Connections
- Component relationships documented
"""
                return f"Converted to {to_format}"

            mock_converter.convert_format.side_effect = convert_side_effect

            # Execute multi-format processing pipeline
            processing_results = {}

            for diagram_name, diagram_config in enterprise_architecture_diagrams.items():
                print(f"🔄 Processing {diagram_name} in multiple formats...")

                # Parse and normalize first
                with patch.object(mock_parser, 'parse_diagram') as mock_parse:
                    mock_parse.return_value = ArchitectureResponse(
                        success=True,
                        parsed_data={
                            "components": [{"id": f"c{i}", "name": f"Component {i}"} for i in range(3)],
                            "connections": [{"from": "c0", "to": "c1", "type": "depends"}],
                            "metadata": {"source": diagram_config["format"]}
                        }
                    )

                    with patch.object(mock_normalizer, 'normalize_enterprise_diagram') as mock_norm:
                        mock_norm.return_value = ArchitectureResponse(
                            success=True,
                            normalized_data={
                                "normalized_components": [{"name": f"Component {i}", "type": "service"} for i in range(3)],
                                "normalized_connections": [{"from": "Component 0", "to": "Component 1"}],
                                "architecture_patterns": ["microservices"]
                            }
                        )

                        # Parse and normalize
                        parsed = mock_parser.parse_diagram(diagram_config["data"], diagram_config["format"])
                        normalized = mock_normalizer.normalize_enterprise_diagram(parsed.parsed_data)

                        # Convert to multiple formats
                        format_conversions = {}
                        for target_format in conversion_formats:
                            converted = mock_converter.convert_format(
                                normalized.normalized_data,
                                "normalized",
                                target_format
                            )
                            format_conversions[target_format] = converted

                        processing_results[diagram_name] = {
                            "original_format": diagram_config["format"],
                            "parsed": parsed,
                            "normalized": normalized,
                            "conversions": format_conversions
                        }

            # Verify multi-format processing results
            assert len(processing_results) == 3

            for diagram_name, result in processing_results.items():
                assert result["parsed"].success is True
                assert result["normalized"].success is True

                conversions = result["conversions"]
                assert len(conversions) == 5  # All target formats

                # Verify specific format conversions
                plantuml = conversions["plantuml"]
                assert "@startuml" in plantuml
                assert "@enduml" in plantuml
                assert "component" in plantuml

                drawio = conversions["drawio"]
                assert "<mxfile>" in drawio
                assert "<mxCell" in drawio

                json_conv = conversions["json"]
                assert isinstance(json_conv, str)
                parsed_json = json.loads(json_conv)
                assert "normalized_components" in parsed_json

                markdown = conversions["markdown"]
                assert "# Architecture Documentation" in markdown
                assert "## Components" in markdown
                assert "- Component" in markdown

    @pytest.mark.asyncio
    async def test_enterprise_architecture_analysis_and_reporting(self, integration_app, enterprise_architecture_requirements):
        """Test enterprise architecture analysis and automated reporting."""
        # Setup enterprise architecture analysis and reporting
        with patch("main.ArchitectureAnalyzer") as mock_analyzer_class, \
             patch("main.ReportGenerator") as mock_report_class, \
             patch("main.ComplianceChecker") as mock_compliance_class:

            mock_analyzer = MagicMock()
            mock_report_generator = MagicMock()
            mock_compliance_checker = MagicMock()

            mock_analyzer_class.return_value = mock_analyzer
            mock_report_class.return_value = mock_report_generator
            mock_compliance_class.return_value = mock_compliance_checker

            # Configure architecture analysis
            def analyze_architecture_side_effect(architecture_data):
                components = architecture_data.get("normalized_components", [])
                connections = architecture_data.get("normalized_connections", [])

                analysis = {
                    "component_count": len(components),
                    "connection_count": len(connections),
                    "architecture_patterns": ["microservices", "api_gateway", "event_driven"],
                    "technology_stack": list(set(comp.get("technology", "Unknown") for comp in components)),
                    "scalability_score": 8.5,
                    "security_score": 9.2,
                    "maintainability_score": 7.8,
                    "recommendations": [
                        "Consider implementing service mesh for better observability",
                        "Add circuit breakers for resilience",
                        "Implement distributed tracing",
                        "Consider database sharding for scalability"
                    ]
                }

                return analysis

            mock_analyzer.analyze_enterprise_architecture.side_effect = analyze_architecture_side_effect

            # Configure compliance checking
            def check_compliance_side_effect(architecture_data, standards):
                compliance_results = {}

                for standard in standards:
                    if standard == "GDPR":
                        compliance_results[standard] = {
                            "compliant": True,
                            "violations": [],
                            "recommendations": ["Implement data encryption", "Regular privacy audits"]
                        }
                    elif standard == "HIPAA":
                        compliance_results[standard] = {
                            "compliant": True,
                            "violations": [],
                            "recommendations": ["PHI data handling procedures", "Access logging"]
                        }
                    elif standard == "PCI_DSS":
                        compliance_results[standard] = {
                            "compliant": True,
                            "violations": [],
                            "recommendations": ["Regular security scans", "Tokenization for card data"]
                        }
                    elif standard == "SOC2":
                        compliance_results[standard] = {
                            "compliant": True,
                            "violations": [],
                            "recommendations": ["Implement SOC2 controls", "Regular audits"]
                        }

                return compliance_results

            mock_compliance_checker.check_enterprise_compliance.side_effect = check_compliance_side_effect

            # Configure report generation
            def generate_report_side_effect(analysis_data, compliance_data, format_type):
                if format_type == "html":
                    return f"""<html>
<head><title>Enterprise Architecture Report</title></head>
<body>
<h1>Architecture Analysis Report</h1>
<p>Components: {analysis_data['component_count']}</p>
<p>Compliance: {'✅ All standards compliant' if all(c['compliant'] for c in compliance_data.values()) else '❌ Compliance issues found'}</p>
</body>
</html>"""
                elif format_type == "pdf":
                    return b"PDF_REPORT_CONTENT_PLACEHOLDER"
                elif format_type == "json":
                    return json.dumps({
                        "analysis": analysis_data,
                        "compliance": compliance_data,
                        "generated_at": datetime.now().isoformat()
                    }, indent=2)
                else:
                    return f"Report in {format_type} format"

            mock_report_generator.generate_enterprise_report.side_effect = generate_report_side_effect

            # Execute enterprise architecture analysis workflow
            enterprise_architecture_data = {
                "normalized_components": [
                    {"name": "API Gateway", "type": "api_gateway", "technology": "Kong"},
                    {"name": "User Service", "type": "microservice", "technology": "Node.js"},
                    {"name": "Order Service", "type": "microservice", "technology": "Java"},
                    {"name": "Payment Service", "type": "microservice", "technology": "Python"},
                    {"name": "PostgreSQL", "type": "database", "technology": "PostgreSQL"},
                    {"name": "Redis Cache", "type": "cache", "technology": "Redis"},
                    {"name": "RabbitMQ", "type": "message_queue", "technology": "RabbitMQ"}
                ],
                "normalized_connections": [
                    {"from": "API Gateway", "to": "User Service", "type": "http"},
                    {"from": "API Gateway", "to": "Order Service", "type": "http"},
                    {"from": "Order Service", "to": "Payment Service", "type": "http"},
                    {"from": "User Service", "to": "PostgreSQL", "type": "database"},
                    {"from": "Order Service", "to": "PostgreSQL", "type": "database"},
                    {"from": "User Service", "to": "Redis Cache", "type": "cache"},
                    {"from": "Order Service", "to": "RabbitMQ", "type": "message_queue"}
                ],
                "architecture_patterns": ["microservices", "api_gateway", "cqrs"],
                "metadata": {
                    "system_name": "E-Commerce Platform",
                    "version": "2.1",
                    "last_updated": datetime.now().isoformat()
                }
            }

            # Perform architecture analysis
            architecture_analysis = mock_analyzer.analyze_enterprise_architecture(enterprise_architecture_data)

            # Check compliance against enterprise standards
            compliance_results = mock_compliance_checker.check_enterprise_compliance(
                enterprise_architecture_data,
                enterprise_architecture_requirements["compliance_standards"]
            )

            # Generate reports in multiple formats
            report_formats = ["html", "pdf", "json"]
            generated_reports = {}

            for format_type in report_formats:
                report = mock_report_generator.generate_enterprise_report(
                    architecture_analysis,
                    compliance_results,
                    format_type
                )
                generated_reports[format_type] = report

            # Verify enterprise architecture analysis results
            assert "component_count" in architecture_analysis
            assert architecture_analysis["component_count"] == 7

            assert "connection_count" in architecture_analysis
            assert architecture_analysis["connection_count"] == 7

            assert "architecture_patterns" in architecture_analysis
            assert len(architecture_analysis["architecture_patterns"]) >= 3

            assert "scalability_score" in architecture_analysis
            assert 0 <= architecture_analysis["scalability_score"] <= 10

            assert "security_score" in architecture_analysis
            assert 0 <= architecture_analysis["security_score"] <= 10

            assert "recommendations" in architecture_analysis
            assert len(architecture_analysis["recommendations"]) >= 4

            # Verify compliance results
            assert len(compliance_results) == 4  # All standards checked

            for standard, result in compliance_results.items():
                assert "compliant" in result
                assert "violations" in result
                assert "recommendations" in result
                assert result["compliant"] is True  # Should pass all compliance checks

            # Verify generated reports
            assert len(generated_reports) == 3

            # HTML report
            html_report = generated_reports["html"]
            assert "<html>" in html_report
            assert "<title>Enterprise Architecture Report</title>" in html_report
            assert "Components:" in html_report
            assert "Compliance:" in html_report

            # PDF report (binary placeholder)
            pdf_report = generated_reports["pdf"]
            assert isinstance(pdf_report, bytes)

            # JSON report
            json_report = generated_reports["json"]
            parsed_json_report = json.loads(json_report)
            assert "analysis" in parsed_json_report
            assert "compliance" in parsed_json_report
            assert "generated_at" in parsed_json_report

            # Verify JSON report structure
            analysis_in_report = parsed_json_report["analysis"]
            compliance_in_report = parsed_json_report["compliance"]

            assert analysis_in_report["component_count"] == 7
            assert len(compliance_in_report) == 4

    @pytest.mark.asyncio
    async def test_architecture_visualization_and_documentation_generation(self, integration_app):
        """Test architecture visualization and automated documentation generation."""
        # Setup architecture visualization and documentation
        with patch("main.DiagramGenerator") as mock_generator_class, \
             patch("main.DocumentationGenerator") as mock_doc_class, \
             patch("main.ArchitectureVisualizer") as mock_viz_class:

            mock_generator = MagicMock()
            mock_doc_generator = MagicMock()
            mock_visualizer = MagicMock()

            mock_generator_class.return_value = mock_generator
            mock_doc_class.return_value = mock_doc_generator
            mock_viz_class.return_value = mock_visualizer

            # Configure diagram generation for different formats
            def generate_diagram_side_effect(architecture_data, format_type):
                if format_type == "plantuml":
                    return f"""@startuml Enterprise Architecture
{chr(10).join([f'component "{comp["name"]}" as {comp["name"].replace(" ", "")}' for comp in architecture_data["components"]])}
{chr(10).join([f'{conn["from"].replace(" ", "")} --> {conn["to"].replace(" ", "")}' for conn in architecture_data["connections"]])}
@enduml"""
                elif format_type == "mermaid":
                    components_md = chr(10).join([f'  {comp["name"].replace(" ", "")}[{comp["name"]}]' for comp in architecture_data["components"]])
                    connections_md = chr(10).join([f'  {conn["from"].replace(" ", "")} --> {conn["to"].replace(" ", "")}' for conn in architecture_data["connections"]])
                    return f"""graph TD
{components_md}
{connections_md}"""
                elif format_type == "drawio":
                    return f"""<mxfile>
<diagram>
{chr(10).join([f'<object label="{comp["name"]}"/>' for comp in architecture_data["components"]])}
</diagram>
</mxfile>"""
                return f"Generated {format_type} diagram"

            mock_generator.generate_diagram.side_effect = generate_diagram_side_effect

            # Configure documentation generation
            def generate_documentation_side_effect(architecture_data, doc_type):
                if doc_type == "markdown":
                    return f"""# Enterprise Architecture Documentation

## System Overview
This document describes the enterprise architecture...

## Components
{chr(10).join([f"### {comp['name']}\n- Type: {comp.get('type', 'Unknown')}\n- Technology: {comp.get('technology', 'Not specified')}\n" for comp in architecture_data["components"]])}

## Architecture Patterns
{chr(10).join([f"- {pattern}" for pattern in architecture_data.get("patterns", [])])}

## Compliance
- GDPR: Compliant
- HIPAA: Compliant
- PCI DSS: Compliant
"""
                elif doc_type == "confluence":
                    return f"""<h1>Enterprise Architecture Documentation</h1>
<p>This document describes the enterprise architecture...</p>
<h2>Components</h2>
{chr(10).join([f"<h3>{comp['name']}</h3><p>Type: {comp.get('type', 'Unknown')}</p>" for comp in architecture_data["components"]])}"""
                elif doc_type == "pdf":
                    return b"PDF_DOCUMENTATION_CONTENT_PLACEHOLDER"
                return f"Generated {doc_type} documentation"

            mock_doc_generator.generate_documentation.side_effect = generate_documentation_side_effect

            # Configure visualization
            mock_visualizer.create_interactive_diagram.return_value = {
                "html_content": "<html><body>Interactive Architecture Diagram</body></html>",
                "javascript_libs": ["d3.js", "vis.js"],
                "data_json": json.dumps({"nodes": [], "edges": []})
            }

            mock_visualizer.generate_architecture_heatmap.return_value = {
                "heatmap_data": [[0.1, 0.3, 0.8], [0.2, 0.5, 0.9], [0.4, 0.6, 0.7]],
                "component_names": ["API Gateway", "User Service", "Database"],
                "metric_name": "Coupling Strength"
            }

            # Test architecture data
            architecture_data = {
                "components": [
                    {"name": "API Gateway", "type": "api_gateway", "technology": "Kong"},
                    {"name": "User Service", "type": "microservice", "technology": "Node.js"},
                    {"name": "Order Service", "type": "microservice", "technology": "Java"},
                    {"name": "Database", "type": "database", "technology": "PostgreSQL"}
                ],
                "connections": [
                    {"from": "API Gateway", "to": "User Service", "type": "http"},
                    {"from": "API Gateway", "to": "Order Service", "type": "http"},
                    {"from": "User Service", "to": "Database", "type": "database"},
                    {"from": "Order Service", "to": "Database", "type": "database"}
                ],
                "patterns": ["microservices", "api_gateway", "database_per_service"]
            }

            # Generate diagrams in multiple formats
            diagram_formats = ["plantuml", "mermaid", "drawio"]
            generated_diagrams = {}

            for format_type in diagram_formats:
                diagram = mock_generator.generate_diagram(architecture_data, format_type)
                generated_diagrams[format_type] = diagram

            # Generate documentation in multiple formats
            doc_formats = ["markdown", "confluence", "pdf"]
            generated_docs = {}

            for doc_type in doc_formats:
                doc = mock_doc_generator.generate_documentation(architecture_data, doc_type)
                generated_docs[doc_type] = doc

            # Generate visualizations
            interactive_diagram = mock_visualizer.create_interactive_diagram(architecture_data)
            architecture_heatmap = mock_visualizer.generate_architecture_heatmap(architecture_data)

            # Verify diagram generation
            assert len(generated_diagrams) == 3

            # PlantUML diagram
            plantuml = generated_diagrams["plantuml"]
            assert "@startuml" in plantuml
            assert "@enduml" in plantuml
            assert 'component "API Gateway"' in plantuml
            assert "APIGateway --> UserService" in plantuml

            # Mermaid diagram
            mermaid = generated_diagrams["mermaid"]
            assert "graph TD" in mermaid
            assert "APIGateway[API Gateway]" in mermaid
            assert "APIGateway --> UserService" in mermaid

            # Draw.io diagram
            drawio = generated_diagrams["drawio"]
            assert "<mxfile>" in drawio
            assert '<object label="API Gateway"/>' in drawio

            # Verify documentation generation
            assert len(generated_docs) == 3

            # Markdown documentation
            markdown_doc = generated_docs["markdown"]
            assert "# Enterprise Architecture Documentation" in markdown_doc
            assert "### API Gateway" in markdown_doc
            assert "- microservices" in markdown_doc
            assert "- GDPR: Compliant" in markdown_doc

            # Confluence documentation
            confluence_doc = generated_docs["confluence"]
            assert "<h1>Enterprise Architecture Documentation</h1>" in confluence_doc
            assert "<h3>API Gateway</h3>" in confluence_doc

            # PDF documentation
            pdf_doc = generated_docs["pdf"]
            assert isinstance(pdf_doc, bytes)

            # Verify visualizations
            assert "html_content" in interactive_diagram
            assert "javascript_libs" in interactive_diagram
            assert "data_json" in interactive_diagram
            assert "<html>" in interactive_diagram["html_content"]
            assert "d3.js" in interactive_diagram["javascript_libs"]

            assert "heatmap_data" in architecture_heatmap
            assert "component_names" in architecture_heatmap
            assert "metric_name" in architecture_heatmap
            assert len(architecture_heatmap["heatmap_data"]) == 3
            assert architecture_heatmap["metric_name"] == "Coupling Strength"
