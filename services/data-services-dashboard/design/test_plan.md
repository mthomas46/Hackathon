# Test Plan - data-services-dashboard

**Service**: data-services-dashboard  
**Type**: Streamlit Dashboard  
**Date**: October 9, 2025  
**Target Coverage**: 80%+

---

## 🎯 Testing Strategy

### **Dashboard Testing Challenges**

Streamlit dashboards present unique testing challenges:
- **Stateful UI**: Entire script re-runs on interaction
- **Visual Output**: Hard to test chart rendering
- **Browser-based**: No traditional API endpoints
- **Session State**: User interactions persist

### **Adapted Test Pyramid**

```
         /\
        /  \       Manual/Visual (5%)
       /____\      - Visual regression
      /      \     - Manual UAT
     /  Func  \    Functional (25%)
    /__________\   - Tab rendering logic
   /            \  - Dashboard flow
  /   Unit (70%) \ Unit (70%)
 /________________\- Data processing
                   - Metric calculation
```

**Target Breakdown**:
- **Unit**: 70% (~200 tests) - Data processing, transformations
- **Functional**: 25% (~50 tests) - Dashboard logic
- **Manual/Visual**: 5% - Visual verification

**Total Target**: 80%+ code coverage

---

## 🧪 Unit Tests (70% - Target: 200+ tests)

### **Test Coverage by Module**

| Module | Target Tests | Coverage Target | Priority |
|--------|--------------|-----------------|----------|
| `data/fetcher.py` | 30 | 90%+ | CRITICAL |
| `data/parser.py` | 40 | 90%+ | CRITICAL |
| `data/models.py` | 20 | 100% | CRITICAL |
| `metrics/calculator.py` | 60 | 90%+ | CRITICAL |
| `utils/formatting.py` | 20 | 90%+ | HIGH |
| `config.py` | 15 | 90%+ | HIGH |
| **TOTAL** | **185** | **90%+** | - |

### **1. data/fetcher.py Tests** (30 tests)

**File**: `tests/unit/test_data_fetcher.py`

**Test Categories**:

#### **Successful Fetching** (10 tests)
```python
def test_fetch_logs_returns_list()
def test_fetch_logs_with_service_filter()
def test_fetch_logs_with_limit()
def test_fetch_logs_with_all_services()
def test_fetch_logs_caching_works()
def test_fetch_logs_cache_expiry()
def test_fetch_logs_empty_response()
def test_fetch_logs_pagination()
def test_fetch_logs_custom_timeout()
def test_fetch_logs_url_construction()
```

#### **Error Handling** (12 tests)
```python
def test_fetch_logs_connection_error()
def test_fetch_logs_timeout_error()
def test_fetch_logs_404_error()
def test_fetch_logs_500_error()
def test_fetch_logs_invalid_json()
def test_fetch_logs_missing_items_key()
def test_fetch_logs_network_timeout()
def test_fetch_logs_ssl_error()
def test_fetch_logs_redirect_handling()
def test_fetch_logs_retries_on_failure()
def test_fetch_logs_max_retries_exceeded()
def test_fetch_logs_graceful_degradation()
```

#### **Edge Cases** (8 tests)
```python
def test_fetch_logs_with_none_service()
def test_fetch_logs_with_empty_service()
def test_fetch_logs_with_zero_limit()
def test_fetch_logs_with_negative_limit()
def test_fetch_logs_with_very_large_limit()
def test_fetch_logs_with_special_chars_in_service()
def test_fetch_logs_with_invalid_url()
def test_fetch_logs_concurrent_requests()
```

**Mock Strategy**:
```python
@pytest.fixture
def mock_http_response():
    """Mock successful HTTP response."""
    return {
        "items": [
            {
                "timestamp": "2025-10-09T12:00:00Z",
                "service": "doc_store",
                "level": "INFO",
                "context": {...}
            }
        ]
    }

@pytest.mark.unit
def test_fetch_logs_returns_list(mock_http_response, monkeypatch):
    """Test fetch_logs returns list of logs."""
    def mock_get(*args, **kwargs):
        response = Mock()
        response.json.return_value = mock_http_response
        response.status_code = 200
        return response
    
    monkeypatch.setattr(httpx, 'get', mock_get)
    
    logs = fetch_logs(url="http://test", limit=10)
    
    assert isinstance(logs, list)
    assert len(logs) == 1
    assert logs[0]["service"] == "doc_store"
```

---

### **2. data/parser.py Tests** (40 tests)

**File**: `tests/unit/test_data_parser.py`

**Test Categories**:

#### **Valid Parsing** (15 tests)
```python
def test_parse_log_entry_complete_data()
def test_parse_log_entry_minimal_data()
def test_parse_log_entry_timestamp_parsing()
def test_parse_log_entry_context_extraction()
def test_parse_log_entry_default_values()
def test_parse_logs_multiple_entries()
def test_parse_logs_empty_list()
def test_parse_logs_preserves_order()
def test_parse_log_entry_with_workflow_id()
def test_parse_log_entry_without_workflow_id()
def test_parse_log_entry_success_flag()
def test_parse_log_entry_duration_extraction()
def test_parse_log_entry_status_code_extraction()
def test_parse_log_entry_operation_type_extraction()
def test_parse_log_entry_phase_extraction()
```

#### **Invalid Data Handling** (15 tests)
```python
def test_parse_log_entry_missing_timestamp()
def test_parse_log_entry_invalid_timestamp_format()
def test_parse_log_entry_missing_service()
def test_parse_log_entry_missing_context()
def test_parse_log_entry_null_values()
def test_parse_log_entry_extra_fields()
def test_parse_log_entry_nested_context()
def test_parse_log_entry_invalid_duration()
def test_parse_log_entry_invalid_status_code()
def test_parse_log_entry_malformed_json()
def test_parse_logs_with_invalid_entry()
def test_parse_logs_partial_failure()
def test_parse_log_entry_unicode_handling()
def test_parse_log_entry_large_message()
def test_parse_log_entry_special_characters()
```

#### **Validation** (10 tests)
```python
def test_validate_log_valid_structure()
def test_validate_log_missing_required_field()
def test_validate_log_empty_dict()
def test_validate_log_null_values()
def test_validate_log_type_errors()
def test_validate_log_timestamp_validation()
def test_validate_log_service_name_validation()
def test_validate_log_level_validation()
def test_validate_log_context_structure()
def test_validate_log_workflow_id_format()
```

---

### **3. metrics/calculator.py Tests** (60 tests)

**File**: `tests/unit/test_metrics_calculator.py`

**Test Categories**:

#### **Basic Calculations** (20 tests)
```python
def test_calculate_metrics_empty_logs()
def test_calculate_metrics_single_log()
def test_calculate_metrics_multiple_logs()
def test_calculate_metrics_total_operations()
def test_calculate_metrics_successful_operations()
def test_calculate_metrics_failed_operations()
def test_calculate_metrics_avg_duration()
def test_calculate_metrics_error_rate()
def test_calculate_metrics_zero_error_rate()
def test_calculate_metrics_100_percent_error_rate()
def test_calculate_metrics_operations_per_service()
def test_calculate_metrics_multiple_services()
def test_calculate_metrics_single_service()
def test_calculate_metrics_duration_aggregation()
def test_calculate_metrics_status_code_filtering()
def test_calculate_metrics_phase_filtering()
def test_calculate_metrics_workflow_grouping()
def test_calculate_metrics_time_range_filtering()
def test_calculate_metrics_service_filtering()
def test_calculate_metrics_operation_type_filtering()
```

#### **Edge Cases** (20 tests)
```python
def test_calculate_metrics_all_success()
def test_calculate_metrics_all_failures()
def test_calculate_metrics_no_completed_operations()
def test_calculate_metrics_no_durations()
def test_calculate_metrics_zero_duration()
def test_calculate_metrics_very_large_duration()
def test_calculate_metrics_negative_duration()
def test_calculate_metrics_null_success_flag()
def test_calculate_metrics_mixed_phases()
def test_calculate_metrics_missing_context()
def test_calculate_metrics_invalid_operation_type()
def test_calculate_metrics_duplicate_workflow_ids()
def test_calculate_metrics_concurrent_operations()
def test_calculate_metrics_large_dataset()
def test_calculate_metrics_service_name_variations()
def test_calculate_metrics_timestamp_ordering()
def test_calculate_metrics_status_code_ranges()
def test_calculate_metrics_incomplete_logs()
def test_calculate_metrics_partial_data()
def test_calculate_metrics_data_consistency()
```

#### **Aggregations** (20 tests)
```python
def test_aggregate_by_service()
def test_aggregate_by_operation_type()
def test_aggregate_by_workflow()
def test_aggregate_by_time_period()
def test_aggregate_by_status_code()
def test_aggregate_by_success_flag()
def test_aggregate_duration_percentiles()
def test_aggregate_error_distribution()
def test_aggregate_service_health()
def test_aggregate_workflow_metrics()
def test_aggregate_performance_trends()
def test_aggregate_with_empty_data()
def test_aggregate_with_single_item()
def test_aggregate_with_multiple_dimensions()
def test_aggregate_statistical_measures()
def test_aggregate_count_unique_workflows()
def test_aggregate_average_by_service()
def test_aggregate_max_duration()
def test_aggregate_min_duration()
def test_aggregate_median_duration()
```

---

### **4. data/models.py Tests** (20 tests)

**File**: `tests/unit/test_models.py`

```python
def test_log_entry_validation_success()
def test_log_entry_required_fields()
def test_log_entry_optional_fields()
def test_log_entry_default_values()
def test_log_entry_timestamp_validation()
def test_log_entry_invalid_timestamp()
def test_log_entry_duration_validation()
def test_log_entry_negative_duration()
def test_log_entry_status_code_validation()
def test_log_entry_invalid_status_code()
def test_log_entry_json_serialization()
def test_log_entry_from_dict()
def test_metrics_summary_validation()
def test_metrics_summary_calculations()
def test_metrics_summary_error_rate_bounds()
def test_metrics_summary_non_negative_values()
def test_metrics_summary_dict_conversion()
def test_dashboard_config_defaults()
def test_dashboard_config_env_vars()
def test_dashboard_config_validation()
```

---

### **5. utils/formatting.py Tests** (20 tests)

**File**: `tests/unit/test_utils_formatting.py`

```python
def test_format_duration_milliseconds()
def test_format_duration_seconds()
def test_format_duration_minutes()
def test_format_duration_zero()
def test_format_duration_none()
def test_format_duration_negative()
def test_truncate_workflow_id_standard()
def test_truncate_workflow_id_short()
def test_truncate_workflow_id_empty()
def test_truncate_workflow_id_none()
def test_format_timestamp()
def test_format_percentage()
def test_format_service_name()
def test_format_operation_type()
def test_format_status_code_success()
def test_format_status_code_error()
def test_format_metric_value()
def test_colorize_status()
def test_render_health_indicator()
def test_format_large_numbers()
```

---

### **6. config.py Tests** (15 tests)

**File**: `tests/unit/test_config.py`

```python
def test_load_config_defaults()
def test_load_config_from_env()
def test_config_log_collector_url()
def test_config_default_services()
def test_config_time_ranges()
def test_config_cache_ttl()
def test_config_cache_ttl_bounds()
def test_config_env_prefix()
def test_config_case_insensitive()
def test_config_validation()
def test_config_reload()
def test_config_invalid_url()
def test_config_invalid_ttl()
def test_config_missing_env_vars()
def test_config_partial_env_vars()
```

---

## 🔗 Integration Tests (20% - Target: 30 tests)

### **1. Log Collector Integration** (30 tests)

**File**: `tests/integration/test_log_collector_integration.py`

**Prerequisites**: log-collector service must be running

```python
@pytest.mark.integration
def test_fetch_logs_from_real_log_collector()
def test_fetch_logs_with_service_filter()
def test_fetch_logs_with_pagination()
def test_fetch_logs_connection_failure()
def test_fetch_logs_timeout_handling()
def test_fetch_logs_retry_logic()
def test_parse_real_log_entries()
def test_calculate_metrics_from_real_data()
def test_end_to_end_data_pipeline()
def test_caching_with_real_requests()
def test_concurrent_requests_handling()
def test_large_dataset_fetching()
def test_service_filter_accuracy()
def test_limit_parameter_enforcement()
def test_response_format_compatibility()
def test_error_response_handling()
def test_malformed_response_handling()
def test_network_interruption_recovery()
def test_service_restart_handling()
def test_data_consistency_checks()
def test_timestamp_ordering()
def test_workflow_id_consistency()
def test_operation_phase_completion()
def test_duration_accuracy()
def test_status_code_propagation()
def test_context_data_preservation()
def test_service_name_normalization()
def test_high_volume_data_handling()
def test_real_time_data_streaming()
def test_data_freshness_validation()
```

**Setup**:
```python
@pytest.fixture(scope="module")
def log_collector_client():
    """Ensure log-collector is available for tests."""
    url = "http://localhost:8104"
    try:
        response = httpx.get(f"{url}/health", timeout=5.0)
        if response.status_code == 200:
            return url
    except Exception:
        pytest.skip("log-collector not available")
```

---

## 🖥️ Functional Tests (10% - Target: 20 tests)

### **Dashboard Rendering Tests**

**File**: `tests/functional/test_dashboard_rendering.py`

**Note**: Streamlit testing is limited - focus on logic, not UI

```python
@pytest.mark.functional
def test_render_overview_tab_with_data()
def test_render_overview_tab_without_data()
def test_render_performance_tab_calculations()
def test_render_operations_tab_filtering()
def test_render_workflows_tab_grouping()
def test_render_errors_tab_error_filtering()
def test_main_dashboard_flow()
def test_sidebar_filter_application()
def test_auto_refresh_behavior()
def test_cache_invalidation()
def test_metric_display_accuracy()
def test_chart_data_transformation()
def test_tab_switching_state()
def test_filter_persistence()
def test_export_functionality()
def test_pagination_controls()
def test_error_message_display()
def test_loading_indicators()
def test_empty_state_handling()
def test_large_dataset_rendering()
```

**Strategy**: Test data transformation logic, not visual output

---

## 📊 Test Execution Plan

### **Phase 1: Unit Tests** (Priority: CRITICAL)
```bash
# Run all unit tests
pytest tests/unit/ -v --cov=data --cov=metrics --cov=utils --cov=config

# Expected: 185+ tests, 90%+ coverage
```

### **Phase 2: Integration Tests** (Priority: HIGH)
```bash
# Requires log-collector running
docker-compose up log-collector -d

# Run integration tests
pytest tests/integration/ -v -m integration

# Expected: 30 tests
```

### **Phase 3: Functional Tests** (Priority: MEDIUM)
```bash
# Run functional tests
pytest tests/functional/ -v -m functional

# Expected: 20 tests
```

### **Phase 4: Full Test Suite**
```bash
# Run all tests with coverage
pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing

# Expected: 235+ tests, 80%+ coverage
```

---

## 🎯 Coverage Targets

| Component | Target | Priority |
|-----------|--------|----------|
| `data/fetcher.py` | 90%+ | CRITICAL |
| `data/parser.py` | 90%+ | CRITICAL |
| `data/models.py` | 100% | CRITICAL |
| `metrics/calculator.py` | 90%+ | CRITICAL |
| `utils/formatting.py` | 90%+ | HIGH |
| `config.py` | 90%+ | HIGH |
| `visualization/*.py` | 60%+ | MEDIUM |
| `app.py` | 70%+ | MEDIUM |
| **OVERALL** | **80%+** | **TARGET** |

---

## ✅ Test Infrastructure

### **pytest.ini**
```ini
[pytest]
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (requires log-collector)
    functional: Functional tests (dashboard logic)
    slow: Slow tests (large datasets)

testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

addopts = 
    --cov=.
    --cov-report=term-missing
    --cov-report=html
    --strict-markers
    -v

cov_fail_under = 80
```

### **conftest.py**
```python
import pytest
from datetime import datetime, timezone
from data.models import LogEntry, MetricsSummary


@pytest.fixture
def sample_log_entry():
    """Sample log entry for testing."""
    return LogEntry(
        timestamp=datetime.now(timezone.utc),
        service="doc_store",
        level="INFO",
        message="Test message",
        operation_type="CREATE",
        method="POST",
        path="/api/v1/documents",
        status_code=201,
        duration_ms=15.5,
        success=True,
        phase="complete",
        workflow_id="wf_test123"
    )


@pytest.fixture
def sample_logs(sample_log_entry):
    """List of sample logs."""
    return [sample_log_entry for _ in range(10)]


@pytest.fixture
def mock_config():
    """Mock dashboard configuration."""
    from config import DashboardConfig
    return DashboardConfig(
        log_collector_url="http://test:8104",
        cache_ttl=5
    )
```

---

## ✅ Test Plan Complete

**Total Tests**: 235+  
**Target Coverage**: 80%+  
**Estimated Effort**: 8-10 hours to write all tests  

**Status**: Ready for implementation

---

**Date**: October 9, 2025  
**Type**: Dashboard Testing Strategy  
**Status**: Plan Complete

