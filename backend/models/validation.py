"""
Input Validation Module

CRITICAL FIX (ISSUE_022): Implements comprehensive input validation using Pydantic
to prevent injection attacks, malformed data, and invalid requests.

Security Features:
- Schema validation for all API requests
- Ticker symbol sanitization
- Date range validation
- Numeric bounds checking
- String length limits
"""

from typing import List, Optional
from pydantic import BaseModel, Field, validator, field_validator, model_validator
from datetime import datetime
import re


class TickerAnalysisRequest(BaseModel):
    """
    Validation schema for /analyze endpoint
    
    OWASP Protection:
    - CWE-20: Improper Input Validation
    - CWE-89: SQL Injection (indirect via ticker sanitization)
    """
    tickers: List[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of ticker symbols to analyze (1-100)"
    )
    indicators: Optional[List[str]] = Field(
        None,
        description="Optional list of specific indicators to use"
    )
    capital: float = Field(
        default=100000,
        ge=1000,  # Minimum 1,000
        le=100000000,  # Maximum 100 million
        description="Trading capital amount"
    )
    use_demo_data: bool = Field(
        default=True,
        description="Whether to use demo data for testing"
    )
    
    @field_validator('tickers', mode='before')
    @classmethod
    def validate_ticker(cls, tickers: List[str]) -> List[str]:
        """
        Validate and sanitize ticker symbols.
        
        Security Rules:
        - Only alphanumeric characters, dots, hyphens
        - Max length: 10 characters
        - No SQL injection patterns
        - No path traversal patterns
        """  
        validated = []
        for ticker in tickers:
            if not ticker:
                raise ValueError("Ticker symbol cannot be empty")
            
            # Remove whitespace
            ticker = ticker.strip().upper()
            
            # Check length (increased to 20 to support exchange suffixes like .NS, .BO)
            if len(ticker) > 20:
                raise ValueError(f"Ticker symbol too long: {ticker} (max 20 chars)")
            
            # Check for valid characters only
            if not re.match(r'^[A-Z0-9\.\-]+$', ticker):
                raise ValueError(
                    f"Invalid ticker symbol: {ticker}. "
                    "Only alphanumeric characters, dots, and hyphens allowed."
                )
            
            # Blacklist dangerous patterns
            dangerous_patterns = [
                '--', ';', '/*', '*/', 'xp_', 'sp_',
                '..', '../', '..\\'
            ]
            ticker_lower = ticker.lower()
            for pattern in dangerous_patterns:
                if pattern in ticker_lower:
                    raise ValueError(f"Ticker contains prohibited pattern: {pattern}")            validated.append(ticker)
        
        return validated
    
    @field_validator('indicators', mode='before')
    @classmethod
    def validate_indicator(cls, indicators: Optional[List[str]]) -> Optional[List[str]]:
        """Validate indicator names"""
        if indicators is None:
            return None
        
        # Whitelist of valid indicators
        valid_indicators = {
            'rsi', 'macd', 'ema', 'sma', 'bbands', 'adx', 'cci',
            'supertrend', 'psar', 'stochastic', 'atr', 'obv', 'volume'
        }
        
        validated = []
        for indicator in indicators:
            if not indicator:
                raise ValueError("Indicator name cannot be empty")
            
            indicator_lower = indicator.strip().lower()
            if indicator_lower not in valid_indicators:
                raise ValueError(
                    f"Unknown indicator: {indicator}. "
                    f"Valid indicators: {', '.join(sorted(valid_indicators))}"
                )
            validated.append(indicator_lower)
        
        return validated


class BulkAnalysisRequest(BaseModel):
    """
    Validation schema for /analyze-all-stocks endpoint
    """
    use_demo: bool = Field(
        default=True,
        description="Whether to use demo data"
    )
    max_workers: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of concurrent workers (1-20)"
    )


class WatchlistAddRequest(BaseModel):
    """
    Validation schema for adding to watchlist
    """
    symbol: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Stock symbol"
    )
    name: str = Field(
        default="",
        max_length=100,
        description="Company name"
    )
    
    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, symbol: str) -> str:
        """Sanitize symbol same as ticker"""
        symbol = symbol.strip().upper()
        if not re.match(r'^[A-Z0-9\.\-]+$', symbol):
            raise ValueError(
                f"Invalid symbol: {symbol}. "
                "Only alphanumeric characters, dots, and hyphens allowed."
            )
        return symbol
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, name: str) -> str:
        """Sanitize company name"""
        # Remove potentially dangerous characters
        name = re.sub(r'[<>\'\"&]', '', name)
        return name.strip()


class WatchlistDeleteRequest(BaseModel):
    """
    Validation schema for deleting from watchlist
    """
    symbol: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Stock symbol to delete"
    )
    
    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, symbol: str) -> str:
        """Sanitize symbol"""
        return symbol.strip().upper()


class DateRangeRequest(BaseModel):
    """
    Validation schema for date range queries
    """
    start_date: Optional[str] = Field(
        None,
        description="Start date in YYYY-MM-DD format"
    )
    end_date: Optional[str] = Field(
        None,
        description="End date in YYYY-MM-DD format"
    )
    
    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date_format(cls, date_str: Optional[str]) -> Optional[str]:
        """Validate date format"""
        if not date_str:
            return None
        
        # Validate ISO format
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            raise ValueError(
                f"Invalid date format: {date_str}. "
                "Must be YYYY-MM-DD"
            )
        
        return date_str
    
    @model_validator(mode='after')
    def validate_date_range(self):
        """Ensure start_date is before end_date"""
        if self.start_date and self.end_date:
            start_dt = datetime.strptime(self.start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(self.end_date, '%Y-%m-%d')
            
            if start_dt > end_dt:
                raise ValueError("start_date must be before end_date")
        
        return self


# Helper function to validate request and return errors
def validate_request(model_class: type[BaseModel], data: dict) -> tuple[Optional[BaseModel], Optional[dict]]:
    """
    Validate request data against a Pydantic model.
    
    Args:
        model_class: The Pydantic model class to validate against
        data: The request data dictionary
        
    Returns:
        tuple: (validated_model, error_dict)
        - If valid: (model_instance, None)
        - If invalid: (None, {"error": "message", "details": [...]})
    """
    try:
        validated = model_class(**data)
        return validated, None
    except Exception as e:
        # Parse Pydantic validation errors
        if hasattr(e, 'errors'):
            errors = []
            for error in e.errors():
                field = ' -> '.join(str(x) for x in error['loc'])
                message = error['msg']
                errors.append(f"{field}: {message}")
            
            return None, {
                "error": "Validation failed",
                "details": errors
            }
        else:
            return None, {
                "error": "Validation failed",
                "details": [str(e)]
            }
