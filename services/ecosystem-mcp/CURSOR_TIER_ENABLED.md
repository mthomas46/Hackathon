# 🥇 Cursor IDE (Tier 1) Setup Complete

## ✅ What Was Done

Similar to the Desktop Ollama setup, Cursor IDE has been configured as the premium Tier 1 for the LLM hierarchy.

### Changes Made

#### 1. **Setup Script Created**
```bash
services/ecosystem-mcp/setup_cursor_ide.sh
```

Automated setup script that:
- ✅ Detects Cursor IDE installation on macOS/Linux
- ✅ Checks if MCP server is running on port 3000
- ✅ Tests connectivity from both host and Docker perspectives
- ✅ Validates tier status via ecosystem-mcp API
- ✅ Provides detailed configuration instructions
- ✅ Updates .env file automatically

#### 2. **Docker Configuration Updated**

**docker-compose.yml** - Added environment variables:
```yaml
# Cursor IDE (Tier 1) - Premium Models
CURSOR_ENABLED: "true"
CURSOR_MCP_URL: http://host.docker.internal:3000
CURSOR_MODEL: claude-4.5-sonnet
```

**.env** - Added configuration section:
```bash
# Cursor IDE (Tier 1) - Premium Models
CURSOR_ENABLED=true
CURSOR_MCP_URL=http://host.docker.internal:3000
CURSOR_MODEL=claude-4.5-sonnet
```

#### 3. **Service Restarted**
```bash
docker compose down ecosystem-mcp
docker compose up -d ecosystem-mcp
```

The ecosystem-mcp service has been restarted and now recognizes Cursor IDE as Tier 1.

---

## 📊 Current Status

### Tier Hierarchy (3-Tier System)

| Tier | Name | Model | Status | Use Case |
|------|------|-------|--------|----------|
| **1** 🥇 | **Cursor IDE** | Claude 4.5 Sonnet | ⚠️ **Not Available** | Extreme complexity, best reasoning |
| **2** 🥈 | **Desktop Ollama** | llama3:latest | ✅ **Available** | Complex queries with GPU |
| **3** 🥉 | **Docker Ollama** | llama3.2:latest | ✅ **Available** | Simple queries, always on |

**Note:** Cursor IDE is currently marked as unavailable because the MCP server is not configured yet.

---

## 🚀 Next Steps: Enabling Cursor IDE

To complete the Cursor IDE setup and make it available, you need to configure the MCP server:

### Option 1: Run the Setup Script
```bash
cd services/ecosystem-mcp
./setup_cursor_ide.sh
```

This will:
1. Check if Cursor IDE is installed
2. Test MCP server connectivity
3. Provide specific setup instructions based on your system
4. Validate the configuration

### Option 2: Manual Configuration

#### Step 1: Verify Cursor IDE is Installed
- **macOS:** Check `/Applications/Cursor.app`
- **Linux:** Run `which cursor`
- **Not installed?** Download from https://cursor.sh

#### Step 2: Enable MCP Server in Cursor

The MCP (Model Context Protocol) server allows external applications to communicate with Cursor's AI models.

**To enable:**
1. Open Cursor IDE
2. Go to Settings (Cmd/Ctrl + ,)
3. Search for "MCP" or "Model Context Protocol"
4. Enable MCP server functionality
5. Set the port to **3000**
6. Save and restart Cursor

**Note:** MCP server configuration varies by Cursor version. Check the Cursor documentation for your specific version.

#### Step 3: Configure API Access

Ensure you have:
- ✅ A Cursor subscription that includes Claude models
- ✅ API access enabled in Cursor settings
- ✅ Proper authentication configured

#### Step 4: Test Connectivity

From your terminal:
```bash
# Test from host
curl http://localhost:3000/health

# Expected: 200 OK response or some JSON
```

#### Step 5: Restart Cursor IDE
- Close and reopen Cursor IDE
- Or reload window: Cmd/Ctrl + Shift + P → "Reload Window"

#### Step 6: Verify in Dashboard

1. Open dashboard: http://localhost:8501
2. Go to: **🔌 LLM Tier Management**
3. Click **"Refresh Status"**
4. Check if Cursor IDE (Tier 1) shows as **✅ Available**

---

## 🧪 Testing Cursor IDE

Once the MCP server is running and Tier 1 shows as available:

### Test 1: Enhanced Query
1. Go to **🎯 Enhanced Query** in the dashboard
2. Select tier: **"Cursor" (Tier 1)**
3. Enter a complex question:
   ```
   Analyze the trade-offs between using a message queue vs. direct API calls 
   for microservices communication in a high-throughput system.
   ```
4. Submit and verify you get a detailed, high-quality response

### Test 2: Multi-Pass Query
1. Go to **🔬 Multi-Pass RAG Query**
2. Select tier: **Cursor**
3. Enter a complex question requiring multiple steps
4. Verify it uses Tier 1 for all sub-queries

### Test 3: RAG Query with Auto-Routing
1. Go to **🤖 RAG Query**
2. Select tier: **"Auto (Recommended)"**
3. Enter a very complex question with high complexity
4. The system should automatically route it to Cursor IDE (Tier 1)

---

## 🔍 Troubleshooting

### Issue 1: Cursor IDE shows "Not Available"

**Possible Causes:**
1. MCP server not running on port 3000
2. Port 3000 is used by another application
3. Cursor IDE not configured for external MCP access
4. Docker can't reach host.docker.internal

**Solutions:**
```bash
# Check what's running on port 3000
lsof -i :3000

# Test connectivity from Docker
docker run --rm curlimages/curl:latest \
  curl -s http://host.docker.internal:3000/health

# Restart ecosystem-mcp service
cd services/ecosystem-mcp
docker compose restart ecosystem-mcp

# Wait 10 seconds, then check tier status
curl http://localhost:8000/api/v1/query/tier-status | jq '.tiers.cursor'
```

### Issue 2: MCP Server Won't Start

**Check:**
1. Cursor IDE version supports MCP server
2. No firewall blocking port 3000
3. Cursor settings saved correctly
4. Cursor fully restarted (not just reloaded)

**Verify Cursor is Running:**
```bash
# macOS
ps aux | grep -i cursor

# Check Cursor logs (location varies by version)
# Usually in: ~/Library/Application Support/Cursor/logs/
```

### Issue 3: Authentication Errors

If you get authentication/API key errors:
1. Verify your Cursor subscription is active
2. Check that Claude models are available in your plan
3. Re-authenticate in Cursor settings
4. Restart Cursor after re-authenticating

### Issue 4: Docker Can't Reach Host

If Docker can't connect to `host.docker.internal:3000`:

**macOS/Windows:**
- `host.docker.internal` should work by default
- If not, update Docker Desktop to the latest version

**Linux:**
```bash
# Add to docker-compose.yml under ecosystem-mcp service:
extra_hosts:
  - "host.docker.internal:host-gateway"
```

---

## 📖 Understanding the Tier System

### When Each Tier is Used

#### 🥇 Tier 1: Cursor IDE (Claude 4.5 Sonnet)
**Automatically used for:**
- Complexity score > 0.8
- Multi-step reasoning tasks
- Code generation and analysis
- Detailed technical explanations

**Manually select for:**
- When you need the highest quality response
- Complex queries where accuracy > speed
- Advanced reasoning or planning
- Critical decision-making tasks

**Cost:** High (uses Claude API via Cursor)

#### 🥈 Tier 2: Desktop Ollama
**Automatically used for:**
- Complexity score 0.4 - 0.8
- RAG queries (when `USE_DESKTOP_FOR_RAG=true`)
- Medium-complexity questions

**Manually select for:**
- Fast queries with good quality
- When you have GPU acceleration
- Batch processing
- Development and testing

**Cost:** Free (local GPU inference)

#### 🥉 Tier 3: Docker Ollama
**Automatically used for:**
- Complexity score < 0.4
- Simple questions
- Fallback when higher tiers unavailable

**Manually select for:**
- Quick lookups
- Simple tasks
- When you want guaranteed availability
- CPU-only environments

**Cost:** Free (local CPU inference)

### Complexity Analysis

The system analyzes your query for:
- **Keywords:** technical terms, domain-specific language
- **Length:** longer queries = more complex
- **Question Type:** "why", "how", "analyze" = higher complexity
- **Context Requirements:** multi-step, comparisons = higher complexity

---

## 🎯 Best Practices

### 1. **Use Auto-Routing for Production**
Let the system choose the best tier based on query complexity:
```python
# In Enhanced Query mode
tier = "auto"  # Recommended for most use cases
```

### 2. **Force Tier Selection for Specific Needs**
```python
# For critical analysis - force Tier 1
tier = "cursor"

# For fast batch processing - force Tier 2
tier = "desktop"

# For development/testing - force Tier 3
tier = "docker"
```

### 3. **Monitor Tier Usage**
Check the dashboard's **📊 Metrics & Analytics** page to see:
- Which tiers are being used most
- Query complexity distribution
- Response times by tier
- Success/failure rates

### 4. **Configure Fallback Behavior**
```python
# In API requests, set max_retries for automatic fallback
{
  "question": "...",
  "tier": "cursor",
  "max_retries": 2  # Will fallback to desktop, then docker if cursor fails
}
```

---

## 📝 Configuration Reference

### Environment Variables

```bash
# Cursor IDE (Tier 1)
CURSOR_ENABLED=true                                    # Enable/disable Cursor tier
CURSOR_MCP_URL=http://host.docker.internal:3000       # MCP server URL (from Docker)
CURSOR_MODEL=claude-4.5-sonnet                        # Model to use via Cursor

# Desktop Ollama (Tier 2)
OLLAMA_DESKTOP_ENABLED=true                           # Enable/disable desktop tier
OLLAMA_DESKTOP_URL=http://host.docker.internal:11435 # Desktop Ollama URL
OLLAMA_DESKTOP_MODEL=llama3:latest                    # Desktop model
USE_DESKTOP_FOR_RAG=true                              # Use desktop for RAG queries

# Docker Ollama (Tier 3)
OLLAMA_ENABLED=true                                   # Enable/disable docker tier
OLLAMA_BASE_URL=http://ollama:11434                   # Docker Ollama URL
OLLAMA_MODEL=llama3.2:latest                          # Docker model (smaller for CPU)
```

### Tier Priority
```
1. Cursor IDE (if available and complexity > 0.8)
2. Desktop Ollama (if available and complexity 0.4-0.8)
3. Docker Ollama (always available, complexity < 0.4)
```

### Fallback Behavior
```
cursor → desktop → docker
  ↓        ↓         ↓
 fail?   fail?   always works
```

---

## 🎉 Summary

✅ **Cursor IDE (Tier 1) is now configured** in the ecosystem-mcp system  
⚠️ **MCP server setup required** to make it available  
✅ **Desktop Ollama (Tier 2) is working** and available now  
✅ **Docker Ollama (Tier 3) is working** and available now  
✅ **Automatic tier routing** is active and will use the best available tier  
✅ **Manual tier selection** is available in all query interfaces  

### Quick Start

```bash
# 1. Run setup script
cd services/ecosystem-mcp
./setup_cursor_ide.sh

# 2. Follow the instructions to configure Cursor MCP server

# 3. Verify in dashboard
open http://localhost:8501
# Navigate to: 🔌 LLM Tier Management

# 4. Test with a query
# Navigate to: 🎯 Enhanced Query
# Select tier: Cursor
# Submit a complex question
```

---

## 📚 Additional Resources

- **Cursor IDE:** https://cursor.sh
- **MCP Documentation:** Check Cursor's official docs for your version
- **Dashboard:** http://localhost:8501
- **API Docs:** http://localhost:8000/docs
- **Tier Status Endpoint:** http://localhost:8000/api/v1/query/tier-status

---

## 🤝 Need Help?

If you encounter issues:

1. **Run the setup script** for diagnostic information:
   ```bash
   ./setup_cursor_ide.sh
   ```

2. **Check the logs** for detailed error messages:
   ```bash
   docker logs ecosystem-mcp-service --tail 100
   ```

3. **Verify tier status** via API:
   ```bash
   curl http://localhost:8000/api/v1/query/tier-status | jq
   ```

4. **Test each tier individually** in the dashboard:
   - Go to **🔌 LLM Tier Management**
   - Use the "Test Connection" buttons

---

**Status:** ✅ Configuration complete, awaiting MCP server setup  
**Next:** Configure Cursor MCP server to enable Tier 1  
**Updated:** 2025-10-14

