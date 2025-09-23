#!/usr/bin/env python3
"""
Dockerfile Audit and Hardening Script

Audits all service Dockerfiles for security issues, inconsistencies, and
best practice violations, then applies hardening fixes.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

import yaml


class DockerfileAuditor:
    """Audits and hardens Dockerfiles."""

    def __init__(self, services_dir: str = "services"):
        self.services_dir = Path(services_dir)
        self.audit_results = {}
        self.hardening_actions = []

    def audit_all_dockerfiles(self) -> Dict[str, Dict]:
        """Audit all service Dockerfiles."""
        results = {}

        for service_dir in self.services_dir.iterdir():
            if service_dir.is_dir() and not service_dir.name.startswith("_"):
                dockerfile_path = service_dir / "Dockerfile"
                if dockerfile_path.exists():
                    service_name = service_dir.name
                    results[service_name] = self.audit_dockerfile(service_name, dockerfile_path)

        return results

    def audit_dockerfile(self, service_name: str, dockerfile_path: Path) -> Dict:
        """Audit a single Dockerfile."""
        issues = []
        warnings = []
        hardening_needed = []

        with open(dockerfile_path, "r") as f:
            content = f.read()

        # Check for security issues
        if "USER root" in content or "sudo" in content:
            issues.append("Root user or sudo usage detected")

        if "RUN apt-get update && apt-get install" in content:
            if "rm -rf /var/lib/apt/lists/*" not in content:
                issues.append("Package cache not cleaned after apt-get install")

        # Check for best practices
        if "HEALTHCHECK" not in content:
            warnings.append("No HEALTHCHECK defined")
        else:
            # Check healthcheck quality
            if "--start-period=" not in content:
                warnings.append("HEALTHCHECK missing start-period")

        # Check for consistent structure
        required_labels = ["maintainer", "service", "version", "description"]
        for label in required_labels:
            if f"LABEL {label}=" not in content:
                hardening_needed.append(f"Missing LABEL {label}")

        # Check port consistency with docker-compose
        port_match = re.search(r'LABEL port="(\d+)"', content)
        if port_match:
            label_port = port_match.group(1)
            # Compare with docker-compose port mapping
            compose_port = self.get_service_port_from_compose(service_name)
            if compose_port and label_port != compose_port:
                issues.append(f"Port mismatch: LABEL port={label_port}, docker-compose port={compose_port}")

        # Check environment variables
        if "ENV PYTHONPATH=/app" not in content:
            hardening_needed.append("Missing PYTHONPATH environment variable")

        # Check for non-root user
        if "useradd" not in content and "USER " not in content:
            issues.append("No non-root user created")
        elif "USER " in content and "useradd" not in content:
            warnings.append("USER directive without proper user creation")

        # Check for security hardening
        if "--no-cache-dir" not in content:
            warnings.append("Not using --no-cache-dir for pip installs")

        return {
            "issues": issues,
            "warnings": warnings,
            "hardening_needed": hardening_needed,
            "security_score": self.calculate_security_score(issues, warnings),
        }

    def get_service_port_from_compose(self, service_name: str) -> str:
        """Get the internal port for a service from docker-compose."""
        compose_file = Path("docker-compose.dev.yml")
        if not compose_file.exists():
            return None

        with open(compose_file, "r") as f:
            compose_data = yaml.safe_load(f)

        services = compose_data.get("services", {})
        if service_name in services:
            service_config = services[service_name]
            ports = service_config.get("ports", [])
            if ports and isinstance(ports, list) and len(ports) > 0:
                port_mapping = str(ports[0])
                if ":" in port_mapping:
                    # Format: "external:internal"
                    parts = port_mapping.split(":")
                    if len(parts) == 2:
                        return parts[1].strip("\"'")

        return None

    def calculate_security_score(self, issues: List[str], warnings: List[str]) -> int:
        """Calculate a security score out of 100."""
        base_score = 100
        issue_penalty = 20
        warning_penalty = 5

        score = base_score - (len(issues) * issue_penalty) - (len(warnings) * warning_penalty)
        return max(0, score)

    def generate_hardening_report(self, results: Dict[str, Dict]) -> str:
        """Generate a comprehensive hardening report."""
        report = []
        report.append("# Dockerfile Security Audit & Hardening Report")
        report.append("=" * 60)
        report.append("")

        total_services = len(results)
        critical_issues = 0
        warnings_total = 0
        average_score = 0

        for service_name, audit_result in results.items():
            score = audit_result["security_score"]
            average_score += score

            issues = audit_result["issues"]
            warnings = audit_result["warnings"]
            hardening = audit_result["hardening_needed"]

            if issues:
                critical_issues += len(issues)
            warnings_total += len(warnings)

            report.append(f"## {service_name.upper()} (Security Score: {score}/100)")
            report.append("")

            if issues:
                report.append("### 🚨 CRITICAL ISSUES")
                for issue in issues:
                    report.append(f"- {issue}")
                report.append("")

            if warnings:
                report.append("### ⚠️  WARNINGS")
                for warning in warnings:
                    report.append(f"- {warning}")
                report.append("")

            if hardening:
                report.append("### 🔧 HARDENING NEEDED")
                for item in hardening:
                    report.append(f"- {item}")
                report.append("")

        # Summary
        average_score = average_score / total_services if total_services > 0 else 0

        report.append("## SUMMARY")
        report.append(f"- **Total Services Audited:** {total_services}")
        report.append(f"- **Critical Issues:** {critical_issues}")
        report.append(f"- **Warnings:** {warnings_total}")
        report.append(".1f")
        report.append("")

        if critical_issues > 0:
            report.append("### 🚨 IMMEDIATE ACTION REQUIRED")
            report.append("Critical security issues must be addressed before deployment.")
        elif warnings_total > 0:
            report.append("### ⚠️  RECOMMENDED IMPROVEMENTS")
            report.append("Address warnings to improve security posture.")
        else:
            report.append("### ✅ EXCELLENT SECURITY POSTURE")
            report.append("All Dockerfiles follow security best practices.")

        return "\n".join(report)

    def apply_hardening_fixes(self, results: Dict[str, Dict]) -> None:
        """Apply hardening fixes to Dockerfiles."""
        for service_name, audit_result in results.items():
            dockerfile_path = self.services_dir / service_name / "Dockerfile"

            if audit_result["issues"] or audit_result["hardening_needed"]:
                self.harden_dockerfile(service_name, dockerfile_path, audit_result)

    def harden_dockerfile(self, service_name: str, dockerfile_path: Path, audit_result: Dict) -> None:
        """Apply hardening fixes to a specific Dockerfile."""
        with open(dockerfile_path, "r") as f:
            content = f.read()

        original_content = content

        # Fix port consistency
        compose_port = self.get_service_port_from_compose(service_name)
        if compose_port:
            # Update LABEL port
            content = re.sub(r'LABEL port="\d+"', f'LABEL port="{compose_port}"', content)
            # Update ENV SERVICE_PORT
            content = re.sub(r"ENV SERVICE_PORT=\d+", f"ENV SERVICE_PORT={compose_port}", content)
            # Update HEALTHCHECK port
            content = re.sub(r"http://localhost:\d+/health", f"http://localhost:{compose_port}/health", content)
            # Update EXPOSE port
            content = re.sub(r"EXPOSE \d+", f"EXPOSE {compose_port}", content)

        # Add missing environment variables
        if "ENV PYTHONPATH=/app" not in content:
            # Find a good place to insert it (after other ENV statements)
            env_match = re.search(r"(ENV [^\n]+\n)+", content)
            if env_match:
                insert_pos = env_match.end()
                content = content[:insert_pos] + "ENV PYTHONPATH=/app\n" + content[insert_pos:]

        # Ensure proper USER directive placement
        if "USER appuser" in content:
            # Make sure USER comes after EXPOSE
            lines = content.split("\n")
            expose_idx = -1
            user_idx = -1

            for i, line in enumerate(lines):
                if line.startswith("EXPOSE"):
                    expose_idx = i
                elif line.startswith("USER"):
                    user_idx = i

            if expose_idx > user_idx and user_idx != -1:
                # Move USER after EXPOSE
                user_line = lines.pop(user_idx)
                lines.insert(expose_idx + 1, user_line)
                content = "\n".join(lines)

        # Save the hardened Dockerfile
        if content != original_content:
            with open(dockerfile_path, "w") as f:
                f.write(content)
            print(f"✅ Hardened {service_name} Dockerfile")
        else:
            print(f"ℹ️  No changes needed for {service_name} Dockerfile")


def main():
    """Main entry point."""
    auditor = DockerfileAuditor()

    print("🔍 Auditing Dockerfiles...")
    results = auditor.audit_all_dockerfiles()

    print("📋 Generating hardening report...")
    report = auditor.generate_hardening_report(results)
    print(report)

    print("\n🔧 Applying hardening fixes...")
    auditor.apply_hardening_fixes(results)

    print("\n✅ Dockerfile audit and hardening complete!")


if __name__ == "__main__":
    main()
