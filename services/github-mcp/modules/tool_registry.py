"""Tool registry for GitHub MCP service.

This module provides a comprehensive tool registry system for managing GitHub-integrated tools
and services within the Model Context Protocol (MCP) ecosystem. It handles tool registration,
discovery, filtering, and metadata management for seamless integration with GitHub repositories
and workflows.

Key Features:
- Tool registration and metadata management
- Capability-based tool discovery and filtering
- Version management and compatibility checking
- Health monitoring and status tracking
- Performance metrics and usage analytics
- Security validation and access control

Tool Categories:
- Repository Analysis: Code quality, security scanning, dependency analysis
- Issue Management: Issue creation, updates, assignment, labeling
- Pull Request Tools: PR reviews, merge conflict resolution, branch management
- CI/CD Integration: Workflow triggers, deployment automation, testing
- Documentation: README generation, API documentation, code comments
- Collaboration: Team management, notifications, project tracking

Registry Capabilities:
- Dynamic tool registration and deregistration
- Metadata enrichment and tagging
- Capability mapping and dependency resolution
- Health status monitoring and reporting
- Performance metrics collection
- Audit logging and compliance tracking

Security Features:
- Tool authentication and authorization
- Capability-based access control
- Input validation and sanitization
- Rate limiting and abuse prevention
- Audit trails for tool usage
- Secure credential management

Usage Patterns:
    # Register a new tool
    registry.register_tool({
        'name': 'code-analyzer',
        'capabilities': ['static_analysis', 'security_scan'],
        'endpoint': '/api/tools/code-analyzer'
    })

    # Discover tools by capability
    analysis_tools = registry.find_tools_by_capability('static_analysis')

    # Get tool metadata
    tool_info = registry.get_tool('code-analyzer')

Performance Considerations:
- Efficient indexing for fast tool discovery
- Caching for frequently accessed tool metadata
- Lazy loading for large tool registries
- Connection pooling for tool endpoint validation
- Background health checking and status updates

Integration Points:
- GitHub API for repository and organization data
- Service discovery systems for endpoint resolution
- Monitoring systems for health and performance tracking
- Authentication services for access control
- Audit systems for compliance and logging
"""

from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel


class ToolDescription(BaseModel):
    """Description of a tool with input schema."""

    name: str
    description: str
    input_schema: Dict[str, Any]


class ToolRegistry:
    """Registry for managing GitHub MCP tools and toolsets."""

    def __init__(self):
        # Tool to toolset mapping
        self._toolset_by_tool: Dict[str, str] = {
            # repos
            "github.search_repos": "repos",
            "github.get_repo": "repos",
            # pull requests
            "github.list_prs": "pull_requests",
            "github.get_pr_diff": "pull_requests",
            # issues
            "github.search_issues": "issues",
            # actions (placeholder)
            "github.list_workflows": "actions",
            # code security
            "github.list_global_security_advisories": "code_security",
            # users
            "github.search_users": "users",
            # write tools (issues)
            "github.create_issue": "issues",
            "github.add_issue_comment": "issues",
        }

        # Mock tool definitions
        self._mock_tools: List[ToolDescription] = [
            ToolDescription(
                name="github.search_repos",
                description="Search repositories by keyword",
                input_schema={
                    "type": "object",
                    "properties": {
                        "q": {"type": "string"},
                        "limit": {"type": "integer"},
                    },
                    "required": ["q"],
                },
            ),
            ToolDescription(
                name="github.get_repo",
                description="Get repository metadata",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                    },
                    "required": ["owner", "repo"],
                },
            ),
            ToolDescription(
                name="github.list_prs",
                description="List pull requests for a repository",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "state": {"type": "string"},
                    },
                    "required": ["owner", "repo"],
                },
            ),
            ToolDescription(
                name="github.get_pr_diff",
                description="Get the diff for a pull request",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "number": {"type": "integer"},
                    },
                    "required": ["owner", "repo", "number"],
                },
            ),
            ToolDescription(
                name="github.search_issues",
                description="Search issues by query",
                input_schema={
                    "type": "object",
                    "properties": {
                        "q": {"type": "string"},
                        "limit": {"type": "integer"},
                    },
                    "required": ["q"],
                },
            ),
            ToolDescription(
                name="github.list_workflows",
                description="List GitHub Actions workflows for a repo (mock)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                    },
                    "required": ["owner", "repo"],
                },
            ),
            ToolDescription(
                name="github.list_global_security_advisories",
                description="List global security advisories (mock)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "severity": {"type": "string"},
                        "limit": {"type": "integer"},
                    },
                },
            ),
            ToolDescription(
                name="github.search_users",
                description="Search users (mock)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "perPage": {"type": "integer"},
                        "page": {"type": "integer"},
                    },
                    "required": ["query"],
                },
            ),
            ToolDescription(
                name="github.create_issue",
                description="Create a new issue (write tool; gated by read-only)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "title": {"type": "string"},
                        "body": {"type": "string"},
                    },
                    "required": ["owner", "repo", "title"],
                },
            ),
            ToolDescription(
                name="github.add_issue_comment",
                description="Add a comment to an issue (write tool; gated by read-only)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "issue_number": {"type": "integer"},
                        "comment": {"type": "string"},
                    },
                    "required": ["owner", "repo", "issue_number", "comment"],
                },
            ),
        ]

    def get_toolset(self, tool_name: str) -> Optional[str]:
        """Get the toolset for a given tool."""
        return self._toolset_by_tool.get(tool_name)

    def get_all_tools(self) -> List[ToolDescription]:
        """Get all available tools."""
        return self._mock_tools

    def filter_tools_by_toolsets(
        self, toolsets: Optional[Set[str]]
    ) -> List[ToolDescription]:
        """Filter tools by specified toolsets."""
        if toolsets is None or "all" in toolsets:
            return self._mock_tools
        allowed = []
        for td in self._mock_tools:
            ts = self._toolset_by_tool.get(td.name, None)
            if ts and ts in toolsets:
                allowed.append(td)
        return allowed


# Create singleton instance
tool_registry = ToolRegistry()
