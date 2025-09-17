"""
GitHub MCP Service Adapter

Comprehensive adapter for the GitHub MCP service providing unified CLI interface
for GitHub tool invocation, repository operations, and GitHub API interactions.
"""

from typing import List, Tuple, Any, Dict
import time
from .base_service_adapter import BaseServiceAdapter, ServiceInfo, ServiceStatus, CommandResult


class GitHubMCPAdapter(BaseServiceAdapter):
    """
    Unified adapter for GitHub MCP Service
    
    Provides standardized access to:
    - GitHub repository operations
    - Issue management
    - Pull request operations
    - File operations
    - Search functionality
    - GitHub API interactions
    """
    
    def get_service_info(self) -> ServiceInfo:
        """Get GitHub MCP Service information"""
        return ServiceInfo(
            name="github-mcp",
            port=5072,
            version="0.1.0",
            status=ServiceStatus.HEALTHY,
            description="GitHub MCP tool invocation and data operation service",
            features=[
                "Repository Operations",
                "Issue Management",
                "Pull Request Operations",
                "File Operations",
                "Search Functionality",
                "GitHub API Integration",
                "Branch Management",
                "Webhook Management"
            ],
            dependencies=["redis"],
            endpoints={
                "health": "/health",
                "repositories": "/repositories",
                "issues": "/issues",
                "pulls": "/pulls",
                "files": "/files",
                "search": "/search",
                "branches": "/branches",
                "commits": "/commits",
                "webhooks": "/webhooks"
            }
        )
    
    async def health_check(self) -> CommandResult:
        """Perform comprehensive health check"""
        try:
            start_time = time.time()
            
            # Test health endpoint
            health_url = f"{self.base_url}/health"
            health_response = await self.clients.get_json(health_url)
            
            execution_time = time.time() - start_time
            
            if health_response and health_response.get('status') == 'healthy':
                return CommandResult(
                    success=True,
                    data=health_response,
                    message="GitHub MCP service is fully operational",
                    execution_time=execution_time
                )
            else:
                return CommandResult(
                    success=False,
                    error="GitHub MCP health check failed",
                    execution_time=execution_time
                )
                
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Health check error: {str(e)}"
            )
    
    async def get_available_commands(self) -> List[Tuple[str, str, str]]:
        """Get available GitHub MCP commands"""
        return [
            ("list_repos", "List GitHub repositories", "list_repos [owner] [limit]"),
            ("get_repo", "Get repository information", "get_repo [owner/repo]"),
            ("list_issues", "List repository issues", "list_issues [owner/repo] [state]"),
            ("create_issue", "Create new issue", "create_issue [owner/repo] [title] [body]"),
            ("list_pulls", "List pull requests", "list_pulls [owner/repo] [state]"),
            ("get_file", "Get file content", "get_file [owner/repo] [path] [ref]"),
            ("search_repos", "Search repositories", "search_repos [query] [limit]"),
            ("search_code", "Search code", "search_code [query] [repo]"),
            ("list_branches", "List repository branches", "list_branches [owner/repo]"),
            ("get_commits", "Get commit history", "get_commits [owner/repo] [branch]"),
            ("create_webhook", "Create repository webhook", "create_webhook [owner/repo] [url]"),
            ("health_detailed", "Get detailed health information", "health_detailed")
        ]
    
    async def execute_command(self, command: str, **kwargs) -> CommandResult:
        """Execute GitHub MCP commands"""
        try:
            start_time = time.time()
            
            if command == "list_repos":
                return await self._list_repositories(kwargs)
            elif command == "get_repo":
                return await self._get_repository(kwargs)
            elif command == "list_issues":
                return await self._list_issues(kwargs)
            elif command == "create_issue":
                return await self._create_issue(kwargs)
            elif command == "list_pulls":
                return await self._list_pull_requests(kwargs)
            elif command == "get_file":
                return await self._get_file(kwargs)
            elif command == "search_repos":
                return await self._search_repositories(kwargs)
            elif command == "search_code":
                return await self._search_code(kwargs)
            elif command == "list_branches":
                return await self._list_branches(kwargs)
            elif command == "get_commits":
                return await self._get_commits(kwargs)
            elif command == "create_webhook":
                return await self._create_webhook(kwargs)
            elif command == "health_detailed":
                return await self.health_check()
            else:
                return CommandResult(
                    success=False,
                    error=f"Unknown command: {command}"
                )
                
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Command execution failed: {str(e)}"
            )
    
    # Private command implementations
    async def _list_repositories(self, params: Dict) -> CommandResult:
        """List GitHub repositories"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/repositories"
            
            # Add query parameters
            query_params = {
                "owner": params.get("owner", ""),
                "limit": params.get("limit", 10)
            }
            
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            repo_count = len(response) if isinstance(response, list) else 0
            return CommandResult(
                success=True,
                data=response,
                message=f"Retrieved {repo_count} repositories",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to list repositories: {str(e)}"
            )
    
    async def _get_repository(self, params: Dict) -> CommandResult:
        """Get repository information"""
        try:
            start_time = time.time()
            repo = params.get("repo", "owner/repo")
            url = f"{self.base_url}/repositories/{repo}"
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Retrieved information for repository {repo}",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to get repository: {str(e)}"
            )
    
    async def _list_issues(self, params: Dict) -> CommandResult:
        """List repository issues"""
        try:
            start_time = time.time()
            repo = params.get("repo", "owner/repo")
            state = params.get("state", "open")
            url = f"{self.base_url}/repositories/{repo}/issues"
            
            query_params = {"state": state}
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            issue_count = len(response) if isinstance(response, list) else 0
            return CommandResult(
                success=True,
                data=response,
                message=f"Retrieved {issue_count} {state} issues for {repo}",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to list issues: {str(e)}"
            )
    
    async def _create_issue(self, params: Dict) -> CommandResult:
        """Create new issue"""
        try:
            start_time = time.time()
            repo = params.get("repo", "owner/repo")
            url = f"{self.base_url}/repositories/{repo}/issues"
            
            payload = {
                "title": params.get("title", "New Issue"),
                "body": params.get("body", "Issue description"),
                "labels": params.get("labels", []),
                "assignees": params.get("assignees", [])
            }
            
            response = await self.clients.post_json(url, payload)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Created issue '{payload['title']}' in {repo}",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to create issue: {str(e)}"
            )
    
    async def _list_pull_requests(self, params: Dict) -> CommandResult:
        """List pull requests"""
        try:
            start_time = time.time()
            repo = params.get("repo", "owner/repo")
            state = params.get("state", "open")
            url = f"{self.base_url}/repositories/{repo}/pulls"
            
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            pr_count = len(response) if isinstance(response, list) else 0
            return CommandResult(
                success=True,
                data=response,
                message=f"Retrieved {pr_count} {state} pull requests for {repo}",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to list pull requests: {str(e)}"
            )
    
    async def _get_file(self, params: Dict) -> CommandResult:
        """Get file content"""
        try:
            start_time = time.time()
            repo = params.get("repo", "owner/repo")
            path = params.get("path", "README.md")
            ref = params.get("ref", "main")
            url = f"{self.base_url}/repositories/{repo}/contents/{path}"
            
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Retrieved file {path} from {repo}@{ref}",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to get file: {str(e)}"
            )
    
    async def _search_repositories(self, params: Dict) -> CommandResult:
        """Search repositories"""
        try:
            start_time = time.time()
            query = params.get("query", "python")
            limit = params.get("limit", 10)
            url = f"{self.base_url}/search/repositories"
            
            search_params = {
                "q": query,
                "limit": limit
            }
            
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            result_count = len(response.get("items", [])) if response else 0
            return CommandResult(
                success=True,
                data=response,
                message=f"Found {result_count} repositories matching '{query}'",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Repository search failed: {str(e)}"
            )
    
    async def _search_code(self, params: Dict) -> CommandResult:
        """Search code"""
        try:
            start_time = time.time()
            query = params.get("query", "function")
            repo = params.get("repo", "")
            url = f"{self.base_url}/search/code"
            
            search_params = {
                "q": query + (f" repo:{repo}" if repo else "")
            }
            
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            result_count = len(response.get("items", [])) if response else 0
            return CommandResult(
                success=True,
                data=response,
                message=f"Found {result_count} code results matching '{query}'",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Code search failed: {str(e)}"
            )
    
    async def _list_branches(self, params: Dict) -> CommandResult:
        """List repository branches"""
        try:
            start_time = time.time()
            repo = params.get("repo", "owner/repo")
            url = f"{self.base_url}/repositories/{repo}/branches"
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            branch_count = len(response) if isinstance(response, list) else 0
            return CommandResult(
                success=True,
                data=response,
                message=f"Retrieved {branch_count} branches for {repo}",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to list branches: {str(e)}"
            )
    
    async def _get_commits(self, params: Dict) -> CommandResult:
        """Get commit history"""
        try:
            start_time = time.time()
            repo = params.get("repo", "owner/repo")
            branch = params.get("branch", "main")
            url = f"{self.base_url}/repositories/{repo}/commits"
            
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            commit_count = len(response) if isinstance(response, list) else 0
            return CommandResult(
                success=True,
                data=response,
                message=f"Retrieved {commit_count} commits from {repo}@{branch}",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to get commits: {str(e)}"
            )
    
    async def _create_webhook(self, params: Dict) -> CommandResult:
        """Create repository webhook"""
        try:
            start_time = time.time()
            repo = params.get("repo", "owner/repo")
            webhook_url = params.get("url", "https://example.com/webhook")
            url = f"{self.base_url}/repositories/{repo}/hooks"
            
            payload = {
                "url": webhook_url,
                "events": params.get("events", ["push", "pull_request"]),
                "active": params.get("active", True)
            }
            
            response = await self.clients.post_json(url, payload)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Created webhook for {repo} pointing to {webhook_url}",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to create webhook: {str(e)}"
            )
