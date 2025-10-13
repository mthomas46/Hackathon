#!/usr/bin/env python3
"""
Ingest 500 commits, then query for ecosystem description and development history.
"""

import httpx
import time
import sys
from datetime import datetime
from pathlib import Path


class EcosystemMCPQuerier:
    """Handles ingestion monitoring and querying."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.Client(timeout=120.0)
    
    def monitor_ingestion(self, timeout: int = 1800):
        """Monitor ingestion until complete or timeout (30 min default)."""
        print("\n" + "=" * 80)
        print("⏳ MONITORING INGESTION PROGRESS")
        print("=" * 80)
        
        start_time = time.time()
        last_doc_count = 0
        stable_count = 0
        
        # Get initial stats
        initial_stats = self.client.get(f"{self.base_url}/api/v1/admin/stats").json()
        initial_docs = initial_stats.get('documents', {}).get('total', 0)
        
        print(f"\nInitial document count: {initial_docs}")
        print(f"Timeout: {timeout}s ({timeout/60:.1f} minutes)")
        print("\nProgress:")
        
        while (time.time() - start_time) < timeout:
            try:
                # Get current stats
                stats = self.client.get(f"{self.base_url}/api/v1/admin/stats").json()
                queue = self.client.get(f"{self.base_url}/api/v1/admin/queue-status").json()
                
                doc_count = stats.get('documents', {}).get('total', 0)
                embedding_count = stats.get('documents', {}).get('embeddings', 0)
                
                ingestion_queue = queue.get('ingestion_queue', 0)
                embedding_queue = queue.get('embedding_queue', 0)
                
                elapsed = int(time.time() - start_time)
                docs_added = doc_count - initial_docs
                rate = docs_added / (elapsed if elapsed > 0 else 1)
                
                print(f"  [{elapsed:4d}s] Docs: {doc_count:5d} (+{docs_added:4d}) | "
                      f"Embeddings: {embedding_count:5d} | "
                      f"Rate: {rate:.2f}/s | "
                      f"Queues: I:{ingestion_queue} E:{embedding_queue}")
                
                # Check if done (queues empty and doc count stable)
                if ingestion_queue == 0 and embedding_queue == 0:
                    if doc_count == last_doc_count:
                        stable_count += 1
                        if stable_count >= 3:  # Stable for 15 seconds
                            print(f"\n✅ Ingestion complete!")
                            print(f"  Total documents: {doc_count}")
                            print(f"  Total embeddings: {embedding_count}")
                            print(f"  Documents added: +{docs_added}")
                            print(f"  Duration: {elapsed}s ({elapsed/60:.1f} minutes)")
                            print(f"  Average rate: {rate:.2f} docs/second")
                            return True
                    else:
                        stable_count = 0
                
                last_doc_count = doc_count
                time.sleep(5)
                
            except Exception as e:
                print(f"  ⚠️  Monitoring error: {e}")
                time.sleep(5)
        
        print(f"\n⏱️  Timeout reached after {timeout}s")
        return False
    
    def query_ecosystem_description(self):
        """Query for ecosystem-mcp description."""
        print("\n" + "=" * 80)
        print("🔍 QUERYING: ECOSYSTEM-MCP DESCRIPTION")
        print("=" * 80)
        
        query = """What is the ecosystem-mcp service? Describe its purpose, 
        architecture, key features, capabilities, and how it fits into the 
        larger microservices ecosystem. Include information about its data 
        storage, processing pipeline, and API endpoints."""
        
        print(f"\nQuery: {query[:100]}...")
        
        response = self.client.post(
            f"{self.base_url}/api/v1/search",
            json={"query": query, "limit": 10}
        )
        
        if response.status_code != 200:
            print(f"❌ Query failed: {response.status_code}")
            return None
        
        data = response.json()
        results = data.get('results', [])
        
        print(f"\n✅ Retrieved {len(results)} results")
        
        # Compile answer from results
        answer = self._compile_answer(query, results)
        return answer
    
    def query_development_history(self):
        """Query for development history."""
        print("\n" + "=" * 80)
        print("🔍 QUERYING: DEVELOPMENT HISTORY")
        print("=" * 80)
        
        query = """Describe the development history of the ecosystem-mcp service. 
        What were the major milestones, features added over time, bugs fixed, 
        architectural decisions, and key improvements? Include information about 
        testing, validation, and any significant refactoring efforts."""
        
        print(f"\nQuery: {query[:100]}...")
        
        response = self.client.post(
            f"{self.base_url}/api/v1/search",
            json={"query": query, "limit": 10}
        )
        
        if response.status_code != 200:
            print(f"❌ Query failed: {response.status_code}")
            return None
        
        data = response.json()
        results = data.get('results', [])
        
        print(f"\n✅ Retrieved {len(results)} results")
        
        # Compile answer from results
        answer = self._compile_answer(query, results)
        return answer
    
    def _compile_answer(self, query: str, results: list) -> str:
        """Compile answer from search results."""
        if not results:
            return "No relevant information found."
        
        # Show top results
        print("\nTop 5 results:")
        for i, result in enumerate(results[:5], 1):
            file_path = result.get('file_path', 'unknown')
            score = result.get('score', 0)
            print(f"  {i}. {file_path[:70]:<70} (score: {score:.3f})")
        
        # Combine content from all results
        combined_content = []
        for result in results:
            content = result.get('content', '')
            file_path = result.get('file_path', 'unknown')
            score = result.get('score', 0)
            
            if content and score > 0.4:  # Only include relevant results
                combined_content.append(f"\n### From: {file_path}\n{content}")
        
        if combined_content:
            return "\n".join(combined_content)
        else:
            return "No sufficiently relevant information found (all scores < 0.4)."
    
    def save_document(self, description: str, history: str, output_path: str):
        """Save the compiled document."""
        print("\n" + "=" * 80)
        print("💾 SAVING DOCUMENT")
        print("=" * 80)
        
        # Get final stats
        stats = self.client.get(f"{self.base_url}/api/v1/admin/stats").json()
        doc_count = stats.get('documents', {}).get('total', 0)
        embedding_count = stats.get('documents', {}).get('embeddings', 0)
        
        document = f"""# Ecosystem-MCP: Service Description & Development History

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Source**: Ecosystem-MCP Semantic Search  
**Documents Indexed**: {doc_count}  
**Embeddings Generated**: {embedding_count}

---

## 🏗️ SERVICE DESCRIPTION

{description}

---

## 📜 DEVELOPMENT HISTORY

{history}

---

## 📊 METADATA

- **Query Date**: {datetime.now().isoformat()}
- **Total Documents**: {doc_count:,}
- **Total Embeddings**: {embedding_count:,}
- **Search Engine**: ChromaDB + Ollama embeddings
- **Model**: nomic-embed-text (via Ollama)

---

*This document was automatically generated by querying the Ecosystem-MCP 
semantic search service. The content is derived from indexed documentation, 
code files, and commit messages from the repository.*
"""
        
        Path(output_path).write_text(document)
        print(f"\n✅ Document saved: {output_path}")
        print(f"   Size: {len(document):,} characters")
        
        return output_path


def main():
    """Main entry point."""
    print("=" * 80)
    print("ECOSYSTEM-MCP: INGEST & QUERY PIPELINE")
    print("=" * 80)
    
    querier = EcosystemMCPQuerier()
    
    # Step 1: Monitor ingestion
    print("\nStep 1: Waiting for ingestion to complete...")
    success = querier.monitor_ingestion(timeout=1800)  # 30 minutes
    
    if not success:
        print("\n⚠️  Ingestion timeout - continuing anyway...")
    
    # Give it a moment to finish any final processing
    print("\n⏳ Waiting 10 seconds for final processing...")
    time.sleep(10)
    
    # Step 2: Query for description
    description = querier.query_ecosystem_description()
    
    if not description:
        print("❌ Failed to get ecosystem description")
        sys.exit(1)
    
    # Step 3: Query for history
    history = querier.query_development_history()
    
    if not history:
        print("❌ Failed to get development history")
        sys.exit(1)
    
    # Step 4: Save document
    output_path = "ECOSYSTEM_MCP_DESCRIPTION_AND_HISTORY.md"
    querier.save_document(description, history, output_path)
    
    print("\n" + "=" * 80)
    print("✅ PIPELINE COMPLETE!")
    print("=" * 80)
    print(f"\nGenerated document: {output_path}")
    print("\nYou can now review the compiled information about ecosystem-mcp.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

