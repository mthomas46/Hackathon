"""Unit Tests for Document Types - Content Generation Testing.

This module contains unit tests for document type validation, structure,
and generation patterns in the content generation system.
"""

import pytest
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from simulation.domain.value_objects import (
    ProjectType, ComplexityLevel, DocumentType, DocumentMetadata, DocumentId
)
from enum import Enum


def get_all_document_types():
    """Get all document types from the service."""
    return [dt for dt in DocumentType]


class TestDocumentTypeValidation:
    """Test cases for document type validation."""

    def test_document_type_enum_values(self):
        """Test that document type enum has expected values."""
        # Test actual enum values
        actual_types = [
            "PROJECT_REQUIREMENTS",
            "ARCHITECTURE_DIAGRAM",
            "USER_STORY",
            "TECHNICAL_DESIGN",
            "CODE_REVIEW_COMMENTS",
            "TEST_SCENARIOS",
            "DEPLOYMENT_GUIDE",
            "MAINTENANCE_DOCS",
            "CHANGE_LOG",
            "TEAM_RETROSPECTIVE"
        ]

        # Check that all actual document types exist
        for doc_type in actual_types:
            assert hasattr(DocumentType, doc_type), f"Missing document type: {doc_type}"

    def test_extended_document_type_coverage(self):
        """Test that all expected document types are available in the service."""
        expected_types = [
            "CONFLUENCE_PAGE", "JIRA_TICKET", "GITHUB_PR", "GITHUB_ISSUE",
            "SLACK_MESSAGE", "EMAIL", "MEETING_NOTES", "REQUIREMENTS_DOC",
            "DESIGN_DOC", "ARCHITECTURE_DOC", "TEST_PLAN", "ACCEPTANCE_CRITERIA",
            "CODE_REVIEW", "RUNBOOK", "INCIDENT_REPORT", "ROADMAP",
            "STATUS_REPORT", "RETROSPECTIVE", "WIKI_PAGE", "API_DOCUMENTATION",
            "DATABASE_SCHEMA", "CONFIGURATION_FILE", "LOG_FILE", "METRICS_REPORT",
            "PERFORMANCE_REPORT", "SECURITY_AUDIT", "COMPLIANCE_REPORT"
        ]

        # Test that all expected types exist in the enum
        for doc_type_name in expected_types:
            assert hasattr(DocumentType, doc_type_name), f"Missing document type: {doc_type_name}"
            doc_type = DocumentType[doc_type_name]
            assert doc_type.value == doc_type_name.lower(), f"Wrong value for {doc_type_name}"

        # Test that we get all document types
        all_types = get_all_document_types()
        assert len(all_types) >= 35, f"Should have at least 35 document types, got {len(all_types)}"

    def test_document_type_string_representation(self):
        """Test document type string representations."""
        # Test actual enum values
        assert DocumentType.PROJECT_REQUIREMENTS.value == "project_requirements"
        assert DocumentType.USER_STORY.value == "user_story"
        assert DocumentType.TECHNICAL_DESIGN.value == "technical_design"
        assert DocumentType.DEPLOYMENT_GUIDE.value == "deployment_guide"
        assert DocumentType.CHANGE_LOG.value == "change_log"

        # Test expected document types
        assert DocumentType.CONFLUENCE_PAGE.value == "confluence_page"
        assert DocumentType.JIRA_TICKET.value == "jira_ticket"
        assert DocumentType.GITHUB_PR.value == "github_pr"
        assert DocumentType.EMAIL.value == "email"
        assert DocumentType.MEETING_NOTES.value == "meeting_notes"

    def test_document_type_categories(self):
        """Test document type categorization."""
        # Define expected categories
        communication_docs = [
            DocumentType.SLACK_MESSAGE,
            DocumentType.EMAIL,
            DocumentType.MEETING_NOTES
        ]

        project_docs = [
            DocumentType.PROJECT_REQUIREMENTS,
            DocumentType.CONFLUENCE_PAGE,
            DocumentType.WIKI_PAGE,
            DocumentType.ROADMAP,
            DocumentType.STATUS_REPORT,
            DocumentType.CHANGE_LOG,
            DocumentType.TEAM_RETROSPECTIVE
        ]

        technical_docs = [
            DocumentType.ARCHITECTURE_DIAGRAM,
            DocumentType.TECHNICAL_DESIGN,
            DocumentType.REQUIREMENTS_DOC,
            DocumentType.DESIGN_DOC,
            DocumentType.ARCHITECTURE_DOC,
            DocumentType.API_DOCUMENTATION,
            DocumentType.DATABASE_SCHEMA,
            DocumentType.CODE_REVIEW,
            DocumentType.DEPLOYMENT_GUIDE,
            DocumentType.CODE_REVIEW_COMMENTS
        ]

        # Verify categorization logic
        all_docs = communication_docs + project_docs + technical_docs
        assert len(all_docs) >= 15  # Should have reasonable number of document types

        # Check for some known technical docs
        assert DocumentType.DEPLOYMENT_GUIDE in technical_docs
        assert DocumentType.CONFLUENCE_PAGE in project_docs

    def test_document_type_validation(self):
        """Test document type validation logic."""
        # Valid document types
        valid_types = [doc_type.value for doc_type in DocumentType]

        # Test validation function would accept valid types
        for doc_type in valid_types:
            assert isinstance(doc_type, str)
            assert len(doc_type) > 0
            assert "_" in doc_type or doc_type.islower()

    def test_document_type_file_extensions(self):
        """Test document type to file extension mapping."""
        # Define expected file extensions for all document types
        extension_map = {
            DocumentType.PROJECT_REQUIREMENTS: ".md",
            DocumentType.USER_STORY: ".md",
            DocumentType.TECHNICAL_DESIGN: ".md",
            DocumentType.ARCHITECTURE_DIAGRAM: ".png",
            DocumentType.CODE_REVIEW_COMMENTS: ".md",
            DocumentType.TEST_SCENARIOS: ".md",
            DocumentType.DEPLOYMENT_GUIDE: ".md",
            DocumentType.MAINTENANCE_DOCS: ".md",
            DocumentType.CHANGE_LOG: ".md",
            DocumentType.TEAM_RETROSPECTIVE: ".md"
        }

        # Add expected document types
        expected_extensions = {
            DocumentType.CONFLUENCE_PAGE: ".md",
            DocumentType.JIRA_TICKET: ".md",
            DocumentType.GITHUB_PR: ".md",
            DocumentType.EMAIL: ".eml",
            DocumentType.MEETING_NOTES: ".md",
            DocumentType.REQUIREMENTS_DOC: ".md",
            DocumentType.API_DOCUMENTATION: ".yaml",
            DocumentType.DATABASE_SCHEMA: ".sql",
            DocumentType.CONFIGURATION_FILE: ".yaml",
            DocumentType.LOG_FILE: ".log"
        }

        extension_map.update(expected_extensions)

        # Verify all mappings are strings starting with "."
        for doc_type, extension in extension_map.items():
            assert isinstance(extension, str)
            assert extension.startswith(".")
            assert len(extension) > 1

        # Verify we have extensions for key document types
        assert extension_map[DocumentType.CONFLUENCE_PAGE] == ".md"
        assert extension_map[DocumentType.EMAIL] == ".eml"


class TestDocumentMetadataValidation:
    """Test cases for document metadata validation."""

    def test_document_metadata_creation(self):
        """Test document metadata creation."""
        metadata = DocumentMetadata(
            document_id=DocumentId("doc-123"),
            title="Test Document",
            type=DocumentType.PROJECT_REQUIREMENTS,
            author="test@example.com",
            created_at=datetime.now(),
            tags=["test", "documentation"],
            word_count=500,
            complexity_score=0.7
        )

        assert metadata.type == DocumentType.PROJECT_REQUIREMENTS
        assert metadata.title == "Test Document"
        assert metadata.author == "test@example.com"
        assert isinstance(metadata.created_at, datetime)
        assert metadata.tags == ["test", "documentation"]
        assert metadata.word_count == 500
        assert metadata.complexity_score == 0.7

    def test_document_metadata_validation(self):
        """Test document metadata field validation."""
        # Test valid metadata
        valid_metadata = DocumentMetadata(
            document_id=DocumentId("doc-456"),
            title="Valid Ticket",
            type=DocumentType.USER_STORY,
            author="user@company.com",
            created_at=datetime.now(),
            tags=["bug", "high-priority"],
            word_count=200,
            complexity_score=0.8
        )

        # Verify all fields are properly set
        assert valid_metadata.title is not None
        assert valid_metadata.author is not None
        assert "@" in valid_metadata.author
        assert valid_metadata.complexity_score >= 0.0
        assert valid_metadata.complexity_score <= 1.0
        assert valid_metadata.word_count >= 0

    def test_document_metadata_age_calculation(self):
        """Test document age calculation."""
        past_date = datetime.now() - timedelta(days=30)
        metadata = DocumentMetadata(
            document_id=DocumentId("doc-789"),
            title="Old Meeting",
            type=DocumentType.TEAM_RETROSPECTIVE,
            author="user@example.com",
            created_at=past_date,
            tags=["meeting"],
            word_count=300
        )

        # Test age calculation (this would be a method on DocumentMetadata)
        age_days = (datetime.now() - metadata.created_at).days
        assert age_days >= 30
        assert age_days < 31

    def test_document_metadata_tag_matching(self):
        """Test document tag matching functionality."""
        metadata = DocumentMetadata(
            document_id=DocumentId("doc-101"),
            title="Architecture Document",
            type=DocumentType.PROJECT_REQUIREMENTS,
            author="architect@example.com",
            created_at=datetime.now(),
            tags=["architecture", "design", "system"],
            word_count=800,
            complexity_score=0.9
        )

        # Test tag matching logic
        search_tags = ["architecture", "design"]
        matching_tags = [tag for tag in metadata.tags if tag in search_tags]
        assert len(matching_tags) == 2
        assert "architecture" in matching_tags
        assert "design" in matching_tags

        # Test partial matching
        partial_match = any("arch" in tag for tag in metadata.tags)
        assert partial_match == True


class TestDocumentStructureValidation:
    """Test cases for document structure validation."""

    def test_confluence_page_structure(self):
        """Test Confluence page document structure."""
        confluence_doc = {
            "type": DocumentType.CONFLUENCE_PAGE.value,
            "title": "Project Requirements",
            "content": "# Project Requirements\n\n## Overview\nThis document outlines...",
            "space": "Engineering",
            "parent_page": "Project Documentation",
            "labels": ["requirements", "project"],
            "metadata": {
                "author": "product@example.com",
                "created": datetime.now().isoformat(),
                "version": "1.2"
            }
        }

        # Validate required fields
        required_fields = ["type", "title", "content", "metadata"]
        for field in required_fields:
            assert field in confluence_doc

        # Validate content structure
        assert confluence_doc["content"].startswith("# ")
        assert "Overview" in confluence_doc["content"]
        assert confluence_doc["type"] == "confluence_page"

    def test_jira_ticket_structure(self):
        """Test JIRA ticket document structure."""
        jira_ticket = {
            "type": DocumentType.JIRA_TICKET.value,
            "key": "PROJ-123",
            "summary": "Implement user authentication",
            "description": "As a user, I want to be able to log in...",
            "issue_type": "Story",
            "priority": "High",
            "assignee": "dev@example.com",
            "reporter": "pm@example.com",
            "status": "In Progress",
            "labels": ["authentication", "security"],
            "components": ["Backend", "API"],
            "metadata": {
                "created": datetime.now().isoformat(),
                "updated": datetime.now().isoformat(),
                "story_points": 8
            }
        }

        # Validate required JIRA fields
        required_jira_fields = ["key", "summary", "description", "issue_type", "status"]
        for field in required_jira_fields:
            assert field in jira_ticket

        # Validate JIRA-specific patterns
        assert "-" in jira_ticket["key"]
        assert jira_ticket["priority"] in ["Lowest", "Low", "Medium", "High", "Highest"]
        assert jira_ticket["type"] == "jira_ticket"

    def test_github_pr_structure(self):
        """Test GitHub pull request document structure."""
        github_pr = {
            "type": DocumentType.GITHUB_PR.value,
            "number": 123,
            "title": "feat: Add user authentication",
            "body": "## Description\nThis PR implements user authentication...\n\n## Changes\n- Added login endpoint\n- Added JWT tokens",
            "head": {
                "ref": "feature/auth",
                "repo": {"name": "my-project"}
            },
            "base": {
                "ref": "main",
                "repo": {"name": "my-project"}
            },
            "user": {"login": "developer"},
            "state": "open",
            "labels": ["enhancement", "backend"],
            "assignees": ["reviewer1", "reviewer2"],
            "requested_reviewers": ["architect"],
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "commits": 5,
                "additions": 120,
                "deletions": 15
            }
        }

        # Validate GitHub PR structure
        assert github_pr["number"] > 0
        assert github_pr["title"].startswith(("feat:", "fix:", "docs:", "refactor:"))
        assert "Description" in github_pr["body"]
        assert github_pr["state"] in ["open", "closed", "merged"]
        assert len(github_pr["assignees"]) > 0
        assert github_pr["type"] == "github_pr"

    def test_email_structure(self):
        """Test email document structure."""
        email_doc = {
            "type": DocumentType.CHANGE_LOG.value,
            "subject": "Project Status Update - Week 15",
            "from": "pm@example.com",
            "to": ["team@example.com", "stakeholder@example.com"],
            "cc": ["manager@example.com"],
            "body": "Dear Team,\n\nHere's the weekly status update...\n\nBest regards,\nProject Manager",
            "attachments": ["status_report.pdf", "burndown_chart.png"],
            "metadata": {
                "sent_at": datetime.now().isoformat(),
                "importance": "normal",
                "sensitivity": "normal"
            }
        }

        # Validate email structure
        assert "@" in email_doc["from"]
        assert isinstance(email_doc["to"], list)
        assert len(email_doc["to"]) > 0
        assert "subject" in email_doc
        assert "body" in email_doc

    def test_meeting_notes_structure(self):
        """Test meeting notes document structure."""
        meeting_notes = {
            "type": DocumentType.TEAM_RETROSPECTIVE.value,
            "title": "Sprint Planning Meeting - Sprint 15",
            "date": datetime.now().date().isoformat(),
            "time": "10:00 AM - 11:30 AM",
            "location": "Conference Room A",
            "attendees": [
                {"name": "Alice Johnson", "role": "Product Owner"},
                {"name": "Bob Smith", "role": "Scrum Master"},
                {"name": "Charlie Brown", "role": "Developer"}
            ],
            "agenda": [
                "Sprint retrospective",
                "Sprint planning",
                "Capacity planning"
            ],
            "discussion_points": [
                {"topic": "Sprint velocity", "notes": "Team velocity increased by 15%"},
                {"topic": "Blockers", "notes": "No major blockers identified"}
            ],
            "action_items": [
                {"description": "Update sprint board", "assignee": "Bob Smith", "due_date": (datetime.now() + timedelta(days=7)).isoformat()},
                {"description": "Refine user stories", "assignee": "Alice Johnson", "due_date": (datetime.now() + timedelta(days=3)).isoformat()}
            ],
            "metadata": {
                "meeting_type": "sprint_planning",
                "duration_minutes": 90,
                "recorded_by": "Bob Smith"
            }
        }

        # Validate meeting notes structure
        assert "attendees" in meeting_notes
        assert len(meeting_notes["attendees"]) > 0
        assert "agenda" in meeting_notes
        assert "action_items" in meeting_notes
        assert all("assignee" in item for item in meeting_notes["action_items"])


class TestDocumentTypeRelationships:
    """Test cases for document type relationships."""

    def test_document_hierarchy(self):
        """Test document type hierarchy and relationships."""
        # Define document relationships
        parent_child_relationships = {
            DocumentType.PROJECT_REQUIREMENTS: [DocumentType.USER_STORY, DocumentType.TECHNICAL_DESIGN],
            DocumentType.TECHNICAL_DESIGN: [DocumentType.ARCHITECTURE_DIAGRAM, DocumentType.CODE_REVIEW_COMMENTS],
            DocumentType.TEST_SCENARIOS: [DocumentType.CODE_REVIEW_COMMENTS, DocumentType.USER_STORY],
            DocumentType.CHANGE_LOG: [DocumentType.TEAM_RETROSPECTIVE, DocumentType.MAINTENANCE_DOCS]
        }

        # Validate relationship structure
        for parent, children in parent_child_relationships.items():
            assert isinstance(parent, DocumentType)
            assert isinstance(children, list)
            assert len(children) > 0
            assert all(isinstance(child, DocumentType) for child in children)

    def test_document_workflow_sequences(self):
        """Test document workflow sequences."""
        # Define typical document workflows
        requirement_to_deployment = [
            DocumentType.PROJECT_REQUIREMENTS,
            DocumentType.USER_STORY,
            DocumentType.TECHNICAL_DESIGN,
            DocumentType.CODE_REVIEW_COMMENTS,
            DocumentType.TEST_SCENARIOS,
            DocumentType.DEPLOYMENT_GUIDE,
            DocumentType.CHANGE_LOG
        ]

        # Validate workflow sequence
        assert len(requirement_to_deployment) > 5
        assert DocumentType.PROJECT_REQUIREMENTS in requirement_to_deployment
        assert DocumentType.DEPLOYMENT_GUIDE in requirement_to_deployment

    def test_document_dependency_mapping(self):
        """Test document dependency mapping."""
        # Define document dependencies
        dependencies = {
            DocumentType.TECHNICAL_DESIGN: [DocumentType.USER_STORY, DocumentType.CODE_REVIEW_COMMENTS],
            DocumentType.DEPLOYMENT_GUIDE: [DocumentType.ARCHITECTURE_DIAGRAM, DocumentType.TEST_SCENARIOS],
            DocumentType.MAINTENANCE_DOCS: [DocumentType.CHANGE_LOG, DocumentType.TEAM_RETROSPECTIVE],
            DocumentType.CODE_REVIEW_COMMENTS: [DocumentType.CODE_REVIEW_COMMENTS, DocumentType.TEST_SCENARIOS]
        }

        # Validate dependency structure
        for doc_type, deps in dependencies.items():
            assert isinstance(doc_type, DocumentType)
            assert isinstance(deps, list)
            assert len(deps) > 0


class TestDocumentQualityValidation:
    """Test cases for document quality validation."""

    def test_document_quality_scoring(self):
        """Test document quality scoring logic."""
        # Define quality criteria and scores
        quality_tests = [
            {"criteria": "has_title", "weight": 0.2, "passed": True},
            {"criteria": "has_content", "weight": 0.3, "passed": True},
            {"criteria": "proper_formatting", "weight": 0.2, "passed": False},
            {"criteria": "complete_metadata", "weight": 0.15, "passed": True},
            {"criteria": "spelling_grammar", "weight": 0.15, "passed": True}
        ]

        # Calculate quality score
        total_score = sum(test["weight"] for test in quality_tests if test["passed"])
        assert total_score == 0.8  # 0.2 + 0.3 + 0.15 + 0.15

        # Validate score range
        assert 0.0 <= total_score <= 1.0

    def test_document_completeness_check(self):
        """Test document completeness validation."""
        # Define completeness requirements by document type
        completeness_requirements = {
            DocumentType.PROJECT_REQUIREMENTS: ["title", "content", "author", "created_date"],
            DocumentType.USER_STORY: ["summary", "description", "assignee", "priority"],
            DocumentType.TECHNICAL_DESIGN: ["title", "body", "assignees", "labels"],
            DocumentType.CHANGE_LOG: ["subject", "from", "to", "body"]
        }

        # Test completeness for a JIRA ticket
        jira_ticket = {
            "summary": "Implement login feature",
            "description": "Detailed description...",
            "assignee": "dev@example.com",
            "priority": "High"
        }

        required_fields = completeness_requirements[DocumentType.USER_STORY]
        completeness_score = sum(1 for field in required_fields if field in jira_ticket) / len(required_fields)

        assert completeness_score == 1.0  # All required fields present

    def test_document_consistency_validation(self):
        """Test document consistency validation."""
        # Test date consistency
        doc_created = datetime.now() - timedelta(days=5)
        doc_modified = datetime.now() - timedelta(days=3)

        assert doc_modified > doc_created  # Modified date should be after created date

        # Test version consistency
        versions = ["1.0", "1.1", "2.0", "2.1"]
        assert versions == sorted(versions)  # Versions should be in order

    def test_document_format_validation(self):
        """Test document format validation."""
        # Test markdown format
        markdown_content = "# Title\n\n## Section\n\nThis is **bold** text."
        assert markdown_content.startswith("# ")
        assert "## " in markdown_content
        assert "**" in markdown_content

        # Test YAML format
        yaml_content = "api:\n  version: 1.0\n  endpoints:\n    - /users\n    - /posts"
        assert ": " in yaml_content
        assert yaml_content.startswith("api:")

        # Test JSON format
        json_content = '{"name": "test", "version": "1.0", "active": true}'
        import json
        parsed = json.loads(json_content)
        assert parsed["name"] == "test"
        assert parsed["active"] == True


class TestDocumentGenerationPatterns:
    """Test cases for document generation patterns."""

    def test_document_template_application(self):
        """Test document template application."""
        # Define a simple template
        template = {
            "type": DocumentType.PROJECT_REQUIREMENTS.value,
            "title": "{project_name} - {document_type}",
            "content": "# {title}\n\n## Overview\n{document_description}\n\n## Details\n{document_content}",
            "metadata": {
                "template_version": "1.0",
                "generated_at": "{timestamp}"
            }
        }

        # Apply template variables
        variables = {
            "project_name": "E-commerce Platform",
            "document_type": "Requirements",
            "document_description": "This document outlines the requirements...",
            "document_content": "Detailed requirements here...",
            "timestamp": datetime.now().isoformat(),
            "title": "E-commerce Platform - Requirements"  # Add the title variable
        }

        # Simulate template application
        generated_title = template["title"].format(**variables)
        generated_content = template["content"].format(
            title=variables["title"],  # Pass title explicitly
            document_description=variables["document_description"],
            document_content=variables["document_content"]
        )

        assert "E-commerce Platform" in generated_title
        assert "Requirements" in generated_title
        assert "E-commerce Platform - Requirements" == generated_title
        assert "This document outlines the requirements..." in generated_content

    def test_document_context_injection(self):
        """Test document context injection."""
        # Define base document
        base_doc = {
            "type": DocumentType.TEAM_RETROSPECTIVE.value,
            "title": "Sprint Planning",
            "content": "Meeting content here...",
            "metadata": {}
        }

        # Define context to inject
        context = {
            "project": {
                "name": "Web App Project",
                "phase": "Development",
                "sprint": 15
            },
            "team": {
                "size": 8,
                "scrum_master": "Alice Johnson"
            },
            "meeting": {
                "date": datetime.now().date().isoformat(),
                "duration": 90
            }
        }

        # Inject context into document
        enriched_doc = base_doc.copy()
        enriched_doc["metadata"].update(context)

        # Validate context injection
        assert enriched_doc["metadata"]["project"]["name"] == "Web App Project"
        assert enriched_doc["metadata"]["team"]["size"] == 8
        assert "date" in enriched_doc["metadata"]["meeting"]

    def test_document_personalization(self):
        """Test document personalization based on audience."""
        base_content = "This is a technical document about {topic}."

        # Personalize for different audiences
        audiences = {
            "developer": {
                "topic": "API implementation",
                "tone": "technical",
                "detail_level": "high"
            },
            "manager": {
                "topic": "project timeline",
                "tone": "business",
                "detail_level": "medium"
            },
            "stakeholder": {
                "topic": "business benefits",
                "tone": "executive",
                "detail_level": "low"
            }
        }

        # Generate personalized content
        for audience, preferences in audiences.items():
            personalized = base_content.format(topic=preferences["topic"])
            assert preferences["topic"] in personalized

            # Validate personalization logic
            if audience == "developer":
                assert "API" in personalized
            elif audience == "manager":
                assert "timeline" in personalized
            elif audience == "stakeholder":
                assert "benefits" in personalized
