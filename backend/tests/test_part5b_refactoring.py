"""
Tests for Refactoring Tools (Part 5B)

Tests dependency analysis, migration sequencing, and rollback management.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

from refactoring.dependency_analyzer import (
    DependencyGraph,
    analyze_dependencies,
    find_circular_dependencies,
    get_migration_order,
    suggest_refactoring_order,
    visualize_dependencies
)

from refactoring.migration_sequencer import (
    MigrationStep,
    MigrationPlan,
    MigrationStatus,
    create_migration_plan,
    execute_migration_step,
    execute_migration_plan,
    generate_migration_report
)

from refactoring.rollback_manager import (
    RollbackPoint,
    create_rollback_point,
    rollback_to_point,
    list_rollback_points,
    delete_rollback_point,
    cleanup_old_rollback_points,
    get_rollback_disk_usage
)


class TestDependencyGraph:
    """Test dependency graph functionality"""
    
    def test_add_dependency(self):
        """Test adding dependencies"""
        graph = DependencyGraph()
        graph.add_dependency("module_a", "module_b")
        
        assert "module_a" in graph.modules
        assert "module_b" in graph.modules
        assert "module_b" in graph.get_dependencies("module_a")
        assert "module_a" in graph.get_dependents("module_b")
    
    def test_get_all_dependencies(self):
        """Test transitive dependencies"""
        graph = DependencyGraph()
        graph.add_dependency("a", "b")
        graph.add_dependency("b", "c")
        graph.add_dependency("c", "d")
        
        all_deps = graph.get_all_dependencies("a")
        
        assert all_deps == {"b", "c", "d"}
    
    def test_circular_dependency_detection(self):
        """Test detecting circular dependencies"""
        graph = DependencyGraph()
        graph.add_dependency("a", "b")
        graph.add_dependency("b", "c")
        graph.add_dependency("c", "a")  # Creates cycle
        
        graph.circular = find_circular_dependencies(graph)
        
        assert len(graph.circular) > 0
        assert graph.has_circular_dependency("a")
        assert graph.has_circular_dependency("b")
        assert graph.has_circular_dependency("c")
    
    def test_no_circular_dependencies(self):
        """Test graph without cycles"""
        graph = DependencyGraph()
        graph.add_dependency("a", "b")
        graph.add_dependency("b", "c")
        graph.add_dependency("d", "c")
        
        graph.circular = find_circular_dependencies(graph)
        
        assert len(graph.circular) == 0
    
    def test_string_representation(self):
        """Test string output"""
        graph = DependencyGraph()
        graph.add_dependency("a", "b")
        
        output = str(graph)
        
        assert "Modules: 2" in output
        assert "Dependencies:" in output


class TestDependencyAnalysis:
    """Test dependency analysis on real files"""
    
    def test_analyze_dependencies_basic(self, tmp_path):
        """Test basic dependency analysis"""
        # Create test files
        (tmp_path / "backend").mkdir()
        (tmp_path / "backend" / "module_a.py").write_text(
            "from module_b import func\n"
        )
        (tmp_path / "backend" / "module_b.py").write_text(
            "def func(): pass\n"
        )
        
        graph = analyze_dependencies(str(tmp_path / "backend"), "backend")
        
        assert "backend.module_a" in graph.modules
        assert "backend.module_b" in graph.modules
        assert "backend.module_b" in graph.get_dependencies("backend.module_a")
    
    def test_get_migration_order(self):
        """Test topological sort for migration order"""
        graph = DependencyGraph()
        graph.add_dependency("app", "utils")
        graph.add_dependency("utils", "base")
        graph.add_dependency("app", "base")
        
        order = get_migration_order(graph)
        
        # base should come before utils and app
        assert order.index("base") < order.index("utils")
        assert order.index("base") < order.index("app")
        assert order.index("utils") < order.index("app")
    
    def test_migration_order_with_circular(self):
        """Test that circular dependencies raise error"""
        graph = DependencyGraph()
        graph.add_dependency("a", "b")
        graph.add_dependency("b", "c")
        graph.add_dependency("c", "a")
        
        with pytest.raises(ValueError, match="circular"):
            get_migration_order(graph)
    
    def test_suggest_refactoring_order(self, tmp_path):
        """Test refactoring suggestions"""
        # Create test structure
        (tmp_path / "backend").mkdir()
        (tmp_path / "backend" / "base.py").write_text("# Base module\n")
        (tmp_path / "backend" / "app.py").write_text("from base import x\n")
        
        suggestions = suggest_refactoring_order(str(tmp_path / "backend"))
        
        assert len(suggestions) > 0
        assert all(isinstance(s, tuple) and len(s) == 2 for s in suggestions)
    
    def test_visualize_dependencies_mermaid(self):
        """Test Mermaid diagram generation"""
        graph = DependencyGraph()
        graph.add_dependency("a", "b")
        graph.add_dependency("b", "c")
        
        mermaid = visualize_dependencies(graph, "mermaid")
        
        assert "graph TD" in mermaid
        assert "a" in mermaid
        assert "b" in mermaid
        assert "c" in mermaid
    
    def test_visualize_dependencies_dot(self):
        """Test DOT diagram generation"""
        graph = DependencyGraph()
        graph.add_dependency("a", "b")
        
        dot = visualize_dependencies(graph, "dot")
        
        assert "digraph dependencies" in dot
        assert '"a" -> "b"' in dot


class TestMigrationStep:
    """Test migration step functionality"""
    
    def test_migration_step_creation(self):
        """Test creating a migration step"""
        step = MigrationStep(
            id="test_step",
            name="Test Step",
            description="A test step",
            risk_level="low"
        )
        
        assert step.id == "test_step"
        assert step.status == MigrationStatus.PENDING
        assert step.can_execute(set())
    
    def test_step_with_dependencies(self):
        """Test step dependency checking"""
        step = MigrationStep(
            id="step2",
            name="Step 2",
            description="Depends on step1",
            dependencies=["step1"]
        )
        
        assert not step.can_execute(set())
        assert step.can_execute({"step1"})
    
    def test_step_duration_calculation(self):
        """Test duration calculation"""
        step = MigrationStep(
            id="timed_step",
            name="Timed Step",
            description="Test timing"
        )
        
        step.started_at = datetime.now()
        step.completed_at = step.started_at + timedelta(minutes=5)
        
        duration = step.duration_minutes()
        
        assert duration is not None
        assert 4.9 < duration < 5.1  # Allow small margin


class TestMigrationPlan:
    """Test migration plan functionality"""
    
    def test_create_migration_plan(self):
        """Test plan creation"""
        plan = create_migration_plan(
            "Test Plan",
            "A test migration plan"
        )
        
        assert plan.name == "Test Plan"
        assert len(plan.steps) == 0
    
    def test_add_steps_to_plan(self):
        """Test adding steps"""
        plan = create_migration_plan("Test", "Test plan")
        
        plan.add_step(MigrationStep(
            id="step1",
            name="Step 1",
            description="First step"
        ))
        
        plan.add_step(MigrationStep(
            id="step2",
            name="Step 2",
            description="Second step",
            dependencies=["step1"]
        ))
        
        assert len(plan.steps) == 2
        assert plan.get_step("step1") is not None
    
    def test_get_executable_steps(self):
        """Test finding ready-to-execute steps"""
        plan = create_migration_plan("Test", "Test")
        
        step1 = MigrationStep(id="step1", name="Step 1", description="First")
        step2 = MigrationStep(
            id="step2",
            name="Step 2",
            description="Second",
            dependencies=["step1"]
        )
        
        plan.add_step(step1)
        plan.add_step(step2)
        
        # Initially only step1 is executable
        executable = plan.get_executable_steps()
        assert len(executable) == 1
        assert executable[0].id == "step1"
        
        # After completing step1, step2 becomes executable
        step1.status = MigrationStatus.COMPLETED
        executable = plan.get_executable_steps()
        assert len(executable) == 1
        assert executable[0].id == "step2"
    
    def test_get_progress(self):
        """Test progress calculation"""
        plan = create_migration_plan("Test", "Test")
        
        plan.add_step(MigrationStep(id="s1", name="S1", description="1"))
        plan.add_step(MigrationStep(id="s2", name="S2", description="2"))
        plan.add_step(MigrationStep(id="s3", name="S3", description="3"))
        
        plan.steps[0].status = MigrationStatus.COMPLETED
        plan.steps[1].status = MigrationStatus.FAILED
        
        progress = plan.get_progress()
        
        assert progress['total'] == 3
        assert progress['completed'] == 1
        assert progress['failed'] == 1
        assert progress['pending'] == 1
        assert progress['completion_percentage'] == pytest.approx(33.33, rel=0.1)


class TestMigrationExecution:
    """Test migration execution"""
    
    def test_execute_successful_step(self):
        """Test executing a successful step"""
        executed = []
        
        def execute_func():
            executed.append(True)
            return True
        
        def validate_func():
            return True
        
        step = MigrationStep(
            id="test",
            name="Test",
            description="Test",
            execute=execute_func,
            validate=validate_func
        )
        
        success = execute_migration_step(step)
        
        assert success
        assert step.status == MigrationStatus.COMPLETED
        assert len(executed) == 1
    
    def test_execute_failed_step(self):
        """Test executing a failed step"""
        def execute_func():
            raise Exception("Intentional failure")
        
        step = MigrationStep(
            id="test",
            name="Test",
            description="Test",
            execute=execute_func
        )
        
        success = execute_migration_step(step)
        
        assert not success
        assert step.status == MigrationStatus.FAILED
        assert step.error is not None
    
    def test_execute_step_with_rollback(self):
        """Test step rollback on failure"""
        rolled_back = []
        
        def execute_func():
            raise Exception("Failure")
        
        def rollback_func():
            rolled_back.append(True)
            return True
        
        step = MigrationStep(
            id="test",
            name="Test",
            description="Test",
            execute=execute_func,
            rollback=rollback_func
        )
        
        success = execute_migration_step(step)
        
        assert not success
        assert step.status == MigrationStatus.ROLLED_BACK
        assert len(rolled_back) == 1
    
    def test_dry_run_execution(self):
        """Test dry run mode"""
        executed = []
        
        def execute_func():
            executed.append(True)
            return True
        
        step = MigrationStep(
            id="test",
            name="Test",
            description="Test",
            execute=execute_func
        )
        
        success = execute_migration_step(step, dry_run=True)
        
        assert success
        assert len(executed) == 0  # Should not execute in dry run
    
    def test_execute_migration_plan(self):
        """Test executing a complete plan"""
        plan = create_migration_plan("Test", "Test")
        
        executed_order = []
        
        def make_execute(step_id):
            def execute():
                executed_order.append(step_id)
                return True
            return execute
        
        plan.add_step(MigrationStep(
            id="step1",
            name="Step 1",
            description="First",
            execute=make_execute("step1")
        ))
        
        plan.add_step(MigrationStep(
            id="step2",
            name="Step 2",
            description="Second",
            dependencies=["step1"],
            execute=make_execute("step2")
        ))
        
        results = execute_migration_plan(plan)
        
        assert results['success']
        assert results['completed'] == 2
        assert results['failed'] == 0
        assert executed_order == ["step1", "step2"]
    
    def test_generate_migration_report(self):
        """Test report generation"""
        plan = create_migration_plan("Test Plan", "Test")
        
        plan.add_step(MigrationStep(
            id="s1",
            name="Step 1",
            description="First"
        ))
        
        plan.steps[0].status = MigrationStatus.COMPLETED
        
        report = generate_migration_report(plan)
        
        assert "Test Plan" in report
        assert "Step 1" in report
        assert "completed" in report.lower()


class TestRollbackManager:
    """Test rollback functionality"""
    
    def test_create_rollback_point(self, tmp_path):
        """Test creating a rollback point"""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("original content")
        
        rollback_dir = tmp_path / ".rollback"
        
        point = create_rollback_point(
            "test_backup",
            "Test backup",
            [str(test_file)],
            rollback_dir=str(rollback_dir)
        )
        
        assert point.name == "test_backup"
        assert len(point.files) == 1
        assert str(test_file) in point.files
    
    def test_rollback_to_point(self, tmp_path):
        """Test restoring from rollback point"""
        # Create and backup original file
        test_file = tmp_path / "test.txt"
        test_file.write_text("original")
        
        rollback_dir = tmp_path / ".rollback"
        point = create_rollback_point(
            "backup",
            "Backup",
            [str(test_file)],
            rollback_dir=str(rollback_dir)
        )
        
        # Modify file
        test_file.write_text("modified")
        assert test_file.read_text() == "modified"
        
        # Rollback
        success = rollback_to_point(point, confirm=False)
        
        assert success
        assert test_file.read_text() == "original"
    
    def test_list_rollback_points(self, tmp_path):
        """Test listing rollback points"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        rollback_dir = tmp_path / ".rollback"
        
        # Create multiple points
        point1 = create_rollback_point(
            "backup1",
            "First backup",
            [str(test_file)],
            rollback_dir=str(rollback_dir)
        )
        
        point2 = create_rollback_point(
            "backup2",
            "Second backup",
            [str(test_file)],
            rollback_dir=str(rollback_dir)
        )
        
        # List points
        points = list_rollback_points(rollback_dir=str(rollback_dir))
        
        assert len(points) == 2
        # Should be sorted newest first
        assert points[0].id == point2.id
        assert points[1].id == point1.id
    
    def test_delete_rollback_point(self, tmp_path):
        """Test deleting a rollback point"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        rollback_dir = tmp_path / ".rollback"
        
        point = create_rollback_point(
            "backup",
            "Backup",
            [str(test_file)],
            rollback_dir=str(rollback_dir)
        )
        
        # Delete point
        success = delete_rollback_point(point, rollback_dir=str(rollback_dir))
        
        assert success
        
        # Verify deleted
        points = list_rollback_points(rollback_dir=str(rollback_dir))
        assert len(points) == 0
    
    def test_cleanup_old_rollback_points(self, tmp_path):
        """Test cleaning up old rollback points"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        rollback_dir = tmp_path / ".rollback"
        
        # Create 15 rollback points
        for i in range(15):
            create_rollback_point(
                f"backup{i}",
                f"Backup {i}",
                [str(test_file)],
                rollback_dir=str(rollback_dir)
            )
        
        # Keep only 10
        deleted = cleanup_old_rollback_points(
            rollback_dir=str(rollback_dir),
            keep_count=10
        )
        
        assert deleted == 5
        
        # Verify only 10 remain
        points = list_rollback_points(rollback_dir=str(rollback_dir))
        assert len(points) == 10
    
    def test_get_rollback_disk_usage(self, tmp_path):
        """Test disk usage calculation"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content" * 1000)  # Some content
        
        rollback_dir = tmp_path / ".rollback"
        
        create_rollback_point(
            "backup",
            "Backup",
            [str(test_file)],
            rollback_dir=str(rollback_dir)
        )
        
        usage = get_rollback_disk_usage(rollback_dir=str(rollback_dir))
        
        assert usage['total_bytes'] > 0
        assert usage['total_mb'] > 0
        assert usage['point_count'] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
