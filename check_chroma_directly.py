#!/usr/bin/env python3
"""Direct check of ChromaDB collection."""

import chromadb

# Connect to ChromaDB (same path as service)
client = chromadb.PersistentClient(path="/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp/data/chroma")

# List all collections
collections = client.list_collections()
print(f"📊 Found {len(collections)} collections:")
for coll in collections:
    print(f"   - {coll.name}: {coll.count()} documents")

# Try to get ecosystem_docs collection
try:
    coll = client.get_collection("ecosystem_docs")
    count = coll.count()
    print(f"\n✅ 'ecosystem_docs' collection exists with {count} embeddings")
    
    if count > 0:
        # Get a sample
        sample = coll.get(limit=3, include=["metadatas", "documents"])
        print(f"\n📝 Sample documents:")
        for i, doc_id in enumerate(sample["ids"][:3]):
            metadata = sample["metadatas"][i] if sample["metadatas"] else {}
            file_path = metadata.get("file_path", "Unknown")
            print(f"   {i+1}. {file_path[:60]}...")
except Exception as e:
    print(f"\n❌ Could not access 'ecosystem_docs': {e}")

