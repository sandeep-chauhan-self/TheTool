"""
Unified error handling and API utilities

Provides:
- StandardizedErrorResponse: Consistent JSON error format
- Global error handlers: Catch all uncaught exceptions
- JSON parsing utilities: Safe JSON deserialization with validation
- Input validators: Pydantic-based request validation
"""

import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from flask import jsonify
from pydantic import BaseModel, ValidationError, validator

logger = logging.getLogger(__name__)


class StandardizedErrorResponse:
    """
    Standard error response format for all API errors.
    
    Structure:
    {
        "error": {
            "code": "ERROR_CODE",
            "message": "Human-readable message",
            "details": {...},  # optional context
            "timestamp": "ISO8601"
        }
    }
    """
    
    @staticmethod
    def format(
        error_code: str,
        message: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], int]:
        """
        Format error response.
        
        Args:
            error_code: Machine-readable error code (e.g., 'VALIDATION_ERROR')
            message: Human-readable error message
            status_code: HTTP status code
            details: Additional context (optional)
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        from datetime import datetime
        response = {
            "error": {
                "code": error_code,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
        }
        if details:
            response["error"]["details"] = details
        return response, status_code
    
    @staticmethod
    def not_found(resource: str = "Resource"):
        """Not found error (404)"""
        return StandardizedErrorResponse.format(
            "NOT_FOUND",
            f"{resource} not found",
            404
        )
    
    @staticmethod
    def validation_error(message: str, details: Optional[Dict] = None):
        """Validation error (400)"""
        return StandardizedErrorResponse.format(
            "VALIDATION_ERROR",
            message,
            400,
            details
        )
    
    @staticmethod
    def auth_error(message: str = "Authentication required"):
        """Auth error (401)"""
        return StandardizedErrorResponse.format(
            "UNAUTHORIZED",
            message,
            401
        )
    
    @staticmethod
    def permission_error(message: str = "Permission denied"):
        """Permission error (403)"""
        return StandardizedErrorResponse.format(
            "FORBIDDEN",
            message,
            403
        )
    
    @staticmethod
    def server_error(message: str = "Internal server error", details: Optional[Dict] = None):
        """Server error (500)"""
        return StandardizedErrorResponse.format(
            "INTERNAL_ERROR",
            message,
            500,
            details
        )


class SafeJsonParser:
    """
    Safe JSON parsing with fallback and validation
    
    Handles:
    - Standard JSON parsing
    - Single-quote fallback (for mal-formatted data)
    - Error sanitization
    - None/empty defaults
    """
    
    @staticmethod
    def parse_string(
        value: str,
        default: Any = None,
        allow_single_quotes: bool = True
    ) -> Any:
        """
        Parse JSON string safely.
        
        Args:
            value: JSON string to parse
            default: Default if parsing fails
            allow_single_quotes: Try single-quote fallback
            
        Returns:
            Parsed object or default
        """
        if not value:
            return default
        
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            if allow_single_quotes:
                try:
                    # Try replacing single quotes with double quotes
                    fixed = value.replace("'", '"')
                    return json.loads(fixed)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON (even with quote fix): {value[:100]}")
                    return default
            logger.warning(f"Failed to parse JSON: {value[:100]}")
            return default
    
    @staticmethod
    def parse_error_field(error_value: str) -> Dict[str, Any]:
        """
        Parse error field from database (may be malformed JSON)
        
        Returns dict with:
        - parsed: bool (True if valid JSON)
        - errors: list or str (the parsed/raw errors)
        """
        parsed = SafeJsonParser.parse_string(error_value, default=[])
        return {
            "parsed": isinstance(parsed, list),
            "errors": parsed if parsed else [],
            "raw": error_value
        }


class RequestValidator:
    """Request validation schemas using Pydantic"""
    
    class AnalyzeRequest(BaseModel):
        """Schema for /analyze endpoint"""
        tickers: List[str]
        capital: Optional[float] = 100000.0
        indicators: Optional[List[str]] = None
        use_demo_data: Optional[bool] = True
        
        @validator('tickers')
        def validate_tickers(cls, v):
            if not v or len(v) == 0:
                raise ValueError('tickers list cannot be empty')
            if len(v) > 100:
                raise ValueError('tickers list cannot exceed 100 items')
            
            # Strip and uppercase
            stripped = [t.strip().upper() for t in v]
            
            # Check for empty strings after stripping
            empty_count = sum(1 for t in stripped if len(t) == 0)
            if empty_count > 0:
                raise ValueError(f'Found {empty_count} empty ticker(s) after stripping whitespace')
            
            # Check for invalid ticker format (should have exchange code like .NS or .BO)
            invalid_format = [t for t in stripped if '.' not in t]
            if invalid_format:
                raise ValueError(f'Invalid ticker format (missing exchange code): {invalid_format}. Expected format like TCS.NS or INFY.BO')
            
            # Check for duplicates
            unique_tickers = set(stripped)
            if len(unique_tickers) < len(stripped):
                duplicates = [t for t in unique_tickers if stripped.count(t) > 1]
                raise ValueError(f'Duplicate tickers found: {duplicates}')
            
            return stripped
        
        @validator('capital')
        def validate_capital(cls, v):
            if v <= 0:
                raise ValueError('capital must be positive')
            if v > 1_000_000:
                raise ValueError('capital cannot exceed 1,000,000')
            return v
    
    class BulkAnalyzeRequest(BaseModel):
        """Schema for /bulk-analyze endpoint"""
        symbols: Optional[List[str]] = None
        use_demo_data: Optional[bool] = True
        max_workers: Optional[int] = 5
        
        @validator('symbols')
        def validate_symbols(cls, v):
            if v is None:
                return v
            return [s.strip().upper() for s in v]
        
        @validator('max_workers')
        def validate_workers(cls, v):
            if v < 1 or v > 10:
                raise ValueError('max_workers must be between 1 and 10')
            return v
    
    class WatchlistAddRequest(BaseModel):
        """Schema for watchlist add endpoint"""
        symbol: str
        name: Optional[str] = None
        
        @validator('symbol')
        def validate_symbol(cls, v):
            if not v or len(v.strip()) == 0:
                raise ValueError('symbol cannot be empty')
            return v.strip().upper()


def validate_request(request_data: Dict[str, Any], schema_class):
    """
    Validate request data against Pydantic schema.
    
    Returns:
        (validated_data, error_response) tuple
        - If valid: (validated_data, None)
        - If invalid: (None, (error_dict, 400))
    """
    try:
        validated = schema_class(**request_data)
        return validated.dict(), None
    except ValidationError as e:
        error_details = []
        invalid_items = []
        
        for error in e.errors():
            field = ".".join(str(x) for x in error["loc"])
            error_details.append({
                "field": field,
                "message": error["msg"],
                "type": error["type"]
            })
            
            # For tickers field, try to extract the invalid values
            if field == "tickers" and "value" in error:
                invalid_items.append({
                    "value": error.get("value"),
                    "reason": error["msg"]
                })
        
        response, status = StandardizedErrorResponse.validation_error(
            "Request validation failed",
            {
                "validation_errors": error_details,
                "invalid_tickers": invalid_items if invalid_items else None,
                "request_data": {k: v for k, v in request_data.items() if k in ["tickers", "capital"]}
            }
        )
        return None, (response, status)


def register_error_handlers(app):
    """
    Register global error handlers with Flask app
    
    Handles:
    - 404: Not found
    - 400: Bad request
    - 500: Internal server errors
    - Unhandled exceptions
    
    Note: Stack traces only logged in debug mode (APP_ENV=development)
    """
    import config
    
    @app.errorhandler(404)
    def handle_not_found(error):
        response, status = StandardizedErrorResponse.not_found()
        return jsonify(response), status
    
    @app.errorhandler(400)
    def handle_bad_request(error):
        response, status = StandardizedErrorResponse.validation_error(str(error))
        return jsonify(response), status
    
    @app.errorhandler(500)
    def handle_server_error(error):
        # Log with stack trace only in development mode
        logger.error(
            f"Unhandled server error: {error}",
            exc_info=config.DEBUG  # Only include stack trace in debug mode
        )
        response, status = StandardizedErrorResponse.server_error(
            "An unexpected error occurred"
        )
        return jsonify(response), status
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        # Log with stack trace only in development mode
        logger.error(
            f"Unexpected exception: {error}",
            exc_info=config.DEBUG  # Only include stack trace in debug mode
        )
        response, status = StandardizedErrorResponse.server_error(
            "An unexpected error occurred",
            {"error_type": type(error).__name__}
        )
        return jsonify(response), status
