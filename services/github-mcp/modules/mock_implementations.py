"""Mock implementations for GitHub MCP tools.

Contains mock implementations for all supported GitHub tools.
"""
from typing import Dict, Any
from fastapi import HTTPException


class MockImplementations:
    """Mock implementations for GitHub MCP tools."""

    @staticmethod
    def search_repos(args: Dict[str, Any]) -> Dict[str, Any]:
        """Mock implementation for github.search_repos."""
        q = str(args.get("q", ""))
        limit = int(args.get("limit", 5))
        return {
            "items": [
                {"full_name": f"example/{q}-repo-{i}", "stars": 100 - i, "language": "python"}
                for i in range(max(0, min(limit, 10)))
            ]
        }

    @staticmethod
    def get_repo(args: Dict[str, Any]) -> Dict[str, Any]:
        """Mock implementation for github.get_repo."""
        owner = args.get("owner", "example")
        repo = args.get("repo", "demo")
        return {
            "full_name": f"{owner}/{repo}",
            "description": "Demo repository",
            "topics": ["docs", "fastapi", "testing"],
            "stars": 123,
        }

    @staticmethod
    def list_prs(args: Dict[str, Any]) -> Dict[str, Any]:
        """Mock implementation for github.list_prs."""
        owner = args.get("owner", "example")
        repo = args.get("repo", "demo")
        state = args.get("state", "open")
        return {
            "items": [
                {"number": n, "title": f"PR {n}", "state": state, "head": {"ref": f"feature-{n}"}}
                for n in range(1, 4)
            ],
            "repo": f"{owner}/{repo}",
        }

    @staticmethod
    def get_pr_diff(args: Dict[str, Any]) -> Dict[str, Any]:
        """Mock implementation for github.get_pr_diff."""
        number = args.get("number", 1)
        return {
            "number": number,
            "diff": """diff --git a/app.py b/app.py
index 111..222 100644
--- a/app.py
+++ b/app.py
@@ -1,3 +1,5 @@
+print('hello')
+print('world')
""",
        }

    @staticmethod
    def search_issues(args: Dict[str, Any]) -> Dict[str, Any]:
        """Mock implementation for github.search_issues."""
        q = str(args.get("q", ""))
        limit = int(args.get("limit", 3))
        return {
            "items": [
                {"number": i, "title": f"Issue {i} about {q}", "state": "open"}
                for i in range(1, limit + 1)
            ]
        }

    @staticmethod
    def list_workflows(args: Dict[str, Any]) -> Dict[str, Any]:
        """Mock implementation for github.list_workflows."""
        owner = args.get("owner", "example")
        repo = args.get("repo", "demo")
        return {"repo": f"{owner}/{repo}", "workflows": [{"name": "ci", "on": ["push", "pull_request"]}]}

    @staticmethod
    def list_global_security_advisories(args: Dict[str, Any]) -> Dict[str, Any]:
        """Mock implementation for github.list_global_security_advisories."""
        severity = args.get("severity", "moderate")
        return {"items": [{"ghsaId": "GHSA-xxxx-xxxx-xxxx", "severity": severity}]}

    @staticmethod
    def search_users(args: Dict[str, Any]) -> Dict[str, Any]:
        """Mock implementation for github.search_users."""
        query = args.get("query", "dev")
        per_page = int(args.get("perPage", 2))
        return {"items": [{"login": f"user{i}", "score": 10 - i} for i in range(per_page)]}

    @staticmethod
    def create_issue(args: Dict[str, Any]) -> Dict[str, Any]:
        """Mock implementation for github.create_issue."""
        return {
            "issue": {
                "number": 1,
                "title": args.get("title", ""),
                "html_url": f"https://github.com/{args.get('owner','org')}/{args.get('repo','repo')}/issues/1",
            },
            "status": "created"
        }

    @staticmethod
    def add_issue_comment(args: Dict[str, Any]) -> Dict[str, Any]:
        """Mock implementation for github.add_issue_comment."""
        return {
            "comment": {
                "id": 1001,
                "issue_number": args.get("issue_number", 1),
                "body": args.get("comment", "")
            },
            "status": "created"
        }

    @staticmethod
    async def invoke_tool(tool: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke the appropriate mock implementation for a tool."""
        implementations = {
            "github.search_repos": MockImplementations.search_repos,
            "github.get_repo": MockImplementations.get_repo,
            "github.list_prs": MockImplementations.list_prs,
            "github.get_pr_diff": MockImplementations.get_pr_diff,
            "github.search_issues": MockImplementations.search_issues,
            "github.list_workflows": MockImplementations.list_workflows,
            "github.list_global_security_advisories": MockImplementations.list_global_security_advisories,
            "github.search_users": MockImplementations.search_users,
            "github.create_issue": MockImplementations.create_issue,
            "github.add_issue_comment": MockImplementations.add_issue_comment,
        }

        impl = implementations.get(tool)
        if impl is None:
            raise HTTPException(status_code=404, detail=f"Unknown tool: {tool}")

        return impl(args)


# Create singleton instance
mock_implementations = MockImplementations()
