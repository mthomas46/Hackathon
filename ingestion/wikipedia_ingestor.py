"""
Wikipedia crawling and ingestion module.
"""
import asyncio
import hashlib
import logging
from typing import List, Optional, Set, Dict, Tuple, Any
from datetime import datetime
import httpx
from ingestion.models import NormalizedDocument, CrawlReport
from ingestion.tagging import UniversalTaggingManager, UniversalTaggingConfig, TagCollection

logger = logging.getLogger(__name__)


class WikipediaIngestor:
    """Crawl and ingest Wikipedia pages with configurable depth."""
    
    def __init__(
        self,
        tagging_config: Optional[UniversalTaggingConfig] = None,
        enable_tagging: bool = True
    ):
        """
        Initialize Wikipedia ingestor.
        
        Args:
            tagging_config: Configuration for universal tagging
            enable_tagging: Whether to apply universal tagging to documents
        """
        self.visited_pages: Set[str] = set()
        self.crawl_graph: Dict[str, Dict[str, Any]] = {}
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        # Tagging integration
        self.enable_tagging = enable_tagging
        self.tagging_manager = UniversalTaggingManager(
            tagging_config or UniversalTaggingConfig()
        ) if enable_tagging else None
        self.tag_collection: Optional[TagCollection] = None
    
    async def crawl_and_ingest(
        self,
        original_page_url: str,
        max_surface_links: int = 10,
        max_depth_distance: int = 2
    ) -> List[NormalizedDocument]:
        """
        Crawl Wikipedia starting from a page.
        
        Args:
            original_page_url: Starting Wikipedia URL
            max_surface_links: Max number of direct links from original page
            max_depth_distance: Max link depth (0 = original only, 1 = +direct links, etc.)
        
        Returns:
            List of normalized documents with link relationships
        
        Example:
            Original: https://en.wikipedia.org/wiki/Machine_learning
            max_surface_links=5, max_depth_distance=2
            
            Depth 0 (original): Machine_learning
            Depth 1 (direct links, max 5): Artificial_intelligence, Deep_learning, Neural_network, Supervised_learning, Unsupervised_learning
            Depth 2 (links from depth 1, max 5 each): ... up to 25 more pages
        """
        self.start_time = datetime.now()
        logger.info(f"Starting Wikipedia crawl from: {original_page_url}")
        logger.info(f"Parameters: max_surface_links={max_surface_links}, max_depth_distance={max_depth_distance}")
        
        # Parse original page info
        page_title = self._extract_page_title(original_page_url)
        
        # Start crawling
        documents = await self._crawl_recursive(
            page_url=original_page_url,
            page_title=page_title,
            current_depth=0,
            max_depth=max_depth_distance,
            max_links_per_page=max_surface_links,
            parent_page=None
        )
        
        # Add crawl metadata to all documents
        for doc in documents:
            doc.metadata['crawl_origin'] = page_title
            doc.metadata['crawl_max_depth'] = max_depth_distance
            doc.metadata['crawl_max_surface'] = max_surface_links
        
        # Apply universal tagging
        if self.enable_tagging and self.tagging_manager:
            logger.info(f"🏷️  Applying universal tagging to {len(documents)} documents...")
            documents, self.tag_collection = await self.tagging_manager.tag_documents(
                documents=documents,
                source_type='wikipedia',
                user_tags=None,  # Use config defaults
                corpus_analysis=None  # No corpus analysis yet
            )
            logger.info(f"✅ Tagging complete: {self.tag_collection.total_count()} unique tags")
        
        self.end_time = datetime.now()
        logger.info(f"✅ Crawled {len(documents)} Wikipedia pages")
        logger.info(f"📊 Crawl graph: {len(self.crawl_graph)} nodes")
        
        return documents
    
    async def _crawl_recursive(
        self,
        page_url: str,
        page_title: str,
        current_depth: int,
        max_depth: int,
        max_links_per_page: int,
        parent_page: Optional[str]
    ) -> List[NormalizedDocument]:
        """Recursively crawl Wikipedia pages."""
        
        # Check if already visited
        if page_url in self.visited_pages:
            return []
        
        # Check depth limit
        if current_depth > max_depth:
            return []
        
        self.visited_pages.add(page_url)
        documents = []
        
        # Fetch and normalize current page
        try:
            page_data = await self._fetch_wikipedia_page(page_url)
            doc = self._normalize_wikipedia_page(
                page_data,
                current_depth,
                parent_page
            )
            documents.append(doc)
            
            indent = "  " * current_depth
            logger.info(f"{indent}[Depth {current_depth}] {page_title} → {len(page_data['links'])} links found")
            
            # Track in crawl graph
            self.crawl_graph[page_title] = {
                'url': page_url,
                'depth': current_depth,
                'parent': parent_page,
                'children': []
            }
            
            # If not at max depth, crawl linked pages
            if current_depth < max_depth:
                # Filter and limit links
                links_to_crawl = self._filter_links(
                    page_data['links'],
                    max_links_per_page
                )
                
                # Crawl each link
                for link_title, link_url in links_to_crawl:
                    if link_url not in self.visited_pages:
                        # Track parent-child relationship
                        self.crawl_graph[page_title]['children'].append(link_title)
                        
                        # Recursive crawl
                        child_docs = await self._crawl_recursive(
                            page_url=link_url,
                            page_title=link_title,
                            current_depth=current_depth + 1,
                            max_depth=max_depth,
                            max_links_per_page=max_links_per_page,
                            parent_page=page_title
                        )
                        documents.extend(child_docs)
                        
                        # Rate limiting
                        await asyncio.sleep(0.5)
        
        except Exception as e:
            logger.warning(f"Failed to crawl {page_url}: {e}")
        
        return documents
    
    async def _fetch_wikipedia_page(self, url: str) -> dict:
        """Fetch Wikipedia page content and extract links."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Use Wikipedia API for structured data
            api_url = "https://en.wikipedia.org/w/api.php"
            
            page_title = self._extract_page_title(url)
            
            # Fetch page content
            params = {
                'action': 'query',
                'format': 'json',
                'titles': page_title,
                'prop': 'extracts|links|info|revisions',
                'explaintext': True,
                'pllimit': 500,  # Get up to 500 links
                'inprop': 'url',
                'rvprop': 'timestamp|user'
            }
            
            response = await client.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            page = list(data['query']['pages'].values())[0]
            
            # Extract links
            links = []
            if 'links' in page:
                for link in page['links']:
                    link_title = link['title']
                    # Only include article links (no special pages)
                    if not link_title.startswith(('Wikipedia:', 'File:', 'Template:', 'Category:', 'Help:', 'Portal:')):
                        link_url = f"https://en.wikipedia.org/wiki/{link_title.replace(' ', '_')}"
                        links.append((link_title, link_url))
            
            return {
                'title': page.get('title', ''),
                'content': page.get('extract', ''),
                'url': page.get('fullurl', url),
                'links': links,
                'last_modified': page.get('revisions', [{}])[0].get('timestamp'),
                'last_editor': page.get('revisions', [{}])[0].get('user')
            }
    
    def _normalize_wikipedia_page(
        self,
        page_data: dict,
        depth: int,
        parent_page: Optional[str]
    ) -> NormalizedDocument:
        """Normalize Wikipedia page to markdown format."""
        
        # Convert Wikipedia content to markdown
        content_md = f"""# {page_data['title']}

**Source**: Wikipedia  
**URL**: {page_data['url']}  
**Last Modified**: {page_data['last_modified']}  
**Last Editor**: {page_data['last_editor']}  
**Crawl Depth**: {depth}  
**Parent Page**: {parent_page or 'N/A (origin)'}

---

## Content

{page_data['content']}

---

## Links Found

This page contains {len(page_data['links'])} links to other Wikipedia articles.
"""
        
        # Add link graph if not at origin
        if parent_page:
            content_md += f"\n**Navigation**: [Origin] → ... → [{parent_page}] → **[{page_data['title']}]**\n"
        
        # Extract categories from title/content
        categories = self._extract_categories(page_data['title'], page_data['content'])
        
        # Parse timestamp
        created_at = None
        updated_at = None
        if page_data['last_modified']:
            try:
                from dateutil import parser
                updated_at = parser.parse(page_data['last_modified'])
                created_at = updated_at  # Wikipedia doesn't expose creation date via API
            except:
                pass
        
        return NormalizedDocument(
            document_id=f"wikipedia-{hashlib.md5(page_data['url'].encode()).hexdigest()[:8]}",
            title=f"Wikipedia: {page_data['title']}",
            content_md=content_md,
            original_format='wikipedia',
            metadata={
                'source': 'wikipedia',
                'file_type': 'document',
                'language': 'en',
                'url': page_data['url'],
                'page_title': page_data['title'],
                'crawl_depth': depth,
                'parent_page': parent_page,
                'link_count': len(page_data['links']),
                'categories': categories,
                'author': page_data['last_editor'],
            },
            tags=[
                "source:wikipedia",
                "file_type:document",
                "language:en",
                f"depth:{depth}",
                *[f"category:{cat}" for cat in categories[:5]]
            ],
            created_at=created_at,
            updated_at=updated_at
        )
    
    def _filter_links(
        self,
        links: List[Tuple[str, str]],
        max_links: int
    ) -> List[Tuple[str, str]]:
        """Filter and prioritize links to crawl."""
        # Filter out common navigation links
        excluded_terms = ['list of', 'index of', 'outline of', 'glossary', 'portal:', 'category:']
        filtered = [
            (title, url) for title, url in links
            if not any(term in title.lower() for term in excluded_terms)
        ]
        
        return filtered[:max_links]
    
    def _extract_categories(self, title: str, content: str) -> List[str]:
        """Extract categories/topics from Wikipedia page."""
        categories = []
        
        # Common Wikipedia categories based on content keywords
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['algorithm', 'computation', 'computer', 'software', 'programming']):
            categories.append('computer-science')
        if any(word in content_lower for word in ['learning', 'neural', 'model', 'artificial intelligence']):
            categories.append('machine-learning')
        if any(word in content_lower for word in ['history', 'century', 'founded', 'ancient']):
            categories.append('history')
        if any(word in content_lower for word in ['science', 'research', 'scientific', 'study']):
            categories.append('science')
        if any(word in content_lower for word in ['technology', 'engineering', 'technical']):
            categories.append('technology')
        if any(word in content_lower for word in ['business', 'company', 'corporate', 'enterprise']):
            categories.append('business')
        
        return categories or ['general']
    
    def _extract_page_title(self, url: str) -> str:
        """Extract page title from Wikipedia URL."""
        # https://en.wikipedia.org/wiki/Machine_learning → Machine learning
        return url.split('/wiki/')[-1].replace('_', ' ')
    
    def get_tag_collection(self) -> Optional[TagCollection]:
        """
        Get the tag collection from the last crawl.
        
        Returns:
            TagCollection if tagging was enabled, None otherwise
        """
        return self.tag_collection
    
    def generate_crawl_report(self) -> CrawlReport:
        """Generate report of crawl graph."""
        duration = (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 0
        
        report = CrawlReport(
            total_pages=len(self.visited_pages),
            crawl_graph=self.crawl_graph,
            depth_distribution=self._calculate_depth_distribution(),
            link_statistics=self._calculate_link_statistics(),
            start_time=self.start_time or datetime.now(),
            end_time=self.end_time or datetime.now(),
            duration_seconds=duration
        )
        
        # Add tag collection if available
        if self.tag_collection:
            report.tag_collection = self.tag_collection.to_dict()
        
        return report
    
    def _calculate_depth_distribution(self) -> Dict[int, int]:
        """Calculate how many pages at each depth."""
        distribution = {}
        for node in self.crawl_graph.values():
            depth = node['depth']
            distribution[depth] = distribution.get(depth, 0) + 1
        return distribution
    
    def _calculate_link_statistics(self) -> Dict[str, Any]:
        """Calculate link statistics."""
        if not self.crawl_graph:
            return {
                'total_links_followed': 0,
                'average_links_per_page': 0,
                'max_children': 0
            }
        
        total_children = sum(len(node['children']) for node in self.crawl_graph.values())
        avg_children = total_children / len(self.crawl_graph)
        
        return {
            'total_links_followed': total_children,
            'average_links_per_page': round(avg_children, 2),
            'max_children': max((len(node['children']) for node in self.crawl_graph.values()), default=0)
        }

