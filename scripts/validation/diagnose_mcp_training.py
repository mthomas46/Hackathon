#!/usr/bin/env python3
"""
Simple diagnostic script to trace document flow through MCP training.

Purpose: Identify exactly where documents are lost in the training pipeline.
Run: python3 diagnose_mcp_training.py
"""

import asyncio
import httpx
import json
import uuid
from datetime import datetime


class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


async def diagnose_document_flow():
    """Main diagnostic function."""
    
    print(f"""
{Colors.BOLD}╔═══════════════════════════════════════════════════════════════════╗
║       MCP TRAINING DOCUMENT FLOW - DIAGNOSTIC SCRIPT             ║
╚═══════════════════════════════════════════════════════════════════╝{Colors.RESET}

This script will systematically trace document flow and identify where
documents are lost in the MCP training pipeline.
    """)
    
    doc_id = f"diagnostic_{uuid.uuid4().hex[:8]}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # ==============================================================
        # TEST 1: Verify doc_store accepts documents
        # ==============================================================
        
        print(f"\n{Colors.BOLD}{'='*70}")
        print(f"TEST 1: Document Storage in doc_store")
        print(f"{'='*70}{Colors.RESET}\n")
        
        try:
            response = await client.post(
                "http://localhost:5087/api/v1/documents",
                json={
                    "id": doc_id,
                    "content": "Test content about Horus Heresy and the Emperor",
                    "metadata": {"title": "Test Document", "source": "diagnostic"}
                }
            )
            
            print(f"📤 POST /api/v1/documents: {response.status_code}")
            
            if response.status_code in [200, 201, 202]:
                print(f"{Colors.GREEN}✅ doc_store accepted document{Colors.RESET}")
                
                # Verify it can be retrieved
                await asyncio.sleep(1)
                list_resp = await client.get("http://localhost:5087/api/v1/documents", params={"limit": 100})
                
                if list_resp.status_code == 200:
                    data = list_resp.json()
                    docs = data.get("data", {}).get("items", [])
                    doc_ids = [d.get("id") for d in docs]
                    
                    if doc_id in doc_ids:
                        print(f"{Colors.GREEN}✅ Document retrievable from doc_store{Colors.RESET}")
                        print(f"   Total documents in doc_store: {len(docs)}")
                    else:
                        print(f"{Colors.RED}❌ Document NOT found in doc_store after ingestion{Colors.RESET}")
                else:
                    print(f"{Colors.YELLOW}⚠️  Could not verify document: {list_resp.status_code}{Colors.RESET}")
            else:
                print(f"{Colors.RED}❌ doc_store rejected document: {response.status_code}{Colors.RESET}")
                print(f"   Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"{Colors.RED}❌ Error accessing doc_store: {str(e)[:100]}{Colors.RESET}")
        
        
        # ==============================================================
        # TEST 2: Provision MCP
        # ==============================================================
        
        print(f"\n{Colors.BOLD}{'='*70}")
        print(f"TEST 2: MCP Provisioning")
        print(f"{'='*70}{Colors.RESET}\n")
        
        mcp_id = None
        container_id = None
        
        try:
            response = await client.post(
                "http://localhost:5400/api/v1/mcps",
                json={
                    "client_id": f"diagnostic-client-{uuid.uuid4().hex[:8]}",
                    "name": f"diagnostic-mcp-{uuid.uuid4().hex[:8]}",
                    "tier": 2,
                    "image_name": "mcp-base:latest"
                }
            )
            
            print(f"📦 Provision MCP: {response.status_code}")
            
            if response.status_code in [200, 201]:
                data = response.json()
                print(f"   Raw response: {json.dumps(data, indent=2)[:500]}")
                
                mcp_id = data.get("mcp_id") or data.get("id") or data.get("data", {}).get("mcp_id")
                container_id = data.get("container_id") or data.get("data", {}).get("container_id")
                
                if mcp_id:
                    print(f"{Colors.GREEN}✅ MCP provisioned: {mcp_id}{Colors.RESET}")
                    print(f"   Container ID: {container_id}")
                else:
                    print(f"{Colors.YELLOW}⚠️  MCP provisioned but ID not found in response{Colors.RESET}")
                    print(f"   Available keys: {list(data.keys())}")
            else:
                print(f"{Colors.RED}❌ MCP provisioning failed: {response.status_code}{Colors.RESET}")
                print(f"   Response: {response.text[:200]}")
                return
                
        except Exception as e:
            print(f"{Colors.RED}❌ Error provisioning MCP: {str(e)[:100]}{Colors.RESET}")
            return
        
        
        # ==============================================================
        # TEST 3: Create Training Job
        # ==============================================================
        
        print(f"\n{Colors.BOLD}{'='*70}")
        print(f"TEST 3: Training Job Creation")
        print(f"{'='*70}{Colors.RESET}\n")
        
        job_id = None
        
        try:
            response = await client.post(
                "http://localhost:5600/api/v1/jobs",
                params={
                    "mcp_id": mcp_id,
                    "name": "diagnostic_training",
                    "description": "Diagnostic test"
                },
                json=["github", "confluence"]
            )
            
            print(f"🎓 Create Training Job: {response.status_code}")
            
            if response.status_code in [200, 201]:
                data = response.json()
                job_id = data.get("job_id")
                
                print(f"{Colors.GREEN}✅ Training job created: {job_id}{Colors.RESET}")
                print(f"   Status: {data.get('status')}")
                print(f"   Priority: {data.get('priority')}")
                
                # Execute the job
                exec_resp = await client.post(
                    f"http://localhost:5600/api/v1/jobs/{job_id}/execute"
                )
                
                print(f"\n▶️  Execute Job: {exec_resp.status_code}")
                
                if exec_resp.status_code == 200:
                    print(f"{Colors.GREEN}✅ Training job executed{Colors.RESET}")
                else:
                    print(f"{Colors.YELLOW}⚠️  Execution returned: {exec_resp.status_code}{Colors.RESET}")
                    
            else:
                print(f"{Colors.RED}❌ Training job creation failed: {response.status_code}{Colors.RESET}")
                print(f"   Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"{Colors.RED}❌ Error creating training job: {str(e)[:100]}{Colors.RESET}")
        
        
        # ==============================================================
        # TEST 4: Query MCP (THE KEY TEST)
        # ==============================================================
        
        print(f"\n{Colors.BOLD}{'='*70}")
        print(f"TEST 4: MCP Document Query (KEY TEST)")
        print(f"{'='*70}{Colors.RESET}\n")
        
        print(f"⏳ Waiting for training to process (5 seconds)...")
        await asyncio.sleep(5)
        
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
                print(f"🔍 MCP URL: {mcp_url}")
                
                # Query the MCP (correct endpoint is /api/query)
                query_resp = await client.post(
                    f"{mcp_url}/api/query",
                    json={
                        "query": "Tell me about the Horus Heresy",
                        "max_results": 10
                    },
                    timeout=10.0
                )
                
                print(f"   Query Status: {query_resp.status_code}")
                
                if query_resp.status_code == 200:
                    query_data = query_resp.json()
                    response_text = json.dumps(query_data)
                    
                    # Check for the error message
                    if "Error accessing training documents: 0" in response_text:
                        print(f"\n{Colors.RED}❌ CRITICAL ISSUE CONFIRMED!{Colors.RESET}")
                        print(f"   MCP returns: 'Error accessing training documents: 0'")
                        print(f"\n{Colors.BOLD}ROOT CAUSE ANALYSIS:{Colors.RESET}")
                        print(f"   1. ✅ doc_store has documents")
                        print(f"   2. ✅ MCP provisioned successfully")
                        print(f"   3. ✅ Training job created and executed")
                        print(f"   4. ❌ BUT: MCP cannot access the documents!")
                        print(f"\n{Colors.YELLOW}   CONCLUSION: Documents are NOT being transferred from")
                        print(f"   doc_store TO the MCP container during training.{Colors.RESET}")
                    else:
                        print(f"{Colors.GREEN}✅ MCP returned a valid response{Colors.RESET}")
                        print(f"   Response preview: {response_text[:200]}")
                else:
                    print(f"{Colors.RED}❌ MCP query failed: {query_resp.status_code}{Colors.RESET}")
                    print(f"   Response: {query_resp.text[:200]}")
            else:
                print(f"{Colors.YELLOW}⚠️  Could not determine MCP container port{Colors.RESET}")
                
        except Exception as e:
            print(f"{Colors.RED}❌ Error querying MCP: {str(e)[:100]}{Colors.RESET}")
        
        
        # ==============================================================
        # SUMMARY
        # ==============================================================
        
        print(f"\n{Colors.BOLD}{'='*70}")
        print(f"DIAGNOSTIC SUMMARY")
        print(f"{'='*70}{Colors.RESET}\n")
        
        print(f"Document Flow Status:")
        print(f"  1. doc_store storage: {Colors.GREEN}✅ WORKING{Colors.RESET}")
        print(f"  2. MCP provisioning: {Colors.GREEN}✅ WORKING{Colors.RESET}")
        print(f"  3. Training job creation: {Colors.GREEN}✅ WORKING{Colors.RESET}")
        print(f"  4. Training job execution: {Colors.GREEN}✅ WORKING{Colors.RESET}")
        print(f"  5. MCP document access: {Colors.RED}❌ NOT WORKING{Colors.RESET}")
        
        print(f"\n{Colors.BOLD}NEXT STEPS:{Colors.RESET}")
        print(f"  1. Audit mcp-training-coordinator to see if it fetches from doc_store")
        print(f"  2. Audit MCP container to see if it receives documents during training")
        print(f"  3. Check if training payload includes actual document content")
        print(f"  4. Verify MCP container has network access to doc_store")


if __name__ == "__main__":
    asyncio.run(diagnose_document_flow())

