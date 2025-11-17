"""
Redis Job State Manager - EVOLUTIONARY_RISK_001 Solution

Replaces in-memory active_jobs dictionary with Redis-based persistence.
This enables:
- Job state persistence across restarts
- Distributed job tracking across multiple servers
- Horizontal scalability
- Job recovery and monitoring

Architecture:
    JobStateManager (Abstract Base Class)
    ??? RedisJobStateManager (Production - Redis backend)
    ??? InMemoryJobStateManager (Fallback - current implementation)

Migration Strategy:
    1. Deploy RedisJobStateManager with Redis server
    2. Fallback to InMemoryJobStateManager if Redis unavailable
    3. Seamless transition without breaking existing code

Author: TheTool Trading System  
Version: 2.0.0 - Part 2 Implementation
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from config import config
from typing import Callable

# Optional Redis import
try:
    import redis
    REDIS_AVAILABLE = True
    RedisType = redis.Redis
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    RedisType = Any  # Fallback type when redis not available

logger = logging.getLogger('job_state')


# ============================================================================
# State Machine Components (Part 4: Architecture Blueprint)
# ============================================================================

class JobState(Enum):
    """Job state enumeration"""
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class JobEvent(Enum):
    """Job event enumeration"""
    CREATE = "create"
    QUEUE = "queue"
    START = "start"
    PAUSE = "pause"
    RESUME = "resume"
    COMPLETE = "complete"
    FAIL = "fail"
    CANCEL = "cancel"
    TIMEOUT = "timeout"
    RETRY = "retry"


@dataclass
class StateTransition:
    """Represents a state transition"""
    from_state: JobState
    to_state: JobState
    event: JobEvent
    timestamp: datetime = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Set default timestamp if not provided"""
        if self.timestamp is None:
            object.__setattr__(self, 'timestamp', datetime.now())


class JobStateMachine:
    """
    Finite State Machine for Job lifecycle management
    
    Valid transitions:
    - CREATED -> QUEUED (queue)
    - QUEUED -> RUNNING (start)
    - RUNNING -> PAUSED (pause)
    - RUNNING -> COMPLETED (complete)
    - RUNNING -> FAILED (fail)
    - RUNNING -> CANCELLED (cancel)
    - RUNNING -> TIMEOUT (timeout)
    - PAUSED -> RUNNING (resume)
    - PAUSED -> CANCELLED (cancel)
    - FAILED -> QUEUED (retry)
    """
    
    VALID_TRANSITIONS = {
        (JobState.CREATED, JobEvent.QUEUE): JobState.QUEUED,
        (JobState.QUEUED, JobEvent.START): JobState.RUNNING,
        (JobState.RUNNING, JobEvent.PAUSE): JobState.PAUSED,
        (JobState.RUNNING, JobEvent.COMPLETE): JobState.COMPLETED,
        (JobState.RUNNING, JobEvent.FAIL): JobState.FAILED,
        (JobState.RUNNING, JobEvent.CANCEL): JobState.CANCELLED,
        (JobState.RUNNING, JobEvent.TIMEOUT): JobState.TIMEOUT,
        (JobState.PAUSED, JobEvent.RESUME): JobState.RUNNING,
        (JobState.PAUSED, JobEvent.CANCEL): JobState.CANCELLED,
        (JobState.FAILED, JobEvent.RETRY): JobState.QUEUED,
    }
    
    TERMINAL_STATES = {JobState.COMPLETED, JobState.FAILED, JobState.CANCELLED, JobState.TIMEOUT}
    
    def __init__(self, initial_state: JobState = JobState.CREATED):
        """Initialize state machine"""
        self.current_state = initial_state
        self.history: List[StateTransition] = []
        self._hooks: Dict[tuple, List[Callable]] = {}
    
    def can_transition(self, event: JobEvent) -> bool:
        """Check if transition is valid"""
        return (self.current_state, event) in self.VALID_TRANSITIONS
    
    def transition(self, event: JobEvent, metadata: Optional[Dict[str, Any]] = None) -> JobState:
        """
        Execute state transition
        
        Returns:
            New state if transition successful
            
        Raises:
            ValueError: If transition is invalid or from terminal state (except retries)
        """
        # Check if transition is valid first
        if not self.can_transition(event):
            # Check if trying to transition from terminal state
            if self.is_terminal():
                raise ValueError(
                    f"Cannot transition from terminal state {self.current_state.value}"
                )
            raise ValueError(
                f"Invalid transition: {self.current_state.value} with event {event.value}"
            )
        
        old_state = self.current_state
        new_state = self.VALID_TRANSITIONS[(self.current_state, event)]
        
        # Record transition
        transition = StateTransition(
            from_state=old_state,
            to_state=new_state,
            event=event,
            timestamp=datetime.now(),
            metadata=metadata
        )
        self.history.append(transition)
        
        # Update state
        self.current_state = new_state
        
        # Execute hooks
        hook_key = (old_state, new_state)
        if hook_key in self._hooks:
            for hook in self._hooks[hook_key]:
                try:
                    hook(transition)
                except Exception as e:
                    logger.error(f"Hook execution failed: {e}")
        
        logger.info(
            f"State transition: {old_state.value} -> {new_state.value} (event: {event.value})"
        )
        
        return new_state
    
    def register_hook(self, from_state: JobState, to_state: JobState, hook: Callable) -> None:
        """Register a hook to be called on specific transition"""
        key = (from_state, to_state)
        if key not in self._hooks:
            self._hooks[key] = []
        self._hooks[key].append(hook)
    
    def is_terminal(self) -> bool:
        """Check if current state is terminal"""
        return self.current_state in self.TERMINAL_STATES
    
    def get_valid_events(self) -> List[JobEvent]:
        """Get list of valid events for current state"""
        return [
            event for (state, event) in self.VALID_TRANSITIONS.keys()
            if state == self.current_state
        ]
    
    def get_history(self) -> List[StateTransition]:
        """Get transition history"""
        return self.history.copy()
    
    def __repr__(self) -> str:
        """String representation"""
        return f"JobStateMachine(current_state={self.current_state.value}, transitions={len(self.history)})"


# ============================================================================
# Job State Manager (Redis/In-Memory)
# ============================================================================


class JobStateManager(ABC):
    """Abstract base class for job state management"""
    
    @abstractmethod
    def create_job(self, job_id: str, initial_state: Dict[str, Any]) -> bool:
        """Create a new job with initial state"""
        pass
    
    @abstractmethod
    def update_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """Update job state"""
        pass
    
    @abstractmethod
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job state"""
        pass
    
    @abstractmethod
    def delete_job(self, job_id: str) -> bool:
        """Delete job state"""
        pass
    
    @abstractmethod
    def get_all_jobs(self) -> Dict[str, Dict[str, Any]]:
        """Get all active jobs"""
        pass
    
    @abstractmethod
    def cancel_job(self, job_id: str) -> bool:
        """Mark job as cancelled"""
        pass
    
    @abstractmethod
    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """Cleanup old completed/failed jobs"""
        pass


class RedisJobStateManager(JobStateManager):
    """
    Redis-based job state manager for distributed systems.
    
    Storage Strategy:
    - Job data: Redis Hash (HSET job:{job_id})
    - Job list: Redis Set (SADD active_jobs {job_id})
    - Expiry: TTL on completed jobs (24 hours default)
    
    Key Structure:
    - job:{job_id} -> Hash with job data
    - active_jobs -> Set of active job IDs
    - job:{job_id}:logs -> List for job logs (optional)
    """
    
    def __init__(self, redis_client: Optional[RedisType] = None):
        """
        Initialize Redis job state manager.
        
        Args:
            redis_client: Optional Redis client (will create if None)
        """
        if redis_client:
            self.redis = redis_client
        else:
            # Create Redis client from config
            self.redis = redis.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                db=config.REDIS_DB,
                password=config.REDIS_PASSWORD if config.REDIS_PASSWORD else None,
                decode_responses=True,  # Return strings instead of bytes
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
        
        # Test connection
        try:
            self.redis.ping()
            logger.info(f"Redis connected: {config.REDIS_HOST}:{config.REDIS_PORT}")
        except redis.ConnectionError as e:
            logger.error(f"Redis connection failed: {str(e)}")
            raise
    
    def create_job(self, job_id: str, initial_state: Dict[str, Any]) -> bool:
        """
        Create a new job in Redis.
        
        Args:
            job_id: Unique job identifier
            initial_state: Initial job state dictionary
        
        Returns:
            True if created successfully
        """
        try:
            # Add timestamp if not present
            if 'created_at' not in initial_state:
                initial_state['created_at'] = datetime.now().isoformat()
            
            # Convert dict to flat structure for HSET
            job_data = self._serialize_job_state(initial_state)
            
            # Store in Redis
            key = f"job:{job_id}"
            self.redis.hset(key, mapping=job_data)
            
            # Add to active jobs set
            self.redis.sadd("active_jobs", job_id)
            
            logger.debug(f"Created job {job_id} in Redis")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create job {job_id}: {str(e)}")
            return False
    
    def update_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update job state in Redis.
        
        Args:
            job_id: Job identifier
            updates: Dictionary of fields to update
        
        Returns:
            True if updated successfully
        """
        try:
            key = f"job:{job_id}"
            
            # Check if job exists
            if not self.redis.exists(key):
                logger.warning(f"Job {job_id} not found for update")
                return False
            
            # Add update timestamp
            updates['updated_at'] = datetime.now().isoformat()
            
            # Serialize and update
            job_data = self._serialize_job_state(updates)
            self.redis.hset(key, mapping=job_data)
            
            # If job completed/failed/cancelled, set expiry and remove from active set
            status = updates.get('status')
            if status in ['completed', 'failed', 'cancelled']:
                self.redis.expire(key, 86400)  # 24 hours
                self.redis.srem("active_jobs", job_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update job {job_id}: {str(e)}")
            return False
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job state from Redis.
        
        Args:
            job_id: Job identifier
        
        Returns:
            Job state dictionary or None if not found
        """
        try:
            key = f"job:{job_id}"
            job_data = self.redis.hgetall(key)
            
            if not job_data:
                return None
            
            return self._deserialize_job_state(job_data)
            
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {str(e)}")
            return None
    
    def delete_job(self, job_id: str) -> bool:
        """
        Delete job from Redis.
        
        Args:
            job_id: Job identifier
        
        Returns:
            True if deleted successfully
        """
        try:
            key = f"job:{job_id}"
            
            # Delete job data
            self.redis.delete(key)
            
            # Remove from active jobs
            self.redis.srem("active_jobs", job_id)
            
            logger.debug(f"Deleted job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete job {job_id}: {str(e)}")
            return False
    
    def get_all_jobs(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all active jobs from Redis.
        
        Returns:
            Dictionary mapping job_id -> job_state
        """
        try:
            # Get all active job IDs
            job_ids = self.redis.smembers("active_jobs")
            
            # Retrieve each job's data
            all_jobs = {}
            for job_id in job_ids:
                job_state = self.get_job(job_id)
                if job_state:
                    all_jobs[job_id] = job_state
            
            return all_jobs
            
        except Exception as e:
            logger.error(f"Failed to get all jobs: {str(e)}")
            return {}
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Mark job as cancelled in Redis.
        
        Args:
            job_id: Job identifier
        
        Returns:
            True if cancelled successfully
        """
        return self.update_job(job_id, {
            'cancelled': True,
            'status': 'cancelled',
            'cancelled_at': datetime.now().isoformat()
        })
    
    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """
        Cleanup old completed/failed jobs from Redis.
        
        Args:
            max_age_hours: Maximum age in hours before deletion
        
        Returns:
            Number of jobs cleaned up
        """
        try:
            # Scan for all job keys
            cursor = 0
            cleaned_count = 0
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            while True:
                cursor, keys = self.redis.scan(cursor, match="job:*", count=100)
                
                for key in keys:
                    job_data = self.redis.hgetall(key)
                    if not job_data:
                        continue
                    
                    # Check if job is old enough
                    completed_at = job_data.get('completed_at')
                    if completed_at:
                        completed_time = datetime.fromisoformat(completed_at)
                        if completed_time < cutoff_time:
                            self.redis.delete(key)
                            cleaned_count += 1
                
                if cursor == 0:
                    break
            
            logger.info(f"Cleaned up {cleaned_count} old jobs")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old jobs: {str(e)}")
            return 0
    
    def _serialize_job_state(self, state: Dict[str, Any]) -> Dict[str, str]:
        """
        Convert job state to Redis-compatible format.
        
        Redis HSET requires all values to be strings, so we serialize
        complex types to JSON.
        
        Args:
            state: Job state dictionary
        
        Returns:
            Flattened dictionary with string values
        """
        serialized = {}
        for key, value in state.items():
            if isinstance(value, (dict, list)):
                serialized[key] = json.dumps(value)
            elif isinstance(value, (int, float, bool)):
                serialized[key] = str(value)
            elif value is None:
                serialized[key] = ''
            else:
                serialized[key] = str(value)
        
        return serialized
    
    def _deserialize_job_state(self, data: Dict[str, str]) -> Dict[str, Any]:
        """
        Convert Redis data back to Python types.
        
        Args:
            data: Dictionary with string values
        
        Returns:
            Job state with proper Python types
        """
        deserialized = {}
        for key, value in data.items():
            if not value:  # Empty string = None
                deserialized[key] = None
                continue
            
            # Try to parse as JSON (for dicts/lists)
            try:
                if value.startswith('{') or value.startswith('['):
                    deserialized[key] = json.loads(value)
                    continue
            except json.JSONDecodeError:
                pass
            
            # Try to parse as number
            try:
                if '.' in value:
                    deserialized[key] = float(value)
                else:
                    deserialized[key] = int(value)
                continue
            except ValueError:
                pass
            
            # Try to parse as boolean
            if value.lower() in ('true', 'false'):
                deserialized[key] = value.lower() == 'true'
                continue
            
            # Keep as string
            deserialized[key] = value
        
        return deserialized


class InMemoryJobStateManager(JobStateManager):
    """
    In-memory job state manager (fallback/testing).
    
    This is the current implementation, preserved for:
    - Local development without Redis
    - Testing environments
    - Graceful degradation if Redis fails
    """
    
    def __init__(self):
        """Initialize in-memory storage"""
        self._jobs: Dict[str, Dict[str, Any]] = {}
        logger.info("Using in-memory job state (not distributed)")
    
    def create_job(self, job_id: str, initial_state: Dict[str, Any]) -> bool:
        """Create job in memory"""
        initial_state['created_at'] = datetime.now().isoformat()
        self._jobs[job_id] = initial_state
        return True
    
    def update_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """Update job in memory"""
        if job_id not in self._jobs:
            return False
        
        self._jobs[job_id].update(updates)
        self._jobs[job_id]['updated_at'] = datetime.now().isoformat()
        return True
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job from memory"""
        return self._jobs.get(job_id)
    
    def delete_job(self, job_id: str) -> bool:
        """Delete job from memory"""
        if job_id in self._jobs:
            del self._jobs[job_id]
            return True
        return False
    
    def get_all_jobs(self) -> Dict[str, Dict[str, Any]]:
        """Get all jobs from memory"""
        return self._jobs.copy()
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel job in memory"""
        if job_id in self._jobs:
            self._jobs[job_id]['cancelled'] = True
            self._jobs[job_id]['status'] = 'cancelled'
            return True
        return False
    
    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """Cleanup old jobs from memory"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        to_delete = []
        
        for job_id, job_state in self._jobs.items():
            completed_at = job_state.get('completed_at')
            if completed_at:
                try:
                    completed_time = datetime.fromisoformat(completed_at)
                    if completed_time < cutoff_time:
                        to_delete.append(job_id)
                except ValueError:
                    pass
        
        for job_id in to_delete:
            del self._jobs[job_id]
        
        return len(to_delete)


def create_job_state_manager() -> JobStateManager:
    """
    Factory function to create appropriate job state manager.
    
    Tries Redis first, falls back to in-memory if:
    - Redis module not installed
    - Redis is not configured
    - Redis connection fails
    - Redis is explicitly disabled
    
    Returns:
        JobStateManager instance (Redis or in-memory)
    """
    # Check if Redis module is available
    if not REDIS_AVAILABLE:
        logger.info("Redis module not installed, using in-memory job state")
        return InMemoryJobStateManager()
    
    # Check if Redis is enabled
    if not config.REDIS_ENABLED:
        logger.info("Redis disabled, using in-memory job state")
        return InMemoryJobStateManager()
    
    # Try to create Redis manager
    try:
        manager = RedisJobStateManager()
        logger.info("? Using Redis-based job state (distributed-ready)")
        return manager
    except Exception as e:
        logger.warning(f"Redis unavailable, falling back to in-memory: {str(e)}")
        return InMemoryJobStateManager()


# Global job state manager instance
_job_state_manager: Optional[JobStateManager] = None


def get_job_state_manager() -> JobStateManager:
    """
    Get singleton job state manager instance.
    
    Returns:
        JobStateManager instance
    """
    global _job_state_manager
    
    if _job_state_manager is None:
        _job_state_manager = create_job_state_manager()
    
    return _job_state_manager
