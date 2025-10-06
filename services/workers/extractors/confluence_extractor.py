"""Confluence Extractor Worker - Extract pages and attachments."""

import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from atlassian import Confluence
from tenacity import retry, stop_after_attempt, wait_exponential

from services.workers.celery_app import app
from services.workers.shared.base_worker import BaseExtractor, Document, WorkerResult

logger = logging.getLogger(__name__)


class ConfluenceExtractor(BaseExtractor):
    """Extract data from Confluence spaces."""
    
    def __init__(self, url: str, username: str, api_token: str):
        super().__init__("confluence")
        self.client = Confluence(
            url=url,
            username=username,
            password=api_token,
            cloud=True
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def extract(self, config: Dict[str, Any]) -> List[Document]:
        """
        Extract documents from Confluence.
        
        Config structure:
        {
            "spaces": ["SPACE1", "SPACE2"],
            "include_attachments": False,
            "max_pages_per_space": 100,
            "labels": ["documentation", "api"]  # Optional filter
        }
        """
        spaces = config.get("spaces", [])
        include_attachments = config.get("include_attachments", False)
        max_pages = config.get("max_pages_per_space", 100)
        label_filter = config.get("labels", [])
        
        all_documents = []
        
        for space_key in spaces:
            try:
                self.logger.info(f"Extracting from Confluence space: {space_key}")
                
                # Get all pages in space
                pages = self._get_pages_in_space(space_key, max_pages, label_filter)
                
                for page in pages:
                    # Extract page content
                    doc = await self._extract_page(page)
                    if doc:
                        all_documents.append(doc)
                    
                    # Extract attachments if requested
                    if include_attachments:
                        attachment_docs = await self._extract_attachments(page)
                        all_documents.extend(attachment_docs)
                
                self.logger.info(f"Extracted {len(all_documents)} documents from {space_key}")
            
            except Exception as e:
                self.logger.error(f"Error extracting space {space_key}: {e}", exc_info=True)
        
        return all_documents
    
    def _get_pages_in_space(
        self, 
        space_key: str,
        max_pages: int,
        labels: List[str]
    ) -> List[Dict]:
        """Get all pages in a space."""
        pages = []
        start = 0
        limit = 50
        
        while len(pages) < max_pages:
            try:
                # Get batch of pages
                results = self.client.get_all_pages_from_space(
                    space=space_key,
                    start=start,
                    limit=limit,
                    expand="body.storage,version,metadata.labels"
                )
                
                if not results:
                    break
                
                # Filter by labels if specified
                if labels:
                    filtered = [
                        p for p in results
                        if any(
                            label.get("name") in labels
                            for label in p.get("metadata", {}).get("labels", {}).get("results", [])
                        )
                    ]
                    pages.extend(filtered)
                else:
                    pages.extend(results)
                
                if len(results) < limit:
                    break
                
                start += limit
            
            except Exception as e:
                self.logger.error(f"Error fetching pages: {e}")
                break
        
        return pages[:max_pages]
    
    async def _extract_page(self, page: Dict) -> Optional[Document]:
        """Extract single Confluence page."""
        try:
            page_id = page["id"]
            title = page["title"]
            
            # Get page content (HTML)
            body = page.get("body", {}).get("storage", {}).get("value", "")
            
            # Get metadata
            version = page.get("version", {})
            created_date = page.get("history", {}).get("createdDate")
            modified_date = version.get("when")
            author = version.get("by", {}).get("displayName")
            
            # Get labels
            labels = [
                label.get("name", "")
                for label in page.get("metadata", {}).get("labels", {}).get("results", [])
            ]
            
            # Build URL
            base_url = self.client.url
            page_url = f"{base_url}/pages/viewpage.action?pageId={page_id}"
            
            doc = Document(
                doc_id=self._generate_doc_id(f"page-{page_id}"),
                source="confluence",
                source_type="page",
                title=title,
                content=body,  # HTML content
                raw_content=body,
                metadata={
                    "page_id": page_id,
                    "space": page.get("space", {}).get("key"),
                    "version": version.get("number"),
                },
                created_at=self._parse_date(created_date),
                updated_at=self._parse_date(modified_date),
                author=author,
                url=page_url,
                tags=labels,
            )
            
            return doc
        
        except Exception as e:
            self.logger.error(f"Error extracting page: {e}")
            return None
    
    async def _extract_attachments(self, page: Dict) -> List[Document]:
        """Extract attachments from a page."""
        docs = []
        
        try:
            page_id = page["id"]
            attachments = self.client.get_attachments_from_content(page_id)
            
            for attachment in attachments.get("results", []):
                # Only extract text-based attachments
                if not self._is_text_attachment(attachment):
                    continue
                
                doc = await self._extract_attachment(attachment, page)
                if doc:
                    docs.append(doc)
        
        except Exception as e:
            self.logger.error(f"Error extracting attachments: {e}")
        
        return docs
    
    async def _extract_attachment(
        self,
        attachment: Dict,
        page: Dict
    ) -> Optional[Document]:
        """Extract single attachment."""
        try:
            attachment_id = attachment["id"]
            title = attachment["title"]
            
            # Download attachment content (for text files)
            # Note: This is simplified - production would need binary handling
            content = f"Attachment: {title}"
            
            doc = Document(
                doc_id=self._generate_doc_id(f"attachment-{attachment_id}"),
                source="confluence",
                source_type="attachment",
                title=title,
                content=content,
                raw_content=content,
                metadata={
                    "attachment_id": attachment_id,
                    "page_id": page["id"],
                    "page_title": page["title"],
                    "media_type": attachment.get("mediaType"),
                },
                url=attachment.get("_links", {}).get("download"),
            )
            
            return doc
        
        except Exception as e:
            self.logger.error(f"Error extracting attachment: {e}")
            return None
    
    def _is_text_attachment(self, attachment: Dict) -> bool:
        """Check if attachment is text-based."""
        media_type = attachment.get("mediaType", "")
        text_types = ["text/", "application/json", "application/xml"]
        return any(media_type.startswith(t) for t in text_types)
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse Confluence date string."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except:
            return None
    
    def _generate_doc_id(self, item: str) -> str:
        """Generate unique document ID."""
        unique_string = f"confluence:{item}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:16]


# Celery task
@app.task(name="extract_confluence", bind=True)
def extract_confluence_task(self, config: Dict[str, Any]) -> Dict[str, Any]:
    """Celery task for Confluence extraction."""
    import asyncio
    
    url = config.get("url")
    username = config.get("username")
    api_token = config.get("api_token")
    
    if not all([url, username, api_token]):
        return {
            "success": False,
            "error": "Missing required Confluence credentials"
        }
    
    extractor = ConfluenceExtractor(url=url, username=username, api_token=api_token)
    
    # Run async extraction
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(extractor.process(config))
    
    return result.dict()

