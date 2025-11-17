import yfinance as yf
import pandas as pd
import os
import logging
import ssl
from datetime import datetime, timedelta
import time

# Fix SSL certificate verification issues (common in corporate environments)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set SSL context to use unverified context
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except Exception:
    pass

logger = logging.getLogger('trading_analyzer')

# Global session for reuse
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
        
        # Configure retry strategy - REDUCED retries for faster failure
        retry = Retry(
            total=2,  # Only 2 retries instead of 5
            backoff_factor=1,  # Reduced from 2
            status_forcelist=[429, 500, 502, 503, 504],
            respect_retry_after_header=False,  # Don't wait for retry-after
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=5, pool_maxsize=10)
        _global_session.mount("http://", adapter)
        _global_session.mount("https://", adapter)
    
    return _global_session

def fetch_ticker_data(ticker, period='200d', timeout=10):
    """
    Fetch OHLCV data from Yahoo Finance with timeout
    
    Args:
        ticker: Stock ticker symbol
        period: Time period for data (default: 200 days)
        timeout: Maximum seconds to wait (default: 10)
    
    Returns:
        pandas DataFrame with OHLCV data
    """
    try:
        logger.info(f"Fetching data for {ticker}")
        
        # Check cache first (fast path)
        cache_dir = os.path.join(os.getenv('DATA_PATH', './data'), 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        
        cache_file = os.path.join(cache_dir, f"{ticker}_{datetime.now().strftime('%Y%m%d')}.csv")
        
        # Use cache if exists and is from today
        if os.path.exists(cache_file):
            logger.info(f"Using cached data for {ticker}")
            df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            if len(df) > 0:
                return df
        
        # Fetch from Yahoo Finance with timeout
        logger.info(f"Fetching fresh data from Yahoo Finance for {ticker} (timeout: {timeout}s)")
        
        session = _get_session()
        stock = yf.Ticker(ticker, session=session)
        
        # Try with shorter period first if 200d fails (faster)
        try:
            # Use download with timeout
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Data fetch timeout after {timeout}s")
            
            # Set alarm for timeout (Unix-like systems)
            # For Windows, we'll use threading
            import threading
            
            result = {'df': None, 'error': None}
            
            def fetch_with_timeout():
                try:
                    result['df'] = stock.history(period=period, timeout=timeout, raise_errors=False)
                except Exception as e:
                    result['error'] = e
            
            thread = threading.Thread(target=fetch_with_timeout)
            thread.daemon = True
            thread.start()
            thread.join(timeout=timeout)
            
            if thread.is_alive():
                logger.error(f"Timeout fetching {ticker} after {timeout}s")
                raise TimeoutError(f"Data fetch timeout after {timeout}s")
            
            if result['error']:
                raise result['error']
            
            df = result['df']
            
        except Exception as e:
            logger.warning(f"Failed to fetch {period} data for {ticker}: {str(e)}")
            # Try shorter period as fallback
            logger.info(f"Trying shorter period (100d) for {ticker}")
            df = stock.history(period='100d', timeout=5, raise_errors=False)
        
        if df is None or df.empty:
            logger.error(f"No data returned for {ticker}")
            raise ValueError(f"No data available for {ticker}. This may be due to:\n"
                           f"1. Network/firewall blocking Yahoo Finance\n"
                           f"2. Invalid ticker symbol\n"
                           f"3. Delisted stock\n"
                           f"Please check your network connection and ticker symbol.")
        
        # Ensure we have all required columns
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"Missing required columns for {ticker}")
        
        # Cache the data
        try:
            df.to_csv(cache_file)
            logger.info(f"Cached {len(df)} rows for {ticker}")
        except Exception as e:
            logger.warning(f"Failed to cache data: {str(e)}")
        
        logger.info(f"Successfully fetched {len(df)} rows for {ticker}")
        return df
        
    except TimeoutError as e:
        logger.error(f"Timeout error for {ticker}: {str(e)}")
        raise ValueError(f"Request timeout for {ticker}. Network may be slow or Yahoo Finance is blocked.")
    except Exception as e:
        logger.error(f"Failed to fetch data for {ticker}: {str(e)}")
        raise ValueError(f"Cannot fetch data for {ticker}: {str(e)}")

def clean_old_cache(days=7):
    """Remove cached data older than specified days"""
    try:
        cache_dir = os.path.join(os.getenv('DATA_PATH', './data'), 'cache')
        if not os.path.exists(cache_dir):
            return
        
        cutoff_date = datetime.now() - timedelta(days=days)
        removed_count = 0
        
        for filename in os.listdir(cache_dir):
            filepath = os.path.join(cache_dir, filename)
            
            if os.path.isfile(filepath):
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                if file_time < cutoff_date:
                    os.remove(filepath)
                    removed_count += 1
        
        logger.info(f"Cleaned {removed_count} old cache files")
        
    except Exception as e:
        logger.error(f"Error cleaning cache: {str(e)}")
