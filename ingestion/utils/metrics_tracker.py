"""
Comprehensive metrics tracking for demo execution.

Tracks:
- Runtime metrics (execution time, memory usage)
- Usability metrics (success rate, errors)
- Service interactions (requests, responses, timing)
- MCP lifecycle metrics (creation, training, queries)
- Resource utilization (CPU, memory, disk)
"""
import time
import psutil
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import json


@dataclass
class ServiceInteraction:
    """Record of a single service interaction."""
    service: str
    endpoint: str
    method: str
    timestamp: float
    duration_ms: float
    status_code: int
    success: bool
    error: Optional[str] = None
    request_size: int = 0
    response_size: int = 0


@dataclass
class MCPLifecycleMetrics:
    """Metrics for MCP creation, training, and usage."""
    mcp_id: str
    
    # Provisioning
    provisioning_start: float
    provisioning_end: Optional[float] = None
    provisioning_duration_s: Optional[float] = None
    
    # Training
    training_start: Optional[float] = None
    training_end: Optional[float] = None
    training_duration_s: Optional[float] = None
    documents_ingested: int = 0
    
    # Container
    container_id: Optional[str] = None
    container_image: Optional[str] = None
    container_size_mb: Optional[float] = None
    
    # Storage
    storage_location: Optional[str] = None
    mcp_size_mb: Optional[float] = None
    
    # Performance
    query_times_ms: List[float] = field(default_factory=list)
    avg_query_time_ms: Optional[float] = None
    p95_query_time_ms: Optional[float] = None
    p99_query_time_ms: Optional[float] = None
    
    # Resources
    peak_cpu_percent: Optional[float] = None
    peak_memory_mb: Optional[float] = None


@dataclass
class RuntimeMetrics:
    """Overall runtime and resource metrics."""
    start_time: float
    end_time: Optional[float] = None
    total_duration_s: Optional[float] = None
    
    # Phase timings
    phase_timings: Dict[str, float] = field(default_factory=dict)
    
    # Resource usage
    initial_memory_mb: float = 0
    peak_memory_mb: float = 0
    avg_cpu_percent: float = 0
    peak_cpu_percent: float = 0
    
    # Disk I/O
    disk_read_mb: float = 0
    disk_write_mb: float = 0


@dataclass
class UsabilityMetrics:
    """User-facing metrics about success and quality."""
    documents_crawled: int = 0
    documents_ingested: int = 0
    documents_generated: int = 0
    documents_target: int = 12
    
    success_rate: float = 0.0
    errors_count: int = 0
    warnings_count: int = 0
    
    service_health: Dict[str, bool] = field(default_factory=dict)


class MetricsTracker:
    """Comprehensive metrics tracking for demo execution."""
    
    def __init__(self):
        self.runtime = RuntimeMetrics(start_time=time.time())
        self.usability = UsabilityMetrics()
        self.mcp_lifecycle: Optional[MCPLifecycleMetrics] = None
        self.service_interactions: List[ServiceInteraction] = []
        
        self.process = psutil.Process()
        self.runtime.initial_memory_mb = self.process.memory_info().rss / (1024 * 1024)
        
        # For calculating averages
        self._cpu_samples: List[float] = []
        self._current_phase: Optional[str] = None
        self._phase_start: Optional[float] = None
    
    def start_phase(self, phase_name: str):
        """Start tracking a new phase."""
        if self._current_phase and self._phase_start:
            # Complete previous phase
            duration = time.time() - self._phase_start
            self.runtime.phase_timings[self._current_phase] = duration
        
        self._current_phase = phase_name
        self._phase_start = time.time()
    
    def end_phase(self):
        """End current phase tracking."""
        if self._current_phase and self._phase_start:
            duration = time.time() - self._phase_start
            self.runtime.phase_timings[self._current_phase] = duration
            self._current_phase = None
            self._phase_start = None
    
    def track_service_interaction(
        self,
        service: str,
        endpoint: str,
        method: str,
        duration_ms: float,
        status_code: int,
        success: bool,
        error: Optional[str] = None,
        request_size: int = 0,
        response_size: int = 0
    ):
        """Record a service interaction."""
        interaction = ServiceInteraction(
            service=service,
            endpoint=endpoint,
            method=method,
            timestamp=time.time(),
            duration_ms=duration_ms,
            status_code=status_code,
            success=success,
            error=error,
            request_size=request_size,
            response_size=response_size
        )
        self.service_interactions.append(interaction)
    
    def start_mcp_provisioning(self, mcp_id: str):
        """Start tracking MCP provisioning."""
        self.mcp_lifecycle = MCPLifecycleMetrics(
            mcp_id=mcp_id,
            provisioning_start=time.time()
        )
    
    def end_mcp_provisioning(self):
        """End MCP provisioning tracking."""
        if self.mcp_lifecycle:
            self.mcp_lifecycle.provisioning_end = time.time()
            self.mcp_lifecycle.provisioning_duration_s = (
                self.mcp_lifecycle.provisioning_end - 
                self.mcp_lifecycle.provisioning_start
            )
    
    def start_mcp_training(self):
        """Start tracking MCP training."""
        if self.mcp_lifecycle:
            self.mcp_lifecycle.training_start = time.time()
    
    def end_mcp_training(self, documents_ingested: int):
        """End MCP training tracking."""
        if self.mcp_lifecycle:
            self.mcp_lifecycle.training_end = time.time()
            self.mcp_lifecycle.training_duration_s = (
                self.mcp_lifecycle.training_end - 
                self.mcp_lifecycle.training_start
            )
            self.mcp_lifecycle.documents_ingested = documents_ingested
    
    def track_query_time(self, duration_ms: float):
        """Track MCP query performance."""
        if self.mcp_lifecycle:
            self.mcp_lifecycle.query_times_ms.append(duration_ms)
    
    def update_resource_metrics(self):
        """Update current resource usage metrics."""
        # Memory
        current_memory_mb = self.process.memory_info().rss / (1024 * 1024)
        self.runtime.peak_memory_mb = max(self.runtime.peak_memory_mb, current_memory_mb)
        
        # CPU
        cpu_percent = self.process.cpu_percent(interval=0.1)
        self._cpu_samples.append(cpu_percent)
        self.runtime.peak_cpu_percent = max(self.runtime.peak_cpu_percent, cpu_percent)
        
        # MCP-specific
        if self.mcp_lifecycle:
            self.mcp_lifecycle.peak_cpu_percent = self.runtime.peak_cpu_percent
            self.mcp_lifecycle.peak_memory_mb = self.runtime.peak_memory_mb
    
    def finalize(self):
        """Finalize all metrics at end of execution."""
        self.runtime.end_time = time.time()
        self.runtime.total_duration_s = self.runtime.end_time - self.runtime.start_time
        
        # Calculate averages
        if self._cpu_samples:
            self.runtime.avg_cpu_percent = sum(self._cpu_samples) / len(self._cpu_samples)
        
        # Calculate success rate
        if self.usability.documents_target > 0:
            self.usability.success_rate = (
                self.usability.documents_generated / self.usability.documents_target
            )
        
        # Calculate MCP query statistics
        if self.mcp_lifecycle and self.mcp_lifecycle.query_times_ms:
            sorted_times = sorted(self.mcp_lifecycle.query_times_ms)
            self.mcp_lifecycle.avg_query_time_ms = (
                sum(sorted_times) / len(sorted_times)
            )
            
            # Calculate percentiles
            p95_idx = int(len(sorted_times) * 0.95)
            p99_idx = int(len(sorted_times) * 0.99)
            self.mcp_lifecycle.p95_query_time_ms = sorted_times[p95_idx] if p95_idx < len(sorted_times) else sorted_times[-1]
            self.mcp_lifecycle.p99_query_time_ms = sorted_times[p99_idx] if p99_idx < len(sorted_times) else sorted_times[-1]
    
    def generate_service_interaction_report(self) -> Dict[str, Any]:
        """Generate service interaction report."""
        # Group by service
        by_service: Dict[str, List[ServiceInteraction]] = {}
        for interaction in self.service_interactions:
            if interaction.service not in by_service:
                by_service[interaction.service] = []
            by_service[interaction.service].append(interaction)
        
        # Calculate statistics per service
        service_stats = {}
        for service, interactions in by_service.items():
            successful = [i for i in interactions if i.success]
            failed = [i for i in interactions if not i.success]
            
            service_stats[service] = {
                "total_requests": len(interactions),
                "successful": len(successful),
                "failed": len(failed),
                "success_rate": len(successful) / len(interactions) if interactions else 0,
                "avg_duration_ms": sum(i.duration_ms for i in interactions) / len(interactions) if interactions else 0,
                "total_request_size": sum(i.request_size for i in interactions),
                "total_response_size": sum(i.response_size for i in interactions),
                "endpoints": list(set(i.endpoint for i in interactions))
            }
        
        return {
            "total_interactions": len(self.service_interactions),
            "by_service": service_stats,
            "timeline": [asdict(i) for i in self.service_interactions]
        }
    
    def generate_mcp_training_report(self) -> Optional[Dict[str, Any]]:
        """Generate comprehensive MCP training and performance report."""
        if not self.mcp_lifecycle:
            return None
        
        # Calculate scalability estimates
        scalability = self._calculate_scalability_estimates()
        
        return {
            "mcp_id": self.mcp_lifecycle.mcp_id,
            "provisioning": {
                "duration_s": self.mcp_lifecycle.provisioning_duration_s,
                "container_id": self.mcp_lifecycle.container_id,
                "container_image": self.mcp_lifecycle.container_image,
                "container_size_mb": self.mcp_lifecycle.container_size_mb
            },
            "training": {
                "duration_s": self.mcp_lifecycle.training_duration_s,
                "documents_ingested": self.mcp_lifecycle.documents_ingested,
                "avg_time_per_doc_ms": (
                    (self.mcp_lifecycle.training_duration_s * 1000) / 
                    self.mcp_lifecycle.documents_ingested
                ) if self.mcp_lifecycle.documents_ingested > 0 else None
            },
            "storage": {
                "location": self.mcp_lifecycle.storage_location,
                "mcp_size_mb": self.mcp_lifecycle.mcp_size_mb
            },
            "performance": {
                "total_queries": len(self.mcp_lifecycle.query_times_ms),
                "avg_query_time_ms": self.mcp_lifecycle.avg_query_time_ms,
                "p95_query_time_ms": self.mcp_lifecycle.p95_query_time_ms,
                "p99_query_time_ms": self.mcp_lifecycle.p99_query_time_ms,
                "queries_per_second": (
                    1000 / self.mcp_lifecycle.avg_query_time_ms
                ) if self.mcp_lifecycle.avg_query_time_ms else None
            },
            "resources": {
                "peak_cpu_percent": self.mcp_lifecycle.peak_cpu_percent,
                "peak_memory_mb": self.mcp_lifecycle.peak_memory_mb
            },
            "scalability": scalability
        }
    
    def _calculate_scalability_estimates(self) -> Dict[str, Any]:
        """Calculate scalability estimates based on measured performance."""
        if not self.mcp_lifecycle:
            return {}
        
        # Assumptions for scalability calculations
        available_ram_gb = psutil.virtual_memory().total / (1024**3)
        available_cpus = psutil.cpu_count()
        
        # Estimate concurrent MCPs
        memory_per_mcp_mb = self.mcp_lifecycle.peak_memory_mb or 512
        mcps_per_ram = int((available_ram_gb * 1024 * 0.8) / memory_per_mcp_mb)  # 80% utilization
        
        # Estimate query throughput
        qps_per_mcp = (
            1000 / self.mcp_lifecycle.avg_query_time_ms
        ) if self.mcp_lifecycle.avg_query_time_ms else 10
        
        total_qps = mcps_per_ram * qps_per_mcp
        
        return {
            "infrastructure": {
                "available_ram_gb": round(available_ram_gb, 2),
                "available_cpus": available_cpus
            },
            "mcp_capacity": {
                "memory_per_mcp_mb": round(memory_per_mcp_mb, 2),
                "concurrent_mcps_estimate": mcps_per_ram,
                "total_mcp_capacity_gb": round((mcps_per_ram * memory_per_mcp_mb) / 1024, 2)
            },
            "throughput_estimates": {
                "qps_per_mcp": round(qps_per_mcp, 2),
                "total_qps_capacity": round(total_qps, 2),
                "daily_query_capacity": int(total_qps * 86400)
            },
            "training_capacity": {
                "docs_per_hour": int(
                    (3600 / (self.mcp_lifecycle.training_duration_s or 1)) * 
                    (self.mcp_lifecycle.documents_ingested or 1)
                )
            }
        }
    
    def export_to_json(self, output_path: Path):
        """Export all metrics to JSON file."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "runtime": asdict(self.runtime),
            "usability": asdict(self.usability),
            "mcp_training": self.generate_mcp_training_report(),
            "service_interactions": self.generate_service_interaction_report()
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
    
    def export_to_markdown(self, output_path: Path):
        """Export metrics to human-readable markdown report."""
        lines = []
        
        lines.append("# Demo Execution Metrics Report\n")
        lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Runtime Metrics
        lines.append("## Runtime Metrics\n")
        lines.append(f"- **Total Duration**: {self.runtime.total_duration_s:.2f}s\n")
        lines.append(f"- **Peak Memory**: {self.runtime.peak_memory_mb:.2f} MB\n")
        lines.append(f"- **Average CPU**: {self.runtime.avg_cpu_percent:.1f}%\n")
        lines.append(f"- **Peak CPU**: {self.runtime.peak_cpu_percent:.1f}%\n\n")
        
        # Phase Timings
        if self.runtime.phase_timings:
            lines.append("### Phase Timings\n")
            for phase, duration in self.runtime.phase_timings.items():
                lines.append(f"- **{phase}**: {duration:.2f}s\n")
            lines.append("\n")
        
        # Usability Metrics
        lines.append("## Usability Metrics\n")
        lines.append(f"- **Documents Crawled**: {self.usability.documents_crawled}\n")
        lines.append(f"- **Documents Ingested**: {self.usability.documents_ingested}\n")
        lines.append(f"- **Documents Generated**: {self.usability.documents_generated}/{self.usability.documents_target}\n")
        lines.append(f"- **Success Rate**: {self.usability.success_rate * 100:.1f}%\n")
        lines.append(f"- **Errors**: {self.usability.errors_count}\n")
        lines.append(f"- **Warnings**: {self.usability.warnings_count}\n\n")
        
        # MCP Training Report
        if self.mcp_lifecycle:
            lines.append("## MCP Training Report\n")
            mcp_report = self.generate_mcp_training_report()
            
            lines.append(f"### Provisioning\n")
            lines.append(f"- **MCP ID**: {self.mcp_lifecycle.mcp_id}\n")
            lines.append(f"- **Duration**: {mcp_report['provisioning']['duration_s']:.2f}s\n")
            lines.append(f"- **Container**: {mcp_report['provisioning']['container_id'] or 'N/A'}\n\n")
            
            lines.append(f"### Training\n")
            lines.append(f"- **Duration**: {mcp_report['training']['duration_s'] or 0:.2f}s\n")
            lines.append(f"- **Documents**: {mcp_report['training']['documents_ingested']}\n")
            lines.append(f"- **Avg Time/Doc**: {mcp_report['training']['avg_time_per_doc_ms'] or 0:.2f}ms\n\n")
            
            if mcp_report['performance']['total_queries'] > 0:
                lines.append(f"### Performance\n")
                lines.append(f"- **Total Queries**: {mcp_report['performance']['total_queries']}\n")
                lines.append(f"- **Avg Query Time**: {mcp_report['performance']['avg_query_time_ms']:.2f}ms\n")
                lines.append(f"- **P95 Query Time**: {mcp_report['performance']['p95_query_time_ms']:.2f}ms\n")
                lines.append(f"- **P99 Query Time**: {mcp_report['performance']['p99_query_time_ms']:.2f}ms\n")
                lines.append(f"- **QPS Capacity**: {mcp_report['performance']['queries_per_second']:.2f}\n\n")
            
            lines.append(f"### Scalability Estimates\n")
            scalability = mcp_report['scalability']
            lines.append(f"- **Concurrent MCPs**: {scalability['mcp_capacity']['concurrent_mcps_estimate']}\n")
            lines.append(f"- **Total QPS**: {scalability['throughput_estimates']['total_qps_capacity']:.2f}\n")
            lines.append(f"- **Daily Capacity**: {scalability['throughput_estimates']['daily_query_capacity']:,} queries\n\n")
        
        # Service Interactions
        interaction_report = self.generate_service_interaction_report()
        lines.append("## Service Interactions\n")
        lines.append(f"- **Total Requests**: {interaction_report['total_interactions']}\n\n")
        
        for service, stats in interaction_report['by_service'].items():
            lines.append(f"### {service}\n")
            lines.append(f"- **Requests**: {stats['total_requests']}\n")
            lines.append(f"- **Success Rate**: {stats['success_rate'] * 100:.1f}%\n")
            lines.append(f"- **Avg Duration**: {stats['avg_duration_ms']:.2f}ms\n")
            lines.append(f"- **Endpoints**: {', '.join(stats['endpoints'])}\n\n")
        
        with open(output_path, 'w') as f:
            f.writelines(lines)

