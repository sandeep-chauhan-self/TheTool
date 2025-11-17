"""
Part 4: Pipeline and Logging - Test Suite

Tests for:
- PIPELINE_ARCHITECTURE_001: Data Pipeline
- CROSS_CUTTING_001: Structured Logging
"""

import pytest
import logging
import json
from io import StringIO
from pipeline.data_pipeline import (
    DataPipeline,
    PipelineResult,
    PipelineStage,
    StageStatus
)
from app_logging.structured_logging import (
    CorrelationFilter,
    JSONFormatter,
    setup_logging,
    set_correlation_id,
    get_correlation_id,
    clear_correlation_id,
    CorrelationContext,
    log_with_context
)


# ============================================================================
# Data Pipeline Tests
# ============================================================================

class TestPipelineResult:
    """Test PipelineResult data class"""
    
    def test_create_success_result(self):
        """Test creating successful result"""
        result = PipelineResult(success=True, data={"key": "value"})
        assert result.success
        assert result.data == {"key": "value"}
        assert not result.has_errors
        assert not result.has_warnings
    
    def test_create_failure_result(self):
        """Test creating failure result"""
        result = PipelineResult(
            success=False,
            errors=["Error 1", "Error 2"]
        )
        assert not result.success
        assert result.has_errors
        assert len(result.errors) == 2
    
    def test_add_error(self):
        """Test adding errors"""
        result = PipelineResult(success=True, data={})
        assert not result.has_errors
        
        result.add_error("Test error")
        assert result.has_errors
        assert result.errors == ["Test error"]
    
    def test_add_warning(self):
        """Test adding warnings"""
        result = PipelineResult(success=True, data={})
        assert not result.has_warnings
        
        result.add_warning("Test warning")
        assert result.has_warnings
        assert result.warnings == ["Test warning"]


class TestPipelineStage:
    """Test PipelineStage execution"""
    
    def test_stage_success(self):
        """Test successful stage execution"""
        def double_value(data):
            return data * 2
        
        stage = PipelineStage(name="Double", func=double_value)
        result = stage.execute(5)
        
        assert result.success
        assert result.data == 10
        assert stage.status == StageStatus.SUCCESS
    
    def test_stage_with_pipeline_result(self):
        """Test stage returning PipelineResult"""
        def return_result(data):
            return PipelineResult(
                success=True,
                data=data + 10,
                warnings=["Test warning"]
            )
        
        stage = PipelineStage(name="Add10", func=return_result)
        result = stage.execute(5)
        
        assert result.success
        assert result.data == 15
        assert result.has_warnings
    
    def test_stage_exception_no_handler(self):
        """Test stage exception without error handler"""
        def raise_error(data):
            raise ValueError("Test error")
        
        stage = PipelineStage(name="Faulty", func=raise_error)
        result = stage.execute(5)
        
        assert not result.success
        assert stage.status == StageStatus.FAILED
        assert result.has_errors
        assert "Test error" in result.errors[0]
    
    def test_stage_exception_with_handler(self):
        """Test stage exception with error handler"""
        def raise_error(data):
            raise ValueError("Test error")
        
        def recover(data, errors):
            return data * 2  # Recovery logic
        
        stage = PipelineStage(
            name="Recoverable",
            func=raise_error,
            error_handler=recover
        )
        result = stage.execute(5)
        
        assert result.success
        assert result.data == 10
        assert stage.status == StageStatus.SUCCESS
        assert result.has_warnings  # Error was recovered
    
    def test_stage_disabled(self):
        """Test disabled stage is skipped"""
        def never_called(data):
            raise AssertionError("Should not be called")
        
        stage = PipelineStage(
            name="Disabled",
            func=never_called,
            enabled=False
        )
        result = stage.execute(5)
        
        assert result.success
        assert result.data == 5  # Input passed through
        assert stage.status == StageStatus.SKIPPED


class TestDataPipeline:
    """Test DataPipeline execution"""
    
    def test_simple_pipeline(self):
        """Test simple 3-stage pipeline"""
        pipeline = DataPipeline(name="Simple")
        
        pipeline.add_stage(
            name="Add 10",
            func=lambda x: x + 10
        ).add_stage(
            name="Multiply by 2",
            func=lambda x: x * 2
        ).add_stage(
            name="Subtract 5",
            func=lambda x: x - 5
        )
        
        result = pipeline.execute(5)
        
        # (5 + 10) * 2 - 5 = 25
        assert result.success
        assert result.data == 25
        assert len(result.stage_results) == 3
    
    def test_pipeline_with_failure_non_critical(self):
        """Test pipeline continues after non-critical failure"""
        pipeline = DataPipeline(name="Resilient")
        
        pipeline.add_stage(
            name="Add 10",
            func=lambda x: x + 10
        ).add_stage(
            name="Fail",
            func=lambda x: 1/0,  # Raises ZeroDivisionError
            critical=False
        ).add_stage(
            name="Multiply by 2",
            func=lambda x: x * 2
        )
        
        result = pipeline.execute(5)
        
        # Should complete with output from stage 1 multiplied by stage 3
        # (5 + 10) = 15, then stage 2 fails, then 15 * 2 = 30
        assert result.success
        assert result.data == 30
        assert result.has_warnings
    
    def test_pipeline_with_failure_critical(self):
        """Test pipeline aborts on critical failure"""
        pipeline = DataPipeline(name="Critical")
        
        pipeline.add_stage(
            name="Add 10",
            func=lambda x: x + 10
        ).add_stage(
            name="Critical Fail",
            func=lambda x: 1/0,  # Raises ZeroDivisionError
            critical=True
        ).add_stage(
            name="Never Reached",
            func=lambda x: x * 2
        )
        
        result = pipeline.execute(5)
        
        assert not result.success
        assert result.has_errors
        # Stage 3 should not execute
        assert len(result.stage_results) == 2
    
    def test_pipeline_with_error_recovery(self):
        """Test pipeline with error recovery handler"""
        def use_fallback(data, errors):
            return data + 100  # Fallback value
        
        pipeline = DataPipeline(name="Recovery")
        
        pipeline.add_stage(
            name="Add 10",
            func=lambda x: x + 10
        ).add_stage(
            name="Fail with Recovery",
            func=lambda x: 1/0,
            error_handler=use_fallback
        ).add_stage(
            name="Multiply by 2",
            func=lambda x: x * 2
        )
        
        result = pipeline.execute(5)
        
        # (5 + 10) = 15, then fallback to 15 + 100 = 115, then 115 * 2 = 230
        assert result.success
        assert result.data == 230
        assert result.has_warnings  # Recovery triggered
    
    def test_pipeline_enable_disable_stage(self):
        """Test enabling/disabling stages"""
        pipeline = DataPipeline(name="Toggle")
        
        pipeline.add_stage(
            name="Add 10",
            func=lambda x: x + 10
        ).add_stage(
            name="Multiply by 2",
            func=lambda x: x * 2
        ).add_stage(
            name="Subtract 5",
            func=lambda x: x - 5
        )
        
        # Disable middle stage
        pipeline.disable_stage("Multiply by 2")
        
        result = pipeline.execute(5)
        
        # 5 + 10 - 5 = 10 (multiply stage skipped)
        assert result.success
        assert result.data == 10
        
        # Re-enable
        pipeline.enable_stage("Multiply by 2")
        pipeline.reset()
        
        result = pipeline.execute(5)
        
        # (5 + 10) * 2 - 5 = 25
        assert result.success
        assert result.data == 25
    
    def test_pipeline_get_stage(self):
        """Test getting stage by name"""
        pipeline = DataPipeline()
        pipeline.add_stage("Test Stage", func=lambda x: x)
        
        stage = pipeline.get_stage("Test Stage")
        assert stage is not None
        assert stage.name == "Test Stage"
        
        missing = pipeline.get_stage("Missing")
        assert missing is None


class TestPipelineIntegration:
    """Integration tests for realistic pipeline scenarios"""
    
    def test_data_processing_pipeline(self):
        """Test realistic data processing pipeline"""
        # Simulate data acquisition -> validation -> transformation
        def acquire_data(ticker):
            return {"ticker": ticker, "price": 100}
        
        def validate_data(data):
            if data["price"] <= 0:
                return PipelineResult(
                    success=False,
                    errors=["Invalid price"]
                )
            return PipelineResult(success=True, data=data)
        
        def transform_data(data):
            data["price_double"] = data["price"] * 2
            return data
        
        pipeline = DataPipeline(name="DataProcessing")
        
        pipeline.add_stage(
            name="Acquire",
            func=acquire_data
        ).add_stage(
            name="Validate",
            func=validate_data,
            critical=True
        ).add_stage(
            name="Transform",
            func=transform_data
        )
        
        result = pipeline.execute("AAPL")
        
        assert result.success
        assert result.data["ticker"] == "AAPL"
        assert result.data["price"] == 100
        assert result.data["price_double"] == 200


# ============================================================================
# Structured Logging Tests
# ============================================================================

class TestCorrelationFilter:
    """Test correlation ID filter"""
    
    def test_filter_adds_correlation_id(self):
        """Test filter adds correlation_id to record"""
        set_correlation_id("test-123")
        
        filter_obj = CorrelationFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test",
            args=(),
            exc_info=None
        )
        
        filter_obj.filter(record)
        assert record.correlation_id == "test-123"
        
        clear_correlation_id()
    
    def test_filter_none_correlation_id(self):
        """Test filter with no correlation ID set"""
        clear_correlation_id()
        
        filter_obj = CorrelationFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test",
            args=(),
            exc_info=None
        )
        
        filter_obj.filter(record)
        assert record.correlation_id == "none"


class TestJSONFormatter:
    """Test JSON formatter"""
    
    def test_format_basic_record(self):
        """Test formatting basic log record"""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.correlation_id = "test-123"
        record.funcName = "test_func"
        record.module = "test"
        
        output = formatter.format(record)
        log_dict = json.loads(output)
        
        assert log_dict["level"] == "INFO"
        assert log_dict["logger"] == "test.logger"
        assert log_dict["correlation_id"] == "test-123"
        assert log_dict["message"] == "Test message"
        assert log_dict["module"] == "test"
        assert log_dict["function"] == "test_func"
        assert log_dict["line"] == 42
        assert "timestamp" in log_dict
    
    def test_format_with_exception(self):
        """Test formatting log with exception"""
        formatter = JSONFormatter()
        
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
            
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="Error occurred",
                args=(),
                exc_info=exc_info
            )
            record.correlation_id = "test-123"
            record.funcName = "test"
            record.module = "test"
            
            output = formatter.format(record)
            log_dict = json.loads(output)
            
            assert "exception" in log_dict
            assert "ValueError: Test error" in log_dict["exception"]
    
    def test_format_with_extra_fields(self):
        """Test formatting with extra fields"""
        formatter = JSONFormatter(include_extra=True)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None
        )
        record.correlation_id = "test-123"
        record.funcName = "test"
        record.module = "test"
        
        # Add custom fields
        record.user_id = 12345
        record.ip_address = "192.168.1.1"
        
        output = formatter.format(record)
        log_dict = json.loads(output)
        
        assert log_dict["user_id"] == 12345
        assert log_dict["ip_address"] == "192.168.1.1"


class TestSetupLogging:
    """Test logging setup"""
    
    def test_setup_json_logging(self):
        """Test setup with JSON format"""
        # Create string buffer to capture logs
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        
        logger = setup_logging(log_level="INFO", log_format="json", handler=handler)
        
        assert logger is not None
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0].formatter, JSONFormatter)
    
    def test_setup_text_logging(self):
        """Test setup with text format"""
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        
        logger = setup_logging(log_level="DEBUG", log_format="text", handler=handler)
        
        assert logger is not None
        assert logger.level == logging.DEBUG


class TestCorrelationID:
    """Test correlation ID management"""
    
    def test_set_correlation_id_explicit(self):
        """Test setting explicit correlation ID"""
        corr_id = set_correlation_id("my-request-123")
        assert corr_id == "my-request-123"
        assert get_correlation_id() == "my-request-123"
        clear_correlation_id()
    
    def test_set_correlation_id_generated(self):
        """Test generating correlation ID"""
        corr_id = set_correlation_id()
        assert corr_id is not None
        assert len(corr_id) > 0
        assert get_correlation_id() == corr_id
        clear_correlation_id()
    
    def test_get_correlation_id_none(self):
        """Test getting correlation ID when not set"""
        clear_correlation_id()
        assert get_correlation_id() is None
    
    def test_clear_correlation_id(self):
        """Test clearing correlation ID"""
        set_correlation_id("test-123")
        assert get_correlation_id() == "test-123"
        
        clear_correlation_id()
        assert get_correlation_id() is None


class TestCorrelationContext:
    """Test correlation context manager"""
    
    def test_context_manager_with_id(self):
        """Test context manager with explicit ID"""
        with CorrelationContext("ctx-123") as corr_id:
            assert corr_id == "ctx-123"
            assert get_correlation_id() == "ctx-123"
        
        # Should be cleared after context
        assert get_correlation_id() is None
    
    def test_context_manager_generated(self):
        """Test context manager with generated ID"""
        with CorrelationContext() as corr_id:
            assert corr_id is not None
            assert get_correlation_id() == corr_id
        
        assert get_correlation_id() is None
    
    def test_nested_contexts(self):
        """Test nested correlation contexts"""
        set_correlation_id("outer-123")
        
        with CorrelationContext("inner-456") as inner_id:
            assert get_correlation_id() == "inner-456"
        
        # Should restore outer ID
        assert get_correlation_id() == "outer-123"
        
        clear_correlation_id()


class TestLogWithContext:
    """Test log_with_context convenience function"""
    
    def test_log_with_extra_fields(self):
        """Test logging with extra fields"""
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        setup_logging(log_level="INFO", log_format="json", handler=handler)
        
        logger = logging.getLogger("test")
        set_correlation_id("test-123")
        
        log_with_context(
            logger,
            "info",
            "User action",
            user_id=456,
            action="login"
        )
        
        # Get log output
        log_output = log_stream.getvalue()
        log_dict = json.loads(log_output.strip().split('\n')[-1])
        
        assert log_dict["message"] == "User action"
        assert log_dict["correlation_id"] == "test-123"
        assert log_dict["user_id"] == 456
        assert log_dict["action"] == "login"
        
        clear_correlation_id()


class TestLoggingIntegration:
    """Integration tests for logging"""
    
    def test_full_logging_workflow(self):
        """Test complete logging workflow"""
        # Setup logging
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        setup_logging(log_level="INFO", log_format="json", handler=handler)
        
        logger = logging.getLogger("integration.test")
        
        # Simulate request processing
        with CorrelationContext("req-789") as corr_id:
            logger.info("Request started", extra={"endpoint": "/api/analyze"})
            logger.info("Processing data")
            logger.info("Request completed", extra={"status": 200})
        
        # Parse logs
        logs = log_stream.getvalue().strip().split('\n')
        log_dicts = [json.loads(log) for log in logs if log]
        
        # Verify all logs have same correlation ID
        assert all(log["correlation_id"] == "req-789" for log in log_dicts[-3:])
        
        # Verify messages
        assert any("Request started" in log["message"] for log in log_dicts)
        assert any("Processing data" in log["message"] for log in log_dicts)
        assert any("Request completed" in log["message"] for log in log_dicts)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
