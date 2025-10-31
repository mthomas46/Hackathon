#!/usr/bin/env python3
"""
Documentation Enrichment Script

Systematically adds YAML frontmatter, semantic tags, and cross-references
to all documentation files for optimal LLM agent processing.

Usage:
    python enrich_documentation.py

Features:
- Detects missing YAML frontmatter
- Adds semantic tags based on content
- Creates cross-references
- Maintains existing content
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from datetime import datetime

# Category-based tag mappings
CATEGORY_TAGS = {
    "api": ["api", "endpoints", "routes", "rest", "http", "interface"],
    "architecture": ["architecture", "design", "system", "components", "structure"],
    "development": ["development", "testing", "debugging", "validation", "quality"],
    "features": ["features", "capabilities", "functionality", "implementation"],
    "guides": ["guide", "howto", "tutorial", "documentation", "instructions"],
    "reference": ["reference", "specification", "documentation"],
}

# Keyword-based tag detection
KEYWORD_TAGS = {
    "rag": ["rag", "retrieval", "generation", "query", "llm"],
    "ingestion": ["ingestion", "pipeline", "processing", "import"],
    "temporal": ["temporal", "timeline", "versioning", "history", "evolution"],
    "database": ["database", "postgresql", "sql", "schema", "tables"],
    "cache": ["cache", "caching", "redis", "performance"],
    "ollama": ["ollama", "llm", "model", "ai"],
    "worker": ["worker", "background", "queue", "job"],
    "monitoring": ["monitoring", "health", "metrics", "observability"],
    "deployment": ["deployment", "docker", "container", "production"],
    "configuration": ["configuration", "config", "settings", "registry"],
    "testing": ["testing", "test", "validation", "verification"],
    "performance": ["performance", "optimization", "speed", "efficiency"],
    "circuit-breaker": ["circuit", "breaker", "resilience", "fallback"],
}


def has_yaml_frontmatter(content: str) -> bool:
    """Check if document already has YAML frontmatter."""
    return content.strip().startswith("---\n") and "\n---" in content[4:]


def extract_title_from_content(content: str) -> str:
    """Extract title from markdown content."""
    # Try to find first H1
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    
    # Fallback to filename
    return "Untitled Document"


def detect_tags_from_content(content: str, category: str, filename: str) -> List[str]:
    """Detect appropriate tags based on content analysis."""
    tags = set()
    
    # Add category tags
    if category in CATEGORY_TAGS:
        tags.update(CATEGORY_TAGS[category][:3])  # Top 3 category tags
    
    # Detect keyword-based tags
    content_lower = content.lower()
    for keyword, tag_list in KEYWORD_TAGS.items():
        if keyword in content_lower or keyword in filename.lower():
            tags.update(tag_list[:2])  # Top 2 tags per keyword
    
    # Limit to 10 tags for readability
    return sorted(list(tags))[:10]


def detect_related_docs(filename: str, category: str, all_files: Set[str]) -> List[str]:
    """Detect related documents based on naming and category."""
    related = []
    
    # Add core docs
    core_docs = [
        "INDEX.md",
        "architecture/OVERVIEW.md",
        "CODE_REFERENCE.md",
        "API_ENDPOINTS_COMPLETE.md",
    ]
    
    for doc in core_docs:
        if doc != filename and doc in all_files:
            related.append(doc)
    
    # Limit to 5 related docs
    return related[:5]


def generate_frontmatter(
    title: str,
    category: str,
    tags: List[str],
    related: List[str],
    filename: str,
) -> str:
    """Generate YAML frontmatter for a document."""
    # Determine audience and difficulty
    audience = "developer"
    if "guide" in category or "guides" in filename.lower():
        audience = "user"
    elif "reference" in category or "api" in category:
        audience = "developer"
    
    difficulty = "intermediate"
    if "quick" in filename.lower() or "guide" in filename.lower():
        difficulty = "beginner"
    elif "architecture" in category or "development" in category:
        difficulty = "advanced"
    
    # Build semantic keywords from tags
    semantic_keywords = [tag.replace("-", " ") for tag in tags[:5]]
    
    # Build search hints
    search_hints = [
        f"what is {title.lower()}",
        f"how does {title.lower()} work",
        f"guide to {title.lower()}",
    ][:3]
    
    frontmatter = f"""---
title: "{title}"
service: "ecosystem-mcp"
category: "{category}"
tags: {tags}
related: {related}
status: "current"
last_updated: "{datetime.now().strftime('%Y-%m-%d')}"
audience: "{audience}"
difficulty: "{difficulty}"
semantic_keywords: {semantic_keywords}
llm_search_hints: {search_hints}
---

"""
    return frontmatter


def process_file(filepath: Path, category: str, all_files: Set[str]) -> Tuple[bool, str]:
    """
    Process a single documentation file.
    
    Returns:
        (modified: bool, status: str)
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Skip if already has frontmatter
        if has_yaml_frontmatter(content):
            return False, "Already has frontmatter"
        
        # Extract metadata
        title = extract_title_from_content(content)
        filename = str(filepath.relative_to(filepath.parents[1]))
        tags = detect_tags_from_content(content, category, filename)
        related = detect_related_docs(filename, category, all_files)
        
        # Generate and prepend frontmatter
        frontmatter = generate_frontmatter(title, category, tags, related, filename)
        enriched_content = frontmatter + content
        
        # Write back
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(enriched_content)
        
        return True, f"Added frontmatter ({len(tags)} tags, {len(related)} related)"
    
    except Exception as e:
        return False, f"Error: {str(e)}"


def main():
    """Main execution function."""
    print("=" * 80)
    print("Documentation Enrichment Script")
    print("=" * 80)
    print()
    
    # Get docs directory
    docs_dir = Path(__file__).parent
    
    # Find all markdown files
    all_files = set()
    for md_file in docs_dir.rglob("*.md"):
        if md_file.name != "enrich_documentation.py":
            rel_path = md_file.relative_to(docs_dir)
            all_files.add(str(rel_path))
    
    print(f"Found {len(all_files)} markdown files")
    print()
    
    # Process by category
    categories = [
        (".", "reference"),
        ("api", "api"),
        ("architecture", "architecture"),
        ("development", "development"),
        ("features", "features"),
        ("guides", "guides"),
    ]
    
    total_processed = 0
    total_modified = 0
    
    for subdir, category in categories:
        category_dir = docs_dir / subdir
        if not category_dir.exists():
            continue
        
        md_files = list(category_dir.glob("*.md"))
        if not md_files:
            continue
        
        print(f"\nProcessing {category}/ ({len(md_files)} files)")
        print("-" * 80)
        
        for md_file in sorted(md_files):
            modified, status = process_file(md_file, category, all_files)
            
            total_processed += 1
            if modified:
                total_modified += 1
                print(f"✅ {md_file.name}: {status}")
            else:
                print(f"⏭️  {md_file.name}: {status}")
    
    print()
    print("=" * 80)
    print(f"COMPLETE: {total_modified}/{total_processed} files enriched")
    print("=" * 80)


if __name__ == "__main__":
    main()

