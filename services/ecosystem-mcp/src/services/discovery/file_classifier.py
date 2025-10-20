"""
File Classifier

Classifies files by importance for prioritized processing.
"""

import logging
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum

from .repository_scanner import FileInfo

logger = logging.getLogger(__name__)


class ImportanceLevel(str, Enum):
    """File importance levels."""
    CORE = "CORE"  # Business logic, APIs, models
    DEPENDENCY = "DEPENDENCY"  # Utilities, libraries
    TEST = "TEST"  # Tests
    EXAMPLE = "EXAMPLE"  # Examples, demos
    DOC = "DOC"  # Documentation
    CONFIG = "CONFIG"  # Configuration
    OTHER = "OTHER"  # Everything else


@dataclass
class ClassifiedFile:
    """File with importance classification."""
    file_info: FileInfo
    importance_level: ImportanceLevel
    importance_score: float  # 0.0-1.0
    priority: int  # Processing order (lower = higher priority)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'file_info': self.file_info.to_dict(),
            'importance_level': self.importance_level.value,
            'importance_score': self.importance_score,
            'priority': self.priority
        }


class FileClassifier:
    """
    Classifies files by importance for prioritized processing.
    
    Uses heuristics to determine which files are most important
    to process first (core business logic vs tests).
    """
    
    def __init__(self):
        # Core patterns (high importance)
        self.core_patterns = {
            "api", "handler", "controller", "service", "model",
            "entity", "repository", "dao", "business", "core",
            "routes", "views", "endpoints"
        }
        
        # Dependency patterns (medium importance)
        self.dependency_patterns = {
            "util", "helper", "common", "shared", "lib", "tool",
            "utils", "helpers", "libraries"
        }
    
    async def classify(self, files: List[FileInfo]) -> List[ClassifiedFile]:
        """
        Classify files by importance.
        
        Args:
            files: List of file information
        
        Returns:
            List of classified files with importance scores
        """
        logger.info(f"📊 Classifying {len(files)} files by importance...")
        
        classified = []
        
        for file_info in files:
            # Determine importance level
            level = self._determine_importance_level(file_info)
            
            # Calculate importance score (0.0-1.0)
            score = self._calculate_importance_score(file_info, level)
            
            # Determine processing priority (lower = higher priority)
            priority = self._calculate_priority(level, score)
            
            classified.append(ClassifiedFile(
                file_info=file_info,
                importance_level=level,
                importance_score=score,
                priority=priority
            ))
        
        # Sort by priority (lower first)
        classified.sort(key=lambda x: x.priority)
        
        # Log statistics
        level_counts = {}
        for cf in classified:
            level_counts[cf.importance_level] = level_counts.get(cf.importance_level, 0) + 1
        
        logger.info(f"✅ Classification complete:")
        for level, count in sorted(level_counts.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"   {level}: {count} files")
        
        return classified
    
    def _determine_importance_level(self, file_info: FileInfo) -> ImportanceLevel:
        """Determine importance level for a file."""
        path_lower = file_info.relative_path.lower()
        
        # Tests
        if file_info.is_test:
            return ImportanceLevel.TEST
        
        # Documentation
        if file_info.is_doc:
            return ImportanceLevel.DOC
        
        # Configuration
        if file_info.is_config:
            return ImportanceLevel.CONFIG
        
        # Examples
        if "example" in path_lower or "demo" in path_lower or "sample" in path_lower:
            return ImportanceLevel.EXAMPLE
        
        # Core business logic
        if any(pattern in path_lower for pattern in self.core_patterns):
            return ImportanceLevel.CORE
        
        # Dependencies/utilities
        if any(pattern in path_lower for pattern in self.dependency_patterns):
            return ImportanceLevel.DEPENDENCY
        
        # Default to OTHER
        return ImportanceLevel.OTHER
    
    def _calculate_importance_score(self, file_info: FileInfo, level: ImportanceLevel) -> float:
        """Calculate importance score (0.0-1.0)."""
        # Base score by level
        base_scores = {
            ImportanceLevel.CORE: 1.0,
            ImportanceLevel.DEPENDENCY: 0.7,
            ImportanceLevel.OTHER: 0.5,
            ImportanceLevel.CONFIG: 0.4,
            ImportanceLevel.DOC: 0.3,
            ImportanceLevel.EXAMPLE: 0.2,
            ImportanceLevel.TEST: 0.1
        }
        
        score = base_scores.get(level, 0.5)
        
        # Adjust based on file characteristics
        # Larger files might be more important (more logic)
        if file_info.size_bytes > 10000:  # > 10KB
            score += 0.1
        
        # Code files are more important than non-code
        if file_info.is_code:
            score += 0.05
        
        # Cap at 1.0
        return min(score, 1.0)
    
    def _calculate_priority(self, level: ImportanceLevel, score: float) -> int:
        """Calculate processing priority (lower = higher priority)."""
        # Priority order:
        # 1. CORE (priority 1000-1999)
        # 2. DEPENDENCY (priority 2000-2999)
        # 3. OTHER (priority 3000-3999)
        # 4. CONFIG (priority 4000-4999)
        # 5. DOC (priority 5000-5999)
        # 6. EXAMPLE (priority 6000-6999)
        # 7. TEST (priority 7000-7999)
        
        base_priorities = {
            ImportanceLevel.CORE: 1000,
            ImportanceLevel.DEPENDENCY: 2000,
            ImportanceLevel.OTHER: 3000,
            ImportanceLevel.CONFIG: 4000,
            ImportanceLevel.DOC: 5000,
            ImportanceLevel.EXAMPLE: 6000,
            ImportanceLevel.TEST: 7000
        }
        
        base = base_priorities.get(level, 3000)
        
        # Within each level, higher score = lower priority number
        # (so higher importance files are processed first)
        offset = int((1.0 - score) * 999)
        
        return base + offset


# Singleton instance
_classifier_instance = None

def get_file_classifier() -> FileClassifier:
    """Get singleton file classifier instance."""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = FileClassifier()
    return _classifier_instance

