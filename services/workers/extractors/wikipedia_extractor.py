"""Wikipedia Extractor Worker - Extract articles with link crawling."""

import hashlib
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from services.workers.celery_app import app
from services.workers.shared.base_worker import BaseExtractor, Document, WorkerResult

logger = logging.getLogger(__name__)


class WikipediaExtractor(BaseExtractor):
    """Extract content from Wikipedia with link crawling support."""
    
    BASE_URL = "https://en.wikipedia.org"
    API_URL = f"{BASE_URL}/w/api.php"
    
    def __init__(self):
        super().__init__("wikipedia")
        self.visited_urls: Set[str] = set()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def extract(self, config: Dict[str, Any]) -> List[Document]:
        """
        Extract documents from Wikipedia.
        
        Config structure:
        {
            "topics": ["Machine Learning", "Neural Networks"],
            "crawl_links": True,
            "max_depth": 2,
            "max_articles": 50,
            "include_references": True,
            "include_tables": True,
            "language": "en"
        }
        """
        topics = config.get("topics", [])
        crawl_links = config.get("crawl_links", True)
        max_depth = config.get("max_depth", 2)
        max_articles = config.get("max_articles", 50)
        include_references = config.get("include_references", True)
        include_tables = config.get("include_tables", True)
        
        all_documents = []
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for topic in topics:
                try:
                    self.logger.info(f"Extracting Wikipedia topic: {topic}")
                    
                    # Get initial article
                    article_docs = await self._extract_article(
                        client, 
                        topic,
                        include_references,
                        include_tables
                    )
                    
                    if article_docs:
                        all_documents.extend(article_docs)
                        
                        # Crawl linked articles if enabled
                        if crawl_links and len(all_documents) < max_articles:
                            linked_docs = await self._crawl_linked_articles(
                                client,
                                article_docs[0],  # Main article
                                max_depth,
                                max_articles - len(all_documents),
                                include_references,
                                include_tables
                            )
                            all_documents.extend(linked_docs)
                    
                    self.logger.info(f"Extracted {len(all_documents)} documents for {topic}")
                    
                except Exception as e:
                    self.logger.error(f"Error extracting topic {topic}: {e}", exc_info=True)
        
        return all_documents[:max_articles]
    
    async def _extract_article(
        self,
        client: httpx.AsyncClient,
        title: str,
        include_references: bool,
        include_tables: bool
    ) -> List[Document]:
        """Extract a single Wikipedia article."""
        try:
            # Get article content via API
            params = {
                "action": "parse",
                "page": title,
                "format": "json",
                "prop": "text|sections|displaytitle|categories|links",
                "redirects": 1
            }
            
            response = await client.get(self.API_URL, params=params)
            
            if response.status_code != 200:
                self.logger.error(f"API error for {title}: {response.status_code}")
                return []
            
            data = response.json()
            
            if "error" in data:
                self.logger.error(f"Article not found: {title}")
                return []
            
            parse_data = data.get("parse", {})
            
            # Extract content
            html_content = parse_data.get("text", {}).get("*", "")
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'sup', 'table']):
                if element.name == 'table' and include_tables:
                    continue
                element.decompose()
            
            # Extract main text
            content = self._html_to_markdown(soup)
            
            # Extract metadata
            categories = [c for c in parse_data.get("categories", [])]
            sections = parse_data.get("sections", [])
            links = parse_data.get("links", [])
            
            # Create document
            page_url = f"{self.BASE_URL}/wiki/{title.replace(' ', '_')}"
            
            doc = Document(
                doc_id=self._generate_doc_id(title),
                source="wikipedia",
                source_type="article",
                title=parse_data.get("displaytitle", title),
                content=content,
                raw_content=html_content,
                metadata={
                    "url": page_url,
                    "categories": [c.get("*") for c in categories],
                    "sections": [s.get("line") for s in sections],
                    "num_links": len(links),
                    "language": "en",
                    "extracted_at": datetime.utcnow().isoformat(),
                },
                url=page_url,
                tags=[c.get("*") for c in categories[:5]],  # First 5 categories as tags
            )
            
            documents = [doc]
            
            # Extract references if requested
            if include_references:
                ref_doc = self._extract_references(soup, title, page_url)
                if ref_doc:
                    documents.append(ref_doc)
            
            return documents
            
        except Exception as e:
            self.logger.error(f"Error extracting article {title}: {e}")
            return []
    
    async def _crawl_linked_articles(
        self,
        client: httpx.AsyncClient,
        root_doc: Document,
        max_depth: int,
        max_articles: int,
        include_references: bool,
        include_tables: bool
    ) -> List[Document]:
        """Crawl linked articles up to specified depth."""
        if max_depth <= 0 or max_articles <= 0:
            return []
        
        documents = []
        to_visit = [(root_doc.metadata.get("url"), 1)]  # (url, depth)
        self.visited_urls.add(root_doc.metadata.get("url"))
        
        while to_visit and len(documents) < max_articles:
            url, depth = to_visit.pop(0)
            
            if depth > max_depth:
                continue
            
            # Extract article title from URL
            title = url.split("/wiki/")[-1].replace("_", " ")
            
            # Skip special pages
            if any(prefix in title for prefix in ["File:", "Template:", "Category:", "Help:", "Wikipedia:"]):
                continue
            
            # Extract article
            article_docs = await self._extract_article(
                client,
                title,
                include_references,
                include_tables
            )
            
            if article_docs:
                documents.extend(article_docs)
                
                # Add linked articles to queue
                if depth < max_depth:
                    links = self._extract_internal_links(article_docs[0])
                    for link in links[:10]:  # Max 10 links per article
                        if link not in self.visited_urls:
                            to_visit.append((link, depth + 1))
                            self.visited_urls.add(link)
        
        return documents[:max_articles]
    
    def _extract_internal_links(self, doc: Document) -> List[str]:
        """Extract internal Wikipedia links from document."""
        links = []
        
        # Extract from content
        link_pattern = r'\[([^\]]+)\]\((/wiki/[^)]+)\)'
        matches = re.findall(link_pattern, doc.content)
        
        for text, path in matches:
            full_url = urljoin(self.BASE_URL, path)
            if "/wiki/" in full_url and "#" not in full_url:
                links.append(full_url)
        
        return links
    
    def _extract_references(
        self,
        soup: BeautifulSoup,
        title: str,
        page_url: str
    ) -> Optional[Document]:
        """Extract references section."""
        try:
            # Find references section
            ref_section = soup.find('ol', class_='references')
            if not ref_section:
                return None
            
            references = []
            for li in ref_section.find_all('li'):
                ref_text = li.get_text(strip=True)
                if ref_text:
                    references.append(ref_text)
            
            if not references:
                return None
            
            content = f"# References for {title}\n\n"
            for i, ref in enumerate(references, 1):
                content += f"{i}. {ref}\n"
            
            doc = Document(
                doc_id=self._generate_doc_id(f"{title}-references"),
                source="wikipedia",
                source_type="references",
                title=f"References: {title}",
                content=content,
                raw_content=str(ref_section),
                metadata={
                    "parent_article": title,
                    "parent_url": page_url,
                    "num_references": len(references),
                },
                url=page_url + "#References",
            )
            
            return doc
            
        except Exception as e:
            self.logger.error(f"Error extracting references: {e}")
            return None
    
    def _html_to_markdown(self, soup: BeautifulSoup) -> str:
        """Convert Wikipedia HTML to markdown."""
        content_parts = []
        
        # Process paragraphs and headings
        for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'ul', 'ol']):
            if element.name.startswith('h'):
                level = int(element.name[1])
                text = element.get_text(strip=True)
                content_parts.append(f"\n{'#' * level} {text}\n")
            
            elif element.name == 'p':
                text = element.get_text(strip=True)
                if text:
                    # Convert links
                    for a in element.find_all('a'):
                        href = a.get('href', '')
                        if href.startswith('/wiki/'):
                            text = text.replace(
                                a.get_text(),
                                f"[{a.get_text()}]({self.BASE_URL}{href})"
                            )
                    content_parts.append(f"\n{text}\n")
            
            elif element.name in ['ul', 'ol']:
                for li in element.find_all('li', recursive=False):
                    text = li.get_text(strip=True)
                    if text:
                        content_parts.append(f"- {text}")
        
        return "\n".join(content_parts)
    
    def _generate_doc_id(self, title: str) -> str:
        """Generate unique document ID."""
        unique_string = f"wikipedia:{title}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:16]


# Celery task
@app.task(name="extract_wikipedia", bind=True)
def extract_wikipedia_task(self, config: Dict[str, Any]) -> Dict[str, Any]:
    """Celery task for Wikipedia extraction."""
    import asyncio
    
    extractor = WikipediaExtractor()
    
    # Run async extraction
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(extractor.process(config))
    
    return result.dict()

