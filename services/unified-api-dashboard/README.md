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

### 📊 Analytics & Insights
- **Usage Analytics**: Comprehensive API usage patterns, trends, and behavioral analysis
- **Performance Insights**: Advanced response time analysis, throughput optimization, and bottleneck detection
- **Error Tracking**: Real-time error monitoring, pattern analysis, and root cause identification
- **Real-Time Metrics**: Live API performance metrics and system health indicators
- **User Behavior Analysis**: User segmentation, journey analysis, and engagement metrics
- **Predictive Analytics**: Usage forecasting and capacity planning recommendations

### 🛠️ Developer Tools
- **Client SDK Generation**: Auto-generate client libraries in Python, TypeScript, Go, Java, and more
- **API Validation**: Comprehensive OpenAPI specification validation and compliance checking
- **Integration Testing**: Automated API testing, load testing, and regression testing
- **Code Templates**: Production-ready templates for multiple programming languages and frameworks
- **Request Validation**: Pre-flight request validation against API specifications
- **Contract Testing**: Validate API contracts between consumer and provider services

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
- **scikit-learn**: Machine learning for user behavior clustering and pattern analysis
- **numpy**: Numerical computing for analytics processing

### Analytics Module

The Unified API Dashboard includes a comprehensive analytics module with four specialized components:

#### Usage Analytics (`modules/analytics/usage_analytics.py`)
- **Request Volume Tracking**: Real-time monitoring of API request volumes and patterns
- **Service Usage Analysis**: Usage distribution across different services and endpoints
- **User Activity Monitoring**: User behavior tracking and engagement metrics
- **Geographic Usage Patterns**: Usage analysis by geographic regions and networks
- **Temporal Pattern Analysis**: Hourly, daily, and weekly usage pattern identification
- **Real-Time RPS Monitoring**: Current requests per second with peak tracking

#### Performance Insights (`modules/analytics/performance_insights.py`)
- **Response Time Analysis**: P50, P95, P99 latency analysis with performance grading
- **Throughput Optimization**: Capacity utilization monitoring and scaling recommendations
- **Resource Utilization**: CPU, memory, and network usage analysis with alerts
- **Bottleneck Detection**: Automatic identification of performance bottlenecks
- **Optimization Recommendations**: Specific recommendations for performance improvements
- **Capacity Planning**: Automated scaling recommendations based on usage patterns

#### Error Tracking (`modules/analytics/error_tracking.py`)
- **Error Rate Monitoring**: Real-time error rate tracking with alerting thresholds
- **Error Pattern Analysis**: Automatic identification of recurring error patterns
- **Root Cause Analysis**: Intelligent root cause identification using error correlation
- **Error Classification**: Categorization by error type (client, server, timeout, auth, etc.)
- **Error Forecasting**: Predictive analysis of future error patterns
- **Alert Generation**: Automated alerts for critical error conditions

#### Usage Patterns (`modules/analytics/usage_patterns.py`)
- **Temporal Pattern Recognition**: Advanced analysis of usage patterns over time
- **User Behavior Clustering**: ML-powered user segmentation based on behavior patterns
- **Journey Analysis**: User journey mapping through the API ecosystem
- **Sequence Mining**: Discovery of common API call sequences and workflows
- **Anomaly Detection**: Statistical detection of unusual usage patterns
- **Predictive Forecasting**: ML-based forecasting of future usage trends

### Developer Tools Module

The Developer Tools module provides comprehensive tools for API developers and integrators:

#### Client Code Generator (`modules/developer_tools/client_generator.py`)
- **Multi-Language Support**: Generate client SDKs in Python, TypeScript, Go, Java, C#, and Rust
- **Client Type Options**: REST, Async, GraphQL, and WebSocket client variants
- **Enterprise Features**: Authentication, error handling, retry logic, and logging
- **Type Safety**: Full type checking and validation in generated code
- **Package Management**: Automatic dependency management and build configuration
- **Comprehensive Testing**: Generated unit tests and integration test helpers

#### API Validator (`modules/developer_tools/api_validator.py`)
- **OpenAPI Compliance**: Validate specifications against OpenAPI 3.0/3.1 standards
- **Schema Validation**: JSON Schema validation for all data models and responses
- **Security Assessment**: Authentication, authorization, and data protection validation
- **API Design Review**: RESTful design principles and best practices checking
- **Live API Validation**: Runtime validation against actual API endpoints
- **Compliance Scoring**: Percentage-based compliance scoring with detailed reports

#### Integration Tester (`modules/developer_tools/integration_tester.py`)
- **Functional Testing**: Automated API functionality and response validation
- **Load Testing**: Concurrent user simulation and performance stress testing
- **Contract Testing**: Validate API contracts between consumer and provider services
- **Regression Testing**: Ensure existing functionality remains intact after changes
- **Performance Benchmarking**: Response time analysis and throughput measurement
- **Edge Case Testing**: Automatic generation and testing of edge cases

#### Code Templates (`modules/developer_tools/code_templates.py`)
- **Template Library**: Production-ready code templates for multiple languages
- **Framework Integration**: Templates for popular frameworks and libraries
- **Best Practices**: Industry-standard patterns and conventions
- **Customization**: Configurable templates for different use cases
- **Documentation**: Comprehensive usage examples and API documentation

### Topology Module

The Topology module provides comprehensive service relationship analysis and visualization:

#### Topology Analyzer (`modules/topology/analyzer.py`)
- **Service Discovery**: Automatic identification and classification of services in the ecosystem
- **Relationship Analysis**: Deep analysis of API calls, data flows, and shared resources
- **Dependency Mapping**: Construction of complete dependency graphs with relationship strengths
- **Critical Path Detection**: Identification of high-impact service chains and failure points
- **Cluster Analysis**: Community detection and functional grouping of services
- **Health Integration**: Incorporation of service health data into topology analysis
- **Impact Assessment**: Calculation of service failure cascading effects

#### Topology Visualizer (`modules/topology/visualizer.py`)
- **Multiple Formats**: Support for Cytoscape, D3.js, GraphViz, and JSON visualization formats
- **Layout Algorithms**: Force-directed, hierarchical, circular, and grid layout options
- **Styling Engine**: Comprehensive visual styling based on service types and health status
- **Interactive Features**: Zoom, pan, filtering, and node detail capabilities
- **Cluster Visualization**: Focused views of individual service clusters
- **Critical Path Highlighting**: Visual emphasis of important dependency chains
- **Export Capabilities**: Save visualizations in various formats for documentation

#### Dependency Graph Builder (`modules/topology/graph_builder.py`)
- **Graph Construction**: Advanced NetworkX-based graph building with metadata
- **Path Analysis**: Shortest paths, critical paths, and dependency chains
- **Circular Dependency Detection**: Identification and resolution of dependency cycles
- **Centrality Calculations**: Betweenness, closeness, and eigenvector centrality measures
- **Impact Simulation**: Service failure impact prediction and recovery analysis
- **Optimization Analysis**: Architecture optimization opportunity identification
- **Performance Modeling**: Load distribution and bottleneck analysis

#### Topology Metrics (`modules/topology/metrics.py`)
- **Health Metrics**: Overall system health scoring and trend analysis
- **Reliability Metrics**: MTBF, MTTR, availability, and redundancy calculations
- **Performance Metrics**: Response times, throughput, scalability, and bottleneck analysis
- **Dependency Metrics**: Coupling analysis, circular dependencies, and dependency depth
- **Comprehensive Reporting**: Multi-dimensional topology health and performance reports
- **Historical Tracking**: Trend analysis and baseline comparisons
- **Risk Assessment**: Failure probability and impact severity calculations

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
#### Usage Analytics
- `GET /api/analytics/usage/overview` - Comprehensive API usage overview and metrics
- `GET /api/analytics/usage/patterns` - Advanced usage patterns and behavioral analysis
- `GET /api/analytics/real-time/metrics` - Current live analytics metrics

#### Performance Insights
- `GET /api/analytics/performance/insights` - Advanced performance analysis and optimization recommendations

#### Error Tracking
- `GET /api/analytics/errors/overview` - Comprehensive error analytics and root cause analysis
- `GET /api/analytics/errors/alerts` - Real-time error alerts and warnings

#### Data Collection
- `POST /api/analytics/record-request` - Record API request for analytics processing
- `POST /api/analytics/record-error` - Record API error for analytics and tracking

### Developer Tools
#### Code Generation
- `POST /api/tools/generate-client` - Generate API client SDK for specific service
- `POST /api/tools/generate-clients` - Generate client SDKs for multiple services
- `GET /api/tools/templates` - Available code generation templates

#### Validation
- `POST /api/tools/validate-spec` - Validate OpenAPI specification compliance
- `POST /api/tools/validate-request` - Validate API request against specification
- `POST /api/tools/validate-client` - Validate generated client against API spec

#### Testing
- `POST /api/tools/run-integration-test` - Run comprehensive integration tests

## Web UI Pages

### API Catalog & Documentation
- Browse all APIs by service, category, and functionality
- Interactive documentation viewer for each service
- Advanced search and filtering capabilities

### API Testing & Development
- Interactive testing tools with authentication
- Visual request builder and response viewer
- API validation and compliance checking

### Analytics & Insights
- **Usage Analytics Dashboard**: API usage patterns, trends, and behavioral analysis
- **Performance Insights**: Response time analysis, throughput optimization, bottleneck detection
- **Error Tracking & Alerts**: Real-time error monitoring with root cause analysis
- **User Behavior Analysis**: User segmentation, journey mapping, and engagement metrics
- **Real-Time Metrics**: Live API performance monitoring and health indicators
- **Predictive Analytics**: Usage forecasting and capacity planning recommendations

### Developer Tools
- **Client SDK Generation**: Generate production-ready API client libraries in multiple programming languages
- **API Specification Validation**: Comprehensive OpenAPI compliance checking and best practices validation
- **Integration Testing**: Automated API testing, load testing, and contract testing
- **Code Templates**: Browse and use production-ready code templates for various languages and frameworks
- **Request Validation**: Pre-flight validation of API requests against specifications
- **Live Testing**: Real-time API testing with authentication and response validation

### 🗺️ Service Topology
- **Dependency Mapping**: Visual representation of service relationships and dependencies
- **Critical Path Analysis**: Identification of high-impact service chains and failure points
- **Cluster Detection**: Automatic grouping of related services into functional clusters
- **Impact Assessment**: Service failure impact analysis and cascading effect prediction
- **Bottleneck Identification**: Performance and reliability bottleneck detection
- **Optimization Recommendations**: AI-powered suggestions for architecture improvements
- **Interactive Visualization**: Real-time topology graphs with multiple layout options

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
