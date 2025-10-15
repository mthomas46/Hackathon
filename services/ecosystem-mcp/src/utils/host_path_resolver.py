"""
Host Path Resolver

Resolves paths from host machine to container-accessible paths,
with automatic git repository root detection.

Handles:
- Host paths outside container
- Docker volume mounts
- Git repository root detection
- Path validation and normalization
"""

import os
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ResolvedPath:
    """
    Represents a resolved path with git repository information.
    
    Attributes:
        original_path: Original path provided by user
        normalized_path: Normalized absolute path
        container_path: Path accessible from container
        git_root: Git repository root directory
        is_git_repo: Whether path is in a git repository
        is_host_mount: Whether path requires host mount
        relative_to_git: Path relative to git root
        target_subdir: Specific subdirectory to target (relative to git root)
        is_subdirectory: Whether targeting a specific subdirectory
    """
    original_path: str
    normalized_path: str
    container_path: str
    git_root: Optional[str]
    is_git_repo: bool
    is_host_mount: bool
    relative_to_git: Optional[str]
    target_subdir: Optional[str] = None
    is_subdirectory: bool = False


class HostPathResolver:
    """
    Resolves host machine paths for container ingestion.
    
    Features:
    - Automatic git repository root detection
    - Path normalization and validation
    - Docker volume mount detection
    - Container path mapping
    """
    
    # Common host mount points (configurable via environment)
    HOST_MOUNTS = {
        "/host": "/",  # Full host root mounted at /host
        "/workspace": os.getenv("HOST_WORKSPACE", "/Users"),  # User workspace
        "/projects": os.getenv("HOST_PROJECTS", "/Users/mykalthomas/Documents/work"),
    }
    
    def __init__(self):
        """Initialize path resolver."""
        self.host_mounts = self._load_mount_config()
        logger.info(f"HostPathResolver initialized with {len(self.host_mounts)} mount points")
    
    def _load_mount_config(self) -> Dict[str, str]:
        """
        Load host mount configuration.
        
        Returns:
            Dictionary mapping container paths to host paths
        """
        # Start with defaults
        mounts = self.HOST_MOUNTS.copy()
        
        # Add custom mounts from environment
        custom_mounts = os.getenv("CUSTOM_HOST_MOUNTS")
        if custom_mounts:
            # Format: "container_path:host_path,container_path:host_path"
            for mount in custom_mounts.split(","):
                if ":" in mount:
                    container_path, host_path = mount.split(":", 1)
                    mounts[container_path.strip()] = host_path.strip()
        
        return mounts
    
    def resolve(self, path: str, preserve_subdir: bool = True) -> ResolvedPath:
        """
        Resolve a path for container ingestion.
        
        Args:
            path: Path to resolve (can be host or container path)
            preserve_subdir: Whether to preserve subdirectory targeting
        
        Returns:
            ResolvedPath with all resolution information
        
        Raises:
            ValueError: If path is invalid or inaccessible
        """
        logger.info(f"Resolving path: {path}")
        
        # Normalize path
        normalized = self._normalize_path(path)
        
        # Detect if this is a host path that needs mounting
        is_host_mount, container_path = self._resolve_container_path(normalized)
        
        # Find git repository root
        # For host paths, we need to check the HOST filesystem (via mounts)
        git_root = self._find_git_root(normalized, is_host_path=is_host_mount)
        
        # Calculate relative path to git root and detect subdirectory targeting
        relative_to_git = None
        target_subdir = None
        is_subdirectory = False
        
        if git_root:
            try:
                rel_path = Path(normalized).relative_to(git_root)
                relative_to_git = str(rel_path)
                
                # If relative path is not ".", user is targeting a subdirectory
                if preserve_subdir and relative_to_git != ".":
                    target_subdir = relative_to_git
                    is_subdirectory = True
                    logger.info(f"Subdirectory targeting detected: {target_subdir}")
                
            except ValueError:
                # Not relative to git root
                pass
        
        resolved = ResolvedPath(
            original_path=path,
            normalized_path=normalized,
            container_path=container_path,
            git_root=git_root,
            is_git_repo=git_root is not None,
            is_host_mount=is_host_mount,
            relative_to_git=relative_to_git,
            target_subdir=target_subdir,
            is_subdirectory=is_subdirectory
        )
        
        logger.info(
            f"Path resolved: is_git={resolved.is_git_repo}, "
            f"is_host_mount={resolved.is_host_mount}, "
            f"is_subdirectory={resolved.is_subdirectory}, "
            f"target_subdir={resolved.target_subdir}, "
            f"container_path={resolved.container_path}"
        )
        
        return resolved
    
    def _normalize_path(self, path: str) -> str:
        """
        Normalize a path to absolute form.
        
        Args:
            path: Path to normalize
        
        Returns:
            Absolute normalized path
        """
        # Expand user home directory
        path = os.path.expanduser(path)
        
        # Expand environment variables
        path = os.path.expandvars(path)
        
        # Convert to absolute path
        path = os.path.abspath(path)
        
        return path
    
    def _resolve_container_path(self, host_path: str) -> Tuple[bool, str]:
        """
        Resolve host path to container-accessible path.
        
        Args:
            host_path: Absolute host path
        
        Returns:
            Tuple of (is_host_mount, container_path)
        """
        # Check if path is already a container path
        if self._is_container_path(host_path):
            return False, host_path
        
        # Check if path matches any known mount point
        for container_mount, host_mount in self.host_mounts.items():
            if host_path.startswith(host_mount):
                # Map to container path
                relative = os.path.relpath(host_path, host_mount)
                container_path = os.path.join(container_mount, relative)
                return True, container_path
        
        # Path not in any mount - needs to be mounted
        # Default to /host prefix
        container_path = os.path.join("/host", host_path.lstrip("/"))
        return True, container_path
    
    def _is_container_path(self, path: str) -> bool:
        """
        Check if path is already a container path.
        
        Args:
            path: Path to check
        
        Returns:
            True if path is in container, False if on host
        """
        # Check if we're running in a container
        if os.path.exists("/.dockerenv"):
            # We're in a container
            # Path is container path if it exists or is under /app
            return path.startswith("/app") or os.path.exists(path)
        
        # Running on host - all paths are host paths
        return False
    
    def _find_git_root(self, path: str, is_host_path: bool = False) -> Optional[str]:
        """
        Find the git repository root for a path.
        
        Args:
            path: Path to search from
            is_host_path: If True, check host filesystem via mounted volumes
        
        Returns:
            Git root directory, or None if not in a git repo
        """
        # For host paths, we need to check if they're accessible
        # Check if we're in a container
        in_container = os.path.exists("/.dockerenv")
        
        if in_container and is_host_path:
            # We're in a container trying to check a host path
            # Try to find if the path is mounted somewhere
            logger.debug(f"Checking host path {path} from within container")
            
            # Check common mount points where host paths might be accessible
            possible_mounts = [
                ("/app", "/Users/mykalthomas/Documents/work/Hackathon"),
                ("/workspace", "/Users/mykalthomas/Documents/work"),
                ("/host", ""),
            ]
            
            for mount_point, host_prefix in possible_mounts:
                if path.startswith(host_prefix if host_prefix else "/"):
                    # Try to map to mounted path
                    if host_prefix:
                        relative = path[len(host_prefix):].lstrip("/")
                        check_path = os.path.join(mount_point, relative) if relative else mount_point
                    else:
                        check_path = os.path.join(mount_point, path.lstrip("/"))
                    
                    logger.debug(f"Checking mounted path: {check_path}")
                    
                    # Try git command on mounted path
                    try:
                        result = subprocess.run(
                            ["git", "-C", check_path, "rev-parse", "--show-toplevel"],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        
                        if result.returncode == 0:
                            # Git found it! Map back to host path
                            container_git_root = result.stdout.strip()
                            logger.debug(f"Found git root in container: {container_git_root}")
                            
                            # Map container path back to host path
                            if container_git_root.startswith(mount_point) and host_prefix:
                                relative_to_mount = container_git_root[len(mount_point):].lstrip("/")
                                host_git_root = os.path.join(host_prefix, relative_to_mount) if relative_to_mount else host_prefix
                                logger.info(f"Mapped git root to host path: {host_git_root}")
                                return host_git_root
                            else:
                                return container_git_root
                    
                    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                        logger.debug(f"Git command failed on {check_path}: {e}")
                        continue
                    
                    # Try manual .git search on mounted path
                    current = Path(check_path)
                    if current.exists():
                        if current.is_file():
                            current = current.parent
                        
                        for parent in [current] + list(current.parents):
                            git_dir = parent / ".git"
                            if git_dir.exists():
                                container_git_root = str(parent)
                                logger.debug(f"Found .git dir in container: {container_git_root}")
                                
                                # Map back to host path
                                if container_git_root.startswith(mount_point) and host_prefix:
                                    relative_to_mount = container_git_root[len(mount_point):].lstrip("/")
                                    host_git_root = os.path.join(host_prefix, relative_to_mount) if relative_to_mount else host_prefix
                                    logger.info(f"Mapped .git root to host path: {host_git_root}")
                                    return host_git_root
                                else:
                                    return container_git_root
            
            logger.warning(f"Could not find git repository for host path {path} in any mounted location")
            return None
        
        # Standard path checking (container path or running on host)
        try:
            # Try using git command
            result = subprocess.run(
                ["git", "-C", path, "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                git_root = result.stdout.strip()
                logger.debug(f"Found git root via git command: {git_root}")
                return git_root
        
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.debug(f"Git command failed: {e}")
        
        # Fallback: Manual search for .git directory
        current = Path(path)
        
        # Handle file paths - start from parent
        if current.is_file():
            current = current.parent
        
        # Walk up directory tree
        for parent in [current] + list(current.parents):
            git_dir = parent / ".git"
            if git_dir.exists():
                git_root = str(parent)
                logger.debug(f"Found git root via manual search: {git_root}")
                return git_root
        
        logger.debug(f"No git repository found for path: {path}")
        return None
    
    def validate_and_prepare(self, path: str) -> ResolvedPath:
        """
        Validate and prepare a path for ingestion.
        
        Args:
            path: Path to validate and prepare
        
        Returns:
            ResolvedPath ready for ingestion
        
        Raises:
            ValueError: If path is invalid or not a git repository
        """
        resolved = self.resolve(path)
        
        # Validate git repository
        if not resolved.is_git_repo:
            raise ValueError(
                f"Path is not in a git repository: {path}\n"
                f"Ingestion requires a git repository for version tracking."
            )
        
        # Validate accessibility
        if resolved.is_host_mount:
            # Check if mount point exists in container
            mount_prefix = resolved.container_path.split("/")[1]
            mount_path = f"/{mount_prefix}"
            
            if not os.path.exists(mount_path):
                raise ValueError(
                    f"Host path requires mount at {mount_path} which is not available.\n"
                    f"Please ensure the host directory is mounted in docker-compose.yml:\n"
                    f"  volumes:\n"
                    f"    - {resolved.git_root}:{mount_path}:ro"
                )
        
        logger.info(f"Path validated and prepared: {resolved.container_path}")
        return resolved
    
    def suggest_mount_config(self, host_path: str) -> str:
        """
        Suggest docker-compose mount configuration for a host path.
        
        Args:
            host_path: Host path to mount
        
        Returns:
            Suggested docker-compose volume configuration
        """
        resolved = self.resolve(host_path)
        
        if not resolved.is_host_mount:
            return "# Path is already accessible in container, no mount needed"
        
        # Suggest mounting the git root
        git_root = resolved.git_root or host_path
        container_mount = resolved.container_path.rsplit("/", 1)[0]
        
        config = f"""
# Add to docker-compose.yml under ecosystem-mcp-service volumes:
volumes:
  - {git_root}:{container_mount}:ro  # Read-only mount

# Then restart the service:
# docker-compose -f docker-compose-mcp-ecosystem.yml restart ecosystem-mcp-service
"""
        return config.strip()


class HostPathValidator:
    """
    Validates host paths for ingestion requirements.
    
    Checks:
    - Git repository presence
    - Directory accessibility
    - File permissions
    - Path security
    """
    
    @staticmethod
    def validate_git_repo(path: str) -> Tuple[bool, str]:
        """
        Validate that path is in a git repository.
        
        Args:
            path: Path to validate
        
        Returns:
            Tuple of (is_valid, message)
        """
        resolver = HostPathResolver()
        resolved = resolver.resolve(path)
        
        if not resolved.is_git_repo:
            return False, f"Path is not in a git repository: {path}"
        
        return True, f"Valid git repository at: {resolved.git_root}"
    
    @staticmethod
    def validate_accessibility(path: str) -> Tuple[bool, str]:
        """
        Validate that path is accessible.
        
        Args:
            path: Path to validate
        
        Returns:
            Tuple of (is_valid, message)
        """
        if not os.path.exists(path):
            return False, f"Path does not exist: {path}"
        
        if not os.access(path, os.R_OK):
            return False, f"Path is not readable: {path}"
        
        return True, "Path is accessible"
    
    @staticmethod
    def validate_security(path: str) -> Tuple[bool, str]:
        """
        Validate path security (no sensitive directories).
        
        Args:
            path: Path to validate
        
        Returns:
            Tuple of (is_valid, message)
        """
        # Forbidden paths
        forbidden = [
            "/etc", "/sys", "/proc", "/dev",
            "/root/.ssh", "/home/*/.ssh"
        ]
        
        normalized = os.path.abspath(path)
        
        for forbidden_path in forbidden:
            if normalized.startswith(forbidden_path.rstrip("*")):
                return False, f"Access to sensitive directory denied: {forbidden_path}"
        
        return True, "Path is secure"


# Convenience functions
def resolve_host_path(path: str) -> ResolvedPath:
    """
    Resolve a host path for container ingestion.
    
    Args:
        path: Path to resolve
    
    Returns:
        ResolvedPath with resolution information
    """
    resolver = HostPathResolver()
    return resolver.resolve(path)


def validate_ingestion_path(path: str) -> Tuple[bool, str, Optional[ResolvedPath]]:
    """
    Validate a path for ingestion.
    
    Args:
        path: Path to validate
    
    Returns:
        Tuple of (is_valid, message, resolved_path)
    """
    try:
        resolver = HostPathResolver()
        resolved = resolver.validate_and_prepare(path)
        return True, "Path is valid for ingestion", resolved
    
    except ValueError as e:
        return False, str(e), None
    except Exception as e:
        logger.error(f"Error validating path: {e}", exc_info=True)
        return False, f"Validation error: {str(e)}", None

