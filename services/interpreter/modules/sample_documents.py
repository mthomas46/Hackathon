"""Sample documents for Interpreter service context.

This module contains a diverse set of sample documents that can be used as context
when processing queries that require document analysis or simulation scenarios.
Includes various document types: Confluence pages, Jira tickets, Pull Requests,
with different content characteristics.
"""

from typing import List, Dict, Any


class SampleDocumentRepository:
    """Repository for managing sample documents used in query processing."""

    def __init__(self):
        self.documents = self._load_sample_documents()

    def _load_sample_documents(self) -> List[Dict[str, Any]]:
        """Load the comprehensive set of sample documents."""
        return [
            # CONFLUENCE DOCUMENTS
            {
                "id": "conf_001",
                "type": "confluence",
                "title": "Financial Services Platform - Architecture Overview",
                "content": "# Financial Services Platform Architecture\n\n## Overview\nThe Financial Services Platform is a comprehensive banking solution built on microservices architecture serving 500K+ customers.\n\n## Core Components\n- **Account Management Service**: Handles customer accounts, balances, and transactions\n- **Transaction Processing Engine**: Real-time transaction validation and processing\n- **Risk Assessment Module**: ML-based fraud detection and risk scoring\n\n## Technology Stack\n- Backend: Java 17, Spring Boot 3.0, PostgreSQL 15\n- Frontend: React 18, TypeScript 5.0, Material-UI\n- Infrastructure: Kubernetes, AWS EKS, Redis Cluster",
                "dateCreated": "2024-01-15T09:00:00Z",
                "dateUpdated": "2024-03-20T14:30:00Z",
                "category": "architecture",
                "tags": ["architecture", "microservices", "security", "performance"],
                "author": "Sarah Johnson",
                "status": "published"
            },
            {
                "id": "conf_002",
                "type": "confluence",
                "title": "Data Retention Policy",
                "content": "# Data Retention Policy\n\n## Overview\nThis document outlines the data retention policies for the Financial Services Platform.\n\n## Retention Periods\n\n### Customer Data\n- **Active Accounts**: Retained indefinitely\n- **Closed Accounts**: Retained for 7 years after closure\n- **Failed Login Attempts**: Retained for 90 days\n\n### Transaction Data\n- **All Transactions**: Retained for 7 years\n- **Transaction Logs**: Retained for 3 years\n- **Audit Logs**: Retained for 7 years",
                "dateCreated": "2024-02-01T10:00:00Z",
                "dateUpdated": "2024-02-15T14:20:00Z",
                "category": "compliance",
                "tags": ["data_retention", "gdpr", "compliance"],
                "author": "Lisa Rodriguez",
                "status": "published"
            },
            {
                "id": "conf_003",
                "type": "confluence",
                "title": "API Documentation - Account Management",
                "content": "# Account Management API\n\n## Overview\nThe Account Management API provides comprehensive account lifecycle management.\n\n## Endpoints\n\n### GET /api/v1/accounts\nRetrieve account information for authenticated user.\n\n**Parameters:**\n- accountId (optional): Specific account ID\n\n**Response:**\n```json\n{\n  \"accountId\": \"12345\",\n  \"balance\": 1500.00,\n  \"currency\": \"USD\",\n  \"status\": \"active\"\n}\n```\n\n### POST /api/v1/accounts\nCreate new account for customer.",
                "dateCreated": "2024-01-20T11:15:00Z",
                "dateUpdated": "2024-02-15T16:45:00Z",
                "category": "api",
                "tags": ["api", "documentation", "account_management"],
                "author": "Mike Chen",
                "status": "published"
            },

            # CONTRADICTORY DOCUMENT - Conflicts with data retention policy
            {
                "id": "conf_conflict_001",
                "type": "confluence",
                "title": "Updated Data Retention Policy",
                "content": "# Updated Data Retention Policy\n\n## Overview\nThis document outlines the updated data retention policies for compliance and operational efficiency.\n\n## Retention Periods\n\n### Customer Data\n- **Active Accounts**: Retained indefinitely\n- **Closed Accounts**: Retained for 7 days after closure\n- **Failed Login Attempts**: Retained for 1 day\n\n### Transaction Data\n- **All Transactions**: Retained for 7 days\n- **Transaction Logs**: Retained for 1 day\n- **Audit Logs**: Retained for 30 days\n\n## Note: This conflicts with the main data retention policy which specifies 7 years retention for transaction data.",
                "dateCreated": "2024-02-01T10:00:00Z",
                "dateUpdated": "2024-02-15T14:20:00Z",
                "category": "compliance",
                "tags": ["data_retention", "gdpr", "compliance", "conflict"],
                "author": "Emma Wilson",
                "status": "published"
            },

            # SPARSE DOCUMENT
            {
                "id": "conf_sparse_001",
                "type": "confluence",
                "title": "Mobile App Design Guidelines",
                "content": "Use Material Design. Keep it simple.",
                "dateCreated": "2024-02-10T15:45:00Z",
                "dateUpdated": "2024-02-10T15:45:00Z",
                "category": "design",
                "tags": ["mobile", "design"],
                "author": "Alex Thompson",
                "status": "draft"
            },

            # BLANK DOCUMENT
            {
                "id": "conf_blank_001",
                "type": "confluence",
                "title": "Third-Party Integration Documentation",
                "content": "",  # BLANK DOCUMENT
                "dateCreated": "2024-02-14T11:10:00Z",
                "dateUpdated": "2024-02-14T11:10:00Z",
                "category": "integration",
                "tags": ["integration", "third_party"],
                "author": "Robert Davis",
                "status": "draft"
            },

            # JIRA TICKETS
            {
                "id": "jira_001",
                "type": "jira",
                "title": "Implement User Authentication System",
                "content": "As a user, I want to be able to securely log into the mobile banking app so that I can access my account information.\n\n## Acceptance Criteria\n- Users can register with email and password\n- Users can login with email and password\n- Password must be at least 8 characters with special characters\n- Implement password reset functionality\n- Multi-factor authentication support\n- Session management with automatic logout",
                "dateCreated": "2024-01-10T09:15:00Z",
                "dateUpdated": "2024-02-20T14:30:00Z",
                "category": "feature",
                "tags": ["authentication", "security", "mobile"],
                "author": "Sarah Johnson",
                "assignee": "Mike Chen",
                "status": "in_progress",
                "priority": "high",
                "comments": [
                    {
                        "author": "Mike Chen",
                        "timestamp": "2024-01-12T10:30:00Z",
                        "content": "Started implementation of OAuth2 flow. Need to clarify MFA requirements."
                    },
                    {
                        "author": "Sarah Johnson",
                        "timestamp": "2024-01-12T14:15:00Z",
                        "content": "MFA is required for all users. Please implement SMS-based 2FA initially."
                    }
                ]
            },
            {
                "id": "jira_002",
                "type": "jira",
                "title": "Fix Memory Leak in Transaction Processing",
                "content": "Memory leak detected in transaction processing service causing gradual performance degradation.\n\n## Steps to Reproduce\n1. Process 1000+ transactions per minute for 2 hours\n2. Monitor memory usage\n3. Observe memory continuously increasing without garbage collection\n\n## Expected Behavior\nMemory usage should stabilize after initial warm-up period.\n\n## Actual Behavior\nMemory usage grows from 2GB to 8GB over 2 hours with no recovery.",
                "dateCreated": "2024-01-25T16:45:00Z",
                "dateUpdated": "2024-02-10T13:20:00Z",
                "category": "bug",
                "tags": ["memory_leak", "performance", "transaction_processing"],
                "author": "Lisa Rodriguez",
                "assignee": "David Kim",
                "status": "resolved",
                "priority": "critical",
                "comments": [
                    {
                        "author": "David Kim",
                        "timestamp": "2024-01-26T09:30:00Z",
                        "content": "Investigating memory leak. Found issue in connection pooling configuration."
                    },
                    {
                        "author": "David Kim",
                        "timestamp": "2024-01-28T14:15:00Z",
                        "content": "Root cause identified: PreparedStatement objects not being closed properly in batch processing."
                    }
                ]
            },
            {
                "id": "jira_003",
                "type": "jira",
                "title": "Data Retention Policy Implementation",
                "content": "Implement automated data retention and deletion policies.\n\n## Requirements\n- Customer data retention: 7 years after account closure\n- Transaction data retention: 7 years\n- Failed login attempts: 90 days\n- GDPR deletion requests: immediate processing\n\n## Note: This conflicts with the policy document which states transaction data should be retained for 7 days.",
                "dateCreated": "2024-02-01T10:00:00Z",
                "dateUpdated": "2024-03-15T16:30:00Z",
                "category": "feature",
                "tags": ["data_retention", "gdpr", "compliance", "conflict"],
                "author": "Emma Wilson",
                "assignee": "Robert Davis",
                "status": "in_progress",
                "priority": "high"
            },

            # GAP IDENTIFICATION DOCUMENT
            {
                "id": "jira_gap_001",
                "type": "jira",
                "title": "Mobile App Deployment Strategy",
                "content": "We need to define and implement a deployment strategy for our mobile applications.\n\n## Current Problem\n- No automated deployment pipeline for mobile apps\n- Manual deployment process taking 2-3 days\n- No beta testing infrastructure\n- Missing app store deployment automation\n\n## Requirements\n- Automated build and deployment for iOS and Android\n- Beta testing distribution\n- App store submission automation\n- Rollback capabilities\n- Performance monitoring\n\n## Blocked By\n- Mobile architecture not finalized\n- Code signing certificates not procured\n- App store developer accounts not set up\n\n## Note: This represents a significant gap in our development infrastructure.",
                "dateCreated": "2024-02-15T13:20:00Z",
                "dateUpdated": "2024-03-01T09:30:00Z",
                "category": "infrastructure",
                "tags": ["mobile", "deployment", "ci_cd", "gap"],
                "author": "Mike Chen",
                "assignee": "David Kim",
                "status": "blocked",
                "priority": "high"
            },

            # PULL REQUESTS
            {
                "id": "pr_001",
                "type": "pull_request",
                "title": "Implement OAuth2 Authentication System",
                "content": "This PR implements OAuth2 authentication with JWT tokens for the mobile banking application.\n\n## Changes Made\n\n### Backend Changes\n- Added OAuth2 configuration in Spring Security\n- Implemented JWT token generation and validation\n- Added user authentication endpoints\n- Created password hashing utilities\n\n### Database Changes\n- Added user_credentials table\n- Added user_sessions table\n- Added oauth_tokens table",
                "dateCreated": "2024-01-15T14:30:00Z",
                "dateUpdated": "2024-01-22T09:45:00Z",
                "category": "feature",
                "tags": ["authentication", "oauth2", "security", "jwt"],
                "author": "Mike Chen",
                "status": "merged",
                "comments": [
                    {
                        "author": "Sarah Johnson",
                        "timestamp": "2024-01-18T10:20:00Z",
                        "content": "Code looks good. Can you add more comprehensive error handling for OAuth2 exceptions?"
                    },
                    {
                        "author": "Mike Chen",
                        "timestamp": "2024-01-18T14:15:00Z",
                        "content": "Added comprehensive error handling and proper HTTP status codes for OAuth2 errors."
                    }
                ]
            },
            {
                "id": "pr_002",
                "type": "pull_request",
                "title": "Fix Memory Leak in Transaction Processor",
                "content": "This PR fixes a critical memory leak in the transaction processing service.\n\n## Problem\nThe transaction processor was not properly closing database connections and prepared statements, leading to gradual memory consumption and eventual service crashes.\n\n## Root Cause\n- PreparedStatement objects not being closed in batch processing\n- Database connection leaks in error handling paths\n- ResultSet objects not being properly closed",
                "dateCreated": "2024-01-28T11:15:00Z",
                "dateUpdated": "2024-02-05T16:20:00Z",
                "category": "bug_fix",
                "tags": ["memory_leak", "performance", "database", "transaction_processing"],
                "author": "David Kim",
                "status": "merged"
            },

            # SIMILAR DOCUMENTS (API Documentation variations)
            {
                "id": "conf_similar_001",
                "type": "confluence",
                "title": "API Documentation - User Management",
                "content": "# User Management API\n\n## Overview\nThe User Management API provides comprehensive user lifecycle management.\n\n## Endpoints\n\n### GET /api/v1/users\nRetrieve user information for authenticated user.\n\n**Parameters:**\n- userId (optional): Specific user ID\n\n**Response:**\n```json\n{\n  \"userId\": \"12345\",\n  \"email\": \"user@example.com\",\n  \"status\": \"active\"\n}\n```\n\n### POST /api/v1/users\nCreate new user account.",
                "dateCreated": "2024-01-20T11:16:00Z",
                "dateUpdated": "2024-02-15T16:46:00Z",
                "category": "api",
                "tags": ["api", "documentation", "user_management"],
                "author": "Mike Chen",
                "status": "published"
            },
            {
                "id": "conf_similar_002",
                "type": "confluence",
                "title": "API Documentation - User Management v2",
                "content": "# User Management API\n\n## Overview\nThe User Management API provides comprehensive user lifecycle management.\n\n## Endpoints\n\n### GET /api/v1/users\nRetrieve user information for authenticated user.\n\n**Parameters:**\n- userId (optional): Specific user ID\n\n**Response:**\n```json\n{\n  \"userId\": \"12345\",\n  \"email\": \"user@example.com\",\n  \"status\": \"active\"\n}\n```\n\n### POST /api/v1/users\nCreate new user account.",
                "dateCreated": "2024-01-20T11:17:00Z",
                "dateUpdated": "2024-02-15T16:47:00Z",
                "category": "api",
                "tags": ["api", "documentation", "user_management"],
                "author": "Mike Chen",
                "status": "published"
            }
        ]

    def get_documents_by_type(self, doc_type: str) -> List[Dict[str, Any]]:
        """Get documents filtered by type (confluence, jira, pull_request)."""
        return [doc for doc in self.documents if doc.get("type", "").lower() == doc_type.lower()]

    def get_documents_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get documents filtered by category."""
        return [doc for doc in self.documents if doc.get("category", "").lower() == category.lower()]

    def get_similar_documents(self) -> List[Dict[str, Any]]:
        """Get documents that are highly similar (for testing deduplication)."""
        return [doc for doc in self.documents if "similar" in doc.get("id", "")]

    def get_contradictory_documents(self) -> List[Dict[str, Any]]:
        """Get documents with contradictory content."""
        return [doc for doc in self.documents if "conflict" in doc.get("tags", [])]

    def get_gap_documents(self) -> List[Dict[str, Any]]:
        """Get documents that identify gaps in development."""
        return [doc for doc in self.documents if "gap" in doc.get("tags", []) or "gap" in doc.get("id", "")]

    def get_sparse_documents(self) -> List[Dict[str, Any]]:
        """Get documents with sparse/minimal content."""
        return [doc for doc in self.documents if "sparse" in doc.get("id", "") or len(doc.get("content", "")) < 50]

    def get_blank_documents(self) -> List[Dict[str, Any]]:
        """Get documents with blank/empty content."""
        return [doc for doc in self.documents if not doc.get("content", "").strip()]

    def get_documents_with_comments(self) -> List[Dict[str, Any]]:
        """Get documents that have conversation history/comments."""
        return [doc for doc in self.documents if doc.get("comments")]

    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all sample documents."""
        return self.documents.copy()

    def get_documents_for_query(self, query: str) -> List[Dict[str, Any]]:
        """Get relevant documents based on query content analysis."""
        query_lower = query.lower()

        relevant_docs = []

        # Check for specific keywords that map to document types
        if "financial" in query_lower or "banking" in query_lower:
            relevant_docs.extend(self.get_documents_by_category("architecture"))
            relevant_docs.extend(self.get_documents_by_category("security"))

        if "api" in query_lower or "documentation" in query_lower:
            relevant_docs.extend(self.get_documents_by_category("api"))
            relevant_docs.extend(self.get_similar_documents())

        if "jira" in query_lower or "ticket" in query_lower or "bug" in query_lower:
            relevant_docs.extend(self.get_documents_by_type("jira"))

        if "pull request" in query_lower or "pr" in query_lower or "code review" in query_lower:
            relevant_docs.extend(self.get_documents_by_type("pull_request"))

        if "confluence" in query_lower or "wiki" in query_lower or "page" in query_lower:
            relevant_docs.extend(self.get_documents_by_type("confluence"))

        if "conflict" in query_lower or "contradiction" in query_lower:
            relevant_docs.extend(self.get_contradictory_documents())

        if "gap" in query_lower or "missing" in query_lower:
            relevant_docs.extend(self.get_gap_documents())

        # Remove duplicates while preserving order
        seen_ids = set()
        unique_docs = []
        for doc in relevant_docs:
            if doc["id"] not in seen_ids:
                seen_ids.add(doc["id"])
                unique_docs.append(doc)

        # If no specific matches, return a subset of diverse documents
        if not unique_docs:
            return self.documents[:5]  # Return first 5 documents

        return unique_docs[:10]  # Limit to 10 most relevant documents


# Global instance for easy access
sample_documents = SampleDocumentRepository()
