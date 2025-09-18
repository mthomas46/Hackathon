# 🏥 Automated Health Monitoring System

**Enterprise-grade automated health monitoring** for the LLM Documentation Ecosystem with real-time alerting, comprehensive reporting, and self-healing capabilities.

## 🎯 **Overview**

The Automated Health Monitoring System provides **continuous 24/7 monitoring** of all 17 services in the LLM Documentation Ecosystem, with intelligent alerting, performance tracking, and comprehensive health reporting.

### **🚀 Key Features**

- **🔄 Continuous Monitoring**: 24/7 automated health checks every 30 seconds
- **📊 Real-time Dashboards**: Live health status with historical trends
- **🚨 Intelligent Alerting**: Multi-channel notifications (Email, Slack, Webhooks)
- **📈 Performance Tracking**: Response time monitoring and uptime statistics
- **🗄️ Historical Data**: SQLite database with configurable retention
- **⚙️ Self-Healing**: Optional automatic service restart capabilities
- **🔧 Production Ready**: Systemd service with resource limits and security

---

## 🏗️ **Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Health Monitor │───▶│   Service APIs  │───▶│   Health Data   │
│    (Main App)   │    │  (17 Services)  │    │   (SQLite DB)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Alert Manager   │    │ Performance     │    │  Notification   │
│ (Rules Engine)  │    │   Tracking      │    │   Channels      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                                              │
         ▼                                              ▼
┌─────────────────┐                          ┌─────────────────┐
│   Dashboard     │                          │ Email/Slack/    │
│    Data API     │                          │   Webhooks      │
└─────────────────┘                          └─────────────────┘
```

---

## 🚀 **Quick Start**

### **1. Installation**

```bash
# Install dependencies
pip install aiohttp sqlite3 asyncio

# Make script executable
chmod +x scripts/monitoring/automated_health_monitoring.py

# Create data directory
mkdir -p data/monitoring
```

### **2. Configuration**

```bash
# Copy and customize configuration
cp config/health_monitoring_config.json config/health_monitoring_custom.json

# Edit configuration for your environment
nano config/health_monitoring_custom.json
```

### **3. Run Health Monitor**

```bash
# Run once to test
python scripts/monitoring/automated_health_monitoring.py --config config/health_monitoring_custom.json --once

# Run continuously
python scripts/monitoring/automated_health_monitoring.py --config config/health_monitoring_custom.json

# Generate health report
python scripts/monitoring/automated_health_monitoring.py --report

# Get dashboard data
python scripts/monitoring/automated_health_monitoring.py --dashboard
```

---

## ⚙️ **Configuration**

### **Core Settings**

```json
{
  "check_interval_seconds": 30,        // How often to check services
  "timeout_seconds": 10,               // HTTP timeout for health checks
  "max_consecutive_failures": 5,       // Max failures before critical alert
  "database_path": "health_monitoring.db",
  "log_level": "INFO"
}
```

### **Service Definitions**

```json
{
  "services": [
    {
      "name": "interpreter",
      "url": "http://localhost:5120/health",
      "critical": true,                 // Critical service flag
      "expected_response_time": 2.0     // Expected response time in seconds
    }
  ]
}
```

### **Alert Rules**

```json
{
  "alert_rules": [
    {
      "name": "service_down",
      "condition": "status == 'unhealthy'",
      "severity": "critical",
      "threshold": 1,
      "duration_minutes": 2,
      "enabled": true
    }
  ]
}
```

### **Notification Channels**

```json
{
  "alerting": {
    "email_notifications": {
      "enabled": true,
      "smtp_server": "smtp.gmail.com",
      "smtp_port": 587,
      "from_email": "health-monitor@company.com",
      "to_email": "devops@company.com"
    },
    "slack_notifications": {
      "enabled": true,
      "webhook_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
      "channel": "#infrastructure-alerts"
    }
  }
}
```

---

## 📊 **Monitoring Dashboard**

### **Real-time Health Status**

```bash
# Get current health status
python scripts/monitoring/automated_health_monitoring.py --dashboard | jq '.summary'

# Example output:
{
  "total_services": 17,
  "healthy_services": 16,
  "unhealthy_services": 1,
  "critical_unhealthy": 0,
  "health_percentage": 94.1
}
```

### **Service Details**

```bash
# Get detailed service status
python scripts/monitoring/automated_health_monitoring.py --report | jq '.services'

# Example output:
[
  {
    "service_name": "interpreter",
    "current_status": "healthy",
    "last_healthy": "2025-09-18T10:30:00Z",
    "consecutive_failures": 0,
    "uptime_percentage": 99.8,
    "last_updated": "2025-09-18T10:30:15Z"
  }
]
```

---

## 🚨 **Alert Management**

### **Alert Severity Levels**

- **🔴 Critical**: Service down, consecutive failures, critical service issues
- **🟡 Warning**: High response times, low uptime, performance degradation  
- **🟢 Info**: Service recovery, status changes, maintenance events

### **Alert Conditions**

| Alert Type | Condition | Severity | Description |
|------------|-----------|----------|-------------|
| `service_down` | `status == 'unhealthy'` | Critical | Service health check failed |
| `high_response_time` | `response_time > expected * 2` | Warning | Response time too high |
| `consecutive_failures` | `consecutive_failures >= 3` | Critical | Multiple consecutive failures |
| `low_uptime` | `uptime_percentage < 95.0` | Warning | Service uptime below threshold |
| `critical_service_down` | `unhealthy AND critical` | Critical | Critical service is down |
| `service_recovery` | `healthy AND was_unhealthy` | Info | Service has recovered |

### **Notification Channels**

#### **Email Notifications**
```json
{
  "email_notifications": {
    "enabled": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "from_email": "health-monitor@company.com",
    "to_email": "devops@company.com",
    "username": "health-monitor@company.com",
    "password": "app_password_here"
  }
}
```

#### **Slack Integration**
```json
{
  "slack_notifications": {
    "enabled": true,
    "webhook_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
    "channel": "#infrastructure-alerts",
    "username": "Health Monitor"
  }
}
```

#### **Webhook Notifications**
```json
{
  "webhook_notifications": {
    "enabled": true,
    "url": "https://your-webhook-endpoint.com/health-alerts",
    "headers": {
      "Authorization": "Bearer your-token",
      "Content-Type": "application/json"
    }
  }
}
```

---

## 🔧 **Production Deployment**

### **Systemd Service**

```bash
# Copy service file
sudo cp scripts/monitoring/health-monitor.service /etc/systemd/system/

# Create service user
sudo useradd -r -s /bin/false llm-ecosystem

# Set permissions
sudo chown -R llm-ecosystem:llm-ecosystem /opt/llm-ecosystem

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable health-monitor
sudo systemctl start health-monitor

# Check status
sudo systemctl status health-monitor
```

### **Service Management**

```bash
# Start health monitoring
sudo systemctl start health-monitor

# Stop health monitoring
sudo systemctl stop health-monitor

# Restart health monitoring
sudo systemctl restart health-monitor

# View logs
sudo journalctl -u health-monitor -f

# View recent logs
sudo journalctl -u health-monitor --since "1 hour ago"
```

### **Log Management**

```bash
# View real-time logs
sudo journalctl -u health-monitor -f

# Search for alerts
sudo journalctl -u health-monitor | grep "ALERT"

# View error logs
sudo journalctl -u health-monitor -p err

# Export logs
sudo journalctl -u health-monitor --since "2025-09-18" --until "2025-09-19" > health-monitor-logs.txt
```

---

## 📈 **Performance Monitoring**

### **Response Time Tracking**

The system tracks response times for all services and alerts when they exceed expected thresholds:

```bash
# View response time trends
sqlite3 health_monitoring.db "
SELECT service_name, 
       AVG(response_time) as avg_response_time,
       MAX(response_time) as max_response_time,
       COUNT(*) as checks_count
FROM health_checks 
WHERE timestamp > datetime('now', '-24 hours')
GROUP BY service_name
ORDER BY avg_response_time DESC;"
```

### **Uptime Statistics**

```bash
# Calculate uptime percentages
sqlite3 health_monitoring.db "
SELECT service_name,
       COUNT(*) as total_checks,
       SUM(CASE WHEN status = 'healthy' THEN 1 ELSE 0 END) as healthy_checks,
       ROUND(SUM(CASE WHEN status = 'healthy' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as uptime_percentage
FROM health_checks 
WHERE timestamp > datetime('now', '-7 days')
GROUP BY service_name
ORDER BY uptime_percentage ASC;"
```

### **Alert History**

```bash
# View recent alerts
sqlite3 health_monitoring.db "
SELECT service_name, alert_type, severity, message, triggered_at
FROM alerts 
WHERE triggered_at > datetime('now', '-24 hours')
ORDER BY triggered_at DESC;"
```

---

## 🛠️ **Troubleshooting**

### **Common Issues**

#### **Service Not Responding**
```bash
# Check if service is running
curl -f http://localhost:5120/health

# Check service logs
docker logs hackathon-interpreter-1

# Restart service
docker restart hackathon-interpreter-1
```

#### **Database Issues**
```bash
# Check database file
ls -la health_monitoring.db

# Backup database
cp health_monitoring.db health_monitoring_backup_$(date +%Y%m%d).db

# Reset database (WARNING: destroys all data)
rm health_monitoring.db
python scripts/monitoring/automated_health_monitoring.py --once
```

#### **High Memory Usage**
```bash
# Check memory usage
ps aux | grep automated_health_monitoring

# Reduce check frequency
# Edit config: "check_interval_seconds": 60

# Reduce database retention
sqlite3 health_monitoring.db "DELETE FROM health_checks WHERE timestamp < datetime('now', '-7 days');"
```

### **Debug Mode**

```bash
# Run with debug logging
python scripts/monitoring/automated_health_monitoring.py --config config/health_monitoring_config.json --once 2>&1 | grep -E "(ERROR|WARNING|DEBUG)"

# Test single service
curl -v http://localhost:5120/health

# Validate configuration
python -c "import json; print(json.load(open('config/health_monitoring_config.json')))"
```

---

## 📊 **Metrics and KPIs**

### **Service Level Objectives (SLOs)**

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Service Availability** | 99.9% | Monthly uptime percentage |
| **Response Time** | < 2s | 95th percentile response time |
| **Alert Response** | < 5min | Time to acknowledge critical alerts |
| **MTTR** | < 30min | Mean Time To Recovery |
| **False Positive Rate** | < 5% | Percentage of false alerts |

### **Key Performance Indicators (KPIs)**

```bash
# Overall ecosystem health
sqlite3 health_monitoring.db "
SELECT 
  ROUND(AVG(CASE WHEN current_status = 'healthy' THEN 100.0 ELSE 0.0 END), 2) as overall_health_percentage,
  COUNT(*) as total_services,
  SUM(CASE WHEN current_status = 'healthy' THEN 1 ELSE 0 END) as healthy_services
FROM service_status;"

# Critical service availability
sqlite3 health_monitoring.db "
SELECT 
  service_name,
  uptime_percentage,
  consecutive_failures,
  last_healthy
FROM service_status 
WHERE service_name IN ('interpreter', 'orchestrator', 'doc_store', 'prompt_store', 'analysis_service', 'llm_gateway')
ORDER BY uptime_percentage ASC;"
```

---

## 🔮 **Advanced Features**

### **Self-Healing Capabilities**

```json
{
  "self_healing": {
    "enabled": true,
    "restart_unhealthy_services": true,
    "max_restart_attempts": 3,
    "restart_cooldown_minutes": 5
  }
}
```

### **Custom Alert Rules**

```python
# Add custom alert rule
custom_rule = {
    "name": "memory_usage_high",
    "condition": "memory_usage > 80",
    "severity": "warning",
    "threshold": 80,
    "duration_minutes": 10,
    "enabled": True
}
```

### **Integration with External Monitoring**

```bash
# Prometheus metrics endpoint
curl http://localhost:8080/metrics

# Grafana dashboard import
# Use dashboard ID: 12345 (custom LLM ecosystem dashboard)

# DataDog integration
# Configure webhook_notifications with DataDog webhook URL
```

---

## 📞 **Support and Maintenance**

### **Monitoring the Monitor**

```bash
# Health check for the health monitor itself
ps aux | grep automated_health_monitoring
systemctl status health-monitor

# Monitor database size
du -h health_monitoring.db

# Check disk space
df -h /opt/llm-ecosystem/data
```

### **Backup and Recovery**

```bash
# Backup configuration
cp config/health_monitoring_config.json config/health_monitoring_config_backup.json

# Backup database
sqlite3 health_monitoring.db ".backup health_monitoring_backup.db"

# Restore from backup
cp health_monitoring_backup.db health_monitoring.db
systemctl restart health-monitor
```

### **Updates and Maintenance**

```bash
# Update health monitor
git pull origin main
systemctl restart health-monitor

# Database maintenance
sqlite3 health_monitoring.db "VACUUM;"
sqlite3 health_monitoring.db "ANALYZE;"

# Log rotation
sudo logrotate -f /etc/logrotate.d/health-monitor
```

---

## 🎯 **Best Practices**

### **Configuration Management**
- Use version control for configuration files
- Test configuration changes in staging environment
- Implement configuration validation
- Document all configuration changes

### **Alert Management**
- Tune alert thresholds to reduce false positives
- Implement alert escalation procedures
- Regular review of alert effectiveness
- Train team on alert response procedures

### **Performance Optimization**
- Monitor the monitor's resource usage
- Optimize database queries for large datasets
- Implement efficient alerting to avoid notification storms
- Regular cleanup of historical data

### **Security Considerations**
- Secure database file permissions
- Use encrypted communication for notifications
- Implement proper authentication for webhook endpoints
- Regular security audits of monitoring infrastructure

---

**🎯 The Automated Health Monitoring System ensures 24/7 reliability and operational excellence for the LLM Documentation Ecosystem, providing enterprise-grade monitoring with intelligent alerting and comprehensive reporting capabilities.**

**Ready to monitor your ecosystem?** 🚀🏥✨
