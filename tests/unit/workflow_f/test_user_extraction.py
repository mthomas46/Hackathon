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
        # Phase 1.5: Assignees are tracked in jira_tickets_assigned, not documents_created
        assert len(user.jira_tickets_assigned) == 1
        assert "jira_PROJ-789" in user.jira_tickets_assigned
    
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


# ⭐ NEW: Phase 1.4 Enhancement Tests
class TestGitHubPREnhancedExtraction:
    """Test Phase 1.4 enhancements: Multi-role extraction, code metrics, review quality."""
    
    def test_extract_assignees(self):
        """Test extracting PR assignees."""
        workflow = UserIntelligenceWorkflow()
        
        pr = {
            "pr_number": "PR-456",
            "title": "Add authentication service",
            "author": "alice.dev",
            "assignees": ["bob.engineer", "carol.tech"],
            "tech_stack": ["Python", "OAuth"],
            "description": "Implementing OAuth2 authentication"
        }
        
        workflow.extract_user_from_github_pr(pr)
        
        # Check assignees were extracted
        assert "bob.engineer" in workflow.user_extractions
        assert "carol.tech" in workflow.user_extractions
        
        # Check role tracking
        bob = workflow.user_extractions["bob.engineer"]
        assert "github_pr_PR-456" in bob.pull_requests_assigned
        
        carol = workflow.user_extractions["carol.tech"]
        assert "github_pr_PR-456" in carol.pull_requests_assigned
    
    def test_extract_reviewers_from_reviews_array(self):
        """Test extracting reviewers from reviews array."""
        workflow = UserIntelligenceWorkflow()
        
        pr = {
            "pr_number": "PR-789",
            "title": "Database migration scripts",
            "author": "alice.dev",
            "reviews": [
                {
                    "user": "reviewer.one",
                    "state": "APPROVED",
                    "body": "LGTM! Great work on the migration scripts. Consider adding rollback procedures."
                },
                {
                    "reviewer": "reviewer.two",
                    "review_state": "CHANGES_REQUESTED",
                    "comment": "Please add proper error handling in migration step 3. Also, consider using transactions for atomicity. The logic in migration_helper.py could be refactored for better readability."
                }
            ],
            "tech_stack": ["PostgreSQL", "Python"],
            "description": "Adding DB migrations"
        }
        
        workflow.extract_user_from_github_pr(pr)
        
        # Check reviewers were extracted
        assert "reviewer.one" in workflow.user_extractions
        assert "reviewer.two" in workflow.user_extractions
        
        # Check role tracking
        rev1 = workflow.user_extractions["reviewer.one"]
        assert "github_pr_PR-789" in rev1.pull_requests_reviewed
        
        rev2 = workflow.user_extractions["reviewer.two"]
        assert "github_pr_PR-789" in rev2.pull_requests_reviewed
        
        # Check approval rate
        assert rev1.approval_rate == 1.0  # Approved
        assert rev2.approval_rate == 0.0  # Requested changes
    
    def test_extract_merger(self):
        """Test extracting PR merger."""
        workflow = UserIntelligenceWorkflow()
        
        pr = {
            "pr_number": "PR-555",
            "title": "Fix bug in authentication",
            "author": "alice.dev",
            "merged_by": "senior.engineer",
            "tech_stack": ["Python"],
            "description": "Bug fix"
        }
        
        workflow.extract_user_from_github_pr(pr)
        
        # Check merger was extracted
        assert "senior.engineer" in workflow.user_extractions
        
        # Check role tracking and authority
        merger = workflow.user_extractions["senior.engineer"]
        assert "github_pr_PR-555" in merger.pull_requests_merged
        assert merger.merge_authority == True
    
    def test_extract_commit_authors(self):
        """Test extracting commit authors from commits array."""
        workflow = UserIntelligenceWorkflow()
        
        pr = {
            "pr_number": "PR-321",
            "title": "Add API endpoints",
            "author": "alice.dev",
            "commits": [
                {"author": "alice.dev", "message": "Initial commit"},
                {"author": "bob.pair", "message": "Add tests"},
                {"committer": "alice.dev", "message": "Fix linting"}
            ],
            "tech_stack": ["Python", "FastAPI"],
            "description": "New endpoints"
        }
        
        workflow.extract_user_from_github_pr(pr)
        
        # Check commit authors were extracted
        assert "alice.dev" in workflow.user_extractions
        assert "bob.pair" in workflow.user_extractions
        
        # Check role tracking
        alice = workflow.user_extractions["alice.dev"]
        assert "github_pr_PR-321" in alice.pull_requests_authored
        assert "github_pr_PR-321" in alice.pull_requests_committed
        
        bob = workflow.user_extractions["bob.pair"]
        assert "github_pr_PR-321" in bob.pull_requests_committed
    
    def test_extract_commenters(self):
        """Test extracting commenters from comments array."""
        workflow = UserIntelligenceWorkflow()
        
        pr = {
            "pr_number": "PR-111",
            "title": "Update documentation",
            "author": "alice.dev",
            "comments": [
                {"user": "doc.reviewer", "body": "Great docs!"},
                {"author": "tech.writer", "body": "Please add examples"}
            ],
            "tech_stack": ["Markdown"],
            "description": "Doc updates"
        }
        
        workflow.extract_user_from_github_pr(pr)
        
        # Check commenters were extracted
        assert "doc.reviewer" in workflow.user_extractions
        assert "tech.writer" in workflow.user_extractions
        
        # Check role tracking
        reviewer = workflow.user_extractions["doc.reviewer"]
        assert "github_pr_PR-111" in reviewer.documents_commented
        
        writer = workflow.user_extractions["tech.writer"]
        assert "github_pr_PR-111" in writer.documents_commented
    
    def test_code_metrics_calculation(self):
        """Test code contribution metrics calculation."""
        workflow = UserIntelligenceWorkflow()
        
        pr = {
            "pr_number": "PR-888",
            "title": "Implement payment service",
            "author": "payment.dev",
            "additions": 350,
            "lines_added": 350,
            "deletions": 150,
            "lines_deleted": 150,
            "files_changed": [
                "/backend/payment/service.py",
                "/backend/payment/models.py",
                "/backend/payment/api.py",
                "/tests/test_payment.py"
            ],
            "commits": [
                {"author": "payment.dev"},
                {"author": "payment.dev"},
                {"author": "payment.dev"}
            ],
            "tech_stack": ["Python"],
            "description": "Payment integration"
        }
        
        workflow.extract_user_from_github_pr(pr)
        
        # Check code metrics were calculated
        user = workflow.user_extractions["payment.dev"]
        assert user.code_metrics is not None
        assert user.code_metrics["lines_added"] == 350
        assert user.code_metrics["lines_deleted"] == 150
        assert user.code_metrics["commit_count"] == 3
        assert len(user.code_metrics["files_touched"]) == 4
        assert user.code_metrics["total_prs"] == 1
        
        # Check avg PR size calculation
        expected_avg = (350 + 150) / 1
        assert user.code_metrics["avg_pr_size"] == expected_avg
    
    def test_technology_inference_from_file_paths(self):
        """Test inferring technologies from file paths."""
        workflow = UserIntelligenceWorkflow()
        
        pr = {
            "pr_number": "PR-999",
            "title": "Full stack feature",
            "author": "fullstack.dev",
            "files_changed": [
                "/backend/api/service.py",
                "/frontend/components/Button.tsx",
                "/frontend/styles/main.scss",
                "/docker/Dockerfile",
                "/infrastructure/terraform/main.tf",
                "/tests/__tests__/service.test.js"
            ],
            "additions": 500,
            "commits": [{"author": "fullstack.dev"}],
            "tech_stack": [],
            "description": "New feature"
        }
        
        workflow.extract_user_from_github_pr(pr)
        
        # Check technologies were inferred
        user = workflow.user_extractions["fullstack.dev"]
        assert "Python" in user.technologies
        assert "React" in user.technologies  # .tsx
        assert "TypeScript" in user.technologies  # .tsx
        assert "SCSS" in user.technologies
        assert "Docker" in user.technologies
        assert "Terraform" in user.technologies
        assert "Backend" in user.technologies  # /backend/ path
        assert "Frontend" in user.technologies  # /frontend/ path
        assert "Testing" in user.technologies  # __tests__
    
    def test_review_quality_scoring_thorough_review(self):
        """Test review quality scoring for thorough reviews."""
        workflow = UserIntelligenceWorkflow()
        
        pr = {
            "pr_number": "PR-777",
            "title": "Security improvements",
            "author": "alice.dev",
            "reviews": [
                {
                    "user": "senior.reviewer",
                    "state": "CHANGES_REQUESTED",
                    "body": """Great work on improving security! However, I have some suggestions:
                    
                    1. Consider using `secrets` module instead of `random` for token generation:
                    ```python
                    import secrets
                    token = secrets.token_urlsafe(32)
                    ```
                    
                    2. The SQL query in auth_service.py could be vulnerable to injection. 
                       Please use parameterized queries.
                    
                    3. You might want to add rate limiting to prevent brute force attacks.
                    
                    4. Consider adding unit tests for the new auth flows.
                    
                    Overall the architecture looks solid, but please fix these security issues before merging."""
                }
            ],
            "tech_stack": ["Python"],
            "description": "Auth improvements"
        }
        
        workflow.extract_user_from_github_pr(pr)
        
        # Check review quality score
        reviewer = workflow.user_extractions["senior.reviewer"]
        # Thorough review: long comment (>500 chars), code snippets, actionable keywords, changes requested
        # Should score high (close to 1.0)
        assert reviewer.review_quality_score > 0.7
        assert reviewer.review_quality_score <= 1.0
    
    def test_review_quality_scoring_superficial_review(self):
        """Test review quality scoring for superficial reviews."""
        workflow = UserIntelligenceWorkflow()
        
        pr = {
            "pr_number": "PR-666",
            "title": "Minor fix",
            "author": "alice.dev",
            "reviews": [
                {
                    "user": "quick.reviewer",
                    "state": "APPROVED",
                    "body": "LGTM"
                }
            ],
            "tech_stack": ["Python"],
            "description": "Quick fix"
        }
        
        workflow.extract_user_from_github_pr(pr)
        
        # Check review quality score
        reviewer = workflow.user_extractions["quick.reviewer"]
        # Superficial review: short comment, no code snippets, no actionable feedback
        # Should score low (< 0.3)
        assert reviewer.review_quality_score < 0.3
        assert reviewer.review_quality_score >= 0.0
    
    def test_multiple_prs_aggregate_metrics(self):
        """Test that code metrics aggregate correctly across multiple PRs."""
        workflow = UserIntelligenceWorkflow()
        
        pr1 = {
            "pr_number": "PR-001",
            "title": "Feature A",
            "author": "prolific.dev",
            "additions": 200,
            "deletions": 50,
            "files_changed": ["/src/feature_a.py"],
            "commits": [{"author": "prolific.dev"}],
            "tech_stack": [],
            "description": "Feature A"
        }
        
        pr2 = {
            "pr_number": "PR-002",
            "title": "Feature B",
            "author": "prolific.dev",
            "additions": 300,
            "deletions": 100,
            "files_changed": ["/src/feature_b.py", "/tests/test_b.py"],
            "commits": [{"author": "prolific.dev"}, {"author": "prolific.dev"}],
            "tech_stack": [],
            "description": "Feature B"
        }
        
        workflow.extract_user_from_github_pr(pr1)
        workflow.extract_user_from_github_pr(pr2)
        
        # Check aggregated metrics
        user = workflow.user_extractions["prolific.dev"]
        assert user.code_metrics["lines_added"] == 500  # 200 + 300
        assert user.code_metrics["lines_deleted"] == 150  # 50 + 100
        assert user.code_metrics["commit_count"] == 3  # 1 + 2
        assert user.code_metrics["total_prs"] == 2
        
        # Check avg PR size
        expected_avg = (500 + 150) / 2  # 325
        assert user.code_metrics["avg_pr_size"] == expected_avg
        
        # Check PR tracking
        assert len(user.pull_requests_authored) == 2
        assert "github_pr_PR-001" in user.pull_requests_authored
        assert "github_pr_PR-002" in user.pull_requests_authored
    
    def test_all_roles_in_single_pr(self):
        """Test extracting all possible roles from a single comprehensive PR."""
        workflow = UserIntelligenceWorkflow()
        
        pr = {
            "pr_number": "PR-MEGA",
            "title": "Major refactoring",
            "author": "lead.dev",
            "assignees": ["backend.specialist", "frontend.specialist"],
            "requested_reviewers": ["senior.architect"],
            "reviews": [
                {
                    "user": "senior.architect",
                    "state": "APPROVED",
                    "body": "Excellent refactoring! Clean code, good tests."
                },
                {
                    "reviewer": "security.expert",
                    "review_state": "APPROVED",
                    "comment": "Security looks good"
                }
            ],
            "merged_by": "tech.lead",
            "commits": [
                {"author": "lead.dev"},
                {"author": "pair.programmer"},
                {"author": "lead.dev"}
            ],
            "comments": [
                {"user": "qa.tester", "body": "Tested on staging, works great!"},
                {"author": "product.manager", "body": "This meets the requirements"}
            ],
            "additions": 1000,
            "deletions": 500,
            "files_changed": [
                "/backend/core/refactored_service.py",
                "/frontend/components/NewUI.tsx",
                "/tests/integration/test_refactor.py"
            ],
            "tech_stack": ["Python", "React"],
            "description": "Major refactoring @documentation.writer please update docs"
        }
        
        workflow.extract_user_from_github_pr(pr)
        
        # Verify all role types were extracted
        # 1. Author
        assert "lead.dev" in workflow.user_extractions
        assert "github_pr_PR-MEGA" in workflow.user_extractions["lead.dev"].pull_requests_authored
        
        # 2. Assignees
        assert "backend.specialist" in workflow.user_extractions
        assert "frontend.specialist" in workflow.user_extractions
        assert "github_pr_PR-MEGA" in workflow.user_extractions["backend.specialist"].pull_requests_assigned
        
        # 3. Reviewers
        assert "senior.architect" in workflow.user_extractions
        assert "security.expert" in workflow.user_extractions
        assert "github_pr_PR-MEGA" in workflow.user_extractions["senior.architect"].pull_requests_reviewed
        
        # 4. Merger
        assert "tech.lead" in workflow.user_extractions
        assert "github_pr_PR-MEGA" in workflow.user_extractions["tech.lead"].pull_requests_merged
        assert workflow.user_extractions["tech.lead"].merge_authority == True
        
        # 5. Commit authors
        assert "pair.programmer" in workflow.user_extractions
        assert "github_pr_PR-MEGA" in workflow.user_extractions["pair.programmer"].pull_requests_committed
        
        # 6. Commenters
        assert "qa.tester" in workflow.user_extractions
        assert "product.manager" in workflow.user_extractions
        assert "github_pr_PR-MEGA" in workflow.user_extractions["qa.tester"].documents_commented
        
        # 7. Mentioned users
        assert "documentation.writer" in workflow.user_extractions
        assert "github_pr_PR-MEGA" in workflow.user_extractions["documentation.writer"].documents_commented
        
        # Total: Should have extracted 10 unique users
        # (lead.dev, 2 assignees, 2 reviewers, merger, pair programmer, 2 commenters, 1 mentioned)
        assert len(workflow.user_extractions) == 10


class TestReviewQualityScoring:
    """Test the review quality scoring algorithm."""
    
    def test_empty_comment_approved(self):
        """Test scoring for empty comment with approval."""
        workflow = UserIntelligenceWorkflow()
        score = workflow._calculate_review_quality("", "APPROVED")
        assert score == 0.2  # Minimal score for approved with no comment
    
    def test_empty_comment_not_approved(self):
        """Test scoring for empty comment without approval."""
        workflow = UserIntelligenceWorkflow()
        score = workflow._calculate_review_quality("", "COMMENTED")
        assert score == 0.1  # Minimal score
    
    def test_short_comment(self):
        """Test scoring for short comment."""
        workflow = UserIntelligenceWorkflow()
        score = workflow._calculate_review_quality("Looks good to me", "APPROVED")
        # Short comment (<50 chars) + approved
        assert 0.1 <= score <= 0.3
    
    def test_medium_comment_with_keywords(self):
        """Test scoring for medium comment with actionable keywords."""
        workflow = UserIntelligenceWorkflow()
        comment = "Good work! Please consider refactoring the error handling and add more tests."
        score = workflow._calculate_review_quality(comment, "CHANGES_REQUESTED")
        # Medium length (>50, <200) + keywords (consider, refactor, add) + changes requested
        assert 0.4 <= score <= 0.7
    
    def test_long_comment_with_code(self):
        """Test scoring for long comment with code snippets."""
        workflow = UserIntelligenceWorkflow()
        comment = """Great implementation! A few suggestions:
        
        1. Consider using a context manager: `with open(file) as f:`
        2. The error handling could be improved
        3. Please add docstrings
        
        Also, you might want to optimize the query performance."""
        score = workflow._calculate_review_quality(comment, "CHANGES_REQUESTED")
        # Long (>200 chars) + code snippets + keywords + changes requested
        assert 0.6 <= score <= 1.0
    
    def test_score_capped_at_one(self):
        """Test that score never exceeds 1.0."""
        workflow = UserIntelligenceWorkflow()
        # Very long, detailed comment with everything
        comment = """Excellent work! Here are my suggestions:
        
        ``` python
        def improved_function():
            # Consider this refactoring
            # Please optimize this
            # You should add error handling
            # Fix the issue here
            # Improve the performance
            pass
        ```
        
        Additional recommendations: refactor, optimize, consider, improve, fix, suggest
        """ * 10  # Make it extremely long
        
        score = workflow._calculate_review_quality(comment, "CHANGES_REQUESTED")
        assert score <= 1.0
        assert score >= 0.0


class TestTechnologyInference:
    """Test technology inference from file paths."""
    
    def test_python_files(self):
        """Test inferring Python from .py files."""
        workflow = UserIntelligenceWorkflow()
        files = ["/src/service.py", "/backend/api.py"]
        technologies = workflow._infer_technologies_from_files(files)
        assert "Python" in technologies
        assert "Backend" in technologies
    
    def test_javascript_react_files(self):
        """Test inferring JavaScript/React from .js/.jsx files."""
        workflow = UserIntelligenceWorkflow()
        files = ["/frontend/app.js", "/components/Button.jsx"]
        technologies = workflow._infer_technologies_from_files(files)
        assert "JavaScript" in technologies
        assert "React" in technologies
        assert "Frontend" in technologies
    
    def test_typescript_react_files(self):
        """Test inferring TypeScript/React from .ts/.tsx files."""
        workflow = UserIntelligenceWorkflow()
        files = ["/src/index.ts", "/components/Card.tsx"]
        technologies = workflow._infer_technologies_from_files(files)
        assert "TypeScript" in technologies
        assert "React" in technologies
    
    def test_docker_files(self):
        """Test inferring Docker from Docker files."""
        workflow = UserIntelligenceWorkflow()
        files = ["/docker/Dockerfile", "/docker-compose.yml"]
        technologies = workflow._infer_technologies_from_files(files)
        assert "Docker" in technologies
        assert "YAML" in technologies
    
    def test_infrastructure_files(self):
        """Test inferring infrastructure tech from paths."""
        workflow = UserIntelligenceWorkflow()
        files = [
            "/terraform/main.tf",
            "/k8s/deployment.yaml",
            "/ci/pipeline.yml"
        ]
        technologies = workflow._infer_technologies_from_files(files)
        assert "Terraform" in technologies
        assert "Kubernetes" in technologies
        assert "CI/CD" in technologies
    
    def test_test_files(self):
        """Test inferring Testing from test paths."""
        workflow = UserIntelligenceWorkflow()
        files = [
            "/tests/test_service.py",
            "/__tests__/component.test.js",
            "/backend/service.spec.ts"
        ]
        technologies = workflow._infer_technologies_from_files(files)
        assert "Testing" in technologies
        assert "Python" in technologies
        assert "JavaScript" in technologies
        assert "TypeScript" in technologies
    
    def test_file_dict_format(self):
        """Test handling file objects with dict format."""
        workflow = UserIntelligenceWorkflow()
        files = [
            {"filename": "/src/app.py"},
            {"path": "/frontend/index.jsx"},
            {"name": "/docker/Dockerfile"}
        ]
        technologies = workflow._infer_technologies_from_files(files)
        assert "Python" in technologies
        assert "React" in technologies
        assert "Docker" in technologies
    
    def test_empty_files_list(self):
        """Test handling empty files list."""
        workflow = UserIntelligenceWorkflow()
        technologies = workflow._infer_technologies_from_files([])
        assert technologies == []
    
    def test_technologies_deduplicated(self):
        """Test that technologies are deduplicated."""
        workflow = UserIntelligenceWorkflow()
        files = [
            "/src/app.py",
            "/backend/service.py",
            "/api/endpoints.py"
        ]
        technologies = workflow._infer_technologies_from_files(files)
        # Python should appear only once
        assert technologies.count("Python") == 1
        assert technologies.count("Backend") == 1


# ⭐ NEW: Phase 1.5 Enhancement Tests
class TestJiraTicketEnhancedExtraction:
    """Test Phase 1.5 enhancements: Multi-role extraction, work metrics, domain expertise."""
    
    def test_extract_reporter(self):
        """Test extracting ticket reporter."""
        workflow = UserIntelligenceWorkflow()
        
        ticket = {
            "key": "PROJ-123",
            "summary": "Fix authentication bug",
            "reporter": "qa.tester",
            "tech_stack": ["Python", "Auth"],
            "description": "Found a critical bug in auth"
        }
        
        workflow.extract_user_from_jira_ticket(ticket)
        
        # Check reporter was extracted
        assert "qa.tester" in workflow.user_extractions
        user = workflow.user_extractions["qa.tester"]
        assert "jira_PROJ-123" in user.jira_tickets_reported
        assert "jira_PROJ-123" in user.documents_created
    
    def test_extract_assignee(self):
        """Test extracting ticket assignee."""
        workflow = UserIntelligenceWorkflow()
        
        ticket = {
            "key": "PROJ-456",
            "summary": "Implement new feature",
            "assignee": "backend.dev",
            "tech_stack": ["Python", "FastAPI"],
            "description": "Add new API endpoints"
        }
        
        workflow.extract_user_from_jira_ticket(ticket)
        
        # Check assignee was extracted
        assert "backend.dev" in workflow.user_extractions
        user = workflow.user_extractions["backend.dev"]
        assert "jira_PROJ-456" in user.jira_tickets_assigned
    
    def test_extract_watchers(self):
        """Test extracting ticket watchers."""
        workflow = UserIntelligenceWorkflow()
        
        ticket = {
            "key": "PROJ-789",
            "summary": "Database migration",
            "assignee": "db.admin",
            "watchers": ["product.manager", "tech.lead", "qa.lead"],
            "tech_stack": ["PostgreSQL"],
            "description": "Migrate to new schema"
        }
        
        workflow.extract_user_from_jira_ticket(ticket)
        
        # Check watchers were extracted
        assert "product.manager" in workflow.user_extractions
        assert "tech.lead" in workflow.user_extractions
        assert "qa.lead" in workflow.user_extractions
        
        pm = workflow.user_extractions["product.manager"]
        assert "jira_PROJ-789" in pm.jira_tickets_watched
        
        tl = workflow.user_extractions["tech.lead"]
        assert "jira_PROJ-789" in tl.jira_tickets_watched
    
    def test_extract_worklog_contributors(self):
        """Test extracting worklog contributors with time tracking."""
        workflow = UserIntelligenceWorkflow()
        
        ticket = {
            "key": "PROJ-111",
            "summary": "Complex refactoring",
            "assignee": "senior.dev",
            "worklog": [
                {"author": "senior.dev", "timeSpent": "4h"},
                {"user": "junior.dev", "time_spent": "2h 30m"},
                {"author": "senior.dev", "timeSpent": "1h 30m"}
            ],
            "tech_stack": ["Python"],
            "description": "Major refactoring effort"
        }
        
        workflow.extract_user_from_jira_ticket(ticket)
        
        # Check worklog contributors were extracted
        assert "senior.dev" in workflow.user_extractions
        assert "junior.dev" in workflow.user_extractions
        
        senior = workflow.user_extractions["senior.dev"]
        assert "jira_PROJ-111" in senior.jira_tickets_worked
        # Should have logged: 4h + 1h 30m = 330 minutes
        assert senior.jira_metrics["time_spent_minutes"] == 330
        
        junior = workflow.user_extractions["junior.dev"]
        assert "jira_PROJ-111" in junior.jira_tickets_worked
        # Should have logged: 2h 30m = 150 minutes
        assert junior.jira_metrics["time_spent_minutes"] == 150
    
    def test_extract_commenters(self):
        """Test extracting commenters from ticket."""
        workflow = UserIntelligenceWorkflow()
        
        ticket = {
            "key": "PROJ-222",
            "summary": "API design discussion",
            "assignee": "api.designer",
            "comments": [
                {"author": "architect.lead", "text": "Consider RESTful design"},
                {"user": "security.expert", "body": "Add rate limiting"}
            ],
            "tech_stack": ["API Design"],
            "description": "Need feedback on API structure"
        }
        
        workflow.extract_user_from_jira_ticket(ticket)
        
        # Check commenters were extracted
        assert "architect.lead" in workflow.user_extractions
        assert "security.expert" in workflow.user_extractions
        
        arch = workflow.user_extractions["architect.lead"]
        assert "jira_PROJ-222" in arch.jira_tickets_commented
        assert "jira_PROJ-222" in arch.documents_commented
        
        sec = workflow.user_extractions["security.expert"]
        assert "jira_PROJ-222" in sec.jira_tickets_commented
    
    def test_extract_components_domain_expertise(self):
        """Test extracting components as domain expertise."""
        workflow = UserIntelligenceWorkflow()
        
        ticket = {
            "key": "PROJ-333",
            "summary": "Fix payment processing",
            "assignee": "payment.specialist",
            "components": ["Payment Gateway", "Billing", "Stripe Integration"],
            "tech_stack": ["Python"],
            "description": "Payment bugs"
        }
        
        workflow.extract_user_from_jira_ticket(ticket)
        
        # Check components were extracted as expertise areas
        user = workflow.user_extractions["payment.specialist"]
        assert "Payment Gateway" in user.components
        assert "Billing" in user.components
        assert "Stripe Integration" in user.components
    
    def test_extract_labels_as_skills(self):
        """Test extracting labels as technical skills."""
        workflow = UserIntelligenceWorkflow()
        
        ticket = {
            "key": "PROJ-444",
            "summary": "Performance optimization",
            "assignee": "performance.engineer",
            "labels": ["performance", "database", "caching", "redis"],
            "tech_stack": ["Python", "Redis"],
            "description": "Optimize DB queries"
        }
        
        workflow.extract_user_from_jira_ticket(ticket)
        
        # Check labels were extracted as skills
        user = workflow.user_extractions["performance.engineer"]
        assert "performance" in user.labels
        assert "database" in user.labels
        assert "caching" in user.labels
        assert "redis" in user.labels
    
    def test_extract_issue_types(self):
        """Test extracting issue types for skill pattern analysis."""
        workflow = UserIntelligenceWorkflow()
        
        ticket1 = {
            "key": "PROJ-501",
            "summary": "Critical bug",
            "assignee": "bug.hunter",
            "issue_type": "Bug",
            "type": "Bug",
            "tech_stack": [],
            "description": "Fix bug"
        }
        
        ticket2 = {
            "key": "PROJ-502",
            "summary": "New feature story",
            "assignee": "bug.hunter",
            "issue_type": "Story",
            "tech_stack": [],
            "description": "Implement feature"
        }
        
        workflow.extract_user_from_jira_ticket(ticket1)
        workflow.extract_user_from_jira_ticket(ticket2)
        
        # Check issue types were tracked
        user = workflow.user_extractions["bug.hunter"]
        assert "Bug" in user.issue_types_handled
        assert "Story" in user.issue_types_handled
    
    def test_work_metrics_with_story_points(self):
        """Test work metrics calculation with story points."""
        workflow = UserIntelligenceWorkflow()
        
        ticket = {
            "key": "PROJ-600",
            "summary": "Large feature",
            "assignee": "feature.dev",
            "story_points": 8,
            "priority": "high",
            "created": "2024-01-01",
            "resolved": "2024-01-05",
            "tech_stack": ["Python"],
            "description": "Complex feature"
        }
        
        workflow.extract_user_from_jira_ticket(ticket)
        
        # Check work metrics were calculated
        user = workflow.user_extractions["feature.dev"]
        assert user.jira_metrics["story_points_handled"] == 8
        assert user.jira_metrics["tickets_resolved"] == 1
        assert user.jira_metrics["complexity_levels"]["high"] == 1
    
    def test_multiple_tickets_aggregate_metrics(self):
        """Test that Jira metrics aggregate correctly across multiple tickets."""
        workflow = UserIntelligenceWorkflow()
        
        ticket1 = {
            "key": "PROJ-701",
            "summary": "Small fix",
            "assignee": "full.stack",
            "story_points": 2,
            "priority": "medium",
            "created": "2024-01-01",
            "resolved": "2024-01-02",
            "worklog": [{"author": "full.stack", "timeSpent": "3h"}],
            "tech_stack": [],
            "description": "Quick fix"
        }
        
        ticket2 = {
            "key": "PROJ-702",
            "summary": "Medium feature",
            "assignee": "full.stack",
            "story_points": 5,
            "priority": "medium",
            "created": "2024-01-03",
            "resolved": "2024-01-08",
            "worklog": [{"author": "full.stack", "timeSpent": "2d"}],
            "tech_stack": [],
            "description": "Feature work"
        }
        
        workflow.extract_user_from_jira_ticket(ticket1)
        workflow.extract_user_from_jira_ticket(ticket2)
        
        # Check aggregated metrics
        user = workflow.user_extractions["full.stack"]
        assert user.jira_metrics["story_points_handled"] == 7  # 2 + 5
        assert user.jira_metrics["tickets_resolved"] == 2
        assert user.jira_metrics["time_spent_minutes"] == 1140  # 3h + 2d (16h) = 19h = 1140m
        assert user.jira_metrics["complexity_levels"]["low"] == 1  # ticket1
        assert user.jira_metrics["complexity_levels"]["medium"] == 1  # ticket2
        assert user.jira_metrics["total_tickets"] == 2
    
    def test_all_roles_in_single_ticket(self):
        """Test extracting all possible roles from a comprehensive Jira ticket."""
        workflow = UserIntelligenceWorkflow()
        
        ticket = {
            "key": "PROJ-MEGA",
            "summary": "Critical system refactoring",
            "reporter": "product.owner",
            "assignee": "lead.architect",
            "watchers": ["cto", "engineering.manager"],
            "worklog": [
                {"author": "lead.architect", "timeSpent": "3d"},
                {"user": "senior.dev", "time_spent": "2d 4h"}
            ],
            "comments": [
                {"author": "security.reviewer", "text": "Security looks good"},
                {"user": "qa.engineer", "body": "Tested successfully"}
            ],
            "components": ["Core System", "Database", "API"],
            "labels": ["refactoring", "performance", "critical"],
            "issue_type": "Epic",
            "story_points": 13,
            "priority": "highest",
            "created": "2024-01-01",
            "resolved": "2024-01-15",
            "tech_stack": ["Python", "PostgreSQL"],
            "description": "Major refactoring @documentation.writer please update docs"
        }
        
        workflow.extract_user_from_jira_ticket(ticket)
        
        # Verify all role types were extracted
        # 1. Reporter
        assert "product.owner" in workflow.user_extractions
        assert "jira_PROJ-MEGA" in workflow.user_extractions["product.owner"].jira_tickets_reported
        
        # 2. Assignee
        assert "lead.architect" in workflow.user_extractions
        assert "jira_PROJ-MEGA" in workflow.user_extractions["lead.architect"].jira_tickets_assigned
        
        # 3. Watchers
        assert "cto" in workflow.user_extractions
        assert "engineering.manager" in workflow.user_extractions
        assert "jira_PROJ-MEGA" in workflow.user_extractions["cto"].jira_tickets_watched
        
        # 4. Worklog contributors
        assert "senior.dev" in workflow.user_extractions
        assert "jira_PROJ-MEGA" in workflow.user_extractions["lead.architect"].jira_tickets_worked
        assert "jira_PROJ-MEGA" in workflow.user_extractions["senior.dev"].jira_tickets_worked
        
        # 5. Commenters
        assert "security.reviewer" in workflow.user_extractions
        assert "qa.engineer" in workflow.user_extractions
        assert "jira_PROJ-MEGA" in workflow.user_extractions["security.reviewer"].jira_tickets_commented
        
        # 6. Mentioned users
        assert "documentation.writer" in workflow.user_extractions
        assert "jira_PROJ-MEGA" in workflow.user_extractions["documentation.writer"].jira_tickets_commented
        
        # Total: Should have extracted 8 unique users
        assert len(workflow.user_extractions) == 8
        
        # Verify domain expertise for assignee
        assignee = workflow.user_extractions["lead.architect"]
        assert "Core System" in assignee.components
        assert "Database" in assignee.components
        assert "API" in assignee.components
        assert "refactoring" in assignee.labels
        assert "performance" in assignee.labels
        assert "Epic" in assignee.issue_types_handled


class TestTimeSpentParsing:
    """Test the time spent parsing algorithm."""
    
    def test_parse_minutes_only(self):
        """Test parsing minutes only format."""
        workflow = UserIntelligenceWorkflow()
        assert workflow._parse_time_spent("30m") == 30
        assert workflow._parse_time_spent("45m") == 45
    
    def test_parse_hours_only(self):
        """Test parsing hours only format."""
        workflow = UserIntelligenceWorkflow()
        assert workflow._parse_time_spent("2h") == 120
        assert workflow._parse_time_spent("4h") == 240
    
    def test_parse_days_only(self):
        """Test parsing days only format (8-hour workday)."""
        workflow = UserIntelligenceWorkflow()
        assert workflow._parse_time_spent("1d") == 480  # 8 hours
        assert workflow._parse_time_spent("2d") == 960  # 16 hours
    
    def test_parse_hours_and_minutes(self):
        """Test parsing combined hours and minutes."""
        workflow = UserIntelligenceWorkflow()
        assert workflow._parse_time_spent("2h 30m") == 150
        assert workflow._parse_time_spent("1h 15m") == 75
        assert workflow._parse_time_spent("4h 45m") == 285
    
    def test_parse_days_and_hours(self):
        """Test parsing combined days and hours."""
        workflow = UserIntelligenceWorkflow()
        assert workflow._parse_time_spent("1d 4h") == 720  # 480 + 240
        assert workflow._parse_time_spent("2d 2h") == 1080  # 960 + 120
    
    def test_parse_days_hours_minutes(self):
        """Test parsing all three units."""
        workflow = UserIntelligenceWorkflow()
        assert workflow._parse_time_spent("1d 2h 30m") == 630  # 480 + 120 + 30
        assert workflow._parse_time_spent("2d 4h 15m") == 1215  # 960 + 240 + 15
    
    def test_parse_with_spaces(self):
        """Test parsing with various spacing."""
        workflow = UserIntelligenceWorkflow()
        assert workflow._parse_time_spent("2h 30m") == 150
        assert workflow._parse_time_spent("2h30m") == 150
        assert workflow._parse_time_spent("  2h  30m  ") == 150
    
    def test_parse_empty_string(self):
        """Test parsing empty string."""
        workflow = UserIntelligenceWorkflow()
        assert workflow._parse_time_spent("") == 0
        assert workflow._parse_time_spent("   ") == 0
    
    def test_parse_decimal_values(self):
        """Test parsing decimal time values."""
        workflow = UserIntelligenceWorkflow()
        assert workflow._parse_time_spent("2.5h") == 150  # 2.5 * 60
        assert workflow._parse_time_spent("0.5d") == 240  # 0.5 * 8 * 60


class TestComplexityDetermination:
    """Test the complexity determination algorithm."""
    
    def test_complexity_from_critical_priority(self):
        """Test that critical priority always returns high complexity."""
        workflow = UserIntelligenceWorkflow()
        assert workflow._determine_complexity(0, "critical") == "high"
        assert workflow._determine_complexity(2, "highest") == "high"
        assert workflow._determine_complexity(5, "blocker") == "high"
    
    def test_complexity_from_high_priority(self):
        """Test high priority with varying story points."""
        workflow = UserIntelligenceWorkflow()
        assert workflow._determine_complexity(3, "high") == "medium"
        assert workflow._determine_complexity(8, "high") == "high"
    
    def test_complexity_from_low_priority(self):
        """Test that low priority returns low complexity."""
        workflow = UserIntelligenceWorkflow()
        assert workflow._determine_complexity(8, "low") == "low"
        assert workflow._determine_complexity(13, "lowest") == "low"
        assert workflow._determine_complexity(5, "trivial") == "low"
    
    def test_complexity_from_story_points_high(self):
        """Test high complexity from story points (>= 8)."""
        workflow = UserIntelligenceWorkflow()
        assert workflow._determine_complexity(8, "medium") == "high"
        assert workflow._determine_complexity(13, "medium") == "high"
        assert workflow._determine_complexity(21, "medium") == "high"
    
    def test_complexity_from_story_points_medium(self):
        """Test medium complexity from story points (3-7)."""
        workflow = UserIntelligenceWorkflow()
        assert workflow._determine_complexity(3, "medium") == "medium"
        assert workflow._determine_complexity(5, "medium") == "medium"
        assert workflow._determine_complexity(7, "medium") == "medium"
    
    def test_complexity_from_story_points_low(self):
        """Test low complexity from story points (1-2)."""
        workflow = UserIntelligenceWorkflow()
        assert workflow._determine_complexity(1, "medium") == "low"
        assert workflow._determine_complexity(2, "medium") == "low"
    
    def test_complexity_default_medium(self):
        """Test default complexity when no clear indicators."""
        workflow = UserIntelligenceWorkflow()
        assert workflow._determine_complexity(0, "medium") == "medium"
        assert workflow._determine_complexity(0, "unknown") == "medium"


class TestJiraMetricsAggregation:
    """Test Jira metrics aggregation across multiple tickets."""
    
    def test_story_points_aggregation(self):
        """Test that story points aggregate correctly."""
        workflow = UserIntelligenceWorkflow()
        user = UserExtraction(username="test.user")
        
        workflow._update_jira_metrics(user, story_points=5, is_resolved=False, complexity="medium")
        workflow._update_jira_metrics(user, story_points=8, is_resolved=False, complexity="high")
        workflow._update_jira_metrics(user, story_points=3, is_resolved=False, complexity="low")
        
        assert user.jira_metrics["story_points_handled"] == 16  # 5 + 8 + 3
        assert user.jira_metrics["total_tickets"] == 3
    
    def test_resolution_tracking(self):
        """Test tracking of resolved tickets."""
        workflow = UserIntelligenceWorkflow()
        user = UserExtraction(username="test.user")
        
        workflow._update_jira_metrics(user, is_resolved=True, complexity="medium")
        workflow._update_jira_metrics(user, is_resolved=False, complexity="medium")
        workflow._update_jira_metrics(user, is_resolved=True, complexity="high")
        
        assert user.jira_metrics["tickets_resolved"] == 2
        assert user.jira_metrics["total_tickets"] == 3
    
    def test_avg_resolution_time_calculation(self):
        """Test average resolution time calculation."""
        workflow = UserIntelligenceWorkflow()
        user = UserExtraction(username="test.user")
        
        workflow._update_jira_metrics(user, resolution_time_hours=10, is_resolved=True, complexity="low")
        workflow._update_jira_metrics(user, resolution_time_hours=30, is_resolved=True, complexity="high")
        workflow._update_jira_metrics(user, resolution_time_hours=20, is_resolved=True, complexity="medium")
        
        # Average: (10 + 30 + 20) / 3 = 20
        assert user.jira_metrics["avg_resolution_time_hours"] == 20.0
        assert user.jira_metrics["tickets_resolved"] == 3
    
    def test_complexity_levels_tracking(self):
        """Test tracking of complexity level distribution."""
        workflow = UserIntelligenceWorkflow()
        user = UserExtraction(username="test.user")
        
        workflow._update_jira_metrics(user, complexity="low")
        workflow._update_jira_metrics(user, complexity="low")
        workflow._update_jira_metrics(user, complexity="medium")
        workflow._update_jira_metrics(user, complexity="medium")
        workflow._update_jira_metrics(user, complexity="medium")
        workflow._update_jira_metrics(user, complexity="high")
        
        assert user.jira_metrics["complexity_levels"]["low"] == 2
        assert user.jira_metrics["complexity_levels"]["medium"] == 3
        assert user.jira_metrics["complexity_levels"]["high"] == 1
    
    def test_metrics_initialization(self):
        """Test that metrics are properly initialized on first update."""
        workflow = UserIntelligenceWorkflow()
        user = UserExtraction(username="test.user")
        
        # User should have no jira_metrics initially
        assert user.jira_metrics == {}
        
        workflow._update_jira_metrics(user, story_points=5, is_resolved=True, complexity="medium")
        
        # After first update, all fields should exist
        assert "story_points_handled" in user.jira_metrics
        assert "tickets_resolved" in user.jira_metrics
        assert "avg_resolution_time_hours" in user.jira_metrics
        assert "complexity_levels" in user.jira_metrics
        assert "total_tickets" in user.jira_metrics
        assert user.jira_metrics["total_tickets"] == 1

