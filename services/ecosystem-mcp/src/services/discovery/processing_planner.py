"""
Processing Planner

Creates execution plan for ingestion based on repository analysis.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict, field

from .repository_scanner import RepositoryInventory
from .file_classifier import ClassifiedFile, ImportanceLevel

logger = logging.getLogger(__name__)


@dataclass
class SubJobPlan:
    """Plan for a sub-job."""
    sub_job_id: str
    sub_job_name: str
    files: List[ClassifiedFile]
    priority: int
    estimated_time_minutes: float
    dependencies: List[str] = field(default_factory=list)  # IDs of sub-jobs that must complete first
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'sub_job_id': self.sub_job_id,
            'sub_job_name': self.sub_job_name,
            'file_count': len(self.files),
            'priority': self.priority,
            'estimated_time_minutes': self.estimated_time_minutes,
            'dependencies': self.dependencies
        }


@dataclass
class ProcessingPlan:
    """Complete processing plan for repository."""
    repo_path: str
    total_files: int
    total_size_mb: float
    sub_jobs: List[SubJobPlan]
    estimated_total_time_minutes: float
    max_parallelization: int
    processing_order: List[str]  # Sub-job IDs in execution order
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'repo_path': self.repo_path,
            'total_files': self.total_files,
            'total_size_mb': round(self.total_size_mb, 2),
            'sub_jobs': [sj.to_dict() for sj in self.sub_jobs],
            'estimated_total_time_minutes': round(self.estimated_total_time_minutes, 1),
            'max_parallelization': self.max_parallelization,
            'processing_order': self.processing_order
        }


class ProcessingPlanner:
    """
    Creates intelligent processing plan for repository ingestion.
    
    Features:
    - Breaks large repos into sub-jobs
    - Prioritizes important files
    - Estimates processing time
    - Determines optimal parallelization
    """
    
    def __init__(self):
        self.files_per_sub_job = 1000  # Target files per sub-job
        self.min_sub_job_size = 100  # Minimum files per sub-job
    
    async def create_plan(
        self,
        inventory: RepositoryInventory,
        classified_files: List[ClassifiedFile],
        repo_path: str
    ) -> ProcessingPlan:
        """
        Create processing plan.
        
        Args:
            inventory: Repository inventory
            classified_files: Files with importance classification
            repo_path: Repository path
        
        Returns:
            Processing plan with sub-jobs
        """
        logger.info(f"📋 Creating processing plan for {len(classified_files)} files...")
        
        # Determine if we need sub-jobs
        if len(classified_files) < self.files_per_sub_job:
            # Small repo - single job
            sub_jobs = [self._create_single_sub_job(classified_files)]
        else:
            # Large repo - multiple sub-jobs
            sub_jobs = await self._create_sub_jobs(classified_files)
        
        # Estimate total time
        total_time = sum(sj.estimated_time_minutes for sj in sub_jobs)
        
        # Determine max parallelization (how many sub-jobs can run concurrently)
        max_parallel = self._calculate_max_parallelization(sub_jobs)
        
        # Determine processing order (topological sort if dependencies exist)
        processing_order = self._determine_processing_order(sub_jobs)
        
        plan = ProcessingPlan(
            repo_path=repo_path,
            total_files=len(classified_files),
            total_size_mb=inventory.total_size_bytes / 1024 / 1024,
            sub_jobs=sub_jobs,
            estimated_total_time_minutes=total_time,
            max_parallelization=max_parallel,
            processing_order=processing_order
        )
        
        logger.info(
            f"✅ Plan created: {len(sub_jobs)} sub-jobs, "
            f"~{total_time:.0f} min estimated, "
            f"max {max_parallel} parallel"
        )
        
        return plan
    
    def _create_single_sub_job(self, files: List[ClassifiedFile]) -> SubJobPlan:
        """Create a single sub-job for small repos."""
        return SubJobPlan(
            sub_job_id="main",
            sub_job_name="Main Ingestion",
            files=files,
            priority=1,
            estimated_time_minutes=self._estimate_time(files),
            dependencies=[]
        )
    
    async def _create_sub_jobs(self, files: List[ClassifiedFile]) -> List[SubJobPlan]:
        """Create multiple sub-jobs for large repos."""
        sub_jobs = []
        
        # Group files by importance level
        files_by_level = {}
        for cf in files:
            level = cf.importance_level
            if level not in files_by_level:
                files_by_level[level] = []
            files_by_level[level].append(cf)
        
        # Create sub-jobs by importance level
        priority = 1
        for level in [ImportanceLevel.CORE, ImportanceLevel.DEPENDENCY, ImportanceLevel.OTHER,
                      ImportanceLevel.CONFIG, ImportanceLevel.DOC, ImportanceLevel.EXAMPLE,
                      ImportanceLevel.TEST]:
            if level not in files_by_level:
                continue
            
            level_files = files_by_level[level]
            
            # Split into chunks if too many files
            chunks = self._split_into_chunks(level_files, self.files_per_sub_job)
            
            for i, chunk in enumerate(chunks):
                sub_job_name = f"{level.value}"
                if len(chunks) > 1:
                    sub_job_name += f" (Part {i+1}/{len(chunks)})"
                
                sub_jobs.append(SubJobPlan(
                    sub_job_id=f"{level.value.lower()}_{i+1}",
                    sub_job_name=sub_job_name,
                    files=chunk,
                    priority=priority,
                    estimated_time_minutes=self._estimate_time(chunk),
                    dependencies=[]  # Could add dependency logic here
                ))
            
            priority += 1
        
        return sub_jobs
    
    def _split_into_chunks(self, files: List[ClassifiedFile], chunk_size: int) -> List[List[ClassifiedFile]]:
        """Split files into chunks of approximately chunk_size."""
        chunks = []
        for i in range(0, len(files), chunk_size):
            chunks.append(files[i:i+chunk_size])
        return chunks
    
    def _estimate_time(self, files: List[ClassifiedFile]) -> float:
        """Estimate processing time in minutes."""
        # Rough estimate: 0.5 seconds per file on average
        # (includes normalization + embedding + storage)
        seconds_per_file = 0.5
        total_seconds = len(files) * seconds_per_file
        return total_seconds / 60
    
    def _calculate_max_parallelization(self, sub_jobs: List[SubJobPlan]) -> int:
        """Calculate maximum number of sub-jobs that can run in parallel."""
        # For now, simple heuristic: up to 5 sub-jobs in parallel
        # (can be adjusted based on system resources)
        return min(5, len(sub_jobs))
    
    def _determine_processing_order(self, sub_jobs: List[SubJobPlan]) -> List[str]:
        """Determine processing order (topological sort if dependencies exist)."""
        # For now, simple priority-based ordering
        # (can be enhanced with dependency graph later)
        sorted_jobs = sorted(sub_jobs, key=lambda x: x.priority)
        return [sj.sub_job_id for sj in sorted_jobs]


# Singleton instance
_planner_instance = None

def get_processing_planner() -> ProcessingPlanner:
    """Get singleton processing planner instance."""
    global _planner_instance
    if _planner_instance is None:
        _planner_instance = ProcessingPlanner()
    return _planner_instance

