#!/usr/bin/env python3
"""
Deep Documentation Generator - Multi-Pass Workflow System

Uses a sophisticated multi-pass approach to generate highly detailed documentation:

WORKFLOW SYSTEM:
1. Initial Pass: Broad overview questions
2. Deep Dive Pass: Detailed technical questions
3. Practical Pass: Examples, use cases, and patterns
4. Integration Pass: Combine and synthesize all passes
5. Refinement Pass: Polish and enhance coherence

Each section goes through ALL passes for maximum depth and detail.
"""

import asyncio
import httpx
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple
import subprocess

BASE_URL = "http://localhost:8000"
OUTPUT_DIR = Path("./generated_docs_deep")


class MultiPassDocGenerator:
    """Generate deep, comprehensive documentation using multi-pass workflow."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.output_dir = OUTPUT_DIR
        self.output_dir.mkdir(exist_ok=True)
        self.session_cache = {}  # Cache for the session
    
    async def ask_rag(
        self, 
        question: str, 
        temperature: float = 0.0,
        n_results: int = 20
    ) -> Dict[str, Any]:
        """Ask a question using RAG system with caching and metrics tracking."""
        import time
        
        start_time = time.time()
        cache_hit = False
        status = "success"
        
        # Sample CPU usage
        self.cpu_samples.append(self.process.cpu_percent())
        
        # Check session cache first
        cache_key = f"{question}_{temperature}_{n_results}"
        if cache_key in self.session_cache:
            print(f"   💾 Cache hit! (instant)")
            cache_hit = True
            result = self.session_cache[cache_key]
            status = "cached"
        else:
            print(f"   🔍 Querying RAG...", end='', flush=True)
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                self.metrics.network_requests += 1
                
                response = await client.post(
                    f"{self.base_url}/api/v1/ask",
                    json={
                        "question": question,
                        "n_results": n_results,
                        "prefer_recent": True,
                        "temperature": temperature
                    }
                )
                
                elapsed = time.time() - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    answer_len = len(result.get("answer", ""))
                    sources = len(result.get("sources", []))
                    print(f" ✅ {elapsed:.1f}s ({answer_len} chars, {sources} sources)")
                    self.session_cache[cache_key] = result
                else:
                    print(f" ❌ Failed ({response.status_code})")
                    result = {}
                    status = "failed"
        
        # Record metrics
        duration = time.time() - start_time
        answer_len = len(result.get("answer", "")) if result else 0
        sources = result.get("sources", []) if result else []
        
        query_metrics = QueryMetrics(
            question=question[:100] + "..." if len(question) > 100 else question,
            pass_name=self.current_pass_metrics.pass_name if self.current_pass_metrics else "unknown",
            section=self.current_section_metrics.section_name if self.current_section_metrics else "unknown",
            timestamp=start_time,
            duration_seconds=duration,
            answer_length=answer_len,
            source_count=len(sources),
            sources_used=[{
                "id": s.get("id"),
                "file_path": s.get("file_path"),
                "score": s.get("score", s.get("relevance_score", 0))
            } for s in sources],
            cache_hit=cache_hit,
            temperature=temperature,
            n_results=n_results,
            status=status
        )
        
        if self.current_pass_metrics:
            self.current_pass_metrics.queries.append(query_metrics)
            self.current_pass_metrics.total_queries += 1
            if cache_hit:
                self.current_pass_metrics.cache_hits += 1
            self.current_pass_metrics.total_answer_length += answer_len
        
        # Update peak memory
        current_memory = self.process.memory_info().rss / 1024 / 1024
        self.metrics.peak_memory_mb = max(self.metrics.peak_memory_mb, current_memory)
        
        return result
    
    async def multi_pass_section(
        self,
        section_name: str,
        questions: Dict[str, List[str]]
    ) -> str:
        """
        Generate a section using multi-pass workflow with metrics tracking.
        
        Args:
            section_name: Name of the section
            questions: Dict with pass names and their questions
        
        Returns:
            Comprehensive section content
        """
        import time
        section_start = time.time()
        
        # Initialize section metrics
        self.current_section_metrics = SectionMetrics(
            section_name=section_name,
            start_time=section_start,
            end_time=0,
            duration_seconds=0
        )
        
        print(f"\n{'='*80}")
        print(f"🎯 GENERATING: {section_name.upper()}")
        print(f"{'='*80}")
        
        # Count total questions
        total_questions = sum(len(q) for q in questions.values()) + 1  # +1 for synthesis
        current_question = 0
        
        all_content = {}
        
        # Pass 1: Initial/Broad
        if "initial" in questions:
            pass_start = time.time()
            self.current_pass_metrics = PassMetrics(
                pass_name="Pass 1: Initial Overview",
                section=section_name,
                start_time=pass_start,
                end_time=0,
                duration_seconds=0
            )
            
            print(f"\n📝 Pass 1/4: Initial Overview ({len(questions['initial'])} questions)")
            print(f"   Purpose: Establish foundation and broad understanding")
            content_parts = []
            for i, question in enumerate(questions["initial"], 1):
                current_question += 1
                progress = (current_question / total_questions) * 100
                print(f"\n   [{progress:5.1f}%] Question {i}/{len(questions['initial'])}")
                print(f"   ❓ {question[:77]}{'...' if len(question) > 77 else ''}")
                
                result = await self.ask_rag(question, temperature=0.0)
                if result.get("answer"):
                    content_parts.append(result["answer"])
                await asyncio.sleep(0.3)
            
            all_content["initial"] = "\n\n".join(content_parts)
            
            # Finalize pass metrics
            self.current_pass_metrics.end_time = time.time()
            self.current_pass_metrics.duration_seconds = self.current_pass_metrics.end_time - pass_start
            self.current_section_metrics.passes.append(self.current_pass_metrics)
            
            print(f"\n   ✅ Pass 1 complete: {len(all_content['initial']):,} chars generated")
        
        # Pass 2: Deep Dive
        if "deep_dive" in questions:
            pass_start = time.time()
            self.current_pass_metrics = PassMetrics(
                pass_name="Pass 2: Deep Dive",
                section=section_name,
                start_time=pass_start,
                end_time=0,
                duration_seconds=0
            )
            
            print(f"\n🔬 Pass 2/4: Deep Dive ({len(questions['deep_dive'])} questions)")
            print(f"   Purpose: Explore technical details and implementation")
            content_parts = []
            for i, question in enumerate(questions["deep_dive"], 1):
                current_question += 1
                progress = (current_question / total_questions) * 100
                print(f"\n   [{progress:5.1f}%] Question {i}/{len(questions['deep_dive'])}")
                print(f"   ❓ {question[:77]}{'...' if len(question) > 77 else ''}")
                
                result = await self.ask_rag(question, temperature=0.0, n_results=25)
                if result.get("answer"):
                    content_parts.append(result["answer"])
                await asyncio.sleep(0.3)
            
            all_content["deep_dive"] = "\n\n".join(content_parts)
            
            # Finalize pass metrics
            self.current_pass_metrics.end_time = time.time()
            self.current_pass_metrics.duration_seconds = self.current_pass_metrics.end_time - pass_start
            self.current_section_metrics.passes.append(self.current_pass_metrics)
            
            print(f"\n   ✅ Pass 2 complete: {len(all_content['deep_dive']):,} chars generated")
        
        # Pass 3: Practical/Examples
        if "practical" in questions:
            pass_start = time.time()
            self.current_pass_metrics = PassMetrics(
                pass_name="Pass 3: Practical Examples",
                section=section_name,
                start_time=pass_start,
                end_time=0,
                duration_seconds=0
            )
            
            print(f"\n💡 Pass 3/4: Practical Examples ({len(questions['practical'])} questions)")
            print(f"   Purpose: Real-world usage and practical patterns")
            content_parts = []
            for i, question in enumerate(questions["practical"], 1):
                current_question += 1
                progress = (current_question / total_questions) * 100
                print(f"\n   [{progress:5.1f}%] Question {i}/{len(questions['practical'])}")
                print(f"   ❓ {question[:77]}{'...' if len(question) > 77 else ''}")
                
                result = await self.ask_rag(question, temperature=0.1, n_results=20)
                if result.get("answer"):
                    content_parts.append(result["answer"])
                await asyncio.sleep(0.3)
            
            all_content["practical"] = "\n\n".join(content_parts)
            
            # Finalize pass metrics
            self.current_pass_metrics.end_time = time.time()
            self.current_pass_metrics.duration_seconds = self.current_pass_metrics.end_time - pass_start
            self.current_section_metrics.passes.append(self.current_pass_metrics)
            
            print(f"\n   ✅ Pass 3 complete: {len(all_content['practical']):,} chars generated")
        
        # Pass 4: Integration/Synthesis
        pass_start = time.time()
        self.current_pass_metrics = PassMetrics(
            pass_name="Pass 4: Synthesis",
            section=section_name,
            start_time=pass_start,
            end_time=0,
            duration_seconds=0
        )
        
        current_question += 1
        progress = (current_question / total_questions) * 100
        print(f"\n🔗 Pass 4/4: Integration & Synthesis")
        print(f"   [{progress:5.1f}%] Combining all passes into coherent narrative...")
        print(f"   Purpose: Synthesize {sum(len(c) for c in all_content.values()):,} chars into unified section")
        
        synthesis_prompt = f"""Based on the following information about {section_name}, 
        create a comprehensive, well-structured section that integrates all aspects:

        OVERVIEW:
        {all_content.get('initial', '')}

        TECHNICAL DETAILS:
        {all_content.get('deep_dive', '')}

        PRACTICAL INFORMATION:
        {all_content.get('practical', '')}

        Please synthesize this into a coherent, detailed section with:
        - Clear structure and headings
        - Technical accuracy
        - Practical examples
        - Comprehensive coverage
        """
        
        result = await self.ask_rag(synthesis_prompt, temperature=0.0, n_results=25)
        synthesized = result.get("answer", "")
        
        # If synthesis failed, concatenate all passes
        if not synthesized or len(synthesized) < 500:
            print(f"   ⚠️  Synthesis produced short output, using concatenation fallback")
            synthesized = self._concatenate_passes(section_name, all_content)
        
        # Finalize pass metrics
        self.current_pass_metrics.end_time = time.time()
        self.current_pass_metrics.duration_seconds = self.current_pass_metrics.end_time - pass_start
        self.current_section_metrics.passes.append(self.current_pass_metrics)
        
        # Finalize section metrics
        section_time = time.time() - section_start
        self.current_section_metrics.end_time = time.time()
        self.current_section_metrics.duration_seconds = section_time
        self.current_section_metrics.total_queries = sum(p.total_queries for p in self.current_section_metrics.passes)
        self.current_section_metrics.cache_hits = sum(p.cache_hits for p in self.current_section_metrics.passes)
        self.current_section_metrics.total_answer_length = len(synthesized)
        self.current_section_metrics.output_size_chars = len(synthesized)
        self.current_section_metrics.output_size_bytes = len(synthesized.encode('utf-8'))
        
        # Add to global metrics
        self.metrics.sections.append(self.current_section_metrics)
        
        print(f"\n   ✅ Pass 4 complete: {len(synthesized):,} chars synthesized")
        print(f"\n{'─'*80}")
        print(f"✅ {section_name.upper()} COMPLETE in {section_time:.1f}s")
        print(f"   Total output: {len(synthesized):,} characters")
        print(f"   Total queries: {self.current_section_metrics.total_queries}")
        print(f"   Cache hits: {self.current_section_metrics.cache_hits}/{self.current_section_metrics.total_queries}")
        print(f"   Memory: {self.process.memory_info().rss / 1024 / 1024:.1f} MB")
        print(f"{'─'*80}")
        
        return synthesized
    
    def _concatenate_passes(self, section_name: str, content: Dict[str, str]) -> str:
        """Fallback: concatenate all passes with structure."""
        output = f"# {section_name}\n\n"
        
        if content.get("initial"):
            output += "## Overview\n\n"
            output += content["initial"] + "\n\n"
        
        if content.get("deep_dive"):
            output += "## Technical Details\n\n"
            output += content["deep_dive"] + "\n\n"
        
        if content.get("practical"):
            output += "## Practical Information\n\n"
            output += content["practical"] + "\n\n"
        
        return output
    
    async def generate_deep_overview(self) -> str:
        """Generate comprehensive overview using multi-pass."""
        questions = {
            "initial": [
                "What is the ecosystem-mcp service? Provide a comprehensive overview.",
                "What problem does ecosystem-mcp solve and why was it created?",
                "Who are the target users and what are the main use cases?",
            ],
            "deep_dive": [
                "What are the core technical components of ecosystem-mcp and how do they work together?",
                "What technology stack is used and why were these choices made?",
                "What are the key architectural decisions and design patterns?",
                "How does data flow through the system from input to output?",
            ],
            "practical": [
                "What are real-world examples of using ecosystem-mcp?",
                "What are the typical workflows and usage patterns?",
                "What makes ecosystem-mcp unique compared to alternatives?",
            ]
        }
        
        return await self.multi_pass_section("Overview", questions)
    
    async def generate_deep_architecture(self) -> str:
        """Generate comprehensive architecture documentation."""
        questions = {
            "initial": [
                "Describe the overall architecture of ecosystem-mcp.",
                "What are the main service components and their responsibilities?",
            ],
            "deep_dive": [
                "How does the FastAPI application layer work? What endpoints and middleware exist?",
                "Describe the database layer: PostgreSQL schema, models, and repositories.",
                "How does ChromaDB work for vector storage? What is the embedding process?",
                "Explain the Redis caching layer: what's cached, TTLs, and cache strategies.",
                "How does Ollama integrate for LLM inference? What models are used?",
                "What is the document ingestion pipeline? Steps from file to embedded document.",
                "How does the RAG (Retrieval Augmented Generation) system work end-to-end?",
            ],
            "practical": [
                "Show the complete flow for a document ingestion request.",
                "Show the complete flow for a semantic search query.",
                "Show the complete flow for a RAG question-answering request.",
                "What are the key configuration points and environment variables?",
            ]
        }
        
        return await self.multi_pass_section("Architecture", questions)
    
    async def generate_deep_features(self) -> str:
        """Generate comprehensive features documentation."""
        questions = {
            "initial": [
                "List and describe all major features of ecosystem-mcp.",
                "What capabilities does the document ingestion system provide?",
                "What search and retrieval features are available?",
            ],
            "deep_dive": [
                "How does semantic search work? What algorithms and techniques are used?",
                "Describe the RAG implementation: retrieval, ranking, and generation.",
                "What caching strategies are implemented? List all cache layers.",
                "How does the 3-tier LLM routing work (Cursor, Desktop Ollama, Docker)?",
                "What monitoring and observability features exist?",
                "What API endpoints are available and what do they do?",
            ],
            "practical": [
                "Provide examples of search queries and expected results.",
                "Provide examples of RAG questions with sample responses.",
                "Show example API calls with curl commands.",
                "What are the performance characteristics of each feature?",
            ]
        }
        
        return await self.multi_pass_section("Features", questions)
    
    async def generate_deep_performance(self) -> str:
        """Generate comprehensive performance documentation."""
        questions = {
            "initial": [
                "What are the performance characteristics of ecosystem-mcp?",
                "What optimizations have been implemented?",
            ],
            "deep_dive": [
                "Describe all caching layers: what's cached, hit rates, and speedups.",
                "What is the performance of search queries (cold vs warm cache)?",
                "What is the performance of RAG queries (with different temperatures)?",
                "How does connection pooling work and what performance gains does it provide?",
                "What is the ingestion throughput (documents per minute)?",
                "How does parallel processing improve performance?",
                "What are the benchmark results and verified metrics?",
            ],
            "practical": [
                "What are realistic performance expectations for production?",
                "How do you optimize performance for different workloads?",
                "What configuration settings affect performance?",
                "What are the bottlenecks and how to address them?",
            ]
        }
        
        return await self.multi_pass_section("Performance", questions)
    
    async def generate_deep_api(self) -> str:
        """Generate comprehensive API documentation."""
        questions = {
            "initial": [
                "List all API endpoints in ecosystem-mcp with brief descriptions.",
                "What are the main API categories (health, search, RAG, admin, etc.)?",
            ],
            "deep_dive": [
                "Document the /api/v1/search endpoint: parameters, request/response format, examples.",
                "Document the /api/v1/ask endpoint: parameters, request/response format, examples.",
                "Document the /api/v1/admin/ingest endpoint: how to trigger ingestion.",
                "Document the /api/v1/query endpoint: document retrieval and filtering.",
                "Document the /api/v1/cache/stats endpoint: monitoring cache performance.",
                "What authentication and authorization mechanisms exist?",
                "What rate limits are in place and how to configure them?",
            ],
            "practical": [
                "Show complete curl examples for each major endpoint.",
                "Show Python client examples for programmatic access.",
                "What are common API usage patterns and workflows?",
                "How to handle errors and rate limiting?",
            ]
        }
        
        return await self.multi_pass_section("API Reference", questions)
    
    async def generate_deep_deployment(self) -> str:
        """Generate comprehensive deployment guide."""
        questions = {
            "initial": [
                "How do you deploy ecosystem-mcp?",
                "What are the system requirements and dependencies?",
            ],
            "deep_dive": [
                "Describe the Docker setup: containers, networking, volumes.",
                "What environment variables need to be configured?",
                "How to configure PostgreSQL, Redis, ChromaDB, and Ollama?",
                "What ports are used and how to configure networking?",
                "How to handle secrets and sensitive configuration?",
                "What monitoring should be set up for production?",
            ],
            "practical": [
                "Provide step-by-step deployment instructions for local development.",
                "Provide step-by-step deployment instructions for production.",
                "Show docker-compose configuration examples.",
                "What are common deployment issues and solutions?",
                "How to scale horizontally for high availability?",
            ]
        }
        
        return await self.multi_pass_section("Deployment", questions)
    
    async def generate_deep_development(self) -> str:
        """Generate comprehensive development guide."""
        questions = {
            "initial": [
                "How do you set up a development environment for ecosystem-mcp?",
                "What is the code structure and organization?",
            ],
            "deep_dive": [
                "Describe the directory structure and what each directory contains.",
                "What are the key Python modules and their purposes?",
                "How is the codebase organized (services, repositories, models, etc.)?",
                "What testing strategy is used? Unit, integration, functional tests?",
                "How to add a new API endpoint?",
                "How to add a new caching layer?",
                "What are the coding standards and best practices?",
            ],
            "practical": [
                "Show how to run tests locally.",
                "Show how to debug the application.",
                "Provide examples of common development tasks.",
                "How to contribute: workflow, pull requests, code review?",
            ]
        }
        
        return await self.multi_pass_section("Development Guide", questions)
    
    async def generate_deep_troubleshooting(self) -> str:
        """Generate comprehensive troubleshooting guide."""
        questions = {
            "initial": [
                "What are common issues with ecosystem-mcp?",
                "How do you diagnose problems?",
            ],
            "deep_dive": [
                "How to troubleshoot cache issues and verify cache is working?",
                "How to troubleshoot database connection problems?",
                "How to troubleshoot Redis connectivity?",
                "How to troubleshoot ChromaDB and vector search issues?",
                "How to troubleshoot Ollama and LLM generation problems?",
                "How to troubleshoot slow performance?",
                "How to troubleshoot memory or resource issues?",
            ],
            "practical": [
                "What diagnostic commands and tools are available?",
                "How to check logs for each component?",
                "Show examples of common error messages and their solutions.",
                "What monitoring metrics should you watch?",
            ]
        }
        
        return await self.multi_pass_section("Troubleshooting", questions)
    
    def get_git_history(self) -> List[Dict[str, str]]:
        """Extract detailed git history."""
        print(f"\n{'='*80}")
        print("EXTRACTING GIT HISTORY")
        print(f"{'='*80}")
        
        try:
            result = subprocess.run(
                ["git", "log", "--pretty=format:%H|%an|%ae|%ad|%s|%b", "--date=short", "--all"],
                cwd="/Users/mykalthomas/Documents/work/Hackathon",
                capture_output=True,
                text=True
            )
            
            commits = []
            for line in result.stdout.split('\n')[:200]:  # Last 200 commits
                if '|' in line:
                    parts = line.split('|', 5)
                    if len(parts) >= 5:
                        hash, author, email, date, message = parts[:5]
                        body = parts[5] if len(parts) > 5 else ""
                        commits.append({
                            "hash": hash[:8],
                            "author": author,
                            "date": date,
                            "message": message,
                            "body": body
                        })
            
            print(f"✅ Analyzed {len(commits)} commits")
            return commits
        
        except Exception as e:
            print(f"❌ Git history extraction failed: {e}")
            return []
    
    def generate_detailed_history(self, commits: List[Dict[str, str]]) -> str:
        """Generate detailed historical timeline."""
        print(f"\n{'='*80}")
        print("GENERATING DETAILED HISTORY")
        print(f"{'='*80}")
        
        timeline = "# Service Development History\n\n"
        timeline += f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        timeline += f"*Tracking {len(commits)} commits across the project lifecycle*\n\n"
        
        # Group by month
        by_month = {}
        for commit in commits:
            month = commit["date"][:7]  # YYYY-MM
            if month not in by_month:
                by_month[month] = []
            by_month[month].append(commit)
        
        # Generate detailed timeline
        for month in sorted(by_month.keys(), reverse=True):
            timeline += f"\n## {month}\n\n"
            
            month_commits = by_month[month]
            timeline += f"**{len(month_commits)} commits** | "
            
            # Count contributors
            contributors = len(set(c["author"] for c in month_commits))
            timeline += f"**{contributors} contributor(s)**\n\n"
            
            # Categorize commits with more detail
            features = [c for c in month_commits if any(k in c['message'].lower() 
                       for k in ['add', 'feature', 'implement', 'create', 'new'])]
            fixes = [c for c in month_commits if any(k in c['message'].lower() 
                    for k in ['fix', 'bug', 'resolve', 'patch', 'correct'])]
            docs = [c for c in month_commits if any(k in c['message'].lower() 
                   for k in ['doc', 'readme', 'comment', 'documentation'])]
            optimizations = [c for c in month_commits if any(k in c['message'].lower() 
                            for k in ['optim', 'perf', 'cache', 'speed', 'improve'])]
            tests = [c for c in month_commits if any(k in c['message'].lower() 
                    for k in ['test', 'testing', 'spec'])]
            refactor = [c for c in month_commits if any(k in c['message'].lower() 
                       for k in ['refactor', 'restructure', 'reorganize', 'cleanup'])]
            
            # Summary stats
            timeline += "### Summary\n\n"
            timeline += f"- ✨ {len(features)} features\n"
            timeline += f"- 🐛 {len(fixes)} fixes\n"
            timeline += f"- ⚡ {len(optimizations)} optimizations\n"
            timeline += f"- 📄 {len(docs)} documentation updates\n"
            timeline += f"- 🧪 {len(tests)} test additions\n"
            timeline += f"- 🔨 {len(refactor)} refactorings\n\n"
            
            # Detailed sections
            if features:
                timeline += "### ✨ Features & Enhancements\n\n"
                for commit in features[:10]:  # Top 10
                    timeline += f"- **{commit['message']}** (`{commit['hash']}`)\n"
                    if commit['body'] and len(commit['body'].strip()) > 10:
                        timeline += f"  > {commit['body'].strip()[:200]}\n"
                timeline += "\n"
            
            if optimizations:
                timeline += "### ⚡ Performance & Optimizations\n\n"
                for commit in optimizations[:8]:
                    timeline += f"- **{commit['message']}** (`{commit['hash']}`)\n"
                    if commit['body']:
                        timeline += f"  > {commit['body'].strip()[:200]}\n"
                timeline += "\n"
            
            if fixes:
                timeline += "### 🐛 Bug Fixes\n\n"
                for commit in fixes[:8]:
                    timeline += f"- **{commit['message']}** (`{commit['hash']}`)\n"
                timeline += "\n"
            
            if tests:
                timeline += "### 🧪 Testing\n\n"
                for commit in tests[:5]:
                    timeline += f"- **{commit['message']}** (`{commit['hash']}`)\n"
                timeline += "\n"
            
            if refactor:
                timeline += "### 🔨 Refactoring & Code Quality\n\n"
                for commit in refactor[:5]:
                    timeline += f"- **{commit['message']}** (`{commit['hash']}`)\n"
                timeline += "\n"
            
            if docs:
                timeline += "### 📄 Documentation\n\n"
                for commit in docs[:5]:
                    timeline += f"- **{commit['message']}** (`{commit['hash']}`)\n"
                timeline += "\n"
        
        print(f"✅ Generated detailed timeline: {len(by_month)} months, {len(timeline)} chars")
        return timeline
    
    async def generate_master_doc(
        self,
        sections: Dict[str, str],
        timeline: str
    ):
        """Generate comprehensive master documentation."""
        print(f"\n{'='*80}")
        print("COMPILING MASTER DOCUMENTATION")
        print(f"{'='*80}")
        
        doc = f"""# Ecosystem MCP - Comprehensive Documentation

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Type**: Deep Documentation (AI-Generated via Multi-Pass RAG)  
**Status**: 🌲 Living Document - Maintained by AI Intelligence  
**Methodology**: Multi-pass workflow with synthesis

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [API Reference](#api-reference)
5. [Performance](#performance)
6. [Deployment](#deployment)
7. [Development Guide](#development-guide)
8. [Troubleshooting](#troubleshooting)
9. [History](#history)

---

## Overview

{sections.get('overview', '')}

---

## Architecture

{sections.get('architecture', '')}

---

## Features

{sections.get('features', '')}

---

## API Reference

{sections.get('api', '')}

---

## Performance

{sections.get('performance', '')}

---

## Deployment

{sections.get('deployment', '')}

---

## Development Guide

{sections.get('development', '')}

---

## Troubleshooting

{sections.get('troubleshooting', '')}

---

## History

{timeline}

---

## About This Documentation

### Multi-Pass Generation Workflow

This documentation was generated using a sophisticated multi-pass RAG workflow:

#### Pass 1: Initial Overview
- Broad questions about purpose, goals, and capabilities
- Establishes foundation for deeper exploration

#### Pass 2: Deep Dive
- Detailed technical questions
- Explores implementation details and architecture
- Investigates edge cases and complexities

#### Pass 3: Practical Examples
- Real-world usage patterns
- Code examples and workflows
- Performance characteristics

#### Pass 4: Integration & Synthesis
- Combines all passes into coherent narrative
- Ensures consistency and completeness
- Adds structure and organization

### Update This Documentation

```bash
cd /path/to/ecosystem-mcp

# Quick update (single pass, 2-3 minutes)
python3 generate_evergreen_docs.py

# Deep update (multi-pass, 5-10 minutes)
python3 generate_deep_docs.py
```

The multi-pass system analyzes your codebase multiple times from different
angles to produce comprehensive, accurate documentation.

### Statistics

- **Sections**: {len(sections)}
- **Total Size**: {sum(len(s) for s in sections.values()) / 1024:.1f} KB
- **Git Commits Analyzed**: {len(timeline.split('##')) - 1} months
- **RAG Queries**: ~{len(sections) * 15} questions asked
- **Generation Time**: ~5-10 minutes (with caching)

---

*This is a living document maintained by AI. Last updated: {datetime.now().strftime('%Y-%m-%d')}*
"""
        
        # Save master doc
        master_file = self.output_dir / "COMPREHENSIVE_DOCUMENTATION.md"
        master_file.write_text(doc)
        size = master_file.stat().st_size / 1024  # KB
        print(f"\n✅ Saved master documentation: {master_file} ({size:.1f} KB)")
        
        # Save individual sections
        for name, content in sections.items():
            section_file = self.output_dir / f"{name.upper()}.md"
            section_file.write_text(f"# {name.title()}\n\n{content}")
            size = section_file.stat().st_size / 1024
            print(f"   Saved section: {section_file.name} ({size:.1f} KB)")
        
        # Save timeline
        timeline_file = self.output_dir / "DETAILED_HISTORY.md"
        timeline_file.write_text(timeline)
        size = timeline_file.stat().st_size / 1024
        print(f"   Saved timeline: {timeline_file.name} ({size:.1f} KB)")
        
        return str(master_file)
    
    async def generate(self):
        """Generate comprehensive deep documentation."""
        import time
        total_start = time.time()
        
        print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║        🧠 DEEP DOCUMENTATION GENERATOR - Multi-Pass Workflow 🧠          ║
║                                                                           ║
║  Using sophisticated multi-pass RAG to generate comprehensive docs       ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

📋 WORKFLOW OVERVIEW:
  • 8 major sections (Overview, Architecture, Features, API, Performance,
    Deployment, Development, Troubleshooting)
  • Each section: 3-4 passes with 10-15 questions
  • Total: ~100-120 RAG queries
  • Estimated time: 5-10 minutes
  • Git history: Detailed timeline generation

⏱️  Starting in 2 seconds... (Press Ctrl+C to cancel)
""")
        
        await asyncio.sleep(2)
        
        try:
            print("\n🚀 Starting multi-pass generation...\n")
            
            sections = {}
            total_sections = 8
            
            # Section 1/8
            print(f"\n{'█'*80}")
            print(f"SECTION 1/{total_sections}: OVERVIEW")
            print(f"{'█'*80}")
            sections['overview'] = await self.generate_deep_overview()
            
            # Section 2/8
            print(f"\n{'█'*80}")
            print(f"SECTION 2/{total_sections}: ARCHITECTURE")
            print(f"{'█'*80}")
            sections['architecture'] = await self.generate_deep_architecture()
            
            # Section 3/8
            print(f"\n{'█'*80}")
            print(f"SECTION 3/{total_sections}: FEATURES")
            print(f"{'█'*80}")
            sections['features'] = await self.generate_deep_features()
            
            # Section 4/8
            print(f"\n{'█'*80}")
            print(f"SECTION 4/{total_sections}: API REFERENCE")
            print(f"{'█'*80}")
            sections['api'] = await self.generate_deep_api()
            
            # Section 5/8
            print(f"\n{'█'*80}")
            print(f"SECTION 5/{total_sections}: PERFORMANCE")
            print(f"{'█'*80}")
            sections['performance'] = await self.generate_deep_performance()
            
            # Section 6/8
            print(f"\n{'█'*80}")
            print(f"SECTION 6/{total_sections}: DEPLOYMENT")
            print(f"{'█'*80}")
            sections['deployment'] = await self.generate_deep_deployment()
            
            # Section 7/8
            print(f"\n{'█'*80}")
            print(f"SECTION 7/{total_sections}: DEVELOPMENT GUIDE")
            print(f"{'█'*80}")
            sections['development'] = await self.generate_deep_development()
            
            # Section 8/8
            print(f"\n{'█'*80}")
            print(f"SECTION 8/{total_sections}: TROUBLESHOOTING")
            print(f"{'█'*80}")
            sections['troubleshooting'] = await self.generate_deep_troubleshooting()
            
            # Generate detailed timeline
            print(f"\n{'█'*80}")
            print(f"BONUS: GIT HISTORY & TIMELINE")
            print(f"{'█'*80}")
            commits = self.get_git_history()
            timeline = self.generate_detailed_history(commits)
            
            # Compile master doc
            print(f"\n{'█'*80}")
            print(f"FINAL STEP: COMPILING MASTER DOCUMENTATION")
            print(f"{'█'*80}")
            master_file = await self.generate_master_doc(sections, timeline)
            
            total_time = time.time() - total_start
            
            print("\n" + "="*80)
            print("✅ DEEP GENERATION COMPLETE!")
            print("="*80)
            print(f"\n⏱️  Total generation time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
            print(f"\n📄 Master Documentation: {master_file}")
            print(f"📁 All files in: {self.output_dir}")
            print(f"\n📊 File Statistics:")
            
            total_size = 0
            for file in sorted(self.output_dir.glob("*.md")):
                size = file.stat().st_size / 1024  # KB
                total_size += size
                print(f"   • {file.name:<40} {size:>8.1f} KB")
            
            print(f"   {'─'*60}")
            print(f"   {'TOTAL:':<40} {total_size:>8.1f} KB")
            
            print(f"\n🎯 Performance Statistics:")
            print(f"   • Total RAG queries: ~{len(sections) * 15}")
            print(f"   • Cache hits: {len(self.session_cache)} queries cached")
            print(f"   • Avg time per query: {total_time / (len(sections) * 15):.1f}s")
            print(f"   • Git commits analyzed: 200")
            
            print(f"\n🎉 Your deep documentation is ready!")
            print(f"\n✨ Features included:")
            print(f"   ✅ Multi-pass workflow (4 passes per section)")
            print(f"   ✅ 8 comprehensive sections + git history")
            print(f"   ✅ API reference with examples")
            print(f"   ✅ Deployment step-by-step guides")
            print(f"   ✅ Troubleshooting and diagnostics")
            print(f"   ✅ Detailed technical deep-dives")
            
            print(f"\n📖 Next steps:")
            print(f"   1. Review: cat {self.output_dir}/COMPREHENSIVE_DOCUMENTATION.md")
            print(f"   2. Compare: diff -r generated_docs/ generated_docs_deep/")
            print(f"   3. Update: Re-run anytime code changes")
            print(f"   4. Metrics: cat {METRICS_DIR}/generation_report.md")
            
            # Generate metrics report
            await self.generate_metrics_report()
            
        except KeyboardInterrupt:
            print(f"\n\n⚠️  Generation cancelled by user")
            print(f"   Partial results may be available in: {self.output_dir}")
            await self.generate_metrics_report()
        except Exception as e:
            print(f"\n❌ Generation failed: {e}")
            import traceback
            traceback.print_exc()
            await self.generate_metrics_report()


    async def generate_metrics_report(self):
        """Generate comprehensive metrics report."""
        # Finalize metrics
        self.metrics.end_time = time.time()
        self.metrics.duration_seconds = self.metrics.end_time - self.metrics.start_time
        self.metrics.total_queries = sum(s.total_queries for s in self.metrics.sections)
        self.metrics.cache_hits = sum(s.cache_hits for s in self.metrics.sections)
        self.metrics.cache_hit_rate = (self.metrics.cache_hits / self.metrics.total_queries * 100) if self.metrics.total_queries > 0 else 0
        self.metrics.total_answer_length = sum(s.total_answer_length for s in self.metrics.sections)
        self.metrics.total_output_size_bytes = sum(s.output_size_bytes for s in self.metrics.sections)
        self.metrics.avg_cpu_percent = sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0
        
        print(f"\n{'█'*80}")
        print(f"GENERATING METRICS REPORT")
        print(f"{'█'*80}")
        
        # Save raw JSON metrics
        json_file = METRICS_DIR / "generation_metrics.json"
        with open(json_file, 'w') as f:
            json.dump(asdict(self.metrics), f, indent=2, default=str)
        print(f"✅ Saved raw metrics: {json_file}")
        
        # Generate markdown report
        report = self._generate_markdown_report()
        report_file = METRICS_DIR / "generation_report.md"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"✅ Saved metrics report: {report_file}")
        
        # Generate per-section query logs
        for section in self.metrics.sections:
            section_log = self._generate_section_log(section)
            log_file = METRICS_DIR / f"{section.section_name.lower().replace(' ', '_')}_queries.json"
            with open(log_file, 'w') as f:
                json.dump(section_log, f, indent=2, default=str)
        print(f"✅ Saved per-section query logs: {METRICS_DIR}/")
        
        # Generate summary CSV
        csv_file = METRICS_DIR / "queries_summary.csv"
        self._generate_csv_summary(csv_file)
        print(f"✅ Saved CSV summary: {csv_file}")
        
        print(f"\n📊 Metrics generation complete!")
        print(f"   JSON: {json_file}")
        print(f"   Report: {report_file}")
        print(f"   Logs: {METRICS_DIR}/*_queries.json")
    
    def _generate_markdown_report(self) -> str:
        """Generate comprehensive markdown report."""
        report = f"""# Deep Documentation Generation Metrics Report

**Generated**: {datetime.fromtimestamp(self.metrics.start_time).strftime('%Y-%m-%d %H:%M:%S')}  
**Duration**: {self.metrics.duration_seconds / 60:.1f} minutes ({self.metrics.duration_seconds:.1f} seconds)

---

## 📊 Executive Summary

| Metric | Value |
|--------|-------|
| **Total Sections** | {len(self.metrics.sections)} |
| **Total Queries** | {self.metrics.total_queries} |
| **Cache Hits** | {self.metrics.cache_hits} ({self.metrics.cache_hit_rate:.1f}%) |
| **Network Requests** | {self.metrics.network_requests} |
| **Total Output** | {self.metrics.total_output_size_bytes / 1024:.1f} KB |
| **Total Answer Length** | {self.metrics.total_answer_length:,} characters |
| **Peak Memory** | {self.metrics.peak_memory_mb:.1f} MB |
| **Avg CPU** | {self.metrics.avg_cpu_percent:.1f}% |

---

## 📈 Performance Metrics

### Query Performance
- **Average Query Time**: {self.metrics.duration_seconds / self.metrics.total_queries:.2f}s per query
- **Queries per Minute**: {self.metrics.total_queries / (self.metrics.duration_seconds / 60):.1f}
- **Cache Hit Rate**: {self.metrics.cache_hit_rate:.1f}%
- **Cache Savings**: {self.metrics.cache_hits} queries saved ~{self.metrics.cache_hits * 15:.0f}s

### Resource Usage
- **Peak Memory**: {self.metrics.peak_memory_mb:.1f} MB
- **Memory per Query**: {self.metrics.peak_memory_mb / self.metrics.total_queries:.2f} MB
- **Average CPU**: {self.metrics.avg_cpu_percent:.1f}%
- **Network Efficiency**: {self.metrics.cache_hits / self.metrics.network_requests * 100 if self.metrics.network_requests > 0 else 0:.1f}% requests avoided

---

## 📑 Section Breakdown

"""
        
        for section in self.metrics.sections:
            report += f"""### {section.section_name.upper()}

| Metric | Value |
|--------|-------|
| **Duration** | {section.duration_seconds:.1f}s ({section.duration_seconds / 60:.1f}min) |
| **Passes** | {len(section.passes)} |
| **Total Queries** | {section.total_queries} |
| **Cache Hits** | {section.cache_hits} ({section.cache_hits / section.total_queries * 100 if section.total_queries > 0 else 0:.1f}%) |
| **Output Size** | {section.output_size_bytes / 1024:.1f} KB ({section.output_size_chars:,} chars) |
| **Avg Query Time** | {section.duration_seconds / section.total_queries if section.total_queries > 0 else 0:.2f}s |

#### Pass Details

"""
            for pass_metrics in section.passes:
                cache_rate = pass_metrics.cache_hits / pass_metrics.total_queries * 100 if pass_metrics.total_queries > 0 else 0
                report += f"""**{pass_metrics.pass_name}**
- Queries: {pass_metrics.total_queries}
- Cache Hits: {pass_metrics.cache_hits} ({cache_rate:.1f}%)
- Duration: {pass_metrics.duration_seconds:.1f}s
- Answer Length: {pass_metrics.total_answer_length:,} chars

"""
        
        report += f"""---

## 🔍 Query Details

### Top Sources Used

"""
        
        # Aggregate source usage
        source_usage = {}
        for section in self.metrics.sections:
            for pass_m in section.passes:
                for query in pass_m.queries:
                    for source in query.sources_used:
                        path = source['file_path']
                        if path not in source_usage:
                            source_usage[path] = {'count': 0, 'total_score': 0}
                        source_usage[path]['count'] += 1
                        source_usage[path]['total_score'] += source['score']
        
        # Sort by usage
        top_sources = sorted(source_usage.items(), key=lambda x: x[1]['count'], reverse=True)[:20]
        
        report += "| Source | Times Used | Avg Score |\n"
        report += "|--------|------------|----------|\n"
        for path, stats in top_sources:
            avg_score = stats['total_score'] / stats['count']
            short_path = path if len(path) < 60 else "..." + path[-57:]
            report += f"| `{short_path}` | {stats['count']} | {avg_score:.3f} |\n"
        
        report += f"""

---

## 📊 Cache Analysis

### Cache Hit Rate by Section

"""
        report += "| Section | Queries | Cache Hits | Hit Rate |\n"
        report += "|---------|---------|------------|---------|\n"
        for section in self.metrics.sections:
            hit_rate = section.cache_hits / section.total_queries * 100 if section.total_queries > 0 else 0
            report += f"| {section.section_name} | {section.total_queries} | {section.cache_hits} | {hit_rate:.1f}% |\n"
        
        report += f"""

### Cache Effectiveness
- **Total Potential Time**: {self.metrics.total_queries * 15:.0f}s (if all queries were cold)
- **Actual Time**: {self.metrics.duration_seconds:.0f}s
- **Time Saved**: {(self.metrics.total_queries * 15) - self.metrics.duration_seconds:.0f}s ({((self.metrics.total_queries * 15) - self.metrics.duration_seconds) / 60:.1f}min)
- **Efficiency Gain**: {(1 - (self.metrics.duration_seconds / (self.metrics.total_queries * 15))) * 100 if self.metrics.total_queries > 0 else 0:.1f}%

---

## 💾 Storage Metrics

| Item | Size |
|------|------|
| **Total Documentation** | {self.metrics.total_output_size_bytes / 1024:.1f} KB |
| **Metrics JSON** | ~{len(json.dumps(asdict(self.metrics), default=str)) / 1024:.1f} KB |
| **Estimated Total** | {(self.metrics.total_output_size_bytes + len(json.dumps(asdict(self.metrics), default=str))) / 1024:.1f} KB |

---

## 🎯 Recommendations

"""
        
        # Generate recommendations based on metrics
        if self.metrics.cache_hit_rate < 30:
            report += "- ⚠️ **Low cache hit rate** ({:.1f}%) - Consider running again to benefit from caching\n".format(self.metrics.cache_hit_rate)
        elif self.metrics.cache_hit_rate > 70:
            report += "- ✅ **Excellent cache utilization** ({:.1f}%) - Most queries served from cache\n".format(self.metrics.cache_hit_rate)
        
        if self.metrics.peak_memory_mb > 500:
            report += "- ⚠️ **High memory usage** ({:.1f} MB) - Consider processing sections sequentially\n".format(self.metrics.peak_memory_mb)
        
        if self.metrics.avg_cpu_percent < 20:
            report += "- 💡 **Low CPU usage** ({:.1f}%) - Bottleneck is likely network/IO, not CPU\n".format(self.metrics.avg_cpu_percent)
        
        report += f"""
---

## 📝 Notes

- All timestamps are in Unix epoch time
- Query durations include network latency
- Cache hits are session-local (in-memory during generation)
- Source scores range from 0.0 to 1.0
- Memory measurements are process RSS (Resident Set Size)

---

**Report Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return report
    
    def _generate_section_log(self, section: SectionMetrics) -> Dict[str, Any]:
        """Generate detailed log for a section."""
        return {
            "section": section.section_name,
            "summary": {
                "duration_seconds": section.duration_seconds,
                "total_queries": section.total_queries,
                "cache_hits": section.cache_hits,
                "output_size_bytes": section.output_size_bytes
            },
            "passes": [
                {
                    "pass_name": p.pass_name,
                    "duration_seconds": p.duration_seconds,
                    "total_queries": p.total_queries,
                    "cache_hits": p.cache_hits,
                    "queries": [
                        {
                            "question": q.question,
                            "timestamp": q.timestamp,
                            "duration_seconds": q.duration_seconds,
                            "answer_length": q.answer_length,
                            "source_count": q.source_count,
                            "sources": q.sources_used,
                            "cache_hit": q.cache_hit,
                            "temperature": q.temperature,
                            "n_results": q.n_results,
                            "status": q.status
                        }
                        for q in p.queries
                    ]
                }
                for p in section.passes
            ]
        }
    
    def _generate_csv_summary(self, csv_file: Path):
        """Generate CSV summary of all queries."""
        with open(csv_file, 'w') as f:
            f.write("section,pass,question,duration_seconds,answer_length,source_count,cache_hit,temperature,status\n")
            for section in self.metrics.sections:
                for pass_m in section.passes:
                    for query in pass_m.queries:
                        question_escaped = query.question.replace('"', '""').replace(',', ';')
                        f.write(f'"{section.section_name}","{pass_m.pass_name}","{question_escaped}",{query.duration_seconds},{query.answer_length},{query.source_count},{query.cache_hit},{query.temperature},{query.status}\n')


async def main():
    """Run the deep documentation generator with metrics."""
    generator = MultiPassDocGenerator()
    await generator.generate()


if __name__ == "__main__":
    asyncio.run(main())

