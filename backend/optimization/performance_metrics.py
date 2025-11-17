"""
Performance Measurement Utilities

Part 5A: Performance Optimization Engine (POE)
PERF_MEASUREMENT_001: Core measurement utilities

Provides tools to measure, profile, and compare performance of functions.
Used to validate the 7-93x speedup claims from the redesign analysis.
"""

import time
import functools
import cProfile
import pstats
import io
from typing import Callable, Any, Dict, Tuple, Optional
from dataclasses import dataclass, field
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """
    Performance measurement results
    
    Attributes:
        cpu_time: CPU time in seconds
        wall_time: Wall clock time in seconds
        peak_memory: Peak memory usage in bytes
        function_name: Name of measured function
        call_count: Number of calls (for profiling)
        result: Return value from function
    """
    cpu_time: float
    wall_time: float
    peak_memory: Optional[int] = None
    function_name: str = ""
    call_count: int = 1
    result: Any = None
    profile_stats: Optional[str] = None
    
    @property
    def speedup(self) -> Optional[float]:
        """Calculate speedup vs baseline (set externally)"""
        if hasattr(self, '_baseline_time') and self._baseline_time > 0:
            return self._baseline_time / self.wall_time
        return None
    
    def set_baseline(self, baseline_time: float) -> None:
        """Set baseline time for speedup calculation"""
        self._baseline_time = baseline_time
    
    def __str__(self) -> str:
        """Human-readable performance summary"""
        lines = [
            f"Performance: {self.function_name}",
            f"  CPU Time:  {self.cpu_time:.6f}s",
            f"  Wall Time: {self.wall_time:.6f}s"
        ]
        
        if self.peak_memory:
            lines.append(f"  Peak Memory: {self.peak_memory / 1024 / 1024:.2f}MB")
        
        if self.speedup:
            lines.append(f"  Speedup: {self.speedup:.1f}x")
        
        return "\n".join(lines)


def measure_performance(func: Optional[Callable] = None, *, measure_memory: bool = False) -> Callable:
    """
    Decorator to measure function performance
    
    Args:
        func: Function to measure (when used without arguments)
        measure_memory: Whether to measure memory usage (requires tracemalloc)
    
    Returns:
        Decorated function that returns (result, metrics)
    
    Usage:
        @measure_performance
        def my_function(x):
            return x * 2
        
        result, metrics = my_function(5)
        print(metrics)  # Shows CPU time, wall time
        
        @measure_performance(measure_memory=True)
        def memory_intensive():
            return [0] * 1000000
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args, **kwargs) -> Tuple[Any, PerformanceMetrics]:
            # Measure memory if requested
            if measure_memory:
                import tracemalloc
                tracemalloc.start()
            
            # CPU time
            start_cpu = time.process_time()
            # Wall time
            start_wall = time.perf_counter()
            
            # Execute function
            result = f(*args, **kwargs)
            
            # Calculate times
            cpu_time = time.process_time() - start_cpu
            wall_time = time.perf_counter() - start_wall
            
            # Measure memory
            peak_memory = None
            if measure_memory:
                import tracemalloc
                _, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                peak_memory = peak
            
            # Create metrics
            metrics = PerformanceMetrics(
                cpu_time=cpu_time,
                wall_time=wall_time,
                peak_memory=peak_memory,
                function_name=f.__name__,
                result=result
            )
            
            logger.debug(f"Performance: {f.__name__} - {wall_time:.6f}s")
            
            return result, metrics
        
        return wrapper
    
    # Handle both @measure_performance and @measure_performance()
    if func is None:
        return decorator
    else:
        return decorator(func)


def profile_function(func: Callable, *args, **kwargs) -> Tuple[Any, str]:
    """
    Profile a function and return detailed statistics
    
    Args:
        func: Function to profile
        *args: Positional arguments to pass to function
        **kwargs: Keyword arguments to pass to function
    
    Returns:
        Tuple of (result, profile_stats_string)
    
    Usage:
        def slow_function(n):
            return sum(i**2 for i in range(n))
        
        result, stats = profile_function(slow_function, 10000)
        print(stats)  # Shows detailed timing breakdown
    """
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Execute function
    result = func(*args, **kwargs)
    
    profiler.disable()
    
    # Get stats
    s = io.StringIO()
    stats = pstats.Stats(profiler, stream=s)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions
    
    return result, s.getvalue()


def compare_performance(
    func_old: Callable,
    func_new: Callable,
    *args,
    runs: int = 10,
    **kwargs
) -> Dict[str, PerformanceMetrics]:
    """
    Compare performance of two function implementations
    
    Args:
        func_old: Original implementation
        func_new: Optimized implementation
        *args: Arguments to pass to both functions
        runs: Number of runs to average
        **kwargs: Keyword arguments to pass to both functions
    
    Returns:
        Dict with 'old' and 'new' metrics
    
    Usage:
        def old_sum(n):
            total = 0
            for i in range(n):
                total += i
            return total
        
        def new_sum(n):
            return n * (n - 1) // 2
        
        comparison = compare_performance(old_sum, new_sum, 10000, runs=100)
        print(f"Speedup: {comparison['new'].speedup:.1f}x")
    """
    # Warm-up runs
    func_old(*args, **kwargs)
    func_new(*args, **kwargs)
    
    # Measure old implementation
    old_times = []
    old_result = None
    for _ in range(runs):
        start = time.perf_counter()
        old_result = func_old(*args, **kwargs)
        old_times.append(time.perf_counter() - start)
    
    old_avg_time = sum(old_times) / len(old_times)
    old_metrics = PerformanceMetrics(
        cpu_time=old_avg_time,  # Simplified
        wall_time=old_avg_time,
        function_name=func_old.__name__,
        call_count=runs,
        result=old_result
    )
    
    # Measure new implementation
    new_times = []
    new_result = None
    for _ in range(runs):
        start = time.perf_counter()
        new_result = func_new(*args, **kwargs)
        new_times.append(time.perf_counter() - start)
    
    new_avg_time = sum(new_times) / len(new_times)
    new_metrics = PerformanceMetrics(
        cpu_time=new_avg_time,
        wall_time=new_avg_time,
        function_name=func_new.__name__,
        call_count=runs,
        result=new_result
    )
    
    # Set baseline for speedup calculation
    new_metrics.set_baseline(old_avg_time)
    
    # Log comparison
    speedup = old_avg_time / new_avg_time
    logger.info(
        f"Performance comparison:\n"
        f"  Old ({func_old.__name__}): {old_avg_time*1000:.3f}ms\n"
        f"  New ({func_new.__name__}): {new_avg_time*1000:.3f}ms\n"
        f"  Speedup: {speedup:.1f}x"
    )
    
    return {
        'old': old_metrics,
        'new': new_metrics
    }


@contextmanager
def performance_timer(name: str = "operation"):
    """
    Context manager for timing code blocks
    
    Usage:
        with performance_timer("data processing"):
            # ... expensive operations ...
            process_data()
    """
    start = time.perf_counter()
    yield
    duration = time.perf_counter() - start
    logger.info(f"{name}: {duration:.6f}s")


def benchmark_iterations(func: Callable, *args, iterations: int = 1000, **kwargs) -> float:
    """
    Benchmark function over many iterations
    
    Args:
        func: Function to benchmark
        *args: Arguments to pass
        iterations: Number of iterations
        **kwargs: Keyword arguments to pass
    
    Returns:
        Average time per iteration in seconds
    """
    start = time.perf_counter()
    for _ in range(iterations):
        func(*args, **kwargs)
    duration = time.perf_counter() - start
    
    avg_time = duration / iterations
    logger.info(f"Benchmark: {func.__name__} - {avg_time*1000:.6f}ms per iteration ({iterations} runs)")
    
    return avg_time
