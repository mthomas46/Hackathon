# New Dashboard Pages Guide

## 📋 Logs Viewer

Access logs from all containers in your ecosystem.

### Features

#### Tab 1: Container Logs
- **View logs** from any Docker container
- **Select container** from dropdown menu
- **Configurable tail lines** (10-1000)
- **Auto-refresh** every 5 seconds
- **Download logs** as .log files
- **Real-time timestamps**

#### Tab 2: Dashboard Logs
- View **Streamlit dashboard** container logs
- Direct access to **ecosystem-mcp-dashboard** logs
- **Refresh on demand**
- **Download** dashboard logs

#### Tab 3: Search Logs
- **Search across multiple containers**
- **Case-sensitive/insensitive** search
- **Multi-container selection**
- **Line number references**
- Displays up to **50 matches per container**
- **Expandable results** by container

### Use Cases

1. **Debug container issues**
   - Select problematic container
   - Enable auto-refresh
   - Watch logs in real-time

2. **Search for errors**
   - Use Search tab
   - Select multiple containers
   - Search for error patterns
   - Download relevant logs

3. **Monitor application**
   - View dashboard logs
   - Track Streamlit events
   - Debug UI issues

---

## 🔌 API Explorer

Discover, document, and test API endpoints using OpenAPI specifications.

### Features

#### Tab 1: Endpoints
- **Discovers all API endpoints** from OpenAPI spec
- **Groups by tag/category**
- **Filter by tag**
- **Method color coding**:
  - 🟢 GET
  - 🔵 POST
  - 🟠 PUT
  - 🔴 DELETE
  - 🟡 PATCH
- **Detailed documentation** for each endpoint:
  - Summary & description
  - Parameters (type, required status)
  - Request body schemas
  - Response schemas
  - Status codes

#### Tab 2: API Tester
- **Interactive endpoint testing**
- Select **HTTP method**
- Enter **endpoint path**
- Configure **custom headers** (JSON)
- Set **request body** (JSON)
- **Real-time response display**:
  - Status code with color coding
  - Response time
  - Response size
  - Headers
  - Body (formatted JSON or text)
- **Download responses**

#### Tab 3: Documentation
- Quick links to **Swagger UI**
- Quick links to **ReDoc**
- **Download OpenAPI spec** (JSON)
- **API statistics**:
  - Total endpoints
  - Total paths
  - Total schemas
- **Quick test links** for common endpoints:
  - Health Check
  - Diagnostics
  - Configuration
  - Cache Stats
  - Containers
  - Redis Info
  - PostgreSQL Info

### Use Cases

1. **Discover APIs**
   - Browse all available endpoints
   - Read documentation
   - Understand parameters

2. **Test APIs**
   - Select endpoint from list
   - Copy to API Tester
   - Configure request
   - Send and view response

3. **Debug API issues**
   - Test failing endpoint
   - Check request/response
   - Verify parameters
   - Download response for analysis

4. **Learn API structure**
   - View all endpoints
   - Read schemas
   - Understand relationships
   - Access Swagger UI

---

## 🚀 Quick Start

### Access the Dashboard
```bash
open http://localhost:8501
```

### Navigate to New Pages
1. Open dashboard
2. Look in left sidebar
3. Select:
   - **📋 Logs Viewer** - For log management
   - **🔌 API Explorer** - For API discovery

---

## 📊 Example Workflows

### Debugging Workflow
```
1. 📋 Logs Viewer → Container Logs
2. Select container with issues
3. Enable auto-refresh (5s)
4. Watch for error patterns
5. Switch to Search tab
6. Search for specific errors
7. Download logs for analysis
```

### API Testing Workflow
```
1. 🔌 API Explorer → Endpoints
2. Browse available endpoints
3. Click on endpoint to view details
4. Copy endpoint path
5. Switch to API Tester tab
6. Paste endpoint
7. Configure headers/body
8. Send request
9. View formatted response
10. Download if needed
```

### Development Workflow
```
1. 🔌 API Explorer → Documentation
2. Download OpenAPI spec
3. Import into Postman/Insomnia
4. Test endpoints in API Tester
5. Check logs in Logs Viewer
6. Debug issues
7. Repeat
```

---

## 🔍 Technical Details

### Logs Viewer Implementation
- Uses Docker API via backend endpoints
- Fetches logs from `/api/v1/containers/{name}/logs`
- Supports tail parameter (10-1000 lines)
- Auto-refresh with Streamlit rerun
- Search using Python string matching

### API Explorer Implementation
- Parses OpenAPI spec from `/openapi.json`
- Groups endpoints by OpenAPI tags
- Displays schemas using JSON formatting
- Interactive testing with `httpx` library
- Response formatting with JSON.dumps
- Download buttons for responses

---

## 📚 All Dashboard Pages

| # | Page | Description |
|---|------|-------------|
| 1 | 🏠 Home | Dashboard overview |
| 2 | 🏥 Health & Infrastructure | System health |
| 3 | 🔬 Diagnostics | Connection testing |
| 4 | ⚙️ Configuration | Config viewer |
| 5 | **📋 Logs Viewer** | **Container logs (NEW!)** |
| 6 | **🔌 API Explorer** | **API endpoints (NEW!)** |
| 7 | 🐳 Container Management | Manage containers |
| 8 | 🔍 Redis Explorer | Browse Redis |
| 9 | 🗄️ PostgreSQL Explorer | Browse PostgreSQL |
| 10 | 🤖 RAG Query | Ask questions |
| 11 | 📚 Documents | Document management |
| 12 | ⚡ Cache Performance | Cache stats |
| 13 | 📊 Metrics & Analytics | System metrics |
| 14 | 🔧 Settings | Configuration |

---

## ✨ Features Summary

### Logs Viewer
- ✅ Multi-container log viewing
- ✅ Auto-refresh capability
- ✅ Log search across containers
- ✅ Download logs
- ✅ Real-time updates
- ✅ Configurable tail lines
- ✅ Dashboard self-inspection

### API Explorer
- ✅ OpenAPI spec parsing
- ✅ Endpoint discovery
- ✅ Interactive API testing
- ✅ Request/response visualization
- ✅ Parameter documentation
- ✅ Schema display
- ✅ Quick documentation access
- ✅ Response downloading

---

## 🎯 Tips & Tricks

### Logs Viewer
- Use **auto-refresh** when debugging live issues
- Use **search** to find patterns across multiple containers
- **Download logs** before they rotate
- Check **dashboard logs** if the UI behaves unexpectedly

### API Explorer
- Start in **Endpoints tab** to discover APIs
- Use **filter by tag** to find related endpoints
- **API Tester** supports JSON headers and bodies
- **Download responses** to compare with expected results
- Use **Documentation tab** for quick access to Swagger UI

---

## 🔧 Troubleshooting

### Logs Viewer Issues
- **"Cannot connect to API"**: Check API_BASE_URL in sidebar
- **"No logs available"**: Container may not have logs yet
- **Search timeout**: Reduce number of selected containers

### API Explorer Issues
- **"Failed to fetch OpenAPI spec"**: Check API is running
- **API Tester shows error**: Verify JSON syntax in headers/body
- **Endpoints not loading**: Refresh the page

---

## 📖 Related Resources

- [Swagger UI](http://localhost:8000/docs)
- [ReDoc](http://localhost:8000/redoc)
- [OpenAPI Spec](http://localhost:8000/openapi.json)
- [API Health](http://localhost:8000/health)

---

**Dashboard URL:** http://localhost:8501

