"""
Algorithm Complexity Analysis

Part 5A: Performance Optimization Engine (POE)
PERF_COMPLEXITY_001: Big-O complexity analysis and benchmarking

Analyzes algorithm complexity by testing with different input sizes.
Helps validate O(N^2) to O(N) optimizations from redesign analysis.
"""

import time
import math
from typing import Callable, List, Tuple, Dict, Any
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class ComplexityMetrics:
    """
    Algorithm complexity analysis results
    
    Attributes:
        complexity: Estimated complexity (e.g., "O(N)", "O(N^2)")
        input_sizes: List of tested input sizes
        times: List of measured times for each input size
        function_name: Name of analyzed function
        r_squared: Goodness of fit (0-1, higher is better)
        coefficients: Fitted coefficients [a, b] for time = a*f(n) + b
    """
    complexity: str
    input_sizes: List[int]
    times: List[float]
    function_name: str = ""
    r_squared: float = 0.0
    coefficients: Tuple[float, float] = (0.0, 0.0)
    
    def __str__(self) -> str:
        """Human-readable complexity summary"""
        lines = [
            f"Complexity Analysis: {self.function_name}",
            f"  Detected: {self.complexity}",
            f"  R-squared: {self.r_squared:.4f}",
            f"  Tested sizes: {self.input_sizes}"
        ]
        
        if len(self.times) > 0:
            lines.append(f"  Time range: {min(self.times)*1000:.3f}ms - {max(self.times)*1000:.3f}ms")
        
        return "\n".join(lines)


def analyze_complexity(
    func: Callable,
    input_generator: Callable[[int], Any],
    sizes: List[int] = None,
    runs_per_size: int = 5
) -> ComplexityMetrics:
    """
    Analyze algorithm complexity by testing with different input sizes
    
    Args:
        func: Function to analyze
        input_generator: Function that generates input of given size
                        Example: lambda n: list(range(n))
        sizes: List of input sizes to test (default: [10, 50, 100, 500, 1000])
        runs_per_size: Number of runs to average for each size
    
    Returns:
        ComplexityMetrics with detected complexity
    
    Usage:
        def bubble_sort(arr):
            # O(N^2) implementation
            for i in range(len(arr)):
                for j in range(len(arr)-1):
                    if arr[j] > arr[j+1]:
                        arr[j], arr[j+1] = arr[j+1], arr[j]
            return arr
        
        metrics = analyze_complexity(
            bubble_sort,
            lambda n: list(range(n, 0, -1))  # Worst case
        )
        print(metrics.complexity)  # "O(N^2)"
    """
    if sizes is None:
        sizes = [10, 50, 100, 500, 1000]
    
    times = []
    
    # Benchmark each size
    for size in sizes:
        size_times = []
        for _ in range(runs_per_size):
            input_data = input_generator(size)
            
            start = time.perf_counter()
            func(input_data)
            duration = time.perf_counter() - start
            
            size_times.append(duration)
        
        avg_time = sum(size_times) / len(size_times)
        times.append(avg_time)
        logger.debug(f"Size {size}: {avg_time*1000:.3f}ms")
    
    # Detect complexity
    complexity, r_squared, coeffs = _detect_complexity(sizes, times)
    
    return ComplexityMetrics(
        complexity=complexity,
        input_sizes=sizes,
        times=times,
        function_name=func.__name__,
        r_squared=r_squared,
        coefficients=coeffs
    )


def _detect_complexity(sizes: List[int], times: List[float]) -> Tuple[str, float, Tuple[float, float]]:
    """
    Detect complexity class from timing data
    
    Tests fits for: O(1), O(log N), O(N), O(N log N), O(N^2), O(N^3)
    Returns best fit based on R^2 value
    """
    if len(sizes) < 3:
        return "Unknown (insufficient data)", 0.0, (0.0, 0.0)
    
    # Define complexity functions
    complexity_functions = {
        "O(1)": lambda n: 1,
        "O(log N)": lambda n: math.log(n) if n > 0 else 1,
        "O(N)": lambda n: n,
        "O(N log N)": lambda n: n * math.log(n) if n > 0 else n,
        "O(N^2)": lambda n: n * n,
        "O(N^3)": lambda n: n * n * n,
    }
    
    best_fit = None
    best_r_squared = -1
    best_coeffs = (0.0, 0.0)
    
    # Try each complexity
    for complexity_name, complexity_func in complexity_functions.items():
        try:
            # Generate x values (complexity function of size)
            x_values = [complexity_func(size) for size in sizes]
            
            # Linear regression: time = a*x + b
            r_squared, coeffs = _linear_regression(x_values, times)
            
            if r_squared > best_r_squared:
                best_r_squared = r_squared
                best_fit = complexity_name
                best_coeffs = coeffs
        except (ValueError, ZeroDivisionError):
            continue
    
    return best_fit or "Unknown", best_r_squared, best_coeffs


def _linear_regression(x: List[float], y: List[float]) -> Tuple[float, Tuple[float, float]]:
    """
    Simple linear regression: y = a*x + b
    Returns (r_squared, (a, b))
    """
    n = len(x)
    if n == 0:
        return 0.0, (0.0, 0.0)
    
    # Calculate means
    x_mean = sum(x) / n
    y_mean = sum(y) / n
    
    # Calculate coefficients
    numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
    
    if denominator == 0:
        return 0.0, (0.0, y_mean)
    
    a = numerator / denominator
    b = y_mean - a * x_mean
    
    # Calculate R^2
    ss_tot = sum((y[i] - y_mean) ** 2 for i in range(n))
    ss_res = sum((y[i] - (a * x[i] + b)) ** 2 for i in range(n))
    
    if ss_tot == 0:
        return 1.0 if ss_res == 0 else 0.0, (a, b)
    
    r_squared = 1 - (ss_res / ss_tot)
    
    return r_squared, (a, b)


def benchmark_algorithm(
    func: Callable,
    input_generator: Callable[[int], Any],
    size: int,
    runs: int = 10
) -> float:
    """
    Benchmark algorithm at a specific input size
    
    Args:
        func: Function to benchmark
        input_generator: Generates input of given size
        size: Input size to test
        runs: Number of runs to average
    
    Returns:
        Average time in seconds
    
    Usage:
        avg_time = benchmark_algorithm(
            sorted,
            lambda n: list(range(n, 0, -1)),
            size=10000,
            runs=20
        )
        print(f"Sorted 10k items in {avg_time*1000:.2f}ms")
    """
    times = []
    
    for _ in range(runs):
        input_data = input_generator(size)
        
        start = time.perf_counter()
        func(input_data)
        duration = time.perf_counter() - start
        
        times.append(duration)
    
    avg_time = sum(times) / len(times)
    logger.info(f"Benchmark: {func.__name__} @ size={size} - {avg_time*1000:.3f}ms (avg of {runs} runs)")
    
    return avg_time


def compare_algorithms(
    func_old: Callable,
    func_new: Callable,
    input_generator: Callable[[int], Any],
    sizes: List[int] = None
) -> Dict[str, ComplexityMetrics]:
    """
    Compare complexity of two algorithm implementations
    
    Args:
        func_old: Original implementation
        func_new: Optimized implementation
        input_generator: Generates inputs
        sizes: Input sizes to test
    
    Returns:
        Dict with 'old' and 'new' complexity metrics
    
    Usage:
        def old_contains(arr, target):
            for x in arr:
                if x == target:
                    return True
            return False
        
        def new_contains(arr, target):
            return target in set(arr)
        
        comparison = compare_algorithms(
            old_contains,
            lambda arr: new_contains(arr, arr[-1] if arr else 0),
            lambda n: list(range(n))
        )
        print(f"Old: {comparison['old'].complexity}")
        print(f"New: {comparison['new'].complexity}")
    """
    if sizes is None:
        sizes = [10, 50, 100, 500, 1000]
    
    old_metrics = analyze_complexity(func_old, input_generator, sizes)
    new_metrics = analyze_complexity(func_new, input_generator, sizes)
    
    # Log comparison
    logger.info(
        f"Complexity comparison:\n"
        f"  Old ({func_old.__name__}): {old_metrics.complexity} (R^2={old_metrics.r_squared:.4f})\n"
        f"  New ({func_new.__name__}): {new_metrics.complexity} (R^2={new_metrics.r_squared:.4f})"
    )
    
    return {
        'old': old_metrics,
        'new': new_metrics
    }


def estimate_scaling(metrics: ComplexityMetrics, target_size: int) -> float:
    """
    Estimate time for a different input size based on complexity
    
    Args:
        metrics: Complexity metrics from analyze_complexity
        target_size: Input size to estimate for
    
    Returns:
        Estimated time in seconds
    
    Usage:
        metrics = analyze_complexity(my_func, input_gen)
        # Tested up to 1000, what about 10000?
        estimated = estimate_scaling(metrics, 10000)
        print(f"Estimated time: {estimated*1000:.2f}ms")
    """
    # Parse complexity to get function
    complexity_map = {
        "O(1)": lambda n: 1,
        "O(log N)": lambda n: math.log(n) if n > 0 else 1,
        "O(N)": lambda n: n,
        "O(N log N)": lambda n: n * math.log(n) if n > 0 else n,
        "O(N^2)": lambda n: n * n,
        "O(N^3)": lambda n: n * n * n,
    }
    
    func = complexity_map.get(metrics.complexity)
    if func is None:
        logger.warning(f"Unknown complexity: {metrics.complexity}")
        return 0.0
    
    # Use fitted coefficients: time = a*f(n) + b
    a, b = metrics.coefficients
    estimated_time = a * func(target_size) + b
    
    return max(0.0, estimated_time)  # Time can't be negative
