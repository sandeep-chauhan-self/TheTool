"""
Database Migration: Add Constraints and Indices to Fix Critical Failure Points
PostgreSQL Version - Wrapper for migrations_add_constraints_postgres.py

Run this migration with:
  railway run python backend/migrations_add_constraints.py

On Railway, it will automatically use the PostgreSQL DATABASE_URL environment variable.
"""

import os
import sys

# Configuration
DATABASE_URL = os.getenv('DATABASE_URL', '')
DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'postgres')

print("\n" + "="*60)
print("Database Migration: Add Constraints & Indices")
print(f"Database Type: {DATABASE_TYPE}")
print("="*60 + "\n")

if DATABASE_TYPE == 'postgres' or DATABASE_URL:
    # Try to import psycopg2
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 not installed!")
        print("   On Railway, this should be pre-installed.")
        print("   Locally, run: pip install psycopg2-binary")
        sys.exit(1)
    
    # Import and run PostgreSQL migration
    try:
        from migrations_add_constraints_postgres import run_migration
        success = run_migration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
else:
    print("❌ Invalid DATABASE_TYPE or DATABASE_URL not set!")
    print(f"   DATABASE_TYPE: {DATABASE_TYPE}")
    print(f"   DATABASE_URL: {'set' if DATABASE_URL else 'NOT SET'}")
    print("\n   Please configure:")
    print("   - On Railway: Set DATABASE_URL environment variable (auto-configured)")
    print("   - Locally: export DATABASE_URL='postgresql://user:pass@host/db'")
    sys.exit(1)
