"""
Robust data fetching with validation and retry logic

Part 3B (FLRM-005): Function-Level Rewrite Mode improvements
- Magic number extraction (MLRM-001)
- Comprehensive ticker validation
- Retry logic with exponential backoff
- Data quality validation
- Descriptive error messages
"""

import yfinance as yf
import pandas as pd
import os
import logging
import ssl
import re
from datetime import datetime, timedelta
import time
from typing import Optional
import threading

# Fix SSL certificate verification issues (common in corporate environments)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set SSL context to use unverified context
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except Exception:
    pass

logger = logging.getLogger('trading_analyzer')

# ============================================================================
# CONSTANTS (Part 3B - MLRM-001: Magic Number Extraction)
# ============================================================================

# Fetch settings
DEFAULT_PERIOD = '200d'
FALLBACK_PERIOD = '100d'
DEFAULT_TIMEOUT = 10  # seconds
SHORT_TIMEOUT = 5  # seconds for fallback

# Retry configuration
MAX_RETRIES = 2
BACKOFF_FACTOR = 1
RETRY_STATUS_CODES = [429, 500, 502, 503, 504]

# Cache settings
CACHE_MAX_AGE_DAYS = 7
CACHE_REUSE_SAME_DAY = True

# Data validation constants
REQUIRED_COLUMNS = ['Open', 'High', 'Low', 'Close', 'Volume']
MIN_REQUIRED_ROWS = 50  # Minimum rows for meaningful analysis

# Ticker validation constants  
TICKER_MIN_LENGTH = 1
TICKER_MAX_LENGTH = 10
TICKER_VALID_CHARS_PATTERN = r'^[A-Z0-9.-]+$'  # Alphanumeric, dots, dashes

# Session configuration
POOL_CONNECTIONS = 5
POOL_MAX_SIZE = 10

# ============================================================================
# CUSTOM EXCEPTIONS (Part 3B - FLRM-005)
# ============================================================================

class DataFetchError(Exception):
    """Raised when data fetching fails"""
    pass

class InvalidTickerError(ValueError):
    """Raised when ticker format is invalid"""
    pass

class InsufficientDataError(DataFetchError):
    """Raised when fetched data is insufficient"""
    pass

class DataQualityError(DataFetchError):
    """Raised when data quality checks fail"""
    pass

# ============================================================================
# VALIDATION FUNCTIONS (Part 3B - FLRM-005)
# ============================================================================

def validate_ticker_format(ticker: str) -> str:
    """
    Validate and normalize ticker symbol format
    
    Rules:
    - Must be non-empty string
    - Length between 1-10 characters
    - Only alphanumeric, dots, dashes allowed
    - Converted to uppercase
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Normalized ticker (uppercase, stripped)
        
    Raises:
        InvalidTickerError: If validation fails
    """
    if not ticker or not isinstance(ticker, str):
        raise InvalidTickerError("Ticker must be a non-empty string")
    
    ticker = ticker.strip().upper()
    
    if len(ticker) < TICKER_MIN_LENGTH:
        raise InvalidTickerError(
            f"Ticker too short: {len(ticker)} chars (minimum {TICKER_MIN_LENGTH})"
        )
    
    if len(ticker) > TICKER_MAX_LENGTH:
        raise InvalidTickerError(
            f"Ticker too long: {len(ticker)} chars (maximum {TICKER_MAX_LENGTH})"
        )
    
    if not re.match(TICKER_VALID_CHARS_PATTERN, ticker):
        invalid_chars = ''.join(set(c for c in ticker if not re.match(r'[A-Z0-9.-]', c)))
        raise InvalidTickerError(
            f"Ticker '{ticker}' contains invalid characters: '{invalid_chars}'. "
            f"Only uppercase letters, numbers, dots, and dashes allowed."
        )
    
    return ticker


def validate_data_quality(df: pd.DataFrame, ticker: str) -> None:
    """
    Validate fetched data quality
    
    Checks:
    - Sufficient rows
    - Required columns present
    - No all-NaN columns
    - Data sanity (High >= Low, etc.)
    - No negative prices
    - No negative volume
    
    Args:
        df: DataFrame to validate
        ticker: Ticker symbol (for error messages)
        
    Raises:
        InsufficientDataError: If not enough data
        DataQualityError: If data quality checks fail
    """
    # Check 1: Sufficient rows
    if len(df) < MIN_REQUIRED_ROWS:
        raise InsufficientDataError(
            f"{ticker} has only {len(df)} rows, need at least {MIN_REQUIRED_ROWS} for meaningful analysis"
        )
    
    # Check 2: Required columns present
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise DataQualityError(f"{ticker} missing required columns: {missing}")
    
    # Check 3: No all-NaN columns
    for col in REQUIRED_COLUMNS:
        if df[col].isna().all():
            raise DataQualityError(f"{ticker} column '{col}' is all NaN")
    
    # Check 4: No negative prices (check early before range checks)
    price_cols = ['Open', 'High', 'Low', 'Close']
    if (df[price_cols] < 0).any().any():
        raise DataQualityError(f"{ticker} has negative prices - invalid data")
    
    # Check 5: No negative volume
    if (df['Volume'] < 0).any():
        raise DataQualityError(f"{ticker} has negative volume - invalid data")
    
    # Check 6: High >= Low (data sanity)
    invalid_mask = df['High'] < df['Low']
    if invalid_mask.any():
        bad_count = invalid_mask.sum()
        raise DataQualityError(
            f"{ticker} has High < Low in {bad_count} row(s) - data corruption detected"
        )
    
    # Check 7: Close within [Low, High] range
    invalid_mask = (df['Close'] < df['Low']) | (df['Close'] > df['High'])
    if invalid_mask.any():
        bad_count = invalid_mask.sum()
        raise DataQualityError(
            f"{ticker} has Close outside High/Low range in {bad_count} row(s)"
        )

# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

_global_session = None

def _get_session():
    """Get or create a global requests session with proper configuration"""
    global _global_session
    
    if _global_session is None:
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        _global_session = requests.Session()
        _global_session.verify = False  # Disable SSL verification
        
        # Add user agent to mimic browser and avoid blocking
        _global_session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # Configure retry strategy
        retry = Retry(
            total=MAX_RETRIES,
            backoff_factor=BACKOFF_FACTOR,
            status_forcelist=RETRY_STATUS_CODES,
            respect_retry_after_header=False,
            raise_on_status=False
        )
        adapter = HTTPAdapter(
            max_retries=retry,
            pool_connections=POOL_CONNECTIONS,
            pool_maxsize=POOL_MAX_SIZE
        )
        _global_session.mount("http://", adapter)
        _global_session.mount("https://", adapter)
    
    return _global_session

# ============================================================================
# CACHE MANAGEMENT
# ============================================================================

def _get_cache_path(ticker: str) -> str:
    """Get cache file path for ticker"""
    cache_dir = os.path.join(os.getenv('DATA_PATH', './data'), 'cache')
    os.makedirs(cache_dir, exist_ok=True)
    date_str = datetime.now().strftime('%Y%m%d')
    return os.path.join(cache_dir, f"{ticker}_{date_str}.csv")


def _load_from_cache(ticker: str) -> Optional[pd.DataFrame]:
    """Load ticker data from cache if available"""
    cache_file = _get_cache_path(ticker)
    
    if os.path.exists(cache_file) and CACHE_REUSE_SAME_DAY:
        try:
            logger.info(f"Using cached data for {ticker}")
            df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            if len(df) > 0:
                return df
        except Exception as e:
            logger.warning(f"Failed to load cache for {ticker}: {str(e)}")
    
    return None


def _save_to_cache(ticker: str, df: pd.DataFrame) -> None:
    """Save ticker data to cache"""
    try:
        cache_file = _get_cache_path(ticker)
        df.to_csv(cache_file)
        logger.info(f"Cached {len(df)} rows for {ticker}")
    except Exception as e:
        logger.warning(f"Failed to cache data for {ticker}: {str(e)}")


def clean_old_cache(days: int = CACHE_MAX_AGE_DAYS) -> int:
    """
    Remove cached data older than specified days
    
    Args:
        days: Maximum cache age in days
        
    Returns:
        Number of files removed
    """
    try:
        cache_dir = os.path.join(os.getenv('DATA_PATH', './data'), 'cache')
        if not os.path.exists(cache_dir):
            return 0
        
        cutoff_date = datetime.now() - timedelta(days=days)
        removed_count = 0
        
        for filename in os.listdir(cache_dir):
            filepath = os.path.join(cache_dir, filename)
            
            if os.path.isfile(filepath):
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                if file_time < cutoff_date:
                    os.remove(filepath)
                    removed_count += 1
        
        if removed_count > 0:
            logger.info(f"Cleaned {removed_count} old cache files")
        
        return removed_count
        
    except Exception as e:
        logger.error(f"Error cleaning cache: {str(e)}")
        return 0

# ============================================================================
# DATA FETCHING (Part 3B - FLRM-005)
# ============================================================================

def _fetch_with_timeout(stock, period: str, timeout: int) -> Optional[pd.DataFrame]:
    """
    Fetch stock history with timeout (Windows-compatible threading approach)
    
    Args:
        stock: yfinance Ticker object
        period: Time period for data
        timeout: Maximum seconds to wait
        
    Returns:
        DataFrame or None
        
    Raises:
        TimeoutError: If fetch exceeds timeout
    """
    result = {'df': None, 'error': None}
    
    def fetch_worker():
        try:
            result['df'] = stock.history(period=period, timeout=timeout, raise_errors=False)
        except Exception as e:
            result['error'] = e
    
    thread = threading.Thread(target=fetch_worker)
    thread.daemon = True
    thread.start()
    thread.join(timeout=timeout)
    
    if thread.is_alive():
        raise TimeoutError(f"Data fetch timeout after {timeout}s")
    
    if result['error']:
        raise result['error']
    
    return result['df']


def fetch_ticker_data(
    ticker: str,
    period: str = DEFAULT_PERIOD,
    timeout: int = DEFAULT_TIMEOUT,
    validate: bool = True,
    use_cache: bool = True
) -> pd.DataFrame:
    """
    Fetch OHLCV data from Yahoo Finance with comprehensive validation
    
    Part 3B (FLRM-005): Enhanced with:
    - Ticker format validation (fail-fast)
    - Data quality validation
    - Retry logic with fallback period
    - Descriptive error messages
    - Magic number extraction to constants
    - Cache management
    
    Args:
        ticker: Stock ticker symbol
        period: Time period for data (default: 200d)
        timeout: Maximum seconds to wait (default: 10)
        validate: Perform data quality validation (default: True)
        use_cache: Use cached data if available (default: True)
    
    Returns:
        pandas DataFrame with OHLCV data
        
    Raises:
        InvalidTickerError: If ticker format invalid
        InsufficientDataError: If not enough data
        DataQualityError: If data quality checks fail
        DataFetchError: If fetching fails
        TimeoutError: If fetch exceeds timeout
    """
    # Step 1: Validate and normalize ticker format (fail-fast)
    ticker = validate_ticker_format(ticker)
    
    # Step 2: Try cache first (fast path)
    if use_cache:
        cached_df = _load_from_cache(ticker)
        if cached_df is not None:
            if validate:
                validate_data_quality(cached_df, ticker)
            return cached_df
    
    # Step 3: Fetch from Yahoo Finance
    try:
        logger.info(f"Fetching fresh data from Yahoo Finance for {ticker} (timeout: {timeout}s)")
        
        session = _get_session()
        stock = yf.Ticker(ticker, session=session)
        
        # Try primary period first
        try:
            df = _fetch_with_timeout(stock, period, timeout)
        except Exception as e:
            logger.warning(f"Failed to fetch {period} data for {ticker}: {str(e)}")
            # Fallback to shorter period
            logger.info(f"Trying shorter period ({FALLBACK_PERIOD}) for {ticker}")
            df = _fetch_with_timeout(stock, FALLBACK_PERIOD, SHORT_TIMEOUT)
        
        # Step 4: Check if data was returned
        if df is None or df.empty:
            logger.error(f"No data returned for {ticker}")
            raise DataFetchError(
                f"No data available for {ticker}. Possible causes:\n"
                f"1. Network/firewall blocking Yahoo Finance\n"
                f"2. Invalid or delisted ticker symbol\n"
                f"3. Yahoo Finance API temporarily unavailable\n"
                f"Please check your network connection and verify the ticker symbol."
            )
        
        # Step 5: Validate data quality
        if validate:
            validate_data_quality(df, ticker)
        
        # Step 6: Cache the data
        if use_cache:
            _save_to_cache(ticker, df)
        
        logger.info(f"Successfully fetched {len(df)} rows for {ticker}")
        return df
        
    except InvalidTickerError:
        # Re-raise ticker validation errors as-is
        raise
    except (InsufficientDataError, DataQualityError):
        # Re-raise data validation errors as-is
        raise
    except TimeoutError as e:
        logger.error(f"Timeout error for {ticker}: {str(e)}")
        raise DataFetchError(
            f"Request timeout for {ticker} after {timeout}s. "
            f"Network may be slow or Yahoo Finance is blocked."
        ) from e
    except Exception as e:
        logger.error(f"Failed to fetch data for {ticker}: {str(e)}")
        raise DataFetchError(
            f"Cannot fetch data for {ticker}: {str(e)}\n"
            f"This may indicate network issues or invalid ticker."
        ) from e
