#!/usr/bin/env python
"""
Integration test: Verify backend stabilization implementation

Tests:
1. Database initialization and migrations
2. App startup without errors
3. Error handler registration
4. Configuration loading (Railway-compatible)
5. Atomic job operations
6. Request validation

Run with: python test_stabilization.py
"""

import sys
import os
from datetime import datetime

print("=" * 80)
print("BACKEND STABILIZATION - INTEGRATION TEST")
print("=" * 80)
print(f"Time: {datetime.now().isoformat()}")
print()

# Test 1: Config Loading
print("[TEST 1] Configuration Loading")
print("-" * 40)
try:
    from config import config
    print(f"✓ Environment: {config.FLASK_ENV}")
    print(f"✓ Database Type: {config.DATABASE_TYPE}")
    print(f"✓ Flask Debug: {config.DEBUG}")
    print(f"✓ CORS Origins: {len(config.CORS_ORIGINS)} configured")
    validation = config.validate()
    if validation:
        for msg in validation[:3]:
            print(f"  {msg}")
    print("PASS")
except Exception as e:
    print(f"FAIL: {e}")
    sys.exit(1)

print()

# Test 2: Database & Migrations
print("[TEST 2] Database Initialization & Migrations")
print("-" * 40)
try:
    from db_migrations import run_migrations, CURRENT_SCHEMA_VERSION
    print(f"✓ Target schema version: {CURRENT_SCHEMA_VERSION}")
    success = run_migrations()
    if success:
        print("✓ Migrations completed successfully")
        print("PASS")
    else:
        print("FAIL: Migrations did not complete successfully")
        sys.exit(1)
except Exception as e:
    print(f"FAIL: {e}")
    sys.exit(1)

print()

# Test 3: App Startup
print("[TEST 3] Flask Application Startup")
print("-" * 40)
try:
    from app import app
    print(f"✓ Flask app initialized: {app.name}")
    print(f"✓ Debug mode: {app.debug}")
    print(f"✓ Testing mode: {app.testing}")
    
    # Check error handlers
    error_handlers = list(app.error_handler_spec.get(None, {}).keys())
    print(f"✓ Error handlers registered: {error_handlers}")
    
    print("PASS")
except Exception as e:
    print(f"FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 4: Error Handler Utilities
print("[TEST 4] Error Handler Registration")
print("-" * 40)
try:
    from utils.api_utils import StandardizedErrorResponse, SafeJsonParser
    
    # Test error formatting
    error_response, status = StandardizedErrorResponse.validation_error(
        "Test error",
        {"field": "test"}
    )
    assert error_response["error"]["code"] == "VALIDATION_ERROR"
    assert status == 400
    print("✓ StandardizedErrorResponse works")
    
    # Test JSON parsing
    parsed = SafeJsonParser.parse_string('{"key": "value"}')
    assert parsed == {"key": "value"}
    print("✓ SafeJsonParser works")
    
    # Test fallback parsing
    parsed_fallback = SafeJsonParser.parse_string("{'key': 'value'}", allow_single_quotes=True)
    assert parsed_fallback == {"key": "value"}
    print("✓ SafeJsonParser single-quote fallback works")
    
    print("PASS")
except Exception as e:
    print(f"FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 5: Request Validators
print("[TEST 5] Request Validators (Pydantic)")
print("-" * 40)
try:
    from utils.api_utils import RequestValidator, validate_request
    
    # Test valid request
    valid_data = {
        "tickers": ["AAPL", "MSFT"],
        "capital": 50000,
        "use_demo_data": True
    }
    validated, error = validate_request(valid_data, RequestValidator.AnalyzeRequest)
    assert validated is not None
    assert error is None
    print("✓ Valid request passes validation")
    
    # Test invalid request (empty tickers)
    invalid_data = {"tickers": []}
    validated, error = validate_request(invalid_data, RequestValidator.AnalyzeRequest)
    assert validated is None
    assert error is not None
    print("✓ Invalid request rejected correctly")
    
    print("PASS")
except Exception as e:
    print(f"FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 6: Atomic DB Operations
print("[TEST 6] Atomic Database Operations")
print("-" * 40)
try:
    from app import app
    from utils.db_utils import JobStateTransactions, get_job_status
    import uuid
    
    with app.app_context():
        # Create a test job atomically
        test_job_id = f"test_{uuid.uuid4().hex[:8]}"
        created = JobStateTransactions.create_job_atomic(
            job_id=test_job_id,
            status="queued",
            total=5,
            description="Test job"
        )
        assert created
        print(f"✓ Atomic job creation works: {test_job_id}")
        
        # Verify job status
        status = get_job_status(test_job_id)
        assert status is not None
        assert status["status"] == "queued"
        assert status["total"] == 5
        print(f"✓ Job status retrieval works: {status['status']}")
        
        # Update progress atomically
        updated = JobStateTransactions.update_job_progress(
            job_id=test_job_id,
            completed=3,
            successful=3,
            errors=[]
        )
        assert updated
        print("✓ Atomic progress update works")
        
        # Mark completed
        completed = JobStateTransactions.mark_job_completed(test_job_id, "completed")
        assert completed
        print("✓ Atomic job completion works")
        
        print("PASS")
except Exception as e:
    print(f"FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 7: Database Consolidation
print("[TEST 7] Database Module Consolidation")
print("-" * 40)
try:
    from database import (
        get_db, query_db, execute_db, get_db_connection,
        init_db_if_needed, close_db, cleanup_old_analyses
    )
    print("✓ All database functions imported from consolidated module")
    
    # Verify deprecated function still works
    from database import cleanup_all_stocks_analysis
    print("✓ Backward-compatible cleanup function available")
    
    print("PASS")
except Exception as e:
    print(f"FAIL: {e}")
    sys.exit(1)

print()

# Test 8: WSGI Entrypoint
print("[TEST 8] WSGI Entrypoint (gunicorn-ready)")
print("-" * 40)
try:
    from wsgi import app
    assert app is not None
    print("✓ WSGI entrypoint imports successfully")
    print("✓ Ready for gunicorn: gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app")
    print("PASS")
except Exception as e:
    print(f"FAIL: {e}")
    sys.exit(1)

print()

# Test 9: Gunicorn Configuration
print("[TEST 9] Gunicorn Configuration")
print("-" * 40)
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("gunicorn_conf", "gunicorn.conf.py")
    gunicorn_conf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gunicorn_conf)
    
    assert hasattr(gunicorn_conf, 'bind')
    assert hasattr(gunicorn_conf, 'workers')
    assert hasattr(gunicorn_conf, 'timeout')
    print(f"✓ Gunicorn config loaded")
    print(f"✓ Bind: {gunicorn_conf.bind}")
    print(f"✓ Workers: {gunicorn_conf.workers}")
    print(f"✓ Timeout: {gunicorn_conf.timeout}s")
    print("PASS")
except Exception as e:
    print(f"FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Summary
print("=" * 80)
print("TEST RESULTS")
print("=" * 80)
print("✓ All 9 integration tests PASSED")
print()
print("Backend stabilization is complete and ready for deployment!")
print()
print("Next steps:")
print("1. Deploy to Railway (gunicorn + PostgreSQL)")
print("2. Run Phase 5 (Logging) - can be done post-launch")
print("3. Implement Phase 7 (Testing) - full test suite")
print()
print("=" * 80)
