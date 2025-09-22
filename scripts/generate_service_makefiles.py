#!/usr/bin/env python3
"""
Service Makefile Generator

Generates standardized Makefiles for all services that don't have them,
based on the template and service configuration.
"""

import os
import re
from pathlib import Path
import yaml


class MakefileGenerator:
    """Generates Makefiles for services."""

    def __init__(self, template_path: str = "services/_template/Makefile.template"):
        self.template_path = Path(template_path)
        self.services_dir = Path("services")
        self.compose_file = Path("docker-compose.dev.yml")

        # Load the template
        with open(self.template_path, 'r') as f:
            self.template = f.read()

        # Load docker-compose to get service configurations
        with open(self.compose_file, 'r') as f:
            self.compose_data = yaml.safe_load(f)

    def get_service_port(self, service_name: str) -> str:
        """Get the internal port for a service from docker-compose."""
        services = self.compose_data.get('services', {})
        if service_name in services:
            service_config = services[service_name]
            ports = service_config.get('ports', [])
            if ports and isinstance(ports, list) and len(ports) > 0:
                port_mapping = str(ports[0])
                if ':' in port_mapping:
                    # Format: "external:internal"
                    parts = port_mapping.split(':')
                    if len(parts) == 2:
                        return parts[1].strip('"\']')
        return "8080"  # Default port

    def get_docker_profile(self, service_name: str) -> str:
        """Get the appropriate docker-compose profile for a service."""
        services = self.compose_data.get('services', {})
        if service_name in services:
            service_config = services[service_name]
            profiles = service_config.get('profiles', [])

            # Priority order for profiles
            profile_priority = ['core', 'development', 'ai_services', 'simulation', 'production']

            for profile in profile_priority:
                if profile in profiles:
                    return profile

        return 'development'  # Default profile

    def generate_makefile(self, service_name: str) -> str:
        """Generate a Makefile for a specific service."""
        port = self.get_service_port(service_name)
        profile = self.get_docker_profile(service_name)

        # Replace template variables
        makefile_content = self.template
        makefile_content = makefile_content.replace('{{SERVICE_NAME}}', service_name)
        makefile_content = makefile_content.replace('{{SERVICE_PORT}}', port)
        makefile_content = makefile_content.replace('{{DOCKER_PROFILE}}', profile)

        return makefile_content

    def needs_makefile(self, service_name: str) -> bool:
        """Check if a service needs a Makefile."""
        makefile_path = self.services_dir / service_name / "Makefile"
        return not makefile_path.exists()

    def generate_all_makefiles(self) -> None:
        """Generate Makefiles for all services that need them."""
        services = self.compose_data.get('services', {})

        generated_count = 0
        skipped_count = 0

        for service_name in services.keys():
            # Skip special services that don't need Makefiles
            if service_name in ['redis', 'ollama']:
                print(f"ℹ️  Skipping {service_name} (infrastructure service)")
                continue

            service_dir = self.services_dir / service_name
            if not service_dir.exists():
                print(f"⚠️  Service directory not found: {service_name}")
                continue

            makefile_path = service_dir / "Makefile"

            if makefile_path.exists():
                print(f"ℹ️  Makefile already exists for {service_name}")
                skipped_count += 1
                continue

            # Generate the Makefile
            makefile_content = self.generate_makefile(service_name)

            # Write the Makefile
            with open(makefile_path, 'w') as f:
                f.write(makefile_content)

            print(f"✅ Generated Makefile for {service_name}")
            generated_count += 1

        print(f"\n📊 Makefile Generation Summary:")
        print(f"   Generated: {generated_count}")
        print(f"   Skipped: {skipped_count}")
        print(f"   Total: {generated_count + skipped_count}")


def main():
    """Main entry point."""
    print("🔧 Generating Makefiles for services...")

    generator = MakefileGenerator()
    generator.generate_all_makefiles()

    print("\n✅ Makefile generation complete!")


if __name__ == "__main__":
    main()
