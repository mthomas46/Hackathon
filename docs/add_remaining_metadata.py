#!/usr/bin/env python3
"""
Add LLM metadata to all remaining documents that don't have it.
"""

import os
import yaml
import re
from pathlib import Path
from datetime import datetime

def get_document_type_from_path(file_path):
    """Determine document type based on file path and subdirectory."""
    path_parts = Path(file_path).parts

    # Map subdirectories to document types
    type_mapping = {
        'achievements': 'report',
        'analysis': 'report',
        'architecture': 'architecture',
        'audit': 'audit',
        'business': 'planning',
        'ci-cd': 'guide',
        'cli': 'guide',
        'config': 'reference',
        'consolidation': 'report',
        'deployment': 'guide',
        'development': 'guide',
        'docker': 'guide',
        'ecosystem': 'architecture',
        'examples': 'guide',
        'guides': 'guide',
        'implementation': 'guide',
        'infrastructure': 'guide',
        'integrations': 'guide',
        'living-docs': 'reference',
        'mcp-system-plan': 'planning',
        'migration': 'guide',
        'operations': 'guide',
        'project-simulation': 'planning',
        'reference': 'reference',
        'reports': 'report',
        'roadmap': 'planning',
        'security': 'guide',
        'service-standardization': 'guide',
        'workflow': 'guide'
    }

    for part in path_parts:
        if part in type_mapping:
            return type_mapping[part]

    return 'reference'

def get_content_focus_from_path(file_path):
    """Determine content focus based on file path."""
    filename = Path(file_path).name.lower()
    subdir = str(Path(file_path).parent.name).lower()

    if any(word in filename for word in ['architecture', 'design', 'system']):
        return 'technical'
    elif any(word in filename for word in ['plan', 'roadmap', 'strategy', 'business']):
        return 'strategic'
    elif any(word in filename for word in ['deployment', 'setup', 'guide', 'tutorial']):
        return 'operational'
    elif any(word in filename for word in ['analysis', 'report', 'audit']):
        return 'analytical'
    elif 'readme' in filename:
        return 'operational'
    else:
        return 'technical'

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
        '5_tier_system': ['5-tier', 'five tier'],
        'ci_cd': ['ci/cd', 'continuous integration', 'continuous deployment'],
        'testing': ['testing', 'test suite', 'unit test'],
        'deployment': ['deployment', 'production'],
        'security': ['security', 'authentication', 'authorization'],
        'monitoring': ['monitoring', 'observability', 'logging'],
        'documentation': ['documentation', 'docs', 'readme']
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

    # Extract creation date from content or filename
    created_date = "2024-09-01"  # Default fallback

    # Try to extract date from content
    date_patterns = [
        r'(\d{4}-\d{2}-\d{2})',
        r'(\d{4}/\d{2}/\d{2})',
        r'Date:\s*(\d{4}-\d{2}-\d{2})',
        r'Created:\s*(\d{4}-\d{2}-\d{2})'
    ]

    for pattern in date_patterns:
        match = re.search(pattern, content)
        if match:
            created_date = match.group(1)
            break

    # Check if it mentions 2025
    if '2025' in content:
        created_date = "2025-10-01"

    metadata = {
        'llm_metadata': {
            'document_type': doc_type,
            'content_focus': content_focus,
            'platform': {
                'primary': platform,
                'secondary': []
            },
            'status': 'active',
            'created_date': created_date,
            'last_modified': datetime.now().strftime('%Y-%m-%d'),
            'topics': topics,
            'concepts': [],  # Will be filled based on content
            'technologies': [],  # Will be filled based on content
            'services_mentioned': [],  # Will be filled based on content
            'semantic_summary': f"{doc_type.title()} document about {content_focus} aspects of the {platform.replace('_', ' ')} platform",
            'archive_reason': 'n/a',
            'historical_value': 'current',
            'reference_value': 'high' if doc_type in ['guide', 'reference'] else 'medium'
        },
        'semantic_embedding': {
            'model': 'text-embedding-ada-002',
            'embedding_date': datetime.now().strftime('%Y-%m-%d'),
            'embedding_checksum': 'pending'
        },
        'rag_metadata': {
            'chunk_strategy': 'semantic',
            'optimal_chunk_size': 512,
            'retrieval_priority': 'high' if doc_type in ['guide', 'reference'] else 'medium'
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
            return False

        # Get title from first heading
        lines = content.split('\n')
        title = "Document Title"
        for line in lines[:10]:
            if line.startswith('# '):
                title = line[2:].strip()
                break

        # Create metadata
        metadata = create_llm_metadata(file_path, content)
        metadata_yaml = yaml.dump(metadata, default_flow_style=False, sort_keys=False, allow_unicode=True)

        # Create new content with metadata
        new_content = f"---\n{metadata_yaml}---\n\n{content}"

        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return True

    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return False

def main():
    """Add metadata to all markdown files outside archive."""
    docs_root = Path('/Users/mykalthomas/Documents/work/Hackathon/docs')

    if not docs_root.exists():
        print(f"Docs directory not found: {docs_root}")
        return

    print("🔍 Adding LLM metadata to active documentation...")

    md_files = []
    for md_file in docs_root.rglob('*.md'):
        # Skip archive directory and special files
        if 'archive' in str(md_file):
            continue
        md_files.append(md_file)

    total_files = len(md_files)
    processed = 0
    added = 0

    print(f"Found {total_files} active markdown files")

    for md_file in md_files:
        if add_metadata_to_file(md_file):
            added += 1
            print(f"✓ Added metadata to {md_file.relative_to(docs_root)}")
        processed += 1

        if processed % 25 == 0:
            print(f"Progress: {processed}/{total_files} files processed")

    print("\n📊 Metadata Addition Complete:")
    print(f"Total files processed: {processed}")
    print(f"Metadata added to: {added} files")
    print(f"Already had metadata: {processed - added} files")

if __name__ == '__main__':
    main()
