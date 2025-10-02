# Integration Test Scripts

This directory contains test scripts for cross-service integration, Docker testing, and end-to-end workflows.

## Scripts

### Docker Integration Tests

#### `comprehensive_docker_test.py`
**Docker Ecosystem Integration Suite** - Comprehensive testing of all services in Docker containers with full orchestration.

**Features:**
- Complete Docker Compose ecosystem testing
- Service dependency validation in containerized environment
- Network connectivity testing between containers
- Volume mount and data persistence validation
- Resource usage monitoring in Docker environment

**Use Cases:**
- Full ecosystem deployment validation
- Docker Compose configuration testing
- Multi-service integration in containerized environment
- Production deployment simulation
- Container orchestration validation

#### `test_docker_services.py`
**Individual Docker Service Validator** - Focused testing of individual services within Docker containers.

**Features:**
- Individual service startup and health validation in Docker
- Service-specific configuration testing in containers
- Docker networking and port mapping validation
- Container resource usage monitoring
- Docker-specific error handling and recovery testing

**Use Cases:**
- Individual service Docker deployment validation
- Service isolation testing in containers
- Docker configuration optimization
- Containerized service debugging
- Microservice deployment validation

### Cross-Service Integration Tests

#### `test_full_integration.py`
**End-to-End Integration Test Suite** - Comprehensive validation of complete business workflows across all services.

**Features:**
- Complete end-to-end business process testing
- Multi-service workflow orchestration validation
- Data flow validation across service boundaries
- Integration point testing and contract validation
- Performance testing under full integration load

**Use Cases:**
- Complete system functionality validation
- Business process automation testing
- Service integration regression testing
- Enterprise workflow validation
- System reliability and consistency testing

#### `test_inter_service_communication.py`
**Service Mesh Communication Validator** - Advanced testing of inter-service communication patterns and protocols.

**Features:**
- Service discovery and registration validation
- Message routing and load balancing testing
- Communication protocol validation (HTTP, gRPC, messaging)
- Service mesh configuration testing
- Communication latency and reliability testing

**Use Cases:**
- Microservice communication architecture validation
- Service mesh troubleshooting and optimization
- Network topology and routing validation
- Distributed system communication testing
- Service discovery and registration validation

#### `test_service_mesh.py`
**Service Mesh Architecture Tester** - Comprehensive validation of service mesh implementation and functionality.

**Features:**
- Service mesh topology validation
- Traffic routing and policy enforcement testing
- Service-to-service authentication validation
- Observability and tracing integration testing
- Service mesh security policy validation

**Use Cases:**
- Service mesh deployment and configuration validation
- Microservice security architecture testing
- Traffic management and routing validation
- Observability pipeline validation
- Service mesh migration and upgrade testing

#### `test_workflow_management.py`
**Workflow Orchestration Validator** - Advanced testing of complex multi-service workflow orchestration.

**Features:**
- Complex workflow execution validation
- Workflow state management and persistence testing
- Error handling and compensation logic testing
- Workflow performance and scalability testing
- Business rule engine integration validation

**Use Cases:**
- Business process automation validation
- Workflow engine reliability testing
- Complex transaction processing validation
- Business rule compliance testing
- Workflow performance optimization

### Event Streaming Tests
- `test_event_streaming.py` - Event streaming between services
- `test_redis_event_emission.py` - Redis-based event emission

### Phase Testing
- `test_phase2_focused.py` - Phase 2 focused integration tests
- `test_phase2_implementation.py` - Phase 2 implementation verification
- `test_phase2_simple.py` - Simple phase 2 integration tests

### Enterprise Feature Tests
- `test_enterprise_error_handling.py` - Enterprise error handling scenarios
- `test_automated_remediation.py` - Automated remediation workflows
- `test_change_impact_analysis.py` - Change impact analysis across services

### Analysis Integration Tests
- `test_content_quality.py` - Content quality analysis integration
- `test_maintenance_forecasting.py` - Maintenance forecasting workflows
- `test_peer_review_enhancement.py` - Peer review enhancement integration
- `test_quality_degradation_detection.py` - Quality degradation detection
- `test_risk_assessment.py` - Risk assessment integration
- `test_sentiment_analysis.py` - Sentiment analysis workflows
- `test_summarizer_categorization.py` - Summarizer categorization
- `test_trend_analysis.py` - Trend analysis integration
- `test_workflow_triggered_analysis.py` - Workflow-triggered analysis

## Test Scope

Integration tests focus on:
- ✅ Cross-service communication and workflows
- ✅ Docker containerization and orchestration
- ✅ Event streaming and messaging between services
- ✅ End-to-end business process validation
- ✅ Service mesh and discovery functionality
- ✅ Multi-service data flow validation
- ✅ Error handling across service boundaries
- ✅ Performance testing with multiple services

## Dependencies

Integration tests require:
- All individual services to pass their unit tests
- Docker environment for containerized testing
- Redis for event streaming tests
- Network connectivity between services

## Usage

```bash
# Test Docker integration
python scripts/integration/test_docker_services.py --individual

# Test full service integration
python scripts/integration/test_full_integration.py

# Test service mesh
python scripts/integration/test_service_mesh.py

# Test workflow orchestration
python scripts/integration/test_workflow_management.py
```

## Test Execution Order

1. **Individual Service Tests** (in `services/`) - Prerequisites
2. **Integration Tests** (this directory) - Main validation
3. **CLI Tests** (in `cli/`) - User interface validation
4. **Validation Tests** (in `validation/`) - Compliance and standards

## Performance Considerations

Integration tests are resource-intensive and should be run:
- On dedicated test environments
- During off-peak hours for CI/CD
- With proper monitoring and resource allocation
- With cleanup procedures for Docker containers
