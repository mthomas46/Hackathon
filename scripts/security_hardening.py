#!/usr/bin/env python3
"""
Security Hardening Script

Applies security hardening measures to Dockerfiles and service configurations.
"""

import os
import re
from pathlib import Path
from typing import Dict, List

import yaml


class SecurityHardener:
    """Applies security hardening to services."""

    def __init__(self, services_dir: str = "services"):
        self.services_dir = Path(services_dir)

    def harden_dockerfile(self, service_name: str, dockerfile_path: Path) -> bool:
        """Apply security hardening to a Dockerfile."""
        with open(dockerfile_path, "r") as f:
            content = f.read()

        original_content = content
        changes_made = []

        # Ensure non-root user creation
        if "useradd" not in content:
            # Add user creation before USER directive
            user_creation = "\n# Create non-root user for security\nRUN useradd -m -u 1000 -s /bin/bash appuser && \\\n    mkdir -p /app && \\\n    chown -R appuser:appuser /app\n"
            content = content.replace("EXPOSE", user_creation + "EXPOSE", 1)
            changes_made.append("Added non-root user creation")

        # Ensure USER directive exists
        if "USER appuser" not in content:
            # Add USER directive at the end
            content += "\n# Run as non-root user\nUSER appuser\n"
            changes_made.append("Added USER appuser directive")

        # Ensure proper permissions on copied files
        if "COPY" in content and "chown" not in content:
            # Add chown to COPY commands that copy to /app
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.strip().startswith("COPY") and "/app" in line:
                    if "services/" in line and not "--chown" in line:
                        lines[i] = line.replace("COPY", "COPY --chown=appuser:appuser")
                        changes_made.append("Added --chown to COPY commands")

            content = "\n".join(lines)

        # Add security-related environment variables
        security_env = [
            "ENV PYTHONUNBUFFERED=1",
            "ENV PYTHONDONTWRITEBYTECODE=1",
            "ENV PYTHONHASHSEED=random",
            "ENV PIP_NO_CACHE_DIR=1",
            "ENV PIP_DISABLE_PIP_VERSION_CHECK=1",
        ]

        env_section = []
        for env_var in security_env:
            if env_var not in content:
                env_section.append(env_var)

        if env_section:
            # Find where to insert security env vars
            if "ENV PYTHONPATH=/app" in content:
                content = content.replace("ENV PYTHONPATH=/app", "ENV PYTHONPATH=/app\n" + "\n".join(env_section))
            else:
                content = content.replace(
                    "WORKDIR /app", "WORKDIR /app\n\n# Security hardening\n" + "\n".join(env_section)
                )

            changes_made.append("Added security environment variables")

        # Ensure apt cache is cleaned
        if "apt-get install" in content and "rm -rf /var/lib/apt/lists/*" not in content:
            apt_lines = []
            in_apt_block = False
            for line in content.split("\n"):
                apt_lines.append(line)
                if "apt-get install" in line:
                    in_apt_block = True
                elif in_apt_block and line.strip() == "" or line.startswith("RUN") or line.startswith("COPY"):
                    apt_lines.insert(len(apt_lines) - 1, "    && rm -rf /var/lib/apt/lists/* \\\n    && apt-get clean")
                    in_apt_block = False
                    changes_made.append("Added apt cache cleanup")

            if in_apt_block:
                apt_lines.append("    && rm -rf /var/lib/apt/lists/* \\\n    && apt-get clean")

            content = "\n".join(apt_lines)

        # Remove unnecessary packages after installation
        if "apt-get install" in content and "--no-install-recommends" not in content:
            content = re.sub(r"apt-get install -y", "apt-get install -y --no-install-recommends", content)
            changes_made.append("Added --no-install-recommends to apt-get")

        # Save hardened Dockerfile
        if content != original_content:
            with open(dockerfile_path, "w") as f:
                f.write(content)

            print(f"🔒 Hardened {service_name} Dockerfile:")
            for change in changes_made:
                print(f"   ✓ {change}")
            return True

        return False

    def harden_makefile(self, service_name: str, makefile_path: Path) -> bool:
        """Apply security hardening to a Makefile."""
        with open(makefile_path, "r") as f:
            content = f.read()

        original_content = content
        changes_made = []

        # Add security-related targets
        security_targets = """

.PHONY: security-scan
security-scan: ## Run security scan on dependencies
	@echo "$(BLUE)🔒 Running security scan...$(NC)"
	@if command -v safety >/dev/null 2>&1; then \
		safety check --full-report; \
	else \
		echo "$(YELLOW)⚠️  safety not installed. Install with: pip install safety$(NC)"; \
	fi

.PHONY: audit-dependencies
audit-dependencies: ## Audit Python dependencies for vulnerabilities
	@echo "$(BLUE)📦 Auditing dependencies...$(NC)"
	@if command -v pip-audit >/dev/null 2>&1; then \
		pip-audit; \
	else \
		echo "$(YELLOW)⚠️  pip-audit not installed. Install with: pip install pip-audit$(NC)"; \
	fi

.PHONY: lint-security
lint-security: ## Run security-focused linting
	@echo "$(BLUE)🛡️  Running security linting...$(NC)"
	@if command -v bandit >/dev/null 2>&1; then \
		bandit -r . -f txt; \
	else \
		echo "$(YELLOW)⚠️  bandit not installed. Install with: pip install bandit$(NC)"; \
	fi

.PHONY: security-check
security-check: security-scan audit-dependencies lint-security ## Run all security checks
	@echo "$(GREEN)✅ Security checks completed$(NC)"
"""

        if "security-check:" not in content:
            content += security_targets
            changes_made.append("Added security check targets")

        # Add security-focused CI target
        ci_security = """
.PHONY: ci-security
ci-security: security-check test ## CI pipeline with security checks
	@echo "$(BLUE)🔄 Running CI with security...$(NC)"
	@echo "$(GREEN)✅ CI security pipeline complete$(NC)"
"""

        if "ci-security:" not in content:
            content += ci_security
            changes_made.append("Added CI security pipeline")

        # Save hardened Makefile
        if content != original_content:
            with open(makefile_path, "w") as f:
                f.write(content)

            print(f"🛡️  Hardened {service_name} Makefile:")
            for change in changes_made:
                print(f"   ✓ {change}")
            return True

        return False

    def harden_service_config(self, service_name: str) -> bool:
        """Add security configurations to service config files."""
        config_files = list(self.services_dir.glob(f"{service_name}/config.y*"))
        config_files = [f for f in config_files if f.is_file()]  # Only files, not directories

        if not config_files:
            return False

        config_file = config_files[0]

        try:
            with open(config_file, "r") as f:
                config = yaml.safe_load(f) or {}
        except Exception:
            config = {}

        changes_made = []

        # Add security section if it doesn't exist
        if "security" not in config:
            config["security"] = {
                "enable_ssl": "${SSL_ENABLED:-false}",
                "ssl_cert_path": "${SSL_CERT_PATH:-}",
                "ssl_key_path": "${SSL_KEY_PATH:-}",
                "cors_origins": "${CORS_ORIGINS:-http://localhost:3000}",
                "rate_limiting_enabled": "${RATE_LIMITING_ENABLED:-true}",
                "max_request_size": "${MAX_REQUEST_SIZE:-10485760}",  # 10MB
                "timeout_seconds": "${TIMEOUT_SECONDS:-30}",
                "enable_request_logging": "${REQUEST_LOGGING:-false}",
                "enable_metrics": "${METRICS_ENABLED:-true}",
            }
            changes_made.append("Added security configuration section")

        # Add development security settings
        if "development" not in config:
            config["development"] = {
                "debug_mode": "${DEBUG_MODE:-false}",
                "enable_cors": "${ENABLE_CORS:-true}",
                "mock_external_services": "${MOCK_EXTERNAL:-false}",
                "log_level": "${LOG_LEVEL:-INFO}",
            }
            changes_made.append("Added development configuration section")

        # Save updated config
        if changes_made:
            with open(config_file, "w") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

            print(f"🔐 Enhanced {service_name} config with security settings:")
            for change in changes_made:
                print(f"   ✓ {change}")
            return True

        return False

    def harden_all_services(self) -> None:
        """Apply security hardening to all services."""
        services = [
            d.name
            for d in self.services_dir.iterdir()
            if d.is_dir() and not d.name.startswith("_") and d.name not in ["redis", "ollama"]
        ]

        print("🔒 Applying security hardening to all services...")
        print("=" * 60)

        total_hardened = 0

        for service_name in services:
            print(f"\n🔧 Hardening {service_name}...")

            hardened = False

            # Harden Dockerfile
            dockerfile_path = self.services_dir / service_name / "Dockerfile"
            if dockerfile_path.exists():
                if self.harden_dockerfile(service_name, dockerfile_path):
                    hardened = True

            # Harden Makefile
            makefile_path = self.services_dir / service_name / "Makefile"
            if makefile_path.exists():
                if self.harden_makefile(service_name, makefile_path):
                    hardened = True

            # Harden config
            if self.harden_service_config(service_name):
                hardened = True

            if hardened:
                total_hardened += 1
            else:
                print(f"   ℹ️  No hardening needed for {service_name}")

        print(f"\n{'='*60}")
        print(f"🔒 Security hardening complete!")
        print(f"   Services hardened: {total_hardened}/{len(services)}")
        print(f"   Coverage: {(total_hardened * 100) // len(services)}%")


def main():
    """Main entry point."""
    hardener = SecurityHardener()
    hardener.harden_all_services()


if __name__ == "__main__":
    main()
