#!/usr/bin/env python3
"""
Script to add LLM metadata to archived documents based on their content and location.
"""

import os
import yaml
import re
from datetime import datetime
from pathlib import Path

def get_document_type_from_path(file_path):
    """Determine document type based on file path and subdirectory."""
    path_parts = Path(file_path).parts

    # Map subdirectories to document types
    type_mapping = {
        'architecture': 'architecture',
        'audit-historical': 'audit',
        'audits': 'audit',
        'demo-reports': 'report',
        'deployment-reports': 'report',
        'future-refinements': 'planning',
        'historical-organization': 'reference',
        'implementation-reports': 'report',
        'misc-reports': 'report',
        'operations-historical': 'report',
        'phase-reports': 'report',
        'planning': 'planning',
        'reports': 'report',
        'session-summaries': 'session',
        'validation-reports': 'report',
        'workflow-reports': 'report'
    }

    for part in path_parts:
        if part in type_mapping:
            return type_mapping[part]

    return 'reference'

def get_content_focus_from_path(file_path):
    """Determine content focus based on file path."""
    filename = Path(file_path).name.lower()

    if any(word in filename for word in ['architecture', 'design', 'system', 'ddd', 'microservice']):
        return 'technical'
    elif any(word in filename for word in ['plan', 'roadmap', 'strategy', 'future']):
        return 'strategic'
    elif any(word in filename for word in ['deployment', 'monitoring', 'operation', 'runbook']):
        return 'operational'
    elif any(word in filename for word in ['audit', 'analysis', 'report', 'assessment']):
        return 'analytical'
    else:
        return 'historical'

def get_platform_from_content(content):
    """Determine platform association from content."""
    content_lower = content.lower()

    has_doc_analysis = any(term in content_lower for term in ['document analysis', 'doc analysis', 'analysis platform'])
    has_mcp = any(term in content_lower for term in ['mcp', 'model context protocol', 'context protocol'])

    if has_doc_analysis and has_mcp:
        return 'both'
    elif has_doc_analysis:
        return 'document_analysis'
    elif has_mcp:
        return 'mcp'
    else:
        return 'shared'

def extract_topics_from_content(content):
    """Extract relevant topics from document content."""
    content_lower = content.lower()
    topics = []

    topic_keywords = {
        'microservices': ['microservice', 'micro-services', 'service architecture'],
        'domain_driven_design': ['ddd', 'domain driven', 'bounded context'],
        'clean_architecture': ['clean architecture', 'hexagonal architecture'],
        'cqrs': ['cqrs', 'command query'],
        'event_sourcing': ['event sourcing', 'event-driven'],
        'service_mesh': ['service mesh', 'istio', 'linkerd'],
        'api_gateway': ['api gateway', 'gateway pattern'],
        'bounded_contexts': ['bounded context'],
        'fastapi': ['fastapi'],
        'python': ['python'],
        'redis': ['redis'],
        'postgresql': ['postgresql', 'postgres'],
        'docker': ['docker'],
        'kubernetes': ['kubernetes', 'k8s'],
        'langchain': ['langchain'],
        'langgraph': ['langgraph'],
        'ollama': ['ollama'],
        'llm_orchestration': ['llm orchestration', 'orchestration'],
        'prompt_engineering': ['prompt engineering'],
        'context_management': ['context management'],
        'rag': ['rag', 'retrieval augmented'],
        'embeddings': ['embedding', 'vector'],
        'vector_search': ['vector search'],
        '5_tier_system': ['5-tier', 'five tier']
    }

    for topic, keywords in topic_keywords.items():
        if any(keyword in content_lower for keyword in keywords):
            topics.append(topic)

    return topics[:10]  # Limit to top 10 topics

def create_llm_metadata(file_path, content):
    """Create LLM metadata for a document."""
    doc_type = get_document_type_from_path(file_path)
    content_focus = get_content_focus_from_path(file_path)
    platform = get_platform_from_content(content)
    topics = extract_topics_from_content(content)

    # Extract creation date from filename or use archive date
    filename = Path(file_path).name
    created_date = "2024-09-01"  # Default fallback

    # Try to extract date from filename
    date_match = re.search(r'(\d{4})(\d{2})(\d{2})', filename)
    if date_match:
        created_date = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
    elif '2025' in filename or 'oct' in filename.lower():
        created_date = "2025-10-01"
    elif 'sep' in filename.lower() or '2024' in filename:
        created_date = "2024-09-15"

    metadata = {
        'llm_metadata': {
            'document_type': doc_type,
            'content_focus': content_focus,
            'platform': {
                'primary': platform,
                'secondary': []
            },
            'status': 'archived',
            'created_date': created_date,
            'archived_date': '2025-10-07',
            'topics': topics,
            'concepts': [],  # Will be filled based on content
            'technologies': [],  # Will be filled based on content
            'services_mentioned': [],  # Will be filled based on content
            'semantic_summary': f"{doc_type.title()} document about {content_focus} aspects of the {platform.replace('_', ' ')} platform",
            'archive_reason': 'consolidated',
            'historical_value': 'medium',
            'reference_value': 'medium'
        },
        'semantic_embedding': {
            'model': 'text-embedding-ada-002',
            'embedding_date': '2025-10-07',
            'embedding_checksum': 'pending'
        },
        'rag_metadata': {
            'chunk_strategy': 'semantic',
            'optimal_chunk_size': 512,
            'retrieval_priority': 'medium'
        }
    }

    return metadata

def add_metadata_to_file(file_path):
    """Add LLM metadata to a markdown file if it doesn't already have it."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if already has metadata
        if 'llm_metadata:' in content:
            print(f"✓ {file_path} already has metadata")
            return False

        # Read the content and extract first few lines for title
        lines = content.split('\n')
        title = "Document Title"
        for line in lines[:10]:
            if line.startswith('# '):
                title = line[2:].strip()
                break

        # Create metadata
        metadata = create_llm_metadata(file_path, content)
        metadata_yaml = yaml.dump(metadata, default_flow_style=False, sort_keys=False)

        # Create new content with metadata
        new_content = f"---\n{metadata_yaml}---\n\n{content}"

        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"✓ Added metadata to {file_path}")
        return True

    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return False

def main():
    """Main function to add metadata to all markdown files in archive."""
    archive_dir = Path('/Users/mykalthomas/Documents/work/Hackathon/docs/archive')

    if not archive_dir.exists():
        print(f"Archive directory not found: {archive_dir}")
        return

    print("🔍 Scanning archive for markdown files...")

    md_files = list(archive_dir.rglob('*.md'))
    total_files = len(md_files)
    processed = 0
    added = 0

    print(f"Found {total_files} markdown files")

    for md_file in md_files:
        # Skip our own script and special files
        if 'add_llm_metadata.py' in str(md_file) or 'LLM_TAGGING_SCHEMA.md' in str(md_file):
            continue

        if add_metadata_to_file(md_file):
            added += 1
        processed += 1

        if processed % 50 == 0:
            print(f"Progress: {processed}/{total_files} files processed")

    print("\n📊 Summary:")
    print(f"Total files processed: {processed}")
    print(f"Metadata added to: {added} files")
    print(f"Already had metadata: {processed - added} files")

if __name__ == '__main__':
    main()
