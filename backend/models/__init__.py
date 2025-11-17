"""
Domain Models Package

Rich domain entities with business logic and invariants.
Part 4: Architecture Blueprint
"""

from models.job_state import (
    JobState,
    JobEvent,
    JobStateMachine,
    StateTransition,
    JobStateManager,
    get_job_state_manager
)
from models.analysis_job import AnalysisJob, Ticker
from models.validation import (
    TickerAnalysisRequest,
    BulkAnalysisRequest,
    validate_request
)

__all__ = [
    'JobState',
    'JobEvent',
    'JobStateMachine',
    'StateTransition',
    'JobStateManager',
    'get_job_state_manager',
    'AnalysisJob',
    'Ticker',
    'TickerAnalysisRequest',
    'BulkAnalysisRequest',
    'validate_request',
]
