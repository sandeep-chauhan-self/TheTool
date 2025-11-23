# -*- coding: utf-8 -*-
"""
Progress Tracker - Monitor refactoring project progress

This module provides tools for tracking tasks, phases, and milestones throughout
a large-scale refactoring project. It enables project managers to:
- Track task completion across multiple phases
- Calculate progress percentages
- Identify blockers and dependencies
- Generate progress reports
- Monitor velocity and estimate completion dates

Usage:
    tracker = ProgressTracker()
    
    # Add phases and tasks
    tracker.add_phase("Foundation", start_date="2025-01-01", duration_days=10)
    tracker.add_task("Foundation", "Setup pytest", effort_days=2, status="completed")
    tracker.add_task("Foundation", "Write tests", effort_days=5, status="in_progress")
    
    # Track progress
    progress = tracker.get_overall_progress()
    print(f"Overall: {progress['percentage']:.1f}% complete")
    
    # Generate report
    report = tracker.generate_report()
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Literal
from enum import Enum


class TaskStatus(Enum):
    """Task completion status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Task:
    """
    Represents a single task in the refactoring project
    
    Attributes:
        name: Task name
        phase: Which phase this task belongs to
        effort_days: Estimated effort in person-days
        status: Current status
        priority: Task priority
        assignee: Person assigned to task
        dependencies: List of task names that must complete first
        start_date: When task started
        completion_date: When task was completed
        blocked_reason: Why task is blocked (if status=blocked)
    """
    name: str
    phase: str
    effort_days: float
    status: TaskStatus = TaskStatus.NOT_STARTED
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    start_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    blocked_reason: Optional[str] = None
    
    def is_ready(self, completed_tasks: set) -> bool:
        """Check if task is ready to start (all dependencies completed)"""
        return all(dep in completed_tasks for dep in self.dependencies)
    
    def complete(self):
        """Mark task as completed"""
        self.status = TaskStatus.COMPLETED
        self.completion_date = datetime.now()
    
    def block(self, reason: str):
        """Mark task as blocked"""
        self.status = TaskStatus.BLOCKED
        self.blocked_reason = reason


@dataclass
class Phase:
    """
    Represents a project phase (e.g., "Foundation", "Indicator Framework")
    
    Attributes:
        name: Phase name
        start_date: Phase start date
        duration_days: Planned duration in days
        tasks: List of tasks in this phase
        go_no_go_criteria: Criteria that must be met to proceed
    """
    name: str
    start_date: datetime
    duration_days: int
    tasks: List[Task] = field(default_factory=list)
    go_no_go_criteria: List[str] = field(default_factory=list)
    
    def get_progress(self) -> Dict:
        """Calculate phase progress"""
        if not self.tasks:
            return {'percentage': 0.0, 'completed': 0, 'total': 0}
        
        completed = sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)
        total = len(self.tasks)
        
        # Weight by effort
        completed_effort = sum(t.effort_days for t in self.tasks if t.status == TaskStatus.COMPLETED)
        total_effort = sum(t.effort_days for t in self.tasks)
        
        return {
            'percentage': (completed_effort / total_effort * 100) if total_effort > 0 else 0.0,
            'completed': completed,
            'total': total,
            'completed_effort': completed_effort,
            'total_effort': total_effort,
        }
    
    def is_complete(self) -> bool:
        """Check if all tasks in phase are completed"""
        return all(t.status == TaskStatus.COMPLETED for t in self.tasks)
    
    def get_end_date(self) -> datetime:
        """Calculate phase end date"""
        return self.start_date + timedelta(days=self.duration_days)


@dataclass
class Milestone:
    """
    Represents a project milestone
    
    Attributes:
        name: Milestone name
        target_date: Target completion date
        criteria: Success criteria
        is_achieved: Whether milestone is achieved
        achieved_date: When milestone was achieved
    """
    name: str
    target_date: datetime
    criteria: List[str]
    is_achieved: bool = False
    achieved_date: Optional[datetime] = None
    
    def achieve(self):
        """Mark milestone as achieved"""
        self.is_achieved = True
        self.achieved_date = datetime.now()


class ProgressTracker:
    """
    Track progress across entire refactoring project
    
    Example:
        tracker = ProgressTracker()
        
        # Setup project structure
        tracker.add_phase("Foundation", "2025-01-01", 10)
        tracker.add_task("Foundation", "Setup pytest", effort_days=2, status="completed")
        tracker.add_task("Foundation", "Write tests", effort_days=5, dependencies=["Setup pytest"])
        
        # Track progress
        status = tracker.get_project_status()
        print(f"Project {status['percentage']:.1f}% complete")
        
        # Generate report
        report = tracker.generate_report()
        print(report)
    """
    
    def __init__(self):
        self.phases: Dict[str, Phase] = {}
        self.tasks: Dict[str, Task] = {}
        self.milestones: List[Milestone] = []
        self.project_start: Optional[datetime] = None
        self.project_end: Optional[datetime] = None
    
    def add_phase(self, name: str, start_date: str, duration_days: int, 
                  go_no_go_criteria: Optional[List[str]] = None):
        """
        Add a project phase
        
        Args:
            name: Phase name
            start_date: Start date (YYYY-MM-DD format)
            duration_days: Duration in days
            go_no_go_criteria: List of criteria to proceed to next phase
        """
        phase = Phase(
            name=name,
            start_date=datetime.fromisoformat(start_date),
            duration_days=duration_days,
            go_no_go_criteria=go_no_go_criteria or []
        )
        self.phases[name] = phase
        
        # Update project dates
        if self.project_start is None or phase.start_date < self.project_start:
            self.project_start = phase.start_date
        
        end_date = phase.get_end_date()
        if self.project_end is None or end_date > self.project_end:
            self.project_end = end_date
    
    def add_task(self, phase_name: str, task_name: str, effort_days: float,
                 status: str = "not_started", priority: str = "medium",
                 assignee: Optional[str] = None, dependencies: Optional[List[str]] = None):
        """
        Add a task to a phase
        
        Args:
            phase_name: Which phase this task belongs to
            task_name: Task name
            effort_days: Effort in person-days
            status: Task status (not_started, in_progress, completed, blocked)
            priority: Priority (low, medium, high, critical)
            assignee: Person assigned
            dependencies: List of task names that must complete first
        """
        if phase_name not in self.phases:
            raise ValueError(f"Phase '{phase_name}' not found. Add phase first.")
        
        task = Task(
            name=task_name,
            phase=phase_name,
            effort_days=effort_days,
            status=TaskStatus(status),
            priority=TaskPriority(priority),
            assignee=assignee,
            dependencies=dependencies or []
        )
        
        self.tasks[task_name] = task
        self.phases[phase_name].tasks.append(task)
    
    def update_task_status(self, task_name: str, status: str, 
                          blocked_reason: Optional[str] = None):
        """Update task status"""
        if task_name not in self.tasks:
            raise ValueError(f"Task '{task_name}' not found")
        
        task = self.tasks[task_name]
        task.status = TaskStatus(status)
        
        if status == "completed":
            task.complete()
        elif status == "blocked" and blocked_reason:
            task.block(blocked_reason)
        elif status == "in_progress" and task.start_date is None:
            task.start_date = datetime.now()
    
    def add_milestone(self, name: str, target_date: str, criteria: List[str]):
        """Add a project milestone"""
        milestone = Milestone(
            name=name,
            target_date=datetime.fromisoformat(target_date),
            criteria=criteria
        )
        self.milestones.append(milestone)
    
    def achieve_milestone(self, name: str):
        """Mark milestone as achieved"""
        for milestone in self.milestones:
            if milestone.name == name:
                milestone.achieve()
                return
        raise ValueError(f"Milestone '{name}' not found")
    
    def get_overall_progress(self) -> Dict:
        """
        Calculate overall project progress
        
        Returns:
            Dict with percentage, completed tasks, total tasks, etc.
        """
        if not self.tasks:
            return {
                'percentage': 0.0,
                'completed_tasks': 0,
                'total_tasks': 0,
                'completed_effort': 0.0,
                'total_effort': 0.0,
            }
        
        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        total = len(self.tasks)
        
        completed_effort = sum(t.effort_days for t in self.tasks.values() 
                              if t.status == TaskStatus.COMPLETED)
        total_effort = sum(t.effort_days for t in self.tasks.values())
        
        return {
            'percentage': (completed_effort / total_effort * 100) if total_effort > 0 else 0.0,
            'completed_tasks': completed,
            'total_tasks': total,
            'completed_effort': completed_effort,
            'total_effort': total_effort,
        }
    
    def get_phase_progress(self, phase_name: str) -> Dict:
        """Get progress for specific phase"""
        if phase_name not in self.phases:
            raise ValueError(f"Phase '{phase_name}' not found")
        return self.phases[phase_name].get_progress()
    
    def get_blocked_tasks(self) -> List[Task]:
        """Get all blocked tasks"""
        return [t for t in self.tasks.values() if t.status == TaskStatus.BLOCKED]
    
    def get_ready_tasks(self) -> List[Task]:
        """Get tasks that are ready to start (dependencies met, not started)"""
        completed = {t.name for t in self.tasks.values() if t.status == TaskStatus.COMPLETED}
        return [
            t for t in self.tasks.values()
            if t.status == TaskStatus.NOT_STARTED and t.is_ready(completed)
        ]
    
    def calculate_velocity(self) -> float:
        """
        Calculate team velocity (effort-days completed per day)
        
        Returns:
            Average effort-days completed per calendar day
        """
        completed_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]
        if not completed_tasks:
            return 0.0
        
        # Find date range
        start_dates = [t.start_date for t in completed_tasks if t.start_date]
        completion_dates = [t.completion_date for t in completed_tasks if t.completion_date]
        
        if not start_dates or not completion_dates:
            return 0.0
        
        earliest = min(start_dates)
        latest = max(completion_dates)
        days_elapsed = max((latest - earliest).days, 1)
        
        completed_effort = sum(t.effort_days for t in completed_tasks)
        return completed_effort / days_elapsed
    
    def estimate_completion(self) -> Optional[datetime]:
        """
        Estimate project completion date based on velocity
        
        Returns:
            Estimated completion date, or None if cannot calculate
        """
        velocity = self.calculate_velocity()
        if velocity <= 0:
            return None
        
        remaining_effort = sum(
            t.effort_days for t in self.tasks.values()
            if t.status != TaskStatus.COMPLETED
        )
        
        days_remaining = remaining_effort / velocity
        return datetime.now() + timedelta(days=days_remaining)
    
    def generate_report(self) -> str:
        """
        Generate comprehensive progress report
        
        Returns:
            Formatted text report
        """
        lines = []
        lines.append("=" * 80)
        lines.append("PROJECT PROGRESS REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Overall progress
        overall = self.get_overall_progress()
        lines.append(f"Overall Progress: {overall['percentage']:.1f}%")
        lines.append(f"Tasks: {overall['completed_tasks']}/{overall['total_tasks']} completed")
        lines.append(f"Effort: {overall['completed_effort']:.1f}/{overall['total_effort']:.1f} person-days")
        lines.append("")
        
        # Velocity and ETA
        velocity = self.calculate_velocity()
        eta = self.estimate_completion()
        lines.append(f"Velocity: {velocity:.2f} effort-days/calendar-day")
        if eta:
            lines.append(f"Estimated Completion: {eta.strftime('%Y-%m-%d')}")
        lines.append("")
        
        # Phase breakdown
        lines.append("PHASE BREAKDOWN:")
        lines.append("-" * 80)
        for phase in self.phases.values():
            progress = phase.get_progress()
            status = "✓ COMPLETE" if phase.is_complete() else "⏳ IN PROGRESS"
            lines.append(f"{phase.name}: {progress['percentage']:.1f}% {status}")
            lines.append(f"  Tasks: {progress['completed']}/{progress['total']}")
            lines.append(f"  Effort: {progress['completed_effort']:.1f}/{progress['total_effort']:.1f} days")
            lines.append(f"  Duration: {phase.start_date.strftime('%Y-%m-%d')} to {phase.get_end_date().strftime('%Y-%m-%d')}")
            lines.append("")
        
        # Blocked tasks
        blocked = self.get_blocked_tasks()
        if blocked:
            lines.append("BLOCKED TASKS:")
            lines.append("-" * 80)
            for task in blocked:
                lines.append(f"⚠️  {task.name} (Phase: {task.phase})")
                lines.append(f"  Reason: {task.blocked_reason}")
                lines.append("")
        
        # Ready tasks
        ready = self.get_ready_tasks()
        if ready:
            lines.append("READY TO START:")
            lines.append("-" * 80)
            for task in ready[:5]:  # Show top 5
                lines.append(f"▶️  {task.name} (Phase: {task.phase}, {task.effort_days} days)")
            if len(ready) > 5:
                lines.append(f"  ... and {len(ready) - 5} more")
            lines.append("")
        
        # Milestones
        if self.milestones:
            lines.append("MILESTONES:")
            lines.append("-" * 80)
            for milestone in self.milestones:
                status = "✓" if milestone.is_achieved else "⏱️ "
                date = milestone.achieved_date or milestone.target_date
                lines.append(f"{status} {milestone.name} ({date.strftime('%Y-%m-%d')})")
            lines.append("")
        
        lines.append("=" * 80)
        return "\n".join(lines)


def get_project_status(tracker: ProgressTracker) -> Dict:
    """
    Get high-level project status
    
    Args:
        tracker: ProgressTracker instance
    
    Returns:
        Dict with status summary
    """
    overall = tracker.get_overall_progress()
    blocked = tracker.get_blocked_tasks()
    ready = tracker.get_ready_tasks()
    
    return {
        'progress_percentage': overall['percentage'],
        'tasks_completed': overall['completed_tasks'],
        'tasks_total': overall['total_tasks'],
        'blocked_count': len(blocked),
        'ready_count': len(ready),
        'velocity': tracker.calculate_velocity(),
        'estimated_completion': tracker.estimate_completion(),
    }


def calculate_phase_progress(phase: Phase) -> float:
    """
    Calculate progress percentage for a phase
    
    Args:
        phase: Phase instance
    
    Returns:
        Progress percentage (0-100)
    """
    return phase.get_progress()['percentage']
