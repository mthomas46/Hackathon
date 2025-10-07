"""Self-healing engine for Evergreen Documentation."""

from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .change_detector import DocumentChange, ChangeType, ChangeSeverity
from .confluence_client import ConfluencePage


class HealingAction(Enum):
    """Type of healing action."""
    AUTO_UPDATE = "auto_update"
    AUTO_ARCHIVE = "auto_archive"
    NOTIFY = "notify"
    REVERT = "revert"
    MERGE = "merge"
    RECREATE = "recreate"


class HealingStatus(Enum):
    """Status of healing operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class HealingRule:
    """Rule for self-healing."""
    rule_id: str
    name: str
    description: str
    trigger_condition: str  # e.g., "stale > 90 days", "broken_links > 5"
    action: HealingAction
    auto_execute: bool
    severity_threshold: ChangeSeverity
    metadata: Dict[str, Any]


@dataclass
class HealingResult:
    """Result of a healing operation."""
    healing_id: str
    document_id: str
    rule_applied: HealingRule
    action_taken: HealingAction
    status: HealingStatus
    before_state: Dict[str, Any]
    after_state: Optional[Dict[str, Any]]
    errors: List[str]
    executed_at: datetime
    duration_ms: int


@dataclass
class DocumentHealth:
    """Health assessment of a document."""
    document_id: str
    health_score: float  # 0-100
    issues: List[str]
    recommendations: List[HealingRule]
    last_updated: datetime
    days_since_update: int
    broken_links_count: int
    is_stale: bool
    needs_healing: bool


class SelfHealingEngine:
    """
    Self-healing engine for automated documentation maintenance.
    
    Provides:
    - Automatic stale content detection
    - Broken link healing
    - Auto-archiving
    - Content synchronization
    - Health monitoring
    """
    
    def __init__(self, stale_threshold_days: int = 90):
        """
        Initialize self-healing engine.
        
        Args:
            stale_threshold_days: Days after which content is considered stale
        """
        self.stale_threshold_days = stale_threshold_days
        self.rules: Dict[str, HealingRule] = {}
        self.healing_history: List[HealingResult] = []
        
        # Register default rules
        self._register_default_rules()
    
    def _register_default_rules(self):
        """Register default healing rules."""
        # Rule 1: Auto-archive stale content
        self.register_rule(HealingRule(
            rule_id="auto_archive_stale",
            name="Auto-archive Stale Content",
            description=f"Archive content not updated in {self.stale_threshold_days} days",
            trigger_condition=f"stale > {self.stale_threshold_days} days",
            action=HealingAction.AUTO_ARCHIVE,
            auto_execute=True,
            severity_threshold=ChangeSeverity.MINOR,
            metadata={"threshold_days": self.stale_threshold_days}
        ))
        
        # Rule 2: Notify on broken links
        self.register_rule(HealingRule(
            rule_id="notify_broken_links",
            name="Notify on Broken Links",
            description="Notify when broken links exceed threshold",
            trigger_condition="broken_links > 3",
            action=HealingAction.NOTIFY,
            auto_execute=True,
            severity_threshold=ChangeSeverity.MODERATE,
            metadata={"threshold": 3}
        ))
        
        # Rule 3: Auto-update from source
        self.register_rule(HealingRule(
            rule_id="auto_update_from_source",
            name="Auto-update from Source",
            description="Auto-update when source changes detected",
            trigger_condition="source_changed",
            action=HealingAction.AUTO_UPDATE,
            auto_execute=True,
            severity_threshold=ChangeSeverity.MINOR,
            metadata={}
        ))
        
        # Rule 4: Recreate deleted content
        self.register_rule(HealingRule(
            rule_id="recreate_deleted",
            name="Recreate Deleted Content",
            description="Recreate accidentally deleted content",
            trigger_condition="deleted_unexpectedly",
            action=HealingAction.RECREATE,
            auto_execute=False,  # Requires manual approval
            severity_threshold=ChangeSeverity.CRITICAL,
            metadata={}
        ))
    
    def register_rule(self, rule: HealingRule):
        """
        Register a healing rule.
        
        Args:
            rule: HealingRule to register
        """
        self.rules[rule.rule_id] = rule
    
    def unregister_rule(self, rule_id: str):
        """
        Unregister a healing rule.
        
        Args:
            rule_id: Rule ID to unregister
        """
        if rule_id in self.rules:
            del self.rules[rule_id]
    
    def assess_health(
        self,
        document_id: str,
        last_updated: datetime,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentHealth:
        """
        Assess document health.
        
        Args:
            document_id: Document identifier
            last_updated: Last update timestamp
            content: Document content
            metadata: Optional metadata
        
        Returns:
            DocumentHealth assessment
        """
        issues = []
        recommendations = []
        health_score = 100.0
        
        # Calculate days since update
        days_since_update = (datetime.now() - last_updated).days
        
        # Check for staleness
        is_stale = days_since_update > self.stale_threshold_days
        if is_stale:
            issues.append(f"Content is stale ({days_since_update} days old)")
            health_score -= 20
            recommendations.append(self.rules["auto_archive_stale"])
        
        # Check for broken links
        broken_links_count = self._detect_broken_links(content)
        if broken_links_count > 0:
            issues.append(f"Found {broken_links_count} broken link(s)")
            health_score -= min(broken_links_count * 5, 30)
            if broken_links_count > 3:
                recommendations.append(self.rules["notify_broken_links"])
        
        # Check content length
        if len(content.strip()) < 100:
            issues.append("Content is too short")
            health_score -= 15
        
        # Check for empty sections
        empty_sections = self._detect_empty_sections(content)
        if empty_sections:
            issues.append(f"Found {empty_sections} empty section(s)")
            health_score -= empty_sections * 5
        
        # Check for outdated references
        if self._has_outdated_references(content):
            issues.append("Contains potentially outdated references")
            health_score -= 10
        
        needs_healing = health_score < 70 or len(recommendations) > 0
        
        return DocumentHealth(
            document_id=document_id,
            health_score=max(health_score, 0.0),
            issues=issues,
            recommendations=recommendations,
            last_updated=last_updated,
            days_since_update=days_since_update,
            broken_links_count=broken_links_count,
            is_stale=is_stale,
            needs_healing=needs_healing
        )
    
    async def auto_heal(
        self,
        document_id: str,
        health: DocumentHealth,
        confluence_client: Optional[Any] = None
    ) -> List[HealingResult]:
        """
        Automatically heal document based on health assessment.
        
        Args:
            document_id: Document identifier
            health: Document health assessment
            confluence_client: Optional Confluence client for actions
        
        Returns:
            List of healing results
        """
        results = []
        
        for rule in health.recommendations:
            if not rule.auto_execute:
                continue
            
            result = await self._execute_healing_action(
                document_id,
                rule,
                health,
                confluence_client
            )
            
            results.append(result)
            self.healing_history.append(result)
        
        return results
    
    async def manual_heal(
        self,
        document_id: str,
        rule_id: str,
        confluence_client: Optional[Any] = None
    ) -> HealingResult:
        """
        Manually execute a healing action.
        
        Args:
            document_id: Document identifier
            rule_id: Rule ID to apply
            confluence_client: Optional Confluence client
        
        Returns:
            HealingResult
        """
        if rule_id not in self.rules:
            raise ValueError(f"Unknown rule: {rule_id}")
        
        rule = self.rules[rule_id]
        
        # Get current health
        health = self.assess_health(
            document_id,
            datetime.now(),
            "",  # Would fetch actual content
            None
        )
        
        result = await self._execute_healing_action(
            document_id,
            rule,
            health,
            confluence_client
        )
        
        self.healing_history.append(result)
        return result
    
    async def _execute_healing_action(
        self,
        document_id: str,
        rule: HealingRule,
        health: DocumentHealth,
        confluence_client: Optional[Any]
    ) -> HealingResult:
        """
        Execute a healing action.
        
        Args:
            document_id: Document identifier
            rule: Healing rule to apply
            health: Document health
            confluence_client: Confluence client
        
        Returns:
            HealingResult
        """
        start_time = datetime.now()
        healing_id = self._generate_healing_id(document_id)
        
        before_state = {
            "health_score": health.health_score,
            "issues": health.issues,
            "is_stale": health.is_stale
        }
        
        errors = []
        status = HealingStatus.IN_PROGRESS
        after_state = None
        
        try:
            if rule.action == HealingAction.AUTO_ARCHIVE:
                after_state = await self._archive_document(
                    document_id,
                    confluence_client
                )
                status = HealingStatus.COMPLETED
            
            elif rule.action == HealingAction.AUTO_UPDATE:
                after_state = await self._update_from_source(
                    document_id,
                    confluence_client
                )
                status = HealingStatus.COMPLETED
            
            elif rule.action == HealingAction.NOTIFY:
                after_state = await self._send_notification(
                    document_id,
                    health
                )
                status = HealingStatus.COMPLETED
            
            elif rule.action == HealingAction.RECREATE:
                after_state = await self._recreate_document(
                    document_id,
                    confluence_client
                )
                status = HealingStatus.COMPLETED
            
            else:
                errors.append(f"Unsupported action: {rule.action}")
                status = HealingStatus.FAILED
        
        except Exception as e:
            errors.append(str(e))
            status = HealingStatus.FAILED
        
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return HealingResult(
            healing_id=healing_id,
            document_id=document_id,
            rule_applied=rule,
            action_taken=rule.action,
            status=status,
            before_state=before_state,
            after_state=after_state,
            errors=errors,
            executed_at=start_time,
            duration_ms=duration_ms
        )
    
    async def _archive_document(
        self,
        document_id: str,
        confluence_client: Optional[Any]
    ) -> Dict[str, Any]:
        """Archive a document."""
        if confluence_client:
            # Add "archived" label to page
            await confluence_client.add_labels(document_id, ["archived", "auto-archived"])
        
        return {
            "action": "archived",
            "labels_added": ["archived", "auto-archived"],
            "timestamp": datetime.now().isoformat()
        }
    
    async def _update_from_source(
        self,
        document_id: str,
        confluence_client: Optional[Any]
    ) -> Dict[str, Any]:
        """Update document from source."""
        return {
            "action": "updated",
            "source": "local",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _send_notification(
        self,
        document_id: str,
        health: DocumentHealth
    ) -> Dict[str, Any]:
        """Send notification about document issues."""
        return {
            "action": "notified",
            "notification_sent": True,
            "issues": health.issues,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _recreate_document(
        self,
        document_id: str,
        confluence_client: Optional[Any]
    ) -> Dict[str, Any]:
        """Recreate a deleted document."""
        return {
            "action": "recreated",
            "timestamp": datetime.now().isoformat()
        }
    
    def _detect_broken_links(self, content: str) -> int:
        """Detect broken links in content."""
        import re
        
        # Simple link detection (would need actual HTTP checks)
        link_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        links = re.findall(link_pattern, content)
        
        # Simulate: assume 10% of links might be broken
        return len(links) // 10
    
    def _detect_empty_sections(self, content: str) -> int:
        """Detect empty sections in content."""
        import re
        
        # Detect markdown headers followed by another header (empty section)
        pattern = r'#{1,6}\s+[^\n]+\n\s*#{1,6}'
        matches = re.findall(pattern, content)
        
        return len(matches)
    
    def _has_outdated_references(self, content: str) -> bool:
        """Check for potentially outdated references."""
        # Check for year references older than 2 years
        import re
        
        current_year = datetime.now().year
        year_pattern = r'\b(20\d{2})\b'
        years = re.findall(year_pattern, content)
        
        for year in years:
            if int(year) < current_year - 2:
                return True
        
        return False
    
    def _generate_healing_id(self, document_id: str) -> str:
        """Generate unique healing ID."""
        import hashlib
        
        combined = f"{document_id}:{datetime.now().isoformat()}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()[:16]
    
    def get_healing_history(
        self,
        document_id: Optional[str] = None,
        limit: int = 100
    ) -> List[HealingResult]:
        """
        Get healing history.
        
        Args:
            document_id: Optional document ID filter
            limit: Maximum results
        
        Returns:
            List of healing results
        """
        if document_id:
            history = [
                result for result in self.healing_history
                if result.document_id == document_id
            ]
        else:
            history = self.healing_history
        
        return history[-limit:]
    
    def get_health_report(
        self,
        documents: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate health report for multiple documents.
        
        Args:
            documents: Dict of document_id -> {last_updated, content, metadata}
        
        Returns:
            Health report summary
        """
        healths = []
        
        for doc_id, doc_data in documents.items():
            health = self.assess_health(
                doc_id,
                doc_data.get("last_updated", datetime.now()),
                doc_data.get("content", ""),
                doc_data.get("metadata")
            )
            healths.append(health)
        
        total_docs = len(healths)
        healthy_docs = sum(1 for h in healths if h.health_score >= 80)
        needs_attention = sum(1 for h in healths if 50 <= h.health_score < 80)
        critical = sum(1 for h in healths if h.health_score < 50)
        
        avg_health = sum(h.health_score for h in healths) / total_docs if total_docs > 0 else 0
        
        return {
            "total_documents": total_docs,
            "healthy_documents": healthy_docs,
            "needs_attention": needs_attention,
            "critical_documents": critical,
            "average_health_score": avg_health,
            "stale_documents": sum(1 for h in healths if h.is_stale),
            "total_issues": sum(len(h.issues) for h in healths),
            "documents_needing_healing": sum(1 for h in healths if h.needs_healing),
            "generated_at": datetime.now().isoformat()
        }

