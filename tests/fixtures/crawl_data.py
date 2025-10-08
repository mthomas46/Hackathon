"""
Crawl data fixtures for testing Wikipedia/Fandom crawlers.
"""
from typing import Dict, Any, List
from datetime import datetime
from ingestion.models import CrawlReport
from ingestion.tagging.tag_collection import TagCollection, TagType


def create_mock_crawl_report(
    total_pages: int = 10,
    duration_seconds: float = 45.2,
    max_depth: int = 2
) -> CrawlReport:
    """
    Create a mock crawl report.
    
    Args:
        total_pages: Number of pages crawled
        duration_seconds: Crawl duration
        max_depth: Maximum depth reached
    
    Returns:
        CrawlReport instance
    """
    depth_distribution = {i: total_pages // (max_depth + 1) for i in range(max_depth + 1)}
    
    # Note: CrawlReport fields may vary - adjust as needed
    return {
        'total_pages': total_pages,
        'duration_seconds': duration_seconds,
        'crawl_graph': {
            "page-0": {"depth": 0, "links_found": 5, "links_followed": 3},
            "page-1": {"depth": 1, "links_found": 8, "links_followed": 2},
            "page-2": {"depth": 1, "links_found": 6, "links_followed": 1},
        },
        'depth_distribution': depth_distribution,
        'link_statistics': {
            "total_links_found": 50,
            "total_links_followed": 15,
            "duplicate_links": 10,
            "filtered_links": 25
        }
    }


def create_mock_tag_collection(
    default_tags: List[str] = None,
    contextual_tags: List[str] = None,
    user_tags: List[str] = None
) -> TagCollection:
    """
    Create a mock tag collection.
    
    Args:
        default_tags: Default tags
        contextual_tags: Contextual (NLP-derived) tags
        user_tags: User-defined tags
    
    Returns:
        TagCollection instance
    """
    collection = TagCollection.empty()
    
    collection.default_tags = set(default_tags or [
        "source:wikipedia",
        "file_type:document",
        "has_references"
    ])
    
    collection.contextual_tags = set(contextual_tags or [
        "character:protagonist",
        "location:city",
        "event:battle",
        "topic:history"
    ])
    
    collection.user_defined_tags = user_tags or [
        "domain:test",
        "project:demo"
    ]
    
    return collection


# Sample crawl reports for different scenarios
SAMPLE_CRAWL_REPORTS = {
    'small': create_mock_crawl_report(total_pages=5, duration_seconds=15.3, max_depth=1),
    'medium': create_mock_crawl_report(total_pages=25, duration_seconds=78.5, max_depth=2),
    'large': create_mock_crawl_report(total_pages=100, duration_seconds=320.1, max_depth=3),
}


def create_mock_crawl_graph(pages: int = 10) -> Dict[str, Dict[str, Any]]:
    """
    Create a mock crawl graph.
    
    Args:
        pages: Number of pages in graph
    
    Returns:
        Dictionary representing crawl graph
    """
    graph = {}
    
    for i in range(pages):
        depth = i // 3  # Distribute across depths
        graph[f"page-{i}"] = {
            "url": f"https://example.com/wiki/Page_{i}",
            "title": f"Page {i}",
            "depth": depth,
            "parent": f"page-{max(0, i-3)}" if i > 0 else None,
            "links_found": 5 + (i % 3),
            "links_followed": 2 + (i % 2),
            "crawled_at": datetime.now().isoformat()
        }
    
    return graph


def create_horus_heresy_sample_data() -> Dict[str, Any]:
    """Create sample data for Horus Heresy use case."""
    return {
        'documents': [
            {
                'title': 'Horus Heresy',
                'content': 'The Horus Heresy was a galaxy-spanning civil war...',
                'tags': ['character:horus', 'character:emperor', 'faction:space-marines', 'event:heresy']
            },
            {
                'title': 'Siege of Terra',
                'content': 'The Siege of Terra was the final battle...',
                'tags': ['location:terra', 'event:siege', 'faction:loyalists']
            },
            {
                'title': 'Primarchs',
                'content': 'The Primarchs were the twenty genetically-enhanced sons...',
                'tags': ['character:primarchs', 'character:emperor', 'topic:genetics']
            }
        ],
        'entities': {
            'PERSON': [('horus', 12), ('emperor', 10), ('primarchs', 8)],
            'ORGANIZATION': [('space marines', 15), ('chaos', 8)],
            'LOCATION': [('terra', 10), ('holy terra', 6)],
            'EVENT': [('horus heresy', 20), ('siege of terra', 12), ('great crusade', 8)]
        },
        'relationships': [
            ('horus', 'emperor', 10),
            ('space marines', 'emperor', 9),
            ('siege of terra', 'terra', 12),
            ('horus', 'chaos', 7)
        ]
    }

