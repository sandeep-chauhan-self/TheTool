"""
Refactoring Tools (Part 5B: DRBE)

Tools for deterministic, safe refactoring with dependency tracking,
migration sequencing, and rollback capabilities.
"""

from backend.refactoring.dependency_analyzer import (
    DependencyGraph,
    analyze_dependencies,
    find_circular_dependencies,
    get_migration_order,
    suggest_refactoring_order,
    visualize_dependencies
)

from backend.refactoring.migration_sequencer import (
    MigrationStep,
    MigrationPlan,
    MigrationStatus,
    create_migration_plan,
    execute_migration_step,
    execute_migration_plan,
    generate_migration_report
)

from backend.refactoring.rollback_manager import (
    RollbackPoint,
    create_rollback_point,
    rollback_to_point,
    list_rollback_points
)

__all__ = [
    # Dependency analysis
    'DependencyGraph',
    'analyze_dependencies',
    'find_circular_dependencies',
    'get_migration_order',
    'suggest_refactoring_order',
    'visualize_dependencies',
    
    # Migration sequencing
    'MigrationStep',
    'MigrationPlan',
    'MigrationStatus',
    'create_migration_plan',
    'execute_migration_step',
    'execute_migration_plan',
    'generate_migration_report',
    
    # Rollback management
    'RollbackPoint',
    'create_rollback_point',
    'rollback_to_point',
    'list_rollback_points',
]
