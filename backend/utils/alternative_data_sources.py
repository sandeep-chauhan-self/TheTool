"""
Alternative data sources when Yahoo Finance fails
Supports: Alpha Vantage, CSV upload, demo data
"""

import pandas as pd
import requests
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger('trading_analyzer')


def fetch_from_alphavantage(ticker, api_key=None):
    """
    Fetch data from Alpha Vantage (free tier: 25 calls/day)
    
    Get free API key: https://www.alphavantage.co/support/#api-key
    """
    if not api_key:
        api_key = os.getenv('ALPHAVANTAGE_API_KEY')
    
    if not api_key:
        raise ValueError("Alpha Vantage API key not configured")
    
    try:
        logger.info(f"Fetching {ticker} from Alpha Vantage")
        
        # Remove .NS or .BO suffix for Indian stocks (Alpha Vantage uses different format)
        symbol = ticker.replace('.NS', '').replace('.BO', '')
        
        url = f"https://www.alphavantage.co/query"
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'outputsize': 'full',  # Get full history
            'apikey': api_key,
            'datatype': 'csv'
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        # Parse CSV response
        from io import StringIO
        df = pd.read_csv(StringIO(response.text))
        
        # Rename columns to match Yahoo Finance format
        df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        df = df.sort_index()  # Oldest first
        
        # Get last 200 days
        df = df.tail(200)
        
        logger.info(f"Fetched {len(df)} rows from Alpha Vantage")
        return df
        
    except Exception as e:
        logger.error(f"Alpha Vantage fetch failed: {str(e)}")
        raise


def generate_demo_data(ticker, days=200):
    """
    Generate demo/sample data for testing
    Uses random walk with realistic patterns
    """
    import numpy as np
    
    logger.warning(f"Generating DEMO data for {ticker} - NOT REAL MARKET DATA!")
    
    # Starting price
    base_price = 100
    
    # Generate dates
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    # Generate random walk with drift
    np.random.seed(hash(ticker) % 2**32)  # Consistent data for same ticker
    
    returns = np.random.normal(0.001, 0.02, days)  # Mean 0.1% daily return, 2% volatility
    prices = base_price * np.exp(np.cumsum(returns))
    
    # Generate OHLCV
    df = pd.DataFrame(index=dates)
    df['Close'] = prices
    df['Open'] = df['Close'].shift(1).fillna(base_price)
    
    # High = max(Open, Close) + some random amount
    df['High'] = df[['Open', 'Close']].max(axis=1) * (1 + np.random.uniform(0, 0.02, days))
    
    # Low = min(Open, Close) - some random amount
    df['Low'] = df[['Open', 'Close']].min(axis=1) * (1 - np.random.uniform(0, 0.02, days))
    
    # Volume
    df['Volume'] = np.random.randint(1000000, 10000000, days)
    
    logger.info(f"Generated {len(df)} rows of demo data")
    return df


def load_from_csv(filepath):
    """
    Load data from CSV file
    Expected format: Date,Open,High,Low,Close,Volume
    """
    try:
        logger.info(f"Loading data from CSV: {filepath}")
        
        df = pd.read_csv(filepath, parse_dates=['Date'], index_col='Date')
        
        # Validate required columns
        required = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required):
            raise ValueError(f"CSV must have columns: {required}")
        
        logger.info(f"Loaded {len(df)} rows from CSV")
        return df
        
    except Exception as e:
        logger.error(f"Failed to load CSV: {str(e)}")
        raise


def fetch_with_fallback(ticker, use_demo=False):
    """
    Try multiple data sources in order:
    1. Yahoo Finance (primary)
    2. Alpha Vantage (if API key available)
    3. Demo data (if use_demo=True)
    
    Returns:
        (df, data_source): DataFrame and source name
    """
    from utils.fetch_data import fetch_ticker_data
    
    errors = []
    
    # Try Yahoo Finance first
    try:
        df = fetch_ticker_data(ticker, timeout=10)
        return df, 'yahoo_finance'
    except Exception as e:
        errors.append(f"Yahoo Finance: {str(e)}")
        logger.warning(f"Yahoo Finance failed, trying alternatives...")
    
    # Try Alpha Vantage
    try:
        if os.getenv('ALPHAVANTAGE_API_KEY'):
            df = fetch_from_alphavantage(ticker)
            return df, 'alpha_vantage'
        else:
            errors.append("Alpha Vantage: No API key configured")
    except Exception as e:
        errors.append(f"Alpha Vantage: {str(e)}")
    
    # Try demo data if allowed
    if use_demo:
        logger.warning("All real data sources failed, using DEMO data")
        df = generate_demo_data(ticker)
        return df, 'demo_data'
    
    # All sources failed
    error_msg = "All data sources failed:\n" + "\n".join(errors)
    logger.error(error_msg)
    raise ValueError(error_msg)


def setup_alphavantage():
    """
    Instructions to setup Alpha Vantage as backup data source
    """
    return """
    Alpha Vantage Setup (Free Backup Data Source):
    
    1. Get free API key: https://www.alphavantage.co/support/#api-key
    2. Add to .env file:
       ALPHAVANTAGE_API_KEY=your_key_here
    3. Free tier limits: 25 API calls per day
    
    Once configured, the system will automatically use Alpha Vantage
    when Yahoo Finance fails.
    """
