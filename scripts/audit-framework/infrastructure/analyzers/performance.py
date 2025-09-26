"""
Performance Analyzer
Handles performance assessments including resource usage, system metrics, and database performance
"""

import os
import time
import psutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Handle imports for both module and script execution
try:
    from ..config import AuditProfile, get_thresholds_for_profile
    from domain.entities.service_info import ServiceInfo
except ImportError:
    import sys
    from pathlib import Path
    current_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(current_dir))

    from config import AuditProfile
    from config.thresholds import get_thresholds_for_profile

    # Create a simple ServiceInfo if models doesn't exist
    from dataclasses import dataclass
    from pathlib import Path
    from typing import Dict, Any

    @dataclass
    class ServiceInfo:
        name: str
        path: Path
        type: str = "python"
        status: str = "unknown"
        metadata: Dict[str, Any] = None

        def __post_init__(self):
            if self.metadata is None:
                self.metadata = {}


@dataclass
class PerformanceAnalysisResult:
    """Results from performance analysis"""
    score: float
    system_metrics_score: float
    database_score: float
    resource_usage_score: float
    system_metrics: Dict[str, Any]
    database_performance: Dict[str, Any]
    resource_usage: Dict[str, Any]
    performance_indicators: Dict[str, Any]
    issues: List[str]
    recommendations: List[str]


class PerformanceAnalyzer:
    """Analyzer for performance metrics and system resource usage"""

    def __init__(self, profile: AuditProfile):
        self.profile = profile
        self.thresholds = get_thresholds_for_profile(profile)

    async def analyze(self, service: ServiceInfo) -> PerformanceAnalysisResult:
        """Perform complete performance analysis"""
        # Collect system metrics during analysis
        system_metrics = await self._collect_system_metrics()

        scores = {
            'system_metrics': await self._analyze_system_performance(system_metrics),
            'database': await self._check_database_performance(service),
            'resources': await self._check_resource_usage(service),
            'runtime': await self._check_runtime_performance(service)
        }

        # Calculate weighted performance score
        system_weight = 0.35
        database_weight = 0.25
        resources_weight = 0.25
        runtime_weight = 0.15

        performance_score = (
            scores['system_metrics'] * system_weight +
            scores['database'] * database_weight +
            scores['resources'] * resources_weight +
            scores['runtime'] * runtime_weight
        )

        return PerformanceAnalysisResult(
            score=round(performance_score, 2),
            system_metrics_score=scores['system_metrics'],
            database_score=scores['database'],
            resource_usage_score=scores['resources'],
            system_metrics=system_metrics or {},
            database_performance=await self._analyze_database_performance(service),
            resource_usage=await self._analyze_resource_usage(service),
            performance_indicators=self._calculate_performance_indicators(system_metrics or {}),
            issues=self._identify_issues(scores),
            recommendations=self._generate_recommendations(scores)
        )

    async def _analyze_system_performance(self, system_metrics: Optional[Dict[str, Any]]) -> float:
        """Analyze system performance metrics"""
        if not system_metrics:
            return 50.0  # Neutral score when metrics unavailable

        score = 100.0

        # Check CPU usage
        cpu_percent = system_metrics.get('cpu_percent', 0)
        if cpu_percent > self.thresholds['performance']['max_cpu_usage_percent']:
            penalty = (cpu_percent - self.thresholds['performance']['max_cpu_usage_percent']) * 2
            score -= min(30, penalty)

        # Check memory usage
        memory_percent = system_metrics.get('memory_percent', 0)
        if memory_percent > self.thresholds['performance']['max_memory_usage_mb']:
            # Convert memory percent to a comparable scale
            memory_penalty = min(20, memory_percent / 5)
            score -= memory_penalty

        # Check disk I/O
        disk_read = system_metrics.get('disk_read_mb', 0)
        disk_write = system_metrics.get('disk_write_mb', 0)
        total_disk_io = disk_read + disk_write

        # Penalize excessive disk I/O (more than 100MB total)
        if total_disk_io > 100:
            disk_penalty = min(15, (total_disk_io - 100) / 10)
            score -= disk_penalty

        # Check network I/O
        network_sent = system_metrics.get('network_sent_mb', 0)
        network_received = system_metrics.get('network_received_mb', 0)
        total_network = network_sent + network_received

        # Penalize excessive network usage (more than 50MB total)
        if total_network > 50:
            network_penalty = min(10, (total_network - 50) / 5)
            score -= network_penalty

        return max(0, min(100, score))

    async def _check_database_performance(self, service: ServiceInfo) -> float:
        """Check database performance indicators"""
        score = 100.0

        # Check for database-related files
        db_files = (list(service.path.glob("**/db/**/*.py")) +
                   list(service.path.glob("**/database/**/*.py")) +
                   list(service.path.glob("**/repositories/**/*.py")))

        if db_files:
            score += 20  # Bonus for having database layer

            # Analyze database-related code for performance issues
            connection_issues = 0
            query_issues = 0
            caching_issues = 0

            for db_file in db_files[:10]:  # Analyze first 10 files
                try:
                    with open(db_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Check for connection pooling
                    if 'connection' in content.lower() and 'pool' not in content.lower():
                        connection_issues += 1

                    # Check for N+1 query patterns (simplified)
                    if 'select' in content.lower() and 'join' not in content.lower():
                        query_issues += 1

                    # Check for caching
                    if 'cache' not in content.lower() and 'redis' not in content.lower():
                        caching_issues += 1

                except Exception:
                    continue

            # Apply penalties
            score -= min(15, connection_issues * 2)
            score -= min(15, query_issues * 1.5)
            score -= min(10, caching_issues * 1)

        else:
            score = 70.0  # Neutral score for services without database layer

        return max(0, min(100, score))

    async def _check_resource_usage(self, service: ServiceInfo) -> float:
        """Check resource usage patterns in code"""
        score = 100.0

        # Analyze Python files for resource management issues
        resource_issues = 0
        memory_leaks = 0
        file_handles = 0

        for root, dirs, files in os.walk(str(service.path)):
            for file in files:
                if file.endswith('.py') and not file.startswith('test_'):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Check for proper resource management
                        if ('open(' in content or 'file(' in content) and 'close()' not in content:
                            file_handles += 1

                        # Check for potential memory leaks
                        if 'global ' in content and 'del ' not in content:
                            memory_leaks += 1

                        # Check for proper exception handling in resource usage
                        if ('with ' not in content and ('open(' in content or 'connect(' in content)):
                            resource_issues += 1

                    except Exception:
                        continue

        # Apply penalties
        score -= min(20, file_handles * 3)
        score -= min(15, memory_leaks * 2)
        score -= min(25, resource_issues * 2)

        # Bonus for good resource management
        if file_handles == 0 and memory_leaks == 0 and resource_issues == 0:
            score += 10

        return max(0, min(100, score))

    async def _check_runtime_performance(self, service: ServiceInfo) -> float:
        """Check runtime performance indicators and patterns"""
        score = 100.0

        try:
            python_files = list(service.path.rglob("*.py"))

            # Analyze code for performance anti-patterns
            performance_issues = 0
            max_files = min(10, len(python_files))

            for file_path in python_files[:max_files]:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Check for inefficient operations
                    inefficient_patterns = [
                        r'for\s+\w+\s+in\s+range\(len\(',  # Iterating over range(len())
                        r'\.append\(.*for.*in.*\)',       # List comprehensions that could be generators
                        r'list\(.*range\(.*\)\)',         # Creating unnecessary lists
                        r'\.sort\(\)',                     # In-place sort when sorted() might be better
                    ]

                    for pattern in inefficient_patterns:
                        if re.search(pattern, content):
                            performance_issues += 1

                    # Check for blocking operations that could be async
                    if not file_path.name.startswith('test_'):
                        blocking_patterns = [
                            'requests.',       # Synchronous HTTP requests
                            'time.sleep',      # Blocking sleep
                            'input(',          # Blocking input
                        ]

                        for pattern in blocking_patterns:
                            if pattern in content:
                                performance_issues += 1

                    # Check for large data structures in memory
                    if 'list(' in content and 'range(' in content and '10000' in content:
                        performance_issues += 2  # Major penalty for large in-memory lists

                except Exception:
                    continue

            # Apply penalties
            score -= min(40, performance_issues * 3)

            # Bonus for good performance patterns
            async_usage = 0
            for file_path in python_files[:max_files]:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'async def' in content or 'await ' in content:
                            async_usage += 1
                except Exception:
                    continue

            if async_usage > 0:
                score += min(15, async_usage * 2)

        except Exception:
            score = 70.0  # Neutral score on error

        return max(0, min(100, score))

    async def _collect_system_metrics(self) -> Optional[Dict[str, Any]]:
        """Collect real-time system performance metrics"""
        try:
            if not self.profile.enable_system_metrics:
                return None

            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024**3)

            # Disk I/O metrics
            disk_io = psutil.disk_io_counters()
            if disk_io:
                disk_read_mb = disk_io.read_bytes / (1024**2)
                disk_write_mb = disk_io.write_bytes / (1024**2)
            else:
                disk_read_mb = disk_write_mb = 0

            # Network I/O metrics
            network_io = psutil.net_io_counters()
            if network_io:
                network_sent_mb = network_io.bytes_sent / (1024**2)
                network_recv_mb = network_io.bytes_recv / (1024**2)
            else:
                network_sent_mb = network_recv_mb = 0

            # Process information
            process = psutil.Process()
            process_memory_percent = process.memory_percent()
            process_cpu_percent = process.cpu_percent(interval=0.1)

            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'memory_used_gb': memory_used_gb,
                'disk_read_mb': disk_read_mb,
                'disk_write_mb': disk_write_mb,
                'network_sent_mb': network_sent_mb,
                'network_recv_mb': network_recv_mb,
                'process_memory_percent': process_memory_percent,
                'process_cpu_percent': process_cpu_percent,
                'timestamp': time.time()
            }

        except ImportError:
            # psutil not available
            return None
        except Exception:
            # Any other error in metrics collection
            return None

    async def _analyze_database_performance(self, service: ServiceInfo) -> Dict[str, Any]:
        """Analyze database performance patterns"""
        db_analysis = {
            'has_database_layer': False,
            'connection_pooling': False,
            'query_optimization': False,
            'caching_strategy': False,
            'migration_scripts': False,
            'performance_issues': [],
            'recommendations': []
        }

        # Check for database-related files
        db_indicators = [
            '**/repositories/**/*.py',
            '**/db/**/*.py',
            '**/database/**/*.py',
            '**/models/**/*.py'
        ]

        db_files = []
        for pattern in db_indicators:
            db_files.extend(list(service.path.glob(pattern)))

        if db_files:
            db_analysis['has_database_layer'] = True

            # Analyze database patterns
            for db_file in db_files[:20]:  # Analyze first 20 files
                try:
                    with open(db_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Check for connection pooling
                    if any(term in content.lower() for term in ['pool', 'connection_pool', 'engine']):
                        db_analysis['connection_pooling'] = True

                    # Check for query optimization
                    if any(term in content.lower() for term in ['select_related', 'prefetch', 'join', 'index']):
                        db_analysis['query_optimization'] = True

                    # Check for caching
                    if any(term in content.lower() for term in ['cache', 'redis', 'memcache']):
                        db_analysis['caching_strategy'] = True

                except Exception:
                    continue

            # Check for migrations
            migration_files = list(service.path.glob("**/migrations/**/*.py"))
            if migration_files:
                db_analysis['migration_scripts'] = True

            # Generate recommendations
            if not db_analysis['connection_pooling']:
                db_analysis['performance_issues'].append("Missing connection pooling")
                db_analysis['recommendations'].append("Implement database connection pooling")

            if not db_analysis['query_optimization']:
                db_analysis['performance_issues'].append("Limited query optimization")
                db_analysis['recommendations'].append("Add database indexes and optimize queries")

            if not db_analysis['caching_strategy']:
                db_analysis['performance_issues'].append("No caching strategy")
                db_analysis['recommendations'].append("Implement caching layer for frequently accessed data")

        return db_analysis

    async def _analyze_resource_usage(self, service: ServiceInfo) -> Dict[str, Any]:
        """Analyze resource usage patterns in the codebase"""
        resource_analysis = {
            'file_handle_leaks': 0,
            'memory_leaks_potential': 0,
            'resource_management_issues': 0,
            'context_manager_usage': 0,
            'exception_handling_resources': 0,
            'large_objects': [],
            'resource_intensive_operations': [],
            'recommendations': []
        }

        for root, dirs, files in os.walk(str(service.path)):
            for file in files:
                if file.endswith('.py') and not file.startswith('test_'):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            lines = content.split('\n')

                        # Check file size
                        if len(lines) > 500:
                            resource_analysis['large_objects'].append(str(file_path.relative_to(service.path)))

                        # Analyze resource usage patterns
                        for i, line in enumerate(lines):
                            line_lower = line.lower()

                            # File handle management
                            if ('open(' in line_lower or 'file(' in line_lower) and 'close()' not in line_lower:
                                # Check if it's in a with statement or has close() nearby
                                in_context_manager = False
                                has_close = False

                                # Check surrounding lines for context manager or close
                                for j in range(max(0, i-5), min(len(lines), i+5)):
                                    context_line = lines[j].lower()
                                    if 'with ' in context_line and ('open(' in context_line or 'file(' in context_line):
                                        in_context_manager = True
                                    if 'close()' in context_line or '.close()' in context_line:
                                        has_close = True

                                if not in_context_manager and not has_close:
                                    resource_analysis['file_handle_leaks'] += 1

                            # Memory leak potential
                            if 'global ' in line_lower and not any('del ' in next_lines.lower()
                                                                 for next_lines in lines[i:i+10]):
                                resource_analysis['memory_leaks_potential'] += 1

                            # Context manager usage
                            if 'with ' in line_lower:
                                resource_analysis['context_manager_usage'] += 1

                            # Resource-intensive operations
                            if any(op in line_lower for op in ['sort(', 'sorted(', 'sum(', 'max(', 'min(']):
                                resource_analysis['resource_intensive_operations'].append(f"{file}:{i+1}")

                    except Exception:
                        continue

        # Generate recommendations
        if resource_analysis['file_handle_leaks'] > 0:
            resource_analysis['recommendations'].append(
                f"Fix {resource_analysis['file_handle_leaks']} potential file handle leaks - use context managers"
            )

        if resource_analysis['memory_leaks_potential'] > 0:
            resource_analysis['recommendations'].append(
                f"Review {resource_analysis['memory_leaks_potential']} potential memory leaks with global variables"
            )

        if len(resource_analysis['large_objects']) > 0:
            resource_analysis['recommendations'].append(
                f"Consider splitting {len(resource_analysis['large_objects'])} large files for better resource management"
            )

        return resource_analysis

    def _calculate_performance_indicators(self, system_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance health indicators"""
        indicators = {
            'cpu_health': 'unknown',
            'memory_health': 'unknown',
            'disk_health': 'unknown',
            'network_health': 'unknown',
            'overall_performance': 'unknown'
        }

        if not system_metrics:
            return indicators

        # CPU health
        cpu_percent = system_metrics.get('cpu_percent', 0)
        if cpu_percent < 50:
            indicators['cpu_health'] = 'good'
        elif cpu_percent < 80:
            indicators['cpu_health'] = 'moderate'
        else:
            indicators['cpu_health'] = 'high'

        # Memory health
        memory_percent = system_metrics.get('memory_percent', 0)
        if memory_percent < 60:
            indicators['memory_health'] = 'good'
        elif memory_percent < 85:
            indicators['memory_health'] = 'moderate'
        else:
            indicators['memory_health'] = 'high'

        # Disk health (based on I/O)
        disk_io = system_metrics.get('disk_read_mb', 0) + system_metrics.get('disk_write_mb', 0)
        if disk_io < 50:
            indicators['disk_health'] = 'good'
        elif disk_io < 200:
            indicators['disk_health'] = 'moderate'
        else:
            indicators['disk_health'] = 'high'

        # Network health
        network_io = system_metrics.get('network_sent_mb', 0) + system_metrics.get('network_recv_mb', 0)
        if network_io < 20:
            indicators['network_health'] = 'good'
        elif network_io < 100:
            indicators['network_health'] = 'moderate'
        else:
            indicators['network_health'] = 'high'

        # Overall performance
        health_scores = {
            'good': 3,
            'moderate': 2,
            'high': 1,
            'unknown': 0
        }

        total_score = sum(health_scores.get(indicators[key], 0)
                         for key in ['cpu_health', 'memory_health', 'disk_health', 'network_health'])

        if total_score >= 10:
            indicators['overall_performance'] = 'good'
        elif total_score >= 6:
            indicators['overall_performance'] = 'moderate'
        else:
            indicators['overall_performance'] = 'poor'

        return indicators

    def _identify_issues(self, scores: Dict[str, float]) -> List[str]:
        """Identify performance issues"""
        issues = []
        if scores.get('system_metrics', 0) < 70:
            issues.append("High system resource usage detected")
        if scores.get('database', 0) < 70:
            issues.append("Database performance issues identified")
        if scores.get('resources', 0) < 70:
            issues.append("Resource management issues in code")
        return issues

    def _generate_recommendations(self, scores: Dict[str, float]) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        if scores.get('system_metrics', 0) < 80:
            recommendations.append("Optimize system resource usage - monitor CPU, memory, and I/O")
        if scores.get('database', 0) < 80:
            recommendations.append("Improve database performance - add connection pooling and query optimization")
        if scores.get('resources', 0) < 80:
            recommendations.append("Fix resource management issues - use context managers and proper cleanup")
        return recommendations
