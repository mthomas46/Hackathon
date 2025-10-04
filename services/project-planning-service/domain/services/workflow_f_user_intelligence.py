"""
Workflow F: User Intelligence & Relationship Mapping

Extracts user information from historical documents and synthesizes
expertise relationships, potential contacts, and subject matter experts.

This workflow:
1. Analyzes historical documents (GitHub PRs, Jira tickets, Confluence docs)
2. Extracts user metadata (username, name, email, interactions)
3. Maps users to topics, services, skills based on document content
4. Identifies collaboration patterns and potential teammates
5. Synthesizes subject matter experts and points of contact
6. Provides context for planning by identifying relevant experts
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import re


@dataclass
class UserExtraction:
    """Extracted user information from documents."""
    username: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    
    # Document relationships
    documents_created: List[str] = field(default_factory=list)
    documents_updated: List[str] = field(default_factory=list)
    documents_commented: List[str] = field(default_factory=list)
    
    # Inferred expertise
    topics: List[str] = field(default_factory=list)
    services: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    
    # Collaboration patterns
    collaborators: List[str] = field(default_factory=list)  # Other users they work with
    
    # Metrics
    total_interactions: int = 0
    expertise_score: float = 0.0
    
    # ⭐ NEW (Phase 1.4): GitHub PR Code Metrics
    code_metrics: Dict[str, Any] = field(default_factory=dict)
    # {
    #   "lines_added": int,
    #   "lines_deleted": int,
    #   "files_touched": List[str],
    #   "commit_count": int,
    #   "languages": List[str],
    #   "avg_pr_size": float
    # }
    
    # ⭐ NEW (Phase 1.4): GitHub PR Role Tracking
    pull_requests_authored: List[str] = field(default_factory=list)
    pull_requests_reviewed: List[str] = field(default_factory=list)
    pull_requests_merged: List[str] = field(default_factory=list)
    pull_requests_assigned: List[str] = field(default_factory=list)
    pull_requests_committed: List[str] = field(default_factory=list)
    
    # ⭐ NEW (Phase 1.4): Review Quality Metrics
    review_quality_score: float = 0.0  # 0.0 to 1.0
    approval_rate: float = 0.0  # Percentage of reviews that resulted in approval
    
    # ⭐ NEW (Phase 1.4): Authority Indicators
    merge_authority: bool = False  # Has merge permissions
    frequent_reviewers: List[str] = field(default_factory=list)  # Users they frequently review with
    technologies: List[str] = field(default_factory=list)  # Inferred from file paths
    
    # ⭐ NEW (Phase 1.5): Jira Ticket Metrics
    jira_metrics: Dict[str, Any] = field(default_factory=dict)
    # {
    #   "time_spent_minutes": int,
    #   "story_points_handled": float,
    #   "tickets_resolved": int,
    #   "avg_resolution_time_hours": float,
    #   "complexity_levels": {"low": int, "medium": int, "high": int}
    # }
    
    # ⭐ NEW (Phase 1.5): Jira Role Tracking
    jira_tickets_reported: List[str] = field(default_factory=list)  # Tickets created
    jira_tickets_assigned: List[str] = field(default_factory=list)  # Tickets assigned to
    jira_tickets_watched: List[str] = field(default_factory=list)  # Tickets watching
    jira_tickets_worked: List[str] = field(default_factory=list)  # Tickets with worklog entries
    jira_tickets_commented: List[str] = field(default_factory=list)  # Tickets commented on
    
    # ⭐ NEW (Phase 1.5): Domain Expertise from Jira
    components: List[str] = field(default_factory=list)  # Jira components (expertise areas)
    is_component_lead: bool = False  # Component lead/owner
    issue_types_handled: List[str] = field(default_factory=list)  # Bug, Story, Task, Epic, etc.
    labels: List[str] = field(default_factory=list)  # Jira labels (technical skills)
    
    # ⭐ NEW (Phase 1.6): Confluence Documentation Metrics
    confluence_metrics: Dict[str, Any] = field(default_factory=dict)
    # {
    #   "pages_created": int,
    #   "pages_edited": int,
    #   "total_likes_received": int,
    #   "total_watches": int,
    #   "total_comments": int,
    #   "avg_page_views": float,
    #   "documentation_quality_score": float  # 0.0 to 1.0
    # }
    
    # ⭐ NEW (Phase 1.6): Confluence Role Tracking
    confluence_pages_authored: List[str] = field(default_factory=list)  # Pages created
    confluence_pages_edited: List[str] = field(default_factory=list)  # Pages edited/updated
    confluence_pages_maintained: List[str] = field(default_factory=list)  # Pages actively maintained
    confluence_pages_watched: List[str] = field(default_factory=list)  # Pages watching
    confluence_pages_commented: List[str] = field(default_factory=list)  # Pages commented on
    
    # ⭐ NEW (Phase 1.6): Documentation Expertise
    confluence_spaces: List[str] = field(default_factory=list)  # Confluence spaces contributed to
    is_space_admin: bool = False  # Space administrator flag
    page_types: List[str] = field(default_factory=list)  # Types of pages created (how-to, API, design, etc.)
    documentation_topics: List[str] = field(default_factory=list)  # Topics documented


@dataclass
class SubjectMatterExpert:
    """Identified subject matter expert for a specific area."""
    username: str
    display_name: str
    area_of_expertise: str  # e.g., "Python Backend Development"
    confidence: float  # 0.0 to 1.0
    evidence: List[str]  # List of documents/interactions supporting this
    contact_priority: str  # "high", "medium", "low"
    is_team_member: bool = False


@dataclass
class WorkflowFResult:
    """Result of Workflow F execution."""
    extracted_users: Dict[str, UserExtraction]
    subject_matter_experts: List[SubjectMatterExpert]
    potential_contacts: Dict[str, List[str]]  # Area -> List of usernames
    collaboration_graph: Dict[str, List[str]]  # User -> List of collaborators
    expertise_map: Dict[str, List[str]]  # Topic/Skill -> List of expert usernames
    
    # Metadata
    total_users_extracted: int = 0
    total_documents_analyzed: int = 0
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


class UserIntelligenceWorkflow:
    """
    Workflow F: Analyzes documents to extract user intelligence and relationships.
    """
    
    def __init__(self):
        self.user_extractions: Dict[str, UserExtraction] = {}
        
    def extract_user_from_github_pr(self, pr: Dict[str, Any]) -> None:
        """
        Extract comprehensive user information from a GitHub PR.
        
        ⭐ Phase 1.4 Enhancements:
        - Extract 5+ user roles (author, assignees, reviewers, merger, commit authors)
        - Calculate code contribution metrics
        - Assess review quality
        - Infer technologies from file paths
        """
        pr_id = f"github_pr_{pr.get('pr_number', pr.get('id', 'unknown'))}"
        topics = pr.get("tech_stack", [])
        title = pr.get("title", "")
        
        # 1. AUTHOR (PR creator)
        author = pr.get("author", "")
        if author:
            self._add_or_update_user_github(
                username=author,
                pr_id=pr_id,
                role="authored",
                topics=topics,
                title=title,
                pr_data=pr
            )
        
        # 2. ASSIGNEES (users responsible for the PR)
        assignees = pr.get("assignees", [])
        if isinstance(assignees, str):
            assignees = [assignees]
        for assignee in assignees:
            if assignee:
                self._add_or_update_user_github(
                    username=assignee,
                    pr_id=pr_id,
                    role="assigned",
                    topics=topics,
                    title=title,
                    pr_data=pr
                )
        
        # 3. REVIEWERS (requested and actual)
        # Requested reviewers
        requested_reviewers = pr.get("requested_reviewers", [])
        if isinstance(requested_reviewers, str):
            requested_reviewers = [requested_reviewers]
        
        # Actual reviewers from reviews array
        reviews = pr.get("reviews", [])
        actual_reviewers = []
        if isinstance(reviews, list):
            for review in reviews:
                reviewer = review.get("user", review.get("reviewer", ""))
                if reviewer:
                    actual_reviewers.append(reviewer)
                    # Calculate review quality for this reviewer
                    review_state = review.get("state", review.get("review_state", ""))
                    comment_body = review.get("body", review.get("comment", ""))
                    quality_score = self._calculate_review_quality(comment_body, review_state)
                    
                    self._add_or_update_user_github(
                        username=reviewer,
                        pr_id=pr_id,
                        role="reviewed",
                        topics=topics,
                        title=title,
                        pr_data=pr,
                        review_quality=quality_score,
                        review_state=review_state
                    )
        
        # Merge requested and actual reviewers
        all_reviewers = list(set(requested_reviewers + actual_reviewers))
        
        # 4. MERGER (user who merged the PR)
        merged_by = pr.get("merged_by", pr.get("merger", ""))
        if merged_by:
            self._add_or_update_user_github(
                username=merged_by,
                pr_id=pr_id,
                role="merged",
                topics=topics,
                title=title,
                pr_data=pr
            )
        
        # 5. COMMIT AUTHORS (from commits array)
        commits = pr.get("commits", [])
        commit_authors = []
        if isinstance(commits, list):
            for commit in commits:
                commit_author = commit.get("author", commit.get("committer", ""))
                if commit_author and commit_author not in commit_authors:
                    commit_authors.append(commit_author)
                    self._add_or_update_user_github(
                        username=commit_author,
                        pr_id=pr_id,
                        role="committed",
                        topics=topics,
                        title=title,
                        pr_data=pr
                    )
        
        # 6. COMMENTERS (from comments array or mentions in description)
        comments = pr.get("comments", [])
        commenters = []
        if isinstance(comments, list):
            for comment in comments:
                commenter = comment.get("user", comment.get("author", ""))
                if commenter and commenter not in commenters:
                    commenters.append(commenter)
                    self._add_or_update_user_github(
                        username=commenter,
                        pr_id=pr_id,
                        role="commented",
                        topics=topics,
                        title=title,
                        pr_data=pr
                    )
        
        # Extract mentions from description as additional commenters
        description = pr.get("description", "")
        mentioned_users = self._extract_mentions(description)
        for mentioned_user in mentioned_users:
            if mentioned_user not in commenters:
                self._add_or_update_user_github(
                    username=mentioned_user,
                    pr_id=pr_id,
                    role="commented",
                    topics=topics,
                    title=title,
                    pr_data=pr
                )
        
        # 7. CALCULATE CODE METRICS (for author and commit authors)
        files_changed = pr.get("files_changed", pr.get("files", []))
        lines_added = pr.get("additions", pr.get("lines_added", 0))
        lines_deleted = pr.get("deletions", pr.get("lines_deleted", 0))
        
        # Infer technologies from file paths
        technologies = self._infer_technologies_from_files(files_changed)
        
        # Update code metrics for author
        if author and author in self.user_extractions:
            user = self.user_extractions[author]
            self._update_code_metrics(
                user,
                lines_added=lines_added,
                lines_deleted=lines_deleted,
                files_touched=files_changed if isinstance(files_changed, list) else [],
                commit_count=len(commits) if isinstance(commits, list) else 1,
                technologies=technologies
            )
    
    def extract_user_from_jira_ticket(self, ticket: Dict[str, Any]) -> None:
        """
        Extract comprehensive user information from a Jira ticket.
        
        ⭐ Phase 1.5 Enhancements:
        - Extract 4+ user roles (reporter, assignee, watchers, worklog contributors, commenters)
        - Parse work patterns (time spent, story points, resolution time)
        - Extract domain expertise signals (components, labels, issue types)
        - Calculate complexity handling levels
        """
        ticket_key = ticket.get('key', ticket.get('id', 'unknown'))
        ticket_id = f"jira_{ticket_key}"
        topics = ticket.get("tech_stack", [])
        summary = ticket.get("summary", "")
        
        # 1. REPORTER (ticket creator)
        reporter = ticket.get("reporter", ticket.get("creator", ""))
        if reporter:
            self._add_or_update_user_jira(
                username=reporter,
                ticket_id=ticket_id,
                role="reported",
                ticket_data=ticket,
                topics=topics,
                summary=summary
            )
        
        # 2. ASSIGNEE (user responsible for the ticket)
        assignee = ticket.get("assignee", "")
        if assignee:
            self._add_or_update_user_jira(
                username=assignee,
                ticket_id=ticket_id,
                role="assigned",
                ticket_data=ticket,
                topics=topics,
                summary=summary
            )
        
        # 3. WATCHERS (users interested in/monitoring the ticket)
        watchers = ticket.get("watchers", [])
        if isinstance(watchers, str):
            watchers = [watchers]
        for watcher in watchers:
            if watcher:
                self._add_or_update_user_jira(
                    username=watcher,
                    ticket_id=ticket_id,
                    role="watched",
                    ticket_data=ticket,
                    topics=topics,
                    summary=summary
                )
        
        # 4. WORKLOG CONTRIBUTORS (users who logged work time)
        worklog = ticket.get("worklog", [])
        if isinstance(worklog, list):
            for entry in worklog:
                worker = entry.get("author", entry.get("user", ""))
                if worker:
                    time_spent = entry.get("timeSpent", entry.get("time_spent", ""))
                    self._add_or_update_user_jira(
                        username=worker,
                        ticket_id=ticket_id,
                        role="worked",
                        ticket_data=ticket,
                        topics=topics,
                        summary=summary,
                        time_spent=time_spent
                    )
        
        # 5. COMMENTERS (users who commented on the ticket)
        comments = ticket.get("comments", [])
        comment_authors = []
        if isinstance(comments, list):
            for comment in comments:
                commenter = comment.get("author", comment.get("user", ""))
                if commenter and commenter not in comment_authors:
                    comment_authors.append(commenter)
                    self._add_or_update_user_jira(
                        username=commenter,
                        ticket_id=ticket_id,
                        role="commented",
                        ticket_data=ticket,
                        topics=topics,
                        summary=summary
                    )
        
        # Extract mentions from description as additional commenters
        description = ticket.get("description", "")
        mentioned_users = self._extract_mentions(description)
        for mentioned_user in mentioned_users:
            if mentioned_user not in comment_authors:
                self._add_or_update_user_jira(
                    username=mentioned_user,
                    ticket_id=ticket_id,
                    role="commented",
                    ticket_data=ticket,
                    topics=topics,
                    summary=summary
                )
        
        # 6. CALCULATE WORK METRICS (for assignee and worklog contributors)
        # Parse story points
        story_points = ticket.get("story_points", ticket.get("storyPoints", 0))
        if isinstance(story_points, str):
            try:
                story_points = float(story_points)
            except (ValueError, TypeError):
                story_points = 0
        
        # Calculate resolution time if resolved
        created_at = ticket.get("created", ticket.get("createdAt", ""))
        resolved_at = ticket.get("resolved", ticket.get("resolutionDate", ""))
        resolution_time_hours = 0
        if created_at and resolved_at:
            # Simple hour difference (in real implementation, would parse dates)
            resolution_time_hours = 24  # Placeholder
        
        # Update metrics for assignee
        if assignee and assignee in self.user_extractions:
            user = self.user_extractions[assignee]
            
            # Determine complexity level from story points or priority
            priority = ticket.get("priority", "medium").lower()
            complexity = self._determine_complexity(story_points, priority)
            
            self._update_jira_metrics(
                user,
                story_points=story_points,
                resolution_time_hours=resolution_time_hours,
                is_resolved=bool(resolved_at),
                complexity=complexity
            )
    
    def extract_user_from_confluence_doc(self, doc: Dict[str, Any]) -> None:
        """
        Extract comprehensive user information from a Confluence document.
        
        ⭐ Phase 1.6 Enhancements:
        - Extract 3+ user roles (author, editors, maintainers, watchers, commenters)
        - Track engagement metrics (likes, watches, comments, page views)
        - Calculate documentation expertise scores
        - Detect space administration
        """
        doc_id_raw = doc.get('doc_id', doc.get('id', doc.get('page_id', 'unknown')))
        doc_id = f"confluence_{doc_id_raw}"
        tags = doc.get("tags", [])
        title = doc.get("title", "")
        space = doc.get("space", doc.get("space_key", ""))
        
        # 1. AUTHOR (page creator)
        author = doc.get("author", doc.get("creator", ""))
        if author:
            self._add_or_update_user_confluence(
                username=author,
                doc_id=doc_id,
                role="authored",
                doc_data=doc,
                tags=tags,
                title=title,
                space=space
            )
        
        # 2. EDITORS (users who have modified the page)
        # Last modifier
        last_modified_by = doc.get("last_modified_by", doc.get("lastModifiedBy", ""))
        if last_modified_by and last_modified_by != author:
            self._add_or_update_user_confluence(
                username=last_modified_by,
                doc_id=doc_id,
                role="edited",
                doc_data=doc,
                tags=tags,
                title=title,
                space=space
            )
        
        # Contributors list
        contributors = doc.get("contributors", [])
        if isinstance(contributors, str):
            contributors = [contributors]
        for contributor in contributors:
            if contributor and contributor != author:
                self._add_or_update_user_confluence(
                    username=contributor,
                    doc_id=doc_id,
                    role="edited",
                    doc_data=doc,
                    tags=tags,
                    title=title,
                    space=space
                )
        
        # 3. MAINTAINERS (page owners / responsible parties)
        maintainers = doc.get("maintainers", doc.get("owners", []))
        if isinstance(maintainers, str):
            maintainers = [maintainers]
        for maintainer in maintainers:
            if maintainer:
                self._add_or_update_user_confluence(
                    username=maintainer,
                    doc_id=doc_id,
                    role="maintained",
                    doc_data=doc,
                    tags=tags,
                    title=title,
                    space=space
                )
        
        # 4. WATCHERS (users watching the page)
        watchers = doc.get("watchers", [])
        if isinstance(watchers, str):
            watchers = [watchers]
        for watcher in watchers:
            if watcher:
                self._add_or_update_user_confluence(
                    username=watcher,
                    doc_id=doc_id,
                    role="watched",
                    doc_data=doc,
                    tags=tags,
                    title=title,
                    space=space
                )
        
        # 5. COMMENTERS (users who commented on the page)
        comments = doc.get("comments", [])
        comment_authors = []
        if isinstance(comments, list):
            for comment in comments:
                commenter = comment.get("author", comment.get("user", ""))
                if commenter and commenter not in comment_authors:
                    comment_authors.append(commenter)
                    self._add_or_update_user_confluence(
                        username=commenter,
                        doc_id=doc_id,
                        role="commented",
                        doc_data=doc,
                        tags=tags,
                        title=title,
                        space=space
                    )
        
        # Extract mentions from content as additional commenters
        content = doc.get("content", {})
        if isinstance(content, dict):
            content_text = content.get("text", "")
        else:
            content_text = str(content)
        
        mentioned_users = self._extract_mentions(content_text)
        for mentioned_user in mentioned_users:
            if mentioned_user not in comment_authors:
                self._add_or_update_user_confluence(
                    username=mentioned_user,
                    doc_id=doc_id,
                    role="commented",
                    doc_data=doc,
                    tags=tags,
                    title=title,
                    space=space
                )
        
        # 6. CALCULATE ENGAGEMENT METRICS (for author and maintainers)
        likes = doc.get("likes", doc.get("like_count", 0))
        if isinstance(likes, list):
            likes = len(likes)
        elif isinstance(likes, str):
            try:
                likes = int(likes)
            except (ValueError, TypeError):
                likes = 0
        
        watches = len(watchers) if watchers else 0
        comments_count = len(comments) if isinstance(comments, list) else 0
        page_views = doc.get("views", doc.get("page_views", 0))
        if isinstance(page_views, str):
            try:
                page_views = int(page_views)
            except (ValueError, TypeError):
                page_views = 0
        
        # Calculate documentation quality score
        quality_score = self._calculate_documentation_quality(
            likes=likes,
            watches=watches,
            comments_count=comments_count,
            page_views=page_views,
            content_length=len(content_text),
            has_code_blocks="```" in content_text or "<code>" in content_text,
            has_images="!" in content_text or "<img" in content_text
        )
        
        # Update metrics for author
        if author and author in self.user_extractions:
            user = self.user_extractions[author]
            self._update_confluence_metrics(
                user,
                likes_received=likes,
                watches=watches,
                comments_count=comments_count,
                page_views=page_views,
                quality_score=quality_score,
                is_created=True
            )
        
        # Update metrics for maintainers
        for maintainer in maintainers:
            if maintainer and maintainer in self.user_extractions:
                user = self.user_extractions[maintainer]
                self._update_confluence_metrics(
                    user,
                    likes_received=likes,
                    watches=watches,
                    comments_count=comments_count,
                    page_views=page_views,
                    quality_score=quality_score,
                    is_created=False
                )
    
    def _extract_mentions(self, text: str) -> List[str]:
        """Extract @mentions from text."""
        if not text:
            return []
        # Pattern: @username or @first.last
        mentions = re.findall(r'@([\w.]+)', text)
        return list(set(mentions))  # Deduplicate
    
    def _add_or_update_user(
        self,
        username: str,
        document_id: str,
        relationship: str,  # "created", "updated", "commented"
        topics: List[str] = None,
        services: List[str] = None,
        skills: List[str] = None,
        document_title: str = ""
    ) -> None:
        """Add or update user extraction data."""
        if username not in self.user_extractions:
            # Create new user extraction
            self.user_extractions[username] = UserExtraction(
                username=username,
                display_name=self._format_display_name(username)
            )
        
        user = self.user_extractions[username]
        
        # Add document relationship
        if relationship == "created":
            if document_id not in user.documents_created:
                user.documents_created.append(document_id)
        elif relationship == "updated":
            if document_id not in user.documents_updated:
                user.documents_updated.append(document_id)
        elif relationship == "commented":
            if document_id not in user.documents_commented:
                user.documents_commented.append(document_id)
        
        # Add topics, services, skills
        if topics:
            for topic in topics:
                if topic and topic not in user.topics:
                    user.topics.append(topic)
        
        if services:
            for service in services:
                if service and service not in user.services:
                    user.services.append(service)
        
        if skills:
            for skill in skills:
                if skill and skill not in user.skills:
                    user.skills.append(skill)
        
        # Increment interaction count
        user.total_interactions += 1
    
    def _format_display_name(self, username: str) -> str:
        """Format username into display name."""
        # Handle formats like: "sarah.chen", "sarah_chen", "schen"
        if '.' in username:
            parts = username.split('.')
            return ' '.join(p.capitalize() for p in parts)
        elif '_' in username:
            parts = username.split('_')
            return ' '.join(p.capitalize() for p in parts)
        else:
            return username.capitalize()
    
    # ⭐ NEW (Phase 1.4): GitHub-specific user extraction and metrics
    
    def _add_or_update_user_github(
        self,
        username: str,
        pr_id: str,
        role: str,  # "authored", "assigned", "reviewed", "merged", "committed", "commented"
        topics: List[str],
        title: str,
        pr_data: Dict[str, Any],
        review_quality: float = 0.0,
        review_state: str = ""
    ) -> None:
        """
        Add or update user extraction data specifically for GitHub PRs.
        
        Tracks PR-specific roles and metrics.
        """
        # Create user if not exists
        if username not in self.user_extractions:
            self.user_extractions[username] = UserExtraction(
                username=username,
                display_name=self._format_display_name(username)
            )
        
        user = self.user_extractions[username]
        
        # Track role-specific PR relationships
        if role == "authored":
            if pr_id not in user.pull_requests_authored:
                user.pull_requests_authored.append(pr_id)
            if pr_id not in user.documents_created:
                user.documents_created.append(pr_id)
        
        elif role == "assigned":
            if pr_id not in user.pull_requests_assigned:
                user.pull_requests_assigned.append(pr_id)
        
        elif role == "reviewed":
            if pr_id not in user.pull_requests_reviewed:
                user.pull_requests_reviewed.append(pr_id)
            
            # Update review quality score (running average)
            if review_quality > 0:
                current_score = user.review_quality_score
                total_reviews = len(user.pull_requests_reviewed)
                if total_reviews == 1:
                    user.review_quality_score = review_quality
                else:
                    # Running average
                    user.review_quality_score = (
                        (current_score * (total_reviews - 1) + review_quality) / total_reviews
                    )
            
            # Update approval rate
            if review_state.upper() in ["APPROVED", "APPROVE"]:
                total_reviews = len(user.pull_requests_reviewed)
                approved_count = int(user.approval_rate * (total_reviews - 1)) + 1
                user.approval_rate = approved_count / total_reviews
        
        elif role == "merged":
            if pr_id not in user.pull_requests_merged:
                user.pull_requests_merged.append(pr_id)
            user.merge_authority = True  # Has merge permissions
        
        elif role == "committed":
            if pr_id not in user.pull_requests_committed:
                user.pull_requests_committed.append(pr_id)
        
        elif role == "commented":
            if pr_id not in user.documents_commented:
                user.documents_commented.append(pr_id)
        
        # Add topics
        if topics:
            for topic in topics:
                if topic and topic not in user.topics:
                    user.topics.append(topic)
        
        # Increment interaction count
        user.total_interactions += 1
    
    def _calculate_review_quality(self, comment_body: str, review_state: str) -> float:
        """
        Calculate review quality score based on comment depth and review state.
        
        Returns: Score from 0.0 to 1.0
        
        Factors:
        - Comment length (longer = more detailed)
        - Presence of code snippets
        - Presence of actionable feedback keywords
        - Review state (APPROVED, CHANGES_REQUESTED, COMMENTED)
        """
        if not comment_body:
            # No comment = superficial review
            return 0.2 if review_state.upper() == "APPROVED" else 0.1
        
        score = 0.0
        
        # Factor 1: Comment length (max 0.3)
        comment_length = len(comment_body)
        if comment_length > 500:
            score += 0.3
        elif comment_length > 200:
            score += 0.2
        elif comment_length > 50:
            score += 0.1
        
        # Factor 2: Code snippets (0.2)
        if '```' in comment_body or '`' in comment_body:
            score += 0.2
        
        # Factor 3: Actionable feedback keywords (0.3)
        actionable_keywords = [
            'suggest', 'recommend', 'consider', 'could',
            'should', 'might want', 'please', 'try',
            'refactor', 'optimize', 'improve', 'fix',
            'issue', 'problem', 'concern', 'question'
        ]
        comment_lower = comment_body.lower()
        keyword_matches = sum(1 for keyword in actionable_keywords if keyword in comment_lower)
        if keyword_matches >= 3:
            score += 0.3
        elif keyword_matches >= 2:
            score += 0.2
        elif keyword_matches >= 1:
            score += 0.1
        
        # Factor 4: Review state (0.2)
        if review_state.upper() == "CHANGES_REQUESTED":
            score += 0.2  # Requested changes = thorough review
        elif review_state.upper() == "APPROVED":
            score += 0.1  # Approved = positive but maybe less critical
        elif review_state.upper() == "COMMENTED":
            score += 0.15  # Just commented = medium engagement
        
        # Ensure score is between 0.0 and 1.0
        return min(1.0, score)
    
    def _infer_technologies_from_files(self, files: List[Any]) -> List[str]:
        """
        Infer technologies/languages from file paths.
        
        Args:
            files: List of file paths (strings) or file objects with 'filename' or 'path' keys
        
        Returns:
            List of inferred technology names
        """
        if not files:
            return []
        
        technologies = set()
        
        # Technology mapping from file extensions and patterns
        tech_map = {
            # Languages
            '.py': 'Python',
            '.js': 'JavaScript',
            '.jsx': 'React',
            '.ts': 'TypeScript',
            '.tsx': 'React',
            '.java': 'Java',
            '.scala': 'Scala',
            '.go': 'Go',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.rs': 'Rust',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.elm': 'Elm',
            
            # Frameworks/Tools
            'Dockerfile': 'Docker',
            'docker-compose': 'Docker',
            '.yml': 'YAML',
            '.yaml': 'YAML',
            '.json': 'JSON',
            '.toml': 'TOML',
            '.tf': 'Terraform',
            'Makefile': 'Make',
            '.sh': 'Shell',
            '.sql': 'SQL',
            '.proto': 'Protobuf',
            '.graphql': 'GraphQL',
            
            # Web
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.sass': 'SASS',
            '.less': 'LESS',
            '.vue': 'Vue',
            
            # Data
            '.csv': 'CSV',
            '.xml': 'XML',
            '.md': 'Markdown'
        }
        
        # Directory/path patterns
        path_patterns = {
            '/backend/': 'Backend',
            '/frontend/': 'Frontend',
            '/api/': 'API',
            '/ui/': 'UI',
            '/web/': 'Web',
            '/mobile/': 'Mobile',
            '/ios/': 'iOS',
            '/android/': 'Android',
            '/tests/': 'Testing',
            '/test/': 'Testing',
            '__tests__': 'Testing',
            '.test.': 'Testing',
            '.spec.': 'Testing',
            '/db/': 'Database',
            '/database/': 'Database',
            '/migrations/': 'Database',
            '/docker/': 'Docker',
            '/k8s/': 'Kubernetes',
            '/kubernetes/': 'Kubernetes',
            '/ci/': 'CI/CD',
            '/infra/': 'Infrastructure',
            '/terraform/': 'Terraform'
        }
        
        for file_item in files:
            # Extract filename from various formats
            if isinstance(file_item, str):
                filename = file_item
            elif isinstance(file_item, dict):
                filename = file_item.get('filename', file_item.get('path', file_item.get('name', '')))
            else:
                continue
            
            if not filename:
                continue
            
            # Check file extension
            for ext, tech in tech_map.items():
                if filename.endswith(ext) or ext in filename:
                    technologies.add(tech)
            
            # Check path patterns
            for pattern, tech in path_patterns.items():
                if pattern in filename.lower():
                    technologies.add(tech)
        
        return sorted(list(technologies))
    
    def _update_code_metrics(
        self,
        user: UserExtraction,
        lines_added: int = 0,
        lines_deleted: int = 0,
        files_touched: List[Any] = None,
        commit_count: int = 0,
        technologies: List[str] = None
    ) -> None:
        """
        Update code contribution metrics for a user.
        
        Aggregates metrics across multiple PRs.
        """
        if not user.code_metrics:
            user.code_metrics = {
                "lines_added": 0,
                "lines_deleted": 0,
                "files_touched": [],
                "commit_count": 0,
                "languages": [],
                "avg_pr_size": 0.0,
                "total_prs": 0
            }
        
        # Aggregate metrics
        user.code_metrics["lines_added"] += lines_added
        user.code_metrics["lines_deleted"] += lines_deleted
        user.code_metrics["commit_count"] += commit_count
        user.code_metrics["total_prs"] += 1
        
        # Add new files (avoid duplicates)
        if files_touched:
            for file in files_touched:
                filename = file if isinstance(file, str) else file.get('filename', file.get('path', ''))
                if filename and filename not in user.code_metrics["files_touched"]:
                    user.code_metrics["files_touched"].append(filename)
        
        # Add technologies to both code_metrics and user.technologies
        if technologies:
            for tech in technologies:
                if tech not in user.code_metrics["languages"]:
                    user.code_metrics["languages"].append(tech)
                if tech not in user.technologies:
                    user.technologies.append(tech)
        
        # Calculate average PR size
        total_prs = user.code_metrics["total_prs"]
        if total_prs > 0:
            total_lines = user.code_metrics["lines_added"] + user.code_metrics["lines_deleted"]
            user.code_metrics["avg_pr_size"] = total_lines / total_prs
    
    # ⭐ NEW (Phase 1.5): Jira-specific user extraction and metrics
    
    def _add_or_update_user_jira(
        self,
        username: str,
        ticket_id: str,
        role: str,  # "reported", "assigned", "watched", "worked", "commented"
        ticket_data: Dict[str, Any],
        topics: List[str],
        summary: str,
        time_spent: str = ""
    ) -> None:
        """
        Add or update user extraction data specifically for Jira tickets.
        
        Tracks Jira-specific roles, metrics, and domain expertise.
        """
        # Create user if not exists
        if username not in self.user_extractions:
            self.user_extractions[username] = UserExtraction(
                username=username,
                display_name=self._format_display_name(username)
            )
        
        user = self.user_extractions[username]
        
        # Track role-specific ticket relationships
        if role == "reported":
            if ticket_id not in user.jira_tickets_reported:
                user.jira_tickets_reported.append(ticket_id)
            if ticket_id not in user.documents_created:
                user.documents_created.append(ticket_id)
        
        elif role == "assigned":
            if ticket_id not in user.jira_tickets_assigned:
                user.jira_tickets_assigned.append(ticket_id)
        
        elif role == "watched":
            if ticket_id not in user.jira_tickets_watched:
                user.jira_tickets_watched.append(ticket_id)
        
        elif role == "worked":
            if ticket_id not in user.jira_tickets_worked:
                user.jira_tickets_worked.append(ticket_id)
            
            # Parse time spent and update metrics
            if time_spent:
                minutes = self._parse_time_spent(time_spent)
                if not user.jira_metrics:
                    user.jira_metrics = {"time_spent_minutes": 0}
                user.jira_metrics["time_spent_minutes"] = user.jira_metrics.get("time_spent_minutes", 0) + minutes
        
        elif role == "commented":
            if ticket_id not in user.jira_tickets_commented:
                user.jira_tickets_commented.append(ticket_id)
            if ticket_id not in user.documents_commented:
                user.documents_commented.append(ticket_id)
        
        # Extract domain expertise signals
        # Components (expertise areas)
        components = ticket_data.get("components", [])
        if isinstance(components, str):
            components = [components]
        for component in components:
            if component and component not in user.components:
                user.components.append(component)
        
        # Labels (technical skills)
        labels = ticket_data.get("labels", [])
        if isinstance(labels, str):
            labels = [labels]
        for label in labels:
            if label and label not in user.labels:
                user.labels.append(label)
        
        # Issue type (skill patterns)
        issue_type = ticket_data.get("issue_type", ticket_data.get("type", ""))
        if issue_type and issue_type not in user.issue_types_handled:
            user.issue_types_handled.append(issue_type)
        
        # Add topics
        if topics:
            for topic in topics:
                if topic and topic not in user.topics:
                    user.topics.append(topic)
        
        # Extract skills from summary
        if summary and role in ["reported", "assigned"]:
            # First 50 chars of summary as skill indicator
            skill = summary[:50]
            if skill and skill not in user.skills:
                user.skills.append(skill)
        
        # Increment interaction count
        user.total_interactions += 1
    
    def _parse_time_spent(self, time_spent_str: str) -> int:
        """
        Parse Jira time spent string to minutes.
        
        Formats: "2h 30m", "1d 4h", "30m", "2h", "1d", etc.
        
        Returns: Total minutes
        """
        if not time_spent_str:
            return 0
        
        minutes = 0
        time_spent_lower = time_spent_str.lower().strip()
        
        # Parse days
        if 'd' in time_spent_lower:
            try:
                days_part = time_spent_lower.split('d')[0].strip()
                days = float(days_part)
                minutes += int(days * 8 * 60)  # Assuming 8-hour workday
                time_spent_lower = time_spent_lower.split('d')[1].strip()
            except (ValueError, IndexError):
                pass
        
        # Parse hours
        if 'h' in time_spent_lower:
            try:
                hours_part = time_spent_lower.split('h')[0].strip()
                hours = float(hours_part)
                minutes += int(hours * 60)
                time_spent_lower = time_spent_lower.split('h')[1].strip()
            except (ValueError, IndexError):
                pass
        
        # Parse minutes
        if 'm' in time_spent_lower:
            try:
                mins_part = time_spent_lower.split('m')[0].strip()
                mins = float(mins_part)
                minutes += int(mins)
            except (ValueError, IndexError):
                pass
        
        return minutes
    
    def _determine_complexity(self, story_points: float, priority: str) -> str:
        """
        Determine complexity level from story points and priority.
        
        Returns: "low", "medium", or "high"
        """
        # Priority-based complexity
        if priority in ["critical", "highest", "blocker"]:
            return "high"
        elif priority in ["high"]:
            return "medium" if story_points < 5 else "high"
        elif priority in ["low", "lowest", "trivial"]:
            return "low"
        
        # Story points-based complexity
        if story_points >= 8:
            return "high"
        elif story_points >= 3:
            return "medium"
        elif story_points > 0:
            return "low"
        
        # Default to medium
        return "medium"
    
    def _update_jira_metrics(
        self,
        user: UserExtraction,
        story_points: float = 0,
        resolution_time_hours: float = 0,
        is_resolved: bool = False,
        complexity: str = "medium"
    ) -> None:
        """
        Update Jira work metrics for a user.
        
        Aggregates metrics across multiple tickets.
        """
        if not user.jira_metrics:
            user.jira_metrics = {
                "time_spent_minutes": 0,
                "story_points_handled": 0.0,
                "tickets_resolved": 0,
                "avg_resolution_time_hours": 0.0,
                "complexity_levels": {"low": 0, "medium": 0, "high": 0},
                "total_tickets": 0
            }
        
        # Aggregate metrics
        user.jira_metrics["story_points_handled"] = (
            user.jira_metrics.get("story_points_handled", 0.0) + story_points
        )
        
        if is_resolved:
            user.jira_metrics["tickets_resolved"] = (
                user.jira_metrics.get("tickets_resolved", 0) + 1
            )
            
            # Update avg resolution time
            current_avg = user.jira_metrics.get("avg_resolution_time_hours", 0.0)
            total_resolved = user.jira_metrics["tickets_resolved"]
            if total_resolved == 1:
                user.jira_metrics["avg_resolution_time_hours"] = resolution_time_hours
            else:
                user.jira_metrics["avg_resolution_time_hours"] = (
                    (current_avg * (total_resolved - 1) + resolution_time_hours) / total_resolved
                )
        
        # Track complexity levels
        if "complexity_levels" not in user.jira_metrics:
            user.jira_metrics["complexity_levels"] = {"low": 0, "medium": 0, "high": 0}
        
        user.jira_metrics["complexity_levels"][complexity] = (
            user.jira_metrics["complexity_levels"].get(complexity, 0) + 1
        )
        
        user.jira_metrics["total_tickets"] = user.jira_metrics.get("total_tickets", 0) + 1
    
    # ⭐ NEW (Phase 1.6): Confluence-specific user extraction and metrics
    
    def _add_or_update_user_confluence(
        self,
        username: str,
        doc_id: str,
        role: str,  # "authored", "edited", "maintained", "watched", "commented"
        doc_data: Dict[str, Any],
        tags: List[str],
        title: str,
        space: str
    ) -> None:
        """
        Add or update user extraction data specifically for Confluence pages.
        
        Tracks Confluence-specific roles, metrics, and documentation expertise.
        """
        # Create user if not exists
        if username not in self.user_extractions:
            self.user_extractions[username] = UserExtraction(
                username=username,
                display_name=self._format_display_name(username)
            )
        
        user = self.user_extractions[username]
        
        # Track role-specific page relationships
        if role == "authored":
            if doc_id not in user.confluence_pages_authored:
                user.confluence_pages_authored.append(doc_id)
            if doc_id not in user.documents_created:
                user.documents_created.append(doc_id)
        
        elif role == "edited":
            if doc_id not in user.confluence_pages_edited:
                user.confluence_pages_edited.append(doc_id)
            if doc_id not in user.documents_updated:
                user.documents_updated.append(doc_id)
        
        elif role == "maintained":
            if doc_id not in user.confluence_pages_maintained:
                user.confluence_pages_maintained.append(doc_id)
        
        elif role == "watched":
            if doc_id not in user.confluence_pages_watched:
                user.confluence_pages_watched.append(doc_id)
        
        elif role == "commented":
            if doc_id not in user.confluence_pages_commented:
                user.confluence_pages_commented.append(doc_id)
            if doc_id not in user.documents_commented:
                user.documents_commented.append(doc_id)
        
        # Extract documentation expertise signals
        # Spaces
        if space and space not in user.confluence_spaces:
            user.confluence_spaces.append(space)
        
        # Check for space admin
        space_admins = doc_data.get("space_admins", doc_data.get("administrators", []))
        if isinstance(space_admins, str):
            space_admins = [space_admins]
        if username in space_admins:
            user.is_space_admin = True
        
        # Page types (infer from title/labels)
        page_type = self._infer_page_type(title, tags, doc_data)
        if page_type and page_type not in user.page_types:
            user.page_types.append(page_type)
        
        # Documentation topics (from tags)
        if tags:
            for tag in tags:
                if tag and tag not in user.documentation_topics:
                    user.documentation_topics.append(tag)
                if tag and tag not in user.topics:
                    user.topics.append(tag)
        
        # Increment interaction count
        user.total_interactions += 1
    
    def _infer_page_type(self, title: str, tags: List[str], doc_data: Dict[str, Any]) -> str:
        """
        Infer the type of Confluence page from title, tags, and content.
        
        Returns: Page type (e.g., "API Documentation", "How-To Guide", "Design Doc")
        """
        title_lower = title.lower()
        tags_lower = [t.lower() for t in tags] if tags else []
        
        # Check explicit page type
        explicit_type = doc_data.get("page_type", doc_data.get("type", ""))
        if explicit_type and explicit_type != "page":
            return explicit_type.title()
        
        # Infer from title
        if any(keyword in title_lower for keyword in ["api", "endpoint", "rest", "graphql"]):
            return "API Documentation"
        elif any(keyword in title_lower for keyword in ["how to", "tutorial", "guide", "walkthrough"]):
            return "How-To Guide"
        elif any(keyword in title_lower for keyword in ["design", "architecture", "rfc", "adr"]):
            return "Design Document"
        elif any(keyword in title_lower for keyword in ["runbook", "playbook", "troubleshooting", "sop"]):
            return "Runbook"
        elif any(keyword in title_lower for keyword in ["meeting", "minutes", "notes", "agenda"]):
            return "Meeting Notes"
        elif any(keyword in title_lower for keyword in ["requirements", "spec", "specification"]):
            return "Requirements"
        elif any(keyword in title_lower for keyword in ["onboarding", "getting started", "setup"]):
            return "Onboarding"
        
        # Infer from tags
        if any(tag in tags_lower for tag in ["api", "rest", "graphql"]):
            return "API Documentation"
        elif any(tag in tags_lower for tag in ["tutorial", "guide", "how-to"]):
            return "How-To Guide"
        elif any(tag in tags_lower for tag in ["design", "architecture"]):
            return "Design Document"
        elif any(tag in tags_lower for tag in ["runbook", "troubleshooting"]):
            return "Runbook"
        
        # Default
        return "Documentation"
    
    def _calculate_documentation_quality(
        self,
        likes: int,
        watches: int,
        comments_count: int,
        page_views: int,
        content_length: int,
        has_code_blocks: bool,
        has_images: bool
    ) -> float:
        """
        Calculate documentation quality score based on engagement and content.
        
        Returns: Quality score from 0.0 to 1.0
        """
        score = 0.0
        
        # Engagement metrics (50% of score)
        # Likes (worth 0.2)
        if page_views > 0:
            like_rate = likes / max(page_views, 1)
            score += min(like_rate * 10, 0.2)  # Max 0.2 for 2%+ like rate
        elif likes > 0:
            score += 0.1
        
        # Watches (worth 0.15)
        if page_views > 0:
            watch_rate = watches / max(page_views, 1)
            score += min(watch_rate * 15, 0.15)  # Max 0.15 for 1%+ watch rate
        elif watches > 0:
            score += 0.05
        
        # Comments (worth 0.15)
        if page_views > 0:
            comment_rate = comments_count / max(page_views, 1)
            score += min(comment_rate * 20, 0.15)  # Max 0.15 for 0.75%+ comment rate
        elif comments_count > 0:
            score += 0.05
        
        # Content quality indicators (50% of score)
        # Content length (worth 0.2)
        if content_length >= 5000:  # Long, comprehensive
            score += 0.2
        elif content_length >= 2000:  # Medium length
            score += 0.15
        elif content_length >= 500:  # Decent length
            score += 0.1
        elif content_length >= 100:  # Short but exists
            score += 0.05
        
        # Code blocks (worth 0.15)
        if has_code_blocks:
            score += 0.15
        
        # Images/diagrams (worth 0.15)
        if has_images:
            score += 0.15
        
        # Cap at 1.0
        return min(score, 1.0)
    
    def _update_confluence_metrics(
        self,
        user: UserExtraction,
        likes_received: int = 0,
        watches: int = 0,
        comments_count: int = 0,
        page_views: int = 0,
        quality_score: float = 0.0,
        is_created: bool = False
    ) -> None:
        """
        Update Confluence documentation metrics for a user.
        
        Aggregates metrics across multiple pages.
        """
        if not user.confluence_metrics:
            user.confluence_metrics = {
                "pages_created": 0,
                "pages_edited": 0,
                "total_likes_received": 0,
                "total_watches": 0,
                "total_comments": 0,
                "avg_page_views": 0.0,
                "documentation_quality_score": 0.0,
                "total_pages": 0
            }
        
        # Track creation vs edit
        if is_created:
            user.confluence_metrics["pages_created"] = user.confluence_metrics.get("pages_created", 0) + 1
        else:
            user.confluence_metrics["pages_edited"] = user.confluence_metrics.get("pages_edited", 0) + 1
        
        # Aggregate engagement metrics
        user.confluence_metrics["total_likes_received"] = (
            user.confluence_metrics.get("total_likes_received", 0) + likes_received
        )
        user.confluence_metrics["total_watches"] = (
            user.confluence_metrics.get("total_watches", 0) + watches
        )
        user.confluence_metrics["total_comments"] = (
            user.confluence_metrics.get("total_comments", 0) + comments_count
        )
        
        # Update page count
        user.confluence_metrics["total_pages"] = user.confluence_metrics.get("total_pages", 0) + 1
        total_pages = user.confluence_metrics["total_pages"]
        
        # Calculate average page views
        current_avg_views = user.confluence_metrics.get("avg_page_views", 0.0)
        if total_pages == 1:
            user.confluence_metrics["avg_page_views"] = float(page_views)
        else:
            user.confluence_metrics["avg_page_views"] = (
                (current_avg_views * (total_pages - 1) + page_views) / total_pages
            )
        
        # Calculate average documentation quality score
        current_avg_quality = user.confluence_metrics.get("documentation_quality_score", 0.0)
        if total_pages == 1:
            user.confluence_metrics["documentation_quality_score"] = quality_score
        else:
            user.confluence_metrics["documentation_quality_score"] = (
                (current_avg_quality * (total_pages - 1) + quality_score) / total_pages
            )
    
    def synthesize_subject_matter_experts(
        self,
        min_interactions: int = 3,
        team_members: List[str] = None
    ) -> List[SubjectMatterExpert]:
        """
        Identify subject matter experts based on interaction patterns.
        """
        team_members = team_members or []
        team_usernames = [m.lower().replace(' ', '.') for m in team_members]
        
        smes = []
        
        for username, extraction in self.user_extractions.items():
            if extraction.total_interactions < min_interactions:
                continue
            
            # Calculate expertise score
            expertise_score = self._calculate_expertise_score(extraction)
            extraction.expertise_score = expertise_score
            
            # Identify areas of expertise
            areas = []
            
            # Topic-based expertise
            for topic in extraction.topics[:3]:  # Top 3 topics
                evidence = [
                    f"Created {len(extraction.documents_created)} documents",
                    f"Contributed to {len(extraction.documents_commented)} discussions",
                    f"Topics: {', '.join(extraction.topics[:5])}"
                ]
                
                smes.append(SubjectMatterExpert(
                    username=username,
                    display_name=extraction.display_name,
                    area_of_expertise=f"{topic} Development",
                    confidence=min(expertise_score, 1.0),
                    evidence=evidence,
                    contact_priority="high" if expertise_score > 0.7 else "medium",
                    is_team_member=username in team_usernames or extraction.display_name in team_members
                ))
        
        # Sort by confidence
        smes.sort(key=lambda x: x.confidence, reverse=True)
        return smes
    
    def _calculate_expertise_score(self, extraction: UserExtraction) -> float:
        """Calculate expertise score based on user's interactions."""
        score = 0.0
        
        # Created documents (strong signal)
        score += len(extraction.documents_created) * 0.3
        
        # Updated documents (medium signal)
        score += len(extraction.documents_updated) * 0.2
        
        # Commented (weak signal)
        score += len(extraction.documents_commented) * 0.1
        
        # Diversity of topics/skills
        score += len(extraction.topics) * 0.05
        score += len(extraction.skills) * 0.05
        
        # Collaboration (indicator of leadership/expertise)
        score += len(extraction.collaborators) * 0.1
        
        return min(score / 10.0, 1.0)  # Normalize to 0-1
    
    def build_collaboration_graph(self) -> Dict[str, List[str]]:
        """Build a graph of who collaborates with whom."""
        collaboration_graph = {}
        
        # Group users by document
        document_users = {}
        for username, extraction in self.user_extractions.items():
            all_docs = (extraction.documents_created + 
                       extraction.documents_updated + 
                       extraction.documents_commented)
            
            for doc_id in all_docs:
                if doc_id not in document_users:
                    document_users[doc_id] = []
                document_users[doc_id].append(username)
        
        # Users who worked on same documents are collaborators
        for username, extraction in self.user_extractions.items():
            collaborators = set()
            all_docs = (extraction.documents_created + 
                       extraction.documents_updated + 
                       extraction.documents_commented)
            
            for doc_id in all_docs:
                for other_user in document_users.get(doc_id, []):
                    if other_user != username:
                        collaborators.add(other_user)
            
            extraction.collaborators = list(collaborators)
            collaboration_graph[username] = list(collaborators)
        
        return collaboration_graph
    
    def build_expertise_map(self) -> Dict[str, List[str]]:
        """Map topics/skills to expert users."""
        expertise_map = {}
        
        for username, extraction in self.user_extractions.items():
            # Map topics to users
            for topic in extraction.topics:
                if topic not in expertise_map:
                    expertise_map[topic] = []
                if username not in expertise_map[topic]:
                    expertise_map[topic].append(username)
            
            # Map skills to users
            for skill in extraction.skills:
                if skill not in expertise_map:
                    expertise_map[skill] = []
                if username not in expertise_map[skill]:
                    expertise_map[skill].append(username)
        
        return expertise_map
    
    def execute(
        self,
        jira_tickets: List[Dict[str, Any]],
        confluence_docs: List[Dict[str, Any]],
        github_prs: List[Dict[str, Any]],
        team_members: List[str] = None
    ) -> WorkflowFResult:
        """
        Execute Workflow F: User Intelligence & Relationship Mapping.
        """
        start_time = datetime.utcnow()
        
        # Extract users from all documents
        for ticket in jira_tickets:
            self.extract_user_from_jira_ticket(ticket)
        
        for doc in confluence_docs:
            self.extract_user_from_confluence_doc(doc)
        
        for pr in github_prs:
            self.extract_user_from_github_pr(pr)
        
        # Build relationships
        collaboration_graph = self.build_collaboration_graph()
        expertise_map = self.build_expertise_map()
        
        # Synthesize subject matter experts
        smes = self.synthesize_subject_matter_experts(
            min_interactions=2,
            team_members=team_members or []
        )
        
        # Build potential contacts map
        potential_contacts = {}
        for sme in smes:
            area = sme.area_of_expertise
            if area not in potential_contacts:
                potential_contacts[area] = []
            potential_contacts[area].append(sme.username)
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        return WorkflowFResult(
            extracted_users=self.user_extractions,
            subject_matter_experts=smes,
            potential_contacts=potential_contacts,
            collaboration_graph=collaboration_graph,
            expertise_map=expertise_map,
            total_users_extracted=len(self.user_extractions),
            total_documents_analyzed=len(jira_tickets) + len(confluence_docs) + len(github_prs),
            execution_time=execution_time
        )

