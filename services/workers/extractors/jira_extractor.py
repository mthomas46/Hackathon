"""Jira Extractor Worker - Extract issues, projects, and workflows."""

import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from jira import JIRA, JIRAError
from tenacity import retry, stop_after_attempt, wait_exponential

from services.workers.celery_app import app
from services.workers.shared.base_worker import BaseExtractor, Document, WorkerResult

logger = logging.getLogger(__name__)


class JiraExtractor(BaseExtractor):
    """Extract data from Jira projects."""
    
    def __init__(self, url: str, username: str, api_token: str):
        super().__init__("jira")
        self.client = JIRA(
            server=url,
            basic_auth=(username, api_token)
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def extract(self, config: Dict[str, Any]) -> List[Document]:
        """
        Extract documents from Jira.
        
        Config structure:
        {
            "projects": ["PROJ1", "PROJ2"],
            "include_issues": True,
            "include_comments": True,
            "max_issues_per_project": 100,
            "jql_filter": "status != Closed"  # Optional
        }
        """
        projects = config.get("projects", [])
        include_issues = config.get("include_issues", True)
        include_comments = config.get("include_comments", True)
        max_issues = config.get("max_issues_per_project", 100)
        jql_filter = config.get("jql_filter", "")
        
        all_documents = []
        
        for project_key in projects:
            try:
                self.logger.info(f"Extracting from Jira project: {project_key}")
                
                # Extract project info
                project_doc = await self._extract_project(project_key)
                if project_doc:
                    all_documents.append(project_doc)
                
                # Extract issues
                if include_issues:
                    issue_docs = await self._extract_issues(
                        project_key,
                        max_issues,
                        jql_filter,
                        include_comments
                    )
                    all_documents.extend(issue_docs)
                
                self.logger.info(f"Extracted {len(all_documents)} documents from {project_key}")
            
            except Exception as e:
                self.logger.error(f"Error extracting project {project_key}: {e}", exc_info=True)
        
        return all_documents
    
    async def _extract_project(self, project_key: str) -> Optional[Document]:
        """Extract project metadata."""
        try:
            project = self.client.project(project_key)
            
            content = f"""# {project.name}

**Project Key:** {project.key}
**Description:** {project.description or 'No description'}

## Project Details
- Lead: {project.lead.displayName if hasattr(project, 'lead') else 'Unknown'}
- Type: {project.projectTypeKey}
- Categories: {', '.join(getattr(project, 'projectCategory', {}).get('name', 'None'))}
"""
            
            doc = Document(
                doc_id=self._generate_doc_id(f"project-{project.key}"),
                source="jira",
                source_type="project",
                title=f"Project: {project.name}",
                content=content,
                raw_content=content,
                metadata={
                    "project_key": project.key,
                    "project_id": project.id,
                    "project_type": project.projectTypeKey,
                },
                url=project.self,
            )
            
            return doc
        
        except Exception as e:
            self.logger.error(f"Error extracting project: {e}")
            return None
    
    async def _extract_issues(
        self,
        project_key: str,
        max_issues: int,
        jql_filter: str,
        include_comments: bool
    ) -> List[Document]:
        """Extract issues from project."""
        docs = []
        
        try:
            # Build JQL query
            jql = f"project = {project_key}"
            if jql_filter:
                jql += f" AND {jql_filter}"
            jql += " ORDER BY updated DESC"
            
            # Search issues
            start_at = 0
            max_results = 50
            
            while len(docs) < max_issues:
                issues = self.client.search_issues(
                    jql,
                    startAt=start_at,
                    maxResults=max_results,
                    expand="changelog"
                )
                
                if not issues:
                    break
                
                for issue in issues:
                    if len(docs) >= max_issues:
                        break
                    
                    doc = await self._extract_issue(issue, include_comments)
                    if doc:
                        docs.append(doc)
                
                if len(issues) < max_results:
                    break
                
                start_at += max_results
        
        except JIRAError as e:
            self.logger.error(f"Jira API error: {e}")
        except Exception as e:
            self.logger.error(f"Error extracting issues: {e}")
        
        return docs
    
    async def _extract_issue(
        self,
        issue,
        include_comments: bool
    ) -> Optional[Document]:
        """Extract single Jira issue."""
        try:
            # Build content
            content_parts = [
                f"# [{issue.key}] {issue.fields.summary}",
                "",
                f"**Status:** {issue.fields.status.name}",
                f"**Type:** {issue.fields.issuetype.name}",
                f"**Priority:** {getattr(issue.fields.priority, 'name', 'None')}",
                f"**Reporter:** {issue.fields.reporter.displayName if issue.fields.reporter else 'Unknown'}",
                f"**Assignee:** {issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned'}",
                "",
                "## Description",
                issue.fields.description or "No description provided",
            ]
            
            # Add comments
            if include_comments and hasattr(issue.fields, 'comment'):
                comments = issue.fields.comment.comments
                if comments:
                    content_parts.append("\n## Comments\n")
                    for comment in comments[:10]:  # Max 10 comments
                        author = comment.author.displayName if comment.author else "Unknown"
                        content_parts.append(f"**{author}:** {comment.body}\n")
            
            content = "\n".join(content_parts)
            
            # Get labels
            labels = getattr(issue.fields, 'labels', [])
            
            doc = Document(
                doc_id=self._generate_doc_id(f"issue-{issue.key}"),
                source="jira",
                source_type="issue",
                title=f"[{issue.key}] {issue.fields.summary}",
                content=content,
                raw_content=content,
                metadata={
                    "issue_key": issue.key,
                    "project": issue.fields.project.key,
                    "issue_type": issue.fields.issuetype.name,
                    "status": issue.fields.status.name,
                    "priority": getattr(issue.fields.priority, 'name', 'None'),
                },
                created_at=self._parse_date(issue.fields.created),
                updated_at=self._parse_date(issue.fields.updated),
                author=issue.fields.reporter.displayName if issue.fields.reporter else None,
                url=f"{self.client._options['server']}/browse/{issue.key}",
                tags=labels,
            )
            
            return doc
        
        except Exception as e:
            self.logger.error(f"Error extracting issue: {e}")
            return None
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse Jira date string."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except:
            return None
    
    def _generate_doc_id(self, item: str) -> str:
        """Generate unique document ID."""
        unique_string = f"jira:{item}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:16]


# Celery task
@app.task(name="extract_jira", bind=True)
def extract_jira_task(self, config: Dict[str, Any]) -> Dict[str, Any]:
    """Celery task for Jira extraction."""
    import asyncio
    
    url = config.get("url")
    username = config.get("username")
    api_token = config.get("api_token")
    
    if not all([url, username, api_token]):
        return {
            "success": False,
            "error": "Missing required Jira credentials"
        }
    
    extractor = JiraExtractor(url=url, username=username, api_token=api_token)
    
    # Run async extraction
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(extractor.process(config))
    
    return result.dict()

