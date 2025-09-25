"""
ServiceDiscoveryService - Infrastructure Service

Handles automatic discovery and registration of services in the ecosystem.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from domain.entities.service_info import ServiceInfo

logger = logging.getLogger(__name__)


class ServiceDiscoveryService:
    """Infrastructure service for discovering services in the ecosystem.

    Automatically scans directories to find and register services
    based on common patterns and file structures.
    """

    def __init__(self, search_paths: Optional[List[Path]] = None):
        """Initialize the service discovery service.

        Args:
            search_paths: List of paths to search for services
        """
        self.search_paths = search_paths or [
            Path.cwd() / "services",
            Path.cwd().parent / "services",
            Path.cwd(),
        ]

    def discover_services(self) -> List[ServiceInfo]:
        """Discover all services in the configured search paths."""
        services = []

        for search_path in self.search_paths:
            if search_path.exists() and search_path.is_dir():
                discovered = self._scan_directory_for_services(search_path)
                services.extend(discovered)

        # Remove duplicates based on service name
        seen_names = set()
        unique_services = []
        for service in services:
            if service.name not in seen_names:
                unique_services.append(service)
                seen_names.add(service.name)

        logger.info(f"Discovered {len(unique_services)} unique services")
        return unique_services

    def _scan_directory_for_services(self, directory: Path) -> List[ServiceInfo]:
        """Scan a directory for service patterns."""
        services = []

        try:
            # Look for service directories (contain main.py, app.py, etc.)
            for item in directory.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    service = self._analyze_potential_service(item)
                    if service:
                        services.append(service)

        except (OSError, PermissionError) as e:
            logger.warning(f"Error scanning directory {directory}: {e}")

        return services

    def _analyze_potential_service(self, service_path: Path) -> Optional[ServiceInfo]:
        """Analyze a directory to determine if it's a service."""
        # Check for service indicators
        service_indicators = [
            service_path / "main.py",
            service_path / "app.py",
            service_path / "run.py",
            service_path / "manage.py",
            service_path / "requirements.txt",
            service_path / "pyproject.toml",
            service_path / "setup.py",
        ]

        has_service_files = any(indicator.exists() for indicator in service_indicators)

        if not has_service_files:
            return None

        # Determine service type
        service_type = self._determine_service_type(service_path)

        # Create service info
        service_info = ServiceInfo(
            name=service_path.name,
            path=service_path,
            type=service_type,
            status="unknown",  # Will be determined by health checks
            metadata=self._extract_service_metadata(service_path)
        )

        return service_info

    def _determine_service_type(self, service_path: Path) -> str:
        """Determine the type of service based on file patterns."""
        # Check for FastAPI
        if (service_path / "main.py").exists():
            with open(service_path / "main.py", 'r', encoding='utf-8') as f:
                content = f.read()
                if 'FastAPI' in content or 'from fastapi' in content:
                    return "fastapi"

        # Check for Flask
        if any((service_path / f).exists() for f in ["app.py", "run.py"]):
            for filename in ["app.py", "run.py", "main.py"]:
                filepath = service_path / filename
                if filepath.exists():
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if 'Flask' in content or 'from flask' in content:
                                return "flask"
                    except (IOError, UnicodeDecodeError):
                        continue

        # Check for Django
        if (service_path / "manage.py").exists() or (service_path / "settings.py").exists():
            return "django"

        # Check for Node.js
        if (service_path / "package.json").exists():
            return "node"

        # Default to python
        return "python"

    def _extract_service_metadata(self, service_path: Path) -> Dict[str, Any]:
        """Extract metadata about the service."""
        metadata = {}

        # Try to read requirements.txt for dependencies
        requirements_file = service_path / "requirements.txt"
        if requirements_file.exists():
            try:
                with open(requirements_file, 'r', encoding='utf-8') as f:
                    dependencies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                    metadata["dependencies"] = dependencies[:10]  # Limit to first 10
            except (IOError, UnicodeDecodeError):
                pass

        # Try to read README for description
        readme_files = ["README.md", "README.rst", "README.txt"]
        for readme_file in readme_files:
            readme_path = service_path / readme_file
            if readme_path.exists():
                try:
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Extract first paragraph as description
                        paragraphs = content.split('\n\n')
                        if paragraphs:
                            description = paragraphs[0].strip()
                            if len(description) > 200:
                                description = description[:197] + "..."
                            metadata["description"] = description
                            break
                except (IOError, UnicodeDecodeError):
                    continue

        # Check for Docker
        if (service_path / "Dockerfile").exists():
            metadata["has_docker"] = True

        # Check for tests
        test_dirs = ["tests", "test"]
        has_tests = any((service_path / test_dir).exists() for test_dir in test_dirs)
        metadata["has_tests"] = has_tests

        return metadata

    def validate_service(self, service_info: ServiceInfo) -> Dict[str, Any]:
        """Validate that a discovered service is properly configured."""
        validation = {
            "is_valid": True,
            "issues": [],
            "warnings": []
        }

        service_path = service_info.path

        # Check for required files based on type
        if service_info.type in ["fastapi", "flask", "django"]:
            required_files = ["requirements.txt"]
            for req_file in required_files:
                if not (service_path / req_file).exists():
                    validation["issues"].append(f"Missing {req_file}")

        # Check for main entry point
        main_files = ["main.py", "app.py", "run.py", "manage.py"]
        has_entry_point = any((service_path / main_file).exists() for main_file in main_files)
        if not has_entry_point:
            validation["issues"].append("No main entry point found")

        # Check for tests
        if not service_info.metadata.get("has_tests", False):
            validation["warnings"].append("No test directory found")

        # Determine validity
        validation["is_valid"] = len(validation["issues"]) == 0

        return validation
