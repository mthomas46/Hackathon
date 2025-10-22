"""
Coverage Analyzer Service

Analyzes documentation coverage:
- Calculate % of files/APIs/classes documented
- Track coverage by service/module
- Track coverage trends over time
- Identify undocumented areas
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID
from pathlib import Path
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ...storage.db_models import DocumentModel, GitCommitModel
from ...storage.repositories import DocumentRepository
from ...storage import get_database

logger = logging.getLogger(__name__)


class CoverageAnalyzer:
    """
    Analyze documentation coverage.
    
    Features:
    - File coverage analysis
    - API/class coverage tracking
    - Service-level coverage
    - Module-level coverage
    - Coverage trends
    """
    
    def __init__(self):
        """Initialize coverage analyzer."""
        self.logger = logging.getLogger(__name__)
    
    async def analyze_coverage(
        self,
        service_name: Optional[str] = None,
        repo_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze documentation coverage.
        
        Args:
            service_name: Optional service filter
            repo_path: Optional repository path
        
        Returns:
            Coverage analysis results
        """
        try:
            self.logger.info(f"📊 Analyzing documentation coverage (service={service_name})")
            
            async with get_database().session() as session:
                doc_repo = DocumentRepository(session)
                
                # Get all documents
                if service_name:
                    documents = await doc_repo.get_by_service(service_name, limit=10000)
                else:
                    documents = await doc_repo.get_all(limit=10000)
                
                self.logger.info(f"   📄 Analyzing {len(documents)} documents")
                
                # Analyze file coverage
                file_coverage = await self._analyze_file_coverage(documents)
                
                # Analyze service coverage
                service_coverage = await self._analyze_service_coverage(documents)
                
                # Analyze module coverage
                module_coverage = await self._analyze_module_coverage(documents)
                
                # Calculate overall coverage
                overall_coverage = self._calculate_overall_coverage(
                    file_coverage,
                    service_coverage,
                    module_coverage
                )
                
                return {
                    "overall_coverage": overall_coverage,
                    "file_coverage": file_coverage,
                    "service_coverage": service_coverage,
                    "module_coverage": module_coverage,
                    "recommendations": self._generate_coverage_recommendations(overall_coverage),
                    "metadata": {
                        "service_name": service_name,
                        "total_documents": len(documents),
                        "analyzed_at": datetime.utcnow().isoformat()
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Failed to analyze coverage: {e}", exc_info=True)
            raise
    
    async def _analyze_file_coverage(
        self,
        documents: List[DocumentModel]
    ) -> Dict[str, Any]:
        """Analyze coverage at the file level."""
        # Count unique files
        unique_files = set()
        file_types = defaultdict(int)
        
        for doc in documents:
            file_path = Path(doc.file_path)
            unique_files.add(str(file_path))
            
            # Track file types
            suffix = file_path.suffix or "no_extension"
            file_types[suffix] += 1
        
        return {
            "total_files_documented": len(unique_files),
            "by_file_type": dict(file_types),
            "top_file_types": sorted(
                file_types.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
    
    async def _analyze_service_coverage(
        self,
        documents: List[DocumentModel]
    ) -> Dict[str, Any]:
        """Analyze coverage by service."""
        services = defaultdict(int)
        
        for doc in documents:
            if doc.service_name:
                services[doc.service_name] += 1
            else:
                services["unknown"] += 1
        
        total_docs = len(documents)
        
        # Calculate percentages
        service_stats = []
        for service, count in services.items():
            service_stats.append({
                "service_name": service,
                "document_count": count,
                "percentage": (count / total_docs * 100) if total_docs > 0 else 0
            })
        
        # Sort by document count
        service_stats.sort(key=lambda x: x["document_count"], reverse=True)
        
        return {
            "total_services": len(services),
            "by_service": service_stats,
            "top_services": service_stats[:10]
        }
    
    async def _analyze_module_coverage(
        self,
        documents: List[DocumentModel]
    ) -> Dict[str, Any]:
        """Analyze coverage by module/directory."""
        modules = defaultdict(int)
        
        for doc in documents:
            # Extract module (top-level directory)
            file_path = Path(doc.file_path)
            if len(file_path.parts) > 0:
                module = file_path.parts[0]
                modules[module] += 1
            else:
                modules["root"] += 1
        
        total_docs = len(documents)
        
        # Calculate percentages
        module_stats = []
        for module, count in modules.items():
            module_stats.append({
                "module_name": module,
                "document_count": count,
                "percentage": (count / total_docs * 100) if total_docs > 0 else 0
            })
        
        # Sort by document count
        module_stats.sort(key=lambda x: x["document_count"], reverse=True)
        
        return {
            "total_modules": len(modules),
            "by_module": module_stats,
            "top_modules": module_stats[:10]
        }
    
    def _calculate_overall_coverage(
        self,
        file_coverage: Dict[str, Any],
        service_coverage: Dict[str, Any],
        module_coverage: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate overall coverage metrics."""
        total_files = file_coverage["total_files_documented"]
        total_services = service_coverage["total_services"]
        total_modules = module_coverage["total_modules"]
        
        # Estimate coverage percentage (simplified)
        # In production, you'd compare against actual codebase size
        coverage_score = min(100, (total_files / 100) * 80 + 20)  # Simplified scoring
        
        return {
            "coverage_score": coverage_score,
            "coverage_level": self._get_coverage_level(coverage_score),
            "total_files_documented": total_files,
            "total_services": total_services,
            "total_modules": total_modules
        }
    
    def _get_coverage_level(self, score: float) -> str:
        """Get coverage level based on score."""
        if score >= 90:
            return "EXCELLENT"
        elif score >= 75:
            return "GOOD"
        elif score >= 50:
            return "FAIR"
        elif score >= 25:
            return "POOR"
        else:
            return "CRITICAL"
    
    def _generate_coverage_recommendations(
        self,
        overall_coverage: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on coverage analysis."""
        recommendations = []
        
        score = overall_coverage["coverage_score"]
        level = overall_coverage["coverage_level"]
        
        if level == "EXCELLENT":
            recommendations.append("✅ Excellent documentation coverage!")
            recommendations.append("Continue maintaining high documentation standards")
        elif level == "GOOD":
            recommendations.append("✅ Good documentation coverage")
            recommendations.append("Consider documenting remaining files for complete coverage")
        elif level == "FAIR":
            recommendations.append("⚠️ Fair documentation coverage")
            recommendations.append("Focus on documenting core APIs and frequently used modules")
        elif level == "POOR":
            recommendations.append("❗ Poor documentation coverage")
            recommendations.append("Prioritize documenting critical services and APIs")
        else:
            recommendations.append("🚨 Critical: Very low documentation coverage")
            recommendations.append("Immediate action needed to improve documentation")
        
        return recommendations
    
    async def track_coverage_trend(
        self,
        service_name: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Track coverage trends over time.
        
        Args:
            service_name: Service to track
            days: Number of days to look back
        
        Returns:
            Coverage trend data
        """
        try:
            self.logger.info(f"📈 Tracking coverage trend for {service_name} ({days} days)")
            
            # This is a simplified version
            # In production, you'd store historical coverage data
            
            current_coverage = await self.analyze_coverage(service_name=service_name)
            
            return {
                "service_name": service_name,
                "period_days": days,
                "current_coverage": current_coverage["overall_coverage"],
                "trend": "stable",  # Would calculate from historical data
                "note": "Historical tracking not yet implemented"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to track coverage trend: {e}", exc_info=True)
            raise
    
    async def identify_gaps(
        self,
        service_name: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Identify documentation gaps.
        
        Args:
            service_name: Optional service filter
            limit: Maximum gaps to return
        
        Returns:
            List of undocumented areas
        """
        try:
            self.logger.info(f"🔍 Identifying documentation gaps (service={service_name})")
            
            # This is a placeholder - in production, you'd:
            # 1. Scan the actual codebase
            # 2. Compare with documented files
            # 3. Identify undocumented APIs, classes, functions
            
            return {
                "gaps": [],
                "total_gaps": 0,
                "message": "Gap identification requires codebase scanning (not yet implemented)",
                "recommendations": [
                    "Implement codebase scanner to identify undocumented code",
                    "Track public APIs and compare with documentation",
                    "Monitor newly added files for documentation"
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to identify gaps: {e}", exc_info=True)
            raise

