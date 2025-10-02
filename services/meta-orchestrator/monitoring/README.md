# Meta-Orchestrator Monitoring System

Comprehensive monitoring, auditing, and analytics system for the Meta-Orchestration Service, providing real-time visibility into service health, configuration drift, and system performance.

## 📋 Overview

The monitoring system is the intelligence layer of the Meta-Orchestrator, continuously tracking service health, detecting configuration drift, and providing actionable insights for system maintenance and optimization.

## 📁 Structure

```
monitoring/
├── __init__.py                    # Monitoring package initialization
├── service.py                     # Main monitoring service orchestration
├── config_manager.py              # Configuration management operations
├── config_validator.py            # Configuration validation logic
├── drift_detector.py              # Configuration drift detection
│
├── alerts/                        # Alert management system
│   └── manager.py
│
├── analytics/                     # Analytics and reporting
│   └── analyzer.py
│
├── audit/                         # Audit and compliance modules
│   ├── config_drift_detector.py   # Configuration drift detection
│   ├── config_standardizer.py     # Configuration standardization
│   ├── docker_compose_validator.py # Docker Compose validation
│   └── docker_standardizer.py     # Docker configuration standardization
│
├── database/                      # Monitoring data persistence
│   ├── manager.py                 # Database operations
│   └── models.py                  # Data models
│
└── health/                        # Health monitoring
    └── checker.py                 # Service health checks
```

## 🔧 Core Components

### Monitoring Service (`service.py`)

The central orchestrator for all monitoring activities:

```python
class MonitoringService:
    """Main monitoring service coordinating all monitoring components"""

    def __init__(self, orchestrator: MetaOrchestrator, db_path: str):
        self.orchestrator = orchestrator
        self.db_manager = DatabaseManager(db_path)

        # Initialize monitoring components
        self.health_checker = HealthChecker(self.db_manager)
        self.drift_detector = ConfigurationDriftDetector(self.db_manager, orchestrator)
        self.alert_manager = AlertManager(self.db_manager)
        self.analytics = DriftAnalytics(self.db_manager)
        self.config_validator = ConfigurationValidator(self.db_manager, orchestrator)
        self.config_manager = ServiceConfigManager(self.db_manager, orchestrator)

        # Initialize audit validators
        self.docker_compose_validator = DockerComposeValidator(orchestrator.settings.workspace_path)
        self.audit_drift_detector = AuditDriftDetector(orchestrator.settings.workspace_path)
        self.production_readiness_validator = ProductionReadinessValidator(orchestrator.settings.workspace_path)
        self.config_standardizer = ConfigurationStandardizer(orchestrator.settings.workspace_path)
        self.docker_standardizer = UnifiedDockerStandardizer(orchestrator.settings.workspace_path)
```

### Health Checker (`health/checker.py`)

Monitors the health of all services in the ecosystem:

```python
class HealthChecker:
    """Service health monitoring and status tracking"""

    async def check_all_services_health(self) -> Dict[str, HealthResult]:
        """Check health of all configured services"""
        results = {}

        for service_name, config in self.health_configs.items():
            result = await self._perform_health_check(config)
            results[service_name] = result

            # Store result in database
            await self.db_manager.store_health_result(service_name, result)

        return results

    async def _perform_health_check(self, config: HealthCheckConfig) -> HealthResult:
        """Perform individual health check"""
        start_time = time.time()

        try:
            # HTTP health check
            async with httpx.AsyncClient(timeout=config.timeout) as client:
                response = await client.get(config.health_endpoint)

                response_time = time.time() - start_time
                is_healthy = response.status_code == 200

                return HealthResult(
                    service_name=config.service_name,
                    healthy=is_healthy,
                    response_time=response_time,
                    status_code=response.status_code,
                    error=None if is_healthy else f"HTTP {response.status_code}"
                )

        except Exception as e:
            return HealthResult(
                service_name=config.service_name,
                healthy=False,
                response_time=time.time() - start_time,
                status_code=None,
                error=str(e)
            )
```

### Configuration Drift Detector (`audit/config_drift_detector.py`)

Detects configuration drift between different sources:

```python
class ConfigurationDriftDetector:
    """Detect configuration drift across Docker, YAML, and Pydantic configs"""

    def detect_all_drift(self, dev_only: bool = True) -> DriftDetectionResult:
        """Comprehensive drift detection across all configuration sources"""

        # Scan configuration files
        config_files = self.scan_configurations()

        # Get running containers
        containers = self.get_running_containers()

        # Parse docker-compose configurations
        compose_services = self.parse_docker_compose()

        # Detect drift between sources
        drift_issues = []

        # Docker vs Compose drift
        docker_compose_drift = self.detect_docker_vs_compose_drift(containers, compose_services)
        drift_issues.extend(docker_compose_drift)

        # Docker vs Pydantic drift
        docker_pydantic_drift = self.detect_docker_vs_pydantic_drift(containers, config_files)
        drift_issues.extend(docker_pydantic_drift)

        # Compose vs Pydantic drift
        compose_pydantic_drift = self.detect_compose_vs_pydantic_drift(compose_services, config_files)
        drift_issues.extend(compose_pydantic_drift)

        return DriftDetectionResult(
            success=True,
            total_issues=len(drift_issues),
            issues=drift_issues,
            scanned_files=len(config_files),
            scanned_containers=len(containers)
        )
```

## 📊 Data Collection & Storage

### Database Models (`database/models.py`)

Structured data models for monitoring data:

```python
@dataclass
class ServiceHealth:
    """Service health check result"""
    id: Optional[int] = None
    service_name: str = ""
    health_status: str = ""  # "healthy", "unhealthy", "degraded"
    response_time: Optional[float] = None
    endpoint: str = ""
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ConfigurationDrift:
    """Configuration drift detection result"""
    id: Optional[int] = None
    service_name: str = ""
    drift_type: str = ""  # "environment", "ports", "volumes", etc.
    severity: str = ""  # "low", "medium", "high", "critical"
    description: str = ""
    field_path: str = ""
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class AuditLog:
    """Audit log entry for all operations"""
    id: Optional[int] = None
    operation: str = ""
    service_name: Optional[str] = None
    user: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_data: Optional[str] = None
    response_data: Optional[str] = None
    status_code: Optional[int] = None
    duration: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
```

### Database Manager (`database/manager.py`)

Handles all database operations for monitoring data:

```python
class DatabaseManager:
    """Database operations for monitoring data"""

    def __init__(self, db_path: str = "/tmp/monitoring.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        """Create all monitoring tables"""
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS service_health (
                id INTEGER PRIMARY KEY,
                service_name TEXT NOT NULL,
                health_status TEXT NOT NULL,
                response_time REAL,
                endpoint TEXT,
                error_message TEXT,
                timestamp REAL NOT NULL
            )
        ''')

        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS configuration_drift (
                id INTEGER PRIMARY KEY,
                service_name TEXT NOT NULL,
                drift_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT,
                field_path TEXT,
                old_value TEXT,
                new_value TEXT,
                timestamp REAL NOT NULL,
                resolved BOOLEAN DEFAULT FALSE
            )
        ''')

    async def store_health_result(self, service_name: str, result: HealthResult):
        """Store health check result"""
        self.conn.execute('''
            INSERT INTO service_health
            (service_name, health_status, response_time, endpoint, error_message, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            service_name,
            "healthy" if result.healthy else "unhealthy",
            result.response_time,
            result.endpoint,
            result.error,
            result.timestamp.timestamp()
        ))
        self.conn.commit()
```

## 🚨 Alert Management

### Alert Manager (`alerts/manager.py`)

Handles alert generation, escalation, and notification:

```python
class AlertManager:
    """Alert management and notification system"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.active_alerts = {}

    async def create_health_alert(self, service_name: str, consecutive_failures: int) -> Optional[Alert]:
        """Create alert for service health issues"""
        if consecutive_failures >= 3:
            alert = Alert(
                alert_type="health_failure",
                severity="high",
                service_name=service_name,
                title=f"Service {service_name} health check failed",
                message=f"{service_name} has failed {consecutive_failures} consecutive health checks"
            )

            await self.store_alert(alert)
            return alert

        return None

    async def create_drift_alert(self, service_name: str, drift_count: int, time_window: int) -> Optional[Alert]:
        """Create alert for excessive configuration drift"""
        if drift_count >= 5:
            alert = Alert(
                alert_type="configuration_drift",
                severity="medium",
                service_name=service_name,
                title=f"High configuration drift in {service_name}",
                message=f"{service_name} has {drift_count} configuration changes in {time_window} hours"
            )

            await self.store_alert(alert)
            return alert

        return None

    async def send_alert(self, alert: Alert):
        """Send alert notification"""
        # Email notification
        await self.send_email_alert(alert)

        # Slack notification
        await self.send_slack_alert(alert)

        # Webhook notification
        await self.send_webhook_alert(alert)
```

## 📈 Analytics & Reporting

### Analytics Engine (`analytics/analyzer.py`)

Provides insights and analytics from monitoring data:

```python
class DriftAnalytics:
    """Analytics and insights from monitoring data"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def get_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive analytics report"""
        # Service health analytics
        health_stats = await self.analyze_health_trends()

        # Configuration drift patterns
        drift_patterns = await self.analyze_drift_patterns()

        # Performance metrics
        performance_metrics = await self.calculate_performance_metrics()

        # Risk assessment
        risk_level = self.assess_system_risk(health_stats, drift_patterns)

        # Generate recommendations
        recommendations = self.generate_recommendations(
            health_stats, drift_patterns, performance_metrics
        )

        return {
            "time_range": "7d",
            "overall_health_score": health_stats.get("average_health_percentage", 0),
            "risk_level": risk_level,
            "total_services": len(health_stats.get("services", [])),
            "healthy_services": health_stats.get("healthy_count", 0),
            "drift_events": drift_patterns.get("total_events", 0),
            "mtbf_hours": performance_metrics.get("mtbf_hours", 0),
            "mttr_minutes": performance_metrics.get("mttr_minutes", 0),
            "recommendations": recommendations
        }

    async def analyze_health_trends(self) -> Dict[str, Any]:
        """Analyze service health trends"""
        # Query health data from last 7 days
        health_data = await self.db_manager.get_health_history(days=7)

        # Calculate health percentages
        health_percentages = {}
        for service_name in health_data:
            checks = health_data[service_name]
            healthy_checks = sum(1 for check in checks if check.healthy)
            total_checks = len(checks)
            health_percentages[service_name] = (healthy_checks / total_checks) * 100 if total_checks > 0 else 0

        average_health = sum(health_percentages.values()) / len(health_percentages) if health_percentages else 0

        return {
            "services": health_percentages,
            "average_health_percentage": average_health,
            "healthy_count": sum(1 for pct in health_percentages.values() if pct >= 95),
            "degraded_count": sum(1 for pct in health_percentages.values() if 80 <= pct < 95),
            "unhealthy_count": sum(1 for pct in health_percentages.values() if pct < 80)
        }
```

## 🔧 Configuration Management

### Configuration Manager (`config_manager.py`)

Manages service configurations and provides configuration operations:

```python
class ServiceConfigManager:
    """Service configuration management"""

    async def sync_all_service_configs(self) -> Dict[str, Any]:
        """Sync configurations from all running services"""
        results = {
            "services_synced": 0,
            "configs_updated": 0,
            "new_configs": 0,
            "errors": 0,
            "sync_duration": 0,
            "results": {"successful": [], "failed": [], "skipped": []}
        }

        start_time = time.time()

        # Get all services
        services = await self.orchestrator.get_service_status()

        for service in services:
            try:
                # Fetch config from service endpoint
                config_data = await self.fetch_service_config(service.name)

                if config_data:
                    # Store in database
                    await self.store_service_config(service.name, config_data)

                    # Check for configuration drift
                    drift_issues = await self.detect_config_drift(service.name, config_data)

                    if drift_issues:
                        results["configs_updated"] += 1
                    else:
                        results["new_configs"] += 1

                    results["results"]["successful"].append(service.name)
                    results["services_synced"] += 1
                else:
                    results["results"]["skipped"].append(service.name)

            except Exception as e:
                logger.error(f"Failed to sync config for {service.name}: {e}")
                results["errors"] += 1
                results["results"]["failed"].append(service.name)

        results["sync_duration"] = time.time() - start_time
        return results

    async def fetch_service_config(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Fetch configuration from service endpoint"""
        try:
            # Get service details to find config endpoint
            service_info = await self.orchestrator.get_service_info(service_name)

            if not service_info or not service_info.config_endpoint:
                return None

            # Fetch configuration
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(service_info.config_endpoint)

                if response.status_code == 200:
                    return response.json()

        except Exception as e:
            logger.error(f"Failed to fetch config for {service_name}: {e}")

        return None
```

## 🔍 Audit & Compliance

### Audit Validators

The audit system provides comprehensive validation and compliance checking:

#### Docker Compose Validator (`audit/docker_compose_validator.py`)
Validates Docker Compose configurations for startup and runtime issues.

#### Configuration Drift Detector (`audit/config_drift_detector.py`)
Advanced drift detection with schema validation and automated corrections.

#### Production Readiness Validator (`audit/production_readiness.py`)
Comprehensive production readiness assessment with detailed checklists.

#### Configuration Standardizer (`audit/config_standardizer.py`)
Automated configuration standardization and best practice enforcement.

#### Docker Standardizer (`audit/docker_standardizer.py`)
Docker configuration standardization and optimization.

## 📊 Monitoring Dashboards

### Health Dashboard
- Real-time service health status
- Response time trends
- Error rate monitoring
- Uptime statistics

### Configuration Dashboard
- Drift detection alerts
- Configuration change history
- Compliance status
- Standardization progress

### Performance Dashboard
- API response times
- Database query performance
- Resource utilization
- Error tracking

## 🔄 Background Processing

The monitoring system runs continuous background tasks:

```python
class MonitoringService:
    async def start_monitoring(self):
        """Start background monitoring tasks"""
        self.monitoring_task = asyncio.create_task(
            self._run_monitoring_loop(
                drift_interval=300,      # 5 minutes
                health_interval=60,      # 1 minute
                analytics_interval=3600  # 1 hour
            )
        )

    async def _run_monitoring_loop(self, drift_interval, health_interval, analytics_interval):
        """Main monitoring loop"""
        while self.is_running:
            current_time = datetime.utcnow().timestamp()

            # Health checks
            if current_time >= self.next_health_check:
                await self._perform_health_checks()
                self.next_health_check = current_time + health_interval

            # Drift detection
            if current_time >= self.next_drift_check:
                await self._perform_drift_detection()
                self.next_drift_check = current_time + drift_interval

            # Analytics
            if current_time >= self.next_analytics_run:
                await self._perform_analytics()
                self.next_analytics_run = current_time + analytics_interval

            await asyncio.sleep(10)  # Check every 10 seconds
```

## 🚨 Alert Configuration

### Alert Types
- **Health Alerts**: Service health failures and degradations
- **Configuration Alerts**: Drift detection and configuration issues
- **Performance Alerts**: Response time and resource usage warnings
- **Security Alerts**: Authentication and authorization issues

### Escalation Policies
- **Low**: Email notification only
- **Medium**: Email + Slack notification
- **High**: Email + Slack + SMS
- **Critical**: All channels + on-call engineer notification

## 📈 Metrics & KPIs

### Service Health Metrics
- Service availability percentage
- Mean time between failures (MTBF)
- Mean time to recovery (MTTR)
- Health check response times

### Configuration Metrics
- Drift detection frequency
- Configuration change velocity
- Standardization compliance rate
- Backup success rate

### Performance Metrics
- API response times (p50, p95, p99)
- Database query performance
- Resource utilization trends
- Error rates by service

This monitoring system provides comprehensive visibility and control over the Meta-Orchestrator ecosystem, enabling proactive management and rapid issue resolution.
