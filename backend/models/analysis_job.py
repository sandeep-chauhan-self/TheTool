"""
Analysis Job Domain Model

Part 4: Architecture Blueprint  
DOMAIN_MODEL_001: Job Entity with Business Logic

Rich domain entity with invariants and business rules.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

from models.job_state import JobStateMachine, JobState, JobEvent


@dataclass
class Ticker:
    """
    Value Object: Ticker Symbol
    
    Immutable ticker symbol with validation.
    """
    symbol: str
    
    def __post_init__(self):
        """Validate ticker symbol"""
        if not self.symbol or not isinstance(self.symbol, str):
            raise ValueError("Ticker symbol must be a non-empty string")
        
        # Normalize to uppercase
        normalized = self.symbol.strip().upper()
        
        if len(normalized) < 1 or len(normalized) > 10:
            raise ValueError("Ticker symbol must be 1-10 characters")
        
        object.__setattr__(self, 'symbol', normalized)
    
    def __str__(self) -> str:
        return self.symbol
    
    def __repr__(self) -> str:
        return f"Ticker('{self.symbol}')"
    
    def __hash__(self) -> int:
        return hash(self.symbol)
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Ticker):
            return False
        return self.symbol == other.symbol


@dataclass
class AnalysisJob:
    """
    Job Aggregate Root
    
    Represents a batch analysis job with lifecycle management.
    
    Invariants:
    - Must have at least 1 ticker
    - Cannot have more than 100 tickers
    - Total tickers = completed + pending
    - Cannot transition from terminal state
    - Capital must be positive
    
    Business Rules:
    - Progress = (completed / total) * 100
    - Status must follow state machine
    - Errors are immutable once added
    """
    
    # Identity
    id: str
    
    # Configuration
    tickers: List[Ticker]
    indicators: Optional[List[str]] = None
    capital: float = 100000
    use_demo_data: bool = False
    
    # State
    state_machine: JobStateMachine = field(default_factory=lambda: JobStateMachine(JobState.CREATED))
    completed_count: int = 0
    error_count: int = 0
    errors: List[Dict[str, str]] = field(default_factory=list)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate invariants"""
        self._validate_invariants()
    
    def _validate_invariants(self) -> None:
        """Ensure business rules are satisfied"""
        if not self.tickers:
            raise ValueError("Job must have at least 1 ticker")
        
        if len(self.tickers) > 100:
            raise ValueError("Job cannot have more than 100 tickers")
        
        if self.capital <= 0:
            raise ValueError("Capital must be positive")
        
        total = len(self.tickers)
        if self.completed_count > total:
            raise ValueError(f"Completed ({self.completed_count}) > Total ({total})")
    
    @property
    def status(self) -> str:
        """Current job status"""
        return self.state_machine.current_state.value
    
    @property
    def total_tickers(self) -> int:
        """Total number of tickers"""
        return len(self.tickers)
    
    @property
    def progress_percentage(self) -> float:
        """Progress as percentage (0-100)"""
        if self.total_tickers == 0:
            return 0.0
        return (self.completed_count / self.total_tickers) * 100
    
    @property
    def is_complete(self) -> bool:
        """Check if job is complete (all tickers processed)"""
        return self.completed_count == self.total_tickers
    
    @property
    def is_terminal(self) -> bool:
        """Check if job is in terminal state"""
        return self.state_machine.is_terminal()
    
    def queue(self) -> None:
        """Transition job to queued state"""
        self.state_machine.transition(JobEvent.QUEUE)
    
    def start(self) -> None:
        """Start job execution"""
        self.state_machine.transition(JobEvent.START)
        self.started_at = datetime.now()
    
    def increment_completed(self) -> None:
        """Increment completed ticker count"""
        self.completed_count += 1
        self._validate_invariants()
    
    def add_error(self, ticker: str, error_message: str) -> None:
        """Record an error for a ticker"""
        self.errors.append({
            "ticker": ticker,
            "error": error_message,
            "timestamp": datetime.now().isoformat()
        })
        self.error_count += 1
    
    def complete(self) -> None:
        """Mark job as completed"""
        self.state_machine.transition(JobEvent.COMPLETE)
        self.completed_at = datetime.now()
    
    def fail(self, error: str) -> None:
        """Mark job as failed"""
        self.state_machine.transition(JobEvent.FAIL, metadata={"error": error})
        self.completed_at = datetime.now()
    
    def cancel(self) -> None:
        """Cancel job"""
        self.state_machine.transition(JobEvent.CANCEL)
        self.completed_at = datetime.now()
    
    def can_be_cancelled(self) -> bool:
        """Check if job can be cancelled"""
        return self.state_machine.can_transition(JobEvent.CANCEL)
    
    def pause(self) -> None:
        """Pause job execution"""
        self.state_machine.transition(JobEvent.PAUSE)
    
    def resume(self) -> None:
        """Resume paused job"""
        self.state_machine.transition(JobEvent.RESUME)
    
    def retry(self) -> None:
        """Retry failed job"""
        self.state_machine.transition(JobEvent.RETRY)
        self.completed_count = 0
        self.error_count = 0
        self.errors = []
        self.started_at = None
        self.completed_at = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "status": self.status,
            "tickers": [str(t) for t in self.tickers],
            "indicators": self.indicators,
            "capital": self.capital,
            "use_demo_data": self.use_demo_data,
            "total": self.total_tickers,
            "completed": self.completed_count,
            "errors": self.error_count,
            "error_details": self.errors,
            "progress": self.progress_percentage,
            "is_complete": self.is_complete,
            "is_terminal": self.is_terminal,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
    
    def __repr__(self) -> str:
        return (
            f"AnalysisJob(id='{self.id}', status='{self.status}', "
            f"progress={self.progress_percentage:.1f}%, tickers={self.total_tickers})"
        )
