#!/usr/bin/env python3
"""
Docker Compose Validator for Pre-Flight Checks

Validates Docker configurations specifically for docker-compose operations.
Used as a pre-flight check before docker-compose commands.
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.shared.infrastructure.config.docker_pydantic import (
    validate_docker_compose_file, PYDANTIC_AVAILABLE
)


def validate_docker_compose_for_startup(compose_file: str = "docker-compose.dev.yml") -> bool:
    """
    Validate Docker Compose file specifically for startup operations.

    Args:
        compose_file: Path to docker-compose file to validate

    Returns:
        True if validation passes, False otherwise
    """
    if not PYDANTIC_AVAILABLE:
        print("❌ Pydantic not available for Docker validation")
        return False

    compose_path = project_root / compose_file
    if not compose_path.exists():
        print(f"❌ Docker Compose file not found: {compose_file}")
        return False

    try:
        config = validate_docker_compose_file(compose_path)

        # Additional startup-specific validations
        issues = []

        # Check for services with build but no context
        for service_name, service in config.services.items():
            if service.build and isinstance(service.build, dict):
                if 'context' not in service.build:
                    issues.append(f"Service '{service_name}' has build section but no context")

        # Check for circular dependencies (already handled by Pydantic model)
        # But we can add more specific checks here

        # Check for services with depends_on as strings instead of lists
        for service_name, service in config.services.items():
            if isinstance(service.depends_on, str):
                issues.append(f"Service '{service_name}' depends_on should be a list, not a string")

        if issues:
            print("❌ Docker Compose validation issues:")
            for issue in issues:
                print(f"  • {issue}")
            return False

        print(f"✅ Docker Compose file validated: {len(config.services)} services, {len(config.networks)} networks, {len(config.volumes)} volumes")
        return True

    except Exception as e:
        print(f"❌ Docker Compose validation failed: {str(e)[:100]}...")
        return False


def validate_docker_compose_pre_flight(compose_files: List[str] = None) -> bool:
    """
    Run pre-flight validation for Docker Compose operations.

    Args:
        compose_files: List of docker-compose files to validate

    Returns:
        True if all validations pass
    """
    if compose_files is None:
        compose_files = ["docker-compose.dev.yml"]

    all_valid = True

    for compose_file in compose_files:
        print(f"🔍 Validating {compose_file}...")
        if not validate_docker_compose_for_startup(compose_file):
            all_valid = False

    return all_valid


def main():
    """Main validation script for docker-compose operations."""
    import argparse

    parser = argparse.ArgumentParser(description="Docker Compose Pre-Flight Validator")
    parser.add_argument('--files', '-f', nargs='*', default=["docker-compose.dev.yml"],
                       help='Docker Compose files to validate')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Quiet mode - no output, just exit code')

    args = parser.parse_args()

    if not args.quiet:
        print("🐳 Docker Compose Pre-Flight Validation")
        print("=" * 50)

    success = validate_docker_compose_pre_flight(args.files)

    if not args.quiet:
        if success:
            print("\n✅ All Docker Compose files validated for startup")
        else:
            print("\n❌ Docker Compose validation failed")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
