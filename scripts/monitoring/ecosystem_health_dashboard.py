#!/usr/bin/env python3
"""
LLM Documentation Ecosystem - Health Monitoring Dashboard

This script provides comprehensive health monitoring and dashboard capabilities
for all 17 services in the ecosystem. It includes:

- Real-time health status monitoring
- Performance metrics collection
- Service dependency mapping
- Alert generation and notification
- Historical trend analysis
- Interactive dashboard generation

Usage:
    python scripts/monitoring/ecosystem_health_dashboard.py
    python scripts/monitoring/ecosystem_health_dashboard.py --json
    python scripts/monitoring/ecosystem_health_dashboard.py --dashboard
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import argparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from rich.progress import Progress, SpinnerColumn, TextColumn
import sqlite3

console = Console()

@dataclass
class ServiceHealth:
    """Data class for service health information."""
    name: str
    port: int
    status: str
    response_time: float
    timestamp: datetime
    version: Optional[str] = None
    uptime: Optional[float] = None
    dependencies: List[str] = None
    metrics: Dict[str, Any] = None
    error_message: Optional[str] = None

@dataclass
class EcosystemHealth:
    """Data class for overall ecosystem health."""
    total_services: int
    healthy_services: int
    unhealthy_services: int
    average_response_time: float
    timestamp: datetime
    services: List[ServiceHealth]
    alerts: List[str] = None

class HealthMonitor:
    """Comprehensive health monitoring for the LLM Documentation Ecosystem."""
    
    def __init__(self):
        """Initialize the health monitor."""
        self.console = Console()
        self.db_path = "data/health_monitoring.db"
        
        # Service configuration
        self.services = {
            "frontend": {"port": 3000, "path": "/", "timeout": 10},
            "source-agent": {"port": 5000, "path": "/health", "timeout": 5},
            "analysis-service": {"port": 5020, "path": "/health", "timeout": 5},
            "memory-agent": {"port": 5040, "path": "/health", "timeout": 5},
            "discovery-agent": {"port": 5045, "path": "/health", "timeout": 5},
            "llm-gateway": {"port": 5055, "path": "/health", "timeout": 5},
            "mock-data-generator": {"port": 5065, "path": "/health", "timeout": 5},
            "secure-analyzer": {"port": 5070, "path": "/health", "timeout": 5},
            "github-mcp": {"port": 5072, "path": "/health", "timeout": 5},
            "log-collector": {"port": 5080, "path": "/health", "timeout": 5},
            "doc_store": {"port": 5087, "path": "/health", "timeout": 5},
            "notification-service": {"port": 5095, "path": "/health", "timeout": 5},
            "orchestrator": {"port": 5099, "path": "/health", "timeout": 5},
            "summarizer-hub": {"port": 5100, "path": "/health", "timeout": 5},
            "architecture-digitizer": {"port": 5105, "path": "/health", "timeout": 5},
            "prompt_store": {"port": 5110, "path": "/health", "timeout": 5},
            "interpreter": {"port": 5120, "path": "/health", "timeout": 5},
            "code-analyzer": {"port": 5130, "path": "/health", "timeout": 5},
            "bedrock-proxy": {"port": 7090, "path": "/health", "timeout": 5},
        }
        
        # Initialize database
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database for health history."""
        Path("data").mkdir(exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS health_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    response_time REAL,
                    timestamp DATETIME,
                    version TEXT,
                    uptime REAL,
                    error_message TEXT,
                    metrics TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_service_timestamp 
                ON health_history(service_name, timestamp)
            """)

    async def check_service_health(self, session: aiohttp.ClientSession, 
                                 service_name: str, config: Dict[str, Any]) -> ServiceHealth:
        """Check health of a single service."""
        start_time = time.time()
        
        try:
            url = f"http://localhost:{config['port']}{config['path']}"
            timeout = aiohttp.ClientTimeout(total=config['timeout'])
            
            async with session.get(url, timeout=timeout) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    try:
                        data = await response.json()
                        return ServiceHealth(
                            name=service_name,
                            port=config['port'],
                            status="healthy",
                            response_time=response_time,
                            timestamp=datetime.now(),
                            version=data.get('version'),
                            uptime=data.get('uptime_seconds'),
                            dependencies=data.get('dependencies', []),
                            metrics=data.get('metrics', {})
                        )
                    except json.JSONDecodeError:
                        # For services that don't return JSON (like frontend)
                        return ServiceHealth(
                            name=service_name,
                            port=config['port'],
                            status="healthy",
                            response_time=response_time,
                            timestamp=datetime.now()
                        )
                else:
                    return ServiceHealth(
                        name=service_name,
                        port=config['port'],
                        status="unhealthy",
                        response_time=response_time,
                        timestamp=datetime.now(),
                        error_message=f"HTTP {response.status}"
                    )
                    
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            return ServiceHealth(
                name=service_name,
                port=config['port'],
                status="timeout",
                response_time=response_time,
                timestamp=datetime.now(),
                error_message="Request timeout"
            )
        except Exception as e:
            response_time = time.time() - start_time
            return ServiceHealth(
                name=service_name,
                port=config['port'],
                status="error",
                response_time=response_time,
                timestamp=datetime.now(),
                error_message=str(e)
            )

    async def check_all_services(self) -> EcosystemHealth:
        """Check health of all services in the ecosystem."""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.check_service_health(session, name, config)
                for name, config in self.services.items()
            ]
            
            service_healths = await asyncio.gather(*tasks)
            
        # Calculate ecosystem metrics
        healthy_count = sum(1 for s in service_healths if s.status == "healthy")
        total_count = len(service_healths)
        avg_response_time = sum(s.response_time for s in service_healths) / total_count
        
        # Generate alerts
        alerts = self._generate_alerts(service_healths)
        
        ecosystem_health = EcosystemHealth(
            total_services=total_count,
            healthy_services=healthy_count,
            unhealthy_services=total_count - healthy_count,
            average_response_time=avg_response_time,
            timestamp=datetime.now(),
            services=service_healths,
            alerts=alerts
        )
        
        # Store in database
        self._store_health_data(service_healths)
        
        return ecosystem_health

    def _generate_alerts(self, service_healths: List[ServiceHealth]) -> List[str]:
        """Generate alerts based on service health status."""
        alerts = []
        
        for service in service_healths:
            if service.status != "healthy":
                alerts.append(f"🚨 {service.name} is {service.status}: {service.error_message}")
            elif service.response_time > 5.0:
                alerts.append(f"⚠️ {service.name} slow response: {service.response_time:.2f}s")
                
        # Ecosystem-level alerts
        healthy_percentage = (len([s for s in service_healths if s.status == "healthy"]) / 
                            len(service_healths)) * 100
        
        if healthy_percentage < 90:
            alerts.append(f"🚨 Ecosystem health below 90%: {healthy_percentage:.1f}%")
        elif healthy_percentage < 95:
            alerts.append(f"⚠️ Ecosystem health below 95%: {healthy_percentage:.1f}%")
            
        return alerts

    def _store_health_data(self, service_healths: List[ServiceHealth]):
        """Store health data in database for historical analysis."""
        with sqlite3.connect(self.db_path) as conn:
            for service in service_healths:
                conn.execute("""
                    INSERT INTO health_history 
                    (service_name, status, response_time, timestamp, version, uptime, error_message, metrics)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    service.name,
                    service.status,
                    service.response_time,
                    service.timestamp,
                    service.version,
                    service.uptime,
                    service.error_message,
                    json.dumps(service.metrics) if service.metrics else None
                ))

    def display_health_table(self, ecosystem_health: EcosystemHealth):
        """Display health status in a formatted table."""
        table = Table(title="🏥 LLM Documentation Ecosystem Health Status")
        
        table.add_column("Service", style="cyan", no_wrap=True)
        table.add_column("Port", style="blue")
        table.add_column("Status", style="green")
        table.add_column("Response Time", style="yellow")
        table.add_column("Version", style="magenta")
        table.add_column("Uptime", style="blue")
        table.add_column("Error", style="red")
        
        for service in sorted(ecosystem_health.services, key=lambda s: s.name):
            status_color = {
                "healthy": "[green]✅ Healthy[/green]",
                "unhealthy": "[red]❌ Unhealthy[/red]",
                "timeout": "[yellow]⏰ Timeout[/yellow]",
                "error": "[red]💥 Error[/red]"
            }.get(service.status, f"[gray]{service.status}[/gray]")
            
            uptime_str = f"{service.uptime:.0f}s" if service.uptime else "-"
            version_str = service.version or "-"
            error_str = service.error_message or "-"
            
            table.add_row(
                service.name,
                str(service.port),
                status_color,
                f"{service.response_time:.3f}s",
                version_str,
                uptime_str,
                error_str[:30] + "..." if len(error_str) > 30 else error_str
            )
        
        console.print(table)
        
        # Display summary
        health_percentage = (ecosystem_health.healthy_services / ecosystem_health.total_services) * 100
        summary = Panel.fit(
            f"[bold]Ecosystem Summary[/bold]\n"
            f"Total Services: {ecosystem_health.total_services}\n"
            f"Healthy: [green]{ecosystem_health.healthy_services}[/green]\n"
            f"Unhealthy: [red]{ecosystem_health.unhealthy_services}[/red]\n"
            f"Health Percentage: [{'green' if health_percentage >= 95 else 'yellow' if health_percentage >= 90 else 'red'}]{health_percentage:.1f}%[/]\n"
            f"Average Response Time: {ecosystem_health.average_response_time:.3f}s\n"
            f"Last Check: {ecosystem_health.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            title="📊 Summary"
        )
        console.print(summary)
        
        # Display alerts
        if ecosystem_health.alerts:
            alerts_panel = Panel.fit(
                "\n".join(ecosystem_health.alerts),
                title="🚨 Alerts",
                border_style="red"
            )
            console.print(alerts_panel)

    def get_historical_data(self, service_name: Optional[str] = None, 
                          hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical health data for analysis."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if service_name:
                query = """
                    SELECT * FROM health_history 
                    WHERE service_name = ? AND timestamp >= datetime('now', '-{} hours')
                    ORDER BY timestamp DESC
                """.format(hours)
                cursor = conn.execute(query, (service_name,))
            else:
                query = """
                    SELECT * FROM health_history 
                    WHERE timestamp >= datetime('now', '-{} hours')
                    ORDER BY timestamp DESC
                """.format(hours)
                cursor = conn.execute(query)
            
            return [dict(row) for row in cursor.fetchall()]

    async def continuous_monitoring(self, interval: int = 30):
        """Run continuous health monitoring with live dashboard."""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        with Live(layout, refresh_per_second=1, screen=True):
            while True:
                try:
                    ecosystem_health = await self.check_all_services()
                    
                    # Update header
                    health_percentage = (ecosystem_health.healthy_services / 
                                       ecosystem_health.total_services) * 100
                    header_color = ("green" if health_percentage >= 95 else 
                                  "yellow" if health_percentage >= 90 else "red")
                    
                    layout["header"].update(Panel.fit(
                        f"[bold]🏥 LLM Documentation Ecosystem - Live Health Monitor[/bold]\n"
                        f"[{header_color}]{ecosystem_health.healthy_services}/{ecosystem_health.total_services} Services Healthy ({health_percentage:.1f}%)[/]",
                        border_style=header_color
                    ))
                    
                    # Update main content
                    table = Table(show_header=True, header_style="bold magenta")
                    table.add_column("Service", style="cyan", width=20)
                    table.add_column("Status", width=15)
                    table.add_column("Response", width=10)
                    table.add_column("Error", width=40)
                    
                    for service in sorted(ecosystem_health.services, key=lambda s: s.name):
                        status_emoji = {
                            "healthy": "✅",
                            "unhealthy": "❌",
                            "timeout": "⏰",
                            "error": "💥"
                        }.get(service.status, "❓")
                        
                        status_text = f"{status_emoji} {service.status}"
                        response_text = f"{service.response_time:.3f}s"
                        error_text = service.error_message or ""
                        
                        table.add_row(
                            service.name,
                            status_text,
                            response_text,
                            error_text[:40] + "..." if len(error_text) > 40 else error_text
                        )
                    
                    layout["main"].update(table)
                    
                    # Update footer
                    next_check = datetime.now() + timedelta(seconds=interval)
                    footer_text = (f"Last updated: {ecosystem_health.timestamp.strftime('%H:%M:%S')} | "
                                 f"Next check: {next_check.strftime('%H:%M:%S')} | "
                                 f"Alerts: {len(ecosystem_health.alerts)}")
                    
                    layout["footer"].update(Panel.fit(footer_text, border_style="blue"))
                    
                    # Wait for next check
                    await asyncio.sleep(interval)
                    
                except KeyboardInterrupt:
                    console.print("\n[yellow]Monitoring stopped by user[/yellow]")
                    break
                except Exception as e:
                    console.print(f"[red]Error in monitoring loop: {e}[/red]")
                    await asyncio.sleep(5)

    def generate_health_report(self, output_file: str = "ecosystem_health_report.json"):
        """Generate comprehensive health report."""
        # Get current health
        ecosystem_health = asyncio.run(self.check_all_services())
        
        # Get historical data
        historical_data = self.get_historical_data(hours=24)
        
        # Calculate statistics
        stats = self._calculate_health_statistics(historical_data)
        
        report = {
            "report_generated": datetime.now().isoformat(),
            "current_status": asdict(ecosystem_health),
            "historical_statistics": stats,
            "recommendations": self._generate_recommendations(ecosystem_health, stats)
        }
        
        # Save report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        console.print(f"[green]Health report saved to {output_file}[/green]")
        return report

    def _calculate_health_statistics(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate health statistics from historical data."""
        if not historical_data:
            return {}
        
        # Group by service
        service_stats = {}
        for record in historical_data:
            service_name = record['service_name']
            if service_name not in service_stats:
                service_stats[service_name] = {
                    'total_checks': 0,
                    'healthy_checks': 0,
                    'response_times': [],
                    'uptime_percentage': 0
                }
            
            service_stats[service_name]['total_checks'] += 1
            if record['status'] == 'healthy':
                service_stats[service_name]['healthy_checks'] += 1
            
            if record['response_time']:
                service_stats[service_name]['response_times'].append(record['response_time'])
        
        # Calculate percentages and averages
        for service_name, stats in service_stats.items():
            stats['uptime_percentage'] = (stats['healthy_checks'] / stats['total_checks']) * 100
            if stats['response_times']:
                stats['avg_response_time'] = sum(stats['response_times']) / len(stats['response_times'])
                stats['max_response_time'] = max(stats['response_times'])
                stats['min_response_time'] = min(stats['response_times'])
        
        return service_stats

    def _generate_recommendations(self, ecosystem_health: EcosystemHealth, 
                                stats: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on health analysis."""
        recommendations = []
        
        # Check for consistently unhealthy services
        for service in ecosystem_health.services:
            if service.status != "healthy":
                recommendations.append(
                    f"🔧 Investigate {service.name}: {service.error_message}"
                )
        
        # Check for slow services
        slow_services = [s for s in ecosystem_health.services if s.response_time > 2.0]
        if slow_services:
            recommendations.append(
                f"⚡ Optimize performance for slow services: {', '.join(s.name for s in slow_services)}"
            )
        
        # Check historical uptime
        for service_name, stat in stats.items():
            if stat.get('uptime_percentage', 100) < 95:
                recommendations.append(
                    f"📊 {service_name} has low uptime ({stat['uptime_percentage']:.1f}%) - investigate reliability"
                )
        
        # Ecosystem-level recommendations
        health_percentage = (ecosystem_health.healthy_services / ecosystem_health.total_services) * 100
        if health_percentage < 90:
            recommendations.append("🚨 Critical: Ecosystem health below 90% - immediate action required")
        
        return recommendations

async def main():
    """Main function to run health monitoring."""
    parser = argparse.ArgumentParser(description="LLM Ecosystem Health Monitor")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    parser.add_argument("--dashboard", action="store_true", help="Run live dashboard")
    parser.add_argument("--report", action="store_true", help="Generate health report")
    parser.add_argument("--interval", type=int, default=30, help="Monitoring interval (seconds)")
    
    args = parser.parse_args()
    
    monitor = HealthMonitor()
    
    if args.dashboard:
        console.print("[blue]Starting live health monitoring dashboard...[/blue]")
        await monitor.continuous_monitoring(interval=args.interval)
    elif args.report:
        console.print("[blue]Generating comprehensive health report...[/blue]")
        monitor.generate_health_report()
    else:
        console.print("[blue]Checking ecosystem health...[/blue]")
        ecosystem_health = await monitor.check_all_services()
        
        if args.json:
            print(json.dumps(asdict(ecosystem_health), indent=2, default=str))
        else:
            monitor.display_health_table(ecosystem_health)

if __name__ == "__main__":
    asyncio.run(main())
