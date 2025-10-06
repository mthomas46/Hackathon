"""GitHub Extractor Worker - Extract repos, PRs, issues, commits."""

import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from github import Github, GithubException
from tenacity import retry, stop_after_attempt, wait_exponential

from services.workers.celery_app import app
from services.workers.shared.base_worker import BaseExtractor, Document, WorkerResult

logger = logging.getLogger(__name__)


class GitHubExtractor(BaseExtractor):
    """Extract data from GitHub repositories."""
    
    def __init__(self, github_token: Optional[str] = None):
        super().__init__("github")
        self.github_token = github_token
        self.client: Optional[Github] = None
    
    def _init_client(self):
        """Initialize GitHub client."""
        if not self.client:
            if self.github_token:
                self.client = Github(self.github_token)
            else:
                self.client = Github()  # Unauthenticated (60 req/hour)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def extract(self, config: Dict[str, Any]) -> List[Document]:
        """
        Extract documents from GitHub.
        
        Config structure:
        {
            "repos": ["owner/repo"],
            "include_readme": True,
            "include_prs": True,
            "include_issues": True,
            "include_commits": False,
            "max_items_per_repo": 100
        }
        """
        self._init_client()
        
        repos = config.get("repos", [])
        include_readme = config.get("include_readme", True)
        include_prs = config.get("include_prs", False)
        include_issues = config.get("include_issues", False)
        include_commits = config.get("include_commits", False)
        max_items = config.get("max_items_per_repo", 100)
        
        all_documents = []
        
        for repo_name in repos:
            try:
                self.logger.info(f"Extracting from {repo_name}")
                repo = self.client.get_repo(repo_name)
                
                # Extract README
                if include_readme:
                    readme_docs = await self._extract_readme(repo)
                    all_documents.extend(readme_docs)
                
                # Extract Pull Requests
                if include_prs:
                    pr_docs = await self._extract_prs(repo, max_items)
                    all_documents.extend(pr_docs)
                
                # Extract Issues
                if include_issues:
                    issue_docs = await self._extract_issues(repo, max_items)
                    all_documents.extend(issue_docs)
                
                # Extract Recent Commits
                if include_commits:
                    commit_docs = await self._extract_commits(repo, max_items)
                    all_documents.extend(commit_docs)
                
                self.logger.info(f"Extracted {len(all_documents)} documents from {repo_name}")
            
            except GithubException as e:
                self.logger.error(f"GitHub API error for {repo_name}: {e}")
            except Exception as e:
                self.logger.error(f"Error extracting {repo_name}: {e}", exc_info=True)
        
        return all_documents
    
    async def _extract_readme(self, repo) -> List[Document]:
        """Extract README file."""
        try:
            readme = repo.get_readme()
            content = readme.decoded_content.decode("utf-8")
            
            doc = Document(
                doc_id=self._generate_doc_id(repo.full_name, "readme"),
                source="github",
                source_type="readme",
                title=f"{repo.full_name} - README",
                content=content,
                raw_content=content,
                metadata={
                    "repo": repo.full_name,
                    "stars": repo.stargazers_count,
                    "language": repo.language,
                    "topics": repo.get_topics(),
                },
                created_at=repo.created_at,
                updated_at=repo.updated_at,
                url=repo.html_url,
            )
            
            return [doc]
        
        except Exception as e:
            self.logger.warning(f"Could not extract README: {e}")
            return []
    
    async def _extract_prs(self, repo, max_items: int) -> List[Document]:
        """Extract pull requests."""
        docs = []
        
        try:
            prs = repo.get_pulls(state="all", sort="updated", direction="desc")
            
            for i, pr in enumerate(prs):
                if i >= max_items:
                    break
                
                # Combine title, body, and comments
                content_parts = [
                    f"# {pr.title}",
                    "",
                    pr.body or "",
                ]
                
                # Add comments if available
                try:
                    comments = pr.get_comments()
                    if comments.totalCount > 0:
                        content_parts.append("\n## Comments\n")
                        for comment in list(comments)[:10]:  # Max 10 comments
                            content_parts.append(f"**{comment.user.login}:** {comment.body}\n")
                except:
                    pass
                
                content = "\n".join(content_parts)
                
                doc = Document(
                    doc_id=self._generate_doc_id(repo.full_name, f"pr-{pr.number}"),
                    source="github",
                    source_type="pull_request",
                    title=f"PR #{pr.number}: {pr.title}",
                    content=content,
                    raw_content=content,
                    metadata={
                        "repo": repo.full_name,
                        "pr_number": pr.number,
                        "state": pr.state,
                        "merged": pr.merged,
                        "labels": [label.name for label in pr.labels],
                    },
                    created_at=pr.created_at,
                    updated_at=pr.updated_at,
                    author=pr.user.login if pr.user else None,
                    url=pr.html_url,
                )
                
                docs.append(doc)
        
        except Exception as e:
            self.logger.error(f"Error extracting PRs: {e}")
        
        return docs
    
    async def _extract_issues(self, repo, max_items: int) -> List[Document]:
        """Extract issues."""
        docs = []
        
        try:
            issues = repo.get_issues(state="all", sort="updated", direction="desc")
            
            for i, issue in enumerate(issues):
                if i >= max_items:
                    break
                
                # Skip PRs (GitHub issues API includes PRs)
                if issue.pull_request:
                    continue
                
                content_parts = [
                    f"# {issue.title}",
                    "",
                    issue.body or "",
                ]
                
                # Add comments
                try:
                    comments = issue.get_comments()
                    if comments.totalCount > 0:
                        content_parts.append("\n## Comments\n")
                        for comment in list(comments)[:10]:
                            content_parts.append(f"**{comment.user.login}:** {comment.body}\n")
                except:
                    pass
                
                content = "\n".join(content_parts)
                
                doc = Document(
                    doc_id=self._generate_doc_id(repo.full_name, f"issue-{issue.number}"),
                    source="github",
                    source_type="issue",
                    title=f"Issue #{issue.number}: {issue.title}",
                    content=content,
                    raw_content=content,
                    metadata={
                        "repo": repo.full_name,
                        "issue_number": issue.number,
                        "state": issue.state,
                        "labels": [label.name for label in issue.labels],
                    },
                    created_at=issue.created_at,
                    updated_at=issue.updated_at,
                    author=issue.user.login if issue.user else None,
                    url=issue.html_url,
                )
                
                docs.append(doc)
        
        except Exception as e:
            self.logger.error(f"Error extracting issues: {e}")
        
        return docs
    
    async def _extract_commits(self, repo, max_items: int) -> List[Document]:
        """Extract recent commits."""
        docs = []
        
        try:
            commits = repo.get_commits()
            
            for i, commit in enumerate(commits):
                if i >= max_items:
                    break
                
                content = f"# Commit: {commit.commit.message}\n\n{commit.commit.message}"
                
                doc = Document(
                    doc_id=self._generate_doc_id(repo.full_name, f"commit-{commit.sha[:8]}"),
                    source="github",
                    source_type="commit",
                    title=f"Commit {commit.sha[:8]}: {commit.commit.message[:50]}",
                    content=content,
                    raw_content=content,
                    metadata={
                        "repo": repo.full_name,
                        "sha": commit.sha,
                        "additions": commit.stats.additions,
                        "deletions": commit.stats.deletions,
                    },
                    created_at=commit.commit.author.date,
                    author=commit.commit.author.name,
                    url=commit.html_url,
                )
                
                docs.append(doc)
        
        except Exception as e:
            self.logger.error(f"Error extracting commits: {e}")
        
        return docs
    
    def _generate_doc_id(self, repo: str, item: str) -> str:
        """Generate unique document ID."""
        unique_string = f"github:{repo}:{item}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:16]


# Celery task
@app.task(name="extract_github", bind=True)
def extract_github_task(self, config: Dict[str, Any]) -> Dict[str, Any]:
    """Celery task for GitHub extraction."""
    import asyncio
    
    github_token = config.get("github_token")
    extractor = GitHubExtractor(github_token=github_token)
    
    # Run async extraction
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(extractor.process(config))
    
    return result.dict()

