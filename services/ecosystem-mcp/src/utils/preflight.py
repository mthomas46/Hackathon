"""
Preflight checks for service startup.

Validates all dependencies and configuration before starting the service.
"""

import logging
import sys
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

import psycopg
import redis
from chromadb import Client as ChromaClient
from chromadb.config import Settings as ChromaSettings

from ..config import settings

logger = logging.getLogger(__name__)


class CheckCategory(Enum):
    """Categorizes checks by criticality."""
    CRITICAL = "critical"    # Must pass for service to start
    HIGH = "high"            # Warn but allow start in lenient mode
    OPTIONAL = "optional"    # Info only, never blocks startup


@dataclass
class CheckResult:
    """Result of a preflight check."""
    name: str
    passed: bool
    message: str
    category: CheckCategory = field(default=CheckCategory.CRITICAL)
    details: Optional[Dict[str, Any]] = None


class PreflightChecker:
    """
    Preflight checker for service startup.
    
    Validates:
    - Configuration
    - Environment variables
    - Database connectivity
    - Redis connectivity
    - ChromaDB initialization
    - File system access
    - Git repository
    """
    
    def __init__(self):
        """Initialize preflight checker."""
        self.results: List[CheckResult] = []
        logger.info("Preflight checker initialized")
    
    async def run_all_checks(self, fail_fast: bool = False) -> bool:
        """
        Run all preflight checks.
        
        Args:
            fail_fast: Stop on first failure
        
        Returns:
            True if all checks passed, False otherwise
        """
        logger.info("=" * 80)
        logger.info("RUNNING PREFLIGHT CHECKS")
        logger.info("=" * 80)
        
        checks = [
            self.check_config,
            self.check_environment,
            self.check_postgresql,
            self.check_redis,
            self.check_chromadb,
            self.check_filesystem,
            self.check_git_repo,
        ]
        
        for check in checks:
            try:
                result = await check()
                self.results.append(result)
                
                if result.passed:
                    logger.info(f"✅ {result.name}: {result.message}")
                else:
                    logger.error(f"❌ {result.name}: {result.message}")
                    if fail_fast:
                        logger.error("Fail-fast enabled, stopping checks")
                        break
            except Exception as e:
                result = CheckResult(
                    name=check.__name__,
                    passed=False,
                    message=f"Check failed with exception: {e}",
                    details={"exception": str(e)}
                )
                self.results.append(result)
                logger.error(f"❌ {check.__name__}: {result.message}")
                if fail_fast:
                    break
        
        # Print summary
        logger.info("=" * 80)
        self._print_summary()
        logger.info("=" * 80)
        
        all_passed = all(r.passed for r in self.results)
        
        if all_passed:
            logger.info("✅ ALL PREFLIGHT CHECKS PASSED")
            return True
        else:
            logger.error("❌ SOME PREFLIGHT CHECKS FAILED")
            return False
    
    async def check_config(self) -> CheckResult:
        """Check configuration is valid."""
        logger.info("Checking configuration...")
        
        try:
            # Check required settings
            required = [
                ("database_url", str(settings.database_url)),
                ("redis_url", str(settings.redis_url)),
            ]
            
            missing = []
            for name, value in required:
                if not value:
                    missing.append(name)
            
            if missing:
                return CheckResult(
                    name="Configuration",
                    passed=False,
                    message=f"Missing required settings: {', '.join(missing)}",
                    details={"missing": missing}
                )
            
            return CheckResult(
                name="Configuration",
                passed=True,
                message="All required settings present",
                details={
                    "database_url": str(settings.database_url),
                    "redis_url": str(settings.redis_url),
                    "model_strategy": settings.model_strategy
                }
            )
        except Exception as e:
            return CheckResult(
                name="Configuration",
                passed=False,
                message=f"Configuration error: {e}",
                details={"exception": str(e)}
            )
    
    async def check_environment(self) -> CheckResult:
        """Check environment variables."""
        logger.info("Checking environment variables...")
        
        try:
            env_vars = {
                "DATABASE_URL": str(settings.database_url),
                "REDIS_URL": str(settings.redis_url),
                "OLLAMA_BASE_URL": settings.ollama_base_url,
            }
            
            return CheckResult(
                name="Environment",
                passed=True,
                message="Environment variables validated",
                details=env_vars
            )
        except Exception as e:
            return CheckResult(
                name="Environment",
                passed=False,
                message=f"Environment error: {e}"
            )
    
    async def check_postgresql(self) -> CheckResult:
        """Check PostgreSQL connectivity."""
        logger.info("Checking PostgreSQL connection...")
        
        try:
            # Try to connect with timeout
            conn = await asyncio.wait_for(
                psycopg.AsyncConnection.connect(
                    str(settings.database_url),
                    autocommit=True
                ),
                timeout=5.0
            )
            
            # Execute simple query
            async with conn.cursor() as cur:
                await cur.execute("SELECT version()")
                version = await cur.fetchone()
            
            await conn.close()
            
            return CheckResult(
                name="PostgreSQL",
                passed=True,
                message="Connection successful",
                details={
                    "version": version[0] if version else "unknown",
                    "database_url": str(settings.database_url)
                }
            )
        except asyncio.TimeoutError:
            return CheckResult(
                name="PostgreSQL",
                passed=False,
                message="Connection timeout (5s)",
                details={"url": str(settings.database_url).split('@')[1] if '@' in str(settings.database_url) else "unknown"}
            )
        except Exception as e:
            return CheckResult(
                name="PostgreSQL",
                passed=False,
                message=f"Connection failed: {e}",
                details={"exception": str(e)}
            )
    
    async def check_redis(self) -> CheckResult:
        """Check Redis connectivity."""
        logger.info("Checking Redis connection...")
        
        try:
            # Parse Redis URL
            from urllib.parse import urlparse
            parsed = urlparse(settings.redis_url)
            host = parsed.hostname or "localhost"
            port = parsed.port or 6379
            
            # Try to connect with timeout
            client = redis.Redis(
                host=host,
                port=port,
                socket_connect_timeout=5,
                socket_timeout=5,
                decode_responses=True
            )
            
            # Test ping
            response = client.ping()
            
            # Get info
            info = client.info("server")
            version = info.get("redis_version", "unknown")
            
            client.close()
            
            return CheckResult(
                name="Redis",
                passed=True,
                message=f"Connection successful (v{version})",
                details={
                    "redis_url": str(settings.redis_url),
                    "version": version
                }
            )
        except redis.ConnectionError as e:
            return CheckResult(
                name="Redis",
                passed=False,
                message=f"Connection failed: {e}",
                details={
                    "redis_url": str(settings.redis_url)
                }
            )
        except Exception as e:
            return CheckResult(
                name="Redis",
                passed=False,
                message=f"Error: {e}",
                details={"exception": str(e)}
            )
    
    async def check_chromadb(self) -> CheckResult:
        """Check ChromaDB initialization."""
        logger.info("Checking ChromaDB...")
        
        try:
            import chromadb
            
            # Ensure path exists
            settings.chroma_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize ChromaDB with persistent client
            client = chromadb.PersistentClient(
                path=str(settings.chroma_path),
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Try to list collections (should work even if empty)
            collections = client.list_collections()
            
            return CheckResult(
                name="ChromaDB",
                passed=True,
                message=f"Initialized successfully ({len(collections)} collections)",
                details={
                    "path": str(settings.chroma_path),
                    "collections": len(collections)
                }
            )
        except Exception as e:
            return CheckResult(
                name="ChromaDB",
                passed=False,
                message=f"Initialization failed: {e}",
                details={"exception": str(e)}
            )
    
    async def check_filesystem(self) -> CheckResult:
        """Check file system access."""
        logger.info("Checking file system access...")
        
        try:
            # Check ChromaDB path
            chroma_path = Path(settings.chroma_path)
            if not chroma_path.exists():
                chroma_path.mkdir(parents=True, exist_ok=True)
            
            # Check write access
            test_file = chroma_path / ".write_test"
            test_file.write_text("test")
            test_file.unlink()
            
            return CheckResult(
                name="Filesystem",
                passed=True,
                message="Read/write access verified",
                details={
                    "chroma_path": str(chroma_path),
                    "writable": True
                }
            )
        except PermissionError as e:
            return CheckResult(
                name="Filesystem",
                passed=False,
                message=f"Permission denied: {e}",
                details={"chroma_path": str(settings.chroma_path)}
            )
        except Exception as e:
            return CheckResult(
                name="Filesystem",
                passed=False,
                message=f"Filesystem error: {e}",
                details={"exception": str(e)}
            )
    
    async def check_git_repo(self) -> CheckResult:
        """Check git repository access."""
        logger.info("Checking git repository...")
        
        try:
            import git
        except ImportError:
            return CheckResult(
                name="Git Repository",
                passed=False,
                message="GitPython not installed (pip install gitpython)",
                details={"error": "ImportError"}
            )
        
        try:
            repo_path = Path(settings.git_repo_path)
            
            if not repo_path.exists():
                return CheckResult(
                    name="Git Repository",
                    passed=False,
                    message=f"Repository path does not exist: {repo_path}",
                    details={"path": str(repo_path)}
                )
            
            # Try to open repository
            repo = git.Repo(repo_path)
            
            # Get basic info
            branch = repo.active_branch.name
            commit_count = sum(1 for _ in repo.iter_commits(max_count=1000))
            
            return CheckResult(
                name="Git Repository",
                passed=True,
                message=f"Repository accessible (branch: {branch})",
                details={
                    "path": str(repo_path),
                    "branch": branch,
                    "commits": commit_count
                }
            )
        except git.InvalidGitRepositoryError:
            return CheckResult(
                name="Git Repository",
                passed=False,
                message=f"Invalid git repository: {settings.git_repo_path}",
                details={"path": str(settings.git_repo_path)}
            )
        except Exception as e:
            return CheckResult(
                name="Git Repository",
                passed=False,
                message=f"Repository error: {e}",
                details={"exception": str(e)}
            )
    
    def _print_summary(self):
        """Print summary of all checks."""
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed
        
        logger.info(f"SUMMARY: {passed} passed, {failed} failed")
        
        if failed > 0:
            logger.info("\nFailed checks:")
            for result in self.results:
                if not result.passed:
                    logger.info(f"  - {result.name}: {result.message}")


async def run_preflight_checks(fail_fast: bool = True, mode: str = "strict") -> bool:
    """
    Run preflight checks with strict or lenient modes and graceful degradation.
    
    Args:
        fail_fast: Stop on first CRITICAL failure
        mode: "strict" (CRITICAL must pass) or "lenient" (warnings only, continue anyway)
    
    Returns:
        True if CRITICAL checks passed (or if in lenient mode)
    
    Raises:
        RuntimeError: If CRITICAL checks fail in strict mode
    """
    import os
    
    # Allow override via environment variable
    mode = os.getenv("PREFLIGHT_MODE", mode).lower()
    
    checker = PreflightChecker()
    passed = await checker.run_all_checks(fail_fast=fail_fast)
    
    # Get critical failures
    critical_failed = [r for r in checker.results if r.category == CheckCategory.CRITICAL and not r.passed]
    
    if critical_failed:
        if mode == "lenient":
            logger.warning("\n⚠️  CRITICAL PREFLIGHT CHECKS FAILED")
            logger.warning("Running in LENIENT mode - continuing anyway")
            logger.warning("Service WILL NOT FUNCTION CORRECTLY!")
            logger.warning(f"Failed: {', '.join(r.name for r in critical_failed)}\n")
            return True  # Continue despite critical failures
        else:
            logger.error("\n🔴 CRITICAL PREFLIGHT CHECKS FAILED - SERVICE CANNOT START")
            logger.error(f"Failed checks: {', '.join(r.name for r in critical_failed)}")
            logger.error("Please fix the critical issues above and try again.")
            logger.error("(Set PREFLIGHT_MODE=lenient to bypass - NOT RECOMMENDED)\n")
            raise RuntimeError(f"Critical preflight checks failed: {', '.join(r.name for r in critical_failed)}")
    
    # Warn about non-critical failures
    high_failed = [r for r in checker.results if r.category == CheckCategory.HIGH and not r.passed]
    if high_failed:
        logger.warning(f"\n⚠️  {len(high_failed)} HIGH priority checks failed - service may be degraded")
        logger.warning(f"Failed: {', '.join(r.name for r in high_failed)}")
    
    logger.info("\n✅ All CRITICAL preflight checks passed - service can start")
    return True

