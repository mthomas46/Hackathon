"""M4 Max optimization utilities for local LLM inference."""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import platform
import subprocess
import psutil


@dataclass
class OptimizationConfig:
    """Configuration for M4 Max optimizations."""
    use_metal: bool = True
    use_neural_engine: bool = True
    max_memory_gb: float = 32.0
    batch_size: int = 8
    num_threads: int = 10
    precision: str = "float16"  # float32, float16, int8
    enable_kv_cache: bool = True
    use_flash_attention: bool = True


@dataclass
class PerformanceMetrics:
    """Performance metrics from inference."""
    inference_time_ms: float
    tokens_per_second: float
    memory_usage_gb: float
    gpu_utilization: float  # 0-1
    cpu_utilization: float  # 0-1
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "inference_time_ms": self.inference_time_ms,
            "tokens_per_second": self.tokens_per_second,
            "memory_usage_gb": self.memory_usage_gb,
            "gpu_utilization": self.gpu_utilization,
            "cpu_utilization": self.cpu_utilization
        }


class M4Optimizer:
    """
    M4 Max specific optimizations for LLM inference.
    
    Provides:
    - Hardware detection
    - Metal GPU acceleration
    - Neural Engine optimization
    - Memory optimization
    - Performance benchmarking
    """
    
    def __init__(self, config: Optional[OptimizationConfig] = None):
        """
        Initialize M4 optimizer.
        
        Args:
            config: OptimizationConfig, uses defaults if None
        """
        self.config = config or OptimizationConfig()
        self.hardware_info = self.detect_hardware()
    
    def detect_hardware(self) -> Dict[str, Any]:
        """
        Detect M4 Max hardware capabilities.
        
        Returns:
            Hardware information dictionary
        """
        info = {
            "system": platform.system(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "cpu_cores": psutil.cpu_count(logical=False),
            "cpu_threads": psutil.cpu_count(logical=True),
            "memory_gb": psutil.virtual_memory().total / (1024 ** 3),
            "has_metal": False,
            "has_neural_engine": False,
            "is_m4_max": False
        }
        
        # Check for Apple Silicon
        if platform.system() == "Darwin" and platform.machine() == "arm64":
            info["has_metal"] = True
            info["has_neural_engine"] = True
            
            # Try to detect M4 Max specifically
            try:
                result = subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    capture_output=True,
                    text=True
                )
                cpu_brand = result.stdout.strip()
                if "M4 Max" in cpu_brand or "M4" in cpu_brand:
                    info["is_m4_max"] = True
                    info["cpu_brand"] = cpu_brand
            except Exception:
                pass
        
        return info
    
    def optimize_model_loading(self, model_path: str) -> Dict[str, Any]:
        """
        Optimize model loading for M4 Max.
        
        Args:
            model_path: Path or identifier of model
        
        Returns:
            Optimization details
        """
        optimizations = {
            "model": model_path,
            "optimization_applied": [],
            "device": "cpu"
        }
        
        # Use Metal if available
        if self.hardware_info["has_metal"] and self.config.use_metal:
            optimizations["device"] = "mps"  # Metal Performance Shaders
            optimizations["optimization_applied"].append("metal_gpu")
        
        # Enable Neural Engine if available
        if self.hardware_info["has_neural_engine"] and self.config.use_neural_engine:
            optimizations["optimization_applied"].append("neural_engine")
        
        # Memory optimization
        if self.config.precision == "float16":
            optimizations["optimization_applied"].append("fp16_precision")
        elif self.config.precision == "int8":
            optimizations["optimization_applied"].append("int8_quantization")
        
        # KV cache
        if self.config.enable_kv_cache:
            optimizations["optimization_applied"].append("kv_cache")
        
        # Flash attention
        if self.config.use_flash_attention:
            optimizations["optimization_applied"].append("flash_attention")
        
        return optimizations
    
    def enable_metal_acceleration(self) -> Dict[str, Any]:
        """
        Enable Metal GPU acceleration.
        
        Returns:
            Metal configuration
        """
        if not self.hardware_info["has_metal"]:
            return {
                "enabled": False,
                "reason": "Metal not available"
            }
        
        return {
            "enabled": True,
            "device": "mps",
            "precision": self.config.precision,
            "batch_size": self.config.batch_size
        }
    
    def enable_neural_engine(self) -> Dict[str, Any]:
        """
        Enable Neural Engine optimization.
        
        Returns:
            Neural Engine configuration
        """
        if not self.hardware_info["has_neural_engine"]:
            return {
                "enabled": False,
                "reason": "Neural Engine not available"
            }
        
        return {
            "enabled": True,
            "optimizations": [
                "matrix_multiplication",
                "attention_kernels",
                "layer_norm"
            ]
        }
    
    def optimize_batch_size(
        self,
        model_size_gb: float,
        available_memory_gb: Optional[float] = None
    ) -> int:
        """
        Calculate optimal batch size for available memory.
        
        Args:
            model_size_gb: Model size in GB
            available_memory_gb: Available memory (defaults to system memory)
        
        Returns:
            Optimal batch size
        """
        if available_memory_gb is None:
            available_memory_gb = self.hardware_info["memory_gb"]
        
        # Rule of thumb: use 50% of available memory for batch processing
        usable_memory_gb = available_memory_gb * 0.5 - model_size_gb
        
        if usable_memory_gb <= 0:
            return 1
        
        # Estimate memory per batch item (rough approximation)
        memory_per_item_gb = 0.5  # GB
        
        optimal_batch = int(usable_memory_gb / memory_per_item_gb)
        
        # Clamp to reasonable range
        return max(1, min(optimal_batch, 32))
    
    def optimize_memory_usage(self) -> Dict[str, Any]:
        """
        Apply memory optimization strategies.
        
        Returns:
            Memory optimization details
        """
        strategies = []
        memory_saved_gb = 0.0
        
        # Use lower precision
        if self.config.precision == "float16":
            strategies.append("fp16_weights")
            memory_saved_gb += 2.0  # Rough estimate
        elif self.config.precision == "int8":
            strategies.append("int8_quantization")
            memory_saved_gb += 6.0  # Rough estimate
        
        # Enable gradient checkpointing (for training)
        strategies.append("gradient_checkpointing")
        
        # Use memory-efficient attention
        if self.config.use_flash_attention:
            strategies.append("flash_attention")
            memory_saved_gb += 1.0
        
        # Enable KV cache sharing
        if self.config.enable_kv_cache:
            strategies.append("kv_cache_sharing")
        
        return {
            "strategy": strategies,
            "memory_saved_gb": memory_saved_gb,
            "estimated_peak_memory_gb": self.config.max_memory_gb - memory_saved_gb
        }
    
    def benchmark_inference(
        self,
        model: str,
        prompt: str,
        num_runs: int = 10
    ) -> PerformanceMetrics:
        """
        Benchmark inference performance.
        
        Args:
            model: Model to benchmark
            prompt: Test prompt
            num_runs: Number of runs for averaging
        
        Returns:
            PerformanceMetrics
        """
        # Simulated benchmarking (would run actual inference)
        import time
        import random
        
        start_time = time.time()
        
        # Simulate inference
        time.sleep(0.1)  # Simulated processing
        
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        # Simulated metrics
        tokens_generated = random.randint(50, 150)
        tokens_per_second = tokens_generated / (duration_ms / 1000)
        
        # Get current resource usage
        memory_usage_gb = psutil.virtual_memory().used / (1024 ** 3)
        cpu_percent = psutil.cpu_percent(interval=0.1) / 100.0
        
        # GPU utilization (simulated, would use actual GPU monitoring)
        gpu_util = random.uniform(0.6, 0.95) if self.hardware_info["has_metal"] else 0.0
        
        return PerformanceMetrics(
            inference_time_ms=duration_ms,
            tokens_per_second=tokens_per_second,
            memory_usage_gb=memory_usage_gb,
            gpu_utilization=gpu_util,
            cpu_utilization=cpu_percent
        )
    
    def compare_configurations(
        self,
        model: str,
        prompt: str,
        configurations: List[OptimizationConfig]
    ) -> List[Dict[str, Any]]:
        """
        Compare different optimization configurations.
        
        Args:
            model: Model to test
            prompt: Test prompt
            configurations: List of configs to compare
        
        Returns:
            List of results with metrics
        """
        results = []
        
        for config in configurations:
            # Temporarily use this config
            original_config = self.config
            self.config = config
            
            # Benchmark
            metrics = self.benchmark_inference(model, prompt)
            
            results.append({
                "config": {
                    "use_metal": config.use_metal,
                    "precision": config.precision,
                    "batch_size": config.batch_size
                },
                "metrics": metrics.to_dict()
            })
            
            # Restore original config
            self.config = original_config
        
        return results
    
    def generate_optimization_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive optimization report.
        
        Returns:
            Optimization report
        """
        report = {
            "hardware": self.hardware_info,
            "configuration": {
                "use_metal": self.config.use_metal,
                "use_neural_engine": self.config.use_neural_engine,
                "precision": self.config.precision,
                "batch_size": self.config.batch_size,
                "num_threads": self.config.num_threads
            },
            "optimizations": {
                "metal": self.enable_metal_acceleration(),
                "neural_engine": self.enable_neural_engine(),
                "memory": self.optimize_memory_usage()
            },
            "performance": {
                "recommended_batch_size": self.optimize_batch_size(7.0),  # 7B model
                "max_memory_gb": self.config.max_memory_gb
            },
            "recommendations": []
        }
        
        # Generate recommendations
        if self.hardware_info["is_m4_max"]:
            report["recommendations"].append(
                "✅ M4 Max detected: All optimizations available"
            )
        
        if self.hardware_info["has_metal"] and not self.config.use_metal:
            report["recommendations"].append(
                "⚠️ Metal available but not enabled. Enable for better performance."
            )
        
        if self.config.precision == "float32":
            report["recommendations"].append(
                "💡 Consider using float16 to reduce memory usage by ~50%"
            )
        
        if self.config.batch_size > 16:
            report["recommendations"].append(
                "⚠️ Large batch size may cause memory issues. Monitor usage."
            )
        
        return report
    
    def get_recommended_config(self, model_size_gb: float) -> OptimizationConfig:
        """
        Get recommended configuration for a model size.
        
        Args:
            model_size_gb: Model size in GB
        
        Returns:
            Recommended OptimizationConfig
        """
        # Base config
        config = OptimizationConfig()
        
        # Enable all Apple Silicon features if available
        if self.hardware_info["has_metal"]:
            config.use_metal = True
        if self.hardware_info["has_neural_engine"]:
            config.use_neural_engine = True
        
        # Adjust precision based on model size
        if model_size_gb > 10:
            config.precision = "int8"  # Quantize large models
        elif model_size_gb > 5:
            config.precision = "float16"
        else:
            config.precision = "float16"  # Still beneficial
        
        # Calculate optimal batch size
        config.batch_size = self.optimize_batch_size(model_size_gb)
        
        # Thread count (use 80% of available cores)
        config.num_threads = max(1, int(self.hardware_info["cpu_cores"] * 0.8))
        
        return config


# Convenience function
def optimize_for_m4_max(model_size_gb: float = 7.0) -> OptimizationConfig:
    """
    Get optimized configuration for M4 Max.
    
    Args:
        model_size_gb: Model size in GB
    
    Returns:
        Optimized configuration
    """
    optimizer = M4Optimizer()
    return optimizer.get_recommended_config(model_size_gb)

