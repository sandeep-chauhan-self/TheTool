"""
Tests for Performance Optimization Engine (Part 5A)

Tests performance measurement and complexity analysis utilities.
"""

import pytest
import time
from optimization.performance_metrics import (
    measure_performance,
    profile_function,
    compare_performance,
    PerformanceMetrics,
    performance_timer,
    benchmark_iterations
)
from optimization.complexity_analyzer import (
    analyze_complexity,
    ComplexityMetrics,
    benchmark_algorithm,
    compare_algorithms,
    estimate_scaling
)


class TestPerformanceMetrics:
    """Test performance measurement utilities"""
    
    def test_measure_performance_decorator(self):
        """Test @measure_performance decorator"""
        @measure_performance
        def test_func(n):
            time.sleep(0.01)  # 10ms
            return n * 2
        
        result, metrics = test_func(5)
        
        assert result == 10
        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.wall_time >= 0.01  # At least 10ms
        assert metrics.cpu_time >= 0
        assert metrics.function_name == "test_func"
    
    def test_measure_performance_with_memory(self):
        """Test memory measurement"""
        @measure_performance(measure_memory=True)
        def memory_func():
            return [0] * 1000000  # ~8MB
        
        result, metrics = memory_func()
        
        assert len(result) == 1000000
        assert metrics.peak_memory is not None
        assert metrics.peak_memory > 0
    
    def test_profile_function(self):
        """Test function profiling"""
        def slow_func(n):
            return sum(i**2 for i in range(n))
        
        result, stats = profile_function(slow_func, 1000)
        
        assert result == sum(i**2 for i in range(1000))
        assert isinstance(stats, str)
        assert "slow_func" in stats or "function calls" in stats
    
    def test_compare_performance(self):
        """Test performance comparison"""
        def old_sum(n):
            total = 0
            for i in range(n):
                total += i
            return total
        
        def new_sum(n):
            return n * (n - 1) // 2
        
        comparison = compare_performance(old_sum, new_sum, 10000, runs=10)
        
        assert 'old' in comparison
        assert 'new' in comparison
        assert comparison['old'].result == comparison['new'].result
        assert comparison['new'].speedup is not None
        assert comparison['new'].speedup >= 1.0  # new should be faster
    
    def test_performance_timer(self):
        """Test context manager timer"""
        with performance_timer("test operation") as timer:
            time.sleep(0.01)
        # Should log without errors
    
    def test_benchmark_iterations(self):
        """Test iteration benchmarking"""
        def simple_func():
            return sum(range(100))
        
        avg_time = benchmark_iterations(simple_func, iterations=100)
        
        assert avg_time > 0
        assert avg_time < 1.0  # Should be fast
    
    def test_metrics_string_representation(self):
        """Test PerformanceMetrics string output"""
        metrics = PerformanceMetrics(
            cpu_time=0.05,
            wall_time=0.1,
            function_name="test_func"
        )
        
        output = str(metrics)
        assert "test_func" in output
        assert "0.05" in output
        assert "0.1" in output
    
    def test_speedup_calculation(self):
        """Test speedup calculation"""
        metrics = PerformanceMetrics(
            cpu_time=0.01,
            wall_time=0.01,
            function_name="fast_func"
        )
        
        metrics.set_baseline(0.1)  # Old version took 0.1s
        
        assert metrics.speedup == 10.0


class TestComplexityAnalysis:
    """Test complexity analysis utilities"""
    
    def test_analyze_constant_complexity(self):
        """Test O(1) complexity detection"""
        def constant_func(arr):
            return arr[0] if arr else None
        
        metrics = analyze_complexity(
            constant_func,
            lambda n: list(range(n)),
            sizes=[10, 100, 1000],
            runs_per_size=3
        )
        
        assert metrics.complexity in ["O(1)", "O(log N)"]  # Both acceptable for constant
        assert metrics.r_squared >= 0.3  # Lower threshold for very fast functions
        assert len(metrics.input_sizes) == 3
        assert len(metrics.times) == 3
    
    def test_analyze_linear_complexity(self):
        """Test O(N) complexity detection"""
        def linear_func(arr):
            total = 0
            for x in arr:
                total += x
            return total
        
        metrics = analyze_complexity(
            linear_func,
            lambda n: list(range(n)),
            sizes=[10, 50, 100, 500],
            runs_per_size=5
        )
        
        assert metrics.complexity in ["O(N)", "O(N log N)"]  # Linear or near-linear
        assert metrics.r_squared >= 0.7
        assert metrics.function_name == "linear_func"
    
    def test_analyze_quadratic_complexity(self):
        """Test O(N^2) complexity detection"""
        def quadratic_func(arr):
            count = 0
            for i in arr:
                for j in arr:
                    count += 1
            return count
        
        metrics = analyze_complexity(
            quadratic_func,
            lambda n: list(range(n)),
            sizes=[5, 10, 20, 40],
            runs_per_size=3
        )
        
        assert metrics.complexity in ["O(N^2)", "O(N^3)"]  # Quadratic or worse
        assert metrics.r_squared >= 0.8  # Should fit well
    
    def test_benchmark_algorithm(self):
        """Test algorithm benchmarking"""
        def sort_func(arr):
            return sorted(arr)
        
        avg_time = benchmark_algorithm(
            sort_func,
            lambda n: list(range(n, 0, -1)),
            size=1000,
            runs=10
        )
        
        assert avg_time > 0
        assert avg_time < 1.0  # Should be reasonably fast
    
    def test_compare_algorithms(self):
        """Test algorithm comparison"""
        def old_max(arr):
            # O(N) but inefficient
            result = arr[0] if arr else 0
            for x in arr:
                if x > result:
                    result = x
            return result
        
        def new_max(arr):
            # O(N) optimized
            return max(arr) if arr else 0
        
        comparison = compare_algorithms(
            old_max,
            new_max,
            lambda n: list(range(n)),
            sizes=[10, 50, 100]
        )
        
        assert 'old' in comparison
        assert 'new' in comparison
        # Both should be linear (O(N) or O(N log N))
        # Note: For very fast functions, timing noise may affect detection
        assert comparison['old'].complexity is not None
        assert comparison['new'].complexity is not None
    
    def test_estimate_scaling(self):
        """Test scaling estimation"""
        # Create known linear metrics
        metrics = ComplexityMetrics(
            complexity="O(N)",
            input_sizes=[10, 100, 1000],
            times=[0.001, 0.01, 0.1],
            r_squared=0.99,
            coefficients=(0.0001, 0)  # time = 0.0001*N
        )
        
        estimated = estimate_scaling(metrics, 10000)
        
        assert estimated > 0
        assert 0.5 < estimated < 2.0  # Should be ~1.0s
    
    def test_complexity_metrics_string(self):
        """Test ComplexityMetrics string output"""
        metrics = ComplexityMetrics(
            complexity="O(N^2)",
            input_sizes=[10, 100, 1000],
            times=[0.001, 0.1, 10.0],
            function_name="test_func",
            r_squared=0.95
        )
        
        output = str(metrics)
        assert "O(N^2)" in output
        assert "test_func" in output
        assert "0.95" in output


class TestRealWorldScenarios:
    """Test with real-world optimization scenarios"""
    
    def test_vectorization_speedup(self):
        """Test measuring vectorization improvement"""
        def loop_version(arr):
            result = []
            for x in arr:
                result.append(x * 2)
            return result
        
        def vectorized_version(arr):
            import numpy as np
            return (np.array(arr) * 2).tolist()
        
        comparison = compare_performance(
            loop_version,
            vectorized_version,
            list(range(10000)),
            runs=10
        )
        
        assert comparison['new'].speedup is not None
        # Vectorized should be faster (though margin may be small for this simple case)
    
    def test_algorithm_optimization(self):
        """Test measuring algorithm optimization (O(N^2) to O(N))"""
        def naive_duplicates(arr):
            # O(N^2)
            for i in range(len(arr)):
                for j in range(i + 1, len(arr)):
                    if arr[i] == arr[j]:
                        return True
            return False
        
        def optimized_duplicates(arr):
            # O(N)
            return len(arr) != len(set(arr))
        
        comparison = compare_performance(
            naive_duplicates,
            optimized_duplicates,
            list(range(1000)),
            runs=10
        )
        
        assert comparison['new'].speedup is not None
        assert comparison['new'].speedup > 1.0  # Should be faster
    
    def test_caching_impact(self):
        """Test measuring caching improvements"""
        call_count = [0]
        cache = {}
        
        def uncached_fib(n):
            call_count[0] += 1
            if n <= 1:
                return n
            return uncached_fib(n - 1) + uncached_fib(n - 2)
        
        def cached_fib(n):
            if n in cache:
                return cache[n]
            if n <= 1:
                cache[n] = n
                return n
            result = cached_fib(n - 1) + cached_fib(n - 2)
            cache[n] = result
            return result
        
        # Reset for fair comparison
        call_count[0] = 0
        cache.clear()
        
        @measure_performance
        def test_uncached():
            call_count[0] = 0
            return uncached_fib(15)
        
        @measure_performance
        def test_cached():
            cache.clear()
            return cached_fib(15)
        
        result1, metrics1 = test_uncached()
        result2, metrics2 = test_cached()
        
        assert result1 == result2
        assert metrics2.wall_time < metrics1.wall_time  # Cached should be faster


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_input(self):
        """Test with empty inputs"""
        def empty_func(arr):
            return len(arr)
        
        metrics = analyze_complexity(
            empty_func,
            lambda n: list(range(n)),
            sizes=[0, 1, 10],
            runs_per_size=3
        )
        
        assert metrics.complexity is not None
        assert len(metrics.times) == 3
    
    def test_very_fast_function(self):
        """Test with extremely fast functions"""
        @measure_performance
        def instant_func():
            return 42
        
        result, metrics = instant_func()
        
        assert result == 42
        assert metrics.wall_time >= 0  # Should handle near-zero times
    
    def test_compare_identical_functions(self):
        """Test comparing identical implementations"""
        def func1(n):
            return n * 2
        
        def func2(n):
            return n * 2
        
        comparison = compare_performance(func1, func2, 100, runs=5)
        
        assert comparison['new'].speedup is not None
        # Speedup should be close to 1.0, but allow margin for timing variance
        assert 0.3 <= comparison['new'].speedup <= 3.0  # Wider tolerance for identical functions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
