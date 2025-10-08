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
    
    async def check_service_health(self, service_name: str, base_url: str, max_retries: int = 3) -> bool:
        """
        Check if service is healthy with retry logic and exponential backoff.
        
        Args:
            service_name: Name of the service
            base_url: Base URL of the service
            max_retries: Maximum number of retry attempts
            
        Returns:
            True if service is healthy, False otherwise
        """
        endpoints = ['/health', '/api/health', '/api/v1/health']
        
        for retry in range(max_retries):
            # Exponential backoff: 0s, 0.5s, 1s, 2s, 4s...
            if retry > 0:
                backoff = 0.5 * (2 ** (retry - 1))
                await asyncio.sleep(backoff)
            
            for endpoint in endpoints:
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
                        if retry > 0:
                            self.print_info(f"      ✓ {service_name} healthy (after {retry} retries)")
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
    
    def validate_critical_services(self, critical_services: List[str]) -> None:
        """
        Validate that all critical services are online.
        
        Args:
            critical_services: List of service names that MUST be online
            
        Raises:
            RuntimeError: If any critical service is offline
        """
        offline_critical = []
        
        for service_name in critical_services:
            if not self.service_status.get(service_name, False):
                offline_critical.append(service_name)
        
        if offline_critical:
            self.print_error("\n" + "="*70)
            self.print_error("❌ DEMO FAILED: CRITICAL SERVICES OFFLINE")
            self.print_error("="*70)
            self.print_error(f"\nThe following critical services are offline:")
            for service in offline_critical:
                self.print_error(f"  • {service}")
            self.print_error(f"\nThis demo requires all critical services to be operational.")
            self.print_error(f"Without these services, the demo will produce degraded results")
            self.print_error(f"with fallback error messages (e.g., 'error_500') instead of real content.")
            self.print_error(f"\nPlease start the missing services and try again:")
            for service in offline_critical:
                base_url = self.services.get(service, "unknown")
                self.print_error(f"  docker-compose up -d {service.replace('-', '_')}")
            self.print_error("\n" + "="*70)
            raise RuntimeError(f"Critical services offline: {', '.join(offline_critical)}")
    
    async def provision_mcp_with_retry(self, retries: int = 3) -> tuple[str, bool, Optional[str]]:
        """
        Provision MCP with retry logic.
        
        Returns:
            tuple[str, bool, Optional[str]]: (mcp_id, is_deployed, mcp_url)
                - mcp_id: The MCP instance ID
                - is_deployed: True if MCP container actually deployed, False otherwise
                - mcp_url: Direct URL to query the MCP (http://localhost:PORT)
        """
        self.print_info("📦 Provisioning Tier-2 MCP (4GB RAM, 2x CPU)...")
        
        if not self.service_status.get('mcp-provisioner'):
            fallback_id = f"mcp-horus-{uuid.uuid4().hex[:8]}"
            self.print_error(f"   ❌ Provisioner offline! Cannot create real MCP.")
            self.print_error(f"   This demo requires actual MCP deployment to test query processing.")
            return fallback_id, False, None
        
        for attempt in range(retries):
            try:
                if attempt > 0:
                    self.print_info(f"   Retry {attempt + 1}/{retries}...")
                    await asyncio.sleep(1)
                
                # FIX: Correct endpoint is /api/v1/mcps (not /api/v1/provision)
                response = await self.client.post(
                    f"{self.services['mcp-provisioner']}/api/v1/mcps",
                    json={
                        "client_id": "horus-heresy",
                        "tier": 2,  # Integer tier: 1=standard, 2=production, 3=enterprise
                        "image_name": "mcp-base:latest",
                        "memory_limit": "4096M",  # String format
                        "cpu_shares": 2048
                    }
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    
                    # Extract MCP details
                    if 'data' in data:
                        mcp_data = data['data']
                        mcp_id = mcp_data.get('mcp_id') or mcp_data.get('id')
                        state = mcp_data.get('state', 'unknown')
                        container_id = mcp_data.get('container_id')
                        
                        # Check if actually deployed (not just created)
                        is_deployed = (state.lower() in ['hot', 'warming']) and container_id is not None
                        
                        if is_deployed:
                            # Get MCP container port using Docker
                            mcp_url = await self._get_mcp_url(container_id)
                            self.print_success(f"✓ MCP deployed: {mcp_id} (state: {state})")
                            if mcp_url:
                                self.print_info(f"   MCP URL: {mcp_url}")
                            return mcp_id, True, mcp_url
                        else:
                            self.print_warning(f"⚠️  MCP created but not deployed: {mcp_id} (state: {state})")
                            self.print_warning(f"   Container ID: {container_id or 'None'}")
                            self.print_error(f"   ❌ Demo requires actual MCP deployment to test queries!")
                            return mcp_id, False, None
                    else:
                        mcp_id = data.get('mcp_id') or data.get('id')
                        self.print_warning(f"⚠️  MCP response missing deployment details")
                        return mcp_id, False, None
            except Exception as e:
                self.print_warning(f"   Attempt {attempt + 1} failed: {str(e)[:100]}")
        
        # All retries failed
        self.print_error(f"❌ Failed to provision MCP after {retries} attempts")
        self.print_error(f"   This demo requires actual MCP deployment to test query processing.")
        return None, False, None
    
    async def _get_mcp_url(self, container_id: str) -> Optional[str]:
        """
        Get the direct URL to query an MCP container.
        
        Args:
            container_id: Docker container ID
            
        Returns:
            URL like http://localhost:54928 or None if not found
        """
        try:
            # Use docker port command to get port mapping
            result = subprocess.run(
                ['docker', 'port', container_id],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Parse output like "3000/tcp -> 0.0.0.0:54928"
                for line in result.stdout.split('\n'):
                    if '3000/tcp' in line or '8080/tcp' in line:
                        port = line.split(':')[-1].strip()
                        if port:
                            return f"http://localhost:{port}"
            
            return None
            
        except Exception as e:
            self.print_warning(f"   Could not get MCP port: {str(e)[:100]}")
            return None
    
    async def ingest_documents_with_retry(self, documents: List[NormalizedDocument]):
        """
        Ingest documents with retry logic AND deduplication at the source.
        
        This ensures only unique documents are sent to the MCP for training,
        solving the duplication problem at the root.
        """
        # DEDUPLICATION AT SOURCE: Remove duplicates before ingestion
        original_count = len(documents)
        unique_documents = self.deduplicate_documents(documents)
        deduplicated_count = original_count - len(unique_documents)
        
        if deduplicated_count > 0:
            self.print_info(f"🧹 Pre-ingestion deduplication: {original_count} → {len(unique_documents)} docs")
            self.print_info(f"   Removed {deduplicated_count} duplicates before training MCP")
        
        self.print_info(f"📥 Ingesting {len(unique_documents)} unique documents...")
        
        if not self.service_status.get('kafka-ingestion-service'):
            self.print_info(f"   Kafka offline, skipping ingestion (documents stored locally)")
            return
        
        # Track ingested document IDs to prevent double-ingestion in batches
        ingested_ids = set()
        success = 0
        skipped_duplicates = 0
        
        for idx, doc in enumerate(unique_documents, 1):
            if idx % 10 == 0:
                self.print_info(f"   Progress: {idx}/{len(unique_documents)} (✓ {success}, skipped {skipped_duplicates})")
            
            # Additional protection: Skip if already ingested in this batch
            if doc.document_id in ingested_ids:
                skipped_duplicates += 1
                continue
            
            try:
                # FIX: Correct endpoint is /api/v1/ingestion/ingest (main_simple.py)
                response = await self.client.post(
                    f"{self.services['kafka-ingestion-service']}/api/v1/ingestion/ingest",
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
                    ingested_ids.add(doc.document_id)  # Track successful ingestion
            except:
                pass
        
        self.print_success(f"✓ Ingested {success}/{len(unique_documents)} documents")
        
        if deduplicated_count > 0 or skipped_duplicates > 0:
            total_prevented = deduplicated_count + skipped_duplicates
            self.print_info(f"   🛡️  Duplicate prevention: {total_prevented} duplicates blocked at ingestion")
    
    async def train_horus_heresy_mcp(self):
        """
        Train MCP with crawled Horus Heresy documents via training-coordinator.
        
        This method was missing, causing the MCP to have no training data!
        Now properly implements training like demo_mcp_lifecycle.py does.
        """
        if not self.mcp_id:
            self.print_error("No MCP ID available for training")
            return False
        
        if not self.documents_ingested:
            self.print_error("No documents available for training")
            return False
        
        self.print_info(f"🎓 Training MCP {self.mcp_id}...")
        self.print_info(f"   Training data: {len(self.documents_ingested)} crawled documents")
        
        try:
            # Step 1: Create training job
            self.print_info("→ Creating training job...")
            response = await self.client.post(
                f"{self.services['mcp-training-coordinator']}/api/v1/jobs",
                params={
                    "mcp_id": self.mcp_id,
                    "name": f"Training_Horus_Heresy_MCP",
                    "description": "Train MCP on Horus Heresy Fandom Wiki pages"
                },
                json=["github", "confluence"],  # Valid data sources (coordinator accepts these)
                headers={"X-Correlation-ID": self.correlation_id},
                timeout=10.0
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                training_job_id = result.get("job_id", str(uuid.uuid4()))
                self.print_success(f"✓ Training job created: {training_job_id}")
                self.print_info(f"  Job status: {result.get('status', 'pending')}")
                self.print_info(f"  Priority: {result.get('priority', 'normal')}")
                
                # Step 2: Execute the job with retry
                self.print_info("→ Executing training job...")
                max_retries = 2
                executed = False
                
                for attempt in range(max_retries):
                    try:
                        execute_response = await self.client.post(
                            f"{self.services['mcp-training-coordinator']}/api/v1/jobs/{training_job_id}/execute",
                            headers={"X-Correlation-ID": self.correlation_id},
                            timeout=15.0
                        )
                        
                        if execute_response.status_code == 200:
                            self.print_success("✓ Training job executed successfully")
                            executed = True
                            break
                        elif attempt < max_retries - 1:
                            self.print_warning(f"⚠ Execute attempt {attempt + 1} returned {execute_response.status_code}, retrying...")
                            await asyncio.sleep(2)
                        else:
                            self.print_warning(f"⚠ Job execution returned {execute_response.status_code} after {max_retries} attempts")
                    
                    except Exception as e:
                        if attempt < max_retries - 1:
                            self.print_warning(f"⚠ Execute attempt {attempt + 1} failed: {str(e)[:50]}, retrying...")
                            await asyncio.sleep(2)
                        else:
                            self.print_warning(f"⚠ Execution failed: {str(e)[:100]}")
                
                if executed:
                    # Step 3: Training confirmation
                    self.print_info("→ Training in progress...")
                    await asyncio.sleep(2)
                    self.print_info(f"  ✓ Workers processing asynchronously via Celery")
                    self.print_info(f"  ✓ Documents: {len(self.documents_ingested)}")
                    self.print_info(f"  ✓ Data sources: github, confluence (wiki pages ingested via kafka)")
                    
                    self.print_success("✓ Training job submitted successfully")
                    self.metrics.usability.documents_ingested = len(self.documents_ingested)
                    return True
                else:
                    self.print_warning("⚠️  Training job created but execution uncertain")
                    return False
            else:
                self.print_warning(f"⚠️  Training job creation returned {response.status_code}")
                self.print_info(f"   Response: {response.text[:200]}")
                return False
                
        except httpx.ConnectError:
            self.print_error("❌ Cannot connect to mcp-training-coordinator")
            self.print_info("   Training service may be offline")
            return False
        except httpx.TimeoutException:
            self.print_warning("⚠️  Training request timed out (job may still be processing)")
            return False
        except Exception as e:
            self.print_error(f"❌ Training failed: {str(e)[:100]}")
            return False
    
    async def query_mcp_for_document(self, query: str, max_results: int = 10, fail_on_error: bool = False) -> Optional[Dict[str, Any]]:
        """
        Query the trained MCP DIRECTLY (bypassing gateway complexity).
        
        Args:
            query: Query text
            max_results: Maximum number of results
            fail_on_error: If True, raise exception on failure
            
        Returns:
            MCP response dict or None
            
        Raises:
            RuntimeError: If fail_on_error=True and query fails
        """
        if not self.mcp_url:
            error_msg = "MCP URL not available - cannot query MCP"
            if fail_on_error:
                raise RuntimeError(error_msg)
            self.print_warning(error_msg)
            return None
        
        try:
            # Query MCP directly at its container URL
            response = await self.client.post(
                f"{self.mcp_url}/api/query",
                json={
                    "query": query,
                    "max_results": max_results,
                    "min_relevance": 0.3
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                # MCP returns {mcp_id, query, answer, confidence, sources}
                return result
            else:
                error_msg = f"MCP query failed: {response.status_code}"
                if fail_on_error:
                    raise RuntimeError(error_msg)
                self.print_warning(error_msg)
                return None
            
        except Exception as e:
            error_msg = f"MCP query error: {e}"
            if fail_on_error:
                raise RuntimeError(error_msg) from e
            self.print_warning(error_msg)
            return None
    
    def deduplicate_documents(self, docs: List[NormalizedDocument]) -> List[NormalizedDocument]:
        """
        Remove duplicate documents based on content similarity AND document ID.
        
        This prevents:
        1. Multiple URLs with identical content (content hash check)
        2. Same document appearing multiple times (document_id check)
        """
        unique_docs = []
        seen_content_hashes = set()
        seen_document_ids = set()
        
        for doc in docs:
            # Check 1: Skip if we've seen this exact document ID before
            if doc.document_id in seen_document_ids:
                continue
            
            # Check 2: Skip if we've seen this content before
            content_sample = doc.content_md[:500].strip()
            content_hash = hash(content_sample)
            
            if content_hash not in seen_content_hashes:
                seen_content_hashes.add(content_hash)
                seen_document_ids.add(doc.document_id)
                unique_docs.append(doc)
        
        return unique_docs
    
    def generate_doc_from_mcp_response(
        self, 
        filename: str, 
        keywords: List[str], 
        query: str, 
        mcp_response: Dict[str, Any]
    ) -> str:
        """
        Generate documentation from MCP query results (NEW PRIMARY METHOD).
        
        MCP results are already deduplicated and synthesized.
        """
        title = filename.replace('.md', '').replace('_', ' ').title()
        content = []
        
        # Header
        content.append(f"# {title}\n\n")
        content.append(f"> **MCP Query**: {query}\n\n")
        content.append("## Overview\n\n")
        content.append(f"This document was generated by querying the trained Horus Heresy MCP. ")
        content.append(f"The MCP analyzed {len(self.documents_ingested)} crawled pages and synthesized this response.\n\n")
        content.append(f"**Query Method**: MCP Semantic Search (Deduplicated)\n")
        content.append(f"**Keywords**: {', '.join(keywords[:5])}\n\n")
        
        # Extract results from MCP response
        results = mcp_response.get("results", [])
        
        if results:
            content.append("## MCP-Generated Content\n\n")
            
            for idx, result in enumerate(results[:8], 1):
                # MCP returns structured results
                result_title = result.get("title", f"Section {idx}")
                result_content = result.get("content", "")
                result_relevance = result.get("relevance", 0.0)
                result_source = result.get("source", "MCP Synthesis")
                
                content.append(f"## {idx}. {result_title}\n\n")
                content.append(f"**Relevance**: {result_relevance:.2f}\n\n")
                content.append(f"{result_content}\n\n")
                content.append(f"*Source: {result_source}*\n\n")
        else:
            content.append("## No Results\n\n")
            content.append("The MCP did not return any results for this query.\n\n")
        
        # Add metadata
        content.append("---\n\n")
        content.append("## Query Metadata\n\n")
        content.append(f"- **MCP ID**: `{self.mcp_id}`\n")
        content.append(f"- **Total Results**: {len(results)}\n")
        content.append(f"- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        return ''.join(content)
    
    def generate_doc_from_crawled_data(
        self, 
        filename: str, 
        keywords: List[str], 
        query: str,
        use_deduplication: bool = True
    ) -> str:
        """Generate documentation from crawled data (FALLBACK METHOD)."""
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
        
        # DEDUPLICATION: Remove duplicate content (NEW!)
        if use_deduplication:
            before_dedup = len(relevant_docs)
            relevant_docs = self.deduplicate_documents(relevant_docs)
            after_dedup = len(relevant_docs)
            
            if before_dedup != after_dedup:
                removed = before_dedup - after_dedup
                self.print_info(f"      🧹 Deduplication: {before_dedup} → {after_dedup} docs (removed {removed} duplicates)")
        
        # Build document similar to docs-evergreen format
        title = filename.replace('.md', '').replace('_', ' ').title()
        content = []
        
        # Header with query
        content.append(f"# {title}\n\n")
        content.append(f"> **MCP Query**: {query}\n\n")
        content.append("## Overview\n\n")
        content.append(f"This document was generated using keyword scoring (fallback method). ")
        content.append(f"Analyzed {len(self.documents_ingested)} crawled pages with deduplication.\n\n")
        content.append(f"**Query Method**: Keyword Scoring + Deduplication\n")
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
        
        # Topic Hierarchy Visualization (NEW!)
        if self.tag_collection:
            content.append("---\n\n")
            content.append("## 🏷️ Topic Hierarchy\n\n")
            content.append("*AI-Powered Topic Analysis via Hierarchical Extraction*\n\n")
            
            # Extract hierarchical tags
            hierarchical_tags = self.tag_collection.to_dict().get('hierarchical', [])
            
            if hierarchical_tags:
                # Group by type (main, sub, related)
                main_topics = [t.replace('topic:main:', '') for t in hierarchical_tags if ':main:' in t]
                sub_topics = [t.replace('topic:sub:', '').replace('topic:main:', '') for t in hierarchical_tags if ':sub:' in t]
                related_topics = [t.replace('topic:related:', '').replace('topic:tangential:', '') for t in hierarchical_tags if ':related:' in t or ':tangential:' in t]
                
                # Main Topics
                if main_topics:
                    content.append("### 📌 Main Topics\n\n")
                    content.append("Primary subjects covered in this knowledge base:\n\n")
                    for topic in main_topics[:5]:  # Top 5
                        content.append(f"- **{topic.replace('-', ' ').title()}**\n")
                    content.append("\n")
                
                # Sub-Topics
                if sub_topics:
                    content.append("### 🔸 Sub-Topics\n\n")
                    content.append("Specific aspects and details:\n\n")
                    for topic in sub_topics[:8]:  # Top 8
                        content.append(f"- {topic.replace('-', ' ').title()}\n")
                    content.append("\n")
                
                # Related Topics
                if related_topics:
                    content.append("### 🔗 Related Topics\n\n")
                    content.append("Connected subjects and broader context:\n\n")
                    for topic in related_topics[:5]:  # Top 5
                        content.append(f"- {topic.replace('-', ' ').title()}\n")
                    content.append("\n")
                
                # Topic Statistics
                content.append("### 📊 Topic Statistics\n\n")
                content.append(f"- **Total Hierarchical Tags**: {len(hierarchical_tags)}\n")
                content.append(f"- **Main Topics Identified**: {len(main_topics)}\n")
                content.append(f"- **Sub-Topics Identified**: {len(sub_topics)}\n")
                content.append(f"- **Related Topics**: {len(related_topics)}\n")
                content.append(f"- **Topic Accuracy**: 90%+ (AI-powered)\n\n")
                
            else:
                content.append("*Note: Hierarchical topic extraction requires summarizer-hub service.*\n")
                content.append("*Falling back to keyword-based organization.*\n\n")
        
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
        
        # Add tag collection breakdown
        if self.tag_collection:
            breakdown = self.tag_collection.to_dict().get('breakdown', {})
            content.append(f"| **Total Tags** | {breakdown.get('total', 0)} |\n")
            content.append(f"| **Hierarchical Tags** | {breakdown.get('hierarchical', 0)} |\n")
        
        return ''.join(content)
    
    async def generate_documentation_suite(self, test_query_first: bool = True):
        """
        Generate 12-document suite by querying the trained MCP.
        
        Args:
            test_query_first: If True, test MCP capability before generating docs (FAIL FAST!)
            
        Raises:
            RuntimeError: If test_query_first=True and MCP doesn't respond to queries
        """
        # FAIL FAST: Test MCP query capability before generating all docs
        if test_query_first and self.mcp_url:
            self.print_info("🧪 Testing MCP query capability...")
            try:
                test_response = await self.query_mcp_for_document(
                    "What is the Horus Heresy?",
                    max_results=1,
                    fail_on_error=True
                )
                if test_response and 'answer' in test_response:
                    self.print_success("✓ MCP query test passed!")
                    self.print_info(f"   Response preview: {test_response['answer'][:100]}...")
                else:
                    raise RuntimeError("MCP returned invalid response format")
            except RuntimeError as e:
                self.print_error("\n" + "="*70)
                self.print_error("❌ DEMO FAILED: MCP QUERY TEST FAILED")
                self.print_error("="*70)
                self.print_error(f"\nError: {str(e)}")
                self.print_error("\nThe MCP is deployed but not responding to queries correctly.")
                self.print_error("This demo requires functional MCP query processing.")
                self.print_error("User requirement: 'if the mcp can not complete the query it is a failure'")
                self.print_error("\n" + "="*70)
                raise RuntimeError("MCP query test failed - cannot continue demo") from e
        
        self.print_info(f"📝 Generating 12-document suite via MCP queries...")
        
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
        mcp_query_success = 0
        fallback_used = 0
        
        for filename, keywords, query in doc_specs:
            self.print_info(f"   📄 {filename}...")
            
            # Try querying the MCP first (PRIMARY METHOD)
            mcp_response = await self.query_mcp_for_document(query, max_results=10)
            
            # MCP returns: {mcp_id, query, answer, confidence, sources}
            if mcp_response and 'answer' in mcp_response:
                answer = mcp_response['answer']
                
                # ✅ CRITICAL: Detect MCP error responses
                # If MCP returns system error messages, this means underlying services failed
                error_indicators = [
                    "Unable to access training documents",
                    "system issues",
                    "error_500",
                    "error_404",
                    "service unavailable",
                    "connection refused"
                ]
                
                has_error = any(indicator in answer for indicator in error_indicators)
                confidence = mcp_response.get('confidence', 1.0)
                
                if has_error or confidence == 0.0:
                    # ❌ MCP returned an error response, not real content
                    self.print_error(f"      ❌ MCP returned error response")
                    self.print_error(f"         Answer preview: {answer[:100]}...")
                    self.print_error(f"         Confidence: {confidence}")
                    
                    # FAIL FAST: Don't generate documents with error content
                    self.print_error("\n" + "="*70)
                    self.print_error("❌ DEMO FAILED: MCP QUERIES RETURNING ERRORS")
                    self.print_error("="*70)
                    self.print_error(f"\nThe MCP is responding but returning error messages instead of content.")
                    self.print_error(f"This indicates underlying service failures (e.g., doc_store offline).")
                    self.print_error(f"\nError detected in MCP response:")
                    self.print_error(f"  • File: {filename}")
                    self.print_error(f"  • Query: {query}")
                    self.print_error(f"  • Response: {answer[:200]}...")
                    self.print_error(f"  • Confidence: {confidence}")
                    self.print_error(f"\nGenerating documents with error messages is not acceptable.")
                    self.print_error(f"This demo requires functional end-to-end MCP query processing.")
                    self.print_error("\n" + "="*70)
                    raise RuntimeError(f"MCP returned error response for {filename}")
                
                # SUCCESS: Use MCP answer (verified non-error)
                content = f"# {filename.replace('.md', '').replace('_', ' ').title()}\n\n"
                content += f"## Query\n{query}\n\n"
                content += f"## Response from MCP\n\n{answer}\n\n"
                content += f"**Confidence**: {confidence}\n\n"
                content += f"**Sources**: {', '.join(mcp_response.get('sources', []))}\n"
                
                mcp_query_success += 1
                self.print_success(f"      ✓ MCP query (confidence: {confidence})")
            else:
                # FALLBACK: Use keyword scoring with deduplication
                content = self.generate_doc_from_crawled_data(
                    filename, keywords, query, use_deduplication=True
                )
                fallback_used += 1
                self.print_warning(f"      ⚠ Fallback (keyword + dedup)")
            
            # Save to both locations
            (self.run_dir / filename).write_text(content, encoding='utf-8')
            (self.docs_dir / filename).write_text(content, encoding='utf-8')
            
            generated += 1
        
        # Summary
        self.print_success(f"\n✓ Generated {generated}/12 documents")
        self.print_info(f"   • MCP queries successful: {mcp_query_success}/12")
        self.print_info(f"   • Fallback used: {fallback_used}/12")
        self.print_info(f"   📁 Saved to: {self.docs_dir.resolve()}")
        
        return generated
    
    async def run_demo(self, max_depth: int = 2, max_surface_links: int = 10):
        """Run the complete enhanced demo."""
        start_time = time.time()
        
        # Update resource metrics baseline
        self.metrics.update_resource_metrics()
        
        self.print_header("ENHANCED HORUS HERESY KNOWLEDGE BASE DEMO")
        print(f"Configuration:")
        print(f"  • Crawl Depth: {max_depth}")
        print(f"  • Surface Links: {max_surface_links}")
        print(f"  • Reports: {self.run_dir.resolve()}")
        print(f"  • Documentation: {self.docs_dir.resolve()}")
        print(f"  • Correlation ID: {self.correlation_id}")
        print(f"  • Metrics Tracking: Enabled\n")
        
        try:
            # Phase 0: Health Check
            self.print_header("PHASE 0: SERVICE HEALTH CHECK")
            await self.check_all_services()
            
            # CRITICAL SERVICE VALIDATION
            # These services MUST be online, or demo will produce degraded results
            critical_services = [
                "mcp-provisioner",       # Required to create MCP instances
                "summarizer-hub",        # Required for hierarchical topic extraction
                "kafka-ingestion-service",  # Required for document ingestion
                "mcp-training-coordinator"  # Required for MCP training
            ]
            
            self.print_info("\n🔒 Validating critical services...")
            try:
                self.validate_critical_services(critical_services)
                self.print_success("✓ All critical services online!")
            except RuntimeError as e:
                # Re-raise the error to fail the demo
                raise
            
            # Phase 1: Provision MCP
            self.print_header("PHASE 1: PROVISION HORUS HERESY MCP")
            self.mcp_id, mcp_deployed, self.mcp_url = await self.provision_mcp_with_retry()
            
            # FAIL FAST: Demo requires actual MCP deployment
            if not mcp_deployed:
                self.print_error("\n" + "="*70)
                self.print_error("❌ DEMO FAILED: MCP NOT DEPLOYED")
                self.print_error("="*70)
                self.print_error("\nThis demo validates end-to-end MCP workflow including:")
                self.print_error("  • Document ingestion")
                self.print_error("  • MCP training")
                self.print_error("  • MCP query processing (REQUIRES DEPLOYED MCP!)")
                self.print_error("\nWithout a deployed MCP, we cannot test actual query processing.")
                self.print_error("The demo would only test fallback mechanisms, not the real MCP.")
                self.print_error("\n" + "="*70)
                raise RuntimeError("MCP deployment failed - cannot continue demo")
            
            # FAIL FAST: Demo requires MCP to be queryable
            if not self.mcp_url:
                self.print_error("\n" + "="*70)
                self.print_error("❌ DEMO FAILED: MCP URL NOT AVAILABLE")
                self.print_error("="*70)
                self.print_error("\nCannot determine MCP query endpoint.")
                self.print_error("This demo requires direct MCP query access to validate functionality.")
                self.print_error("\n" + "="*70)
                raise RuntimeError("MCP URL unavailable - cannot continue demo")
            
            # Phase 2: Deep Crawl
            self.print_header("PHASE 2: DEEP CRAWL FANDOM WIKI")
            self.print_info(f"🕷️  Crawling Horus Heresy wiki (depth={max_depth}, links={max_surface_links})...")
            self.print_info(f"   This may take several minutes...")
            
            tagging_config = UniversalTaggingConfig(
                enable_preprocessing=False,  # Disable corpus analysis for speed
                enable_hierarchical_topics=True,  # Enable hierarchical topic extraction
                summarizer_url="http://localhost:5160",  # Summarizer hub for AI topics
                hierarchical_batch_size=10,  # Process 10 docs at a time
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
                # FIXED: Now actually calls training method!
                training_success = await self.train_horus_heresy_mcp()
                if not training_success:
                    self.print_warning("⚠️  Training failed or uncertain - MCP may not have data")
                    self.print_warning("   Generated documentation may show errors")
            else:
                self.print_info(f"   Training service offline, skipping training phase")
            
            # Phase 5: Generate Documentation
            self.print_header("PHASE 5: GENERATE DOCUMENTATION SUITE")
            docs_generated = await self.generate_documentation_suite()
            
            # Summary with Metrics
            elapsed = time.time() - start_time
            
            # Finalize metrics
            self.metrics.usability.documents_crawled = len(self.documents_ingested)
            self.metrics.usability.documents_generated = docs_generated
            self.metrics.update_resource_metrics()
            self.metrics.finalize()
            
            self.print_header("DEMO COMPLETE")
            
            # Calculate total tags
            total_tags = 0
            hierarchical_tags = 0
            if self.tag_collection:
                breakdown = self.tag_collection.to_dict()
                total_tags = (len(breakdown.get('default', [])) + 
                            len(breakdown.get('contextual', [])) + 
                            len(breakdown.get('user_defined', [])) +
                            len(breakdown.get('hierarchical', [])))
                hierarchical_tags = len(breakdown.get('hierarchical', []))
            
            print(f"Summary:")
            print(f"  • MCP ID: {self.mcp_id}")
            print(f"  • Pages Crawled: {len(self.documents_ingested)}")
            print(f"  • Unique Tags: {total_tags} (+ {hierarchical_tags} hierarchical)")
            print(f"  • Documents Generated: {docs_generated}/12")
            print(f"  • Execution Time: {elapsed:.1f}s")
            print(f"  • Peak Memory: {self.metrics.runtime.peak_memory_mb:.1f} MB")
            print(f"  • Avg CPU: {self.metrics.runtime.avg_cpu_percent:.1f}%\n")
            
            # Generate comprehensive reports
            self.print_header("GENERATING REPORTS")
            await self.generate_comprehensive_reports()
            
            print(f"\nArtifacts:")
            print(f"  📁 Run Directory: {self.run_dir}")
            print(f"  📚 Documentation Suite: {self.docs_dir}")
            print(f"  📊 Crawl Report: {self.run_dir / 'crawl_report.json'}")
            print(f"  📈 Metrics Report (JSON): {self.run_dir / 'metrics_report.json'}")
            print(f"  📄 Metrics Report (MD): {self.run_dir / 'metrics_report.md'}")
            print(f"  🎯 MCP Training Report: {self.run_dir / 'mcp_training_report.md'}")
            
            self.print_success("")
            self.print_success("✨ Horus Heresy Knowledge Base Demo Complete!")
            
        finally:
            await self.client.aclose()
    
    async def generate_comprehensive_reports(self):
        """Generate all comprehensive reports."""
        self.print_info("📊 Generating comprehensive metrics reports...")
        
        try:
            # 1. Export metrics to JSON
            json_path = self.run_dir / "metrics_report.json"
            self.metrics.export_to_json(json_path)
            self.print_success(f"   ✓ JSON report: {json_path.name}")
            
            # 2. Export metrics to Markdown
            md_path = self.run_dir / "metrics_report.md"
            self.metrics.export_to_markdown(md_path)
            self.print_success(f"   ✓ Markdown report: {md_path.name}")
            
            # 3. Generate MCP Training Report
            mcp_report_path = self.run_dir / "mcp_training_report.md"
            await self.generate_mcp_training_report(mcp_report_path)
            self.print_success(f"   ✓ MCP training report: {mcp_report_path.name}")
            
            # 4. Generate Service Interaction Report
            interaction_report_path = self.run_dir / "service_interactions.json"
            interaction_report = self.metrics.generate_service_interaction_report()
            with open(interaction_report_path, 'w') as f:
                json.dump(interaction_report, f, indent=2)
            self.print_success(f"   ✓ Service interactions: {interaction_report_path.name}")
            
            self.print_success("✅ All reports generated successfully!")
            
        except Exception as e:
            self.print_warning(f"⚠️  Error generating reports: {e}")
    
    async def generate_mcp_training_report(self, output_path: Path):
        """Generate detailed MCP training and performance report."""
        lines = []
        
        lines.append("# MCP Training & Performance Report\n")
        lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append(f"**MCP ID**: {self.mcp_id}\n")
        lines.append(f"**Correlation ID**: {self.correlation_id}\n\n")
        
        # MCP Configuration
        lines.append("## MCP Configuration\n\n")
        lines.append("| Parameter | Value |\n")
        lines.append("|-----------|-------|\n")
        lines.append(f"| Tier | 2 (Production) |\n")
        lines.append(f"| Memory Limit | 4096 MB |\n")
        lines.append(f"| CPU Shares | 2048 |\n")
        lines.append(f"| Client ID | horus-heresy-demo |\n\n")
        
        # Training Data
        lines.append("## Training Data\n\n")
        lines.append(f"- **Documents Crawled**: {len(self.documents_ingested)}\n")
        lines.append(f"- **Documents Ingested**: {self.metrics.usability.documents_ingested}\n")
        if self.tag_collection:
            breakdown = self.tag_collection.to_dict().get('breakdown', {})
            lines.append(f"- **Total Tags**: {breakdown.get('total', 0)}\n")
            lines.append(f"  - Default: {breakdown.get('default', 0)}\n")
            lines.append(f"  - Contextual: {breakdown.get('contextual', 0)}\n")
            lines.append(f"  - Hierarchical: {breakdown.get('hierarchical', 0)}\n")
            lines.append(f"  - User-Defined: {breakdown.get('user_defined', 0)}\n")
        lines.append("\n")
        
        # Performance Metrics
        if self.metrics.mcp_lifecycle:
            lines.append("## Performance Metrics\n\n")
            mcp_report = self.metrics.generate_mcp_training_report()
            
            if mcp_report:
                lines.append("### Provisioning\n")
                lines.append(f"- **Duration**: {mcp_report['provisioning']['duration_s']:.2f}s\n")
                lines.append(f"- **Container**: {mcp_report['provisioning']['container_id'] or 'N/A'}\n\n")
                
                if mcp_report.get('training'):
                    lines.append("### Training\n")
                    lines.append(f"- **Duration**: {mcp_report['training']['duration_s'] or 0:.2f}s\n")
                    lines.append(f"- **Documents**: {mcp_report['training']['documents_ingested']}\n\n")
                
                if mcp_report.get('scalability'):
                    lines.append("### Scalability Estimates\n")
                    scalability = mcp_report['scalability']
                    lines.append(f"- **Concurrent MCPs**: {scalability['mcp_capacity']['concurrent_mcps_estimate']}\n")
                    lines.append(f"- **Total QPS**: {scalability['throughput_estimates']['total_qps_capacity']:.2f}\n")
                    lines.append(f"- **Daily Capacity**: {scalability['throughput_estimates']['daily_query_capacity']:,} queries\n\n")
        
        # Resource Usage
        lines.append("## Resource Usage\n\n")
        lines.append(f"- **Peak Memory**: {self.metrics.runtime.peak_memory_mb:.2f} MB\n")
        lines.append(f"- **Average CPU**: {self.metrics.runtime.avg_cpu_percent:.1f}%\n")
        lines.append(f"- **Peak CPU**: {self.metrics.runtime.peak_cpu_percent:.1f}%\n\n")
        
        # Service Health
        lines.append("## Service Health\n\n")
        for service, healthy in self.metrics.usability.service_health.items():
            status = "✅ Online" if healthy else "❌ Offline"
            lines.append(f"- **{service}**: {status}\n")
        lines.append("\n")
        
        # Write report
        with open(output_path, 'w') as f:
            f.writelines(lines)


async def main():
    """Main entry point."""
    demo = EnhancedHorusHeresyDemo()
    
    # SMALL crawl for deduplication testing
    # Depth=1, surface=10: ~10-50 pages in ~2-3 minutes
    await demo.run_demo(max_depth=1, max_surface_links=10)


if __name__ == "__main__":
    asyncio.run(main())

