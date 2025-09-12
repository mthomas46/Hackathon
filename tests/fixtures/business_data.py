"""Business Data Fixtures - Modular business domain fixtures.

This module now serves as a compatibility layer that orchestrates the
modular business fixture components for backward compatibility.

Components are now available in:
- fixtures/user_fixtures.py: User-related fixtures
- fixtures/repository_fixtures.py: Repository-related fixtures
- fixtures/workflow_fixtures.py: Workflow-related fixtures
- fixtures/documentation_fixtures.py: Documentation-related fixtures
- fixtures/jira_fixtures.py: Jira-related fixtures
- fixtures/github_fixtures.py: GitHub-related fixtures

This maintains backward compatibility while enabling focused, modular development.
"""

# Import from modular components for backward compatibility
from .user_fixtures import *
from .repository_fixtures import *
from .workflow_fixtures import *
from .documentation_fixtures import *
from .jira_fixtures import *
from .github_fixtures import *

# Ensure core fixtures are available at module level
__all__ = [
    # User fixtures
    "sample_user", "sample_users", "admin_user", "developer_user",
    "manager_user", "qa_user", "inactive_user", "guest_user",
    "user_with_profile", "users_by_role", "users_by_department",
    "large_user_set",
    
    # Repository fixtures
    "sample_repository", "sample_repositories", "python_repository",
    "javascript_repository", "private_repository", "repository_with_ci",
    "repository_with_issues", "repository_with_contributors",
    "repository_with_releases", "repository_with_dependencies",
    "repositories_by_language", "repositories_by_visibility",
    
    # Workflow fixtures
    "sample_workflow", "sample_workflows", "ci_workflow",
    "deployment_workflow", "security_workflow", "business_workflow",
    "failed_workflow", "workflow_with_artifacts", "workflow_with_matrix",
    "workflow_templates", "workflow_metrics",
    
    # Documentation fixtures
    "sample_confluence_page", "sample_github_wiki",
    "confluence_api_page", "confluence_troubleshooting_page",
    "github_readme", "github_contributing_guide",
    "documentation_with_images", "documentation_with_code",
    "documentation_search_results", "documentation_metrics",
    "documentation_templates",
    
    # Jira fixtures
    "sample_jira_ticket", "sample_jira_epic", "jira_bug_ticket",
    "jira_task_ticket", "jira_project", "jira_sprint",
    "jira_workflow_states", "jira_transition", "jira_comment",
    "jira_attachment", "jira_search_results", "jira_board",
    
    # GitHub fixtures
    "sample_pull_request", "sample_github_issue", "sample_commit",
    "github_webhook_payload", "github_release", "github_check_run",
    "github_repository_event", "github_deployment",
    "github_branch_protection", "github_search_results", "github_workflow_run"
]
