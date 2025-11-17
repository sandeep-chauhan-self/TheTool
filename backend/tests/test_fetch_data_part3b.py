"""
Unit tests for fetch_data.py Part 3B improvements

Tests:
- Ticker format validation
- Data quality validation
- Error handling
- Constants usage
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.fetch_data import (
    validate_ticker_format,
    validate_data_quality,
    InvalidTickerError,
    DataQualityError,
    InsufficientDataError,
    DataFetchError,
    TICKER_MIN_LENGTH,
    TICKER_MAX_LENGTH,
    MIN_REQUIRED_ROWS,
    REQUIRED_COLUMNS
)


class TestTickerValidation:
    """Test ticker format validation (Part 3B - FLRM-005)"""
    
    def test_valid_tickers(self):
        """Test valid ticker formats"""
        valid_tickers = [
            'AAPL',
            'MSFT',
            'BRK.B',  # Berkshire Hathaway Class B
            'BRK-B',  # Alternative format
            'SPY',
            'A',      # Single character
            'ABCDEFGHIJ'  # 10 characters (max)
        ]
        
        for ticker in valid_tickers:
            result = validate_ticker_format(ticker)
            assert result == ticker.upper()
            assert isinstance(result, str)
    
    def test_lowercase_normalized(self):
        """Test lowercase tickers are normalized to uppercase"""
        assert validate_ticker_format('aapl') == 'AAPL'
        assert validate_ticker_format('Msft') == 'MSFT'
        assert validate_ticker_format('spy') == 'SPY'
    
    def test_whitespace_stripped(self):
        """Test whitespace is stripped"""
        assert validate_ticker_format(' AAPL ') == 'AAPL'
        assert validate_ticker_format('\tMSFT\n') == 'MSFT'
    
    def test_empty_ticker_rejected(self):
        """Test empty tickers are rejected"""
        with pytest.raises(InvalidTickerError, match="non-empty|too short"):
            validate_ticker_format('')
        
        with pytest.raises(InvalidTickerError, match="non-empty|too short"):
            validate_ticker_format('   ')
    
    def test_none_rejected(self):
        """Test None ticker is rejected"""
        with pytest.raises(InvalidTickerError, match="non-empty"):
            validate_ticker_format(None)
    
    def test_too_long_rejected(self):
        """Test ticker longer than max length is rejected"""
        long_ticker = 'A' * (TICKER_MAX_LENGTH + 1)
        with pytest.raises(InvalidTickerError, match="too long"):
            validate_ticker_format(long_ticker)
    
    def test_invalid_characters_rejected(self):
        """Test tickers with invalid characters are rejected"""
        invalid_tickers = [
            'AAP$L',  # Dollar sign
            'MS FT',  # Space
            'SPY!',   # Exclamation
            'A@PL',   # At symbol
            'MS*T',   # Asterisk
        ]
        
        for ticker in invalid_tickers:
            with pytest.raises(InvalidTickerError, match="invalid characters"):
                validate_ticker_format(ticker)
    
    def test_error_message_descriptive(self):
        """Test error messages are descriptive"""
        try:
            validate_ticker_format('AAP$L')
            pytest.fail("Should have raised InvalidTickerError")
        except InvalidTickerError as e:
            error_msg = str(e)
            assert '$' in error_msg  # Shows invalid character
            assert 'AAP$L' in error_msg  # Shows ticker
            assert 'invalid' in error_msg.lower()


class TestDataQualityValidation:
    """Test data quality validation (Part 3B - FLRM-005)"""
    
    def create_valid_dataframe(self, rows=100):
        """Helper to create valid test DataFrame"""
        dates = pd.date_range(start='2023-01-01', periods=rows, freq='D')
        return pd.DataFrame({
            'Open': np.random.uniform(100, 110, rows),
            'High': np.random.uniform(110, 120, rows),
            'Low': np.random.uniform(90, 100, rows),
            'Close': np.random.uniform(95, 105, rows),
            'Volume': np.random.randint(1000000, 10000000, rows)
        }, index=dates)
    
    def test_valid_data_passes(self):
        """Test valid data passes all checks"""
        df = self.create_valid_dataframe()
        # Ensure High >= Low and Close in range
        df['High'] = df['Low'] + 10
        df['Close'] = df['Low'] + 5
        
        validate_data_quality(df, 'TEST')  # Should not raise
    
    def test_insufficient_rows_rejected(self):
        """Test data with too few rows is rejected"""
        df = self.create_valid_dataframe(rows=MIN_REQUIRED_ROWS - 1)
        
        with pytest.raises(InsufficientDataError, match=str(MIN_REQUIRED_ROWS)):
            validate_data_quality(df, 'TEST')
    
    def test_missing_columns_rejected(self):
        """Test data missing required columns is rejected"""
        df = self.create_valid_dataframe()
        df_missing = df.drop(columns=['Volume'])
        
        with pytest.raises(DataQualityError, match="missing.*Volume"):
            validate_data_quality(df_missing, 'TEST')
    
    def test_all_nan_column_rejected(self):
        """Test data with all-NaN column is rejected"""
        df = self.create_valid_dataframe()
        df['Close'] = np.nan
        
        with pytest.raises(DataQualityError, match="all NaN"):
            validate_data_quality(df, 'TEST')
    
    def test_high_less_than_low_rejected(self):
        """Test data where High < Low is rejected"""
        df = self.create_valid_dataframe()
        df.loc[df.index[0], 'High'] = 50  # Make High < Low
        df.loc[df.index[0], 'Low'] = 100
        
        with pytest.raises(DataQualityError, match="High < Low"):
            validate_data_quality(df, 'TEST')
    
    def test_close_outside_range_rejected(self):
        """Test data where Close outside [Low, High] is rejected"""
        df = self.create_valid_dataframe()
        df.loc[df.index[0], 'Low'] = 100
        df.loc[df.index[0], 'High'] = 110
        df.loc[df.index[0], 'Close'] = 120  # Close > High
        
        with pytest.raises(DataQualityError, match="outside High/Low range"):
            validate_data_quality(df, 'TEST')
    
    def test_negative_prices_rejected(self):
        """Test data with negative prices is rejected"""
        df = self.create_valid_dataframe()
        # Ensure High >= Low and Close in range first
        df['High'] = df['Low'] + 10
        df['Close'] = df['Low'] + 5
        # Then set negative price
        df.loc[df.index[0], 'Close'] = -10
        
        with pytest.raises(DataQualityError, match="negative prices"):
            validate_data_quality(df, 'TEST')
    
    def test_negative_volume_rejected(self):
        """Test data with negative volume is rejected"""
        df = self.create_valid_dataframe()
        df['High'] = df['Low'] + 10
        df['Close'] = df['Low'] + 5
        df.loc[df.index[0], 'Volume'] = -1000
        
        with pytest.raises(DataQualityError, match="negative volume"):
            validate_data_quality(df, 'TEST')
    
    def test_error_messages_include_ticker(self):
        """Test error messages include ticker symbol"""
        df = self.create_valid_dataframe(rows=MIN_REQUIRED_ROWS - 1)
        
        try:
            validate_data_quality(df, 'AAPL')
            pytest.fail("Should have raised InsufficientDataError")
        except InsufficientDataError as e:
            assert 'AAPL' in str(e)


class TestConstants:
    """Test that magic numbers are extracted to constants"""
    
    def test_constants_defined(self):
        """Test all required constants are defined"""
        assert TICKER_MIN_LENGTH == 1
        assert TICKER_MAX_LENGTH == 10
        assert MIN_REQUIRED_ROWS > 0
        assert len(REQUIRED_COLUMNS) == 5
    
    def test_required_columns_complete(self):
        """Test required columns list is complete"""
        expected = {'Open', 'High', 'Low', 'Close', 'Volume'}
        assert set(REQUIRED_COLUMNS) == expected


class TestExceptionHierarchy:
    """Test custom exception hierarchy"""
    
    def test_exception_inheritance(self):
        """Test exceptions inherit correctly"""
        assert issubclass(InvalidTickerError, ValueError)
        assert issubclass(DataFetchError, Exception)
        assert issubclass(InsufficientDataError, DataFetchError)
        assert issubclass(DataQualityError, DataFetchError)
    
    def test_exceptions_instantiable(self):
        """Test exceptions can be instantiated with messages"""
        e1 = InvalidTickerError("Test message")
        assert str(e1) == "Test message"
        
        e2 = DataQualityError("Quality issue")
        assert str(e2) == "Quality issue"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
