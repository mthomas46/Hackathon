"""
Discovery Engine

Orchestrates repository scanning, classification, and planning.
"""

import logging
from pathlib import Path
from typing import Dict, Any

from .repository_scanner import RepositoryScanner, RepositoryInventory, get_repository_scanner
from .file_classifier import FileClassifier, get_file_classifier
from .processing_planner import ProcessingPlanner, ProcessingPlan, get_processing_planner

logger = logging.getLogger(__name__)


class DiscoveryEngine:
    """
    Discovery Engine - orchestrates repository analysis.
    
    Usage:
        engine = DiscoveryEngine()
        plan = await engine.discover(repo_path)
    """
    
    def __init__(self):
        self.scanner = get_repository_scanner()
        self.classifier = get_file_classifier()
        self.planner = get_processing_planner()
    
    async def discover(self, repo_path: str) -> ProcessingPlan:
        """
        Discover repository and create processing plan.
        
        Args:
            repo_path: Path to repository
        
        Returns:
            Processing plan
        """
        logger.info(f"🔍 Starting discovery for: {repo_path}")
        
        # Step 1: Scan repository
        inventory = await self.scanner.scan(Path(repo_path))
        
        # Step 2: Classify files
        classified_files = await self.classifier.classify(inventory.files)
        
        # Step 3: Create processing plan
        plan = await self.planner.create_plan(inventory, classified_files, repo_path)
        
        logger.info(f"✅ Discovery complete!")
        
        return plan
    
    def get_plan_summary(self, plan: ProcessingPlan) -> Dict[str, Any]:
        """Get human-readable plan summary."""
        return {
            "repo_path": plan.repo_path,
            "total_files": plan.total_files,
            "total_size_mb": round(plan.total_size_mb, 2),
            "sub_jobs": len(plan.sub_jobs),
            "estimated_time_minutes": round(plan.estimated_total_time_minutes, 1),
            "max_parallelization": plan.max_parallelization,
            "sub_job_details": [
                {
                    "id": sj.sub_job_id,
                    "name": sj.sub_job_name,
                    "files": len(sj.files),
                    "priority": sj.priority,
                    "estimated_minutes": round(sj.estimated_time_minutes, 1)
                }
                for sj in plan.sub_jobs
            ]
        }


# Singleton instance
_discovery_engine_instance = None

def get_discovery_engine() -> DiscoveryEngine:
    """Get singleton discovery engine instance."""
    global _discovery_engine_instance
    if _discovery_engine_instance is None:
        _discovery_engine_instance = DiscoveryEngine()
    return _discovery_engine_instance

