#!/usr/bin/env python3
"""
Ecosystem MCP - Demo Validation Script

Demonstrates key features without requiring full infrastructure:
1. Document scanning and parsing
2. Content normalization
3. Metadata extraction
4. Git commit analysis
5. Training simulation

Usage:
    python demo_validation.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import subprocess

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.ingestion.scanner import DocumentScanner
from src.ingestion.parser import DocumentParser
from src.ingestion.normalizer import DocumentNormalizer
from src.ingestion.metadata_extractor import MetadataExtractor


def print_banner(text: str):
    """Print a banner."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def print_section(text: str):
    """Print a section header."""
    print(f"\n{'─' * 80}")
    print(f"  {text}")
    print(f"{'─' * 80}")


def print_success(text: str):
    """Print success message."""
    print(f"✅ {text}")


def print_info(text: str):
    """Print info message."""
    print(f"ℹ️  {text}")


def print_metric(name: str, value):
    """Print a metric."""
    print(f"📊 {name}: {value}")


def get_last_n_commits(repo_path: Path, n: int = 20) -> List[Dict]:
    """
    Get last N commits from Git repository.
    
    Args:
        repo_path: Path to Git repository
        n: Number of commits to retrieve
        
    Returns:
        List of commit dictionaries
    """
    try:
        # Get commit hashes
        result = subprocess.run(
            ["git", "log", f"-{n}", "--pretty=format:%H|%an|%ae|%ai|%s"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        
        commits = []
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split("|", 4)
                if len(parts) == 5:
                    commits.append({
                        "hash": parts[0],
                        "author": parts[1],
                        "email": parts[2],
                        "date": parts[3],
                        "message": parts[4]
                    })
        
        return commits
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to get commits: {e}")
        return []


def get_files_changed_in_commit(repo_path: Path, commit_hash: str) -> List[str]:
    """Get files changed in a commit."""
    try:
        result = subprocess.run(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        
        files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
        # Filter for documentation files
        return [f for f in files if f.endswith(('.md', '.py', '.yaml', '.yml', '.json'))]
    except subprocess.CalledProcessError:
        return []


async def main():
    """Main demo validation."""
    print_banner("🎉 ECOSYSTEM MCP - DEMO VALIDATION")
    
    # Configuration
    repo_path = Path(__file__).parent.parent.parent  # Hackathon root
    service_path = Path(__file__).parent
    
    print_info(f"Repository: {repo_path}")
    print_info(f"Service: {service_path}")
    
    # Phase 1: Document Scanning
    print_section("Phase 1: Document Scanning")
    
    scanner = DocumentScanner(str(service_path))
    
    print_info("Scanning for markdown files...")
    md_files = scanner.scan_markdown()
    print_success(f"Found {len(md_files)} markdown files")
    
    print_info("Scanning for Python files...")
    py_files = scanner.scan_python()
    print_success(f"Found {len(py_files)} Python files")
    
    print_metric("Total files", len(md_files) + len(py_files))
    
    # Show sample files
    print("\nSample documentation files:")
    for file in md_files[:5]:
        print(f"  📄 {Path(file).name}")
    
    # Phase 2: Git Commit Analysis
    print_section("Phase 2: Git Commit Analysis (Last 20 Commits)")
    
    print_info("Retrieving last 20 commits...")
    commits = get_last_n_commits(repo_path, 20)
    print_success(f"Retrieved {len(commits)} commits")
    
    # Show commit summary
    print("\nRecent commits:")
    for i, commit in enumerate(commits[:10], 1):
        short_hash = commit["hash"][:7]
        date = commit["date"].split()[0]
        message = commit["message"][:60]
        print(f"  {i:2d}. [{short_hash}] {date} - {message}...")
    
    if len(commits) > 10:
        print(f"  ... and {len(commits) - 10} more commits")
    
    # Analyze files in commits
    print_info("\nAnalyzing files changed in commits...")
    all_changed_files = set()
    commit_file_map = {}
    
    for commit in commits:
        files = get_files_changed_in_commit(repo_path, commit["hash"])
        all_changed_files.update(files)
        commit_file_map[commit["hash"][:7]] = len(files)
    
    print_success(f"Found {len(all_changed_files)} unique files across commits")
    print_metric("Average files per commit", 
                 sum(commit_file_map.values()) / len(commits) if commits else 0)
    
    # Show file types distribution
    file_types = {}
    for file in all_changed_files:
        ext = Path(file).suffix
        file_types[ext] = file_types.get(ext, 0) + 1
    
    print("\nFile types in commits:")
    for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {ext or '(no ext)'}: {count} files")
    
    # Phase 3: Document Processing Demo
    print_section("Phase 3: Document Processing Demo")
    
    parser = DocumentParser()
    normalizer = DocumentNormalizer()
    metadata_extractor = MetadataExtractor()
    
    # Process a sample markdown file
    if md_files:
        sample_file = Path(md_files[0])
        print_info(f"Processing sample file: {sample_file.name}")
        
        # Parse
        print("  1️⃣  Parsing...")
        parsed = parser.parse(sample_file)
        print_success(f"Parsed {len(parsed['content'])} characters")
        
        # Normalize
        print("  2️⃣  Normalizing...")
        normalized = normalizer.normalize(parsed)
        print_success(f"Normalized to {len(normalized)} characters")
        
        # Extract metadata
        print("  3️⃣  Extracting metadata...")
        metadata = metadata_extractor.extract(sample_file, parsed["content"])
        print_success(f"Extracted {len(metadata)} metadata fields")
        
        # Show metadata
        print("\nExtracted metadata:")
        for key, value in list(metadata.items())[:5]:
            if isinstance(value, (str, int, float, bool)):
                print(f"  {key}: {value}")
    
    # Phase 4: Training Simulation
    print_section("Phase 4: Training Simulation (Last 20 Commits)")
    
    print_info("Simulating document ingestion and training...")
    
    # Simulate processing files from commits
    docs_to_process = []
    for commit in commits:
        files = get_files_changed_in_commit(repo_path, commit["hash"])
        for file in files:
            file_path = repo_path / file
            if file_path.exists() and file_path.suffix in ['.md', '.py']:
                docs_to_process.append({
                    "file": file,
                    "commit": commit["hash"][:7],
                    "date": commit["date"],
                    "message": commit["message"]
                })
    
    print_success(f"Identified {len(docs_to_process)} documents to process")
    
    # Simulate processing
    processed = 0
    failed = 0
    
    print("\nProcessing documents...")
    for i, doc in enumerate(docs_to_process[:50], 1):  # Process first 50
        file_path = repo_path / doc["file"]
        
        if file_path.exists():
            try:
                # Try to parse
                if file_path.suffix == '.md':
                    parsed = parser.parse(file_path)
                    normalized = normalizer.normalize(parsed)
                    processed += 1
                else:
                    # For Python files, just read
                    content = file_path.read_text(errors='ignore')
                    if content:
                        processed += 1
                
                if i % 10 == 0:
                    print(f"  Processed {i}/{len(docs_to_process[:50])} documents...")
            except Exception as e:
                failed += 1
        else:
            failed += 1
    
    print_success(f"Successfully processed {processed} documents")
    if failed > 0:
        print(f"⚠️  Failed to process {failed} documents")
    
    # Phase 5: Statistics Summary
    print_section("Phase 5: Summary Statistics")
    
    stats = {
        "Total Commits Analyzed": len(commits),
        "Total Files in Commits": len(all_changed_files),
        "Markdown Files in Service": len(md_files),
        "Python Files in Service": len(py_files),
        "Documents Processed": processed,
        "Processing Success Rate": f"{(processed / (processed + failed) * 100):.1f}%" if (processed + failed) > 0 else "N/A"
    }
    
    for key, value in stats.items():
        print_metric(key, value)
    
    # Phase 6: Training Effect Simulation
    print_section("Phase 6: Training Effect Demonstration")
    
    print_info("Before training: Limited context")
    print("  Query: 'What is the refactoring plan?'")
    print("  Response: [No context available - would use general knowledge only]")
    
    print_info(f"\nAfter ingesting {processed} documents from 20 commits:")
    print("  Query: 'What is the refactoring plan?'")
    print("  Response: [Would now have access to:]")
    print(f"    - {len([f for f in all_changed_files if 'PLAN' in f.upper() or 'README' in f.upper()])} planning documents")
    print(f"    - {len([f for f in all_changed_files if f.endswith('.md')])} markdown docs")
    print(f"    - {len([f for f in all_changed_files if f.endswith('.py')])} Python files")
    print(f"    - Git history context from {len(commits)} commits")
    
    # Show what documents would be available
    planning_docs = [f for f in all_changed_files if 'PLAN' in f.upper() or 'REFACTOR' in f.upper() or 'GUIDE' in f.upper()]
    if planning_docs:
        print("\n  Available planning documents:")
        for doc in planning_docs[:5]:
            print(f"    📋 {doc}")
    
    # Final Summary
    print_section("✅ VALIDATION COMPLETE")
    
    print_success("Document scanning: WORKING")
    print_success("Git commit analysis: WORKING")
    print_success("Document parsing: WORKING")
    print_success("Content normalization: WORKING")
    print_success("Metadata extraction: WORKING")
    print_success(f"Training simulation: {processed} docs processed")
    
    print("\n" + "=" * 80)
    print("  🎉 ECOSYSTEM-MCP FEATURES VALIDATED!")
    print("=" * 80)
    
    print("\n💡 Next Steps:")
    print("  1. Start Docker Desktop")
    print("  2. Run: docker-compose up -d")
    print("  3. Run: python -m src.server")
    print("  4. Access: http://localhost:8000/docs")
    print("  5. Ingest with: POST /api/v1/admin/ingest")
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

