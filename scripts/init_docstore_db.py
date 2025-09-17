#!/usr/bin/env python3
"""Doc Store Database Initialization and Seeding Script.

This script initializes the Doc Store database with all required tables and indexes,
and can optionally seed it with realistic test data for development and testing.
"""

import os
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.doc_store.db.schema import init_database
from services.doc_store.db.connection import get_doc_store_connection, return_doc_store_connection
from services.doc_store.db.queries import execute_query


def seed_test_data():
    """Seed database with realistic but clearly marked test data."""
    print("🌱 Seeding database with test data...")

    # Test documents across different types
    test_documents = [
        # GitHub-related documents
        {
            "id": "test-github-readme-001",
            "content": "# Test Project\n\nThis is a test README for development.\n\n## Features\n- Feature 1\n- Feature 2\n\n## Installation\n```bash\npip install test-project\n```",
            "content_hash": "hash_test_readme_001",
            "metadata": {
                "type": "github_readme",
                "source": "github.com/test/repo",
                "language": "markdown",
                "category": "documentation",
                "is_test_data": True,
                "test_marker": "DEVELOPMENT_TEST_DATA"
            },
            "correlation_id": "test-session-001"
        },
        {
            "id": "test-github-issue-001",
            "content": "## Issue: Bug in authentication\n\n**Description:** Users cannot log in with valid credentials.\n\n**Steps to reproduce:**\n1. Go to login page\n2. Enter valid credentials\n3. Click login\n\n**Expected:** User should be logged in\n**Actual:** Error message displayed\n\n**Environment:**\n- Browser: Chrome 91\n- OS: macOS 12.1",
            "content_hash": "hash_test_issue_001",
            "metadata": {
                "type": "github_issue",
                "source": "github.com/test/repo/issues/123",
                "status": "open",
                "labels": ["bug", "authentication", "high-priority"],
                "is_test_data": True,
                "test_marker": "DEVELOPMENT_TEST_DATA"
            },
            "correlation_id": "test-session-001"
        },
        # Jira documents
        {
            "id": "test-jira-epic-001",
            "content": "# Epic: User Management System\n\n## Overview\nImplement a comprehensive user management system including authentication, authorization, and profile management.\n\n## Stories\n- As a user, I want to register an account\n- As a user, I want to log in securely\n- As an admin, I want to manage user roles\n\n## Acceptance Criteria\n- Secure authentication with JWT\n- Role-based access control\n- User profile management\n- Password reset functionality",
            "content_hash": "hash_test_epic_001",
            "metadata": {
                "type": "jira_epic",
                "source": "company.atlassian.net/browse/PROJ-123",
                "project": "PROJ",
                "status": "in_progress",
                "priority": "high",
                "is_test_data": True,
                "test_marker": "DEVELOPMENT_TEST_DATA"
            },
            "correlation_id": "test-session-001"
        },
        # Confluence pages
        {
            "id": "test-confluence-page-001",
            "content": "# API Documentation\n\n## Authentication\n\nThe API uses JWT tokens for authentication.\n\n### Getting a Token\n```bash\ncurl -X POST /api/auth/login \\\n  -d 'username=user&password=pass'\n```\n\n### Using the Token\n```bash\ncurl -H 'Authorization: Bearer <token>' /api/users\n```\n\n## Endpoints\n\n### GET /api/users\nReturns list of users.\n\n**Response:**\n```json\n[{\"id\": 1, \"name\": \"John Doe\"}]\n```",
            "content_hash": "hash_test_confluence_001",
            "metadata": {
                "type": "confluence_page",
                "source": "company.atlassian.net/wiki/spaces/DEV/pages/12345",
                "space": "DEV",
                "title": "API Documentation",
                "last_modified": "2024-01-15",
                "is_test_data": True,
                "test_marker": "DEVELOPMENT_TEST_DATA"
            },
            "correlation_id": "test-session-001"
        },
        # Code files
        {
            "id": "test-python-code-001",
            "content": '"""User authentication module."""\n\nfrom typing import Optional\nfrom datetime import datetime\nfrom pydantic import BaseModel\n\n\nclass UserCredentials(BaseModel):\n    """User login credentials."""\n    username: str\n    password: str\n\n\nclass UserSession(BaseModel):\n    """User session data."""\n    user_id: int\n    token: str\n    expires_at: datetime\n\n\ndef authenticate_user(credentials: UserCredentials) -> Optional[UserSession]:\n    """Authenticate a user and return session if successful."""\n    # Implementation would go here\n    if credentials.username == "admin" and credentials.password == "secret":\n        return UserSession(\n            user_id=1,\n            token="fake-jwt-token",\n            expires_at=datetime.now()\n        )\n    return None\n\n\ndef validate_token(token: str) -> bool:\n    """Validate JWT token."""\n    # Implementation would go here\n    return token.startswith("fake-")',
            "content_hash": "hash_test_python_001",
            "metadata": {
                "type": "code_file",
                "language": "python",
                "filename": "auth.py",
                "path": "src/auth/",
                "lines": 42,
                "complexity": "medium",
                "is_test_data": True,
                "test_marker": "DEVELOPMENT_TEST_DATA"
            },
            "correlation_id": "test-session-001"
        },
        # API documentation
        {
            "id": "test-api-spec-001",
            "content": '{\n  "openapi": "3.0.1",\n  "info": {\n    "title": "User Management API",\n    "version": "1.0.0",\n    "description": "API for managing users"\n  },\n  "paths": {\n    "/users": {\n      "get": {\n        "summary": "Get all users",\n        "responses": {\n          "200": {\n            "description": "List of users",\n            "content": {\n              "application/json": {\n                "schema": {\n                  "type": "array",\n                  "items": {\n                    "$ref": "#/components/schemas/User"\n                  }\n                }\n              }\n            }\n          }\n        }\n      }\n    }\n  },\n  "components": {\n    "schemas": {\n      "User": {\n        "type": "object",\n        "properties": {\n          "id": {"type": "integer"},\n          "name": {"type": "string"},\n          "email": {"type": "string"}\n        }\n      }\n    }\n  }\n}',
            "content_hash": "hash_test_api_spec_001",
            "metadata": {
                "type": "api_specification",
                "format": "openapi",
                "version": "3.0.1",
                "endpoints": 5,
                "schemas": 3,
                "is_test_data": True,
                "test_marker": "DEVELOPMENT_TEST_DATA"
            },
            "correlation_id": "test-session-001"
        },
        # Analysis results
        {
            "id": "test-analysis-result-001",
            "content": "## Code Analysis Report\n\n### Security Issues\n- **HIGH**: SQL injection vulnerability in user lookup\n- **MEDIUM**: Weak password policy\n\n### Performance Issues\n- **INFO**: N+1 query in user listing endpoint\n\n### Code Quality\n- **INFO**: Missing type hints in 3 functions\n- **INFO**: Code complexity could be reduced in auth.py\n\n### Recommendations\n1. Use parameterized queries for database access\n2. Implement stronger password requirements\n3. Add pagination to user listing\n4. Add type hints throughout codebase\n5. Refactor complex functions",
            "content_hash": "hash_test_analysis_001",
            "metadata": {
                "type": "analysis_report",
                "analyzer": "code_quality_analyzer",
                "target": "src/auth/",
                "issues_found": 6,
                "severity_breakdown": {"high": 1, "medium": 1, "low": 0, "info": 4},
                "is_test_data": True,
                "test_marker": "DEVELOPMENT_TEST_DATA"
            },
            "correlation_id": "test-session-001"
        },
        # Ensemble results
        {
            "id": "test-ensemble-result-001",
            "content": "# Ensemble Analysis Summary\n\n## Multiple Analyzer Consensus\n\n### Security Assessment\n**Consensus Score:** 7.5/10\n\n- **SQL Injection Risk:** High confidence detection\n- **Authentication Strength:** Medium confidence assessment\n- **Input Validation:** Strong consensus on improvements needed\n\n### Performance Assessment\n**Consensus Score:** 8.2/10\n\n- **Query Optimization:** High agreement on N+1 problem\n- **Caching Opportunities:** Medium confidence recommendations\n- **Database Indexing:** Strong consensus on needs\n\n### Code Quality Assessment\n**Consensus Score:** 9.1/10\n\n- **Type Safety:** Near-unanimous agreement on improvements\n- **Documentation:** Strong consensus on API docs completeness\n- **Test Coverage:** High confidence on testing gaps\n\n## Recommendations\n1. **HIGH PRIORITY**: Fix SQL injection vulnerability\n2. **HIGH PRIORITY**: Add comprehensive input validation\n3. **MEDIUM PRIORITY**: Implement database query optimization\n4. **MEDIUM PRIORITY**: Add type hints throughout codebase\n5. **LOW PRIORITY**: Improve test coverage to 90%+",
            "content_hash": "hash_test_ensemble_001",
            "metadata": {
                "type": "ensemble_report",
                "analyzers_used": ["security", "performance", "quality"],
                "consensus_score": 8.3,
                "confidence_level": "high",
                "recommendations_count": 5,
                "is_test_data": True,
                "test_marker": "DEVELOPMENT_TEST_DATA"
            },
            "correlation_id": "test-session-001"
        }
    ]

    # Insert test documents
    for doc in test_documents:
        try:
            execute_query("""
                INSERT OR REPLACE INTO documents
                (id, content, content_hash, metadata, correlation_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                doc["id"],
                doc["content"],
                doc["content_hash"],
                json.dumps(doc["metadata"]),  # Store as proper JSON
                doc.get("correlation_id"),
                datetime.now(timezone.utc).isoformat(),
                datetime.now(timezone.utc).isoformat()
            ))
            print(f"✅ Inserted test document: {doc['id']}")
        except Exception as e:
            print(f"❌ Failed to insert document {doc['id']}: {e}")

    # Create some analysis records for the documents
    analysis_records = [
        {
            "document_id": "test-github-readme-001",
            "analyzer": "content_quality",
            "model": "gpt-4",
            "result": '{"quality_score": 8.5, "readability": "excellent", "completeness": "good"}',
            "score": 8.5
        },
        {
            "document_id": "test-python-code-001",
            "analyzer": "code_security",
            "model": "security_scanner_v1",
            "result": '{"vulnerabilities": 1, "severity": "high", "recommendations": ["Use parameterized queries"]}',
            "score": 2.0
        },
        {
            "document_id": "test-api-spec-001",
            "analyzer": "api_completeness",
            "model": "openapi_validator",
            "result": '{"endpoints_covered": 5, "schemas_defined": 3, "documentation_complete": true}',
            "score": 9.0
        }
    ]

    for analysis in analysis_records:
        try:
            execute_query("""
                INSERT OR REPLACE INTO analyses
                (id, document_id, analyzer, model, result, score, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                f"{analysis['document_id']}_{analysis['analyzer']}",
                analysis["document_id"],
                analysis["analyzer"],
                analysis["model"],
                analysis["result"],
                analysis["score"],
                datetime.now(timezone.utc).isoformat()
            ))
            print(f"✅ Inserted analysis for: {analysis['document_id']}")
        except Exception as e:
            print(f"❌ Failed to insert analysis for {analysis['document_id']}: {e}")

    print("🎉 Test data seeding completed!")
    print(f"📊 Added {len(test_documents)} test documents and {len(analysis_records)} analysis records")
    print("⚠️  All test data is clearly marked with 'is_test_data': true and 'test_marker': 'DEVELOPMENT_TEST_DATA'")


def clean_test_data():
    """Remove all test data from the database."""
    print("🧹 Cleaning test data...")

    try:
        # Delete test documents
        result = execute_query("""
            DELETE FROM documents
            WHERE json_extract(metadata, '$.is_test_data') = 1
               OR json_extract(metadata, '$.test_marker') = 'DEVELOPMENT_TEST_DATA'
        """)
        print(f"✅ Deleted test documents")

        # Delete associated analyses
        result = execute_query("""
            DELETE FROM analyses
            WHERE document_id LIKE 'test-%'
        """)
        print(f"✅ Deleted associated analyses")

        print("🎉 Test data cleanup completed!")
    except Exception as e:
        print(f"❌ Failed to clean test data: {e}")


def main():
    """Main script entry point."""
    parser = argparse.ArgumentParser(description="Doc Store Database Management")
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Seed database with test data"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean test data from database"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force operation without confirmation"
    )

    args = parser.parse_args()

    # Set environment
    os.environ.setdefault('DOCSTORE_DB', str(PROJECT_ROOT / 'services' / 'doc_store' / 'db.sqlite3'))

    print("🏗️  Doc Store Database Management")
    print(f"📍 Database: {os.environ['DOCSTORE_DB']}")

    # Initialize database
    print("🔧 Initializing database schema...")
    try:
        init_database()
        print("✅ Database schema initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        sys.exit(1)

    # Handle operations
    if args.clean:
        if not args.force:
            confirm = input("⚠️  This will delete all test data. Continue? (y/N): ")
            if confirm.lower() != 'y':
                print("Operation cancelled.")
                return
        clean_test_data()

    elif args.seed:
        if not args.force:
            confirm = input("🌱 This will add test data to the database. Continue? (y/N): ")
            if confirm.lower() != 'y':
                print("Operation cancelled.")
                return
        seed_test_data()

    else:
        print("ℹ️  Database initialized. Use --seed to add test data or --clean to remove it.")
        print("📊 Run tests to verify everything works correctly.")


if __name__ == "__main__":
    main()
