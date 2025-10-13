# Ecosystem MCP Dashboard

A comprehensive Streamlit dashboard for monitoring and managing the Ecosystem MCP service.

## Features

### 🏠 Home
- Service overview and information
- Key capabilities and features
- Quick action buttons
- Recent activity feed

### 🏥 Health & Infrastructure
- Real-time component health monitoring
- PostgreSQL, Redis, ChromaDB status
- Circuit breaker status and management
- Infrastructure diagnostics
- Component details and troubleshooting

### 🤖 RAG Query
- Interactive question-answering interface
- Configurable search parameters (n_results, temperature)
- Source document display
- Response metadata (timing, cache hits, model used)
- Query history tracking

### 📚 Documents
- Browse ingested documents
- Search and filter capabilities
- Document ingestion interface
- Ingestion job monitoring
- Document content preview

### ⚡ Cache Performance
- Real-time cache hit/miss statistics
- Cache hit rate visualization
- Per-prefix cache analytics
- Cache management (clear, export)
- Performance graphs and charts

### 📊 Metrics & Analytics
- System-wide metrics
- Document distribution
- Query performance analytics
- Database statistics
- Redis statistics
- Export and reporting

### 🔧 Settings
- API configuration
- Connection testing
- Dashboard preferences
- Theme settings
- Cache management
- System information

## Quick Start

### Local Development

```bash
cd services/ecosystem-mcp-dashboard

# Install dependencies
pip install -r requirements.txt

# Run dashboard
streamlit run app.py
```

The dashboard will be available at http://localhost:8501

### Docker Deployment

```bash
# Build and run with docker-compose
docker-compose up ecosystem-mcp-dashboard

# Or build manually
docker build -t ecosystem-mcp-dashboard .
docker run -p 8501:8501 \
  -e API_BASE_URL=http://ecosystem-mcp:8000 \
  ecosystem-mcp-dashboard
```

The dashboard will be available at http://localhost:8501

## Configuration

### Environment Variables

- `API_BASE_URL` - Base URL for Ecosystem MCP API (default: http://ecosystem-mcp:8000)
- `DASHBOARD_PORT` - Port for Streamlit dashboard (default: 8501)

### Docker Compose Integration

The dashboard is configured to run as part of the ecosystem-mcp docker-compose stack:

```yaml
ecosystem-mcp-dashboard:
  build: ./services/ecosystem-mcp-dashboard
  ports:
    - "8501:8501"
  environment:
    - API_BASE_URL=http://ecosystem-mcp:8000
  depends_on:
    - ecosystem-mcp
  networks:
    - hackathon_default
```

## API Endpoints Used

The dashboard interacts with the following Ecosystem MCP API endpoints:

- `GET /health` - Health check
- `GET /about-me` - Service information
- `GET /api/v1/infrastructure/health` - Infrastructure health
- `GET /api/v1/infrastructure/diagnostics` - Detailed diagnostics
- `POST /api/v1/ask` - RAG query
- `POST /api/v1/query` - Document query
- `GET /api/v1/cache/stats` - Cache statistics
- `POST /api/v1/admin/clear-cache` - Clear cache
- `GET /api/v1/admin/stats` - System statistics
- `GET /api/v1/admin/queue-status` - Ingestion queue status
- `POST /api/v1/admin/ingest` - Start ingestion job

## Architecture

```
┌─────────────────────────────────────────────┐
│         Streamlit Dashboard (8501)          │
│                                             │
│  ┌─────────┬─────────┬──────────┬────────┐ │
│  │  Home   │ Health  │   RAG    │  Docs  │ │
│  ├─────────┼─────────┼──────────┼────────┤ │
│  │ Cache   │ Metrics │ Settings │   ...  │ │
│  └─────────┴─────────┴──────────┴────────┘ │
│                                             │
│         HTTP Requests (httpx)               │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  Ecosystem MCP API   │
        │    (Port 8000)       │
        │                      │
        │  FastAPI + RAG       │
        └──────────────────────┘
```

## Development

### Adding New Pages

1. Create a new page module in `pages/`:

```python
# pages/my_new_page.py
import streamlit as st

def show(api_base_url: str):
    st.title("My New Page")
    # Your page content here
```

2. Add navigation in `app.py`:

```python
elif page == "🆕 My New Page":
    from pages import my_new_page
    my_new_page.show(api_base_url)
```

### Styling

Custom CSS is defined in `app.py`. Modify the `st.markdown()` block to add new styles.

### API Calls

Use `httpx` for all API calls with proper error handling:

```python
import httpx

try:
    response = httpx.get(f"{api_base_url}/endpoint", timeout=10.0)
    if response.status_code == 200:
        data = response.json()
        # Handle success
    else:
        st.error(f"Error: {response.status_code}")
except httpx.ConnectError:
    st.error("Cannot connect to API")
except Exception as e:
    st.error(f"Error: {str(e)}")
```

## Troubleshooting

### Cannot Connect to API

- Verify Ecosystem MCP service is running
- Check API_BASE_URL configuration
- Ensure network connectivity between containers

### Dashboard Not Loading

- Check Streamlit logs: `docker logs ecosystem-mcp-dashboard`
- Verify port 8501 is not in use
- Check browser console for errors

### Slow Performance

- Enable caching in settings
- Reduce auto-refresh interval
- Limit items per page

## Future Enhancements

- [ ] Real-time WebSocket updates
- [ ] User authentication and roles
- [ ] Custom dashboard layouts
- [ ] Alert and notification system
- [ ] Advanced analytics and reporting
- [ ] Export to PDF/CSV
- [ ] Dark mode theme
- [ ] Mobile-responsive design
- [ ] Multi-language support
- [ ] Grafana integration

## License

MIT License

## Support

For issues and questions, please file an issue on GitHub or contact the development team.

