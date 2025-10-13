#!/usr/bin/env python3
"""
Ecosystem MCP Audit & Ingestion Script

This script performs a comprehensive audit of the ecosystem-mcp service,
ingests .md documents in batches of 10, and records detailed metrics for
RAG-based queries.

Usage:
    python audit_and_ingest.py --base-url http://localhost:8000

Features:
- Service health check and API audit
- Batch ingestion of .md documents (10 per batch)
- Metrics collection for ingestion process
- RAG query performance testing
- Comprehensive audit report generation
"""

import asyncio
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import argparse
import sys
import signal

import httpx


@dataclass
class IngestionMetrics:
    """Metrics for document ingestion."""
    batch_number: int
    documents_count: int
    start_time: float
    end_time: float
    duration_seconds: float
    success: bool
    error: Optional[str] = None
    job_id: Optional[str] = None


@dataclass
class QueryMetrics:
    """Metrics for RAG queries."""
    query_number: int
    question: str
    start_time: float
    end_time: float
    duration_seconds: float
    success: bool
    answer_length: int
    sources_count: int
    confidence: float
    error: Optional[str] = None


@dataclass
class ServiceAudit:
    """Service audit information."""
    service_name: str
    version: str
    status: str
    endpoints: List[Dict[str, Any]]
    health_status: Dict[str, Any]
    document_count: int
    timestamp: str


class EcosystemMCPAuditor:
    """Auditor for ecosystem-mcp service."""
    
    def __init__(self, base_url: str = "http://localhost:8000", query_timeout: int = 60):
        """
        Initialize the auditor.
        
        Args:
            base_url: Base URL of the ecosystem-mcp service
            query_timeout: Timeout for individual RAG queries in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=300.0)  # 5 minute timeout for HTTP
        self.query_timeout = query_timeout  # Timeout for individual queries
        self.ingestion_metrics: List[IngestionMetrics] = []
        self.query_metrics: List[QueryMetrics] = []
        self.audit_data: Optional[ServiceAudit] = None
        
        # Test queries for RAG evaluation
        self.test_queries = [
            "What is ecosystem-mcp and what does it do?",
            "How does the ingestion pipeline work?",
            "What are the main features of the RAG system?",
            "How is document versioning handled?",
            "What models are used for embeddings?",
            "How does the caching system work?",
            "What are the rate limits for API endpoints?",
            "How does the 3-tier LLM routing work?",
            "What is the deployment architecture?",
            "How are errors handled in the ingestion pipeline?"
        ]
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()
    
    async def audit_service(self) -> ServiceAudit:
        """
        Audit the ecosystem-mcp service.
        
        Returns:
            Service audit data
        """
        print(f"\n{'='*80}")
        print("ECOSYSTEM MCP SERVICE AUDIT")
        print(f"{'='*80}\n")
        
        # Check service health
        print("🔍 Checking service health...")
        health = await self._check_health()
        print(f"   Status: {health.get('status', 'unknown')}")
        
        # Get service info
        print("\n🔍 Getting service information...")
        about = await self._get_about_me()
        print(f"   Service: {about.get('service', 'unknown')}")
        print(f"   Version: {about.get('version', 'unknown')}")
        
        # List endpoints
        print("\n🔍 Listing API endpoints...")
        endpoints = await self._list_endpoints()
        print(f"   Total endpoints: {len(endpoints)}")
        
        # Get document count
        print("\n🔍 Checking document count...")
        doc_count = await self._get_document_count()
        print(f"   Documents in database: {doc_count}")
        
        self.audit_data = ServiceAudit(
            service_name=about.get('service', 'ecosystem-mcp'),
            version=about.get('version', 'unknown'),
            status=health.get('status', 'unknown'),
            endpoints=endpoints,
            health_status=health,
            document_count=doc_count,
            timestamp=datetime.utcnow().isoformat()
        )
        
        print(f"\n{'='*80}")
        print("✅ Service audit complete")
        print(f"{'='*80}\n")
        
        return self.audit_data
    
    async def _check_health(self) -> Dict[str, Any]:
        """Check service health."""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"   ⚠️ Warning: Health check failed: {e}")
            return {"status": "unknown", "error": str(e)}
    
    async def _get_about_me(self) -> Dict[str, Any]:
        """Get service information."""
        try:
            response = await self.client.get(f"{self.base_url}/about-me")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"   ⚠️ Warning: About-me failed: {e}")
            return {"service": "unknown", "version": "unknown"}
    
    async def _list_endpoints(self) -> List[Dict[str, Any]]:
        """List all API endpoints."""
        try:
            response = await self.client.get(f"{self.base_url}/endpoints")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"   ⚠️ Warning: Endpoint listing failed: {e}")
            return []
    
    async def _get_document_count(self) -> int:
        """Get total document count."""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/documents",
                params={"limit": 1, "offset": 0}
            )
            response.raise_for_status()
            data = response.json()
            return data.get('total', 0)
        except Exception as e:
            print(f"   ⚠️ Warning: Document count failed: {e}")
            return 0
    
    async def find_markdown_files(self, repo_path: Path) -> List[Path]:
        """
        Find all .md files in the repository.
        
        Args:
            repo_path: Path to repository
            
        Returns:
            List of markdown file paths
        """
        print(f"\n🔍 Finding .md files in {repo_path}...")
        
        md_files = list(repo_path.rglob("*.md"))
        
        # Filter out some common non-documentation files
        excluded_patterns = [
            '.pytest_cache',
            'node_modules',
            'venv',
            '__pycache__',
            '.git'
        ]
        
        filtered_files = [
            f for f in md_files
            if not any(pattern in str(f) for pattern in excluded_patterns)
        ]
        
        print(f"   Found {len(filtered_files)} .md files (filtered from {len(md_files)} total)")
        
        return filtered_files
    
    async def ingest_documents_in_batches(
        self,
        documents: List[Path],
        batch_size: int = 10,
        wait_for_completion: bool = True
    ) -> List[IngestionMetrics]:
        """
        Ingest documents in batches.
        
        Args:
            documents: List of document paths
            batch_size: Number of documents per batch
            
        Returns:
            List of ingestion metrics
        """
        print(f"\n{'='*80}")
        print(f"DOCUMENT INGESTION (Batch Size: {batch_size})")
        print(f"{'='*80}\n")
        
        print(f"📦 Total documents: {len(documents)}")
        print(f"📦 Batch size: {batch_size}")
        print(f"📦 Total batches: {(len(documents) + batch_size - 1) // batch_size}\n")
        
        # Create batches
        batches = [
            documents[i:i + batch_size]
            for i in range(0, len(documents), batch_size)
        ]
        
        for batch_idx, batch in enumerate(batches, start=1):
            print(f"\n{'─'*80}")
            print(f"Batch {batch_idx}/{len(batches)}: Processing {len(batch)} documents")
            print(f"{'─'*80}")
            
            start_time = time.time()
            
            try:
                # Create temporary directory with symbolic links to batch files
                # This allows us to ingest only specific files
                temp_batch_dir = Path(f"/tmp/ecosystem-mcp-batch-{batch_idx}")
                temp_batch_dir.mkdir(parents=True, exist_ok=True)
                
                # Copy or link files to temp directory
                for doc in batch:
                    dest = temp_batch_dir / doc.name
                    if not dest.exists():
                        dest.write_text(doc.read_text())
                    print(f"   📄 {doc.name}")
                
                # Start ingestion job
                print(f"\n   🚀 Starting ingestion job...")
                response = await self.client.post(
                    f"{self.base_url}/api/v1/admin/ingest",
                    json={
                        "repo_path": str(temp_batch_dir),
                        "mode": "quick"
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                job_id = result.get('job_id')
                print(f"   ✅ Job created: {job_id}")
                
                # Wait for job completion (with timeout) if requested
                completed = True
                if wait_for_completion:
                    print(f"   ⏳ Waiting for job completion...")
                    completed = await self._wait_for_job_completion(job_id, timeout=300)
                else:
                    print(f"   ⏭️  Skipping wait for job completion")
                
                end_time = time.time()
                duration = end_time - start_time
                
                metrics = IngestionMetrics(
                    batch_number=batch_idx,
                    documents_count=len(batch),
                    start_time=start_time,
                    end_time=end_time,
                    duration_seconds=duration,
                    success=completed,
                    job_id=job_id
                )
                
                self.ingestion_metrics.append(metrics)
                
                print(f"\n   ✅ Batch {batch_idx} complete in {duration:.2f}s")
                
                # Clean up temp directory
                import shutil
                shutil.rmtree(temp_batch_dir, ignore_errors=True)
                
                # Rate limiting - wait between batches
                if batch_idx < len(batches):
                    await asyncio.sleep(2)
                
            except Exception as e:
                end_time = time.time()
                duration = end_time - start_time
                
                print(f"\n   ❌ Batch {batch_idx} failed: {e}")
                
                metrics = IngestionMetrics(
                    batch_number=batch_idx,
                    documents_count=len(batch),
                    start_time=start_time,
                    end_time=end_time,
                    duration_seconds=duration,
                    success=False,
                    error=str(e)
                )
                
                self.ingestion_metrics.append(metrics)
        
        print(f"\n{'='*80}")
        print("✅ All batches processed")
        print(f"{'='*80}\n")
        
        return self.ingestion_metrics
    
    async def _wait_for_job_completion(self, job_id: str, timeout: int = 300) -> bool:
        """
        Wait for ingestion job to complete.
        
        Args:
            job_id: Job ID
            timeout: Timeout in seconds
            
        Returns:
            True if job completed successfully, False otherwise
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = await self.client.get(
                    f"{self.base_url}/api/v1/admin/ingest/{job_id}"
                )
                response.raise_for_status()
                job = response.json()
                
                status = job.get('status', 'unknown')
                
                if status == 'completed':
                    return True
                elif status == 'failed':
                    print(f"      ❌ Job failed: {job.get('error_message', 'unknown error')}")
                    return False
                elif status in ['queued', 'processing']:
                    # Still processing
                    await asyncio.sleep(5)
                else:
                    print(f"      ⚠️ Unknown status: {status}")
                    await asyncio.sleep(5)
                    
            except Exception as e:
                print(f"      ⚠️ Error checking job status: {e}")
                await asyncio.sleep(5)
        
        print(f"      ⏱️ Timeout waiting for job completion")
        return False
    
    async def run_rag_queries(self) -> List[QueryMetrics]:
        """
        Run RAG queries and collect metrics.
        
        Returns:
            List of query metrics
        """
        print(f"\n{'='*80}")
        print("RAG QUERY PERFORMANCE TESTING")
        print(f"{'='*80}\n")
        
        print(f"📊 Running {len(self.test_queries)} test queries...\n")
        
        for idx, question in enumerate(self.test_queries, start=1):
            print(f"\n{'─'*80}")
            print(f"Query {idx}/{len(self.test_queries)}")
            print(f"{'─'*80}")
            print(f"❓ Question: {question}")
            print(f"⏱️  Timeout: {self.query_timeout}s")
            
            start_time = time.time()
            
            try:
                # Create progress indicator task
                progress_task = asyncio.create_task(self._show_query_progress(start_time))
                
                # Execute query with timeout
                try:
                    response = await asyncio.wait_for(
                        self.client.post(
                            f"{self.base_url}/api/v1/ask",
                            json={
                                "question": question,
                                "n_results": 10,
                                "prefer_recent": True,
                                "temperature": 0.7
                            }
                        ),
                        timeout=self.query_timeout
                    )
                    
                    # Cancel progress indicator
                    progress_task.cancel()
                    try:
                        await progress_task
                    except asyncio.CancelledError:
                        pass
                    
                    response.raise_for_status()
                    result = response.json()
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    answer = result.get('answer', '')
                    sources = result.get('sources', [])
                    confidence = result.get('confidence', 0.0)
                    
                    print(f"\n✅ Answer ({len(answer)} chars, {duration:.2f}s):")
                    print(f"   {answer[:200]}..." if len(answer) > 200 else f"   {answer}")
                    print(f"\n📚 Sources: {len(sources)}")
                    print(f"🎯 Confidence: {confidence:.2f}")
                    
                    metrics = QueryMetrics(
                        query_number=idx,
                        question=question,
                        start_time=start_time,
                        end_time=end_time,
                        duration_seconds=duration,
                        success=True,
                        answer_length=len(answer),
                        sources_count=len(sources),
                        confidence=confidence
                    )
                    
                    self.query_metrics.append(metrics)
                    
                except asyncio.TimeoutError:
                    # Cancel progress indicator
                    progress_task.cancel()
                    try:
                        await progress_task
                    except asyncio.CancelledError:
                        pass
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    print(f"\n⏱️ Query timed out after {duration:.2f}s (limit: {self.query_timeout}s)")
                    
                    metrics = QueryMetrics(
                        query_number=idx,
                        question=question,
                        start_time=start_time,
                        end_time=end_time,
                        duration_seconds=duration,
                        success=False,
                        answer_length=0,
                        sources_count=0,
                        confidence=0.0,
                        error=f"Timeout after {duration:.2f}s"
                    )
                    
                    self.query_metrics.append(metrics)
                
                # Rate limiting - shorter wait for efficiency
                await asyncio.sleep(2)
                
            except Exception as e:
                end_time = time.time()
                duration = end_time - start_time
                
                print(f"\n❌ Query failed: {e}")
                
                metrics = QueryMetrics(
                    query_number=idx,
                    question=question,
                    start_time=start_time,
                    end_time=end_time,
                    duration_seconds=duration,
                    success=False,
                    answer_length=0,
                    sources_count=0,
                    confidence=0.0,
                    error=str(e)
                )
                
                self.query_metrics.append(metrics)
        
        print(f"\n{'='*80}")
        print("✅ RAG query testing complete")
        print(f"{'='*80}\n")
        
        # Print summary
        successful = sum(1 for m in self.query_metrics if m.success)
        failed = sum(1 for m in self.query_metrics if not m.success)
        timeouts = sum(1 for m in self.query_metrics if not m.success and "Timeout" in str(m.error))
        
        print(f"📊 Query Summary:")
        print(f"   Total: {len(self.query_metrics)}")
        print(f"   Successful: {successful} ({successful/len(self.query_metrics)*100:.1f}%)" if self.query_metrics else "   Successful: 0")
        print(f"   Failed: {failed}")
        if timeouts > 0:
            print(f"   Timeouts: {timeouts} ⏱️")
        print()
        
        return self.query_metrics
    
    async def _show_query_progress(self, start_time: float):
        """
        Show progress indicator while query is running.
        
        Args:
            start_time: Query start time
        """
        try:
            # Wait a bit before showing progress (fast queries don't need it)
            await asyncio.sleep(3)
            
            print(f"\n   ⏳ Processing", end='', flush=True)
            
            while True:
                elapsed = time.time() - start_time
                print(f".", end='', flush=True)
                
                # Show elapsed time every 5 seconds
                if int(elapsed) % 5 == 0 and int(elapsed) > 0:
                    print(f" [{elapsed:.0f}s]", end='', flush=True)
                
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            # Query completed, clean up progress line
            print()  # New line after dots
            raise
    
    def generate_report(self, output_dir: Path) -> Dict[str, Any]:
        """
        Generate comprehensive audit report.
        
        Args:
            output_dir: Directory to save reports
            
        Returns:
            Report summary
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        print(f"\n{'='*80}")
        print("GENERATING AUDIT REPORT")
        print(f"{'='*80}\n")
        
        # Calculate statistics
        ingestion_stats = self._calculate_ingestion_stats()
        query_stats = self._calculate_query_stats()
        
        # Create comprehensive report
        report = {
            "audit_timestamp": timestamp,
            "service_audit": asdict(self.audit_data) if self.audit_data else {},
            "ingestion_summary": ingestion_stats,
            "query_summary": query_stats,
            "ingestion_metrics": [asdict(m) for m in self.ingestion_metrics],
            "query_metrics": [asdict(m) for m in self.query_metrics]
        }
        
        # Save full report as JSON
        report_file = output_dir / f"audit_report_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Full report saved: {report_file}")
        
        # Generate markdown summary
        md_file = output_dir / f"audit_summary_{timestamp}.md"
        self._generate_markdown_summary(md_file, report, ingestion_stats, query_stats)
        
        print(f"📄 Markdown summary saved: {md_file}")
        
        # Print summary to console
        self._print_summary(ingestion_stats, query_stats)
        
        return report
    
    def _calculate_ingestion_stats(self) -> Dict[str, Any]:
        """Calculate ingestion statistics."""
        if not self.ingestion_metrics:
            return {}
        
        successful = [m for m in self.ingestion_metrics if m.success]
        failed = [m for m in self.ingestion_metrics if not m.success]
        
        total_docs = sum(m.documents_count for m in self.ingestion_metrics)
        total_duration = sum(m.duration_seconds for m in self.ingestion_metrics)
        
        return {
            "total_batches": len(self.ingestion_metrics),
            "successful_batches": len(successful),
            "failed_batches": len(failed),
            "total_documents": total_docs,
            "total_duration_seconds": total_duration,
            "average_batch_duration": total_duration / len(self.ingestion_metrics) if self.ingestion_metrics else 0,
            "documents_per_second": total_docs / total_duration if total_duration > 0 else 0,
            "success_rate": len(successful) / len(self.ingestion_metrics) * 100 if self.ingestion_metrics else 0
        }
    
    def _calculate_query_stats(self) -> Dict[str, Any]:
        """Calculate query statistics."""
        if not self.query_metrics:
            return {}
        
        successful = [m for m in self.query_metrics if m.success]
        failed = [m for m in self.query_metrics if not m.success]
        
        total_duration = sum(m.duration_seconds for m in self.query_metrics)
        avg_duration = total_duration / len(self.query_metrics) if self.query_metrics else 0
        
        avg_answer_length = sum(m.answer_length for m in successful) / len(successful) if successful else 0
        avg_sources = sum(m.sources_count for m in successful) / len(successful) if successful else 0
        avg_confidence = sum(m.confidence for m in successful) / len(successful) if successful else 0
        
        return {
            "total_queries": len(self.query_metrics),
            "successful_queries": len(successful),
            "failed_queries": len(failed),
            "total_duration_seconds": total_duration,
            "average_query_duration": avg_duration,
            "min_query_duration": min(m.duration_seconds for m in self.query_metrics) if self.query_metrics else 0,
            "max_query_duration": max(m.duration_seconds for m in self.query_metrics) if self.query_metrics else 0,
            "average_answer_length": avg_answer_length,
            "average_sources_count": avg_sources,
            "average_confidence": avg_confidence,
            "success_rate": len(successful) / len(self.query_metrics) * 100 if self.query_metrics else 0
        }
    
    def _generate_markdown_summary(
        self,
        output_file: Path,
        report: Dict[str, Any],
        ingestion_stats: Dict[str, Any],
        query_stats: Dict[str, Any]
    ):
        """Generate markdown summary report."""
        content = f"""# Ecosystem MCP Service Audit Report

**Generated**: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}

## Service Information

- **Service**: {report['service_audit'].get('service_name', 'unknown')}
- **Version**: {report['service_audit'].get('version', 'unknown')}
- **Status**: {report['service_audit'].get('status', 'unknown')}
- **Documents in Database**: {report['service_audit'].get('document_count', 0)}
- **API Endpoints**: {len(report['service_audit'].get('endpoints', []))}

## Ingestion Metrics

### Summary

- **Total Batches**: {ingestion_stats.get('total_batches', 0)}
- **Successful Batches**: {ingestion_stats.get('successful_batches', 0)}
- **Failed Batches**: {ingestion_stats.get('failed_batches', 0)}
- **Total Documents Processed**: {ingestion_stats.get('total_documents', 0)}
- **Success Rate**: {ingestion_stats.get('success_rate', 0):.1f}%

### Performance

- **Total Duration**: {ingestion_stats.get('total_duration_seconds', 0):.2f} seconds
- **Average Batch Duration**: {ingestion_stats.get('average_batch_duration', 0):.2f} seconds
- **Throughput**: {ingestion_stats.get('documents_per_second', 0):.2f} documents/second

## RAG Query Metrics

### Summary

- **Total Queries**: {query_stats.get('total_queries', 0)}
- **Successful Queries**: {query_stats.get('successful_queries', 0)}
- **Failed Queries**: {query_stats.get('failed_queries', 0)}
- **Success Rate**: {query_stats.get('success_rate', 0):.1f}%

### Performance

- **Total Duration**: {query_stats.get('total_duration_seconds', 0):.2f} seconds
- **Average Query Duration**: {query_stats.get('average_query_duration', 0):.2f} seconds
- **Min Query Duration**: {query_stats.get('min_query_duration', 0):.2f} seconds
- **Max Query Duration**: {query_stats.get('max_query_duration', 0):.2f} seconds

### Quality

- **Average Answer Length**: {query_stats.get('average_answer_length', 0):.0f} characters
- **Average Sources**: {query_stats.get('average_sources_count', 0):.1f} sources per query
- **Average Confidence**: {query_stats.get('average_confidence', 0):.2f}

## Detailed Batch Metrics

| Batch | Documents | Duration (s) | Status | Job ID |
|-------|-----------|--------------|--------|--------|
"""
        
        for m in self.ingestion_metrics:
            status = "✅" if m.success else "❌"
            content += f"| {m.batch_number} | {m.documents_count} | {m.duration_seconds:.2f} | {status} | {m.job_id or 'N/A'} |\n"
        
        content += """
## Detailed Query Metrics

| # | Question | Duration (s) | Sources | Confidence | Status |
|---|----------|--------------|---------|------------|--------|
"""
        
        for m in self.query_metrics:
            status = "✅" if m.success else "❌"
            question_short = m.question[:50] + "..." if len(m.question) > 50 else m.question
            content += f"| {m.query_number} | {question_short} | {m.duration_seconds:.2f} | {m.sources_count} | {m.confidence:.2f} | {status} |\n"
        
        content += """
## Conclusion

This audit provides comprehensive insights into the ecosystem-mcp service's performance,
including document ingestion efficiency and RAG query quality. The metrics can be used
to identify optimization opportunities and track improvements over time.

### Key Findings

"""
        
        # Add key findings based on metrics
        if ingestion_stats.get('success_rate', 0) == 100:
            content += "- ✅ All ingestion batches completed successfully\n"
        else:
            content += f"- ⚠️ Ingestion success rate: {ingestion_stats.get('success_rate', 0):.1f}%\n"
        
        if query_stats.get('success_rate', 0) == 100:
            content += "- ✅ All RAG queries completed successfully\n"
        else:
            content += f"- ⚠️ Query success rate: {query_stats.get('success_rate', 0):.1f}%\n"
        
        if query_stats.get('average_confidence', 0) >= 0.7:
            content += f"- ✅ High average confidence: {query_stats.get('average_confidence', 0):.2f}\n"
        else:
            content += f"- ⚠️ Lower average confidence: {query_stats.get('average_confidence', 0):.2f}\n"
        
        if query_stats.get('average_query_duration', 0) < 5.0:
            content += f"- ✅ Fast query response time: {query_stats.get('average_query_duration', 0):.2f}s\n"
        else:
            content += f"- ⚠️ Slower query response time: {query_stats.get('average_query_duration', 0):.2f}s\n"
        
        output_file.write_text(content)
    
    def _print_summary(self, ingestion_stats: Dict[str, Any], query_stats: Dict[str, Any]):
        """Print summary to console."""
        print(f"\n{'='*80}")
        print("AUDIT SUMMARY")
        print(f"{'='*80}\n")
        
        print("📊 INGESTION METRICS")
        print(f"   Batches: {ingestion_stats.get('total_batches', 0)} total, "
              f"{ingestion_stats.get('successful_batches', 0)} successful, "
              f"{ingestion_stats.get('failed_batches', 0)} failed")
        print(f"   Documents: {ingestion_stats.get('total_documents', 0)} total")
        print(f"   Duration: {ingestion_stats.get('total_duration_seconds', 0):.2f}s total, "
              f"{ingestion_stats.get('average_batch_duration', 0):.2f}s per batch")
        print(f"   Throughput: {ingestion_stats.get('documents_per_second', 0):.2f} docs/second")
        print(f"   Success Rate: {ingestion_stats.get('success_rate', 0):.1f}%")
        
        print("\n📊 RAG QUERY METRICS")
        print(f"   Queries: {query_stats.get('total_queries', 0)} total, "
              f"{query_stats.get('successful_queries', 0)} successful, "
              f"{query_stats.get('failed_queries', 0)} failed")
        print(f"   Duration: {query_stats.get('average_query_duration', 0):.2f}s average "
              f"({query_stats.get('min_query_duration', 0):.2f}s min, "
              f"{query_stats.get('max_query_duration', 0):.2f}s max)")
        print(f"   Answer Length: {query_stats.get('average_answer_length', 0):.0f} chars average")
        print(f"   Sources: {query_stats.get('average_sources_count', 0):.1f} per query")
        print(f"   Confidence: {query_stats.get('average_confidence', 0):.2f} average")
        print(f"   Success Rate: {query_stats.get('success_rate', 0):.1f}%")
        
        print(f"\n{'='*80}\n")


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Audit ecosystem-mcp service")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of ecosystem-mcp service"
    )
    parser.add_argument(
        "--repo-path",
        default="/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp",
        help="Path to repository to scan for .md files"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of documents per batch"
    )
    parser.add_argument(
        "--output-dir",
        default="./audit_results",
        help="Directory to save audit reports"
    )
    parser.add_argument(
        "--skip-ingestion",
        action="store_true",
        help="Skip document ingestion"
    )
    parser.add_argument(
        "--skip-queries",
        action="store_true",
        help="Skip RAG queries"
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Don't wait for ingestion jobs to complete"
    )
    parser.add_argument(
        "--query-timeout",
        type=int,
        default=60,
        help="Timeout for individual RAG queries in seconds (default: 60)"
    )
    parser.add_argument(
        "--max-queries",
        type=int,
        default=10,
        help="Maximum number of RAG queries to run (default: 10)"
    )
    
    args = parser.parse_args()
    
    repo_path = Path(args.repo_path)
    output_dir = Path(args.output_dir)
    
    if not repo_path.exists():
        print(f"❌ Repository path does not exist: {repo_path}")
        sys.exit(1)
    
    async with EcosystemMCPAuditor(args.base_url, query_timeout=args.query_timeout) as auditor:
        try:
            # Step 1: Audit service
            await auditor.audit_service()
            
            # Step 2: Ingest documents
            if not args.skip_ingestion:
                md_files = await auditor.find_markdown_files(repo_path)
                if md_files:
                    await auditor.ingest_documents_in_batches(
                        md_files,
                        batch_size=args.batch_size,
                        wait_for_completion=not args.no_wait
                    )
                else:
                    print("⚠️ No markdown files found to ingest")
            
            # Step 3: Run RAG queries
            if not args.skip_queries:
                # Limit number of queries if specified
                if args.max_queries < len(auditor.test_queries):
                    original_queries = auditor.test_queries.copy()
                    auditor.test_queries = auditor.test_queries[:args.max_queries]
                    print(f"\n⚠️ Running {args.max_queries} of {len(original_queries)} test queries")
                
                await auditor.run_rag_queries()
            
            # Step 4: Generate report
            report = auditor.generate_report(output_dir)
            
            print(f"\n✅ Audit complete! Reports saved to {output_dir}")
            
        except KeyboardInterrupt:
            print("\n\n⚠️ Audit interrupted by user")
            print("\n📊 Partial results collected:")
            print(f"   Ingestion batches: {len(auditor.ingestion_metrics)}")
            print(f"   RAG queries: {len(auditor.query_metrics)}")
            
            # Try to save partial results
            if auditor.ingestion_metrics or auditor.query_metrics:
                try:
                    print(f"\n💾 Saving partial results to {output_dir}...")
                    auditor.generate_report(output_dir)
                    print("✅ Partial results saved")
                except Exception as save_error:
                    print(f"⚠️ Could not save partial results: {save_error}")
            
            sys.exit(130)  # Standard exit code for SIGINT
        except Exception as e:
            print(f"\n\n❌ Audit failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Try to save any results we have
            if auditor and (auditor.ingestion_metrics or auditor.query_metrics):
                try:
                    print(f"\n💾 Attempting to save collected results...")
                    auditor.generate_report(output_dir)
                    print("✅ Partial results saved despite error")
                except Exception as save_error:
                    print(f"⚠️ Could not save results: {save_error}")
            
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

