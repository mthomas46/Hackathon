#!/usr/bin/env python3
"""
Evergreen Documentation Generator

Uses the RAG system to generate comprehensive, intelligent documentation
by analyzing all code, documents, and git history in the service.

This leverages:
- Document ingestion pipeline
- Semantic search (ChromaDB)
- RAG-based synthesis (LLM)
- Git history analysis
"""

import asyncio
import httpx
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import subprocess

BASE_URL = "http://localhost:8000"
OUTPUT_DIR = Path("./generated_docs")


class EvergreenDocsGenerator:
    """Generate master documentation using RAG system."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.output_dir = OUTPUT_DIR
        self.output_dir.mkdir(exist_ok=True)
    
    async def ensure_documents_ingested(self):
        """Ensure all documents are ingested into the RAG system."""
        print("\n" + "="*80)
        print("STEP 1: DOCUMENT INGESTION")
        print("="*80)
        
        async with httpx.AsyncClient(timeout=600.0) as client:
            # Check document count
            response = await client.post(
                f"{self.base_url}/api/v1/query",
                json={"limit": 1}
            )
            
            if response.status_code == 200:
                data = response.json()
                doc_count = data.get("total", 0)
                print(f"\n✅ Current document count: {doc_count}")
                
                if doc_count < 100:
                    print(f"\n⚠️  Low document count. Triggering ingestion...")
                    
                    # Trigger ingestion
                    repo_path = Path("/Users/mykalthomas/Documents/work/Hackathon")
                    ingest_response = await client.post(
                        f"{self.base_url}/api/v1/admin/ingest",
                        json={
                            "repo_path": str(repo_path),
                            "patterns": ["*.md", "*.py"],
                            "mode": "incremental"
                        }
                    )
                    
                    if ingest_response.status_code == 200:
                        job_data = ingest_response.json()
                        job_id = job_data["job_id"]
                        print(f"   Ingestion job started: {job_id}")
                        print(f"   This may take several minutes...")
                        
                        # Wait for completion
                        await self._wait_for_ingestion(client, job_id)
                    else:
                        print(f"   ❌ Failed to start ingestion: {ingest_response.text}")
                else:
                    print(f"   ✅ Sufficient documents available for generation")
    
    async def _wait_for_ingestion(self, client: httpx.AsyncClient, job_id: str):
        """Wait for ingestion job to complete."""
        while True:
            await asyncio.sleep(5)
            
            response = await client.get(f"{self.base_url}/api/v1/admin/ingest/{job_id}")
            if response.status_code == 200:
                status = response.json()
                
                if status["status"] in ["completed", "failed"]:
                    print(f"\n   Ingestion {status['status']}: {status.get('processed_documents', 0)} documents")
                    break
                
                print(f"   Progress: {status.get('processed_documents', 0)} documents...", end='\r')
    
    async def ask_rag(self, question: str, temperature: float = 0.0) -> Dict[str, Any]:
        """Ask a question using RAG system."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/ask",
                json={
                    "question": question,
                    "n_results": 20,
                    "prefer_recent": True,
                    "temperature": temperature
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ RAG query failed: {response.text}")
                return {}
    
    def get_git_history(self) -> List[Dict[str, str]]:
        """Extract git history for timeline."""
        print("\n" + "="*80)
        print("STEP 2: GIT HISTORY ANALYSIS")
        print("="*80)
        
        try:
            # Get git log
            result = subprocess.run(
                ["git", "log", "--pretty=format:%H|%an|%ae|%ad|%s", "--date=short", "--all"],
                cwd="/Users/mykalthomas/Documents/work/Hackathon",
                capture_output=True,
                text=True
            )
            
            commits = []
            for line in result.stdout.split('\n')[:100]:  # Last 100 commits
                if '|' in line:
                    hash, author, email, date, message = line.split('|', 4)
                    commits.append({
                        "hash": hash[:8],
                        "author": author,
                        "date": date,
                        "message": message
                    })
            
            print(f"\n✅ Analyzed {len(commits)} commits")
            return commits
        
        except Exception as e:
            print(f"❌ Git history extraction failed: {e}")
            return []
    
    async def generate_overview(self) -> str:
        """Generate service overview."""
        print("\n" + "="*80)
        print("STEP 3: GENERATING OVERVIEW")
        print("="*80)
        
        question = """What is the ecosystem-mcp service? Provide a comprehensive overview including:
        - Main purpose and goals
        - Key features and capabilities
        - Architecture and components
        - Technology stack"""
        
        print(f"\n🤖 Asking RAG: {question[:100]}...")
        result = await self.ask_rag(question)
        
        overview = result.get("answer", "")
        sources = result.get("sources", [])
        
        print(f"✅ Generated overview: {len(overview)} chars from {len(sources)} sources")
        
        return overview
    
    async def generate_architecture(self) -> str:
        """Generate architecture documentation."""
        print("\n" + "="*80)
        print("STEP 4: GENERATING ARCHITECTURE")
        print("="*80)
        
        question = """Describe the architecture of ecosystem-mcp in detail:
        - Service components and their roles
        - Data flow and interactions
        - Database schema and storage
        - Caching layers and optimization
        - API endpoints and interfaces"""
        
        print(f"\n🤖 Asking RAG: {question[:100]}...")
        result = await self.ask_rag(question)
        
        architecture = result.get("answer", "")
        print(f"✅ Generated architecture: {len(architecture)} chars")
        
        return architecture
    
    async def generate_features(self) -> str:
        """Generate features documentation."""
        print("\n" + "="*80)
        print("STEP 5: GENERATING FEATURES")
        print("="*80)
        
        question = """What are the main features of ecosystem-mcp? Include:
        - Document ingestion and processing
        - Semantic search capabilities
        - RAG (Retrieval Augmented Generation)
        - Caching and performance optimizations
        - LLM integration (Ollama, Cursor, etc.)
        - API endpoints and usage"""
        
        print(f"\n🤖 Asking RAG: {question[:100]}...")
        result = await self.ask_rag(question)
        
        features = result.get("answer", "")
        print(f"✅ Generated features: {len(features)} chars")
        
        return features
    
    async def generate_performance(self) -> str:
        """Generate performance documentation."""
        print("\n" + "="*80)
        print("STEP 6: GENERATING PERFORMANCE")
        print("="*80)
        
        question = """What are the performance characteristics and optimizations in ecosystem-mcp?
        Include caching strategies, throughput improvements, latency optimizations, and benchmarks."""
        
        print(f"\n🤖 Asking RAG: {question[:100]}...")
        result = await self.ask_rag(question)
        
        performance = result.get("answer", "")
        print(f"✅ Generated performance: {len(performance)} chars")
        
        return performance
    
    async def generate_usage_guide(self) -> str:
        """Generate usage guide."""
        print("\n" + "="*80)
        print("STEP 7: GENERATING USAGE GUIDE")
        print("="*80)
        
        question = """How do you use the ecosystem-mcp service? Provide:
        - Getting started guide
        - API endpoint usage with examples
        - Configuration options
        - Common use cases
        - Troubleshooting tips"""
        
        print(f"\n🤖 Asking RAG: {question[:100]}...")
        result = await self.ask_rag(question)
        
        usage = result.get("answer", "")
        print(f"✅ Generated usage guide: {len(usage)} chars")
        
        return usage
    
    async def generate_development_guide(self) -> str:
        """Generate development guide."""
        print("\n" + "="*80)
        print("STEP 8: GENERATING DEVELOPMENT GUIDE")
        print("="*80)
        
        question = """How do you develop and contribute to ecosystem-mcp? Include:
        - Development setup
        - Code structure and organization
        - Testing approach
        - Adding new features
        - Best practices"""
        
        print(f"\n🤖 Asking RAG: {question[:100]}...")
        result = await self.ask_rag(question)
        
        dev_guide = result.get("answer", "")
        print(f"✅ Generated dev guide: {len(dev_guide)} chars")
        
        return dev_guide
    
    def generate_history_timeline(self, commits: List[Dict[str, str]]) -> str:
        """Generate historical timeline from commits."""
        print("\n" + "="*80)
        print("STEP 9: GENERATING HISTORY TIMELINE")
        print("="*80)
        
        timeline = "# Service History Timeline\n\n"
        timeline += f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        
        # Group by month
        by_month = {}
        for commit in commits:
            month = commit["date"][:7]  # YYYY-MM
            if month not in by_month:
                by_month[month] = []
            by_month[month].append(commit)
        
        # Generate timeline
        for month in sorted(by_month.keys(), reverse=True):
            timeline += f"\n## {month}\n\n"
            
            month_commits = by_month[month]
            timeline += f"*{len(month_commits)} commits this month*\n\n"
            
            # Categorize commits
            features = [c for c in month_commits if any(k in c['message'].lower() 
                       for k in ['add', 'feature', 'implement', 'create'])]
            fixes = [c for c in month_commits if any(k in c['message'].lower() 
                    for k in ['fix', 'bug', 'resolve', 'patch'])]
            docs = [c for c in month_commits if any(k in c['message'].lower() 
                   for k in ['doc', 'readme', 'comment'])]
            optimizations = [c for c in month_commits if any(k in c['message'].lower() 
                            for k in ['optim', 'perf', 'cache', 'speed'])]
            
            if features:
                timeline += "### ✨ Features\n\n"
                for commit in features[:5]:
                    timeline += f"- {commit['message']} (`{commit['hash']}`)\n"
                timeline += "\n"
            
            if fixes:
                timeline += "### 🐛 Fixes\n\n"
                for commit in fixes[:5]:
                    timeline += f"- {commit['message']} (`{commit['hash']}`)\n"
                timeline += "\n"
            
            if optimizations:
                timeline += "### ⚡ Optimizations\n\n"
                for commit in optimizations[:3]:
                    timeline += f"- {commit['message']} (`{commit['hash']}`)\n"
                timeline += "\n"
            
            if docs:
                timeline += "### 📄 Documentation\n\n"
                for commit in docs[:3]:
                    timeline += f"- {commit['message']} (`{commit['hash']}`)\n"
                timeline += "\n"
        
        print(f"✅ Generated timeline: {len(by_month)} months")
        return timeline
    
    async def generate_master_doc(self, sections: Dict[str, str], timeline: str):
        """Generate master evergreen documentation."""
        print("\n" + "="*80)
        print("STEP 10: COMPILING MASTER DOCUMENTATION")
        print("="*80)
        
        doc = f"""# Ecosystem MCP - Master Documentation

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Type**: Evergreen Documentation (AI-Generated using RAG)  
**Status**: 🌲 Living Document - Auto-updated from service intelligence

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Performance](#performance)
5. [Usage Guide](#usage-guide)
6. [Development Guide](#development-guide)
7. [History](#history)

---

## Overview

{sections['overview']}

---

## Architecture

{sections['architecture']}

---

## Features

{sections['features']}

---

## Performance

{sections['performance']}

---

## Usage Guide

{sections['usage']}

---

## Development Guide

{sections['development']}

---

## History

{timeline}

---

## How This Documentation Was Generated

This documentation was automatically generated using the ecosystem-mcp service itself:

1. **Document Ingestion**: All `.md` and `.py` files were ingested and embedded
2. **Semantic Analysis**: ChromaDB vector search analyzed relationships
3. **RAG Synthesis**: LLM (Ollama) generated coherent explanations
4. **Git Integration**: Commit history extracted for timeline
5. **Intelligent Compilation**: Sections combined into master document

### Update This Documentation

To regenerate with latest information:

```bash
cd /path/to/ecosystem-mcp
python3 generate_evergreen_docs.py
```

The RAG system will analyze all current documents and code to produce
an updated version incorporating the latest changes.

---

*This is a living document maintained by AI. Last updated: {datetime.now().strftime('%Y-%m-%d')}*
"""
        
        # Save master doc
        master_file = self.output_dir / "MASTER_DOCUMENTATION.md"
        master_file.write_text(doc)
        print(f"\n✅ Saved master documentation: {master_file}")
        
        # Save individual sections for modularity
        for name, content in sections.items():
            section_file = self.output_dir / f"{name.upper()}.md"
            section_file.write_text(f"# {name.title()}\n\n{content}")
            print(f"   Saved section: {section_file.name}")
        
        # Save timeline separately
        timeline_file = self.output_dir / "SERVICE_HISTORY.md"
        timeline_file.write_text(timeline)
        print(f"   Saved timeline: {timeline_file.name}")
        
        return str(master_file)
    
    async def generate(self):
        """Generate all evergreen documentation."""
        print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║          🌲 EVERGREEN DOCUMENTATION GENERATOR 🌲                         ║
║                                                                           ║
║  Using RAG intelligence to generate master documentation and history     ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

This will:
1. Ensure documents are ingested
2. Extract git history
3. Generate comprehensive documentation using RAG
4. Compile into master evergreen doc
5. Create modular sections

""")
        
        try:
            # Step 1: Ensure documents ingested
            await self.ensure_documents_ingested()
            
            # Step 2: Get git history
            commits = self.get_git_history()
            
            # Steps 3-8: Generate sections using RAG
            sections = {
                'overview': await self.generate_overview(),
                'architecture': await self.generate_architecture(),
                'features': await self.generate_features(),
                'performance': await self.generate_performance(),
                'usage': await self.generate_usage_guide(),
                'development': await self.generate_development_guide(),
            }
            
            # Step 9: Generate timeline
            timeline = self.generate_history_timeline(commits)
            
            # Step 10: Compile master doc
            master_file = await self.generate_master_doc(sections, timeline)
            
            print("\n" + "="*80)
            print("✅ GENERATION COMPLETE!")
            print("="*80)
            print(f"\n📄 Master Documentation: {master_file}")
            print(f"📁 All files in: {self.output_dir}")
            print(f"\nGenerated files:")
            for file in sorted(self.output_dir.glob("*.md")):
                size = file.stat().st_size / 1024  # KB
                print(f"   • {file.name} ({size:.1f} KB)")
            
            print(f"\n🎉 Your evergreen documentation is ready!")
            print(f"\nNext steps:")
            print(f"1. Review the generated documentation")
            print(f"2. Customize as needed")
            print(f"3. Re-run anytime to update with latest changes")
            print(f"4. The RAG system learns from all your code and docs!")
            
        except Exception as e:
            print(f"\n❌ Generation failed: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Run the evergreen documentation generator."""
    generator = EvergreenDocsGenerator()
    await generator.generate()


if __name__ == "__main__":
    asyncio.run(main())

