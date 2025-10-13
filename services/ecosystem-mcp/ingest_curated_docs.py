#!/usr/bin/env python3
"""
Quick script to ingest curated documentation files.
"""

import asyncio
import httpx
from pathlib import Path

# Curated list of important docs (10-15 files)
CURATED_DOCS = [
    "README.md",
    "QUICK_START_GUIDE.md",
    "DEPLOYMENT_GUIDE.md",
    "3_TIER_STATUS_REPORT.md",
    "PERFORMANCE_COMPARISON_ANALYSIS.md",
    "CLEANUP_SUCCESS_SUMMARY.md",
    "TESTING_GUIDE.md",
    "IMPLEMENTATION_COMPLETE.md",
    "FINAL_TESTING_AND_DEMO_SUMMARY.md",
    "RAG_IMPLEMENTATION_COMPLETE.md",
]

BASE_DIR = Path(__file__).parent


async def ingest_document(client: httpx.AsyncClient, file_path: Path) -> dict:
    """Ingest a single document."""
    
    if not file_path.exists():
        return {"file": str(file_path), "status": "skipped", "reason": "not found"}
    
    content = file_path.read_text()
    
    # Create document via API
    try:
        response = await client.post(
            "http://localhost:8000/api/v1/admin/ingest/direct",
            json={
                "file_path": str(file_path.relative_to(BASE_DIR)),
                "content": content,
                "metadata": {
                    "source": "manual_ingestion",
                    "type": "documentation"
                }
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            return {
                "file": file_path.name,
                "status": "success",
                "size": len(content)
            }
        else:
            return {
                "file": file_path.name,
                "status": "failed",
                "reason": f"HTTP {response.status_code}"
            }
    except Exception as e:
        return {
            "file": file_path.name,
            "status": "error",
            "reason": str(e)
        }


async def main():
    """Ingest all curated documents."""
    
    print("="*80)
    print("INGESTING CURATED DOCUMENTATION")
    print("="*80)
    print()
    
    async with httpx.AsyncClient() as client:
        results = []
        
        for doc_name in CURATED_DOCS:
            file_path = BASE_DIR / doc_name
            print(f"📄 Ingesting: {doc_name}...", end=" ")
            
            result = await ingest_document(client, file_path)
            results.append(result)
            
            if result["status"] == "success":
                size_kb = result["size"] / 1024
                print(f"✅ ({size_kb:.1f} KB)")
            elif result["status"] == "skipped":
                print(f"⏭️  Skipped ({result['reason']})")
            else:
                print(f"❌ Failed ({result.get('reason', 'unknown')})")
        
        print()
        print("="*80)
        print("INGESTION SUMMARY")
        print("="*80)
        
        successful = sum(1 for r in results if r["status"] == "success")
        failed = sum(1 for r in results if r["status"] == "failed")
        skipped = sum(1 for r in results if r["status"] == "skipped")
        
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"⏭️  Skipped: {skipped}")
        print(f"📊 Total: {len(results)}")
        print()
        
        # Check database stats
        try:
            response = await client.get("http://localhost:8000/api/v1/admin/stats")
            if response.status_code == 200:
                stats = response.json()
                print(f"📚 Documents in database: {stats['documents']['total']}")
                print(f"🔢 Embeddings: {stats['documents']['embeddings']}")
        except Exception as e:
            print(f"⚠️  Could not fetch stats: {e}")


if __name__ == "__main__":
    asyncio.run(main())

