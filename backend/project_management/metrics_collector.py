"""
Metrics Collector - Gather technical and business KPIs

This module collects and tracks various metrics to measure project success:
- Technical metrics: Response time, throughput, test coverage, complexity
- Business metrics: User satisfaction, feature velocity, bug fix time
- System metrics: CPU, memory, cache hit ratio, error rate

Usage:
    collector = MetricsCollector()
    
    # Collect technical metrics
    collector.collect_technical_metric(
        "response_time",
        baseline=5.2,
        current=0.48,
        target=0.5,
        unit="seconds"
    )
    
    # Collect business metrics
    collector.collect_business_metric(
        "user_satisfaction",
        baseline=7.2,
        current=8.3,
        target=8.5,
        unit="NPS"
    )
    
    # Generate report
    report = collector.generate_report()
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Literal
from enum import Enum


class MetricCategory(Enum):
    """Metric categories"""
    PERFORMANCE = "performance"
    QUALITY = "quality"
    RELIABILITY = "reliability"
    BUSINESS = "business"
    SYSTEM = "system"


class MetricStatus(Enum):
    """Metric achievement status"""
    BELOW_TARGET = "below_target"
    AT_TARGET = "at_target"
    ABOVE_TARGET = "above_target"
    DEGRADED = "degraded"


@dataclass
class TechnicalMetric:
    """
    Technical metric (performance, quality, reliability)
    
    Attributes:
        name: Metric name
        category: Metric category
        baseline: Starting value before refactoring
        current: Current measured value
        target: Target value after refactoring
        unit: Unit of measurement
        timestamp: When metric was collected
        measurement_method: How metric is measured
    """
    name: str
    category: MetricCategory
    baseline: float
    current: float
    target: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    measurement_method: Optional[str] = None
    
    def get_improvement(self) -> float:
        """Calculate improvement percentage"""
        if self.baseline == 0:
            return 0.0
        return ((self.current - self.baseline) / self.baseline) * 100
    
    def get_target_achievement(self) -> float:
        """Calculate percentage of target achieved"""
        if self.target == self.baseline:
            return 100.0 if self.current == self.target else 0.0
        
        progress = (self.current - self.baseline) / (self.target - self.baseline)
        return min(max(progress * 100, 0.0), 100.0)
    
    def get_status(self) -> MetricStatus:
        """Determine if metric is on target"""
        # For "lower is better" metrics (response time, errors)
        if "time" in self.name.lower() or "error" in self.name.lower():
            if self.current <= self.target:
                return MetricStatus.AT_TARGET
            elif self.current > self.baseline:
                return MetricStatus.DEGRADED
            else:
                return MetricStatus.BELOW_TARGET
        
        # For "higher is better" metrics (throughput, coverage)
        else:
            if self.current >= self.target:
                return MetricStatus.ABOVE_TARGET
            elif self.current < self.baseline:
                return MetricStatus.DEGRADED
            else:
                return MetricStatus.BELOW_TARGET


@dataclass
class BusinessMetric:
    """
    Business metric (user satisfaction, velocity, costs)
    
    Attributes:
        name: Metric name
        baseline: Starting value
        current: Current value
        target: Target value
        unit: Unit of measurement
        annual_value: Financial value per year (if applicable)
        timestamp: When metric was collected
    """
    name: str
    baseline: float
    current: float
    target: float
    unit: str
    annual_value: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def get_improvement(self) -> float:
        """Calculate improvement percentage"""
        if self.baseline == 0:
            return 0.0
        return ((self.current - self.baseline) / self.baseline) * 100
    
    def get_status(self) -> MetricStatus:
        """Determine if metric meets target"""
        if self.current >= self.target:
            return MetricStatus.AT_TARGET
        elif self.current >= self.baseline:
            return MetricStatus.BELOW_TARGET
        else:
            return MetricStatus.DEGRADED


@dataclass
class MetricSnapshot:
    """
    Point-in-time snapshot of all metrics
    
    Attributes:
        timestamp: When snapshot was taken
        technical_metrics: Dict of technical metrics
        business_metrics: Dict of business metrics
        notes: Optional notes about this snapshot
    """
    timestamp: datetime
    technical_metrics: Dict[str, TechnicalMetric]
    business_metrics: Dict[str, BusinessMetric]
    notes: Optional[str] = None


class MetricsCollector:
    """
    Collect and track metrics throughout refactoring
    
    Example:
        collector = MetricsCollector()
        
        # Collect technical metrics
        collector.collect_technical_metric(
            "response_time",
            category="performance",
            baseline=5.2,
            current=0.48,
            target=0.5,
            unit="seconds"
        )
        
        collector.collect_technical_metric(
            "test_coverage",
            category="quality",
            baseline=40.0,
            current=75.0,
            target=90.0,
            unit="percent"
        )
        
        # Collect business metrics
        collector.collect_business_metric(
            "user_satisfaction",
            baseline=7.2,
            current=8.3,
            target=8.5,
            unit="NPS",
            annual_value=50000
        )
        
        # Generate report
        report = collector.generate_report()
        print(report)
    """
    
    def __init__(self):
        self.technical_metrics: Dict[str, TechnicalMetric] = {}
        self.business_metrics: Dict[str, BusinessMetric] = {}
        self.snapshots: List[MetricSnapshot] = []
    
    def collect_technical_metric(self, name: str, category: str,
                                 baseline: float, current: float, target: float,
                                 unit: str, measurement_method: Optional[str] = None):
        """
        Collect a technical metric
        
        Args:
            name: Metric name (e.g., "response_time")
            category: Category (performance, quality, reliability)
            baseline: Starting value
            current: Current value
            target: Target value
            unit: Unit (e.g., "seconds", "percent")
            measurement_method: How metric is measured
        """
        metric = TechnicalMetric(
            name=name,
            category=MetricCategory(category),
            baseline=baseline,
            current=current,
            target=target,
            unit=unit,
            measurement_method=measurement_method
        )
        self.technical_metrics[name] = metric
    
    def collect_business_metric(self, name: str, baseline: float, current: float,
                                target: float, unit: str, annual_value: Optional[float] = None):
        """
        Collect a business metric
        
        Args:
            name: Metric name (e.g., "user_satisfaction")
            baseline: Starting value
            current: Current value
            target: Target value
            unit: Unit (e.g., "NPS", "features/month")
            annual_value: Annual financial value (optional)
        """
        metric = BusinessMetric(
            name=name,
            baseline=baseline,
            current=current,
            target=target,
            unit=unit,
            annual_value=annual_value
        )
        self.business_metrics[name] = metric
    
    def update_metric(self, name: str, current: float):
        """Update current value of a metric"""
        if name in self.technical_metrics:
            self.technical_metrics[name].current = current
            self.technical_metrics[name].timestamp = datetime.now()
        elif name in self.business_metrics:
            self.business_metrics[name].current = current
            self.business_metrics[name].timestamp = datetime.now()
        else:
            raise ValueError(f"Metric '{name}' not found")
    
    def take_snapshot(self, notes: Optional[str] = None):
        """Take a snapshot of all current metrics"""
        snapshot = MetricSnapshot(
            timestamp=datetime.now(),
            technical_metrics=self.technical_metrics.copy(),
            business_metrics=self.business_metrics.copy(),
            notes=notes
        )
        self.snapshots.append(snapshot)
    
    def get_metrics_by_category(self, category: str) -> List[TechnicalMetric]:
        """Get all metrics in a category"""
        return [
            m for m in self.technical_metrics.values()
            if m.category == MetricCategory(category)
        ]
    
    def get_degraded_metrics(self) -> List[TechnicalMetric]:
        """Get metrics that have degraded below baseline"""
        return [
            m for m in self.technical_metrics.values()
            if m.get_status() == MetricStatus.DEGRADED
        ]
    
    def get_achieved_targets(self) -> List[TechnicalMetric]:
        """Get metrics that have achieved target"""
        return [
            m for m in self.technical_metrics.values()
            if m.get_status() in [MetricStatus.AT_TARGET, MetricStatus.ABOVE_TARGET]
        ]
    
    def calculate_total_annual_value(self) -> float:
        """Calculate total annual value from business metrics"""
        return sum(
            m.annual_value for m in self.business_metrics.values()
            if m.annual_value is not None
        )
    
    def generate_report(self) -> str:
        """
        Generate comprehensive metrics report
        
        Returns:
            Formatted text report
        """
        lines = []
        lines.append("=" * 80)
        lines.append("METRICS REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Technical metrics by category
        for cat in MetricCategory:
            if cat == MetricCategory.BUSINESS:
                continue
            
            metrics = self.get_metrics_by_category(cat.value)
            if not metrics:
                continue
            
            lines.append(f"{cat.value.upper()} METRICS:")
            lines.append("-" * 80)
            
            for metric in metrics:
                improvement = metric.get_improvement()
                achievement = metric.get_target_achievement()
                status = metric.get_status()
                
                status_icon = {
                    MetricStatus.AT_TARGET: "?",
                    MetricStatus.ABOVE_TARGET: "?",
                    MetricStatus.BELOW_TARGET: "?",
                    MetricStatus.DEGRADED: "?"
                }[status]
                
                lines.append(f"{status_icon} {metric.name}")
                lines.append(f"  Baseline: {metric.baseline:.2f} {metric.unit}")
                lines.append(f"  Current:  {metric.current:.2f} {metric.unit}")
                lines.append(f"  Target:   {metric.target:.2f} {metric.unit}")
                lines.append(f"  Improvement: {improvement:+.1f}%")
                lines.append(f"  Target Achievement: {achievement:.1f}%")
                if metric.measurement_method:
                    lines.append(f"  Method: {metric.measurement_method}")
                lines.append("")
            
            lines.append("")
        
        # Business metrics
        if self.business_metrics:
            lines.append("BUSINESS METRICS:")
            lines.append("-" * 80)
            
            for metric in self.business_metrics.values():
                improvement = metric.get_improvement()
                status = metric.get_status()
                
                status_icon = "?" if status == MetricStatus.AT_TARGET else "?"
                
                lines.append(f"{status_icon} {metric.name}")
                lines.append(f"  Baseline: {metric.baseline:.2f} {metric.unit}")
                lines.append(f"  Current:  {metric.current:.2f} {metric.unit}")
                lines.append(f"  Target:   {metric.target:.2f} {metric.unit}")
                lines.append(f"  Improvement: {improvement:+.1f}%")
                if metric.annual_value:
                    lines.append(f"  Annual Value: ${metric.annual_value:,.0f}")
                lines.append("")
            
            total_value = self.calculate_total_annual_value()
            lines.append(f"Total Annual Value: ${total_value:,.0f}")
            lines.append("")
        
        # Summary
        lines.append("SUMMARY:")
        lines.append("-" * 80)
        total_tech = len(self.technical_metrics)
        achieved = len(self.get_achieved_targets())
        degraded = len(self.get_degraded_metrics())
        
        lines.append(f"Technical Metrics: {total_tech}")
        lines.append(f"  Targets Achieved: {achieved}/{total_tech} ({achieved/total_tech*100:.1f}%)")
        lines.append(f"  Degraded: {degraded}")
        lines.append(f"Business Metrics: {len(self.business_metrics)}")
        lines.append("")
        
        lines.append("=" * 80)
        return "\n".join(lines)


def collect_system_metrics() -> Dict[str, float]:
    """
    Collect current system metrics
    
    Returns:
        Dict of metric name to value
    
    Note: This is a stub that returns mock data. In production, integrate with
    actual monitoring tools (Prometheus, DataDog, etc.)
    """
    import random
    
    return {
        'cpu_percent': random.uniform(20, 60),
        'memory_percent': random.uniform(40, 70),
        'disk_usage_percent': random.uniform(50, 80),
        'cache_hit_ratio': random.uniform(0.6, 0.9),
        'request_count': random.randint(100, 500),
        'error_count': random.randint(0, 10),
        'active_connections': random.randint(10, 50),
    }


def generate_metrics_report(collector: MetricsCollector) -> str:
    """
    Generate metrics report
    
    Args:
        collector: MetricsCollector instance
    
    Returns:
        Formatted report string
    """
    return collector.generate_report()
