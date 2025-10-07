---
llm_metadata:
  document_type: planning
  content_focus: historical
  platform:
    primary: mcp
    secondary: []
  status: archived
  created_date: '2024-09-01'
  archived_date: '2025-10-07'
  topics:
  - microservices
  - event_sourcing
  - fastapi
  - python
  - redis
  - postgresql
  - docker
  - rag
  - 5_tier_system
  concepts: []
  technologies: []
  services_mentioned: []
  semantic_summary: Planning document about historical aspects of the mcp platform
  archive_reason: consolidated
  historical_value: medium
  reference_value: medium
semantic_embedding:
  model: text-embedding-ada-002
  embedding_date: '2025-10-07'
  embedding_checksum: pending
rag_metadata:
  chunk_strategy: semantic
  optimal_chunk_size: 512
  retrieval_priority: medium
---

# 🎯 Client-Specific MCP Enhancement
## On-Demand Multi-Tenant Knowledge Isolation & Hyper-Personalization

**Document Type:** Architecture Enhancement  
**Status:** Design Complete  
**Parent Document:** [HIERARCHICAL_MCP_TRAINING_PIPELINE.md](./HIERARCHICAL_MCP_TRAINING_PIPELINE.md)  
**Enhancement:** Adds Client MCP tier with on-demand provisioning  
**Use Case:** Multi-client consultancy with client-specific contexts

---

## 📚 Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Multi-Client Challenge](#2-the-multi-client-challenge)
3. [Enhanced 5-Tier Architecture](#3-enhanced-5-tier-architecture)
4. [Client MCP (Tier 0)](#4-client-mcp-tier-0)
5. [On-Demand Provisioning System](#5-on-demand-provisioning-system)
6. [Client-Specific Knowledge Extraction](#6-client-specific-knowledge-extraction)
7. [Hyper-Personalized Query Routing](#7-hyper-personalized-query-routing)
8. [Multi-Tenancy & Data Isolation](#8-multi-tenancy--data-isolation)
9. [Resource Management](#9-resource-management)
10. [Implementation Guide](#10-implementation-guide)
11. [Example Workflows](#11-example-workflows)
12. [Migration from 4-Tier](#12-migration-from-4-tier)

---

## 1. Executive Summary

### 1.1 The Enhancement

**Problem:** Your company works with multiple clients, each with unique:
- Documentation (client-specific APIs, workflows)
- Features (custom implementations)
- Concepts (industry-specific terminology)
- Requirements (regulatory, compliance)

**Existing 4-tier MCP doesn't account for CLIENT dimension.**

**Solution:** Add **Client MCP (Tier 0)** with on-demand provisioning:

```
┌─────────────────────────────────────────────────────────────┐
│                   ENHANCED 5-TIER MCP                       │
└─────────────────────────────────────────────────────────────┘

Tier 4: Ecosystem MCP (Individual developer)
  "How does Alice write code?"
  
Tier 3: Team MCP (Development team)
  "What are our team's best practices?"
  
Tier 2: Company MCP (Your consultancy)
  "What are our enterprise standards?"
  
Tier 1: Project MCP (Specific project)
  "What does this project require?"
  
🆕 Tier 0: Client MCP (Specific client)
  "What does CLIENT X need?"
  "What are CLIENT X's APIs/workflows/concepts?"
  "What compliance rules apply to CLIENT X?"
```

**Key Enhancements:**
- ✅ **Client-specific MCPs** provisioned on-demand
- ✅ **Multi-tenant data isolation** (Client A data ≠ Client B data)
- ✅ **Hyper-personalized queries** (individual + team + company + project + **client**)
- ✅ **Resource-efficient** (spin up/down MCPs as needed)
- ✅ **Client tagging** (all knowledge tagged with client_id)

---

### 1.2 Updated Data Source → MCP Tier Mapping

| Data Source | Tiers | Knowledge Type | Client Tag? |
|-------------|-------|----------------|-------------|
| **GitHub** (your repos) | 4 → 3 | Code patterns | ❌ No |
| **GitHub** (client repos) | 4 → 3 → **0** | Client-specific code | ✅ **client_id** |
| **Jira** (internal) | 4 → 3 → 2 | Work patterns | ❌ No |
| **Jira** (client project) | 4 → 3 → 1 → **0** | Client work | ✅ **client_id** |
| **Confluence** (internal) | 4 → 3 → 2 | Team knowledge | ❌ No |
| **Confluence** (client space) | 3 → 2 → 1 → **0** | Client docs | ✅ **client_id** |
| **FullStory** (client app) | 1 → **0** | Client usage | ✅ **client_id** |
| **Client-specific docs** | **0 only** | Client APIs, workflows | ✅ **client_id** |

---

## 2. The Multi-Client Challenge

### 2.1 Real-World Scenario

**Your Company:** Software consultancy building custom solutions

**Clients:**
- **Client A:** Healthcare company (HIPAA compliance, HL7 APIs, medical terminology)
- **Client B:** FinTech startup (PCI DSS, payment gateways, financial regulations)
- **Client C:** E-commerce platform (Shopify integration, inventory systems)

**Problem:**

```
Developer asks MCP:
"How do I authenticate users?"

Without client context:
❌ Generic answer: "Use OAuth2 + JWT"
   (Doesn't help: Client A requires SAML + MFA, Client B uses Auth0)

With client context:
✅ Client A: "Use SAML 2.0 with MFA via Okta (HIPAA requirement)"
✅ Client B: "Use Auth0 with SMS verification (PCI DSS Level 1)"
✅ Client C: "Use Shopify OAuth for customer accounts"
```

**The Issue:**
- Client A's authentication != Client B's authentication
- Need **client-specific context** for hyper-relevant answers

---

### 2.2 Client-Specific Knowledge Types

**Development Side:**

1. **Client-specific APIs**
   - Client A: Epic EHR API, HL7 FHIR, Allscripts
   - Client B: Stripe API, Plaid API, Dwolla
   - Client C: Shopify API, WooCommerce, Magento

2. **Client-specific architecture**
   - Client A: Microservices with HIPAA-compliant data storage
   - Client B: Event-driven with fraud detection pipeline
   - Client C: Monolithic with CDN for images

3. **Client-specific deployment**
   - Client A: AWS GovCloud (HIPAA), encrypted EBS
   - Client B: Azure with PCI DSS compliance
   - Client C: Vercel + AWS S3

**Customer Experience Side:**

1. **Client-specific workflows**
   - Client A: Patient intake → Consent forms → Medical records
   - Client B: KYC verification → Account setup → Funding
   - Client C: Browse products → Add to cart → Checkout

2. **Client-specific terminology**
   - Client A: "Patient", "Encounter", "Diagnosis", "CPT code"
   - Client B: "Account holder", "Transaction", "Settlement", "Chargeback"
   - Client C: "Customer", "Order", "SKU", "Fulfillment"

3. **Client-specific compliance**
   - Client A: HIPAA, HITECH, state privacy laws
   - Client B: PCI DSS, SOX, AML/KYC
   - Client C: GDPR, CCPA, consumer protection

**All of this needs to be in a CLIENT-SPECIFIC MCP!**

---

## 3. Enhanced 5-Tier Architecture

### 3.1 Complete Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│              5-TIER HIERARCHICAL MCP                        │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  Tier 4: Ecosystem MCP (Individual)                      │
│  Scope: Personal patterns                                │
│  Example: "How does Alice write authentication code?"   │
│  Storage: Local (Alice's laptop)                         │
└────────────────────────┬─────────────────────────────────┘
                         │ Aggregates to
                         ▼
┌──────────────────────────────────────────────────────────┐
│  Tier 3: Team MCP (Team)                                 │
│  Scope: Team practices                                   │
│  Example: "What testing framework does the team use?"    │
│  Storage: Team server                                    │
└────────────────────────┬─────────────────────────────────┘
                         │ Aggregates to
                         ▼
┌──────────────────────────────────────────────────────────┐
│  Tier 2: Company MCP (Enterprise)                        │
│  Scope: Company-wide standards                           │
│  Example: "What's our security policy?"                  │
│  Storage: Company server                                 │
└────────────────────────┬─────────────────────────────────┘
                         │ Informs
                         ▼
┌──────────────────────────────────────────────────────────┐
│  Tier 1: Project MCP (Project)                           │
│  Scope: Project requirements                             │
│  Example: "What's the project timeline?"                 │
│  Storage: Project server                                 │
└────────────────────────┬─────────────────────────────────┘
                         │ Constrained by
                         ▼
┌──────────────────────────────────────────────────────────┐
│  🆕 Tier 0: Client MCP (Client-specific)                 │
│  Scope: Client context (APIs, workflows, compliance)     │
│  Example: "What's Client A's authentication method?"     │
│  Storage: Dynamic (provisioned on-demand)                │
│                                                          │
│  Instances:                                              │
│  ├─ client-a-mcp (Healthcare, HIPAA)                    │
│  ├─ client-b-mcp (FinTech, PCI DSS)                     │
│  └─ client-c-mcp (E-commerce, Shopify)                  │
└──────────────────────────────────────────────────────────┘
```

**Flow:**
1. **Individual writes code** → Tier 4 learns patterns
2. **Team aggregates** → Tier 3 identifies best practices
3. **Company synthesizes** → Tier 2 standardizes
4. **Project defines scope** → Tier 1 sets requirements
5. **Client provides context** → Tier 0 constrains solutions

---

### 3.2 Query Resolution (5-Tier)

**Query:** "How do I authenticate users for the payment dashboard?"

**Context:**
- User: Alice (Tier 4)
- Team: Backend Team (Tier 3)
- Company: Your Consultancy (Tier 2)
- Project: Payment Dashboard v2 (Tier 1)
- Client: FinTech Startup (Tier 0)

**Resolution Process:**

```
1. Query sent to Tier 0 (Client MCP)
   Client MCP checks: "What's FinTech Startup's auth?"
   → "Client uses Auth0 with SMS verification (PCI DSS Level 1)"
   
2. Client MCP queries Tier 1 (Project MCP)
   Project MCP checks: "What does Payment Dashboard v2 require?"
   → "Must support multi-tenant, role-based access"
   
3. Tier 1 queries Tier 2 (Company MCP)
   Company MCP checks: "What's our security policy?"
   → "Enforce OAuth2, JWT tokens, refresh tokens"
   
4. Tier 2 queries Tier 3 (Team MCP)
   Team MCP checks: "How does Backend Team handle auth?"
   → "Use FastAPI dependency injection, httpx for Auth0 API"
   
5. Tier 3 queries Tier 4 (Ecosystem MCP)
   Ecosystem MCP checks: "How does Alice write auth code?"
   → "Alice uses async/await, specific exception handling"
   
6. Synthesized recommendation (all 5 tiers):
   
   "For FinTech Startup's Payment Dashboard v2:
   
   1. CLIENT REQUIREMENT (Tier 0):
      • Use Auth0 (client's chosen provider)
      • Enable SMS verification (PCI DSS)
      • Store tokens securely (encrypted Redis)
   
   2. PROJECT REQUIREMENT (Tier 1):
      • Support multi-tenant (client_id in claims)
      • Implement RBAC (admin, user, auditor roles)
   
   3. COMPANY STANDARD (Tier 2):
      • Use OAuth2 authorization code flow
      • JWT access tokens (15 min expiry)
      • Refresh tokens (7 day expiry, rotate on use)
   
   4. TEAM PRACTICE (Tier 3):
      • FastAPI dependency for auth: get_current_user()
      • httpx.AsyncClient for Auth0 API calls
      • pytest fixtures for auth tests
   
   5. YOUR STYLE (Tier 4):
      • async/await for all I/O
      • Specific exceptions: AuthenticationError, AuthorizationError
      • Type hints on all functions
   
   Here's the complete code:
   
   [Generated code implementing all 5 tiers]"
```

**This is HYPER-PERSONALIZED!** Uses context from all 5 tiers.

---

## 4. Client MCP (Tier 0)

### 4.1 What Client MCP Stores

**For each client:**

```python
Client MCP (client-a-mcp) stores:

1. CLIENT PROFILE
   {
     "client_id": "client-a",
     "client_name": "HealthCare Corp",
     "industry": "Healthcare",
     "compliance": ["HIPAA", "HITECH", "State Privacy Laws"],
     "active": true,
     "provisioned_at": "2025-01-15T10:00:00Z"
   }

2. CLIENT-SPECIFIC APIS
   {
     "apis": [
       {
         "name": "Epic EHR API",
         "base_url": "https://fhir.epic.com",
         "auth_method": "SAML 2.0 + OAuth2",
         "docs_url": "https://fhir.epic.com/Documentation",
         "used_endpoints": [
           "GET /Patient/{id}",
           "POST /Appointment",
           "GET /Observation"
         ]
       },
       {
         "name": "Allscripts API",
         "base_url": "https://api.allscripts.com",
         "auth_method": "API Key + OAuth2"
       }
     ]
   }

3. CLIENT-SPECIFIC WORKFLOWS
   {
     "workflows": [
       {
         "name": "Patient Intake",
         "steps": [
           "Patient registration",
           "Insurance verification",
           "Consent forms",
           "Medical history collection",
           "Provider assignment"
         ],
         "systems": ["Epic EHR", "Internal Portal"]
       }
     ]
   }

4. CLIENT-SPECIFIC TERMINOLOGY
   {
     "terminology": {
       "patient": "Individual receiving medical care",
       "encounter": "Interaction between patient and provider",
       "diagnosis": "ICD-10 code for medical condition",
       "cpt_code": "Current Procedural Terminology code for billing"
     }
   }

5. CLIENT-SPECIFIC ARCHITECTURE
   {
     "architecture": {
       "deployment": "AWS GovCloud (HIPAA compliant)",
       "database": "PostgreSQL with encryption at rest",
       "storage": "S3 with HIPAA BAA",
       "networking": "VPC with private subnets",
       "monitoring": "CloudWatch with audit logs"
     }
   }

6. CLIENT-SPECIFIC COMPLIANCE
   {
     "compliance": {
       "hipaa": {
         "requirements": [
           "All PHI must be encrypted at rest and in transit",
           "Access logs must be retained for 6 years",
           "MFA required for all accounts",
           "Business Associate Agreement (BAA) required"
         ]
       }
     }
   }

7. CLIENT-SPECIFIC TEAM
   {
     "team": {
       "developers_assigned": ["alice", "bob", "charlie"],
       "client_contacts": [
         {"name": "Dr. Sarah Johnson", "role": "Medical Director"},
         {"name": "Tom Wilson", "role": "IT Manager"}
       ]
     }
   }
```

---

### 4.2 Client MCP Data Sources

**Where does client-specific knowledge come from?**

| Source | Client Tag | What to Extract |
|--------|------------|-----------------|
| **GitHub** (client repos) | `client_id: client-a` | Client-specific code, integrations |
| **Jira** (client project) | `project.client_id` | Client requirements, feedback |
| **Confluence** (client space) | `space.client_id` | Client docs, workflows, ADRs |
| **FullStory** (client app) | `app.client_id` | Client user behavior |
| **Client API docs** | `client_id` | APIs, schemas, examples |
| **Client contracts** | `client_id` | Compliance, SLAs, requirements |
| **Client meetings** | `client_id` | Decisions, feedback, roadmap |

**Example: Confluence page in "Client A - HealthCare Corp" space:**

```markdown
Title: "Patient Data Access API - Epic Integration"
Space: Client A - HealthCare Corp
Tags: ["api", "epic", "fhir", "patient-data"]

Content:
# Patient Data Access API

## Overview
We integrate with Epic's FHIR API to fetch patient data.

## Authentication
- SAML 2.0 for initial authentication
- OAuth2 for API access
- Requires MFA for all users (HIPAA requirement)

## Endpoints Used
- GET /Patient/{id} - Fetch patient demographics
- GET /Observation?patient={id} - Fetch lab results
- POST /Appointment - Create appointments

## Compliance Notes
- All requests must be logged (HIPAA audit requirement)
- Data must be encrypted in transit (TLS 1.3)
- Access tokens expire after 15 minutes
```

**Extractor identifies:**
- `client_id: client-a`
- `api: Epic FHIR API`
- `auth_method: SAML 2.0 + OAuth2 + MFA`
- `compliance: HIPAA (audit logs, encryption)`

**Routes to:**
- ✅ **Client MCP (Tier 0, client-a)**
- ✅ Project MCP (Tier 1, if project specified)
- ✅ Team MCP (Tier 3, team knowledge)

---

## 5. On-Demand Provisioning System

### 5.1 Dynamic MCP Creation

**Problem:** Can't have 100 Client MCPs running 24/7 (resource intensive)

**Solution:** Provision on-demand, cache, and spin down when idle

```
┌─────────────────────────────────────────────────────────────┐
│            CLIENT MCP PROVISIONING SERVICE                  │
│                 (mcp-provisioner)                           │
└─────────────────────────────────────────────────────────────┘

Components:
├─ MCP Registry (who needs an MCP?)
├─ Provisioning Engine (spin up/down)
├─ Resource Manager (monitor usage)
└─ Cache (keep hot MCPs in memory)

States:
├─ COLD: No MCP instance (client inactive)
├─ WARMING: MCP provisioning (takes 30-60 seconds)
├─ HOT: MCP running and ready
└─ COOLING: MCP idle, will shut down soon
```

---

### 5.2 Provisioning Workflow

**Scenario: Developer queries about Client A for first time today**

```
1. Developer query: "How do I fetch patient data for Client A?"
   
2. Query router checks: "Does client-a-mcp exist?"
   → No (client-a-mcp is COLD)
   
3. Provisioner starts: "Provision client-a-mcp"
   ├─ Create Docker container
   ├─ Load ChromaDB with client-a knowledge
   ├─ Load Neo4j with client-a relationships
   ├─ Start FastMCP server (port 3100)
   └─ Wait for health check (30 seconds)
   
4. Client-a-mcp state: COLD → WARMING → HOT
   
5. Query router retries: "Query client-a-mcp"
   → Success! Gets client-specific answer
   
6. Developer receives answer (45 seconds total)
   
7. Client-a-mcp remains HOT for next queries
   (Subsequent queries: <1 second)
   
8. After 30 minutes of inactivity:
   Client-a-mcp state: HOT → COOLING → COLD
   Container stopped, resources freed
```

---

### 5.3 Implementation: `mcp-provisioner` Service

```python
# services/mcp-provisioner/main.py

from fastapi import FastAPI, HTTPException
import docker
import asyncio
from typing import Dict, Optional
from enum import Enum

app = FastAPI(title="MCP Provisioner")

# Docker client
docker_client = docker.from_env()

# MCP registry
class MCPState(Enum):
    COLD = "cold"        # Not running
    WARMING = "warming"  # Starting up
    HOT = "hot"          # Running and ready
    COOLING = "cooling"  # Idle, will shut down

mcp_registry: Dict[str, Dict] = {}

# ============================================
# PROVISIONING
# ============================================

@app.post("/provision/{client_id}")
async def provision_client_mcp(client_id: str):
    """Provision a client-specific MCP on-demand"""
    
    # Check if already exists
    if client_id in mcp_registry:
        state = mcp_registry[client_id]['state']
        if state == MCPState.HOT:
            return {"status": "already_running", "client_id": client_id}
        elif state == MCPState.WARMING:
            return {"status": "provisioning", "client_id": client_id}
    
    # Start provisioning
    mcp_registry[client_id] = {
        'state': MCPState.WARMING,
        'started_at': datetime.now(),
        'last_accessed': datetime.now(),
        'query_count': 0
    }
    
    # Provision asynchronously
    asyncio.create_task(provision_mcp_async(client_id))
    
    return {"status": "provisioning_started", "client_id": client_id, "estimated_time": "30-60 seconds"}

async def provision_mcp_async(client_id: str):
    """Background task: provision MCP"""
    
    try:
        # 1. Fetch client profile
        client_profile = await fetch_client_profile(client_id)
        
        # 2. Create Docker container
        container = docker_client.containers.run(
            image="client-mcp:latest",
            name=f"client-{client_id}-mcp",
            environment={
                "CLIENT_ID": client_id,
                "CHROMADB_PATH": f"/data/{client_id}/chromadb",
                "NEO4J_URI": f"bolt://neo4j-{client_id}:7687",
                "PORT": get_available_port()
            },
            volumes={
                f"/data/clients/{client_id}": {"bind": f"/data/{client_id}", "mode": "rw"}
            },
            ports={f"{get_available_port()}/tcp": get_available_port()},
            detach=True,
            network="mcp-network"
        )
        
        # 3. Wait for health check
        max_retries = 30
        for i in range(max_retries):
            await asyncio.sleep(2)
            
            try:
                health = await check_health(client_id)
                if health['status'] == 'healthy':
                    break
            except:
                continue
        
        # 4. Mark as HOT
        mcp_registry[client_id]['state'] = MCPState.HOT
        mcp_registry[client_id]['container_id'] = container.id
        mcp_registry[client_id]['port'] = get_available_port()
        
        print(f"✅ Client MCP provisioned: {client_id}")
        
    except Exception as e:
        # Mark as failed
        mcp_registry[client_id]['state'] = MCPState.COLD
        mcp_registry[client_id]['error'] = str(e)
        print(f"❌ Failed to provision {client_id}: {e}")

# ============================================
# QUERY ROUTING (with auto-provision)
# ============================================

@app.post("/query/{client_id}")
async def query_client_mcp(client_id: str, query: Dict):
    """Query client MCP (auto-provision if needed)"""
    
    # Check state
    if client_id not in mcp_registry or mcp_registry[client_id]['state'] == MCPState.COLD:
        # Auto-provision
        await provision_client_mcp(client_id)
        
        # Wait for provisioning (max 60 seconds)
        for i in range(30):
            await asyncio.sleep(2)
            if mcp_registry[client_id]['state'] == MCPState.HOT:
                break
        
        if mcp_registry[client_id]['state'] != MCPState.HOT:
            raise HTTPException(status_code=503, detail="MCP provisioning timed out")
    
    # Get MCP endpoint
    port = mcp_registry[client_id]['port']
    
    # Forward query
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://localhost:{port}/query",
            json=query,
            timeout=30.0
        )
    
    # Update stats
    mcp_registry[client_id]['last_accessed'] = datetime.now()
    mcp_registry[client_id]['query_count'] += 1
    
    return response.json()

# ============================================
# RESOURCE MANAGEMENT (auto-shutdown)
# ============================================

async def monitor_and_cleanup():
    """Background task: shut down idle MCPs"""
    
    while True:
        await asyncio.sleep(60)  # Check every minute
        
        for client_id, info in list(mcp_registry.items()):
            if info['state'] != MCPState.HOT:
                continue
            
            # Check if idle
            idle_time = (datetime.now() - info['last_accessed']).seconds
            
            if idle_time > 1800:  # 30 minutes
                # Mark as COOLING
                info['state'] = MCPState.COOLING
                
                # Shut down after 5 more minutes
                await asyncio.sleep(300)
                
                if info['state'] == MCPState.COOLING:  # Still cooling (no new queries)
                    await shutdown_mcp(client_id)

async def shutdown_mcp(client_id: str):
    """Shut down client MCP"""
    
    container_id = mcp_registry[client_id]['container_id']
    
    # Stop container
    container = docker_client.containers.get(container_id)
    container.stop()
    container.remove()
    
    # Mark as COLD
    mcp_registry[client_id]['state'] = MCPState.COLD
    mcp_registry[client_id]['stopped_at'] = datetime.now()
    
    print(f"❄️ Client MCP shut down: {client_id}")

# Start background monitor
@app.on_event("startup")
async def startup():
    asyncio.create_task(monitor_and_cleanup())
```

---

### 5.4 Pre-Warming Strategy

**For active clients, pre-warm MCPs:**

```python
@app.post("/prewarm")
async def prewarm_mcps():
    """Pre-warm MCPs for active clients (e.g., at 8 AM)"""
    
    # Get active clients (worked on in last 7 days)
    active_clients = await get_active_clients(days=7)
    
    # Provision in parallel
    tasks = [
        provision_client_mcp(client_id)
        for client_id in active_clients
    ]
    
    results = await asyncio.gather(*tasks)
    
    return {
        "prewarmed": len(active_clients),
        "clients": active_clients
    }

# Cron job: Run at 8 AM every weekday
# 0 8 * * 1-5 curl -X POST http://localhost:5300/prewarm
```

---

## 6. Client-Specific Knowledge Extraction

### 6.1 Enhanced Extractors with Client Tagging

**Modify extractors to detect and tag client-specific knowledge:**

```python
# services/mcp-training-pipeline/domain/extractors/client_aware_github_extractor.py

class ClientAwareGitHubExtractor:
    """Extract GitHub knowledge with client awareness"""
    
    async def extract_from_pr(self, pr: Dict[str, Any]) -> List[Dict]:
        """Extract knowledge, tag with client_id if applicable"""
        
        knowledge_items = []
        
        # Detect if PR is client-specific
        client_id = await self._detect_client(pr)
        
        # Extract code patterns (as before)
        code_patterns = await self._extract_code_patterns(pr['files'])
        
        for pattern in code_patterns:
            knowledge_item = {
                'type': 'code_pattern',
                'scope': 'individual' if not client_id else 'client',
                'author': pr['author']['username'],
                'pattern': pattern,
                'client_id': client_id,  # 🆕 Client tag!
                'confidence': pattern['confidence'],
                'source': f"github_pr_{pr['number']}",
                'timestamp': pr['created_at']
            }
            knowledge_items.append(knowledge_item)
        
        return knowledge_items
    
    async def _detect_client(self, pr: Dict) -> Optional[str]:
        """Detect if PR is client-specific"""
        
        # Method 1: Check repo name
        repo_name = pr['repository']['name']
        if 'client-' in repo_name:
            return repo_name.split('client-')[1].split('-')[0]  # Extract client_id
        
        # Method 2: Check branch name
        branch = pr['head']['ref']
        if branch.startswith('client/'):
            return branch.split('/')[1]  # e.g., "client/client-a/feature"
        
        # Method 3: Check PR labels
        labels = [label['name'] for label in pr.get('labels', [])]
        for label in labels:
            if label.startswith('client:'):
                return label.split(':')[1]  # e.g., "client:client-a"
        
        # Method 4: Check files changed (client-specific directory)
        if pr.get('files'):
            for file in pr['files']:
                if file['filename'].startswith('clients/'):
                    return file['filename'].split('/')[1]  # e.g., "clients/client-a/..."
        
        return None  # Not client-specific
```

---

### 6.2 Client-Specific Confluence Extractor

**Extract from client-specific Confluence spaces:**

```python
class ClientAwareConfluenceExtractor:
    """Extract Confluence knowledge with client awareness"""
    
    async def extract_from_page(self, page: Dict) -> List[Dict]:
        """Extract knowledge from Confluence page"""
        
        knowledge_items = []
        
        # Detect client from space
        client_id = await self._detect_client_from_space(page['space'])
        
        if client_id:
            # This is client-specific documentation
            client_doc = await self._extract_client_documentation(page, client_id)
            knowledge_items.append({
                'type': 'client_documentation',
                'scope': 'client',
                'client_id': client_id,
                'documentation': client_doc,
                'confidence': 0.95,  # High confidence (official docs)
                'source': f"confluence_{page['id']}",
                'timestamp': page['updated']
            })
        
        return knowledge_items
    
    async def _detect_client_from_space(self, space: Dict) -> Optional[str]:
        """Detect client from Confluence space"""
        
        space_key = space.get('key', '').lower()
        space_name = space.get('name', '').lower()
        
        # Method 1: Space key pattern (e.g., "CLIENTA", "CLA")
        if space_key.startswith('client'):
            return space_key.replace('client', '')
        
        # Method 2: Space name pattern (e.g., "Client A - HealthCare Corp")
        if 'client' in space_name:
            # Extract client ID from name
            # "Client A - HealthCare Corp" → "client-a"
            client_letter = space_name.split('client')[1].strip().split()[0].lower()
            return f"client-{client_letter}"
        
        # Method 3: Space metadata (custom field)
        if 'metadata' in space and 'client_id' in space['metadata']:
            return space['metadata']['client_id']
        
        return None
    
    async def _extract_client_documentation(self, page: Dict, client_id: str) -> Dict:
        """Extract client-specific documentation"""
        
        content = page.get('content', {}).get('body', '')
        title = page.get('title', '')
        
        doc = {
            'title': title,
            'type': self._categorize_doc_type(title, content),
            'content_summary': self._summarize_content(content),
            'apis_mentioned': self._extract_api_mentions(content),
            'compliance_mentioned': self._extract_compliance_mentions(content),
            'workflows_described': self._extract_workflows(content)
        }
        
        return doc
    
    def _extract_api_mentions(self, content: str) -> List[Dict]:
        """Extract API mentions from content"""
        
        apis = []
        
        # Look for common API patterns
        # "Epic FHIR API", "Stripe API", "Shopify API"
        import re
        api_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+API'
        matches = re.findall(api_pattern, content)
        
        for match in matches:
            apis.append({
                'name': f"{match} API",
                'mentioned_in': 'documentation'
            })
        
        # Look for API endpoints
        # "GET /Patient/{id}", "POST /v1/charges"
        endpoint_pattern = r'(GET|POST|PUT|DELETE|PATCH)\s+(/[^\s\)]+)'
        endpoints = re.findall(endpoint_pattern, content)
        
        if endpoints:
            apis.append({
                'endpoints': [f"{method} {path}" for method, path in endpoints]
            })
        
        return apis
    
    def _extract_compliance_mentions(self, content: str) -> List[str]:
        """Extract compliance mentions"""
        
        compliance_keywords = ['HIPAA', 'PCI DSS', 'GDPR', 'SOC 2', 'CCPA', 'HITECH', 'SOX', 'ISO 27001']
        
        mentioned = []
        for keyword in compliance_keywords:
            if keyword in content:
                mentioned.append(keyword)
        
        return mentioned
```

---

## 7. Hyper-Personalized Query Routing

### 7.1 Enhanced Query Router with Client Context

**Route queries through all 5 tiers:**

```python
# services/mcp-training-pipeline/domain/routers/five_tier_mcp_router.py

class FiveTierMCPRouter:
    """Route queries through all 5 MCP tiers"""
    
    def __init__(self):
        self.mcp_provisioner_url = "http://localhost:5300"
        
        # MCP endpoints
        self.mcp_endpoints = {
            'ecosystem': "http://localhost:3000",  # Tier 4
            'team': "http://team-mcp:3000",        # Tier 3
            'company': "http://company-mcp:3000",  # Tier 2
            'project': "http://project-mcp:3000",  # Tier 1
            # Tier 0 (client) is dynamic
        }
    
    async def query_with_full_context(
        self,
        query: str,
        user: str,
        team: Optional[str] = None,
        project: Optional[str] = None,
        client: Optional[str] = None
    ) -> Dict:
        """
        Query all applicable MCP tiers and synthesize response.
        
        This is HYPER-PERSONALIZED!
        """
        
        responses = {}
        
        # 1. Query Tier 4 (Ecosystem/Individual)
        if user:
            responses['individual'] = await self._query_tier(
                'ecosystem',
                query,
                context={'user': user}
            )
        
        # 2. Query Tier 3 (Team)
        if team:
            responses['team'] = await self._query_tier(
                'team',
                query,
                context={'team': team}
            )
        
        # 3. Query Tier 2 (Company)
        responses['company'] = await self._query_tier(
            'company',
            query,
            context={}
        )
        
        # 4. Query Tier 1 (Project)
        if project:
            responses['project'] = await self._query_tier(
                'project',
                query,
                context={'project': project}
            )
        
        # 5. Query Tier 0 (Client) - AUTO-PROVISION IF NEEDED!
        if client:
            # Check if client MCP exists, provision if not
            client_mcp_url = await self._ensure_client_mcp(client)
            
            responses['client'] = await self._query_client_mcp(
                client_mcp_url,
                query,
                context={'client': client}
            )
        
        # 6. Synthesize response from all tiers
        synthesized = await self._synthesize_responses(
            query=query,
            responses=responses,
            priority_order=['client', 'project', 'company', 'team', 'individual']
        )
        
        return synthesized
    
    async def _ensure_client_mcp(self, client_id: str) -> str:
        """Ensure client MCP is running (provision if needed)"""
        
        # Query provisioner
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.mcp_provisioner_url}/query/{client_id}",
                json={"query": "health_check"},
                timeout=60.0  # May need to wait for provisioning
            )
        
        # Get client MCP URL
        client_mcp_port = response.json()['port']
        return f"http://localhost:{client_mcp_port}"
    
    async def _query_client_mcp(self, url: str, query: str, context: Dict) -> Dict:
        """Query client-specific MCP"""
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{url}/query",
                json={
                    'query': query,
                    'context': context
                },
                timeout=30.0
            )
        
        return response.json()
    
    async def _synthesize_responses(
        self,
        query: str,
        responses: Dict[str, Dict],
        priority_order: List[str]
    ) -> Dict:
        """
        Synthesize responses from all tiers.
        
        Priority: Client > Project > Company > Team > Individual
        (Client constraints override everything)
        """
        
        synthesis = {
            'query': query,
            'tiers_consulted': list(responses.keys()),
            'recommendations': []
        }
        
        # Add recommendations in priority order
        for tier in priority_order:
            if tier in responses:
                rec = responses[tier].get('recommendation')
                if rec:
                    synthesis['recommendations'].append({
                        'tier': tier,
                        'recommendation': rec,
                        'confidence': responses[tier].get('confidence', 0.5)
                    })
        
        # Generate combined recommendation
        synthesis['combined_recommendation'] = await self._generate_combined(
            query, synthesis['recommendations']
        )
        
        return synthesis
    
    async def _generate_combined(self, query: str, recommendations: List[Dict]) -> str:
        """Generate combined recommendation from all tiers"""
        
        # Use LLM to synthesize
        prompt = f"""
        Query: {query}
        
        Recommendations from all tiers:
        {json.dumps(recommendations, indent=2)}
        
        Synthesize a single, cohesive recommendation that:
        1. Respects client constraints (highest priority)
        2. Meets project requirements
        3. Follows company standards
        4. Uses team best practices
        5. Matches individual style
        
        Provide specific, actionable guidance.
        """
        
        llm_response = await self.llm_gateway.generate(prompt)
        
        return llm_response
```

---

### 7.2 Example: Hyper-Personalized Query

**Query:** "How do I authenticate users?"

**Context:**
- User: alice
- Team: backend-team
- Project: payment-dashboard-v2
- Client: client-b (FinTech startup)

**Routing:**

```python
router = FiveTierMCPRouter()

response = await router.query_with_full_context(
    query="How do I authenticate users?",
    user="alice",
    team="backend-team",
    project="payment-dashboard-v2",
    client="client-b"
)

# Response:
{
  "query": "How do I authenticate users?",
  "tiers_consulted": ["individual", "team", "company", "project", "client"],
  "recommendations": [
    {
      "tier": "client",
      "recommendation": "Client B (FinTech) uses Auth0 with SMS verification (PCI DSS Level 1 requirement). Must store tokens in encrypted Redis.",
      "confidence": 0.95
    },
    {
      "tier": "project",
      "recommendation": "Payment Dashboard v2 requires multi-tenant support (client_id in JWT claims) and role-based access control.",
      "confidence": 0.9
    },
    {
      "tier": "company",
      "recommendation": "Company standard: OAuth2 authorization code flow, JWT access tokens (15 min expiry), refresh tokens (7 day expiry with rotation).",
      "confidence": 0.95
    },
    {
      "tier": "team",
      "recommendation": "Backend team uses FastAPI dependency injection for auth (get_current_user()), httpx for Auth0 API calls, pytest fixtures for testing.",
      "confidence": 0.85
    },
    {
      "tier": "individual",
      "recommendation": "Alice prefers async/await for all I/O, specific exception handling (AuthenticationError, AuthorizationError), type hints.",
      "confidence": 0.9
    }
  ],
  "combined_recommendation": "
    For Client B's Payment Dashboard v2, implement authentication as follows:
    
    1. CLIENT REQUIREMENT (Highest Priority):
       - Use Auth0 (client's provider)
       - Enable SMS verification via Twilio (PCI DSS)
       - Store tokens in Redis with encryption (redis-om with cryptography)
       - Environment: AUTH0_DOMAIN, AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET
    
    2. PROJECT REQUIREMENT:
       - JWT claims must include: client_id, user_id, roles[]
       - Implement RBAC: admin, user, auditor
       - Endpoints: /auth/login, /auth/refresh, /auth/logout
    
    3. COMPANY STANDARD:
       - OAuth2 authorization code flow (not client credentials)
       - Access token: 15 min expiry
       - Refresh token: 7 days, rotate on use
       - Store refresh tokens in database for revocation
    
    4. TEAM PRACTICE:
       - FastAPI dependency:
         ```python
         async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
             # Verify JWT with Auth0 public key
             # Check expiry, signature
             # Return User object
         ```
       - Use httpx.AsyncClient for Auth0 API calls
       - pytest fixtures:
         ```python
         @pytest.fixture
         def mock_auth0():
             # Mock Auth0 responses
         ```
    
    5. YOUR STYLE (Alice):
       - Use async/await:
         ```python
         async def verify_token(token: str) -> Dict:
             async with httpx.AsyncClient() as client:
                 response = await client.get(...)
         ```
       - Specific exceptions:
         ```python
         class AuthenticationError(HTTPException):
             def __init__(self):
                 super().__init__(status_code=401, detail='Invalid credentials')
         ```
       - Type hints everywhere:
         ```python
         async def get_current_user(token: str) -> User:
         ```
    
    Complete implementation:
    [Generated code incorporating ALL 5 tiers]
  "
}
```

**This is MAXIMALLY RELEVANT!**
- ✅ Uses client's specific provider (Auth0)
- ✅ Meets client's compliance (PCI DSS SMS verification)
- ✅ Fulfills project's requirements (multi-tenant, RBAC)
- ✅ Follows company standards (OAuth2, token expiry)
- ✅ Uses team's practices (FastAPI dependencies, pytest)
- ✅ Matches individual's style (async/await, type hints)

---

## 8. Multi-Tenancy & Data Isolation

### 8.1 Strict Data Isolation

**Problem:** Client A's data must NEVER leak to Client B

**Solution:** 3-layer isolation

```
┌──────────────────────────────────────────────────────────┐
│              LAYER 1: CONTAINER ISOLATION                │
│  Each client MCP runs in separate Docker container       │
│  • client-a-mcp (container 1)                           │
│  • client-b-mcp (container 2)                           │
│  • client-c-mcp (container 3)                           │
│  No shared memory, no cross-container access             │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│              LAYER 2: DATABASE ISOLATION                 │
│  Each client has separate database instances             │
│  • ChromaDB: /data/clients/client-a/chromadb            │
│  • Neo4j: neo4j-client-a (separate instance)            │
│  No shared collections, no cross-client queries          │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│              LAYER 3: NETWORK ISOLATION                  │
│  Each client MCP on separate port                        │
│  • client-a-mcp: localhost:3100                         │
│  • client-b-mcp: localhost:3101                         │
│  • client-c-mcp: localhost:3102                         │
│  Firewall rules prevent cross-client access              │
└──────────────────────────────────────────────────────────┘
```

---

### 8.2 Access Control

**Who can query which Client MCP?**

```python
class ClientMCPAccessControl:
    """Control access to client-specific MCPs"""
    
    def __init__(self):
        # User → Client assignments
        self.user_clients = {
            'alice': ['client-a', 'client-b'],
            'bob': ['client-b', 'client-c'],
            'charlie': ['client-a']
        }
    
    async def check_access(self, user: str, client_id: str) -> bool:
        """Check if user can access client MCP"""
        
        # Check direct assignment
        if client_id in self.user_clients.get(user, []):
            return True
        
        # Check team assignment (team has access → all members have access)
        user_teams = await self.get_user_teams(user)
        for team in user_teams:
            if client_id in await self.get_team_clients(team):
                return True
        
        return False
    
    async def authorize_query(self, user: str, client_id: str):
        """Authorize query to client MCP"""
        
        if not await self.check_access(user, client_id):
            raise HTTPException(
                status_code=403,
                detail=f"User {user} does not have access to {client_id}"
            )
```

**Integration:**

```python
@app.post("/query/{client_id}")
async def query_client_mcp(
    client_id: str,
    query: Dict,
    user: str = Depends(get_current_user)
):
    """Query client MCP (with access control)"""
    
    # Check access
    await access_control.authorize_query(user, client_id)
    
    # Proceed with query
    response = await router.query_with_full_context(
        query=query['query'],
        user=user,
        client=client_id
    )
    
    return response
```

---

## 9. Resource Management

### 9.1 Capacity Planning

**Problem:** 100 clients × 5GB per MCP = 500GB RAM (too much!)

**Solution:** Dynamic provisioning with limits

```python
class ResourceManager:
    """Manage MCP resources"""
    
    def __init__(self):
        self.max_concurrent_mcps = 10  # Max 10 client MCPs running simultaneously
        self.max_memory_per_mcp = 5 * 1024 * 1024 * 1024  # 5GB
        self.max_total_memory = 50 * 1024 * 1024 * 1024  # 50GB total
    
    async def can_provision(self, client_id: str) -> bool:
        """Check if we can provision another MCP"""
        
        # Count running MCPs
        running = self.count_running_mcps()
        
        if running >= self.max_concurrent_mcps:
            # Find least recently used, shut it down
            await self.evict_lru_mcp()
        
        # Check total memory
        total_memory = self.get_total_memory_usage()
        
        if total_memory + self.max_memory_per_mcp > self.max_total_memory:
            # Need to free up memory
            await self.evict_lru_mcp()
        
        return True
    
    async def evict_lru_mcp(self):
        """Evict least recently used MCP"""
        
        # Find LRU
        lru_client = min(
            mcp_registry.items(),
            key=lambda x: x[1]['last_accessed']
        )[0]
        
        # Shut down
        await shutdown_mcp(lru_client)
        
        print(f"⏏️ Evicted LRU MCP: {lru_client}")
```

---

### 9.2 Pre-Warming for Active Clients

**Strategy:**
1. **Morning pre-warm (8 AM)**: Provision MCPs for clients worked on yesterday
2. **On-demand**: Provision for unexpected queries
3. **Evening shutdown (6 PM)**: Shut down all idle MCPs

```python
@app.post("/prewarm/smart")
async def smart_prewarm():
    """Pre-warm MCPs for likely-active clients"""
    
    # Get clients worked on in last 7 days
    recent_clients = await get_recent_clients(days=7)
    
    # Get clients with scheduled meetings today
    meeting_clients = await get_clients_with_meetings_today()
    
    # Combine and deduplicate
    clients_to_prewarm = list(set(recent_clients + meeting_clients))
    
    # Limit to top 10 (resource constraint)
    clients_to_prewarm = clients_to_prewarm[:10]
    
    # Provision
    tasks = [provision_client_mcp(c) for c in clients_to_prewarm]
    await asyncio.gather(*tasks)
    
    return {
        "prewarmed": len(clients_to_prewarm),
        "clients": clients_to_prewarm
    }

# Cron: 0 8 * * 1-5 (8 AM weekdays)
```

---

## 10. Implementation Guide

### 10.1 New Services Required

```
1. mcp-provisioner (port 5300)
   • Provision/shutdown client MCPs on-demand
   • Resource management
   • Access control

2. client-mcp-template (Docker image)
   • Template for client MCPs
   • FastMCP server
   • ChromaDB + Neo4j clients

3. Enhanced mcp-training-pipeline
   • Client-aware extractors
   • Client tagging logic
   • Routes to Tier 0 (client MCPs)
```

---

### 10.2 Docker Setup

**Client MCP Template (Dockerfile):**

```dockerfile
# services/client-mcp-template/Dockerfile

FROM python:3.11-slim

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install FastMCP
RUN pip install fastmcp chromadb neo4j httpx

# Copy MCP server code
COPY main.py /app/main.py
WORKDIR /app

# Environment variables (set at runtime)
ENV CLIENT_ID=""
ENV CHROMADB_PATH="/data/chromadb"
ENV NEO4J_URI="bolt://localhost:7687"
ENV PORT=3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s \
  CMD python -c "import httpx; httpx.get('http://localhost:${PORT}/health')"

# Start MCP server
CMD ["python", "main.py"]
```

**Client MCP Server:**

```python
# services/client-mcp-template/main.py

import os
from fastmcp import FastMCP
import chromadb
from neo4j import GraphDatabase

# Get client ID from environment
CLIENT_ID = os.getenv("CLIENT_ID")
CHROMADB_PATH = os.getenv("CHROMADB_PATH")
NEO4J_URI = os.getenv("NEO4J_URI")
PORT = int(os.getenv("PORT", 3000))

mcp = FastMCP(f"client-{CLIENT_ID}-mcp")

# Initialize storage
chroma = chromadb.Client(chromadb.Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory=CHROMADB_PATH
))

neo4j = GraphDatabase.driver(NEO4J_URI, auth=("neo4j", "password"))

# Collections
client_apis = chroma.get_or_create_collection(f"{CLIENT_ID}_apis")
client_workflows = chroma.get_or_create_collection(f"{CLIENT_ID}_workflows")
client_docs = chroma.get_or_create_collection(f"{CLIENT_ID}_docs")

# ============================================
# RESOURCES (Client-Specific Knowledge)
# ============================================

@mcp.resource(f"client://{CLIENT_ID}/apis")
async def get_client_apis():
    """Get this client's APIs"""
    
    # Query ChromaDB
    results = client_apis.query(
        query_texts=["APIs"],
        n_results=50
    )
    
    return {
        "uri": f"client://{CLIENT_ID}/apis",
        "client_id": CLIENT_ID,
        "apis": results['documents'],
        "count": len(results['documents'])
    }

@mcp.resource(f"client://{CLIENT_ID}/compliance")
async def get_client_compliance():
    """Get this client's compliance requirements"""
    
    # Query Neo4j
    with neo4j.session() as session:
        result = session.run(
            """
            MATCH (c:Client {id: $client_id})-[:REQUIRES_COMPLIANCE]->(comp:Compliance)
            RETURN comp.name as name, comp.requirements as requirements
            """,
            client_id=CLIENT_ID
        )
        
        compliance = [
            {"name": record["name"], "requirements": record["requirements"]}
            for record in result
        ]
    
    return {
        "uri": f"client://{CLIENT_ID}/compliance",
        "client_id": CLIENT_ID,
        "compliance": compliance
    }

# ============================================
# TOOLS (Client-Specific Actions)
# ============================================

@mcp.tool()
async def query_client_knowledge(query: str, knowledge_type: str = "all"):
    """Query this client's knowledge"""
    
    if knowledge_type == "apis" or knowledge_type == "all":
        api_results = client_apis.query(
            query_texts=[query],
            n_results=5
        )
    else:
        api_results = None
    
    if knowledge_type == "workflows" or knowledge_type == "all":
        workflow_results = client_workflows.query(
            query_texts=[query],
            n_results=5
        )
    else:
        workflow_results = None
    
    if knowledge_type == "docs" or knowledge_type == "all":
        doc_results = client_docs.query(
            query_texts=[query],
            n_results=5
        )
    else:
        doc_results = None
    
    return {
        "client_id": CLIENT_ID,
        "query": query,
        "apis": api_results['documents'] if api_results else [],
        "workflows": workflow_results['documents'] if workflow_results else [],
        "docs": doc_results['documents'] if doc_results else []
    }

# ============================================
# KNOWLEDGE INGESTION (from training pipeline)
# ============================================

@mcp.tool()
async def ingest_client_knowledge(knowledge_type: str, content: Dict, metadata: Dict):
    """Ingest knowledge into this client's MCP"""
    
    if knowledge_type == "api":
        client_apis.add(
            documents=[str(content)],
            metadatas=[{
                'client_id': CLIENT_ID,
                'type': knowledge_type,
                **metadata
            }],
            ids=[f"{CLIENT_ID}_{knowledge_type}_{metadata['timestamp']}"]
        )
    
    elif knowledge_type == "workflow":
        client_workflows.add(
            documents=[str(content)],
            metadatas=[{
                'client_id': CLIENT_ID,
                'type': knowledge_type,
                **metadata
            }],
            ids=[f"{CLIENT_ID}_{knowledge_type}_{metadata['timestamp']}"]
        )
    
    return {"status": "ingested", "client_id": CLIENT_ID, "type": knowledge_type}

# ============================================
# START MCP SERVER
# ============================================

if __name__ == "__main__":
    print(f"🚀 Starting Client MCP for {CLIENT_ID} on port {PORT}")
    mcp.run(transport="http", port=PORT)
```

---

## 11. Example Workflows

### 11.1 Complete Flow: Client-Specific PR → MCP

```
1. Developer (Alice) creates PR in client-a repo
   Repository: "client-a-healthcare-portal"
   Branch: "feature/epic-fhir-integration"
   Files: ["src/integrations/epic.py", "docs/epic-api.md"]
   
2. source-agent fetches PR
   
3. source-agent emits event to mcp-training-pipeline
   
4. GitHubExtractor analyzes PR:
   • _detect_client(pr) → "client-a" (from repo name)
   • Extracts code patterns (async Epic API calls)
   • Extracts API integration (Epic FHIR endpoints)
   
   knowledge_item = {
     'type': 'api_integration',
     'scope': 'client',
     'client_id': 'client-a',
     'api': 'Epic FHIR',
     'endpoints': ['GET /Patient/{id}', 'GET /Observation'],
     'auth_method': 'SAML 2.0 + OAuth2'
   }
   
5. ScopeClassifier determines: [CLIENT, ECOSYSTEM, TEAM]
   
6. MCPRouter routes to:
   • Client MCP (Tier 0, client-a) ← PRIMARY
   • Ecosystem MCP (Tier 4, Alice)
   • Team MCP (Tier 3, backend-team)
   
7. MCPRouter checks: "Is client-a-mcp running?"
   → No (COLD)
   
8. MCPRouter provisions: "Provision client-a-mcp"
   mcp-provisioner starts Docker container
   (30 seconds)
   
9. client-a-mcp receives knowledge:
   • Stores in ChromaDB (client_apis collection)
   • Creates relationship in Neo4j:
     (Client A)-[:USES_API]->(Epic FHIR)
     (Epic FHIR)-[:HAS_ENDPOINT]->(GET /Patient/{id})
   
10. Next time Alice queries:
    "How do I fetch patient data for Client A?"
    
    → client-a-mcp is already running (HOT)
    → Instant response (<1 second):
    
    "Client A uses Epic FHIR API.
    
    Endpoint: GET /Patient/{id}
    Auth: SAML 2.0 + OAuth2 (requires MFA)
    Compliance: HIPAA (log all requests, encrypt in transit)
    
    Code example (matches your style):
    ```python
    async def fetch_patient(patient_id: str) -> Patient:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f'https://fhir.epic.com/Patient/{patient_id}',
                    headers={'Authorization': f'Bearer {token}'}
                )
                response.raise_for_status()
                return Patient.from_fhir(response.json())
        except httpx.HTTPError as e:
            raise EpicAPIError(f'Failed to fetch patient: {e}')
    ```
    "
```

---

### 11.2 Query with Full 5-Tier Context

**Developer asks Cursor AI:**

```
"How do I implement the checkout flow for Client C?"
```

**Context:**
- User: alice
- Team: frontend-team
- Project: ecommerce-replatform
- Client: client-c (E-commerce, Shopify)

**Resolution:**

```
1. Cursor MCP client → Ecosystem MCP (Alice's laptop)
   
2. Ecosystem MCP → FiveTierMCPRouter
   
3. Router queries all 5 tiers:
   
   [Tier 0: Client C MCP]
   Q: "What's Client C's checkout flow?"
   A: "Client C uses Shopify Checkout API.
       Workflow: Cart → Shipping → Payment → Order Confirmation
       Integration: Shopify REST API + Webhooks
       Payment: Shopify Payments (PCI SAQ A compliant)"
   
   [Tier 1: Project MCP]
   Q: "What does ecommerce-replatform require?"
   A: "Must migrate from WooCommerce to Shopify.
       Keep existing cart structure.
       Timeline: 6 weeks, Sprint 3 focuses on checkout."
   
   [Tier 2: Company MCP]
   Q: "What's our e-commerce standard?"
   A: "Use headless commerce architecture.
       Decouple frontend from backend.
       API-first design.
       Track all events (analytics)."
   
   [Tier 3: Team MCP]
   Q: "How does frontend team handle checkout?"
   A: "React + Redux for state management.
       Stripe Elements for payment UI.
       Jest + React Testing Library for tests.
       Cypress for e2e."
   
   [Tier 4: Ecosystem MCP]
   Q: "How does Alice write checkout code?"
   A: "Alice prefers React Hooks (useState, useEffect).
       TypeScript for all components.
       Async/await for API calls.
       Error boundaries for payment errors."
   
4. Synthesized response:
   
   "For Client C's checkout (Shopify-based):
   
   CLIENT CONTEXT (Tier 0):
   • Use Shopify Checkout API (client's platform)
   • Workflow: Cart → Shipping → Payment → Confirmation
   • Payment via Shopify Payments (PCI compliant)
   • Webhooks for order updates
   
   PROJECT CONTEXT (Tier 1):
   • Migrating from WooCommerce → keep cart structure
   • Sprint 3 timeline (2 weeks)
   • Must support existing customer accounts
   
   COMPANY STANDARD (Tier 2):
   • Headless architecture (frontend decoupled)
   • API-first design
   • Track all checkout events (Google Analytics)
   
   TEAM PRACTICE (Tier 3):
   • React + Redux (checkout state in Redux store)
   • Use Stripe Elements UI components (even for Shopify)
   • Jest tests + Cypress e2e tests
   
   YOUR STYLE (Tier 4):
   • React Hooks (useState for form, useEffect for API)
   • TypeScript interfaces for all props/state
   • Async/await for Shopify API calls
   • Error boundaries around payment component
   
   Complete implementation:
   
   [Generated code with 5 tiers of context]
   
   ```typescript
   // CheckoutFlow.tsx (Alice's style + all constraints)
   
   import React, { useState, useEffect } from 'react';
   import { useDispatch, useSelector } from 'react-redux';
   import { ShopifyCheckout } from './integrations/shopify';
   import { trackEvent } from './analytics';
   
   interface CheckoutProps {
     cartId: string;
   }
   
   export const CheckoutFlow: React.FC<CheckoutProps> = ({ cartId }) => {
     const [step, setStep] = useState<'shipping' | 'payment' | 'confirmation'>('shipping');
     const cart = useSelector(state => state.cart);
     const dispatch = useDispatch();
     
     useEffect(() => {
       // Track checkout started (company requirement)
       trackEvent('checkout_started', { cart_id: cartId });
     }, []);
     
     const handleShippingSubmit = async (shippingInfo: ShippingInfo) => {
       try {
         // Call Shopify API (client requirement)
         const checkout = await ShopifyCheckout.updateShipping(cartId, shippingInfo);
         setStep('payment');
         trackEvent('shipping_completed');
       } catch (error) {
         // Your error handling style
         handleCheckoutError(error);
       }
     };
     
     // ... rest of implementation
   };
   ```
   "
```

**This is the ULTIMATE in hyper-personalization!**

---

## 12. Migration from 4-Tier

### 12.1 Backward Compatibility

**Existing 4-tier queries still work:**

```python
# Old API (4-tier)
response = await router.query_with_full_context(
    query="How do I write tests?",
    user="alice",
    team="backend-team",
    project="api-v2"
    # No client parameter
)
# Works fine, just skips Tier 0

# New API (5-tier)
response = await router.query_with_full_context(
    query="How do I write tests?",
    user="alice",
    team="backend-team",
    project="api-v2",
    client="client-a"  # NEW!
)
# Uses all 5 tiers
```

---

### 12.2 Gradual Rollout

**Phase 1: Deploy infrastructure (Week 1-2)**
- Deploy `mcp-provisioner` service
- Build `client-mcp-template` Docker image
- Deploy to staging

**Phase 2: Tag existing data (Week 3-4)**
- Backfill client tags on historical data
- Run script to tag GitHub repos, Jira projects, Confluence spaces
- Verify client detection logic

**Phase 3: Provision first client MCP (Week 5)**
- Choose pilot client (most active)
- Provision manually
- Test queries
- Gather feedback

**Phase 4: Roll out to all clients (Week 6-8)**
- Provision MCPs for all active clients
- Enable on-demand provisioning
- Monitor resource usage
- Adjust capacity

**Phase 5: Integrate into workflows (Week 9-12)**
- Update Cursor IDE integration
- Train developers on client context
- Create documentation
- Measure improvement

---

## 13. Conclusion

### 13.1 Summary

You can enhance the Hierarchical MCP with **Client-Specific MCPs (Tier 0)** that:

✅ **Isolate client-specific knowledge** (APIs, workflows, compliance)  
✅ **Provision on-demand** (spin up when needed, shut down when idle)  
✅ **Provide hyper-personalized recommendations** (individual + team + company + project + **client**)  
✅ **Maintain strict data isolation** (container, database, network)  
✅ **Scale efficiently** (max 10 concurrent MCPs, LRU eviction)  

**Architecture:**
- **5-tier hierarchy**: Ecosystem → Team → Company → Project → **Client**
- **On-demand provisioning**: `mcp-provisioner` service
- **Client-aware extractors**: Tag knowledge with `client_id`
- **Hyper-personalized routing**: Query all 5 tiers, synthesize

**Use Cases:**
- Multi-client consultancy
- Client-specific APIs, workflows, compliance
- Development + customer experience contexts
- Maximally relevant recommendations

**Timeline:** 12 weeks (gradual rollout)

---

📍 **Location:** `/docs/CLIENT_SPECIFIC_MCP_ENHANCEMENT.md`  
📄 **Status:** Design complete, ready for implementation  
🎯 **Enhancement:** Adds Client MCP (Tier 0) with on-demand provisioning  
📊 **Scope:** Multi-client consultancy with client-specific contexts  
⏱️ **Timeline:** 12 weeks (5 phases)  
🔒 **Isolation:** 3-layer (container, database, network)  

**This makes your MCP architecture COMPLETE for a multi-client consultancy!** 🚀

