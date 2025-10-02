#!/usr/bin/env python3
"""
Docker Configuration Validation Script

Uses Pydantic to validate and reinforce Docker configurations including:
- docker-compose.yml files
- Dockerfile validation
- Container configurations
- Build contexts
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.shared.infrastructure.config.docker_pydantic import (
    validate_docker_compose_file, validate_dockerfile, validate_container_config,
    DockerComposeConfig, DockerfileConfig, DockerImageReference, PortMapping,
    PYDANTIC_AVAILABLE
)


def validate_project_docker_configs() -> Dict[str, Any]:
    """
    Validate all Docker configurations in the project.

    Returns:
        Dictionary with validation results
    """
    if not PYDANTIC_AVAILABLE:
        return {"error": "Pydantic not available for Docker validation"}

    results = {
        "docker_compose_files": {},
        "dockerfiles": {},
        "container_configs": {},
        "summary": {"valid": 0, "invalid": 0, "total": 0}
    }

    # Find all docker-compose.yml files
    compose_files = list(project_root.glob("**/docker-compose*.yml"))
    compose_files.extend(list(project_root.glob("**/docker-compose*.yaml")))

    print("🔍 Validating Docker Compose files...")
    for compose_file in compose_files:
        service_name = compose_file.parent.name
        try:
            config = validate_docker_compose_file(compose_file)
            results["docker_compose_files"][service_name] = {
                "status": "valid",
                "services": len(config.services),
                "networks": len(config.networks),
                "volumes": len(config.volumes)
            }
            results["summary"]["valid"] += 1
            print(f"  ✅ {service_name}: {len(config.services)} services")
        except Exception as e:
            results["docker_compose_files"][service_name] = {
                "status": "invalid",
                "error": str(e)
            }
            results["summary"]["invalid"] += 1
            print(f"  ❌ {service_name}: {str(e)[:100]}...")

    # Find all Dockerfiles
    dockerfiles = list(project_root.glob("**/Dockerfile"))
    dockerfiles.extend(list(project_root.glob("**/Dockerfile.*")))

    print("\n🔍 Validating Dockerfiles...")
    for dockerfile in dockerfiles:
        service_name = dockerfile.parent.name
        try:
            config = validate_dockerfile(dockerfile)
            results["dockerfiles"][service_name] = {
                "status": "valid",
                "instructions": len(config.instructions)
            }
            results["summary"]["valid"] += 1
            print(f"  ✅ {service_name}: {len(config.instructions)} instructions")
        except Exception as e:
            results["dockerfiles"][service_name] = {
                "status": "invalid",
                "error": str(e)
            }
            results["summary"]["invalid"] += 1
            print(f"  ❌ {service_name}: {str(e)[:100]}...")

    results["summary"]["total"] = results["summary"]["valid"] + results["summary"]["invalid"]

    return results


def demonstrate_docker_validation() -> None:
    """Demonstrate various Docker validation capabilities."""
    print("🚀 Docker Configuration Validation Demo")
    print("=" * 50)

    if not PYDANTIC_AVAILABLE:
        print("❌ Pydantic not available - cannot demonstrate Docker validation")
        return

    # Test 1: Validate a docker-compose.yml structure
    print("\n1. 🐳 Docker Compose Validation")
    print("-" * 30)

    sample_compose = {
        "version": "3.8",
        "services": {
            "web": {
                "image": "nginx:latest",
                "ports": ["80:80", "443:443"],
                "volumes": ["/host/logs:/var/log/nginx"],
                "environment": ["DEBUG=false", "API_PORT=80"],
                "healthcheck": {
                    "test": ["CMD", "curl", "-f", "http://localhost"],
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3
                }
            },
            "db": {
                "image": "postgres:13",
                "environment": ["POSTGRES_PASSWORD=mypass"],
                "volumes": ["db_data:/var/lib/postgresql/data"],
                "healthcheck": {
                    "test": ["CMD-SHELL", "pg_isready -U postgres"],
                    "interval": "10s"
                }
            }
        },
        "volumes": {
            "db_data": {}
        }
    }

    try:
        config = DockerComposeConfig(**sample_compose)
        print("✅ Valid Docker Compose configuration")
        print(f"   Services: {len(config.services)}")
        print(f"   Networks: {len(config.networks)}")
        print(f"   Volumes: {len(config.volumes)}")
    except Exception as e:
        print(f"❌ Invalid Docker Compose: {e}")

    # Test 2: Validate container configurations
    print("\n2. 📦 Container Configuration Validation")
    print("-" * 40)

    container_configs = [
        {
            "name": "web-server",
            "image": "nginx:1.21",
            "ports": ["8080:80", "8443:443"],
            "volumes": ["/tmp/logs:/var/log/nginx:ro"],
            "env_vars": {"DEBUG": "false", "API_PORT": "80"}
        },
        {
            "name": "database",
            "image": "postgres:15",
            "ports": ["5432:5432"],
            "volumes": ["/tmp/data:/var/lib/postgresql/data"],
            "env_vars": {"POSTGRES_DB": "mydb", "POSTGRES_USER": "admin"}
        }
    ]

    for container in container_configs:
        try:
            validated = validate_container_config(
                image=container["image"],
                ports=container["ports"],
                volumes=container["volumes"],
                env_vars=container["env_vars"]
            )
            print(f"✅ {container['name']}: {container['image']}")
        except Exception as e:
            print(f"❌ {container['name']}: {e}")

    # Test 3: Validate Docker image references
    print("\n3. 🖼️  Docker Image Reference Validation")
    print("-" * 35)

    image_refs = [
        "nginx:latest",
        "postgres:15-alpine",
        "myregistry.com/myapp:v1.2.3",
        "ubuntu:20.04",
        "invalid image name!",  # Should fail
        "nginx",  # Should work (defaults to latest)
    ]

    for ref in image_refs:
        try:
            # Parse image reference (simplified parsing)
            if ":" in ref:
                repo, tag = ref.rsplit(":", 1)
            else:
                repo, tag = ref, "latest"

            if "/" in repo:
                registry, repository = repo.rsplit("/", 1)
            else:
                registry, repository = None, repo

            img = DockerImageReference(repository=repository, tag=tag, registry=registry)
            print(f"✅ {ref} → {img.to_string()}")
        except Exception as e:
            print(f"❌ {ref}: {e}")

    # Test 4: Port mapping validation
    print("\n4. 🔌 Port Mapping Validation")
    print("-" * 25)

    port_mappings = [
        {"host": 8080, "container": 80, "protocol": "tcp"},
        {"host": 8443, "container": 443, "protocol": "tcp"},
        {"host": 53, "container": 53, "protocol": "udp"},
        {"host": 70000, "container": 80, "protocol": "tcp"},  # Should fail - invalid port
    ]

    for mapping in port_mappings:
        try:
            port = PortMapping(
                host_port=mapping["host"],
                container_port=mapping["container"],
                protocol=mapping["protocol"]
            )
            print(f"✅ {mapping['host']}:{mapping['container']}/{mapping['protocol']} → {port.to_docker_format()}")
        except Exception as e:
            print(f"❌ {mapping['host']}:{mapping['container']}: {e}")


def show_docker_validation_benefits() -> None:
    """Show the benefits of using Pydantic for Docker validation."""
    print("\n" + "=" * 60)
    print("🎯 PYDANTIC DOCKER VALIDATION BENEFITS")
    print("=" * 60)

    benefits = [
        ("🔍 Type Safety", "Validate Docker configurations at development time"),
        ("🚫 Error Prevention", "Catch misconfigurations before docker-compose up"),
        ("📚 Documentation", "Self-documenting configuration schemas"),
        ("🔧 IDE Support", "Autocomplete and validation in your editor"),
        ("⚡ CI/CD Integration", "Validate configurations in your pipeline"),
        ("🏗️ Infrastructure as Code", "Programmatically generate valid Docker configs"),
        ("🔄 Migration Safety", "Validate changes before deployment"),
        ("📊 Monitoring", "Track configuration patterns and issues")
    ]

    for benefit, description in benefits:
        print("<15")

    print("\n" + "=" * 60)
    print("💡 PRACTICAL APPLICATIONS")
    print("=" * 60)

    applications = [
        "Validate docker-compose.yml before deployment",
        "Ensure Dockerfile follows best practices",
        "Check container resource limits and configurations",
        "Validate environment variable formats and values",
        "Verify network and volume configurations",
        "Generate Docker configurations from templates",
        "CI/CD pipeline validation gates",
        "Infrastructure configuration drift detection"
    ]

    for app in applications:
        print(f"  • {app}")

    print("\n" + "=" * 60)
    print("🚀 INTEGRATION WITH EXISTING WORKFLOW")
    print("=" * 60)

    integration_steps = [
        "1. Add Pydantic validation to docker-compose config loading",
        "2. Integrate with existing Makefile docker-* targets",
        "3. Add pre-deployment validation hooks",
        "4. Generate configuration documentation automatically",
        "5. Monitor configuration patterns in production"
    ]

    for step in integration_steps:
        print(f"  {step}")


def main():
    """Main validation script."""
    try:
        # Run comprehensive validation
        results = validate_project_docker_configs()

        if "error" in results:
            print(f"❌ {results['error']}")
            return

        # Show results
        print("\n" + "=" * 60)
        print("📊 DOCKER CONFIGURATION VALIDATION RESULTS")
        print("=" * 60)

        summary = results["summary"]
        print(f"Total Files Validated: {summary['total']}")
        print(f"Valid Configurations: {summary['valid']}")
        print(f"Invalid Configurations: {summary['invalid']}")
        print(".1f")

        if summary["invalid"] > 0:
            print("\n❌ Issues Found:")
            for category, items in results.items():
                if category != "summary" and isinstance(items, dict):
                    for name, item in items.items():
                        if item.get("status") == "invalid":
                            print(f"  • {category}.{name}: {item.get('error', 'Unknown error')[:100]}...")

        # Run demonstration
        demonstrate_docker_validation()

        # Show benefits
        show_docker_validation_benefits()

        print("\n" + "=" * 60)
        print("✅ DOCKER CONFIGURATION VALIDATION COMPLETE")
        print("=" * 60)

        # Exit with appropriate code
        if summary["invalid"] > 0:
            print("⚠️  Some configurations have validation issues")
            sys.exit(1)
        else:
            print("🎉 All Docker configurations are valid!")
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
