"""
Test fixtures for the MCP ecosystem.

This module provides reusable test fixtures for:
- Mock documents (various sources and formats)
- Mock entities and tags
- Mock API responses
- Mock crawl data
"""

from .documents import *
from .entities import *
from .api_responses import *
from .crawl_data import *

__all__ = [
    # Documents
    'create_mock_document',
    'create_github_commit_doc',
    'create_jira_ticket_doc',
    'create_wikipedia_doc',
    'create_confluence_doc',
    'create_code_file_doc',
    'SAMPLE_DOCUMENTS',
    
    # Entities
    'create_mock_entity',
    'create_mock_relationship',
    'SAMPLE_ENTITIES',
    'SAMPLE_RELATIONSHIPS',
    
    # API Responses
    'mock_mcp_provisioning_response',
    'mock_training_job_response',
    'mock_query_response',
    'mock_ingestion_response',
    
    # Crawl Data
    'create_mock_crawl_report',
    'create_mock_tag_collection',
    'SAMPLE_CRAWL_REPORTS',
]

