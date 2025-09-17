# Integration Test Scripts

This directory contains test scripts for cross-service integration, Docker testing, and end-to-end workflows.

## Test Categories

### Docker Integration Tests
- `test_docker_services.py` - Test individual services and full ecosystem in Docker containers

### Cross-Service Integration Tests
- `test_full_integration.py` - End-to-end integration testing
- `test_service_mesh.py` - Service mesh and communication testing
- `test_workflow_management.py` - Workflow orchestration testing
- `test_orchestrator_minimal.py` - Minimal orchestrator integration
- `test_orchestrator_simple.py` - Simple orchestrator workflows

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
