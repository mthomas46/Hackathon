"""
Unit tests for Workflow F: User Extraction from Documents

Tests user extraction logic from GitHub PRs, Jira tickets, and Confluence documents.
"""

import pytest
from typing import Dict, Any
import sys
import os

# Add services directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../services')))

try:
    from services.project_planning_service.domain.services.workflow_f_user_intelligence import (
        UserIntelligenceWorkflow,
        UserExtraction,
        WorkflowFResult
    )
except ImportError:
    # Try alternative import path
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "workflow_f_user_intelligence",
        os.path.join(os.path.dirname(__file__), "../../../services/project-planning-service/domain/services/workflow_f_user_intelligence.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    UserIntelligenceWorkflow = module.UserIntelligenceWorkflow
    UserExtraction = module.UserExtraction
    WorkflowFResult = module.WorkflowFResult


class TestUserExtractionFromGitHubPR:
    """Test user extraction from GitHub Pull Requests."""
    
    def test_extract_author_from_pr(self, sample_github_pr):
        """Test extracting PR author."""
        workflow = UserIntelligenceWorkflow()
        
        workflow.extract_user_from_github_pr(sample_github_pr)
        
        # Check author was extracted
        assert "marcus.johnson" in workflow.user_extractions
        user = workflow.user_extractions["marcus.johnson"]
        assert user.username == "marcus.johnson"
        assert user.display_name == "Marcus Johnson"
        assert len(user.documents_created) == 1
        assert "github_pr_PR-123" in user.documents_created
    
    def test_extract_mentions_from_pr_description(self, sample_github_pr):
        """Test extracting @mentions from PR description."""
        workflow = UserIntelligenceWorkflow()
        
        workflow.extract_user_from_github_pr(sample_github_pr)
        
        # Check mentioned users were extracted
        assert "john.doe" in workflow.user_extractions
        assert "sarah.chen" in workflow.user_extractions
        
        # Check they're marked as commented (mentioned)
        john = workflow.user_extractions["john.doe"]
        assert "github_pr_PR-123" in john.documents_commented
        
        sarah = workflow.user_extractions["sarah.chen"]
        assert "github_pr_PR-123" in sarah.documents_commented
    
    def test_extract_topics_from_pr_tech_stack(self, sample_github_pr):
        """Test extracting topics from PR tech stack."""
        workflow = UserIntelligenceWorkflow()
        
        workflow.extract_user_from_github_pr(sample_github_pr)
        
        # Check author has topics from tech stack
        author = workflow.user_extractions["marcus.johnson"]
        assert "Python" in author.topics
        assert "FastAPI" in author.topics
        assert "PostgreSQL" in author.topics
    
    def test_pr_without_mentions(self, sample_github_pr_no_mentions):
        """Test PR without any @mentions."""
        workflow = UserIntelligenceWorkflow()
        
        workflow.extract_user_from_github_pr(sample_github_pr_no_mentions)
        
        # Only author should be extracted
        assert len(workflow.user_extractions) == 1
        assert "emily.wu" in workflow.user_extractions
        
        user = workflow.user_extractions["emily.wu"]
        assert len(user.documents_created) == 1
        assert len(user.documents_commented) == 0
    
    def test_multiple_prs_same_author(self, sample_github_pr):
        """Test that same author across multiple PRs is deduplicated."""
        workflow = UserIntelligenceWorkflow()
        
        # Extract from same PR twice (simulating similar PRs)
        workflow.extract_user_from_github_pr(sample_github_pr)
        
        pr2 = sample_github_pr.copy()
        pr2["pr_number"] = "PR-456"
        workflow.extract_user_from_github_pr(pr2)
        
        # Should still be one user, but with multiple documents
        assert len([u for u in workflow.user_extractions.keys() if u == "marcus.johnson"]) == 1
        
        author = workflow.user_extractions["marcus.johnson"]
        assert len(author.documents_created) == 2
        assert "github_pr_PR-123" in author.documents_created
        assert "github_pr_PR-456" in author.documents_created


class TestUserExtractionFromJiraTicket:
    """Test user extraction from Jira tickets."""
    
    def test_extract_assignee_from_ticket(self, sample_jira_ticket):
        """Test extracting ticket assignee."""
        workflow = UserIntelligenceWorkflow()
        
        workflow.extract_user_from_jira_ticket(sample_jira_ticket)
        
        # Check assignee was extracted
        assert "priya.patel" in workflow.user_extractions
        user = workflow.user_extractions["priya.patel"]
        assert user.username == "priya.patel"
        assert user.display_name == "Priya Patel"
        assert len(user.documents_created) == 1
        assert "jira_PROJ-789" in user.documents_created
    
    def test_extract_mentions_from_ticket_description(self, sample_jira_ticket):
        """Test extracting @mentions from ticket description."""
        workflow = UserIntelligenceWorkflow()
        
        workflow.extract_user_from_jira_ticket(sample_jira_ticket)
        
        # Check mentioned users were extracted
        assert "david.kim" in workflow.user_extractions
        assert "alex.rivera" in workflow.user_extractions
        
        # Check they're marked as commented
        david = workflow.user_extractions["david.kim"]
        assert "jira_PROJ-789" in david.documents_commented
    
    def test_extract_topics_from_ticket_tech_stack(self, sample_jira_ticket):
        """Test extracting topics from ticket tech stack."""
        workflow = UserIntelligenceWorkflow()
        
        workflow.extract_user_from_jira_ticket(sample_jira_ticket)
        
        # Check assignee has topics from tech stack
        assignee = workflow.user_extractions["priya.patel"]
        assert "React" in assignee.topics
        assert "TypeScript" in assignee.topics
        assert "Redux" in assignee.topics
    
    def test_extract_skill_from_ticket_summary(self, sample_jira_ticket):
        """Test extracting skill indicator from ticket summary."""
        workflow = UserIntelligenceWorkflow()
        
        workflow.extract_user_from_jira_ticket(sample_jira_ticket)
        
        # Check assignee has skill from summary
        assignee = workflow.user_extractions["priya.patel"]
        # Summary is used as skill indicator
        assert len(assignee.skills) > 0


class TestUserExtractionFromConfluenceDoc:
    """Test user extraction from Confluence documents."""
    
    def test_extract_author_from_doc(self, sample_confluence_doc):
        """Test extracting document author."""
        workflow = UserIntelligenceWorkflow()
        
        workflow.extract_user_from_confluence_doc(sample_confluence_doc)
        
        # Check author was extracted
        assert "jordan.lee" in workflow.user_extractions
        user = workflow.user_extractions["jordan.lee"]
        assert user.username == "jordan.lee"
        assert user.display_name == "Jordan Lee"
        assert len(user.documents_created) == 1
        assert "confluence_CONF-101" in user.documents_created
    
    def test_extract_mentions_from_doc_content(self, sample_confluence_doc):
        """Test extracting @mentions from document content."""
        workflow = UserIntelligenceWorkflow()
        
        workflow.extract_user_from_confluence_doc(sample_confluence_doc)
        
        # Check mentioned users were extracted
        assert "sarah.chen" in workflow.user_extractions
        assert "marcus.johnson" in workflow.user_extractions
        
        # Check they're marked as commented
        sarah = workflow.user_extractions["sarah.chen"]
        assert "confluence_CONF-101" in sarah.documents_commented
    
    def test_extract_topics_from_doc_tags(self, sample_confluence_doc):
        """Test extracting topics from document tags."""
        workflow = UserIntelligenceWorkflow()
        
        workflow.extract_user_from_confluence_doc(sample_confluence_doc)
        
        # Check author has topics from tags
        author = workflow.user_extractions["jordan.lee"]
        assert "Architecture" in author.topics
        assert "Backend" in author.topics
        assert "Python" in author.topics
        assert "Microservices" in author.topics


class TestMentionExtraction:
    """Test @mention pattern extraction."""
    
    def test_extract_simple_mention(self):
        """Test extracting simple @username."""
        workflow = UserIntelligenceWorkflow()
        
        text = "Please review this @john.doe"
        mentions = workflow._extract_mentions(text)
        
        assert "john.doe" in mentions
    
    def test_extract_multiple_mentions(self):
        """Test extracting multiple @mentions."""
        workflow = UserIntelligenceWorkflow()
        
        text = "@alice.cooper and @bob.martin please review"
        mentions = workflow._extract_mentions(text)
        
        assert len(mentions) == 2
        assert "alice.cooper" in mentions
        assert "bob.martin" in mentions
    
    def test_extract_mentions_with_underscores(self):
        """Test extracting @mentions with underscores."""
        workflow = UserIntelligenceWorkflow()
        
        text = "Contact @sarah_chen for questions"
        mentions = workflow._extract_mentions(text)
        
        assert "sarah_chen" in mentions
    
    def test_deduplicate_mentions(self):
        """Test that duplicate mentions are deduplicated."""
        workflow = UserIntelligenceWorkflow()
        
        text = "@john.doe please review. @john.doe has the context"
        mentions = workflow._extract_mentions(text)
        
        # Should only appear once
        assert mentions.count("john.doe") == 1
    
    def test_empty_text(self):
        """Test extracting from empty text."""
        workflow = UserIntelligenceWorkflow()
        
        mentions = workflow._extract_mentions("")
        assert len(mentions) == 0
    
    def test_no_mentions(self):
        """Test text without mentions."""
        workflow = UserIntelligenceWorkflow()
        
        text = "This text has no mentions at all"
        mentions = workflow._extract_mentions(text)
        
        assert len(mentions) == 0


class TestUserDeduplication:
    """Test user deduplication and aggregation."""
    
    def test_same_user_multiple_documents_created(self):
        """Test same user creating multiple documents."""
        workflow = UserIntelligenceWorkflow()
        
        # Add user to two different documents as creator
        workflow._add_or_update_user(
            username="alice.cooper",
            document_id="doc1",
            relationship="created",
            topics=["Python"]
        )
        
        workflow._add_or_update_user(
            username="alice.cooper",
            document_id="doc2",
            relationship="created",
            topics=["JavaScript"]
        )
        
        # Should be one user with multiple documents
        assert len(workflow.user_extractions) == 1
        user = workflow.user_extractions["alice.cooper"]
        
        assert len(user.documents_created) == 2
        assert "doc1" in user.documents_created
        assert "doc2" in user.documents_created
    
    def test_same_user_different_relationships(self):
        """Test same user with different document relationships."""
        workflow = UserIntelligenceWorkflow()
        
        # Add user with different relationships
        workflow._add_or_update_user(
            username="bob.martin",
            document_id="doc1",
            relationship="created"
        )
        
        workflow._add_or_update_user(
            username="bob.martin",
            document_id="doc2",
            relationship="commented"
        )
        
        workflow._add_or_update_user(
            username="bob.martin",
            document_id="doc3",
            relationship="updated"
        )
        
        # Should be one user with documents in each category
        user = workflow.user_extractions["bob.martin"]
        assert len(user.documents_created) == 1
        assert len(user.documents_commented) == 1
        assert len(user.documents_updated) == 1
        assert user.total_interactions == 3
    
    def test_topic_aggregation(self):
        """Test that topics are aggregated without duplication."""
        workflow = UserIntelligenceWorkflow()
        
        # Add user with overlapping topics
        workflow._add_or_update_user(
            username="charlie.davis",
            document_id="doc1",
            relationship="created",
            topics=["Python", "Backend"]
        )
        
        workflow._add_or_update_user(
            username="charlie.davis",
            document_id="doc2",
            relationship="created",
            topics=["Python", "APIs"]  # Python is duplicate
        )
        
        # Topics should be deduplicated
        user = workflow.user_extractions["charlie.davis"]
        assert user.topics.count("Python") == 1
        assert "Backend" in user.topics
        assert "APIs" in user.topics
    
    def test_display_name_formatting(self):
        """Test display name formatting from username."""
        workflow = UserIntelligenceWorkflow()
        
        # Test with dot separator
        workflow._add_or_update_user(
            username="john.doe",
            document_id="doc1",
            relationship="created"
        )
        user1 = workflow.user_extractions["john.doe"]
        assert user1.display_name == "John Doe"
        
        # Test with underscore separator
        workflow._add_or_update_user(
            username="jane_smith",
            document_id="doc2",
            relationship="created"
        )
        user2 = workflow.user_extractions["jane_smith"]
        assert user2.display_name == "Jane Smith"


class TestWorkflowExecution:
    """Test full workflow execution."""
    
    def test_execute_with_mixed_documents(self, sample_documents_batch):
        """Test executing workflow with mix of document types."""
        workflow = UserIntelligenceWorkflow()
        
        jira_tickets = [d["data"] for d in sample_documents_batch if d["type"] == "jira"]
        github_prs = [d["data"] for d in sample_documents_batch if d["type"] == "github_pr"]
        confluence_docs = [d["data"] for d in sample_documents_batch if d["type"] == "confluence"]
        
        result = workflow.execute(
            jira_tickets=jira_tickets,
            confluence_docs=confluence_docs,
            github_prs=github_prs
        )
        
        # Should have extracted multiple users
        assert result.total_users_extracted > 0
        assert len(result.extracted_users) > 0
        assert result.total_documents_analyzed == len(sample_documents_batch)
        
        # Should have built relationships
        assert len(result.collaboration_graph) > 0
        assert len(result.expertise_map) > 0
    
    def test_execute_calculates_execution_time(self):
        """Test that execution time is calculated."""
        workflow = UserIntelligenceWorkflow()
        
        result = workflow.execute(
            jira_tickets=[],
            confluence_docs=[],
            github_prs=[]
        )
        
        # Should have positive execution time
        assert result.execution_time >= 0


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_document_lists(self):
        """Test execution with empty document lists."""
        workflow = UserIntelligenceWorkflow()
        
        result = workflow.execute(
            jira_tickets=[],
            confluence_docs=[],
            github_prs=[]
        )
        
        assert result.total_users_extracted == 0
        assert len(result.extracted_users) == 0
        assert result.total_documents_analyzed == 0
    
    def test_document_missing_author(self):
        """Test handling document without author."""
        workflow = UserIntelligenceWorkflow()
        
        pr = {
            "pr_number": "PR-999",
            "title": "Test PR",
            "description": "Test description",
            # author missing
            "tech_stack": ["Python"]
        }
        
        # Should not crash
        workflow.extract_user_from_github_pr(pr)
        
        # Should not have created a user
        assert "" not in workflow.user_extractions
    
    def test_document_with_none_values(self):
        """Test handling document with None values."""
        workflow = UserIntelligenceWorkflow()
        
        ticket = {
            "key": "PROJ-999",
            "summary": "Test ticket",
            "description": None,  # None instead of string
            "assignee": "test.user",
            "tech_stack": None  # None instead of list
        }
        
        # Should not crash
        workflow.extract_user_from_jira_ticket(ticket)
        
        # Should have extracted assignee
        assert "test.user" in workflow.user_extractions
    
    def test_duplicate_document_ids(self):
        """Test handling duplicate document IDs."""
        workflow = UserIntelligenceWorkflow()
        
        # Add same document twice
        workflow._add_or_update_user(
            username="test.user",
            document_id="doc1",
            relationship="created"
        )
        
        workflow._add_or_update_user(
            username="test.user",
            document_id="doc1",  # Same document ID
            relationship="created"
        )
        
        # Should not have duplicate document IDs
        user = workflow.user_extractions["test.user"]
        assert user.documents_created.count("doc1") == 1

