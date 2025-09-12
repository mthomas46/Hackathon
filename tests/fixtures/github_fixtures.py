"""GitHub Fixtures - Modular GitHub domain fixtures.

This module now serves as a compatibility layer that orchestrates the
modular GitHub fixture components for backward compatibility.

Components are now available in:
- fixtures/github_pr_fixtures.py: Pull request related fixtures
- fixtures/github_issue_fixtures.py: Issue related fixtures
- fixtures/github_commit_fixtures.py: Commit related fixtures
- fixtures/github_webhook_fixtures.py: Webhook and event fixtures
- fixtures/github_release_fixtures.py: Release related fixtures
- fixtures/github_ci_fixtures.py: CI/CD and workflow fixtures
- fixtures/github_search_fixtures.py: Search and repository fixtures

This maintains backward compatibility while enabling focused, modular development.
"""

# Import from modular components for backward compatibility
from .github_pr_fixtures import *
from .github_issue_fixtures import *
from .github_commit_fixtures import *
from .github_webhook_fixtures import *
from .github_release_fixtures import *
from .github_ci_fixtures import *
from .github_search_fixtures import *

# Ensure core fixtures are available at module level
__all__ = [
    # Pull request fixtures
    "sample_pull_request", "merged_pull_request", "draft_pull_request",
    "pull_request_with_reviews", "pull_request_with_conflicts",
    "pull_request_templates", "pull_request_metrics",

    # Issue fixtures
    "sample_github_issue", "closed_github_issue", "feature_request_issue",
    "security_issue", "documentation_issue", "issue_with_attachments",
    "issue_templates", "issue_metrics",

    # Commit fixtures
    "sample_commit", "merge_commit", "large_commit", "hotfix_commit",
    "commit_with_co_authors", "revert_commit", "commit_with_tests",
    "commit_templates", "commit_activity_metrics",

    # Webhook fixtures
    "github_webhook_payload", "push_webhook_payload", "issue_webhook_payload",
    "release_webhook_payload", "deployment_webhook_payload",
    "check_run_webhook_payload", "github_repository_event",
    "webhook_headers", "webhook_verification_data",
    "webhook_event_types", "webhook_payload_templates",
    "webhook_processing_metrics",

    # Release fixtures
    "github_release", "prerelease", "draft_release", "major_release",
    "release_with_many_assets", "release_with_milestones",
    "release_notes_templates", "release_management_workflow",
    "release_metrics",

    # CI/CD fixtures
    "github_check_run", "failed_check_run", "github_workflow_run",
    "deployment_check_run", "security_check_run", "github_deployment",
    "failed_deployment", "github_branch_protection",
    "ci_workflow_metrics", "ci_cd_configurations",

    # Search fixtures
    "github_search_results", "github_code_search_results",
    "github_issue_search_results", "github_user_search_results",
    "github_topic_search_results", "github_commit_search_results",
    "github_search_filters", "github_search_suggestions",
    "github_search_metrics"
]
