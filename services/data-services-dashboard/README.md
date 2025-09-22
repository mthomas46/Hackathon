# Data Services Dashboard

A unified web interface for browsing, managing, and interacting with the Memory Agent, Prompt Store, and Document Store services in the LLM Documentation Ecosystem.

## 🌟 Features

### 🧠 Memory Agent Browser
- **Browse Memory Items**: View conversation memory and operational context with filtering
- **Search Memory**: Full-text search across summaries and data
- **Add Memory**: Create new memory items with custom data
- **Memory Statistics**: Analytics and insights about memory usage

### 📝 Prompt Store Browser
- **Browse Prompts**: View prompts by category, tags, and lifecycle status
- **Create & Edit**: Full CRUD operations for prompt management
- **Version Control**: Manage prompt versions and forking
- **Analytics**: Usage statistics and performance metrics

### 📄 Document Store Browser
- **Document Management**: Upload, view, and organize documents
- **Advanced Search**: Full-text search with metadata filters
- **Versioning**: Document versioning and lifecycle management
- **Relationships**: Link documents and manage dependencies

### 🔗 Cross-Service Integration
- **Link Items**: Connect documents to prompts, memory to prompts
- **Relationship Graphs**: Visualize connections across services
- **Unified Search**: Search across all services simultaneously

### 🔍 Advanced Search
- **Unified Search**: Search across all services with advanced filters
- **Query Building**: Complex search queries with operators
- **Result Aggregation**: Combined results from multiple services

### ⚡ Bulk Operations
- **Import/Export**: Bulk data operations
- **Batch Processing**: Apply operations to multiple items
- **Job Management**: Track and monitor bulk operations

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Running Memory Agent (port 5040)
- Running Prompt Store (port 8080)
- Running Document Store (port 8081)

### Installation & Running

```bash
# Navigate to the dashboard directory
cd services/data-services-dashboard

# Run the dashboard (auto-installs dependencies)
python3 run_dashboard.py
```

The dashboard will be available at: http://localhost:8502

### Manual Installation

```bash
# Install dependencies
pip install streamlit httpx plotly pandas pydantic pydantic-settings

# Run the dashboard
streamlit run app.py --server.port 8502
```

## 📋 Dashboard Pages

### 🏠 Overview
- Service health monitoring
- Key metrics and statistics
- Quick actions and navigation
- Recent activity feed

### 🧠 Memory Agent
- Browse memory items with filters
- Search memory content
- Add new memory items
- View memory statistics

### 📝 Prompt Store
- Browse prompts by category/tags
- Create and edit prompts
- Manage versions and lifecycle
- View analytics and suggestions

### 📄 Document Store
- Upload and manage documents
- Advanced document search
- Version control and lifecycle
- Document relationships

### 🔗 Cross-Service
- Link documents to prompts
- Connect memory to prompts
- View relationship graphs
- Manage cross-service dependencies

### 🔍 Advanced Search
- Unified search across services
- Advanced query building
- Filter combinations
- Result aggregation

### ⚡ Bulk Operations
- Bulk import/export
- Batch operations
- Job monitoring
- File operations

## 🔧 Configuration

The dashboard uses environment variables for configuration:

```bash
# Service URLs
DATA_DASHBOARD_MEMORY_SERVICE_HOST=localhost
DATA_DASHBOARD_MEMORY_SERVICE_PORT=5040
DATA_DASHBOARD_PROMPT_SERVICE_HOST=localhost
DATA_DASHBOARD_PROMPT_SERVICE_PORT=8080
DATA_DASHBOARD_DOCUMENT_SERVICE_HOST=localhost
DATA_DASHBOARD_DOCUMENT_SERVICE_PORT=8081

# Dashboard settings
DATA_DASHBOARD_ENVIRONMENT=development
DATA_DASHBOARD_DEBUG=true
DATA_DASHBOARD_PORT=8502
```

## 🏗️ Architecture

### Technology Stack
- **Frontend**: Streamlit (React-based web interface)
- **Backend**: Async HTTP clients (httpx)
- **Data Visualization**: Plotly
- **Configuration**: Pydantic Settings
- **Logging**: Structured logging with structlog

### Project Structure
```
services/data-services-dashboard/
├── app.py                      # Main application
├── run_dashboard.py           # Startup script
├── infrastructure/
│   ├── config/                # Configuration management
│   └── logging/               # Logging setup
├── services/
│   └── clients/               # Service API clients
├── components/                # UI components
│   ├── sidebar.py            # Navigation sidebar
│   ├── header.py             # Dashboard header
│   └── footer.py             # Dashboard footer
└── pages/                     # Page implementations
    ├── overview.py           # Overview dashboard
    ├── memory_browser.py     # Memory agent interface
    ├── prompt_browser.py     # Prompt store interface
    ├── document_browser.py   # Document store interface
    ├── cross_service.py      # Cross-service features
    ├── search.py            # Advanced search
    └── bulk_operations.py   # Bulk operations
```

## 🔌 API Integration

### Memory Agent Client
- Health checks and statistics
- CRUD operations for memory items
- Search and filtering capabilities

### Prompt Store Client
- Full prompt lifecycle management
- Category and tag management
- Version control and forking
- Analytics and suggestions

### Document Store Client
- Document upload and management
- Advanced search with filters
- Versioning and relationships
- Lifecycle and tagging operations

## 🎯 Development Status

### ✅ Completed Features
- [x] Unified dashboard structure
- [x] Service health monitoring
- [x] Memory Agent browser (full implementation)
- [x] Basic UI components and navigation
- [x] Configuration management
- [x] Service client libraries

### 🚧 In Development
- [ ] Prompt Store browser (placeholder)
- [ ] Document Store browser (placeholder)
- [ ] Cross-service integration (placeholder)
- [ ] Advanced search (placeholder)
- [ ] Bulk operations (placeholder)

### 📋 Planned Features
- [ ] Real-time updates and WebSocket support
- [ ] Advanced analytics and reporting
- [ ] User authentication and permissions
- [ ] Plugin system for custom integrations
- [ ] Export/import templates
- [ ] Audit logging and compliance

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is part of the LLM Documentation Ecosystem. See the main project license for details.

## 🆘 Support

- **Documentation**: [LLM Documentation Ecosystem Docs](https://docs.ecosystem.ai)
- **Issues**: [GitHub Issues](https://github.com/your-org/data-services-dashboard/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/data-services-dashboard/discussions)

---

**Built with ❤️ for the LLM Documentation Ecosystem**
