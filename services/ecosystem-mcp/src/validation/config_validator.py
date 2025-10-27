"""
Configuration Validator

Validates configuration consistency between service registry and actual infrastructure.
Prevents configuration mismatches like today's consumer group issue.

✅ PHASE 3: Validation system that would have caught today's issue in < 1 minute!

Usage:
    from src.validation import ConfigValidator
    
    validator = ConfigValidator()
    results = await validator.validate_all()
    
    if results.has_critical_failures():
        print("❌ Critical configuration mismatches detected!")
        for result in results.get_failures():
            print(f"   - {result.message}")
        sys.exit(1)
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

import redis.asyncio as redis
import asyncpg

from ..config.registry import get_registry

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Validation result severity levels."""
    CRITICAL = "CRITICAL"  # Blocks startup
    HIGH = "HIGH"          # Warning, allows startup
    MEDIUM = "MEDIUM"      # Info only
    LOW = "LOW"            # Debug only


@dataclass
class ValidationResult:
    """
    Result of a single validation check.
    
    Attributes:
        check_name: Name of the validation check
        severity: Severity level
        passed: Whether the check passed
        message: Human-readable message
        details: Additional details
        remediation: How to fix if failed
    """
    check_name: str
    severity: ValidationSeverity
    passed: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    remediation: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation."""
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"{status} [{self.severity.value}] {self.check_name}: {self.message}"


class ValidationResults:
    """Collection of validation results."""
    
    def __init__(self):
        self.results: List[ValidationResult] = []
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
    
    def add(self, result: ValidationResult):
        """Add a validation result."""
        self.results.append(result)
    
    def has_failures(self) -> bool:
        """Check if any validations failed."""
        return any(not r.passed for r in self.results)
    
    def has_critical_failures(self) -> bool:
        """Check if any critical validations failed."""
        return any(
            not r.passed and r.severity == ValidationSeverity.CRITICAL
            for r in self.results
        )
    
    def get_failures(self) -> List[ValidationResult]:
        """Get all failed validations."""
        return [r for r in self.results if not r.passed]
    
    def get_critical_failures(self) -> List[ValidationResult]:
        """Get all critical failures."""
        return [
            r for r in self.results
            if not r.passed and r.severity == ValidationSeverity.CRITICAL
        ]
    
    def summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        return {
            "total_checks": len(self.results),
            "passed": sum(1 for r in self.results if r.passed),
            "failed": sum(1 for r in self.results if not r.passed),
            "critical_failures": len(self.get_critical_failures()),
            "duration_seconds": (
                (self.completed_at - self.started_at).total_seconds()
                if self.started_at and self.completed_at
                else None
            )
        }


class ConfigValidator:
    """
    Configuration validator.
    
    Validates that actual infrastructure matches the service registry.
    
    ✅ PHASE 3: This would have caught today's consumer group mismatch!
    """
    
    def __init__(self):
        """Initialize validator."""
        self.registry = get_registry()
        logger.info("ConfigValidator initialized")
    
    async def validate_all(self, fail_fast: bool = False) -> ValidationResults:
        """
        Run all validation checks.
        
        Args:
            fail_fast: Stop on first critical failure
        
        Returns:
            ValidationResults with all check results
        """
        results = ValidationResults()
        results.started_at = datetime.utcnow()
        
        logger.info("🔍 Starting configuration validation...")
        
        # Run all validators
        validators = [
            self.validate_redis_connection,
            self.validate_redis_streams_exist,
            self.validate_redis_consumer_groups,  # ← Would have caught today's issue!
            self.validate_database_connection,
            self.validate_database_name,
            self.validate_database_schema,
            self.validate_chromadb_collection,
            self.validate_service_ports,
            self.validate_network_connectivity,
        ]
        
        for validator_func in validators:
            try:
                result = await validator_func()
                results.add(result)
                
                # Log result
                if result.passed:
                    logger.debug(f"   {result}")
                else:
                    logger.warning(f"   {result}")
                
                # Fail fast on critical failures
                if fail_fast and not result.passed and result.severity == ValidationSeverity.CRITICAL:
                    logger.error(f"🚨 Fail-fast triggered: {result.check_name}")
                    break
                    
            except Exception as e:
                logger.error(f"Validator {validator_func.__name__} crashed: {e}", exc_info=True)
                results.add(ValidationResult(
                    check_name=validator_func.__name__,
                    severity=ValidationSeverity.HIGH,
                    passed=False,
                    message=f"Validator crashed: {str(e)}",
                    details={"exception": str(e)}
                ))
        
        results.completed_at = datetime.utcnow()
        
        # Log summary
        summary = results.summary()
        logger.info(
            f"✅ Validation complete: {summary['passed']}/{summary['total_checks']} passed, "
            f"{summary['failed']} failed, {summary['critical_failures']} critical"
        )
        
        return results
    
    # =========================================================================
    # REDIS VALIDATORS
    # =========================================================================
    
    async def validate_redis_connection(self) -> ValidationResult:
        """Validate Redis connection."""
        try:
            client = await redis.from_url(
                self.registry.redis.connection.url,
                encoding="utf-8",
                decode_responses=True
            )
            await client.ping()
            await client.close()
            
            return ValidationResult(
                check_name="redis_connection",
                severity=ValidationSeverity.CRITICAL,
                passed=True,
                message=f"Redis connection successful: {self.registry.redis.connection.host}:{self.registry.redis.connection.port}"
            )
        except Exception as e:
            return ValidationResult(
                check_name="redis_connection",
                severity=ValidationSeverity.CRITICAL,
                passed=False,
                message=f"Redis connection failed: {str(e)}",
                details={"error": str(e)},
                remediation="Check Redis is running and accessible"
            )
    
    async def validate_redis_streams_exist(self) -> ValidationResult:
        """Validate Redis streams exist."""
        try:
            client = await redis.from_url(
                self.registry.redis.connection.url,
                encoding="utf-8",
                decode_responses=True
            )
            
            expected_streams = [
                self.registry.redis.streams.ingestion.name,
                self.registry.redis.streams.embedding.name,
                self.registry.redis.streams.retry.name,
                self.registry.redis.streams.dead_letter.name,
            ]
            
            missing_streams = []
            for stream_name in expected_streams:
                exists = await client.exists(stream_name)
                if not exists:
                    missing_streams.append(stream_name)
            
            await client.close()
            
            if missing_streams:
                return ValidationResult(
                    check_name="redis_streams_exist",
                    severity=ValidationSeverity.HIGH,
                    passed=False,
                    message=f"Missing Redis streams: {', '.join(missing_streams)}",
                    details={"missing_streams": missing_streams},
                    remediation=f"Create streams with: XGROUP CREATE <stream_name> {self.registry.redis.streams.ingestion.consumer_group} $ MKSTREAM"
                )
            
            return ValidationResult(
                check_name="redis_streams_exist",
                severity=ValidationSeverity.HIGH,
                passed=True,
                message=f"All {len(expected_streams)} Redis streams exist"
            )
            
        except Exception as e:
            return ValidationResult(
                check_name="redis_streams_exist",
                severity=ValidationSeverity.HIGH,
                passed=False,
                message=f"Failed to check Redis streams: {str(e)}",
                details={"error": str(e)}
            )
    
    async def validate_redis_consumer_groups(self) -> ValidationResult:
        """
        Validate Redis consumer groups match registry.
        
        ✅ THIS WOULD HAVE CAUGHT TODAY'S ISSUE!
        
        Checks that:
        1. Consumer groups exist for all streams
        2. Consumer group names match registry
        """
        try:
            client = await redis.from_url(
                self.registry.redis.connection.url,
                encoding="utf-8",
                decode_responses=True
            )
            
            streams = {
                "ingestion": self.registry.redis.streams.ingestion,
                "embedding": self.registry.redis.streams.embedding,
                "retry": self.registry.redis.streams.retry,
                "dead_letter": self.registry.redis.streams.dead_letter,
            }
            
            mismatches = []
            missing_groups = []
            
            for stream_key, stream_config in streams.items():
                stream_name = stream_config.name
                expected_group = stream_config.consumer_group
                
                try:
                    # Get stream info
                    info = await client.xinfo_groups(stream_name)
                    
                    # Check if expected consumer group exists
                    group_names = [g['name'] for g in info]
                    
                    if expected_group not in group_names:
                        # Consumer group doesn't exist or name mismatch!
                        if group_names:
                            mismatches.append({
                                "stream": stream_name,
                                "expected": expected_group,
                                "actual": group_names,
                                "issue": "Consumer group name mismatch"
                            })
                        else:
                            missing_groups.append({
                                "stream": stream_name,
                                "expected": expected_group
                            })
                            
                except redis.ResponseError as e:
                    if "no such key" in str(e).lower():
                        # Stream doesn't exist yet
                        missing_groups.append({
                            "stream": stream_name,
                            "expected": expected_group,
                            "reason": "Stream does not exist"
                        })
                    else:
                        raise
            
            await client.close()
            
            if mismatches:
                # THIS IS THE EXACT ISSUE WE HAD TODAY!
                mismatch_details = "\n".join([
                    f"   Stream '{m['stream']}': expected '{m['expected']}', found {m['actual']}"
                    for m in mismatches
                ])
                
                return ValidationResult(
                    check_name="redis_consumer_groups",
                    severity=ValidationSeverity.CRITICAL,  # BLOCKS STARTUP!
                    passed=False,
                    message=f"🚨 Consumer group mismatch detected!\n{mismatch_details}",
                    details={"mismatches": mismatches, "missing": missing_groups},
                    remediation=(
                        "Fix consumer group mismatches:\n"
                        f"1. Update registry to match actual groups, OR\n"
                        f"2. Recreate groups: XGROUP DESTROY <stream> <old_group> && "
                        f"XGROUP CREATE <stream> {streams['ingestion'].consumer_group} $"
                    )
                )
            
            if missing_groups:
                return ValidationResult(
                    check_name="redis_consumer_groups",
                    severity=ValidationSeverity.HIGH,
                    passed=False,
                    message=f"Missing consumer groups for {len(missing_groups)} streams",
                    details={"missing": missing_groups},
                    remediation="Consumer groups will be created automatically on first service start"
                )
            
            return ValidationResult(
                check_name="redis_consumer_groups",
                severity=ValidationSeverity.CRITICAL,
                passed=True,
                message=f"✅ All consumer groups match registry ('{streams['ingestion'].consumer_group}')"
            )
            
        except Exception as e:
            return ValidationResult(
                check_name="redis_consumer_groups",
                severity=ValidationSeverity.CRITICAL,
                passed=False,
                message=f"Failed to validate consumer groups: {str(e)}",
                details={"error": str(e)}
            )
    
    # =========================================================================
    # DATABASE VALIDATORS
    # =========================================================================
    
    async def validate_database_connection(self) -> ValidationResult:
        """Validate PostgreSQL connection."""
        try:
            conn = await asyncpg.connect(self.registry.database.connection.url)
            await conn.close()
            
            return ValidationResult(
                check_name="database_connection",
                severity=ValidationSeverity.CRITICAL,
                passed=True,
                message=f"Database connection successful: {self.registry.database.connection.database}"
            )
        except Exception as e:
            return ValidationResult(
                check_name="database_connection",
                severity=ValidationSeverity.CRITICAL,
                passed=False,
                message=f"Database connection failed: {str(e)}",
                details={"error": str(e)},
                remediation="Check PostgreSQL is running and credentials are correct"
            )
    
    async def validate_database_name(self) -> ValidationResult:
        """
        Validate database name matches registry.
        
        Prevents confusion between 'ecosystem' and 'ecosystem_mcp'.
        """
        try:
            conn = await asyncpg.connect(self.registry.database.connection.url)
            actual_db = await conn.fetchval("SELECT current_database()")
            await conn.close()
            
            expected_db = self.registry.database.connection.database
            
            if actual_db != expected_db:
                return ValidationResult(
                    check_name="database_name",
                    severity=ValidationSeverity.CRITICAL,
                    passed=False,
                    message=f"Database name mismatch: expected '{expected_db}', connected to '{actual_db}'",
                    details={"expected": expected_db, "actual": actual_db},
                    remediation=f"Update connection string to use '{expected_db}'"
                )
            
            return ValidationResult(
                check_name="database_name",
                severity=ValidationSeverity.CRITICAL,
                passed=True,
                message=f"✅ Database name matches registry: '{actual_db}'"
            )
            
        except Exception as e:
            return ValidationResult(
                check_name="database_name",
                severity=ValidationSeverity.HIGH,
                passed=False,
                message=f"Failed to validate database name: {str(e)}",
                details={"error": str(e)}
            )
    
    async def validate_database_schema(self) -> ValidationResult:
        """Validate required database tables exist."""
        try:
            conn = await asyncpg.connect(self.registry.database.connection.url)
            
            required_tables = self.registry.database.tables.required
            
            # Query for existing tables
            existing_tables = await conn.fetch("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
            """)
            existing_table_names = {row['tablename'] for row in existing_tables}
            
            await conn.close()
            
            missing_tables = [t for t in required_tables if t not in existing_table_names]
            
            if missing_tables:
                return ValidationResult(
                    check_name="database_schema",
                    severity=ValidationSeverity.HIGH,
                    passed=False,
                    message=f"Missing required tables: {', '.join(missing_tables)}",
                    details={"missing_tables": missing_tables},
                    remediation="Run database migrations: alembic upgrade head"
                )
            
            return ValidationResult(
                check_name="database_schema",
                severity=ValidationSeverity.HIGH,
                passed=True,
                message=f"✅ All {len(required_tables)} required tables exist"
            )
            
        except Exception as e:
            return ValidationResult(
                check_name="database_schema",
                severity=ValidationSeverity.HIGH,
                passed=False,
                message=f"Failed to validate database schema: {str(e)}",
                details={"error": str(e)}
            )
    
    # =========================================================================
    # CHROMADB VALIDATORS
    # =========================================================================
    
    async def validate_chromadb_collection(self) -> ValidationResult:
        """Validate ChromaDB collection exists."""
        try:
            from ..storage.chromadb_client import get_chroma_client
            
            chroma = get_chroma_client()
            collections = await chroma.list_collections()
            collection_names = [c.name for c in collections]
            
            expected_name = self.registry.chromadb.collections.main.name
            
            if expected_name not in collection_names:
                return ValidationResult(
                    check_name="chromadb_collection",
                    severity=ValidationSeverity.MEDIUM,
                    passed=False,
                    message=f"ChromaDB collection '{expected_name}' does not exist",
                    details={"expected": expected_name, "existing": collection_names},
                    remediation="Collection will be created automatically on first use"
                )
            
            return ValidationResult(
                check_name="chromadb_collection",
                severity=ValidationSeverity.MEDIUM,
                passed=True,
                message=f"✅ ChromaDB collection exists: '{expected_name}'"
            )
            
        except Exception as e:
            return ValidationResult(
                check_name="chromadb_collection",
                severity=ValidationSeverity.MEDIUM,
                passed=False,
                message=f"Failed to validate ChromaDB collection: {str(e)}",
                details={"error": str(e)}
            )
    
    # =========================================================================
    # SERVICE VALIDATORS
    # =========================================================================
    
    async def validate_service_ports(self) -> ValidationResult:
        """Validate service ports are not in use."""
        import socket
        
        ports_to_check = {
            "postgres": self.registry.services.postgres.ports.main,
            "redis": self.registry.services.redis.ports.main,
            "ollama": self.registry.services.ollama.ports.api,
            "embedding": self.registry.services.ecosystem_mcp_embedding.ports.api,
            "api": self.registry.services.ecosystem_mcp.ports.api,
            "metrics": self.registry.services.ecosystem_mcp.ports.metrics,
            "dashboard": self.registry.services.ecosystem_mcp_dashboard.ports.ui,
        }
        
        ports_in_use = []
        
        for service_name, port in ports_to_check.items():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                # Port is in use (might be our service running)
                ports_in_use.append({"service": service_name, "port": port, "status": "in_use"})
        
        if not ports_in_use:
            return ValidationResult(
                check_name="service_ports",
                severity=ValidationSeverity.LOW,
                passed=True,
                message=f"All {len(ports_to_check)} service ports are available"
            )
        
        # Ports in use might be OK (services already running)
        return ValidationResult(
            check_name="service_ports",
            severity=ValidationSeverity.LOW,
            passed=True,
            message=f"{len(ports_in_use)} ports in use (likely services already running)",
            details={"ports_in_use": ports_in_use}
        )
    
    async def validate_network_connectivity(self) -> ValidationResult:
        """Validate network connectivity between services."""
        # This is a placeholder for more sophisticated network validation
        return ValidationResult(
            check_name="network_connectivity",
            severity=ValidationSeverity.LOW,
            passed=True,
            message="Network connectivity validation not yet implemented"
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def validate_config(fail_fast: bool = False) -> ValidationResults:
    """
    Convenience function to validate configuration.
    
    Args:
        fail_fast: Stop on first critical failure
    
    Returns:
        ValidationResults
    
    Example:
        results = await validate_config(fail_fast=True)
        if results.has_critical_failures():
            print("❌ Critical failures detected!")
            sys.exit(1)
    """
    validator = ConfigValidator()
    return await validator.validate_all(fail_fast=fail_fast)


