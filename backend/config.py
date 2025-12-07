"""
Configuration Management Module

CRITICAL FIX (ISSUE_019): Centralized configuration management
to eliminate hardcoded values throughout the codebase.

All configuration values are read from environment variables with
sensible defaults for development.

FOLLOW: TheTool.prompt.md Section 2.1 (Application Factory & Configuration)
- All external service initializations tolerate missing dependencies
- CORS must list explicit origins; never use wildcard in production
- Do not embed secrets directly—rely on env variables
"""

import os
from typing import List
from dotenv import load_dotenv
from constants import CORS_CONFIG, REDIS_CONFIG, DATABASE_CONFIG, get_api_base_url

# Load environment variables from .env file
load_dotenv()


class Config:
    """Central configuration class for the trading platform"""
    
    # =============================================================================
    # ENVIRONMENT CONFIGURATION
    # =============================================================================
    
    APP_ENV = os.getenv("APP_ENV", "production").lower()
    DEBUG = APP_ENV == "development"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG" if DEBUG else "INFO").upper()
    
    # =============================================================================
    # SECURITY CONFIGURATION
    # =============================================================================
    
    MASTER_API_KEY = os.getenv('MASTER_API_KEY')
    
    # =============================================================================
    # DATABASE CONFIGURATION (PostgreSQL Only)
    # =============================================================================
    
    # PostgreSQL via DATABASE_URL env var (REQUIRED)
    # Local: postgresql://postgres:password@localhost:5432/trading_app
    # Railway: Automatically set by Railway's PostgreSQL addon
    _raw_database_url = os.getenv('DATABASE_URL', None)
    
    # Fix PostgreSQL URL format (Railway might use postgres:// instead of postgresql://)
    if _raw_database_url:
        # Only replace at the start (scheme), not in password/username
        if _raw_database_url.startswith('postgres://'):
            DATABASE_URL = 'postgresql://' + _raw_database_url[11:]
        else:
            DATABASE_URL = _raw_database_url
    else:
        DATABASE_URL = None
    
    # PostgreSQL is now required - no SQLite fallback
    DATABASE_TYPE = 'postgres'
    
    # Legacy property for backward compatibility (always returns None now)
    @property
    def DB_PATH(self) -> str:
        """Legacy property - SQLite is no longer supported. Always returns None."""
        return None
    
    # =============================================================================
    # APPLICATION CONFIGURATION
    # =============================================================================
    
    FLASK_ENV = os.getenv('FLASK_ENV', APP_ENV)  # Deprecated: use APP_ENV instead
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
    
    # =============================================================================
    # CORS CONFIGURATION - Dual Environment Support
    # =============================================================================
    # Production Railway: thetool-production.up.railway.app (live backend)
    # Development Railway: thetool-development.up.railway.app (debug backend)
    # Local: localhost:3000, localhost:5173
    #
    # Both backends accept requests from all frontends to support testing
    # in different environments simultaneously
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """
        Get CORS allowed origins based on current environment.
        
        Supports:
        - Multiple frontend URLs (Vercel production + local dev)
        - Multiple backend URLs (production + development Railway)
        - Simultaneous environment testing
        
        Can be overridden with CORS_ORIGINS environment variable.
        """
        env_override = os.getenv('CORS_ORIGINS')
        if env_override:
            return [o.strip() for o in env_override.split(',')]
        
        # Default configuration by backend environment
        if self.APP_ENV == 'development':
            # Development backend accepts from everywhere (for testing)
            return [
                # Local development
                'http://localhost:3000',
                'http://localhost:5173',
                'http://127.0.0.1:3000',
                'http://127.0.0.1:5173',
                # Production frontend URLs
                'https://the-tool-theta.vercel.app',
                # Vercel preview deployment (development)
                'https://the-tool-git-development-sandeep-chauhan-selfs-projects.vercel.app',
                # Railway backends (both)
                'https://thetool-development.up.railway.app',
                'https://thetool-production.up.railway.app',
            ]
        else:
            # Production backend - restrictive but includes dev frontend for testing
            return [
                'https://the-tool-theta.vercel.app',
                'https://the-tool-git-development-sandeep-chauhan-selfs-projects.vercel.app',
                'https://thetool-production.up.railway.app',
            ]
    
    # =============================================================================
    # THREADING CONFIGURATION
    # =============================================================================
    
    MAX_THREADS = int(os.getenv('MAX_THREADS', '10'))
    MAX_BULK_WORKERS = int(os.getenv('MAX_BULK_WORKERS', '5'))
    
    # =============================================================================
    # CACHE CONFIGURATION
    # =============================================================================
    
    CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'True').lower() in ('true', '1', 'yes')
    CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))  # 1 hour
    CACHE_MAX_SIZE = int(os.getenv('CACHE_MAX_SIZE', '1000'))
    
    # =============================================================================
    # RATE LIMITING CONFIGURATION
    # =============================================================================
    
    RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'True').lower() in ('true', '1', 'yes')
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', '60'))
    ANALYZE_RATE_LIMIT = int(os.getenv('ANALYZE_RATE_LIMIT', '10'))
    
    # =============================================================================
    # MARKET DATA CONFIGURATION
    # =============================================================================
    
    DEFAULT_CAPITAL = float(os.getenv('DEFAULT_CAPITAL', '100000'))
    USE_DEMO_DATA = os.getenv('USE_DEMO_DATA', 'True').lower() in ('true', '1', 'yes')
    YAHOO_TIMEOUT = int(os.getenv('YAHOO_TIMEOUT', '30'))
    
    # =============================================================================
    # LOGGING CONFIGURATION
    # =============================================================================
    
    LOG_FILE = os.getenv('LOG_FILE', './logs/trading_app.log')
    LOG_MAX_SIZE = int(os.getenv('LOG_MAX_SIZE', '10485760'))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    
    # =============================================================================
    # REDIS CONFIGURATION (EVOLUTIONARY_RISK_001 - Message Queue System)
    # =============================================================================
    
    # Use centralized Redis configuration from constants module
    REDIS_URL = REDIS_CONFIG.get_url()
    
    # Fallback to individual host/port config
    REDIS_ENABLED = os.getenv('REDIS_ENABLED', 'False').lower() in ('true', '1', 'yes') or bool(REDIS_URL)
    REDIS_HOST = REDIS_CONFIG.get_host()
    REDIS_PORT = REDIS_CONFIG.get_port()
    REDIS_DB = int(os.getenv('REDIS_DB', '0'))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
    REDIS_MAX_CONNECTIONS = int(os.getenv('REDIS_MAX_CONNECTIONS', '50'))
    
    # Job state management
    JOB_STATE_TTL = int(os.getenv('JOB_STATE_TTL', '86400'))  # 24 hours
    JOB_CLEANUP_INTERVAL = int(os.getenv('JOB_CLEANUP_INTERVAL', '3600'))  # 1 hour
    
    # =============================================================================
    # PERFORMANCE CONFIGURATION
    # =============================================================================
    
    ENABLE_NUMBA = os.getenv('ENABLE_NUMBA', 'True').lower() in ('true', '1', 'yes')
    ENABLE_VECTORIZATION = os.getenv('ENABLE_VECTORIZATION', 'True').lower() in ('true', '1', 'yes')
    
    # =============================================================================
    # CLEANUP CONFIGURATION
    # =============================================================================
    
    KEEP_LAST_ANALYSES = int(os.getenv('KEEP_LAST_ANALYSES', '10'))
    CLEANUP_INTERVAL = int(os.getenv('CLEANUP_INTERVAL', '3600'))  # 1 hour
    
    # =============================================================================
    # MONITORING & METRICS
    # =============================================================================
    
    METRICS_ENABLED = os.getenv('METRICS_ENABLED', 'False').lower() in ('true', '1', 'yes')
    METRICS_PORT = int(os.getenv('METRICS_PORT', '9090'))
    
    # =============================================================================
    # DEVELOPMENT SETTINGS
    # =============================================================================
    
    FLASK_DEBUG_TOOLBAR = os.getenv('FLASK_DEBUG_TOOLBAR', 'False').lower() in ('true', '1', 'yes')
    SQL_DEBUG = os.getenv('SQL_DEBUG', 'False').lower() in ('true', '1', 'yes')
    TIME_REQUESTS = os.getenv('TIME_REQUESTS', 'True').lower() in ('true', '1', 'yes')
    
    # =============================================================================
    # VALIDATION METHODS
    # =============================================================================
    
    def validate(self) -> List[str]:
        """
        Validate configuration and return list of warnings/errors.
        
        Returns:
            List[str]: List of validation messages
        """
        messages = []
        
        # Environment info
        messages.append(f"Environment Mode: {self.APP_ENV.upper()}")
        messages.append(f"Debug Mode: {self.DEBUG}")
        messages.append(f"Log Level: {self.LOG_LEVEL}")
        
        # Critical validations
        if not self.MASTER_API_KEY:
            if self.APP_ENV == 'production':
                messages.append("ERROR: MASTER_API_KEY must be set in production!")
            else:
                messages.append("INFO: MASTER_API_KEY not set. API will generate a temporary key.")
        
        if self.DEBUG and self.APP_ENV == 'production':
            messages.append("ERROR: DEBUG mode enabled in production environment!")
        
        if self.MAX_THREADS > 50:
            messages.append(f"WARNING: MAX_THREADS={self.MAX_THREADS} is very high. May cause resource exhaustion.")
        
        if self.CACHE_TTL < 60:
            messages.append(f"WARNING: CACHE_TTL={self.CACHE_TTL}s is very short. Cache effectiveness will be low.")
        
        # Database validations - PostgreSQL is now required
        if not self.DATABASE_URL:
            messages.append("ERROR: DATABASE_URL must be configured! PostgreSQL is required.")
            messages.append("  Local: DATABASE_URL=postgresql://postgres:password@localhost:5432/trading_app")
            messages.append("  Railway: Set automatically by Railway's PostgreSQL addon")
        
        # Redis validations
        if self.REDIS_ENABLED:
            if self.REDIS_URL:
                messages.append(f"INFO: Using Redis from REDIS_URL (Railway managed)")
            elif not self.REDIS_HOST:
                messages.append("ERROR: REDIS_ENABLED=True but REDIS_HOST/REDIS_URL not configured!")
            else:
                messages.append(f"INFO: Using Redis at {self.REDIS_HOST}:{self.REDIS_PORT}")
        
        return messages
    
    def print_config(self):
        """Print configuration summary (for debugging)"""
        print("=" * 80)
        print("CONFIGURATION SUMMARY")
        print("=" * 80)
        print(f"Environment: {self.APP_ENV.upper()}")
        print(f"Debug Mode: {self.DEBUG}")
        print(f"Log Level: {self.LOG_LEVEL}")
        print(f"Database: PostgreSQL (via DATABASE_URL)")
        print(f"Max Threads: {self.MAX_THREADS}")
        print(f"Cache Enabled: {self.CACHE_ENABLED}")
        print(f"Rate Limiting: {self.RATE_LIMIT_ENABLED}")
        if self.REDIS_ENABLED:
            print(f"Redis: Enabled ({self.REDIS_HOST}:{self.REDIS_PORT})")
        print(f"Numba JIT: {self.ENABLE_NUMBA}")
        print(f"Vectorization: {self.ENABLE_VECTORIZATION}")
        print("=" * 80)


# Global configuration instance
config = Config()

# Validate configuration on import
_validation_messages = config.validate()
if _validation_messages:
    print("\n".join(_validation_messages))
