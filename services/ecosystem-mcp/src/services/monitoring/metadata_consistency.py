"""
Metadata Consistency Monitor

Monitors and reports on metadata consistency between PostgreSQL and ChromaDB.
Helps detect issues before they impact Temporal RAG queries.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, text, func

from ...storage.database import get_database
from ...storage.chromadb_client import get_chroma_client
from ...storage.db_models import DocumentModel

logger = logging.getLogger(__name__)


@dataclass
class MetadataMismatch:
    """Represents a metadata mismatch between PostgreSQL and ChromaDB."""
    document_id: str
    field: str
    postgresql_value: any
    chromadb_value: any
    severity: str  # "low", "medium", "high"


@dataclass
class ConsistencyReport:
    """Report of metadata consistency check."""
    timestamp: datetime
    total_postgresql: int
    total_chromadb: int
    matched: int
    postgresql_only: int
    chromadb_only: int
    metadata_mismatches: List[MetadataMismatch]
    coverage_postgresql: float
    coverage_chromadb: float
    health_status: str  # "healthy", "warning", "critical"
    recommendations: List[str]


class MetadataConsistencyMonitor:
    """
    Monitor metadata consistency between PostgreSQL and ChromaDB.
    
    ✅ Detects missing temporal metadata
    ✅ Identifies service_name mismatches
    ✅ Reports coverage statistics
    ✅ Provides actionable recommendations
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def check_consistency(
        self,
        sample_size: int = 100,
        check_all: bool = False
    ) -> ConsistencyReport:
        """
        Check metadata consistency across systems.
        
        Args:
            sample_size: Number of documents to sample from ChromaDB for detailed checks
            check_all: If True, check all documents (slower but comprehensive)
        
        Returns:
            ConsistencyReport with health status and recommendations
        """
        self.logger.info("🔍 Starting metadata consistency check...")
        
        try:
            db = get_database()
            chroma = get_chroma_client()
            collection = chroma.collection
            
            async with db.session() as session:
                # Get PostgreSQL statistics
                pg_stats = await self._get_postgresql_stats(session)
                
                # Get ChromaDB statistics
                chroma_stats = await self._get_chromadb_stats(collection, sample_size)
                
                # Find matches and mismatches
                matched, mismatches = await self._compare_metadata(
                    session,
                    collection,
                    sample_size if not check_all else None
                )
                
                # Calculate coverage
                coverage_postgresql = pg_stats["with_git_date"] / pg_stats["total"] if pg_stats["total"] > 0 else 0
                coverage_chromadb = chroma_stats["with_git_date"] / chroma_stats["sampled"] if chroma_stats["sampled"] > 0 else 0
                
                # Determine health status
                health_status, recommendations = self._analyze_health(
                    pg_stats,
                    chroma_stats,
                    matched,
                    mismatches,
                    coverage_postgresql,
                    coverage_chromadb
                )
                
                report = ConsistencyReport(
                    timestamp=datetime.utcnow(),
                    total_postgresql=pg_stats["total"],
                    total_chromadb=chroma_stats["total"],
                    matched=matched,
                    postgresql_only=pg_stats["total"] - matched,
                    chromadb_only=chroma_stats["total"] - matched,
                    metadata_mismatches=mismatches,
                    coverage_postgresql=coverage_postgresql,
                    coverage_chromadb=coverage_chromadb,
                    health_status=health_status,
                    recommendations=recommendations
                )
                
                # Log summary
                self.logger.info(f"✅ Consistency check complete: {health_status.upper()}")
                self.logger.info(f"   PostgreSQL: {pg_stats['total']} docs, {coverage_postgresql:.1%} with git_date")
                self.logger.info(f"   ChromaDB: {chroma_stats['total']} docs, {coverage_chromadb:.1%} with git_date")
                self.logger.info(f"   Matched: {matched}, Mismatches: {len(mismatches)}")
                
                return report
                
        except Exception as e:
            self.logger.error(f"❌ Consistency check failed: {e}", exc_info=True)
            raise
    
    async def _get_postgresql_stats(self, session) -> Dict:
        """Get statistics from PostgreSQL."""
        # Total documents
        result = await session.execute(text("SELECT COUNT(*) FROM documents"))
        total = result.scalar()
        
        # Documents with git_date
        result = await session.execute(
            text("SELECT COUNT(*) FROM documents WHERE git_date IS NOT NULL")
        )
        with_git_date = result.scalar()
        
        # Service name distribution
        result = await session.execute(
            text("SELECT service_name, COUNT(*) FROM documents GROUP BY service_name")
        )
        service_distribution = {row[0]: row[1] for row in result}
        
        return {
            "total": total,
            "with_git_date": with_git_date,
            "service_distribution": service_distribution
        }
    
    async def _get_chromadb_stats(self, collection, sample_size: int) -> Dict:
        """Get statistics from ChromaDB."""
        # Total documents
        total = collection.count()
        
        # Sample for detailed analysis
        sample = collection.get(limit=sample_size, include=["metadatas"])
        
        with_git_date = 0
        service_distribution = {}
        
        for meta in sample.get("metadatas", []):
            # Check git_date
            git_date = meta.get("git_date")
            if isinstance(git_date, (int, float)) and git_date > 0:
                with_git_date += 1
            
            # Count service names
            service = meta.get("service_name", "unknown")
            service_distribution[service] = service_distribution.get(service, 0) + 1
        
        return {
            "total": total,
            "sampled": len(sample.get("metadatas", [])),
            "with_git_date": with_git_date,
            "service_distribution": service_distribution
        }
    
    async def _compare_metadata(
        self,
        session,
        collection,
        sample_size: Optional[int]
    ) -> Tuple[int, List[MetadataMismatch]]:
        """
        Compare metadata between PostgreSQL and ChromaDB.
        
        Returns:
            Tuple of (matched_count, list_of_mismatches)
        """
        mismatches = []
        matched = 0
        
        # Get sample of PostgreSQL documents
        if sample_size:
            result = await session.execute(
                text(f"""
                    SELECT id, service_name, git_date, git_commit_sha, git_author
                    FROM documents
                    WHERE git_date IS NOT NULL
                    LIMIT {sample_size}
                """)
            )
        else:
            result = await session.execute(
                text("""
                    SELECT id, service_name, git_date, git_commit_sha, git_author
                    FROM documents
                    WHERE git_date IS NOT NULL
                """)
            )
        
        for row in result:
            doc_id, service_name, git_date, git_sha, git_author = row
            
            # Get from ChromaDB
            chroma_result = collection.get(
                ids=[str(doc_id)],
                include=["metadatas"]
            )
            
            if not chroma_result or not chroma_result.get("ids"):
                # Document not in ChromaDB
                continue
            
            chroma_meta = chroma_result["metadatas"][0]
            
            # Check service_name
            chroma_service = chroma_meta.get("service_name")
            if service_name != chroma_service:
                mismatches.append(MetadataMismatch(
                    document_id=str(doc_id),
                    field="service_name",
                    postgresql_value=service_name,
                    chromadb_value=chroma_service,
                    severity="high"
                ))
            
            # Check git_date (convert PG datetime to timestamp)
            if git_date:
                pg_timestamp = git_date.timestamp()
                chroma_git_date = chroma_meta.get("git_date")
                
                if not isinstance(chroma_git_date, (int, float)):
                    mismatches.append(MetadataMismatch(
                        document_id=str(doc_id),
                        field="git_date",
                        postgresql_value=pg_timestamp,
                        chromadb_value=chroma_git_date,
                        severity="high"
                    ))
                elif abs(pg_timestamp - chroma_git_date) > 1:  # Allow 1 second tolerance
                    mismatches.append(MetadataMismatch(
                        document_id=str(doc_id),
                        field="git_date",
                        postgresql_value=pg_timestamp,
                        chromadb_value=chroma_git_date,
                        severity="medium"
                    ))
            
            # Check git_commit_sha
            chroma_sha = chroma_meta.get("git_commit_sha", "")
            if git_sha and git_sha[:8] != chroma_sha:
                mismatches.append(MetadataMismatch(
                    document_id=str(doc_id),
                    field="git_commit_sha",
                    postgresql_value=git_sha[:8],
                    chromadb_value=chroma_sha,
                    severity="low"
                ))
            
            if not mismatches or all(m.document_id != str(doc_id) for m in mismatches[-3:]):
                matched += 1
        
        return matched, mismatches
    
    def _analyze_health(
        self,
        pg_stats: Dict,
        chroma_stats: Dict,
        matched: int,
        mismatches: List[MetadataMismatch],
        coverage_pg: float,
        coverage_chroma: float
    ) -> Tuple[str, List[str]]:
        """
        Analyze health status and generate recommendations.
        
        Returns:
            Tuple of (health_status, recommendations)
        """
        recommendations = []
        
        # Check coverage
        if coverage_pg < 0.8:
            recommendations.append(
                f"⚠️ PostgreSQL coverage low ({coverage_pg:.1%}). "
                "Consider running enriched ingestion."
            )
        
        if coverage_chroma < 0.8:
            recommendations.append(
                f"⚠️ ChromaDB coverage low ({coverage_chroma:.1%}). "
                "Run metadata enrichment to sync from PostgreSQL."
            )
        
        # Check mismatches
        high_severity = [m for m in mismatches if m.severity == "high"]
        if high_severity:
            recommendations.append(
                f"🚨 {len(high_severity)} high-severity mismatches found. "
                "Run metadata enrichment immediately."
            )
        
        # Check document count mismatch
        if chroma_stats["total"] > pg_stats["total"] * 1.5:
            diff = chroma_stats["total"] - pg_stats["total"]
            recommendations.append(
                f"⚠️ ChromaDB has {diff} more documents than PostgreSQL. "
                "Consider cleanup of orphaned documents."
            )
        
        # Check service_name distribution
        if "unknown" in chroma_stats["service_distribution"]:
            unknown_count = chroma_stats["service_distribution"]["unknown"]
            if unknown_count > chroma_stats["sampled"] * 0.1:
                recommendations.append(
                    f"⚠️ {unknown_count} documents have service_name='unknown'. "
                    "Update metadata to improve query precision."
                )
        
        # Determine health status
        if coverage_chroma < 0.5 or len(high_severity) > 10:
            health_status = "critical"
            recommendations.insert(0, "🚨 CRITICAL: Temporal RAG may not function correctly.")
        elif coverage_chroma < 0.8 or len(high_severity) > 0 or len(mismatches) > 10:
            health_status = "warning"
            recommendations.insert(0, "⚠️ WARNING: Metadata inconsistencies detected.")
        else:
            health_status = "healthy"
            if not recommendations:
                recommendations.append("✅ All systems nominal.")
        
        return health_status, recommendations


# Singleton instance
_monitor_instance: Optional[MetadataConsistencyMonitor] = None


def get_metadata_consistency_monitor() -> MetadataConsistencyMonitor:
    """Get or create the metadata consistency monitor singleton."""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = MetadataConsistencyMonitor()
    return _monitor_instance

