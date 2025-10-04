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
        """Extract user information from a GitHub PR."""
        # Author
        author = pr.get("author", "")
        if author:
            self._add_or_update_user(
                username=author,
                document_id=f"github_pr_{pr.get('pr_number')}",
                relationship="created",
                topics=pr.get("tech_stack", []),
                document_title=pr.get("title", "")
            )
        
        # Reviewers (from description or metadata)
        description = pr.get("description", "")
        reviewers = self._extract_mentions(description)
        for reviewer in reviewers:
            self._add_or_update_user(
                username=reviewer,
                document_id=f"github_pr_{pr.get('pr_number')}",
                relationship="commented",
                topics=pr.get("tech_stack", []),
                document_title=pr.get("title", "")
            )
    
    def extract_user_from_jira_ticket(self, ticket: Dict[str, Any]) -> None:
        """Extract user information from a Jira ticket."""
        # Assignee
        assignee = ticket.get("assignee", "")
        if assignee:
            self._add_or_update_user(
                username=assignee,
                document_id=f"jira_{ticket.get('key')}",
                relationship="created",
                topics=ticket.get("tech_stack", []),
                skills=[ticket.get("summary", "")[:50]],  # Use summary as skill indicator
                document_title=ticket.get("summary", "")
            )
        
        # Extract mentions from description
        description = ticket.get("description", "")
        mentions = self._extract_mentions(description)
        for mentioned_user in mentions:
            self._add_or_update_user(
                username=mentioned_user,
                document_id=f"jira_{ticket.get('key')}",
                relationship="commented",
                topics=ticket.get("tech_stack", []),
                document_title=ticket.get("summary", "")
            )
    
    def extract_user_from_confluence_doc(self, doc: Dict[str, Any]) -> None:
        """Extract user information from a Confluence document."""
        # Author
        author = doc.get("author", "")
        if author:
            self._add_or_update_user(
                username=author,
                document_id=f"confluence_{doc.get('doc_id')}",
                relationship="created",
                topics=doc.get("tags", []),
                document_title=doc.get("title", "")
            )
        
        # Extract contributors from content
        content = doc.get("content", {})
        if isinstance(content, dict):
            content_text = content.get("text", "")
        else:
            content_text = str(content)
        
        contributors = self._extract_mentions(content_text)
        for contributor in contributors:
            self._add_or_update_user(
                username=contributor,
                document_id=f"confluence_{doc.get('doc_id')}",
                relationship="commented",
                topics=doc.get("tags", []),
                document_title=doc.get("title", "")
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

