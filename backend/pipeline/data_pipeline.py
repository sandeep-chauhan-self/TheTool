"""
Enterprise Data Pipeline with Error Isolation

Part 4: Architecture Blueprint
PIPELINE_ARCHITECTURE_001: Multi-stage Data Pipeline

7-Stage Pipeline:
1. Data Acquisition - Fetch ticker data
2. Data Validation - Validate OHLCV data
3. Indicator Computation - Calculate indicators in parallel
4. Vote Aggregation - Aggregate signals
5. Trade Calculation - Calculate entry/stop/target
6. Trade Validation - Validate risk/reward
7. Persistence - Save results

Key Features:
- Error isolation (stage failures don't cascade)
- Error recovery handlers per stage
- Partial results preserved
- Independent stage testing
- Structured logging
"""

from typing import Any, Callable, Optional, List, Dict
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class StageStatus(Enum):
    """Pipeline stage execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PipelineResult:
    """
    Result of pipeline or stage execution
    
    Attributes:
        success: Whether execution succeeded
        data: Output data from stage/pipeline
        errors: List of error messages
        warnings: List of warning messages
        stage_results: Results from individual stages (for full pipeline)
    """
    success: bool
    data: Any = None
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    stage_results: Optional[Dict[str, 'PipelineResult']] = None
    
    def add_error(self, error: str) -> None:
        """Add error message"""
        if self.errors is None:
            self.errors = []
        self.errors.append(error)
    
    def add_warning(self, warning: str) -> None:
        """Add warning message"""
        if self.warnings is None:
            self.warnings = []
        self.warnings.append(warning)
    
    @property
    def has_errors(self) -> bool:
        """Check if result has errors"""
        return self.errors is not None and len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if result has warnings"""
        return self.warnings is not None and len(self.warnings) > 0


@dataclass
class PipelineStage:
    """
    Single stage in data pipeline
    
    Attributes:
        name: Stage name (e.g., "Data Acquisition")
        func: Stage function (input) -> output or PipelineResult
        error_handler: Optional error recovery function
        critical: If True, abort pipeline on failure
        enabled: If False, skip this stage
    """
    name: str
    func: Callable[[Any], Any]
    error_handler: Optional[Callable[[Any, List[str]], Any]] = None
    critical: bool = False
    enabled: bool = True
    status: StageStatus = field(default=StageStatus.PENDING, init=False)
    
    def execute(self, input_data: Any) -> PipelineResult:
        """
        Execute this stage
        
        Args:
            input_data: Input from previous stage
        
        Returns:
            PipelineResult with success/failure information
        """
        if not self.enabled:
            logger.info(f"Stage '{self.name}' skipped (disabled)")
            self.status = StageStatus.SKIPPED
            return PipelineResult(
                success=True,
                data=input_data,
                warnings=[f"Stage '{self.name}' was skipped"]
            )
        
        self.status = StageStatus.RUNNING
        logger.info(f"Executing stage: {self.name}")
        
        try:
            result = self.func(input_data)
            
            # Handle different return types
            if isinstance(result, PipelineResult):
                if result.success:
                    self.status = StageStatus.SUCCESS
                    logger.info(f"Stage '{self.name}' completed successfully")
                else:
                    self.status = StageStatus.FAILED
                    logger.error(f"Stage '{self.name}' failed: {result.errors}")
                return result
            else:
                # Plain return value - success
                self.status = StageStatus.SUCCESS
                logger.info(f"Stage '{self.name}' completed successfully")
                return PipelineResult(success=True, data=result)
                
        except Exception as e:
            self.status = StageStatus.FAILED
            error_msg = f"Stage '{self.name}' raised exception: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # Try error handler
            if self.error_handler:
                try:
                    logger.info(f"Attempting error recovery for stage '{self.name}'")
                    recovered_data = self.error_handler(input_data, [str(e)])
                    self.status = StageStatus.SUCCESS
                    return PipelineResult(
                        success=True,
                        data=recovered_data,
                        warnings=[f"Stage '{self.name}' recovered from error: {str(e)}"]
                    )
                except Exception as recovery_error:
                    logger.error(f"Error recovery failed: {recovery_error}")
                    return PipelineResult(
                        success=False,
                        data=None,
                        errors=[error_msg, f"Recovery failed: {str(recovery_error)}"]
                    )
            else:
                return PipelineResult(
                    success=False,
                    data=None,
                    errors=[error_msg]
                )


class DataPipeline:
    """
    Multi-stage data pipeline with error isolation
    
    Each stage:
    - Has clear input/output contract
    - Handles its own errors
    - Can have error recovery handler
    - Can be marked as critical (abort on failure)
    - Can be enabled/disabled
    
    Usage:
        pipeline = DataPipeline()
        
        pipeline.add_stage(
            name="Data Acquisition",
            func=fetch_data,
            error_handler=use_demo_data,
            critical=True
        ).add_stage(
            name="Data Validation",
            func=validate_data,
            critical=True
        ).add_stage(
            name="Indicator Computation",
            func=compute_indicators,
            error_handler=compute_with_fallback
        )
        
        result = pipeline.execute({"ticker": "AAPL"})
        
        if result.success:
            print(f"Pipeline succeeded: {result.data}")
        else:
            print(f"Pipeline failed: {result.errors}")
    """
    
    def __init__(self, name: str = "DataPipeline"):
        self.name = name
        self.stages: List[PipelineStage] = []
    
    def add_stage(
        self,
        name: str,
        func: Callable[[Any], Any],
        error_handler: Optional[Callable[[Any, List[str]], Any]] = None,
        critical: bool = False,
        enabled: bool = True
    ) -> 'DataPipeline':
        """
        Add stage to pipeline
        
        Args:
            name: Stage name
            func: Stage function (input) -> output
            error_handler: Optional error recovery function (input, errors) -> output
            critical: If True, abort pipeline if this stage fails
            enabled: If False, skip this stage
        
        Returns:
            Self for chaining
        """
        stage = PipelineStage(
            name=name,
            func=func,
            error_handler=error_handler,
            critical=critical,
            enabled=enabled
        )
        self.stages.append(stage)
        return self
    
    def execute(self, initial_input: Any) -> PipelineResult:
        """
        Execute all pipeline stages
        
        Args:
            initial_input: Initial input data
        
        Returns:
            PipelineResult with final output or errors
        """
        logger.info(f"Starting pipeline '{self.name}' with {len(self.stages)} stages")
        
        current_data = initial_input
        all_errors: List[str] = []
        all_warnings: List[str] = []
        stage_results: Dict[str, PipelineResult] = {}
        
        for i, stage in enumerate(self.stages, 1):
            logger.debug(f"Stage {i}/{len(self.stages)}: {stage.name}")
            
            # Execute stage
            result = stage.execute(current_data)
            stage_results[stage.name] = result
            
            # Collect warnings
            if result.has_warnings:
                all_warnings.extend(result.warnings)
            
            if result.success:
                # Stage succeeded - use its output
                current_data = result.data
            else:
                # Stage failed
                all_errors.extend(result.errors)
                
                if stage.critical:
                    # Critical stage failed - abort pipeline
                    logger.error(
                        f"Critical stage '{stage.name}' failed. "
                        f"Aborting pipeline '{self.name}'"
                    )
                    return PipelineResult(
                        success=False,
                        data=None,
                        errors=all_errors,
                        warnings=all_warnings if all_warnings else None,
                        stage_results=stage_results
                    )
                else:
                    # Non-critical stage failed - continue with previous data
                    logger.warning(
                        f"Non-critical stage '{stage.name}' failed. "
                        f"Continuing with previous data"
                    )
                    all_warnings.append(
                        f"Stage '{stage.name}' failed but pipeline continued"
                    )
        
        # All stages completed
        logger.info(f"Pipeline '{self.name}' completed successfully")
        
        return PipelineResult(
            success=True,
            data=current_data,
            errors=all_errors if all_errors else None,
            warnings=all_warnings if all_warnings else None,
            stage_results=stage_results
        )
    
    def get_stage(self, name: str) -> Optional[PipelineStage]:
        """Get stage by name"""
        for stage in self.stages:
            if stage.name == name:
                return stage
        return None
    
    def enable_stage(self, name: str) -> bool:
        """Enable a stage by name"""
        stage = self.get_stage(name)
        if stage:
            stage.enabled = True
            return True
        return False
    
    def disable_stage(self, name: str) -> bool:
        """Disable a stage by name"""
        stage = self.get_stage(name)
        if stage:
            stage.enabled = False
            return True
        return False
    
    def reset(self) -> None:
        """Reset all stage statuses"""
        for stage in self.stages:
            stage.status = StageStatus.PENDING
    
    def __repr__(self) -> str:
        return (
            f"<DataPipeline name='{self.name}' "
            f"stages={len(self.stages)}>"
        )
