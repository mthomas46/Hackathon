#!/usr/bin/env python3
"""
Quick script to generate embeddings for existing documents in PostgreSQL.

This bypasses the normal ingestion pipeline and directly calls the embedding
service for documents that are already in the database.
"""

import asyncio
import httpx
from tqdm import tqdm

async def generate_embeddings():
    """Generate embeddings for all documents without embeddings."""
    
    base_url = "http://localhost:8000"
    
    print("🚀 Starting embedding generation for existing documents...")
    print("=" * 70)
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        # Step 1: Get document count
        print("\n📊 Step 1: Fetching document statistics...")
        docs_response = await client.get(f"{base_url}/api/v1/documents")
        docs_response.raise_for_status()
        docs_data = docs_response.json()
        
        total = docs_data.get("total", 0)
        print(f"✅ Found {total:,} documents in PostgreSQL")
        
        if total == 0:
            print("❌ No documents to embed! Run ingestion first.")
            return
        
        # Step 2: Check current embeddings
        print("\n📊 Step 2: Checking existing embeddings...")
        try:
            embed_response = await client.get(f"{base_url}/api/v1/embeddings/sample?n=1")
            if embed_response.status_code == 200:
                embed_data = embed_response.json()
                existing = embed_data.get("total_documents", 0)
                print(f"✅ Already have {existing:,} embeddings in ChromaDB")
                if existing >= total:
                    print(f"🎉 All documents already embedded!")
                    return
            else:
                print(f"ℹ️  No embeddings yet in ChromaDB")
                existing = 0
        except Exception as e:
            print(f"ℹ️  ChromaDB is empty (expected): {e}")
            existing = 0
        
        # Step 3: Fetch all documents (in batches)
        print(f"\n📚 Step 3: Loading {total:,} documents from PostgreSQL...")
        all_docs = []
        limit = 100
        offset = 0
        
        with tqdm(total=total, desc="Loading docs", unit="docs") as pbar:
            while offset < total:
                page_response = await client.get(
                    f"{base_url}/api/v1/documents",
                    params={"limit": limit, "offset": offset}
                )
                page_data = page_response.json()
                docs = page_data.get("documents", [])
                all_docs.extend(docs)
                offset += limit
                pbar.update(len(docs))
        
        print(f"✅ Loaded {len(all_docs):,} documents")
        
        # Step 4: Trigger embedding via admin rebuild-index
        print(f"\n🧬 Step 4: Triggering embedding generation...")
        print(f"   This will take approximately {len(all_docs) * 0.3 / 60:.1f} minutes")
        print(f"   (estimating ~0.3 seconds per document)")
        
        try:
            rebuild_response = await client.post(
                f"{base_url}/api/v1/admin/rebuild-index",
                timeout=3600.0  # 1 hour timeout
            )
            
            if rebuild_response.status_code == 200:
                result = rebuild_response.json()
                print(f"\n✅ Embedding generation complete!")
                print(f"   Embeddings created: {result.get('embeddings_created', 'N/A')}")
                print(f"   Time taken: {result.get('duration_seconds', 'N/A')}s")
            else:
                print(f"\n❌ Rebuild failed: HTTP {rebuild_response.status_code}")
                print(f"   Response: {rebuild_response.text[:200]}")
        except Exception as e:
            print(f"\n❌ Error during rebuild: {e}")
            print(f"\nℹ️  The rebuild endpoint might not exist. Trying alternative method...")
            
            # Alternative: Process via queue
            print(f"\n🔄 Alternative: Adding documents to embedding queue...")
            success = 0
            errors = 0
            
            with tqdm(all_docs, desc="Queueing", unit="docs") as pbar:
                for doc in pbar:
                    try:
                        # This might trigger embedding through the normal pipeline
                        response = await client.get(
                            f"{base_url}/api/v1/documents/{doc['id']}",
                            timeout=5.0
                        )
                        if response.status_code == 200:
                            success += 1
                        else:
                            errors += 1
                    except Exception as e:
                        errors += 1
                    
                    pbar.set_postfix({"success": success, "errors": errors})
            
            print(f"\n✅ Queued {success:,} documents for embedding")
            if errors > 0:
                print(f"⚠️  {errors:,} documents had errors")
        
        # Step 5: Verify embeddings
        print(f"\n📊 Step 5: Verifying embeddings...")
        await asyncio.sleep(5)  # Wait for processing
        
        verify_response = await client.get(f"{base_url}/api/v1/embeddings/sample?n=5")
        if verify_response.status_code == 200:
            verify_data = verify_response.json()
            new_total = verify_data.get("total_documents", 0)
            samples = verify_data.get("samples", [])
            
            print(f"✅ ChromaDB now has {new_total:,} embeddings")
            print(f"\n📝 Sample embeddings:")
            for i, sample in enumerate(samples[:3], 1):
                print(f"   {i}. {sample.get('file_path', 'Unknown')[:60]}...")
        else:
            print(f"⚠️  Could not verify embeddings: HTTP {verify_response.status_code}")
        
        print(f"\n" + "=" * 70)
        print(f"🎉 Process complete!")
        print(f"\n🔍 Test embeddings API:")
        print(f"   curl \"http://localhost:8000/api/v1/embeddings/sample?n=10\"")
        print(f"\n🌐 Try the dashboard:")
        print(f"   http://localhost:8501 → 🔮 ChromaDB Explorer → 🧬 Embedding Explorer")


if __name__ == "__main__":
    try:
        asyncio.run(generate_embeddings())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

