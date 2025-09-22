# 🌐 Unified API Ecosystem Dashboard

## Overview

The Unified API Ecosystem Dashboard is a comprehensive platform that aggregates, documents, and provides interactive access to all APIs across the LLM Documentation Ecosystem. It serves as the central hub for API discovery, testing, monitoring, and developer tools, with deep integration with the Discovery Agent for real-time API intelligence.

## Key Features

### 📚 Unified API Catalog
- **Centralized Documentation**: Single source of truth for all ecosystem API documentation
- **Real-Time Discovery**: Dynamic API discovery and documentation updates via Discovery Agent
- **Advanced Search**: Powerful search and filtering across all API endpoints and operations
- **Interactive Exploration**: Browse APIs by service, category, and functionality

### 🧪 API Testing & Validation
- **Interactive Testing**: Built-in API testing interface with authentication support
- **Request/Response Examples**: Comprehensive examples for all API operations
- **Validation Tools**: API specification validation and compliance checking
- **Performance Testing**: API performance monitoring and benchmarking

### 📊 Analytics & Monitoring
- **Health Monitoring**: Real-time API availability and performance monitoring
- **Usage Analytics**: API usage patterns, performance metrics, and error tracking
- **Service Dependencies**: Visual representation of API relationships and dependencies
- **Performance Insights**: API response times, error rates, and throughput metrics

### 🔗 Discovery Agent Integration
- **Intelligent Discovery**: Automatic API endpoint discovery and registration
- **OpenAPI Processing**: Advanced parsing and validation of API specifications
- **Service Mapping**: Dynamic service topology and API relationship mapping
- **Real-Time Updates**: Live API documentation updates as services change

## Architecture

### Dual Interface Design
- **Streamlit Web UI**: Interactive dashboards for API exploration and management
- **FastAPI REST API**: Programmatic access for automation and external integrations

### Technology Stack
- **Streamlit**: Web interface with interactive dashboards
- **FastAPI**: REST API layer with comprehensive OpenAPI documentation
- **httpx**: Async HTTP clients for API communication
- **Plotly**: Data visualizations and analytics
- **OpenAPI Parser**: Advanced API specification processing

## API Endpoints

### Health & Monitoring
- `GET /health` - Service health and system status
- `GET /api/health/apis` - API ecosystem health overview
- `GET /api/health/services` - Individual service connectivity status

### API Discovery
- `POST /api/discovery/scan` - Trigger API discovery scan
- `GET /api/discovery/apis` - List all discovered APIs
- `GET /api/discovery/services` - List all discovered services

### API Catalog
- `GET /api/catalog/endpoints` - Comprehensive API endpoint catalog
- `GET /api/catalog/services/{service}` - API catalog for specific service
- `GET /api/catalog/search` - Search API endpoints with filtering

### API Testing
- `POST /api/testing/execute` - Execute API test against endpoint
- `GET /api/testing/history` - API testing history and results
- `POST /api/testing/batch` - Execute batch API tests

### Analytics & Insights
- `GET /api/analytics/overview` - API ecosystem analytics overview
- `GET /api/analytics/endpoints` - Analytics for specific endpoints
- `GET /api/analytics/performance` - API performance metrics and trends

## Web UI Pages

### API Catalog & Documentation
- Browse all APIs by service, category, and functionality
- Interactive documentation viewer for each service
- Advanced search and filtering capabilities

### API Testing & Development
- Interactive testing tools with authentication
- Visual request builder and response viewer
- API validation and compliance checking

### Analytics & Monitoring
- Real-time API health and performance monitoring
- Usage analytics and performance insights
- Service dependency visualization

### Developer Tools
- API client code generation
- OpenAPI specification validation
- Integration testing utilities

## Usage

### Running the Dashboard

```bash
# Run with Streamlit (default)
streamlit run app.py

# Run with custom configuration
streamlit run app.py --server.port 8501 --server.address 0.0.0.0

# Run FastAPI server only
uvicorn app:app --host 0.0.0.0 --port 8000
```

### Docker Deployment

```bash
# Build the image
docker build -t unified-api-dashboard .

# Run the container
docker run -p 8501:8501 -p 8000:8000 unified-api-dashboard
```

## Configuration

The service uses configuration files for various settings:

- `config/config.yaml` - Main service configuration
- Environment variables for runtime customization
- Discovery Agent connection settings

## Integration Points

### Discovery Agent
- Primary source for API discovery and specification management
- Real-time updates for API changes and new service registrations
- Health monitoring and connectivity validation

### All Ecosystem Services
- Automatic API specification harvesting
- Health status monitoring and alerting
- Performance metrics collection and analysis

### External Systems
- REST API for programmatic access and automation
- Webhook support for real-time notifications
- Integration APIs for third-party tools

## Development

### Project Structure
```
unified-api-dashboard/
├── app.py                 # Main application with Streamlit UI and FastAPI
├── components/           # Reusable UI components
├── infrastructure/       # Configuration and infrastructure code
├── pages/               # Streamlit page implementations
├── services/            # Service clients and integrations
├── tests/               # Test suites
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container definition
└── README.md           # This file
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

### API Documentation

When running the service, API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

Proprietary - All rights reserved.
