#!/usr/bin/env python3
"""
Documentation Organization Script

Analyzes and organizes markdown files across services.
Adds metadata and creates cross-references.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

CATEGORIES = {
    'architecture': ['architecture', 'design', 'system', 'component', 'overview'],
    'api': ['api', 'endpoint', 'specification', 'model', 'schema'],
    'guides': ['guide', 'quick', 'start', 'deployment', 'configuration', 'setup'],
    'features': ['feature', 'rag', 'caching', 'ingestion', 'worker', 'temporal', 'tree'],
    'development': ['test', 'debug', 'contributing', 'development', 'code'],
    'planning': ['plan', 'implementation', 'phase', 'spec', 'execution'],
    'history': ['milestone', 'session', 'summary', 'complete', 'status', 'final'],
}

def categorize_file(filepath: Path) -> str:
    """Analyze file and determine category."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = ''.join(f.readlines()[:50]).lower()
    except:
        return 'archive'
    
    # Score each category
    scores = {}
    for category, keywords in CATEGORIES.items():
        score = sum(content.count(kw) for kw in keywords)
        scores[category] = score
    
    # Special cases
    if 'audit' in filepath.name.lower():
        return 'history'
    if 'checkpoint' in str(filepath):
        return 'history'
    if 'generated' in str(filepath):
        return 'generated'
    
    # Return highest scoring category
    max_score = max(scores.values()) if scores else 0
    if max_score > 0:
        return max(scores, key=scores.get)
    
    return 'archive'

def organize_files(service_dir: Path, dry_run=False):
    """Organize all .md files in a service directory."""
    # Find all .md files in root
    md_files = [f for f in service_dir.glob('*.md') if f.is_file()]
    
    print(f"\n{'='*80}")
    print(f"Organizing: {service_dir.name}")
    print(f"{'='*80}")
    print(f"Found {len(md_files)} .md files in root\n")
    
    moves = []
    
    for filepath in md_files:
        # Skip README
        if filepath.name == 'README.md':
            print(f"⏭️  Skipping: {filepath.name} (keeping in root)")
            continue
        
        # Categorize
        category = categorize_file(filepath)
        
        # Determine destination
        if category == 'generated':
            dest_dir = service_dir / 'docs' / 'generated'
        elif category in ['planning', 'history', 'archive']:
            dest_dir = service_dir / category
        else:
            dest_dir = service_dir / 'docs' / category
        
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / filepath.name
        
        # Track move
        moves.append((filepath, dest, category))
        
        if dry_run:
            print(f"📋 Would move: {filepath.name} → {category}/")
        else:
            # Check if destination exists
            if dest.exists():
                print(f"⚠️  Skipping: {filepath.name} (already exists in {category}/)")
            else:
                filepath.rename(dest)
                print(f"✅ Moved: {filepath.name} → {category}/")
    
    print(f"\n📊 Summary for {service_dir.name}:")
    print(f"   Total files: {len(md_files)}")
    print(f"   Moved: {len([m for m in moves if not dry_run])}")
    print(f"   Skipped: {len(md_files) - len(moves)}")
    
    return moves

def main():
    """Main execution."""
    base = Path('services')
    
    services = [
        base / 'ecosystem-mcp',
        base / 'ecosystem-mcp-dashboard',
        base / 'ecosystem-mcp-embedding',
    ]
    
    print("🚀 Documentation Organization Script")
    print("=" * 80)
    
    total_moved = 0
    
    for service_dir in services:
        if service_dir.exists():
            moves = organize_files(service_dir, dry_run=False)
            total_moved += len(moves)
        else:
            print(f"⚠️  Service not found: {service_dir}")
    
    print(f"\n{'='*80}")
    print(f"✅ Organization Complete!")
    print(f"📊 Total files organized: {total_moved}")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    main()
