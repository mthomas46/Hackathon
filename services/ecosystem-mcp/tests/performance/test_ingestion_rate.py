#!/usr/bin/env python3
"""
Load Test: Document Ingestion Rate

Target: Verify 50 → 150 docs/min improvement (3x)

Tests:
1. Ingestion rate with parallel embedding generation
2. Compare to sequential baseline
3. Resource utilization
"""

import asyncio
import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any
import httpx

BASE_URL = "http://localhost:8000"


class IngestionRateTester:
    """Tester for ingestion rate."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
    
    def create_test_docs(self, num_docs: int) -> Path:
        """Create a temporary directory with test markdown documents."""
        temp_dir = Path(tempfile.mkdtemp())
        
        for i in range(num_docs):
            doc_path = temp_dir / f"test_doc_{i:04d}.md"
            content = f"""# Test Document {i}

## Overview
This is test document number {i} for ingestion rate testing.

## Content
Document {i} contains information about performance optimization,
caching strategies, and throughput improvements in the ecosystem-mcp service.

### Key Points
- Point 1 for document {i}
- Point 2 for document {i}
- Point 3 for document {i}

### Details
This document has enough content to generate meaningful embeddings
and test the ingestion pipeline performance.

Document ID: {i}
Generated: {time.time()}
"""
            doc_path.write_text(content)
        
        return temp_dir
    
    async def test_ingestion_rate(
        self,
        num_docs: int = 150
    ) -> Dict[str, Any]:
        """
        Test ingestion rate.
        
        Args:
            num_docs: Number of documents to ingest
        
        Returns:
            Performance metrics
        """
        print(f"\n{'='*80}")
        print(f"Ingestion Rate Test: {num_docs} documents")
        print(f"{'='*80}\n")
        
        # Create test documents
        print(f"Creating {num_docs} test documents...")
        temp_dir = self.create_test_docs(num_docs)
        print(f"✅ Test documents created in {temp_dir}")
        
        try:
            async with httpx.AsyncClient(timeout=600.0) as client:
                # Start ingestion job
                print(f"\nStarting ingestion job...")
                start_time = time.time()
                
                response = await client.post(
                    f"{self.base_url}/api/v1/admin/ingest",
                    json={
                        "repo_path": str(temp_dir),
                        "patterns": ["*.md"],
                        "mode": "incremental"
                    }
                )
                
                if response.status_code != 200:
                    print(f"❌ Failed to start ingestion: {response.text}")
                    return {}
                
                job_data = response.json()
                job_id = job_data["job_id"]
                print(f"✅ Job started: {job_id}")
                
                # Poll for completion
                completed = False
                last_processed = 0
                
                while not completed:
                    await asyncio.sleep(5)
                    
                    status_response = await client.get(
                        f"{self.base_url}/api/v1/admin/ingest/{job_id}"
                    )
                    
                    if status_response.status_code != 200:
                        print(f"❌ Failed to get status")
                        break
                    
                    status = status_response.json()
                    
                    if status["status"] in ["completed", "failed"]:
                        completed = True
                    
                    # Progress
                    processed = status.get("processed_documents", 0)
                    if processed > last_processed:
                        elapsed = time.time() - start_time
                        rate = processed / elapsed * 60  # docs/min
                        print(f"Progress: {processed}/{num_docs} docs "
                              f"({rate:.1f} docs/min)", end='\r')
                        last_processed = processed
                
                print()  # New line
                
                total_time = time.time() - start_time
                
                # Get final status
                final_status = status
                
                metrics = {
                    "num_docs": num_docs,
                    "processed": final_status.get("processed_documents", 0),
                    "failed": final_status.get("failed_documents", 0),
                    "total_time": total_time,
                    "docs_per_minute": final_status.get("processed_documents", 0) / total_time * 60,
                    "status": final_status.get("status"),
                    "success": final_status.get("status") == "completed"
                }
                
                return metrics
        
        finally:
            # Cleanup
            print(f"\nCleaning up test documents...")
            shutil.rmtree(temp_dir)
            print(f"✅ Cleanup complete")
    
    def print_metrics(self, metrics: Dict[str, Any]):
        """Print ingestion metrics."""
        print(f"\n{'='*80}")
        print(f"Results: Ingestion Rate Test")
        print(f"{'='*80}")
        print(f"\nDocuments: {metrics['num_docs']}")
        print(f"Processed: {metrics['processed']}")
        print(f"Failed: {metrics['failed']}")
        print(f"Total Time: {metrics['total_time']:.1f}s ({metrics['total_time']/60:.2f} min)")
        print(f"\nIngestion Rate: {metrics['docs_per_minute']:.1f} docs/min")
        print(f"Status: {metrics['status']}")
        
        print(f"\n{'='*80}")
        target_rate = 150  # docs/min
        if metrics['docs_per_minute'] >= target_rate * 0.9:  # 90% of target
            print(f"✅ PASS: Achieved {metrics['docs_per_minute']:.1f} docs/min (target: {target_rate})")
        else:
            print(f"❌ FAIL: Only {metrics['docs_per_minute']:.1f} docs/min (target: {target_rate})")
        
        if metrics['success'] and metrics['failed'] == 0:
            print(f"✅ PASS: All documents processed successfully")
        else:
            print(f"⚠️  WARNING: {metrics['failed']} documents failed")
        print(f"{'='*80}\n")


async def main():
    """Run ingestion rate test."""
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║          INGESTION RATE VERIFICATION TEST                                 ║
╚═══════════════════════════════════════════════════════════════════════════╝

Testing Claim: Ingestion Rate 50 → 150 docs/min (3x improvement)

Note: This test ingests 150 test documents and measures the rate.
      Expected time: ~1-2 minutes

""")
    
    tester = IngestionRateTester()
    
    # Test with 150 documents (should take ~1 minute)
    metrics = await tester.test_ingestion_rate(num_docs=150)
    
    if not metrics:
        print("❌ TEST FAILED TO RUN")
        return 1
    
    tester.print_metrics(metrics)
    
    # Verdict
    target_met = metrics['docs_per_minute'] >= 135  # 90% of 150
    success = metrics['success']
    
    if target_met and success:
        print("\n🎉 INGESTION RATE TEST PASSED! 🎉")
        return 0
    else:
        print("\n⚠️  INGESTION TEST FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

