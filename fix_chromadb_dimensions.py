#!/usr/bin/env python3
"""
Fix ChromaDB Dimension Mismatch

Delete and recreate the ChromaDB collection with the correct
embedding dimensions (768 for nomic-embed-text).
"""

import asyncio
import sys

# Add src to path
sys.path.insert(0, "/app")

async def main():
    from src.storage.chromadb_client import get_chroma_client
    from src.services.embeddings.embedding_service import EmbeddingService
    
    print("🔍 Diagnosing ChromaDB dimension mismatch...")
    print("")
    
    # Get clients
    chroma = get_chroma_client()
    embedding_svc = EmbeddingService()
    
    # Test embedding generation
    print("1️⃣ Testing embedding service...")
    test_result = await embedding_svc.generate_embedding("test")
    actual_dim = len(test_result["embedding"])
    print(f"   ✅ Embedding service generates {actual_dim}-dimensional vectors")
    print("")
    
    # Check current collection
    print("2️⃣ Checking current ChromaDB collection...")
    try:
        count = await chroma.count()
        print(f"   📊 Current collection: {chroma.collection_name}")
        print(f"   📈 Current count: {count} embeddings")
        
        # Get collection metadata
        import asyncio as aio
        metadata = await aio.to_thread(lambda: chroma.collection.metadata)
        print(f"   ℹ️  Metadata: {metadata}")
        print("")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print("")
    
    # Delete and recreate
    print("3️⃣ Recreating collection with correct dimensions...")
    confirmation = input(f"   ⚠️  This will DELETE all existing embeddings. Continue? (yes/no): ")
    
    if confirmation.lower() != "yes":
        print("   ❌ Aborted by user")
        return
    
    try:
        # Delete collection
        print(f"   🗑️  Deleting collection '{chroma.collection_name}'...")
        await asyncio.to_thread(chroma.client.delete_collection, chroma.collection_name)
        print(f"   ✅ Collection deleted")
        
        # Recreate with correct dimensions
        print(f"   🔨 Creating collection with {actual_dim} dimensions...")
        new_collection = chroma.client.create_collection(
            name=chroma.collection_name,
            metadata={
                "hnsw:space": "cosine",
                "dimension": actual_dim
            }
        )
        chroma.collection = new_collection
        print(f"   ✅ Collection created: {chroma.collection_name}")
        print("")
        
        # Verify
        print("4️⃣ Verification...")
        count = await chroma.count()
        print(f"   📊 New collection count: {count}")
        print(f"   ✅ Collection ready for {actual_dim}-dimensional embeddings")
        print("")
        
        print("=" * 70)
        print("🎉 ChromaDB collection fixed!")
        print("=" * 70)
        print("Next steps:")
        print("1. Restart ecosystem-mcp-service")
        print("2. Start new embedding regeneration")
        print("3. Monitor progress via dashboard")
        print("=" * 70)
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

