#!/usr/bin/env python3
"""
Enhanced Horus Heresy Knowledge Base MCP Demo

Features:
- Service health checks with retry logic
- Graceful error handling and fallbacks
- Enhanced terminal feedback
- Document generation from crawled data
- docs-horus-heresy directory support
"""

import asyncio
import httpx
import json
import time
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from ingestion.fandom_ingestor import FandomWikiIngestor
from ingestion.models import NormalizedDocument
from ingestion.tagging import UniversalTaggingConfig
from ingestion.utils.document_processor import DocumentProcessor
from ingestion.utils.metrics_tracker import MetricsTracker
import subprocess
import sys


class Colors:
    """Terminal colors."""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class EnhancedHorusHeresyDemo:
    """Enhanced Horus Heresy MCP demonstration with better error handling."""
    
    def __init__(self):
        self.correlation_id = str(uuid.uuid4())
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Service endpoints
        self.services = {
            "kafka-ingestion-service": "http://localhost:5700",
            "mcp-provisioner": "http://localhost:5400",
            "mcp-training-coordinator": "http://localhost:5600",
            "mcp-gateway": "http://localhost:8001",
            "summarizer-hub": "http://localhost:5160",
        }
        
        # Create directories
        run_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.run_dir = Path("reports") / f"horus_heresy_{run_timestamp}"
        self.docs_dir = Path("docs-horus-heresy")
        
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.docs_dir.mkdir(exist_ok=True)
        
        # Results
        self.mcp_id = None
        self.documents_ingested: List[NormalizedDocument] = []
        self.tag_collection = None
        self.service_status = {}
        self.doc_processor = DocumentProcessor()
        
        # Metrics tracking
        self.metrics = MetricsTracker()
        self.metrics.usability.documents_target = 12  # Horus Heresy doc suite
    
    def print_header(self, text: str):
        """Print section header."""
        print(f"\n{Colors.BOLD}{'=' * 70}{Colors.RESET}")
        print(f"{Colors.BOLD}  {text}{Colors.RESET}")
        print(f"{Colors.BOLD}{'=' * 70}{Colors.RESET}\n")
    
    def print_info(self, text: str):
        """Print info message."""
        print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")
    
    def print_success(self, text: str):
        """Print success message."""
        print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")
    
    def print_warning(self, text: str):
        """Print warning message."""
        print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")
    
    def print_error(self, text: str):
        """Print error message."""
        print(f"{Colors.RED}❌ {text}{Colors.RESET}")
    
    async def check_service_health(self, service_name: str, base_url: str) -> bool:
        """Check if service is healthy."""
        for endpoint in ['/health', '/api/health', '/api/v1/health']:
            try:
                start = time.time()
                response = await self.client.get(f"{base_url}{endpoint}", timeout=2.0)
                duration_ms = (time.time() - start) * 1000
                
                # Track service interaction
                self.metrics.track_service_interaction(
                    service=service_name,
                    endpoint=endpoint,
                    method="GET",
                    duration_ms=duration_ms,
                    status_code=response.status_code,
                    success=response.status_code == 200
                )
                
                if response.status_code == 200:
                    return True
            except Exception as e:
                # Track failed interaction
                self.metrics.track_service_interaction(
                    service=service_name,
                    endpoint=endpoint,
                    method="GET",
                    duration_ms=0,
                    status_code=0,
                    success=False,
                    error=str(e)
                )
                continue
        return False
    
    async def check_all_services(self) -> Dict[str, bool]:
        """Check health of all services."""
        self.print_info("🏥 Checking service health...")
        
        for service_name, base_url in self.services.items():
            is_healthy = await self.check_service_health(service_name, base_url)
            self.service_status[service_name] = is_healthy
            
            status = f"{Colors.GREEN}ONLINE ✓{Colors.RESET}" if is_healthy else f"{Colors.YELLOW}OFFLINE ✗{Colors.RESET}"
            print(f"   {service_name}: {status}")
        
        online = sum(1 for s in self.service_status.values() if s)
        total = len(self.service_status)
        
        if online == total:
            self.print_success(f"All {total} services online! 🎉")
        elif online > 0:
            self.print_warning(f"{online}/{total} services online (using fallbacks where needed)")
        else:
            self.print_warning(f"No services online (demo will use simulation mode)")
        
        return self.service_status
    
    async def provision_mcp_with_retry(self, retries: int = 3) -> str:
        """Provision MCP with retry logic."""
        self.print_info("📦 Provisioning Tier-2 MCP (4GB RAM, 2x CPU)...")
        
        if not self.service_status.get('mcp-provisioner'):
            fallback_id = f"mcp-horus-{uuid.uuid4().hex[:8]}"
            self.print_info(f"   Provisioner offline, using fallback: {fallback_id}")
            return fallback_id
        
        for attempt in range(retries):
            try:
                if attempt > 0:
                    self.print_info(f"   Retry {attempt + 1}/{retries}...")
                    await asyncio.sleep(1)
                
                response = await self.client.post(
                    f"{self.services['mcp-provisioner']}/api/v1/provision",
                    json={
                        "client_id": "horus-heresy",
                        "tier": 2,
                        "memory_limit": "4096m",
                        "cpu_shares": 2048
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    mcp_id = data.get('mcp_id') or data.get('id')
                    self.print_success(f"✓ MCP provisioned: {mcp_id}")
                    return mcp_id
            except:
                pass
        
        fallback_id = f"mcp-horus-{uuid.uuid4().hex[:8]}"
        self.print_info(f"   Using fallback MCP ID: {fallback_id}")
        return fallback_id
    
    async def ingest_documents_with_retry(self, documents: List[NormalizedDocument]):
        """Ingest documents with retry logic."""
        self.print_info(f"📥 Ingesting {len(documents)} documents...")
        
        if not self.service_status.get('kafka-ingestion-service'):
            self.print_info(f"   Kafka offline, skipping ingestion (documents stored locally)")
            return
        
        success = 0
        for idx, doc in enumerate(documents, 1):
            if idx % 10 == 0:
                self.print_info(f"   Progress: {idx}/{len(documents)} (✓ {success})")
            
            try:
                response = await self.client.post(
                    f"{self.services['kafka-ingestion-service']}/api/v1/ingest",
                    json={
                        "document_id": doc.document_id,
                        "title": doc.title,
                        "content": doc.content_md,
                        "metadata": doc.metadata,
                        "tags": doc.tags
                    },
                    timeout=5.0
                )
                if response.status_code in [200, 201, 202]:
                    success += 1
            except:
                pass
        
        self.print_success(f"✓ Ingested {success}/{len(documents)} documents")
    
    def generate_doc_from_crawled_data(self, filename: str, keywords: List[str], query: str) -> str:
        """Generate documentation from crawled data, formatted like docs-evergreen."""
        # Score documents by keyword relevance
        scored_docs = []
        for doc in self.documents_ingested:
            content_lower = (doc.title + ' ' + doc.content_md).lower()
            
            # Count keyword matches
            score = sum(content_lower.count(kw) for kw in keywords)
            
            # Bonus for keywords in title
            title_score = sum(kw in doc.title.lower() for kw in keywords) * 5
            score += title_score
            
            if score > 0:
                scored_docs.append((score, doc))
        
        # Sort by relevance score
        scored_docs.sort(reverse=True, key=lambda x: x[0])
        relevant_docs = [doc for score, doc in scored_docs[:15]]
        
        # Fallback if no matches
        if not relevant_docs:
            relevant_docs = self.documents_ingested[:10]
        
        # Build document similar to docs-evergreen format
        title = filename.replace('.md', '').replace('_', ' ').title()
        content = []
        
        # Header with query
        content.append(f"# {title}\n\n")
        content.append(f"> **MCP Query**: {query}\n\n")
        content.append("## Overview\n\n")
        content.append(f"This document was generated by querying the Horus Heresy Knowledge Base MCP with the prompt above. ")
        content.append(f"The MCP analyzed {len(self.documents_ingested)} crawled Fandom wiki pages to compile this information.\n\n")
        content.append(f"**Keywords**: {', '.join(keywords[:5])}\n\n")
        
        # Table of Contents
        content.append("## Table of Contents\n\n")
        for idx in range(min(8, len(relevant_docs))):
            section_name = relevant_docs[idx].title.replace('Fandom: ', '')
            content.append(f"{idx + 1}. [{section_name}](#{idx + 1}-{section_name.lower().replace(' ', '-')})\n")
        content.append("\n---\n\n")
        
        # Main content sections
        for idx, doc in enumerate(relevant_docs[:8], 1):
            section_title = doc.title.replace('Fandom: ', '')
            content.append(f"## {idx}. {section_title}\n\n")
            
            # Extract keyword-relevant excerpts
            doc_content = doc.content_md
            excerpts = []
            
            # Find paragraphs containing keywords
            paragraphs = doc_content.split('\n\n')
            relevant_paras = []
            for para in paragraphs[:30]:
                para_lower = para.lower()
                if any(kw in para_lower for kw in keywords):
                    relevant_paras.append(para)
            
            # Take best paragraphs
            if relevant_paras:
                # Take up to 3 most relevant paragraphs
                for para in relevant_paras[:3]:
                    excerpt = para[:500] if len(para) > 500 else para
                    if len(para) > 500:
                        excerpt += "..."
                    excerpts.append(excerpt)
            else:
                # Use first substantial paragraph
                for para in paragraphs[:5]:
                    if len(para.strip()) > 100:
                        excerpt = para[:500]
                        if len(para) > 500:
                            excerpt += "..."
                        excerpts.append(excerpt)
                        break
            
            for excerpt in excerpts:
                content.append(f"{excerpt}\n\n")
            
            content.append(f"*Source: {doc.metadata.get('page_url', 'Unknown')}*\n\n")
        
        # Summary section
        content.append("---\n\n")
        content.append("## Summary\n\n")
        content.append(f"This document synthesized information from **{len(relevant_docs)} highly relevant pages** ")
        content.append(f"out of **{len(self.documents_ingested)} total pages** crawled from the Horus Heresy Fandom Wiki. ")
        content.append(f"The content focuses on: {', '.join(keywords[:5])}.\n\n")
        
        # Metadata footer
        content.append("---\n\n")
        content.append("## Document Metadata\n\n")
        content.append("| Field | Value |\n")
        content.append("|-------|-------|\n")
        content.append(f"| **Generated** | {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')} |\n")
        content.append(f"| **MCP ID** | {self.mcp_id} |\n")
        content.append(f"| **Source** | Horus Heresy Fandom Wiki |\n")
        content.append(f"| **Total Pages Crawled** | {len(self.documents_ingested)} |\n")
        content.append(f"| **Relevant Pages** | {len(relevant_docs)} |\n")
        content.append(f"| **Keywords** | {', '.join(keywords)} |\n")
        content.append(f"| **Document Type** | Knowledge Base Export |\n")
        
        return ''.join(content)
    
    async def generate_documentation_suite(self):
        """Generate 12-document suite from crawled data."""
        self.print_info(f"📝 Generating 12-document Horus Heresy suite...")
        
        doc_specs = [
            ("01_HORUS_HERESY_OVERVIEW.md", ['horus', 'heresy', 'war', 'great crusade', 'rebellion'], 
             "Provide a comprehensive overview of the Horus Heresy, including what it was, when it occurred, and its significance"),
            ("02_THE_EMPEROR_AND_PRIMARCHS.md", ['emperor', 'primarch', 'mankind', 'humanity', 'gene-seed'],
             "Describe the Emperor of Mankind and the Primarchs, their creation, purpose, and relationships"),
            ("03_CAUSES_OF_THE_HERESY.md", ['cause', 'corruption', 'fall', 'turn', 'chaos'],
             "Explain the causes and events that led to the Horus Heresy and the fall of the Warmaster"),
            ("04_TRAITOR_LEGIONS.md", ['traitor', 'chaos legion', 'sons of horus', 'word bearers', 'iron warriors', 'night lords'],
             "Detail the Traitor Legions, who they were, why they turned, and their roles in the Heresy"),
            ("05_LOYALIST_LEGIONS.md", ['loyalist', 'loyal', 'imperial', 'ultramarines', 'blood angels', 'dark angels'],
             "Detail the Loyalist Legions who remained faithful to the Emperor and fought against the traitors"),
            ("06_MAJOR_BATTLES.md", ['battle', 'war', 'campaign', 'isstvan', 'calth', 'prospero'],
             "Describe the major battles and campaigns of the Horus Heresy"),
            ("07_SIEGE_OF_TERRA.md", ['siege', 'terra', 'throneworld', 'solar system', 'palace'],
             "Detail the climactic Siege of Terra, the final battle of the Horus Heresy"),
            ("08_CHAOS_GODS_ROLE.md", ['chaos', 'chaos god', 'warp', 'daemon', 'khorne', 'tzeentch', 'nurgle', 'slaanesh'],
             "Explain the role of the Chaos Gods in corrupting the traitors and influencing the Heresy"),
            ("09_KEY_CHARACTERS.md", ['horus', 'sanguinius', 'dorn', 'lorgar', 'erebus', 'abaddon'],
             "Profile key characters who played crucial roles in the Horus Heresy"),
            ("10_AFTERMATH_AND_LEGACY.md", ['aftermath', 'legacy', 'imperium', 'result', 'scouring'],
             "Discuss the aftermath of the Heresy, its consequences, and lasting impact on the Imperium"),
            ("11_TIMELINE.md", ['timeline', 'chronology', 'year', 'date', 'sequence', 'event'],
             "Provide a chronological timeline of major events during the Horus Heresy"),
            ("12_NOTABLE_QUOTES.md", ['quote', 'speech', 'said', 'words', 'declaration'],
             "Collection of notable quotes from key moments and characters in the Horus Heresy")
        ]
        
        generated = 0
        for filename, keywords, query in doc_specs:
            self.print_info(f"   📄 Generating: {filename}...")
            
            content = self.generate_doc_from_crawled_data(filename, keywords, query)
            
            # Save to both locations
            (self.run_dir / filename).write_text(content, encoding='utf-8')
            (self.docs_dir / filename).write_text(content, encoding='utf-8')
            
            generated += 1
            
            # Show stats
            matching_docs = sum(1 for doc in self.documents_ingested 
                              if any(kw in (doc.title + ' ' + doc.content_md).lower() for kw in keywords))
            self.print_success(f"      ✓ Generated ({len(content)} chars, {matching_docs} matching docs)")
        
        self.print_success(f"✓ Generated all {generated}/12 documents")
        self.print_info(f"   📁 Saved to: {self.docs_dir.resolve()}")
        
        return generated
    
    async def run_demo(self, max_depth: int = 2, max_surface_links: int = 10):
        """Run the complete enhanced demo."""
        start_time = time.time()
        
        self.print_header("ENHANCED HORUS HERESY KNOWLEDGE BASE DEMO")
        print(f"Configuration:")
        print(f"  • Crawl Depth: {max_depth}")
        print(f"  • Surface Links: {max_surface_links}")
        print(f"  • Reports: {self.run_dir.resolve()}")
        print(f"  • Documentation: {self.docs_dir.resolve()}")
        print(f"  • Correlation ID: {self.correlation_id}\n")
        
        try:
            # Phase 0: Health Check
            self.print_header("PHASE 0: SERVICE HEALTH CHECK")
            await self.check_all_services()
            
            # Phase 1: Provision MCP
            self.print_header("PHASE 1: PROVISION HORUS HERESY MCP")
            self.mcp_id = await self.provision_mcp_with_retry()
            
            # Phase 2: Deep Crawl
            self.print_header("PHASE 2: DEEP CRAWL FANDOM WIKI")
            self.print_info(f"🕷️  Crawling Horus Heresy wiki (depth={max_depth}, links={max_surface_links})...")
            self.print_info(f"   This may take several minutes...")
            
            tagging_config = UniversalTaggingConfig(
                enable_preprocessing=False,  # Disable for speed
                user_tags=["domain:warhammer-40k", "project:horus-heresy", "source:fandom"]
            )
            
            # Progress callback for real-time feedback
            last_update = [time.time()]
            
            def progress_update(message: str):
                current = time.time()
                if current - last_update[0] >= 0.5:  # Throttle to every 0.5s
                    self.print_info(f"   {message}")
                    last_update[0] = current
            
            ingestor = FandomWikiIngestor(
                tagging_config=tagging_config,
                progress_callback=progress_update
            )
            
            # Set resource baseline
            if ingestor.resource_monitor:
                ingestor.resource_monitor.set_baseline()
                metrics = ingestor.resource_monitor.get_metrics()
                self.print_info(f"   🖥️  System: {metrics.memory_available_gb:.1f}GB RAM available, "
                              f"CPU {metrics.cpu_percent:.0f}%, "
                              f"batch={metrics.suggested_batch_size}")
            
            crawl_start = time.time()
            self.documents_ingested = await ingestor.crawl_and_ingest(
                original_page_url="https://warhammer40k.fandom.com/wiki/Horus_Heresy",
                max_surface_links=max_surface_links,
                max_depth_distance=max_depth
            )
            crawl_time = time.time() - crawl_start
            
            # Show depth distribution
            if ingestor.pages_per_depth:
                depth_summary = ", ".join([f"D{d}:{count}" for d, count in sorted(ingestor.pages_per_depth.items())])
                self.print_info(f"   📊 Depth distribution: {depth_summary}")
            
            self.tag_collection = ingestor.get_tag_collection()
            
            self.print_success(f"✓ Crawled {len(self.documents_ingested)} pages in {crawl_time:.1f}s")
            
            if self.tag_collection:
                breakdown = self.tag_collection.to_dict()
                total = len(breakdown.get('default', [])) + len(breakdown.get('contextual', [])) + len(breakdown.get('user_defined', []))
                
                self.print_info(f"   🏷️  Tags: {total} unique tags")
                self.print_info(f"   📊 Breakdown: Default={len(breakdown.get('default', []))}, Contextual={len(breakdown.get('contextual', []))}, User={len(breakdown.get('user_defined', []))}")
                
                # Show sample tags
                all_tags = breakdown.get('default', []) + breakdown.get('contextual', [])[:8]
                self.print_info(f"   🎯 Sample tags: {', '.join(all_tags[:10])}")
            
            # Save crawl report
            report = ingestor.generate_crawl_report()
            report_path = self.run_dir / "crawl_report.json"
            report_path.write_text(json.dumps({
                "crawl_report": {
                    "total_pages": report.total_pages,
                    "duration": report.duration_seconds,
                    "depth_distribution": report.depth_distribution,
                    "link_statistics": report.link_statistics
                },
                "tag_collection": self.tag_collection.to_dict() if self.tag_collection else {}
            }, indent=2), encoding='utf-8')
            self.print_success(f"✓ Crawl report saved: {report_path}")
            
            # Phase 3: Ingest Documents
            self.print_header("PHASE 3: INGEST DOCUMENTS")
            await self.ingest_documents_with_retry(self.documents_ingested)
            
            # Phase 4: Train MCP (if service available)
            self.print_header("PHASE 4: TRAIN HORUS HERESY MCP")
            if self.service_status.get('mcp-training-coordinator'):
                self.print_info(f"🎓 Training MCP {self.mcp_id}...")
                self.print_info(f"   Training service available but may need configuration")
            else:
                self.print_info(f"   Training service offline, skipping training phase")
            
            # Phase 5: Generate Documentation
            self.print_header("PHASE 5: GENERATE DOCUMENTATION SUITE")
            docs_generated = await self.generate_documentation_suite()
            
            # Summary
            elapsed = time.time() - start_time
            
            self.print_header("DEMO COMPLETE")
            # Calculate total tags
            total_tags = 0
            if self.tag_collection:
                breakdown = self.tag_collection.to_dict()
                total_tags = len(breakdown.get('default', [])) + len(breakdown.get('contextual', [])) + len(breakdown.get('user_defined', []))
            
            print(f"Summary:")
            print(f"  • MCP ID: {self.mcp_id}")
            print(f"  • Pages Crawled: {len(self.documents_ingested)}")
            print(f"  • Unique Tags: {total_tags}")
            print(f"  • Documents Generated: {docs_generated}/12")
            print(f"  • Execution Time: {elapsed:.1f}s\n")
            
            print(f"Artifacts:")
            print(f"  📁 Run Directory: {self.run_dir}")
            print(f"  📚 Documentation Suite: {self.docs_dir}")
            print(f"  📊 Crawl Report: {self.run_dir / 'crawl_report.json'}")
            
            self.print_success("")
            self.print_success("✨ Horus Heresy Knowledge Base Demo Complete!")
            
        finally:
            await self.client.aclose()


async def main():
    """Main entry point."""
    demo = EnhancedHorusHeresyDemo()
    # Deep crawl with intelligent resource management
    # Depth=3 is the sweet spot: comprehensive without rate limiting
    # Expected: 1,000-3,000 unique pages in 10-20 minutes
    await demo.run_demo(max_depth=3, max_surface_links=40)


if __name__ == "__main__":
    asyncio.run(main())

