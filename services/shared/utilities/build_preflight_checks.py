"""Build Process Preflight Checks - Docker build validation and dependency checking.

Ensures build stability by validating environment, dependencies, and configurations
before Docker builds proceed. Prevents build failures and provides early feedback.
"""

import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


@dataclass
class BuildCheck:
    """Represents a single build check."""

    name: str
    description: str
    required: bool = True
    check_func: callable = None
    fix_suggestion: str = ""


@dataclass
class BuildCheckResult:
    """Result of a build check."""

    check: BuildCheck
    passed: bool
    message: str
    details: Dict[str, Any] = None
    duration: float = 0.0


class BuildPreflightChecker:
    """Comprehensive build preflight checker for Docker builds."""

    def __init__(self, service_name: str, service_path: str = None):
        self.service_name = service_name
        self.service_path = Path(service_path) if service_path else Path.cwd()
        self.project_root = self._find_project_root()
        self.checks: List[BuildCheck] = []
        self.results: List[BuildCheckResult] = []

        # Initialize default checks
        self._initialize_checks()

    def _find_project_root(self) -> Path:
        """Find the project root directory."""
        current = self.service_path
        while current.parent != current:
            if (current / "docker-compose.dev.yml").exists():
                return current
            current = current.parent
        return self.service_path

    def _initialize_checks(self):
        """Initialize all default build checks."""
        self.checks = [
            BuildCheck(
                name="docker_available",
                description="Docker daemon is available and accessible",
                check_func=self._check_docker_available,
                fix_suggestion="Start Docker daemon or install Docker",
            ),
            BuildCheck(
                name="dockerfile_exists",
                description="Dockerfile exists in service directory",
                check_func=self._check_dockerfile_exists,
                fix_suggestion="Create Dockerfile in service directory",
            ),
            BuildCheck(
                name="dockerfile_valid",
                description="Dockerfile syntax is valid",
                check_func=self._check_dockerfile_valid,
                fix_suggestion="Fix Dockerfile syntax errors",
            ),
            BuildCheck(
                name="dependencies_resolvable",
                description="All required dependencies are available",
                check_func=self._check_dependencies_resolvable,
                fix_suggestion="Check requirements.txt or package.json files",
            ),
            BuildCheck(
                name="build_context_size",
                description="Build context size is reasonable",
                check_func=self._check_build_context_size,
                fix_suggestion="Use .dockerignore to exclude unnecessary files",
            ),
            BuildCheck(
                name="security_vulnerabilities",
                description="No critical security vulnerabilities in dependencies",
                required=False,  # Warning only
                check_func=self._check_security_vulnerabilities,
                fix_suggestion="Update dependencies to fix security issues",
            ),
            BuildCheck(
                name="shared_utilities_compatible",
                description="Shared utilities are compatible with service",
                check_func=self._check_shared_utilities_compatibility,
                fix_suggestion="Update service to use compatible shared utilities",
            ),
            BuildCheck(
                name="environment_variables_defined",
                description="Required environment variables are defined",
                check_func=self._check_environment_variables,
                fix_suggestion="Define required environment variables",
            ),
            BuildCheck(
                name="network_ports_available",
                description="Required network ports are available",
                check_func=self._check_network_ports,
                fix_suggestion="Ensure ports are not in use by other services",
            ),
            BuildCheck(
                name="disk_space_sufficient",
                description="Sufficient disk space for build",
                check_func=self._check_disk_space,
                fix_suggestion="Free up disk space or use external build cache",
            ),
        ]

    async def run_all_checks(self) -> List[BuildCheckResult]:
        """Run all preflight checks and return results."""
        import time

        self.results = []
        logger.info(f"Running {len(self.checks)} preflight checks for {self.service_name}")

        for check in self.checks:
            start_time = time.time()
            try:
                passed, message, details = await check.check_func()
                duration = time.time() - start_time

                result = BuildCheckResult(
                    check=check, passed=passed, message=message, details=details or {}, duration=duration
                )

                self.results.append(result)

                status = "PASS" if passed else "FAIL"
                logger.info(f"[{status}] {check.name}: {message} ({duration:.2f}s)")

                if not passed and check.required:
                    logger.error(f"Required check failed: {check.name}")
                    break  # Stop on first required failure

            except Exception as e:
                duration = time.time() - start_time
                result = BuildCheckResult(
                    check=check,
                    passed=False,
                    message=f"Check failed with exception: {str(e)}",
                    details={"error": str(e)},
                    duration=duration,
                )
                self.results.append(result)
                logger.error(f"[ERROR] {check.name}: {str(e)} ({duration:.2f}s)")

                if check.required:
                    break

        return self.results

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of check results."""
        total = len(self.results)
        passed = len([r for r in self.results if r.passed])
        failed = total - passed
        required_failed = len([r for r in self.results if not r.passed and r.check.required])

        return {
            "service_name": self.service_name,
            "total_checks": total,
            "passed": passed,
            "failed": failed,
            "required_failed": required_failed,
            "success": required_failed == 0,
            "total_duration": sum(r.duration for r in self.results),
            "results": [
                {
                    "name": r.check.name,
                    "passed": r.passed,
                    "required": r.check.required,
                    "message": r.message,
                    "duration": r.duration,
                }
                for r in self.results
            ],
        }

    async def _check_docker_available(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Check if Docker is available."""
        try:
            result = await self._run_command(["docker", "version"], timeout=10)
            if result.returncode == 0:
                # Parse version info
                lines = result.stdout.strip().split("\n")
                version_info = {}
                for line in lines[:2]:  # First two lines typically have version info
                    if "Version:" in line:
                        version_info["docker_version"] = line.split("Version:")[1].strip()
                    elif "API version:" in line:
                        version_info["api_version"] = line.split("API version:")[1].strip()

                return True, "Docker is available and accessible", version_info

            return False, f"Docker version check failed: {result.stderr}", {}
        except Exception as e:
            return False, f"Docker not available: {str(e)}", {}

    async def _check_dockerfile_exists(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Check if Dockerfile exists."""
        dockerfile_path = self.service_path / "Dockerfile"
        if dockerfile_path.exists():
            stat = dockerfile_path.stat()
            return (
                True,
                f"Dockerfile found at {dockerfile_path}",
                {"path": str(dockerfile_path), "size": stat.st_size, "modified": stat.st_mtime},
            )

        # Try common Dockerfile names
        for name in ["Dockerfile", "dockerfile", "Dockerfile.dev", "Dockerfile.prod"]:
            alt_path = self.service_path / name
            if alt_path.exists():
                stat = alt_path.stat()
                return (
                    True,
                    f"Dockerfile found as {name}",
                    {"path": str(alt_path), "size": stat.st_size, "modified": stat.st_mtime},
                )

        return (
            False,
            "No Dockerfile found in service directory",
            {
                "searched_paths": [
                    str(self.service_path / name)
                    for name in ["Dockerfile", "dockerfile", "Dockerfile.dev", "Dockerfile.prod"]
                ]
            },
        )

    async def _check_dockerfile_valid(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Check if Dockerfile syntax is valid."""
        dockerfile_path = self.service_path / "Dockerfile"

        # Try alternative names if main Dockerfile doesn't exist
        if not dockerfile_path.exists():
            for name in ["dockerfile", "Dockerfile.dev", "Dockerfile.prod"]:
                alt_path = self.service_path / name
                if alt_path.exists():
                    dockerfile_path = alt_path
                    break

        if not dockerfile_path.exists():
            return False, "Dockerfile not found", {}

        try:
            # Use docker build --dry-run or docker build with a fake tag to validate syntax
            result = await self._run_command(
                [
                    "docker",
                    "build",
                    "--dry-run",
                    "-t",
                    f"preflight-check-{self.service_name.lower().replace('_', '-')}",
                    "-f",
                    str(dockerfile_path),
                    str(self.service_path),
                ],
                timeout=30,
            )

            if result.returncode == 0:
                return True, "Dockerfile syntax is valid", {}
            else:
                return (
                    False,
                    f"Dockerfile syntax error: {result.stderr}",
                    {"error": result.stderr, "stdout": result.stdout},
                )

        except Exception as e:
            return False, f"Failed to validate Dockerfile: {str(e)}", {"error": str(e)}

    async def _check_dependencies_resolvable(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Check if dependencies can be resolved."""
        issues = []
        details = {}

        # Check Python requirements
        requirements_files = ["requirements.txt", "pyproject.toml", "Pipfile"]
        for req_file in requirements_files:
            req_path = self.service_path / req_file
            if req_path.exists():
                try:
                    if req_file == "requirements.txt":
                        # Try to parse requirements without installing
                        with open(req_path, "r") as f:
                            content = f.read()
                        lines = [
                            line.strip() for line in content.split("\n") if line.strip() and not line.startswith("#")
                        ]
                        details["python_requirements"] = len(lines)
                    elif req_file == "pyproject.toml":
                        details["has_pyproject"] = True
                    elif req_file == "Pipfile":
                        details["has_pipfile"] = True
                except Exception as e:
                    issues.append(f"Error reading {req_file}: {str(e)}")

        # Check Node.js dependencies
        package_json = self.service_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json, "r") as f:
                    package_data = json.load(f)
                details["node_dependencies"] = len(package_data.get("dependencies", {}))
                details["node_dev_dependencies"] = len(package_data.get("devDependencies", {}))
            except Exception as e:
                issues.append(f"Error reading package.json: {str(e)}")

        # Check Go modules
        go_mod = self.service_path / "go.mod"
        if go_mod.exists():
            details["has_go_mod"] = True

        if issues:
            return False, f"Dependency issues found: {'; '.join(issues)}", details

        if not any(key in details for key in ["python_requirements", "node_dependencies", "has_go_mod"]):
            return False, "No dependency files found (requirements.txt, package.json, go.mod)", details

        return True, "Dependencies appear resolvable", details

    async def _check_build_context_size(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Check build context size."""
        try:
            total_size = 0
            file_count = 0
            large_files = []

            # Check for .dockerignore
            dockerignore = self.service_path / ".dockerignore"
            has_dockerignore = dockerignore.exists()

            # Calculate build context size (excluding common exclusions)
            exclude_patterns = (
                [
                    "__pycache__",
                    "*.pyc",
                    ".git",
                    ".DS_Store",
                    "node_modules",
                    ".next",
                    "dist",
                    "build",
                    "*.log",
                    ".env",
                    ".venv",
                    "venv",
                ]
                if not has_dockerignore
                else []
            )

            for root, dirs, files in os.walk(self.service_path):
                # Skip excluded directories
                dirs[:] = [d for d in dirs if not any(pattern in d for pattern in exclude_patterns)]

                for file in files:
                    if not any(pattern in file for pattern in exclude_patterns):
                        file_path = Path(root) / file
                        try:
                            size = file_path.stat().st_size
                            total_size += size
                            file_count += 1

                            # Track large files (>10MB)
                            if size > 10 * 1024 * 1024:
                                large_files.append(
                                    {
                                        "path": str(file_path.relative_to(self.service_path)),
                                        "size_mb": size / (1024 * 1024),
                                    }
                                )
                        except OSError:
                            pass  # Skip files we can't read

            size_mb = total_size / (1024 * 1024)
            size_gb = total_size / (1024 * 1024 * 1024)

            details = {
                "total_size_mb": size_mb,
                "file_count": file_count,
                "has_dockerignore": has_dockerignore,
                "large_files": large_files[:10],  # Top 10 largest files
            }

            # Warn if build context > 1GB or has many large files
            if size_gb > 1:
                return False, f"Build context too large: {size_gb:.2f}GB ({file_count} files)", details
            elif len(large_files) > 5:
                return False, f"Too many large files in build context: {len(large_files)} files >10MB", details
            elif not has_dockerignore:
                return True, f"Build context size: {size_mb:.2f}MB (consider adding .dockerignore)", details

            return True, f"Build context size acceptable: {size_mb:.2f}MB", details

        except Exception as e:
            return False, f"Failed to check build context: {str(e)}", {"error": str(e)}

    async def _check_security_vulnerabilities(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Check for security vulnerabilities in dependencies."""
        # This is a basic check - in production you'd use tools like:
        # - safety (Python)
        # - npm audit (Node.js)
        # - trivy (container scanning)
        # For now, we'll do basic checks

        vulnerabilities = []

        # Check for known vulnerable patterns in requirements.txt
        req_file = self.service_path / "requirements.txt"
        if req_file.exists():
            try:
                with open(req_file, "r") as f:
                    content = f.read()

                # Simple checks for known vulnerable versions
                if "Django==1.11" in content or "Django<2.0" in content:
                    vulnerabilities.append("Potentially vulnerable Django version")
                if "flask<1.0" in content:
                    vulnerabilities.append("Potentially vulnerable Flask version")

            except Exception as e:
                vulnerabilities.append(f"Error checking requirements.txt: {str(e)}")

        if vulnerabilities:
            return (
                False,
                f"Security vulnerabilities found: {'; '.join(vulnerabilities)}",
                {"vulnerabilities": vulnerabilities},
            )

        return True, "No obvious security vulnerabilities detected", {}

    async def _check_shared_utilities_compatibility(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Check compatibility with shared utilities."""
        try:
            # Check if service imports shared utilities
            shared_usage = False
            import_statements = []

            # Look for Python files that import shared utilities
            for py_file in self.service_path.rglob("*.py"):
                try:
                    with open(py_file, "r") as f:
                        content = f.read()
                    if "from services.shared.utilities" in content:
                        shared_usage = True
                        # Extract import lines
                        lines = content.split("\n")
                        for line in lines:
                            if "from services.shared.utilities" in line:
                                import_statements.append(line.strip())
                except Exception:
                    pass

            if not shared_usage:
                return True, "Service does not use shared utilities", {}

            # Check if shared utilities directory exists
            shared_dir = self.project_root / "services" / "shared" / "utilities"
            if not shared_dir.exists():
                return (
                    False,
                    "Shared utilities directory not found",
                    {"shared_dir_path": str(shared_dir), "imports_found": import_statements[:5]},
                )

            # Check if __init__.py exists
            init_file = shared_dir / "__init__.py"
            if not init_file.exists():
                return False, "Shared utilities __init__.py not found", {"init_file_path": str(init_file)}

            return (
                True,
                "Shared utilities compatibility verified",
                {"imports_found": len(import_statements), "shared_dir_exists": True},
            )

        except Exception as e:
            return False, f"Failed to check shared utilities compatibility: {str(e)}", {"error": str(e)}

    async def _check_environment_variables(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Check if required environment variables are defined."""
        try:
            # Look for environment variable references in code
            env_vars_found = set()
            required_env_vars = set()

            for py_file in self.service_path.rglob("*.py"):
                try:
                    with open(py_file, "r") as f:
                        content = f.read()

                    # Find os.environ.get() calls
                    import re

                    env_get_matches = re.findall(r'os\.environ\.get\(["\']([^"\']+)["\']', content)
                    env_vars_found.update(env_get_matches)

                    # Find direct os.environ[] access
                    env_direct_matches = re.findall(r'os\.environ\[["\']([^"\']+)["\']', content)
                    env_vars_found.update(env_direct_matches)

                except Exception:
                    pass

            # Check which variables are actually defined
            missing_vars = []
            for var in env_vars_found:
                if var not in os.environ and not var.startswith(("SERVICE_", "PYTHONPATH")):
                    # Some variables might have defaults or be optional
                    if not any(default_indicator in var for default_indicator in ["_URL", "_HOST", "_PORT"]):
                        required_env_vars.add(var)
                    else:
                        missing_vars.append(var)

            if required_env_vars:
                return (
                    False,
                    f"Required environment variables not defined: {', '.join(sorted(required_env_vars))}",
                    {"required_vars": sorted(required_env_vars), "optional_missing": sorted(missing_vars)},
                )

            return (
                True,
                "Environment variables check passed",
                {"vars_found": len(env_vars_found), "optional_missing": sorted(missing_vars)},
            )

        except Exception as e:
            return False, f"Failed to check environment variables: {str(e)}", {"error": str(e)}

    async def _check_network_ports(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Check if required network ports are available."""
        try:
            import socket

            # Look for port configurations in environment or config
            ports_to_check = set()

            # Check environment variables for SERVICE_PORT
            service_port = os.environ.get("SERVICE_PORT")
            if service_port:
                try:
                    ports_to_check.add(int(service_port))
                except ValueError:
                    pass

            # Check docker-compose for port mappings
            compose_file = self.project_root / "docker-compose.dev.yml"
            if compose_file.exists():
                try:
                    import yaml

                    with open(compose_file, "r") as f:
                        compose_data = yaml.safe_load(f)

                    service_config = compose_data.get("services", {}).get(self.service_name, {})
                    ports = service_config.get("ports", [])
                    for port_mapping in ports:
                        if isinstance(port_mapping, str):
                            # Format: "host_port:container_port"
                            host_port = port_mapping.split(":")[0]
                            try:
                                ports_to_check.add(int(host_port))
                            except ValueError:
                                pass
                except Exception:
                    pass

            # Check if ports are available
            unavailable_ports = []
            for port in ports_to_check:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex(("127.0.0.1", port))
                    sock.close()
                    if result == 0:
                        unavailable_ports.append(port)
                except Exception:
                    pass  # Assume port is available if we can't check

            if unavailable_ports:
                return (
                    False,
                    f"Required ports are in use: {', '.join(map(str, unavailable_ports))}",
                    {"ports_checked": sorted(ports_to_check), "unavailable_ports": sorted(unavailable_ports)},
                )

            return (
                True,
                f"Network ports available: {', '.join(map(str, sorted(ports_to_check)))}",
                {"ports_checked": sorted(ports_to_check)},
            )

        except Exception as e:
            return False, f"Failed to check network ports: {str(e)}", {"error": str(e)}

    async def _check_disk_space(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Check if sufficient disk space is available for build."""
        try:
            stat = os.statvfs(self.service_path)
            free_bytes = stat.f_bavail * stat.f_frsize
            free_gb = free_bytes / (1024**3)

            # Require at least 2GB free space for builds
            min_required_gb = 2.0

            details = {
                "free_space_gb": free_gb,
                "min_required_gb": min_required_gb,
                "sufficient": free_gb >= min_required_gb,
            }

            if free_gb < min_required_gb:
                return False, f"Insufficient disk space: {free_gb:.2f}GB free, {min_required_gb}GB required", details

            return True, f"Sufficient disk space available: {free_gb:.2f}GB", details

        except Exception as e:
            return False, f"Failed to check disk space: {str(e)}", {"error": str(e)}

    async def _run_command(self, cmd: List[str], timeout: int = 30) -> subprocess.CompletedProcess:
        """Run a command asynchronously."""
        import asyncio

        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=str(self.service_path)
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            return subprocess.CompletedProcess(
                cmd,
                process.returncode,
                stdout.decode("utf-8", errors="ignore"),
                stderr.decode("utf-8", errors="ignore"),
            )
        except asyncio.TimeoutError:
            process.kill()
            raise Exception(f"Command timed out after {timeout}s")


# Convenience functions
async def run_preflight_checks(service_name: str, service_path: str = None) -> Dict[str, Any]:
    """Run preflight checks for a service and return summary."""
    checker = BuildPreflightChecker(service_name, service_path)
    await checker.run_all_checks()
    return checker.get_summary()


def create_preflight_dockerfile_checker(service_name: str, service_path: str = None) -> BuildPreflightChecker:
    """Create a preflight checker for Dockerfile validation."""
    return BuildPreflightChecker(service_name, service_path)


# CLI integration for Docker builds
def integrate_with_docker_build():
    """Integrate preflight checks with Docker build process.

    Usage in Dockerfile:
    # Add this at the top of your Dockerfile
    COPY services/shared/utilities/build_preflight_checks.py /tmp/
    RUN python /tmp/build_preflight_checks.py --check-only
    """
    if len(sys.argv) > 1 and sys.argv[1] == "--check-only":
        # Run checks and exit with appropriate code
        import asyncio

        async def main():
            service_name = os.environ.get("SERVICE_NAME", "unknown-service")
            checker = BuildPreflightChecker(service_name)
            results = await checker.run_all_checks()
            summary = checker.get_summary()

            if summary["success"]:
                print(f"✅ All preflight checks passed for {service_name}")
                sys.exit(0)
            else:
                print(f"❌ Preflight checks failed for {service_name}")
                failed_required = [r for r in results if not r.passed and r.check.required]
                for result in failed_required:
                    print(f"  - {result.check.name}: {result.message}")
                sys.exit(1)

        asyncio.run(main())


if __name__ == "__main__":
    integrate_with_docker_build()
