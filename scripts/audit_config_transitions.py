#!/usr/bin/env python3
"""
Configuration Transition Audit Script

Audits services to identify hardcoded configurations that should be moved
to external config files, and ensures proper config file usage.
"""

import os
import re
from pathlib import Path
from typing import Dict

import yaml


class ConfigTransitionAuditor:
    """Audits configuration transitions for services."""

    def __init__(self, services_dir: str = "services"):
        self.services_dir = Path(services_dir)
        self.audit_results = {}

    def audit_service_config_usage(self, service_name: str) -> Dict:
        """Audit how a service uses configuration."""
        service_dir = self.services_dir / service_name
        issues = []
        recommendations = []
        config_usage = {
            "has_config_file": False,
            "uses_config_file": False,
            "hardcoded_values": [],
            "missing_config_values": [],
        }

        # Check if config file exists
        config_files = list(service_dir.glob("config.y*"))
        if config_files:
            config_usage["has_config_file"] = True
            config_file = config_files[0]

            # Load config file
            try:
                with open(config_file, "r") as f:
                    config_data = yaml.safe_load(f)
            except Exception as e:
                issues.append(f"Cannot parse config file: {e}")
                config_data = {}

            # Find Python files in service
            python_files = list(service_dir.glob("**/*.py"))
            python_files.extend(list(service_dir.glob("*.py")))

            for py_file in python_files:
                if "test" in str(py_file) or "__pycache__" in str(py_file):
                    continue

                try:
                    with open(py_file, "r") as f:
                        content = f.read()

                    # Check for hardcoded environment variables
                    hardcoded_env = re.findall(r"os\.getenv\([^,)]+, [^\)]+\)", content)
                    hardcoded_environ = re.findall(r"os\.environ\.get\([^,)]+, [^\)]+\)", content)

                    for match in hardcoded_env + hardcoded_environ:
                        config_usage["hardcoded_values"].append(f"{py_file.name}: {match}")

                    # Check if config file is being loaded
                    if "yaml" in content and ("load" in content or "safe_load" in content):
                        config_usage["uses_config_file"] = True

                    # Check for specific config patterns
                    if "config_data" in content or "config." in content:
                        config_usage["uses_config_file"] = True

                except Exception as e:
                    issues.append(f"Error reading {py_file}: {e}")

            # Check what config values are defined but not used
            if config_data:
                # Extract all environment variable references from config
                env_vars_in_config = set()
                config_str = str(config_data)

                # Find ${VAR_NAME} patterns
                env_refs = re.findall(r"\$\{([^}]+)\}", config_str)
                for ref in env_refs:
                    var_name = ref.split(":")[0]  # Handle ${VAR:default} format
                    env_vars_in_config.add(var_name)

                # Check if service uses these variables
                used_vars = set()
                for py_file in python_files:
                    if "test" in str(py_file) or "__pycache__" in str(py_file):
                        continue

                    try:
                        with open(py_file, "r") as f:
                            content = f.read()

                        for var in env_vars_in_config:
                            if var in content:
                                used_vars.add(var)
                    except:
                        pass

                unused_vars = env_vars_in_config - used_vars
                if unused_vars:
                    recommendations.append(f"Unused config variables: {', '.join(unused_vars)}")

        else:
            issues.append("No config file found")

        return {"config_usage": config_usage, "issues": issues, "recommendations": recommendations}

    def audit_all_services(self) -> Dict[str, Dict]:
        """Audit all services for configuration usage."""
        results = {}

        for service_dir in self.services_dir.iterdir():
            if service_dir.is_dir() and not service_dir.name.startswith("_"):
                service_name = service_dir.name
                results[service_name] = self.audit_service_config_usage(service_name)

        return results

    def generate_transition_report(self, results: Dict[str, Dict]) -> str:
        """Generate a configuration transition report."""
        report = []
        report.append("# Configuration Transition Audit Report")
        report.append("=" * 50)
        report.append("")

        total_services = len(results)
        services_with_config = 0
        services_using_config = 0
        services_with_hardcoded = 0

        for service_name, audit_result in results.items():
            config_usage = audit_result["config_usage"]
            issues = audit_result["issues"]
            recommendations = audit_result["recommendations"]

            report.append(f"## {service_name.upper()}")
            report.append("")

            if config_usage["has_config_file"]:
                services_with_config += 1
                report.append("✅ Has config file")
            else:
                report.append("❌ No config file")

            if config_usage["uses_config_file"]:
                services_using_config += 1
                report.append("✅ Uses config file in code")
            else:
                report.append("❌ Does not use config file in code")

            if config_usage["hardcoded_values"]:
                services_with_hardcoded += 1
                report.append(f"⚠️  {len(config_usage['hardcoded_values'])} hardcoded values:")
                for hardcoded in config_usage["hardcoded_values"][:3]:  # Show first 3
                    report.append(f"   - {hardcoded}")
                if len(config_usage["hardcoded_values"]) > 3:
                    report.append(f"   ... and {len(config_usage['hardcoded_values']) - 3} more")

            if issues:
                report.append("🚨 Issues:")
                for issue in issues:
                    report.append(f"   - {issue}")

            if recommendations:
                report.append("💡 Recommendations:")
                for rec in recommendations:
                    report.append(f"   - {rec}")

            report.append("")

        # Summary
        report.append("## SUMMARY")
        report.append(f"- **Total Services:** {total_services}")
        report.append(
            f"- **Services with config files:** {services_with_config} ({services_with_config*100//total_services}%)"
        )
        report.append(
            f"- **Services using config files:** {services_using_config} ({services_using_config*100//total_services}%)"
        )
        report.append(
            f"- **Services with hardcoded values:** {services_with_hardcoded} ({services_with_hardcoded*100//total_services}%)"
        )
        report.append("")

        if services_with_hardcoded > 0:
            report.append("## REQUIRED ACTIONS")
            report.append("The following services need configuration transitions:")
            report.append("")

            for service_name, audit_result in results.items():
                if audit_result["config_usage"]["hardcoded_values"]:
                    report.append(f"### {service_name}")
                    report.append("- [ ] Create/update config file")
                    report.append("- [ ] Replace hardcoded values with config loading")
                    report.append("- [ ] Update Dockerfile if needed")
                    report.append("- [ ] Test configuration loading")
                    report.append("")

        report.append("## CONFIGURATION BEST PRACTICES")
        report.append("1. **Environment Variables**: Use ${VAR_NAME} syntax in config files")
        report.append("2. **Default Values**: Provide sensible defaults in config files")
        report.append("3. **Config Loading**: Load config files at service startup")
        report.append("4. **Validation**: Validate required config values on startup")
        report.append("5. **Documentation**: Document all configuration options")

        return "\n".join(report)


def main():
    """Main entry point."""
    print("🔍 Auditing configuration transitions...")

    auditor = ConfigTransitionAuditor()
    results = auditor.audit_all_services()

    print("📋 Generating transition report...")
    report = auditor.generate_transition_report(results)
    print(report)

    # Save detailed report
    with open("config_transition_audit.md", "w") as f:
        f.write(report)

    print("\n✅ Configuration audit complete!")
    print("📄 Detailed report saved to: config_transition_audit.md")


if __name__ == "__main__":
    main()
