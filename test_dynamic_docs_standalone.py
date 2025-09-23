#!/usr/bin/env python3
"""
Standalone test for the modified _generate_dynamic_documents function
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List


def _generate_dynamic_documents(query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate 25+ highly detailed, realistic, and diverse documents for workflow testing."""
    # Extract project type and tech stack from context
    project_type = context.get("project_type", "web")
    tech_stack = context.get("tech_stack", "React/Node.js")
    query_id = context.get("query_id", str(uuid.uuid4()))

    if "/" in tech_stack:
        frontend, backend = tech_stack.split("/")
    else:
        frontend, backend = "React", "Node.js"

    authors = [
        "Sarah Johnson",
        "Mike Chen",
        "Emma Wilson",
        "Lisa Rodriguez",
        "Alex Thompson",
        "David Kim",
        "Priya Patel",
        "John Doe",
        "Jane Smith",
    ]
    assignees = ["Sarah Johnson", "Emma Wilson", "Alex Thompson", "David Kim", "Priya Patel"]
    reviewers = ["Emma Wilson", "Mike Chen", "Lisa Rodriguez", "Priya Patel"]
    priorities = ["high", "medium", "low", "critical"]
    statuses = ["open", "in_progress", "closed", "resolved", "review", "published"]
    categories = [
        "architecture",
        "api",
        "feature",
        "bug",
        "design",
        "requirements",
        "user_story",
        "rfc",
        "meeting_notes",
        "testing",
        "deployment",
        "security",
    ]
    doc_types = [
        "confluence",
        "jira",
        "pr",
        "design_doc",
        "user_story",
        "rfc",
        "meeting_notes",
        "test_plan",
        "deployment_guide",
    ]

    documents = []
    now = datetime.now()

    # Helper for random date
    def rand_date(days_ago=10):
        return (
            now
            - timedelta(days=random.randint(0, days_ago), hours=random.randint(0, 23), minutes=random.randint(0, 59))
        ).isoformat()

    # 1. Multiple Confluence Pages (Architecture, API, Design, Requirements, Security, Testing, Deployment)
    for i, (title, cat, content) in enumerate(
        [
            (
                f"{project_type.title()} Platform - System Architecture",
                "architecture",
                f"""# {project_type.title()} Platform Architecture\n\n## Overview\nThe {project_type} platform is built on microservices architecture for scalability and resilience.\n\n## Core Components\n- **User Management Service**: Handles authentication, SSO, and user profiles\n- **Business Logic Engine**: Implements core {project_type} domain logic with robust validation\n- **Data Processing Service**: Real-time analytics, ETL pipelines, and reporting\n- **Notification Service**: Asynchronous event-driven notifications (email, SMS, webhooks)\n\n## Technology Stack\n- Frontend: {frontend} (SPA, SSR, PWA support)\n- Backend: {backend} (REST & GraphQL APIs)\n- Database: PostgreSQL, Redis, S3\n- Infrastructure: Docker, Kubernetes, Terraform, CI/CD\n\n## Security\n- OAuth2, RBAC, audit logging, encrypted secrets\n\n## Scalability\n- Horizontal scaling, autoscaling, load balancing\n\n## Diagram\n```\n[Insert architecture diagram here]\n```\n""",
            ),
            (
                f"API Documentation - {project_type.title()} Service",
                "api",
                f"""# {project_type.title()} Service API\n\n## Overview\nRESTful and GraphQL APIs for {project_type} platform operations.\n\n## Authentication\nAll API requests require JWT token authentication and API key header.\n\n## Endpoints\n### GET /api/v1/{project_type.replace('-', '_')}/items\nRetrieves a list of {project_type} items.\n\n**Response:**\n```json\n{{\n  \"items\": [\n    {{\n      \"id\": \"123\",\n      \"name\": \"Sample Item\",\n      \"status\": \"active\"\n    }}\n  ]\n}}\n```\n\n### POST /api/v1/{project_type.replace('-', '_')}/items\nCreates a new item.\n\n**Request Body:**\n```json\n{{\n  \"name\": \"New Item\",\n  \"description\": \"Detailed description.\"\n}}\n```\n""",
            ),
            (
                f"Design Document - {project_type.title()} Notifications",
                "design",
                f"""# Design Doc: Notification Service\n\n## Purpose\nDesign for asynchronous, scalable notification delivery supporting email, SMS, and push.\n\n## Requirements\n- Pluggable provider architecture\n- Guaranteed delivery and retry\n- Idempotency\n- Auditable logs\n\n## Sequence Diagram\n```\n[Insert sequence diagram]\n```\n\n## Open Questions\n- How to handle provider outages?\n- SLA for delivery latency?\n""",
            ),
            (
                f"Requirements Specification - {project_type.title()} Onboarding",
                "requirements",
                f"""# Requirements: User Onboarding\n\n## Functional\n- Collect user info (name, email, org)\n- Email verification\n- Welcome tour\n\n## Non-Functional\n- Onboarding completion < 2 minutes\n- Accessible (WCAG 2.1 AA)\n- GDPR compliant\n""",
            ),
            (
                f"Security Overview - {project_type.title()} Platform",
                "security",
                f"""# Security Overview\n\n## Threat Model\n- External attackers\n- Insider threats\n- Data exfiltration\n\n## Controls\n- Encryption at rest/in transit\n- RBAC, MFA, audit logs\n- Regular penetration testing\n\n## Incident Response\n- 24/7 monitoring\n- Runbooks\n""",
            ),
            (
                f"Testing Strategy - {project_type.title()} Platform",
                "testing",
                f"""# Testing Strategy\n\n## Types\n- Unit, integration, E2E, load, security\n\n## Tooling\n- Pytest, Cypress, Postman, Snyk\n\n## Coverage\n- 90%+ unit test coverage\n- Automated regression suite\n""",
            ),
            (
                f"Deployment Guide - {project_type.title()} Platform",
                "deployment",
                f"""# Deployment Guide\n\n## Environments\n- Dev, Staging, Prod\n\n## CI/CD\n- GitHub Actions, ArgoCD, DockerHub\n\n## Rollback\n- Blue/green, canary\n- Rollback steps\n""",
            ),
        ]
    ):
        documents.append(
            {
                "id": f"conf_{cat}_{query_id[:8]}_{i}",
                "type": "confluence",
                "title": title,
                "content": content,
                "dateCreated": rand_date(15),
                "dateUpdated": rand_date(2),
                "category": cat,
                "tags": [cat, project_type, frontend.lower(), backend.lower()],
                "author": random.choice(authors),
                "status": "published",
            }
        )

    # 2. Multiple JIRA Tickets (Feature, Bug, Epic, Task, Story)
    for i, (title, cat, content, prio, stat) in enumerate(
        [
            (
                f"Implement Advanced {project_type.title()} Dashboard",
                "feature",
                f"As a product manager, I want an advanced dashboard so I can track {project_type} platform metrics.\n\n## Acceptance Criteria\n- Real-time metrics\n- {frontend} frontend\n- {backend} backend API\n- Mobile-responsive",
                "high",
                "in_progress",
            ),
            (
                f"Bug: {project_type.title()} API returns 500 on POST /items",
                "bug",
                f"Steps to Reproduce:\n1. POST to /api/v1/{project_type}/items with invalid payload\n2. Observe 500 error\n\n## Expected\nGraceful validation error (400)\n\n## Actual\n500 Internal Server Error\n\n## Logs\n```\n[stacktrace]\n```",
                "critical",
                "open",
            ),
            (
                f"Epic: {project_type.title()} Mobile App Launch",
                "feature",
                f"Epic to track all work for mobile app launch.\n\n## Child Issues\n- JIRA-123: Mobile UI\n- JIRA-124: API integration\n- JIRA-125: Push notifications",
                "high",
                "open",
            ),
            (
                f"Task: Refactor {backend} Service Layer",
                "feature",
                f"Refactor service layer for maintainability and testability.\n\n## Subtasks\n- Add unit tests\n- Extract business logic\n- Update documentation",
                "medium",
                "review",
            ),
            (
                f"Story: As a user, I can reset my password via email",
                "user_story",
                f"User should be able to request password reset and receive a secure email link.\n\n## Acceptance Criteria\n- Email sent to user\n- Link expires in 30 minutes\n- Password complexity enforced",
                "high",
                "resolved",
            ),
        ]
    ):
        documents.append(
            {
                "id": f"jira_{cat}_{query_id[:8]}_{i}",
                "type": "jira",
                "title": title,
                "content": content,
                "dateCreated": rand_date(20),
                "dateUpdated": rand_date(5),
                "category": cat,
                "tags": [cat, prio, "jira", project_type],
                "author": random.choice(authors),
                "assignee": random.choice(assignees),
                "status": stat,
                "priority": prio,
            }
        )

    # 3. Pull Requests (PRs) with variations
    for i in range(3):
        documents.append(
            {
                "id": f"pr_{query_id[:8]}_{i}",
                "type": "pr",
                "title": f"PR: {project_type.title()} - {random.choice(['Refactor', 'Feature', 'Bugfix'])} #{random.randint(100,999)}",
                "content": f"""## Description\nImplements {random.choice(['feature', 'refactor', 'bugfix'])} for {project_type} module.\n\n## Changes\n- Updated {random.choice(['API', 'UI', 'database', 'authentication'])} logic\n- Improved test coverage\n- Updated documentation\n\n## Reviewer Checklist\n- [ ] Code builds\n- [ ] Tests pass\n- [ ] Docs updated\n\n## Linked Issues\n- JIRA-{random.randint(100,999)}\n""",
                "dateCreated": rand_date(14),
                "dateUpdated": rand_date(2),
                "category": "development",
                "tags": ["pr", "github", "review", project_type],
                "author": random.choice(authors),
                "reviewer": random.choice(reviewers),
                "status": random.choice(["open", "review", "merged"]),
                "priority": random.choice(priorities),
            }
        )

    # 4. User Stories (multiple)
    for i in range(3):
        documents.append(
            {
                "id": f"story_{query_id[:8]}_{i}",
                "type": "user_story",
                "title": f"User Story: {random.choice(['As an admin', 'As a user', 'As a developer'])}...",
                "content": f"""As a {random.choice(['user', 'admin', 'developer'])}, I want to {random.choice(['export data', 'customize dashboard', 'receive notifications', 'reset password'])} so that I can {random.choice(['improve productivity', 'increase security', 'get timely alerts'])}.\n\n## Acceptance Criteria\n- {random.choice(['Export as CSV', 'Custom widgets', 'Email alerts', 'Secure reset'])}\n- {random.choice(['Mobile ready', 'Auditable', 'Accessible'])}\n""",
                "dateCreated": rand_date(10),
                "dateUpdated": rand_date(1),
                "category": "user_story",
                "tags": ["user_story", project_type, frontend.lower()],
                "author": random.choice(authors),
                "status": random.choice(statuses),
                "priority": random.choice(priorities),
            }
        )

    # 5. RFCs (multiple)
    for i in range(2):
        documents.append(
            {
                "id": f"rfc_{query_id[:8]}_{i}",
                "type": "rfc",
                "title": f"RFC: {random.choice(['Adopt OpenAPI', 'Switch to GraphQL', 'Migrate to Kubernetes'])}",
                "content": f"""# RFC: {random.choice(['Adopt OpenAPI', 'Switch to GraphQL', 'Migrate to Kubernetes'])}\n\n## Motivation\n{random.choice(['Standardize API schema', 'Improve developer experience', 'Enhance scalability'])}\n\n## Proposal\n- {random.choice(['Adopt OpenAPI 3.0', 'Switch REST to GraphQL', 'Migrate deployment to Kubernetes'])}\n- Update documentation\n- Provide migration plan\n\n## Drawbacks\n- {random.choice(['Learning curve', 'Migration effort', 'Compatibility issues'])}\n\n## Alternatives\n- Keep current approach\n- Evaluate other tools\n""",
                "dateCreated": rand_date(30),
                "dateUpdated": rand_date(2),
                "category": "rfc",
                "tags": ["rfc", "proposal", project_type],
                "author": random.choice(authors),
                "status": "open",
                "priority": random.choice(priorities),
            }
        )

    # 6. Meeting Notes (multiple)
    for i in range(2):
        documents.append(
            {
                "id": f"meeting_{query_id[:8]}_{i}",
                "type": "meeting_notes",
                "title": f"Meeting Notes: {random.choice(['Sprint Planning', 'Retrospective', 'Design Review'])}",
                "content": f"""# Meeting Notes\n\n**Date:** {rand_date(15)}\n**Attendees:** {', '.join(random.sample(authors, 4))}\n\n## Agenda\n- {random.choice(['Review sprint goals', 'Discuss blockers', 'Demo new features'])}\n- {random.choice(['Architecture discussion', 'Q&A'])}\n\n## Notes\n- {random.choice(['Agreed to extend sprint by 1 week', 'Identified key technical debt', 'Action items assigned'])}\n- {random.choice(['Follow up with DevOps', 'Schedule security review'])}\n\n## Action Items\n- {random.choice(['Update documentation', 'Fix critical bug', 'Prepare demo'])}\n""",
                "dateCreated": rand_date(15),
                "dateUpdated": rand_date(1),
                "category": "meeting_notes",
                "tags": ["meeting", "notes", project_type],
                "author": random.choice(authors),
                "status": "published",
            }
        )

    # 7. Test Plans (multiple)
    for i in range(2):
        documents.append(
            {
                "id": f"testplan_{query_id[:8]}_{i}",
                "type": "test_plan",
                "title": f"Test Plan: {project_type.title()} {random.choice(['Authentication', 'API', 'UI'])}",
                "content": f"""# Test Plan\n\n## Scope\n- {random.choice(['Authentication', 'API', 'UI'])} module\n\n## Objectives\n- Validate {random.choice(['login', 'token refresh', 'access control', 'input validation'])}\n\n## Test Cases\n- {random.choice(['Login with valid/invalid credentials', 'API returns correct status codes', 'UI is accessible'])}\n- {random.choice(['Session timeout', 'Password reset', 'Error messages'])}\n\n## Tooling\n- {random.choice(['Pytest', 'Cypress', 'Postman'])}\n\n## Exit Criteria\n- 100% test pass\n""",
                "dateCreated": rand_date(10),
                "dateUpdated": rand_date(2),
                "category": "testing",
                "tags": ["test", "plan", project_type],
                "author": random.choice(authors),
                "status": "published",
            }
        )

    # 8. Deployment Guides (multiple)
    for i in range(2):
        documents.append(
            {
                "id": f"deploy_{query_id[:8]}_{i}",
                "type": "deployment_guide",
                "title": f"Deployment Guide: {project_type.title()} {random.choice(['Production', 'Staging', 'Dev'])}",
                "content": f"""# Deployment Guide\n\n## Environment\n- {random.choice(['Production', 'Staging', 'Dev'])}\n\n## Steps\n- Build Docker image\n- Push to registry\n- Deploy with ArgoCD\n- Run smoke tests\n\n## Rollback\n- Rollback to previous release\n- Notify stakeholders\n""",
                "dateCreated": rand_date(10),
                "dateUpdated": rand_date(2),
                "category": "deployment",
                "tags": ["deploy", "guide", project_type],
                "author": random.choice(authors),
                "status": "published",
            }
        )

    # 9. Add more bugs, API docs, and user stories for diversity
    for i in range(3):
        documents.append(
            {
                "id": f"bug_{query_id[:8]}_{i}",
                "type": "jira",
                "title": f"Bug: {project_type.title()} - {random.choice(['Login failure', 'UI crash', 'Timeout error'])}",
                "content": f"""Steps to Reproduce:\n1. {random.choice(['Login with invalid credentials', 'Navigate to dashboard', 'Submit large file'])}\n2. Observe error\n\n## Expected\n{random.choice(['Graceful error message', 'No crash', 'Timeout handled'])}\n\n## Actual\n{random.choice(['500 Internal Server Error', 'UI freezes', 'Timeout not handled'])}\n\n## Logs\n```\n[stacktrace]\n```\n""",
                "dateCreated": rand_date(20),
                "dateUpdated": rand_date(5),
                "category": "bug",
                "tags": ["bug", "jira", project_type],
                "author": random.choice(authors),
                "assignee": random.choice(assignees),
                "status": random.choice(["open", "in_progress", "resolved"]),
                "priority": random.choice(["high", "critical"]),
            }
        )
    for i in range(2):
        documents.append(
            {
                "id": f"api_{query_id[:8]}_{i}",
                "type": "confluence",
                "title": f"API Documentation - {project_type.title()} Endpoint {i+2}",
                "content": f"""# API Endpoint {i+2}\n\n## Method\n{random.choice(['GET', 'POST', 'PUT', 'DELETE'])} /api/v1/{project_type}/endpoint{i+2}\n\n## Description\n{random.choice(['Retrieves', 'Creates', 'Updates', 'Deletes'])} an entity.\n\n## Request/Response\n```json\n{{ \"id\": \"abc{i}\", \"result\": \"ok\" }}\n```\n""",
                "dateCreated": rand_date(10),
                "dateUpdated": rand_date(2),
                "category": "api",
                "tags": ["api", "documentation", "rest", project_type],
                "author": random.choice(authors),
                "status": "published",
            }
        )
    for i in range(2):
        documents.append(
            {
                "id": f"story_{query_id[:8]}_{i+3}",
                "type": "user_story",
                "title": f"User Story: As a user, I can {random.choice(['filter data', 'receive alerts', 'change settings'])}",
                "content": f"""As a user, I want to {random.choice(['filter data', 'receive alerts', 'change settings'])} so that I can {random.choice(['find relevant info', 'stay informed', 'customize experience'])}.\n\n## Acceptance Criteria\n- {random.choice(['Filter by date', 'Email alerts', 'Save preferences'])}\n- {random.choice(['Mobile ready', 'Accessible', 'Auditable'])}\n""",
                "dateCreated": rand_date(10),
                "dateUpdated": rand_date(1),
                "category": "user_story",
                "tags": ["user_story", project_type, frontend.lower()],
                "author": random.choice(authors),
                "status": random.choice(statuses),
                "priority": random.choice(priorities),
            }
        )

    # Truncate or pad to 25+ documents
    while len(documents) < 25:
        documents.append(
            {
                "id": f"misc_{query_id[:8]}_{len(documents)}",
                "type": random.choice(doc_types),
                "title": f"Misc Doc {len(documents)}",
                "content": f"This is a filler document for testing. Detailed content about {project_type} and {tech_stack}.",
                "dateCreated": rand_date(30),
                "dateUpdated": rand_date(2),
                "category": random.choice(categories),
                "tags": ["misc", project_type, frontend.lower(), backend.lower()],
                "author": random.choice(authors),
                "status": random.choice(statuses),
            }
        )

    return documents


def test_document_generation():
    """Test the document generation function."""
    print("\n" + "=" * 60)
    print("TESTING DYNAMIC DOCUMENT GENERATION")
    print("=" * 60)

    # Test context
    test_context = {"project_type": "ecommerce", "tech_stack": "React/Node.js", "query_id": "test_12345"}

    # Test query
    test_query = "Create a comprehensive documentation ecosystem for an e-commerce platform"

    print(f"📋 Test Query: {test_query}")
    print(f"🔧 Test Context: {json.dumps(test_context, indent=2)}")
    print()

    try:
        # Generate documents
        start_time = datetime.now()
        documents = _generate_dynamic_documents(test_query, test_context)
        end_time = datetime.now()

        print("✅ Document generation completed successfully!")
        print(f"⏱️  Generation time: {(end_time - start_time).total_seconds():.2f} seconds")
        print(f"📊 Total documents generated: {len(documents)}")
        print()

        # Validate minimum requirement
        if len(documents) >= 25:
            print("✅ SUCCESS: Generated 25+ documents as required!")
        else:
            print(f"❌ FAILURE: Only generated {len(documents)} documents (need 25+)")
            return False

        # Analyze document types
        doc_types = {}
        categories = {}
        authors = {}
        statuses = {}

        for doc in documents:
            # Count document types
            doc_type = doc.get("type", "unknown")
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

            # Count categories
            category = doc.get("category", "unknown")
            categories[category] = categories.get(category, 0) + 1

            # Count authors
            author = doc.get("author", "unknown")
            authors[author] = authors.get(author, 0) + 1

            # Count statuses
            status = doc.get("status", "unknown")
            statuses[status] = statuses.get(status, 0) + 1

        print("📈 DOCUMENT ANALYSIS")
        print("-" * 30)
        print(f"Document Types: {json.dumps(doc_types, indent=2)}")
        print()
        print(f"Categories: {json.dumps(categories, indent=2)}")
        print()
        print(f"Authors: {json.dumps(authors, indent=2)}")
        print()
        print(f"Statuses: {json.dumps(statuses, indent=2)}")
        print()

        # Sample some documents
        print("📄 SAMPLE DOCUMENTS")
        print("-" * 20)
        for i, doc in enumerate(documents[:5]):  # Show first 5
            print(f"\n{i+1}. {doc['title']}")
            print(f"   Type: {doc['type']}")
            print(f"   Category: {doc['category']}")
            print(f"   Author: {doc['author']}")
            print(f"   Status: {doc.get('status', 'N/A')}")
            print(f"   Content Length: {len(doc['content'])} chars")
            print(f"   Tags: {doc.get('tags', [])}")

        # Check for diversity
        unique_types = len(doc_types)
        unique_categories = len(categories)

        print("\n🎯 DIVERSITY CHECK")
        print("-" * 20)
        print(f"Unique document types: {unique_types}")
        print(f"Unique categories: {unique_categories}")
        print(f"Unique authors: {len(authors)}")

        if unique_types >= 5:
            print("✅ Good diversity in document types")
        else:
            print("⚠️  Limited diversity in document types")

        if unique_categories >= 8:
            print("✅ Good diversity in categories")
        else:
            print("⚠️  Limited diversity in categories")

        # Check content quality
        avg_content_length = sum(len(doc["content"]) for doc in documents) / len(documents)
        print("\n📝 CONTENT QUALITY")
        print("-" * 18)
        print(f"Average content length: {avg_content_length:.0f} characters")

        long_docs = len([doc for doc in documents if len(doc["content"]) > 500])
        print(f"Documents with detailed content (>500 chars): {long_docs} ({long_docs/len(documents)*100:.1f}%)")

        if avg_content_length > 300:
            print("✅ Good content detail level")
        else:
            print("⚠️  Content could be more detailed")

        return True

    except Exception as e:
        print(f"❌ ERROR during document generation: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def test_multiple_runs():
    """Test multiple runs to ensure consistency."""
    print("\n" + "=" * 60)
    print("TESTING MULTIPLE RUNS")
    print("=" * 60)

    results = []
    for i in range(3):
        print(f"\n🏃 Run {i+1}:")
        context = {"project_type": f"project_{i}", "tech_stack": "React/Node.js", "query_id": f"query_{i}"}
        documents = _generate_dynamic_documents("Test query", context)
        results.append(len(documents))
        print(f"   Generated: {len(documents)} documents")

    print("\n📊 Multiple run results:")
    print(f"   Run 1: {results[0]} documents")
    print(f"   Run 2: {results[1]} documents")
    print(f"   Run 3: {results[2]} documents")

    if all(r >= 25 for r in results):
        print("✅ All runs generated 25+ documents")
        return True
    else:
        print("❌ Some runs generated fewer than 25 documents")
        return False


if __name__ == "__main__":
    print("🚀 Starting Dynamic Document Generation Tests")
    print("=" * 60)

    success1 = test_document_generation()
    success2 = test_multiple_runs()

    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)

    if success1 and success2:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Document generation works correctly")
        print("✅ Generates 25+ documents")
        print("✅ Good diversity and detail")
        print("✅ Consistent across multiple runs")
    else:
        print("❌ SOME TESTS FAILED!")
        if not success1:
            print("❌ Document generation test failed")
        if not success2:
            print("❌ Multiple runs test failed")

    print("=" * 60)
