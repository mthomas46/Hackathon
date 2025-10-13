#!/usr/bin/env python3
"""Quick monitoring and validation."""

import httpx
import time

client = httpx.Client(timeout=30.0)
base_url = "http://localhost:8000"

print("\n" + "=" * 80)
print("📊 CURRENT STATUS")
print("=" * 80)

# Get stats
stats = client.get(f"{base_url}/api/v1/admin/stats").json()
queue = client.get(f"{base_url}/api/v1/admin/queue-status").json()

docs = stats['documents']['total']
embeddings = stats['documents']['embeddings']
ing_q = queue['ingestion_queue']
emb_q = queue['embedding_queue']

print(f"\n✅ Documents:        {docs:,}")
print(f"✅ Embeddings:       {embeddings:,}")
print(f"⏳ Ingestion Queue:  {ing_q}")
print(f"⏳ Embedding Queue:  {emb_q}")

if ing_q == 0 and emb_q == 0:
    print("\n✅ ALL QUEUES EMPTY - INGESTION COMPLETE!")
else:
    print(f"\n⏳ Still processing... ({ing_q + emb_q} jobs remaining)")
    print("\nEstimated time remaining: ~{:.1f} minutes".format((ing_q + emb_q) * 5 / 60))

print("\n" + "=" * 80)

