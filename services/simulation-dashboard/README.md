# 🎯 Project Simulation Dashboard Service

A comprehensive, interactive frontend platform for the Project Simulation Service, providing rich visualizations, real-time monitoring, and intuitive management interfaces through a modern Python-based dashboard.

## 🚀 Quick Start

### Option 1: Terminal Mode (Development)
```bash
# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run app.py --server.port 8501
```

### Option 2: Docker Mode (Production)
```bash
# Build and run with Docker
docker build -t simulation-dashboard .
docker run -p 8501:8501 simulation-dashboard
```

### Option 3: Ecosystem Mode (Full Integration)
```bash
# Run simulation services only
docker-compose -f docker-compose.simulation.yml up

# Or run with the full LLM Documentation Ecosystem
cd ../..  # Go to project root
docker-compose --profile simulation up
```

## 📋 Features

### 🎮 Interactive Dashboard
- **Real-time Monitoring**: Live simulation progress with WebSocket integration
- **Comprehensive Analytics**: Interactive charts and performance visualizations
- **Intuitive Interface**: User-friendly design for complex simulation workflows

### 📊 Key Capabilities
- **Simulation Management**: Create, monitor, and manage project simulations
- **Live Progress Tracking**: Real-time updates during simulation execution
- **Report Generation**: Interactive reports with export capabilities
- **Health Monitoring**: System status and ecosystem service monitoring
- **Configuration Management**: Easy setup and parameter management

### 🌐 Multi-Deployment Support
- **Terminal Mode**: Run locally for development and testing
- **Docker Mode**: Containerized deployment for production
- **Ecosystem Mode**: Full integration with the LLM Documentation Ecosystem

## 🏗️ Architecture

### Directory Structure
```
simulation-dashboard/
├── app.py                 # Main Streamlit application
├── pages/                 # Page-based navigation
│   ├── overview.py        # Main dashboard
│   ├── create.py          # Simulation creation
│   ├── monitor.py         # Real-time monitoring
│   ├── reports.py         # Analytics & reporting
│   └── config.py          # Configuration management
├── components/            # Reusable UI components
├── services/              # Service clients
│   ├── simulation_client.py
│   └── websocket_client.py
├── domain/                # Domain models
├── infrastructure/        # Infrastructure concerns
│   ├── config.py          # Configuration management
│   └── logging/           # Logging setup
├── utils/                 # Utility functions
├── tests/                 # Test suite
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose setup
└── README.md             # This file
```

### Service Integration
- **Primary**: Project Simulation Service (HTTP API + WebSocket)
- **Secondary**: Analysis Service (optional, HTTP API)
- **Minimal**: Health Monitoring Service (optional, HTTP API)

## ⚙️ Configuration

### Environment Variables
```bash
# Dashboard Configuration
DASHBOARD_ENVIRONMENT=development|production
DASHBOARD_DEBUG=true|false
DASHBOARD_PORT=8501

# Simulation Service Connection
DASHBOARD_SIMULATION_SERVICE_HOST=localhost
DASHBOARD_SIMULATION_SERVICE_PORT=5075

# Optional Services
DASHBOARD_ANALYSIS_SERVICE_URL=http://localhost:5080
DASHBOARD_HEALTH_SERVICE_URL=http://localhost:5090

# WebSocket Configuration
DASHBOARD_WEBSOCKET_ENABLED=true
DASHBOARD_WEBSOCKET_RECONNECT_ATTEMPTS=5
```

### Configuration File
Create a `.env` file in the project root:
```env
DASHBOARD_ENVIRONMENT=development
DASHBOARD_SIMULATION_SERVICE_HOST=localhost
DASHBOARD_SIMULATION_SERVICE_PORT=5075
```

## 📊 Dashboard Pages

### 🏠 Overview
- Key performance metrics and KPIs
- Active simulations overview
- Recent activity feed
- Quick action buttons
- System status indicators

### ➕ Create
- Guided simulation creation wizard
- Configuration file management
- Template selection and customization
- Parameter validation and preview

### 📊 Monitor
- Real-time simulation progress tracking
- Live event stream and notifications
- Timeline visualization
- Performance metrics display
- WebSocket-powered updates

### 📋 Reports
- Interactive report generation
- Chart and graph visualizations
- Multiple export formats (PDF, Excel, JSON)
- Report history and management
- Custom dashboard creation

### ⚙️ Configure
- Service connection management
- Health monitoring dashboard
- System configuration settings
- Theme and UI customization

## 🔧 Development

### Prerequisites
- Python 3.13+
- pip package manager
- Docker (optional, for containerized deployment)

### Local Development Setup
```bash
# Clone the repository
git clone <repository-url>
cd services/simulation-dashboard

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run in development mode
streamlit run app.py --server.port 8501 --server.reload=True
```

### Testing
```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html
```

## 🚀 Quick Start

## Prerequisites
- Python 3.13+
- pip package manager
- Simulation service running (optional for basic functionality)

## Option 1: Terminal Mode (Development)
```bash
# Install dependencies
pip install -r requirements.txt

# Start the dashboard
python run_dashboard.py
# or directly with streamlit
streamlit run app.py --server.port 8501
```

## Option 2: Docker Mode (Production)
```bash
# Build and run with Docker
docker build -t simulation-dashboard .
docker run -p 8501:8501 simulation-dashboard
```

## Option 3: Docker Compose (Ecosystem Integration)
```bash
# Run simulation services only
cd ../..  # Go to project root
docker-compose -f docker-compose.simulation.yml up

# Or run with the full LLM Documentation Ecosystem
docker-compose --profile simulation up
```

# 🧪 Testing

## Run Tests
```bash
# Run all tests
python test_dashboard.py

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/functional/
```

## Test Coverage
```bash
# Run tests with coverage
pytest --cov=. --cov-report=html
```

# 📊 Dashboard Features

## 🏠 Overview Page
- **Key Metrics**: Total simulations, active simulations, success rates
- **Recent Activity**: Latest simulation events and status updates
- **Quick Actions**: Fast access to common operations
- **System Status**: Health indicators and performance metrics

## ➕ Create Page
- **Quick Start**: One-click simulation creation for common types
- **Advanced Configuration**: Full simulation setup with validation
- **Template Support**: Pre-configured simulation templates
- **Parameter Validation**: Real-time validation and error checking

## 📊 Monitor Page
- **Real-Time Updates**: Live progress tracking via WebSocket
- **Event Stream**: Real-time event notifications and filtering
- **Performance Metrics**: System and simulation performance data
- **Connection Status**: WebSocket and service connection monitoring

## 📋 Reports Page
- **Report Generation**: Interactive report creation
- **Multiple Formats**: JSON, HTML, PDF, Markdown export
- **Visualization**: Charts and graphs for insights
- **Report History**: Access to previously generated reports

## ⚙️ Configuration Page
- **Service Management**: Connection settings and health checks
- **Environment Settings**: Theme and UI customization
- **Integration Status**: Ecosystem service connectivity
- **System Diagnostics**: Performance and health monitoring

# 🐳 Docker Deployment

## Standalone Docker
```bash
# Build the image
docker build -t simulation-dashboard .

# Run with simulation service
docker run -p 8501:8501 \
  -e DASHBOARD_SIMULATION_SERVICE_HOST=host.docker.internal \
  -e DASHBOARD_SIMULATION_SERVICE_PORT=5075 \
  simulation-dashboard
```

## Docker Compose Configuration
```yaml
version: '3.8'
services:
  simulation-dashboard:
    build: ./services/simulation-dashboard
    ports:
      - "8501:8501"
    environment:
      - DASHBOARD_SIMULATION_SERVICE_HOST=project-simulation
      - DASHBOARD_SIMULATION_SERVICE_PORT=5075
      - DASHBOARD_ENVIRONMENT=production
    depends_on:
      - project-simulation
    networks:
      - simulation-network
    restart: unless-stopped
```

# ⚙️ Configuration

## Environment Variables
```bash
# Core Configuration
DASHBOARD_ENVIRONMENT=development|production
DASHBOARD_DEBUG=true|false
DASHBOARD_PORT=8501

# Simulation Service
DASHBOARD_SIMULATION_SERVICE_HOST=localhost
DASHBOARD_SIMULATION_SERVICE_PORT=5075

# Optional Ecosystem Services
DASHBOARD_ANALYSIS_SERVICE_URL=http://localhost:5080
DASHBOARD_HEALTH_SERVICE_URL=http://localhost:5090

# WebSocket Settings
DASHBOARD_WEBSOCKET_ENABLED=true
DASHBOARD_WEBSOCKET_RECONNECT_ATTEMPTS=5

# Performance
DASHBOARD_PERFORMANCE_MAX_CONCURRENT_REQUESTS=10
DASHBOARD_PERFORMANCE_ENABLE_COMPRESSION=true
```

## Configuration File
Copy `config.example.env` to `.env` and modify as needed:
```bash
cp config.example.env .env
# Edit .env with your settings
```

# 🔧 Development

## Local Development Setup
```bash
# Clone and setup
git clone <repository-url>
cd services/simulation-dashboard

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
python test_dashboard.py

# Start development server
python run_dashboard.py
```

## Project Structure
```
simulation-dashboard/
├── app.py                    # Main Streamlit application
├── pages/                    # Page components
│   ├── overview.py          # Dashboard overview
│   ├── create.py            # Simulation creation
│   ├── monitor.py           # Real-time monitoring
│   ├── reports.py           # Reporting interface
│   └── config.py            # Configuration page
├── components/               # Reusable UI components
│   ├── sidebar.py           # Navigation sidebar
│   ├── header.py            # Page header
│   └── footer.py            # Page footer
├── services/                 # Service clients
│   ├── clients/
│   │   ├── simulation_client.py
│   │   └── websocket_client.py
├── infrastructure/           # Infrastructure code
│   ├── config/              # Configuration management
│   └── logging/             # Logging setup
├── tests/                   # Test suite
├── requirements.txt         # Python dependencies
├── run_dashboard.py         # Development runner
├── test_dashboard.py        # Test runner
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose setup
└── README.md               # This file
```

# 🌐 API Integration

## Simulation Service Endpoints
The dashboard integrates with these key endpoints:

- `GET /api/v1/simulations` - List simulations
- `POST /api/v1/simulations` - Create simulation
- `GET /api/v1/simulations/{id}` - Get simulation details
- `POST /api/v1/simulations/{id}/execute` - Execute simulation
- `GET /api/v1/simulations/{id}/reports` - Get reports
- `WS /ws/simulations/{id}` - Real-time updates

## WebSocket Events
Real-time updates include:
- Simulation progress updates
- Domain event notifications
- System status changes
- Performance metrics

# 📈 Performance & Monitoring

## Performance Metrics
- **Load Time**: < 3 seconds dashboard load
- **Real-time Updates**: < 1 second latency
- **API Response**: < 100ms cached responses
- **Memory Usage**: < 500MB Docker container
- **Concurrent Users**: Supports 10+ simultaneous users

## Health Checks
- Service connectivity monitoring
- WebSocket connection status
- API endpoint availability
- System resource usage
- Cache performance metrics

# 🔒 Security

## Best Practices
- Environment-aware configuration
- Secure WebSocket connections (WSS in production)
- Input validation and sanitization
- CORS configuration for web security
- Non-root Docker container execution

## Production Considerations
- SSL/TLS encryption for WebSocket connections
- Authentication and authorization
- Rate limiting and DDoS protection
- Audit logging and monitoring
- Regular security updates

# 🤝 Contributing

## Development Workflow
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`python test_dashboard.py`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Code Standards
- Follow PEP 8 style guidelines
- Use type hints for function parameters
- Write comprehensive docstrings
- Add tests for new functionality
- Maintain test coverage above 80%

# 📚 Documentation

## User Guides
- [Getting Started](docs/user/getting-started.md)
- [Dashboard Features](docs/user/features.md)
- [Configuration Guide](docs/user/configuration.md)

## Developer Documentation
- [Architecture Overview](docs/developer/architecture.md)
- [API Reference](docs/developer/api-reference.md)
- [Contributing Guide](docs/developer/contributing.md)

## Deployment Guides
- [Local Development](docs/deployment/local-development.md)
- [Docker Deployment](docs/deployment/docker-deployment.md)
- [Production Setup](docs/deployment/production-setup.md)

# 🐛 Troubleshooting

## Common Issues

### Dashboard won't start
```bash
# Check Python version
python --version  # Should be 3.13+

# Check dependencies
python test_dashboard.py

# Check port availability
lsof -i :8501
```

### WebSocket connection fails
```bash
# Verify simulation service is running
curl http://localhost:5075/health

# Check WebSocket configuration
echo $DASHBOARD_WEBSOCKET_ENABLED  # Should be 'true'

# Check network connectivity
telnet localhost 5075
```

### Slow performance
```bash
# Enable caching
export DASHBOARD_PERFORMANCE_ENABLE_COMPRESSION=true

# Increase concurrent requests
export DASHBOARD_PERFORMANCE_MAX_CONCURRENT_REQUESTS=20

# Check system resources
top  # Monitor CPU and memory usage
```

### Import errors
```bash
# Install missing dependencies
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"

# Verify file permissions
ls -la services/simulation-dashboard/
```

## Debug Mode
Enable detailed logging for troubleshooting:
```bash
export DASHBOARD_DEBUG=true
export DASHBOARD_LOGGING_LEVEL=DEBUG
python run_dashboard.py
```

# 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

# 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Part of the LLM Documentation Ecosystem
- Inspired by modern dashboard design patterns
- Thanks to the open-source community for amazing tools

---

**🎉 Ready to explore the future of project simulation management? Start the dashboard and create your first simulation!**

```bash
# Quick start
pip install -r requirements.txt
python run_dashboard.py
```

Then open http://localhost:8501 in your browser! 🚀

## 🌐 API Integration

### Simulation Service Endpoints
The dashboard integrates with the following simulation service endpoints:

- `GET /api/v1/simulations` - List simulations
- `POST /api/v1/simulations` - Create simulation
- `GET /api/v1/simulations/{id}` - Get simulation details
- `POST /api/v1/simulations/{id}/execute` - Execute simulation
- `GET /api/v1/simulations/{id}/reports` - Get simulation reports
- `WS /ws/simulations/{id}` - Real-time updates

### WebSocket Integration
Real-time updates are handled through WebSocket connections:
- Simulation progress updates
- Domain event notifications
- System status changes
- Live event streaming

## 📈 Performance & Monitoring

### Performance Metrics
- Dashboard load time: < 3 seconds
- Real-time updates: < 1 second latency
- API response times: < 100ms (cached)
- Memory usage: < 500MB Docker image
- Concurrent users: Support for 10+ simultaneous users

### Health Checks
- Service connectivity monitoring
- WebSocket connection status
- API endpoint availability
- System resource usage tracking

## 🔒 Security

### Best Practices
- Environment-aware configuration
- Secure WebSocket connections
- Input validation and sanitization
- CORS configuration for web security
- Non-root Docker container execution

### Production Considerations
- SSL/TLS encryption for WebSocket connections
- Authentication and authorization
- Rate limiting and DDoS protection
- Audit logging and monitoring
- Regular security updates

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Code Standards
- Follow PEP 8 style guidelines
- Use type hints for function parameters
- Write comprehensive docstrings
- Maintain test coverage above 80%
- Use meaningful commit messages

## 📚 Documentation

### User Guides
- [Getting Started](docs/user/getting-started.md)
- [Dashboard Features](docs/user/features.md)
- [Configuration Guide](docs/user/configuration.md)

### Developer Documentation
- [Architecture Overview](docs/developer/architecture.md)
- [API Reference](docs/developer/api-reference.md)
- [Contributing Guide](docs/developer/contributing.md)

### Deployment Guides
- [Local Development](docs/deployment/local-development.md)
- [Docker Deployment](docs/deployment/docker-deployment.md)
- [Production Setup](docs/deployment/production-setup.md)

## 🐛 Troubleshooting

### Common Issues

**Dashboard won't start**
```bash
# Check if port 8501 is available
lsof -i :8501

# Check Python dependencies
pip check
```

**WebSocket connection fails**
```bash
# Verify simulation service is running
curl http://localhost:5075/health

# Check WebSocket configuration
# Ensure DASHBOARD_WEBSOCKET_ENABLED=true
```

**Slow performance**
```bash
# Enable caching
export DASHBOARD_PERFORMANCE_ENABLE_COMPRESSION=true

# Increase concurrent requests
export DASHBOARD_PERFORMANCE_MAX_CONCURRENT_REQUESTS=20
```

### Debug Mode
Enable debug logging for detailed information:
```bash
export DASHBOARD_DEBUG=true
export DASHBOARD_LOGGING_LEVEL=DEBUG
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Part of the LLM Documentation Ecosystem
- Inspired by modern dashboard design patterns
- Thanks to the open-source community

---

**🎉 Ready to explore the future of project simulation management? Start the dashboard and create your first simulation!**
