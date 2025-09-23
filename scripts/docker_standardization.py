#!/usr/bin/env python3
"""
Docker Compose Standardization Script

This script standardizes the docker-compose.dev.yml file to ensure all services
follow consistent patterns and best practices.

Usage:
    python scripts/docker_standardization.py
"""

import re
from pathlib import Path
from typing import Any, Dict, List

import yaml


class DockerComposeStandardizer:
    """Standardizes docker-compose.dev.yml configurations."""

    def __init__(self, compose_file: str = "docker-compose.dev.yml"):
        self.compose_file = Path(compose_file)
        self.data = None

    def load_compose_file(self) -> Dict[str, Any]:
        """Load the docker-compose file."""
        with open(self.compose_file, "r") as f:
            self.data = yaml.safe_load(f)
        return self.data

    def save_compose_file(self) -> None:
        """Save the docker-compose file."""
        with open(self.compose_file, "w") as f:
            yaml.dump(self.data, f, default_flow_style=False, sort_keys=False)

    def standardize_service(self, service_name: str, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize a single service configuration."""
        standardized = service_config.copy()

        # Ensure environment variables are in list format
        if "environment" in standardized:
            env_vars = standardized["environment"]
            if isinstance(env_vars, dict):
                # Convert dict to list format
                standardized["environment"] = [f"{k}={v}" for k, v in env_vars.items()]
            elif isinstance(env_vars, list):
                # Ensure consistent format (KEY=value)
                standardized["environment"] = [env if "=" in str(env) else f"{env}=${{{env}}}" for env in env_vars]

        # Add missing standard environment variables
        standard_env = {"PYTHONPATH": "/app", "REDIS_HOST": "redis", "ENVIRONMENT": "development"}

        if "environment" not in standardized:
            standardized["environment"] = []

        existing_env = {}
        for env in standardized["environment"]:
            if "=" in env:
                key, value = env.split("=", 1)
                existing_env[key] = value

        # Add missing standard environment variables
        for key, default_value in standard_env.items():
            if key not in existing_env:
                standardized["environment"].append(f"{key}={default_value}")

        # Add SERVICE_PORT if ports are defined
        if "ports" in standardized and len(standardized["ports"]) > 0:
            port_mapping = standardized["ports"][0]
            if ":" in port_mapping:
                external, internal = port_mapping.split(":")
                if "SERVICE_PORT" not in existing_env:
                    standardized["environment"].append(f"SERVICE_PORT={internal}")

        # Standardize healthcheck
        if "healthcheck" in standardized:
            healthcheck = standardized["healthcheck"]

            # Add missing standard fields
            if "start_period" not in healthcheck:
                healthcheck["start_period"] = "40s"

            # Ensure consistent field order
            standardized["healthcheck"] = {
                "test": healthcheck.get("test", ["CMD", "curl", "-f", "http://localhost:8000/health"]),
                "interval": healthcheck.get("interval", "30s"),
                "timeout": healthcheck.get("timeout", "10s"),
                "retries": healthcheck.get("retries", 3),
                "start_period": healthcheck.get("start_period", "40s"),
            }

        # Add restart policy if missing
        if "restart" not in standardized:
            standardized["restart"] = "unless-stopped"

        # Ensure volumes are properly formatted
        if "volumes" in standardized:
            volumes = standardized["volumes"]
            if isinstance(volumes, list):
                # Ensure named volumes have proper format
                standardized_volumes = []
                for volume in volumes:
                    if isinstance(volume, str):
                        standardized_volumes.append(volume)
                    elif isinstance(volume, dict):
                        # Handle bind mounts and named volumes
                        standardized_volumes.append(volume)
                standardized["volumes"] = standardized_volumes

        # Add log volume if service has data volume but no log volume
        if "volumes" in standardized:
            has_data_volume = any(f"{service_name}_data:" in str(v) for v in standardized["volumes"])
            has_log_volume = any(f"{service_name}_logs:" in str(v) for v in standardized["volumes"])

            if has_data_volume and not has_log_volume:
                standardized["volumes"].append(f"{service_name}_logs:/app/logs")

        return standardized

    def add_missing_volumes(self) -> None:
        """Add missing volume definitions."""
        if "volumes" not in self.data:
            self.data["volumes"] = {}

        services = self.data.get("services", {})

        for service_name, service_config in services.items():
            if "volumes" in service_config:
                for volume in service_config["volumes"]:
                    if isinstance(volume, str) and ":" in volume:
                        volume_name = volume.split(":")[0]
                        if volume_name not in self.data["volumes"]:
                            self.data["volumes"][volume_name] = {"driver": "local"}

    def standardize_all_services(self) -> None:
        """Standardize all services in the compose file."""
        services = self.data.get("services", {})

        for service_name, service_config in services.items():
            if service_name not in ["redis"]:  # Skip redis as it has different structure
                standardized_config = self.standardize_service(service_name, service_config)
                self.data["services"][service_name] = standardized_config

        self.add_missing_volumes()

    def validate_standardization(self) -> List[str]:
        """Validate that standardization was successful."""
        issues = []
        services = self.data.get("services", {})

        for service_name, service_config in services.items():
            # Check for required fields
            required_fields = ["environment", "restart"]
            for field in required_fields:
                if field not in service_config:
                    issues.append(f"Service {service_name}: missing {field}")

            # Check environment variables
            if "environment" in service_config:
                env_vars = service_config["environment"]
                required_env = ["PYTHONPATH", "ENVIRONMENT"]
                existing_env = []
                for env in env_vars:
                    if "=" in str(env):
                        key = str(env).split("=")[0]
                        existing_env.append(key)

                for req_env in required_env:
                    if req_env not in existing_env:
                        issues.append(f"Service {service_name}: missing environment variable {req_env}")

            # Check healthcheck
            if "healthcheck" in service_config:
                healthcheck = service_config["healthcheck"]
                required_health_fields = ["interval", "timeout", "retries", "start_period"]
                for field in required_health_fields:
                    if field not in healthcheck:
                        issues.append(f"Service {service_name}: healthcheck missing {field}")

        return issues

    def run_standardization(self) -> None:
        """Run the complete standardization process."""
        print("🔧 Loading docker-compose.dev.yml...")
        self.load_compose_file()

        print("📋 Standardizing services...")
        self.standardize_all_services()

        print("✅ Validating standardization...")
        issues = self.validate_standardization()

        if issues:
            print("⚠️  Found issues:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("✅ All services standardized successfully!")

        print("💾 Saving standardized configuration...")
        self.save_compose_file()

        print("🎉 Docker Compose standardization complete!")


def main():
    """Main entry point."""
    standardizer = DockerComposeStandardizer()
    standardizer.run_standardization()


if __name__ == "__main__":
    main()
