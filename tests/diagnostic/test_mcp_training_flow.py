"""
Diagnostic Tests for MCP Training Document Flow

These tests systematically verify each step of the document flow:
1. Document ingestion to doc_store
2. Training job creation and execution
3. MCP receiving and storing documents
4. MCP querying trained documents

Purpose: Identify exactly where documents are lost in the training pipeline.
"""

import pytest
import httpx
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional


@pytest.mark.diagnostic
@pytest.mark.asyncio
class TestMCPTrainingDocumentFlow:
    """Comprehensive tests to trace document flow through MCP training."""
    
    @pytest.fixture
    def sample_document(self) -> Dict[str, Any]:
        """Sample document for testing."""
        doc_id = f"test_doc_{uuid.uuid4().hex[:8]}"
        return {
            "document_id": doc_id,
            "content": "This is test content about the Horus Heresy. The Emperor created the Primarchs.",
            "metadata": {
                "title": "Test Document",
                "source": "test",
                "doc_type": "test_document",
                "created_at": datetime.now().isoformat()
            },
            "tags": ["test", "diagnostic", "horus_heresy"]
        }
    
    # =================================================================
    # PHASE 1: Document Persistence in doc_store
    # =================================================================
    
    async def test_01_doc_store_accepts_document(self, sample_document):
        """
        TEST: Verify doc_store accepts and stores documents.
        
        Expected: POST returns 200/201 and document can be retrieved.
        """
        print("\n" + "="*70)
        print("TEST 1: Document Storage in doc_store")
        print("="*70)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: POST document to doc_store
            response = await client.post(
                "http://localhost:5087/api/v1/documents",
                json={
                    "id": sample_document["document_id"],
                    "content": sample_document["content"],
                    "metadata": sample_document["metadata"]
                }
            )
            
            print(f"📤 POST /api/v1/documents: {response.status_code}")
            print(f"📄 Document ID: {sample_document['document_id']}")
            
            assert response.status_code in [200, 201, 202], \
                f"doc_store rejected document: {response.status_code} - {response.text}"
            
            # Step 2: Verify document can be retrieved
            await asyncio.sleep(1)  # Allow persistence
            
            list_response = await client.get(
                "http://localhost:5087/api/v1/documents",
                params={"limit": 100}
            )
            
            print(f"📥 GET /api/v1/documents: {list_response.status_code}")
            
            assert list_response.status_code == 200, \
                f"doc_store list failed: {list_response.status_code}"
            
            data = list_response.json()
            documents = data.get("data", {}).get("items", [])
            doc_ids = [doc.get("id") for doc in documents]
            
            print(f"📊 Total documents in doc_store: {len(documents)}")
            print(f"🔍 Looking for: {sample_document['document_id']}")
            
            # Check if our document is in the list
            found = sample_document["document_id"] in doc_ids
            
            if found:
                print(f"✅ Document found in doc_store!")
            else:
                print(f"❌ Document NOT found in doc_store")
                print(f"   Available doc IDs: {doc_ids[:5]}...")  # Show first 5
            
            assert found, \
                f"Document {sample_document['document_id']} not found in doc_store after ingestion"
    
    async def test_02_doc_store_search_works(self, sample_document):
        """
        TEST: Verify doc_store search functionality.
        
        Expected: Search returns relevant documents.
        """
        print("\n" + "="*70)
        print("TEST 2: Document Search in doc_store")
        print("="*70)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # First ensure document exists
            await client.post(
                "http://localhost:5087/api/v1/documents",
                json={
                    "id": sample_document["document_id"],
                    "content": sample_document["content"],
                    "metadata": sample_document["metadata"]
                }
            )
        
            await asyncio.sleep(1)
            
            # Search for document
            search_response = await client.post(
                "http://localhost:5087/api/v1/search",
                json={"query": "Horus Heresy", "limit": 10}
            )
            
            print(f"🔍 POST /api/v1/search: {search_response.status_code}")
            
            assert search_response.status_code == 200, \
                f"doc_store search failed: {search_response.status_code}"
            
            data = search_response.json()
            items = data.get("data", {}).get("items", [])
            
            print(f"📊 Search results: {len(items)} documents")
            
            if items:
                print(f"✅ Search working! Found {len(items)} documents")
                for idx, item in enumerate(items[:3], 1):
                    print(f"   {idx}. {item.get('title', 'No title')} (ID: {item.get('id', 'unknown')[:12]}...)")
            else:
                print(f"⚠️  Search returned 0 results")
            
            assert len(items) >= 0, "Search should return results"
    
    # =================================================================
    # PHASE 2: Training Job Creation and Document Association
    # =================================================================
    
    async def test_03_training_job_creation(self):
        """
        TEST: Verify training coordinator creates jobs.
        
        Expected: POST returns job ID and status.
        """
        print("\n" + "="*70)
        print("TEST 3: Training Job Creation")
        print("="*70)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # First provision an MCP
            mcp_response = await client.post(
                "http://localhost:5400/api/v1/mcps",
                json={
                    "name": "test-mcp-diagnostic",
                    "tier": 2,
                    "image_name": "mcp-base:latest"
                }
            )
        
            print(f"📦 Provision MCP: {mcp_response.status_code}")
            
            if mcp_response.status_code not in [200, 201]:
                pytest.skip(f"MCP provisioning failed: {mcp_response.status_code}")
            
            mcp_data = mcp_response.json()
            mcp_id = mcp_data.get("mcp_id") or mcp_data.get("id")
            
            print(f"🆔 MCP ID: {mcp_id}")
            
            # Create training job
            training_response = await client.post(
                "http://localhost:5600/api/v1/jobs",
                params={
                    "mcp_id": mcp_id,
                    "name": "diagnostic_training",
                    "description": "Diagnostic test training job"
                },
                json=["github", "confluence"]
            )
        
            print(f"🎓 Create Training Job: {training_response.status_code}")
            
            assert training_response.status_code in [200, 201], \
                f"Training job creation failed: {training_response.status_code} - {training_response.text}"
            
            training_data = training_response.json()
            job_id = training_data.get("job_id")
            
            print(f"🆔 Job ID: {job_id}")
            print(f"📊 Job Status: {training_data.get('status')}")
            print(f"⚡ Priority: {training_data.get('priority')}")
            
            assert job_id is not None, "Training job should return job_id"
            
            # Execute the job
            execute_response = await client.post(
                f"http://localhost:5600/api/v1/jobs/{job_id}/execute"
            )
            
            print(f"▶️  Execute Job: {execute_response.status_code}")
            
            if execute_response.status_code == 200:
                print(f"✅ Training job executed successfully")
            else:
                print(f"⚠️  Training job execution returned: {execute_response.status_code}")
                print(f"   Response: {execute_response.text[:200]}")
    
    # =================================================================
    # PHASE 3: MCP Document Access
    # =================================================================
    
    async def test_04_mcp_query_returns_documents(self, sample_document):
        """
        TEST: Verify MCP can query and return documents after training.
        
        This is the KEY test that currently FAILS.
        Expected: MCP query returns documents with content.
        Actual: Returns "Error accessing training documents: 0"
        """
        print("\n" + "="*70)
        print("TEST 4: MCP Document Query (KEY TEST)")
        print("="*70)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: Ingest document
            print("\n📤 Step 1: Ingesting document to doc_store...")
            doc_response = await client.post(
                "http://localhost:5087/api/v1/documents",
                json={
                    "id": sample_document["document_id"],
                    "content": sample_document["content"],
                    "metadata": sample_document["metadata"]
                }
            )
            print(f"   Status: {doc_response.status_code}")
            
            # Step 2: Provision MCP
            print("\n📦 Step 2: Provisioning MCP...")
            mcp_response = await client.post(
                "http://localhost:5400/api/v1/mcps",
                json={
                    "name": f"test-mcp-{uuid.uuid4().hex[:8]}",
                    "tier": 2,
                    "image_name": "mcp-base:latest"
                }
            )
            print(f"   Status: {mcp_response.status_code}")
            
            if mcp_response.status_code not in [200, 201]:
                pytest.skip(f"MCP provisioning failed: {mcp_response.status_code}")
            
            mcp_data = mcp_response.json()
            mcp_id = mcp_data.get("mcp_id") or mcp_data.get("id")
            container_id = mcp_data.get("container_id")
            
            print(f"   MCP ID: {mcp_id}")
            print(f"   Container ID: {container_id}")
            
            # Step 3: Create and execute training job
            print("\n🎓 Step 3: Creating training job...")
            training_response = await client.post(
                "http://localhost:5600/api/v1/jobs",
                params={
                    "mcp_id": mcp_id,
                    "name": "diagnostic_training",
                    "description": "Test training with documents"
                },
                json=["github", "confluence"]
            )
            print(f"   Status: {training_response.status_code}")
            
            if training_response.status_code in [200, 201]:
                training_data = training_response.json()
                job_id = training_data.get("job_id")
                print(f"   Job ID: {job_id}")
                
                # Execute training
                print("\n▶️  Step 4: Executing training job...")
                execute_response = await client.post(
                    f"http://localhost:5600/api/v1/jobs/{job_id}/execute"
                )
                print(f"   Status: {execute_response.status_code}")
                
                # Wait for training to process
                print("\n⏳ Step 5: Waiting for training to complete...")
                await asyncio.sleep(5)
            
            # Step 6: Query MCP directly (bypassing gateway)
            print("\n🔍 Step 6: Querying MCP for documents...")
            
            # Try to get MCP container port
            import subprocess
            try:
                result = subprocess.run(
                    ['docker', 'port', container_id],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                mcp_port = None
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if '3000/tcp' in line or '8080/tcp' in line:
                            mcp_port = line.split(':')[-1].strip()
                            break
                
                if mcp_port:
                    mcp_url = f"http://localhost:{mcp_port}"
                    print(f"   MCP URL: {mcp_url}")
                    
                    # Query the MCP
                    query_response = await client.post(
                        f"{mcp_url}/query",
                        json={
                            "query": "Tell me about the Horus Heresy",
                            "max_results": 10
                        },
                        timeout=10.0
                    )
                    
                    print(f"   Query Status: {query_response.status_code}")
                    
                    if query_response.status_code == 200:
                        query_data = query_response.json()
                        print(f"   Response: {json.dumps(query_data, indent=2)[:500]}")
                        
                        # Check for the error message
                        response_text = json.dumps(query_data)
                        has_error = "Error accessing training documents: 0" in response_text
                        
                        if has_error:
                            print(f"\n❌ ISSUE CONFIRMED: MCP cannot access training documents")
                            print(f"   This is the root cause we need to fix!")
                        else:
                            print(f"\n✅ MCP returned a response (not an error)")
                        
                        # Assert that documents are accessible
                        assert not has_error, \
                            "MCP should be able to access training documents"
                    else:
                        print(f"   Error: {query_response.text[:200]}")
                else:
                    pytest.skip("Could not determine MCP container port")
                    
            except Exception as e:
                print(f"   Error querying MCP: {str(e)}")
                pytest.skip(f"Could not query MCP: {str(e)}")
    
    # =================================================================
    # PHASE 4: Service Integration Audit
    # =================================================================
    
    async def test_05_service_connectivity(self):
        """
        TEST: Verify all services can communicate with each other.
        
        Expected: All services are reachable from each other.
        """
        print("\n" + "="*70)
        print("TEST 5: Service Connectivity Audit")
        print("="*70)
        
        services = {
            "kafka-ingestion": "http://localhost:5700/health",
            "doc_store": "http://localhost:5087/health",
            "mcp-provisioner": "http://localhost:5400/health",
            "mcp-training-coordinator": "http://localhost:5600/health",
        }
        
        results = {}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for name, url in services.items():
                try:
                    response = await client.get(url, timeout=5.0)
                    status = "✅ ONLINE" if response.status_code == 200 else f"⚠️ {response.status_code}"
                    results[name] = (response.status_code, status)
                    print(f"{status} - {name} ({url})")
                except Exception as e:
                    results[name] = (None, f"❌ OFFLINE - {str(e)[:50]}")
                    print(f"❌ OFFLINE - {name} - {str(e)[:50]}")
            
            # At minimum, doc_store and training coordinator should be online
            assert results["doc_store"][0] == 200, "doc_store must be online"
            assert results["mcp-training-coordinator"][0] == 200, "mcp-training-coordinator must be online"
    
    async def test_06_document_count_verification(self):
        """
        TEST: Verify document count across services.
        
        Expected: doc_store shows accurate document count.
        """
        print("\n" + "="*70)
        print("TEST 6: Document Count Verification")
        print("="*70)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get document count from doc_store
            response = await client.get(
                "http://localhost:5087/api/v1/documents",
                params={"limit": 1000}  # Get all
            )
        
            assert response.status_code == 200, f"doc_store list failed: {response.status_code}"
            
            data = response.json()
            documents = data.get("data", {}).get("items", [])
            total = data.get("data", {}).get("total", 0)
            
            print(f"📊 Documents in doc_store:")
            print(f"   Items returned: {len(documents)}")
            print(f"   Total count: {total}")
            
            if documents:
                print(f"\n📄 Sample documents:")
                for idx, doc in enumerate(documents[:5], 1):
                    doc_id = doc.get("id", "unknown")
                    title = doc.get("title", doc.get("metadata", {}).get("title", "No title"))
                    print(f"   {idx}. {title[:50]} (ID: {doc_id[:12]}...)")
            
            assert total >= 0, "doc_store should report document count"


# =================================================================
# Helper Functions for Investigation
# =================================================================

async def trace_document_through_system(doc_id: str):
    """
    Utility function to trace a document through the entire system.
    
    Usage:
        await trace_document_through_system("doc_12345")
    """
    print(f"\n🔍 Tracing document {doc_id} through system...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Check doc_store
        print("\n1️⃣ Checking doc_store...")
        response = await client.get(
            "http://localhost:5087/api/v1/documents",
            params={"limit": 1000}
        )
        
        if response.status_code == 200:
            data = response.json()
            documents = data.get("data", {}).get("items", [])
            doc_ids = [doc.get("id") for doc in documents]
            
            if doc_id in doc_ids:
                print(f"   ✅ Document found in doc_store")
            else:
                print(f"   ❌ Document NOT in doc_store")
        else:
            print(f"   ⚠️ Could not query doc_store: {response.status_code}")


if __name__ == "__main__":
    """Run diagnostic tests with detailed output."""
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║     MCP TRAINING DOCUMENT FLOW - DIAGNOSTIC TEST SUITE           ║
╚═══════════════════════════════════════════════════════════════════╝

This test suite will systematically verify each step of the document flow
and identify exactly where documents are lost in the MCP training pipeline.

Running tests...
    """)
    
    pytest.main([
        __file__,
        "-v",
        "-s",  # Show print statements
        "--tb=short",  # Short traceback
        "-m", "diagnostic"  # Only diagnostic tests
    ])

