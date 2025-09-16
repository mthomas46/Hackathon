"""Content conversion utilities for transforming Confluence HTML to Markdown."""

import html
import re
import logging
from typing import Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def confluence_to_markdown(confluence_html: str) -> str:
    """Convert Confluence HTML content to markdown.
    
    This is a basic implementation. For production use, consider using
    libraries like markdownify or implementing more sophisticated conversion.
    
    Args:
        confluence_html: Raw Confluence HTML content
        
    Returns:
        Converted markdown content
    """
    if not confluence_html:
        return ""
    
    # Unescape HTML entities
    content = html.unescape(confluence_html)
    
    # Remove confluence-specific macros and elements
    content = re.sub(r'<ac:.*?</ac:.*?>', '', content, flags=re.DOTALL)
    content = re.sub(r'<ri:.*?/>', '', content)
    
    # Convert headings
    content = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1', content, flags=re.DOTALL)
    content = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1', content, flags=re.DOTALL)
    content = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1', content, flags=re.DOTALL)
    content = re.sub(r'<h4[^>]*>(.*?)</h4>', r'#### \1', content, flags=re.DOTALL)
    content = re.sub(r'<h5[^>]*>(.*?)</h5>', r'##### \1', content, flags=re.DOTALL)
    content = re.sub(r'<h6[^>]*>(.*?)</h6>', r'###### \1', content, flags=re.DOTALL)
    
    # Convert paragraphs
    content = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', content, flags=re.DOTALL)
    
    # Convert lists
    content = re.sub(r'<ul[^>]*>', '', content)
    content = re.sub(r'</ul>', '\n', content)
    content = re.sub(r'<ol[^>]*>', '', content)
    content = re.sub(r'</ol>', '\n', content)
    content = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1', content, flags=re.DOTALL)
    
    # Convert emphasis
    content = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', content, flags=re.DOTALL)
    content = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', content, flags=re.DOTALL)
    content = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', content, flags=re.DOTALL)
    content = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', content, flags=re.DOTALL)
    
    # Convert links
    content = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', content, flags=re.DOTALL)
    
    # Convert code blocks and inline code
    content = re.sub(r'<pre[^>]*><code[^>]*>(.*?)</code></pre>', r'```\n\1\n```', content, flags=re.DOTALL)
    content = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', content, flags=re.DOTALL)
    
    # Convert line breaks
    content = re.sub(r'<br[^>]*/?>', '\n', content)
    
    # Convert horizontal rules
    content = re.sub(r'<hr[^>]*/?>', '\n---\n', content)
    
    # Convert blockquotes
    content = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>', r'> \1', content, flags=re.DOTALL)
    
    # Remove remaining HTML tags
    content = re.sub(r'<[^>]+>', '', content)
    
    # Clean up extra whitespace
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    content = re.sub(r'^\s+|\s+$', '', content, flags=re.MULTILINE)
    content = content.strip()
    
    return content


async def process_confluence_page(
    confluence_page: Dict[str, Any], 
    session_id: str, 
    base_url: str
) -> Dict[str, Any]:
    """Process a confluence page and prepare it for storage.
    
    Args:
        confluence_page: Raw Confluence page data from API
        session_id: Session identifier for tracking
        base_url: Confluence base URL for generating full URLs
        
    Returns:
        Processed page data ready for MongoDB storage
    """
    try:
        # Extract content
        content_html = ""
        if confluence_page.get('body', {}).get('storage', {}).get('value'):
            content_html = confluence_page['body']['storage']['value']
        
        # Convert to markdown
        content_markdown = confluence_to_markdown(content_html)
        
        # Parse modification date
        when_str = confluence_page['version']['when']
        # Handle both ISO format with and without 'Z' suffix
        if when_str.endswith('Z'):
            last_modified = datetime.fromisoformat(when_str.replace('Z', '+00:00'))
        else:
            last_modified = datetime.fromisoformat(when_str)
        
        # Prepare metadata
        metadata = {
            "original_url": f"{base_url}{confluence_page['_links']['webui']}",
            "space_key": confluence_page['space']['key'],
            "last_modified": last_modified,
            "author": confluence_page['version']['by']['displayName'],
            "version": confluence_page['version']['number']
        }
        
        # Set parent page ID if available
        if confluence_page.get('ancestors') and len(confluence_page['ancestors']) > 0:
            metadata["parent_page_id"] = confluence_page['ancestors'][-1]['id']
        
        # Prepare file path
        space_key = confluence_page['space']['key']
        page_id = confluence_page['id']
        file_path = f"{space_key}/{page_id}.md"
        
        return {
            "session_id": session_id,
            "confluence_page_id": confluence_page['id'],
            "title": confluence_page['title'],
            "content": content_markdown,
            "metadata": metadata,
            "file_path": file_path,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
    except Exception as e:
        page_title = confluence_page.get('title', 'Unknown')
        page_id = confluence_page.get('id', 'Unknown')
        logger.error(f"Error processing page {page_title} ({page_id}): {str(e)}")
        raise