"""
Confluence Connector - Documentation Intelligence
=================================================

Integrates with Confluence to fetch documentation, assess quality,
and identify knowledge gaps for intelligent documentation analysis.
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass
import re
from collections import Counter

try:
    from atlassian import Confluence
    CONFLUENCE_AVAILABLE = True
except ImportError:
    CONFLUENCE_AVAILABLE = False
    Confluence = None


@dataclass
class ConfluenceDocument:
    """Represents a Confluence document with analysis metadata."""
    id: str
    title: str
    space_key: str
    content: str
    content_type: str  # page, blogpost, comment
    created: datetime
    updated: datetime
    creator: str
    last_modifier: str
    labels: List[str]
    word_count: int
    links_count: int
    attachments_count: int
    version: int
    url: str


@dataclass
class DocumentQuality:
    """Quality assessment for documentation."""
    completeness_score: float  # 0-1
    freshness_score: float  # 0-1
    structure_score: float  # 0-1
    coverage_score: float  # 0-1
    overall_score: float  # 0-1
    issues: List[str]
    recommendations: List[str]


@dataclass
class DocumentationAnalytics:
    """Analytics for a set of Confluence documents."""
    total_documents: int
    total_pages: int
    total_blogposts: int
    avg_word_count: float
    avg_quality_score: float
    stale_documents: int  # Not updated in 6+ months
    outdated_documents: int  # Not updated in 3-6 months
    recent_documents: int  # Updated in last 3 months
    coverage_gaps: List[str]
    top_contributors: List[Dict[str, Any]]
    common_topics: List[str]


class ConfluenceConnector:
    """
    Confluence API integration with documentation intelligence.
    
    Provides:
    - Document fetching from spaces
    - Content quality assessment
    - Knowledge gap identification
    - Documentation coverage analysis
    - Freshness and completeness metrics
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, log_client=None):
        """
        Initialize Confluence connector.
        
        Args:
            config: Confluence configuration with url, username, api_token
            log_client: Optional log collector client
        """
        self.config = config or self._get_config_from_env()
        self.log_client = log_client
        self.confluence_client = None
        
        if CONFLUENCE_AVAILABLE and self.config.get('url'):
            try:
                self.confluence_client = Confluence(
                    url=self.config['url'],
                    username=self.config.get('username'),
                    password=self.config.get('api_token'),
                    cloud=True
                )
            except Exception as e:
                if self.log_client:
                    asyncio.create_task(self.log_client.log_error(
                        f"Failed to initialize Confluence client: {str(e)}",
                        context={"config": self.config}
                    ))
    
    def _get_config_from_env(self) -> Dict[str, str]:
        """Get Confluence configuration from environment variables."""
        return {
            'url': os.getenv('CONFLUENCE_URL', ''),
            'username': os.getenv('CONFLUENCE_USERNAME', ''),
            'api_token': os.getenv('CONFLUENCE_API_TOKEN', ''),
            'space_key': os.getenv('CONFLUENCE_SPACE_KEY', '')
        }
    
    async def fetch_documents(
        self,
        space_key: str,
        max_results: int = 500,
        content_type: str = 'page'
    ) -> List[ConfluenceDocument]:
        """
        Fetch Confluence documents from a space.
        
        Args:
            space_key: Confluence space key
            max_results: Maximum number of documents to fetch
            content_type: Type of content (page, blogpost)
            
        Returns:
            List of ConfluenceDocument objects
        """
        if not self.confluence_client:
            if self.log_client:
                await self.log_client.log_warning(
                    "Confluence client not initialized, returning mock data",
                    context={"space_key": space_key}
                )
            return self._generate_mock_documents(space_key, 20)
        
        try:
            # Fetch pages from space
            start = 0
            limit = 50
            all_documents = []
            
            while len(all_documents) < max_results:
                pages = self.confluence_client.get_all_pages_from_space(
                    space=space_key,
                    start=start,
                    limit=limit,
                    expand='body.storage,version,history,metadata.labels'
                )
                
                if not pages:
                    break
                
                for page in pages:
                    doc = await self._page_to_document(page, space_key)
                    if doc:
                        all_documents.append(doc)
                
                start += limit
                
                if len(pages) < limit:
                    break
            
            if self.log_client:
                await self.log_client.log_info(
                    f"Fetched {len(all_documents)} documents from Confluence",
                    context={
                        "space_key": space_key,
                        "document_count": len(all_documents)
                    }
                )
            
            return all_documents[:max_results]
            
        except Exception as e:
            if self.log_client:
                await self.log_client.log_error(
                    f"Failed to fetch Confluence documents: {str(e)}",
                    context={"space_key": space_key}
                )
            return []
    
    async def _page_to_document(
        self,
        page: Dict[str, Any],
        space_key: str
    ) -> Optional[ConfluenceDocument]:
        """Convert Confluence page to ConfluenceDocument object."""
        try:
            # Extract content
            content = page.get('body', {}).get('storage', {}).get('value', '')
            content_text = self._strip_html(content)
            
            # Parse dates
            created = datetime.fromisoformat(
                page.get('history', {}).get('createdDate', datetime.now().isoformat()).replace('Z', '+00:00')
            )
            
            version_info = page.get('version', {})
            updated = datetime.fromisoformat(
                version_info.get('when', datetime.now().isoformat()).replace('Z', '+00:00')
            )
            
            # Extract labels
            labels = [
                label.get('name', '')
                for label in page.get('metadata', {}).get('labels', {}).get('results', [])
            ]
            
            # Count links and attachments
            links_count = content.count('<a href=') + content.count('</a>')
            attachments_count = len(page.get('metadata', {}).get('attachments', {}).get('results', []))
            
            return ConfluenceDocument(
                id=page.get('id', ''),
                title=page.get('title', ''),
                space_key=space_key,
                content=content_text,
                content_type=page.get('type', 'page'),
                created=created,
                updated=updated,
                creator=page.get('history', {}).get('createdBy', {}).get('displayName', 'Unknown'),
                last_modifier=version_info.get('by', {}).get('displayName', 'Unknown'),
                labels=labels,
                word_count=len(content_text.split()),
                links_count=links_count,
                attachments_count=attachments_count,
                version=version_info.get('number', 1),
                url=f"{self.config['url']}/wiki/spaces/{space_key}/pages/{page.get('id', '')}",
            )
            
        except Exception as e:
            if self.log_client:
                await self.log_client.log_error(
                    f"Failed to parse Confluence page: {str(e)}",
                    context={"page_id": page.get('id', 'unknown')}
                )
            return None
    
    def _strip_html(self, html: str) -> str:
        """Strip HTML tags from content."""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', html)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    async def assess_document_quality(
        self,
        document: ConfluenceDocument
    ) -> DocumentQuality:
        """
        Assess the quality of a Confluence document.
        
        Args:
            document: ConfluenceDocument to assess
            
        Returns:
            DocumentQuality with scores and recommendations
        """
        issues = []
        recommendations = []
        
        # 1. Completeness score
        completeness_score = self._calculate_completeness(document, issues, recommendations)
        
        # 2. Freshness score
        freshness_score = self._calculate_freshness(document, issues, recommendations)
        
        # 3. Structure score
        structure_score = self._calculate_structure(document, issues, recommendations)
        
        # 4. Coverage score
        coverage_score = self._calculate_coverage(document, issues, recommendations)
        
        # Overall score
        overall_score = (
            completeness_score * 0.3 +
            freshness_score * 0.25 +
            structure_score * 0.25 +
            coverage_score * 0.2
        )
        
        if self.log_client:
            await self.log_client.log_business_event(
                "document_quality_assessed",
                {
                    "document_id": document.id,
                    "overall_score": overall_score,
                    "issue_count": len(issues)
                }
            )
        
        return DocumentQuality(
            completeness_score=round(completeness_score, 2),
            freshness_score=round(freshness_score, 2),
            structure_score=round(structure_score, 2),
            coverage_score=round(coverage_score, 2),
            overall_score=round(overall_score, 2),
            issues=issues,
            recommendations=recommendations
        )
    
    def _calculate_completeness(
        self,
        document: ConfluenceDocument,
        issues: List[str],
        recommendations: List[str]
    ) -> float:
        """Calculate completeness score based on content depth."""
        score = 1.0
        
        # Word count check
        if document.word_count < 100:
            score -= 0.4
            issues.append("Document is too short (< 100 words)")
            recommendations.append("Add more detailed content")
        elif document.word_count < 300:
            score -= 0.2
            recommendations.append("Consider adding more details")
        
        # Links check
        if document.links_count == 0:
            score -= 0.2
            issues.append("No links to related content")
            recommendations.append("Add links to related documentation")
        
        # Labels check
        if not document.labels:
            score -= 0.1
            recommendations.append("Add labels for better discoverability")
        
        return max(0.0, score)
    
    def _calculate_freshness(
        self,
        document: ConfluenceDocument,
        issues: List[str],
        recommendations: List[str]
    ) -> float:
        """Calculate freshness score based on update recency."""
        days_since_update = (datetime.now() - document.updated.replace(tzinfo=None)).days
        
        if days_since_update <= 90:
            return 1.0
        elif days_since_update <= 180:
            recommendations.append("Consider reviewing for relevance")
            return 0.7
        elif days_since_update <= 365:
            issues.append("Document is outdated (6+ months)")
            recommendations.append("Update or archive this document")
            return 0.4
        else:
            issues.append("Document is very stale (1+ year)")
            recommendations.append("Urgently review or archive")
            return 0.1
    
    def _calculate_structure(
        self,
        document: ConfluenceDocument,
        issues: List[str],
        recommendations: List[str]
    ) -> float:
        """Calculate structure score based on formatting and organization."""
        score = 1.0
        content = document.content.lower()
        
        # Check for headings (approximate)
        heading_count = len(re.findall(r'\n[A-Z][^\n]+\n', document.content))
        
        if heading_count == 0:
            score -= 0.3
            issues.append("No clear headings or structure")
            recommendations.append("Add headings to organize content")
        elif heading_count < 3 and document.word_count > 500:
            score -= 0.1
            recommendations.append("Add more section headings")
        
        # Check for code blocks
        has_code = 'code' in content or '```' in content
        
        # Check for lists (bullet points or numbered)
        has_lists = any(indicator in content for indicator in ['* ', '- ', '1. ', '2. '])
        
        if not has_lists and document.word_count > 300:
            score -= 0.1
            recommendations.append("Use lists for better readability")
        
        return max(0.0, score)
    
    def _calculate_coverage(
        self,
        document: ConfluenceDocument,
        issues: List[str],
        recommendations: List[str]
    ) -> float:
        """Calculate coverage score based on expected content areas."""
        score = 1.0
        content = document.content.lower()
        title = document.title.lower()
        
        # Keywords that suggest documentation types
        is_api_doc = any(kw in title or kw in content for kw in ['api', 'endpoint', 'rest', 'graphql'])
        is_guide = any(kw in title for kw in ['guide', 'tutorial', 'how to', 'quickstart'])
        is_reference = any(kw in title for kw in ['reference', 'specification', 'schema'])
        
        # API documentation should have examples
        if is_api_doc:
            if 'example' not in content and 'sample' not in content:
                score -= 0.2
                recommendations.append("Add API usage examples")
            if 'request' not in content or 'response' not in content:
                score -= 0.1
                recommendations.append("Include request/response examples")
        
        # Guides should have steps
        if is_guide:
            step_indicators = ['step 1', 'first', 'then', 'next', 'finally']
            if not any(indicator in content for indicator in step_indicators):
                score -= 0.2
                recommendations.append("Add clear step-by-step instructions")
        
        # Technical docs should have some depth
        if document.word_count < 200:
            score -= 0.1
        
        return max(0.0, score)
    
    async def analyze_documentation(
        self,
        documents: List[ConfluenceDocument]
    ) -> DocumentationAnalytics:
        """
        Analyze a set of Confluence documents for insights.
        
        Args:
            documents: List of ConfluenceDocument objects
            
        Returns:
            DocumentationAnalytics with metrics and insights
        """
        if not documents:
            return DocumentationAnalytics(
                total_documents=0,
                total_pages=0,
                total_blogposts=0,
                avg_word_count=0.0,
                avg_quality_score=0.0,
                stale_documents=0,
                outdated_documents=0,
                recent_documents=0,
                coverage_gaps=[],
                top_contributors=[],
                common_topics=[]
            )
        
        # Basic counts
        total_documents = len(documents)
        total_pages = sum(1 for d in documents if d.content_type == 'page')
        total_blogposts = sum(1 for d in documents if d.content_type == 'blogpost')
        
        # Average word count
        avg_word_count = sum(d.word_count for d in documents) / total_documents
        
        # Assess quality for all documents
        quality_scores = []
        for doc in documents:
            quality = await self.assess_document_quality(doc)
            quality_scores.append(quality.overall_score)
        
        avg_quality_score = sum(quality_scores) / len(quality_scores)
        
        # Document freshness
        now = datetime.now()
        stale_documents = 0
        outdated_documents = 0
        recent_documents = 0
        
        for doc in documents:
            days_since_update = (now - doc.updated.replace(tzinfo=None)).days
            if days_since_update > 180:
                stale_documents += 1
            elif days_since_update > 90:
                outdated_documents += 1
            else:
                recent_documents += 1
        
        # Top contributors
        contributor_counts = Counter()
        for doc in documents:
            contributor_counts[doc.last_modifier] += 1
        
        top_contributors = [
            {"name": name, "document_count": count}
            for name, count in contributor_counts.most_common(5)
        ]
        
        # Common topics (from labels)
        all_labels = []
        for doc in documents:
            all_labels.extend(doc.labels)
        
        label_counts = Counter(all_labels)
        common_topics = [label for label, _ in label_counts.most_common(10)]
        
        # Identify coverage gaps
        coverage_gaps = self._identify_coverage_gaps(documents)
        
        if self.log_client:
            await self.log_client.log_business_event(
                "documentation_analysis_completed",
                {
                    "total_documents": total_documents,
                    "avg_quality_score": avg_quality_score,
                    "stale_documents": stale_documents
                }
            )
        
        return DocumentationAnalytics(
            total_documents=total_documents,
            total_pages=total_pages,
            total_blogposts=total_blogposts,
            avg_word_count=round(avg_word_count, 2),
            avg_quality_score=round(avg_quality_score, 2),
            stale_documents=stale_documents,
            outdated_documents=outdated_documents,
            recent_documents=recent_documents,
            coverage_gaps=coverage_gaps,
            top_contributors=top_contributors,
            common_topics=common_topics
        )
    
    def _identify_coverage_gaps(
        self,
        documents: List[ConfluenceDocument]
    ) -> List[str]:
        """Identify gaps in documentation coverage."""
        gaps = []
        
        # Expected documentation types
        all_content = ' '.join(doc.title.lower() + ' ' + doc.content.lower() for doc in documents)
        
        # Check for common documentation needs
        doc_types = {
            'api': ['api', 'endpoint', 'rest'],
            'architecture': ['architecture', 'design', 'system'],
            'onboarding': ['onboarding', 'getting started', 'quickstart'],
            'deployment': ['deployment', 'installation', 'setup'],
            'troubleshooting': ['troubleshooting', 'debugging', 'common issues'],
            'testing': ['testing', 'test', 'qa'],
            'security': ['security', 'authentication', 'authorization']
        }
        
        for doc_type, keywords in doc_types.items():
            if not any(keyword in all_content for keyword in keywords):
                gaps.append(f"Missing {doc_type} documentation")
        
        return gaps
    
    def _generate_mock_documents(
        self,
        space_key: str,
        count: int
    ) -> List[ConfluenceDocument]:
        """Generate mock Confluence documents for testing."""
        documents = []
        
        doc_types = [
            ("API Reference", "This document provides comprehensive API documentation with endpoints and examples."),
            ("User Guide", "A step-by-step guide for users to get started with the platform."),
            ("Architecture Overview", "System architecture and design decisions for the platform."),
            ("Troubleshooting", "Common issues and how to resolve them."),
            ("Release Notes", "Latest features and bug fixes in this release.")
        ]
        
        for i in range(count):
            title, content_snippet = doc_types[i % len(doc_types)]
            
            created = datetime.now() - timedelta(days=count - i)
            updated = created + timedelta(days=(count - i) // 2)
            
            document = ConfluenceDocument(
                id=f"page-{1000 + i}",
                title=f"{title} {i}",
                space_key=space_key,
                content=content_snippet * 10,  # Repeat to get more words
                content_type='page',
                created=created,
                updated=updated,
                creator=f"user-{i % 3}",
                last_modifier=f"user-{i % 4}",
                labels=[f"label-{i % 5}", "documentation"],
                word_count=len((content_snippet * 10).split()),
                links_count=(i % 5) + 1,
                attachments_count=i % 3,
                version=(i % 10) + 1,
                url=f"https://mock.atlassian.net/wiki/spaces/{space_key}/pages/page-{1000 + i}"
            )
            documents.append(document)
        
        return documents
    
    async def get_space_overview(
        self,
        space_key: str
    ) -> Dict[str, Any]:
        """
        Get overview metrics for a Confluence space.
        
        Args:
            space_key: Confluence space key
            
        Returns:
            Dictionary with space overview metrics
        """
        documents = await self.fetch_documents(space_key)
        analytics = await self.analyze_documentation(documents)
        
        return {
            "space_key": space_key,
            "total_documents": analytics.total_documents,
            "avg_word_count": analytics.avg_word_count,
            "avg_quality_score": analytics.avg_quality_score,
            "freshness": {
                "recent": analytics.recent_documents,
                "outdated": analytics.outdated_documents,
                "stale": analytics.stale_documents
            },
            "coverage_gaps": analytics.coverage_gaps,
            "top_contributors": analytics.top_contributors,
            "common_topics": analytics.common_topics
        }

