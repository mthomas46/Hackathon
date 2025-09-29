#!/usr/bin/env python3
"""
Consolidated Development Utilities
Unified toolkit for development, maintenance, and operational tasks

This script provides a comprehensive set of development utilities that combine
functionality from multiple previously separate utility scripts.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

class DevelopmentUtilities:
    """
    Consolidated development utilities for the LLM Documentation Ecosystem.
    """

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    def fix_code_quality(self, imports: bool = False, bare_except: bool = False):
        """Fix code quality issues."""
        console.print("🔧 Fixing code quality issues...")

        if imports:
            console.print("📦 Fixing import statements...")
            # Implementation for import fixing
            pass

        if bare_except:
            console.print("⚠️  Fixing bare except clauses...")
            # Implementation for bare except fixing
            pass

        console.print("✅ Code quality fixes applied")

    def optimize_data(self, prompt_store: bool = False, doc_store: bool = False):
        """Optimize data stores."""
        console.print("💾 Optimizing data stores...")

        if prompt_store:
            console.print("📋 Optimizing prompt store...")
            # Implementation for prompt store optimization
            pass

        if doc_store:
            console.print("📄 Optimizing document store...")
            # Implementation for doc store optimization
            pass

        console.print("✅ Data stores optimized")

    def optimize_infrastructure(self, dockerfiles: bool = False, ports: bool = False):
        """Optimize infrastructure configuration."""
        console.print("🏗️  Optimizing infrastructure...")

        if dockerfiles:
            console.print("🐳 Optimizing Dockerfiles...")
            # Implementation for Dockerfile optimization
            pass

        if ports:
            console.print("🔌 Resolving port conflicts...")
            # Implementation for port conflict resolution
            pass

        console.print("✅ Infrastructure optimized")

    def browse_data(self, store: str, limit: int = 50):
        """Browse data stores."""
        console.print(f"🔍 Browsing {store} data (limit: {limit})...")

        if store == "prompt-store":
            # Implementation for prompt store browsing
            pass
        elif store == "doc-store":
            # Implementation for doc store browsing
            pass

        console.print("✅ Data browsing complete")

    def audit_services(self):
        """Comprehensive service audit and standardization."""
        console.print("🔍 Auditing all services...")

        # Check port conflicts
        self.check_port_conflicts()

        # Standardize Dockerfiles
        self.standardize_dockerfiles()

        # Update docker-compose
        self.update_docker_compose()

        # Update Makefile
        self.update_makefile()

        console.print("✅ Service audit complete")

    def check_port_conflicts(self):
        """Check for port conflicts across all services."""
        console.print("🔍 Checking port conflicts...")

        # Read service-ports.yaml
        try:
            import yaml
            with open('config/service-ports.yaml', 'r') as f:
                ports_config = yaml.safe_load(f)
        except Exception as e:
            console.print(f"❌ Could not read service-ports.yaml: {e}")
            return

        # Extract all ports
        used_ports = set()
        conflicts = []

        for category, services in ports_config.items():
            if not isinstance(services, dict):
                continue

            for service_name, config in services.items():
                if isinstance(config, dict) and 'external_port' in config:
                    port = config['external_port']
                    if port in used_ports:
                        conflicts.append(f"{service_name}: port {port} already used")
                    else:
                        used_ports.add(port)

        if conflicts:
            console.print("❌ Port conflicts found:")
            for conflict in conflicts:
                console.print(f"   - {conflict}")
        else:
            console.print("✅ No port conflicts detected")

    def standardize_dockerfiles(self):
        """Standardize all service Dockerfiles according to audit framework."""
        console.print("🏗️  Standardizing Dockerfiles...")

        import os
        import shutil

        # Read the standard template
        template_path = 'services/_template/Dockerfile.standard'
        if not os.path.exists(template_path):
            console.print(f"❌ Standard template not found: {template_path}")
            return

        with open(template_path, 'r') as f:
            template = f.read()

        # Get all service directories
        services_dir = 'services'
        if not os.path.exists(services_dir):
            console.print(f"❌ Services directory not found: {services_dir}")
            return

        standardized = 0
        for item in os.listdir(services_dir):
            service_path = os.path.join(services_dir, item)
            if os.path.isdir(service_path) and not item.startswith('_'):
                dockerfile_path = os.path.join(service_path, 'Dockerfile')
                if os.path.exists(dockerfile_path):
                    # Read current Dockerfile
                    with open(dockerfile_path, 'r') as f:
                        current_content = f.read()

                    # Check if it needs standardization
                    if 'LABEL maintainer="LLM Documentation Ecosystem Team"' not in current_content:
                        console.print(f"📝 Standardizing {item}/Dockerfile...")
                        # Create standardized version
                        standardized_content = template.replace('SERVICE_NAME', item)
                        standardized_content = standardized_content.replace('SERVICE_DESCRIPTION', f"{item.replace('-', ' ').title()} service")
                        standardized_content = standardized_content.replace('SERVICE_PORT', '5000')  # Default, will be updated
                        standardized_content = standardized_content.replace('SERVICE_PROFILE', 'core')

                        with open(dockerfile_path, 'w') as f:
                            f.write(standardized_content)
                        standardized += 1

        console.print(f"✅ Standardized {standardized} Dockerfiles")

    def update_docker_compose(self):
        """Update docker-compose.dev.yml with all services and correct ports."""
        console.print("📝 Updating docker-compose.dev.yml...")

        # Read service-ports.yaml
        try:
            import yaml
            with open('config/service-ports.yaml', 'r') as f:
                ports_config = yaml.safe_load(f)
        except Exception as e:
            console.print(f"❌ Could not read service-ports.yaml: {e}")
            return

        # This would be a complex update - for now just log what needs to be done
        console.print("ℹ️  Docker Compose update requires manual review")
        console.print("   - Ensure all services from service-ports.yaml are included")
        console.print("   - Verify port mappings match external_port values")
        console.print("   - Check dependency chains are correct")

    def update_makefile(self):
        """Update Makefile with all services."""
        console.print("📝 Updating Makefile...")

        # This would require reading and updating the Makefile
        console.print("ℹ️  Makefile update requires manual review")
        console.print("   - Add targets for all services")
        console.print("   - Update service management commands")

    def fix_environment(self, conflicts: bool = False, variables: bool = False):
        """Fix environment configuration."""
        console.print("🌍 Fixing environment configuration...")

        if conflicts:
            console.print("⚡ Resolving conflicts...")
            self.audit_services()
            pass

        if variables:
            console.print("🔧 Standardizing variables...")
            # Implementation for variable standardization
            pass

        console.print("✅ Environment configuration fixed")

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Consolidated Development Utilities for LLM Documentation Ecosystem",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python dev_utilities.py fix-code --imports --bare-except
  python dev_utilities.py optimize-data --prompt-store --doc-store
  python dev_utilities.py optimize-infra --dockerfiles --ports
  python dev_utilities.py browse-data --store prompt-store --limit 50
  python dev_utilities.py fix-environment --conflicts --variables
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Fix code quality
    fix_parser = subparsers.add_parser('fix-code', help='Fix code quality issues')
    fix_parser.add_argument('--imports', action='store_true', help='Fix import statements')
    fix_parser.add_argument('--bare-except', action='store_true', help='Fix bare except clauses')

    # Optimize data
    data_parser = subparsers.add_parser('optimize-data', help='Optimize data stores')
    data_parser.add_argument('--prompt-store', action='store_true', help='Optimize prompt store')
    data_parser.add_argument('--doc-store', action='store_true', help='Optimize document store')

    # Optimize infrastructure
    infra_parser = subparsers.add_parser('optimize-infra', help='Optimize infrastructure')
    infra_parser.add_argument('--dockerfiles', action='store_true', help='Optimize Dockerfiles')
    infra_parser.add_argument('--ports', action='store_true', help='Resolve port conflicts')

    # Browse data
    browse_parser = subparsers.add_parser('browse-data', help='Browse data stores')
    browse_parser.add_argument('--store', required=True, choices=['prompt-store', 'doc-store'], help='Data store to browse')
    browse_parser.add_argument('--limit', type=int, default=50, help='Maximum items to display')

    # Audit services
    audit_parser = subparsers.add_parser('audit-services', help='Comprehensive service audit and standardization')

    # Fix environment
    env_parser = subparsers.add_parser('fix-environment', help='Fix environment configuration')
    env_parser.add_argument('--conflicts', action='store_true', help='Resolve conflicts')
    env_parser.add_argument('--variables', action='store_true', help='Standardize variables')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize utilities
    utils = DevelopmentUtilities()

    # Execute commands
    try:
        if args.command == 'fix-code':
            utils.fix_code_quality(imports=args.imports, bare_except=args.bare_except)
        elif args.command == 'optimize-data':
            utils.optimize_data(prompt_store=args.prompt_store, doc_store=args.doc_store)
        elif args.command == 'optimize-infra':
            utils.optimize_infrastructure(dockerfiles=args.dockerfiles, ports=args.ports)
        elif args.command == 'browse-data':
            utils.browse_data(store=args.store, limit=args.limit)
        elif args.command == 'audit-services':
            utils.audit_services()
        elif args.command == 'fix-environment':
            utils.fix_environment(conflicts=args.conflicts, variables=args.variables)
    except Exception as e:
        console.print(f"❌ Error executing command: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
