"""
Centralized Constants Module

This module defines all environment-specific URLs, endpoints, and configuration
constants to ensure consistency across the application and eliminate hardcoded values.

FOLLOW: TheTool.prompt.md Section 2.6 (Utilities & Abstractions)
- Keep hardcoded values in single location
- Enable easy switching between dev/prod environments
- Support new deployment targets without code changes

Usage:
    from constants import API_URLS, ENVIRONMENTS, get_api_base_url
    
    # Get current environment
    env = ENVIRONMENTS.get_current()
    
    # Get API base URL based on environment
    api_url = get_api_base_url()
    
    # Access specific URLs
    health_url = API_URLS.HEALTH_CHECK
"""

import os
import urllib.parse
from typing import Dict, Union, Literal, Any
from enum import Enum


# =============================================================================
# ENVIRONMENT DEFINITIONS
# =============================================================================

class Environment(Enum):
    """Supported deployment environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class ENVIRONMENTS:
    """Environment configuration container"""
    
    # Development (local testing)
    DEVELOPMENT = {
        "name": "development",
        "backend_url": "http://localhost:5000",
        "frontend_url": "http://localhost:3000",
        "redis_url": "redis://localhost:6379/0",
        "is_secure": False,
    }
    
    # Staging (pre-production testing)
    STAGING = {
        "name": "staging",
        "backend_url": "https://thetool-staging.up.railway.app",
        "frontend_url": "https://thetool-staging.vercel.app",
        "redis_url": "redis://staging-redis.railway.app:6379/0",
        "is_secure": True,
    }
    
    # Production (live deployment)
    PRODUCTION = {
        "name": "production",
        "backend_url": "https://thetool-production.up.railway.app",
        "frontend_url": "https://the-tool-theta.vercel.app",
        "redis_url": "redis://production-redis.railway.app:6379/0",
        "is_secure": True,
    }
    
    @staticmethod
    def get_current() -> Dict[str, Union[str, bool]]:
        """
        Get current environment configuration based on FLASK_ENV variable.
        
        Returns:
            Dict[str, Union[str, bool]]: Environment configuration dict with string and boolean values
        """
        env = os.getenv('FLASK_ENV', 'development').lower()
        
        if env == 'production':
            return ENVIRONMENTS.PRODUCTION
        elif env == 'staging':
            return ENVIRONMENTS.STAGING
        else:
            return ENVIRONMENTS.DEVELOPMENT
    
    @staticmethod
    def all() -> Dict[str, Dict[str, Union[str, bool]]]:
        """Get all environment configurations"""
        return {
            "development": ENVIRONMENTS.DEVELOPMENT,
            "staging": ENVIRONMENTS.STAGING,
            "production": ENVIRONMENTS.PRODUCTION,
        }


# =============================================================================
# API URL CONFIGURATION
# =============================================================================

def get_api_base_url() -> str:
    """
    Get API base URL for current environment.
    
    Respects explicit BACKEND_URL env var, otherwise uses FLASK_ENV detection.
    
    Returns:
        str: Full API base URL (e.g., http://localhost:5000)
    """
    # Allow explicit override
    if backend_url := os.getenv('BACKEND_URL'):
        return backend_url
    
    # Use environment-based default
    return ENVIRONMENTS.get_current()['backend_url']


def get_frontend_url() -> str:
    """
    Get frontend URL for current environment.
    
    Returns:
        str: Full frontend URL
    """
    if frontend_url := os.getenv('FRONTEND_URL'):
        return frontend_url
    
    return ENVIRONMENTS.get_current()['frontend_url']


def get_redis_url() -> str:
    """
    Get Redis URL for current environment.
    
    Respects explicit REDIS_URL env var first.
    
    Returns:
        str: Redis connection URL
    """
    if redis_url := os.getenv('REDIS_URL'):
        return redis_url
    
    return ENVIRONMENTS.get_current()['redis_url']


class API_URLS:
    """
    Centralized API endpoint definitions.
    
    All endpoints are defined relative to API base URL.
    Use these constants throughout the codebase instead of hardcoding strings.
    """
    
    # Root endpoints
    HEALTH_CHECK = "/health"
    CONFIG = "/config"
    INFO = "/"
    
    # Analysis endpoints
    ANALYSIS_BASE = "/api/analysis"
    ANALYZE = f"{ANALYSIS_BASE}/analyze"
    ANALYSIS_STATUS = f"{ANALYSIS_BASE}/status"
    ANALYSIS_REPORT = f"{ANALYSIS_BASE}/report"
    ANALYSIS_HISTORY = f"{ANALYSIS_BASE}/history"
    ANALYSIS_CANCEL = f"{ANALYSIS_BASE}/cancel"
    ANALYSIS_JOBS = f"{ANALYSIS_BASE}/jobs"
    
    # Stock endpoints
    STOCKS_BASE = "/api/stocks"
    STOCKS_NSE = f"{STOCKS_BASE}/nse"
    STOCKS_NSE_STOCKS = f"{STOCKS_BASE}/nse-stocks"
    STOCKS_ALL = f"{STOCKS_BASE}/all-stocks"
    STOCKS_INITIALIZE_ALL = f"{STOCKS_BASE}/initialize-all-stocks"
    STOCKS_ANALYZE_ALL = f"{STOCKS_BASE}/analyze-all-stocks"
    STOCKS_PROGRESS = f"{STOCKS_BASE}/all-stocks/progress"
    
    # Watchlist endpoints
    WATCHLIST_BASE = "/api/watchlist"
    WATCHLIST = WATCHLIST_BASE
    
    # Combined/derived endpoints (examples with placeholders)
    @staticmethod
    def get_status(job_id: str) -> str:
        """Build full status endpoint URL"""
        return f"{API_URLS.ANALYSIS_STATUS}/{job_id}"
    
    @staticmethod
    def get_report(ticker: str) -> str:
        """Build full report endpoint URL"""
        return f"{API_URLS.ANALYSIS_REPORT}/{ticker}"
    
    @staticmethod
    def get_report_download(ticker: str) -> str:
        """Build full report download endpoint URL"""
        return f"{API_URLS.ANALYSIS_REPORT}/{ticker}/download"
    
    @staticmethod
    def get_history(ticker: str) -> str:
        """Build full history endpoint URL (watchlist)"""
        return f"{API_URLS.ANALYSIS_HISTORY}/{ticker}"
    
    @staticmethod
    def get_stock_history(symbol: str) -> str:
        """Build full stock history endpoint URL (all-stocks)"""
        return f"{API_URLS.STOCKS_ALL}/{symbol}/history"
    
    @staticmethod
    def get_cancel(job_id: str) -> str:
        """Build full cancel endpoint URL"""
        return f"{API_URLS.ANALYSIS_CANCEL}/{job_id}"


# =============================================================================
# FRONTEND CONFIGURATION
# =============================================================================

class FRONTEND_URLS:
    """Frontend URLs (used by frontend .env files)"""
    
    @staticmethod
    def get_api_base_url() -> str:
        """Get API base URL for frontend React app"""
        return get_api_base_url()
    
    @staticmethod
    def get_api_key() -> str:
        """
        Get API key from environment.
        
        In production, MASTER_API_KEY must be explicitly set (no fallback).
        In development/testing, uses a default development key for convenience.
        
        Returns:
            str: API key
            
        Raises:
            RuntimeError: If MASTER_API_KEY is missing in production
        """
        api_key = os.getenv('MASTER_API_KEY')
        
        # Determine current environment
        flask_env = os.getenv('FLASK_ENV', 'development').lower()
        is_production = flask_env in ('production', 'prod')
        
        if api_key:
            return api_key
        
        # Production requires explicit API key
        if is_production:
            raise RuntimeError(
                "MASTER_API_KEY environment variable is required in production. "
                "Please set it before starting the application."
            )
        
        # Development/testing: allow convenient fallback
        return 'development-key'


# =============================================================================
# CORS CONFIGURATION
# =============================================================================

class CORS_CONFIG:
    """CORS allowed origins configuration"""
    
    # Development origins
    DEVELOPMENT_ORIGINS = [
        "http://localhost:3000",           # Local React dev server
        "http://192.168.57.1:3000",       # Local network access
        "http://localhost:5000",          # Local backend (for testing)
    ]
    
    # Staging origins
    STAGING_ORIGINS = [
        "https://thetool-staging.vercel.app",
        "https://thetool-staging.up.railway.app",
    ]
    
    # Production origins
    PRODUCTION_ORIGINS = [
        "https://the-tool-theta.vercel.app",  # Frontend
        "https://thetool-production.up.railway.app",  # Backend (for health checks, webhooks)
    ]
    
    @staticmethod
    def get_allowed_origins() -> list[str]:
        """
        Get CORS allowed origins based on environment.
        
        Can be overridden via CORS_ORIGINS env var (comma-separated).
        
        Returns:
            list[str]: List of allowed origin URLs
        """
        # Allow explicit override
        if cors_env := os.getenv('CORS_ORIGINS'):
            return [origin.strip() for origin in cors_env.split(',')]
        
        # Use environment-based defaults
        env = os.getenv('FLASK_ENV', 'development').lower()
        
        if env == 'production':
            return CORS_CONFIG.PRODUCTION_ORIGINS
        elif env == 'staging':
            return CORS_CONFIG.STAGING_ORIGINS
        else:
            return CORS_CONFIG.DEVELOPMENT_ORIGINS
    
    @staticmethod
    def get_allowed_origins_string() -> str:
        """Get CORS origins as comma-separated string (for config files)"""
        return ','.join(CORS_CONFIG.get_allowed_origins())


# =============================================================================
# REDIS CONFIGURATION
# =============================================================================

class REDIS_CONFIG:
    """Redis connection configuration"""
    
    @staticmethod
    def get_url() -> str:
        """
        Get Redis connection URL.
        
        Supports both full Redis URL (railway) and individual host/port config.
        
        Returns:
            str: Redis URL
        """
        return get_redis_url()
    
    @staticmethod
    def get_host() -> str:
        """
        Get Redis host.
        
        Extracts hostname from REDIS_URL if present, otherwise uses REDIS_HOST env var.
        
        Returns:
            str: Redis hostname
        """
        if redis_url := os.getenv('REDIS_URL'):
            # Parse Redis URL to extract hostname (redis://host:port/db)
            try:
                parsed = urllib.parse.urlparse(redis_url)
                if parsed.hostname:
                    return parsed.hostname
            except (ValueError, AttributeError):
                pass
            # Fall back to REDIS_HOST if parsing fails
            return os.getenv('REDIS_HOST', 'localhost')
        
        return os.getenv('REDIS_HOST', 'localhost')
    
    @staticmethod
    def get_port() -> int:
        """Get Redis port"""
        return int(os.getenv('REDIS_PORT', '6379'))


# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

class DATABASE_CONFIG:
    """Database configuration"""
    
    @staticmethod
    def get_database_url() -> str:
        """
        Get database URL.
        
        Supports PostgreSQL (Railway) or SQLite (local).
        
        Returns:
            str: Database URL or path
        """
        if db_url := os.getenv('DATABASE_URL'):
            return db_url
        
        # SQLite default
        data_path = os.getenv('DATA_PATH', './data')
        db_name = os.getenv('DB_NAME', 'trading_app.db')
        return f"sqlite:///{data_path}/{db_name}"


# =============================================================================
# REQUEST/RESPONSE TEMPLATES
# =============================================================================

class REQUEST_TEMPLATES:
    """Common request templates for testing and documentation"""
    
    # Analysis request template
    ANALYZE_REQUEST = {
        "tickers": ["INFY.NS", "TCS.NS", "RELIANCE.NS"],
        "capital": 100000,
        "indicators": None,
    }
    
    # Watchlist add template
    WATCHLIST_ADD = {
        "symbol": "INFY.NS",
        "name": "Infosys Limited",
    }
    
    # Bulk analysis template (empty = all stocks)
    BULK_ANALYZE_ALL = {
        "symbols": [],
    }


# =============================================================================
# VALIDATION HELPERS
# =============================================================================

def validate_urls() -> tuple[bool, list[str]]:
    """
    Validate that all URLs are properly configured.
    
    Returns:
        tuple[bool, list[str]]: (is_valid, messages)
    """
    messages = []
    
    backend_url = get_api_base_url()
    if not backend_url:
        messages.append("ERROR: Backend URL not configured")
    elif not (backend_url.startswith('http://') or backend_url.startswith('https://')):
        messages.append(f"ERROR: Backend URL invalid format: {backend_url}")
    
    redis_url = get_redis_url()
    if redis_url and not redis_url.startswith('redis://'):
        messages.append(f"ERROR: Redis URL invalid format: {redis_url}")
    
    return len(messages) == 0, messages




# =============================================================================
# TRADING STRATEGY CONFIGURATION CONSTANTS
# =============================================================================

# Breakout Strategy - Technical Indicator Periods
DEFAULT_LOOKBACK_PERIOD = 20           # Bars to analyze for consolidation
DEFAULT_ATR_PERIOD = 14                # Average True Range period
DEFAULT_EMA_PERIOD = 12                # Exponential Moving Average period

# Breakout Strategy - Trade Parameters
DEFAULT_VOLUME_FACTOR = 1.25           # Volume must be > average * this factor
DEFAULT_ATR_MULTIPLIER = 1.0           # Stop loss buffer in ATR multiples
DEFAULT_RISK_REWARD_RATIO = 2.0        # Target = risk * this ratio
DEFAULT_ENTRY_OFFSET_PCT = 0.5         # Entry offset as % above/below breakout
MIN_CONSOLIDATION_PCT = 2.0            # Min 2% range for valid consolidation

# Technical Indicator Thresholds
RSI_NEUTRAL_THRESHOLD = 50             # RSI threshold for directional bias
RSI_OVERBOUGHT_THRESHOLD = 70          # RSI overbought level
RSI_OVERSOLD_THRESHOLD = 30            # RSI oversold level
MACD_SIGNAL_THRESHOLD = 0              # MACD must cross signal line
SUPERTREND_SENSITIVITY = 3.0           # Supertrend multiplier for ATR


# =============================================================================
# INITIALIZATION & DEBUGGING
# =============================================================================

def print_config_summary():
    """Print configuration summary for debugging"""
    print("\n" + "=" * 80)
    print("THETOOL CONFIGURATION SUMMARY")
    print("=" * 80)
    print(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    print(f"\nAPI Configuration:")
    print(f"  Backend URL: {get_api_base_url()}")
    print(f"  Frontend URL: {get_frontend_url()}")
    print(f"  Redis URL: {get_redis_url()}")
    print(f"\nCORS Allowed Origins:")
    for origin in CORS_CONFIG.get_allowed_origins():
        print(f"  - {origin}")
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    print_config_summary()
    is_valid, validation_msgs = validate_urls()
    if validation_msgs:
        print("Validation Messages:")
        for msg in validation_msgs:
            print(f"  {msg}")
