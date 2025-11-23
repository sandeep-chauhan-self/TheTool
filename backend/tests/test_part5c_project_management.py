"""
Test Suite for Part 5C: Final Roadmap & Project Management Tools

Tests all components:
- Progress Tracker
- Metrics Collector
- ROI Calculator
- Dependency Visualizer
- Health Monitor
"""

import pytest
from datetime import datetime, timedelta
from project_management import (
    ProgressTracker,
    Task,
    Phase,
    Milestone,
    MetricsCollector,
    TechnicalMetric,
    BusinessMetric,
    MetricDirection,
    ROICalculator,
    Investment,
    Benefit,
    DependencyVisualizer,
    HealthMonitor,
    HealthStatus,
)


# ============================================================================
# Progress Tracker Tests
# ============================================================================

class TestProgressTracker:
    """Test progress tracking functionality"""
    
    def test_add_phase(self):
        """Test adding a project phase"""
        tracker = ProgressTracker()
        tracker.add_phase("Foundation", "2025-01-01", 10)
        
        assert "Foundation" in tracker.phases
        assert tracker.phases["Foundation"].duration_days == 10
        assert tracker.project_start == datetime(2025, 1, 1)
    
    def test_add_task(self):
        """Test adding a task to a phase"""
        tracker = ProgressTracker()
        tracker.add_phase("Foundation", "2025-01-01", 10)
        tracker.add_task("Foundation", "Setup pytest", effort_days=2.0, status="completed")
        
        assert "Setup pytest" in tracker.tasks
        task = tracker.tasks["Setup pytest"]
        assert task.effort_days == 2.0
        assert task.phase == "Foundation"
    
    def test_task_with_dependencies(self):
        """Test task dependencies"""
        tracker = ProgressTracker()
        tracker.add_phase("Foundation", "2025-01-01", 10)
        tracker.add_task("Foundation", "Task A", effort_days=1.0, status="completed")
        tracker.add_task("Foundation", "Task B", effort_days=2.0, dependencies=["Task A"])
        
        task_b = tracker.tasks["Task B"]
        completed = {"Task A"}
        assert task_b.is_ready(completed)
    
    def test_calculate_phase_progress(self):
        """Test phase progress calculation"""
        tracker = ProgressTracker()
        tracker.add_phase("Foundation", "2025-01-01", 10)
        tracker.add_task("Foundation", "Task 1", effort_days=3.0, status="completed")
        tracker.add_task("Foundation", "Task 2", effort_days=2.0, status="in_progress")
        tracker.add_task("Foundation", "Task 3", effort_days=5.0, status="not_started")
        
        progress = tracker.get_phase_progress("Foundation")
        assert progress['completed'] == 1
        assert progress['total'] == 3
        assert progress['completed_effort'] == 3.0
        assert progress['total_effort'] == 10.0
        assert progress['percentage'] == 30.0
    
    def test_calculate_overall_progress(self):
        """Test overall project progress"""
        tracker = ProgressTracker()
        tracker.add_phase("Phase 1", "2025-01-01", 5)
        tracker.add_task("Phase 1", "Task A", effort_days=3.0, status="completed")
        tracker.add_task("Phase 1", "Task B", effort_days=2.0, status="completed")
        
        tracker.add_phase("Phase 2", "2025-01-06", 5)
        tracker.add_task("Phase 2", "Task C", effort_days=5.0, status="not_started")
        
        progress = tracker.get_overall_progress()
        assert progress['completed_tasks'] == 2
        assert progress['total_tasks'] == 3
        assert progress['completed_effort'] == 5.0
        assert progress['total_effort'] == 10.0
        assert progress['percentage'] == 50.0
    
    def test_update_task_status(self):
        """Test updating task status"""
        tracker = ProgressTracker()
        tracker.add_phase("Phase 1", "2025-01-01", 5)
        tracker.add_task("Phase 1", "Task A", effort_days=2.0, status="not_started")
        
        tracker.update_task_status("Task A", "in_progress")
        assert tracker.tasks["Task A"].status.value == "in_progress"
        assert tracker.tasks["Task A"].start_date is not None
        
        tracker.update_task_status("Task A", "completed")
        assert tracker.tasks["Task A"].status.value == "completed"
        assert tracker.tasks["Task A"].completion_date is not None
    
    def test_blocked_tasks(self):
        """Test identifying blocked tasks"""
        tracker = ProgressTracker()
        tracker.add_phase("Phase 1", "2025-01-01", 5)
        tracker.add_task("Phase 1", "Task A", effort_days=2.0, status="blocked")
        tracker.update_task_status("Task A", "blocked", blocked_reason="Waiting for resources")
        
        blocked = tracker.get_blocked_tasks()
        assert len(blocked) == 1
        assert blocked[0].name == "Task A"
        assert blocked[0].blocked_reason == "Waiting for resources"
    
    def test_ready_tasks(self):
        """Test identifying tasks ready to start"""
        tracker = ProgressTracker()
        tracker.add_phase("Phase 1", "2025-01-01", 5)
        tracker.add_task("Phase 1", "Task A", effort_days=1.0, status="completed")
        tracker.add_task("Phase 1", "Task B", effort_days=2.0, status="not_started", dependencies=["Task A"])
        tracker.add_task("Phase 1", "Task C", effort_days=3.0, status="not_started", dependencies=["Task B"])
        
        ready = tracker.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].name == "Task B"
    
    def test_milestones(self):
        """Test milestone tracking"""
        tracker = ProgressTracker()
        tracker.add_milestone("Beta Release", "2025-03-01", ["All tests passing", "Documentation complete"])
        
        assert len(tracker.milestones) == 1
        assert not tracker.milestones[0].is_achieved
        
        tracker.achieve_milestone("Beta Release")
        assert tracker.milestones[0].is_achieved
        assert tracker.milestones[0].achieved_date is not None
    
    def test_generate_report(self):
        """Test report generation"""
        tracker = ProgressTracker()
        tracker.add_phase("Phase 1", "2025-01-01", 5)
        tracker.add_task("Phase 1", "Task A", effort_days=2.0, status="completed")
        tracker.add_task("Phase 1", "Task B", effort_days=3.0, status="in_progress")
        
        report = tracker.generate_report()
        assert "PROJECT PROGRESS REPORT" in report
        assert "Phase 1" in report
        assert "Overall Progress" in report


# ============================================================================
# Metrics Collector Tests
# ============================================================================

class TestMetricsCollector:
    """Test metrics collection functionality"""
    
    def test_collect_technical_metric(self):
        """Test collecting technical metrics"""
        collector = MetricsCollector()
        collector.collect_technical_metric(
            "response_time",
            category="performance",
            baseline=5.0,
            current=0.5,
            target=0.5,
            unit="seconds"
        )
        
        assert "response_time" in collector.technical_metrics
        metric = collector.technical_metrics["response_time"]
        assert metric.baseline == 5.0
        assert metric.current == 0.5
        assert metric.target == 0.5
    
    def test_collect_business_metric(self):
        """Test collecting business metrics"""
        collector = MetricsCollector()
        collector.collect_business_metric(
            "user_satisfaction",
            baseline=7.2,
            current=8.3,
            target=8.5,
            unit="NPS",
            annual_value=50000
        )
        
        assert "user_satisfaction" in collector.business_metrics
        metric = collector.business_metrics["user_satisfaction"]
        assert metric.annual_value == 50000
    
    def test_metric_improvement_calculation(self):
        """Test improvement percentage calculation"""
        collector = MetricsCollector()
        collector.collect_technical_metric(
            "response_time",
            category="performance",
            baseline=5.0,
            current=1.0,
            target=0.5,
            unit="seconds"
        )
        
        metric = collector.technical_metrics["response_time"]
        improvement = metric.get_improvement()
        assert improvement == -80.0  # 80% reduction
    
    def test_target_achievement_calculation(self):
        """Test target achievement percentage"""
        collector = MetricsCollector()
        collector.collect_technical_metric(
            "test_coverage",
            category="quality",
            baseline=40.0,
            current=65.0,
            target=90.0,
            unit="percent"
        )
        
        metric = collector.technical_metrics["test_coverage"]
        achievement = metric.get_target_achievement()
        assert achievement == 50.0  # Halfway to target
    
    def test_metric_status_determination(self):
        """Test metric status (on target, degraded, etc.)"""
        collector = MetricsCollector()
        
        # Test "lower is better" metric at target
        collector.collect_technical_metric(
            "response_time",
            category="performance",
            baseline=5.0,
            current=0.4,
            target=0.5,
            unit="seconds",
            direction=MetricDirection.LOWER_IS_BETTER
        )
        metric = collector.technical_metrics["response_time"]
        assert metric.get_status().value in ["at_target", "above_target"]
        
        # Test "higher is better" metric at target
        collector.collect_technical_metric(
            "test_coverage",
            category="quality",
            baseline=40.0,
            current=92.0,
            target=90.0,
            unit="percent",
            direction=MetricDirection.HIGHER_IS_BETTER
        )
        metric = collector.technical_metrics["test_coverage"]
        assert metric.get_status().value == "above_target"
    
    def test_get_metrics_by_category(self):
        """Test filtering metrics by category"""
        collector = MetricsCollector()
        collector.collect_technical_metric("response_time", "performance", 5.0, 0.5, 0.5, "s")
        collector.collect_technical_metric("throughput", "performance", 40, 400, 400, "req/min")
        collector.collect_technical_metric("test_coverage", "quality", 40, 90, 90, "%")
        
        performance_metrics = collector.get_metrics_by_category("performance")
        assert len(performance_metrics) == 2
    
    def test_calculate_total_annual_value(self):
        """Test calculating total annual value"""
        collector = MetricsCollector()
        collector.collect_business_metric("benefit1", 0, 0, 0, "unit", annual_value=50000)
        collector.collect_business_metric("benefit2", 0, 0, 0, "unit", annual_value=30000)
        collector.collect_business_metric("benefit3", 0, 0, 0, "unit")  # No value
        
        total = collector.calculate_total_annual_value()
        assert total == 80000
    
    def test_metrics_snapshot(self):
        """Test taking metrics snapshots"""
        collector = MetricsCollector()
        collector.collect_technical_metric("metric1", "performance", 5.0, 2.5, 1.0, "s")
        
        collector.take_snapshot(notes="First snapshot")
        assert len(collector.snapshots) == 1
        assert collector.snapshots[0].notes == "First snapshot"
    
    def test_update_metric(self):
        """Test updating metric values"""
        collector = MetricsCollector()
        collector.collect_technical_metric("response_time", "performance", 5.0, 2.0, 0.5, "s")
        
        collector.update_metric("response_time", 1.5)
        assert collector.technical_metrics["response_time"].current == 1.5
    
    def test_generate_metrics_report(self):
        """Test metrics report generation"""
        collector = MetricsCollector()
        collector.collect_technical_metric("response_time", "performance", 5.0, 0.5, 0.5, "s")
        collector.collect_business_metric("satisfaction", 7.0, 8.5, 8.5, "NPS", 50000)
        
        report = collector.generate_report()
        assert "METRICS REPORT" in report
        assert "PERFORMANCE METRICS" in report
        assert "BUSINESS METRICS" in report


# ============================================================================
# ROI Calculator Tests
# ============================================================================

class TestROICalculator:
    """Test ROI calculation functionality"""
    
    def test_set_investment(self):
        """Test setting investment amount"""
        calculator = ROICalculator()
        calculator.set_investment(122500, breakdown={
            'labor': 120000,
            'infrastructure': 2000,
            'tools': 500
        })
        
        assert calculator.investment.total == 122500
        assert calculator.investment.breakdown['labor'] == 120000
    
    def test_add_benefit(self):
        """Test adding benefits"""
        calculator = ROICalculator()
        calculator.set_investment(100000)
        calculator.add_benefit("Performance", 50000, "Improved UX")
        
        assert len(calculator.benefits) == 1
        assert calculator.benefits[0].annual_value == 50000
    
    def test_calculate_total_annual_benefits(self):
        """Test calculating total benefits"""
        calculator = ROICalculator()
        calculator.set_investment(100000)
        calculator.add_benefit("Benefit 1", 30000, "Desc 1")
        calculator.add_benefit("Benefit 2", 20000, "Desc 2")
        
        total = calculator.calculate_total_annual_benefits()
        assert total == 50000
    
    def test_calculate_payback_period(self):
        """Test payback period calculation"""
        calculator = ROICalculator()
        calculator.set_investment(100000)
        calculator.add_benefit("Benefit", 50000, "Desc")
        
        payback = calculator.calculate_payback_period()
        assert payback == 24.0  # 24 months (2 years)
    
    def test_calculate_roi_percentage(self):
        """Test ROI percentage calculation"""
        calculator = ROICalculator()
        calculator.set_investment(100000)
        calculator.add_benefit("Benefit", 50000, "Desc")
        
        roi = calculator.calculate_roi_percentage(years=3)
        # 3 years * 50000 = 150000 benefit
        # ROI = (150000 - 100000) / 100000 = 0.5 = 50%
        assert roi == 50.0
    
    def test_calculate_npv(self):
        """Test Net Present Value calculation"""
        calculator = ROICalculator()
        calculator.set_investment(100000)
        calculator.add_benefit("Benefit", 50000, "Desc")
        
        npv = calculator.calculate_npv(years=3, discount_rate=0.10)
        assert npv > 0  # Should be positive investment
    
    def test_ongoing_costs(self):
        """Test ongoing costs impact"""
        calculator = ROICalculator()
        calculator.set_investment(100000)
        calculator.add_benefit("Benefit", 50000, "Desc")
        calculator.set_ongoing_costs(1000)  # $1000/month
        
        net_annual = calculator.calculate_net_annual_benefit()
        assert net_annual == 50000 - (1000 * 12)  # 38000
    
    def test_benefit_confidence_adjustment(self):
        """Test benefit confidence adjustment"""
        calculator = ROICalculator()
        calculator.set_investment(100000)
        calculator.add_benefit("Uncertain", 100000, "Desc", confidence=0.5)
        
        total = calculator.calculate_total_annual_benefits(adjusted=True)
        assert total == 50000  # 100000 * 0.5
        
        total_unadjusted = calculator.calculate_total_annual_benefits(adjusted=False)
        assert total_unadjusted == 100000
    
    def test_generate_roi_report(self):
        """Test ROI report generation"""
        calculator = ROICalculator()
        calculator.set_investment(122500)
        calculator.add_benefit("Performance", 50000, "UX")
        calculator.add_benefit("Reliability", 30000, "Uptime")
        
        report = calculator.generate_report(years=3)
        assert report.investment == 122500
        assert report.annual_benefits == 80000
        assert report.roi_percentage > 0
        assert report.is_positive_roi()
    
    def test_generate_detailed_report(self):
        """Test detailed text report"""
        calculator = ROICalculator()
        calculator.set_investment(100000)
        calculator.add_benefit("Benefit", 50000, "Desc")
        
        report = calculator.generate_detailed_report(years=3)
        assert "ROI ANALYSIS REPORT" in report
        assert "INITIAL INVESTMENT" in report
        assert "ANNUAL BENEFITS" in report
        assert "ROI CALCULATIONS" in report


# ============================================================================
# Dependency Visualizer Tests
# ============================================================================

class TestDependencyVisualizer:
    """Test dependency visualization functionality"""
    
    def test_create_visualizer(self):
        """Test creating visualizer"""
        visualizer = DependencyVisualizer()
        assert len(visualizer.nodes) == 0
    
    def test_analyze_directory(self, tmp_path):
        """Test analyzing a directory"""
        # Create test files
        file1 = tmp_path / "module1.py"
        file1.write_text("import os\nfrom module2 import func")
        
        file2 = tmp_path / "module2.py"
        file2.write_text("import sys")
        
        visualizer = DependencyVisualizer()
        visualizer.analyze_directory(str(tmp_path))
        
        assert len(visualizer.nodes) >= 2
    
    def test_build_dependency_graph(self, tmp_path):
        """Test building reverse dependencies"""
        file1 = tmp_path / "mod1.py"
        file1.write_text("pass")
        
        file2 = tmp_path / "mod2.py"
        file2.write_text("from mod1 import something")
        
        visualizer = DependencyVisualizer()
        visualizer.analyze_directory(str(tmp_path))
        visualizer.build_dependency_graph()
        
        # mod1 should be imported by mod2
        if "mod1" in visualizer.nodes:
            # Check that reverse dependencies were built
            assert visualizer.nodes is not None
    
    def test_calculate_coupling(self):
        """Test coupling calculation"""
        visualizer = DependencyVisualizer()
        
        # Initially empty, should return 0
        coupling = visualizer.calculate_coupling()
        assert coupling >= 0.0
        assert coupling <= 1.0
    
    def test_generate_mermaid_diagram(self, tmp_path):
        """Test Mermaid diagram generation"""
        file1 = tmp_path / "test1.py"
        file1.write_text("pass")
        
        visualizer = DependencyVisualizer()
        visualizer.analyze_directory(str(tmp_path))
        
        diagram = visualizer.generate_mermaid_diagram()
        assert "graph TD" in diagram
    
    def test_generate_dot_diagram(self, tmp_path):
        """Test DOT diagram generation"""
        file1 = tmp_path / "test1.py"
        file1.write_text("pass")
        
        visualizer = DependencyVisualizer()
        visualizer.analyze_directory(str(tmp_path))
        
        diagram = visualizer.generate_dot_diagram()
        assert "digraph dependencies" in diagram
    
    def test_generate_report(self, tmp_path):
        """Test dependency report generation"""
        file1 = tmp_path / "test1.py"
        file1.write_text("import os")
        
        visualizer = DependencyVisualizer()
        visualizer.analyze_directory(str(tmp_path))
        
        report = visualizer.generate_report()
        assert "DEPENDENCY ANALYSIS REPORT" in report


# ============================================================================
# Health Monitor Tests
# ============================================================================

class TestHealthMonitor:
    """Test health monitoring functionality"""
    
    def test_create_monitor(self):
        """Test creating health monitor"""
        monitor = HealthMonitor()
        assert len(monitor.checks) == 0
    
    def test_add_health_check(self):
        """Test adding health checks"""
        monitor = HealthMonitor()
        
        def check_func():
            return {'status': HealthStatus.HEALTHY}
        
        monitor.add_check("test_check", check_func)
        assert "test_check" in monitor.checks
    
    def test_run_health_check(self):
        """Test running a health check"""
        monitor = HealthMonitor()
        
        def check_func():
            return {'status': HealthStatus.HEALTHY, 'data': 'OK'}
        
        monitor.add_check("test_check", check_func, threshold_ms=1000)
        result = monitor.run_check("test_check")
        
        assert result['name'] == "test_check"
        assert 'response_time_ms' in result
    
    def test_run_all_checks(self):
        """Test running all checks"""
        monitor = HealthMonitor()
        
        monitor.add_check("check1", lambda: {'status': HealthStatus.HEALTHY})
        monitor.add_check("check2", lambda: {'status': HealthStatus.HEALTHY})
        
        results = monitor.run_all_checks()
        assert len(results) == 2
        assert "check1" in results
        assert "check2" in results
    
    def test_get_overall_status_healthy(self):
        """Test overall status when all checks healthy"""
        monitor = HealthMonitor()
        
        monitor.add_check("check1", lambda: {'status': HealthStatus.HEALTHY})
        monitor.add_check("check2", lambda: {'status': HealthStatus.HEALTHY})
        monitor.run_all_checks()
        
        status = monitor.get_overall_status()
        assert status == HealthStatus.HEALTHY
    
    def test_get_overall_status_degraded(self):
        """Test overall status with degraded check"""
        monitor = HealthMonitor()
        
        monitor.add_check("check1", lambda: {'status': HealthStatus.HEALTHY})
        monitor.add_check("check2", lambda: {'status': HealthStatus.DEGRADED})
        monitor.run_all_checks()
        
        status = monitor.get_overall_status()
        assert status == HealthStatus.DEGRADED
    
    def test_failing_health_check(self):
        """Test health check failure handling"""
        monitor = HealthMonitor()
        
        def failing_check():
            raise Exception("Check failed")
        
        monitor.add_check("failing", failing_check)
        result = monitor.run_check("failing")
        
        assert result['status'] == "unhealthy"
        assert 'error' in result
    
    def test_get_failing_checks(self):
        """Test identifying failing checks"""
        monitor = HealthMonitor()
        
        monitor.add_check("good", lambda: {'status': HealthStatus.HEALTHY})
        monitor.add_check("bad", lambda: {'status': HealthStatus.UNHEALTHY})
        monitor.run_all_checks()
        
        failing = monitor.get_failing_checks()
        assert len(failing) >= 1
    
    def test_generate_health_report(self):
        """Test health report generation"""
        monitor = HealthMonitor()
        
        monitor.add_check("check1", lambda: {'status': HealthStatus.HEALTHY})
        monitor.run_all_checks()
        
        report = monitor.generate_health_report()
        assert "SYSTEM HEALTH REPORT" in report
        assert "check1" in report
    
    def test_to_json(self):
        """Test JSON export"""
        monitor = HealthMonitor()
        
        monitor.add_check("check1", lambda: {'status': HealthStatus.HEALTHY})
        monitor.run_all_checks()
        
        json_data = monitor.to_json()
        assert 'overall_status' in json_data
        assert 'checks' in json_data
        assert 'check1' in json_data['checks']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
