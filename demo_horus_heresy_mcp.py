#!/usr/bin/env python3
"""
Horus Heresy Knowledge Base MCP Demo

This script demonstrates creating a specialized MCP for Warhammer 40K lore:
1. Provision a high-tier MCP (4GB RAM, 2x CPU)
2. Deep crawl Fandom wiki with intelligent tagging
3. Train specialized domain MCP
4. Generate 12-document comprehensive suite
5. Query and showcase domain expertise

Features:
- Fandom wiki crawling with configurable depth
- Intelligent corpus analysis and tagging
- Knowledge graph building
- Multi-MCP comparison
"""

import asyncio
import httpx
import json
import time
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional


class Colors:
    """Terminal colors for pretty output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class HorusHeresyMCPDemo:
    """Horus Heresy specialized MCP demonstration."""
    
    def __init__(self):
        self.correlation_id = str(uuid.uuid4())
        self.client = httpx.AsyncClient(timeout=90.0)
        
        # Service endpoints
        self.services = {
            "kafka-ingestion-service": "http://localhost:5700",
            "mcp-provisioner": "http://localhost:5400",
            "mcp-training-coordinator": "http://localhost:5600",
            "mcp-registry": "http://localhost:8102",
            "mcp-gateway": "http://localhost:8001",
        }
        
        # Create unique directory for this run
        run_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.run_dir = Path("reports") / f"horus_heresy_{run_timestamp}"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        
        # Results tracking
        self.results = {}
        self.horus_mcp_id = None
        self.documents = []
        self.tag_collection = None
    
    def print_header(self, text: str):
        """Print section header."""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}  {text}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")
    
    def print_info(self, text: str):
        """Print info message."""
        print(f"{Colors.OKBLUE}ℹ️  {text}{Colors.ENDC}")
    
    def print_success(self, text: str):
        """Print success message."""
        print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")
    
    def print_warning(self, text: str):
        """Print warning message."""
        print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")
    
    def print_error(self, text: str):
        """Print error message."""
        print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")
    
    async def provision_horus_mcp(self):
        """Provision a high-tier MCP for Horus Heresy."""
        self.print_header("PHASE 1: PROVISION HORUS HERESY MCP")
        
        self.print_info("📦 Provisioning Tier-2 MCP (4GB RAM, 2x CPU)...")
        
        try:
            response = await self.client.post(
                f"{self.services['mcp-provisioner']}/api/v1/provision",
                json={
                    "client_id": "demo-horus-heresy",
                    "tier": 2,
                    "memory_limit": "4096m",
                    "cpu_shares": 2048
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                self.horus_mcp_id = data.get('mcp_id') or data.get('id')
                self.print_success(f"MCP provisioned: {self.horus_mcp_id}")
                self.results['mcp_id'] = self.horus_mcp_id
                return True
            else:
                self.print_warning(f"Provisioning returned {response.status_code}, using fallback")
                self.horus_mcp_id = f"mcp-horus-{uuid.uuid4().hex[:8]}"
                self.results['mcp_id'] = self.horus_mcp_id
                return True
        
        except Exception as e:
            self.print_error(f"Provisioning failed: {e}")
            self.horus_mcp_id = f"mcp-horus-{uuid.uuid4().hex[:8]}"
            self.results['mcp_id'] = self.horus_mcp_id
            return False
    
    async def crawl_fandom_wiki(self, depth: int = 2, surface_links: int = 10):
        """
        Crawl Horus Heresy Fandom wiki with intelligent tagging.
        
        Args:
            depth: Maximum crawl depth
            surface_links: Maximum links per page
        """
        self.print_header("PHASE 2: DEEP CRAWL FANDOM WIKI")
        
        self.print_info(f"🕷️  Crawling with depth={depth}, surface_links={surface_links}...")
        self.print_info("   This may take several minutes...")
        
        try:
            # Import ingestion modules
            from ingestion.fandom_ingestor import FandomWikiIngestor
            from ingestion.tagging import UniversalTaggingConfig
            
            # Configure intelligent tagging
            tagging_config = UniversalTaggingConfig(
                enable_preprocessing=True,
                preprocessing_sample_size=50,
                min_entity_frequency=3,
                enable_relationships=True,
                enable_knowledge_graph=True,
                user_tags=["domain:warhammer-40k", "project:horus-heresy-kb", "mcp:specialized"]
            )
            
            # Create Fandom ingestor
            ingestor = FandomWikiIngestor(
                tagging_config=tagging_config,
                enable_tagging=True
            )
            
            # Deep crawl
            start_time = time.time()
            self.documents = await ingestor.crawl_and_ingest(
                "https://warhammer40k.fandom.com/wiki/Horus_Heresy",
                max_surface_links=surface_links,
                max_depth_distance=depth
            )
            crawl_time = time.time() - start_time
            
            self.print_success(f"Crawled {len(self.documents)} pages in {crawl_time:.1f}s")
            
            # Get crawl report and tag collection
            crawl_report = ingestor.generate_crawl_report()
            self.tag_collection = ingestor.get_tag_collection()
            
            if self.tag_collection:
                self.print_info(f"   🏷️  Tags: {self.tag_collection.total_count()} unique tags")
                breakdown = self.tag_collection.breakdown()
                self.print_info(f"   📊 Breakdown: Default={breakdown['default']}, Contextual={breakdown['contextual']}, User={breakdown['user_defined']}")
                
                # Print sample contextual tags
                if self.tag_collection.contextual_tags:
                    sample_tags = list(self.tag_collection.contextual_tags)[:10]
                    self.print_info(f"   🎯 Sample tags: {', '.join(sample_tags)}")
            
            # Store results
            self.results['documents_crawled'] = len(self.documents)
            self.results['crawl_time'] = crawl_time
            self.results['tag_collection'] = self.tag_collection.to_dict() if self.tag_collection else {}
            self.results['crawl_report'] = {
                'total_pages': crawl_report.total_pages,
                'duration': crawl_report.duration_seconds,
                'depth_distribution': crawl_report.depth_distribution,
                'link_statistics': crawl_report.link_statistics
            }
            
            # Save crawl report
            report_path = self.run_dir / "crawl_report.json"
            report_path.write_text(json.dumps({
                'crawl_report': self.results['crawl_report'],
                'tag_collection': self.results['tag_collection']
            }, indent=2))
            
            self.print_success(f"Crawl report saved: {report_path}")
            
            return True
        
        except Exception as e:
            self.print_error(f"Crawling failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def ingest_documents(self):
        """Ingest crawled documents into the system."""
        self.print_header("PHASE 3: INGEST DOCUMENTS")
        
        if not self.documents:
            self.print_warning("No documents to ingest")
            return False
        
        self.print_info(f"📥 Ingesting {len(self.documents)} documents...")
        
        ingested_count = 0
        failed_count = 0
        
        for idx, doc in enumerate(self.documents, 1):
            try:
                await self.client.post(
                    f"{self.services['kafka-ingestion-service']}/api/v1/ingest",
                    json={
                        "document_id": doc.document_id,
                        "title": doc.title,
                        "content": doc.content_md,
                        "metadata": doc.metadata,
                        "tags": doc.tags
                    },
                    timeout=10.0
                )
                ingested_count += 1
                
                if idx % 10 == 0:
                    self.print_info(f"   Progress: {idx}/{len(self.documents)}...")
            
            except Exception as e:
                failed_count += 1
                if failed_count == 1:  # Only print first error
                    self.print_warning(f"Document {idx} ingestion failed: {e}")
        
        self.print_success(f"Ingested {ingested_count}/{len(self.documents)} documents ({failed_count} failed)")
        self.results['documents_ingested'] = ingested_count
        self.results['documents_failed'] = failed_count
        
        return ingested_count > 0
    
    async def train_mcp(self):
        """Train Horus Heresy MCP on ingested documents."""
        self.print_header("PHASE 4: TRAIN HORUS HERESY MCP")
        
        if not self.horus_mcp_id:
            self.print_error("No MCP ID available")
            return False
        
        self.print_info(f"🎓 Training MCP {self.horus_mcp_id}...")
        
        try:
            # Create training job
            create_response = await self.client.post(
                f"{self.services['mcp-training-coordinator']}/api/v1/jobs",
                params={"mcp_id": self.horus_mcp_id, "data_sources": ["doc_store"]},
                timeout=30.0
            )
            
            if create_response.status_code == 200:
                job_data = create_response.json()
                job_id = job_data.get('job_id')
                self.print_success(f"Training job created: {job_id}")
                
                # Execute training
                exec_response = await self.client.post(
                    f"{self.services['mcp-training-coordinator']}/api/v1/jobs/{job_id}/execute",
                    timeout=60.0
                )
                
                if exec_response.status_code == 200:
                    self.print_success(f"Training initiated successfully")
                    self.results['training_job_id'] = job_id
                    return True
                else:
                    self.print_warning(f"Training execution returned {exec_response.status_code}")
                    return False
            else:
                self.print_warning(f"Training job creation returned {create_response.status_code}")
                return False
        
        except Exception as e:
            self.print_error(f"Training failed: {e}")
            return False
    
    async def generate_documentation_suite(self):
        """Generate 12-document Horus Heresy suite."""
        self.print_header("PHASE 5: GENERATE DOCUMENTATION SUITE")
        
        doc_topics = [
            ("01_HORUS_HERESY_OVERVIEW.md", "Provide a comprehensive overview of the Horus Heresy"),
            ("02_THE_EMPEROR_AND_PRIMARCHS.md", "Describe the Emperor of Mankind and the Primarchs"),
            ("03_CAUSES_OF_THE_HERESY.md", "Explain what led to Horus's betrayal"),
            ("04_TRAITOR_LEGIONS.md", "Detail the nine Traitor Legions"),
            ("05_LOYALIST_LEGIONS.md", "Detail the nine Loyalist Legions"),
            ("06_MAJOR_BATTLES.md", "Chronicle the major battles of the Horus Heresy"),
            ("07_SIEGE_OF_TERRA.md", "Describe the Siege of Terra in detail"),
            ("08_CHAOS_GODS_ROLE.md", "Explain the role of the Chaos Gods"),
            ("09_KEY_CHARACTERS.md", "Profile key characters beyond the Primarchs"),
            ("10_AFTERMATH_AND_LEGACY.md", "Describe the aftermath and lasting effects"),
            ("11_TIMELINE.md", "Provide a chronological timeline"),
            ("12_NOTABLE_QUOTES.md", "Compile memorable quotes"),
        ]
        
        self.print_info(f"📝 Generating {len(doc_topics)} documents...")
        
        docs_dir = self.run_dir / "documentation_suite"
        docs_dir.mkdir(exist_ok=True)
        
        docs_generated = 0
        
        for filename, query in doc_topics:
            self.print_info(f"   Generating: {filename}...")
            
            try:
                # Query MCP via gateway
                response = await self.client.post(
                    f"{self.services['mcp-gateway']}/api/v1/query",
                    json={
                        "mcp_id": self.horus_mcp_id,
                        "query": query,
                        "correlation_id": self.correlation_id
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get('response') or data.get('answer', '[No content generated]')
                    
                    # Write document
                    doc_path = docs_dir / filename
                    doc_content = f"""# {filename.replace('_', ' ').replace('.md', '')}

{content}

---

**Generated by Horus Heresy MCP**: `{self.horus_mcp_id}`  
**Query**: {query}  
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Tags**: {', '.join(list(self.tag_collection.contextual_tags)[:5]) if self.tag_collection else 'N/A'}
"""
                    doc_path.write_text(doc_content)
                    
                    docs_generated += 1
                    self.print_success(f"   ✅ {filename} ({len(content)} chars)")
                else:
                    self.print_warning(f"   ⚠️  {filename} - Query returned {response.status_code}")
                    # Write placeholder
                    doc_path = docs_dir / filename
                    doc_path.write_text(f"# {filename}\n\n[Content could not be generated - Status {response.status_code}]\n")
            
            except Exception as e:
                self.print_warning(f"   ⚠️  {filename} failed: {e}")
                doc_path = docs_dir / filename
                doc_path.write_text(f"# {filename}\n\n[Content could not be generated - Error: {e}]\n")
        
        self.print_success(f"Generated {docs_generated}/{len(doc_topics)} documents")
        self.results['docs_generated'] = docs_generated
        self.results['docs_dir'] = str(docs_dir)
        
        return docs_generated > 0
    
    async def run_demo(self, crawl_depth: int = 2, surface_links: int = 10):
        """
        Run complete Horus Heresy MCP demo.
        
        Args:
            crawl_depth: Crawl depth (default 2, max 50)
            surface_links: Surface links per page (default 10, max 50)
        """
        start_time = time.time()
        
        self.print_header("HORUS HERESY KNOWLEDGE BASE MCP DEMO")
        print(f"{Colors.BOLD}Configuration:{Colors.ENDC}")
        print(f"  • Crawl Depth: {crawl_depth}")
        print(f"  • Surface Links: {surface_links}")
        print(f"  • Run Directory: {self.run_dir}")
        print(f"  • Correlation ID: {self.correlation_id}\n")
        
        try:
            # Phase 1: Provision MCP
            success = await self.provision_horus_mcp()
            if not success:
                self.print_warning("Continuing with fallback MCP ID...")
            
            # Phase 2: Crawl Fandom wiki
            success = await self.crawl_fandom_wiki(depth=crawl_depth, surface_links=surface_links)
            if not success:
                self.print_error("Crawling failed - cannot continue")
                return
            
            # Phase 3: Ingest documents
            success = await self.ingest_documents()
            if not success:
                self.print_warning("Ingestion had issues - continuing...")
            
            # Phase 4: Train MCP
            success = await self.train_mcp()
            if not success:
                self.print_warning("Training had issues - continuing...")
            
            # Phase 5: Generate documentation suite
            success = await self.generate_documentation_suite()
            if not success:
                self.print_warning("Documentation generation had issues")
            
            # Final summary
            elapsed_time = time.time() - start_time
            
            self.print_header("DEMO COMPLETE")
            print(f"{Colors.BOLD}Summary:{Colors.ENDC}")
            print(f"  • MCP ID: {self.horus_mcp_id}")
            print(f"  • Documents Crawled: {self.results.get('documents_crawled', 0)}")
            print(f"  • Documents Ingested: {self.results.get('documents_ingested', 0)}")
            print(f"  • Documents Generated: {self.results.get('docs_generated', 0)}")
            print(f"  • Unique Tags: {self.results.get('tag_collection', {}).get('total', 0)}")
            print(f"  • Execution Time: {elapsed_time:.1f}s")
            print(f"\n{Colors.BOLD}Artifacts:{Colors.ENDC}")
            print(f"  📁 Run Directory: {self.run_dir}")
            print(f"  📝 Documentation Suite: {self.results.get('docs_dir', 'N/A')}")
            print(f"  📊 Crawl Report: {self.run_dir / 'crawl_report.json'}")
            
            # Save final results
            results_path = self.run_dir / "demo_results.json"
            results_path.write_text(json.dumps(self.results, indent=2, default=str))
            print(f"  📄 Results: {results_path}")
            
            self.print_success("\n✅ Horus Heresy MCP Demo Complete!")
        
        except Exception as e:
            self.print_error(f"Demo failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await self.client.aclose()


async def main():
    """Main entry point."""
    import sys
    
    # Parse command line arguments
    crawl_depth = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    surface_links = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    demo = HorusHeresyMCPDemo()
    await demo.run_demo(crawl_depth=crawl_depth, surface_links=surface_links)


if __name__ == "__main__":
    asyncio.run(main())

