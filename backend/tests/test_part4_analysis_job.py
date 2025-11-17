"""
Tests for Analysis Job Domain Model

Part 4: Architecture Blueprint
Tests DOMAIN_MODEL_001 implementation
"""

import pytest
from datetime import datetime

from models.analysis_job import AnalysisJob, Ticker
from models.job_state import JobState, JobEvent


class TestTicker:
    """Test Ticker value object"""
    
    def test_create_ticker(self):
        """Test creating ticker"""
        ticker = Ticker("AAPL")
        assert ticker.symbol == "AAPL"
    
    def test_ticker_normalization(self):
        """Test ticker is normalized to uppercase"""
        ticker = Ticker("aapl")
        assert ticker.symbol == "AAPL"
        
        ticker2 = Ticker("  msft  ")
        assert ticker2.symbol == "MSFT"
    
    def test_invalid_ticker_empty(self):
        """Test empty ticker raises error"""
        with pytest.raises(ValueError, match="non-empty string"):
            Ticker("")
    
    def test_invalid_ticker_length(self):
        """Test ticker length validation"""
        with pytest.raises(ValueError, match="1-10 characters"):
            Ticker("TOOLONGTICKER")  # 13 characters
    
    def test_ticker_equality(self):
        """Test ticker equality comparison"""
        ticker1 = Ticker("AAPL")
        ticker2 = Ticker("AAPL")
        ticker3 = Ticker("MSFT")
        
        assert ticker1 == ticker2
        assert ticker1 != ticker3
    
    def test_ticker_hashable(self):
        """Test ticker can be used in sets/dicts"""
        tickers = {Ticker("AAPL"), Ticker("MSFT"), Ticker("AAPL")}
        assert len(tickers) == 2
    
    def test_ticker_str(self):
        """Test ticker string representation"""
        ticker = Ticker("AAPL")
        assert str(ticker) == "AAPL"


class TestAnalysisJob:
    """Test AnalysisJob domain model"""
    
    def test_create_job_minimal(self):
        """Test creating job with minimal parameters"""
        job = AnalysisJob(
            id="job-123",
            tickers=[Ticker("AAPL")]
        )
        
        assert job.id == "job-123"
        assert len(job.tickers) == 1
        assert job.tickers[0].symbol == "AAPL"
        assert job.capital == 100000
        assert job.use_demo_data is False
    
    def test_create_job_full_params(self):
        """Test creating job with all parameters"""
        job = AnalysisJob(
            id="job-456",
            tickers=[Ticker("AAPL"), Ticker("MSFT")],
            indicators=["RSI", "MACD"],
            capital=50000,
            use_demo_data=True
        )
        
        assert job.id == "job-456"
        assert len(job.tickers) == 2
        assert job.indicators == ["RSI", "MACD"]
        assert job.capital == 50000
        assert job.use_demo_data is True
    
    def test_invariant_at_least_one_ticker(self):
        """Test job must have at least 1 ticker"""
        with pytest.raises(ValueError, match="at least 1 ticker"):
            AnalysisJob(id="job-1", tickers=[])
    
    def test_invariant_max_100_tickers(self):
        """Test job cannot have more than 100 tickers"""
        tickers = [Ticker(f"T{i:03d}") for i in range(101)]
        
        with pytest.raises(ValueError, match="cannot have more than 100"):
            AnalysisJob(id="job-1", tickers=tickers)
    
    def test_invariant_positive_capital(self):
        """Test capital must be positive"""
        with pytest.raises(ValueError, match="Capital must be positive"):
            AnalysisJob(
                id="job-1",
                tickers=[Ticker("AAPL")],
                capital=0
            )
        
        with pytest.raises(ValueError, match="Capital must be positive"):
            AnalysisJob(
                id="job-1",
                tickers=[Ticker("AAPL")],
                capital=-1000
            )
    
    def test_initial_state(self):
        """Test initial job state"""
        job = AnalysisJob(id="job-1", tickers=[Ticker("AAPL")])
        
        assert job.status == "created"
        assert job.completed_count == 0
        assert job.error_count == 0
        assert job.progress_percentage == 0.0
        assert job.is_complete is False
        assert job.is_terminal is False
    
    def test_total_tickers(self):
        """Test total_tickers property"""
        job = AnalysisJob(
            id="job-1",
            tickers=[Ticker("AAPL"), Ticker("MSFT"), Ticker("GOOGL")]
        )
        
        assert job.total_tickers == 3
    
    def test_progress_calculation(self):
        """Test progress percentage calculation"""
        job = AnalysisJob(
            id="job-1",
            tickers=[Ticker("AAPL"), Ticker("MSFT"), Ticker("GOOGL"), Ticker("AMZN")]
        )
        
        assert job.progress_percentage == 0.0
        
        job.increment_completed()
        assert job.progress_percentage == 25.0
        
        job.increment_completed()
        assert job.progress_percentage == 50.0
        
        job.increment_completed()
        assert job.progress_percentage == 75.0
        
        job.increment_completed()
        assert job.progress_percentage == 100.0
    
    def test_queue_transition(self):
        """Test queue transition"""
        job = AnalysisJob(id="job-1", tickers=[Ticker("AAPL")])
        
        job.queue()
        assert job.status == "queued"
    
    def test_start_transition(self):
        """Test start transition"""
        job = AnalysisJob(id="job-1", tickers=[Ticker("AAPL")])
        job.queue()
        
        assert job.started_at is None
        job.start()
        
        assert job.status == "running"
        assert job.started_at is not None
        assert isinstance(job.started_at, datetime)
    
    def test_increment_completed(self):
        """Test incrementing completed count"""
        job = AnalysisJob(
            id="job-1",
            tickers=[Ticker("AAPL"), Ticker("MSFT")]
        )
        
        job.increment_completed()
        assert job.completed_count == 1
        
        job.increment_completed()
        assert job.completed_count == 2
        assert job.is_complete is True
    
    def test_increment_completed_validates_invariants(self):
        """Test increment_completed enforces invariants"""
        job = AnalysisJob(id="job-1", tickers=[Ticker("AAPL")])
        
        job.increment_completed()
        
        with pytest.raises(ValueError, match="Completed .* > Total"):
            job.increment_completed()
    
    def test_add_error(self):
        """Test adding error"""
        job = AnalysisJob(id="job-1", tickers=[Ticker("AAPL")])
        
        job.add_error("AAPL", "Fetch failed")
        
        assert job.error_count == 1
        assert len(job.errors) == 1
        assert job.errors[0]["ticker"] == "AAPL"
        assert job.errors[0]["error"] == "Fetch failed"
        assert "timestamp" in job.errors[0]
    
    def test_complete_transition(self):
        """Test complete transition"""
        job = AnalysisJob(id="job-1", tickers=[Ticker("AAPL")])
        job.queue()
        job.start()
        
        assert job.completed_at is None
        job.complete()
        
        assert job.status == "completed"
        assert job.completed_at is not None
        assert job.is_terminal is True
    
    def test_fail_transition(self):
        """Test fail transition"""
        job = AnalysisJob(id="job-1", tickers=[Ticker("AAPL")])
        job.queue()
        job.start()
        
        job.fail("Critical error")
        
        assert job.status == "failed"
        assert job.completed_at is not None
        # FAILED is not terminal (allows retry)
        assert job.is_terminal is False
    
    def test_cancel_transition(self):
        """Test cancel transition"""
        job = AnalysisJob(id="job-1", tickers=[Ticker("AAPL")])
        job.queue()
        job.start()
        
        job.cancel()
        
        assert job.status == "cancelled"
        assert job.completed_at is not None
        assert job.is_terminal is True
    
    def test_can_be_cancelled(self):
        """Test can_be_cancelled check"""
        job = AnalysisJob(id="job-1", tickers=[Ticker("AAPL")])
        
        # Can't cancel from CREATED
        assert job.can_be_cancelled() is False
        
        job.queue()
        # Can cancel from QUEUED
        assert job.can_be_cancelled() is True
        
        job.start()
        # Can cancel from RUNNING
        assert job.can_be_cancelled() is True
        
        job.complete()
        # Can't cancel from COMPLETED (terminal)
        assert job.can_be_cancelled() is False
    
    def test_pause_resume(self):
        """Test pause and resume"""
        job = AnalysisJob(id="job-1", tickers=[Ticker("AAPL")])
        job.queue()
        job.start()
        
        job.pause()
        assert job.status == "paused"
        
        job.resume()
        assert job.status == "running"
    
    def test_retry_failed_job(self):
        """Test retrying failed job"""
        job = AnalysisJob(id="job-1", tickers=[Ticker("AAPL"), Ticker("MSFT")])
        job.queue()
        job.start()
        job.increment_completed()
        job.add_error("MSFT", "Error")
        job.fail("Failed")
        
        assert job.completed_count == 1
        assert job.error_count == 1
        
        job.retry()
        
        assert job.status == "queued"
        assert job.completed_count == 0
        assert job.error_count == 0
        assert len(job.errors) == 0
        assert job.started_at is None
        assert job.completed_at is None
    
    def test_to_dict(self):
        """Test serialization to dict"""
        job = AnalysisJob(
            id="job-123",
            tickers=[Ticker("AAPL"), Ticker("MSFT")],
            indicators=["RSI", "MACD"],
            capital=50000,
            use_demo_data=True
        )
        job.queue()
        job.start()
        job.increment_completed()
        
        data = job.to_dict()
        
        assert data["id"] == "job-123"
        assert data["status"] == "running"
        assert data["tickers"] == ["AAPL", "MSFT"]
        assert data["indicators"] == ["RSI", "MACD"]
        assert data["capital"] == 50000
        assert data["use_demo_data"] is True
        assert data["total"] == 2
        assert data["completed"] == 1
        assert data["errors"] == 0
        assert data["progress"] == 50.0
        assert data["is_complete"] is False
        assert data["is_terminal"] is False
        assert data["created_at"] is not None
        assert data["started_at"] is not None
        assert data["completed_at"] is None
    
    def test_repr(self):
        """Test string representation"""
        job = AnalysisJob(
            id="job-123",
            tickers=[Ticker("AAPL"), Ticker("MSFT")]
        )
        
        repr_str = repr(job)
        assert "job-123" in repr_str
        assert "created" in repr_str
        assert "tickers=2" in repr_str


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
