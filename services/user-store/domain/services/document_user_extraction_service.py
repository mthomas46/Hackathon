"""Document User Extraction Service for the User Store service.

This service analyzes document content and metadata to extract user relationships
based on markers like "created by", "assigned to", "reviewed by", etc. It supports
various document types from different sources (GitHub, Jira, Confluence).
"""

import re
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

from ..entities.document_relationship import RelationshipType, AccessLevel


@dataclass
class UserRelationship:
    """Represents a relationship between a user identifier and relationship type."""
    user_identifier: str  # email, username, or display name
    relationship_type: RelationshipType
    confidence: float  # 0.0 to 1.0
    source_field: str  # which field this was extracted from


class DocumentUserExtractionService:
    """Service for extracting user relationships from document content and metadata."""

    def __init__(self):
        """Initialize the extraction service with patterns for different sources."""
        self._patterns = self._build_extraction_patterns()

    def _build_extraction_patterns(self) -> Dict[str, List[tuple]]:
        """Build regex patterns for extracting user information from different sources."""

        # Common patterns that work across all sources
        common_patterns = [
            # Email patterns
            (r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b', 'email', 0.9),

            # GitHub-style mentions
            (r'@([a-zA-Z0-9_-]+)', 'username', 0.8),

            # Full name patterns
            (r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b', 'display_name', 0.6),
        ]

        return {
            'github': common_patterns + [
                # GitHub specific patterns
                (r'by @?([a-zA-Z0-9_-]+)', 'author', 0.95),
                (r'author:?\s*@?([a-zA-Z0-9_-]+)', 'author', 0.95),
                (r'reviewed by:? @?([a-zA-Z0-9_-]+)', 'reviewer', 0.95),
                (r'assigned to:? @?([a-zA-Z0-9_-]+)', 'assignee', 0.95),
                (r'opened by:? @?([a-zA-Z0-9_-]+)', 'author', 0.95),
            ],
            'jira': common_patterns + [
                # Jira specific patterns
                (r'reporter:?\s*([a-zA-Z0-9._%+-]+)', 'reporter', 0.95),
                (r'assignee:?\s*([a-zA-Z0-9._%+-]+)', 'assignee', 0.95),
                (r'created by:?\s*([a-zA-Z0-9._%+-]+)', 'author', 0.95),
                (r'updated by:?\s*([a-zA-Z0-9._%+-]+)', 'updater', 0.85),
                (r'commented by:?\s*([a-zA-Z0-9._%+-]+)', 'commenter', 0.8),
            ],
            'confluence': common_patterns + [
                # Confluence specific patterns
                (r'created by:?\s*([a-zA-Z0-9._%+-@\s]+)', 'author', 0.95),
                (r'last modified by:?\s*([a-zA-Z0-9._%+-@\s]+)', 'updater', 0.9),
                (r'contributors?:?\s*([a-zA-Z0-9._%+-@\s,]+)', 'contributor', 0.8),
                (r'authors?:?\s*([a-zA-Z0-9._%+-@\s,]+)', 'author', 0.85),
            ],
            'common': common_patterns + [
                # Generic patterns that work for any document type
                (r'created by:?\s*([a-zA-Z0-9._%+-@\s]+)', 'author', 0.85),
                (r'updated by:?\s*([a-zA-Z0-9._%+-@\s]+)', 'updater', 0.8),
                (r'assigned to:?\s*([a-zA-Z0-9._%+-@\s]+)', 'assignee', 0.85),
                (r'opened by:?\s*([a-zA-Z0-9._%+-@\s]+)', 'author', 0.85),
                (r'reviewed by:?\s*([a-zA-Z0-9._%+-@\s]+)', 'reviewer', 0.9),
                (r'approved by:?\s*([a-zA-Z0-9._%+-@\s]+)', 'approver', 0.9),
            ]
        }

    def extract_user_relationships(
        self,
        document_content: str,
        document_metadata: Dict[str, any],
        source_type: str
    ) -> List[UserRelationship]:
        """Extract user relationships from document content and metadata.

        Args:
            document_content: The full text content of the document
            document_metadata: Document metadata dictionary
            source_type: Source system (github, jira, confluence)

        Returns:
            List of UserRelationship objects found in the document
        """
        relationships = []

        # Extract from metadata first (higher confidence)
        metadata_relationships = self._extract_from_metadata(document_metadata, source_type)
        relationships.extend(metadata_relationships)

        # Extract from content (lower confidence, but broader coverage)
        content_relationships = self._extract_from_content(document_content, source_type)
        relationships.extend(content_relationships)

        # Remove duplicates and return sorted by confidence
        unique_relationships = self._deduplicate_relationships(relationships)

        return sorted(unique_relationships, key=lambda x: x.confidence, reverse=True)

    def _extract_from_metadata(
        self,
        metadata: Dict[str, any],
        source_type: str
    ) -> List[UserRelationship]:
        """Extract user relationships from document metadata."""
        relationships = []

        # Source-specific metadata extraction
        if source_type == 'github':
            relationships.extend(self._extract_github_metadata(metadata))
        elif source_type == 'jira':
            relationships.extend(self._extract_jira_metadata(metadata))
        elif source_type == 'confluence':
            relationships.extend(self._extract_confluence_metadata(metadata))

        # Common metadata patterns
        relationships.extend(self._extract_common_metadata(metadata))

        return relationships

    def _extract_github_metadata(self, metadata: Dict[str, any]) -> List[UserRelationship]:
        """Extract user relationships from GitHub metadata."""
        relationships = []

        # PR/issue author
        if 'user' in metadata and metadata['user']:
            user_info = metadata['user']
            if 'login' in user_info:
                relationships.append(UserRelationship(
                    user_identifier=user_info['login'],
                    relationship_type=RelationshipType.OWNER,
                    confidence=1.0,
                    source_field='user.login'
                ))

        # Assignees
        if 'assignees' in metadata and metadata['assignees']:
            for assignee in metadata['assignees']:
                if isinstance(assignee, dict) and 'login' in assignee:
                    relationships.append(UserRelationship(
                        user_identifier=assignee['login'],
                        relationship_type=RelationshipType.SUBSCRIBER,
                        confidence=0.95,
                        source_field='assignees'
                    ))

        # Reviewers (if available in metadata)
        if 'reviews' in metadata and metadata['reviews']:
            for review in metadata['reviews']:
                if 'user' in review and review['user'] and 'login' in review['user']:
                    relationships.append(UserRelationship(
                        user_identifier=review['user']['login'],
                        relationship_type=RelationshipType.REVIEWER,
                        confidence=0.95,
                        source_field='reviews'
                    ))

        return relationships

    def _extract_jira_metadata(self, metadata: Dict[str, any]) -> List[UserRelationship]:
        """Extract user relationships from Jira metadata."""
        relationships = []

        # Reporter
        if 'reporter' in metadata and metadata['reporter']:
            reporter = metadata['reporter']
            if isinstance(reporter, dict):
                if 'emailAddress' in reporter:
                    relationships.append(UserRelationship(
                        user_identifier=reporter['emailAddress'],
                        relationship_type=RelationshipType.OWNER,
                        confidence=1.0,
                        source_field='reporter.emailAddress'
                    ))
                elif 'displayName' in reporter:
                    relationships.append(UserRelationship(
                        user_identifier=reporter['displayName'],
                        relationship_type=RelationshipType.OWNER,
                        confidence=0.9,
                        source_field='reporter.displayName'
                    ))

        # Assignee
        if 'assignee' in metadata and metadata['assignee']:
            assignee = metadata['assignee']
            if isinstance(assignee, dict):
                if 'emailAddress' in assignee:
                    relationships.append(UserRelationship(
                        user_identifier=assignee['emailAddress'],
                        relationship_type=RelationshipType.SUBSCRIBER,
                        confidence=0.95,
                        source_field='assignee.emailAddress'
                    ))

        # Comments authors
        if 'comments' in metadata and metadata['comments']:
            for comment in metadata['comments']:
                if 'author' in comment and comment['author']:
                    author = comment['author']
                    if isinstance(author, dict) and 'emailAddress' in author:
                        relationships.append(UserRelationship(
                            user_identifier=author['emailAddress'],
                            relationship_type=RelationshipType.CONTRIBUTOR,
                            confidence=0.8,
                            source_field='comments.author'
                        ))

        return relationships

    def _extract_confluence_metadata(self, metadata: Dict[str, any]) -> List[UserRelationship]:
        """Extract user relationships from Confluence metadata."""
        relationships = []

        # Creator
        if 'creator' in metadata and metadata['creator']:
            creator = metadata['creator']
            if isinstance(creator, dict):
                if 'email' in creator:
                    relationships.append(UserRelationship(
                        user_identifier=creator['email'],
                        relationship_type=RelationshipType.OWNER,
                        confidence=1.0,
                        source_field='creator.email'
                    ))
                elif 'displayName' in creator:
                    relationships.append(UserRelationship(
                        user_identifier=creator['displayName'],
                        relationship_type=RelationshipType.OWNER,
                        confidence=0.9,
                        source_field='creator.displayName'
                    ))

        # Last modifier
        if 'lastModifier' in metadata and metadata['lastModifier']:
            modifier = metadata['lastModifier']
            if isinstance(modifier, dict):
                if 'email' in modifier:
                    relationships.append(UserRelationship(
                        user_identifier=modifier['email'],
                        relationship_type=RelationshipType.CONTRIBUTOR,
                        confidence=0.95,
                        source_field='lastModifier.email'
                    ))

        # Contributors/Restrictions
        if 'restrictions' in metadata and metadata['restrictions']:
            restrictions = metadata['restrictions']
            if 'user' in restrictions:
                for user in restrictions['user']:
                    if isinstance(user, dict) and 'email' in user:
                        relationships.append(UserRelationship(
                            user_identifier=user['email'],
                            relationship_type=RelationshipType.SUBSCRIBER,
                            confidence=0.85,
                            source_field='restrictions.user'
                        ))

        return relationships

    def _extract_common_metadata(self, metadata: Dict[str, any]) -> List[UserRelationship]:
        """Extract user relationships using common metadata patterns."""
        relationships = []

        # Look for common metadata fields
        common_fields = {
            'author': RelationshipType.OWNER,
            'creator': RelationshipType.OWNER,
            'owner': RelationshipType.OWNER,
            'assignee': RelationshipType.SUBSCRIBER,
            'reviewer': RelationshipType.REVIEWER,
            'contributor': RelationshipType.CONTRIBUTOR,
            'updater': RelationshipType.CONTRIBUTOR,
        }

        for field_name, rel_type in common_fields.items():
            if field_name in metadata and metadata[field_name]:
                value = metadata[field_name]
                if isinstance(value, str) and value.strip():
                    relationships.append(UserRelationship(
                        user_identifier=value.strip(),
                        relationship_type=rel_type,
                        confidence=0.8,
                        source_field=f'metadata.{field_name}'
                    ))
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str) and item.strip():
                            relationships.append(UserRelationship(
                                user_identifier=item.strip(),
                                relationship_type=rel_type,
                                confidence=0.8,
                                source_field=f'metadata.{field_name}'
                            ))

        return relationships

    def _extract_from_content(self, content: str, source_type: str) -> List[UserRelationship]:
        """Extract user relationships from document content using regex patterns."""
        relationships = []
        content_lower = content.lower()

        # Get patterns for this source type
        patterns = self._patterns.get(source_type, self._patterns['common'])

        for pattern, rel_type_str, confidence in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            rel_type = getattr(RelationshipType, rel_type_str.upper(), RelationshipType.VIEWER)

            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]  # Take first group if multiple

                relationships.append(UserRelationship(
                    user_identifier=match.strip(),
                    relationship_type=rel_type,
                    confidence=confidence * 0.7,  # Reduce confidence for content extraction
                    source_field='content'
                ))

        return relationships

    def _deduplicate_relationships(self, relationships: List[UserRelationship]) -> List[UserRelationship]:
        """Remove duplicate relationships, keeping the highest confidence one."""
        seen = {}
        unique_relationships = []

        for rel in relationships:
            key = (rel.user_identifier.lower(), rel.relationship_type)

            if key not in seen or rel.confidence > seen[key].confidence:
                seen[key] = rel
                unique_relationships.append(rel)

        return unique_relationships

    def get_supported_sources(self) -> List[str]:
        """Get list of supported source types for user extraction."""
        return list(self._patterns.keys())
