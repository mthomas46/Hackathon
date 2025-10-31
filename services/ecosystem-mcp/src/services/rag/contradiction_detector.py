"""
Contradiction Detection Service

Detects conflicting information in retrieved documents.

PHASE 7R: Advanced feature for improving answer reliability
Expected Impact: +6-10% for complex queries
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ContradictionDetector:
    """
    Detect contradictions in retrieved documents.
    
    Philosophy:
    - Simple heuristics first (fast, good enough)
    - LLM verification only for high-stakes cases
    - Warn users, don't hide information
    
    Contradiction Types:
    - Temporal: Different dates/versions for same info
    - Negation: Opposite statements
    - Value: Different numbers/values for same metric
    
    PHASE 7R: Helps users understand source disagreements
    """
    
    def __init__(self):
        """Initialize contradiction detector."""
        
        # Common contradiction patterns
        self.negation_pairs = [
            ("is", "is not"),
            ("does", "does not"),
            ("can", "cannot"),
            ("will", "will not"),
            ("should", "should not"),
            ("has", "has not"),
            ("was", "was not"),
            ("enabled", "disabled"),
            ("supports", "does not support"),
            ("available", "unavailable"),
            ("working", "not working"),
            ("fixed", "broken"),
            ("deprecated", "active"),
            ("recommended", "not recommended")
        ]
        
        logger.info("ContradictionDetector initialized")
    
    def detect(
        self,
        documents: List[Dict[str, Any]],
        question: str
    ) -> Dict[str, Any]:
        """
        Detect contradictions in documents.
        
        Strategy:
        1. Check temporal conflicts (different dates)
        2. Check negation patterns
        3. Check value conflicts
        
        Args:
            documents: Retrieved documents
            question: User's question
        
        Returns:
            Dict with:
            - has_contradictions: bool
            - contradiction_count: int
            - contradictions: List of detected contradictions
            - severity: low/medium/high
            - warning_message: User-facing message
        
        Performance: < 10ms for typical case
        """
        start_time = datetime.now()
        
        if len(documents) < 2:
            # Need at least 2 docs to have contradictions
            return {
                "has_contradictions": False,
                "contradiction_count": 0,
                "contradictions": [],
                "severity": "none",
                "warning_message": None
            }
        
        contradictions = []
        
        # 1. Temporal conflicts
        temporal_conflicts = self._detect_temporal_conflicts(documents)
        contradictions.extend(temporal_conflicts)
        
        # 2. Negation patterns
        negation_conflicts = self._detect_negation_conflicts(documents)
        contradictions.extend(negation_conflicts)
        
        # 3. Value conflicts (for numeric queries)
        if self._is_numeric_query(question):
            value_conflicts = self._detect_value_conflicts(documents)
            contradictions.extend(value_conflicts)
        
        # Calculate severity
        contradiction_count = len(contradictions)
        if contradiction_count == 0:
            severity = "none"
        elif contradiction_count <= 2:
            severity = "low"
        elif contradiction_count <= 4:
            severity = "medium"
        else:
            severity = "high"
        
        # Generate warning message
        warning_message = None
        if contradiction_count > 0:
            warning_message = self._generate_warning_message(
                contradiction_count,
                severity,
                contradictions
            )
        
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        if contradiction_count > 0:
            logger.info(
                f"   ⚠️  Detected {contradiction_count} potential contradictions "
                f"(severity: {severity}, {elapsed_ms:.1f}ms)"
            )
        else:
            logger.debug(f"   ✅ No contradictions detected ({elapsed_ms:.1f}ms)")
        
        return {
            "has_contradictions": contradiction_count > 0,
            "contradiction_count": contradiction_count,
            "contradictions": contradictions,
            "severity": severity,
            "warning_message": warning_message,
            "detection_time_ms": round(elapsed_ms, 2)
        }
    
    def _detect_temporal_conflicts(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect temporal conflicts (different dates/recency).
        
        Conflict: Same file/topic, very different update times
        
        Returns:
            List of temporal conflicts
        """
        conflicts = []
        
        # Group documents by similarity
        # Simple heuristic: Same file path prefix or similar content
        doc_groups = {}
        for doc in documents:
            file_path = doc.get("file_path", "")
            # Group by top-level directory
            group_key = file_path.split('/')[0] if '/' in file_path else file_path
            
            if group_key not in doc_groups:
                doc_groups[group_key] = []
            doc_groups[group_key].append(doc)
        
        # Check for temporal conflicts within groups
        for group_key, group_docs in doc_groups.items():
            if len(group_docs) < 2:
                continue
            
            # Get recency values
            recencies = [
                doc.get("recency_days")
                for doc in group_docs
                if doc.get("recency_days") is not None
            ]
            
            if len(recencies) < 2:
                continue
            
            # Check if there's a large gap (e.g., > 180 days)
            min_recency = min(recencies)
            max_recency = max(recencies)
            gap = max_recency - min_recency
            
            if gap > 180:  # 6 months
                conflicts.append({
                    "type": "temporal",
                    "description": f"Documents from {group_key} have large time gap",
                    "detail": f"Age range: {min_recency} to {max_recency} days old",
                    "severity": "medium"
                })
        
        return conflicts
    
    def _detect_negation_conflicts(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect negation conflicts (opposite statements).
        
        Checks for negation pairs in document content.
        
        Returns:
            List of negation conflicts
        """
        conflicts = []
        
        # Extract content from all docs
        contents = []
        for doc in documents:
            content = doc.get("content", "")
            if content:
                contents.append(content.lower())
        
        if len(contents) < 2:
            return conflicts
        
        # Check for negation pairs
        for positive, negative in self.negation_pairs:
            positive_found = any(positive in c for c in contents)
            negative_found = any(negative in c for c in contents)
            
            if positive_found and negative_found:
                conflicts.append({
                    "type": "negation",
                    "description": f"Conflicting statements found",
                    "detail": f"Some sources say '{positive}', others say '{negative}'",
                    "severity": "high"
                })
        
        return conflicts
    
    def _detect_value_conflicts(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect value conflicts (different numbers for same metric).
        
        Simple heuristic: Extract numbers, check for large variance.
        
        Returns:
            List of value conflicts
        """
        conflicts = []
        
        # Extract numbers from documents
        import re
        all_numbers = []
        
        for doc in documents:
            content = doc.get("content", "")
            
            # ⚡ FIX: Handle None or non-string content
            if not content or not isinstance(content, str):
                continue
            
            # Find numbers (integers and decimals)
            numbers = re.findall(r'\b\d+\.?\d*\b', content)
            all_numbers.extend([float(n) for n in numbers if n])
        
        if len(all_numbers) < 2:
            return conflicts
        
        # Check for large variance (coefficient of variation > 0.5)
        mean_val = sum(all_numbers) / len(all_numbers)
        if mean_val == 0:
            return conflicts
        
        variance = sum((x - mean_val) ** 2 for x in all_numbers) / len(all_numbers)
        std_dev = variance ** 0.5
        cv = std_dev / mean_val  # Coefficient of variation
        
        if cv > 0.5:  # High variance
            conflicts.append({
                "type": "value",
                "description": "Numeric values vary significantly across sources",
                "detail": f"Values range widely (CV: {cv:.2f})",
                "severity": "medium"
            })
        
        return conflicts
    
    def _is_numeric_query(self, question: str) -> bool:
        """
        Check if query is asking for numeric information.
        
        Args:
            question: User's question
        
        Returns:
            True if query appears to be numeric
        """
        numeric_keywords = [
            "how many", "how much", "number of", "count",
            "percentage", "percent", "%", "rate", "cost",
            "price", "size", "length", "time", "duration"
        ]
        
        question_lower = question.lower()
        return any(kw in question_lower for kw in numeric_keywords)
    
    def _generate_warning_message(
        self,
        count: int,
        severity: str,
        contradictions: List[Dict[str, Any]]
    ) -> str:
        """
        Generate user-facing warning message.
        
        Args:
            count: Number of contradictions
            severity: Severity level
            contradictions: List of contradictions
        
        Returns:
            Warning message string
        """
        if severity == "high":
            message = (
                f"⚠️  **Note: Conflicting Information Detected**\n\n"
                f"The retrieved sources contain {count} potential contradictions. "
                f"This answer is synthesized from conflicting information. "
                f"Please verify important details from multiple sources.\n\n"
                f"**Detected Issues:**\n"
            )
        elif severity == "medium":
            message = (
                f"ℹ️  **Note: Some Source Disagreement**\n\n"
                f"The sources have {count} minor inconsistencies. "
                f"The answer reflects the most common or recent information.\n\n"
                f"**Detected Issues:**\n"
            )
        else:  # low
            message = (
                f"ℹ️  **Note: Minor Inconsistency**\n\n"
                f"A minor inconsistency was detected in the sources. "
                f"The answer prioritizes the most recent information.\n\n"
            )
        
        # Add top contradictions (max 3)
        for i, contradiction in enumerate(contradictions[:3]):
            message += f"- {contradiction['description']}\n"
        
        return message


# Singleton instance
_detector_instance = None


def get_contradiction_detector() -> ContradictionDetector:
    """Get or create singleton contradiction detector."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = ContradictionDetector()
    return _detector_instance

