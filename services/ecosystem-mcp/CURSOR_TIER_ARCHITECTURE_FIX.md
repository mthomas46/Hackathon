# Cursor Tier 1 - Architecture Issue & Fix

**Date:** October 14, 2025  
**Issue:** Tier 1 (Cursor IDE) shows as red/unavailable in dashboard  
**Root Cause:** Architectural misunderstanding  

---

## 🔍 Problem Analysis

### Current Behavior
The RAG Query page shows "Tier 1: Cursor IDE" as ❌ red/unavailable.

### What the Code is Doing
```python
# cursor_client.py line 42-58
async def is_available(self) -> bool:
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(f"{self.base_url}/health")
        available = response.status_code == 200
        return available
```

The code tries to check if Cursor IDE is available by:
1. Making HTTP GET request to `http://host.docker.internal:3000/health`
2. Expecting Cursor IDE to respond with 200 OK
3. Marking tier as available if response is successful

### Why This Fails
**Cursor IDE doesn't have an HTTP API server!**

---

## 📚 Actual Architecture

### From CURSOR_MCP_SETUP_COMPLETE.md:

```
┌─────────────┐         stdio         ┌──────────────┐      HTTP       ┌─────────────────┐
│  Cursor IDE │ ──────────────────────> │  MCP Server  │ ───────────────> │ ecosystem-mcp   │
│             │   (JSON-RPC requests)  │  (Python)    │  (API calls)    │ API :8000       │
└─────────────┘                        └──────────────┘                 └─────────────────┘
```

**The flow is:**
1. **Cursor IDE** → calls MCP server (via stdio/JSON-RPC)
2. **MCP Server** (`mcp_server.py`) → calls ecosystem-mcp API (HTTP)
3. **ecosystem-mcp API** → processes query and returns result

**NOT:**
- ~~ecosystem-mcp → calls Cursor IDE~~
- ~~Cursor IDE hosts an HTTP server~~

---

## 🎯 The Confusion

### What "Tier 1: Cursor IDE" Was Intended To Mean
"Use Claude 4.5 Sonnet (premium model) via Cursor IDE's credentials"

### What It Actually Should Mean in This Architecture
**Nothing - the tier doesn't make sense!**

**Why:**
- The 3-tier routing is for ecosystem-mcp to CALL different LLM backends
- Cursor IDE is not a backend that ecosystem-mcp calls
- Cursor IDE calls ecosystem-mcp (via MCP), not the other way around
- This is a fundamental architectural mismatch

---

## 🔄 Correct Architecture

### Tier System (for ecosystem-mcp calling OUT):
```
Tier 3: Docker Ollama (http://ollama:11434)
   ↑
Tier 2: Desktop Ollama (http://host.docker.internal:11435)  
   ↑
Tier 1: ??? (Should be a premium API like Claude/GPT-4, NOT Cursor)
```

### MCP Integration (for Cursor calling IN):
```
Cursor IDE → MCP Server → ecosystem-mcp API → (uses tier system) → Returns result
```

**These are separate flows!**

---

## ❌ What's Wrong

1. **Conceptual Error**: "Cursor Tier" tries to call Cursor, but Cursor calls us
2. **Health Check Error**: Checking `http://localhost:3000/health` makes no sense
3. **UI Confusion**: Dashboard shows Cursor as unavailable when it's actually working fine (via MCP)
4. **Naming Error**: "Tier 1" suggests premium model access, but provides no implementation

---

## ✅ Solutions

### Option 1: Remove Cursor Tier (Recommended)

**Rationale:** Clean separation of concerns

**Changes:**
1. Remove Cursor from 3-tier routing system
2. Keep MCP server for Cursor → ecosystem-mcp calls
3. Use Tier 1 for actual premium API (Claude/GPT-4 if available)
4. Update dashboard to remove Cursor tier status

**Benefits:**
- ✅ Architecturally correct
- ✅ No confusing "unavailable" status
- ✅ Clear separation: Tiers = outbound, MCP = inbound
- ✅ Can add real Tier 1 (Claude API, GPT-4, etc.)

---

### Option 2: Rename and Clarify

**Rationale:** Keep the tier but fix messaging

**Changes:**
1. Rename "Tier 1: Cursor IDE" → "Tier 1: Claude API (via Anthropic)"
2. Remove Cursor-specific health check
3. Check for actual Anthropic API key
4. Use `anthropic_api_key` from settings
5. Update UI to show "Not configured" instead of "Unavailable"

**Benefits:**
- ✅ Provides actual premium tier
- ✅ Clear naming
- ✅ Real functionality (if API key provided)

---

### Option 3: Make Cursor "Always Available" 

**Rationale:** Mark as available if enabled, since we can't actually check

**Changes:**
```python
async def is_available(self) -> bool:
    # Cursor calls US via MCP, we don't call Cursor
    # So if enabled, assume it's available
    return settings.cursor_enabled
```

**Benefits:**
- ✅ Quick fix
- ❌ Still architecturally wrong
- ❌ Doesn't actually route to Cursor (can't!)

---

## 🎯 Recommended Fix: Option 1

### Step 1: Remove Cursor from Tier System

**File:** `src/config.py`
```python
# REMOVE these settings (lines 82-103):
cursor_enabled: bool = Field(...)
cursor_mcp_url: str = Field(...)
cursor_model: str = Field(...)
cursor_complexity_threshold: float = Field(...)
cursor_fallback_enabled: bool = Field(...)
```

**File:** `src/services/models/cursor_client.py`
```python
# REMOVE entire file - not used for outbound calls
```

**File:** `src/services/models/ollama_router.py`
```python
# REMOVE Cursor references from router
# Keep only Desktop and Docker tiers
```

### Step 2: Update Dashboard

**File:** `services/ecosystem-mcp-dashboard/pages/rag.py`
```python
# Change from 3 columns to 2 columns:
col1, col2 = st.columns(2)  # was: col1, col2, col3

with col1:
    desktop_tier = tiers.get("desktop", {})
    if desktop_tier.get("available"):
        st.success("✅ **Tier 1: Desktop Ollama (GPU)**")
    else:
        st.warning("⚠️ **Tier 1: Desktop Ollama (GPU)**")
    st.caption(f"Model: {desktop_tier.get('model', 'Unknown')}")
    st.caption(desktop_tier.get('use_case', ''))

with col2:
    docker_tier = tiers.get("docker", {})
    if docker_tier.get("available"):
        st.success("✅ **Tier 2: Docker Ollama (CPU)**")
    else:
        st.error("❌ **Tier 2: Docker Ollama (CPU)**")
    st.caption(f"Model: {docker_tier.get('model', 'Unknown')}")
    st.caption(docker_tier.get('use_case', ''))
```

### Step 3: Update Tier Status Endpoint

**File:** `src/api/routes/query_enhanced.py`
```python
@router.get("/query/tier-status")
async def check_tier_status():
    """Check availability of all LLM tiers."""
    ollama_router = get_ollama_router()
    
    # Only 2 tiers now: Desktop (Tier 1) and Docker (Tier 2)
    desktop_available = False
    docker_available = True  # Always available
    
    if ollama_router.desktop_client:
        desktop_available = await ollama_router._check_desktop_availability()
    
    return {
        "tiers": {
            "desktop": {
                "tier": 1,
                "name": "Desktop Ollama (GPU)",
                "available": desktop_available,
                "model": "llama3:latest (GPU)",
                "use_case": "All queries (GPU accelerated)"
            },
            "docker": {
                "tier": 2,
                "name": "Docker Ollama (CPU)",
                "available": docker_available,
                "model": "llama3.2:3b (CPU)",
                "use_case": "Fallback (always available)"
            }
        },
        "recommendation": "desktop" if desktop_available else "docker"
    }
```

### Step 4: Update Documentation

Add note explaining:
- **Tier System**: ecosystem-mcp calling OUT to LLM backends
- **MCP Integration**: Cursor calling IN to ecosystem-mcp
- **Separate Concerns**: These are different flows

---

## 🔄 Alternative: Option 2 (Add Real Premium Tier)

If you want a true Tier 1 premium option:

### Step 1: Add Anthropic Claude API

**File:** `src/config.py`
```python
# Tier 1: Premium API (Claude/GPT-4)
tier1_enabled: bool = Field(
    default=False,
    description="Enable premium API for Tier 1 (requires API key)"
)
tier1_provider: str = Field(
    default="anthropic",
    description="Premium provider: anthropic, openai, etc."
)
```

### Step 2: Create Claude Client

**File:** `src/services/models/claude_client.py`
```python
import anthropic

class ClaudeClient:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-3-5-sonnet-20241022"
    
    async def is_available(self) -> bool:
        return settings.anthropic_api_key is not None
    
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        response = await self.client.messages.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return {"response": response.content[0].text}
```

### Step 3: Update Router

Use Claude for Tier 1 (high complexity), Desktop for Tier 2, Docker for Tier 3.

---

## 📊 Impact Analysis

### Current State
```
❌ Tier 1: Cursor IDE - Shows as unavailable (broken)
✅ Tier 2: Desktop Ollama - Works
✅ Tier 3: Docker Ollama - Works
✅ MCP Integration - Works (Cursor → ecosystem-mcp)
```

### After Option 1 (Remove Cursor Tier)
```
✅ Tier 1: Desktop Ollama (GPU) - Works  
✅ Tier 2: Docker Ollama (CPU) - Works
✅ MCP Integration - Works (Cursor → ecosystem-mcp)
```

### After Option 2 (Add Real Premium Tier)
```
⚠️  Tier 1: Claude API - Works IF API key provided
✅ Tier 2: Desktop Ollama (GPU) - Works
✅ Tier 3: Docker Ollama (CPU) - Works  
✅ MCP Integration - Works (Cursor → ecosystem-mcp)
```

---

## 🎯 Recommendation

**Implement Option 1: Remove Cursor Tier**

**Why:**
1. ✅ Architecturally correct
2. ✅ Removes broken health check
3. ✅ Eliminates user confusion
4. ✅ Clean 2-tier system that works
5. ✅ MCP integration continues to work fine
6. ✅ Can add real premium tier later (Option 2) if needed

**Steps:**
1. Remove Cursor config settings
2. Update dashboard to show 2 tiers
3. Update tier-status endpoint
4. Update all 3 RAG pages (rag.py, query_enhanced.py, rag_multi_pass.py)
5. Document the correct architecture

---

## 📝 Summary

**The Issue:**
- "Tier 1: Cursor IDE" is architecturally incorrect
- Health check tries to call Cursor, but Cursor calls us
- Shows as red/unavailable causing user confusion

**The Fix:**
- Remove Cursor from tier system (it's not a tier!)
- Keep MCP integration (it works correctly)
- Use 2-tier system: Desktop (GPU) + Docker (CPU)
- Optionally add real premium tier (Claude/GPT-4 API)

**Result:**
- ✅ No more red "unavailable" status
- ✅ Architecturally correct
- ✅ Clear separation of concerns
- ✅ MCP integration unaffected

---

**Next Steps:** Choose option and implement fixes

**Estimated Effort:**
- Option 1: 1-2 hours
- Option 2: 3-4 hours

**Risk:** 🟢 Low (removes broken feature, improves clarity)

