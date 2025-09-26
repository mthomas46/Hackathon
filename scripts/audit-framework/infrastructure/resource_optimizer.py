"""
Resource Optimizer for Audit Framework

Automatically optimizes parallel processing and batch sizes based on system resources
and workload characteristics.
"""

import os
import psutil
import asyncio
from typing import Dict, Any, List, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ResourceOptimizer:
    """Optimizes audit processing based on system resources and workload."""
    
    def __init__(self):
        self.system_info = self._detect_system_resources()
        self.optimization_profile = self._create_optimization_profile()
    
    def _detect_system_resources(self) -> Dict[str, Any]:
        """Detect available system resources."""
        try:
            # CPU information
            cpu_count = os.cpu_count() or 1
            cpu_logical = psutil.cpu_count(logical=True) or cpu_count
            cpu_physical = psutil.cpu_count(logical=False) or cpu_count
            
            # Memory information
            memory = psutil.virtual_memory()
            total_memory_gb = memory.total / (1024**3)
            available_memory_gb = memory.available / (1024**3)
            
            # Disk information
            disk = psutil.disk_usage('/')
            total_disk_gb = disk.total / (1024**3)
            free_disk_gb = disk.free / (1024**3)
            
            # System load
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0)
            
            return {
                'cpu': {
                    'physical_cores': cpu_physical,
                    'logical_cores': cpu_logical,
                    'total_cores': cpu_count,
                    'load_avg': load_avg
                },
                'memory': {
                    'total_gb': total_memory_gb,
                    'available_gb': available_memory_gb,
                    'usage_percent': memory.percent
                },
                'disk': {
                    'total_gb': total_disk_gb,
                    'free_gb': free_disk_gb,
                    'usage_percent': disk.percent
                },
                'system_load': load_avg[0] if load_avg else 0
            }
        except Exception as e:
            logger.warning(f"Failed to detect system resources: {e}")
            # Fallback to conservative defaults
            return {
                'cpu': {'physical_cores': 2, 'logical_cores': 4, 'total_cores': 4, 'load_avg': (1.0, 1.0, 1.0)},
                'memory': {'total_gb': 8, 'available_gb': 4, 'usage_percent': 50},
                'disk': {'total_gb': 100, 'free_gb': 50, 'usage_percent': 50},
                'system_load': 1.0
            }
    
    def _create_optimization_profile(self) -> Dict[str, Any]:
        """Create optimization profile based on detected resources."""
        resources = self.system_info
        
        # Base calculations
        cpu_cores = resources['cpu']['physical_cores']
        memory_gb = resources['memory']['available_gb']
        system_load = resources['system_load']
        
        # Adjust for system load (higher load = fewer resources)
        load_factor = min(1.0, max(0.3, 1.0 - (system_load / cpu_cores)))
        
        # Memory-based parallel workers
        # Conservative: 1 worker per 2GB available memory
        memory_based_workers = max(1, int(memory_gb / 2))
        
        # CPU-based parallel workers
        # Conservative: use 75% of available cores, adjusted for hyperthreading
        cpu_based_workers = max(1, int(cpu_cores * 0.75))
        
        # Take the minimum of CPU and memory constraints
        optimal_parallel_workers = min(cpu_based_workers, memory_based_workers)
        
        # Apply load factor
        optimal_parallel_workers = max(1, int(optimal_parallel_workers * load_factor))
        
        # Batch size calculations
        # Base batch size depends on available memory
        base_batch_size = max(5, int(memory_gb * 2))  # 2 files per GB
        
        # Adjust batch size based on CPU cores
        cpu_batch_multiplier = min(2.0, cpu_cores / 4.0)  # Scale up for more cores
        optimal_batch_size = max(5, int(base_batch_size * cpu_batch_multiplier * load_factor))
        
        # Memory limits for file processing
        memory_per_file_mb = 50  # Conservative estimate
        max_files_in_memory = int((memory_gb * 1024) / memory_per_file_mb)
        
        return {
            'parallel_workers': optimal_parallel_workers,
            'batch_size': optimal_batch_size,
            'max_files_in_memory': max_files_in_memory,
            'memory_per_file_mb': memory_per_file_mb,
            'load_factor': load_factor,
            'recommendations': self._generate_recommendations(resources)
        }
    
    def _generate_recommendations(self, resources: Dict[str, Any]) -> List[str]:
        """Generate resource optimization recommendations."""
        recommendations = []
        
        cpu_cores = resources['cpu']['physical_cores']
        memory_gb = resources['memory']['available_gb']
        load = resources['system_load']
        
        if cpu_cores < 4:
            recommendations.append("⚠️ Limited CPU cores detected - consider sequential processing for large codebases")
        
        if memory_gb < 4:
            recommendations.append("⚠️ Limited memory detected - reduce batch sizes and parallel workers")
        
        if load > cpu_cores * 0.8:
            recommendations.append("⚠️ High system load detected - reduce parallel processing intensity")
        
        if memory_gb > 16 and cpu_cores > 8:
            recommendations.append("✅ High-performance system detected - optimal for parallel processing")
        
        return recommendations
    
    async def analyze_workload(self, service_path: Path, full_audit: bool = False) -> Dict[str, Any]:
        """Analyze the workload characteristics for optimization."""
        try:
            # Count Python files
            python_files = []
            total_size_bytes = 0
            
            for root, dirs, files in os.walk(service_path):
                for file in files:
                    if file.endswith('.py') and not file.startswith('.') and not file.startswith('test_'):
                        file_path = Path(root) / file
                        try:
                            stat = file_path.stat()
                            file_size = stat.st_size
                            total_size_bytes += file_size
                            
                            # Categorize files by size
                            if file_size < 1024:  # < 1KB
                                size_category = 'tiny'
                            elif file_size < 10240:  # < 10KB
                                size_category = 'small'
                            elif file_size < 102400:  # < 100KB
                                size_category = 'medium'
                            elif file_size < 1048576:  # < 1MB
                                size_category = 'large'
                            else:
                                size_category = 'huge'
                            
                            python_files.append({
                                'path': file_path,
                                'size_bytes': file_size,
                                'size_kb': file_size / 1024,
                                'size_mb': file_size / (1024 * 1024),
                                'size_category': size_category
                            })
                            
                        except OSError:
                            continue
            
            # Analyze file size distribution
            size_categories = {}
            for file_info in python_files:
                category = file_info['size_category']
                size_categories[category] = size_categories.get(category, 0) + 1
            
            # Calculate workload metrics
            total_files = len(python_files)
            total_size_mb = total_size_bytes / (1024 * 1024)
            avg_file_size_kb = (total_size_bytes / max(1, total_files)) / 1024
            
            # Estimate processing requirements
            large_files = sum(1 for f in python_files if f['size_category'] in ['large', 'huge'])
            estimated_memory_mb = total_files * 10  # Conservative estimate
            
            # Adjust optimization based on workload
            workload_adjusted = self._adjust_for_workload(total_files, total_size_mb, large_files, full_audit)
            
            return {
                'file_count': total_files,
                'total_size_mb': total_size_mb,
                'avg_file_size_kb': avg_file_size_kb,
                'size_distribution': size_categories,
                'large_files_count': large_files,
                'estimated_memory_mb': estimated_memory_mb,
                'workload_adjusted_optimization': workload_adjusted
            }
            
        except Exception as e:
            logger.warning(f"Failed to analyze workload: {e}")
            return {
                'file_count': 0,
                'error': str(e),
                'workload_adjusted_optimization': self.optimization_profile
            }
    
    def _adjust_for_workload(self, file_count: int, total_size_mb: float, 
                           large_files: int, full_audit: bool) -> Dict[str, Any]:
        """Adjust optimization profile based on specific workload characteristics."""
        base_profile = self.optimization_profile.copy()
        
        # Adjust based on file count
        if file_count > 500:
            # Large codebase - reduce parallelism
            base_profile['parallel_workers'] = max(1, base_profile['parallel_workers'] // 2)
            base_profile['batch_size'] = max(5, base_profile['batch_size'] // 2)
        elif file_count < 20:
            # Small codebase - reduce parallelism
            base_profile['parallel_workers'] = min(2, base_profile['parallel_workers'])
            base_profile['batch_size'] = min(10, base_profile['batch_size'])
        
        # Adjust based on file sizes
        if large_files > file_count * 0.1:  # More than 10% large files
            base_profile['batch_size'] = max(3, base_profile['batch_size'] // 2)
            base_profile['parallel_workers'] = max(1, base_profile['parallel_workers'] - 1)
        
        # Adjust for full audit mode
        if full_audit:
            # Full audit processes everything - be more conservative
            base_profile['parallel_workers'] = max(1, base_profile['parallel_workers'] // 2)
            base_profile['batch_size'] = max(5, base_profile['batch_size'] // 2)
        
        # Ensure minimum values
        base_profile['parallel_workers'] = max(1, base_profile['parallel_workers'])
        base_profile['batch_size'] = max(1, base_profile['batch_size'])
        
        return base_profile
    
    def get_optimal_settings(self, service_path: Path = None, full_audit: bool = False) -> Dict[str, Any]:
        """Get optimal processing settings for the current system and workload."""
        if service_path:
            try:
                # Check if we're already in an event loop
                try:
                    running_loop = asyncio.get_running_loop()
                    # We're in an async context, so we can't create a new event loop
                    # Fall back to synchronous workload analysis
                    workload_analysis = self._analyze_workload_sync(service_path, full_audit)
                except RuntimeError:
                    # No running loop, safe to create one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        workload_analysis = loop.run_until_complete(self.analyze_workload(service_path, full_audit))
                    finally:
                        loop.close()

                return {
                    'system_info': self.system_info,
                    'optimization_profile': workload_analysis.get('workload_adjusted_optimization', self.optimization_profile),
                    'workload_analysis': workload_analysis,
                    'recommendations': self.optimization_profile.get('recommendations', [])
                }
            except Exception as e:
                logger.warning(f"Failed to analyze workload for optimization: {e}")

        return {
            'system_info': self.system_info,
            'optimization_profile': self.optimization_profile,
            'workload_analysis': None,
            'recommendations': self.optimization_profile.get('recommendations', [])
        }

    def _analyze_workload_sync(self, service_path: Path, full_audit: bool = False) -> Dict[str, Any]:
        """Synchronous version of workload analysis for when we're in an async context."""
        try:
            # Count Python files synchronously
            python_files = []
            total_size_bytes = 0

            for root, dirs, files in os.walk(service_path):
                for file in files:
                    if file.endswith('.py') and not file.startswith('.') and not file.startswith('test_'):
                        file_path = Path(root) / file
                        try:
                            stat = file_path.stat()
                            file_size = stat.st_size
                            total_size_bytes += file_size

                            # Categorize files by size
                            if file_size < 1024:  # < 1KB
                                size_category = 'tiny'
                            elif file_size < 10240:  # < 10KB
                                size_category = 'small'
                            elif file_size < 102400:  # < 100KB
                                size_category = 'medium'
                            elif file_size < 1048576:  # < 1MB
                                size_category = 'large'
                            else:
                                size_category = 'huge'

                            python_files.append({
                                'path': file_path,
                                'size_bytes': file_size,
                                'size_kb': file_size / 1024,
                                'size_mb': file_size / (1024 * 1024),
                                'size_category': size_category
                            })

                        except OSError:
                            continue

            # Analyze file size distribution
            size_categories = {}
            for file_info in python_files:
                category = file_info['size_category']
                size_categories[category] = size_categories.get(category, 0) + 1

            # Calculate workload metrics
            total_files = len(python_files)
            total_size_mb = total_size_bytes / (1024 * 1024)
            avg_file_size_kb = (total_size_bytes / max(1, total_files)) / 1024

            # Estimate processing requirements
            large_files = sum(1 for f in python_files if f['size_category'] in ['large', 'huge'])
            estimated_memory_mb = total_files * 10  # Conservative estimate

            # Adjust optimization based on workload
            workload_adjusted = self._adjust_for_workload(total_files, total_size_mb, large_files, full_audit)

            return {
                'file_count': total_files,
                'total_size_mb': total_size_mb,
                'avg_file_size_kb': avg_file_size_kb,
                'size_distribution': size_categories,
                'large_files_count': large_files,
                'estimated_memory_mb': estimated_memory_mb,
                'workload_adjusted_optimization': workload_adjusted
            }

        except Exception as e:
            logger.warning(f"Failed to analyze workload synchronously: {e}")
            return {
                'file_count': 0,
                'error': str(e),
                'workload_adjusted_optimization': self.optimization_profile
            }
    
    def get_batch_size_for_files(self, file_count: int, file_sizes_mb: List[float] = None) -> int:
        """Calculate optimal batch size for a specific set of files."""
        base_batch_size = self.optimization_profile['batch_size']
        
        # Adjust based on file count
        if file_count < 10:
            return min(file_count, base_batch_size // 2)
        elif file_count < 50:
            return min(file_count, base_batch_size)
        elif file_count < 200:
            return min(file_count, base_batch_size * 2)
        else:
            # Very large file sets - use smaller batches
            return min(file_count, base_batch_size // 2)
    
    def should_use_parallel_processing(self, file_count: int, estimated_memory_mb: float) -> bool:
        """Determine if parallel processing should be used."""
        min_files_for_parallel = 20
        min_memory_for_parallel = 1024  # 1GB
        
        return (file_count >= min_files_for_parallel and 
                estimated_memory_mb >= min_memory_for_parallel and
                self.optimization_profile['parallel_workers'] > 1)
    
    def get_memory_limits(self) -> Dict[str, float]:
        """Get memory limits for safe processing."""
        available_memory = self.system_info['memory']['available_gb']
        
        return {
            'max_memory_per_batch_gb': available_memory * 0.3,  # Use 30% of available memory
            'max_memory_total_gb': available_memory * 0.7,      # Use 70% of available memory total
            'memory_warning_threshold_gb': available_memory * 0.5,
            'memory_critical_threshold_gb': available_memory * 0.8
        }

# Global optimizer instance
_resource_optimizer = None

def get_resource_optimizer() -> ResourceOptimizer:
    """Get or create the global resource optimizer instance."""
    global _resource_optimizer
    if _resource_optimizer is None:
        _resource_optimizer = ResourceOptimizer()
    return _resource_optimizer
