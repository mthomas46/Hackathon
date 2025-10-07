# 🧠 MCP Ecosystem Dashboard

A beautiful, production-ready Python dashboard built with Streamlit for managing and monitoring the Model Context Protocol ecosystem.

## ✨ Features

### 🏠 **Home Dashboard**
- Real-time system metrics and KPIs
- Query volume trends (24h)
- Top performing patterns
- Recent events feed
- Quick action buttons

### ⚙️ **MCP Management**
- List all active MCP instances
- Provision new MCPs with advanced options
- Start, stop, restart, and delete MCPs
- Resource usage monitoring
- Statistics and distribution charts

### 📈 **Performance Monitor**
- Real-time performance metrics
- Pattern-specific analytics
- Response time trends
- Anomaly detection with severity levels
- Success rate tracking

### 🏪 **Marketplace**
- Browse MCP packages
- Trending and popular packages
- Download and star packages
- Search and filter capabilities
- Detailed package information

### 🔍 **Query Playground**
- Interactive query testing
- Pattern selection (RAG, CoT, ReAct, etc.)
- Advanced options (temperature, tokens)
- Response metrics and timing
- Source attribution

### 🎓 **Training Dashboard**
- Active training job monitoring
- Progress tracking with ETAs
- Completed job history
- Training statistics
- Source distribution analytics

### 💚 **System Health**
- Service status monitoring (11 services)
- Health checks and uptime
- System resource metrics
- Active alerts and warnings
- Response time tracking

---

## 🚀 Quick Start

### **Prerequisites**
- Python 3.9+
- pip or conda

### **Installation**

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env

# Edit .env with your service URLs
nano .env
```

### **Run the Dashboard**

```bash
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`

---

## 📦 Dependencies

- **streamlit** - Core dashboard framework
- **plotly** - Interactive visualizations
- **pandas** - Data manipulation
- **streamlit-option-menu** - Beautiful sidebar navigation
- **httpx** - Async HTTP client for backend APIs
- **python-dotenv** - Environment configuration

See `requirements.txt` for full list.

---

## 🔧 Configuration

Edit `.env` to configure service URLs:

```env
MCP_PROVISIONER_URL=http://localhost:5001
MCP_COMPOSER_URL=http://localhost:5002
MCP_ORCHESTRATOR_URL=http://localhost:5003
MCP_INTERPRETER_URL=http://localhost:5004
MCP_REGISTRY_URL=http://localhost:5005
API_GATEWAY_URL=http://localhost:5006
TRAINING_COORDINATOR_URL=http://localhost:5007
MCP_PERFORMANCE_STORE_URL=http://localhost:5649
MCP_STORE_URL=http://localhost:5648
```

---

## 📊 Architecture

```
dashboard/
├── app.py                      # Main application entry point
├── requirements.txt            # Python dependencies
├── .env.example               # Environment configuration template
├── pages/                     # Dashboard pages
│   ├── __init__.py
│   ├── home.py                # Home dashboard
│   ├── mcp_management.py      # MCP management interface
│   ├── performance_monitor.py  # Performance analytics
│   ├── marketplace.py         # Package marketplace
│   ├── query_playground.py    # Query testing
│   ├── training_dashboard.py  # Training job monitoring
│   └── system_health.py       # System health monitoring
└── utils/                     # Utility functions (future)
```

---

## 🎨 Design Philosophy

- **Beautiful & Modern**: Clean UI with consistent styling
- **Production-Ready**: Error handling and graceful degradation
- **Responsive**: Works on desktop and tablet
- **Fast**: Optimized for quick page loads
- **Intuitive**: Easy navigation and clear information hierarchy

---

## 🔜 Future Enhancements

- Real-time updates via WebSocket
- User authentication and RBAC
- Custom dashboards and widgets
- Dark mode support
- Export/download capabilities
- Advanced filtering and search
- Notification system
- Mobile responsive design

---

## 📝 Development

### **Code Style**
- PEP 8 compliant
- Type hints where applicable
- Docstrings for all functions
- Clear variable names

### **Project Structure**
- Each page is a separate module in `pages/`
- Utility functions go in `utils/`
- API clients go in `clients/` (future)
- State management in Streamlit session state

---

## 🤝 Integration with Backend

The dashboard integrates with all MCP backend services:

1. **MCP Provisioner** - Provision and manage MCPs
2. **MCP Composer** - Composition management
3. **MCP Orchestrator** - Pattern execution
4. **MCP Interpreter** - Query parsing
5. **MCP Registry** - Package registry
6. **API Gateway** - Unified API access
7. **Training Coordinator** - Training jobs
8. **MCP Performance Store** - Performance metrics
9. **MCP Store** - Package storage
10. **Log Collector** - System logs

---

## 📄 License

Part of the MCP Ecosystem project.

---

**Built with ❤️ using Streamlit**
