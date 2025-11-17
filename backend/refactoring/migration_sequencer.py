"""
Migration Sequencer

Part 5B: Deterministic Refactoring Blueprint Engine (DRBE)
Manages step-by-step migration with validation and checkpoints.
"""

from typing import List, Dict, Callable, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MigrationStatus(Enum):
    """Migration step status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class MigrationStep:
    """
    Single migration step with validation
    
    Attributes:
        id: Unique step identifier
        name: Human-readable step name
        description: Detailed description
        dependencies: List of step IDs that must complete first
        execute: Function to run the migration
        validate: Function to validate success
        rollback: Function to undo changes
        risk_level: "low", "medium", or "high"
        estimated_duration: Expected duration in minutes
        status: Current status
        error: Error message if failed
    """
    id: str
    name: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    execute: Optional[Callable[[], bool]] = None
    validate: Optional[Callable[[], bool]] = None
    rollback: Optional[Callable[[], bool]] = None
    risk_level: str = "low"
    estimated_duration: int = 0
    status: MigrationStatus = MigrationStatus.PENDING
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def can_execute(self, completed_steps: set) -> bool:
        """Check if all dependencies are completed"""
        return all(dep in completed_steps for dep in self.dependencies)
    
    def duration_minutes(self) -> Optional[float]:
        """Calculate actual duration in minutes"""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds() / 60
        return None
    
    def __str__(self) -> str:
        """Human-readable summary"""
        lines = [
            f"Migration Step: {self.name} ({self.id})",
            f"  Status: {self.status.value}",
            f"  Risk: {self.risk_level}",
            f"  Dependencies: {', '.join(self.dependencies) if self.dependencies else 'None'}"
        ]
        
        if self.error:
            lines.append(f"  Error: {self.error}")
        
        if self.duration_minutes():
            lines.append(f"  Duration: {self.duration_minutes():.2f} minutes")
        
        return "\n".join(lines)


@dataclass
class MigrationPlan:
    """
    Complete migration plan with multiple steps
    
    Attributes:
        name: Plan name
        description: Plan description
        steps: List of migration steps
        current_step: Index of current step
    """
    name: str
    description: str
    steps: List[MigrationStep] = field(default_factory=list)
    current_step: int = 0
    
    def add_step(self, step: MigrationStep) -> None:
        """Add a migration step"""
        self.steps.append(step)
    
    def get_step(self, step_id: str) -> Optional[MigrationStep]:
        """Get step by ID"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None
    
    def get_executable_steps(self) -> List[MigrationStep]:
        """Get steps ready to execute"""
        completed = {
            step.id for step in self.steps 
            if step.status == MigrationStatus.COMPLETED
        }
        
        return [
            step for step in self.steps
            if step.status == MigrationStatus.PENDING
            and step.can_execute(completed)
        ]
    
    def get_progress(self) -> Dict[str, Any]:
        """Get migration progress statistics"""
        total = len(self.steps)
        completed = sum(1 for s in self.steps if s.status == MigrationStatus.COMPLETED)
        failed = sum(1 for s in self.steps if s.status == MigrationStatus.FAILED)
        in_progress = sum(1 for s in self.steps if s.status == MigrationStatus.IN_PROGRESS)
        
        return {
            'total': total,
            'completed': completed,
            'failed': failed,
            'in_progress': in_progress,
            'pending': total - completed - failed - in_progress,
            'completion_percentage': (completed / total * 100) if total > 0 else 0
        }
    
    def __str__(self) -> str:
        """Human-readable summary"""
        progress = self.get_progress()
        
        lines = [
            f"Migration Plan: {self.name}",
            f"  Total steps: {progress['total']}",
            f"  Completed: {progress['completed']} ({progress['completion_percentage']:.1f}%)",
            f"  Failed: {progress['failed']}",
            f"  In progress: {progress['in_progress']}",
            f"  Pending: {progress['pending']}"
        ]
        
        return "\n".join(lines)


def create_migration_plan(
    name: str,
    description: str,
    steps: Optional[List[MigrationStep]] = None
) -> MigrationPlan:
    """
    Create a new migration plan
    
    Args:
        name: Plan name
        description: Plan description
        steps: Initial steps (optional)
    
    Returns:
        MigrationPlan instance
    
    Usage:
        plan = create_migration_plan(
            "Phase 1: Foundation",
            "Setup testing infrastructure"
        )
        
        plan.add_step(MigrationStep(
            id="setup_pytest",
            name="Setup pytest",
            description="Install and configure pytest",
            execute=setup_pytest_func,
            validate=check_pytest_func,
            risk_level="low"
        ))
    """
    plan = MigrationPlan(name=name, description=description)
    
    if steps:
        for step in steps:
            plan.add_step(step)
    
    return plan


def execute_migration_step(
    step: MigrationStep,
    dry_run: bool = False
) -> bool:
    """
    Execute a single migration step with validation
    
    Args:
        step: MigrationStep to execute
        dry_run: If True, validate but don't execute
    
    Returns:
        True if successful, False if failed
    
    Usage:
        step = MigrationStep(
            id="migrate_rsi",
            name="Migrate RSI indicator",
            execute=migrate_rsi,
            validate=test_rsi
        )
        
        success = execute_migration_step(step)
        if not success:
            print(f"Migration failed: {step.error}")
    """
    logger.info(f"{'[DRY RUN] ' if dry_run else ''}Executing step: {step.name}")
    
    step.status = MigrationStatus.IN_PROGRESS
    step.started_at = datetime.now()
    step.error = None
    
    try:
        # Execute migration
        if not dry_run and step.execute:
            result = step.execute()
            if not result:
                raise Exception("Execute function returned False")
        
        # Validate result
        if step.validate:
            if not step.validate():
                raise Exception("Validation failed")
        
        # Success
        step.status = MigrationStatus.COMPLETED
        step.completed_at = datetime.now()
        logger.info(f"Step completed: {step.name}")
        return True
    
    except Exception as e:
        # Failure
        step.status = MigrationStatus.FAILED
        step.completed_at = datetime.now()
        step.error = str(e)
        logger.error(f"Step failed: {step.name} - {e}")
        
        # Attempt rollback
        if step.rollback:
            try:
                logger.info(f"Attempting rollback for: {step.name}")
                step.rollback()
                step.status = MigrationStatus.ROLLED_BACK
                logger.info(f"Rollback successful: {step.name}")
            except Exception as rollback_error:
                logger.error(f"Rollback failed: {step.name} - {rollback_error}")
        
        return False


def execute_migration_plan(
    plan: MigrationPlan,
    dry_run: bool = False,
    stop_on_failure: bool = True
) -> Dict[str, Any]:
    """
    Execute all steps in a migration plan
    
    Args:
        plan: MigrationPlan to execute
        dry_run: If True, validate but don't execute
        stop_on_failure: If True, stop on first failure
    
    Returns:
        Execution summary with results
    
    Usage:
        plan = create_migration_plan("Phase 1", "Foundation")
        # ... add steps ...
        
        # Dry run first
        results = execute_migration_plan(plan, dry_run=True)
        print(f"Would complete {results['completed']} steps")
        
        # Execute for real
        results = execute_migration_plan(plan)
        print(f"Completed {results['completed']}/{results['total']} steps")
    """
    logger.info(f"{'[DRY RUN] ' if dry_run else ''}Starting migration plan: {plan.name}")
    
    completed = 0
    failed = 0
    skipped = 0
    
    while True:
        # Get next executable steps
        executable = plan.get_executable_steps()
        
        if not executable:
            # No more steps to execute
            break
        
        # Execute all ready steps (parallel execution possible here)
        for step in executable:
            success = execute_migration_step(step, dry_run=dry_run)
            
            if success:
                completed += 1
            else:
                failed += 1
                
                if stop_on_failure:
                    # Skip remaining steps
                    for remaining in plan.steps:
                        if remaining.status == MigrationStatus.PENDING:
                            remaining.status = MigrationStatus.PENDING  # Keep as pending
                            skipped += 1
                    
                    logger.warning(f"Stopping migration due to failure in: {step.name}")
                    break
        
        if failed > 0 and stop_on_failure:
            break
    
    result = {
        'plan': plan.name,
        'total': len(plan.steps),
        'completed': completed,
        'failed': failed,
        'skipped': skipped,
        'success': failed == 0,
        'dry_run': dry_run
    }
    
    logger.info(f"Migration plan finished: {result}")
    
    return result


def generate_migration_report(plan: MigrationPlan) -> str:
    """
    Generate detailed migration report
    
    Args:
        plan: MigrationPlan to report on
    
    Returns:
        Formatted report string
    
    Usage:
        report = generate_migration_report(plan)
        print(report)
        
        # Or save to file
        with open('migration_report.txt', 'w') as f:
            f.write(report)
    """
    lines = [
        "=" * 60,
        f"MIGRATION REPORT: {plan.name}",
        "=" * 60,
        f"Description: {plan.description}",
        ""
    ]
    
    # Progress summary
    progress = plan.get_progress()
    lines.extend([
        "Progress Summary:",
        f"  Total steps: {progress['total']}",
        f"  Completed: {progress['completed']} ({progress['completion_percentage']:.1f}%)",
        f"  Failed: {progress['failed']}",
        f"  In progress: {progress['in_progress']}",
        f"  Pending: {progress['pending']}",
        ""
    ])
    
    # Step details
    lines.append("Step Details:")
    lines.append("-" * 60)
    
    for i, step in enumerate(plan.steps, 1):
        status_symbol = {
            MigrationStatus.COMPLETED: "?",
            MigrationStatus.FAILED: "?",
            MigrationStatus.ROLLED_BACK: "?",
            MigrationStatus.IN_PROGRESS: "?",
            MigrationStatus.PENDING: "?"
        }
        
        symbol = status_symbol.get(step.status, "?")
        lines.append(f"{i}. [{symbol}] {step.name} ({step.id})")
        lines.append(f"    Status: {step.status.value}")
        lines.append(f"    Risk: {step.risk_level}")
        
        if step.dependencies:
            lines.append(f"    Dependencies: {', '.join(step.dependencies)}")
        
        if step.duration_minutes():
            est = step.estimated_duration
            actual = step.duration_minutes()
            diff = actual - est if est > 0 else 0
            lines.append(f"    Duration: {actual:.2f}m (estimated: {est}m, diff: {diff:+.2f}m)")
        
        if step.error:
            lines.append(f"    Error: {step.error}")
        
        lines.append("")
    
    # Failed steps summary
    failed_steps = [s for s in plan.steps if s.status == MigrationStatus.FAILED]
    if failed_steps:
        lines.append("=" * 60)
        lines.append("FAILED STEPS:")
        lines.append("=" * 60)
        for step in failed_steps:
            lines.append(f"- {step.name}: {step.error}")
        lines.append("")
    
    return "\n".join(lines)
