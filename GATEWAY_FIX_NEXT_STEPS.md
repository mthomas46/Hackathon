# Gateway Fix - Next Steps

**Date**: October 8, 2025  
**Status**: Plan Complete, Ready for Implementation  
**Context**: 100+ tool calls completed, approaching token limit

---

## 🎯 What Was Accomplished

### ✅ Phase 1: Problem Identification & Solution Design

1. **✅ Identified Root Causes**
   - MCP deployment: FIXED (100% success)
   - MCP queries: WORKING via direct access (12/12 success)
   - Gateway routing: ROOT CAUSE IDENTIFIED (architectural issue)
   - Training data: NOT BEING USED (mcp-base is a mock)

2. **✅ User Proposal Evaluated**
   > "the mcp-provisioner and the mcp-registry should work together to dynamically add the provisioned mcp to the gateway"
   
   **Evaluation**: ✅ **APPROVED** - Architecturally sound, follows microservice patterns

3. **✅ Comprehensive Plan Created**
   - File: `ARCHITECTURAL_FIX_PLAN.md`
   - Full implementation strategy documented
   - Test cases defined
   - Success criteria established

---

## 📋 Implementation Tasks (Documented)

### Task 1: Create Gateway Client ⏳
**File**: `services/mcp-provisioner/infrastructure/external_services/gateway_client.py`

```python
import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class GatewayClient:
    """Client for registering MCPs with the gateway."""
    
    def __init__(self, gateway_url: str = "http://mcp-gateway:8001"):
        self.gateway_url = gateway_url
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def register_mcp(
        self,
        mcp_id: str,
        host: str,
        port: int,
        name: str,
        tier: int,
        health_check_url: str,
        tags: list[str] = None,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Register MCP instance with gateway.
        
        Returns:
            bool: True if registration successful
        """
        try:
            response = await self.client.post(
                f"{self.gateway_url}/api/v1/gateway/register",
                json={
                    "mcp_id": mcp_id,
                    "host": host,
                    "port": port,
                    "name": name,
                    "tier": tier,
                    "priority": 100,
                    "weight": 100,
                    "max_concurrent_requests": 50,
                    "health_check_url": health_check_url,
                    "tags": tags or [],
                    "metadata": metadata or {}
                }
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Successfully registered MCP {mcp_id} with gateway")
                return True
            else:
                logger.warning(f"Failed to register MCP {mcp_id}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error registering MCP {mcp_id} with gateway: {e}")
            return False
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
```

### Task 2: Integrate into Provisioner ⏳
**File**: `services/mcp-provisioner/application/use_cases/provision_mcp_use_case.py`

**Add to `__init__`**:
```python
from services.mcp_provisioner.infrastructure.external_services.gateway_client import GatewayClient

class ProvisionMCPUseCase:
    def __init__(
        self,
        repository: MCPRepository,
        gateway_client: Optional[GatewayClient] = None
    ):
        self.repository = repository
        self.gateway_client = gateway_client or GatewayClient()
```

**Add after container deployment (after line 105)**:
```python
# Step 4.5: Deploy Docker container
container_id = await self._deploy_docker_container(mcp_instance)
if container_id:
    logger.info(f"Successfully deployed container {container_id[:12]} for MCP {mcp_id}")
    
    # Update entity with container info
    mcp_instance.container_id = container_id
    mcp_instance.metadata["container_id"] = container_id
    mcp_instance.metadata["status"] = "deployed"
    mcp_instance.metadata["deployment_time"] = asyncio.get_event_loop().time()
    
    # Get container port
    mcp_port = await self._get_container_port(container_id)
    
    # Step 4.6: Register with Gateway (NEW!)
    if mcp_port:
        gateway_success = await self.gateway_client.register_mcp(
            mcp_id=mcp_id,
            host="localhost",  # Or use actual Docker network hostname
            port=mcp_port,
            name=f"{request.client_id} MCP (Tier {request.tier})",
            tier=request.tier,
            health_check_url=f"http://localhost:{mcp_port}/health",
            tags=[request.client_id, f"tier-{request.tier}", "auto-provisioned"],
            metadata=mcp_instance.metadata
        )
        
        if gateway_success:
            logger.info(f"MCP {mcp_id} registered with gateway")
            mcp_instance.metadata["gateway_registered"] = True
        else:
            logger.warning(f"Failed to register MCP {mcp_id} with gateway")
            mcp_instance.metadata["gateway_registered"] = False
    
    # Transition to HOT state
    object.__setattr__(mcp_instance, 'state', hot_state())
    logger.info(f"MCP {mcp_id} transitioned to HOT state")
```

**Add helper method**:
```python
async def _get_container_port(self, container_id: str) -> Optional[int]:
    """Get the mapped port for an MCP container."""
    try:
        # Use docker port command
        result = subprocess.run(
            ['docker', 'port', container_id],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if '3000/tcp' in line or '8080/tcp' in line:
                    port_str = line.split(':')[-1].strip()
                    if port_str:
                        return int(port_str)
        
        return None
    except Exception as e:
        logger.error(f"Error getting container port: {e}")
        return None
```

### Task 3: Fix MCP-Base Image ⏳
**File**: `docker/mcp-base/Dockerfile`

**Option A: Use doc_store service** (RECOMMENDED for current architecture):

```dockerfile
# MCP Base Image - Connect to doc_store for training data

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    httpx==0.25.2 \
    pydantic==2.5.0

# Create MCP server that queries doc_store
RUN echo 'from fastapi import FastAPI, HTTPException\n\
import os\n\
import httpx\n\
import logging\n\
\n\
logging.basicConfig(level=logging.INFO)\n\
logger = logging.getLogger(__name__)\n\
\n\
app = FastAPI()\n\
\n\
mcp_id = os.getenv("MCP_ID", "unknown")\n\
mcp_tier = os.getenv("MCP_TIER", "0")\n\
doc_store_url = os.getenv("DOC_STORE_URL", "http://doc_store:8007")\n\
\n\
@app.get("/health")\n\
async def health():\n\
    return {"status": "healthy", "mcp_id": mcp_id, "tier": mcp_tier}\n\
\n\
@app.post("/api/query")\n\
async def query(body: dict):\n\
    query_text = body.get("query", "")\n\
    logger.info(f"MCP {mcp_id} received query: {query_text[:100]}")\n\
    \n\
    try:\n\
        # Query doc_store for relevant documents\n\
        async with httpx.AsyncClient(timeout=10.0) as client:\n\
            response = await client.post(\n\
                f"{doc_store_url}/search",\n\
                json={\n\
                    "query": query_text,\n\
                    "mcp_id": mcp_id,\n\
                    "limit": 5\n\
                }\n\
            )\n\
            \n\
            if response.status_code == 200:\n\
                docs = response.json()\n\
                \n\
                if docs and len(docs) > 0:\n\
                    # Use actual document content\n\
                    answer = docs[0].get("content", "No content available")\n\
                    sources = [d.get("source", "unknown") for d in docs[:3]]\n\
                    confidence = 0.85\n\
                else:\n\
                    # Fallback if no docs found\n\
                    answer = f"No relevant documents found for query: {query_text}"\n\
                    sources = []\n\
                    confidence = 0.0\n\
            else:\n\
                # Fallback if doc_store unavailable\n\
                answer = f"Document store unavailable. MCP {mcp_id} cannot process query."\n\
                sources = ["fallback"]\n\
                confidence = 0.0\n\
    \n\
    except Exception as e:\n\
        logger.error(f"Error querying doc_store: {e}")\n\
        answer = f"Error accessing training documents: {str(e)}"\n\
        sources = ["error"]\n\
        confidence = 0.0\n\
    \n\
    return {\n\
        "mcp_id": mcp_id,\n\
        "query": query_text,\n\
        "answer": answer,\n\
        "confidence": confidence,\n\
        "sources": sources\n\
    }\n\
\n\
@app.get("/")\n\
async def root():\n\
    return {"mcp_id": mcp_id, "tier": mcp_tier, "status": "running", "doc_store": doc_store_url}\n\
' > /app/main.py

EXPOSE 8080
EXPOSE 3000

# Use MCP_PORT environment variable or default to 8080
CMD python -m uvicorn main:app --host 0.0.0.0 --port ${MCP_PORT:-8080}
```

**Update provisioner to set DOC_STORE_URL** in `_deploy_docker_container`:
```python
environment = {
    "MCP_ID": mcp_instance.mcp_id,
    "MCP_TIER": str(mcp_instance.config.tier),
    "MCP_PORT": str(mcp_port),
    "DOC_STORE_URL": "http://doc_store:8007"  # NEW!
}
```

### Task 4: Test End-to-End ⏳
**File**: `tests/integration/test_gateway_integration.py`

```python
"""Integration tests for gateway registration and routing."""

import pytest
import httpx
import asyncio

@pytest.mark.asyncio
async def test_mcp_auto_registers_with_gateway():
    """Test that provisioned MCPs automatically register with gateway."""
    
    # 1. Provision MCP
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:5400/api/v1/mcps",
            json={
                "client_id": "gateway-test",
                "tier": 2,
                "memory_limit": "2048M",
                "cpu_shares": 1024,
                "image_name": "mcp-base:latest"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        mcp_id = data["data"]["mcp_id"]
        
        # 2. Wait for health check
        await asyncio.sleep(5)
        
        # 3. Check gateway knows about MCP
        gateway_response = await client.get(
            f"http://localhost:8001/api/v1/gateway/instances?mcp_id={mcp_id}"
        )
        
        assert gateway_response.status_code == 200
        instances = gateway_response.json()
        assert len(instances) > 0
        assert instances[0]["mcp_id"] == mcp_id

@pytest.mark.asyncio
async def test_gateway_routes_to_registered_mcp():
    """Test that gateway can route queries to registered MCPs."""
    
    # Assumes MCP already provisioned and registered
    mcp_id = "mcp-gateway-test-xyz"  # From previous test
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/api/v1/gateway/route",
            json={
                "mcp_id": mcp_id,
                "method": "POST",
                "path": "/api/query",
                "body": {"query": "What is the Horus Heresy?"},
                "timeout_seconds": 30
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "answer" in data["body"]
```

### Task 5: Update Demo ⏳
**File**: `demo_horus_heresy_enhanced.py`

```python
async def query_mcp_for_document(self, query: str, max_results: int = 10, fail_on_error: bool = False) -> Optional[Dict[str, Any]]:
    """
    Query the trained MCP via GATEWAY (proper architecture).
    
    Falls back to direct querying if gateway unavailable.
    """
    # Try gateway first (PROPER ARCHITECTURE)
    if self.service_status.get('mcp-gateway'):
        try:
            response = await self.client.post(
                f"{self.services['mcp-gateway']}/api/v1/gateway/route",
                json={
                    "mcp_id": self.mcp_id,
                    "method": "POST",
                    "path": "/api/query",
                    "body": {
                        "query": query,
                        "max_results": max_results
                    },
                    "tier": 2,
                    "timeout_seconds": 30
                },
                timeout=35.0
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success") and result.get("body"):
                    # Gateway successfully routed
                    return result["body"]
        except Exception as e:
            self.print_warning(f"Gateway routing failed: {str(e)[:100]}")
    
    # Fallback: Direct query (if gateway unavailable)
    if self.mcp_url:
        try:
            response = await self.client.post(
                f"{self.mcp_url}/api/query",
                json={"query": query, "max_results": max_results},
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            if fail_on_error:
                raise RuntimeError(f"MCP query failed: {e}")
    
    return None
```

---

## 🧪 Testing Commands

```bash
# 1. Rebuild mcp-base image
cd docker/mcp-base
docker build -t mcp-base:latest .

# 2. Rebuild mcp-provisioner with gateway client
cd ../../
docker-compose -f docker-compose-mcp-ecosystem.yml build mcp-provisioner

# 3. Restart services
docker-compose -f docker-compose-mcp-ecosystem.yml up -d mcp-provisioner mcp-gateway doc_store

# 4. Run integration tests
pytest tests/integration/test_gateway_integration.py -v -s

# 5. Run full demo
python3 demo_horus_heresy_enhanced.py
```

---

## 📊 Expected Results

### Before Gateway Fix
```
❌ MCP Queries: via direct access (workaround)
❌ Gateway: No instances registered
❌ Responses: Generic mock text
```

### After Gateway Fix
```
✅ MCP Queries: via gateway (proper architecture)
✅ Gateway: Auto-registers MCPs on provision
✅ Responses: Real training document content
✅ Demo: 12/12 queries via gateway with real data
```

---

## 🎯 Next Session Tasks

1. **Implement gateway_client.py** (~15 min)
2. **Integrate into provision_mcp_use_case.py** (~20 min)
3. **Update mcp-base Dockerfile** (~15 min)
4. **Rebuild images** (~5 min)
5. **Test integration** (~15 min)
6. **Update demo** (~10 min)
7. **Validate end-to-end** (~15 min)

**Total Estimated Time**: ~1.5 hours

---

## 💡 Key Implementation Notes

1. **Gateway Registration**
   - Happens automatically after container deployment
   - Includes health check URL for gateway monitoring
   - Metadata includes tier, tags, and provisioning info

2. **MCP-Base Image**
   - Connects to `doc_store` service
   - Searches for relevant documents
   - Returns actual training content
   - Graceful fallback if doc_store unavailable

3. **Gateway Discovery**
   - Gateway tracks instances in Redis
   - Health checker marks instances as AVAILABLE
   - Routing uses least_loaded strategy by default

4. **Demo Updates**
   - Try gateway routing first (proper)
   - Fallback to direct if gateway unavailable
   - Clear feedback on which method used

---

## 📝 Files to Create/Modify

### New Files
1. `services/mcp-provisioner/infrastructure/external_services/gateway_client.py`
2. `tests/integration/test_gateway_integration.py`

### Modified Files
1. `services/mcp-provisioner/application/use_cases/provision_mcp_use_case.py`
2. `docker/mcp-base/Dockerfile`
3. `demo_horus_heresy_enhanced.py`

---

**Status**: Ready for next session implementation  
**Documentation**: Complete  
**Architecture**: Validated  
**User Proposal**: Approved and enhanced

