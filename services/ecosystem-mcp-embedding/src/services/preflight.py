"""
Preflight validation and health checks.

Validates service dependencies and configuration before startup.
"""

import logging
import asyncio
from typing import Dict, Any, List
import redis.asyncio as redis

from ..config.settings import settings

logger = logging.getLogger(__name__)


class PreflightCheck:
    """Preflight validation checks."""
    
    def __init__(self):
        """Initialize preflight checker."""
        self.checks_passed = []
        self.checks_failed = []
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """
        Run all preflight checks.
        
        Returns:
            Dict with check results and status
        """
        logger.info("🔍 Running preflight checks...")
        
        checks = [
            ("Redis Connection", self.check_redis),
            ("Model Configuration", self.check_model_config),
            ("Environment Variables", self.check_environment),
            ("Disk Space", self.check_disk_space),
        ]
        
        results = {}
        all_passed = True
        
        for check_name, check_func in checks:
            try:
                passed, message = await check_func()
                results[check_name] = {
                    "passed": passed,
                    "message": message
                }
                
                if passed:
                    logger.info(f"✅ {check_name}: {message}")
                    self.checks_passed.append(check_name)
                else:
                    logger.warning(f"⚠️  {check_name}: {message}")
                    self.checks_failed.append(check_name)
                    all_passed = False
                    
            except Exception as e:
                logger.error(f"❌ {check_name}: {e}")
                results[check_name] = {
                    "passed": False,
                    "message": str(e)
                }
                self.checks_failed.append(check_name)
                all_passed = False
        
        results["summary"] = {
            "all_passed": all_passed,
            "passed_count": len(self.checks_passed),
            "failed_count": len(self.checks_failed),
            "passed_checks": self.checks_passed,
            "failed_checks": self.checks_failed
        }
        
        if all_passed:
            logger.info("✅ All preflight checks passed")
        else:
            logger.warning(f"⚠️  {len(self.checks_failed)} preflight check(s) failed")
        
        return results
    
    async def check_redis(self) -> tuple[bool, str]:
        """Check Redis connectivity."""
        try:
            if not settings.cache_enabled:
                return True, "Redis caching disabled (service will work without cache)"
            
            client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password,
                socket_connect_timeout=5
            )
            
            # Test connection
            await client.ping()
            await client.close()
            
            return True, f"Redis connection successful ({settings.redis_host}:{settings.redis_port})"
            
        except Exception as e:
            return False, f"Redis connection failed: {e}"
    
    async def check_model_config(self) -> tuple[bool, str]:
        """Check model configuration."""
        try:
            model_name = settings.model_name
            
            # Validate model name format
            if not model_name or "/" not in model_name:
                return False, f"Invalid model name format: {model_name}"
            
            # Check model cache directory
            import os
            cache_dir = settings.model_cache_dir
            
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir, exist_ok=True)
                logger.info(f"Created model cache directory: {cache_dir}")
            
            if not os.access(cache_dir, os.W_OK):
                return False, f"Model cache directory not writable: {cache_dir}"
            
            return True, f"Model configuration valid: {model_name}"
            
        except Exception as e:
            return False, f"Model configuration check failed: {e}"
    
    async def check_environment(self) -> tuple[bool, str]:
        """Check environment variables."""
        try:
            issues = []
            
            # Check critical settings
            if not settings.model_name:
                issues.append("MODEL_NAME not set")
            
            if settings.cache_enabled and not settings.redis_host:
                issues.append("REDIS_HOST not set but cache enabled")
            
            if settings.max_text_length <= 0:
                issues.append("MAX_TEXT_LENGTH invalid")
            
            if issues:
                return False, f"Environment issues: {', '.join(issues)}"
            
            return True, "Environment variables valid"
            
        except Exception as e:
            return False, f"Environment check failed: {e}"
    
    async def check_disk_space(self) -> tuple[bool, str]:
        """Check available disk space for model cache."""
        try:
            import shutil
            
            cache_dir = settings.model_cache_dir
            stat = shutil.disk_usage(cache_dir)
            
            # Convert to GB
            free_gb = stat.free / (1024 ** 3)
            
            # Need at least 5GB for model cache
            if free_gb < 5:
                return False, f"Low disk space: {free_gb:.1f}GB available (need 5GB+)"
            
            return True, f"Disk space sufficient: {free_gb:.1f}GB available"
            
        except Exception as e:
            return False, f"Disk space check failed: {e}"


class GracefulRecovery:
    """Graceful recovery and fallback mechanisms."""
    
    @staticmethod
    async def retry_with_backoff(
        func,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 10.0
    ):
        """
        Retry a function with exponential backoff.
        
        Args:
            func: Async function to retry
            max_retries: Maximum number of retries
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
        
        Returns:
            Function result
        
        Raises:
            Last exception if all retries fail
        """
        delay = initial_delay
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                last_exception = e
                
                if attempt < max_retries - 1:
                    logger.warning(
                        f"⚠️  Attempt {attempt + 1}/{max_retries} failed: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, max_delay)
                else:
                    logger.error(f"❌ All {max_retries} attempts failed")
        
        raise last_exception
    
    @staticmethod
    def handle_redis_failure(func):
        """
        Decorator to handle Redis failures gracefully.
        
        Returns None on failure instead of raising exception.
        """
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"⚠️  Redis operation failed (continuing without cache): {e}")
                return None
        
        return wrapper
    
    @staticmethod
    async def safe_shutdown(services: List[Any]):
        """
        Safely shutdown multiple services.
        
        Args:
            services: List of services with close() methods
        """
        logger.info("🛑 Initiating graceful shutdown...")
        
        for service in services:
            try:
                if hasattr(service, 'close'):
                    await service.close()
                    logger.info(f"✅ Closed {service.__class__.__name__}")
            except Exception as e:
                logger.error(f"❌ Error closing {service.__class__.__name__}: {e}")
        
        logger.info("✅ Graceful shutdown complete")


# Global preflight instance
_preflight_checker: PreflightCheck | None = None


def get_preflight_checker() -> PreflightCheck:
    """Get global preflight checker instance."""
    global _preflight_checker
    if _preflight_checker is None:
        _preflight_checker = PreflightCheck()
    return _preflight_checker

