"""
Database migration for API key management tables.

Creates api_keys and api_key_audit tables with proper indexes and constraints.
Supports both PostgreSQL and SQLite.

Run this migration during app startup or use db_migrations.py.
"""

import logging
from database import execute_query, DATABASE_TYPE

logger = logging.getLogger(__name__)


def migrate_create_api_key_tables():
    """
    Create API key management tables if they don't exist.
    
    Tables:
    - api_keys: Stores API keys with metadata and revocation status
    - api_key_audit: Audit trail for all API key operations
    
    Raises:
        Exception: If migration fails
    """
    try:
        if DATABASE_TYPE == 'postgres':
            migrate_postgres()
        else:
            migrate_sqlite()
        
        logger.info("API key tables migration completed successfully")
        
    except Exception as e:
        logger.error(f"API key tables migration failed: {e}")
        raise


def migrate_sqlite():
    """Create API key tables for SQLite"""
    
    # Create api_keys table
    execute_query("""
    CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key_hash TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        permissions TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        revoked_at TIMESTAMP,
        last_used_at TIMESTAMP,
        created_by TEXT
    )
    """)
    
    # Create api_key_audit table
    execute_query("""
    CREATE TABLE IF NOT EXISTS api_key_audit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key_hash TEXT NOT NULL,
        action TEXT NOT NULL,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (key_hash) REFERENCES api_keys(key_hash) ON DELETE CASCADE
    )
    """)
    
    # Create indexes for better query performance
    execute_query("""
    CREATE INDEX IF NOT EXISTS idx_api_keys_revoked ON api_keys(revoked_at)
    """)
    
    execute_query("""
    CREATE INDEX IF NOT EXISTS idx_audit_action ON api_key_audit(action)
    """)
    
    logger.info("SQLite API key tables created")


def migrate_postgres():
    """Create API key tables for PostgreSQL"""
    
    # Create api_keys table
    execute_query("""
    CREATE TABLE IF NOT EXISTS api_keys (
        id SERIAL PRIMARY KEY,
        key_hash TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        permissions TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        revoked_at TIMESTAMP NULL,
        last_used_at TIMESTAMP NULL,
        created_by TEXT
    )
    """)
    
    # Create api_key_audit table
    execute_query("""
    CREATE TABLE IF NOT EXISTS api_key_audit (
        id SERIAL PRIMARY KEY,
        key_hash TEXT NOT NULL,
        action TEXT NOT NULL,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (key_hash) REFERENCES api_keys(key_hash) ON DELETE CASCADE
    )
    """)
    
    # Create indexes for better query performance
    execute_query("""
    CREATE INDEX IF NOT EXISTS idx_api_keys_revoked ON api_keys(revoked_at)
    """)
    
    execute_query("""
    CREATE INDEX IF NOT EXISTS idx_audit_action ON api_key_audit(action)
    """)
    
    logger.info("PostgreSQL API key tables created")


if __name__ == '__main__':
    # Run migration directly if executed as script
    migrate_create_api_key_tables()
