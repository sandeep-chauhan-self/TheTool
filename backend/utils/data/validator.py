"""
Data Validator Module
Validates OHLCV data quality before analysis

Inspired by NSE Stock Screener's validation framework
"""

import pandas as pd
import logging

logger = logging.getLogger('trading_analyzer')


class DataValidator:
    """Validates stock data quality and completeness"""
    
    # Minimum required data points for reliable analysis
    MIN_DATA_POINTS = 50
    
    # Required OHLCV columns
    REQUIRED_COLUMNS = ['Open', 'High', 'Low', 'Close', 'Volume']
    
    @staticmethod
    def validate_ohlcv_data(df, ticker=None):
        """
        Comprehensive OHLCV data validation
        
        Args:
            df: DataFrame with OHLCV data
            ticker: Stock ticker symbol (for logging)
        
        Returns:
            (is_valid: bool, error_message: str, warnings: list)
        """
        ticker_info = f" for {ticker}" if ticker else ""
        warnings = []
        
        # Check 1: DataFrame is not None or empty
        if df is None:
            return False, f"No data available{ticker_info}", []
        
        if df.empty:
            return False, f"Empty DataFrame{ticker_info}", []
        
        # Check 2: Required columns exist
        missing_cols = [col for col in DataValidator.REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            return False, f"Missing required columns: {', '.join(missing_cols)}{ticker_info}", []
        
        # Check 3: Sufficient data points
        data_length = len(df)
        if data_length < DataValidator.MIN_DATA_POINTS:
            return False, f"Insufficient data: {data_length} rows (minimum {DataValidator.MIN_DATA_POINTS} required){ticker_info}", []
        
        # Check 4: Check for NaN values
        nan_cols = []
        for col in DataValidator.REQUIRED_COLUMNS:
            if df[col].isnull().any():
                nan_count = df[col].isnull().sum()
                nan_cols.append(f"{col}({nan_count})")
        
        if nan_cols:
            # If few NaN values, it's a warning; if many, it's an error
            total_nan = sum([df[col].isnull().sum() for col in DataValidator.REQUIRED_COLUMNS])
            nan_percentage = (total_nan / (len(df) * len(DataValidator.REQUIRED_COLUMNS))) * 100
            
            if nan_percentage > 10:  # More than 10% NaN values
                return False, f"Too many NaN values ({nan_percentage:.1f}%) in: {', '.join(nan_cols)}{ticker_info}", []
            else:
                warnings.append(f"Some NaN values detected in: {', '.join(nan_cols)}")
        
        # Check 5: Validate price values (no zeros, no negatives)
        price_cols = ['Open', 'High', 'Low', 'Close']
        for col in price_cols:
            if (df[col] <= 0).any():
                invalid_count = (df[col] <= 0).sum()
                return False, f"Invalid {col} prices (zero/negative): {invalid_count} rows{ticker_info}", warnings
        
        # Check 6: Validate High >= Low
        if (df['High'] < df['Low']).any():
            invalid_count = (df['High'] < df['Low']).sum()
            return False, f"Invalid data: High < Low in {invalid_count} rows{ticker_info}", warnings
        
        # Check 7: Validate Close within High/Low range
        if ((df['Close'] > df['High']) | (df['Close'] < df['Low'])).any():
            invalid_count = ((df['Close'] > df['High']) | (df['Close'] < df['Low'])).sum()
            return False, f"Invalid data: Close outside High/Low range in {invalid_count} rows{ticker_info}", warnings
        
        # Check 8: Validate volume (should be non-negative)
        if (df['Volume'] < 0).any():
            invalid_count = (df['Volume'] < 0).sum()
            return False, f"Invalid Volume (negative): {invalid_count} rows{ticker_info}", warnings
        
        # Warning: Check for zero volume days (suspicious but not fatal)
        zero_volume_days = (df['Volume'] == 0).sum()
        if zero_volume_days > 0:
            zero_pct = (zero_volume_days / len(df)) * 100
            if zero_pct > 5:  # More than 5% zero volume
                warnings.append(f"High zero-volume days: {zero_volume_days} ({zero_pct:.1f}%)")
        
        # Warning: Check for extreme price jumps (potential data errors)
        returns = df['Close'].pct_change().abs()
        extreme_moves = (returns > 0.50).sum()  # >50% daily move
        if extreme_moves > 0:
            warnings.append(f"Extreme price movements detected: {extreme_moves} days (>50% change)")
        
        # All checks passed
        logger.info(f"Data validation passed{ticker_info}: {len(df)} rows, {len(warnings)} warnings")
        return True, "Valid", warnings
    
    @staticmethod
    def validate_and_clean(df, ticker=None):
        """
        Validate data and attempt to clean it
        
        Args:
            df: DataFrame with OHLCV data
            ticker: Stock ticker symbol
        
        Returns:
            (cleaned_df, is_valid, message, warnings)
        """
        if df is None or df.empty:
            return None, False, "No data to clean", []
        
        df_clean = df.copy()
        cleaning_actions = []
        
        # Forward fill small gaps in data (max 2 consecutive NaN)
        for col in DataValidator.REQUIRED_COLUMNS:
            if df_clean[col].isnull().any():
                # Only fill small gaps
                df_clean[col] = df_clean[col].fillna(method='ffill', limit=2)
                if df_clean[col].isnull().any():
                    # If still NaN, try backfill
                    df_clean[col] = df_clean[col].fillna(method='bfill', limit=2)
                
                filled = df[col].isnull().sum() - df_clean[col].isnull().sum()
                if filled > 0:
                    cleaning_actions.append(f"Filled {filled} NaN values in {col}")
        
        # Drop remaining rows with NaN
        rows_before = len(df_clean)
        df_clean = df_clean.dropna(subset=DataValidator.REQUIRED_COLUMNS)
        rows_dropped = rows_before - len(df_clean)
        if rows_dropped > 0:
            cleaning_actions.append(f"Dropped {rows_dropped} rows with remaining NaN values")
        
        # Validate cleaned data
        is_valid, message, warnings = DataValidator.validate_ohlcv_data(df_clean, ticker)
        
        if cleaning_actions:
            warnings = cleaning_actions + warnings
        
        return df_clean, is_valid, message, warnings
    
    @staticmethod
    def get_data_quality_score(df):
        """
        Calculate data quality score (0-100)
        
        Args:
            df: DataFrame with OHLCV data
        
        Returns:
            quality_score: int (0-100)
        """
        if df is None or df.empty:
            return 0
        
        score = 100
        
        # Penalize for missing data
        total_cells = len(df) * len(DataValidator.REQUIRED_COLUMNS)
        nan_cells = sum([df[col].isnull().sum() for col in DataValidator.REQUIRED_COLUMNS if col in df.columns])
        if nan_cells > 0:
            score -= min(30, (nan_cells / total_cells) * 100)
        
        # Penalize for insufficient data
        if len(df) < DataValidator.MIN_DATA_POINTS:
            score -= 40
        elif len(df) < 100:
            score -= 20
        
        # Penalize for zero volume days
        if 'Volume' in df.columns:
            zero_vol_pct = (df['Volume'] == 0).sum() / len(df) * 100
            score -= min(20, zero_vol_pct * 2)
        
        # Penalize for extreme volatility (data quality issue)
        if 'Close' in df.columns and len(df) > 1:
            returns = df['Close'].pct_change().abs()
            extreme_moves = (returns > 0.50).sum()
            if extreme_moves > 0:
                score -= min(10, extreme_moves * 2)
        
        return max(0, int(score))


# Convenience function for backward compatibility
def validate_ohlcv_data(df, ticker=None):
    """Wrapper function for easy import"""
    is_valid, message, warnings = DataValidator.validate_ohlcv_data(df, ticker)
    return is_valid, message
