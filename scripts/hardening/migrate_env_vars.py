#!/usr/bin/env python3
"""
Environment Variable Migration Script

This script helps migrate hardcoded environment variable usage to centralized
configuration management across all services in the ecosystem.

It identifies services that directly access environment variables and helps
migrate them to use the ConfigurationManager instead.
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from dataclasses import dataclass


@dataclass
class EnvVarUsage:
    """Represents environment variable usage in a file."""
    file_path: Path
    line_number: int
    variable_name: str
    context: str
    usage_type: str  # 'get', 'direct', 'getenv'


@dataclass
class MigrationResult:
    """Result of migrating environment variables for a service."""
    service_name: str
    env_vars_found: List[EnvVarUsage]
    migrated_vars: List[str]
    remaining_vars: List[str]
    config_updates: Dict[str, Any]


class EnvironmentVariableMigrator:
    """Migrates environment variable usage to centralized configuration."""

    def __init__(self, services_dir: Path = Path("services")):
        self.services_dir = services_dir

        # Environment variable mappings to configuration paths
        self.env_mappings = {
            # Server configuration
            "SERVER_API_HOST": "server.host",
            "SERVER_API_PORT": "server.port",
            "SERVER_WORKERS": "server.workers",
            "SERVER_TIMEOUT": "server.timeout",
            "DEBUG": "server.debug",

            # Redis configuration
            "REDIS_API_HOST": "redis.host",
            "REDIS_API_PORT": "redis.port",
            "REDIS_DB": "redis.db",
            "REDIS_PASSWORD": "redis.password",
            "REDIS_MAX_CONNECTIONS": "redis.max_connections",

            # Logging configuration
            "LOG_LEVEL": "logging.level",
            "LOG_FORMAT": "logging.format",
            "LOG_FILE": "logging.file_path",
            "LOG_STRUCTURED": "logging.structured",
            "LOG_CONSOLE": "logging.console",

            # Service URLs
            "ORCHESTRATOR_URL": "services.orchestrator_url",
            "DOC_STORE_URL": "services.doc_store_url",
            "ANALYSIS_SERVICE_URL": "services.analysis_service_url",
            "SOURCE_AGENT_URL": "services.source_agent_url",
            "FRONTEND_URL": "services.frontend_url",
            "MEMORY_AGENT_URL": "services.memory_agent_url",
            "DISCOVERY_AGENT_URL": "services.discovery_agent_url",
            "PROMPT_STORE_URL": "services.prompt_store_url",
            "INTERPRETER_URL": "services.interpreter_url",
            "CLI_SERVICE_URL": "services.cli_service_url",
            "USER_STORE_URL": "services.user_store_url",
            "EXTERNAL_SERVICE_STORE_URL": "services.external_service_store_url",
            "NOTIFICATION_SERVICE_URL": "services.notification_service_url",
            "LLM_GATEWAY_URL": "services.llm_gateway_url",
            "SUMMARIZER_HUB_URL": "services.summarizer_hub_url",
            "GITHUB_MCP_URL": "services.github_mcp_url",
            "BEDROCK_PROXY_URL": "services.bedrock_proxy_url",
            "SECURE_ANALYZER_URL": "services.secure_analyzer_url",
            "CODE_ANALYZER_URL": "services.code_analyzer_url",
            "ARCHITECTURE_DIGITIZER_URL": "services.architecture_digitizer_url",
            "PROJECT_SIMULATION_URL": "services.project_simulation_url",
            "MOCK_DATA_GENERATOR_URL": "services.mock_data_generator_url",
            "SIMULATION_DASHBOARD_URL": "services.simulation_dashboard_url",
            "UNIFIED_API_DASHBOARD_URL": "services.unified_api_dashboard_url",
            "LOG_COLLECTOR_URL": "services.log_collector_url",

            # Health and limits
            "HEALTH_CHECK_INTERVAL": "health.check_interval",
            "HEALTH_TIMEOUT": "health.timeout",
            "HEALTH_ENABLED": "health.enabled",
            "MAX_ITEMS": "limits.max_items",
            "TIMEOUT": "limits.timeout",
            "MAX_CONNECTIONS": "limits.max_connections",
            "MAX_MESSAGE_LENGTH": "limits.max_message_length",

            # Security
            "CORS_ORIGINS": "security.cors_origins",
            "JWT_SECRET": "security.jwt_secret",
            "TOKEN_EXPIRY_HOURS": "security.token_expiry_hours",

            # Service-specific variables (add more as needed)
            "LOG_RETENTION_DAYS": "log_collector.retention_days",
            "MAX_LOG_SIZE_MB": "log_collector.max_log_size_mb",
            "SERVICE_HEALTH_CHECK_INTERVAL": "log_collector.health_check_interval",
            "ENABLE_HEALTH_SAFEGUARDS": "log_collector.enable_health_safeguards",

            # Analysis service specific
            "DRIFT_OVERLAP_THRESHOLD": "analysis.drift_overlap_threshold",
            "CRITICAL_SCORE": "analysis.critical_score",
            "HIGH_PRIORITY_SCORE": "analysis.high_priority_score",
            "MEDIUM_PRIORITY_SCORE": "analysis.medium_priority_score",
            "TESTING": "analysis.testing",
            "SERVICE_CLIENT_TIMEOUT": "timeouts.service_client",
            "ANALYSIS_PROCESSING_TIMEOUT": "timeouts.analysis_processing",
            "WORKFLOW_PROCESSING_TIMEOUT": "timeouts.workflow_processing",
            "FINDINGS_RETRIEVAL_TIMEOUT": "timeouts.findings_retrieval",
            "MAX_LINES_ADDED_THRESHOLD": "limits.max_lines_added_threshold",
            "QUALITY_SCORE_WEIGHT": "limits.quality_score_weight",
            "MAX_DOCUMENT_ID_LENGTH": "limits.max_document_id_length",
            "DEFAULT_FINDINGS_LIMIT": "limits.default_findings_limit",
            "MAX_FINDINGS_LIMIT": "limits.max_findings_limit",
            "MAX_MESSAGE_LENGTH": "limits.max_message_length",
            "HEALTH_SCORE_THRESHOLD": "limits.health_score_threshold",
            "ANALYSIS_CONFIDENCE_THRESHOLD": "limits.analysis_confidence_threshold",
        }

    def analyze_service(self, service_dir: Path) -> MigrationResult:
        """Analyze environment variable usage in a service."""
        service_name = service_dir.name
        result = MigrationResult(service_name, [], [], [], {})

        # Find all Python files in the service
        python_files = list(service_dir.rglob("*.py"))

        for py_file in python_files:
            if "test" in str(py_file).lower() or "__pycache__" in str(py_file):
                continue

            usages = self._analyze_file(py_file)
            result.env_vars_found.extend(usages)

        # Categorize variables
        for usage in result.env_vars_found:
            if usage.variable_name in self.env_mappings:
                result.migrated_vars.append(usage.variable_name)
            else:
                result.remaining_vars.append(usage.variable_name)

        # Remove duplicates
        result.migrated_vars = list(set(result.migrated_vars))
        result.remaining_vars = list(set(result.remaining_vars))

        # Generate configuration updates
        result.config_updates = self._generate_config_updates(result.migrated_vars)

        return result

    def _analyze_file(self, file_path: Path) -> List[EnvVarUsage]:
        """Analyze a Python file for environment variable usage."""
        usages = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                # Look for os.environ.get patterns
                env_get_matches = re.finditer(r'os\.environ\.get\(["\']([^"\']+)["\'](?:\s*,\s*[^)]*)?\)', line)
                for match in env_get_matches:
                    var_name = match.group(1)
                    usages.append(EnvVarUsage(
                        file_path=file_path,
                        line_number=line_num,
                        variable_name=var_name,
                        context=line.strip(),
                        usage_type='get'
                    ))

                # Look for direct os.environ access
                env_direct_matches = re.finditer(r'os\.environ\[["\']([^"\']+)["\']\]', line)
                for match in env_direct_matches:
                    var_name = match.group(1)
                    usages.append(EnvVarUsage(
                        file_path=file_path,
                        line_number=line_num,
                        variable_name=var_name,
                        context=line.strip(),
                        usage_type='direct'
                    ))

                # Look for getenv calls
                getenv_matches = re.finditer(r'getenv\(["\']([^"\']+)["\'](?:\s*,\s*[^)]*)?\)', line)
                for match in getenv_matches:
                    var_name = match.group(1)
                    usages.append(EnvVarUsage(
                        file_path=file_path,
                        line_number=line_num,
                        variable_name=var_name,
                        context=line.strip(),
                        usage_type='getenv'
                    ))

        except Exception as e:
            print(f"Warning: Could not analyze {file_path}: {e}")

        return usages

    def _generate_config_updates(self, migrated_vars: List[str]) -> Dict[str, Any]:
        """Generate configuration updates for migrated variables."""
        config_updates = {}

        for var_name in migrated_vars:
            if var_name in self.env_mappings:
                config_path = self.env_mappings[var_name]
                self._set_nested_config(config_updates, config_path, f"${{{var_name}:-}}")

        return config_updates

    def _set_nested_config(self, config: Dict[str, Any], path: str, value: Any):
        """Set a value in nested configuration dictionary."""
        keys = path.split('.')
        current = config

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def migrate_service(self, service_dir: Path, dry_run: bool = True) -> MigrationResult:
        """Migrate environment variable usage in a service."""
        result = self.analyze_service(service_dir)

        if not dry_run and result.config_updates:
            # Update the service's config.yaml
            config_path = service_dir / "config.yaml"

            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        existing_config = yaml.safe_load(f) or {}
                except Exception:
                    existing_config = {}
            else:
                existing_config = {}

            # Merge configuration updates
            self._deep_merge(existing_config, result.config_updates)

            # Write back the updated configuration
            with open(config_path, 'w') as f:
                yaml.dump(existing_config, f, default_flow_style=False, indent=2, sort_keys=False)

        return result

    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]):
        """Deep merge two dictionaries."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def generate_migration_report(self, results: List[MigrationResult]) -> str:
        """Generate a comprehensive migration report."""
        report = []
        report.append("# Environment Variable Migration Report")
        report.append("")

        total_services = len(results)
        services_with_env_vars = sum(1 for r in results if r.env_vars_found)
        total_migrated = sum(len(r.migrated_vars) for r in results)
        total_remaining = sum(len(r.remaining_vars) for r in results)

        report.append("## Summary")
        report.append(f"- Total services analyzed: {total_services}")
        report.append(f"- Services using environment variables: {services_with_env_vars}")
        report.append(f"- Environment variables migrated: {total_migrated}")
        report.append(f"- Environment variables requiring manual review: {total_remaining}")
        report.append("")

        for result in results:
            if not result.env_vars_found:
                continue

            report.append(f"## {result.service_name}")
            report.append("")
            report.append(f"**Environment variables found:** {len(result.env_vars_found)}")
            report.append("")

            if result.migrated_vars:
                report.append("### Migrated Variables")
                for var in sorted(result.migrated_vars):
                    config_path = self.env_mappings.get(var, "unknown")
                    report.append(f"- `{var}` → `{config_path}`")
                report.append("")

            if result.remaining_vars:
                report.append("### Variables Requiring Manual Review")
                for var in sorted(result.remaining_vars):
                    report.append(f"- `{var}` (no standard mapping found)")
                report.append("")

            report.append("### Usage Locations")
            file_groups = {}
            for usage in result.env_vars_found:
                file_name = str(usage.file_path.relative_to(Path("services")))
                if file_name not in file_groups:
                    file_groups[file_name] = []
                file_groups[file_name].append(usage)

            for file_name, usages in file_groups.items():
                report.append(f"#### {file_name}")
                for usage in usages[:5]:  # Show first 5 usages per file
                    report.append(f"  - Line {usage.line_number}: `{usage.context}`")
                if len(usages) > 5:
                    report.append(f"  - ... and {len(usages) - 5} more")
                report.append("")

        return "\n".join(report)


def main():
    """Main migration function."""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate environment variable usage to centralized configuration")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be migrated without making changes")
    parser.add_argument("--service", help="Migrate only the specified service")
    parser.add_argument("--report", action="store_true", help="Generate a detailed migration report")
    parser.add_argument("--output", help="Output file for the report (default: migration_report.md)")

    args = parser.parse_args()

    migrator = EnvironmentVariableMigrator()

    if args.service:
        # Migrate single service
        service_dir = Path(f"services/{args.service}")
        if not service_dir.exists():
            print(f"❌ Service {args.service} not found")
            return

        result = migrator.migrate_service(service_dir, args.dry_run)

        if args.report:
            report = migrator.generate_migration_report([result])
            output_file = args.output or f"{args.service}_migration_report.md"
            with open(output_file, 'w') as f:
                f.write(report)
            print(f"📋 Migration report saved to {output_file}")
        else:
            print(f"📋 Migration Result for {result.service_name}:")
            print(f"  Environment variables found: {len(result.env_vars_found)}")
            print(f"  Migrated: {len(result.migrated_vars)}")
            print(f"  Remaining: {len(result.remaining_vars)}")

            if result.migrated_vars:
                print("  Migrated variables:")
                for var in result.migrated_vars:
                    print(f"    • {var}")
            if result.remaining_vars:
                print("  Variables requiring manual review:")
                for var in result.remaining_vars:
                    print(f"    • {var}")

    else:
        # Analyze all services
        results = []
        service_dirs = [d for d in Path("services").iterdir()
                       if d.is_dir() and not d.name.startswith('.') and d.name not in ['shared', '__pycache__']]

        for service_dir in service_dirs:
            result = migrator.migrate_service(service_dir, dry_run=True)  # Always dry run for all services
            results.append(result)

        if args.report:
            report = migrator.generate_migration_report(results)
            output_file = args.output or "environment_variable_migration_report.md"
            with open(output_file, 'w') as f:
                f.write(report)
            print(f"📋 Comprehensive migration report saved to {output_file}")
        else:
            # Summary
            services_with_env_vars = sum(1 for r in results if r.env_vars_found)
            total_migrated = sum(len(r.migrated_vars) for r in results)
            total_remaining = sum(len(r.remaining_vars) for r in results)

            print("📊 Environment Variable Migration Summary:")
            print(f"  Services analyzed: {len(results)}")
            print(f"  Services using environment variables: {services_with_env_vars}")
            print(f"  Variables that can be migrated: {total_migrated}")
            print(f"  Variables requiring manual review: {total_remaining}")

            if not args.dry_run and total_migrated > 0:
                print("\n🔄 Applying migrations...")
                for result in results:
                    if result.migrated_vars:
                        service_dir = Path(f"services/{result.service_name}")
                        migrator.migrate_service(service_dir, dry_run=False)
                print("✅ Migration complete!")


if __name__ == "__main__":
    main()
