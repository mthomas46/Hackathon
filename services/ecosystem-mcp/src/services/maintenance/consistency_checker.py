"""
Consistency Checker Service

Checks for inconsistencies in documentation:
- Find conflicting information
- Detect outdated cross-references
- Check terminology consistency
- Identify contradictions
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID
import re

from sqlalchemy.ext.asyncio import AsyncSession

from ...storage.db_models import DocumentModel
from ...storage.repositories import DocumentRepository
from ...storage import get_database
from ...services.rag import get_context_aware_rag

logger = logging.getLogger(__name__)


class InconsistencyIssue:
    """Represents a consistency issue."""
    
    def __init__(
        self,
        issue_type: str,
        severity: str,
        description: str,
        affected_documents: List[Dict[str, Any]],
        details: Optional[Dict[str, Any]] = None
    ):
        self.issue_type = issue_type
        self.severity = severity
        self.description = description
        self.affected_documents = affected_documents
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "issue_type": self.issue_type,
            "severity": self.severity,
            "description": self.description,
            "affected_documents": self.affected_documents,
            "details": self.details
        }


class ConsistencyChecker:
    """
    Check documentation consistency.
    
    Features:
    - Conflicting information detection
    - Outdated cross-reference detection
    - Terminology consistency checking
    - Version mismatch detection
    """
    
    def __init__(self):
        """Initialize consistency checker."""
        self.logger = logging.getLogger(__name__)
        self.context_rag = get_context_aware_rag()
    
    async def check_consistency(
        self,
        service_name: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Check documentation consistency.
        
        Args:
            service_name: Optional service filter
            limit: Maximum documents to check
        
        Returns:
            Consistency check results
        """
        try:
            self.logger.info(f"🔍 Checking documentation consistency (service={service_name})")
            
            async with get_database().session() as session:
                doc_repo = DocumentRepository(session)
                
                # Get documents
                if service_name:
                    documents = await doc_repo.get_by_service(service_name, limit=limit * 2)
                else:
                    documents = await doc_repo.get_all(limit=limit * 2)
                
                self.logger.info(f"   📄 Checking {len(documents)} documents")
                
                # Run consistency checks
                issues = []
                
                # Check for outdated cross-references
                ref_issues = await self._check_cross_references(documents)
                issues.extend(ref_issues)
                
                # Check for terminology inconsistencies
                term_issues = await self._check_terminology(documents)
                issues.extend(term_issues)
                
                # Check for conflicting information (simplified)
                conflict_issues = await self._check_conflicts(documents)
                issues.extend(conflict_issues)
                
                # Categorize by severity
                categorized = {
                    "CRITICAL": [i for i in issues if i.severity == "CRITICAL"],
                    "HIGH": [i for i in issues if i.severity == "HIGH"],
                    "MEDIUM": [i for i in issues if i.severity == "MEDIUM"],
                    "LOW": [i for i in issues if i.severity == "LOW"]
                }
                
                return {
                    "total_checked": len(documents),
                    "total_issues": len(issues),
                    "by_severity": {
                        "CRITICAL": len(categorized["CRITICAL"]),
                        "HIGH": len(categorized["HIGH"]),
                        "MEDIUM": len(categorized["MEDIUM"]),
                        "LOW": len(categorized["LOW"])
                    },
                    "issues": {
                        "CRITICAL": [i.to_dict() for i in categorized["CRITICAL"]],
                        "HIGH": [i.to_dict() for i in categorized["HIGH"]],
                        "MEDIUM": [i.to_dict() for i in categorized["MEDIUM"]],
                        "LOW": [i.to_dict() for i in categorized["LOW"]]
                    },
                    "recommendations": self._generate_recommendations(categorized),
                    "metadata": {
                        "service_name": service_name,
                        "checked_at": datetime.utcnow().isoformat()
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Failed to check consistency: {e}", exc_info=True)
            raise
    
    async def _check_cross_references(
        self,
        documents: List[DocumentModel]
    ) -> List[InconsistencyIssue]:
        """Check for outdated or broken cross-references."""
        issues = []
        
        # Pattern to find markdown links and references
        link_pattern = re.compile(r'\[([^\]]+)\]\(([^\)]+)\)')
        ref_pattern = re.compile(r'see `([^`]+)`|refer to `([^`]+)`', re.IGNORECASE)
        
        # Build index of document paths
        doc_paths = {doc.file_path: doc for doc in documents}
        
        for doc in documents:
            if not doc.normalized_content:
                continue
            
            # Find all links
            links = link_pattern.findall(doc.normalized_content)
            refs = ref_pattern.findall(doc.normalized_content)
            
            # Check if referenced files exist
            for text, path in links:
                if path.startswith(('http://', 'https://', '#')):
                    continue  # Skip external links and anchors
                
                # Check if referenced document exists
                if path not in doc_paths:
                    issues.append(InconsistencyIssue(
                        issue_type="broken_cross_reference",
                        severity="MEDIUM",
                        description=f"Broken reference to '{path}' in document",
                        affected_documents=[{
                            "document_id": str(doc.id),
                            "file_path": doc.file_path,
                            "link_text": text,
                            "broken_path": path
                        }]
                    ))
        
        return issues
    
    async def _check_terminology(
        self,
        documents: List[DocumentModel]
    ) -> List[InconsistencyIssue]:
        """Check for terminology inconsistencies."""
        issues = []
        
        # Common terms that should be consistent
        terminology_variants = {
            "api": ["API", "api", "Api"],
            "database": ["database", "Database", "DB", "db"],
            "configuration": ["configuration", "config", "Config", "Configuration"],
            "authentication": ["authentication", "auth", "Auth", "Authentication"]
        }
        
        # Track term usage across documents
        term_usage = {}
        
        for doc in documents:
            if not doc.normalized_content:
                continue
            
            for canonical, variants in terminology_variants.items():
                found_variants = []
                for variant in variants:
                    # Case-sensitive search
                    if re.search(r'\b' + re.escape(variant) + r'\b', doc.normalized_content):
                        found_variants.append(variant)
                
                if len(found_variants) > 1:
                    # Multiple variants found in same document
                    term_usage.setdefault(canonical, []).append({
                        "document_id": str(doc.id),
                        "file_path": doc.file_path,
                        "variants_found": found_variants
                    })
        
        # Report inconsistencies
        for canonical, usages in term_usage.items():
            if len(usages) > 1:
                issues.append(InconsistencyIssue(
                    issue_type="terminology_inconsistency",
                    severity="LOW",
                    description=f"Inconsistent usage of term '{canonical}' across documents",
                    affected_documents=usages,
                    details={"canonical_term": canonical}
                ))
        
        return issues
    
    async def _check_conflicts(
        self,
        documents: List[DocumentModel]
    ) -> List[InconsistencyIssue]:
        """Check for conflicting information (simplified version)."""
        issues = []
        
        # This is a simplified check - in production, you'd use:
        # - Semantic similarity to find similar content
        # - NLP to detect contradictions
        # - Version comparison to find changed facts
        
        # For now, just check for documents with very similar content
        # but different file paths (potential duplicates with conflicts)
        
        seen_content_hashes = {}
        
        for doc in documents:
            if not doc.normalized_content or len(doc.normalized_content) < 100:
                continue
            
            # Simple content hash (first 200 chars)
            content_sample = doc.normalized_content[:200].lower().strip()
            
            if content_sample in seen_content_hashes:
                # Potential duplicate or conflict
                other_doc = seen_content_hashes[content_sample]
                
                # Check if content is different beyond the sample
                if doc.normalized_content != other_doc.normalized_content:
                    issues.append(InconsistencyIssue(
                        issue_type="potential_conflict",
                        severity="MEDIUM",
                        description="Similar documents with potentially conflicting content",
                        affected_documents=[
                            {
                                "document_id": str(doc.id),
                                "file_path": doc.file_path
                            },
                            {
                                "document_id": str(other_doc.id),
                                "file_path": other_doc.file_path
                            }
                        ],
                        details={"reason": "Similar content but different details"}
                    ))
            else:
                seen_content_hashes[content_sample] = doc
        
        return issues
    
    def _generate_recommendations(
        self,
        categorized: Dict[str, List[InconsistencyIssue]]
    ) -> List[str]:
        """Generate recommendations based on consistency issues."""
        recommendations = []
        
        critical_count = len(categorized["CRITICAL"])
        high_count = len(categorized["HIGH"])
        medium_count = len(categorized["MEDIUM"])
        low_count = len(categorized["LOW"])
        
        if critical_count > 0:
            recommendations.append(
                f"🚨 {critical_count} critical consistency issues - immediate attention required"
            )
        
        if high_count > 0:
            recommendations.append(
                f"❗ {high_count} high-priority consistency issues - review soon"
            )
        
        if medium_count > 0:
            recommendations.append(
                f"⚠️ {medium_count} medium-priority issues - consider fixing in next update"
            )
        
        if low_count > 0:
            recommendations.append(
                f"ℹ️ {low_count} low-priority issues - standardize terminology gradually"
            )
        
        if not recommendations:
            recommendations.append("✅ No consistency issues found!")
        
        return recommendations
    
    async def check_specific_term(
        self,
        term: str,
        service_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check consistency of a specific term across documentation.
        
        Args:
            term: Term to check
            service_name: Optional service filter
        
        Returns:
            Term usage analysis
        """
        try:
            self.logger.info(f"🔍 Checking consistency of term: {term}")
            
            async with get_database().session() as session:
                doc_repo = DocumentRepository(session)
                
                # Get documents
                if service_name:
                    documents = await doc_repo.get_by_service(service_name, limit=1000)
                else:
                    documents = await doc_repo.get_all(limit=1000)
                
                # Find term usages
                usages = []
                for doc in documents:
                    if not doc.normalized_content:
                        continue
                    
                    # Find all occurrences (case-insensitive)
                    pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
                    matches = pattern.findall(doc.normalized_content)
                    
                    if matches:
                        usages.append({
                            "document_id": str(doc.id),
                            "file_path": doc.file_path,
                            "occurrences": len(matches),
                            "variants": list(set(matches))
                        })
                
                # Analyze variants
                all_variants = set()
                for usage in usages:
                    all_variants.update(usage["variants"])
                
                return {
                    "term": term,
                    "total_documents": len(usages),
                    "total_occurrences": sum(u["occurrences"] for u in usages),
                    "variants_found": list(all_variants),
                    "is_consistent": len(all_variants) <= 1,
                    "usages": usages[:50],  # Limit to 50 examples
                    "recommendation": (
                        "✅ Term usage is consistent"
                        if len(all_variants) <= 1
                        else f"⚠️ Found {len(all_variants)} variants - consider standardizing"
                    )
                }
                
        except Exception as e:
            self.logger.error(f"Failed to check term: {e}", exc_info=True)
            raise

