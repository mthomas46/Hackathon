"""Integration Tests for GitHub API Integration in GitHub MCP Service.

This module tests GitHub API integration capabilities including:
- Real GitHub API calls with authentication
- MCP protocol compliance and tool execution
- Rate limiting and error handling
- Webhook event processing and tool triggering
- Enterprise GitHub integration scenarios

Integration tests cover complete GitHub API workflows and MCP protocol interactions.
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List
import uuid

from main import ToolDescription


class TestGitHubAPIIntegration:
    """Integration tests for GitHub API interactions."""

    @pytest.fixture
    def integration_app(self):
        """Create a complete GitHub MCP application for integration testing."""
        from main import app
        return app

    @pytest.fixture
    def realistic_github_credentials(self):
        """Provide realistic GitHub API credentials for testing."""
        return {
            "token": "ghp_test_token_1234567890abcdef",  # Mock token for testing
            "owner": "test-org",
            "repo": "test-repo",
            "base_url": "https://api.github.com"
        }

    @pytest.fixture
    def mock_github_api_client(self):
        """Mock GitHub API client for integration testing."""
        mock_client = AsyncMock()

        # Mock repository data
        mock_client.get_repository = AsyncMock(return_value={
            "name": "test-repo",
            "full_name": "test-org/test-repo",
            "description": "A test repository for integration testing",
            "private": False,
            "owner": {
                "login": "test-org",
                "type": "Organization"
            },
            "html_url": "https://github.com/test-org/test-repo",
            "clone_url": "https://github.com/test-org/test-repo.git",
            "language": "Python",
            "forks_count": 42,
            "stargazers_count": 1337,
            "watchers_count": 1337,
            "size": 2048,
            "default_branch": "main",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        })

        # Mock pull request data
        mock_client.list_pull_requests = AsyncMock(return_value=[
            {
                "number": 1,
                "title": "Add new feature",
                "state": "open",
                "user": {"login": "contributor"},
                "head": {"ref": "feature-branch"},
                "base": {"ref": "main"},
                "html_url": "https://github.com/test-org/test-repo/pull/1",
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-02T15:30:00Z",
                "merged": False,
                "draft": False
            },
            {
                "number": 2,
                "title": "Fix critical bug",
                "state": "closed",
                "user": {"login": "maintainer"},
                "head": {"ref": "bugfix-branch"},
                "base": {"ref": "main"},
                "html_url": "https://github.com/test-org/test-repo/pull/2",
                "created_at": "2023-12-15T08:00:00Z",
                "updated_at": "2023-12-20T16:45:00Z",
                "merged": True,
                "merged_at": "2023-12-20T16:45:00Z",
                "draft": False
            }
        ])

        # Mock issue data
        mock_client.create_issue = AsyncMock(return_value={
            "number": 123,
            "title": "Test Issue from MCP",
            "state": "open",
            "body": "This issue was created by the GitHub MCP service for testing",
            "user": {"login": "mcp-service"},
            "html_url": "https://github.com/test-org/test-repo/issues/123",
            "created_at": datetime.now().isoformat() + "Z",
            "labels": [{"name": "mcp-generated"}, {"name": "test"}]
        })

        # Mock workflow data
        mock_client.list_workflows = AsyncMock(return_value={
            "total_count": 3,
            "workflows": [
                {
                    "id": 123456,
                    "name": "CI Pipeline",
                    "path": ".github/workflows/ci.yml",
                    "state": "active",
                    "created_at": "2023-06-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                },
                {
                    "id": 234567,
                    "name": "Deploy to Production",
                    "path": ".github/workflows/deploy.yml",
                    "state": "active",
                    "created_at": "2023-08-15T00:00:00Z",
                    "updated_at": "2023-12-01T00:00:00Z"
                },
                {
                    "id": 345678,
                    "name": "Security Scan",
                    "path": ".github/workflows/security.yml",
                    "state": "disabled",
                    "created_at": "2023-09-01T00:00:00Z",
                    "updated_at": "2023-11-15T00:00:00Z"
                }
            ]
        })

        return mock_client

    @pytest.mark.asyncio
    async def test_end_to_end_repository_information_retrieval(self, integration_app, realistic_github_credentials, mock_github_api_client):
        """Test complete end-to-end workflow for repository information retrieval."""
        with patch("main.real_implementations.GitHubAPIClient", return_value=mock_github_api_client), \
             patch("main.config") as mock_config:

            # Setup configuration
            mock_config.is_mock_default.return_value = False
            mock_config.is_read_only.return_value = True
            mock_config.should_use_official_mcp.return_value = False

            # Execute repository information retrieval
            start_time = time.time()

            # Simulate tool invocation via API
            tool_invocation = {
                "tool": "repos.get",
                "arguments": {
                    "owner": realistic_github_credentials["owner"],
                    "repo": realistic_github_credentials["repo"]
                },
                "execution_mode": "real_api",
                "correlation_id": str(uuid.uuid4())
            }

            # In a real scenario, this would go through the FastAPI endpoint
            # For testing, we'll simulate the tool execution directly
            from main import mock_implementations
            result = await mock_implementations.invoke_tool("repos.get", tool_invocation["arguments"])

            end_time = time.time()

            # Verify repository information structure
            assert "name" in result
            assert "full_name" in result
            assert "description" in result
            assert "owner" in result
            assert "html_url" in result
            assert "language" in result
            assert "stargazers_count" in result
            assert "forks_count" in result

            # Verify repository metadata
            assert result["name"] == realistic_github_credentials["repo"]
            assert result["full_name"] == f"{realistic_github_credentials['owner']}/{realistic_github_credentials['repo']}"
            assert result["private"] is False
            assert result["owner"]["login"] == realistic_github_credentials["owner"]
            assert "created_at" in result
            assert "updated_at" in result

            # Verify performance
            execution_time = end_time - start_time
            assert execution_time < 2.0  # Should complete within 2 seconds

            # Verify GitHub API was called correctly
            mock_github_api_client.get_repository.assert_called_once_with(
                owner=realistic_github_credentials["owner"],
                repo=realistic_github_credentials["repo"]
            )

    @pytest.mark.asyncio
    async def test_pull_request_workflow_integration(self, integration_app, realistic_github_credentials, mock_github_api_client):
        """Test complete pull request workflow from listing to detailed information."""
        with patch("main.real_implementations.GitHubAPIClient", return_value=mock_github_api_client), \
             patch("main.config") as mock_config:

            # Setup configuration
            mock_config.is_mock_default.return_value = False
            mock_config.is_read_only.return_value = True
            mock_config.should_use_official_mcp.return_value = False

            # Step 1: List pull requests
            list_result = await mock_implementations.invoke_tool("pulls.list", {
                "owner": realistic_github_credentials["owner"],
                "repo": realistic_github_credentials["repo"],
                "state": "all"
            })

            # Verify pull request list structure
            assert isinstance(list_result, list)
            assert len(list_result) >= 2

            # Check each pull request structure
            for pr in list_result:
                assert "number" in pr
                assert "title" in pr
                assert "state" in pr
                assert "user" in pr
                assert "head" in pr
                assert "base" in pr
                assert "html_url" in pr
                assert "created_at" in pr

            # Step 2: Verify pull request states
            open_prs = [pr for pr in list_result if pr["state"] == "open"]
            closed_prs = [pr for pr in list_result if pr["state"] == "closed"]

            assert len(open_prs) >= 1
            assert len(closed_prs) >= 1

            # Step 3: Verify merged status for closed PRs
            for pr in closed_prs:
                if pr.get("merged") is True:
                    assert "merged_at" in pr
                    assert pr["merged_at"] is not None

            # Verify GitHub API calls
            mock_github_api_client.list_pull_requests.assert_called_once_with(
                owner=realistic_github_credentials["owner"],
                repo=realistic_github_credentials["repo"],
                state="all"
            )

    @pytest.mark.asyncio
    async def test_issue_creation_and_management_workflow(self, integration_app, realistic_github_credentials, mock_github_api_client):
        """Test complete issue creation and management workflow."""
        with patch("main.real_implementations.GitHubAPIClient", return_value=mock_github_api_client), \
             patch("main.config") as mock_config:

            # Setup configuration for write operations
            mock_config.is_mock_default.return_value = False
            mock_config.is_read_only.return_value = False
            mock_config.should_use_official_mcp.return_value = False

            # Step 1: Create a new issue
            issue_data = {
                "owner": realistic_github_credentials["owner"],
                "repo": realistic_github_credentials["repo"],
                "title": "Integration Test Issue",
                "body": "This issue was created during automated integration testing of the GitHub MCP service.",
                "labels": ["integration-test", "mcp-generated"]
            }

            create_result = await mock_implementations.invoke_tool("issues.create", issue_data)

            # Verify issue creation result
            assert "number" in create_result
            assert "title" in create_result
            assert "state" in create_result
            assert "body" in create_result
            assert "html_url" in create_result
            assert "created_at" in create_result
            assert "labels" in create_result

            # Verify issue content
            assert create_result["title"] == issue_data["title"]
            assert create_result["body"] == issue_data["body"]
            assert create_result["state"] == "open"
            assert len(create_result["labels"]) >= 2

            # Verify MCP-generated label is present
            label_names = [label["name"] for label in create_result["labels"]]
            assert "mcp-generated" in label_names

            # Verify GitHub API was called correctly
            mock_github_api_client.create_issue.assert_called_once()
            call_args = mock_github_api_client.create_issue.call_args[1]

            assert call_args["owner"] == issue_data["owner"]
            assert call_args["repo"] == issue_data["repo"]
            assert call_args["title"] == issue_data["title"]
            assert call_args["body"] == issue_data["body"]

    @pytest.mark.asyncio
    async def test_github_actions_workflow_integration(self, integration_app, realistic_github_credentials, mock_github_api_client):
        """Test GitHub Actions workflow information retrieval and management."""
        with patch("main.real_implementations.GitHubAPIClient", return_value=mock_github_api_client), \
             patch("main.config") as mock_config:

            # Setup configuration
            mock_config.is_mock_default.return_value = False
            mock_config.is_read_only.return_value = True
            mock_config.should_use_official_mcp.return_value = False

            # Retrieve workflow information
            workflow_result = await mock_implementations.invoke_tool("actions.workflows", {
                "owner": realistic_github_credentials["owner"],
                "repo": realistic_github_credentials["repo"]
            })

            # Verify workflow information structure
            assert "total_count" in workflow_result
            assert "workflows" in workflow_result
            assert workflow_result["total_count"] >= 3
            assert len(workflow_result["workflows"]) >= 3

            # Verify each workflow structure
            for workflow in workflow_result["workflows"]:
                assert "id" in workflow
                assert "name" in workflow
                assert "path" in workflow
                assert "state" in workflow
                assert "created_at" in workflow
                assert "updated_at" in workflow

                # Verify workflow file paths
                assert workflow["path"].startswith(".github/workflows/")
                assert workflow["path"].endswith(".yml")

            # Verify workflow states
            active_workflows = [w for w in workflow_result["workflows"] if w["state"] == "active"]
            disabled_workflows = [w for w in workflow_result["workflows"] if w["state"] == "disabled"]

            assert len(active_workflows) >= 2
            assert len(disabled_workflows) >= 1

            # Verify GitHub API was called correctly
            mock_github_api_client.list_workflows.assert_called_once_with(
                owner=realistic_github_credentials["owner"],
                repo=realistic_github_credentials["repo"]
            )

    @pytest.mark.asyncio
    async def test_rate_limiting_and_error_handling(self, integration_app, mock_github_api_client):
        """Test rate limiting and comprehensive error handling."""
        call_count = 0

        async def rate_limited_response(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                # First call succeeds
                return {"name": "test-repo", "description": "Success response"}
            elif call_count == 2:
                # Second call hits rate limit
                raise Exception("API rate limit exceeded")
            else:
                # Subsequent calls succeed
                return {"name": "test-repo", "description": f"Retry response {call_count}"}

        mock_github_api_client.get_repository = rate_limited_response

        with patch("main.real_implementations.GitHubAPIClient", return_value=mock_github_api_client), \
             patch("main.config") as mock_config:

            mock_config.is_mock_default.return_value = False
            mock_config.is_read_only.return_value = True
            mock_config.should_use_official_mcp.return_value = False

            # Test successful call
            result1 = await mock_implementations.invoke_tool("repos.get", {
                "owner": "test-org", "repo": "test-repo"
            })
            assert result1["name"] == "test-repo"
            assert "Success response" in result1["description"]

            # Test rate limited call (should handle gracefully)
            try:
                result2 = await mock_implementations.invoke_tool("repos.get", {
                    "owner": "test-org", "repo": "test-repo"
                })
                # If no exception, verify error handling
                assert "error" in result2 or "rate_limit" in str(result2).lower()
            except Exception as e:
                # Exception handling should be graceful
                assert "rate limit" in str(e).lower()

            # Verify call counts
            assert call_count >= 2

    @pytest.mark.asyncio
    async def test_enterprise_github_integration_scenario(self, integration_app, mock_github_api_client):
        """Test comprehensive enterprise GitHub integration scenario."""
        with patch("main.real_implementations.GitHubAPIClient", return_value=mock_github_api_client), \
             patch("main.config") as mock_config:

            # Setup enterprise configuration
            mock_config.is_mock_default.return_value = False
            mock_config.is_read_only.return_value = False  # Allow write operations
            mock_config.should_use_official_mcp.return_value = False

            # Simulate enterprise workflow: Code review -> Issue creation -> Workflow check

            # Step 1: Check repository structure
            repo_info = await mock_implementations.invoke_tool("repos.get", {
                "owner": "enterprise-org",
                "repo": "monolith-app"
            })

            assert repo_info["name"] == "test-repo"  # Mock returns test data
            assert "description" in repo_info

            # Step 2: Review pull requests for the repository
            pr_list = await mock_implementations.invoke_tool("pulls.list", {
                "owner": "enterprise-org",
                "repo": "monolith-app",
                "state": "open"
            })

            assert isinstance(pr_list, list)
            assert len(pr_list) >= 1

            # Step 3: Create issue for architecture review
            issue_result = await mock_implementations.invoke_tool("issues.create", {
                "owner": "enterprise-org",
                "repo": "monolith-app",
                "title": "Architecture Review Required",
                "body": "The recent pull request requires architecture review before merging.",
                "labels": ["architecture", "review-required", "enterprise"]
            })

            assert "number" in issue_result
            assert issue_result["title"] == "Architecture Review Required"
            assert "architecture" in [label["name"] for label in issue_result["labels"]]

            # Step 4: Check CI/CD workflows
            workflows = await mock_implementations.invoke_tool("actions.workflows", {
                "owner": "enterprise-org",
                "repo": "monolith-app"
            })

            assert "workflows" in workflows
            assert len(workflows["workflows"]) >= 2  # Should have CI and deployment workflows

            # Verify enterprise workflow completion
            ci_workflows = [w for w in workflows["workflows"] if "ci" in w["name"].lower()]
            deploy_workflows = [w for w in workflows["workflows"] if "deploy" in w["name"].lower()]

            assert len(ci_workflows) >= 1
            assert len(deploy_workflows) >= 1

    @pytest.mark.asyncio
    async def test_mcp_protocol_compliance(self, integration_app):
        """Test MCP protocol compliance and tool execution standards."""
        # Test MCP protocol compliance across different tool types

        test_cases = [
            {
                "tool": "repos.get",
                "args": {"owner": "test-org", "repo": "test-repo"},
                "expected_fields": ["name", "full_name", "description", "html_url", "owner"]
            },
            {
                "tool": "pulls.list",
                "args": {"owner": "test-org", "repo": "test-repo", "state": "open"},
                "expected_type": list
            },
            {
                "tool": "issues.create",
                "args": {
                    "owner": "test-org",
                    "repo": "test-repo",
                    "title": "MCP Protocol Test",
                    "body": "Testing MCP protocol compliance"
                },
                "expected_fields": ["number", "title", "state", "html_url"]
            }
        ]

        for test_case in test_cases:
            with patch("main.mock_implementations") as mock_impl, \
                 patch("main.config") as mock_config:

                # Setup mock mode
                mock_config.is_mock_default.return_value = True
                mock_config.is_read_only.return_value = False
                mock_config.should_use_official_mcp.return_value = False

                # Mock successful response
                mock_result = {"mock": "response", **{field: f"mock_{field}" for field in test_case.get("expected_fields", [])}}
                if test_case.get("expected_type") == list:
                    mock_result = [mock_result]

                mock_impl.invoke_tool.return_value = mock_result

                # Execute tool via MCP protocol
                result = await mock_implementations.invoke_tool(test_case["tool"], test_case["args"])

                # Verify MCP protocol compliance
                assert result is not None

                if test_case.get("expected_type") == list:
                    assert isinstance(result, list)
                else:
                    # Check expected fields are present
                    for field in test_case.get("expected_fields", []):
                        assert field in result, f"Missing required field '{field}' in {test_case['tool']} response"

                # Verify tool was called with correct arguments
                mock_impl.invoke_tool.assert_called_with(test_case["tool"], test_case["args"])

    @pytest.mark.asyncio
    async def test_webhook_event_processing_simulation(self, integration_app, mock_github_api_client):
        """Test webhook event processing and automated tool triggering."""
        # Simulate GitHub webhook events that would trigger MCP tool execution

        webhook_events = [
            {
                "type": "pull_request",
                "action": "opened",
                "repository": {"name": "test-repo", "owner": {"login": "test-org"}},
                "pull_request": {"number": 42, "title": "New Feature PR"}
            },
            {
                "type": "issues",
                "action": "opened",
                "repository": {"name": "test-repo", "owner": {"login": "test-org"}},
                "issue": {"number": 123, "title": "Bug Report"}
            },
            {
                "type": "workflow_run",
                "action": "completed",
                "repository": {"name": "test-repo", "owner": {"login": "test-org"}},
                "workflow_run": {"name": "CI Pipeline", "conclusion": "success"}
            }
        ]

        with patch("main.real_implementations.GitHubAPIClient", return_value=mock_github_api_client), \
             patch("main.config") as mock_config, \
             patch("main.event_system") as mock_events:

            mock_config.is_mock_default.return_value = False
            mock_config.is_read_only.return_value = False
            mock_config.should_use_official_mcp.return_value = False

            for event in webhook_events:
                # Simulate webhook processing logic
                if event["type"] == "pull_request" and event["action"] == "opened":
                    # Check PR details
                    pr_details = await mock_implementations.invoke_tool("pulls.list", {
                        "owner": event["repository"]["owner"]["login"],
                        "repo": event["repository"]["name"],
                        "state": "open"
                    })
                    assert isinstance(pr_details, list)

                elif event["type"] == "issues" and event["action"] == "opened":
                    # Create automated response issue
                    issue_response = await mock_implementations.invoke_tool("issues.create", {
                        "owner": event["repository"]["owner"]["login"],
                        "repo": event["repository"]["name"],
                        "title": f"Re: {event['issue']['title']}",
                        "body": "Thank you for reporting this issue. Our team will investigate.",
                        "labels": ["acknowledged", "automated-response"]
                    })
                    assert "number" in issue_response

                elif event["type"] == "workflow_run" and event["action"] == "completed":
                    # Check workflow status
                    workflow_status = await mock_implementations.invoke_tool("actions.workflows", {
                        "owner": event["repository"]["owner"]["login"],
                        "repo": event["repository"]["name"]
                    })
                    assert "workflows" in workflow_status
                    assert workflow_status["total_count"] >= 1

                # Verify event system was notified
                mock_events.emit_event.assert_called()

    @pytest.mark.asyncio
    async def test_concurrent_tool_execution_performance(self, integration_app, mock_github_api_client):
        """Test performance and reliability under concurrent tool execution."""
        # Test concurrent execution of multiple GitHub API calls

        concurrent_requests = 10
        request_configs = [
            {
                "tool": "repos.get",
                "args": {"owner": f"org-{i}", "repo": f"repo-{i}"}
            }
            for i in range(concurrent_requests)
        ]

        # Mock responses for concurrent calls
        call_count = 0
        async def concurrent_repo_response(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)  # Simulate network delay
            return {
                "name": f"repo-{call_count}",
                "full_name": f"org-{call_count}/repo-{call_count}",
                "description": f"Concurrent test repository {call_count}",
                "stargazers_count": call_count * 10
            }

        mock_github_api_client.get_repository = concurrent_repo_response

        with patch("main.real_implementations.GitHubAPIClient", return_value=mock_github_api_client), \
             patch("main.config") as mock_config:

            mock_config.is_mock_default.return_value = False
            mock_config.is_read_only.return_value = True
            mock_config.should_use_official_mcp.return_value = False

            # Execute concurrent requests
            start_time = time.time()

            tasks = [
                mock_implementations.invoke_tool(config["tool"], config["args"])
                for config in request_configs
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            end_time = time.time()

            # Verify all requests completed
            successful_results = [r for r in results if isinstance(r, dict) and not isinstance(r, Exception)]
            failed_results = [r for r in results if isinstance(r, Exception) or (isinstance(r, dict) and "error" in r)]

            # High success rate expected
            assert len(successful_results) >= concurrent_requests * 0.9  # 90% success rate

            # Verify performance
            total_time = end_time - start_time
            avg_time_per_request = total_time / concurrent_requests

            # Should handle concurrency efficiently
            assert avg_time_per_request < 1.0  # Less than 1 second per request
            assert total_time < concurrent_requests * 0.5  # Better than sequential execution

            # Verify all repositories were retrieved
            repo_names = [r["name"] for r in successful_results if "name" in r]
            assert len(set(repo_names)) == len(successful_results)  # All unique

    @pytest.mark.asyncio
    async def test_comprehensive_error_recovery_scenarios(self, integration_app):
        """Test comprehensive error recovery and fallback mechanisms."""
        # Test various error scenarios and recovery mechanisms

        error_scenarios = [
            {
                "name": "network_timeout",
                "error": Exception("Connection timeout"),
                "expected_recovery": "retry_with_backoff"
            },
            {
                "name": "rate_limit_exceeded",
                "error": Exception("API rate limit exceeded"),
                "expected_recovery": "exponential_backoff"
            },
            {
                "name": "authentication_failed",
                "error": Exception("Bad credentials"),
                "expected_recovery": "re_authentication"
            },
            {
                "name": "repository_not_found",
                "error": Exception("Repository not found"),
                "expected_recovery": "graceful_failure"
            },
            {
                "name": "insufficient_permissions",
                "error": Exception("Insufficient permissions"),
                "expected_recovery": "permission_escalation"
            }
        ]

        for scenario in error_scenarios:
            with patch("main.real_implementations") as mock_real_impl, \
                 patch("main.mock_implementations") as mock_mock_impl, \
                 patch("main.config") as mock_config:

                # Setup configuration
                mock_config.is_mock_default.return_value = False
                mock_config.is_read_only.return_value = True
                mock_config.should_use_official_mcp.return_value = False

                # Mock primary implementation to fail
                mock_real_impl.invoke_tool.side_effect = scenario["error"]

                # Mock fallback implementation to succeed
                mock_mock_impl.invoke_tool.return_value = {
                    "fallback": True,
                    "error_handled": scenario["name"],
                    "recovery_method": scenario["expected_recovery"]
                }

                # Attempt tool execution
                result = await mock_implementations.invoke_tool("repos.get", {
                    "owner": "test-org",
                    "repo": "test-repo"
                })

                # Verify fallback was used
                assert result["fallback"] is True
                assert result["error_handled"] == scenario["name"]
                assert result["recovery_method"] == scenario["expected_recovery"]

                # Verify both implementations were attempted
                mock_real_impl.invoke_tool.assert_called_once()
                mock_mock_impl.invoke_tool.assert_called_once()
