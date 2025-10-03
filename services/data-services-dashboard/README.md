# Datastore Operations Dashboard

A comprehensive, real-time monitoring dashboard for visualizing datastore operations across the entire ecosystem. Built with Streamlit and integrated with the log-collector service for centralized observability.

## 🎯 Features

### 📊 Overview Tab
- **Service Health**: Visual breakdown of operations by service
- **Operation Types**: Distribution of CREATE, READ, UPDATE, DELETE, SEARCH operations
- **Recent Activity Timeline**: Real-time scatter plot of operations with duration and status

### ⏱️ Performance Tab
- **Response Time Trends**: Line charts showing performance over time by service
- **Duration Distribution**: Histogram of operation response times
- **Duration by Operation**: Box plots comparing different operation types
- **Performance Statistics**: Detailed stats table (min, max, mean, median, std dev)

### 🔍 Operations Tab
- **Detailed Operation Log**: Searchable, filterable table of all operations
- **Filters**: By operation type, success status, time range
- **Export**: Download operations data as CSV
- **Pagination**: Configurable number of entries to display

### 🌊 Workflows Tab
- **Workflow Tracking**: Trace operations across services by workflow ID
- **Service Flow Visualization**: Timeline showing which services were called
- **Workflow Metrics**: Total operations, services touched, success rate, duration
- **Call Timeline**: Interactive Gantt chart of service call flow

### ⚠️ Errors Tab
- **Error Distribution**: Visual breakdown of errors by service and status code
- **Error Details**: Detailed table of failed operations
- **Alerting**: Visual indicators for error rates and anomalies

## 🚀 Quick Start

### Prerequisites

```bash
# Ensure log-collector is running
python3 check_services.py

# Install dependencies
pip install -r services/data-services-dashboard/requirements.txt
```

### Start Dashboard

```bash
# From project root
streamlit run services/data-services-dashboard/app.py

# Or use the helper script
./services/data-services-dashboard/run_dashboard.sh
```

The dashboard will open in your browser at `http://localhost:8501`

## 🔧 Configuration

### Log Collector URL

Edit `app.py` to change the log-collector URL:

```python
LOG_COLLECTOR_URL = "http://localhost:8104"  # Default
```

### Default Services

Modify the list of tracked services:

```python
DEFAULT_SERVICES = [
    "doc_store",
    "prompt_store",
    "external-service-store",
    "memory-agent"
]
```

### Auto-Refresh

Adjust the auto-refresh interval in the sidebar:
- 0 seconds: Manual refresh only
- 5, 10, 30, 60 seconds: Automatic refresh

## 📊 Metrics Tracked

| Metric | Description |
|--------|-------------|
| **Total Operations** | Count of completed operations |
| **Successful Operations** | Operations with status code < 400 |
| **Failed Operations** | Operations with status code >= 400 |
| **Average Duration** | Mean operation duration in milliseconds |
| **Error Rate** | Percentage of failed operations |

## 🎨 Dashboard Tabs

### 1. Overview
Get a high-level view of system activity:
- Operations per service (pie chart)
- Operation type distribution (bar chart)
- Recent activity timeline (scatter plot)

### 2. Performance
Deep-dive into performance metrics:
- Response time trends over time
- Duration distribution histograms
- Box plots by operation type
- Statistical analysis table

### 3. Operations
Detailed operation log with:
- Timestamp, service, operation, method, path
- Duration, status code, success indicator
- Workflow ID for traceability
- CSV export functionality

### 4. Workflows
End-to-end request tracing:
- Group operations by workflow ID
- Visualize service call flow
- Calculate total workflow duration
- Identify service dependencies

### 5. Errors
Error analysis and alerting:
- Error count by service
- Status code distribution
- Detailed error log with messages
- Visual indicators for error rates

## 🧪 Usage Examples

### Monitoring a Specific Service

1. Select service from sidebar dropdown
2. View service-specific metrics
3. Analyze performance trends
4. Investigate errors

### Tracing a Workflow

1. Go to **Workflows** tab
2. Select workflow ID from dropdown
3. View timeline of service calls
4. Analyze total duration and success rate

### Performance Analysis

1. Go to **Performance** tab
2. Identify slow operations
3. Compare services
4. Export data for further analysis

### Error Investigation

1. Go to **Errors** tab
2. Identify services with high error rates
3. Review error details and status codes
4. Correlate with performance metrics

## 🔍 Data Source

The dashboard connects to the **log-collector** service at `http://localhost:8104/logs`.

All datastore services automatically log operations via the `DataStoreOperationMiddleware`:
- **doc_store** (port 5087)
- **prompt_store** (port 5110)
- **external-service-store** (port 5140)
- **memory-agent** (port 5090)

## 📈 Visualization Libraries

- **Streamlit**: Interactive web dashboard
- **Plotly**: Interactive charts (line, bar, pie, scatter, timeline)
- **Pandas**: Data processing and aggregation
- **Streamlit-autorefresh**: Auto-refresh functionality

## 🛠️ Development

### Running in Development Mode

```bash
streamlit run services/data-services-dashboard/app.py --server.runOnSave true
```

### Adding New Visualizations

1. Create a new tab in the main dashboard
2. Fetch data using `fetch_logs()`
3. Process with pandas
4. Visualize with plotly
5. Add interactivity with streamlit widgets

### Customizing Metrics

Modify `calculate_metrics()` function to add new aggregate metrics.

### Extending Filters

Add new filter controls in the sidebar and apply them in the respective tab functions.

## 🐛 Troubleshooting

### Dashboard shows "No data available"

**Solution:**
1. Ensure log-collector is running: `python3 check_services.py`
2. Verify datastore services have the middleware integrated
3. Make test requests to generate logs
4. Check log-collector URL configuration

### Auto-refresh not working

**Solution:**
1. Ensure `streamlit-autorefresh` is installed
2. Check browser console for errors
3. Try manual refresh first

### Performance issues with large datasets

**Solution:**
1. Reduce the time range (e.g., "Last 100 operations")
2. Use service filters to narrow down data
3. Increase cache TTL in `@st.cache_data(ttl=5)`

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Dashboard                       │
│  (http://localhost:8501)                                    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  │ HTTP GET /logs
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              Log Collector Service                           │
│  (http://localhost:8104)                                    │
└─────────────────┬───────────────────────────────────────────┘
                  │
        ┌─────────┼─────────┬─────────┐
        │         │         │         │
        ▼         ▼         ▼         ▼
   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
   │  doc_  │ │prompt_ │ │external│ │memory- │
   │ store  │ │ store  │ │service │ │ agent  │
   │        │ │        │ │ store  │ │        │
   └────────┘ └────────┘ └────────┘ └────────┘
    Middleware  Middleware Middleware Middleware
```

## 🎯 Key Benefits

1. **Real-time Monitoring**: See operations as they happen
2. **Performance Insights**: Identify slow operations and bottlenecks
3. **Error Detection**: Quickly spot and diagnose issues
4. **Workflow Tracing**: Track requests across multiple services
5. **Historical Analysis**: Review trends and patterns over time
6. **Export Capabilities**: Download data for offline analysis

## 📝 Notes

- Dashboard uses client-side caching (5-second TTL) for performance
- All timestamps are in server timezone
- Workflow IDs are truncated to 12 characters for display
- Duration is measured in milliseconds
- Success/failure is based on HTTP status codes (< 400 = success)

## 🔗 Related Documentation

- [DataStore Operation Tracking Infrastructure](../../DATASTORE_OPERATION_TRACKING_REPORT.md)
- [Service Startup Guide](../../SERVICE_STARTUP_GUIDE.md)
- [Log Collector Service](../log-collector/README.md)

---

**Version:** 1.0.0  
**Last Updated:** October 3, 2025  
**Maintainer:** Development Team

