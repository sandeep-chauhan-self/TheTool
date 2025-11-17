"""
Health Monitor - Track system health and performance

This module provides real-time system health monitoring:
- Check API response times
- Monitor database connections
- Track cache performance
- Monitor queue health
- Check external service availability
- Generate health reports

Usage:
    monitor = HealthMonitor()
    
    # Add health checks
    monitor.add_check("database", check_database_connection)
    monitor.add_check("cache", check_redis_connection)
    monitor.add_check("api", check_api_response_time)
    
    # Run all checks
    results = monitor.run_all_checks()
    
    # Generate report
    report = monitor.generate_health_report()
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
import time


class HealthStatus(Enum):
    """Health check status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """
    Represents a single health check
    
    Attributes:
        name: Check name
        check_function: Function to run check
        status: Current status
        last_check: When check last ran
        response_time_ms: How long check took
        error_message: Error message if check failed
        threshold_ms: Response time threshold for degraded status
    """
    name: str
    check_function: Callable[[], Dict[str, Any]]
    status: HealthStatus = HealthStatus.UNKNOWN
    last_check: Optional[datetime] = None
    response_time_ms: float = 0.0
    error_message: Optional[str] = None
    threshold_ms: float = 1000.0  # 1 second
    
    def run(self) -> Dict[str, Any]:
        """
        Run health check
        
        Returns:
            Dict with status, response_time_ms, and optional data
        """
        start = time.time()
        
        try:
            result = self.check_function()
            elapsed_ms = (time.time() - start) * 1000
            
            self.response_time_ms = elapsed_ms
            self.last_check = datetime.now()
            self.error_message = None
            
            # Determine status
            if elapsed_ms > self.threshold_ms * 2:
                self.status = HealthStatus.UNHEALTHY
            elif elapsed_ms > self.threshold_ms:
                self.status = HealthStatus.DEGRADED
            else:
                self.status = result.get('status', HealthStatus.HEALTHY)
            
            return {
                'name': self.name,
                'status': self.status.value,
                'response_time_ms': elapsed_ms,
                'data': result
            }
        
        except Exception as e:
            elapsed_ms = (time.time() - start) * 1000
            self.response_time_ms = elapsed_ms
            self.last_check = datetime.now()
            self.status = HealthStatus.UNHEALTHY
            self.error_message = str(e)
            
            return {
                'name': self.name,
                'status': self.status.value,
                'response_time_ms': elapsed_ms,
                'error': str(e)
            }


class HealthMonitor:
    """
    Monitor system health with configurable checks
    
    Example:
        monitor = HealthMonitor()
        
        # Add built-in checks
        monitor.add_check("database", lambda: {'status': 'healthy', 'connections': 10})
        monitor.add_check("cache", lambda: {'status': 'healthy', 'hit_ratio': 0.85})
        monitor.add_check("queue", lambda: {'status': 'healthy', 'size': 5})
        
        # Run checks
        results = monitor.run_all_checks()
        
        # Get overall status
        status = monitor.get_overall_status()
        print(f"System status: {status}")
        
        # Generate report
        report = monitor.generate_health_report()
        print(report)
    """
    
    def __init__(self):
        self.checks: Dict[str, HealthCheck] = {}
        self.check_history: List[Dict] = []
        self.max_history: int = 100
    
    def add_check(self, name: str, check_function: Callable[[], Dict[str, Any]],
                  threshold_ms: float = 1000.0):
        """
        Add a health check
        
        Args:
            name: Check name
            check_function: Function that returns status dict
            threshold_ms: Response time threshold
        """
        check = HealthCheck(
            name=name,
            check_function=check_function,
            threshold_ms=threshold_ms
        )
        self.checks[name] = check
    
    def remove_check(self, name: str):
        """Remove a health check"""
        if name in self.checks:
            del self.checks[name]
    
    def run_check(self, name: str) -> Dict[str, Any]:
        """
        Run a specific health check
        
        Args:
            name: Check name
        
        Returns:
            Check result dict
        """
        if name not in self.checks:
            raise ValueError(f"Health check '{name}' not found")
        
        result = self.checks[name].run()
        
        # Add to history
        self.check_history.append({
            'timestamp': datetime.now(),
            'check': name,
            'result': result
        })
        
        # Trim history
        if len(self.check_history) > self.max_history:
            self.check_history = self.check_history[-self.max_history:]
        
        return result
    
    def run_all_checks(self) -> Dict[str, Dict[str, Any]]:
        """
        Run all health checks
        
        Returns:
            Dict mapping check name to result
        """
        results = {}
        for name in self.checks:
            results[name] = self.run_check(name)
        return results
    
    def get_overall_status(self) -> HealthStatus:
        """
        Get overall system health status
        
        Returns:
            Overall status (worst of all checks)
        """
        if not self.checks:
            return HealthStatus.UNKNOWN
        
        # Get worst status
        statuses = [check.status for check in self.checks.values()]
        
        if any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            return HealthStatus.DEGRADED
        elif all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN
    
    def get_failing_checks(self) -> List[HealthCheck]:
        """Get all checks that are not healthy"""
        return [
            check for check in self.checks.values()
            if check.status in [HealthStatus.UNHEALTHY, HealthStatus.DEGRADED]
        ]
    
    def get_average_response_time(self) -> float:
        """Get average response time across all checks"""
        if not self.checks:
            return 0.0
        
        total = sum(check.response_time_ms for check in self.checks.values())
        return total / len(self.checks)
    
    def generate_health_report(self) -> str:
        """
        Generate comprehensive health report
        
        Returns:
            Formatted text report
        """
        lines = []
        lines.append("=" * 80)
        lines.append("SYSTEM HEALTH REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Overall status
        overall = self.get_overall_status()
        status_icon_map = {
            HealthStatus.HEALTHY: "?",
            HealthStatus.DEGRADED: "?",
            HealthStatus.UNHEALTHY: "?",
            HealthStatus.UNKNOWN: "?"
        }
        overall_icon = status_icon_map[overall]
        
        lines.append(f"Overall Status: {overall_icon} {overall.value.upper()}")
        lines.append(f"Checks: {len(self.checks)}")
        lines.append(f"Average Response Time: {self.get_average_response_time():.2f}ms")
        lines.append("")
        
        # Individual checks
        lines.append("HEALTH CHECKS:")
        lines.append("-" * 80)
        
        for check in self.checks.values():
            icon = status_icon_map.get(check.status, "?")
            lines.append(f"{icon} {check.name}: {check.status.value.upper()}")
            lines.append(f"  Response Time: {check.response_time_ms:.2f}ms")
            
            if check.last_check:
                lines.append(f"  Last Check: {check.last_check.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if check.error_message:
                lines.append(f"  Error: {check.error_message}")
            
            lines.append("")
        
        # Failing checks
        failing = self.get_failing_checks()
        if failing:
            lines.append("ATTENTION REQUIRED:")
            lines.append("-" * 80)
            for check in failing:
                lines.append(f"? {check.name}: {check.status.value}")
                if check.error_message:
                    lines.append(f"  {check.error_message}")
            lines.append("")
        
        lines.append("=" * 80)
        return "\n".join(lines)
    
    def to_json(self) -> Dict[str, Any]:
        """
        Export health status as JSON
        
        Returns:
            Dict suitable for JSON serialization
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_status': self.get_overall_status().value,
            'checks': {
                name: {
                    'status': check.status.value,
                    'response_time_ms': check.response_time_ms,
                    'last_check': check.last_check.isoformat() if check.last_check else None,
                    'error': check.error_message
                }
                for name, check in self.checks.items()
            }
        }


def monitor_system_health() -> Dict[str, Any]:
    """
    Quick system health check with default checks
    
    Returns:
        Dict with health status
    
    Note: This is a stub implementation. In production, implement actual checks.
    """
    monitor = HealthMonitor()
    
    # Add default checks (stubs)
    monitor.add_check("database", lambda: {'status': HealthStatus.HEALTHY, 'connections': 10})
    monitor.add_check("cache", lambda: {'status': HealthStatus.HEALTHY, 'hit_ratio': 0.75})
    monitor.add_check("api", lambda: {'status': HealthStatus.HEALTHY, 'requests_per_min': 120})
    
    results = monitor.run_all_checks()
    
    return {
        'overall_status': monitor.get_overall_status().value,
        'checks': results
    }


def generate_health_report(monitor: HealthMonitor) -> str:
    """
    Generate health report
    
    Args:
        monitor: HealthMonitor instance
    
    Returns:
        Formatted report string
    """
    return monitor.generate_health_report()


# Example health check functions that can be used with HealthMonitor

def check_database_connection() -> Dict[str, Any]:
    """
    Check database connection health
    
    Returns:
        Status dict
    """
    # Stub implementation - replace with actual database check
    return {
        'status': HealthStatus.HEALTHY,
        'connections': 10,
        'max_connections': 100,
        'query_time_ms': 5.2
    }


def check_cache_connection() -> Dict[str, Any]:
    """
    Check cache (Redis) connection health
    
    Returns:
        Status dict
    """
    # Stub implementation - replace with actual Redis check
    return {
        'status': HealthStatus.HEALTHY,
        'hit_ratio': 0.78,
        'memory_usage_mb': 256,
        'connected_clients': 5
    }


def check_queue_health() -> Dict[str, Any]:
    """
    Check message queue health
    
    Returns:
        Status dict
    """
    # Stub implementation - replace with actual queue check
    return {
        'status': HealthStatus.HEALTHY,
        'queue_size': 12,
        'processing_rate': 50,
        'failed_jobs': 0
    }


def check_api_response_time() -> Dict[str, Any]:
    """
    Check API response time
    
    Returns:
        Status dict
    """
    # Stub implementation - replace with actual API check
    return {
        'status': HealthStatus.HEALTHY,
        'avg_response_time_ms': 145,
        'p95_response_time_ms': 320,
        'requests_per_minute': 180
    }


def check_external_service(url: str, timeout: float = 5.0) -> Dict[str, Any]:
    """
    Check external service availability
    
    Args:
        url: Service URL
        timeout: Timeout in seconds
    
    Returns:
        Status dict
    """
    # Stub implementation - replace with actual HTTP check
    return {
        'status': HealthStatus.HEALTHY,
        'response_time_ms': 234,
        'status_code': 200
    }
