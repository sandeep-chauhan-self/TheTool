"""
Part 5C: Final Roadmap & Project Management Tools

This package provides comprehensive project management, tracking, and reporting tools
for managing large-scale refactoring projects.

Components:
- Progress Tracker: Monitor refactoring progress across all phases
- Metrics Collector: Gather technical and business KPIs
- ROI Calculator: Calculate business value and investment returns
- Dependency Visualizer: Generate dependency graphs and reports
- Health Monitor: Track system health and performance

Usage:
    from backend.project_management import (
        ProgressTracker,
        MetricsCollector,
        ROICalculator,
        DependencyVisualizer,
        HealthMonitor
    )
    
    # Track progress
    tracker = ProgressTracker()
    tracker.add_task("Phase 1", "Foundation", status="completed")
    progress = tracker.get_overall_progress()
    
    # Calculate ROI
    roi_calc = ROICalculator()
    roi_calc.set_investment(122500)
    roi_calc.add_benefit("Performance", 50000)
    report = roi_calc.generate_report()
"""

from backend.project_management.progress_tracker import (
    ProgressTracker,
    Task,
    Phase,
    Milestone,
    get_project_status,
    calculate_phase_progress,
)

from backend.project_management.metrics_collector import (
    MetricsCollector,
    TechnicalMetric,
    BusinessMetric,
    MetricSnapshot,
    collect_system_metrics,
    generate_metrics_report,
)

from backend.project_management.roi_calculator import (
    ROICalculator,
    Investment,
    Benefit,
    ROIReport,
    calculate_payback_period,
    calculate_roi_percentage,
)

from backend.project_management.dependency_visualizer import (
    DependencyVisualizer,
    visualize_dependencies,
    generate_dependency_report,
    check_circular_dependencies,
)

from backend.project_management.health_monitor import (
    HealthMonitor,
    HealthCheck,
    HealthStatus,
    monitor_system_health,
    generate_health_report,
)

__all__ = [
    # Progress Tracking
    'ProgressTracker',
    'Task',
    'Phase',
    'Milestone',
    'get_project_status',
    'calculate_phase_progress',
    
    # Metrics Collection
    'MetricsCollector',
    'TechnicalMetric',
    'BusinessMetric',
    'MetricSnapshot',
    'collect_system_metrics',
    'generate_metrics_report',
    
    # ROI Calculation
    'ROICalculator',
    'Investment',
    'Benefit',
    'ROIReport',
    'calculate_payback_period',
    'calculate_roi_percentage',
    
    # Dependency Visualization
    'DependencyVisualizer',
    'visualize_dependencies',
    'generate_dependency_report',
    'check_circular_dependencies',
    
    # Health Monitoring
    'HealthMonitor',
    'HealthCheck',
    'HealthStatus',
    'monitor_system_health',
    'generate_health_report',
]
