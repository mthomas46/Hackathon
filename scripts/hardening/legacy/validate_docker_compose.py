#!/usr/bin/env python3
"""
Docker Compose Validation Script

Validates docker-compose.yml files using Pydantic.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.shared.infrastructure.config.docker_pydantic import (
    validate_docker_compose_file, PYDANTIC_AVAILABLE
)


def main():
    """Validate all docker-compose files in the project."""
    if not PYDANTIC_AVAILABLE:
        print("❌ Pydantic not available")
        sys.exit(1)

    compose_files = list(project_root.glob("**/docker-compose*.yml"))
    compose_files.extend(list(project_root.glob("**/docker-compose*.yaml")))

    errors = 0
    for compose_file in compose_files:
        try:
            config = validate_docker_compose_file(compose_file)
            print(f"✅ {compose_file.parent.name}: {len(config.services)} services")
        except Exception as e:
            print(f"❌ {compose_file.parent.name}: {str(e)[:80]}...")
            errors += 1

    if errors > 0:
        print(f"❌ Found {errors} invalid Docker Compose files")
        sys.exit(1)
    else:
        print("✅ All Docker Compose files validated")


if __name__ == "__main__":
    main()
