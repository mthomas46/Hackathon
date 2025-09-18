#!/usr/bin/env python3
"""
Docker Standardization and Port Management System
Standardizes Docker configurations and prevents port mapping issues
"""

import yaml
import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import subprocess
from pathlib import Path
import sys


@dataclass
class ServicePortConfig:
    """Configuration for service port mappings"""
    service_name: str
    external_port: int
    internal_port: int
    protocol: str = "tcp"
    health_endpoint: str = "/health"
    required_for_production: bool = True


@dataclass
class ServiceConfig:
    """Complete service configuration"""
    name: str
    port_config: ServicePortConfig
    dependencies: List[str]
    environment_vars: Dict[str, str]
    health_check: Dict[str, Any]
    volumes: List[str] = None
    profiles: List[str] = None


class DockerStandardizationManager:
    """Manages Docker standardization and port mapping consistency"""
    
    def __init__(self):
        self.services_config = self._load_services_config()
        self.port_registry = self._build_port_registry()
        
    def _load_services_config(self) -> Dict[str, ServiceConfig]:
        """Load standardized service configurations"""
        return {
            "redis": ServiceConfig(
                name="redis",
                port_config=ServicePortConfig(
                    service_name="redis",
                    external_port=6379,
                    internal_port=6379,
                    protocol="tcp",
                    health_endpoint="/",
                    required_for_production=True
                ),
                dependencies=[],
                environment_vars={},
                health_check={
                    "test": ["CMD", "redis-cli", "ping"],
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3
                },
                profiles=["core", "development", "production"]
            ),
            "doc_store": ServiceConfig(
                name="doc_store",
                port_config=ServicePortConfig(
                    service_name="doc_store",
                    external_port=5087,
                    internal_port=5010,
                    health_endpoint="/health"
                ),
                dependencies=["redis"],
                environment_vars={
                    "SERVICE_PORT": "5010",
                    "REDIS_URL": "redis://redis:6379"
                },
                health_check={
                    "test": ["CMD", "curl", "-f", "http://localhost:5010/health"],
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3
                },
                profiles=["core", "development", "production"]
            ),
            "orchestrator": ServiceConfig(
                name="orchestrator",
                port_config=ServicePortConfig(
                    service_name="orchestrator",
                    external_port=5099,
                    internal_port=5099,
                    health_endpoint="/health"
                ),
                dependencies=["redis"],
                environment_vars={
                    "SERVICE_PORT": "5099",
                    "REDIS_URL": "redis://redis:6379"
                },
                health_check={
                    "test": ["CMD", "curl", "-f", "http://localhost:5099/health"],
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3
                },
                profiles=["core", "development", "production"]
            ),
            "llm-gateway": ServiceConfig(
                name="llm-gateway",
                port_config=ServicePortConfig(
                    service_name="llm-gateway",
                    external_port=5055,
                    internal_port=5055,
                    health_endpoint="/health"
                ),
                dependencies=["ollama"],
                environment_vars={
                    "SERVICE_PORT": "5055",
                    "OLLAMA_ENDPOINT": "http://ollama:11434"
                },
                health_check={
                    "test": ["CMD", "curl", "-f", "http://localhost:5055/health"],
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3
                },
                profiles=["ai_services", "development", "production"]
            ),
            "analysis-service": ServiceConfig(
                name="analysis-service",
                port_config=ServicePortConfig(
                    service_name="analysis-service",
                    external_port=5080,
                    internal_port=5020,  # Fixed mapping issue
                    health_endpoint="/health"
                ),
                dependencies=["doc_store", "llm-gateway"],
                environment_vars={
                    "SERVICE_PORT": "5020",  # Internal port
                    "DOC_STORE_URL": "http://doc_store:5010",
                    "LLM_GATEWAY_URL": "http://llm-gateway:5055"
                },
                health_check={
                    "test": ["CMD", "curl", "-f", "http://localhost:5020/health"],
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3
                },
                profiles=["ai_services", "development", "production"]
            ),
            "discovery-agent": ServiceConfig(
                name="discovery-agent",
                port_config=ServicePortConfig(
                    service_name="discovery-agent",
                    external_port=5045,
                    internal_port=5045,
                    health_endpoint="/health"
                ),
                dependencies=["orchestrator"],
                environment_vars={
                    "SERVICE_PORT": "5045",
                    "ORCHESTRATOR_URL": "http://orchestrator:5099"
                },
                health_check={
                    "test": ["CMD", "curl", "-f", "http://localhost:5045/health"],
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3
                },
                profiles=["ai_services", "development", "production"]
            ),
            "notification-service": ServiceConfig(
                name="notification-service",
                port_config=ServicePortConfig(
                    service_name="notification-service",
                    external_port=5130,
                    internal_port=5020,  # Fixed port configuration
                    health_endpoint="/health"
                ),
                dependencies=[],
                environment_vars={
                    "SERVICE_PORT": "5020"
                },
                health_check={
                    "test": ["CMD", "curl", "-f", "http://localhost:5020/health"],
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3
                },
                profiles=["core", "development", "production"]
            ),
            "code-analyzer": ServiceConfig(
                name="code-analyzer",
                port_config=ServicePortConfig(
                    service_name="code-analyzer",
                    external_port=5025,
                    internal_port=5025,
                    health_endpoint="/health"
                ),
                dependencies=[],
                environment_vars={
                    "SERVICE_PORT": "5025"
                },
                health_check={
                    "test": ["CMD", "curl", "-f", "http://localhost:5025/health"],
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3
                },
                profiles=["ai_services", "development"]
            ),
            "source-agent": ServiceConfig(
                name="source-agent",
                port_config=ServicePortConfig(
                    service_name="source-agent",
                    external_port=5085,
                    internal_port=5070,  # Fixed internal port
                    health_endpoint="/health"
                ),
                dependencies=["doc_store"],
                environment_vars={
                    "SERVICE_PORT": "5070",
                    "DOC_STORE_URL": "http://doc_store:5010"
                },
                health_check={
                    "test": ["CMD", "curl", "-f", "http://localhost:5070/health"],
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3
                },
                profiles=["ai_services", "development"]
            ),
            "frontend": ServiceConfig(
                name="frontend",
                port_config=ServicePortConfig(
                    service_name="frontend",
                    external_port=3000,
                    internal_port=3000,
                    health_endpoint="/"
                ),
                dependencies=["orchestrator"],
                environment_vars={
                    "REACT_APP_API_URL": "http://localhost:5099"
                },
                health_check={
                    "test": ["CMD", "curl", "-f", "http://localhost:3000"],
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3
                },
                profiles=["development", "production"]
            ),
            "ollama": ServiceConfig(
                name="ollama",
                port_config=ServicePortConfig(
                    service_name="ollama",
                    external_port=11434,
                    internal_port=11434,
                    health_endpoint="/api/tags"
                ),
                dependencies=[],
                environment_vars={},
                health_check={
                    "test": ["CMD", "curl", "-f", "http://localhost:11434/api/tags"],
                    "interval": "60s",
                    "timeout": "30s",
                    "retries": 3
                },
                profiles=["ai_services", "development", "production"]
            )
        }
    
    def _build_port_registry(self) -> Dict[int, str]:
        """Build port registry to detect conflicts"""
        registry = {}
        for service_name, config in self.services_config.items():
            port = config.port_config.external_port
            if port in registry:
                raise ValueError(f"Port conflict: {port} used by both {registry[port]} and {service_name}")
            registry[port] = service_name
        return registry
    
    def validate_port_consistency(self) -> Dict[str, Any]:
        """Validate port configurations for consistency"""
        validation_results = {
            "port_conflicts": [],
            "configuration_issues": [],
            "recommendations": []
        }
        
        # Check for port conflicts
        used_ports = {}
        for service_name, config in self.services_config.items():
            ext_port = config.port_config.external_port
            int_port = config.port_config.internal_port
            
            if ext_port in used_ports:
                validation_results["port_conflicts"].append({
                    "port": ext_port,
                    "services": [used_ports[ext_port], service_name],
                    "severity": "critical"
                })
            else:
                used_ports[ext_port] = service_name
            
            # Check for mismatched internal/external ports that could cause issues
            if ext_port != int_port:
                validation_results["configuration_issues"].append({
                    "service": service_name,
                    "issue": f"Port mapping {ext_port}:{int_port} - ensure health checks use internal port",
                    "severity": "medium"
                })
        
        # Generate recommendations
        if validation_results["port_conflicts"]:
            validation_results["recommendations"].append("Resolve port conflicts before deployment")
        
        if validation_results["configuration_issues"]:
            validation_results["recommendations"].append("Update health check endpoints to use correct internal ports")
        
        return validation_results
    
    def generate_docker_compose(self, environment: str = "development") -> str:
        """Generate standardized Docker Compose file"""
        
        compose_config = {
            "version": "3.8",
            "services": {},
            "networks": {
                "hackathon": {
                    "driver": "bridge"
                }
            },
            "profiles": {}
        }
        
        # Add services to compose config
        for service_name, config in self.services_config.items():
            if environment in config.profiles:
                service_def = self._generate_service_definition(config, environment)
                compose_config["services"][service_name] = service_def
        
        return yaml.dump(compose_config, default_flow_style=False, sort_keys=False)
    
    def _generate_service_definition(self, config: ServiceConfig, environment: str) -> Dict[str, Any]:
        """Generate Docker Compose service definition"""
        
        service_def = {
            "container_name": f"hackathon-{config.name}-1",
            "build": f"./services/{config.name}",
            "networks": ["hackathon"],
            "ports": [f"{config.port_config.external_port}:{config.port_config.internal_port}"],
            "environment": config.environment_vars,
            "healthcheck": config.health_check,
            "profiles": config.profiles,
            "restart": "unless-stopped"
        }
        
        # Add dependencies
        if config.dependencies:
            service_def["depends_on"] = config.dependencies
        
        # Add volumes if specified
        if config.volumes:
            service_def["volumes"] = config.volumes
        
        # Environment-specific overrides
        if environment == "production":
            service_def["restart"] = "always"
            service_def["logging"] = {
                "driver": "json-file",
                "options": {
                    "max-size": "10m",
                    "max-file": "3"
                }
            }
        
        return service_def
    
    def update_service_dockerfiles(self) -> Dict[str, Any]:
        """Update service Dockerfiles to match port configurations"""
        update_results = {
            "updated_services": [],
            "errors": [],
            "recommendations": []
        }
        
        for service_name, config in self.services_config.items():
            dockerfile_path = f"/Users/mykalthomas/Documents/work/Hackathon/services/{service_name}/Dockerfile"
            
            if os.path.exists(dockerfile_path):
                try:
                    # Read current Dockerfile
                    with open(dockerfile_path, 'r') as f:
                        dockerfile_content = f.read()
                    
                    # Update port configurations
                    updated_content = self._update_dockerfile_ports(
                        dockerfile_content, config.port_config
                    )
                    
                    # Write updated Dockerfile
                    with open(dockerfile_path, 'w') as f:
                        f.write(updated_content)
                    
                    update_results["updated_services"].append(service_name)
                    
                except Exception as e:
                    update_results["errors"].append({
                        "service": service_name,
                        "error": str(e)
                    })
            else:
                update_results["errors"].append({
                    "service": service_name,
                    "error": "Dockerfile not found"
                })
        
        return update_results
    
    def _update_dockerfile_ports(self, dockerfile_content: str, port_config: ServicePortConfig) -> str:
        """Update Dockerfile port configurations"""
        lines = dockerfile_content.split('\n')
        updated_lines = []
        
        for line in lines:
            # Update EXPOSE directive
            if line.strip().startswith('EXPOSE'):
                updated_lines.append(f"EXPOSE {port_config.internal_port}")
            
            # Update port label
            elif 'LABEL port=' in line:
                updated_lines.append(f'LABEL port="{port_config.internal_port}"')
            
            # Update SERVICE_PORT environment variable
            elif 'ENV SERVICE_PORT=' in line:
                updated_lines.append(f"ENV SERVICE_PORT={port_config.internal_port}")
            
            # Update health check URL
            elif 'HEALTHCHECK' in line and 'curl' in line:
                if port_config.health_endpoint != "/":
                    health_url = f"http://localhost:{port_config.internal_port}{port_config.health_endpoint}"
                    updated_line = line.replace(
                        "http://localhost:[0-9]+/[^ ]*",
                        health_url
                    )
                    updated_lines.append(updated_line)
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        
        return '\n'.join(updated_lines)
    
    def create_port_mapping_documentation(self) -> str:
        """Create comprehensive port mapping documentation"""
        
        doc = "# Service Port Mappings\n\n"
        doc += "This document defines the standardized port mappings for all ecosystem services.\n\n"
        
        doc += "## Port Registry\n\n"
        doc += "| Service | External Port | Internal Port | Health Endpoint | Required for Production |\n"
        doc += "|---------|---------------|---------------|-----------------|------------------------|\n"
        
        for service_name, config in self.services_config.items():
            port_cfg = config.port_config
            required = "✅" if port_cfg.required_for_production else "❌"
            doc += f"| {service_name} | {port_cfg.external_port} | {port_cfg.internal_port} | {port_cfg.health_endpoint} | {required} |\n"
        
        doc += "\n## Service Dependencies\n\n"
        for service_name, config in self.services_config.items():
            if config.dependencies:
                doc += f"- **{service_name}**: depends on {', '.join(config.dependencies)}\n"
        
        doc += "\n## Environment Variables\n\n"
        for service_name, config in self.services_config.items():
            if config.environment_vars:
                doc += f"### {service_name}\n"
                for var, value in config.environment_vars.items():
                    doc += f"- `{var}`: {value}\n"
                doc += "\n"
        
        return doc
    
    def export_configurations(self, output_dir: str = "/Users/mykalthomas/Documents/work/Hackathon/config/standardized"):
        """Export all standardized configurations"""
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Export port registry
        port_registry = {
            service_name: {
                "external_port": config.port_config.external_port,
                "internal_port": config.port_config.internal_port,
                "health_endpoint": config.port_config.health_endpoint,
                "dependencies": config.dependencies,
                "environment_vars": config.environment_vars
            }
            for service_name, config in self.services_config.items()
        }
        
        with open(f"{output_dir}/port_registry.json", "w") as f:
            json.dump(port_registry, f, indent=2)
        
        # Export Docker Compose files for different environments
        for env in ["development", "production"]:
            compose_content = self.generate_docker_compose(env)
            with open(f"{output_dir}/docker-compose.{env}.yml", "w") as f:
                f.write(compose_content)
        
        # Export port documentation
        port_docs = self.create_port_mapping_documentation()
        with open(f"{output_dir}/PORT_MAPPINGS.md", "w") as f:
            f.write(port_docs)
        
        print(f"✅ Configurations exported to: {output_dir}")

    def run_port_conflict_detection(self):
        """Run comprehensive port conflict detection using the dedicated detector"""
        try:
            # Import the port conflict detector
            from port_conflict_detector import PortConflictDetector

            print("\n🔍 Running Port Conflict Detection...")

            # Initialize detector with current docker-compose file
            detector = PortConflictDetector()

            # Run comprehensive analysis
            report = detector.run_comprehensive_analysis()

            # Print summary
            summary = report["summary"]
            if summary["total_conflicts"] > 0:
                print(f"🚨 Found {summary['total_conflicts']} port conflicts")
                print(f"   Critical: {summary['critical_conflicts']}")
                print(f"   High Priority: {summary['high_conflicts']}")

                # Show top conflicts
                for i, conflict in enumerate(report["conflicts"][:5]):  # Show first 5
                    severity_icon = "🔴" if conflict["severity"] == "critical" else "🟠"
                    print(f"   {severity_icon} Port {conflict['port']}: {', '.join(conflict['services'])}")

                if len(report["conflicts"]) > 5:
                    print(f"   ... and {len(report['conflicts']) - 5} more conflicts")

            else:
                print("✅ No port conflicts detected")

            # Show recommendations
            if report["recommendations"]:
                print(f"\n💡 {len(report['recommendations'])} optimization recommendations available")

            return report

        except ImportError:
            print("⚠️ Port conflict detector not available - install required dependencies")
            return None
        except Exception as e:
            print(f"❌ Port conflict detection failed: {e}")
            return None

    def validate_with_conflict_detection(self):
        """Enhanced validation that includes port conflict detection"""
        print("🔍 Enhanced Docker Validation with Conflict Detection")
        print("=" * 55)

        # Run existing validation
        validation = self.validate_port_consistency()

        # Run port conflict detection
        conflict_report = self.run_port_conflict_detection()

        # Combine results
        combined_validation = {
            "port_conflicts": validation["port_conflicts"],
            "configuration_issues": validation["configuration_issues"],
            "recommendations": validation["recommendations"],
            "conflict_detection": conflict_report
        }

        return combined_validation


def main():
    """Main Docker standardization execution"""
    manager = DockerStandardizationManager()

    # Check command line arguments for enhanced validation
    if len(sys.argv) > 1 and sys.argv[1] == "--check-drift":
        # Run enhanced validation with conflict detection
        validation = manager.validate_with_conflict_detection()
    else:
        # Run standard validation
        print("🐳 Docker Standardization and Port Management")
        print("=" * 50)
        validation = manager.validate_port_consistency()
    
    if validation["port_conflicts"]:
        print("\n🚨 PORT CONFLICTS DETECTED:")
        for conflict in validation["port_conflicts"]:
            print(f"  ❌ Port {conflict['port']}: {', '.join(conflict['services'])}")
    
    if validation["configuration_issues"]:
        print("\n⚠️ CONFIGURATION ISSUES:")
        for issue in validation["configuration_issues"]:
            print(f"  ⚠️ {issue['service']}: {issue['issue']}")
    
    if validation["recommendations"]:
        print("\n💡 RECOMMENDATIONS:")
        for rec in validation["recommendations"]:
            print(f"  • {rec}")
    
    # Export standardized configurations
    manager.export_configurations()
    
    # Update Dockerfiles
    update_results = manager.update_service_dockerfiles()
    
    print(f"\n📝 DOCKERFILE UPDATES:")
    print(f"  Updated: {len(update_results['updated_services'])} services")
    print(f"  Errors: {len(update_results['errors'])} services")
    
    if update_results["errors"]:
        print("\n❌ UPDATE ERRORS:")
        for error in update_results["errors"]:
            print(f"  • {error['service']}: {error['error']}")


if __name__ == "__main__":
    main()
