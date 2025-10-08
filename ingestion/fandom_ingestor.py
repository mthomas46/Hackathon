"""
Fandom Wiki crawler and ingestion module.

Fandom wikis (like Warhammer 40k) have different HTML structure and API
compared to standard Wikipedia. This module provides a specialized crawler.
"""
import asyncio
import hashlib
import logging
from typing import List, Optional, Set, Dict, Tuple, Any
from datetime import datetime
import httpx
from bs4 import BeautifulSoup

from ingestion.models import NormalizedDocument, CrawlReport
from ingestion.tagging import UniversalTaggingManager, UniversalTaggingConfig, TagCollection

logger = logging.getLogger(__name__)


class FandomWikiIngestor:
    """
    Crawl and ingest Fandom wiki pages with configurable depth.
    
    Fandom wikis use a different API and HTML structure than Wikipedia.
    This ingestor is specifically designed for fandom.com wikis (e.g., Warhammer 40k).
    """
    
    def __init__(
        self,
        tagging_config: Optional[UniversalTaggingConfig] = None,
        enable_tagging: bool = True
    ):
        """
        Initialize Fandom wiki ingestor.
        
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
        Crawl Fandom wiki starting from a page.
        
        Args:
            original_page_url: Starting Fandom wiki URL
            max_surface_links: Max number of direct links from original page
            max_depth_distance: Max link depth (0 = original only, 1 = +direct links, etc.)
        
        Returns:
            List of normalized documents with link relationships
        
        Example:
            Original: https://warhammer40k.fandom.com/wiki/Horus_Heresy
            max_surface_links=50, max_depth_distance=2
        """
        self.start_time = datetime.now()
        logger.info(f"Starting Fandom wiki crawl from: {original_page_url}")
        logger.info(f"Parameters: max_surface_links={max_surface_links}, max_depth_distance={max_depth_distance}")
        
        # Extract wiki domain and page title
        wiki_domain = self._extract_wiki_domain(original_page_url)
        page_title = self._extract_page_title(original_page_url)
        
        # Start crawling
        documents = await self._crawl_recursive(
            page_url=original_page_url,
            page_title=page_title,
            wiki_domain=wiki_domain,
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
            doc.metadata['wiki_domain'] = wiki_domain
        
        # Apply universal tagging
        if self.enable_tagging and self.tagging_manager:
            logger.info(f"🏷️  Applying universal tagging to {len(documents)} documents...")
            documents, self.tag_collection = await self.tagging_manager.tag_documents(
                documents=documents,
                source_type='wikipedia',  # Use 'wikipedia' type for tag prefixes
                user_tags=None,  # Use config defaults
                corpus_analysis=None  # No corpus analysis yet
            )
            logger.info(f"✅ Tagging complete: {self.tag_collection.total_count()} unique tags")
        
        self.end_time = datetime.now()
        logger.info(f"✅ Crawled {len(documents)} Fandom wiki pages")
        logger.info(f"📊 Crawl graph: {len(self.crawl_graph)} nodes")
        
        return documents
    
    async def _crawl_recursive(
        self,
        page_url: str,
        page_title: str,
        wiki_domain: str,
        current_depth: int,
        max_depth: int,
        max_links_per_page: int,
        parent_page: Optional[str]
    ) -> List[NormalizedDocument]:
        """Recursively crawl Fandom wiki pages."""
        
        # Check if already visited
        if page_url in self.visited_pages:
            return []
        
        # Check depth limit
        if current_depth > max_depth:
            return []
        
        self.visited_pages.add(page_url)
        documents = []
        
        try:
            # Fetch page data
            page_data = await self._fetch_fandom_page(page_url, wiki_domain)
            
            # Normalize to document
            doc = await self._normalize_fandom_page(
                page_data,
                current_depth,
                parent_page
            )
            documents.append(doc)
            
            # Log link discovery and filtering
            total_links_found = len(page_data['links'])
            links_to_follow = min(max_links_per_page, total_links_found) if current_depth < max_depth else 0
            logger.info(f"  {'  ' * current_depth}[Depth {current_depth}] {page_title} → {total_links_found} links found, following {links_to_follow}")
            
            # Track in crawl graph
            self.crawl_graph[page_title] = {
                'url': page_url,
                'depth': current_depth,
                'parent': parent_page,
                'children': []
            }
            
            # Continue crawling if not at max depth
            if current_depth < max_depth:
                links_to_crawl = self._filter_links(
                    page_data['links'],
                    max_links_per_page
                )
                
                # Crawl linked pages
                tasks = []
                for link_title, link_url in links_to_crawl:
                    if link_url not in self.visited_pages:
                        self.crawl_graph[page_title]['children'].append(link_title)
                        tasks.append(
                            self._crawl_recursive(
                                page_url=link_url,
                                page_title=link_title,
                                wiki_domain=wiki_domain,
                                current_depth=current_depth + 1,
                                max_depth=max_depth,
                                max_links_per_page=max_links_per_page,
                                parent_page=page_title
                            )
                        )
                
                # Execute tasks concurrently
                results = await asyncio.gather(*tasks)
                for res in results:
                    documents.extend(res)
                
                # Rate limiting
                await asyncio.sleep(0.5)
        
        except Exception as e:
            logger.warning(f"Failed to crawl {page_url}: {e}")
        
        return documents
    
    async def _fetch_fandom_page(self, url: str, wiki_domain: str) -> Dict[str, Any]:
        """
        Fetch Fandom wiki page content using web scraping.
        
        Fandom wikis don't have a public API like Wikipedia, so we scrape HTML.
        """
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                html = response.text
                
                # Parse HTML with BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract title
                title_elem = soup.find('h1', class_='page-header__title')
                title = title_elem.get_text(strip=True) if title_elem else self._extract_page_title(url)
                
                # Extract main content
                content = self._extract_fandom_content(soup)
                
                # Extract links
                links = self._extract_fandom_links(soup, wiki_domain)
                
                # Extract metadata
                last_modified = self._extract_last_modified(soup)
                categories = self._extract_fandom_categories(soup)
                
                return {
                    'title': title,
                    'content': content,
                    'url': url,
                    'links': links,
                    'last_modified': last_modified,
                    'categories': categories
                }
            
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error fetching {url}: {e}")
                raise
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                raise
    
    def _extract_fandom_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from Fandom page."""
        # Fandom pages have content in <div class="mw-parser-output">
        content_div = soup.find('div', class_='mw-parser-output')
        
        if not content_div:
            logger.warning("Could not find main content div")
            return ""
        
        # Extract text from paragraphs and headings
        content_parts = []
        
        for elem in content_div.find_all(['p', 'h2', 'h3', 'h4', 'ul', 'ol']):
            if elem.name in ['h2', 'h3', 'h4']:
                # Heading
                text = elem.get_text(strip=True)
                if text and not text.startswith('[edit'):
                    level = int(elem.name[1])
                    content_parts.append('#' * level + ' ' + text)
            elif elem.name in ['ul', 'ol']:
                # List
                for li in elem.find_all('li', recursive=False):
                    text = li.get_text(strip=True)
                    if text:
                        content_parts.append('- ' + text)
            else:
                # Paragraph
                text = elem.get_text(strip=True)
                if text:
                    content_parts.append(text)
        
        return '\n\n'.join(content_parts)
    
    def _extract_fandom_links(self, soup: BeautifulSoup, wiki_domain: str) -> List[Tuple[str, str]]:
        """Extract internal wiki links from Fandom page."""
        links = []
        content_div = soup.find('div', class_='mw-parser-output')
        
        if not content_div:
            return links
        
        for link in content_div.find_all('a', href=True):
            href = link['href']
            
            # Only internal wiki links
            if href.startswith('/wiki/'):
                # Make absolute URL
                full_url = f"https://{wiki_domain}{href}"
                
                # Extract link title
                link_title = link.get_text(strip=True) or href.split('/')[-1].replace('_', ' ')
                
                # Filter out special pages
                if not self._is_special_page(href):
                    links.append((link_title, full_url))
        
        return links
    
    def _is_special_page(self, href: str) -> bool:
        """Check if a link is to a special/meta page."""
        special_terms = [
            'Special:',
            'File:',
            'Template:',
            'Category:',
            'Help:',
            'MediaWiki:',
            'User:',
            'Talk:',
            'Portal:',
            ':File:',
            ':Category:'
        ]
        return any(term in href for term in special_terms)
    
    def _extract_last_modified(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract last modified date from Fandom page."""
        # Try to find page tools or footer with last modified info
        modified_elem = soup.find('span', class_='last-modified-date')
        if modified_elem:
            return modified_elem.get_text(strip=True)
        
        # Fallback: look for any date-like text
        return None
    
    def _extract_fandom_categories(self, soup: BeautifulSoup) -> List[str]:
        """Extract categories from Fandom page."""
        categories = []
        
        # Categories are usually in the footer
        cat_container = soup.find('div', class_='page-footer__categories')
        if cat_container:
            for cat_link in cat_container.find_all('a'):
                cat_text = cat_link.get_text(strip=True)
                if cat_text:
                    categories.append(cat_text.lower().replace(' ', '-'))
        
        return categories or ['general']
    
    async def _normalize_fandom_page(
        self,
        page_data: Dict[str, Any],
        depth: int,
        parent_page: Optional[str]
    ) -> NormalizedDocument:
        """Normalize Fandom wiki page to markdown format."""
        
        content_md = f"""# {page_data['title']}

**Source**: Fandom Wiki  
**URL**: {page_data['url']}  
**Last Modified**: {page_data['last_modified'] or 'Unknown'}  
**Crawl Depth**: {depth}  
**Parent Page**: {parent_page or 'N/A (origin)'}

---

## Content

{page_data['content']}

---

## Links Found

This page contains {len(page_data['links'])} links to other wiki articles.

"""
        
        if parent_page:
            content_md += f"\n**Navigation**: [Origin] → ... → [{parent_page}] → **[{page_data['title']}]**\n"
        
        return NormalizedDocument(
            document_id=f"fandom-{hashlib.md5(page_data['url'].encode()).hexdigest()[:8]}",
            title=f"Fandom: {page_data['title']}",
            content_md=content_md,
            original_format='fandom-wiki',
            metadata={
                'source': 'fandom-wiki',
                'file_type': 'document',
                'url': page_data['url'],
                'page_title': page_data['title'],
                'crawl_depth': depth,
                'parent_page': parent_page,
                'link_count': len(page_data['links']),
                'categories': page_data['categories'],
                'last_modified': page_data['last_modified'],
            },
            tags=[
                "source:fandom-wiki",
                "file_type:document",
                f"depth:{depth}",
                *[f"category:{cat}" for cat in page_data['categories'][:5]]
            ]
        )
    
    def _filter_links(
        self,
        links: List[Tuple[str, str]],
        max_links: int
    ) -> List[Tuple[str, str]]:
        """Filter and prioritize links to crawl."""
        # Remove duplicates
        unique_links = list(dict.fromkeys(links))
        
        return unique_links[:max_links]
    
    def _extract_wiki_domain(self, url: str) -> str:
        """Extract wiki domain from URL."""
        # https://warhammer40k.fandom.com/wiki/Horus_Heresy → warhammer40k.fandom.com
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc
    
    def _extract_page_title(self, url: str) -> str:
        """Extract page title from Fandom wiki URL."""
        # https://warhammer40k.fandom.com/wiki/Horus_Heresy → Horus Heresy
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

