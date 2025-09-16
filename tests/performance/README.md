# Prompt Store Performance Testing

This directory contains comprehensive performance testing and benchmarking tools for the prompt_store service.

## Overview

The performance testing suite includes:
- **Unit Performance Tests**: Benchmark individual functions and operations
- **API Performance Tests**: HTTP endpoint response time and throughput testing
- **Load Testing**: Concurrent user simulation and stress testing
- **Benchmarking Script**: Standalone performance analysis tool

## Test Categories

### 🔬 Unit Performance Tests (`test_prompt_store_performance.py`)
- Individual function benchmarking using pytest-benchmark
- Memory usage profiling during operations
- Database query performance analysis
- Algorithm complexity validation

**Run unit performance tests:**
```bash
pytest tests/performance/test_prompt_store_performance.py -k "performance" --benchmark-only -v
```

### 🌐 API Performance Tests (`test_api_performance.py`)
- HTTP endpoint response time benchmarking
- Concurrent API call load testing
- Throughput and latency analysis
- Memory usage during API operations

**Run API performance tests:**
```bash
# Requires prompt_store service running on localhost:5110
pytest tests/performance/test_api_performance.py -k "performance" -v
```

### 📊 Load Testing
- Concurrent user simulation
- Stress testing under high load
- Error rate monitoring
- Resource usage analysis

**Run load tests:**
```bash
pytest tests/performance/test_api_performance.py -k "load_test" -v
```

### 🏃 Standalone Benchmarking (`benchmark_prompt_store.py`)

Comprehensive benchmarking script with multiple test modes:

#### Quick Benchmark
```bash
python scripts/benchmark_prompt_store.py --quick
```
- Health endpoint performance (50 requests)
- Basic prompt operations (20 iterations)
- Fast, basic performance metrics

#### Full Benchmark
```bash
python scripts/benchmark_prompt_store.py --full
```
- Comprehensive health checks (200 requests)
- Full prompt operations (100 iterations)
- Load testing (20 concurrent users, 30 seconds)
- Detailed performance analysis

#### Load Testing
```bash
python scripts/benchmark_prompt_store.py --load-test
```
- Multiple concurrency levels (5, 10, 20, 50 users)
- Sustained load testing (30 seconds each)
- Throughput and scalability analysis

#### Options
```bash
python scripts/benchmark_prompt_store.py --help
```

## Performance Metrics

### Response Time Metrics
- **Mean**: Average response time
- **Median (P50)**: 50th percentile response time
- **P95**: 95th percentile (critical for performance)
- **P99**: 99th percentile (worst-case performance)
- **Min/Max**: Response time range

### Throughput Metrics
- **Requests per Second (RPS)**: Overall system throughput
- **Concurrent Users**: Simultaneous user capacity
- **Success Rate**: Percentage of successful requests

### Resource Metrics
- **Memory Usage**: RAM consumption during operations
- **CPU Usage**: Processor utilization
- **Error Rate**: Failed request percentage

## Performance Targets

### Health Endpoint
- **Response Time**: < 100ms (P95)
- **Throughput**: > 50 RPS
- **Success Rate**: > 99.9%

### Prompt Operations
- **Create**: < 500ms (P95)
- **Read**: < 200ms (P95)
- **Update**: < 300ms (P95)

### Load Testing
- **Concurrent Users**: > 20 simultaneous users
- **Throughput**: > 100 RPS sustained
- **Memory Growth**: < 50MB under load

## Benchmark Results

Results are automatically saved to JSON files with timestamps:
```
benchmark_results_1703123456.json
```

Example result structure:
```json
{
  "timestamp": 1703123456,
  "results": {
    "health": {
      "mean": 0.023,
      "p95": 0.045,
      "requests_per_second": 43.2
    },
    "load_test": {
      "concurrent_users": 20,
      "requests_per_second": 185.3,
      "p95": 0.234
    }
  }
}
```

## Prerequisites

### pytest-benchmark
```bash
pip install pytest-benchmark
```

### aiohttp (for API testing)
```bash
pip install aiohttp
```

### matplotlib (optional, for charts)
```bash
pip install matplotlib numpy
```

### Service Running
For API and load tests, ensure prompt_store service is running:
```bash
python run_promptstore.py
```

## Best Practices

### Running Benchmarks
1. **Isolate Testing**: Run benchmarks on dedicated hardware
2. **Warm-up Period**: Allow system to stabilize before measurements
3. **Multiple Runs**: Run benchmarks multiple times for consistency
4. **Baseline Comparison**: Compare against previous benchmark results

### Interpreting Results
1. **Focus on P95/P99**: These represent typical user experience
2. **Monitor Trends**: Track performance changes over time
3. **Identify Bottlenecks**: Use profiling to find performance issues
4. **Set Realistic Targets**: Base targets on actual user requirements

### Performance Regression Detection
- Compare benchmark results against baseline
- Set up automated performance testing in CI/CD
- Alert on significant performance degradation
- Profile code changes that impact performance

## Troubleshooting

### Common Issues

**Service Not Running**
```
Error: Prompt store service is not running
```
**Solution**: Start the service with `python run_promptstore.py`

**High Memory Usage**
- Check for memory leaks in application code
- Monitor garbage collection behavior
- Review object caching strategies

**Slow Response Times**
- Profile database queries
- Check network latency
- Review async/await usage
- Monitor CPU and memory usage

**Low Throughput**
- Check database connection pooling
- Review caching strategies
- Monitor system resources
- Check for blocking operations

## Contributing

When adding new performance tests:
1. Follow existing naming conventions
2. Include appropriate performance targets
3. Add documentation for new metrics
4. Update this README with new test descriptions
5. Ensure tests can run in CI/CD environment
