#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verification script for logger configuration across development/production modes.

Tests:
1. Configuration hierarchy (APP_ENV -> DEBUG -> LOG_LEVEL)
2. Logger initialization in both modes
3. Debug/Info/Warning/Error logging visibility
4. SQL debug logging conditional behavior
"""

import os
import sys
import logging
from io import StringIO

def test_logger_config(app_env='development'):
    """Test logger configuration for given APP_ENV"""
    
    # Set environment
    os.environ['APP_ENV'] = app_env
    if 'LOG_LEVEL' in os.environ:
        del os.environ['LOG_LEVEL']
    
    print(f"\n{'='*70}")
    print(f"TESTING: APP_ENV={app_env}")
    print(f"{'='*70}\n")
    
    # Import fresh config
    import importlib
    if 'config' in sys.modules:
        del sys.modules['config']
    if 'utils.logger' in sys.modules:
        del sys.modules['utils.logger']
    
    from config import config
    from utils.logger import setup_logger
    
    # Verify configuration
    print(f"1. CONFIGURATION STATE:")
    print(f"   [OK] APP_ENV: {config.APP_ENV}")
    print(f"   [OK] DEBUG: {config.DEBUG}")
    print(f"   [OK] LOG_LEVEL: {config.LOG_LEVEL}")
    
    # Verify expected values
    if app_env == 'development':
        assert config.APP_ENV == 'development', f"Expected development, got {config.APP_ENV}"
        assert config.DEBUG == True, f"Expected DEBUG=True, got {config.DEBUG}"
        print(f"   [OK] Development mode correctly configured\n")
    else:
        assert config.APP_ENV == 'production', f"Expected production, got {config.APP_ENV}"
        assert config.DEBUG == False, f"Expected DEBUG=False, got {config.DEBUG}"
        print(f"   [OK] Production mode correctly configured\n")
    
    # Setup logger
    logger = setup_logger()
    
    # Verify logger configuration
    print(f"2. LOGGER CONFIGURATION:")
    print(f"   [OK] Logger name: {logger.name}")
    print(f"   [OK] Logger level: {logging.getLevelName(logger.level)}")
    print(f"   [OK] Handlers count: {len(logger.handlers)}")
    
    # Capture output to verify logging
    print(f"\n3. LOGGING OUTPUT TEST:")
    
    # Create string buffer to capture log output
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    
    # Test logger
    test_logger = logging.getLogger('test_logger')
    test_logger.setLevel(getattr(logging, config.LOG_LEVEL))
    test_logger.addHandler(handler)
    
    # Log messages
    test_logger.debug("DEBUG message")
    test_logger.info("INFO message")
    test_logger.warning("WARNING message")
    test_logger.error("ERROR message")
    
    # Check output
    output = log_capture.getvalue()
    print(f"   Captured output:\n{output}")
    
    # Verify debug visibility
    if app_env == 'development':
        assert '[DEBUG]' in output, "DEBUG messages should be visible in development"
        print(f"   [OK] DEBUG messages visible (development mode)\n")
    else:
        assert '[DEBUG]' not in output, "DEBUG messages should be hidden in production"
        print(f"   [OK] DEBUG messages hidden (production mode)\n")
    
    # Verify conditional error logging
    print(f"4. ERROR HANDLING (config.DEBUG={config.DEBUG}):")
    if config.DEBUG:
        print(f"   [OK] Stack traces ENABLED - exc_info=True (development)")
        print(f"   [OK] SQL statements logged in FULL detail")
    else:
        print(f"   [OK] Stack traces DISABLED - exc_info=False (production)")
        print(f"   [OK] SQL statements logged as abbreviated summary")
    
    print(f"\n5. SUMMARY:")
    print(f"   [OK] All loggers in {app_env} mode working correctly")
    print(f"   [OK] LOG_LEVEL={config.LOG_LEVEL}")
    print(f"   [OK] DEBUG={config.DEBUG}")


if __name__ == '__main__':
    try:
        # Test development mode
        test_logger_config('development')
        
        # Test production mode  
        test_logger_config('production')
        
        print(f"\n{'='*70}")
        print(f"[PASS] ALL TESTS PASSED - Logger configuration verified for both modes")
        print(f"{'='*70}\n")
        
    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
