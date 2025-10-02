#!/usr/bin/env python3
"""
Unified Configuration Management Interface

This script provides a single entry point for all configuration management operations
in the LLM Documentation Ecosystem, consolidating functionality from multiple scripts
into a cohesive, user-friendly interface.

Features:
- Configuration auditing and validation
- Automated standardization
- Environment variable migration
- Docker consistency checking
- Configuration drift detection
- Comprehensive reporting
"""

import sys
import os
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import our new configuration system
try:
    from services.shared.infrastructure.config import (
        load_service_config,
        ConfigurationManager,
        Environment
    )
    NEW_CONFIG_SYSTEM_AVAILABLE = True
except ImportError:
    NEW_CONFIG_SYSTEM_AVAILABLE = False
    print("⚠️  New configuration system not available, falling back to legacy scripts")

# Import existing audit script
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    import audit_configuration
    AUDIT_AVAILABLE = True
except ImportError:
    AUDIT_AVAILABLE = False

# Import existing standardization script
try:
    from scripts.hardening.configuration_standardization import ConfigurationStandardizer
    STANDARDIZATION_AVAILABLE = True
except ImportError:
    STANDARDIZATION_AVAILABLE = False

# Import existing migration script
try:
    from scripts.hardening.migrate_env_vars import EnvironmentVariableMigrator
    MIGRATION_AVAILABLE = True
except ImportError:
    MIGRATION_AVAILABLE = False


class UnifiedConfigManager:
    """
    Unified Configuration Management Interface

    Consolidates all configuration management operations into a single,
    easy-to-use interface with consistent behavior and reporting.
    """

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.services_dir = self.project_root / "services"
        self.scripts_dir = self.project_root / "scripts" / "hardening"

        # Check availability of subsystems
        self.capabilities = {
            'audit': AUDIT_AVAILABLE,
            'standardization': STANDARDIZATION_AVAILABLE,
            'migration': MIGRATION_AVAILABLE,
            'new_system': NEW_CONFIG_SYSTEM_AVAILABLE,
            'startup_validation': True  # Always available (uses basic YAML parsing)
        }

    def show_status(self) -> None:
        """Show the status of all configuration management subsystems."""
        print("🔧 Unified Configuration Management Status")
        print("=" * 50)

        for capability, available in self.capabilities.items():
            status = "✅ Available" if available else "❌ Not Available"
            print(f"  {capability.capitalize()}: {status}")

        print(f"\n📁 Project root: {self.project_root}")
        print(f"📁 Services directory: {self.services_dir}")
        print(f"📁 Scripts directory: {self.scripts_dir}")

    def validate_service_startup_readiness(self, compose_file: str = "docker-compose.dev.yml") -> Dict[str, Any]:
        """
        Validate that services are ready for startup based on real-world issues encountered.
        This checks for common problems that prevent services from starting together.

        Returns:
            Dictionary with validation results
        """
        results = {
            "compose_file": compose_file,
            "valid": True,
            "issues": [],
            "warnings": [],
            "recommendations": []
        }

        try:
            # Check if docker-compose file exists
            compose_path = self.project_root / compose_file
            if not compose_path.exists():
                results["issues"].append(f"Docker Compose file not found: {compose_file}")
                results["valid"] = False
                return results

            # Parse docker-compose file (simplified)
            import yaml
            with open(compose_path, 'r') as f:
                compose_config = yaml.safe_load(f)

            services = compose_config.get('services', {})

            # Check for port conflicts
            used_ports = set()
            for service_name, service_config in services.items():
                ports = service_config.get('ports', [])
                for port_mapping in ports:
                    if isinstance(port_mapping, str) and ':' in port_mapping:
                        host_port = port_mapping.split(':')[0]
                        try:
                            port_int = int(host_port)
                            if port_int in used_ports:
                                results["issues"].append(f"Port conflict: {service_name} uses port {port_int} which is already used")
                                results["valid"] = False
                            else:
                                used_ports.add(port_int)
                        except ValueError:
                            results["warnings"].append(f"Non-numeric port in {service_name}: {host_port}")

            # Check for required shared volume mounts
            services_needing_shared = [
                'orchestrator', 'doc_store', 'analysis-service', 'source-agent',
                'frontend', 'llm-gateway', 'mock-data-generator', 'github-mcp',
                'memory-agent', 'discovery-agent', 'notification-service', 'prompt_store',
                'interpreter', 'code-analyzer', 'secure-analyzer', 'log-collector',
                'external-service-store', 'user-store', 'project-planning-service'
            ]

            for service_name in services_needing_shared:
                if service_name in services:
                    service_config = services[service_name]
                    volumes = service_config.get('volumes', [])
                    has_shared = any('services/shared' in str(volume) for volume in volumes)

                    if not has_shared:
                        results["issues"].append(f"Service '{service_name}' missing required shared volume mount")
                        results["recommendations"].append(f"Add './services/shared:/app/services/shared:ro' to {service_name} volumes")
                        results["valid"] = False

            # Check for health check configurations
            for service_name, service_config in services.items():
                healthcheck = service_config.get('healthcheck', {})
                if healthcheck:
                    if 'start_period' not in healthcheck:
                        results["warnings"].append(f"Service '{service_name}' missing start_period in healthcheck")
                        results["recommendations"].append(f"Add start_period to {service_name} healthcheck (recommended: 30s)")

            # Check for dependency cycles (simplified)
            dependency_graph = {}
            for service_name, service_config in services.items():
                depends_on = service_config.get('depends_on', [])
                if isinstance(depends_on, str):
                    depends_on = [depends_on]
                elif isinstance(depends_on, dict):
                    depends_on = list(depends_on.keys())

                dependency_graph[service_name] = depends_on

            # Simple cycle detection
            for service, deps in dependency_graph.items():
                for dep in deps:
                    if dep in dependency_graph and service in dependency_graph.get(dep, []):
                        results["issues"].append(f"Circular dependency detected: {service} <-> {dep}")
                        results["valid"] = False

            # Check for import path issues in service code
            self._check_import_paths(results, services)

        except Exception as e:
            results["issues"].append(f"Failed to validate startup readiness: {e}")
            results["valid"] = False

        return results

    def _check_import_paths(self, results: Dict[str, Any], services: Dict[str, Any]) -> None:
        """
        Check for common import path issues in service code that cause ModuleNotFoundError.
        """
        import os
        import re
        from pathlib import Path

        # Common incorrect import patterns and their corrections
        import_fixes = {
            r'from services\.shared\.presentation\.responses import': 'from services.shared.presentation.api.responses import',
            r'from services\.shared\.utilities\.error_handling import': 'from services.shared.infrastructure.utilities.error_handling import',
            r'from services\.shared\.utilities import BaseService': 'from services.shared.domain.services.base_service import BaseService',
        }

        for service_name in services.keys():
            service_dir = self.project_root / "services" / service_name
            if not service_dir.exists():
                continue

            # Find all Python files in the service
            for py_file in service_dir.rglob("*.py"):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    for wrong_import, correct_import in import_fixes.items():
                        if re.search(wrong_import, content):
                            relative_path = py_file.relative_to(self.project_root)
                            results["issues"].append(
                                f"Service '{service_name}' has incorrect import in {relative_path}: "
                                f"Found '{wrong_import.strip()}' should be '{correct_import}'"
                            )
                            results["recommendations"].append(
                                f"Fix import in {relative_path}: change '{wrong_import.strip()}' to '{correct_import}'"
                            )
                            results["valid"] = False
                            break  # Only report one issue per file

                except Exception as e:
                    results["warnings"].append(f"Could not check imports in {service_name}/{py_file.name}: {e}")

    def audit_configuration(self, output_format: str = 'text', output_file: Optional[str] = None) -> int:
        """Perform comprehensive configuration audit."""
        if not AUDIT_AVAILABLE:
            print("❌ Configuration audit not available")
            return 1

        print("🔍 Running Configuration Audit...")
        print("-" * 40)

        try:
            # Import and run audit
            import subprocess
            result = subprocess.run([sys.executable, 'audit_configuration.py'],
                                  capture_output=True, text=True, cwd=self.project_root)

            if result.returncode == 0:
                print("✅ Configuration audit completed successfully")

                # Save output if requested
                if output_file:
                    with open(output_file, 'w') as f:
                        f.write(result.stdout)
                    print(f"💾 Audit results saved to {output_file}")

                # Print summary
                print("\n📊 Audit Summary:")
                for line in result.stdout.split('\n'):
                    if any(keyword in line for keyword in ['Total services', 'Services with', 'Configuration issues']):
                        print(f"  {line.strip()}")
            else:
                print("❌ Configuration audit failed")
                print(result.stderr)
                return 1

        except Exception as e:
            print(f"❌ Error running configuration audit: {e}")
            return 1

        return 0

    def standardize_configuration(self, service: Optional[str] = None,
                                dry_run: bool = True,
                                output_file: Optional[str] = None) -> int:
        """Apply configuration standardization."""
        if not STANDARDIZATION_AVAILABLE:
            print("❌ Configuration standardization not available")
            return 1

        print("🔧 Running Configuration Standardization...")
        print("-" * 40)

        try:
            standardizer = ConfigurationStandardizer()

            if service:
                # Standardize single service
                service_dir = self.services_dir / service
                if not service_dir.exists():
                    print(f"❌ Service '{service}' not found")
                    return 1

                result = standardizer.standardize_service(service_dir, dry_run)

                if output_file:
                    # Save detailed results
                    import json
                    with open(output_file, 'w') as f:
                        json.dump({
                            'service': result.service_name,
                            'success': result.success,
                            'changes': result.changes_made,
                            'warnings': result.warnings,
                            'errors': result.errors
                        }, f, indent=2)

                # Print results
                self._print_standardization_result(result)
                return 0 if result.success else 1

            else:
                # Standardize all services
                results = standardizer.standardize_all_services(dry_run)

                # Save results if requested
                if output_file:
                    import json
                    output_data = [{
                        'service': r.service_name,
                        'success': r.success,
                        'changes': len(r.changes_made),
                        'warnings': len(r.warnings),
                        'errors': len(r.errors)
                    } for r in results]

                    with open(output_file, 'w') as f:
                        json.dump(output_data, f, indent=2)

                # Print summary
                successful = sum(1 for r in results if r.success)
                total_changes = sum(len(r.changes_made) for r in results)

                print("\n📊 Standardization Summary:")
                print(f"  Services processed: {len(results)}")
                print(f"  Successful: {successful}")
                print(f"  Failed: {len(results) - successful}")
                print(f"  Total changes: {total_changes}")

                if dry_run:
                    print("\n🔍 Dry run completed. Use --apply to make actual changes.")
                else:
                    print("\n✅ Standardization completed!")

                return 0

        except Exception as e:
            print(f"❌ Error during standardization: {e}")
            return 1

    def migrate_environment_variables(self, service: Optional[str] = None,
                                    report: bool = True,
                                    output_file: Optional[str] = None) -> int:
        """Migrate environment variable usage to centralized configuration."""
        if not MIGRATION_AVAILABLE:
            print("❌ Environment variable migration not available")
            return 1

        print("🔄 Running Environment Variable Migration...")
        print("-" * 40)

        try:
            migrator = EnvironmentVariableMigrator()

            if service:
                # Migrate single service
                service_dir = self.services_dir / service
                if not service_dir.exists():
                    print(f"❌ Service '{service}' not found")
                    return 1

                result = migrator.migrate_service(service_dir, dry_run=True)

                if report:
                    report_content = migrator.generate_migration_report([result])

                    if output_file:
                        with open(output_file, 'w') as f:
                            f.write(report_content)
                        print(f"💾 Migration report saved to {output_file}")
                    else:
                        print(report_content)

                return 0

            else:
                # Analyze all services
                results = []
                service_dirs = [d for d in self.services_dir.iterdir()
                               if d.is_dir() and not d.name.startswith('.') and d.name not in ['shared', '__pycache__']]

                for service_dir in service_dirs:
                    result = migrator.migrate_service(service_dir, dry_run=True)
                    results.append(result)

                if report:
                    report_content = migrator.generate_migration_report(results)

                    if output_file:
                        with open(output_file, 'w') as f:
                            f.write(report_content)
                        print(f"💾 Comprehensive migration report saved to {output_file}")
                    else:
                        # Print summary
                        total_services = len(results)
                        services_with_env_vars = sum(1 for r in results if r.env_vars_found)
                        total_migrated = sum(len(r.migrated_vars) for r in results)
                        total_remaining = sum(len(r.remaining_vars) for r in results)

                        print("\n📊 Environment Variable Migration Summary:")
                        print(f"  Services analyzed: {total_services}")
                        print(f"  Services using environment variables: {services_with_env_vars}")
                        print(f"  Variables that can be migrated: {total_migrated}")
                        print(f"  Variables requiring manual review: {total_remaining}")

                return 0

        except Exception as e:
            print(f"❌ Error during migration: {e}")
            return 1

    def validate_docker_consistency(self) -> int:
        """Validate Docker and Docker Compose configuration consistency."""
        print("🐳 Validating Docker Configuration Consistency...")
        print("-" * 40)

        try:
            # Check main docker-compose files
            compose_files = [
                'docker-compose.yml',
                'docker-compose.dev.yml',
                'docker-compose.prod.yml',
                'docker-compose.services.yml'
            ]

            issues = []

            for compose_file in compose_files:
                if (self.project_root / compose_file).exists():
                    print(f"  Checking {compose_file}...")

                    try:
                        with open(self.project_root / compose_file, 'r') as f:
                            config = yaml.safe_load(f)

                        if 'services' in config:
                            services = config['services']
                            print(f"    Found {len(services)} services")

                            # Check for common issues
                            for service_name, service_config in services.items():
                                if 'ports' in service_config:
                                    ports = service_config['ports']
                                    # Allow multiple ports for infrastructure services
                                    infra_services = ['nginx', 'redis', 'postgres', 'grafana', 'prometheus', 'jaeger']
                                    if len(ports) > 1 and service_name not in infra_services:
                                        issues.append(f"Service '{service_name}' has multiple port mappings in {compose_file}")

                    except Exception as e:
                        issues.append(f"Error parsing {compose_file}: {e}")

            if issues:
                print("\n🚨 Docker Configuration Issues:")
                for issue in issues:
                    print(f"  ❌ {issue}")
                return 1
            else:
                print("✅ Docker configuration consistency validated!")
                return 0

        except Exception as e:
            print(f"❌ Error validating Docker consistency: {e}")
            return 1

    def generate_comprehensive_report(self, output_file: str) -> int:
        """Generate a comprehensive configuration management report."""
        print("📊 Generating Comprehensive Configuration Report...")
        print("-" * 40)

        try:
            report = {
                'timestamp': str(Path(output_file).stat().st_mtime) if Path(output_file).exists() else None,
                'capabilities': self.capabilities,
                'audit_results': {},
                'migration_analysis': {},
                'recommendations': []
            }

            # Run audit if available
            if AUDIT_AVAILABLE:
                print("  Running configuration audit...")
                audit_result = self.audit_configuration(output_format='json')
                if audit_result == 0:
                    # Read the audit results
                    audit_file = self.project_root / 'configuration_audit_results.json'
                    if audit_file.exists():
                        with open(audit_file, 'r') as f:
                            report['audit_results'] = json.load(f)

            # Run migration analysis if available
            if MIGRATION_AVAILABLE:
                print("  Analyzing environment variable usage...")
                migrator = EnvironmentVariableMigrator()
                results = []

                service_dirs = [d for d in self.services_dir.iterdir()
                               if d.is_dir() and not d.name.startswith('.') and d.name not in ['shared', '__pycache__']]

                for service_dir in service_dirs:
                    result = migrator.migrate_service(service_dir, dry_run=True)
                    results.append({
                        'service': result.service_name,
                        'env_vars_found': len(result.env_vars_found),
                        'migrated_vars': len(result.migrated_vars),
                        'remaining_vars': len(result.remaining_vars)
                    })

                report['migration_analysis'] = results

            # Generate recommendations
            report['recommendations'] = [
                "Run configuration audit regularly to detect drift",
                "Apply configuration standardization to maintain consistency",
                "Review environment variable migration reports for manual updates",
                "Validate Docker consistency before deployments",
                "Update service configurations when adding new environment variables"
            ]

            # Save comprehensive report
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)

            print(f"✅ Comprehensive report saved to {output_file}")
            return 0

        except Exception as e:
            print(f"❌ Error generating comprehensive report: {e}")
            return 1

    def _print_standardization_result(self, result):
        """Print standardization result in a readable format."""
        print(f"\n📋 Standardization Result for {result.service_name}:")
        print(f"  Success: {'✅' if result.success else '❌'}")

        if result.changes_made:
            print("  Changes made:")
            for change in result.changes_made:
                print(f"    • {change}")

        if result.warnings:
            print("  Warnings:")
            for warning in result.warnings:
                print(f"    ⚠️  {warning}")

        if result.errors:
            print("  Errors:")
            for error in result.errors:
                print(f"    ❌ {error}")


def main():
    """Main entry point for unified configuration management."""
    parser = argparse.ArgumentParser(
        description="Unified Configuration Management for LLM Documentation Ecosystem",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s status                                    # Show system status
  %(prog)s audit                                     # Run configuration audit
  %(prog)s startup-check                              # Validate service startup readiness
  %(prog)s standardize --dry-run                     # Preview standardization
  %(prog)s standardize --apply                       # Apply standardization
  %(prog)s migrate --service log-collector           # Migrate env vars for service
  %(prog)s migrate --report                          # Generate migration report
  %(prog)s docker-check                              # Validate Docker consistency
  %(prog)s report --output config_report.json        # Generate comprehensive report
        """
    )

    parser.add_argument('command', choices=[
        'status', 'audit', 'standardize', 'migrate', 'docker-check', 'report', 'startup-check'
    ], help='Configuration management command to run')

    # Audit options
    parser.add_argument('--format', choices=['text', 'json'],
                       default='text', help='Output format for audit')

    # Standardization options
    parser.add_argument('--service', help='Specific service to operate on')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview changes without applying them')
    parser.add_argument('--apply', action='store_true',
                       help='Apply changes (overrides --dry-run)')

    # Migration options
    parser.add_argument('--report', action='store_true',
                       help='Generate detailed migration report')

    # Output options
    parser.add_argument('--output', help='Output file for results')

    args = parser.parse_args()

    # Initialize manager
    manager = UnifiedConfigManager()

    # Handle dry-run vs apply logic
    if args.command == 'standardize':
        dry_run = not args.apply
        if args.apply:
            print("⚠️  Applying actual changes to configuration files!")
            confirm = input("Continue? (y/N): ")
            if confirm.lower() not in ['y', 'yes']:
                print("Operation cancelled.")
                return 0
    else:
        dry_run = args.dry_run

    # Execute command
    try:
        if args.command == 'status':
            manager.show_status()

        elif args.command == 'audit':
            return manager.audit_configuration(args.format, args.output)

        elif args.command == 'standardize':
            return manager.standardize_configuration(args.service, dry_run, args.output)

        elif args.command == 'migrate':
            return manager.migrate_environment_variables(args.service, args.report, args.output)

        elif args.command == 'docker-check':
            return manager.validate_docker_consistency()

        elif args.command == 'report':
            output_file = args.output or 'comprehensive_config_report.json'
            return manager.generate_comprehensive_report(output_file)

        elif args.command == 'startup-check':
            compose_file = args.service or 'docker-compose.dev.yml'
            results = manager.validate_service_startup_readiness(compose_file)

            print("🚀 Service Startup Readiness Validation")
            print("=" * 50)
            print(f"Compose File: {results['compose_file']}")
            print(f"Overall Status: {'✅ VALID' if results['valid'] else '❌ INVALID'}")

            if results['issues']:
                print(f"\n❌ Critical Issues ({len(results['issues'])}):")
                for issue in results['issues']:
                    print(f"  • {issue}")

            if results['warnings']:
                print(f"\n⚠️  Warnings ({len(results['warnings'])}):")
                for warning in results['warnings']:
                    print(f"  • {warning}")

            if results['recommendations']:
                print(f"\n💡 Recommendations ({len(results['recommendations'])}):")
                for rec in results['recommendations']:
                    print(f"  • {rec}")

            return 0 if results['valid'] else 1

    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
