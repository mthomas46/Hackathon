"""Integration tests for Evergreen Documentation system."""

import sys
from pathlib import Path

# Add services to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services"))

import pytest
from datetime import datetime, timedelta

from mcp_evergreen_docs.src.sync_engine import SyncEngine, SyncDirection, ConflictResolution
from mcp_evergreen_docs.src.change_detector import ChangeDetector, ChangeType, ChangeSeverity
from mcp_evergreen_docs.src.self_healing_engine import SelfHealingEngine, HealingAction


@pytest.mark.asyncio
class TestEvergreenDocsIntegration:
    """Integration tests for Evergreen Documentation."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.sync_engine = SyncEngine()
        self.change_detector = ChangeDetector()
        self.healing_engine = SelfHealingEngine(stale_threshold_days=30)
    
    async def test_complete_sync_workflow(self):
        """Test complete sync workflow: detect changes → sync → heal."""
        # Step 1: Register initial documents
        doc_id = "doc-001"
        initial_content = "# API Documentation\n\nThis is the initial content."
        
        self.change_detector.register_document(doc_id, initial_content)
        
        # Step 2: Simulate local change
        updated_content = "# API Documentation\n\nThis is the updated content with new examples."
        change = self.change_detector.detect_changes(doc_id, updated_content)
        
        assert change is not None
        assert change.change_type == ChangeType.MODIFIED
        assert change.severity in [ChangeSeverity.MINOR, ChangeSeverity.MODERATE]
        
        # Step 3: Sync to Confluence
        sync_result = await self.sync_engine.sync_to_confluence(
            doc_id,
            updated_content,
            space_key="TEST",
            author="test-user"
        )
        
        assert sync_result.success
        assert sync_result.direction == SyncDirection.TO_CONFLUENCE
        
        # Step 4: Assess health
        health = self.healing_engine.assess_health(
            doc_id,
            datetime.now(),
            updated_content
        )
        
        assert health.health_score > 50
        assert not health.is_stale  # Just updated
    
    async def test_bidirectional_sync_with_conflicts(self):
        """Test bidirectional sync with conflict resolution."""
        doc_id = "doc-002"
        
        # Initial content
        mcp_content = "# User Guide\n\nVersion 1.0"
        confluence_content = "# User Guide\n\nVersion 1.1"
        
        # Register both versions
        self.change_detector.register_document(doc_id, mcp_content)
        
        # Detect conflict (both changed)
        change = self.change_detector.detect_changes(doc_id, confluence_content)
        assert change is not None
        
        # Sync with conflict resolution (MCP wins)
        sync_result = await self.sync_engine.sync_bidirectional(
            doc_id,
            mcp_content,
            confluence_content,
            conflict_resolution=ConflictResolution.MCP_WINS,
            space_key="TEST"
        )
        
        assert sync_result.success
        assert sync_result.conflicts_detected
        assert sync_result.conflict_resolution == ConflictResolution.MCP_WINS
    
    async def test_stale_content_auto_archiving(self):
        """Test automatic archiving of stale content."""
        doc_id = "doc-003"
        content = "# Old Documentation\n\nThis is outdated."
        
        # Simulate old document (40 days old)
        old_date = datetime.now() - timedelta(days=40)
        
        # Assess health
        health = self.healing_engine.assess_health(
            doc_id,
            old_date,
            content
        )
        
        assert health.is_stale
        assert health.days_since_update == 40
        assert health.health_score < 100
        assert health.needs_healing
        
        # Check for auto-archive recommendation
        rule_ids = [rule.rule_id for rule in health.recommendations]
        assert "auto_archive_stale" in rule_ids
        
        # Execute auto-healing
        results = await self.healing_engine.auto_heal(doc_id, health)
        
        assert len(results) > 0
        archive_result = next(
            (r for r in results if r.action_taken == HealingAction.AUTO_ARCHIVE),
            None
        )
        assert archive_result is not None
    
    async def test_broken_links_detection_and_notification(self):
        """Test broken link detection and notification."""
        doc_id = "doc-004"
        content = """
        # API Reference
        
        Check out these links:
        - https://api.example.com/v1
        - https://api.example.com/v2
        - https://api.example.com/v3
        - https://deprecated.example.com
        - https://old-service.example.com
        """
        
        # Assess health
        health = self.healing_engine.assess_health(
            doc_id,
            datetime.now(),
            content
        )
        
        # Should detect some potential issues
        assert len(health.issues) > 0
        
        # If broken links exceed threshold, should recommend notification
        if health.broken_links_count > 3:
            rule_ids = [rule.rule_id for rule in health.recommendations]
            assert "notify_broken_links" in rule_ids
    
    async def test_batch_change_detection(self):
        """Test batch change detection across multiple documents."""
        documents = {
            "doc-A": "# Document A\nContent A",
            "doc-B": "# Document B\nContent B",
            "doc-C": "# Document C\nContent C",
        }
        
        # Register initial versions
        for doc_id, content in documents.items():
            self.change_detector.register_document(doc_id, content)
        
        # Modify documents
        updated_documents = {
            "doc-A": "# Document A\nUpdated Content A",
            "doc-B": "# Document B\nContent B",  # No change
            "doc-C": "# Document C\nMajor update to content C with lots of changes",
        }
        
        # Detect batch changes
        result = self.change_detector.detect_batch_changes(updated_documents)
        
        assert result.total_changes == 2  # doc-A and doc-C changed
        assert "modified" in result.changes_by_type
        assert result.changes_by_type["modified"] == 2
    
    async def test_health_report_generation(self):
        """Test health report generation for multiple documents."""
        documents = {
            "doc-fresh": {
                "content": "# Fresh Document\nRecently updated content with good quality.",
                "last_updated": datetime.now() - timedelta(days=1),
                "metadata": {}
            },
            "doc-stale": {
                "content": "# Stale Document\nOld content from 2020.",
                "last_updated": datetime.now() - timedelta(days=100),
                "metadata": {}
            },
            "doc-short": {
                "content": "# Too Short",
                "last_updated": datetime.now() - timedelta(days=5),
                "metadata": {}
            },
        }
        
        # Generate health report
        report = self.healing_engine.get_health_report(documents)
        
        assert report["total_documents"] == 3
        assert report["stale_documents"] >= 1
        assert report["documents_needing_healing"] >= 1
        assert 0 <= report["average_health_score"] <= 100
        assert report["total_issues"] > 0
    
    async def test_sync_schedule_creation(self):
        """Test scheduled sync configuration."""
        schedule = self.sync_engine.create_schedule(
            doc_id="doc-scheduled",
            direction=SyncDirection.BIDIRECTIONAL,
            interval_minutes=60,
            enabled=True
        )
        
        assert schedule.doc_id == "doc-scheduled"
        assert schedule.direction == SyncDirection.BIDIRECTIONAL
        assert schedule.interval_minutes == 60
        assert schedule.enabled
        assert schedule.last_run is None
    
    async def test_healing_history_tracking(self):
        """Test healing operation history tracking."""
        doc_id = "doc-history"
        content = "# Test Document"
        old_date = datetime.now() - timedelta(days=100)
        
        # Assess and heal multiple times
        for i in range(3):
            health = self.healing_engine.assess_health(
                doc_id,
                old_date,
                content + f" v{i}"
            )
            
            await self.healing_engine.auto_heal(doc_id, health)
        
        # Get healing history
        history = self.healing_engine.get_healing_history(doc_id)
        
        assert len(history) >= 3
        
        for result in history:
            assert result.document_id == doc_id
            assert result.healing_id is not None
            assert result.executed_at is not None
            assert result.duration_ms >= 0
    
    async def test_change_history_tracking(self):
        """Test change history tracking."""
        doc_id = "doc-changes"
        
        # Make multiple changes
        versions = [
            "# Version 1",
            "# Version 2\nAdded content",
            "# Version 3\nAdded more content",
        ]
        
        for version in versions:
            change = self.change_detector.detect_changes(doc_id, version)
            assert change is not None
        
        # Get change history
        history = self.change_detector.get_change_history(doc_id)
        
        assert len(history) == len(versions)
        
        # First should be ADD, rest should be MODIFIED
        assert history[0].change_type == ChangeType.ADDED
        for change in history[1:]:
            assert change.change_type == ChangeType.MODIFIED
    
    async def test_empty_sections_detection(self):
        """Test detection of empty sections in documents."""
        doc_id = "doc-empty-sections"
        content = """
        # Main Title
        
        ## Section 1
        
        ## Section 2
        Content here
        
        ## Section 3
        
        ## Section 4
        """
        
        health = self.healing_engine.assess_health(
            doc_id,
            datetime.now(),
            content
        )
        
        # Should detect empty sections
        empty_section_issues = [
            issue for issue in health.issues
            if "empty section" in issue.lower()
        ]
        
        assert len(empty_section_issues) > 0
    
    async def test_document_rename_tracking(self):
        """Test document rename tracking."""
        old_id = "doc-old-name"
        new_id = "doc-new-name"
        content = "# Renamed Document"
        
        # Register original
        self.change_detector.register_document(old_id, content)
        
        # Rename
        change = self.change_detector.detect_rename(old_id, new_id)
        
        assert change is not None
        assert change.change_type == ChangeType.RENAMED
        assert change.metadata["old_id"] == old_id
        assert change.metadata["new_id"] == new_id
    
    async def test_document_deletion_tracking(self):
        """Test document deletion tracking."""
        doc_id = "doc-to-delete"
        content = "# Document to Delete"
        
        # Register
        self.change_detector.register_document(doc_id, content)
        
        # Delete
        change = self.change_detector.detect_deletion(doc_id)
        
        assert change is not None
        assert change.change_type == ChangeType.DELETED
        assert change.severity == ChangeSeverity.MAJOR
    
    async def test_severity_classification(self):
        """Test change severity classification."""
        doc_id = "doc-severity"
        
        # Original content (100 lines simulated)
        original = "# Document\n" + "\n".join([f"Line {i}" for i in range(100)])
        self.change_detector.register_document(doc_id, original)
        
        # Minor change (< 5%)
        minor_change = original + "\nOne new line"
        change_minor = self.change_detector.detect_changes(doc_id, minor_change)
        assert change_minor.severity == ChangeSeverity.MINOR
        
        # Register again for next test
        self.change_detector.register_document(doc_id, original)
        
        # Major change (> 20%)
        major_change = "# Document\n" + "\n".join([f"Changed Line {i}" for i in range(30)])
        change_major = self.change_detector.detect_changes(doc_id, major_change)
        assert change_major.severity in [ChangeSeverity.MAJOR, ChangeSeverity.CRITICAL]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

