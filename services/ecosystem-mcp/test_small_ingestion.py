#!/usr/bin/env python3
"""
Quick test of ingestion with a small number of commits.
"""

import httpx
import time
import sys

def test_small_ingestion():
    client = httpx.Client(timeout=60.0)
    base_url = "http://localhost:8000"
    
    print("=" * 80)
    print("Testing Small Ingestion (Test Mode)")
    print("=" * 80)
    
    # 1. Trigger ingestion
    print("\n1. Triggering ingestion...")
    response = client.post(
        f"{base_url}/api/v1/admin/ingest",
        json={
            "repo_path": "/Users/mykalthomas/Documents/work/Hackathon",
            "mode": "test"  # Test mode should process fewer commits
        }
    )
    
    if response.status_code not in [200, 201, 202]:
        print(f"✗ Failed: {response.status_code}")
        print(response.text)
        return False
    
    data = response.json()
    job_id = data.get("job_id")
    print(f"✓ Job created: {job_id}")
    
    # 2. Monitor for 60 seconds
    print("\n2. Monitoring progress for 60 seconds...")
    for i in range(12):  # 12 x 5 = 60 seconds
        time.sleep(5)
        
        # Get stats
        stats_response = client.get(f"{base_url}/api/v1/admin/stats")
        stats = stats_response.json()
        
        # Get queue
        queue_response = client.get(f"{base_url}/api/v1/admin/queue-status")
        queue = queue_response.json()
        
        docs = stats.get('documents', {}).get('total', 0)
        embeddings = stats.get('documents', {}).get('embeddings', 0)
        ing_queue = queue.get('ingestion_queue', 0)
        emb_queue = queue.get('embedding_queue', 0)
        
        print(f"  [{i*5:2d}s] Docs: {docs:3d} | Embeddings: {embeddings:3d} | "
              f"Queues: I:{ing_queue} E:{emb_queue}")
        
        # If queues empty and we have docs, we're done
        if ing_queue == 0 and emb_queue == 0 and docs > 0:
            print("\n✓ Processing complete!")
            break
    
    # 3. Final stats
    print("\n3. Final statistics:")
    final_stats = client.get(f"{base_url}/api/v1/admin/stats").json()
    final_docs = final_stats.get('documents', {}).get('total', 0)
    final_embeddings = final_stats.get('documents', {}).get('embeddings', 0)
    
    print(f"  Documents: {final_docs}")
    print(f"  Embeddings: {final_embeddings}")
    
    # 4. Test search
    if final_docs > 0:
        print("\n4. Testing search...")
        search_response = client.post(
            f"{base_url}/api/v1/search",
            json={"query": "test", "limit": 3}
        )
        
        if search_response.status_code == 200:
            search_data = search_response.json()
            results = search_data.get('results', [])
            print(f"✓ Search works! Found {len(results)} results")
            if results:
                print(f"  Top result: {results[0].get('file_path', 'unknown')[:60]}")
        else:
            print(f"⚠️  Search failed: {search_response.status_code}")
    
    print("\n" + "=" * 80)
    if final_docs > 0:
        print("✅ TEST PASSED: Ingestion is working!")
        return True
    else:
        print("❌ TEST FAILED: No documents ingested")
        return False

if __name__ == "__main__":
    try:
        success = test_small_ingestion()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

