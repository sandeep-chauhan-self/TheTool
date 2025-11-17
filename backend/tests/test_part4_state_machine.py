"""
Tests for Job State Machine

Part 4: Architecture Blueprint
Tests STATE_MACHINE_001 implementation
"""

import pytest
from datetime import datetime

from models.job_state import JobState, JobEvent, JobStateMachine, StateTransition


class TestJobState:
    """Test JobState enum"""
    
    def test_all_states_defined(self):
        """Test all required states are defined"""
        assert JobState.CREATED.value == "created"
        assert JobState.QUEUED.value == "queued"
        assert JobState.RUNNING.value == "running"
        assert JobState.PAUSED.value == "paused"
        assert JobState.COMPLETED.value == "completed"
        assert JobState.FAILED.value == "failed"
        assert JobState.CANCELLED.value == "cancelled"
        assert JobState.TIMEOUT.value == "timeout"


class TestJobEvent:
    """Test JobEvent enum"""
    
    def test_all_events_defined(self):
        """Test all required events are defined"""
        assert JobEvent.CREATE.value == "create"
        assert JobEvent.QUEUE.value == "queue"
        assert JobEvent.START.value == "start"
        assert JobEvent.PAUSE.value == "pause"
        assert JobEvent.RESUME.value == "resume"
        assert JobEvent.COMPLETE.value == "complete"
        assert JobEvent.FAIL.value == "fail"
        assert JobEvent.CANCEL.value == "cancel"
        assert JobEvent.TIMEOUT.value == "timeout"
        assert JobEvent.RETRY.value == "retry"


class TestStateTransition:
    """Test StateTransition dataclass"""
    
    def test_create_transition(self):
        """Test creating state transition"""
        transition = StateTransition(
            from_state=JobState.QUEUED,
            to_state=JobState.RUNNING,
            event=JobEvent.START,
            metadata={"worker": "worker-1"}
        )
        
        assert transition.from_state == JobState.QUEUED
        assert transition.to_state == JobState.RUNNING
        assert transition.event == JobEvent.START
        assert transition.metadata["worker"] == "worker-1"
        assert isinstance(transition.timestamp, datetime)


class TestJobStateMachine:
    """Test JobStateMachine"""
    
    def test_initial_state(self):
        """Test state machine starts in CREATED state"""
        sm = JobStateMachine()
        assert sm.current_state == JobState.CREATED
    
    def test_custom_initial_state(self):
        """Test custom initial state"""
        sm = JobStateMachine(JobState.QUEUED)
        assert sm.current_state == JobState.QUEUED
    
    def test_valid_transition_created_to_queued(self):
        """Test transition from CREATED to QUEUED"""
        sm = JobStateMachine()
        new_state = sm.transition(JobEvent.QUEUE)
        
        assert new_state == JobState.QUEUED
        assert sm.current_state == JobState.QUEUED
        assert len(sm.history) == 1
    
    def test_valid_transition_queued_to_running(self):
        """Test transition from QUEUED to RUNNING"""
        sm = JobStateMachine()
        sm.transition(JobEvent.QUEUE)
        new_state = sm.transition(JobEvent.START)
        
        assert new_state == JobState.RUNNING
        assert sm.current_state == JobState.RUNNING
        assert len(sm.history) == 2
    
    def test_valid_transition_running_to_completed(self):
        """Test transition from RUNNING to COMPLETED"""
        sm = JobStateMachine()
        sm.transition(JobEvent.QUEUE)
        sm.transition(JobEvent.START)
        new_state = sm.transition(JobEvent.COMPLETE)
        
        assert new_state == JobState.COMPLETED
        assert sm.current_state == JobState.COMPLETED
    
    def test_valid_transition_running_to_failed(self):
        """Test transition from RUNNING to FAILED"""
        sm = JobStateMachine()
        sm.transition(JobEvent.QUEUE)
        sm.transition(JobEvent.START)
        new_state = sm.transition(JobEvent.FAIL, metadata={"error": "test error"})
        
        assert new_state == JobState.FAILED
        assert sm.current_state == JobState.FAILED
    
    def test_valid_transition_running_to_cancelled(self):
        """Test transition from RUNNING to CANCELLED"""
        sm = JobStateMachine()
        sm.transition(JobEvent.QUEUE)
        sm.transition(JobEvent.START)
        new_state = sm.transition(JobEvent.CANCEL)
        
        assert new_state == JobState.CANCELLED
        assert sm.current_state == JobState.CANCELLED
    
    def test_valid_transition_running_to_paused(self):
        """Test transition from RUNNING to PAUSED"""
        sm = JobStateMachine()
        sm.transition(JobEvent.QUEUE)
        sm.transition(JobEvent.START)
        new_state = sm.transition(JobEvent.PAUSE)
        
        assert new_state == JobState.PAUSED
        assert sm.current_state == JobState.PAUSED
    
    def test_valid_transition_paused_to_running(self):
        """Test transition from PAUSED to RUNNING"""
        sm = JobStateMachine()
        sm.transition(JobEvent.QUEUE)
        sm.transition(JobEvent.START)
        sm.transition(JobEvent.PAUSE)
        new_state = sm.transition(JobEvent.RESUME)
        
        assert new_state == JobState.RUNNING
        assert sm.current_state == JobState.RUNNING
    
    def test_valid_transition_failed_to_queued_retry(self):
        """Test retry transition from FAILED to QUEUED"""
        sm = JobStateMachine()
        sm.transition(JobEvent.QUEUE)
        sm.transition(JobEvent.START)
        sm.transition(JobEvent.FAIL)
        new_state = sm.transition(JobEvent.RETRY)
        
        assert new_state == JobState.QUEUED
        assert sm.current_state == JobState.QUEUED
    
    def test_invalid_transition_raises_error(self):
        """Test invalid transition raises ValueError"""
        sm = JobStateMachine()
        
        with pytest.raises(ValueError, match="Invalid transition"):
            sm.transition(JobEvent.START)  # Can't START from CREATED
    
    def test_terminal_state_prevents_transition(self):
        """Test transition from terminal state raises error"""
        sm = JobStateMachine()
        sm.transition(JobEvent.QUEUE)
        sm.transition(JobEvent.START)
        sm.transition(JobEvent.COMPLETE)
        
        with pytest.raises(ValueError, match="Cannot transition from terminal state"):
            sm.transition(JobEvent.RETRY)
    
    def test_can_transition(self):
        """Test can_transition check"""
        sm = JobStateMachine()
        
        assert sm.can_transition(JobEvent.QUEUE) is True
        assert sm.can_transition(JobEvent.START) is False
        
        sm.transition(JobEvent.QUEUE)
        assert sm.can_transition(JobEvent.START) is True
        assert sm.can_transition(JobEvent.COMPLETE) is False
    
    def test_transition_history(self):
        """Test transition history is recorded"""
        sm = JobStateMachine()
        sm.transition(JobEvent.QUEUE)
        sm.transition(JobEvent.START)
        sm.transition(JobEvent.COMPLETE)
        
        history = sm.get_history()
        assert len(history) == 3
        
        assert history[0].from_state == JobState.CREATED
        assert history[0].to_state == JobState.QUEUED
        assert history[0].event == JobEvent.QUEUE
        
        assert history[1].from_state == JobState.QUEUED
        assert history[1].to_state == JobState.RUNNING
        
        assert history[2].from_state == JobState.RUNNING
        assert history[2].to_state == JobState.COMPLETED
    
    def test_transition_metadata(self):
        """Test transition metadata is stored"""
        sm = JobStateMachine()
        sm.transition(JobEvent.QUEUE)
        sm.transition(JobEvent.START, metadata={"worker_id": "worker-1"})
        
        history = sm.get_history()
        assert history[1].metadata["worker_id"] == "worker-1"
    
    def test_is_terminal(self):
        """Test is_terminal check"""
        sm = JobStateMachine()
        
        assert sm.is_terminal() is False
        
        sm.transition(JobEvent.QUEUE)
        assert sm.is_terminal() is False
        
        sm.transition(JobEvent.START)
        assert sm.is_terminal() is False
        
        sm.transition(JobEvent.COMPLETE)
        assert sm.is_terminal() is True
    
    def test_register_and_execute_hook(self):
        """Test hook registration and execution"""
        sm = JobStateMachine()
        hook_called = []
        
        def on_start(transition):
            hook_called.append(transition.to_state)
        
        sm.register_hook(JobState.QUEUED, JobState.RUNNING, on_start)
        sm.transition(JobEvent.QUEUE)
        sm.transition(JobEvent.START)
        
        assert len(hook_called) == 1
        assert hook_called[0] == JobState.RUNNING
    
    def test_multiple_hooks_on_same_transition(self):
        """Test multiple hooks execute on same transition"""
        sm = JobStateMachine()
        call_order = []
        
        def hook1(transition):
            call_order.append("hook1")
        
        def hook2(transition):
            call_order.append("hook2")
        
        sm.register_hook(JobState.QUEUED, JobState.RUNNING, hook1)
        sm.register_hook(JobState.QUEUED, JobState.RUNNING, hook2)
        
        sm.transition(JobEvent.QUEUE)
        sm.transition(JobEvent.START)
        
        assert call_order == ["hook1", "hook2"]
    
    def test_hook_error_doesnt_break_transition(self):
        """Test hook error doesn't prevent transition"""
        sm = JobStateMachine()
        
        def failing_hook(transition):
            raise RuntimeError("Hook failed")
        
        sm.register_hook(JobState.QUEUED, JobState.RUNNING, failing_hook)
        sm.transition(JobEvent.QUEUE)
        
        # Transition should succeed despite hook failure
        new_state = sm.transition(JobEvent.START)
        assert new_state == JobState.RUNNING
    
    def test_repr(self):
        """Test string representation"""
        sm = JobStateMachine()
        sm.transition(JobEvent.QUEUE)
        
        repr_str = repr(sm)
        assert "JobStateMachine" in repr_str
        assert "queued" in repr_str
        assert "transitions=1" in repr_str


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
