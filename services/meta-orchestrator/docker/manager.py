"""Docker operations manager for the Meta-Orchestration Service"""

import asyncio
import logging
import subprocess
import json
import os
from typing import List, Optional, Dict, Any
from pathlib import Path

from config.settings import DockerSettings
from models.container import ContainerInfo
from models.result import OperationResult
from utils.exceptions import DockerError

logger = logging.getLogger(__name__)


class DockerManager:
    """Manages Docker and Docker Compose operations"""

    def __init__(self, docker_settings: DockerSettings):
        self.settings = docker_settings
        self.workspace_path: Optional[Path] = None
        self.client = None

    async def initialize(self) -> None:
        """Initialize Docker client"""
        try:
            # We'll use subprocess calls to docker/docker-compose for reliability
            # rather than the Python client which can have connection issues
            logger.info("🐳 Docker manager initialized (using subprocess)")

            # Set workspace path if not set
            if not self.workspace_path:
                self.workspace_path = Path("/app")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Docker manager: {e}")
            raise DockerError(f"Docker initialization failed: {e}")

    async def cleanup(self) -> None:
        """Cleanup Docker resources"""
        try:
            if self.client:
                # Close client if using Python client
                pass
            logger.info("🧹 Docker manager cleanup completed")
        except Exception as e:
            logger.error(f"❌ Error during Docker cleanup: {e}")

    async def list_containers(self, all: bool = True) -> List[ContainerInfo]:
        """List Docker containers"""
        try:
            cmd = ["docker", "ps", "--format", "json"]
            if all:
                cmd.append("-a")

            result = await self._run_command(cmd)
            containers = []

            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    try:
                        container_data = json.loads(line)
                        container = ContainerInfo(
                            id=container_data.get("ID", ""),
                            name=container_data.get("Names", "").lstrip("/"),
                            image=container_data.get("Image", ""),
                            status=container_data.get("Status", ""),
                            ports=container_data.get("Ports", "")
                        )
                        containers.append(container)
                    except json.JSONDecodeError:
                        continue

            return containers

        except Exception as e:
            logger.error(f"❌ Failed to list containers: {e}")
            return []

    async def compose_up(self, services: List[str], profile: str = "all") -> OperationResult:
        """Start services using docker-compose"""
        try:
            cmd = ["docker", "compose", "-f", "docker-compose.dev.yml", "up", "-d"]

            # Add profile
            if profile and profile != "all":
                cmd.extend(["--profile", profile])

            # Add specific services
            if services:
                cmd.extend(services)

            result = await self._run_command(cmd, cwd=self.workspace_path)

            return OperationResult(
                success=result.returncode == 0,
                message=result.stdout if result.returncode == 0 else result.stderr
            )

        except Exception as e:
            logger.error(f"❌ Failed to start services {services}: {e}")
            return OperationResult(
                success=False,
                message=f"Failed to start services: {e}"
            )

    async def compose_down(self, services: List[str]) -> OperationResult:
        """Stop services using docker-compose"""
        try:
            cmd = ["docker", "compose", "-f", "docker-compose.dev.yml", "down"]

            # Add specific services
            if services:
                cmd.extend(services)

            result = await self._run_command(cmd, cwd=self.workspace_path)

            return OperationResult(
                success=result.returncode == 0,
                message=result.stdout if result.returncode == 0 else result.stderr
            )

        except Exception as e:
            logger.error(f"❌ Failed to stop services {services}: {e}")
            return OperationResult(
                success=False,
                message=f"Failed to stop services: {e}"
            )

    async def compose_restart(self, services: List[str]) -> OperationResult:
        """Restart services using docker-compose"""
        try:
            cmd = ["docker", "compose", "-f", "docker-compose.dev.yml", "restart"]

            if services:
                cmd.extend(services)

            result = await self._run_command(cmd, cwd=self.workspace_path)

            return OperationResult(
                success=result.returncode == 0,
                message=result.stdout if result.returncode == 0 else result.stderr
            )

        except Exception as e:
            logger.error(f"❌ Failed to restart services {services}: {e}")
            return OperationResult(
                success=False,
                message=f"Failed to restart services: {e}"
            )

    async def get_container_logs(self, service_name: str, lines: int = 100) -> str:
        """Get logs for a container"""
        try:
            cmd = ["docker", "logs", "--tail", str(lines), service_name]
            result = await self._run_command(cmd)

            if result.returncode == 0:
                return result.stdout
            else:
                return f"Error getting logs: {result.stderr}"

        except Exception as e:
            logger.error(f"❌ Failed to get logs for {service_name}: {e}")
            return f"Error retrieving logs: {e}"

    async def inspect_container(self, container_id: str) -> Optional[Dict[str, Any]]:
        """Inspect a container"""
        try:
            cmd = ["docker", "inspect", container_id]
            result = await self._run_command(cmd)

            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.error(f"❌ Failed to inspect container {container_id}: {result.stderr}")
                return None

        except Exception as e:
            logger.error(f"❌ Failed to inspect container {container_id}: {e}")
            return None

    async def get_service_status(self, service_name: str) -> Optional[str]:
        """Get the status of a specific service"""
        try:
            containers = await self.list_containers()
            for container in containers:
                if container.name.startswith(service_name):
                    return container.status
            return "not found"
        except Exception as e:
            logger.error(f"❌ Failed to get status for {service_name}: {e}")
            return None

    async def _run_command(self, cmd: List[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
        """Run a command asynchronously"""
        try:
            # Use the host environment but override DOCKER_HOST
            env = os.environ.copy()
            env["DOCKER_HOST"] = self.settings.host
            # Ensure TLS is disabled
            env["DOCKER_TLS_VERIFY"] = "0"

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd or self.workspace_path,
                env=env
            )

            stdout, stderr = await process.communicate()

            return subprocess.CompletedProcess(
                args=cmd,
                returncode=process.returncode,
                stdout=stdout.decode('utf-8', errors='ignore') if stdout else "",
                stderr=stderr.decode('utf-8', errors='ignore') if stderr else ""
            )

        except Exception as e:
            logger.error(f"❌ Command execution failed: {' '.join(cmd)}: {e}")
            # Return a failed CompletedProcess
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=1,
                stdout="",
                stderr=str(e)
            )
